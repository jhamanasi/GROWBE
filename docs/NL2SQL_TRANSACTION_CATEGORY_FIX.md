# NL2SQL Transaction Category Fix ✅

## 🐛 **Issue: NL2SQL Generating Wrong SQL for Rent Transactions**

### **Problem Reported**

User C002 asked: **"Can you check my transactions to see what my rent is?"**

Agent **DID** use `nl2sql_query` (good! ✅), but the SQL was WRONG:

**Generated SQL (WRONG)**:
```sql
SELECT ... 
FROM transactions t
JOIN accounts a ON t.account_id = a.account_id
WHERE a.customer_id = 'C002' AND t.category_lvl1 = 'Rent'  ← WRONG!
ORDER BY t.posted_date DESC
```

**Result**: 0 rows found ❌

**Actual Data in Database**:
```csv
txn_id  | posted_date | amount   | merchant      | category_lvl1 | category_lvl2
T99366  | 2024-11-02  | -2412.0  | LandlordRent  | Housing       | Rent
T11971  | 2024-12-02  | -2227.0  | LandlordRent  | Housing       | Rent
T39249  | 2025-01-02  | -2122.0  | LandlordRent  | Housing       | Rent
```

---

## 🔍 **Root Cause Analysis**

### **The Problem**

The NL2SQL system prompt was too vague about the `transactions` table structure:

**Old Prompt (Line 28)**:
```
- transactions: Individual transactions with amounts, merchants, categories
```

❌ Doesn't specify what "categories" means  
❌ Doesn't explain `category_lvl1` vs `category_lvl2`  
❌ Doesn't give examples of category values  

**Result**: OpenAI's model guessed that rent would be in `category_lvl1`, but it's actually in `category_lvl2`.

---

### **Actual Schema**

```sql
CREATE TABLE transactions (
  txn_id TEXT,
  account_id INTEGER,
  posted_date TEXT,
  amount REAL,
  merchant TEXT,
  mcc TEXT,
  category_lvl1 TEXT,    ← Broad category: "Housing", "Food", "Transport", "Income"
  category_lvl2 TEXT     ← Specific category: "Rent", "Groceries", "Gas", "Salary"
);
```

**Category Hierarchy Examples**:
- Rent: `category_lvl1 = 'Housing'` AND `category_lvl2 = 'Rent'`
- Groceries: `category_lvl1 = 'Food'` AND `category_lvl2 = 'Groceries'`
- Gas: `category_lvl1 = 'Transport'` AND `category_lvl2 = 'Gas'`
- Salary: `category_lvl1 = 'Income'` AND `category_lvl2 = 'Salary'`

---

## ✅ **Fix Applied**

### **1. Updated TABLE STRUCTURE Section (Lines 28-32)**

**Before**:
```
- transactions: Individual transactions with amounts, merchants, categories
```

**After**:
```python
- transactions: Individual transactions (txn_id, account_id, posted_date, amount, 
                merchant, category_lvl1, category_lvl2)
  * category_lvl1 = broad category (e.g., 'Housing', 'Food', 'Transport', 'Income')
  * category_lvl2 = specific category (e.g., 'Rent', 'Groceries', 'Gas', 'Salary')
  * For rent: category_lvl1 = 'Housing' AND category_lvl2 = 'Rent'
  * For income: category_lvl1 = 'Income'
```

**Key Additions**:
- ✅ Listed all column names explicitly
- ✅ Explained the two-level category hierarchy
- ✅ Provided concrete examples for each level
- ✅ **Explicit instruction for rent queries**: `category_lvl2 = 'Rent'`

---

### **2. Added Transaction Examples to COMMON FINANCIAL QUERIES (Lines 79-81)**

**Before**:
```
- Recent transactions: SELECT * FROM transactions t ...
- Credit score history: ...
```

**After**:
```sql
- Recent transactions: SELECT * FROM transactions t JOIN accounts a 
  ON t.account_id = a.account_id WHERE a.customer_id = 'C001' 
  ORDER BY posted_date DESC LIMIT 10

- Rent transactions: SELECT posted_date, amount, merchant FROM transactions t 
  JOIN accounts a ON t.account_id = a.account_id 
  WHERE a.customer_id = 'C001' AND category_lvl2 = 'Rent' 
  ORDER BY posted_date DESC

- Monthly rent amount: SELECT AVG(amount) as avg_rent FROM transactions t 
  JOIN accounts a ON t.account_id = a.account_id 
  WHERE a.customer_id = 'C001' AND category_lvl2 = 'Rent'

- Spending by category: SELECT category_lvl1, SUM(amount) as total 
  FROM transactions t JOIN accounts a ON t.account_id = a.account_id 
  WHERE a.customer_id = 'C001' GROUP BY category_lvl1

- Credit score history: ...
```

**Key Additions**:
- ✅ **Rent transactions** example with correct `category_lvl2 = 'Rent'`
- ✅ **Monthly rent amount** example using `AVG(amount)`
- ✅ **Spending by category** example showing `category_lvl1` usage

---

## 📊 **Expected Behavior After Fix**

### **User Query**: "Can you check my transactions to see what my rent is?"

**Agent Behavior**:
1. Calls `nl2sql_query` ✅
2. Prompt now includes clear transaction category structure ✅
3. OpenAI generates **CORRECT SQL** ✅

**Correct SQL Generated**:
```sql
SELECT posted_date, amount, merchant 
FROM transactions t
JOIN accounts a ON t.account_id = a.account_id
WHERE a.customer_id = 'C002' 
  AND category_lvl2 = 'Rent'  ← CORRECT!
ORDER BY posted_date DESC;
```

