"""
FastAPI router for conversation and message management.

Endpoints:
- POST /api/conversations/start - Create new conversation
- POST /api/conversations/{conversation_id}/message - Send message and get agent response
- GET /api/conversations - List conversations for user
- GET /api/conversations/{conversation_id}/messages - Get messages for conversation
- POST /api/conversations/{conversation_id}/summary - Generate title/summary
- POST /api/conversations/{conversation_id}/new - Start new chat from existing
- DELETE /api/conversations/{conversation_id} - Soft delete conversation
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid
import re
import json
import sqlite3
from pathlib import Path
from datetime import datetime

from services.conversation_service import conversation_service
from services.customer_service import customer_service
from tools.nl2sql_tool import get_last_sql_details, clear_sql_details
from tools.debt_optimizer_tool import get_last_calculation_details, clear_calculation_details
from tools.rent_vs_buy_tool import get_last_rent_buy_details, clear_rent_buy_details

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


# Request/Response Models
class StartConversationRequest(BaseModel):
    customer_id: Optional[str] = None
    session_id: Optional[str] = None  # UUIDv4 for Scenario B
    scenario_type: str  # "existing" or "new"
    initial_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class StartConversationResponse(BaseModel):
    conversation_id: str
    title: str
    customer_id: Optional[str] = None
    session_id: Optional[str] = None


class SendMessageRequest(BaseModel):
    message: str


class SendMessageResponse(BaseModel):
    message_id: str
    content: str
    sql_details: Optional[Dict[str, Any]] = None
    calculation_details: Optional[Dict[str, Any]] = None
    tool_payload: Optional[Dict[str, Any]] = None


class ConversationListItem(BaseModel):
    conversation_id: str
    title: str
    preview: str
    last_message_at: Optional[str] = None
    message_count: int
    scenario_type: str


class MessageItem(BaseModel):
    message_id: str
    role: str
    content: Optional[str]
    tool_name: Optional[str] = None
    tool_payload: Optional[Dict[str, Any]] = None
    sql_details: Optional[Dict[str, Any]] = None
    calculation_details: Optional[Dict[str, Any]] = None
    chart_data: Optional[Dict[str, Any]] = None
    created_at: str


class SummaryResponse(BaseModel):
    title: str
    summary: str


# Helper function to check if customer_id is predefined (C001-C018)
def is_predefined_customer_id(customer_id: Optional[str]) -> bool:
    if not customer_id:
        return False
    m = re.match(r"^C(\d{3,})$", str(customer_id).strip().upper())
    if not m:
        return False
    try:
        return int(m.group(1)) <= 18
    except ValueError:
        return False


# Endpoints
@router.post("/start", response_model=StartConversationResponse)
async def start_conversation(request: StartConversationRequest):
    """Create a new conversation."""
    if request.scenario_type not in ["existing", "new"]:
        raise HTTPException(status_code=400, detail="scenario_type must be 'existing' or 'new'")

    # Validate customer_id exists for Scenario A
    if request.scenario_type == "existing" and request.customer_id:
        customer = customer_service.get_customer(request.customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail=f"Customer {request.customer_id} not found")

    # Generate session_id if not provided for Scenario B
    session_id = request.session_id or (str(uuid.uuid4()) if request.scenario_type == "new" else None)

    conv = conversation_service.create_conversation(
        customer_id=request.customer_id,
        scenario_type=request.scenario_type,
        initial_message=request.initial_message,
        metadata=request.metadata,
        session_id=session_id,
    )

    # Auto-generate a concise title/summary on creation
    try:
        conversation_service.generate_conversation_title(conv["conversation_id"]) 
    except Exception:
        pass

    return StartConversationResponse(
        conversation_id=conv["conversation_id"],
        title=conv.get("title", "New Chat"),
        customer_id=conv.get("customer_id"),
        session_id=conv.get("session_id"),
    )


@router.post("/{conversation_id}/message", response_model=SendMessageResponse)
async def send_message(conversation_id: str, request: SendMessageRequest):
    """
    Send a user message, get agent response, and persist both with tool outputs.

    Flow:
    1. Save user message to DB
    2. Fetch last 10 messages from DB for context
    3. Build agent prompt with context
    4. Call agent (with gating based on scenario_type)
    5. Save assistant message with tool outputs (sql_details, calculation_details)
    6. Return response
    """
    from strands import Agent
    from strands.models.openai import OpenAIModel
    from tools.tool_manager import registry
    from tools.customer_profile_tool import CustomerProfileTool
    from utils.prompt_loader import load_system_prompt
    import os

    # Get conversation to determine scenario and customer_id
    db_path = Path(__file__).resolve().parents[1] / "data" / "financial_data.db"
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            "SELECT customer_id, session_id, scenario_type FROM conversations WHERE conversation_id = ? AND is_active = 1",
            (conversation_id,),
        )
        conv_row = cur.fetchone()
        if not conv_row:
            raise HTTPException(status_code=404, detail="Conversation not found")
        conv_data = dict(conv_row)

    customer_id = conv_data.get("customer_id")
    scenario_type = conv_data.get("scenario_type", "new")

    # Step 1: Save user message FIRST
    user_msg = conversation_service.add_message(
        conversation_id=conversation_id,
        role="user",
        content=request.message,
    )

    # Step 2: Get last 10 messages from DB for agent context
    all_messages = conversation_service.get_messages(conversation_id, limit=100)
    last_10 = all_messages[-10:] if len(all_messages) > 10 else all_messages

    # Step 3: Build agent prompt with context
    message_parts = []

    # Add scenario context
    scenario_line = (
        "Scenario: Existing user with full profile."
        if scenario_type == "existing"
        else "Scenario: New user with no stored profile — collect missing data before tool calls."
    )
    message_parts.append(scenario_line)

    # Add customer context if existing user
    customer_context = None
    if scenario_type == "existing" and customer_id:
        try:
            customer_context = customer_service.get_customer_context(customer_id)
            if customer_context:
                message_parts.append(f"Customer Context:\n{customer_context}")
        except Exception as e:
            print(f"⚠️ Warning: Could not retrieve customer context: {e}")

    # Add customer ID token if existing
    if scenario_type == "existing" and customer_id:
        message_parts.append(f"Explicit Customer ID Token: {customer_id}")

    # Add conversation history from DB (last 10 messages)
    if last_10:
        history_text = "Conversation History:"
        for msg in last_10:
            role_name = "User" if msg.get("role") == "user" else "Assistant"
            content = msg.get("content", "") or ""
            if content.strip():
                history_text += f"\n\n{role_name}: {content}"
        message_parts.append(history_text)

    # Add current user message
    message_parts.append(f"User Message: {request.message}")

    message_with_context = "\n\n".join(filter(None, message_parts))

    # Step 4: Clear tool results from previous requests
    clear_sql_details()
    clear_calculation_details()
    clear_rent_buy_details()

    # Step 5: Determine DB access gating
    use_db = (scenario_type == "existing") and is_predefined_customer_id(customer_id)

    # Step 6: Call agent with appropriate tools
    try:
        openai_model = OpenAIModel(
            client_args={"api_key": os.getenv("OPENAI_API_KEY")},
            model_id="gpt-4o",
            params={"max_tokens": 2500, "temperature": 0.2},
        )

        if not use_db:
            # Scenario B: No DB tools
            from tools.tool_manager import registry as tool_registry
            allowed_tools = [
                t for t in tool_registry.get_all_tools() if t.name not in {"nl2sql_query", "sqlite_query"}
            ]
            session_agent = Agent(
                model=openai_model,
                tools=allowed_tools,
            )
            system_guardrail = (
                "System: You are in assessment mode or using a non-preloaded user. "
                "Do not query the database. Do not use NL2SQL or SQLite. "
                "Collect information, run calculators, and update assessments only."
            )
            agent_result = session_agent(f"{message_with_context}\n\n{system_guardrail}")
        else:
            # Scenario A: Full tools including DB
            customer_profile_tool = CustomerProfileTool()
            financial_agent = Agent(
                model=openai_model,
                system_prompt=load_system_prompt("fin-adv-v2"),
                tools=registry.get_strands_tools() + [customer_profile_tool.to_strands_tool()],
            )
            agent_result = financial_agent(message_with_context)

        # Extract response text
        if hasattr(agent_result, "content"):
            response = agent_result.content
        elif hasattr(agent_result, "text"):
            response = agent_result.text
        elif isinstance(agent_result, str):
            response = agent_result
        else:
            response = str(agent_result)

    except Exception as e:
        print(f"❌ Agent error: {str(e)}")
        import traceback
        traceback.print_exc()
        # Save error message
        error_msg = conversation_service.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=f"I encountered an error: {str(e)}",
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Agent failed: {str(e)}")

    # Step 7: Capture tool outputs
    sql_details = get_last_sql_details()
    calculation_details = get_last_calculation_details()
    if not calculation_details:
        calculation_details = get_last_rent_buy_details()

    # Step 8: Save assistant message with tool outputs
    assistant_msg = conversation_service.add_message(
        conversation_id=conversation_id,
        role="assistant",
        content=response,
        sql_details=sql_details,
        calculation_details=calculation_details,
    )

    # Auto-title generation every 6 assistant messages
    try:
        # Count assistant messages; if multiple of 6, refresh title
        db_path = Path(__file__).resolve().parents[1] / "data" / "financial_data.db"
        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT COUNT(*) FROM chat_messages WHERE conversation_id = ? AND role = 'assistant' AND is_active = 1",
                (conversation_id,),
            )
            count = cur.fetchone()[0]
        if count and count % 6 == 0:
            conversation_service.generate_conversation_title(conversation_id)
    except Exception:
        pass

    # Step 9: Return response
    return SendMessageResponse(
        message_id=assistant_msg["message_id"],
        content=response,
        sql_details=json.loads(assistant_msg["sql_details"]) if assistant_msg.get("sql_details") else None,
        calculation_details=json.loads(assistant_msg["calculation_details"])
        if assistant_msg.get("calculation_details")
        else None,
        tool_payload=None,  # Can be extended if needed
    )


@router.get("", response_model=List[ConversationListItem])
async def list_conversations(customer_id: Optional[str] = None, session_id: Optional[str] = None):
    """List conversations for a customer or session."""
    convs = conversation_service.list_conversations(customer_id=customer_id, session_id=session_id)
    return [
        ConversationListItem(
            conversation_id=c["conversation_id"],
            title=c.get("title", "New Chat"),
            preview=c.get("preview", ""),
            last_message_at=c.get("last_message_at"),
            message_count=c.get("message_count", 0),
            scenario_type=c.get("scenario_type", "new"),
        )
        for c in convs
    ]


# Helper function to safely parse JSON strings
def parse_json_field(value):
    """Parse a JSON field that might be a string or already a dict."""
    if not value:
        return None
    if isinstance(value, dict):
        return value  # Already a dict
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else None
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            print(f"⚠️ Failed to parse JSON field: {e}, value: {value[:100] if len(str(value)) > 100 else value}")
            return None
    return None


@router.get("/{conversation_id}/messages", response_model=List[MessageItem])
async def get_messages(conversation_id: str, limit: int = 30, offset: int = 0):
    """Get messages for a conversation (ascending order)."""
    messages = conversation_service.get_messages(conversation_id, limit=limit, offset=offset)
    result = []
    for msg in messages:
        try:
            # Parse JSON fields safely
            tool_payload = parse_json_field(msg.get("tool_payload"))
            sql_details = parse_json_field(msg.get("sql_details"))
            calc_details = parse_json_field(msg.get("calculation_details"))
            chart_data = parse_json_field(msg.get("chart_data"))
            
            item = MessageItem(
                message_id=msg["message_id"],
                role=msg["role"],
                content=msg.get("content"),
                tool_name=msg.get("tool_name"),
                tool_payload=tool_payload,
                sql_details=sql_details,
                calculation_details=calc_details,
                chart_data=chart_data,
                created_at=msg["created_at"],
            )
            result.append(item)
        except Exception as e:
            print(f"❌ Error processing message {msg.get('message_id')}: {e}")
            print(f"   Raw calculation_details type: {type(msg.get('calculation_details'))}")
            print(f"   Raw calculation_details value: {str(msg.get('calculation_details'))[:200]}")
            # Skip this message or create a minimal version
            continue
    return result


@router.post("/{conversation_id}/summary", response_model=SummaryResponse)
async def generate_summary(conversation_id: str):
    """Generate title and summary for a conversation."""
    result = conversation_service.generate_conversation_title(conversation_id)
    return SummaryResponse(title=result["title"], summary=result.get("summary", ""))


@router.post("/{conversation_id}/new", response_model=StartConversationResponse)
async def start_new_from_existing(conversation_id: str):
    """Start a new conversation from an existing one (clone metadata)."""
    conv = conversation_service.start_new_chat_from(conversation_id)
    return StartConversationResponse(
        conversation_id=conv["conversation_id"],
        title=conv.get("title", "New Chat"),
        customer_id=conv.get("customer_id"),
        session_id=conv.get("session_id"),
    )


@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Soft delete a conversation."""
    db_path = Path(__file__).resolve().parents[1] / "data" / "financial_data.db"
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE conversations SET is_active = 0, updated_at = ? WHERE conversation_id = ?",
            (datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), conversation_id),
        )
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "deleted", "conversation_id": conversation_id}


@router.get("/{conversation_id}/export")
async def export_conversation(conversation_id: str):
    """Export a full conversation as JSON including messages and tool payloads."""
    db_path = Path(__file__).resolve().parents[1] / "data" / "financial_data.db"
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Conversation
        cur.execute(
            "SELECT * FROM conversations WHERE conversation_id = ?",
            (conversation_id,),
        )
        conv = cur.fetchone()
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Messages (ascending)
        cur.execute(
            """
            SELECT * FROM chat_messages
             WHERE conversation_id = ? AND is_active = 1
             ORDER BY created_at ASC
            """,
            (conversation_id,),
        )
        msgs = [dict(r) for r in cur.fetchall()]

    # Parse JSON text fields for convenience
    for m in msgs:
        for field in ("tool_payload", "sql_details", "calculation_details"):
            val = m.get(field)
            if isinstance(val, str):
                try:
                    m[field] = json.loads(val)
                except Exception:
                    pass

    export = {
        "conversation": dict(conv),
        "messages": msgs,
    }
    return export

