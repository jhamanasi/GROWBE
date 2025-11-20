# Stress Test Queries for Growbe FinAgent

Comprehensive list of queries to test the financial advisory chatbot across all features.

## **1. Debt & Loan Questions**

### Basic Debt Information
- [ ] What type of debt do I have?
- [ ] What is the term months for my student loan?
- [ ] What is the original tenure period for my student loan?
- [ ] When did I take out my student loan?
- [ ] What was my original loan amount?
- [ ] How much do I still owe on my student loan?
- [ ] What's my interest rate on the student loan?
- [ ] What's my minimum monthly payment?
- [ ] Is my loan current or in default?
- [ ] How much principal have I paid off so far?

### Advanced Debt Queries
- [ ] Show me all my debts with their interest rates
- [ ] What's my total debt across all loans?
- [ ] Which of my loans has the highest interest rate?
- [ ] Compare my student loan to my credit card debt
- [ ] What percentage of my original loan have I paid off?

## **2. Account & Balance Questions**

### Basic Account Information
- [ ] What are my account balances?
- [ ] How many accounts do I have?
- [ ] What types of accounts do I have?
- [ ] Which bank is my checking account with?
- [ ] What's my total balance across all accounts?
- [ ] When did I open my savings account?

### Advanced Account Queries
- [ ] Show me all my accounts sorted by balance
- [ ] What's my largest account balance?
- [ ] Compare my checking vs savings balance
- [ ] Which accounts are with Chase?
- [ ] What's the interest rate on my savings account?

## **3. Transaction Questions**

### Basic Transactions
- [ ] Show me my recent transactions
- [ ] What did I spend at Starbucks last month?
- [ ] How much did I spend on groceries?
- [ ] What's my biggest expense this month?
- [ ] Show me all transactions over $100

### Advanced Transaction Analysis
- [ ] What's my average daily spending?
- [ ] Compare my spending this month vs last month
- [ ] What percentage of my income goes to dining out?
- [ ] Show me my top 5 expenses by category
- [ ] How much have I spent on entertainment?

## **4. Credit Score Questions**

### Basic Credit Information
- [ ] What's my FICO score?
- [ ] What's my credit utilization?
- [ ] How has my credit score changed over time?
- [ ] What's my credit limit?
- [ ] When was my credit score last updated?

### Advanced Credit Queries
- [ ] Is my credit score improving or declining?
- [ ] What factors are affecting my credit score?
- [ ] How does my credit utilization compare to recommendations?
- [ ] Show me my credit history for the last 6 months

## **5. Income & Employment**

### Basic Employment Information
- [ ] What's my annual salary?
- [ ] Where do I work?
- [ ] What's my employment status?
- [ ] When did I start my current job?
- [ ] What's my monthly income?

### Advanced Employment Queries
- [ ] What's my hourly rate equivalent?
- [ ] How much do I make after taxes?
- [ ] What's my take-home pay?
- [ ] Show me my income sources

## **6. Asset Questions**

### Basic Asset Information
- [ ] What assets do I have?
- [ ] How much cash do I have?
- [ ] What investments do I have?
- [ ] What's my total net worth?
- [ ] Show me my liquid assets

### Advanced Asset Queries
- [ ] What's my asset-to-debt ratio?
- [ ] How much of my assets are liquid vs illiquid?
- [ ] What percentage of my net worth is in investments?
- [ ] Compare my assets to my liabilities

## **7. Complex Calculation Questions**

### Payment Scenarios
- [ ] How much should I pay monthly to pay off my loan in 1 year?
- [ ] How much interest will I save if I pay $200 extra per month?
- [ ] What happens if I double my monthly payment?
- [ ] How long will it take to pay off my loan at the current rate?
- [ ] If I pay $500 per month, when will my loan be paid off?

### Refinancing Questions
- [ ] Should I refinance my student loan?
- [ ] What if I refinance at 3% interest rate?
- [ ] How much would I save by refinancing?
- [ ] Compare current loan vs refinancing at 2.5%
- [ ] Is refinancing worth the fees?

### Consolidation Questions
- [ ] What if I consolidate all my debts?
- [ ] Should I combine my student loans?
- [ ] How much would consolidation save me?
- [ ] Compare individual loans vs consolidated loan

## **8. Comparison Questions**

### Financial Ratios
- [ ] Compare my debt to my income
- [ ] What's my debt-to-income ratio?
- [ ] Compare my spending on dining vs groceries
- [ ] How much am I saving vs spending each month?
- [ ] What percentage of my income goes to debt payments?

