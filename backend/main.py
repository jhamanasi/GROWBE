from fastapi import FastAPI, HTTPException, Depends

print("🚀 [DEBUG] Loading main.py - CURRENT VERSION")
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import os
from dotenv import load_dotenv
try:
    # Apply database migrations early so tables exist before use
    from migrations.run_migrations import apply_migrations
    apply_migrations()
    print("✅ Database migrations applied")
except Exception as mig_e:
    print(f"⚠️ Warning: Failed to apply migrations: {mig_e}")
from tools.tool_manager import registry
import json
import asyncio
from typing import List, Optional, Dict
import re

# Financial agent imports
from services.customer_service import customer_service
from services.conversation_service import conversation_service
from hooks.financial_conversation_hook import FinancialConversationHook
from hooks.sql_capture_hook import SQLResultCaptureHook
from hooks.calculation_capture_hook import CalculationCaptureHook
from hooks.conversation_capture_hook import ConversationCaptureHook
from hooks.chart_capture_hook import ChartCaptureHook
from tools.nl2sql_tool import get_last_sql_details, clear_sql_details
from tools.debt_optimizer_tool import get_last_calculation_details, clear_calculation_details
from tools.rent_vs_buy_tool import get_last_rent_buy_details, clear_rent_buy_details
from tools.visualization_tool import get_last_chart_data, clear_chart_data

# Tool imports
from tools.customer_profile_tool import CustomerProfileTool

# Prompt loader import
from utils.prompt_loader import load_system_prompt

def get_scenario_b_system_prompt() -> str:
    """
    Get the unified Scenario B system prompt for new users without database access.
    
    This prompt guides the agent to:
    1. Ask for missing parameters BEFORE calling tools
    2. Handle tool errors gracefully
    3. Provide friendly, helpful responses
    """
    return """You are Growbe, a helpful AI financial advisor.

You are helping a new user who doesn't have a full financial profile yet.
You can help them with financial calculations, assessments, and general financial advice.
You cannot access their personal financial database, but you can use calculators and tools to help them.

🎯 CORE PRINCIPLE: ASK FIRST, CALCULATE SECOND
Before calling ANY tool, verify you have ALL required information. If anything is missing, ask the user for it first.

CRITICAL CONVERSATION FLOW FOR FINANCIAL CALCULATIONS:

1️⃣ WHEN USER MENTIONS A FINANCIAL GOAL (without providing full details):
   - DO NOT call any calculation tool immediately
   - Respond enthusiastically and ask for the required information
   - Be specific about what you need
   
   Example user message: "I want to pay off my student loan"
   
   Your response should be:
   "That's great! I'd love to help you create a payoff plan. To give you the most accurate calculations, I'll need a few details:
   
   • The current loan balance (e.g., $40,000)
   • The interest rate (e.g., 4% APR or 4.0)
   • The loan type (student, auto, credit_card, personal, or mortgage)
   • Your target payoff timeframe, if you have one (e.g., 1 year or 12 months)
   
   Once I have these details, I can calculate the exact monthly payment you'll need and show you the total interest you'll pay!"

2️⃣ WHEN USER PROVIDES ALL REQUIRED DETAILS:
   - Verify you have extracted all required parameters
   - Call the appropriate tool with correct parameter types:
     * Loan amounts: numbers (e.g., 40000 for $40,000, NOT "$40,000")
     * Interest rates: numbers (e.g., 4.0 for 4% APR, NOT 0.04 or "4%")
     * Debt types: exact strings ('student', 'auto', 'credit_card', 'personal', 'mortgage')
     * Time periods: numbers in months (e.g., 12 for 1 year, NOT "12 months" or "1 year")
   
   Example tool call:
   debt_optimizer(principal=40000, interest_rate_apr=4.0, debt_type='student', target_payoff_months=12)

3️⃣ REQUIRED PARAMETERS CHECKLIST:
   
   For debt_optimizer tool:
   ✓ principal (loan amount) - required
   ✓ interest_rate_apr (APR as percentage) - required
   ✓ debt_type (loan type) - required
   ✓ scenario_type (current/extra_payment/target_payoff/refinance) - optional, defaults to 'current'
   ✓ target_payoff_months (payoff timeframe) - required ONLY for target_payoff scenario
   ✓ extra_payment (additional payment) - required ONLY for extra_payment scenario
   
   If ANY required parameter is missing, ASK the user first. DO NOT call the tool.

4️⃣ ERROR HANDLING:
   - If a tool returns an error with 'user_friendly: True' or 'stop_retrying: True', STOP IMMEDIATELY
   - DO NOT call the tool again. DO NOT retry
   - Present the error message from 'error' or 'message_for_user' field to the user exactly as written
   - The error message is already user-friendly - just show it to them

5️⃣ PARAMETER EXTRACTION RULES:
   - Extract loan amounts from strings like "$40,000", "40K", "40000" → 40000
   - Extract interest rates from strings like "4%", "4.0%", "4" → 4.0
   - Extract timeframes from strings like "1 year", "12 months", "12" → 12 (always in months)
   - Map loan types: "student loan" → "student", "car loan" → "auto", "credit card" → "credit_card"

PERSONALITY & APPROACH:
- Be friendly, professional, and encouraging
- Ask clarifying questions naturally
- Celebrate user goals ("That's great!", "I'm excited to help you with that!")
- Provide context for why you need information ("To give you the most accurate calculations...")
- Break down complex concepts into simple terms

Remember: Your primary goal is to help users make informed financial decisions. Always prioritize accuracy and user understanding over speed."""

