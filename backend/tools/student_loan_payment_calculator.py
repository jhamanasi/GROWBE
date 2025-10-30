"""
Student Loan Payment Calculator Tool for Financial Advisory Agent.

This tool calculates monthly student loan payments with various scenarios including
existing customer loans, hypothetical loans, refinancing, and payment optimization.
"""

import sqlite3
import math
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from .base_tool import BaseTool
from pathlib import Path

class StudentLoanPaymentCalculator(BaseTool):
    """Calculate student loan payments with comprehensive scenarios and optimizations."""
    
    def __init__(self):
        super().__init__()
        # Use the same path resolution as sqlite_tool.py
        import os
        from pathlib import Path
        
        db_path = os.getenv("SQLITE_DB_PATH", "data/financial_data.db")
        if not os.path.isabs(db_path):
            BASE_DIR = Path(__file__).parent.parent
            self.db_path = str(BASE_DIR / db_path)
        else:
            self.db_path = db_path
    
    @property
    def name(self) -> str:
        """Return the tool name."""
        return "student_loan_payment_calculator"
    
    @property
    def description(self) -> str:
        """Return the tool description."""
        return """Calculate student loan payments with various scenarios and optimizations.

        This tool can handle:
        1. Existing customer loans (fetch from database)
        2. Hypothetical loan calculations
        3. Refinancing scenarios
        4. Extra payment strategies
        5. Consolidation scenarios
        6. Payoff timeline comparisons
        7. Target payoff calculations (pay off loan in specific timeframe)

        Args:
            customer_id: Customer ID to fetch existing loans (optional)
            principal: Loan amount in dollars (required if no customer_id)
            annual_interest_rate: Annual interest rate as percentage (required if no customer_id)
            loan_term_years: Loan term in years (required if no customer_id)
            payment_frequency: Payment frequency - monthly/biweekly/weekly (optional, default: monthly)
            extra_payment: Additional monthly payment amount (optional, default: 0)
            grace_period_months: Grace period before payments start (optional, default: 0)
            scenario_type: Type of calculation - current/refinance/consolidate/extra_payment/target_payoff (optional, default: current)
            new_rate: New interest rate for refinancing scenarios (optional)
            new_term: New loan term for refinancing scenarios (optional)
            target_payoff_months: Target payoff timeframe in months for target_payoff scenario (optional, default: 12)
            
        Returns:
            Detailed payment calculation results with scenarios and recommendations
        """
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the student loan payment calculation."""
        try:
            # Test database connection first
            if not self._test_database_connection():
                return {
                    "status": "error",
                    "error": "Database connection failed"
                }
            
            # Handle Strands framework parameter passing - it passes JSON string in kwargs
            if 'kwargs' in kwargs and isinstance(kwargs['kwargs'], str):
                import json
                try:
                    parsed_kwargs = json.loads(kwargs['kwargs'])
                    # Merge parsed kwargs with existing kwargs
                    kwargs.update(parsed_kwargs)
                except json.JSONDecodeError as e:
                    return {
                        "status": "error",
                        "error": f"Failed to parse tool parameters: {str(e)}"
                    }
            
            # Extract parameters
            customer_id = kwargs.get('customer_id')
            principal = kwargs.get('principal')
            annual_interest_rate = kwargs.get('annual_interest_rate')
            loan_term_years = kwargs.get('loan_term_years')
            payment_frequency = kwargs.get('payment_frequency', 'monthly')
            extra_payment = kwargs.get('extra_payment', 0)
            grace_period_months = kwargs.get('grace_period_months', 0)
            scenario_type = kwargs.get('scenario_type', 'current')
            new_rate = kwargs.get('new_rate')
            new_term = kwargs.get('new_term')
            target_payoff_months = kwargs.get('target_payoff_months')
            
            # Handle different scenarios
            if customer_id:
                result = self._handle_existing_customer(customer_id, extra_payment, scenario_type, new_rate, new_term, target_payoff_months)
            else:
                result = self._handle_hypothetical_loan(principal, annual_interest_rate, loan_term_years, 
                                                    payment_frequency, extra_payment, grace_period_months)
            
            return result
        
        except Exception as e:
            return {
                "status": "error",
                "error": f"Calculation failed: {str(e)}"
            }
    
    def _test_database_connection(self) -> bool:
        """Test if we can connect to the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            conn.close()
            return True
        except Exception as e:
            return False
    
    def _handle_existing_customer(self, customer_id: str, extra_payment: float, scenario_type: str, 
                                new_rate: Optional[float], new_term: Optional[int], target_payoff_months: Optional[int] = None) -> Dict[str, Any]:
        """Handle calculations for existing customer loans."""
        try:
            # Fetch customer's student loans
            loans = self._get_customer_student_loans(customer_id)
            
            if not loans:
                return {
                    "status": "error",
                    "error": f"No student loans found for customer {customer_id}"
                }
            
            results = {
                "status": "success",
                "customer_id": customer_id,
                "scenario_type": scenario_type,
                "loans": [],
                "summary": {},
                "recommendations": [],
                "latex_formulas": [],
                "calculation_steps": []
            }
            
            total_current_payment = 0
            total_new_payment = 0
            total_savings = 0
            
            for loan in loans:
                loan_result = self._calculate_loan_scenario(loan, extra_payment, scenario_type, new_rate, new_term, target_payoff_months)
                results["loans"].append(loan_result)
                
                total_current_payment += loan_result["current_payment"]
                total_new_payment += loan_result["new_payment"]
                total_savings += loan_result.get("savings", 0)

                base_formula = loan_result.get("base_formula")
                if base_formula:
                    results["latex_formulas"].append(base_formula)

                extra_details = loan_result.get("extra_payment_details")
                if extra_details and extra_details.get("formula"):
                    results["latex_formulas"].append(extra_details["formula"])

                if loan_result.get("calculation_steps"):
                    for step in loan_result["calculation_steps"]:
                        if step.get("latex") and step.get("display"):
                            results["latex_formulas"].append(step["latex"])

            # Generate summary
            results["summary"] = {
                "total_loans": len(loans),
                "total_current_payment": total_current_payment,
                "total_new_payment": total_new_payment,
                "total_savings": total_savings,
                "savings_percentage": (total_savings / total_current_payment * 100) if total_current_payment > 0 else 0
            }
            
            # Generate recommendations
            results["recommendations"] = self._generate_recommendations(loans, scenario_type, total_savings)
            
            # Generate mathematical explanations
            results["mathematical_explanation"] = self._generate_mathematical_explanation(loans, scenario_type, extra_payment, new_rate, new_term)

            if results["loans"]:
                results["calculation_steps"] = results["loans"][0].get("calculation_steps", [])

            return results
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to process customer loans: {str(e)}"
            }
    
    def _handle_hypothetical_loan(self, principal: float, annual_interest_rate: float, 
                                loan_term_years: int, payment_frequency: str, 
                                extra_payment: float, grace_period_months: int) -> Dict[str, Any]:
        """Handle calculations for hypothetical loans."""
        try:
            # Validate inputs
            if not all([principal, annual_interest_rate, loan_term_years]):
                return {
                    "status": "error",
                    "error": "principal, annual_interest_rate, and loan_term_years are required for hypothetical loans"
                }
            
            if principal <= 0 or annual_interest_rate < 0 or loan_term_years <= 0:
                return {
                    "status": "error",
                    "error": "Invalid input values. Principal and term must be positive, interest rate must be non-negative"
                }
            
            # Calculate base payment
            base_payment = self._calculate_monthly_payment(principal, annual_interest_rate, loan_term_years)
            
            # Calculate with extra payment
            extra_payment_result = self._calculate_extra_payment_scenario(
                principal, annual_interest_rate, loan_term_years, extra_payment
            )
            
            # Calculate different scenarios
            scenarios = self._calculate_scenarios(principal, annual_interest_rate, loan_term_years)
            
            # Generate LaTeX formula for payment calculation
            monthly_rate = annual_interest_rate / 100 / 12
            num_payments = loan_term_years * 12
            payment_formula = self._generate_payment_formula_latex(principal, monthly_rate, num_payments)
            
            latex_formulas = [payment_formula]
            if extra_payment_result and extra_payment_result.get("formula"):
                latex_formulas.append(extra_payment_result["formula"])

            calculation_steps = self._build_monthly_payment_steps(
                principal=principal,
                annual_rate=annual_interest_rate,
                num_payments=int(loan_term_years * 12),
                monthly_payment=base_payment
            )

            if extra_payment > 0 and extra_payment_result:
                calculation_steps.extend(
                    self._build_interest_savings_steps(
                        original_interest=extra_payment_result["original_total_interest"],
                        new_interest=extra_payment_result["total_interest"],
                        savings=extra_payment_result["total_savings"]
                    )
                )

            return {
                "status": "success",
                "loan_details": {
                    "principal": principal,
                    "annual_interest_rate": annual_interest_rate,
                    "loan_term_years": loan_term_years,
                    "payment_frequency": payment_frequency
                },
                "base_calculation": {
                    "monthly_payment": base_payment,
                    "total_payments": loan_term_years * 12,
                    "total_interest": (base_payment * loan_term_years * 12) - principal,
                    "total_cost": base_payment * loan_term_years * 12,
                    "payoff_date": self._calculate_payoff_date(loan_term_years),
                    "formula": payment_formula
                },
                "extra_payment_scenario": extra_payment_result,
                "scenarios": scenarios,
                "recommendations": self._generate_hypothetical_recommendations(principal, annual_interest_rate, loan_term_years),
                "latex_formulas": latex_formulas,
                "calculation_steps": calculation_steps
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to calculate hypothetical loan: {str(e)}"
            }
    
    def _get_customer_student_loans(self, customer_id: str) -> List[Dict[str, Any]]:
        """Fetch customer's student loans from database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    d.debt_id,
                    d.original_principal,
                    d.current_principal,
                    d.interest_rate_apr,
                    d.term_months,
                    d.min_payment_mo,
                    d.origination_date,
                    d.status
                FROM debts_loans d
                WHERE d.customer_id = ? AND d.type = 'student'
                ORDER BY d.current_principal DESC
            """
            
            cursor.execute(query, (customer_id,))
            
            loans = []
            for row in cursor.fetchall():
                loan_data = {
                    "debt_id": row[0],
                    "original_principal": row[1],
                    "current_principal": row[2],
                    "interest_rate_apr": row[3],
                    "term_months": row[4],
                    "min_payment_mo": row[5],
                    "origination_date": row[6],
                    "status": row[7]
                }
                loans.append(loan_data)
            
            conn.close()
            return loans
            
        except Exception as e:
            raise Exception(f"Failed to fetch customer loans: {str(e)}")
    
    def _calculate_loan_scenario(self, loan: Dict[str, Any], extra_payment: float, 
                               scenario_type: str, new_rate: Optional[float], 
                               new_term: Optional[int], target_payoff_months: Optional[int] = None) -> Dict[str, Any]:
        """Calculate different scenarios for a single loan."""
        principal = loan["current_principal"]
        current_rate = loan["interest_rate_apr"]
        current_term_months = loan["term_months"]
        current_payment = loan["min_payment_mo"]
        
        result = {
            "debt_id": loan["debt_id"],
            "current_principal": principal,
            "current_rate": current_rate,
            "current_payment": current_payment,
            "current_term_months": current_term_months
        }
        
        if scenario_type in ["current", "extra_payment"]:
            # Just add extra payment to current loan
            new_payment = current_payment + extra_payment
            result["new_payment"] = new_payment
            result["extra_payment"] = extra_payment
            
            if extra_payment > 0:
                # Calculate savings with extra payment
                savings_result = self._calculate_extra_payment_scenario(
                    principal, current_rate, current_term_months / 12, extra_payment
                )
                result["savings"] = savings_result["total_savings"]
                result["new_payoff_date"] = savings_result["payoff_date"]
                result["months_saved"] = savings_result["months_saved"]
                result["extra_payment_details"] = savings_result
        
        elif scenario_type == "refinance" and new_rate:
            # Refinancing scenario
            new_term_years = new_term if new_term else current_term_months / 12
            new_payment = self._calculate_monthly_payment(principal, new_rate, new_term_years)
            result["new_payment"] = new_payment
            result["new_rate"] = new_rate
            result["new_term_years"] = new_term_years
            
            # Calculate savings
            current_total = current_payment * current_term_months
            new_total = new_payment * (new_term_years * 12)
            result["savings"] = current_total - new_total
            result["savings_percentage"] = (result["savings"] / current_total * 100) if current_total > 0 else 0
        
        elif scenario_type == "consolidate":
            # Consolidation scenario (would need multiple loans)
            result["new_payment"] = current_payment
            result["savings"] = 0
        
        elif scenario_type == "target_payoff":
            # Target payoff scenario - calculate required payment for specific timeframe
            target_months = target_payoff_months or 12  # Default to 12 months
            required_result = self._calculate_required_payment_for_target_payoff(
                principal, current_rate, target_months
            )
            result["required_payment"] = required_result["required_monthly_payment"]
            result["target_payoff_months"] = target_months
            result["target_payoff_date"] = required_result["payoff_date"]
            result["total_interest"] = required_result["total_interest"]
            result["total_cost"] = required_result["total_cost"]
            result["new_payment"] = required_result["required_monthly_payment"]
            
            # Calculate how much more than current payment is needed
            extra_required = required_result["required_monthly_payment"] - current_payment
            result["extra_required"] = max(0, extra_required)
        
        else:
            result["new_payment"] = current_payment
            result["savings"] = 0
        
        # Always capture base formula for transparency
        monthly_rate = current_rate / 100 / 12
        result["base_formula"] = self._generate_payment_formula_latex(principal, monthly_rate, current_term_months)

        payments_for_steps = (
            target_payoff_months if scenario_type == "target_payoff" and target_payoff_months
            else int((new_term if new_term else current_term_months / 12) * 12) if scenario_type == "refinance"
            else current_term_months
        )

        rate_for_steps = (
            (new_rate if (scenario_type == "refinance" and new_rate is not None) else current_rate)
        )

        result["calculation_steps"] = self._build_monthly_payment_steps(
            principal=principal,
            annual_rate=rate_for_steps,
            num_payments=int(payments_for_steps),
            monthly_payment=result["new_payment"]
        )

        if scenario_type in ["current", "extra_payment"] and extra_payment > 0 and result.get("extra_payment_details"):
            extra_info = result["extra_payment_details"]
            result["calculation_steps"].extend(
                self._build_interest_savings_steps(
                    original_interest=extra_info["original_total_interest"],
                    new_interest=extra_info["total_interest"],
                    savings=extra_info["total_savings"]
                )
            )

        return result
    
    def _calculate_monthly_payment(self, principal: float, annual_rate: float, term_years: int) -> float:
        """Calculate monthly payment using amortization formula."""
        if annual_rate == 0:
            return principal / (term_years * 12)
        
        monthly_rate = annual_rate / 100 / 12
        total_payments = term_years * 12
        
        monthly_payment = principal * (monthly_rate * (1 + monthly_rate)**total_payments) / ((1 + monthly_rate)**total_payments - 1)
        return round(monthly_payment, 2)
    
    def _generate_payment_formula_latex(self, principal: float, monthly_rate: float, num_payments: int) -> str:
        """Generate LaTeX formula for monthly payment calculation."""
        return f"$$P = {principal:.2f} \\times \\frac{{{monthly_rate:.6f}(1 + {monthly_rate:.6f})^{{{num_payments}}}}}{{(1 + {monthly_rate:.6f})^{{{num_payments}}} - 1}}$$"
    
    def _generate_interest_savings_latex(self, original_interest: float, new_interest: float) -> str:
        """Generate LaTeX formula for interest savings."""
        savings = original_interest - new_interest
        return f"$$\\text{{Interest Savings}} = \\${original_interest:.2f} - \\${new_interest:.2f} = \\${savings:.2f}$$"

    def _build_monthly_payment_steps(self, principal: float, annual_rate: float, num_payments: int, monthly_payment: float) -> List[Dict[str, Any]]:
        """Create structured steps describing the monthly payment calculation."""
        monthly_rate = (annual_rate / 100) / 12 if annual_rate else 0
        steps: List[Dict[str, Any]] = [
            {
                "title": "Monthly payment formula",
                "description": "M = monthly payment, P = principal, r = monthly interest rate, n = total number of payments.",
                "latex": "M = P \\times \\frac{r(1+r)^n}{(1+r)^n - 1}",
                "display": True
            }
        ]

        steps.append(
            {
                "title": "Plug in your numbers",
                "description": f"P = ${principal:,.2f}, r = {monthly_rate * 100:.3f}% per month, n = {num_payments} payments.",
                "latex": self._build_monthly_payment_latex(principal, monthly_rate, num_payments),
                "display": True
            }
        )

        steps.append(
            {
                "title": "Calculated monthly payment",
                "description": f"Your monthly payment comes to approximately ${monthly_payment:,.2f}.",
                "latex": f"M = {monthly_payment:.2f}",
                "display": False
            }
        )

        return steps

    def _build_interest_savings_steps(self, original_interest: float, new_interest: float, savings: float) -> List[Dict[str, Any]]:
        """Create structured steps describing interest savings from extra payments."""
        return [
            {
                "title": "Interest savings formula",
                "description": "Savings = interest without extra payments minus interest with extra payments.",
                "latex": "\\text{Savings} = I_{\\text{original}} - I_{\\text{new}}",
                "display": True
            },
            {
                "title": "Plug in your numbers",
                "description": (
                    f"I_{{original}} = ${original_interest:,.2f}, I_{{new}} = ${new_interest:,.2f}."
                ),
                "latex": (
                    f"\\text{{Savings}} = \\${original_interest:.2f} - \\${new_interest:.2f} = \\${savings:.2f}"
                ),
                "display": True
            }
        ]

    def _build_monthly_payment_latex(self, principal: float, monthly_rate: float, num_payments: int) -> str:
        numerator = f"{monthly_rate:.6f}(1 + {monthly_rate:.6f})^{num_payments}"
        denominator = f"(1 + {monthly_rate:.6f})^{num_payments} - 1"
        return f"M = {principal:.2f} \\times \\frac{{{numerator}}}{{{denominator}}}"
    
    def _validate_calculation(self, principal: float, total_interest: float, months: int) -> bool:
        """Validate that calculations are reasonable to prevent errors."""
        # Interest should not be negative
        if total_interest < 0:
            return False
        
        # Interest should not exceed 3x principal (even for very long terms)
        if total_interest > principal * 3:
            return False
        
        # Months should be reasonable (not negative, not too high)
        if months < 0 or months > 600:  # 50 years max
            return False
        
        # Principal should be positive
        if principal <= 0:
            return False
        
        return True
    
    def _calculate_extra_payment_scenario(self, principal: float, annual_rate: float, 
                                        term_years: int, extra_payment: float) -> Dict[str, Any]:
        """Calculate scenario with extra payments."""
        base_payment = self._calculate_monthly_payment(principal, annual_rate, term_years)
        total_payment = base_payment + extra_payment
        
        # Calculate original total interest (without extra payments)
        original_months = term_years * 12
        original_total_interest = (base_payment * original_months) - principal
        
        if annual_rate == 0:
            months_to_payoff = principal / total_payment
            total_interest = 0
        else:
            monthly_rate = annual_rate / 100 / 12
            months_to_payoff = 0
            remaining_balance = principal
            total_interest = 0
            
            while remaining_balance > 0.01 and months_to_payoff < term_years * 12:
                interest_payment = remaining_balance * monthly_rate
                principal_payment = total_payment - interest_payment
                
                if principal_payment > remaining_balance:
                    principal_payment = remaining_balance
                    interest_payment = 0
                
                remaining_balance -= principal_payment
                total_interest += interest_payment
                months_to_payoff += 1
        
        months_saved = max(0, original_months - months_to_payoff)
        
        # Calculate actual interest savings (original interest - new interest)
        interest_savings = original_total_interest - total_interest
        interest_formula = self._generate_interest_savings_latex(original_total_interest, total_interest)
        
        # Validate calculations to prevent errors
        if not self._validate_calculation(principal, total_interest, months_to_payoff):
            raise ValueError(f"Calculation validation failed: principal=${principal}, interest=${total_interest}, months={months_to_payoff}")
        
        return {
            "monthly_payment": total_payment,
            "payoff_date": self._calculate_payoff_date(months_to_payoff / 12),
            "months_saved": months_saved,
            "total_interest": total_interest,
            "original_total_interest": original_total_interest,
            "total_savings": interest_savings,
            "formula": interest_formula
        }
    
    def _calculate_required_payment_for_target_payoff(self, principal: float, annual_rate: float, 
                                                    target_months: int) -> Dict[str, Any]:
        """Calculate required monthly payment to pay off loan in target timeframe."""
        if annual_rate == 0:
            required_payment = principal / target_months
            total_interest = 0
            monthly_rate = 0
        else:
            monthly_rate = annual_rate / 100 / 12
            # Use loan payment formula: P = [r*PV] / [1-(1+r)^-n]
            required_payment = (monthly_rate * principal) / (1 - (1 + monthly_rate) ** (-target_months))
            total_interest = (required_payment * target_months) - principal
        
        # Validate the calculation
        if not self._validate_calculation(principal, total_interest, target_months):
            raise ValueError(f"Target payoff calculation validation failed: principal=${principal}, interest=${total_interest}, months={target_months}")
        
        payment_formula = self._generate_payment_formula_latex(principal, monthly_rate, target_months) if annual_rate != 0 else None

        return {
            "required_monthly_payment": required_payment,
            "target_payoff_months": target_months,
            "total_interest": total_interest,
            "payoff_date": self._calculate_payoff_date(target_months / 12),
            "total_cost": principal + total_interest,
            "formula": payment_formula
        }
    
    def _calculate_scenarios(self, principal: float, annual_rate: float, term_years: int) -> Dict[str, Any]:
        """Calculate different loan scenarios."""
        scenarios = {}
        
        # Different terms
        for years in [10, 15, 20, 25, 30]:
            if years != term_years:
                payment = self._calculate_monthly_payment(principal, annual_rate, years)
                total_cost = payment * years * 12
                scenarios[f"{years}_year_term"] = {
                    "monthly_payment": payment,
                    "total_cost": total_cost,
                    "total_interest": total_cost - principal
                }
        
        # Different rates (refinancing scenarios)
        for rate in [3.0, 4.0, 5.0, 6.0, 7.0]:
            if abs(rate - annual_rate) > 0.1:
                payment = self._calculate_monthly_payment(principal, rate, term_years)
                total_cost = payment * term_years * 12
                scenarios[f"refinance_{rate}%"] = {
                    "monthly_payment": payment,
                    "total_cost": total_cost,
                    "total_interest": total_cost - principal,
                    "savings_vs_current": (self._calculate_monthly_payment(principal, annual_rate, term_years) * term_years * 12) - total_cost
                }
        
        return scenarios
    
    def _calculate_payoff_date(self, years: float) -> str:
        """Calculate payoff date."""
        payoff_date = datetime.now() + timedelta(days=years * 365)
        return payoff_date.strftime("%Y-%m-%d")
    
    def _generate_recommendations(self, loans: List[Dict[str, Any]], scenario_type: str, total_savings: float) -> List[str]:
        """Generate recommendations based on loan analysis."""
        recommendations = []
        
        if scenario_type in ["current", "extra_payment"]:
            if total_savings > 0:
                recommendations.append(f"Adding extra payments could save you ${total_savings:,.2f} over the life of your loans.")
            
            # Find highest rate loan
            highest_rate_loan = max(loans, key=lambda x: x["interest_rate_apr"])
            if highest_rate_loan["interest_rate_apr"] > 6.0:
                recommendations.append(f"Consider refinancing your highest rate loan ({highest_rate_loan['interest_rate_apr']}%) to save money.")
            
            # Check for multiple loans
            if len(loans) > 1:
                recommendations.append("You have multiple student loans. Consider consolidation to simplify payments.")
        
        elif scenario_type == "refinance":
            if total_savings > 0:
                recommendations.append(f"Refinancing could save you ${total_savings:,.2f} over the life of your loans.")
            else:
                recommendations.append("Refinancing may not save you money with current rates. Consider other strategies.")
        
        return recommendations
    
    def _generate_hypothetical_recommendations(self, principal: float, annual_rate: float, term_years: int) -> List[str]:
        """Generate recommendations for hypothetical loans."""
        recommendations = []
        
        if annual_rate > 6.0:
            recommendations.append("Consider refinancing if you can get a lower rate. Current rates are high.")
        
        if term_years > 20:
            recommendations.append("Longer terms mean lower monthly payments but more total interest. Consider shorter terms if affordable.")
        
        if principal > 50000:
            recommendations.append("Large loan amounts benefit most from extra payments. Even small extra payments can save thousands.")
        
        recommendations.append("Make sure to consider your other financial goals when choosing loan terms.")
        
        return recommendations
    
    def _generate_mathematical_explanation(self, loans: List[Dict[str, Any]], scenario_type: str, 
                                         extra_payment: float, new_rate: Optional[float], 
                                         new_term: Optional[int]) -> str:
        """Generate detailed mathematical explanation of the calculations."""
        if not loans:
            return ""
        
        loan = loans[0]  # Focus on first loan for explanation
        principal = loan["current_principal"]
        current_rate = loan["interest_rate_apr"]
        current_term_months = loan["term_months"]
        current_payment = loan["min_payment_mo"]
        
        explanation = "## 📊 Mathematical Explanation\n\n"
        
        # Basic amortization formula
        explanation += "### Monthly Payment Formula:\n"
        explanation += "```\n"
        explanation += "      r(1+r)^n\n"
        explanation += "M = P ─────────\n"
        explanation += "     (1+r)^n - 1\n"
        explanation += "```\n\n"
        
        explanation += "**Where:**\n"
        explanation += f"• **P** = Principal amount = ${principal:,.2f}\n"
        explanation += f"• **r** = Monthly interest rate = {current_rate}% ÷ 12 = {current_rate/12:.4f}% = {current_rate/1200:.6f}\n"
        explanation += f"• **n** = Total number of payments = {current_term_months} months\n\n"
        
        # Step-by-step calculation
        explanation += "### Step-by-Step Calculation:\n\n"
        explanation += "**Step 1: Calculate (1+r)^n**\n"
        explanation += f"```\n"
        explanation += f"(1+r)^n = (1 + {current_rate/1200:.6f})^{current_term_months}\n"
        explanation += f"        = {1 + current_rate/1200:.6f}^{current_term_months}\n"
        explanation += f"        = {pow(1 + current_rate/1200, current_term_months):.6f}\n"
        explanation += f"```\n\n"
        
        explanation += "**Step 2: Calculate numerator**\n"
        explanation += f"```\n"
        explanation += f"r(1+r)^n = {current_rate/1200:.6f} × {pow(1 + current_rate/1200, current_term_months):.6f}\n"
        explanation += f"         = {current_rate/1200 * pow(1 + current_rate/1200, current_term_months):.6f}\n"
        explanation += f"```\n\n"
        
        explanation += "**Step 3: Calculate denominator**\n"
        explanation += f"```\n"
        explanation += f"(1+r)^n - 1 = {pow(1 + current_rate/1200, current_term_months):.6f} - 1\n"
        explanation += f"            = {pow(1 + current_rate/1200, current_term_months) - 1:.6f}\n"
        explanation += f"```\n\n"
        
        explanation += "**Step 4: Calculate monthly payment**\n"
        explanation += f"```\n"
        explanation += f"      {current_rate/1200 * pow(1 + current_rate/1200, current_term_months):.6f}\n"
        explanation += f"M = ${principal:,.2f} × ─────────────────────────────\n"
        explanation += f"      {pow(1 + current_rate/1200, current_term_months) - 1:.6f}\n"
        explanation += f"\nM = ${principal:,.2f} × {current_rate/1200 * pow(1 + current_rate/1200, current_term_months) / (pow(1 + current_rate/1200, current_term_months) - 1):.6f}\n"
        explanation += f"M = ${current_payment:.2f}\n"
        explanation += f"```\n\n"
        
        # Extra payment scenario
        if scenario_type in ["current", "extra_payment"] and extra_payment > 0:
            explanation += "### Extra Payment Analysis:\n\n"
            explanation += f"**New Monthly Payment:**\n"
            explanation += f"```\n"
            explanation += f"New Payment = Current Payment + Extra Payment\n"
            explanation += f"New Payment = ${current_payment:.2f} + ${extra_payment:.2f}\n"
            explanation += f"New Payment = ${current_payment + extra_payment:.2f}\n"
            explanation += f"```\n\n"
            
            explanation += "**Interest Savings Calculation:**\n"
            explanation += "```\n"
            explanation += "Total Interest = (Monthly Payment × Total Months) - Principal\n"
            explanation += f"Current Total Interest = (${current_payment:.2f} × {current_term_months}) - ${principal:,.2f}\n"
            explanation += f"Current Total Interest = ${current_payment * current_term_months:,.2f} - ${principal:,.2f}\n"
            explanation += f"Current Total Interest = ${current_payment * current_term_months - principal:,.2f}\n"
            explanation += f"```\n\n"
            
            # Calculate new payoff with extra payment
            new_payment = current_payment + extra_payment
            monthly_rate = current_rate / 1200
            remaining_balance = principal
            months_paid = 0
            total_interest_new = 0
            
            while remaining_balance > 0.01 and months_paid < current_term_months:
                interest_payment = remaining_balance * monthly_rate
                principal_payment = new_payment - interest_payment
                if principal_payment > remaining_balance:
                    principal_payment = remaining_balance
                remaining_balance -= principal_payment
                total_interest_new += interest_payment
                months_paid += 1
            
            explanation += f"**With Extra Payment:**\n"
            explanation += f"```\n"
            explanation += f"New Total Interest = ${total_interest_new:,.2f}\n"
            explanation += f"Interest Savings = ${current_payment * current_term_months - principal:,.2f} - ${total_interest_new:,.2f}\n"
            explanation += f"Interest Savings = ${(current_payment * current_term_months - principal) - total_interest_new:,.2f}\n"
            explanation += f"Months to Payoff = {months_paid} months\n"
            explanation += f"Months Saved = {current_term_months} - {months_paid} = {current_term_months - months_paid} months\n"
            explanation += f"```\n\n"
        
        # Refinancing scenario
        elif scenario_type == "refinance" and new_rate:
            explanation += "### Refinancing Analysis:\n\n"
            explanation += f"**New Interest Rate:** {new_rate}%\n"
            explanation += f"**New Monthly Rate:** {new_rate/12:.4f}% = {new_rate/1200:.6f}\n\n"
            
            new_term_years = new_term if new_term else current_term_months / 12
            new_term_months = new_term_years * 12
            new_payment = self._calculate_monthly_payment(principal, new_rate, new_term_years)
            
            explanation += f"**New Monthly Payment Calculation:**\n"
            explanation += f"```\n"
            explanation += f"      {new_rate/1200:.6f}(1+{new_rate/1200:.6f})^{new_term_months:.0f}\n"
            explanation += f"M = ${principal:,.2f} × ──────────────────────────\n"
            explanation += f"     (1+{new_rate/1200:.6f})^{new_term_months:.0f} - 1\n"
            explanation += f"\nM = ${new_payment:.2f}\n"
            explanation += f"```\n\n"
            
            explanation += "**Savings Analysis:**\n"
            explanation += f"```\n"
            explanation += f"Current Total Cost = ${current_payment:.2f} × {current_term_months} = ${current_payment * current_term_months:,.2f}\n"
            explanation += f"New Total Cost = ${new_payment:.2f} × {new_term_months:.0f} = ${new_payment * new_term_months:,.2f}\n"
            explanation += f"Total Savings = ${current_payment * current_term_months:,.2f} - ${new_payment * new_term_months:,.2f}\n"
            explanation += f"Total Savings = ${(current_payment * current_term_months) - (new_payment * new_term_months):,.2f}\n"
            explanation += f"```\n\n"
        
        return explanation
