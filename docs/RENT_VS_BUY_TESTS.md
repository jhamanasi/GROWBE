# Rent vs Buy Tool - Comprehensive Test Scenarios 🏠

## 📋 Tool Overview

The `rent_vs_buy` tool provides comprehensive housing decision analysis for the DMV area (DC, Maryland, Virginia) with:

- ✅ Monthly cost breakdown (PITI vs Rent)
- ✅ Long-term cost projections (5, 10, 20, 30 years)
- ✅ Break-even point calculation
- ✅ Home equity accumulation tracking
- ✅ Tax benefit calculations (mortgage interest + property tax deductions)
- ✅ Opportunity cost of down payment
- ✅ Sensitivity analysis (rates, down payment, appreciation)
- ✅ DMV region-specific defaults (DC/MD/VA)
- ✅ LaTeX formulas for frontend display

---

## 🧪 Test Scenarios

### **Scenario A: Existing User (Database Profile)**

#### Test 1: Basic Rent vs Buy - Maya (C001)
**User**: Maya (C001)  
**Income**: $73,000  
**Credit Score**: 686  
**Current Situation**: Renting at $2,100/month

**Query**: "Should I buy a $350,000 house or keep renting?"

**Expected Tool Call**:
```json
{
  "customer_id": "C001",
  "home_price": 350000,
  "monthly_rent": 2100,
  "region": "MD"
}
```

**Expected Analysis**:
- Monthly homeownership cost (with 20% down)
- Break-even analysis
- Tax benefits calculation
- 10-year projection
- Sensitivity scenarios

---

#### Test 2: First-Time Buyer with Low Down Payment - Aisha (C002)
**User**: Aisha (C002)  
**Income**: $51,000  
**Credit Score**: 580  
**Query**: "Can I afford a $280,000 home with only 5% down?"

**Expected Tool Call**:
```json
{
  "customer_id": "C002",
  "home_price": 280000,
  "down_payment_pct": 5,
  "monthly_rent": 1800,
  "region": "MD"
}
```

**Expected Warnings**:
- PMI requirement notice
- Higher monthly payment due to low down payment
- Impact of lower credit score on rates

---

#### Test 3: High-Income User Comparing Luxury Properties - Marcus (C010)
**User**: Marcus (C010)  
**Income**: $210,000  
**Credit Score**: 775  
**Query**: "I'm paying $4,500/month rent. Should I buy a $850,000 condo in DC?"

**Expected Tool Call**:
```json
{
  "customer_id": "C010",
  "home_price": 850000,
  "monthly_rent": 4500,
  "region": "DC",
  "hoa_monthly": 450,
  "down_payment_pct": 25
}
```

**Expected Features**:
- DC-specific tax rates (0.85%)
- HOA costs included
- Higher tax bracket benefits (32%)
- Luxury market appreciation

---

### **Scenario B: New User (Hypothetical)**

#### Test 4: Young Professional Exploring Options
**Query**: "I make $85,000/year and pay $2,300 rent. What if I buy a $400,000 house in Virginia?"

**Expected Tool Call**:
```json
{
  "home_price": 400000,
  "monthly_rent": 2300,
  "region": "VA",
  "down_payment_pct": 20,
  "mortgage_rate": 7.0,
  "analysis_years": 10
}
```

**Expected Analysis**:
- VA-specific defaults (0.8% property tax)
- Standard 30-year mortgage at current rates
- 10-year break-even analysis

---

#### Test 5: Comparing Short-Term vs Long-Term
**Query**: "I might move in 5 years. Should I buy a $320,000 house or rent at $2,000/month?"

**Expected Tool Call**:
```json
{
  "home_price": 320000,
  "monthly_rent": 2000,
  "analysis_years": 5,
  "region": "MD"
}
```

**Expected Recommendation**:
- Likely favor renting for short timeline
- Break-even analysis showing insufficient time
- Transaction costs warning

---

#### Test 6: Different Down Payment Scenarios
**Query**: "Compare 10% vs 20% down payment on a $450,000 home"