# Load environment variables AS EARLY AS POSSIBLE and configure OTEL before importing Strands
# load_dotenv()
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
# Keep logs clean during streaming teardown: disable OTEL by default in dev (can override in real env)
if os.getenv("OTEL_SDK_DISABLED") is None:
    os.environ["OTEL_SDK_DISABLED"] = "true"
if os.getenv("OTEL_TRACES_EXPORTER") is None:
    os.environ["OTEL_TRACES_EXPORTER"] = "none"

# Import Strands AFTER OTEL env is set so it picks up tracing config
from strands import Agent
from strands.models.openai import OpenAIModel

app = FastAPI()

# Register conversation router
from routers.conversations import router as conversations_router
app.include_router(conversations_router)

# Feature flags
ENABLE_COMPONENTS = False  # Disable interactive component analyzer to reduce latency
# Helper: predefined demo users are C001–C018
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

# Auto-discover and register all tools
print("\n" + "="*50)
print("INITIALIZING FINANCIAL AGENT TOOL SYSTEM")
print("="*50)
registry.auto_discover_tools()
registry.list_tools()
print("="*50 + "\n")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:4000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API
class ChatRequest(BaseModel):
    message: str
    session_id: str = None  # Customer ID for existing users, or new user session
    user_type: str = "existing"  # "existing" or "new"
    history: List[Dict[str, str]] = []  # Conversation history: [{"role": "user"|"assistant", "content": "..."}]
    conversation_id: Optional[str] = None  # If provided, use persistent conversation flow

class InteractiveComponent(BaseModel):
    """Model for interactive UI components in chat responses."""
    type: str  # 'buttons', 'slider', 'range_slider', 'toggle', 'dropdown'
    config: dict  # Component-specific configuration
    field_name: Optional[str] = None  # Assessment field to update

class ComponentAnalysisResult(BaseModel):
    """Model for component analysis results including guidance."""
    interactive_component: Optional[InteractiveComponent] = None
    guidance: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    sql_details: dict = None
    calculation_details: dict = None
    customer_id: str = None
    interactive_component: Optional[InteractiveComponent] = None
    guidance: Optional[str] = None
    customer_context: Optional[str] = None

class SuggestionRequest(BaseModel):
    user_context: str = None  # Optional context about user's financial situation

class Suggestion(BaseModel):
    title: str
    description: str
    question: str
    icon: str

class SuggestionsResponse(BaseModel):
    suggestions: List[Suggestion]

class CustomerAssessmentRequest(BaseModel):
    """Request model for new customer assessment."""
    first_name: str
    last_name: str
    session_id: str # Add session_id here
    phone: str = None
    annual_income: int = None
    primary_goal: str = None
    debt_status: str = None
    employment_status: str = None
    timeline: str = None
    risk_tolerance: str = None

class CustomerAssessmentResponse(BaseModel):
    """Response model for customer assessment."""
    customer_id: str
    message: str
    assessment_complete: bool
    next_questions: List[str] = []

# Initialize Financial Services
print("Initializing Financial Services...")

# Initialize Hooks
sql_capture_hook = SQLResultCaptureHook()
calculation_capture_hook = CalculationCaptureHook()
chart_capture_hook = ChartCaptureHook()
financial_conversation_hook = FinancialConversationHook()
conversation_capture_hook = ConversationCaptureHook(customer_service)

# Initialize Customer Profile Tool
customer_profile_tool = CustomerProfileTool()

