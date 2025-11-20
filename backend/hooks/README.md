# Hooks System Documentation

## Overview

The hooks system in the Financial Advisory Agent provides a powerful event-driven architecture that allows components to react to agent activities in real-time. Hooks enable automatic data capture, UI enhancements, conversation tracking, and intelligent feature activation without modifying core agent logic.

## Architecture

### HookProvider Base Class
All hooks inherit from `HookProvider` and implement:
- `register_hooks(registry: HookRegistry)` - Registers callback functions
- Callback methods for specific events

### Event Types
Hooks respond to different types of events:
- `AfterInvocationEvent` - Fired after tool execution
- `MessageAddedEvent` - Fired when messages are added to conversations

## Available Hooks

### 1. CalculationCaptureHook (`calculation_capture_hook.py`)

**Purpose**: Captures mathematical calculation details from financial tools for enhanced UI display.

**What it does**:
- Monitors tool executions for calculation-heavy tools (`debt_optimizer`, `student_loan_payment_calculator`, etc.)
- Extracts `calculation_steps` and `latex_formulas` from tool results
- Stores them globally for frontend collapsible display panels

**Key Features**:
- Intelligent tool detection (only captures from calculation tools)
- Robust result parsing (handles different result formats)
- Debug logging for troubleshooting

**Benefits**: Users can see step-by-step math behind financial calculations without cluttering the chat.

---

### 2. ChartCaptureHook (`chart_capture_hook.py`)

**Purpose**: Automatically captures chart data from visualization tools for seamless UI integration.

**What it does**:
- Monitors all tool executions for chart generation
- Extracts chart configuration from `visualization_tool` results
- Stores chart data globally for frontend rendering

**Key Features**:
- Non-intrusive (works with any tool that generates charts)
- Automatic data persistence across requests
- Memory-efficient (clears previous chart data)

**Benefits**: Charts appear inline in conversations without manual intervention.

---

### 3. ConversationCaptureHook (`conversation_capture_hook.py`)

**Purpose**: Automatically saves conversation data for lead management and CRM integration.

**What it does**:
- Captures user messages and agent responses in real-time
- Parses conversation content for lead information extraction
- Updates lead profiles with extracted data (location, budget, timeline, etc.)
- Saves conversations to database for realtor access

**Key Features**:
- Intelligent information extraction using regex patterns
- Lead profile auto-updating (engagement scores, property requirements)
- Context-aware parsing (combines user + agent messages)

**Benefits**: Enables seamless lead management and conversation history tracking for business operations.

---

### 4. FinancialConversationHook (`financial_conversation_hook.py`)

**Purpose**: Extracts financial information from conversations and updates customer profiles automatically.

**What it does**:
- Monitors incoming messages for financial data patterns
- Extracts income, debt, savings amounts using regex
- Updates customer profiles with discovered information
- Identifies assessment question opportunities

**Key Features**:
- Pattern-based extraction (income: "$75K", debt: "$20K loan")
- Automatic profile updates during natural conversation
- Assessment question detection and suggestions

**Benefits**: Customer profiles stay current without explicit data entry, enabling personalized advice.

---

### 5. SQLResultCaptureHook (`sql_capture_hook.py`)

**Purpose**: Enhances database query results with intelligent chart suggestions and UI formatting.

**What it does**:
- Captures SQL queries and results from `nl2sql_query` tool
- Analyzes result patterns to suggest optimal visualizations
- Provides structured data for enhanced frontend display
- Auto-generates chart configurations based on data characteristics

**Key Features**:
- Chart eligibility analysis (numeric data, row counts, query patterns)
- Intelligent chart type suggestions (bar, line, pie, scatter)
- Performance optimization (limits large result sets)

**Benefits**: Database queries automatically become visual when appropriate, improving data comprehension.

## Hook Registration System

### How Hooks Are Loaded
```python
# In main.py or agent initialization
hook_registry = HookRegistry()
hooks = [
    CalculationCaptureHook(),
    ChartCaptureHook(),
    ConversationCaptureHook(lead_service),
    FinancialConversationHook(),
    SQLResultCaptureHook()
]

for hook in hooks:
    hook.register_hooks(hook_registry)
```

### Event Flow
1. **Agent executes tool** → `AfterInvocationEvent` fired
2. **Hooks receive event** → Process relevant data
3. **Data stored globally** → Available for UI consumption
4. **Frontend displays enhanced content** → Charts, calculations, etc.

## Configuration & Customization

### Adding New Hooks
1. Create class inheriting from `HookProvider`
2. Implement `register_hooks()` method
3. Add callback methods for desired events
4. Register with `HookRegistry`

### Event Customization
Hooks can respond to any `strands.hooks.events`:
- `AfterInvocationEvent` - Tool execution complete
- `BeforeInvocationEvent` - Tool about to execute
- `MessageAddedEvent` - New conversation message
- Custom events as needed

## Benefits & Use Cases

### For Users
- **Rich Visualizations**: Charts appear automatically for data queries
- **Calculation Transparency**: Step-by-step math behind financial advice
- **Seamless Experience**: No manual chart generation or data export

### For Developers
- **Modular Architecture**: Hooks don't modify core agent logic
- **Event-Driven**: Reactive programming paradigm
- **Easy Extension**: New features via hook addition

### For Business
- **Lead Management**: Automatic conversation capture and CRM integration
- **Profile Enrichment**: Customer data extracted from natural conversation
- **Analytics**: Rich data for conversation and user behavior analysis

## Technical Details

### Global Data Storage
Hooks use module-level variables for data persistence:
```python
# Module level storage
_last_calculation_details = None
_captured_chart_data = None

def get_last_calculation_details():
    return _last_calculation_details
```

### Error Handling
All hooks include comprehensive error handling:
- Try/catch blocks around all operations
- Graceful degradation when hooks fail
- Debug logging for troubleshooting

### Performance Considerations
- Hooks execute synchronously with agent operations
- Minimal overhead for non-matching events
- Data limits (100 rows max for SQL results)

## Future Enhancements

### Planned Hook Features
- **Analytics Hook**: Track user behavior patterns
- **Notification Hook**: Alert on important financial thresholds
- **Integration Hook**: Connect to external CRM systems
- **Audit Hook**: Log all financial advice for compliance

### Customization Options
- Configurable data retention periods
- Custom event filtering
- Hook enable/disable toggles
- Priority-based hook execution

## Troubleshooting

### Common Issues
1. **Hook not firing**: Check event type registration
2. **Data not captured**: Verify tool result format compatibility
3. **Performance impact**: Profile hook execution times

### Debug Mode
Enable debug logging to see hook activity:
```python
import logging
logging.getLogger('hooks').setLevel(logging.DEBUG)
```

## Conclusion

The hooks system transforms the Financial Advisory Agent from a simple chatbot into a rich, integrated financial platform. By automatically capturing data, generating visualizations, and managing conversations, hooks enable seamless user experiences and powerful business capabilities without complicating the core agent logic.

Hooks represent the "glue" that connects agent intelligence with user interface and business systems, making complex financial interactions feel natural and effortless.
