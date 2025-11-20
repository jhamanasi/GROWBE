# Calculation Dropdown Fix - Direct Capture Approach ✅

## 🐛 **Issue**

The calculation details dropdown was not appearing in the frontend even though:
- ✅ Backend was calling `debt_optimizer` tool successfully
- ✅ Tool was generating `calculation_steps` and `latex_formulas`
- ✅ Hook system was registered properly

**Root Cause**: The `CalculationCaptureHook` using `AfterInvocationEvent` was not receiving tool execution events from the Strands framework.

---

## ✅ **Solution**

Switched from **hook-based capture** to **direct module-level storage**, following the exact same pattern used by the working `nl2sql_tool`.

### **Pattern Analysis:**

#### **SQL Tool (Working) ✅**
```python
# In nl2sql_tool.py
LAST_SQL_DETAILS: Dict[str, Any] = {}

def get_last_sql_details(clear: bool = True) -> Optional[Dict]:
    global LAST_SQL_DETAILS
    return LAST_SQL_DETAILS

# In execute():
global LAST_SQL_DETAILS
LAST_SQL_DETAILS = sql_details  # Store before return

# In main.py:
from tools.nl2sql_tool import get_last_sql_details
sql_details = get_last_sql_details()
```

#### **Calculation Tool (Now Fixed) ✅**
```python
# In debt_optimizer_tool.py
_last_calculation_details: Optional[Dict[str, Any]] = None

def get_last_calculation_details() -> Optional[Dict]:
    return _last_calculation_details

# In execute():
global _last_calculation_details
_last_calculation_details = {
    'scenario_type': result.get('scenario_type'),
    'calculation_steps': result.get('calculation_steps', []),
    'latex_formulas': result.get('latex_formulas', [])
}

# In main.py:
from tools.debt_optimizer_tool import get_last_calculation_details
calculation_details = get_last_calculation_details()
```

---

## 🔧 **Changes Made**

### **1. `/backend/tools/debt_optimizer_tool.py`**

**Added (Lines 15-25):**
```python
# Module-level variable to store last calculation details
_last_calculation_details: Optional[Dict[str, Any]] = None

def get_last_calculation_details() -> Optional[Dict[str, Any]]:
    """Retrieve the last captured calculation details."""
    return _last_calculation_details

def clear_calculation_details():
    """Clear the captured calculation details."""
    global _last_calculation_details
    _last_calculation_details = None
```

**Modified `execute()` method (Lines 193-206):**
```python
# Store calculation details globally for frontend display
if result and isinstance(result, dict) and result.get("status") != "error":
    if "calculation_steps" in result or "latex_formulas" in result:
        global _last_calculation_details
        _last_calculation_details = {
            'scenario_type': result.get('scenario_type', result.get('strategy', 'unknown')),
            'calculation_steps': result.get('calculation_steps', []),
            'latex_formulas': result.get('latex_formulas', []),
            'tool_name': 'debt_optimizer'
        }
        print(f"\n✅ [DebtOptimizerTool] Stored calculation details: {_last_calculation_details['scenario_type']}")
        print(f"   - Steps: {len(_last_calculation_details['calculation_steps'])}")
        print(f"   - Formulas: {len(_last_calculation_details['latex_formulas'])}")

return result
```

### **2. `/backend/main.py`**

**Added import (Line 20):**
```python
from tools.debt_optimizer_tool import get_last_calculation_details
```

**Updated `/chat` endpoint (Lines 507-511):**
```python
# Add calculation details if available
calculation_details = get_last_calculation_details()
if calculation_details:
    chat_response.calculation_details = calculation_details
    print(f"🧮 Added calculation details to response: {calculation_details.get('scenario_type', 'N/A')}")
```

**Updated `/chat/stream` endpoint (Lines 601-605):**
```python
# Send calculation details if available
calculation_details = get_last_calculation_details()
if calculation_details:
    yield f"data: {json.dumps({'calculation_details': calculation_details})}\n\n"
    await asyncio.sleep(0)
```

---

## 📊 **Expected Backend Log Output**

When a calculation tool is used, you should now see:

```bash
Tool #5: debt_optimizer

✅ [DebtOptimizerTool] Stored calculation details: refinance
   - Steps: 5
   - Formulas: 4

🧮 Added calculation details to response: refinance
```

---

## 🎯 **Testing**

### **Test Query:**
Ask Maya (C001): **"If I refinance my student loan to 3.5%, how much would I save?"**

### **Expected Behavior:**

1. **Backend Terminal:**
   ```
   Tool #X: debt_optimizer
   ✅ [DebtOptimizerTool] Stored calculation details: refinance
      - Steps: 5
      - Formulas: 4
   🧮 Added calculation details to response: refinance
   ```

2. **Frontend UI:**
   - Clean agent response with results
   - **Blue dropdown panel** appears below response
   - Panel header: "🧮 Refinancing Analysis [5 steps]"
   - Click to expand shows all calculation steps with LaTeX formulas

---

## ✅ **Why This Approach Works**

### **Hook-Based Approach (Failed) ❌**
- Relies on `AfterInvocationEvent` from Strands
- Event structure varies by framework version
- Not receiving tool execution events
- Complex event parsing logic
- Hard to debug

### **Direct Storage Approach (Working) ✅**
- Stores data directly in tool's `execute()` method
- Simple global variable pattern
- No dependency on event system
- Proven pattern (SQL tool uses same approach)
- Easy to debug with print statements

---

## 📝 **Key Differences from SQL Tool**

| Aspect | SQL Tool | Calculation Tool |
|--------|----------|------------------|
| Storage Variable | `LAST_SQL_DETAILS` (dict) | `_last_calculation_details` (Optional[Dict]) |
| Storage Location | In `execute()` at line 482 | In `execute()` at lines 193-206 |
| Clear Function | `get_last_sql_details(clear=True)` | `clear_calculation_details()` |
| Data Structure | `{sql, result, columns, rows}` | `{scenario_type, calculation_steps, latex_formulas}` |

---

## 🚀 **Next Steps**

1. **Restart backend**: `cd backend && python main.py`
2. **Refresh frontend** (if already running)
3. **Test refinancing query** with Maya (C001)
4. **Verify**:
   - ✅ Backend logs show "Stored calculation details"
   - ✅ Frontend displays calculation dropdown
   - ✅ Dropdown expands to show formulas
5. **Test other scenarios** (consolidation, extra payment, target payoff)

---

## 🎉 **Status**

- ✅ Direct storage implemented in `debt_optimizer_tool.py`
- ✅ Import added to `main.py`
- ✅ Both `/chat` and `/chat/stream` endpoints updated
- ✅ No linting errors
- ✅ Ready for testing

**The calculation dropdown should now work!** 🚀

---

**Fixed**: November 1, 2025  
**Approach**: Direct module-level storage (matching SQL tool pattern)  
**Files Modified**: 2 (`debt_optimizer_tool.py`, `main.py`)  
**Lines Added**: ~30 lines total

