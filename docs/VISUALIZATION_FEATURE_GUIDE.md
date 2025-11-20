# Financial Visualization Feature - Complete Guide

## Overview
The financial visualization feature allows Growbe to generate interactive, insightful charts and graphs that help Scenario A users better understand their financial data. Charts are displayed inline within chat messages, making financial insights more accessible and actionable.

---

## Implementation Summary

### Backend Components

1. **`backend/tools/visualization_tool.py`**
   - Smart chart generation tool with 9 chart types
   - Automatic data retrieval from financial database
   - Recharts-compatible configuration generation
   - Color palettes optimized for financial data

2. **`backend/hooks/chart_capture_hook.py`**
   - Captures chart data after visualization tool execution
   - Stores chart configuration for message persistence

3. **`backend/migrations/004_add_chart_data_to_messages.sql`**
   - Adds `chart_data` column to `chat_messages` table
   - Enables conversation history with charts

4. **`backend/services/conversation_service.py`**
   - Updated `add_message()` to accept `chart_data` parameter
   - Serializes chart configuration to JSON

5. **`backend/main.py`**
   - Integrated chart capture hook into agent pipeline
   - Streams chart data to frontend
   - Saves chart data with messages

6. **`backend/prompts/fin-adv-v2.txt`**
   - Added comprehensive visualization tool documentation
   - Best practices for when and how to generate charts
   - Example usage patterns for agent

### Frontend Components

1. **`frontend/src/components/ChartDisplay.tsx`**
   - Recharts-based chart renderer
   - Supports pie, bar, and line charts
   - Custom tooltips with currency formatting
   - Responsive design

2. **`frontend/src/components/ChatWindow.tsx`**
   - Integrated ChartDisplay component
   - Parses chart_data from messages
   - Displays charts inline in assistant messages
   - Handles streaming chart data

3. **`frontend/package.json`**
   - Added Recharts library dependency

---

## Supported Chart Types

### 1. **Debt Breakdown** (Pie Chart)
Shows distribution of debt balances by type (student, auto, credit card, personal, mortgage).

**Use Cases:**
- "Show me a breakdown of my debts"
- "What types of debt do I have?"
- "Visualize my debt portfolio"

**Agent Call:**
```python
create_visualization(
    chart_type="debt_breakdown",
    customer_id="C001"
)
```

---

### 2. **Debt Comparison** (Bar Chart)
Compares debt metrics including balance, interest rate, and monthly payments across all debts.

**Use Cases:**
- "Compare my debts"
- "Which debt has the highest interest rate?"
- "Show me my monthly payments for each debt"

**Agent Call:**
```python
create_visualization(
    chart_type="debt_comparison",
    customer_id="C001"
)
```

---

### 3. **Payoff Timeline** (Line Chart)
Shows projected debt payoff schedule over time.

**Use Cases:**
- "Show me when I'll pay off each debt"
- "Visualize my payoff timeline"
- "When will I be debt-free?"

**Agent Call:**
```python
# First, get payoff data
debt_data = debt_optimizer(
    customer_id="C001",
    scenario_type="current"
)

# Then visualize
create_visualization(
    chart_type="payoff_timeline",
    data=debt_data
)
```

---

### 4. **Spending by Category** (Pie Chart)
Breaks down expenses by category (Housing, Food, Transport, etc.).

**Use Cases:**
- "Show me where my money goes"
- "Breakdown my spending by category"
- "Visualize my expenses for the last 3 months"

**Agent Call:**
```python
create_visualization(
    chart_type="spending_by_category",
    customer_id="C001",
    timeframe="3m"  # Options: "3m", "6m", "12m"
)
```

---

### 5. **Income vs Expense** (Bar Chart)
Monthly comparison of income and expenses with surplus/deficit visualization.

**Use Cases:**
- "Compare my income and expenses"
- "Show me if I'm spending more than I earn"
- "Visualize my monthly cash flow"

**Agent Call:**
```python
create_visualization(
    chart_type="income_vs_expense",
    customer_id="C001",
    timeframe="6m"
)
```

---

### 6. **Net Worth Composition** (Pie Chart)
Shows total assets vs total liabilities.

