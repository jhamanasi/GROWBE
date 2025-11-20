# Debt Optimizer Tool - Comprehensive Stress Test Queries

Test all scenarios and debt types systematically for both existing users (Scenario A) and new users (Scenario B).

---

## 🎯 SCENARIO A: EXISTING USERS (Database Customers C001-C018)

### **Student Loans**

#### Basic Calculations
1. **Current Payment**: "What's my current monthly payment for my student loan?" (C001, C002, C006-C009, C011, C013, C014, C017, C018)
2. **Loan Details**: "Tell me about my student loan - balance, rate, and term." (Any customer with student loans)
3. **Total Interest**: "How much total interest will I pay on my student loan if I stick to minimum payments?" (C001)

#### Extra Payment Scenarios
4. **Extra $100**: "If I pay an extra $100 per month on my student loan, how much faster will I pay it off?" (C001)
5. **Extra $250**: "How much interest would I save by adding $250/month to my student loan payment?" (C002)
6. **Extra $500**: "If I add $500 extra per month, when will my student loan be paid off?" (C006)

#### Target Payoff Scenarios
7. **1 Year Payoff**: "How much should I pay monthly to pay off my student loan in 1 year?" (C018 - smaller balance)
8. **2 Year Payoff**: "What monthly payment do I need to eliminate my student loans in 24 months?" (C001)
9. **3 Year Payoff**: "I want to be debt-free from student loans in 3 years. What's the required payment?" (C013 - multiple loans)

#### Refinancing Scenarios
10. **Lower Rate**: "If I refinance my student loan to 3.5%, how much would I save?" (C001, rate from 5.13% to 3.5%)
11. **Shorter Term**: "What if I refinance to 10 years at 4.0%? Show me the comparison." (C002, current 20 years to 10 years)
12. **Longer Term**: "If I refinance to 25 years at 4.5%, how does my payment change?" (C008)

---

### **Auto Loans**

#### Basic Calculations
13. **Auto Loan Payment**: "What's my current auto loan payment?" (C003, C004, C011, C015)
14. **Auto Loan Balance**: "How much do I owe on my car?" (C003)
15. **Auto Loan Rate**: "What interest rate am I paying on my auto loan?" (C004)

#### Extra Payment & Target Payoff
16. **Extra $200 Auto**: "If I pay $200 extra per month on my auto loan, when will it be paid off?" (C003)
17. **6 Month Payoff**: "How much do I need to pay monthly to pay off my car in 6 months?" (C015 - check if feasible)

#### Refinancing Auto Loans
18. **Auto Refi**: "If I refinance my auto loan to 4.5%, how much would I save monthly?" (C004, from 11.93%)

---

### **Credit Cards**

#### Basic Calculations
19. **Credit Card Details**: "Tell me about my credit card debt." (C003, C005, C009-C010, C012, C016, C017)
20. **Minimum Payment**: "What's the minimum payment on my credit card?" (C010)
21. **CC Balance**: "How much do I owe on all my credit cards?" (C009 - has 2 cards)

#### Extra Payment & Payoff
22. **CC Extra $100**: "If I pay $100/month on my credit card, how long until it's paid off?" (C005)
23. **CC Target 12 Months**: "How much should I pay to clear my credit card debt in 1 year?" (C012 - low balance)
24. **CC Target 24 Months**: "What payment would clear my credit cards in 2 years?" (C016 - multiple cards)