# Initialize Component Analysis Agent - lightweight agent for detecting interactive components
component_analyzer_agent = Agent(
    system_prompt="""You are an expert at analyzing financial advisor conversations and determining when interactive UI components would be helpful.

Your job is to analyze an agent's response and determine if an interactive component should be shown to help the user respond more easily.

Available component types:
1. **buttons**: For choosing from 2-5 options
   - Example config: {"title": "Primary Financial Goal", "options": [{"label": "Student Loans", "value": "student_loans", "response_text": "I want to pay off my student loans"}, {"label": "Home Buying", "value": "home_buying", "response_text": "I want to buy a home"}]}

2. **slider**: For selecting a single number
   - Example config: {"title": "Annual Income", "min": 20000, "max": 200000, "default": 75000, "suffix": " per year", "step": 5000}

3. **range_slider**: For selecting a range
   - Example config: {"title": "Debt Amount", "min": 0, "max": 200000, "default_min": 20000, "default_max": 50000, "step": 5000, "format": "currency"}

4. **toggle**: For yes/no questions
   - Example config: {"title": "Are you employed?", "options": [{"label": "Yes", "value": true, "response_text": "Yes, I'm employed"}, {"label": "No", "value": false, "response_text": "No, I'm not currently employed"}]}

5. **dropdown**: For selecting from many options (5+)
   - Example config: {"title": "Employment Status", "options": [{"label": "Full-time", "value": "full_time"}, {"label": "Part-time", "value": "part_time"}, {"label": "Self-employed", "value": "self_employed"}]}

**CRITICAL: ONLY show interactive components for:**

1. **Financial Assessment Questions**:
   - Primary goal selection
   - Income range selection
   - Debt amount ranges
   - Employment status
   - Timeline selection
   - Risk tolerance

2. **Structured Data Gathering**:
   - Annual income
   - Debt amounts
   - Savings amounts
   - Timeline preferences
   - Risk preferences

**DO NOT show interactive components for:**
- Conversational questions about financial situation
- Follow-up questions about personal story
- Questions asking "why" or "what's important to you"
- Questions asking about their background or motivation
- Any conversational, rapport-building questions

**When NO interactive component is shown, provide subtle guidance with example responses:**

Examples of guidance prompts:
- For goal questions: "You can share things like 'I want to pay off my student loans' or 'I'm saving for a house' or 'I need to build an emergency fund'..."
- For debt questions: "Feel free to share details like 'I have about $30k in student loans' or 'I have credit card debt'..."
- For income questions: "You might say 'I make about $60k per year' or 'My salary is $75,000'..."

Respond with valid JSON in this format:
{
  "should_show": true,
  "component": {
    "type": "buttons",
    "config": {...},
    "field_name": "primary_goal"
  }
}

OR if no component should be shown, include guidance:
{
  "should_show": false,
  "component": null,
  "guidance": "You can share things like 'I want to pay off my student loans' or 'I'm saving for a house'..."
}

CRITICAL: Your response must be ONLY valid JSON, nothing else. No explanations, no markdown, just pure JSON."""
)

# Initialize OpenAI Model
print("Initializing OpenAI Model...")
try:
    openai_model = OpenAIModel(
        client_args={
            "api_key": os.getenv("OPENAI_API_KEY"),
        },
        model_id="gpt-4o",
        params={
            "max_tokens": 2500,
            "temperature": 0.2,
        }
    )
    print("✅ OpenAI Model initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize OpenAI Model: {str(e)}")
    raise

# Initialize Financial Agent with OpenAI model and financial tools
print("Initializing Financial Agent (Scenario A - Existing Users)...")
try:
    financial_agent = Agent(
        model=openai_model,
        system_prompt=load_system_prompt('scenario-a'),  # New conversational prompt
        tools=registry.get_strands_tools() + [customer_profile_tool.to_strands_tool()],
        hooks=[sql_capture_hook, calculation_capture_hook, chart_capture_hook, financial_conversation_hook, conversation_capture_hook]
    )
    print("✅ Financial Agent (Scenario A) initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize Financial Agent: {str(e)}")
    raise

print("🚀 Financial Advisory Agent is ready!")

# API Endpoints
@app.get("/")
async def root():
    return {"message": "Financial Advisory Agent API is running!"}

@app.get("/suggestions")
async def generate_suggestions(
    request: SuggestionRequest = None
) -> SuggestionsResponse:
    """Generate dynamic suggestions based on financial tools and user context."""
    try:
        # Financial-focused suggestions
        suggestions = [
            Suggestion(
                title="Student Loan Analysis",
                description="Analyze your student loan payments and refinancing options",
                question="Help me analyze my student loan payments and see if I should refinance",
                icon="🎓"
            ),
            Suggestion(
                title="Home Buying Calculator",
                description="Calculate mortgage affordability and down payment needs",
                question="Can I afford to buy a home? What would my monthly payments be?",
                icon="🏠"
            ),
            Suggestion(
                title="Debt Payoff Strategy",
                description="Create a plan to pay off your debts efficiently",
                question="Help me create a strategy to pay off my debts faster",
                icon="💳"
            ),
            Suggestion(
                title="Emergency Fund Planning",
                description="Calculate how much you need in emergency savings",
                question="How much should I have in my emergency fund?",
                icon="💰"
            ),
            Suggestion(
                title="Budget Analysis",
                description="Analyze your spending and create a budget plan",
                question="Help me analyze my spending and create a better budget",
                icon="📊"
            ),
            Suggestion(
                title="Investment Planning",
                description="Plan your investment strategy and retirement savings",
                question="How should I invest my money for the future?",
                icon="📈"
            )
        ]
        
        return SuggestionsResponse(suggestions=suggestions)
        
    except Exception as e:
        # Return fallback suggestions on any error
        fallback_suggestions = [
            Suggestion(
                title="Student Loans",
                description="Get help with student loan management",
                question="Help me with my student loans",
                icon="🎓"
            ),
            Suggestion(
                title="Home Buying",
                description="Calculate home buying affordability",
                question="Can I afford to buy a home?",
                icon="🏠"
            ),
            Suggestion(
                title="Financial Planning",
                description="Get personalized financial advice",
                question="Help me with my financial planning",
                icon="💰"
            ),
            Suggestion(
                title="Debt Management",
                description="Create a debt payoff strategy",
                question="Help me manage my debt",
                icon="💳"
            )
        ]
        return SuggestionsResponse(suggestions=fallback_suggestions)