**Use Cases:**
- "What's my net worth?"
- "Show me my assets and liabilities"
- "Visualize my financial position"

**Agent Call:**
```python
create_visualization(
    chart_type="net_worth_composition",
    customer_id="C001"
)
```

---

### 7. **Credit Score Trend** (Line Chart)
Displays credit score changes over time.

**Use Cases:**
- "How has my credit score changed?"
- "Show me my credit score history"
- "Visualize my credit trend"

**Agent Call:**
```python
create_visualization(
    chart_type="credit_score_trend",
    customer_id="C001",
    timeframe="12m"
)
```

---

### 8. **Payment Comparison** (Bar Chart)
Compares different payment scenarios (current vs proposed).

**Use Cases:**
- "Compare my current payment to the new payment"
- "Show me the difference visually"
- "Visualize the payment change"

**Agent Call:**
```python
# After getting refinance/calculation data
create_visualization(
    chart_type="payment_comparison",
    data=calculator_results
)
```

---

### 9. **Strategy Comparison** (Bar Chart)
Side-by-side comparison of debt payoff strategies (avalanche vs snowball).

**Use Cases:**
- "Compare avalanche vs snowball strategies"
- "Show me the difference between payoff methods"
- "Visualize which strategy saves more"

**Agent Call:**
```python
# First, get strategy data
strategy_data = debt_optimizer(
    customer_id="C001",
    scenario_type="avalanche",
    extra_payment=200
)

# Then visualize
create_visualization(
    chart_type="strategy_comparison",
    data=strategy_data
)
```

---

## Example User Queries That Trigger Visualizations

### Explicit Requests
1. "Can you show me a chart of my debts?"
2. "Visualize my spending"
3. "Create a graph of my debt payoff"
4. "Show me a pie chart of my expenses"
5. "Graph my credit score over time"

### Implicit Opportunities (Agent Decision)
1. "Tell me about my debts" → Suggest: "Here's a breakdown [+ debt_breakdown chart]"
2. "How much am I spending?" → Include: spending_by_category chart
3. "Compare my debts" → Automatically include: debt_comparison chart
4. "What's my net worth?" → Include: net_worth_composition chart
5. "How has my credit changed?" → Include: credit_score_trend chart

### Comparison Scenarios
1. "Should I use avalanche or snowball?" → strategy_comparison chart
2. "Compare my income and expenses" → income_vs_expense chart
3. "Show me current vs refinanced payments" → payment_comparison chart

---

## Agent Decision Framework

The agent should generate visualizations when:

1. **User explicitly asks** for a chart, graph, or visualization
2. **Data would be clearer visually** (e.g., multiple debts, category breakdown)
3. **Comparing scenarios** (avalanche vs snowball, before vs after refinance)
4. **Showing trends** (credit score over time, income/expense patterns)
5. **After data retrieval** that benefits from visual representation

The agent should NOT generate visualizations when:
- User only wants a single number (e.g., "What's my student loan balance?")
- Data is too simple for visualization (e.g., one debt, one category)
- User explicitly wants text-only response
- Insufficient data available

---

## Technical Architecture

### Data Flow

```
User Query
    ↓
Agent Reasoning
    ↓
Tool Selection (create_visualization)
    ↓
visualization_tool.py
    ├─ Fetch data from database
    ├─ Determine chart type
    ├─ Format data for Recharts
    └─ Generate chart configuration
    ↓
chart_capture_hook.py
    └─ Capture chart data
    ↓
main.py (streaming)
    └─ Send chart_data to frontend
    ↓
conversation_service.py
    └─ Save chart_data to database
    ↓
ChatWindow.tsx
    ├─ Receive chart_data via stream
    ├─ Parse chart configuration
    └─ Render ChartDisplay component
    ↓
ChartDisplay.tsx
    └─ Render Recharts visualization
```

### Database Schema

```sql
-- chat_messages table
CREATE TABLE chat_messages (
    message_id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT,
    tool_name TEXT,
    tool_payload TEXT,  -- JSON
    sql_details TEXT,   -- JSON
    calculation_details TEXT,  -- JSON
    chart_data TEXT,    -- JSON (NEW)
    error TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id)
);
```