**Results**:
```
posted_date | amount   | merchant
2025-03-02  | -2043.0  | LandlordRent
2025-02-02  | -2093.0  | LandlordRent
2025-01-02  | -2122.0  | LandlordRent
2024-12-02  | -2227.0  | LandlordRent
2024-11-02  | -2412.0  | LandlordRent
```

**Agent Response**:
```
Based on your transaction history, you've been paying rent to LandlordRent. 
Your most recent rent payment was $2,043 on March 2, 2025. Looking at your 
recent payments, your average monthly rent is approximately $2,179.

[SQL Query & Results dropdown appears with 5 rows]
```

---

## 🧪 **Testing Instructions**

### **Test Case 1: Basic Rent Query**

**Query**: "Can you check my transactions to see what my rent is?"

**Verify**:
1. ✅ Backend shows: `Tool #X: nl2sql_query`
2. ✅ SQL includes: `category_lvl2 = 'Rent'` (NOT `category_lvl1 = 'Rent'`)
3. ✅ Results show 5 rent transactions for C002
4. ✅ Agent provides rent amounts
5. ✅ SQL dropdown shows correct query

### **Test Case 2: Monthly Rent Average**

**Query**: "What's my average monthly rent?"

**Expected SQL**:
```sql
SELECT AVG(amount) as avg_rent 
FROM transactions t
JOIN accounts a ON t.account_id = a.account_id
WHERE a.customer_id = 'C002' AND category_lvl2 = 'Rent';
```

**Verify**: Agent says approximately $2,179/month

### **Test Case 3: Recent Rent Payments**

**Query**: "Show me my last 3 rent payments"

**Expected SQL**:
```sql
SELECT posted_date, amount, merchant 
FROM transactions t
JOIN accounts a ON t.account_id = a.account_id
WHERE a.customer_id = 'C002' AND category_lvl2 = 'Rent'
ORDER BY posted_date DESC
LIMIT 3;
```

**Verify**: Shows March, February, January 2025 payments

### **Test Case 4: Spending by Category**

**Query**: "How much do I spend on housing?"

**Expected SQL**:
```sql
SELECT SUM(amount) as total_housing
FROM transactions t
JOIN accounts a ON t.account_id = a.account_id
WHERE a.customer_id = 'C002' AND category_lvl1 = 'Housing';
```

**Verify**: Includes rent + utilities + other housing costs

### **Test Case 5: Other Categories**

**Queries to Test**:
- "How much do I spend on groceries?" → `category_lvl2 = 'Groceries'`
- "Show my gas expenses" → `category_lvl2 = 'Gas'`
- "What's my income?" → `category_lvl1 = 'Income'`
- "Show food expenses" → `category_lvl1 = 'Food'`

---

## 🔍 **Why This Happened**

### **Design Evolution**

1. **Initial Implementation**: NL2SQL system prompt was created with basic table descriptions
2. **Focus on Debt Queries**: Most testing focused on `debts_loans`, `accounts`, `customers` tables
3. **Transaction Table Underdocumented**: `transactions` table had minimal description
4. **Category Structure Assumed**: Assumed OpenAI would figure out the two-level category structure

**Result**: OpenAI made reasonable but incorrect guesses about category placement.

---

### **The Fix Strategy**

**Principle**: **Be explicit, not implicit** in system prompts.

**Bad Approach** ❌:
```
- transactions: transactions with amounts and categories
```
(Relies on LLM to guess structure)

**Good Approach** ✅:
```
- transactions: transactions (txn_id, account_id, posted_date, amount, 
                merchant, category_lvl1, category_lvl2)
  * category_lvl1 = broad category (examples: 'Housing', 'Food')
  * category_lvl2 = specific category (examples: 'Rent', 'Groceries')
  * For rent: category_lvl1 = 'Housing' AND category_lvl2 = 'Rent'
```
(Explicitly documents structure with examples and special cases)

---

## ✅ **Status**

- ✅ **Transaction table structure documented** with all columns
- ✅ **Category hierarchy explained** (`category_lvl1` vs `category_lvl2`)
- ✅ **Concrete examples added** for rent, groceries, gas, income
- ✅ **3 new query examples added** (rent transactions, monthly rent, spending by category)
- ✅ No linting errors
- ✅ Ready for testing

**NL2SQL should now generate correct SQL for transaction queries!** 🎉

---

## 📋 **Lessons Learned**

### **For Future Schema Documentation**

When documenting database tables in system prompts:

1. ✅ **List ALL column names explicitly** (not just "with various fields")
2. ✅ **Explain any hierarchical structures** (e.g., `category_lvl1` vs `category_lvl2`)
3. ✅ **Provide concrete examples** for each column with real values
4. ✅ **Document special cases** (e.g., "For rent queries, use `category_lvl2 = 'Rent'`")
5. ✅ **Add query examples** for common use cases
6. ✅ **Test with edge cases** (not just the "happy path")

**General Rule**: If a human would need clarification, the LLM definitely needs it documented!

---

**Fixed**: November 2, 2025  
**Issue**: NL2SQL generating wrong SQL for transaction category queries  
**Resolution**: Documented transaction table structure with category hierarchy and examples  
**File**: `backend/tools/nl2sql_tool.py`  
**Impact**: CRITICAL - fixes all transaction-based queries (rent, groceries, spending analysis, etc.)