### Benchmarking
- [ ] How does my FICO score compare to average?
- [ ] Is my interest rate competitive?
- [ ] Am I saving enough for my age?
- [ ] Compare my student loan terms to standard terms

## **9. Synonym Testing (Edge Cases)**

### Alternative Phrasings - Tenure/Term
- [ ] How long is my loan period?
- [ ] What's the repayment period for my student loan?
- [ ] What's the duration of my loan?
- [ ] How many months is my loan for?
- [ ] What's the loan tenure?

### Alternative Phrasings - Balance
- [ ] How much do I still need to pay?
- [ ] What's my remaining balance?
- [ ] How much is left on my loan?
- [ ] What's my outstanding amount?
- [ ] How much debt remains?

### Alternative Phrasings - Payment
- [ ] What's my required monthly payment?
- [ ] How much do I need to pay each month?
- [ ] What's my monthly obligation?
- [ ] What's the minimum I have to pay?

## **10. Goal-Oriented Questions**

### Financial Planning
- [ ] How can I pay off my debt faster?
- [ ] What's the best strategy to improve my credit score?
- [ ] How much should I save each month?
- [ ] When can I afford to buy a house?
- [ ] Should I focus on debt or savings?

### Budget Questions
- [ ] Am I spending too much on dining out?
- [ ] How can I reduce my monthly expenses?
- [ ] What's my biggest financial weakness?
- [ ] Where should I cut back?
- [ ] How can I increase my savings rate?

## **11. Multi-Step Questions (Complex)**

- [ ] Show me my total debt, then calculate how to pay it off in 2 years
- [ ] What's my credit score and how can I improve it?
- [ ] List all my debts and recommend which to pay off first
- [ ] Show my accounts and suggest how to optimize them
- [ ] What's my net worth and how does debt affect it?

## **12. Error Handling & Edge Cases**

### Ambiguous Questions
- [ ] Tell me about my finances
- [ ] What should I know?
- [ ] Help me with money
- [ ] I need financial advice
- [ ] What can you do?

### Missing Data
- [ ] What's my mortgage balance? (if customer doesn't have one)
- [ ] Show me my car loan (if customer doesn't have one)
- [ ] What's my spouse's income? (if not tracked)

### Invalid Questions
- [ ] Can you transfer money for me?
- [ ] Approve my loan application
- [ ] Change my interest rate
- [ ] Delete my debt

## **Test Results Format**

For each question, record:
- ✅ **Pass**: Agent answered correctly with accurate data
- ⚠️ **Partial**: Agent answered but data incomplete or formatting issues
- ❌ **Fail**: Agent couldn't answer or gave incorrect information
- 🐛 **Error**: Technical error occurred

### Example Result:
```
✅ "What type of debt do I have?"
   - Response: "You have a Student loan with a current balance of $23,816.32..."
   - SQL Query: SELECT * FROM debts_loans WHERE customer_id = 'C001'
   - Execution Time: 0.15s

❌ "What's my mortgage balance?"
   - Response: "I don't have access to mortgage information"
   - Issue: Should clarify customer doesn't have a mortgage
```

## **Testing Instructions**

1. **Test with Different Customer IDs**: C001, C002, C003, etc.
2. **Test in Order**: Start with basic queries, progress to complex
3. **Record All SQL Queries**: Expand the SQL dropdown and verify queries
4. **Check Math Formulas**: Verify LaTeX rendering for calculations
5. **Test Streaming**: Ensure responses stream properly
6. **Test Error Handling**: Try invalid customer IDs and edge cases
7. **Performance**: Note response times for each query type

## **Success Criteria**

- [ ] 90%+ pass rate on basic questions (sections 1-6)
- [ ] 80%+ pass rate on complex calculations (section 7)
- [ ] 75%+ pass rate on comparisons (section 8)
- [ ] 95%+ pass rate on synonym testing (section 9)
- [ ] 70%+ pass rate on goal-oriented questions (section 10)
- [ ] Proper error handling for all invalid/missing data scenarios
- [ ] SQL queries generated for all database questions
- [ ] Math formulas display correctly with KaTeX
- [ ] Average response time < 3 seconds
- [ ] No crashes or infinite loops

---

**Test Date**: _____________
**Tester**: _____________
**Overall Score**: ______ / 100 questions passed
