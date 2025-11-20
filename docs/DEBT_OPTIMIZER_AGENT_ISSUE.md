# Debt Optimizer Tool Agent Issue 🔴

**Date**: November 2, 2025  
**Issue**: Agent calls debt_optimizer 8 times and fails to calculate payoff with doubled payment

---

## 🐛 **The Problem**

**User Question**: "If I double my monthly payment, how soon can I pay off my student loan?"

**Current Monthly Payment**: $259.11  
**Doubled Payment**: $518.22

**Agent Behavior**:
```
Tool #3: debt_optimizer
Tool #4: debt_optimizer
Tool #5: debt_optimizer
Tool #6: debt_optimizer
Tool #7: debt_optimizer
Tool #8: debt_optimizer
```

**Agent Response**: "It seems there was an issue with processing your request..."

---

## 🔍 **Investigation Results**

### **Tool Works Correctly** ✅

Testing the tool directly:
```python
tool.execute(
    customer_id="C001",
    scenario_type="extra_payment",
    extra_payment=259.11  # Double the payment (add $259.11 to current $259.11)
)
```

**Results**:
- Status: success ✅
- New Payment: $518.22 ✅ (CORRECT!)
- Months to Payoff: ~52 months ✅
- Total Interest: $1,953.03 ✅
- Total Savings: $39,990.61 ✅

**Tool is working perfectly!**

---

## 🔍 **Root Causes**

### **Cause 1: Agent Doesn't Know How to Use the Tool Properly** 🔴

The agent is trying to calculate "double my payment" but:
1. It doesn't realize it needs to use `scenario_type="extra_payment"`
2. It doesn't know that `extra_payment=$259.11` will add to the current payment
3. It might be using `scenario_type="target_payoff"` incorrectly

---

### **Cause 2: Agent Hits Infinite Loop** 🔴

Looking at the terminal output:
- Agent calls tool multiple times (Tools #3-#8)
- This matches the infinite loop pattern we fixed earlier
- BUT the agent still isn't understanding when to STOP

**Why**:
- The tool returns complex nested JSON
- Agent might not be parsing the response correctly
- Agent tries again, gets same result, tries again...

---

### **Cause 3: Ambiguous Prompt Instructions** 🟡

The prompt says:
```
- scenario_type: current/extra_payment/refinance/avalanche/snowball/consolidate/target_payoff  
- extra_payment: additional monthly payment (default: 0)  
```

**Problem**: When user says "double my payment", agent might think:
- Should I use `target_payoff` with some calculated months?
- Should I use `extra_payment` with $259.11?
- Should I calculate what "double" means first?

---

## ✅ **Solutions Required**

### **Solution 1: Add Clear Examples to Prompt** (HIGH PRIORITY)

Add to `fin-adv-v2.txt` in the debt_optimizer section:

```markdown
### Common User Questions & How to Handle:

**"If I double my monthly payment, how soon can I pay off [debt]?"**
→ Use scenario_type="extra_payment"
→ Set extra_payment = current monthly payment amount
→ Example: If current payment is $259.11, use extra_payment=259.11 (total payment becomes $518.22)

**"What if I pay an extra $X per month?"**
→ Use scenario_type="extra_payment"
→ Set extra_payment = X

**"How much do I need to pay to pay off in X months?"**
→ Use scenario_type="target_payoff"
→ Set target_payoff_months = X

**"What's my current payoff timeline?"**
→ Use scenario_type="current"
→ No extra parameters needed
```

---

### **Solution 2: Improve Tool Response Format** (MEDIUM PRIORITY)

The tool returns data in nested structures:
- `result["debts"][0]["extra_payment_details"]["months_to_payoff"]`

This is hard for the agent to parse. Consider flattening:

```python
# Add top-level convenience fields
if scenario_type == "extra_payment":
    results["total_payoff_months"] = debts[0]["extra_payment_details"]["months_to_payoff"]
    results["total_interest_paid"] = debts[0]["extra_payment_details"]["total_interest"]
    results["total_savings"] = debts[0]["extra_payment_details"]["total_savings"]
```

---

### **Solution 3: Add Validation to Prevent Infinite Loops** (HIGH PRIORITY)

The agent is calling the tool 6+ times. This shouldn't happen.

**Add to prompt** (already added but needs reinforcement):
```markdown
### CRITICAL: Tool Call Limits for debt_optimizer

1. **Call the tool ONCE per scenario**
2. **If tool returns success, USE the results immediately**
3. **Do NOT call the tool again with the same parameters**
4. **If unsure about parameters, ask user for clarification BEFORE calling tool**

Example CORRECT:
- User: "If I double my payment..."
- You: Calculate extra_payment = current_payment
- Call tool ONCE with extra_payment=259.11
- Use the results to answer
- STOP

Example WRONG:
- Call tool
- Get results but don't understand them
- Call tool again  ← WRONG!
- Call tool again  ← WRONG!
- Give up          ← WRONG!
```

---

### **Solution 4: Enhance Agent's Understanding of Context** (MEDIUM PRIORITY)

With chat history now implemented, the agent should:
1. Remember the current monthly payment from earlier in the conversation
2. Know what "double" means in that context
3. Calculate: double of $259.11 = $518.22 = current + extra $259.11

**Already Fixed**: Chat history is now working ✅

**Still Needed**: Agent needs to better understand how to translate user intent into tool parameters

---

## 🧪 **Testing Plan**

### **Test 1: Direct Instruction**
```
User: "Calculate my payoff if I add an extra $259 to my monthly payment"
Expected: Agent uses scenario_type="extra_payment", extra_payment=259
```

### **Test 2: Contextual (Double)**
```
Chat Turn 1:
User: "What's my current monthly payment?"
Agent: "$259.11"

Chat Turn 2:
User: "If I double my payment, how soon can I pay it off?"
Expected: Agent calculates 259.11 * 2 = 518.22
Expected: Agent realizes extra_payment = 259.11
Expected: Agent calls tool ONCE
Expected: Agent provides answer
```

### **Test 3: Ambiguous**
```
User: "How quickly can I pay off my loan if I pay more?"
Expected: Agent asks "How much extra would you like to pay per month?"
```

---

## 📁 **Files to Modify**

1. **`backend/prompts/fin-adv-v2.txt`**:
   - Add detailed examples for common debt payoff questions
   - Add explicit instructions for "double payment" scenario
   - Reinforce "call tool once, then stop" rule

2. **`backend/tools/debt_optimizer_tool.py`** (Optional):
   - Add convenience fields to top level of response
   - Make response easier for agent to parse

---

## 🎯 **Priority Actions**

1. **HIGH**: Add clear examples to agent prompt for "double payment" scenario
2. **HIGH**: Reinforce "call tool once" rule in prompt
3. **MEDIUM**: Flatten tool response structure for easier parsing
4. **LOW**: Add explicit error messages when tool is called repeatedly

---

**Status**: 🔴 CRITICAL - Agent cannot handle basic debt payoff questions  
**Impact**: Core functionality broken for users asking about payment scenarios  
**ETA**: 1-2 hours to fix (mostly prompt engineering)

