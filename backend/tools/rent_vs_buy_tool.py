"""
Rent vs Buy Tool for Financial Advisory Agent.

Comprehensive rent vs buy analysis for the DMV area (DC, Maryland, Virginia)
with break-even calculations, sensitivity analysis, and detailed cost breakdowns.
"""

import sqlite3
import math
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from .base_tool import BaseTool
from pathlib import Path

# Module-level variable to store last calculation details for frontend display
_last_rent_buy_details: Optional[Dict[str, Any]] = None

def get_last_rent_buy_details() -> Optional[Dict[str, Any]]:
    """Retrieve the last captured rent vs buy calculation details."""
    return _last_rent_buy_details

def clear_rent_buy_details():
    """Clear the captured rent vs buy calculation details."""
    global _last_rent_buy_details
    _last_rent_buy_details = None


class RentVsBuyTool(BaseTool):
    """
    Comprehensive rent vs buy calculator for housing decisions.
    
    Features:
    - Monthly cost breakdown (PITI vs Rent)
    - Long-term cost analysis with projections
    - Break-even point calculation
    - Home equity accumulation tracking
    - Opportunity cost of down payment
    - Sensitivity analysis (rates, down payment %, appreciation)
    - DMV market defaults (DC, MD, VA)
    - Tax deduction modeling (mortgage interest, property tax)
    """
    
    # DMV Market Defaults
    DMV_DEFAULTS = {
        'DC': {
            'property_tax_rate': 0.0085,  # 0.85%
            'appreciation_rate': 0.038,    # 3.8% annual
            'median_home_price': 650000,
            'median_rent': 2800,
            'description': 'Washington DC'
        },
        'MD': {
            'property_tax_rate': 0.011,    # 1.1%
            'appreciation_rate': 0.035,    # 3.5% annual
            'median_home_price': 425000,
            'median_rent': 2100,
            'description': 'Maryland'
        },
        'VA': {
            'property_tax_rate': 0.008,    # 0.8%
            'appreciation_rate': 0.037,    # 3.7% annual
            'median_home_price': 475000,
            'median_rent': 2300,
            'description': 'Virginia'
        }
    }
    
    @property
    def name(self) -> str:
        return "rent_vs_buy"
    
    @property
    def description(self) -> str:
        return """Comprehensive rent vs buy analysis for housing decisions in the DMV area.

        This tool provides:
        1. Monthly cost comparison (PITI vs Rent)
        2. Long-term cost projections (5, 10, 20, 30 years)
        3. Break-even point analysis
        4. Home equity accumulation
        5. Opportunity cost of down payment
        6. Tax benefit calculations
        7. Sensitivity analysis scenarios
        8. DMV market-specific defaults

        Args:
            customer_id: Customer ID to fetch profile data (optional for Scenario A)
            
            # Home Purchase Inputs
            home_price: Home purchase price (required)
            down_payment_pct: Down payment as percentage (0-100, default: 20)
            mortgage_rate: Annual mortgage interest rate (default: 7.0)
            mortgage_term_years: Mortgage term in years (default: 30)
            closing_costs_pct: Closing costs as percentage of price (default: 3)
            
            # Ongoing Homeownership Costs
            property_tax_rate: Annual property tax rate (default: DMV average 1.0%)
            home_insurance_annual: Annual home insurance (default: $1,500)
            hoa_monthly: Monthly HOA/condo fees (default: 0)
            maintenance_pct: Annual maintenance as % of home value (default: 1)
            
            # Market Assumptions
            appreciation_rate: Annual home appreciation rate (default: 3.5%)
            selling_cost_pct: Cost to sell home as % (default: 6 for realtor)
            
            # Rental Comparison
            monthly_rent: Current monthly rent (required)
            rent_inflation: Annual rent increase rate (default: 3%)
            renters_insurance: Monthly renters insurance (default: 25)
            
            # Analysis Parameters
            analysis_years: Years to analyze (default: 10, options: 5, 10, 20, 30)
            region: DMV region for defaults - DC/MD/VA (optional)
            marginal_tax_rate: User's tax bracket for deductions (default: 24%)
            investment_return_rate: Expected return on invested down payment (default: 7%)
            
            # Sensitivity Analysis
            run_sensitivity: Whether to run sensitivity scenarios (default: True)
            
        Returns:
            Comprehensive rent vs buy analysis with break-even point, cost projections,
            equity accumulation, tax benefits, and sensitivity scenarios with LaTeX formulas.
        """
    
    def __init__(self):
        self.db_path = Path(__file__).parent.parent / "data" / "financial_data.db"
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the rent vs buy analysis."""
        try:
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
            
            # Debug: Print received parameters
            print(f"\n[RentVsBuyTool] Received parameters:")
            print(f"  - Keys: {list(kwargs.keys())}")
            for key, value in kwargs.items():
                if key not in ['kwargs']:  # Skip the raw kwargs string
                    print(f"  - {key}: {value} (type: {type(value).__name__})")
            
            # Extract parameters
            customer_id = kwargs.get('customer_id')
            
            # Home purchase inputs
            home_price = kwargs.get('home_price')
            # Convert to float if it's a string
            if home_price is not None and isinstance(home_price, str):
                try:
                    home_price = float(home_price)
                except ValueError:
                    home_price = None
            
            down_payment_pct = float(kwargs.get('down_payment_pct', 20.0))
            mortgage_rate = float(kwargs.get('mortgage_rate', 7.0))
            mortgage_term_years = int(kwargs.get('mortgage_term_years', 30))
            closing_costs_pct = float(kwargs.get('closing_costs_pct', 3.0))
            
            # Ongoing costs
            property_tax_rate = kwargs.get('property_tax_rate')
            if property_tax_rate is not None:
                property_tax_rate = float(property_tax_rate)
            home_insurance_annual = float(kwargs.get('home_insurance_annual', 1500))
            hoa_monthly = float(kwargs.get('hoa_monthly', 0))
            maintenance_pct = float(kwargs.get('maintenance_pct', 1.0))
            
            # Market assumptions
            appreciation_rate = kwargs.get('appreciation_rate')
            if appreciation_rate is not None:
                appreciation_rate = float(appreciation_rate)
            selling_cost_pct = float(kwargs.get('selling_cost_pct', 6.0))
            
            # Rental comparison
            monthly_rent = kwargs.get('monthly_rent')
            # Convert to float if it's a string
            if monthly_rent is not None and isinstance(monthly_rent, str):
                try:
                    monthly_rent = float(monthly_rent)
                except ValueError:
                    monthly_rent = None
            
            rent_inflation = float(kwargs.get('rent_inflation', 3.0))
            renters_insurance = float(kwargs.get('renters_insurance', 25))
            
            # Analysis parameters
            analysis_years = int(kwargs.get('analysis_years', 10))
            region = str(kwargs.get('region', 'MD')).upper()
            marginal_tax_rate = float(kwargs.get('marginal_tax_rate', 24.0))
            investment_return_rate = float(kwargs.get('investment_return_rate', 7.0))
            run_sensitivity = kwargs.get('run_sensitivity', True)
            if isinstance(run_sensitivity, str):
                run_sensitivity = run_sensitivity.lower() in ['true', '1', 'yes']
            
            # Handle Scenario A: Fetch customer data
            if customer_id and not home_price:
                customer_data = self._get_customer_data(customer_id)
                if customer_data:
                    # Use customer income to suggest affordable price if not provided
                    income = customer_data.get('annual_income', 0)
                    if income and not home_price:
                        # 3x annual income rule of thumb
                        home_price = income * 3
            
            # Validate required inputs
            if not home_price:
                return {
                    "status": "error",
                    "error": "home_price is required for rent vs buy analysis"
                }
            
            if not monthly_rent:
                return {
                    "status": "error",
                    "error": "monthly_rent is required for comparison"
                }
            
            # Apply DMV regional defaults if not provided
            if region in self.DMV_DEFAULTS:
                defaults = self.DMV_DEFAULTS[region]
                if property_tax_rate is None:
                    property_tax_rate = defaults['property_tax_rate'] * 100  # Convert to percentage
                if appreciation_rate is None:
                    appreciation_rate = defaults['appreciation_rate'] * 100
            else:
                # Fallback defaults
                if property_tax_rate is None:
                    property_tax_rate = 1.0
                if appreciation_rate is None:
                    appreciation_rate = 3.5
            
            # Calculate comprehensive analysis
            result = self._calculate_rent_vs_buy(
                home_price=home_price,
                down_payment_pct=down_payment_pct,
                mortgage_rate=mortgage_rate,
                mortgage_term_years=mortgage_term_years,
                closing_costs_pct=closing_costs_pct,
                property_tax_rate=property_tax_rate,
                home_insurance_annual=home_insurance_annual,
                hoa_monthly=hoa_monthly,
                maintenance_pct=maintenance_pct,
                appreciation_rate=appreciation_rate,
                selling_cost_pct=selling_cost_pct,
                monthly_rent=monthly_rent,
                rent_inflation=rent_inflation,
                renters_insurance=renters_insurance,
                analysis_years=analysis_years,
                region=region,
                marginal_tax_rate=marginal_tax_rate,
                investment_return_rate=investment_return_rate,
                run_sensitivity=run_sensitivity,
                customer_id=customer_id
            )
            
            # Store for frontend display
            if result and isinstance(result, dict) and result.get("status") != "error":
                if "calculation_steps" in result or "latex_formulas" in result:
                    global _last_rent_buy_details
                    _last_rent_buy_details = {
                        'scenario_type': 'rent_vs_buy',
                        'calculation_steps': result.get('calculation_steps', []),
                        'latex_formulas': result.get('latex_formulas', []),
                        'tool_name': 'rent_vs_buy'
                    }
                    print(f"\n✅ [RentVsBuyTool] Stored calculation details")
                    print(f"   - Steps: {len(_last_rent_buy_details['calculation_steps'])}")
                    print(f"   - Formulas: {len(_last_rent_buy_details['latex_formulas'])}")
            
            return result
        
        except Exception as e:
            import traceback
            return {
                "status": "error",
                "error": f"Rent vs buy analysis failed: {str(e)}",
                "traceback": traceback.format_exc()
            }
    
    def _get_customer_data(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Fetch customer data from database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT base_salary_annual, fico_score
                FROM customers
                WHERE customer_id = ?
            """, (customer_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'annual_income': row[0],
                    'credit_score': row[1]
                }
            return None
        
        except Exception as e:
            print(f"Error fetching customer data: {e}")
            return None
    
    def _calculate_rent_vs_buy(self, **params) -> Dict[str, Any]:
        """Comprehensive rent vs buy calculation."""
        
        # Extract all parameters
        home_price = params['home_price']
        down_payment_pct = params['down_payment_pct']
        mortgage_rate = params['mortgage_rate']
        mortgage_term_years = params['mortgage_term_years']
        closing_costs_pct = params['closing_costs_pct']
        property_tax_rate = params['property_tax_rate']
        home_insurance_annual = params['home_insurance_annual']
        hoa_monthly = params['hoa_monthly']
        maintenance_pct = params['maintenance_pct']
        appreciation_rate = params['appreciation_rate']
        selling_cost_pct = params['selling_cost_pct']
        monthly_rent = params['monthly_rent']
        rent_inflation = params['rent_inflation']
        renters_insurance = params['renters_insurance']
        analysis_years = params['analysis_years']
        region = params['region']
        marginal_tax_rate = params['marginal_tax_rate']
        investment_return_rate = params['investment_return_rate']
        run_sensitivity = params['run_sensitivity']
        customer_id = params.get('customer_id')
        
        # Calculate upfront costs
        down_payment = home_price * (down_payment_pct / 100)
        loan_amount = home_price - down_payment
        closing_costs = home_price * (closing_costs_pct / 100)
        total_upfront = down_payment + closing_costs
        
        # Calculate monthly mortgage payment (P&I only)
        monthly_rate = mortgage_rate / 100 / 12
        num_payments = mortgage_term_years * 12
        
        if monthly_rate > 0:
            monthly_pi = loan_amount * (monthly_rate * (1 + monthly_rate) ** num_payments) / \
                        ((1 + monthly_rate) ** num_payments - 1)
        else:
            monthly_pi = loan_amount / num_payments
        
        # Calculate monthly homeownership costs
        monthly_property_tax = (home_price * (property_tax_rate / 100)) / 12
        monthly_insurance = home_insurance_annual / 12
        monthly_maintenance = (home_price * (maintenance_pct / 100)) / 12
        
        monthly_piti = monthly_pi + monthly_property_tax + monthly_insurance + hoa_monthly
        monthly_total_own = monthly_piti + monthly_maintenance
        
        # Tax benefits (mortgage interest and property tax deductions)
        # Year 1 interest (approximate)
        first_year_interest = loan_amount * (mortgage_rate / 100)
        first_year_prop_tax = home_price * (property_tax_rate / 100)
        annual_tax_benefit = (first_year_interest + first_year_prop_tax) * (marginal_tax_rate / 100)
        monthly_tax_benefit = annual_tax_benefit / 12
        
        # Effective monthly cost after tax benefits
        monthly_own_after_tax = monthly_total_own - monthly_tax_benefit
        
        # Year-by-year analysis
        yearly_analysis = []
        cumulative_rent_cost = 0
        cumulative_own_cost = 0
        remaining_balance = loan_amount
        home_value = home_price
        break_even_year = None
        
        for year in range(1, analysis_years + 1):
            # Rent costs for this year
            current_rent = monthly_rent * ((1 + rent_inflation / 100) ** (year - 1))
            annual_rent_cost = (current_rent * 12) + (renters_insurance * 12)
            cumulative_rent_cost += annual_rent_cost
            
            # Home appreciation
            home_value = home_value * (1 + appreciation_rate / 100)
            
            # Ownership costs for this year
            # Recalculate property tax and maintenance on appreciated home value
            current_prop_tax_monthly = (home_value * (property_tax_rate / 100)) / 12
            current_maintenance_monthly = (home_value * (maintenance_pct / 100)) / 12
            
            # Interest payment for this year (decreases over time)
            annual_interest = remaining_balance * (mortgage_rate / 100)
            annual_principal = (monthly_pi * 12) - annual_interest
            remaining_balance = max(0, remaining_balance - annual_principal)
            
            # Tax benefit for this year
            annual_tax_deduction = (annual_interest + home_value * (property_tax_rate / 100)) * (marginal_tax_rate / 100)
            
            # Total ownership cost
            annual_own_cost = (monthly_pi * 12) + (current_prop_tax_monthly * 12) + \
                             (monthly_insurance * 12) + (hoa_monthly * 12) + \
                             (current_maintenance_monthly * 12) - annual_tax_deduction
            
            cumulative_own_cost += annual_own_cost
            
            # Add opportunity cost of down payment
            opportunity_cost = total_upfront * ((1 + investment_return_rate / 100) ** year - 1)
            
            # Net position for buying (equity - costs - opportunity cost)
            equity = home_value - remaining_balance
            net_own_position = equity - cumulative_own_cost - opportunity_cost - (home_value * selling_cost_pct / 100)
            
            # Net position for renting (negative costs)
            net_rent_position = -cumulative_rent_cost
            
            # Check for break-even
            if break_even_year is None and net_own_position > net_rent_position:
                break_even_year = year
            
            yearly_analysis.append({
                'year': year,
                'rent_monthly': round(current_rent, 2),
                'own_monthly': round(monthly_own_after_tax, 2),
                'cumulative_rent_cost': round(cumulative_rent_cost, 2),
                'cumulative_own_cost': round(cumulative_own_cost, 2),
                'home_value': round(home_value, 2),
                'remaining_mortgage': round(remaining_balance, 2),
                'equity': round(equity, 2),
                'net_own_position': round(net_own_position, 2),
                'net_rent_position': round(net_rent_position, 2)
            })
        
        # Final year analysis
        final_year = yearly_analysis[-1]
        final_home_value = final_year['home_value']
        final_equity = final_year['equity']
        final_selling_cost = final_home_value * (selling_cost_pct / 100)
        net_proceeds = final_equity - final_selling_cost
        
        # Sensitivity analysis
        sensitivity_scenarios = []
        if run_sensitivity:
            sensitivity_scenarios = self._run_sensitivity_analysis(params)
        
        # Generate calculation steps and formulas
        calculation_steps, latex_formulas = self._generate_calculation_steps(
            home_price, down_payment, loan_amount, monthly_rate, num_payments,
            monthly_pi, monthly_property_tax, monthly_insurance, monthly_total_own,
            monthly_tax_benefit, monthly_own_after_tax, monthly_rent,
            break_even_year, final_equity, cumulative_rent_cost, cumulative_own_cost
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            break_even_year, monthly_own_after_tax, monthly_rent,
            analysis_years, final_equity, cumulative_rent_cost, cumulative_own_cost,
            down_payment_pct
        )
        
        return {
            "status": "success",
            "customer_id": customer_id,
            "scenario_type": "rent_vs_buy",
            "analysis_years": analysis_years,
            "region": region,
            
            # Upfront costs
            "upfront_costs": {
                "home_price": round(home_price, 2),
                "down_payment": round(down_payment, 2),
                "down_payment_pct": down_payment_pct,
                "closing_costs": round(closing_costs, 2),
                "total_upfront": round(total_upfront, 2)
            },
            
            # Monthly comparison
            "monthly_comparison": {
                "rent": {
                    "base_rent": round(monthly_rent, 2),
                    "renters_insurance": renters_insurance,
                    "total": round(monthly_rent + renters_insurance, 2)
                },
                "own": {
                    "principal_interest": round(monthly_pi, 2),
                    "property_tax": round(monthly_property_tax, 2),
                    "insurance": round(monthly_insurance, 2),
                    "hoa": hoa_monthly,
                    "maintenance": round(monthly_maintenance, 2),
                    "piti_total": round(monthly_piti, 2),
                    "all_costs_total": round(monthly_total_own, 2),
                    "tax_benefit": round(monthly_tax_benefit, 2),
                    "effective_cost": round(monthly_own_after_tax, 2)
                },
                "monthly_difference": round(monthly_own_after_tax - monthly_rent, 2)
            },
            
            # Break-even analysis
            "break_even": {
                "break_even_year": break_even_year,
                "message": f"Buying breaks even in year {break_even_year}" if break_even_year else \
                          f"Buying does not break even within {analysis_years} years"
            },
            
            # Long-term projections
            "projections": {
                "final_year": analysis_years,
                "final_home_value": round(final_home_value, 2),
                "final_equity": round(final_equity, 2),
                "total_rent_paid": round(cumulative_rent_cost, 2),
                "total_own_costs": round(cumulative_own_cost, 2),
                "net_proceeds_if_sold": round(net_proceeds, 2)
            },
            
            # Year-by-year breakdown
            "yearly_analysis": yearly_analysis,
            
            # Sensitivity scenarios
            "sensitivity_scenarios": sensitivity_scenarios,
            
            # Recommendations
            "recommendations": recommendations,
            
            # Calculation details for frontend
            "calculation_steps": calculation_steps,
            "latex_formulas": latex_formulas
        }
    
    def _run_sensitivity_analysis(self, base_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Run sensitivity analysis with different scenarios."""
        scenarios = []
        
        # Scenario 1: Higher interest rate (+1%)
        params_high_rate = base_params.copy()
        params_high_rate['mortgage_rate'] = base_params['mortgage_rate'] + 1.0
        params_high_rate['run_sensitivity'] = False
        result_high_rate = self._calculate_rent_vs_buy(**params_high_rate)
        scenarios.append({
            'name': 'Higher Interest Rate (+1%)',
            'break_even_year': result_high_rate['break_even']['break_even_year'],
            'monthly_own_cost': result_high_rate['monthly_comparison']['own']['effective_cost']
        })
        
        # Scenario 2: Lower down payment (10%)
        params_low_down = base_params.copy()
        params_low_down['down_payment_pct'] = 10.0
        params_low_down['run_sensitivity'] = False
        result_low_down = self._calculate_rent_vs_buy(**params_low_down)
        scenarios.append({
            'name': 'Lower Down Payment (10%)',
            'break_even_year': result_low_down['break_even']['break_even_year'],
            'monthly_own_cost': result_low_down['monthly_comparison']['own']['effective_cost']
        })
        
        # Scenario 3: Lower appreciation (2%)
        params_low_appr = base_params.copy()
        params_low_appr['appreciation_rate'] = 2.0
        params_low_appr['run_sensitivity'] = False
        result_low_appr = self._calculate_rent_vs_buy(**params_low_appr)
        scenarios.append({
            'name': 'Lower Appreciation (2%)',
            'break_even_year': result_low_appr['break_even']['break_even_year'],
            'net_proceeds': result_low_appr['projections']['net_proceeds_if_sold']
        })
        
        return scenarios
    
    def _generate_calculation_steps(self, home_price, down_payment, loan_amount,
                                   monthly_rate, num_payments, monthly_pi,
                                   monthly_property_tax, monthly_insurance,
                                   monthly_total_own, monthly_tax_benefit,
                                   monthly_own_after_tax, monthly_rent,
                                   break_even_year, final_equity,
                                   cumulative_rent_cost, cumulative_own_cost) -> Tuple[List, List]:
        """Generate calculation steps and LaTeX formulas for frontend display."""
        
        calculation_steps = [
            {
                "title": "Home Purchase Overview",
                "description": f"Home Price: ${home_price:,.2f}, Down Payment: ${down_payment:,.2f} ({down_payment/home_price*100:.1f}%), Loan Amount: ${loan_amount:,.2f}",
                "latex": f"\\text{{Loan Amount}} = \\${home_price:,.2f} - \\${down_payment:,.2f} = \\${loan_amount:,.2f}",
                "display": True
            },
            {
                "title": "Monthly Mortgage Payment (P&I)",
                "description": f"Using standard amortization formula with {monthly_rate*100:.3f}% monthly rate over {num_payments} months.",
                "latex": f"M = L \\times \\frac{{r(1+r)^n}}{{(1+r)^n - 1}}",
                "display": True
            },
            {
                "title": "Monthly P&I Calculation",
                "description": f"L = ${loan_amount:,.2f}, r = {monthly_rate:.6f}, n = {num_payments}",
                "latex": f"M = {loan_amount:,.2f} \\times \\frac{{{monthly_rate:.6f}(1+{monthly_rate:.6f})^{{{num_payments}}}}}{{(1+{monthly_rate:.6f})^{{{num_payments}}} - 1}} = \\${monthly_pi:,.2f}",
                "display": True
            },
            {
                "title": "Total Monthly Homeownership Costs",
                "description": f"P&I: ${monthly_pi:,.2f}, Property Tax: ${monthly_property_tax:,.2f}, Insurance: ${monthly_insurance:,.2f}",
                "latex": f"\\text{{Total}} = \\${monthly_pi:,.2f} + \\${monthly_property_tax:,.2f} + \\${monthly_insurance:,.2f} = \\${monthly_total_own:,.2f}",
                "display": True
            },
            {
                "title": "After-Tax Effective Cost",
                "description": f"Monthly tax benefit from mortgage interest deduction: ${monthly_tax_benefit:,.2f}",
                "latex": f"\\text{{Effective Cost}} = \\${monthly_total_own:,.2f} - \\${monthly_tax_benefit:,.2f} = \\${monthly_own_after_tax:,.2f}",
                "display": True
            },
            {
                "title": "Monthly Cost Comparison",
                "description": f"Renting: ${monthly_rent:,.2f}/month vs Owning: ${monthly_own_after_tax:,.2f}/month (after tax benefits)",
                "latex": f"\\text{{Difference}} = \\${monthly_own_after_tax:,.2f} - \\${monthly_rent:,.2f} = \\${monthly_own_after_tax - monthly_rent:,.2f}",
                "display": True
            },
            {
                "title": "Break-Even Analysis",
                "description": f"Break-even year: {break_even_year if break_even_year else 'Not reached'}",
                "latex": f"\\text{{Break-even year}} = {break_even_year if break_even_year else '>10'}",
                "display": True
            },
            {
                "title": "Long-Term Net Position",
                "description": f"Final equity: ${final_equity:,.2f}, Total rent paid: ${cumulative_rent_cost:,.2f}",
                "latex": f"\\text{{Net Benefit of Owning}} = \\${final_equity:,.2f} - \\${cumulative_own_cost:,.2f} = \\${final_equity - cumulative_own_cost:,.2f}",
                "display": True
            }
        ]
        
        latex_formulas = [
            f"$$\\text{{Loan Amount}} = \\${loan_amount:,.2f}$$",
            "$$M = L \\times \\frac{r(1+r)^n}{(1+r)^n - 1}$$",
            f"$$\\text{{Monthly P\\&I}} = \\${monthly_pi:,.2f}$$",
            f"$$\\text{{Effective Cost}} = \\${monthly_own_after_tax:,.2f}$$",
            f"$$\\text{{Break-even Year}} = {break_even_year if break_even_year else '>10'}$$"
        ]
        
        return calculation_steps, latex_formulas
    
    def _generate_recommendations(self, break_even_year, monthly_own, monthly_rent,
                                 analysis_years, final_equity, cumulative_rent,
                                 cumulative_own, down_payment_pct) -> List[str]:
        """Generate personalized recommendations based on analysis."""
        recommendations = []
        
        if break_even_year and break_even_year <= 5:
            recommendations.append(f"✅ **Strong Buy Signal**: You'll break even in just {break_even_year} years. Buying is financially advantageous if you plan to stay long-term.")
        elif break_even_year and break_even_year <= analysis_years:
            recommendations.append(f"⚖️ **Moderate Buy Signal**: Break-even at year {break_even_year}. Consider buying if you plan to stay at least {break_even_year + 2} years.")
        else:
            recommendations.append(f"⚠️ **Renting May Be Better**: Break-even not reached within {analysis_years} years. Renting offers more flexibility and lower short-term costs.")
        
        monthly_diff = monthly_own - monthly_rent
        if monthly_diff > 500:
            recommendations.append(f"💰 **Cash Flow Impact**: Owning costs ${abs(monthly_diff):,.2f}/month more than renting. Ensure your budget can handle this increase.")
        elif monthly_diff < -200:
            recommendations.append(f"💰 **Cash Flow Advantage**: Owning costs ${abs(monthly_diff):,.2f}/month less than renting after tax benefits.")
        
        if down_payment_pct < 20:
            recommendations.append(f"🏦 **PMI Alert**: With {down_payment_pct}% down, you'll need Private Mortgage Insurance (PMI), adding ~$100-200/month until 20% equity.")
        
        if final_equity > cumulative_rent:
            equity_advantage = final_equity - cumulative_rent
            recommendations.append(f"📈 **Wealth Building**: After {analysis_years} years, you'll have ${equity_advantage:,.2f} more in home equity compared to renting.")
        
        recommendations.append(f"🏡 **Consider Your Timeline**: The longer you stay, the more sense buying makes due to home appreciation and equity buildup.")
        
        return recommendations