### Chart Data Format (JSON)

```json
{
  "status": "success",
  "chart_type": "debt_breakdown",
  "title": "Debt Breakdown (Total: $50,000)",
  "chart_config": {
    "type": "pie",
    "data": [
      {"name": "Student", "value": 30000, "percentage": 60},
      {"name": "Auto", "value": 15000, "percentage": 30},
      {"name": "Credit Card", "value": 5000, "percentage": 10}
    ],
    "dataKey": "value",
    "nameKey": "name",
    "colors": ["#EF4444", "#F97316", "#F59E0B"],
    "legend": true,
    "tooltip": true,
    "labelFormat": "percentage"
  },
  "summary": {
    "total_debt": 50000,
    "debt_count": 3,
    "largest_debt": {"name": "Student", "value": 30000}
  }
}
```

---

## Testing Checklist

### Scenario A (Existing Users - C001, C002, etc.)

#### Debt Visualizations
- [ ] "Show me a breakdown of my debts" → debt_breakdown pie chart
- [ ] "Compare my debts" → debt_comparison bar chart
- [ ] "Visualize my debt payoff timeline" → payoff_timeline line chart

#### Spending Visualizations
- [ ] "Show me where my money goes" → spending_by_category pie chart
- [ ] "Breakdown my spending for the last 6 months" → spending_by_category with timeframe

#### Financial Health
- [ ] "What's my net worth?" → net_worth_composition pie chart
- [ ] "Compare my income and expenses" → income_vs_expense bar chart
- [ ] "Show my credit score history" → credit_score_trend line chart

#### Comparison Scenarios
- [ ] "Compare avalanche vs snowball strategies" → strategy_comparison chart
- [ ] "Show me current vs refinanced payments" → payment_comparison chart

---

## Future Enhancements

1. **Additional Chart Types**
   - Area charts for cumulative visualizations
   - Stacked bar charts for multi-category comparisons
   - Combo charts (bar + line)

2. **Customization Options**
   - User-selectable color themes
   - Chart export/download functionality
   - Interactive zoom and drill-down

3. **Advanced Analytics**
   - Goal progress visualizations
   - Budget vs actual spending
   - Savings rate trends
   - Investment portfolio allocation

4. **Scenario B Support**
   - Hypothetical scenario visualizations
   - Before/after comparison charts
   - Goal-based projections

---

## Summary

The visualization feature is now fully implemented and integrated into the Growbe financial advisory agent. It provides:

✅ **9 chart types** covering all major financial data categories
✅ **Smart agent integration** with clear prompting guidelines
✅ **Inline rendering** in chat messages (not in dropdowns)
✅ **Conversation persistence** - charts saved in chat history
✅ **Responsive design** with Recharts library
✅ **Hybrid approach** - explicit requests + smart suggestions
✅ **Scenario A ready** - full database integration

The system is production-ready for Scenario A users and can be easily extended for additional chart types and Scenario B support.

---

## Troubleshooting & Fixes Applied

### Issue 1: ImportError - Hook Class Not Found
**Problem:** `ImportError: cannot import name 'Hook' from 'strands.hooks'`

**Solution:** Changed `ChartCaptureHook` from inheriting `Hook` to `HookProvider` to match the Strands framework pattern used by other hooks.

**Files Modified:**
- `backend/hooks/chart_capture_hook.py` - Changed base class and implemented `register_hooks()` method

### Issue 2: Agent Not Passing customer_id to Visualization Tool
**Problem:** Agent was calling `create_visualization` multiple times without the `customer_id` parameter, causing repeated failures.

**Root Cause:** The agent didn't understand that "Explicit Customer ID Token: C001" in the prompt meant it should extract and use "C001" as the `customer_id` parameter.

**Solution:**
1. Added **"CUSTOMER IDENTIFICATION (CRITICAL)"** section to `backend/prompts/fin-adv-v2.txt` explicitly instructing the agent to:
   - Extract customer_id from "Explicit Customer ID Token: C001"
   - Pass it as a parameter to tools like `create_visualization`
   - Example: `create_visualization(chart_type="debt_breakdown", customer_id="C001")`

