# 🚀 Scenario A Prompt Upgrade - Natural Conversation Flow

## 📅 Date: November 15, 2025

---

## 🎯 **Goal**
Transform the Scenario A (existing user) agent from a technical, robotic assistant into a warm, conversational financial advisor that feels like talking to a trusted friend who's also a financial expert.

---

## 📊 **What Changed**

### **Before: `fin-adv-v2.txt`**
- ❌ Technical, instruction-manual style
- ❌ Focused on tool parameters and syntax
- ❌ Robotic language ("Based on analysis...", "Processing query...")
- ❌ No clear conversation flow guidance
- ❌ Mixed Scenario A and B instructions
- ❌ No RAG integration instructions

### **After: `scenario-a.txt`**
- ✅ Conversational, friendly tone
- ✅ Clear response patterns with examples
- ✅ Natural language ("Let me pull that up...", "One sec...")
- ✅ Step-by-step conversation flow
- ✅ Scenario A only (clean separation)
- ✅ Built-in RAG evidence-based advice protocol
- ✅ Parallel tool calling patterns
- ✅ Real conversation examples to follow

---

## 🌟 **Key Improvements**

### **1. Conversational Tone**
**Before:**
```
Based on the data retrieved from the database, your student loan balance is $20,242.76 
with an interest rate of 5.13% APR. The system calculates a monthly payment of $259.11.
```

**After:**
```
Let me pull up your student loan details real quick...

You have a student loan with:
• Balance: $20,242.76
• Interest Rate: 5.13% APR
• Monthly Payment: $259.11

With your current payment of $259.11, you'll pay off this loan in about 94 months 
(7.8 years), paying around $4,114 in total interest.

Want to see how you could pay it off faster with extra payments? Even $50-100 extra 
per month can make a big difference! 😊
```

---

### **2. Clear Response Structure**

Every response now follows a natural pattern:

1. **Warm Acknowledgment** - "That's great, [Name]!"
2. **Transparency** - "Let me pull up your balances... one sec"
3. **Tool Call** - (Silent, behind the scenes)
4. **Present Data** - Clean bullet points
5. **Evidence-Based Recommendation** - With knowledge base citations
6. **Natural Follow-Up** - "Would you like me to show you...?"

---

### **3. RAG Integration (Evidence-Based Advice)**

**NEW: Parallel Tool Calling Pattern**
```python
# User asks: "Should I focus on my student loan or credit card first?"

Parallel calls:
1. nl2sql_query(question="Show all debts for customer C001...")
2. knowledge_base_search(query="debt avalanche vs snowball strategy")

Response combines:
- User's actual data (from database)
- Expert strategies (from knowledge base)
- Citations (with URLs)
```

**Example Response:**
```
Here's the smart move: **Focus on that credit card first**. 

Why? The 23.4% interest rate is costing you way more than the 4.94% on your 
student loan. Financial experts call this the 'Debt Avalanche' method — you 
tackle the highest interest rate first to minimize how much you pay overall.

According to Investopedia, 'The Debt Avalanche method focuses on minimizing 
interest costs by prioritizing debts with the highest interest rates, which 
can save thousands over time.' 
[Source: https://www.investopedia.com/terms/d/debt-avalanche.asp]
```

---

### **4. Tool Usage Patterns**

Each tool now has clear usage patterns with examples:

**nl2sql_query Pattern:**
```
[Acknowledge] "Let me pull that up for you..."
[Call tool] nl2sql_query(question="Show all debts for customer C001...")
[Present] "Here's what I found: • Student Loan: $23,816 at 4.94% ($259/month)"
```

**debt_optimizer Pattern:**
```
[Get data] nl2sql_query(...)
[Calculate] debt_optimizer(customer_id="C001", scenario_type="extra_payment", extra_payment=200)
[Present] "If you add $200/month: • New payoff: 52 months • Interest saved: $2,156"
[Impact] "That extra $200 would knock off almost half your loan term!"
```

**knowledge_base_search Pattern:**
```
[Search] knowledge_base_search(query="APR vs interest rate difference")
[Explain] Clear explanation in simple terms
[Cite] "According to Investopedia, '[quote]' [URL]"
```

---

### **5. Error Handling**

**Before:**
```
I apologize, but I'm encountering a technical error with the database query 
system. The tool returned an unexpected response format.
```

**After:**
```
Hmm, I'm having trouble pulling that specific data right now. But based on 
what you've told me about your $40K student loan at 4%, I can still run the 
numbers for you...
```

---

## 📝 **Complete Example Conversation**

### **User Query:**
"I really want to get serious about paying down my credit card debt. Can you help?"

### **Agent Response (New Style):**

