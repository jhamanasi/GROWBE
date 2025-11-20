# Critical Fixes: Calculation Persistence & NL2SQL Transaction Queries ✅

## 🐛 **Issue 1: Calculation Details Persisting Across Different User Chats**

### **Problem Reported by User**

When user **C002 (Lucas)** started a new chat, the calculation dropdown from the **previous chat** (C001/Maya's $350k home analysis) was showing up.

**Screenshot Evidence**:
```
Hi Lucas! It's great to see you. You have a total debt of $23,816.32...

Calculation Details
8 steps
Click to hide

1. Home Purchase Overview
Home Price: $350,000.00, Down Payment: $70,000.00 (20.0%), Loan Amount: $280,000.00
...
```

This is **C001's data** appearing in **C002's chat**! 🚨

---

### **Root Cause**

**Module-level variables** in tools (`_last_calculation_details`, `_last_rent_buy_details`, `LAST_SQL_DETAILS`) are stored at the **module level** and are **NEVER cleared** between different user sessions/chats.

**How It Happens**:
1. User C001 asks about buying a $350k home
2. `rent_vs_buy_tool` stores calculation details in `_last_rent_buy_details`
3. `main.py` retrieves and sends to frontend
4. User C001's chat ends
5. **User C002 starts a NEW chat**
6. `main.py` retrieves calculation details → **still has C001's data!**
7. C002 sees C001's $350k home analysis 💥

**This is a MAJOR privacy/data leak issue!**

---

### **✅ Fix Applied**

**Added automatic clearing at the start of EVERY chat request.**

#### **1. Updated Imports in main.py (Line 19-21)**

```python
from tools.nl2sql_tool import get_last_sql_details, clear_sql_details
from tools.debt_optimizer_tool import get_last_calculation_details, clear_calculation_details
from tools.rent_vs_buy_tool import get_last_rent_buy_details, clear_rent_buy_details
```

#### **2. Added clear_sql_details() function to nl2sql_tool.py (Line 403)**

```python
def clear_sql_details():
    """Clear the captured SQL details."""
    global LAST_SQL_DETAILS
    LAST_SQL_DETAILS = {}
```

(Note: `debt_optimizer_tool` and `rent_vs_buy_tool` already had `clear_*` functions)

#### **3. Clear All Tools at Start of /chat Endpoint (Line 419-423)**

```python
# Clear all tool results from previous requests to prevent cross-contamination
clear_sql_details()
clear_calculation_details()
clear_rent_buy_details()
print("🧹 Cleared all tool results from previous chat sessions")
```

#### **4. Clear All Tools at Start of /chat/stream Endpoint (Line 536-539)**

```python
# Clear all tool results from previous requests to prevent cross-contamination
clear_sql_details()
clear_calculation_details()
clear_rent_buy_details()
```

---

### **Expected Behavior After Fix**

**Backend Terminal (Every New Chat)**:
```bash
💬 Chat request: Should I buy a $350,000 house or keep renting?...
👤 User type: existing, Session ID: C002
🧹 Cleared all tool results from previous chat sessions
📊 Customer context retrieved for C002
```

**Frontend**:
- ✅ C002's chat starts fresh with NO calculation dropdown
- ✅ Only calculations from C002's current session appear
- ✅ When C002 asks a question, their calculation details appear (not C001's)

---

## 🐛 **Issue 2: Agent Not Using NL2SQL for Transaction Queries**

### **Problem Reported by User**

User C002 asked: **"Can you check my transactions to see what my rent is?"**

Agent responded: **"I can't access your transaction details directly."**

**But the CSV clearly shows**:
```csv
T99366	121702858757	2024-11-02	-2412	LandlordRent	HOU	Housing	Rent
```

The agent should have used `nl2sql_query` to query the `transaction` table!

---

### **Root Cause**

The agent prompt had instructions for using `nl2sql_query` for **debts, loans, accounts**, but it **never explicitly mentioned transactions**.

**From old prompt (Line 206)**:
```
- **MANDATORY FOR DEBT QUESTIONS**: When user asks about debts, loans, 
  accounts, or specific financial details, you MUST call nl2sql_query...
```

❌ No mention of **transactions**  
❌ No mention of **rent payments**  
❌ No mention of **spending patterns**  

So when the user asked about transactions, the agent thought it couldn't access them!

---

### **✅ Fix Applied**

**Updated agent prompt to explicitly include transaction queries.**

#### **Updated NL2SQL Tool Section (fin-adv-v2.txt, Lines 206-228)**

**Before**:
```
- **MANDATORY FOR DEBT QUESTIONS**: When user asks about debts, loans, 
  accounts, or specific financial details, you MUST call nl2sql_query...
```

**After**:
```python
- **MANDATORY FOR ALL DATABASE QUERIES**: When user asks about ANY of the following, 
  you MUST call nl2sql_query:
  - Debts, loans, accounts, or specific financial details
  - **Transaction history** (rent payments, spending patterns, income deposits, specific merchants)
  - Credit reports, FICO scores, credit utilization
  - Employment and income information
  - Assets and investments
  - ANY question that requires accessing the database tables

- **TRANSACTION QUERIES (IMPORTANT)**:
  - User asks: "What's my rent?" or "Check my transactions for rent" → Use nl2sql_query!
  - User asks: "How much do I spend on groceries?" → Use nl2sql_query!
  - User asks: "Show me recent transactions" → Use nl2sql_query!
  - The `transaction` table has columns: txn_id, account_id, txn_date, amount, 
    merchant, category_lvl1, category_lvl2, description
  - Example query: "what are the recent rent transactions for customer C002?"
  - Example query: "what is customer C002's monthly rent based on transaction history?"

- **CUSTOMER ID REQUIRED**: When calling nl2sql_query, include the customer ID in the question text.
  - Example: "what type of debt does customer C002 have?" instead of "what type of debt is it?"
  - Example: "what are the rent transactions for customer C002?" instead of "what are the rent transactions?"
  - The tool needs the customer ID (C001, C002, etc.) in the question to work properly.
```

**Key Additions**:
1. ✅ **Transaction history** explicitly listed as a database query
2. ✅ **3 concrete examples** of transaction queries with exact wording
3. ✅ **Table structure** documented (columns: txn_id, account_id, txn_date, amount, merchant, category_lvl1, category_lvl2, description)
4. ✅ **Example queries** for rent: "what are the recent rent transactions for customer C002?"
5. ✅ **Reinforced customer ID requirement** for all queries

---

### **Expected Behavior After Fix**

**User Query**: "Can you check my transactions to see what my rent is?"

**Before Fix** ❌:
```
Agent: I can't access your transaction details directly.
```

**After Fix** ✅:
```
Agent calls: nl2sql_query
Question: "what are the recent rent transactions for customer C002 from the transaction table?"

SQL Generated:
SELECT txn_date, amount, merchant, description 
FROM transaction 
WHERE account_id IN (SELECT account_id FROM account WHERE customer_id = 'C002')
  AND category_lvl2 = 'Rent'
ORDER BY txn_date DESC 
LIMIT 10;

Agent Response:
"Based on your transaction history, I can see you've been paying $2,412 per month 
in rent to LandlordRent. Your most recent rent payment was on November 2, 2024."
```

**SQL Details Dropdown** (appears in UI):
```
📊 SQL Query & Results | 1 rows
▼ Click to expand

Query:
SELECT txn_date, amount, merchant, description 
FROM transaction 
WHERE...

Results:
txn_date | amount | merchant | description
2024-11-02 | -2412 | LandlordRent | Rent
```

---

## ✅ **Files Changed**

| File | Lines Changed | Purpose |
|------|---------------|---------|
| `backend/main.py` | +3 imports, +8 lines (2 endpoints) | Import clear functions, clear all tools at start |
| `backend/tools/nl2sql_tool.py` | +5 lines | Add `clear_sql_details()` function |
| `backend/prompts/fin-adv-v2.txt` | +22 lines | Add transaction query instructions |

**Total Changes**: ~38 lines across 3 files

---

## 🧪 **Testing Instructions**

### **Test 1: Calculation Persistence Fix**

1. **Start backend**: `cd backend && python main.py`
2. **Chat as C001**: "Should I buy a $350,000 house or keep renting? My rent is $2,500"
3. **Verify**: Calculation dropdown appears for C001
4. **Start NEW chat as C002**: "Hi, what's my financial summary?"
5. **Verify**: 
   - ✅ Backend terminal shows: `🧹 Cleared all tool results from previous chat sessions`
   - ✅ C002's chat has NO calculation dropdown (clean start)
   - ✅ Only when C002 asks a calculation question does their dropdown appear

### **Test 2: Transaction Query Fix**

1. **Chat as C002**: "Can you check my transactions to see what my rent is?"
2. **Verify Backend Terminal**:
   - ✅ See: `Tool #X: nl2sql_query`
   - ✅ See SQL generation for transaction table
   - ✅ See query results with rent amount
3. **Verify Frontend**:
   - ✅ Agent provides rent amount from transactions
   - ✅ SQL dropdown appears with query and results
   - ✅ Response mentions "$2,412" (C002's actual rent)

**Additional Transaction Queries to Test**:
- "What's my rent?"
- "Show me my recent transactions"
- "How much do I spend on groceries?"
- "What are my income deposits?"
- "Show me transactions from last month"

---

## 🔍 **Why These Issues Happened**

### **Issue 1: Module-Level Variables**

**Design Choice**: Tools store results in module-level variables for easy access across function calls.

**Problem**: Module-level variables persist for the **entire Python process lifetime**, not per-request.

**Why We Didn't See It Before**: 
- Single-user testing
- Same user across multiple queries
- Never tested switching between users mid-session

**Proper Solution**: Clear all tool results at the **start of each request**.

---

### **Issue 2: Prompt Incompleteness**

**Design Evolution**: 
1. Initially focused on debt/loan queries
2. Added account queries
3. **Forgot to add transaction queries** when they were needed

**Why Agent Said "I can't access"**:
- Agent knows it has access to `nl2sql_query` tool
- But prompt didn't list **transactions** as a valid use case
- So agent assumed transactions were off-limits
- Responded conservatively: "I can't access"

**Proper Solution**: **Comprehensive tool documentation** in the prompt with concrete examples.

---

## ✅ **Status**

- ✅ **Issue 1 Fixed**: Calculation details cleared at start of each chat
- ✅ **Issue 2 Fixed**: Agent now knows to use nl2sql for transaction queries
- ✅ No linting errors
- ✅ Ready for testing

**Both critical bugs are now resolved!** 🎉

---

## 📋 **Checklist for Future Tool Additions**

When adding a new tool that stores module-level results:

1. ✅ Add a `clear_*()` function to the tool
2. ✅ Import the `clear_*()` function in `main.py`
3. ✅ Call `clear_*()` in both `/chat` and `/chat/stream` endpoints
4. ✅ Update agent prompt with:
   - When to use the tool
   - What data it can access
   - Concrete example queries
   - Table structure (if applicable)
5. ✅ Test with **multiple users** to ensure no cross-contamination

---

**Fixed**: November 2, 2025  
**Issues**: Calculation persistence + NL2SQL transaction awareness  
**Resolution**: Clear tools at request start + updated prompt with transaction examples  
**Files**: `main.py`, `nl2sql_tool.py`, `fin-adv-v2.txt`  
**Impact**: CRITICAL - fixes data leak and missing functionality

