import os
import sqlite3
from typing import Any, Dict, Iterable, List, Optional, Sequence, Union
from pathlib import Path
from .base_tool import BaseTool


def _db_path() -> str:
    # Go up one level from tools/ to backend/ directory
    BASE_DIR = Path(__file__).parent.parent
    # Check for environment variable first, then default to financial database
    db_path = os.getenv("SQLITE_DB_PATH", "data/financial_data.db")
    if not os.path.isabs(db_path):
        DB_PATH = BASE_DIR / db_path
    else:
        DB_PATH = Path(db_path)
    print(f"Looking for database at: {DB_PATH}")
    return str(DB_PATH)


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(
        _db_path(),
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
        timeout=10,
        check_same_thread=False,
        isolation_level=None,  # autocommit
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    return conn


def _first_token(sql: str) -> str:
    s = sql.lstrip()
    while s.startswith("/*"):
        end = s.find("*/")
        if end == -1:
            break
        s = s[end + 2 :].lstrip()
    while s.startswith("--"):
        nl = s.find("\n")
        if nl == -1:
            return ""
        s = s[nl + 1 :].lstrip()
    for ch in ("(",):
        if s.startswith(ch):
            s = s[1:].lstrip()
    return (s.split(None, 1)[0] if s else "").upper()


class SQLiteTool(BaseTool):
    @property
    def name(self) -> str:
        return "sqlite_query"

    @property
    def description(self) -> str:
        return (
            "Run SQLite queries against the financial advisory database. "
            "Args: sql (str), params (dict|list|tuple)=None, many (sequence)=None, "
            "write (bool)=False, script (bool)=False, limit (int|None)=200, explain (bool)=False. "
            "DB path via env SQLITE_DB_PATH, default ./data/financial_data.db"
        )

    def execute(
        self,
        sql: str,
        params: Optional[Union[Sequence[Any], Dict[str, Any]]] = None,
        many: Optional[Sequence[Union[Sequence[Any], Dict[str, Any]]]] = None,
        write: bool = False,
        script: bool = False,
        limit: Optional[int] = 200,
        explain: bool = False,
    ) -> Dict[str, Any]:
        if not sql or not sql.strip():
            raise ValueError("sql is required and cannot be empty")

        first = _first_token(sql)
        is_read = first in ("SELECT", "WITH")

        if script and not write:
            raise ValueError("script=True requires write=True.")
        if not write and not is_read:
            raise ValueError("Read-only mode: only SELECT/WITH statements allowed. Set write=True to modify.")

        # Optional safety: require explicit customer_id on sensitive reads
        import re
        upper_sql = sql.upper()
        sensitive_tables = {"DEBTS_LOANS", "ACCOUNTS", "TRANSACTIONS", "CREDIT_REPORTS", "ASSETS", "EMPLOYMENT_INCOME", "CUSTOMERS"}
        touches_sensitive = any(f" {t} " in upper_sql or upper_sql.startswith(f"SELECT * FROM {t}") for t in sensitive_tables)
        if touches_sensitive and _first_token(sql) in ("SELECT", "WITH"):
            if re.search(r"CUSTOMER_ID\s*=\s*'C\d{3,}'", upper_sql) is None:
                return {"ok": False, "error": "SQL must include explicit customer_id filter (e.g., customer_id='C004') for sensitive tables."}

        conn = _connect()
        try:
            if write:
                conn.execute("BEGIN IMMEDIATE;")

            cur = conn.cursor()
            result: Dict[str, Any] = {"ok": True, "rowcount": 0, "last_row_id": None}

            if script:
                cur.executescript(sql)
                result["rowcount"] = cur.rowcount if cur.rowcount is not None else 0

            elif many is not None:
                cur.executemany(sql, many)
                result["rowcount"] = cur.rowcount if cur.rowcount is not None else 0
                result["last_row_id"] = cur.lastrowid

            else:
                cur.execute(sql, params or [])
                if is_read:
                    rows: List[Dict[str, Any]] = []
                    fetched = cur.fetchmany(limit if limit is not None else 1000000000)
                    columns = [d[0] for d in cur.description] if cur.description else []
                    for r in fetched:
                        rows.append({k: r[k] for k in r.keys()})
                    result.update({"rows": rows, "columns": columns, "rowcount": len(rows)})
                    if explain:
                        plan_cur = conn.execute(f"EXPLAIN QUERY PLAN {sql}", params or [])
                        plan = [dict(row) for row in plan_cur.fetchall()]
                        result["plan"] = plan
                else:
                    result["rowcount"] = cur.rowcount if cur.rowcount is not None else 0
                    result["last_row_id"] = cur.lastrowid

            if write:
                conn.commit()
            return result

        except Exception as e:
            if write:
                conn.rollback()
            return {"ok": False, "error": str(e)}
        finally:
            conn.close()
