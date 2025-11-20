"""
Evaluation Debt Optimizer Tool

Specialized version of debt_optimizer_tool.py for evaluation purposes.
Fixes bugs in hypothetical debt calculations while maintaining exact API compatibility.
Used exclusively for generating ground truth answers for evaluation.
"""

import math
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta


class EvaluationDebtOptimizer:
    """
    Specialized debt optimizer for evaluation purposes only.

    This tool fixes critical bugs in the production debt_optimizer_tool:
    1. Properly calculates monthly payments for hypothetical debts in "current" scenarios
    2. Uses term_months correctly when provided in debt objects
    3. Maintains exact API compatibility with production tool
    """

    # Debt type configurations (copied from production tool)
    DEBT_TYPES = {
        "student": {
            "name": "Student Loan",
            "typical_term_years": [10, 15, 20, 25],
            "typical_rates": [3.0, 4.0, 5.0, 6.0, 7.0],
            "has_fixed_term": True
        },
        "auto": {
            "name": "Auto Loan",
            "typical_term_years": [3, 4, 5, 6, 7],
            "typical_rates": [3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0],
            "has_fixed_term": True
        },
        "credit_card": {
            "name": "Credit Card",
            "typical_term_years": None,  # No fixed term
            "typical_rates": [15.0, 18.0, 20.0, 24.0, 28.0],
            "has_fixed_term": False,
            "min_payment_pct": 0.02,  # 2% minimum payment default
            "fixed_min_payment": 25.0
        },
        "personal": {
            "name": "Personal Loan",
            "typical_term_years": [2, 3, 5, 7],
            "typical_rates": [6.0, 8.0, 10.0, 12.0, 15.0],
            "has_fixed_term": True
        },
        "mortgage": {
            "name": "Mortgage",
            "typical_term_years": [15, 20, 30],
            "typical_rates": [3.0, 3.5, 4.0, 4.5, 5.0, 6.0],
            "has_fixed_term": True
        }
    }

    def calculate_monthly_payment(self, principal: float, apr: float, term_months: int) -> float:
        """
        Calculate monthly payment using amortization formula.

        FIX: This method correctly uses term_months instead of term_years.
        """
        if apr == 0:
            return principal / term_months

        monthly_rate = apr / 100 / 12
        numerator = monthly_rate * (1 + monthly_rate) ** term_months
        denominator = (1 + monthly_rate) ** term_months - 1

        if denominator == 0:
            return principal / term_months

        monthly_payment = principal * (numerator / denominator)
        return round(monthly_payment, 2)

    def calculate_credit_card_min_payment(self, balance: float, annual_rate: float) -> float:
        """Calculate minimum payment for credit card."""
        # Typical: 2% of balance or $25, whichever is greater
        min_pct_payment = balance * 0.02
        fixed_min = 25.0
        return max(min_pct_payment, fixed_min)

    def simulate_debt_payoff(self, principal: float, apr: float,
                           monthly_payment: float, extra_payment: float = 0) -> Dict[str, Any]:
        """
        Simulate debt payoff and calculate total interest.
        """
        monthly_rate = apr / 100 / 12
        balance = principal
        total_interest = 0
        months = 0
        max_iterations = 600  # 50 years max

        while balance > 0.01 and months < max_iterations:
            interest = balance * monthly_rate
            total_interest += interest
            principal_payment = monthly_payment + extra_payment - interest
            principal_payment = max(principal_payment, 0)  # Don't go negative
            balance -= principal_payment
            months += 1

            if balance <= 0:
                break

        total_cost = principal + total_interest
        payoff_date = datetime.now() + timedelta(days=months * 30)

        return {
            "total_interest": total_interest,
            "total_cost": total_cost,
            "months": months,
            "payoff_date": payoff_date.strftime("%Y-%m-%d"),
            "total_savings": 0  # Will be calculated by caller
        }

    def process_hypothetical_debts(self, debts: List[Dict[str, Any]], scenario_type: str,
                                 extra_payment: float = 0, target_payoff_months: Optional[int] = None,
                                 new_rate: Optional[float] = None, new_term_years: Optional[int] = None,
                                 refinancing_fee: float = 0, payment_frequency: str = "monthly",
                                 credit_card_promo_rate: Optional[float] = None,
                                 credit_card_promo_months: Optional[int] = None,
                                 debt_type: str = "all") -> Dict[str, Any]:
        """
        Process hypothetical debts with proper calculations.

        FIX: This method correctly calculates monthly payments for "current" scenarios
        instead of defaulting to 0.
        """
        try:
            # Validate hypothetical debts have required fields
            for debt in debts:
                required_fields = ['principal', 'interest_rate_apr', 'debt_type']
                missing_fields = [f for f in required_fields if f not in debt]
                if missing_fields:
                    return {
                        "status": "error",
                        "error": f"Missing required fields in debt: {', '.join(missing_fields)}"
                    }

                # Validate debt type
                if debt['debt_type'] not in self.DEBT_TYPES:
                    return {
                        "status": "error",
                        "error": f"Invalid debt_type: {debt['debt_type']}. Must be one of: {', '.join(self.DEBT_TYPES.keys())}"
                    }

            # Execute scenario-specific calculations
            if scenario_type == "avalanche":
                return self._calculate_avalanche_strategy(debts, extra_payment)
            elif scenario_type == "snowball":
                return self._calculate_snowball_strategy(debts, extra_payment)
            elif scenario_type == "consolidate":
                return self._calculate_consolidation(debts, new_rate, new_term_years, refinancing_fee)
            elif scenario_type == "refinance":
                return self._calculate_refinancing(debts, new_rate, new_term_years, refinancing_fee)
            else:
                # current, extra_payment, target_payoff
                return self._calculate_standard_scenarios(
                    debts, scenario_type, extra_payment, target_payoff_months,
                    new_rate, new_term_years, payment_frequency,
                    credit_card_promo_rate, credit_card_promo_months, debt_type
                )

        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to calculate hypothetical debts: {str(e)}"
            }

    def _calculate_standard_scenarios(self, debts: List[Dict[str, Any]], scenario_type: str,
                                    extra_payment: float, target_payoff_months: Optional[int],
                                    new_rate: Optional[float], new_term_years: Optional[int],
                                    payment_frequency: str, credit_card_promo_rate: Optional[float],
                                    credit_card_promo_months: Optional[int], debt_type: str = "all") -> Dict[str, Any]:
        """Calculate standard scenarios (current, extra_payment, target_payoff)."""

        results = {
            "status": "success",
            "scenario_type": scenario_type,
            "debts": [],
            "summary": {},
            "recommendations": [],
            "latex_formulas": [],
            "calculation_steps": []
        }

        total_current_payment = 0
        total_new_payment = 0
        total_savings = 0
        total_principal = 0

        for debt in debts:
            debt_result = self._calculate_debt_scenario(
                debt, extra_payment, scenario_type, new_rate, new_term_years,
                target_payoff_months, payment_frequency, credit_card_promo_rate,
                credit_card_promo_months
            )
            results["debts"].append(debt_result)

            total_current_payment += debt_result["current_payment"]
            total_new_payment += debt_result["new_payment"]
            total_savings += debt_result.get("savings", 0)
            total_principal += debt["principal"]

            # Collect LaTeX formulas
            if debt_result.get("base_formula"):
                results["latex_formulas"].append(debt_result["base_formula"])

            extra_details = debt_result.get("extra_payment_details")
            if extra_details and extra_details.get("formula"):
                results["latex_formulas"].append(extra_details["formula"])

            if debt_result.get("calculation_steps"):
                for step in debt_result["calculation_steps"]:
                    if step.get("latex") and step.get("display"):
                        results["latex_formulas"].append(step["latex"])

        # Generate summary
        results["summary"] = {
            "total_debts": len(debts),
            "total_principal": total_principal,
            "total_current_payment": total_current_payment,
            "total_new_payment": total_new_payment,
            "total_savings": total_savings,
            "savings_percentage": (total_savings / total_current_payment * 100) if total_current_payment > 0 else 0
        }

        # Generate recommendations
        results["recommendations"] = self._generate_recommendations(results["summary"], debts)

        # Store calculation details for frontend display
        global _last_calculation_details
        _last_calculation_details = results

        return results

    def _calculate_debt_scenario(self, debt: Dict[str, Any], extra_payment: float,
                                scenario_type: str, new_rate: Optional[float],
                                new_term_years: Optional[int], target_payoff_months: Optional[int],
                                payment_frequency: str, credit_card_promo_rate: Optional[float],
                                credit_card_promo_months: Optional[int]) -> Dict[str, Any]:
        """Calculate different scenarios for a single debt."""

        principal = debt.get("principal") or debt.get("current_principal")
        current_rate = debt["interest_rate_apr"]

        # FIX: Use term_months from debt object if provided, otherwise calculate from typical terms
        term_months = debt.get("term_months")
        if term_months is None:
            # Calculate typical term based on debt type
            debt_type = debt.get("debt_type", "personal")
            if debt_type in self.DEBT_TYPES and self.DEBT_TYPES[debt_type]["typical_term_years"]:
                term_months = self.DEBT_TYPES[debt_type]["typical_term_years"][-1] * 12  # Use longest typical term
            else:
                term_months = 999  # Default for credit cards

        current_payment = debt.get("min_payment_mo", 0)
        debt_type = debt.get("debt_type", "personal")

        # Handle credit card minimum payment if not provided
        if debt_type == "credit_card" and current_payment == 0:
            current_payment = self.calculate_credit_card_min_payment(principal, current_rate)

        result = {
            "debt_id": debt.get("debt_id", "hypothetical"),
            "debt_type": debt_type,
            "current_principal": principal,
            "current_rate": current_rate,
            "current_payment": current_payment,
            "current_term_months": term_months
        }

        if scenario_type == "current":
            # FIX: Calculate proper monthly payment for hypothetical debts in current scenario
            if debt_type == "credit_card":
                new_payment = current_payment
            else:
                # Calculate proper amortization payment
                new_payment = self.calculate_monthly_payment(principal, current_rate, term_months)
            result["new_payment"] = new_payment
            result["extra_payment"] = 0

        elif scenario_type == "extra_payment":
            # For extra payment, first calculate the regular payment, then add extra
            if debt_type == "credit_card":
                base_payment = current_payment
            else:
                base_payment = self.calculate_monthly_payment(principal, current_rate, term_months)

            new_payment = base_payment + extra_payment
            result["new_payment"] = new_payment
            result["extra_payment"] = extra_payment

            if extra_payment > 0:
                # Calculate savings with extra payment
                if debt_type == "credit_card":
                    savings_result = self._calculate_credit_card_payoff(
                        principal, current_rate, new_payment, credit_card_promo_rate, credit_card_promo_months
                    )
                else:
                    savings_result = self._calculate_extra_payment_scenario(
                        principal, current_rate, term_months / 12, extra_payment, base_payment
                    )

                result["savings"] = savings_result["total_savings"]
                result["new_payoff_date"] = savings_result.get("payoff_date")
                result["months_saved"] = savings_result.get("months_saved", 0)
                result["extra_payment_details"] = savings_result

        elif scenario_type == "refinance" and new_rate:
            # Refinancing scenario
            new_term = new_term_years if new_term_years else term_months / 12
            new_payment = self.calculate_monthly_payment(principal, new_rate, int(new_term * 12))
            result["new_payment"] = new_payment
            result["new_rate"] = new_rate
            result["new_term_years"] = new_term

            # Calculate savings
            current_total = current_payment * term_months
            new_total = new_payment * (new_term * 12)
            result["savings"] = current_total - new_total
            result["savings_percentage"] = (result["savings"] / current_total * 100) if current_total > 0 else 0

        elif scenario_type == "target_payoff":
            # Target payoff scenario
            target_months = target_payoff_months or 12
            required_result = self._calculate_required_payment_for_target_payoff(
                principal, current_rate, target_months
            )
            result["required_payment"] = required_result["required_monthly_payment"]
            result["target_payoff_months"] = target_months
            result["target_payoff_date"] = required_result["payoff_date"]
            result["total_interest"] = required_result["total_interest"]
            result["total_cost"] = required_result["total_cost"]
            result["new_payment"] = required_result["required_monthly_payment"]
            result["extra_required"] = max(0, required_result["required_monthly_payment"] - current_payment)

        else:
            result["new_payment"] = current_payment
            result["savings"] = 0

        # Add base formula and calculation steps
        monthly_rate = current_rate / 100 / 12
        result["base_formula"] = self._generate_payment_formula_latex(principal, monthly_rate, term_months)

        # Determine parameters for calculation steps
        payments_for_steps = (
            target_payoff_months if scenario_type == "target_payoff" and target_payoff_months
            else int((new_term_years if new_term_years else term_months / 12) * 12) if scenario_type == "refinance"
            else term_months
        )

        rate_for_steps = (
            new_rate if (scenario_type == "refinance" and new_rate is not None) else current_rate
        )

        result["calculation_steps"] = self._build_monthly_payment_steps(
            principal=principal,
            annual_rate=rate_for_steps,
            num_payments=int(payments_for_steps),
            monthly_payment=result["new_payment"]
        )

        return result

    def _calculate_extra_payment_scenario(self, principal: float, apr: float, term_years: float,
                                       extra_payment: float, base_payment: float) -> Dict[str, Any]:
        """Calculate savings from extra payment."""

        # Simulate both scenarios
        original_result = self.simulate_debt_payoff(principal, apr, base_payment, 0)
        extra_result = self.simulate_debt_payoff(principal, apr, base_payment, extra_payment)

        total_savings = original_result["total_interest"] - extra_result["total_interest"]
        months_saved = original_result["months"] - extra_result["months"]

        return {
            "original_total_interest": original_result["total_interest"],
            "new_total_interest": extra_result["total_interest"],
            "total_savings": total_savings,
            "months_saved": months_saved,
            "payoff_date": extra_result["payoff_date"],
            "original_payoff_months": original_result["months"],
            "new_payoff_months": extra_result["months"]
        }

    def _calculate_required_payment_for_target_payoff(self, principal: float, apr: float,
                                                   target_months: int) -> Dict[str, Any]:
        """Calculate required monthly payment to pay off debt in target months."""

        # Binary search for required payment
        low = principal / target_months  # Minimum payment
        high = principal * (1 + apr/100/12) ** target_months / target_months * 2  # High estimate

        for _ in range(50):  # Binary search iterations
            mid = (low + high) / 2
            result = self.simulate_debt_payoff(principal, apr, mid, 0)
            if result["months"] <= target_months:
                high = mid
            else:
                low = mid

        required_payment = round((low + high) / 2, 2)
        final_result = self.simulate_debt_payoff(principal, apr, required_payment, 0)

        return {
            "required_monthly_payment": required_payment,
            "payoff_date": final_result["payoff_date"],
            "total_interest": final_result["total_interest"],
            "total_cost": final_result["total_cost"]
        }

    def _calculate_avalanche_strategy(self, debts: List[Dict[str, Any]], extra_payment: float) -> Dict[str, Any]:
        """Calculate avalanche strategy (highest interest first)."""
        # Sort debts by interest rate (highest first)
        sorted_debts = sorted(debts, key=lambda x: x["interest_rate_apr"], reverse=True)

        total_interest = 0
        total_payoff_months = 0
        payoff_timeline = []

        for i, debt in enumerate(sorted_debts):
            principal = debt["principal"]
            rate = debt["interest_rate_apr"]
            term_months = debt.get("term_months", 120)  # Default 10 years

            # Calculate minimum payment
            if debt["debt_type"] == "credit_card":
                min_payment = self.calculate_credit_card_min_payment(principal, rate)
            else:
                min_payment = self.calculate_monthly_payment(principal, rate, term_months)

            # For avalanche, only first debt gets extra payment
            payment = min_payment + (extra_payment if i == 0 else 0)

            result = self.simulate_debt_payoff(principal, rate, payment, 0)
            total_interest += result["total_interest"]
            total_payoff_months = max(total_payoff_months, result["months"])

            payoff_timeline.append({
                "debt_type": debt["debt_type"],
                "principal": principal,
                "rate": rate,
                "payoff_months": result["months"],
                "interest_paid": result["total_interest"]
            })

        return {
            "status": "success",
            "strategy": "avalanche",
            "total_interest_paid": total_interest,
            "total_payoff_months": total_payoff_months,
            "payoff_timeline": payoff_timeline,
            "total_interest_saved": 0  # Would need original calculation to compare
        }

    def _calculate_snowball_strategy(self, debts: List[Dict[str, Any]], extra_payment: float) -> Dict[str, Any]:
        """Calculate snowball strategy (smallest balance first)."""
        # Sort debts by principal (smallest first)
        sorted_debts = sorted(debts, key=lambda x: x["principal"])

        total_interest = 0
        total_payoff_months = 0
        payoff_timeline = []

        for i, debt in enumerate(sorted_debts):
            principal = debt["principal"]
            rate = debt["interest_rate_apr"]
            term_months = debt.get("term_months", 120)  # Default 10 years

            # Calculate minimum payment
            if debt["debt_type"] == "credit_card":
                min_payment = self.calculate_credit_card_min_payment(principal, rate)
            else:
                min_payment = self.calculate_monthly_payment(principal, rate, term_months)

            # For snowball, only first debt gets extra payment
            payment = min_payment + (extra_payment if i == 0 else 0)

            result = self.simulate_debt_payoff(principal, rate, payment, 0)
            total_interest += result["total_interest"]
            total_payoff_months = max(total_payoff_months, result["months"])

            payoff_timeline.append({
                "debt_type": debt["debt_type"],
                "principal": principal,
                "rate": rate,
                "payoff_months": result["months"],
                "interest_paid": result["total_interest"]
            })

        return {
            "status": "success",
            "strategy": "snowball",
            "total_interest_paid": total_interest,
            "total_payoff_months": total_payoff_months,
            "payoff_timeline": payoff_timeline,
            "total_interest_saved": 0  # Would need original calculation to compare
        }

    def _calculate_consolidation(self, debts: List[Dict[str, Any]], new_rate: float,
                               new_term_years: int, refinancing_fee: float) -> Dict[str, Any]:
        """Calculate debt consolidation."""

        total_principal = sum(debt["principal"] for debt in debts)
        new_term_months = new_term_years * 12
        new_payment = self.calculate_monthly_payment(total_principal, new_rate, new_term_months)

        # Calculate original total payments
        original_total_payment = 0
        for debt in debts:
            principal = debt["principal"]
            rate = debt["interest_rate_apr"]
            term_months = debt.get("term_months", 120)
            if debt["debt_type"] == "credit_card":
                payment = self.calculate_credit_card_min_payment(principal, rate)
            else:
                payment = self.calculate_monthly_payment(principal, rate, term_months)
            original_total_payment += payment

        monthly_savings = original_total_payment - new_payment
        total_savings = monthly_savings * new_term_months - refinancing_fee

        # Break-even analysis
        break_even_months = refinancing_fee / monthly_savings if monthly_savings > 0 else float('inf')

        return {
            "status": "success",
            "scenario_type": "consolidate",
            "consolidation_scenario": {
                "total_principal": total_principal,
                "new_rate": new_rate,
                "new_term_years": new_term_years,
                "new_monthly_payment": new_payment,
                "monthly_savings": monthly_savings,
                "total_savings": total_savings,
                "refinancing_fee": refinancing_fee,
                "break_even_analysis": {
                    "break_even_months": break_even_months,
                    "break_even_years": break_even_months / 12
                }
            }
        }

    def _calculate_refinancing(self, debts: List[Dict[str, Any]], new_rate: float,
                             new_term_years: int, refinancing_fee: float) -> Dict[str, Any]:
        """Calculate refinancing for single debt."""

        debt = debts[0]  # Assume single debt for refinancing
        principal = debt["principal"]
        current_rate = debt["interest_rate_apr"]
        current_term_months = debt.get("term_months", 120)

        # Calculate current payment
        if debt["debt_type"] == "credit_card":
            current_payment = self.calculate_credit_card_min_payment(principal, current_rate)
        else:
            current_payment = self.calculate_monthly_payment(principal, current_rate, current_term_months)

        # Calculate new payment
        new_term_months = new_term_years * 12
        new_payment = self.calculate_monthly_payment(principal, new_rate, new_term_months)

        monthly_savings = current_payment - new_payment
        total_savings = monthly_savings * new_term_months - refinancing_fee

        # Break-even analysis
        break_even_months = refinancing_fee / monthly_savings if monthly_savings > 0 else float('inf')

        return {
            "status": "success",
            "scenario_type": "refinance",
            "summary": {
                "current_payment": current_payment,
                "new_payment": new_payment,
                "monthly_savings": monthly_savings,
                "total_savings": total_savings,
                "refinancing_fee": refinancing_fee,
                "break_even_analysis": {
                    "break_even_months": break_even_months,
                    "break_even_years": break_even_months / 12
                }
            }
        }

    def _generate_payment_formula_latex(self, principal: float, monthly_rate: float, term_months: int) -> str:
        """Generate LaTeX formula for monthly payment calculation."""
        return f"$$M = {principal:,.0f} \\times \\frac{{{monthly_rate:.6f}(1 + {monthly_rate:.6f})^{{{term_months}}}}}{{(1 + {monthly_rate:.6f})^{{{term_months}}} - 1}}$$"

    def _build_monthly_payment_steps(self, principal: float, annual_rate: float,
                                   num_payments: int, monthly_payment: float) -> List[Dict[str, Any]]:
        """Build calculation steps for monthly payment."""

        monthly_rate = annual_rate / 100 / 12

        return [
            {
                "title": "Monthly payment formula",
                "description": "M = monthly payment, P = principal, r = monthly interest rate, n = total number of payments.",
                "latex": "M = P \\times \\frac{r(1+r)^n}{(1+r)^n - 1}",
                "display": True
            },
            {
                "title": "Plug in your numbers",
                "description": f"P = ${principal:,.0f}, r = {monthly_rate:.1%} per month, n = {num_payments} payments.",
                "latex": f"M = {principal:,.0f} \\times \\frac{{{monthly_rate:.6f}(1 + {monthly_rate:.6f})^{{{num_payments}}}}}{{(1 + {monthly_rate:.6f})^{{{num_payments}}} - 1}}",
                "display": True
            },
            {
                "title": "Calculated monthly payment",
                "description": f"Your monthly payment comes to approximately ${monthly_payment:.2f}.",
                "latex": f"M = {monthly_payment:.2f}",
                "display": False
            }
        ]

    def _generate_recommendations(self, summary: Dict[str, Any], debts: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []

        # Check for high-interest debts
        high_interest_debts = [d for d in debts if d["interest_rate_apr"] > 15]
        if high_interest_debts:
            recommendations.append(f"You have {len(high_interest_debts)} high-interest debt(s). Consider refinancing or using the avalanche method.")

        # Check savings potential
        if summary.get("total_savings", 0) > 0:
            recommendations.append(f"This scenario could save you ${summary['total_savings']:,.0f} in total payments.")

        return recommendations


# Global variable to store last calculation details (for compatibility)
_last_calculation_details: Optional[Dict[str, Any]] = None

def get_last_calculation_details() -> Optional[Dict[str, Any]]:
    """Retrieve the last captured calculation details."""
    return _last_calculation_details

def clear_calculation_details():
    """Clear the captured calculation details."""
    global _last_calculation_details
    _last_calculation_details = None