#### Promotional Rates
25. **0% Promo**: "I have a 0% APR promotional rate for 12 months on a balance transfer. If I transfer my $2,000 balance and pay $200/month, will I pay it off before the promo ends?" (Hypothetical with C010's balance)

---

### **Multiple Debts - Mixed Types**

#### Avalanche Strategy
26. **Avalanche C003**: "Show me the avalanche method for all my debts with $300 extra per month." (C003: student + auto + credit card)
27. **Avalanche C009**: "Use the avalanche strategy to pay off my debts. I can add $400/month." (C009: student + 2 credit cards)

#### Snowball Strategy
28. **Snowball C003**: "Show me the snowball method for paying off my debts with $300 extra." (C003: student + auto + credit card)
29. **Snowball C016**: "I want to use the snowball method with $150 extra per month. How long until I'm debt-free?" (C016: 3 credit cards)

#### Consolidation
30. **Consolidate All C007**: "What if I consolidate both my student loans at 4.5%? Show me the savings." (C007: 2 student loans)
31. **Consolidate Mixed C003**: "Can I consolidate my student loan, auto loan, and credit card at 6.5%? Is it worth it?" (C003)
32. **Consolidate Cards C010**: "Should I consolidate my credit cards with a personal loan at 12%?" (C010: 2 credit cards)

#### Refinancing Multiple Debts
33. **Refi All Debts C011**: "If I refinance all my debts, what rate would make it worthwhile?" (C011: 2 student + 1 auto)
34. **Selective Refi C013**: "Which of my three student loans should I refinance?" (C013: 3 student loans with different rates)

---

## 🆕 SCENARIO B: NEW USERS (Hypothetical Debts)

### **Student Loans - Hypothetical**

#### Basic Hypothetical
35. **New Grad**: "I just graduated with $35,000 in student loans at 5.5% over 10 years. What's my monthly payment?"
36. **Large Loan**: "I have $80,000 student loan debt at 6.2% for 20 years. Show me the total interest I'll pay."
37. **Low Rate**: "My student loan is $25,000 at 3.8% for 15 years. What are my payments?"

#### Hypothetical Extra Payments
38. **Extra $150**: "On a $40,000 loan at 5% over 10 years, how much do I save with $150 extra per month?"
39. **Extra $500**: "I have $50,000 at 6% for 15 years. If I pay $500 extra, when will I be done?"

#### Hypothetical Target Payoff
40. **5 Year Goal**: "I want to pay off $30,000 (at 4.5%) in 5 years. What's my monthly payment?"
41. **Aggressive 2 Year**: "To pay off $20,000 at 5.5% in 2 years, how much per month?"

#### Hypothetical Refinancing
42. **Refi Comparison**: "I have $60,000 at 7% for 20 years. Compare this to refinancing at 4.5% for 15 years."
43. **Rate Shopping**: "Show me payment options for $45,000: 3%, 4%, 5%, and 6% all at 10 years."

---

### **Auto Loans - Hypothetical**

#### Basic Auto
44. **New Car**: "I'm buying a car for $30,000 at 5.5% for 5 years. What's my payment?"
45. **Used Car**: "Used car loan of $15,000 at 7.9% for 4 years. Monthly payment?"
46. **High Rate Auto**: "I got approved for $20,000 at 11% for 6 years. What will this cost me total?"

#### Auto Extra Payments
47. **Auto Extra $100**: "On a $25,000 car loan at 6% for 5 years, how much do I save with $100 extra monthly?"

#### Auto Target Payoff
48. **3 Year Auto Goal**: "I want to pay off my $18,000 car (at 5.2%) in 3 years. What payment?"

---

### **Credit Cards - Hypothetical**

#### Basic Credit Card
49. **High Balance CC**: "I have $8,000 in credit card debt at 22% APR. What's my minimum payment and how long to pay it off?"
50. **Medium Balance CC**: "Credit card balance of $3,500 at 18.5%. If I pay $150/month, how long until it's gone?"
51. **Low Balance CC**: "I owe $1,200 on a card at 24% APR. Paying $100/month - when am I done?"

#### CC with Promo Rates
52. **0% for 18 Months**: "I transferred $5,000 to a 0% APR card for 18 months, then it goes to 19.99%. Pay $300/month - will I clear it in promo period?"
53. **0% for 12 Months**: "Balance transfer of $3,000 at 0% for 12 months, then 21%. Paying $250/month - what's my savings?"

#### High-Interest CC Payoff
54. **Aggressive CC Pay**: "I have $6,000 at 26% APR. How much to pay monthly to clear it in 1 year?"
55. **Min Payment Trap**: "If I only pay minimum (2%) on $5,000 at 22%, how long and how much total?"

---

### **Personal Loans - Hypothetical**

#### Basic Personal
56. **Debt Consolidation Loan**: "I'm considering a $20,000 personal loan at 9% for 5 years. What's my payment?"
57. **Medical Debt**: "Medical bills totaling $12,000. Personal loan at 11% for 3 years. Monthly payment?"

#### Personal Loan Payoff
58. **Personal Extra Payment**: "On a $15,000 personal loan at 8% for 5 years, adding $200/month saves how much?"

---

### **Multiple Debts - Hypothetical**

#### Avalanche - Hypothetical
59. **3 Debts Avalanche**: "I have: $15,000 student at 5%, $8,000 credit card at 20%, $10,000 auto at 6%. Avalanche method with $500 extra?"
60. **5 Debts Avalanche**: "Debts: $25K student (4.5%), $5K CC (22%), $12K auto (7%), $3K CC (24%), $8K personal (9%). Avalanche with $600 extra?"

#### Snowball - Hypothetical
61. **3 Debts Snowball**: "Same debts as above, but use snowball method with $500 extra."
62. **5 Debts Snowball**: "Same 5 debts as #60, snowball with $600 extra. Which debt gets paid first?"

#### Consolidation - Hypothetical
63. **Consolidate 3 Debts**: "Consolidate $15K student (5%), $8K CC (20%), $10K auto (6%) into one loan at 7% for 7 years. Worth it?"
64. **Consolidate High-Interest**: "I have 3 credit cards: $4K (21%), $3K (24%), $5K (19%). Consolidate at 12% for 5 years?"

---

### **Complex Scenarios - Edge Cases**

#### Zero Interest
65. **0% Interest Loan**: "I have a $10,000 loan at 0% interest for 3 years. What's my payment?"
66. **Family Loan**: "Borrowed $5,000 from family at 0% interest. Paying $200/month - how long?"

#### Very Short Terms
67. **6 Month Loan**: "Need to pay off $3,000 in 6 months at 8%. What payment?"
68. **3 Month Payoff**: "Aggressively paying $2,000 debt in 3 months at 15%. Monthly payment?"

#### Very Long Terms
69. **30 Year Loan**: "If I take a $40,000 loan at 5.5% for 30 years, what's total interest?"

#### Near-Payoff Balances
70. **Almost Done**: "I have $500 left on a loan at 7%. One more payment or spread over 6 months?"

#### High-Rate, High-Balance
71. **Worst Case**: "$50,000 credit card debt at 29.99% APR. What's my path to payoff?"

#### Multiple Same Type
72. **3 Student Loans**: "I have 3 student loans: $20K (4%), $15K (5.5%), $10K (6%). Best strategy to pay them off?"

---

## 📊 TESTING CHECKLIST

### For Each Query, Verify:
- ✅ Correct debt type identified
- ✅ Accurate payment calculations
- ✅ Proper handling of extra payments
- ✅ Realistic payoff timelines
- ✅ Correct interest calculations
- ✅ Break-even analysis for refinancing
- ✅ LaTeX formulas displayed correctly
- ✅ calculation_steps rendered properly
- ✅ Recommendations are relevant
- ✅ Error handling for impossible scenarios

### Specific Validations:
- **Credit Cards**: Minimum payment at least 2% or $25
- **0% Promo Rates**: Correctly transitions to regular APR after promo
- **Avalanche**: Debts paid in order of highest to lowest interest rate
- **Snowball**: Debts paid in order of smallest to largest balance
- **Consolidation**: Accurately calculates weighted average and savings
- **Target Payoff**: Payment high enough to exceed interest
- **Refinancing**: Break-even months calculated correctly

---

## 🚨 KNOWN EDGE CASES TO TEST

### Edge Case 1: Payment Too Low
**Query**: "I have $10,000 at 20% APR. Can I pay it off with $50/month?"
**Expected**: Tool should warn that payment doesn't cover interest.

### Edge Case 2: Impossible Target
**Query**: "Pay off $50,000 at 8% in 1 month. What's the payment?"
**Expected**: Tool calculates accurately, agent warns it may be unrealistic.

### Edge Case 3: Multiple Debt Types for One Customer
**Query** (C003): "Show me all my debts and recommend best payoff strategy."
**Expected**: Lists student, auto, and credit card; recommends avalanche.

### Edge Case 4: No Debts Found
**Query** (C005 asking for student loans): "How much are my student loan payments?"
**Expected**: "No student loans found for customer C005."

### Edge Case 5: Refinancing Same Rate
**Query**: "What if I refinance my 5% loan to another 5% loan?"
**Expected**: Tool shows no savings, agent explains it's not beneficial.

---

## 🎬 SUGGESTED TESTING ORDER

1. **Start with Simple Student Loan Queries** (Basic, Extra Payment)
2. **Test Auto Loans** (C003, C004 for existing; hypothetical for new)
3. **Test Credit Cards** (Min payments, high rates, promo rates)
4. **Test Avalanche/Snowball** (Start with 2-3 debts, then complex)
5. **Test Consolidation & Refinancing** (Break-even analysis critical)
6. **Test Edge Cases** (0% rates, impossible targets, etc.)
7. **Test Formula Display** (Ensure LaTeX and calculation_steps render)

---

## ✅ SUCCESS CRITERIA

Tool is **production-ready** when:
- ✅ All 72 queries return accurate calculations
- ✅ No calculation errors or NaN values
- ✅ All formulas render correctly in frontend
- ✅ Recommendations are contextual and helpful
- ✅ Edge cases handled gracefully with clear messages
- ✅ Agent never falls back to manual calculations
- ✅ Both Scenario A and Scenario B work seamlessly
- ✅ Break-even analysis accurate for all refinancing scenarios
- ✅ Avalanche/snowball simulations mathematically correct

---

**Test Execution Date**: _________
**Tester**: _________
**Pass Rate**: _____ / 72
**Critical Failures**: _________