2. Enhanced error messages in `visualization_tool.py`:
   - Added `stop_retrying: True` flag to error responses
   - Clearer error messages explaining what went wrong
   - List of supported chart types in unsupported type error

3. Added **"ERROR HANDLING"** section to the prompt:
   - Instructs agent NOT to retry when `stop_retrying: True` is returned
   - Tells agent to present errors gracefully to users
   - Provide text-based information when charts fail

**Files Modified:**
- `backend/prompts/fin-adv-v2.txt` - Added customer ID extraction instructions and error handling guidelines
- `backend/tools/visualization_tool.py` - Enhanced error messages with stop_retrying flag

### Issue 3: Tool Not Being Invoked by Strands Framework
**Problem:** Agent was calling `create_visualization` but the tool's `execute()` method was never being invoked. No debug logs appeared, and charts weren't generated.

**Root Cause:** The `execute()` method was using `**kwargs` which prevents the Strands framework from understanding the tool's parameter signature. Without explicit parameters, Strands couldn't properly marshal arguments from the LLM to the tool.

**Solution:** Changed the `execute()` method signature from:
```python
def execute(self, **kwargs) -> Dict[str, Any]:
```

To explicit parameters:
```python
def execute(
    self,
    chart_type: str,
    customer_id: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    title: Optional[str] = None,
    timeframe: str = "3m"
) -> Dict[str, Any]:
```

This allows:
- Strands framework to understand required vs optional parameters
- Agent to see parameter types and defaults
- Proper argument marshaling from LLM responses to tool invocations

**Files Modified:**
- `backend/tools/visualization_tool.py` - Changed execute() signature to use explicit parameters

### Testing Results
✅ All imports successful
✅ Tool executes correctly with customer_id parameter
✅ Charts generate successfully for C001
✅ Hook properly integrated with agent
✅ Strands tool signature verified: `(chart_type: str, customer_id: Optional[str] = None, ...)`
✅ No linter errors

**⚠️ IMPORTANT:** After this fix, you must restart the backend server for changes to take effect!

### Issue 4: Agent Converting Charts to Base64 Images
**Problem:** Agent successfully called the visualization tool and generated chart data, but then tried to describe it as a base64-encoded PNG image, causing:
- Extremely long responses (base64 strings are thousands of characters)
- `max_tokens` errors from the LLM
- Charts not displaying in the frontend
- Frontend showing broken image syntax

**Root Cause:** The agent didn't understand that:
1. It should NOT try to render or describe the chart data
2. The frontend will automatically display the chart
3. It should just provide a brief acknowledgment message

**Solution:**
1. **Added explicit instructions to the prompt** (`backend/prompts/fin-adv-v2.txt`):
   - **"CHART RESPONSE FORMAT (CRITICAL)"** section
   - Tells agent to use the `_display_message` from the tool
   - Explicitly says: "DO NOT describe the chart data, DO NOT try to convert it to an image or base64"
   - Keep responses SHORT when charts are generated (1-2 sentences max)

2. **Added `_display_message` field to tool responses** (`backend/tools/visualization_tool.py`):
   ```python
   result["_display_message"] = (
       f"✅ Chart created: {result.get('title')}. "
       "The chart will be displayed automatically in the chat interface."
   )
   ```

3. **Chart rendering is handled entirely by the frontend**:
   - Backend streams `chart_data` separately from text content
   - Frontend `ChatWindow.tsx` receives and parses `chart_data`
   - `ChartDisplay.tsx` component renders the interactive Recharts visualization
   - No base64 encoding or image generation needed

**Expected Behavior After Fix:**
- Agent calls `create_visualization(chart_type="debt_breakdown", customer_id="C001")`
- Tool returns JSON with chart configuration
- Agent responds with simple message: "Here's your debt breakdown visualization."
- Frontend automatically renders interactive chart below the message
- No long base64 strings, no max_tokens errors

**Files Modified:**
- `backend/prompts/fin-adv-v2.txt` - Added chart response format instructions
- `backend/tools/visualization_tool.py` - Added `_display_message` field to success responses

