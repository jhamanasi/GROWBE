# Rent vs Buy Tool - Parameter Parsing Fix ✅

## 🐛 **Issue Identified**

The `rent_vs_buy` tool was being called by the agent but failing with:
```
"error": "home_price is required for rent vs buy analysis"
```

Even though the user provided:
- Home price: $350,000
- Monthly rent: $2,500

**Root Cause**: The tool was missing the **Strands framework parameter parsing logic** that handles parameters passed as JSON strings.

---

## ✅ **Fix Applied**

### **1. Added Strands Framework Parameter Parsing**

**Lines 131-141**:
```python
# Handle Strands framework parameter passing
if 'kwargs' in kwargs and isinstance(kwargs['kwargs'], str):
    import json
    try:
        parsed_kwargs = json.loads(kwargs['kwargs'])
        kwargs.update(parsed_kwargs)
    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "error": f"Failed to parse tool parameters: {str(e)}"
        }
```

This mirrors the same pattern used in `debt_optimizer_tool.py` (lines 146-156).

---

### **2. Added Debug Logging**

**Lines 143-148**:
```python
# Debug: Print received parameters
print(f"\n[RentVsBuyTool] Received parameters:")
print(f"  - Keys: {list(kwargs.keys())}")
for key, value in kwargs.items():
    if key not in ['kwargs']:  # Skip the raw kwargs string
        print(f"  - {key}: {value} (type: {type(value).__name__})")
```

This helps diagnose parameter issues in the backend logs.

---

### **3. Added Robust Type Conversion**

Parameters can arrive as strings from the agent, so we now convert them:

**Home Price (Lines 154-160)**:
```python
home_price = kwargs.get('home_price')
# Convert to float if it's a string
if home_price is not None and isinstance(home_price, str):
    try:
        home_price = float(home_price)
    except ValueError:
        home_price = None
```

**Monthly Rent (Lines 182-188)**:
```python
monthly_rent = kwargs.get('monthly_rent')
# Convert to float if it's a string
if monthly_rent is not None and isinstance(monthly_rent, str):
    try:
        monthly_rent = float(monthly_rent)
    except ValueError:
        monthly_rent = None
```

**All Numeric Parameters**:
- `down_payment_pct` → `float()`
- `mortgage_rate` → `float()`
- `mortgage_term_years` → `int()`
- `property_tax_rate` → `float()`
- `home_insurance_annual` → `float()`
- `hoa_monthly` → `float()`
- `maintenance_pct` → `float()`
- `appreciation_rate` → `float()`
- `analysis_years` → `int()`
- `marginal_tax_rate` → `float()`
- `investment_return_rate` → `float()`

**Boolean Parameters (Line 198-200)**:
```python
run_sensitivity = kwargs.get('run_sensitivity', True)
if isinstance(run_sensitivity, str):
    run_sensitivity = run_sensitivity.lower() in ['true', '1', 'yes']
```

---

## 📊 **Expected Backend Log Output (After Fix)**

When the tool is called, you should now see:

```bash
Tool #X: rent_vs_buy

[RentVsBuyTool] Received parameters:
  - Keys: ['home_price', 'monthly_rent', 'customer_id', 'region']
  - home_price: 350000 (type: int)
  - monthly_rent: 2500 (type: int)
  - customer_id: C001 (type: str)
  - region: MD (type: str)

✅ [RentVsBuyTool] Stored calculation details
   - Steps: 8
   - Formulas: 5
```

---

## 🧪 **Test Case That Was Failing**

**User**: Maya (C001)  
**Query**: "Should I buy a $350,000 house or keep renting? My current rent is around $2500"

**Before Fix**:
```
Tool #2: rent_vs_buy
It seems there was an issue with the analysis due to the home price requirement.

Tool #3: rent_vs_buy
It appears that I'm still encountering an issue with the analysis tool...
```

**After Fix (Expected)**:
```
Tool #2: rent_vs_buy
[RentVsBuyTool] Received parameters: ...
[RentVsBuyTool] Stored calculation details

Agent Response:
Based on a comprehensive analysis, here's how buying a $350,000 home compares to renting at $2,500/month:

**Monthly Costs:**
- Renting: $2,525/month
- Owning (after tax benefits): $2,427/month

**Break-Even Point:** Year 7

**Long-Term (10 years):**
- Total rent paid: $313,000
- Home equity: $283,000
- Net proceeds if sold: $254,000

[Blue Calculation Dropdown Appears]
🏠 Rent vs Buy Analysis [8 steps]
```

---

## ✅ **Changes Summary**

| Change | Lines | Purpose |
|--------|-------|---------|
| Strands parameter parsing | 131-141 | Handle JSON string parameters |
| Debug logging | 143-148 | Diagnose parameter issues |
| `home_price` type conversion | 154-160 | Handle string to float |
| `monthly_rent` type conversion | 182-188 | Handle string to float |
| All numeric params conversion | Various | Ensure correct types |
| Boolean param conversion | 198-200 | Handle string booleans |

**Total Lines Modified**: ~50 lines  
**Files Changed**: 1 (`rent_vs_buy_tool.py`)

---

## 🚀 **Testing Instructions**

1. **Restart backend**: `cd backend && python main.py`
2. **Ask Maya (C001)**: "Should I buy a $350,000 house or keep renting? My rent is $2,500"
3. **Watch backend logs** for:
   - `[RentVsBuyTool] Received parameters` with all values
   - `✅ [RentVsBuyTool] Stored calculation details`
4. **Verify frontend**:
   - Agent provides clean analysis summary
   - Blue "🏠 Rent vs Buy Analysis" dropdown appears
   - Dropdown expands to show LaTeX formulas

---

## 🔍 **Why This Happened**

The `debt_optimizer_tool` already had this parsing logic because it was created earlier and tested extensively. When creating `rent_vs_buy_tool`, I initially followed the pattern but missed the critical Strands framework parameter handling that wraps parameters in a JSON string.

**Lesson Learned**: Always include the Strands parameter parsing boilerplate in new tools!

---

## ✅ **Status**

- ✅ Parameter parsing fixed
- ✅ Type conversion added
- ✅ Debug logging added
- ✅ No linting errors
- ✅ Ready for testing

**The rent vs buy tool should now work correctly!** 🏠🎉

---

**Fixed**: November 1, 2025  
**File**: `backend/tools/rent_vs_buy_tool.py`  
**Issue**: Missing Strands parameter parsing  
**Resolution**: Added JSON parsing + type conversion

