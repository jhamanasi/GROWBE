import os
import sqlite3
import glob
from pathlib import Path


MIGRATIONS_DIR = Path(__file__).parent
DB_PATH = Path(__file__).parents[1] / "data" / "financial_data.db"


def apply_migrations():
    os.makedirs(DB_PATH.parent, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS _migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT UNIQUE NOT NULL,
                applied_at DATETIME DEFAULT (datetime('now'))
            );
            """
        )
        applied = {row[0] for row in conn.execute("SELECT filename FROM _migrations")}
        files = sorted(glob.glob(str(MIGRATIONS_DIR / "*.sql")))
        for f in files:
            name = os.path.basename(f)
            if name in applied:
                continue
            with open(f, "r", encoding="utf-8") as fh:
                sql = fh.read()
            conn.executescript(sql)
            conn.execute("INSERT INTO _migrations(filename) VALUES (?)", (name,))
            conn.commit()
            print(f"Applied migration: {name}")
    finally:
        conn.close()


if __name__ == "__main__":
    apply_migrations()