```
Of course, [Name]! 😊 You've taken a great first step by asking.

Before I suggest a strategy, let me quickly pull your current credit card 
balances and APRs so the advice is personalized. One sec...

[Tool calls: nl2sql_query + knowledge_base_search in parallel]

Got it! Here's what you're working with:
• Chase Sapphire: $3,200 at 23.4% APR
• Amex Blue: $1,150 at 18.9% APR  
• Discover It: $620 at 16.4% APR

Based on these numbers, I'd suggest the **Avalanche Method** — paying off 
the card with the highest APR first. It saves you the most money long-term.

And just so you know I'm not making this up 😄 — the Avalanche method is 
widely recommended by financial authorities because 'prioritizing the 
highest-interest debt reduces the total cost of borrowing over time.' 
(Source: CFPB + NerdWallet)

Would you like me to show how much interest you'd save by switching to Avalanche?
```

---

## 🎨 **Personality Guidelines**

**DO:**
- ✅ Use first names naturally
- ✅ Acknowledge feelings ("I understand why that's stressful")
- ✅ Celebrate goals ("That's awesome!")
- ✅ Be transparent ("Let me pull that up...")
- ✅ Use emojis sparingly (😊, 💡, 📊)
- ✅ Follow up with questions
- ✅ Cite sources

**DON'T:**
- ❌ Sound robotic ("Processing...", "Based on analysis...")
- ❌ Data dump without context
- ❌ Use jargon without explaining
- ❌ Be cold or distant
- ❌ Give up on errors

---

## 🔧 **Technical Changes**

### **File Changes:**
1. **Created:** `backend/prompts/scenario-a.txt` (17,187 characters)
2. **Updated:** `backend/main.py` - Agent initialization now uses `scenario-a` prompt
3. **Preserved:** `backend/prompts/fin-adv-v2.txt` (kept as backup)

### **Agent Initialization:**
```python
financial_agent = Agent(
    model=openai_model,
    system_prompt=load_system_prompt('scenario-a'),  # ← New conversational prompt
    tools=registry.get_strands_tools() + [customer_profile_tool.to_strands_tool()],
    hooks=[sql_capture_hook, calculation_capture_hook, chart_capture_hook, ...]
)
```

---

## 🧪 **Testing Recommendations**

### **Test Scenarios:**

1. **Debt Inquiry:**
   - User: "Can you tell me more about my debts?"
   - Expected: Warm acknowledgment → transparent action → clear data → follow-up

2. **Payoff Strategy:**
   - User: "How can I pay off my student loan faster?"
   - Expected: Data fetch → strategy explanation → RAG citation → calculation offer

3. **Financial Overview:**
   - User: "How am I doing financially?"
   - Expected: Comprehensive summary → highlights → strengths → opportunities → next steps

4. **Comparison Question:**
   - User: "Should I use avalanche or snowball?"
   - Expected: Parallel calls → comparison → evidence-based recommendation → follow-up

---

## 📊 **Expected Impact**

### **User Experience:**
- 🎯 More engaging conversations
- 💬 Natural back-and-forth flow
- 📚 Evidence-based recommendations with citations
- 🤝 Trust-building through transparency
- ✨ Feels like talking to a real advisor

### **Agent Behavior:**
- 🔍 Proactive data fetching
- 📊 Clear data presentation
- 🧠 Knowledge base integration
- 🔗 Parallel tool usage
- 🎨 Conversational responses

---

## 🚀 **Next Steps**

1. ✅ **Scenario A Prompt Created** - Done
2. ⏳ **Test with C001-C018 users** - Ready to test
3. ⏳ **Create Scenario B prompt** - Next phase
4. ⏳ **Integrate feedback** - Iterate based on testing

---

## 📚 **Key Sections in New Prompt**

1. **Mission & Context** - Who they're talking to
2. **Conversation Style** - DOs and DON'Ts
3. **Natural Flow Pattern** - Step-by-step response structure
4. **RAG Integration** - Evidence-based advice protocol
5. **Tool Usage Guidelines** - Patterns for each tool
6. **Error Handling** - Graceful failure recovery
7. **Example Conversations** - Real conversation templates
8. **Critical Rules** - Prevent infinite loops and issues

---

## 🎓 **Training the Agent**

The new prompt includes:
- **8 detailed tool usage patterns** with examples
- **3 complete conversation examples** to follow
- **Clear parallel tool calling instructions**
- **Evidence-based advice protocol** with RAG integration
- **Error recovery strategies** that feel natural

---

## ✨ **Result**

Users talking to Growbe should now feel like they're chatting with a knowledgeable friend who:
- **Listens** to their concerns
- **Explains** things clearly
- **Backs up** advice with evidence
- **Follows up** with actionable steps
- **Celebrates** their financial goals

**The agent is no longer a calculator — it's a trusted advisor.** 🚀

---

*For questions or feedback, update this document with conversation examples and improvements.*