async def analyze_response_for_interactive_components(response_text: str, customer_context: dict = None) -> ComponentAnalysisResult:
    """
    Use LLM to analyze agent response and determine if it should have interactive UI components.
    
    Args:
        response_text: The agent's response text
        customer_context: Optional customer context for smart defaults
        
    Returns:
        ComponentAnalysisResult with interactive component and/or guidance
    """
    print(f"🔍 DEBUG: Analyzing response with LLM: '{response_text[:100]}...'")
    
    try:
        # Prepare customer context info for better analysis
        customer_info = ""
        if customer_context:
            customer_info = "\n\nCurrent Customer Information (what we already know):"
            if isinstance(customer_context, dict):
                for key, value in customer_context.items():
                    if value and value != "Not specified":
                        customer_info += f"\n- {key}: {value}"
        
        # Prepare the analysis prompt
        analysis_prompt = f"""Analyze this financial advisor response and determine if an interactive UI component should be shown:

{response_text}

{customer_info}

Determine if this response should have an interactive component for data collection."""

        # Use the component analyzer agent
        agent_result = component_analyzer_agent(analysis_prompt)
        
        # Extract the response text from the agent result
        if hasattr(agent_result, 'content'):
            analysis_result = agent_result.content
        elif hasattr(agent_result, 'text'):
            analysis_result = agent_result.text
        elif isinstance(agent_result, str):
            analysis_result = agent_result
        else:
            analysis_result = str(agent_result)
        
        print(f"🔍 DEBUG: Component analysis result: {analysis_result}")
        
        # Parse the JSON response
        try:
            analysis_data = json.loads(analysis_result)
        except json.JSONDecodeError as e:
            print(f"⚠️ WARNING: Failed to parse component analysis JSON: {e}")
            print(f"Raw response: {analysis_result}")
            return ComponentAnalysisResult()

        if analysis_data.get("should_show", False):
            component = analysis_data.get("component")
            if component:
                return ComponentAnalysisResult(
                    interactive_component=InteractiveComponent(
                        type=component["type"],
                        config=component["config"],
                        field_name=component.get("field_name")
                    )
                )

        # Return guidance if no component should be shown
        guidance = analysis_data.get("guidance")
        if guidance:
            return ComponentAnalysisResult(guidance=guidance)

        return ComponentAnalysisResult()

    except Exception as e:
        print(f"⚠️ WARNING: Component analysis failed: {e}")
        return ComponentAnalysisResult()

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint for financial advisory agent."""
    try:
        print(f"💬 Chat request: {request.message[:100]}...")
        print(f"👤 User type: {request.user_type}, Session ID: {request.session_id}")
        
        # Clear all tool results from previous requests to prevent cross-contamination
        clear_sql_details()
        clear_calculation_details()
        clear_rent_buy_details()
        clear_chart_data()
        print("🧹 Cleared all tool results from previous chat sessions")
        
        # Persistent conversation flow if conversation_id provided
        if request.conversation_id:
            import sqlite3
            from pathlib import Path

            # Save user message first
            conversation_service.add_message(
                conversation_id=request.conversation_id,
                role="user",
                content=request.message,
            )

            # Load conversation metadata
            db_path = Path(__file__).resolve().parent / "data" / "financial_data.db"
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute(
                    "SELECT customer_id, session_id, scenario_type FROM conversations WHERE conversation_id = ? AND is_active = 1",
                    (request.conversation_id,),
                )
                conv_row = cur.fetchone()
                if not conv_row:
                    raise HTTPException(status_code=404, detail="Conversation not found")
                conv_data = dict(conv_row)

            customer_id = conv_data.get("customer_id")
            scenario_type = conv_data.get("scenario_type", "new")

            # Build prompt from last 10 persisted messages
            messages = conversation_service.get_messages(request.conversation_id, limit=100)
            last_10 = messages[-10:] if len(messages) > 10 else messages

            message_parts = []
            scenario_line = (
                "Scenario: Existing user with full profile." if scenario_type == "existing" else "Scenario: New user with no stored profile — collect missing data before tool calls."
            )
            message_parts.append(scenario_line)

            # Customer context if existing
            customer_context = None
            if scenario_type == "existing" and customer_id:
                try:
                    customer_context = customer_service.get_customer_context(customer_id)
                    print(f"📊 Customer context retrieved for {customer_id}")
                except Exception as e:
                    print(f"⚠️ Warning: Could not retrieve customer context: {e}")
            if customer_context:
                message_parts.append(f"Customer Context:\n{customer_context}")

            if scenario_type == "existing" and customer_id:
                message_parts.append(f"Explicit Customer ID Token: {customer_id}")

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

            # Determine DB tool gating
            use_db = (scenario_type == "existing") and is_predefined_customer_id(customer_id)

        else:
            # Legacy flow without conversation_id
            # Get customer context if existing user
            customer_context = None
            if request.user_type == "existing" and request.session_id:
                try:
                    customer_context = customer_service.get_customer_context(request.session_id)
                    print(f"📊 Customer context retrieved for {request.session_id}")
                except Exception as e:
                    print(f"⚠️ Warning: Could not retrieve customer context: {e}")

            # Prepare the message with explicit customer_id token so tools see CXXX
            message_parts = []

            # Add scenario context
            scenario_line = "Scenario: Existing user with full profile." if request.user_type == "existing" else "Scenario: New user with no stored profile — collect missing data before tool calls."
            message_parts.append(scenario_line)

            # Add customer context
            if customer_context:
                message_parts.append(f"Customer Context:\n{customer_context}")

            # Add customer ID token
            if request.user_type == "existing" and request.session_id:
                message_parts.append(f"Explicit Customer ID Token: {request.session_id}")

            # Add conversation history if present
            if request.history:
                print(f"📜 Including {len(request.history)} previous messages in conversation history")
                history_text = "Conversation History:"
                for msg in request.history[-10:]:  # Keep last 10 messages to avoid token limit
                    role = "User" if msg.get("role") == "user" else "Assistant"
                    content = msg.get("content", "")
                    history_text += f"\n\n{role}: {content}"
                message_parts.append(history_text)

            # Add current user message
            message_parts.append(f"User Message: {request.message}")

            message_with_context = "\n\n".join(filter(None, message_parts))

            # Enable DB tools only for predefined demo users C001–C018
            use_db = (request.user_type == "existing") and is_predefined_customer_id(request.session_id)

        # Get response from financial agent
        print("🤖 Getting response from financial agent...")
        if not use_db:
            try:
                from tools.tool_manager import registry as tool_registry
                # Get all tools except DB tools
                all_tools_dict = tool_registry.get_all_tools()
                excluded_names = {"nl2sql_query", "sqlite_query"}
                allowed_tools = []
                for tool_name, tool_instance in all_tools_dict.items():
                    if tool_name not in excluded_names:
                        allowed_tools.append(tool_instance.to_strands_tool())
                
                print(f"🔧 Scenario B: Allowed {len(allowed_tools)} tools (excluded: {excluded_names})")
                
                session_agent = Agent(
                    model=openai_model,
                    tools=allowed_tools,
                    system_prompt=get_scenario_b_system_prompt()
                )
                agent_result = session_agent(message_with_context)
            except Exception as e:
                print(f"⚠️ Warning: Failed to create session-scoped agent without DB tools: {e}")
                agent_result = financial_agent(message_with_context)
        else:
            agent_result = financial_agent(message_with_context)
 
        # Extract the response text from the agent result
        if hasattr(agent_result, 'content'):
            response = agent_result.content
        elif hasattr(agent_result, 'text'):
            response = agent_result.text
        elif isinstance(agent_result, str):
            response = agent_result
        else:
            response = str(agent_result)
        
        # Analyze response for interactive components (optional)
        if ENABLE_COMPONENTS:
            print("🔍 Analyzing response for interactive components...")
            component_analysis = await analyze_response_for_interactive_components(
                response, 
                customer_context
            )
        else:
            component_analysis = ComponentAnalysisResult()
        
        # Prepare response
        chat_response = ChatResponse(
            response=response,
            customer_id=request.session_id,
            customer_context=customer_context
        )
        
        # Add interactive component if found
        if component_analysis.interactive_component:
            chat_response.interactive_component = component_analysis.interactive_component
            print(f"🎛️ Added interactive component: {component_analysis.interactive_component.type}")
        
        # Add guidance if provided
        if component_analysis.guidance:
            chat_response.guidance = component_analysis.guidance
            print(f"💡 Added guidance: {component_analysis.guidance[:50]}...")
        
        # Add SQL details if available
        sql_details = get_last_sql_details()
        if sql_details:
            chat_response.sql_details = sql_details
            print("📊 Added SQL details to response")
        
        # Add calculation details if available (check both debt_optimizer and rent_vs_buy)
        calculation_details = get_last_calculation_details()
        if not calculation_details:
            calculation_details = get_last_rent_buy_details()
        
        if calculation_details:
            chat_response.calculation_details = calculation_details
            print(f"🧮 Added calculation details to response: {calculation_details.get('scenario_type', 'N/A')} from {calculation_details.get('tool_name', 'unknown')}")
        
        # Persist assistant response and tool payloads if conversation_id present
        if request.conversation_id:
            # Save assistant message
            conversation_service.add_message(
                conversation_id=request.conversation_id,
                role="assistant",
                content=response,
                sql_details=chat_response.sql_details,
                calculation_details=chat_response.calculation_details,
            )
            # Save tool messages separately when available
            if chat_response.sql_details:
                conversation_service.add_message(
                    conversation_id=request.conversation_id,
                    role="tool",
                    content=None,
                    tool_name="nl2sql_query",
                    tool_payload=chat_response.sql_details,
                )
            if chat_response.calculation_details:
                conversation_service.add_message(
                    conversation_id=request.conversation_id,
                    role="tool",
                    content=None,
                    tool_name=chat_response.calculation_details.get("tool_name", "calculation"),
                    tool_payload=chat_response.calculation_details,
                )

            # Auto-title generation every 6 assistant messages
            try:
                import sqlite3
                from pathlib import Path
                db_path = Path(__file__).resolve().parent / "data" / "financial_data.db"
                with sqlite3.connect(db_path) as conn:
                    cur = conn.cursor()
                    cur.execute(
                        "SELECT COUNT(*) FROM chat_messages WHERE conversation_id = ? AND role = 'assistant' AND is_active = 1",
                        (request.conversation_id,),
                    )
                    count = cur.fetchone()[0]
                if count and count % 6 == 0:
                    from services.conversation_service import conversation_service as _cs
                    _cs.generate_conversation_title(request.conversation_id)
            except Exception:
                pass
        
        print("✅ Chat response prepared successfully")
        return chat_response
        
    except Exception as e:
        print(f"❌ Chat error: {str(e)}")
        import traceback
        traceback.print_exc()  # Print full stack trace for debugging
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    async def event_generator():
        full_response = ""  # Collect full response for persistence
        try:
            # If conversation_id is provided, save user message first
            if request.conversation_id:
                from services.conversation_service import conversation_service
                conversation_service.add_message(
                    conversation_id=request.conversation_id,
                    role="user",
                    content=request.message,
                )
            
            # Clear all tool results from previous requests to prevent cross-contamination
            clear_sql_details()
            clear_calculation_details()
            clear_rent_buy_details()
            clear_chart_data()
            
            # Prepare customer context (existing users only)
            customer_context = None
            if request.user_type == "existing" and request.session_id:
                try:
                    customer_context = customer_service.get_customer_context(request.session_id)
                except Exception:
                    customer_context = None

            # Prepare the message with explicit customer_id token so tools see CXXX
            message_parts = []
            
            # Add customer context
            if customer_context:
                message_parts.append(f"Customer Context:\n{customer_context}")
            
            # Add customer ID token
            if request.user_type == "existing" and request.session_id:
                message_parts.append(f"Explicit Customer ID Token: {request.session_id}")
            
            # Add conversation history if present
            if request.history:
                history_text = "Conversation History:"
                for msg in request.history[-10:]:  # Keep last 10 messages to avoid token limit
                    role = "User" if msg.get("role") == "user" else "Assistant"
                    content = msg.get("content", "")
                    history_text += f"\n\n{role}: {content}"
                message_parts.append(history_text)
            
            # Add current user message
            message_parts.append(f"User Message: {request.message}")
            
            message_with_context = "\n\n".join(filter(None, message_parts)) or request.message

            # Respect routing guard for DB tools
            use_db = (request.user_type == "existing") and is_predefined_customer_id(request.session_id)
            if not use_db:
                from tools.tool_manager import registry as tool_registry
                # Get all registered tools (dict of name -> BaseTool)
                all_tools_dict = tool_registry.get_all_tools()
                # Filter: exclude DB tools by name, keep calculation tools (debt_optimizer, rent_vs_buy, financial_summary, etc.)
                excluded_names = {"nl2sql_query", "sqlite_query"}
                allowed_tools = []
                allowed_tool_names = []
                for tool_name, tool_instance in all_tools_dict.items():
                    if tool_name not in excluded_names:
                        # Convert each allowed tool to Strands format
                        strands_tool = tool_instance.to_strands_tool()
                        allowed_tools.append(strands_tool)
                        allowed_tool_names.append(tool_name)
                print(f"🔧 Scenario B: Allowed {len(allowed_tools)} tools (excluded DB tools: {excluded_names})")
                print(f"   Available tools: {allowed_tool_names}")
                
                session_agent = Agent(
                    model=openai_model, 
                    tools=allowed_tools,
                    system_prompt=get_scenario_b_system_prompt()
                )
                agent = session_agent
                prompt = message_with_context
            else:
                agent = financial_agent
                prompt = message_with_context

            # Native streaming via Strands
            print(f"🔵 Starting agent stream for conversation_id={request.conversation_id}, user_type={request.user_type}")
            event_count = 0
            async for event in agent.stream_async(prompt):
                event_count += 1
                # Strands may emit different shapes; handle common ones
                if event is None:
                    continue
                # Direct string chunk
                if isinstance(event, str):
                    chunk = event
                    if chunk:
                        full_response += chunk
                        yield f"data: {json.dumps({'content': chunk})}\n\n"
                        await asyncio.sleep(0)
                    continue
                # Object with content/text attributes
                try:
                    if hasattr(event, "content"):
                        chunk = getattr(event, "content") or ""
                        if chunk:
                            full_response += chunk
                            yield f"data: {json.dumps({'content': chunk})}\n\n"
                            await asyncio.sleep(0)
                            continue
                    if hasattr(event, "text"):
                        chunk = getattr(event, "text") or ""
                        if chunk:
                            full_response += chunk
                            yield f"data: {json.dumps({'content': chunk})}\n\n"
                            await asyncio.sleep(0)
                            continue
                except Exception:
                    pass
                # Simple data key (per docs)
                if isinstance(event, dict) and 'data' in event:
                    chunk = str(event['data'])
                    if chunk:
                        full_response += chunk
                        yield f"data: {json.dumps({'content': chunk})}\n\n"
                        await asyncio.sleep(0)
                    continue
                # Anthropic-like
                cbd = event.get('contentBlockDelta') if isinstance(event, dict) else None
                if cbd and isinstance(cbd, dict):
                    delta = cbd.get('delta', {})
                    text = delta.get('text') or ''
                    if text:
                        full_response += text
                        yield f"data: {json.dumps({'content': text})}\n\n"
                        await asyncio.sleep(0)
                    continue
                # OpenAI-like chunk
                if isinstance(event, dict) and 'delta' in event:
                    text = event['delta'].get('text') if isinstance(event['delta'], dict) else None
                    if text:
                        full_response += text
                        yield f"data: {json.dumps({'content': text})}\n\n"
                        await asyncio.sleep(0)
                    continue
                # Final/stop signals: do NOT break; let stream_async finish its own span cleanly
                if isinstance(event, dict) and (event.get('messageStop') or event.get('result')):
                    continue

            # After streaming completes, send SQL details if available
            sql_details = get_last_sql_details()
            if sql_details:
                yield f"data: {json.dumps({'sql_details': sql_details})}\n\n"
                await asyncio.sleep(0)
            
            # Send calculation details if available (check both debt_optimizer and rent_vs_buy)
            calculation_details = get_last_calculation_details()
            if not calculation_details:
                calculation_details = get_last_rent_buy_details()
            
            if calculation_details:
                yield f"data: {json.dumps({'calculation_details': calculation_details})}\n\n"
                await asyncio.sleep(0)
            
            # Send chart data if available
            chart_data = get_last_chart_data()
            print(f"\n📊 [DEBUG] Checking for chart data after stream...")
            print(f"   - Chart data available: {chart_data is not None}")
            if chart_data:
                print(f"   - Chart type: {chart_data.get('chart_type')}")
                print(f"   - Sending chart data to frontend...")
                yield f"data: {json.dumps({'chart_data': chart_data})}\n\n"
                await asyncio.sleep(0)
            else:
                print(f"   - No chart data to send")

            # If nothing streamed, try a one-shot call as a fallback
            if not full_response:
                try:
                    result = agent(prompt)
                    text = getattr(result, 'content', getattr(result, 'text', str(result))) or ''
                    if text:
                        full_response = text
                        yield f"data: {json.dumps({'content': text})}\n\n"
                        await asyncio.sleep(0)
                except Exception as e:
                    print(f"❌ Fallback agent call failed: {e}")

            # Log stream completion
            print(f"✅ Stream completed: {event_count} events, response length: {len(full_response)} chars")
            
            # Save assistant message if conversation_id provided
            if request.conversation_id and full_response:
                from services.conversation_service import conversation_service
                # Light normalization to improve markdown readability
                normalized_text = (full_response or "").replace("\r\n", "\n").strip()
                if not normalized_text.endswith("\n"):
                    normalized_text += "\n"
                conversation_service.add_message(
                    conversation_id=request.conversation_id,
                    role="assistant",
                    content=normalized_text,
                    sql_details=sql_details if sql_details else None,
                    calculation_details=calculation_details if calculation_details else None,
                    chart_data=chart_data if chart_data else None,
                )
                print(f"💾 Saved assistant message to conversation {request.conversation_id}")
            elif request.conversation_id and not full_response:
                print(f"⚠️ WARNING: No response content for conversation {request.conversation_id}")

            yield "data: [DONE]\n\n"
        except (asyncio.CancelledError, GeneratorExit):
            # Client disconnected or stream closed; exit quietly without logging noisy tracebacks
            return
        except Exception as e:
            # Log the full error for debugging
            import traceback
            error_trace = traceback.format_exc()
            print(f"❌ Stream error in chat_stream: {e}")
            print(f"📋 Traceback:\n{error_trace}")
            # Stream a final error event
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/assess", response_model=CustomerAssessmentResponse)
async def create_customer_assessment(request: CustomerAssessmentRequest):
    """Create a new customer assessment for new users."""
    try:
        print(f"📝 Creating customer assessment for {request.first_name} {request.last_name}")
        
        # Create customer
        customer_data = {
            'first_name': request.first_name,
            'last_name': request.last_name,
            'annual_income': request.annual_income
        }
        
        customer = customer_service.create_customer(customer_data)
        
        if not customer:
            raise HTTPException(status_code=500, detail="Failed to create customer")
        
        # Link the session_id to the newly created customer_id in the conversations table
        # Find the most recent conversation for this session_id and update its customer_id
        try:
            import sqlite3
            from pathlib import Path
            db_path = Path(__file__).resolve().parent / "data" / "financial_data.db"
            with sqlite3.connect(db_path) as conn:
                cur = conn.cursor()
                cur.execute(
                    "UPDATE conversations SET customer_id = ? WHERE session_id = ? AND customer_id IS NULL ORDER BY created_at DESC LIMIT 1",
                    (customer.customer_id, request.session_id)
                )
                conn.commit()
                print(f"Linked session_id {request.session_id} to customer_id {customer.customer_id}")
        except Exception as update_error:
            print(f"WARNING: Failed to link session_id to customer_id in conversations: {update_error}")

        # Create assessment
        assessment_data = {
            'phone': request.phone,
            'primary_goal': request.primary_goal,
            'debt_status': request.debt_status,
            'employment_status': request.employment_status,
            'timeline': request.timeline,
            'risk_tolerance': request.risk_tolerance
        }
        
        assessment = customer_service.create_assessment(customer.customer_id, assessment_data)
        
        # Assign persona
        persona = customer_service.assign_persona(customer.customer_id)
        customer_service.update_customer(customer.customer_id, {'persona_type': persona})
        
        # Determine next questions
        next_questions = []
        if not request.primary_goal:
            next_questions.append("What is your primary financial goal?")
        if not request.debt_status:
            next_questions.append("How would you describe your current debt situation?")
        if not request.employment_status:
            next_questions.append("What is your current employment status?")
        
        assessment_complete = len(next_questions) == 0
        
        return CustomerAssessmentResponse(
            customer_id=customer.customer_id,
            message=f"Welcome {request.first_name}! I've created your financial profile. Let's continue with your assessment.",
            assessment_complete=assessment_complete,
            next_questions=next_questions
        )
        
    except Exception as e:
        print(f"❌ Assessment creation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Assessment creation failed: {str(e)}")

@app.get("/customer/{customer_id}/context")
async def get_customer_context_new(customer_id: str):
    """Get customer context for frontend validation and chat initialization."""
    try:
        # Use the existing customer service to get customer data
        customer = customer_service.get_customer(customer_id)
        
        if not customer:
            return {"found": False, "customer_id": customer_id}
        
        # Get customer context using the same method as the chat endpoint
        try:
            customer_context = customer_service.get_customer_context(customer_id)
            
            return {
                "found": True,
                "customer_id": customer_id,
                "first_name": customer.first_name,
                "last_name": customer.last_name,
                "context": customer_context
            }
        except Exception as context_error:
            print(f"⚠️ Warning: Could not retrieve customer context: {context_error}")
            # Still return found=True if customer exists, even if context fails
            # Create a basic context from available customer data
            basic_context = f"Customer {customer.first_name} {customer.last_name} (ID: {customer_id})"
            if customer.base_salary_annual:
                basic_context += f", Annual Income: ${customer.base_salary_annual:,.2f}"
            if customer.fico_baseline:
                basic_context += f", FICO Score: {customer.fico_baseline}"
            
            return {
                "found": True,
                "customer_id": customer_id,
                "first_name": customer.first_name,
                "last_name": customer.last_name,
                "context": basic_context
            }
            
    except Exception as e:
        print(f"❌ Error in get_customer_context: {str(e)}")
        return {"found": False, "customer_id": customer_id, "error": str(e)}

@app.get("/customer/{customer_id}/profile")
async def get_customer_profile(customer_id: str):
    """Get detailed customer profile."""
    try:
        customer = customer_service.get_customer(customer_id)
        assessment = customer_service.get_customer_assessment(customer_id)
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        profile = {
            "customer_id": customer.customer_id,
            "first_name": customer.first_name,
            "last_name": customer.last_name,
            "base_salary_annual": customer.base_salary_annual,
            "persona_type": customer.persona_type,
            "assessment": assessment.__dict__ if assessment else None
        }
        
        return profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get customer profile: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Financial Advisory Agent",
        "tools_loaded": len(registry.get_all_tools()),
        "model": "gpt-4o"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)