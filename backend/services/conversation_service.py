"""
Conversation Service for persisting conversations and messages.

Responsibilities:
- Create conversations (Scenario A via customer_id; Scenario B via session_id after API layer)
- Persist chat messages, including tool outputs (tool_payload, sql_details, calculation_details)
- List conversations with latest preview
- Fetch messages (ascending)
- Generate short title and summary via LLM, persist to conversation_summaries and conversations
- Start a new chat from an existing one (clone metadata)
"""

import sqlite3
import uuid
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


DB_PATH = Path(__file__).resolve().parents[1] / "data" / "financial_data.db"


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    return conn


def _now_iso() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


class ConversationService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = Path(db_path) if db_path else DB_PATH

    # Core APIs
    def create_conversation(
        self,
        customer_id: Optional[str],
        scenario_type: str,
        initial_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        conversation_id = str(uuid.uuid4())
        title = (initial_message or "New Chat").strip()[:60] if initial_message else "New Chat"
        metadata_text = json.dumps(metadata or {})
        now = _now_iso()

        with _get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO conversations (
                    conversation_id, customer_id, session_id, title, summary, scenario_type,
                    is_active, created_at, updated_at, metadata, message_count, last_message_at
                ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?, 0, NULL)
                """,
                (
                    conversation_id,
                    customer_id,
                    session_id,
                    title,
                    None,
                    scenario_type,
                    now,
                    now,
                    metadata_text,
                ),
            )

            if initial_message:
                # Insert initial assistant welcome message using the SAME connection to avoid SQLite lock
                message_id = str(uuid.uuid4())
                cur.execute(
                    """
                    INSERT INTO chat_messages (
                        message_id, conversation_id, role, content, tool_name, tool_payload,
                        sql_details, calculation_details, error, is_active, created_at
                    ) VALUES (?, ?, 'assistant', ?, NULL, NULL, NULL, NULL, NULL, 1, ?)
                    """,
                    (
                        message_id,
                        conversation_id,
                        initial_message,
                        now,
                    ),
                )
                # Update counters for the conversation within the same transaction
                cur.execute(
                    """
                    UPDATE conversations
                       SET updated_at = ?, last_message_at = ?, message_count = COALESCE(message_count,0) + 1
                     WHERE conversation_id = ?
                    """,
                    (now, now, conversation_id),
                )

            cur.execute(
                "SELECT * FROM conversations WHERE conversation_id = ?",
                (conversation_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else {
                "conversation_id": conversation_id,
                "customer_id": customer_id,
                "session_id": session_id,
                "title": title,
                "scenario_type": scenario_type,
            }

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: Optional[str],
        tool_name: Optional[str] = None,
        tool_payload: Optional[Any] = None,
        sql_details: Optional[Any] = None,
        calculation_details: Optional[Any] = None,
        chart_data: Optional[Any] = None,
        error: Optional[str] = None,
    ) -> Dict[str, Any]:
        message_id = str(uuid.uuid4())
        now = _now_iso()

        # Serialize JSON fields to TEXT
        tool_payload_text = json.dumps(tool_payload) if tool_payload is not None else None
        sql_details_text = json.dumps(sql_details) if sql_details is not None else None
        calc_details_text = json.dumps(calculation_details) if calculation_details is not None else None
        chart_data_text = json.dumps(chart_data) if chart_data is not None else None

        with _get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO chat_messages (
                    message_id, conversation_id, role, content, tool_name, tool_payload,
                    sql_details, calculation_details, chart_data, error, is_active, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                """,
                (
                    message_id,
                    conversation_id,
                    role,
                    content,
                    tool_name,
                    tool_payload_text,
                    sql_details_text,
                    calc_details_text,
                    chart_data_text,
                    error,
                    now,
                ),
            )

            # Update conversation counters
            cur.execute(
                """
                UPDATE conversations
                   SET updated_at = ?, last_message_at = ?, message_count = COALESCE(message_count,0) + 1
                 WHERE conversation_id = ?
                """,
                (now, now, conversation_id),
            )

            # Return inserted message
            cur.execute(
                "SELECT * FROM chat_messages WHERE message_id = ?",
                (message_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else {
                "message_id": message_id,
                "conversation_id": conversation_id,
                "role": role,
                "content": content,
                "created_at": now,
            }

    def list_conversations(self, customer_id: Optional[str] = None, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return conversations for a customer or session, newest first, with a preview from last message."""
        where = ["is_active = 1"]
        params: List[Any] = []
        if customer_id:
            where.append("customer_id = ?")
            params.append(customer_id)
        if session_id and not customer_id:
            # Only use session fallback when no customer_id is present yet
            where.append("session_id = ?")
            params.append(session_id)
        where_sql = " AND ".join(where)

        sql = f"""
            SELECT c.*, (
                SELECT cm.content FROM chat_messages cm
                 WHERE cm.conversation_id = c.conversation_id AND cm.is_active = 1
                 ORDER BY cm.created_at DESC LIMIT 1
            ) AS last_message
            FROM conversations c
            WHERE {where_sql}
            ORDER BY COALESCE(c.last_message_at, c.updated_at) DESC
        """

        with _get_connection() as conn:
            rows = conn.execute(sql, params).fetchall()
            result: List[Dict[str, Any]] = []
            for r in rows:
                item = dict(r)
                preview = (item.get("last_message") or "").strip()
                item["preview"] = preview[:120] if preview else ""
                result.append(item)
            return result

    def get_messages(self, conversation_id: str, limit: int = 30, offset: int = 0) -> List[Dict[str, Any]]:
        sql = (
            "SELECT * FROM chat_messages WHERE conversation_id = ? AND is_active = 1 "
            "ORDER BY created_at ASC LIMIT ? OFFSET ?"
        )
        with _get_connection() as conn:
            rows = conn.execute(sql, (conversation_id, limit, offset)).fetchall()
            return [dict(r) for r in rows]

    def generate_conversation_title(self, conversation_id: str, model: str = "gpt-4o") -> Dict[str, Any]:
        """Generate a <=6-word title and one-line summary using the LLM; persist results."""
        # Pull last few messages as context
        with _get_connection() as conn:
            messages = conn.execute(
                """
                SELECT role, content FROM chat_messages
                 WHERE conversation_id = ? AND is_active = 1
                 ORDER BY created_at ASC LIMIT 20
                """,
                (conversation_id,),
            ).fetchall()

        convo_text = []
        for m in messages:
            role = m["role"]
            content = (m["content"] or "").strip()
            if content:
                convo_text.append(f"{role}: {content}")
        joined = "\n".join(convo_text) or "user: New chat"

        # Use Strands Agent with OpenAI model to produce JSON {"title": "...", "summary": "..."}
        title, summary = None, None
        try:
            from strands import Agent
            from strands.models.openai import OpenAIModel
            import os

            openai_model = OpenAIModel(
                client_args={"api_key": os.getenv("OPENAI_API_KEY")},
                model_id=model,
                params={"max_tokens": 200, "temperature": 0.2},
            )
            system = (
                "You create concise conversation titles and one-line summaries. "
                "Respond ONLY JSON with keys 'title' and 'summary'. Title must be <=6 words."
            )
            prompt = (
                "Given the following chat messages, produce: "
                "1) a concise title of at most 6 words, and 2) a one-sentence summary of the user's primary goal.\n\n"
                + joined
            )
            agent = Agent(model=openai_model, system_prompt=system)
            result = agent(prompt)
            text = getattr(result, "content", getattr(result, "text", str(result)))
            data = json.loads(text) if isinstance(text, str) else {}
            # Enforce <=6 words for title
            raw_title = (data.get("title") or "New Chat").strip()
            words = [w for w in raw_title.split() if w]
            title = " ".join(words[:6]) if words else "New Chat"
            summary = (data.get("summary") or "").strip()
        except Exception:
            # Fallback: first user line
            for m in messages:
                if m["role"] == "user" and m["content"]:
                    # Take first 6 words as fallback title
                    _words = [w for w in m["content"].strip().split() if w]
                    title = " ".join(_words[:6]) if _words else "New Chat"
                    break
            title = title or "New Chat"
            summary = summary or ""

        # Persist into conversation_summaries and update conversations.title
        with _get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO conversation_summaries (conversation_id, short_title, summary_text, updated_at, metadata)
                VALUES (?, ?, ?, ?, '{}')
                ON CONFLICT(conversation_id) DO UPDATE SET
                    short_title=excluded.short_title,
                    summary_text=excluded.summary_text,
                    updated_at=excluded.updated_at
                """,
                (conversation_id, title, summary, _now_iso()),
            )
            cur.execute(
                "UPDATE conversations SET title = ?, updated_at = ? WHERE conversation_id = ?",
                (title, _now_iso(), conversation_id),
            )
        return {"title": title, "summary": summary}

    def start_new_chat_from(self, conversation_id: str) -> Dict[str, Any]:
        """Clone conversation metadata into a fresh conversation (no messages)."""
        with _get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT customer_id, session_id, scenario_type, metadata FROM conversations WHERE conversation_id = ?",
                (conversation_id,),
            )
            row = cur.fetchone()
            if not row:
                raise ValueError("Conversation not found")
            metadata = row["metadata"] if row["metadata"] else "{}"
            try:
                meta_dict = json.loads(metadata)
            except Exception:
                meta_dict = {}
            return self.create_conversation(
                customer_id=row["customer_id"],
                scenario_type=row["scenario_type"],
                initial_message=None,
                metadata=meta_dict,
                session_id=row["session_id"],
            )


# Global instance
conversation_service = ConversationService()


