from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from tools.tool_manager import registry
import json
import asyncio
from typing import List, Optional
import re

# Financial agent imports
from services.customer_service import customer_service
from hooks.financial_conversation_hook import FinancialConversationHook
from hooks.sql_capture_hook import SQLResultCaptureHook
from hooks.conversation_capture_hook import ConversationCaptureHook

# Tool imports
from tools.customer_profile_tool import CustomerProfileTool

# Prompt loader import
from utils.prompt_loader import load_system_prompt

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
    email: str
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
        model_id="gpt-4o-mini",
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
print("Initializing Financial Agent...")
try:
    financial_agent = Agent(
        model=openai_model,
        system_prompt=load_system_prompt('fin-adv-v2'),
        tools=registry.get_strands_tools() + [customer_profile_tool.to_strands_tool()],
        hooks=[sql_capture_hook, financial_conversation_hook, conversation_capture_hook]
    )
    print("✅ Financial Agent initialized successfully")
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
        
        # Get customer context if existing user
        customer_context = None
        if request.user_type == "existing" and request.session_id:
            try:
                customer_context = customer_service.get_customer_context(request.session_id)
                print(f"📊 Customer context retrieved for {request.session_id}")
            except Exception as e:
                print(f"⚠️ Warning: Could not retrieve customer context: {e}")
        
        # Prepare the message with explicit customer_id token so tools see CXXX
        message_with_context = request.message
        if request.user_type == "existing" and request.session_id:
            token_line = f"Explicit Customer ID Token: {request.session_id}"
        else:
            token_line = None
        if customer_context:
            ctx = f"Customer Context:\n{customer_context}"
            message_with_context = "\n\n".join(filter(None, [ctx, token_line, f"User Message: {request.message}"]))
        else:
            message_with_context = "\n\n".join(filter(None, [token_line, f"User Message: {request.message}"])) or request.message
        
        # Get response from financial agent
        print("🤖 Getting response from financial agent...")
        # Enable DB tools only for predefined demo users C001–C018
        use_db = (request.user_type == "existing") and is_predefined_customer_id(request.session_id)
        if not use_db:
            try:
                from tools.tool_manager import registry as tool_registry
                allowed_tools = [t for t in tool_registry.get_all_tools() if t.name not in {"nl2sql_query", "sqlite_query"}]
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
        if hasattr(sql_capture_hook, 'last_result') and sql_capture_hook.last_result:
            chat_response.sql_details = sql_capture_hook.last_result
            print("📊 Added SQL details to response")
        
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
        try:
            # Prepare customer context (existing users only)
            customer_context = None
            if request.user_type == "existing" and request.session_id:
                try:
                    customer_context = customer_service.get_customer_context(request.session_id)
                except Exception:
                    customer_context = None

            # Prepare the message with explicit customer_id token so tools see CXXX
            message_with_context = request.message
            if request.user_type == "existing" and request.session_id:
                token_line = f"Explicit Customer ID Token: {request.session_id}"
            else:
                token_line = None
            if customer_context:
                ctx = f"Customer Context:\n{customer_context}"
                message_with_context = "\n\n".join(filter(None, [ctx, token_line, f"User Message: {request.message}"]))
            else:
                message_with_context = "\n\n".join(filter(None, [token_line, f"User Message: {request.message}"])) or request.message

            # Respect routing guard for DB tools
            use_db = (request.user_type == "existing") and is_predefined_customer_id(request.session_id)
            if not use_db:
                from tools.tool_manager import registry as tool_registry
                allowed_tools = [t for t in tool_registry.get_all_tools() if t.name not in {"nl2sql_query", "sqlite_query"}]
                session_agent = Agent(model=openai_model, tools=allowed_tools)
                system_guardrail = (
                    "System: You are in assessment mode or using a non-preloaded user. "
                    "Do not query the database. Do not use NL2SQL or SQLite. "
                    "Collect information, run calculators, and update assessments only."
                )
                agent = session_agent
                prompt = f"{message_with_context}\n\n{system_guardrail}"
            else:
                agent = financial_agent
                prompt = message_with_context

            # Native streaming via Strands
            async for event in agent.stream_async(prompt):
                # Strands may emit different shapes; handle common ones
                if event is None:
                    continue
                # Simple data key (per docs)
                if isinstance(event, dict) and 'data' in event:
                    chunk = str(event['data'])
                    if chunk:
                        yield f"data: {json.dumps({'content': chunk})}\n\n"
                        await asyncio.sleep(0)
                    continue
                # Anthropic-like
                cbd = event.get('contentBlockDelta') if isinstance(event, dict) else None
                if cbd and isinstance(cbd, dict):
                    delta = cbd.get('delta', {})
                    text = delta.get('text') or ''
                    if text:
                        yield f"data: {json.dumps({'content': text})}\n\n"
                        await asyncio.sleep(0)
                    continue
                # OpenAI-like chunk
                if isinstance(event, dict) and 'delta' in event:
                    text = event['delta'].get('text') if isinstance(event['delta'], dict) else None
                    if text:
                        yield f"data: {json.dumps({'content': text})}\n\n"
                        await asyncio.sleep(0)
                    continue
                # Final/stop signals: do NOT break; let stream_async finish its own span cleanly
                if isinstance(event, dict) and (event.get('messageStop') or event.get('result')):
                    continue

            yield "data: [DONE]\n\n"
        except (asyncio.CancelledError, GeneratorExit):
            # Client disconnected or stream closed; exit quietly without logging noisy tracebacks
            return
        except Exception as e:
            # Stream a final error event but avoid raising which would log large traces
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
        
        # Create assessment
        assessment_data = {
            'email': request.email,
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
async def get_customer_context(customer_id: str):
    """Get customer context for existing users."""
    try:
        context = customer_service.get_customer_context(customer_id)
        return {"customer_id": customer_id, "context": context}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Customer not found: {str(e)}")

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