**Expected Tool Call** (agent should call twice or use sensitivity):
```json
{
  "home_price": 450000,
  "monthly_rent": 2400,
  "down_payment_pct": 10,
  "run_sensitivity": true
}
```

**Expected Output**:
- Base scenario with 10% down
- Sensitivity showing 20% down alternative
- PMI impact highlighted
- Cash flow comparison

---

#### Test 7: High Mortgage Rate Environment
**Query**: "With 7.5% interest rates, does it still make sense to buy a $375,000 home?"

**Expected Tool Call**:
```json
{
  "home_price": 375000,
  "monthly_rent": 2200,
  "mortgage_rate": 7.5,
  "region": "MD"
}
```

**Expected Analysis**:
- Higher monthly payment due to rate
- Extended break-even period
- Sensitivity showing rate drop scenario

---

#### Test 8: Condo vs House (HOA Considerations)
**Query**: "Should I buy a $380,000 condo with $300 HOA or rent for $2,100?"

**Expected Tool Call**:
```json
{
  "home_price": 380000,
  "monthly_rent": 2100,
  "hoa_monthly": 300,
  "maintenance_pct": 0.5,
  "region": "MD"
}
```

**Expected Features**:
- HOA included in monthly costs
- Lower maintenance % for condo (0.5% vs 1% for house)
- Clear cost breakdown

---

#### Test 9: Investment Property Analysis
**Query**: "Would it be worth buying a $320,000 rental property if I can get $2,400/month rent?"

**Expected Tool Call**:
```json
{
  "home_price": 320000,
  "monthly_rent": 2400,
  "analysis_years": 20,
  "region": "VA"
}
```

**Note**: Tool will show break-even from owner perspective (if they were living there)

---

#### Test 10: Sensitivity Analysis Deep Dive
**Query**: "Show me all scenarios for a $400,000 home purchase - different rates, down payments, and appreciation"

**Expected Tool Call**:
```json
{
  "home_price": 400000,
  "monthly_rent": 2300,
  "run_sensitivity": true,
  "analysis_years": 10
}
```

**Expected Sensitivity Scenarios**:
1. Base case
2. Higher interest rate (+1%)
3. Lower down payment (10%)
4. Lower appreciation (2%)

---

## 🎯 Edge Cases to Test

### Edge Case 1: Zero Down Payment (100% Financing)
**Query**: "Can I buy with 0% down using a VA loan?"

```json
{
  "home_price": 300000,
  "down_payment_pct": 0,
  "monthly_rent": 1900,
  "closing_costs_pct": 0
}
```

**Expected**: Tool should handle gracefully, show high monthly payment

---

### Edge Case 2: Very High Property Tax (DC)
**Query**: "Analyze a $700,000 home in DC"

```json
{
  "home_price": 700000,
  "monthly_rent": 3500,
  "region": "DC",
  "property_tax_rate": 0.85
}
```

**Expected**: DC defaults applied, accurate tax calculations

---

### Edge Case 3: Long-Term Analysis (30 years)
**Query**: "Compare rent vs buy over 30 years for a $350,000 home"

```json
{
  "home_price": 350000,
  "monthly_rent": 2000,
  "analysis_years": 30
}
```

**Expected**: Full mortgage payoff shown, significant equity accumulation

---

### Edge Case 4: Negative Appreciation Market
**Query**: "What if home prices decrease by 1% annually?"

```json
{
  "home_price": 400000,
  "monthly_rent": 2300,
  "appreciation_rate": -1.0
}
```

**Expected**: Negative equity scenarios, extended break-even, caution recommendations

---

### Edge Case 5: Very Low Interest Rate (Historical)
**Query**: "If I locked in a 3% rate, how does that change things?"

```json
{
  "home_price": 350000,
  "monthly_rent": 2100,
  "mortgage_rate": 3.0
}
```

**Expected**: Much lower monthly payment, faster break-even

---

## ✅ Validation Checklist

For **each test**, verify:

### **Calculation Accuracy**
- [ ] Monthly P&I uses correct amortization formula
- [ ] Property tax calculated on appreciated home value annually
- [ ] Tax benefits properly calculated (mortgage interest + property tax)
- [ ] Opportunity cost of down payment included
- [ ] Selling costs factored into net proceeds

### **Frontend Display**
- [ ] **Calculation dropdown appears** with blue styling
- [ ] LaTeX formulas render correctly
- [ ] Step-by-step breakdown shows all calculations
- [ ] Collapsed by default, expands on click

### **Agent Response Quality**
- [ ] Clean summary without inline formulas
- [ ] Break-even year clearly stated
- [ ] Monthly comparison highlighted
- [ ] Recommendations are actionable
- [ ] Tax benefits explained

### **Regional Defaults**
- [ ] DC: 0.85% property tax, $650k median, $2,800 rent
- [ ] MD: 1.1% property tax, $425k median, $2,100 rent
- [ ] VA: 0.8% property tax, $475k median, $2,300 rent

### **Sensitivity Analysis**
- [ ] 3 sensitivity scenarios generated when enabled
- [ ] Higher rate scenario shows impact
- [ ] Lower down payment scenario includes PMI note
- [ ] Lower appreciation scenario warns of risk

---

## 📊 Sample Expected Output Structure

```json
{
  "status": "success",
  "scenario_type": "rent_vs_buy",
  "analysis_years": 10,
  
  "upfront_costs": {
    "home_price": 350000,
    "down_payment": 70000,
    "down_payment_pct": 20,
    "closing_costs": 10500,
    "total_upfront": 80500
  },
  
  "monthly_comparison": {
    "rent": {
      "base_rent": 2100,
      "renters_insurance": 25,
      "total": 2125
    },
    "own": {
      "principal_interest": 1856,
      "property_tax": 321,
      "insurance": 125,
      "hoa": 0,
      "maintenance": 292,
      "piti_total": 2302,
      "all_costs_total": 2594,
      "tax_benefit": 167,
      "effective_cost": 2427
    },
    "monthly_difference": 302
  },
  
  "break_even": {
    "break_even_year": 7,
    "message": "Buying breaks even in year 7"
  },
  
  "projections": {
    "final_year": 10,
    "final_home_value": 483195,
    "final_equity": 283195,
    "total_rent_paid": 263542,
    "total_own_costs": 310840,
    "net_proceeds_if_sold": 254216
  },
  
  "calculation_steps": [...],
  "latex_formulas": [...],
  "recommendations": [...]
}
```

---

## 🚀 Integration with Main System

### **1. Tool Registration**
Tool auto-discovered by tool_manager.py ✅

### **2. Agent Prompt Update**
Add tool description to `fin-adv-v2.txt`:
```
rent_vs_buy Tool:
- Compare renting vs buying for housing decisions
- Provides break-even analysis and long-term projections
- DMV-specific defaults (DC/MD/VA)
- Call when user asks about buying vs renting, home affordability, or housing decisions
```

### **3. Frontend Integration**
- Calculation dropdown already supports this tool ✅
- LaTeX formulas will render in expandable panel
- Clean agent response shows summary

---

## 💡 Usage Examples for Agent

**Simple Query**:
> "Should I buy or rent?"

**Agent Response**:
> "I'd be happy to help you analyze that! To provide an accurate rent vs buy comparison, I need a few details:
> 1. What's your target home price range?
> 2. What's your current monthly rent?
> 3. Which area are you considering (DC, Maryland, or Virginia)?"

**Complete Query**:
> "I'm paying $2,300/month rent in Maryland. Should I buy a $380,000 house?"

**Agent Action**:
```
Tool: rent_vs_buy
Parameters: {
  "home_price": 380000,
  "monthly_rent": 2300,
  "region": "MD",
  "customer_id": "C001"  // if existing user
}
```

---

**Status**: ✅ **READY FOR TESTING**  
**Created**: November 1, 2025  
**Tool**: `rent_vs_buy_tool.py`  
**Test Count**: 10 scenarios + 5 edge cases

