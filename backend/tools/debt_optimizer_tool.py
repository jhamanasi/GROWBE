"""
Debt Optimizer Tool for Financial Advisory Agent.

Universal debt calculator supporting all debt types (student, auto, credit_card, personal, mortgage)
with comprehensive scenarios including refinancing, consolidation, and payoff strategies.
"""

import sqlite3
import math
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from .base_tool import BaseTool
from pathlib import Path

# Module-level variable to store last calculation details for frontend display
_last_calculation_details: Optional[Dict[str, Any]] = None

def get_last_calculation_details() -> Optional[Dict[str, Any]]:
    """Retrieve the last captured calculation details."""
    return _last_calculation_details

def clear_calculation_details():
    """Clear the captured calculation details."""
    global _last_calculation_details
    _last_calculation_details = None


class DebtOptimizerTool(BaseTool):
    """
    Universal debt calculator and optimizer.
    
    Handles all debt types with comprehensive scenarios:
    - Payment calculations with multiple frequencies
    - Refinancing analysis with break-even calculations
    - Extra payment strategies and target payoff
    - Avalanche and snowball debt payoff methods
    - Multi-debt consolidation
    - Credit card specific features (min payments, 0% promos, utilization)
    """
    
    # Debt type configurations
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
    
    # Rate qualification matrix based on credit score
    RATE_QUALIFICATION = {
        "excellent": {"min_score": 740, "rate_adjustment": 0.0, "description": "Excellent credit"},
        "good": {"min_score": 680, "rate_adjustment": 0.25, "description": "Good credit"},
        "fair": {"min_score": 620, "rate_adjustment": 0.75, "description": "Fair credit"},
        "poor": {"min_score": 580, "rate_adjustment": 1.5, "description": "Poor credit"}
    }
    
    def __init__(self):
        super().__init__()
        import os
        
        db_path = os.getenv("SQLITE_DB_PATH", "data/financial_data.db")
        if not os.path.isabs(db_path):
            BASE_DIR = Path(__file__).parent.parent
            self.db_path = str(BASE_DIR / db_path)
        else:
            self.db_path = db_path
    
    @property
    def name(self) -> str:
        """Return the tool name."""
        return "debt_optimizer"
    
    @property
    def description(self) -> str:
        """Return the tool description."""
        return """Universal debt calculator and optimizer for all debt types (student, auto, credit_card, personal, mortgage).

        This tool handles:
        1. All debt types with type-specific features
        2. Payment calculations with multiple frequencies (monthly, biweekly, weekly)
        3. Refinancing analysis with break-even calculations
        4. Extra payment strategies and target payoff scenarios
        5. Avalanche and snowball debt payoff methods
        6. Multi-debt consolidation analysis
        7. Credit card specific features (min payments, 0% promos, utilization impact)
        8. Comprehensive LaTeX formula display

        IMPORTANT: BEFORE CALLING THIS TOOL
        - Check if the user has provided ALL required information
        - If information is missing, ASK the user for it first (do NOT call this tool)
        - Only call this tool when you have ALL required parameters
        
        REQUIRED PARAMETERS FOR SCENARIO B (hypothetical calculations):
        You MUST provide ONE of these two options:
        
        OPTION 1 (Preferred): debts parameter as a list of dictionaries
        - debts: [{"principal": 40000, "interest_rate_apr": 4.0, "debt_type": "student"}]
        
        OPTION 2 (Fallback): Individual parameters (will be auto-converted to debts list)
        - principal: Loan amount as a NUMBER (e.g., 40000 for $40,000, NOT "$40,000")
        - interest_rate_apr: Interest rate as a NUMBER (e.g., 4.0 for 4% APR, NOT 0.04 or "4%")
        - debt_type: One of these exact strings: "student", "auto", "credit_card", "personal", "mortgage"
        
        For target payoff scenarios, also provide:
        - target_payoff_months: Number of months (e.g., 12 for 1 year, NOT "12 months" or "1 year")
        
        EXAMPLE CALLS:
        - For target payoff: debt_optimizer(principal=40000, interest_rate_apr=4.0, debt_type="student", target_payoff_months=12)
        - For current payment: debt_optimizer(principal=40000, interest_rate_apr=4.0, debt_type="student")
        
        ERROR HANDLING:
        If ANY required parameter is missing, the tool will return a user-friendly error message.
        When you receive an error with 'stop_retrying: True', DO NOT retry the tool.
        Present the error message directly to the user exactly as written.

        Args:
            customer_id: Customer ID to fetch existing debts (required for Scenario A, omit for Scenario B)
            debts: List of debt dictionaries for hypothetical scenarios (REQUIRED for Scenario B)
                Example: [{"principal": 40000, "interest_rate_apr": 4.0, "debt_type": "student"}]
            scenario_type: Type of analysis - current/extra_payment/target_payoff/refinance/avalanche/snowball/consolidate (default: current)
            target_payoff_months: Target payoff timeframe in months (REQUIRED for target_payoff scenario)
            extra_payment: Additional monthly payment amount (optional, default: 0)
            new_rate: New interest rate for refinancing (required for refinance/consolidate scenarios)
            new_term_years: New term in years for refinancing (optional)
            refinancing_fee: Origination/closing costs for refinancing (optional, default: 0)
            credit_score: Credit score for rate qualification (optional)
            payment_frequency: Payment frequency - monthly/biweekly/weekly (optional, default: monthly)
            credit_card_promo_rate: Promotional APR for credit cards (optional)
            credit_card_promo_months: Promotional period in months (optional)
            
        Returns:
            Comprehensive debt optimization analysis with scenarios, savings, formulas, and recommendations
            
        ERROR HANDLING:
        If required parameters are missing, the tool will return an error. DO NOT retry the tool call.
        Instead, ask the user for the missing information and then call the tool again with all required parameters.
        """
    
    def execute(
        self,
        customer_id: Optional[str] = None,
        debt_type: str = "all",
        debts: Optional[List[Dict[str, Any]]] = None,
        scenario_type: str = "current",
        extra_payment: float = 0.0,
        target_payoff_months: Optional[int] = None,
        new_rate: Optional[float] = None,
        new_term_years: Optional[int] = None,
        refinancing_fee: float = 0.0,
        credit_score: Optional[int] = None,
        payment_frequency: str = "monthly",
        credit_card_promo_rate: Optional[float] = None,
        credit_card_promo_months: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute the debt optimization analysis.
        
        Args:
            customer_id: Customer ID for existing users (Scenario A)
            debt_type: Type of debt to analyze ('all', 'student', 'auto', 'credit_card', etc.)
            debts: List of hypothetical debts for new users (Scenario B)
            scenario_type: Analysis type ('current', 'extra_payment', 'avalanche', 'snowball', 'consolidate', 'refinance')
            extra_payment: Additional monthly payment amount
            target_payoff_months: Target number of months to pay off debt
            new_rate: New interest rate for refinancing/consolidation
            new_term_years: New loan term in years
            refinancing_fee: One-time refinancing fee
            credit_score: Customer credit score
            payment_frequency: Payment frequency ('monthly', 'biweekly', 'weekly')
            credit_card_promo_rate: Promotional interest rate for credit cards
            credit_card_promo_months: Duration of promotional period in months
        
        Returns:
            Dictionary with analysis results or error message
        """
        try:
            # Debug: Print received parameters
            print(f"\n🔧 [DEBUG] debt_optimizer called")
            print(f"   customer_id={customer_id}, scenario_type={scenario_type}")
            print(f"   extra_payment={extra_payment}, target_payoff_months={target_payoff_months}")
            print(f"   debt_type={debt_type}")
            
            # Test database connection first
            if not self._test_database_connection():
                return {
                    "status": "error",
                    "error": "Database connection failed"
                }
            
            print(f"🔧 [DEBUG] Parsed parameters:")
            print(f"   customer_id={customer_id}, scenario_type={scenario_type}")
            print(f"   extra_payment={extra_payment} (type: {type(extra_payment).__name__})")
            print(f"   target_payoff_months={target_payoff_months}")
            
            # Handle different scenarios
            if customer_id:
                # Scenario A: Existing customer
                result = self._handle_existing_customer(
                    customer_id, debt_type, scenario_type, extra_payment,
                    target_payoff_months, new_rate, new_term_years, refinancing_fee,
                    credit_score, payment_frequency, credit_card_promo_rate, credit_card_promo_months
                )
            elif debts:
                # Scenario B: Hypothetical debts
                result = self._handle_hypothetical_debts(
                    debts, scenario_type, extra_payment, target_payoff_months,
                    new_rate, new_term_years, refinancing_fee, payment_frequency,
                    credit_card_promo_rate, credit_card_promo_months, debt_type
                )
            else:
                return {
                    "status": "error",
                    "error": "Either customer_id or debts list must be provided"
                }
            
            # Store calculation details globally for frontend display
            if result and isinstance(result, dict) and result.get("status") != "error":
                if "calculation_steps" in result or "latex_formulas" in result:
                    global _last_calculation_details
                    _last_calculation_details = {
                        'scenario_type': result.get('scenario_type', result.get('strategy', 'unknown')),
                        'calculation_steps': result.get('calculation_steps', []),
                        'latex_formulas': result.get('latex_formulas', []),
                        'tool_name': 'debt_optimizer'
                    }
                    print(f"\n✅ [DebtOptimizerTool] Stored calculation details: {_last_calculation_details['scenario_type']}")
                    print(f"   - Steps: {len(_last_calculation_details['calculation_steps'])}")
                    print(f"   - Formulas: {len(_last_calculation_details['latex_formulas'])}")
            
            return result
        
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"\n❌ [ERROR] debt_optimizer exception: {str(e)}")
            print(f"Full traceback:\n{error_details}")
            return {
                "status": "error",
                "error": f"Debt optimization failed: {str(e)}",
                "details": error_details
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
    
    def _handle_existing_customer(self, customer_id: str, debt_type: str, scenario_type: str,
                                 extra_payment: float, target_payoff_months: Optional[int],
                                 new_rate: Optional[float], new_term_years: Optional[int],
                                 refinancing_fee: float, credit_score: Optional[int],
                                 payment_frequency: str, credit_card_promo_rate: Optional[float],
                                 credit_card_promo_months: Optional[int]) -> Dict[str, Any]:
        """Handle calculations for existing customer debts."""
        try:
            # Fetch customer's debts
            debts = self._get_customer_debts(customer_id, debt_type)
            
            if not debts:
                return {
                    "status": "error",
                    "error": f"No {debt_type} debts found for customer {customer_id}"
                }
            
            # For avalanche/snowball strategies, if no extra payment specified,
            # calculate a reasonable default (15% of total minimum payments)
            if scenario_type in ["avalanche", "snowball"] and extra_payment == 0:
                total_min_payments = sum(d.get("min_payment_mo", 0) for d in debts)
                if total_min_payments > 0:
                    # Suggest 15% extra payment (reasonable for comparison)
                    extra_payment = round(total_min_payments * 0.15, 2)
                    print(f"ℹ️  No extra payment specified for {scenario_type}. Using ${extra_payment:,.2f} (15% of minimum payments) for comparison.")
            
            # Execute scenario-specific calculations
            if scenario_type == "avalanche":
                return self._calculate_avalanche_strategy(debts, customer_id, extra_payment)
            elif scenario_type == "snowball":
                return self._calculate_snowball_strategy(debts, customer_id, extra_payment)
            elif scenario_type == "consolidate":
                return self._calculate_consolidation(debts, customer_id, new_rate, new_term_years, refinancing_fee, credit_score)
            elif scenario_type == "refinance":
                return self._calculate_refinancing(debts, customer_id, new_rate, new_term_years, refinancing_fee, credit_score)
            else:
                # current, extra_payment, target_payoff
                return self._calculate_standard_scenarios(
                    debts, customer_id, scenario_type, extra_payment,
                    target_payoff_months, new_rate, new_term_years, payment_frequency,
                    credit_card_promo_rate, credit_card_promo_months, debt_type
                )
        
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to process customer debts: {str(e)}"
            }
    
    def _handle_hypothetical_debts(self, debts: List[Dict[str, Any]], scenario_type: str,
                                  extra_payment: float, target_payoff_months: Optional[int],
                                  new_rate: Optional[float], new_term_years: Optional[int],
                                  refinancing_fee: float, payment_frequency: str,
                                  credit_card_promo_rate: Optional[float],
                                  credit_card_promo_months: Optional[int], debt_type: str = "all") -> Dict[str, Any]:
        """Handle calculations for hypothetical debts (Scenario B)."""
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
                return self._calculate_avalanche_strategy(debts, None, extra_payment)
            elif scenario_type == "snowball":
                return self._calculate_snowball_strategy(debts, None, extra_payment)
            elif scenario_type == "consolidate":
                return self._calculate_consolidation(debts, None, new_rate, new_term_years, refinancing_fee, None)
            elif scenario_type == "refinance":
                return self._calculate_refinancing(debts, None, new_rate, new_term_years, refinancing_fee, None)
            else:
                # current, extra_payment, target_payoff
                return self._calculate_standard_scenarios(
                    debts, None, scenario_type, extra_payment,
                    target_payoff_months, new_rate, new_term_years, payment_frequency,
                    credit_card_promo_rate, credit_card_promo_months, debt_type
                )
        
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to calculate hypothetical debts: {str(e)}"
            }
    
    def _get_customer_debts(self, customer_id: str, debt_type: str) -> List[Dict[str, Any]]:
        """Fetch customer's debts from database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if debt_type == "all":
                query = """
                    SELECT 
                        d.debt_id,
                        d.type,
                        d.original_principal,
                        d.current_principal,
                        d.interest_rate_apr,
                        d.term_months,
                        d.min_payment_mo,
                        d.origination_date,
                        d.status
                    FROM debts_loans d
                    WHERE d.customer_id = ?
                    ORDER BY d.interest_rate_apr DESC
                """
                cursor.execute(query, (customer_id,))
            else:
                query = """
                    SELECT 
                        d.debt_id,
                        d.type,
                        d.original_principal,
                        d.current_principal,
                        d.interest_rate_apr,
                        d.term_months,
                        d.min_payment_mo,
                        d.origination_date,
                        d.status
                    FROM debts_loans d
                    WHERE d.customer_id = ? AND d.type = ?
                    ORDER BY d.interest_rate_apr DESC
                """
                cursor.execute(query, (customer_id, debt_type))
            
            debts = []
            for row in cursor.fetchall():
                debt_data = {
                    "debt_id": row[0],
                    "debt_type": row[1],
                    "original_principal": row[2],
                    "principal": row[3],  # Use 'principal' for consistency
                    "current_principal": row[3],
                    "interest_rate_apr": row[4],
                    "term_months": row[5],
                    "min_payment_mo": row[6],
                    "origination_date": row[7],
                    "status": row[8]
                }
                debts.append(debt_data)
            
            conn.close()
            return debts
        
        except Exception as e:
            raise Exception(f"Failed to fetch customer debts: {str(e)}")
    
    def _calculate_standard_scenarios(self, debts: List[Dict[str, Any]], customer_id: Optional[str],
                                    scenario_type: str, extra_payment: float,
                                    target_payoff_months: Optional[int], new_rate: Optional[float],
                                    new_term_years: Optional[int], payment_frequency: str,
                                    credit_card_promo_rate: Optional[float],
                                    credit_card_promo_months: Optional[int], debt_type: str = "all") -> Dict[str, Any]:
        """Calculate standard scenarios (current, extra_payment, target_payoff)."""
        
        results = {
            "status": "success",
            "customer_id": customer_id,
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
            "savings_percentage": (total_savings / (total_current_payment * 12) * 100) if total_current_payment > 0 else 0
        }
        
        # Generate recommendations
        results["recommendations"] = self._generate_standard_recommendations(debts, scenario_type, total_savings)
        
        # Use calculation steps from the appropriate debt for display
        # Priority: 1) If only one debt, use it. 2) If multiple debts and debt_type specified, use matching debt. 3) Use first debt as fallback
        if results["debts"]:
            debt_for_display = results["debts"][0]  # Default to first
            
            # If debt_type was specified (not "all"), find the matching debt
            if debt_type and debt_type != "all" and len(results["debts"]) > 1:
                for debt in results["debts"]:
                    if debt.get("debt_type") == debt_type:
                        debt_for_display = debt
                        print(f"✓ Using calculation steps from {debt_type} debt (not first debt)")
                        break
            
            if debt_for_display.get("calculation_steps"):
                results["calculation_steps"] = debt_for_display["calculation_steps"]
        
        # Add top-level convenience fields for easier agent parsing
        if len(debts) == 1 and results["debts"]:
            debt_result = results["debts"][0]
            
            # For extra_payment scenario, add payoff timeline
            if scenario_type in ["current", "extra_payment"] and debt_result.get("extra_payment_details"):
                details = debt_result["extra_payment_details"]
                # Calculate total payoff months from original term and months saved
                current_term = debt_result.get("current_term_months", 0)
                months_saved = details.get("months_saved", 0)
                results["total_payoff_months"] = int(current_term - months_saved) if current_term > months_saved else 0
                results["total_interest_paid"] = details.get("total_interest", 0)
                results["payoff_date"] = details.get("payoff_date")
                results["months_saved"] = months_saved
            
            # For target_payoff scenario, add required payment
            if scenario_type == "target_payoff":
                results["required_monthly_payment"] = debt_result.get("required_payment", 0)
                results["target_payoff_months"] = debt_result.get("target_payoff_months", 0)
                results["total_interest_paid"] = debt_result.get("total_interest", 0)
        
        return results
    
    def _calculate_debt_scenario(self, debt: Dict[str, Any], extra_payment: float,
                                scenario_type: str, new_rate: Optional[float],
                                new_term_years: Optional[int], target_payoff_months: Optional[int],
                                payment_frequency: str, credit_card_promo_rate: Optional[float],
                                credit_card_promo_months: Optional[int]) -> Dict[str, Any]:
        """Calculate different scenarios for a single debt."""
        principal = debt.get("principal") or debt.get("current_principal")
        current_rate = debt["interest_rate_apr"]
        term_months = debt.get("term_months", 999)  # Default for credit cards
        current_payment = debt.get("min_payment_mo", 0)
        debt_type = debt.get("debt_type", "personal")
        
        # Handle credit card minimum payment if not provided
        if debt_type == "credit_card" and current_payment == 0:
            current_payment = self._calculate_credit_card_min_payment(principal, current_rate)
        
        result = {
            "debt_id": debt.get("debt_id", "hypothetical"),
            "debt_type": debt_type,
            "current_principal": principal,
            "current_rate": current_rate,
            "current_payment": current_payment,
            "current_term_months": term_months
        }
        
        if scenario_type in ["current", "extra_payment"]:
            # Add extra payment to current debt
            new_payment = current_payment + extra_payment
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
                        principal, current_rate, term_months / 12, extra_payment, current_payment
                    )
                
                result["savings"] = savings_result["total_savings"]
                result["new_payoff_date"] = savings_result.get("payoff_date")
                result["months_saved"] = savings_result.get("months_saved", 0)
                result["extra_payment_details"] = savings_result
        
        elif scenario_type == "refinance" and new_rate:
            # Refinancing scenario
            new_term = new_term_years if new_term_years else term_months / 12
            new_payment = self._calculate_monthly_payment(principal, new_rate, new_term)
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
        
        # Add interest savings steps if applicable
        if scenario_type in ["current", "extra_payment"] and extra_payment > 0 and result.get("extra_payment_details"):
            extra_info = result["extra_payment_details"]
            result["calculation_steps"].extend(
                self._build_interest_savings_steps(
                    original_interest=extra_info.get("original_total_interest", 0),
                    new_interest=extra_info.get("total_interest", 0),
                    savings=extra_info.get("total_savings", 0)
                )
            )
        
        return result
    
    def _calculate_avalanche_strategy(self, debts: List[Dict[str, Any]], customer_id: Optional[str],
                                     extra_payment: float) -> Dict[str, Any]:
        """Calculate debt avalanche strategy (highest interest rate first)."""
        # Sort by interest rate (highest first)
        sorted_debts = sorted(debts, key=lambda x: x["interest_rate_apr"], reverse=True)
        
        return self._calculate_payoff_strategy(
            sorted_debts, customer_id, extra_payment, "avalanche",
            "Pay off highest interest rate debt first to minimize total interest paid"
        )
    
    def _calculate_snowball_strategy(self, debts: List[Dict[str, Any]], customer_id: Optional[str],
                                    extra_payment: float) -> Dict[str, Any]:
        """Calculate debt snowball strategy (smallest balance first)."""
        # Sort by balance (smallest first)
        sorted_debts = sorted(debts, key=lambda x: x.get("principal", x.get("current_principal", 0)))
        
        return self._calculate_payoff_strategy(
            sorted_debts, customer_id, extra_payment, "snowball",
            "Pay off smallest balance first for psychological wins and momentum"
        )
    
    def _calculate_payoff_strategy(self, sorted_debts: List[Dict[str, Any]], customer_id: Optional[str],
                                  extra_payment: float, strategy_name: str,
                                  strategy_description: str) -> Dict[str, Any]:
        """Calculate payoff strategy (avalanche or snowball)."""
        results = {
            "status": "success",
            "customer_id": customer_id,
            "strategy": strategy_name,
            "strategy_description": strategy_description,
            "extra_payment": extra_payment,
            "debts": [],
            "payoff_timeline": [],
            "total_interest_saved": 0,
            "total_months_saved": 0,
            "total_interest_paid": 0,
            "total_payoff_months": 0,
            "recommendations": []
        }
        
        # Calculate minimum payment scenario (no extra payment)
        min_scenario = self._simulate_minimum_payments(sorted_debts)
        
        # Calculate strategy scenario (with extra payment focused on target debt)
        strategy_scenario = self._simulate_strategy_payments(sorted_debts, extra_payment)
        
        results["minimum_payment_scenario"] = min_scenario
        results["strategy_scenario"] = strategy_scenario
        results["total_interest_saved"] = min_scenario["total_interest"] - strategy_scenario["total_interest"]
        results["total_months_saved"] = min_scenario["total_months"] - strategy_scenario["total_months"]
        results["total_interest_paid"] = strategy_scenario["total_interest"]
        results["total_payoff_months"] = strategy_scenario["total_months"]
        results["payoff_timeline"] = strategy_scenario["payoff_order"]
        
        # Generate recommendations
        results["recommendations"] = [
            f"Using the {strategy_name} method, you could be debt-free in {strategy_scenario['total_months']} months (vs {min_scenario['total_months']} months with minimum payments).",
            f"You would save ${results['total_interest_saved']:,.2f} in interest.",
            f"Focus extra payments of ${extra_payment:,.2f}/month on your {strategy_name} priority debt.",
            f"Once each debt is paid off, roll that payment into the next target debt (snowballing effect)."
        ]
        
        # Generate calculation steps and formulas for strategy
        calculation_steps = [
            {
                "title": f"{strategy_name.capitalize()} Strategy Explanation",
                "description": strategy_description,
                "latex": f"\\text{{{strategy_name.capitalize()} Method}}",
                "display": True
            },
            {
                "title": "Debt Payoff Order",
                "description": f"Priority order for paying off {len(sorted_debts)} debt(s).",
                "latex": "\\text{Priority: } " + " \\rightarrow ".join([f"\\text{{Debt {i+1}}}" for i in range(min(3, len(sorted_debts)))]),
                "display": True
            },
            {
                "title": "Extra Payment Application",
                "description": f"Apply ${extra_payment:,.2f} extra per month to the priority debt while paying minimums on others.",
                "latex": f"\\text{{Extra Payment}} = \\${extra_payment:,.2f}/\\text{{month}}",
                "display": True
            },
            {
                "title": "Time Savings",
                "description": f"With minimum payments only: {min_scenario['total_months']} months. With {strategy_name}: {strategy_scenario['total_months']} months.",
                "latex": f"\\text{{Months Saved}} = {min_scenario['total_months']} - {strategy_scenario['total_months']} = {results['total_months_saved']}",
                "display": True
            },
            {
                "title": "Interest Savings",
                "description": f"Total interest without strategy: ${min_scenario['total_interest']:,.2f}. With strategy: ${strategy_scenario['total_interest']:,.2f}.",
                "latex": f"\\text{{Interest Saved}} = \\${min_scenario['total_interest']:.2f} - \\${strategy_scenario['total_interest']:.2f} = \\${results['total_interest_saved']:.2f}",
                "display": True
            }
        ]
        
        latex_formulas = [
            f"$$\\text{{{strategy_name.capitalize()} Method}}$$",
            f"$$\\text{{Extra Payment}} = \\${extra_payment:,.2f}/\\text{{month}}$$",
            f"$$\\text{{Months Saved}} = {results['total_months_saved']}$$",
            f"$$\\text{{Interest Saved}} = \\${results['total_interest_saved']:.2f}$$"
        ]
        
        results["calculation_steps"] = calculation_steps
        results["latex_formulas"] = latex_formulas
        
        return results
    
    def _simulate_minimum_payments(self, debts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Simulate paying only minimum payments on all debts."""
        total_months = 0
        total_interest = 0
        
        for debt in debts:
            principal = debt.get("principal", debt.get("current_principal"))
            rate = debt["interest_rate_apr"]
            min_payment = debt.get("min_payment_mo", 0)
            debt_type = debt.get("debt_type", "personal")
            
            # Calculate minimum payment if not provided
            if min_payment == 0:
                if debt_type == "credit_card":
                    min_payment = self._calculate_credit_card_min_payment(principal, rate)
                else:
                    term_years = debt.get("term_months", 120) / 12
                    min_payment = self._calculate_monthly_payment(principal, rate, term_years)
            
            # Simulate payoff
            payoff_result = self._simulate_debt_payoff(principal, rate, min_payment, 0)
            total_months = max(total_months, payoff_result["months"])
            total_interest += payoff_result["total_interest"]
        
        return {
            "total_months": total_months,
            "total_interest": total_interest,
            "method": "minimum_payments_only"
        }
    
    def _simulate_strategy_payments(self, sorted_debts: List[Dict[str, Any]], extra_payment: float) -> Dict[str, Any]:
        """Simulate strategy payments (avalanche or snowball)."""
        total_interest = 0
        current_month = 0
        payoff_order = []
        
        # Create working list of debts
        remaining_debts = []
        for debt in sorted_debts:
            principal = debt.get("principal", debt.get("current_principal"))
            rate = debt["interest_rate_apr"]
            min_payment = debt.get("min_payment_mo", 0)
            debt_type = debt.get("debt_type", "personal")
            
            if min_payment == 0:
                if debt_type == "credit_card":
                    min_payment = self._calculate_credit_card_min_payment(principal, rate)
                else:
                    term_years = debt.get("term_months", 120) / 12
                    min_payment = self._calculate_monthly_payment(principal, rate, term_years)
            
            remaining_debts.append({
                "debt_id": debt.get("debt_id", "hypothetical"),
                "debt_type": debt_type,
                "balance": principal,
                "rate": rate,
                "min_payment": min_payment
            })
        
        # Simulate month-by-month payments
        available_extra = extra_payment
        
        while remaining_debts:
            current_month += 1
            
            if current_month > 600:  # Safety limit (50 years)
                break
            
            # Pay minimum on all debts
            for debt in remaining_debts:
                monthly_rate = debt["rate"] / 100 / 12
                interest = debt["balance"] * monthly_rate
                principal_paid = min(debt["min_payment"] - interest, debt["balance"])
                debt["balance"] -= max(0, principal_paid)
                total_interest += interest
            
            # Apply extra payment to first debt (priority debt)
            if remaining_debts and available_extra > 0:
                priority_debt = remaining_debts[0]
                extra_applied = min(available_extra, priority_debt["balance"])
                priority_debt["balance"] -= extra_applied
            
            # Remove paid-off debts and add their payment to available extra
            paid_off = []
            for debt in remaining_debts[:]:
                if debt["balance"] <= 0.01:
                    payoff_order.append({
                        "debt_id": debt["debt_id"],
                        "debt_type": debt["debt_type"],
                        "month_paid_off": current_month
                    })
                    available_extra += debt["min_payment"]
                    remaining_debts.remove(debt)
        
        return {
            "total_months": current_month,
            "total_interest": total_interest,
            "payoff_order": payoff_order,
            "method": "strategy_with_extra_payment"
        }
    
    def _calculate_consolidation(self, debts: List[Dict[str, Any]], customer_id: Optional[str],
                                new_rate: Optional[float], new_term_years: Optional[int],
                                refinancing_fee: float, credit_score: Optional[int]) -> Dict[str, Any]:
        """Calculate debt consolidation scenario."""
        if not new_rate:
            return {
                "status": "error",
                "error": "new_rate is required for consolidation analysis"
            }
        
        # Adjust rate based on credit score
        if credit_score:
            new_rate = self._adjust_rate_for_credit_score(new_rate, credit_score)
        
        # Calculate current situation
        total_balance = sum(debt.get("principal", debt.get("current_principal")) for debt in debts)
        total_current_payment = sum(debt.get("min_payment_mo", 0) for debt in debts)
        
        # Calculate weighted average term if not provided
        if not new_term_years:
            total_balance_for_weight = total_balance
            weighted_term = 0
            for debt in debts:
                balance = debt.get("principal", debt.get("current_principal"))
                weight = balance / total_balance_for_weight
                term = debt.get("term_months", 120) / 12
                weighted_term += weight * term
            new_term_years = round(weighted_term)
        
        # Calculate new consolidated payment
        new_payment = self._calculate_monthly_payment(total_balance, new_rate, new_term_years)
        
        # Calculate savings
        monthly_savings = total_current_payment - new_payment
        total_new_cost = new_payment * new_term_years * 12
        total_current_cost = total_current_payment * new_term_years * 12
        total_savings = total_current_cost - total_new_cost
        
        # Break-even analysis
        break_even = self._calculate_break_even(monthly_savings, refinancing_fee)
        
        # Generate calculation steps and formulas for consolidation
        monthly_rate = new_rate / 100 / 12
        num_payments = new_term_years * 12
        
        calculation_steps = [
            {
                "title": "Consolidation: Combining Multiple Debts",
                "description": f"Consolidating {len(debts)} debt(s) totaling ${total_balance:,.2f} into a single loan at {new_rate}% for {new_term_years} years.",
                "latex": f"\\text{{Total Balance}} = \\${total_balance:,.2f}",
                "display": True
            },
            {
                "title": "Monthly Payment Formula",
                "description": "M = monthly payment, P = principal, r = monthly interest rate, n = total number of payments.",
                "latex": "M = P \\times \\frac{r(1+r)^n}{(1+r)^n - 1}",
                "display": True
            },
            {
                "title": "Plug in your consolidated loan numbers",
                "description": f"P = ${total_balance:,.2f}, r = {monthly_rate * 100:.4f}% per month, n = {num_payments} payments.",
                "latex": self._build_monthly_payment_latex(total_balance, monthly_rate, num_payments),
                "display": True
            },
            {
                "title": "New Consolidated Payment",
                "description": f"Your new consolidated monthly payment is ${new_payment:,.2f}.",
                "latex": f"M = {new_payment:.2f}",
                "display": False
            },
            {
                "title": "Monthly Savings",
                "description": f"Current total payments: ${total_current_payment:,.2f}, New payment: ${new_payment:,.2f}.",
                "latex": f"\\text{{Savings}} = \\${total_current_payment:.2f} - \\${new_payment:.2f} = \\${monthly_savings:.2f}",
                "display": True
            }
        ]
        
        latex_formulas = [
            f"$$\\text{{Total Balance}} = \\${total_balance:,.2f}$$",
            "$$M = P \\times \\frac{r(1+r)^n}{(1+r)^n - 1}$$",
            f"$${self._build_monthly_payment_latex(total_balance, monthly_rate, num_payments)}$$",
            f"$$\\text{{Monthly Savings}} = \\${total_current_payment:.2f} - \\${new_payment:.2f} = \\${monthly_savings:.2f}$$"
        ]
        
        return {
            "status": "success",
            "customer_id": customer_id,
            "scenario_type": "consolidate",
            "current_situation": {
                "total_debts": len(debts),
                "total_balance": total_balance,
                "total_monthly_payment": total_current_payment
            },
            "consolidation_scenario": {
                "new_rate": new_rate,
                "new_term_years": new_term_years,
                "new_monthly_payment": new_payment,
                "monthly_savings": monthly_savings,
                "total_savings": total_savings,
                "refinancing_fee": refinancing_fee,
                "break_even_analysis": break_even
            },
            "recommendations": self._generate_consolidation_recommendations(
                monthly_savings, total_savings, new_rate, break_even
            ),
            "calculation_steps": calculation_steps,
            "latex_formulas": latex_formulas
        }
    
    def _calculate_refinancing(self, debts: List[Dict[str, Any]], customer_id: Optional[str],
                             new_rate: Optional[float], new_term_years: Optional[int],
                             refinancing_fee: float, credit_score: Optional[int]) -> Dict[str, Any]:
        """Calculate refinancing scenario (similar to consolidation but individual debts)."""
        if not new_rate:
            return {
                "status": "error",
                "error": "new_rate is required for refinancing analysis"
            }
        
        # Adjust rate based on credit score
        if credit_score:
            new_rate = self._adjust_rate_for_credit_score(new_rate, credit_score)
        
        results = {
            "status": "success",
            "customer_id": customer_id,
            "scenario_type": "refinance",
            "debts": [],
            "summary": {},
            "recommendations": []
        }
        
        total_current_payment = 0
        total_new_payment = 0
        total_savings = 0
        
        for debt in debts:
            principal = debt.get("principal", debt.get("current_principal"))
            current_rate = debt["interest_rate_apr"]
            current_payment = debt.get("min_payment_mo", 0)
            current_term_months = debt.get("term_months", 120)
            
            # Use provided term or keep existing
            refi_term_years = new_term_years if new_term_years else current_term_months / 12
            new_payment = self._calculate_monthly_payment(principal, new_rate, refi_term_years)
            
            # Calculate savings
            current_total = current_payment * current_term_months
            new_total = new_payment * (refi_term_years * 12)
            savings = current_total - new_total
            
            debt_result = {
                "debt_id": debt.get("debt_id", "hypothetical"),
                "debt_type": debt.get("debt_type", "personal"),
                "current_principal": principal,
                "current_rate": current_rate,
                "current_payment": current_payment,
                "new_rate": new_rate,
                "new_term_years": refi_term_years,
                "new_payment": new_payment,
                "savings": savings,
                "savings_percentage": (savings / current_total * 100) if current_total > 0 else 0
            }
            
            results["debts"].append(debt_result)
            total_current_payment += current_payment
            total_new_payment += new_payment
            total_savings += savings
        
        # Calculate break-even
        monthly_savings = total_current_payment - total_new_payment
        break_even = self._calculate_break_even(monthly_savings, refinancing_fee)
        
        results["summary"] = {
            "total_debts": len(debts),
            "total_current_payment": total_current_payment,
            "total_new_payment": total_new_payment,
            "total_savings": total_savings,
            "monthly_savings": monthly_savings,
            "break_even_analysis": break_even
        }
        
        results["recommendations"] = self._generate_refinancing_recommendations(
            new_rate, total_savings, break_even
        )
        
        # Generate calculation steps and formulas for refinancing
        # Use the first debt for detailed calculation example
        if debts:
            first_debt = debts[0]
            principal = first_debt.get("principal", first_debt.get("current_principal"))
            current_rate = first_debt["interest_rate_apr"]
            current_payment = first_debt.get("min_payment_mo", 0)
            refi_term_years = new_term_years if new_term_years else first_debt.get("term_months", 120) / 12
            monthly_rate = new_rate / 100 / 12
            num_payments = int(refi_term_years * 12)
            new_payment_first = self._calculate_monthly_payment(principal, new_rate, refi_term_years)
            
            calculation_steps = [
                {
                    "title": "Refinancing Analysis",
                    "description": f"Refinancing {len(debts)} debt(s) from current rates to {new_rate}%.",
                    "latex": f"\\text{{New Rate}} = {new_rate}\\%",
                    "display": True
                },
                {
                    "title": "Monthly Payment Formula",
                    "description": "M = monthly payment, P = principal, r = monthly interest rate, n = total number of payments.",
                    "latex": "M = P \\times \\frac{r(1+r)^n}{(1+r)^n - 1}",
                    "display": True
                },
                {
                    "title": "Example: First Debt Refinancing",
                    "description": f"Original: ${principal:,.2f} @ {current_rate}% → ${current_payment:,.2f}/month. New: ${principal:,.2f} @ {new_rate}% → ${new_payment_first:,.2f}/month.",
                    "latex": self._build_monthly_payment_latex(principal, monthly_rate, num_payments),
                    "display": True
                },
                {
                    "title": "Total Monthly Savings",
                    "description": f"Current total: ${total_current_payment:,.2f}, New total: ${total_new_payment:,.2f}.",
                    "latex": f"\\text{{Savings}} = \\${total_current_payment:.2f} - \\${total_new_payment:.2f} = \\${monthly_savings:.2f}",
                    "display": True
                },
                {
                    "title": "Total Interest Savings",
                    "description": f"Over the life of all loans, you save ${total_savings:,.2f}.",
                    "latex": f"\\text{{Total Savings}} = \\${total_savings:,.2f}",
                    "display": True
                }
            ]
            
            latex_formulas = [
                f"$$\\text{{New Rate}} = {new_rate}\\%$$",
                "$$M = P \\times \\frac{r(1+r)^n}{(1+r)^n - 1}$$",
                f"$${self._build_monthly_payment_latex(principal, monthly_rate, num_payments)}$$",
                f"$$\\text{{Monthly Savings}} = \\${total_current_payment:.2f} - \\${total_new_payment:.2f} = \\${monthly_savings:.2f}$$"
            ]
            
            results["calculation_steps"] = calculation_steps
            results["latex_formulas"] = latex_formulas
        
        return results
    
    def _calculate_monthly_payment(self, principal: float, annual_rate: float, term_years: float) -> float:
        """Calculate monthly payment using amortization formula."""
        if annual_rate == 0:
            return principal / (term_years * 12)
        
        monthly_rate = annual_rate / 100 / 12
        total_payments = term_years * 12
        
        monthly_payment = principal * (monthly_rate * (1 + monthly_rate)**total_payments) / ((1 + monthly_rate)**total_payments - 1)
        return round(monthly_payment, 2)
    
    def _calculate_credit_card_min_payment(self, balance: float, annual_rate: float) -> float:
        """Calculate minimum payment for credit card."""
        # Typical: 2% of balance or $25, whichever is greater
        min_pct_payment = balance * 0.02
        fixed_min = 25.0
        return max(min_pct_payment, fixed_min)
    
    def _calculate_credit_card_payoff(self, balance: float, annual_rate: float, monthly_payment: float,
                                     promo_rate: Optional[float], promo_months: Optional[int]) -> Dict[str, Any]:
        """Calculate credit card payoff with optional promotional rate."""
        months = 0
        total_interest = 0
        remaining_balance = balance
        
        while remaining_balance > 0.01 and months < 600:
            months += 1
            
            # Use promo rate if within promo period
            if promo_rate is not None and promo_months and months <= promo_months:
                current_rate = promo_rate / 100 / 12
            else:
                current_rate = annual_rate / 100 / 12
            
            interest = remaining_balance * current_rate
            principal_payment = monthly_payment - interest
            
            if principal_payment <= 0:
                # Payment doesn't cover interest
                return {
                    "status": "error",
                    "error": "Monthly payment too low to cover interest",
                    "total_interest": 0,
                    "total_savings": 0,
                    "months_saved": 0
                }
            
            remaining_balance -= principal_payment
            total_interest += interest
        
        # Calculate original scenario (minimum payment only)
        original_payment = self._calculate_credit_card_min_payment(balance, annual_rate)
        original_result = self._simulate_debt_payoff(balance, annual_rate, original_payment, 0)
        
        return {
            "monthly_payment": monthly_payment,
            "months_to_payoff": months,
            "total_interest": total_interest,
            "original_total_interest": original_result["total_interest"],
            "total_savings": original_result["total_interest"] - total_interest,
            "months_saved": original_result["months"] - months,
            "payoff_date": self._calculate_payoff_date(months / 12)
        }
    
    def _calculate_extra_payment_scenario(self, principal: float, annual_rate: float,
                                        term_years: float, extra_payment: float,
                                        base_payment: float) -> Dict[str, Any]:
        """Calculate scenario with extra payments."""
        total_payment = base_payment + extra_payment
        
        # Calculate original total interest (without extra payments)
        original_months = term_years * 12
        original_total_interest = (base_payment * original_months) - principal
        
        # Calculate with extra payment
        if annual_rate == 0:
            months_to_payoff = principal / total_payment
            total_interest = 0
        else:
            payoff_result = self._simulate_debt_payoff(principal, annual_rate, total_payment, 0)
            months_to_payoff = payoff_result["months"]
            total_interest = payoff_result["total_interest"]
        
        months_saved = max(0, original_months - months_to_payoff)
        interest_savings = original_total_interest - total_interest
        
        # Generate LaTeX formula
        interest_formula = self._generate_interest_savings_latex(original_total_interest, total_interest)
        
        # Validate calculations
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
        """Calculate required monthly payment to pay off debt in target timeframe."""
        if annual_rate == 0:
            required_payment = principal / target_months
            total_interest = 0
            monthly_rate = 0
        else:
            monthly_rate = annual_rate / 100 / 12
            # Loan payment formula: P = [r*PV] / [1-(1+r)^-n]
            required_payment = (monthly_rate * principal) / (1 - (1 + monthly_rate) ** (-target_months))
            total_interest = (required_payment * target_months) - principal
        
        # Validate the calculation
        if not self._validate_calculation(principal, total_interest, target_months):
            raise ValueError(f"Target payoff calculation validation failed: principal=${principal}, interest=${total_interest}, months={target_months}")
        
        payment_formula = self._generate_payment_formula_latex(principal, monthly_rate, target_months) if annual_rate != 0 else None
        
        return {
            "required_monthly_payment": round(required_payment, 2),
            "target_payoff_months": target_months,
            "total_interest": total_interest,
            "payoff_date": self._calculate_payoff_date(target_months / 12),
            "total_cost": principal + total_interest,
            "formula": payment_formula
        }
    
    def _simulate_debt_payoff(self, principal: float, annual_rate: float,
                            monthly_payment: float, extra_payment: float) -> Dict[str, Any]:
        """Simulate debt payoff month by month."""
        months = 0
        total_interest = 0
        remaining_balance = principal
        payment = monthly_payment + extra_payment
        
        if annual_rate == 0:
            months = remaining_balance / payment
            return {"months": months, "total_interest": 0}
        
        monthly_rate = annual_rate / 100 / 12
        
        while remaining_balance > 0.01 and months < 600:
            interest = remaining_balance * monthly_rate
            principal_payment = payment - interest
            
            if principal_payment <= 0:
                months = 600  # Can't pay off
                break
            
            if principal_payment > remaining_balance:
                principal_payment = remaining_balance
            
            remaining_balance -= principal_payment
            total_interest += interest
            months += 1
        
        return {"months": months, "total_interest": total_interest}
    
    def _adjust_rate_for_credit_score(self, base_rate: float, credit_score: int) -> float:
        """Adjust rate based on credit score."""
        for tier, criteria in self.RATE_QUALIFICATION.items():
            if credit_score >= criteria["min_score"]:
                adjusted_rate = base_rate + criteria["rate_adjustment"]
                return round(adjusted_rate, 2)
        
        # Below all tiers
        return base_rate + self.RATE_QUALIFICATION["poor"]["rate_adjustment"]
    
    def _calculate_break_even(self, monthly_savings: float, refinancing_fee: float) -> Dict[str, Any]:
        """Calculate break-even analysis for refinancing."""
        if refinancing_fee == 0:
            return {
                "break_even_months": 0,
                "break_even_date": datetime.now().strftime("%Y-%m-%d"),
                "profitable": True,
                "message": "No refinancing fees to recover"
            }
        
        if monthly_savings <= 0:
            return {
                "break_even_months": None,
                "break_even_date": None,
                "profitable": False,
                "message": "Refinancing does not provide monthly savings"
            }
        
        break_even_months = refinancing_fee / monthly_savings
        break_even_date = datetime.now() + timedelta(days=break_even_months * 30)
        
        return {
            "break_even_months": round(break_even_months, 1),
            "break_even_date": break_even_date.strftime("%Y-%m-%d"),
            "profitable": break_even_months < 24,
            "message": f"Break-even in {break_even_months:.1f} months"
        }
    
    def _calculate_payoff_date(self, years: float) -> str:
        """Calculate payoff date."""
        payoff_date = datetime.now() + timedelta(days=years * 365)
        return payoff_date.strftime("%Y-%m-%d")
    
    def _validate_calculation(self, principal: float, total_interest: float, months: float) -> bool:
        """Validate that calculations are reasonable."""
        if total_interest < 0 or total_interest > principal * 3:
            return False
        if months < 0 or months > 600:
            return False
        if principal <= 0:
            return False
        return True
    
    def _generate_payment_formula_latex(self, principal: float, monthly_rate: float, num_payments: int) -> str:
        """Generate LaTeX formula for monthly payment."""
        return f"$$M = {principal:.2f} \\times \\frac{{{monthly_rate:.6f}(1 + {monthly_rate:.6f})^{{{num_payments}}}}}{{(1 + {monthly_rate:.6f})^{{{num_payments}}} - 1}}$$"
    
    def _generate_interest_savings_latex(self, original_interest: float, new_interest: float) -> str:
        """Generate LaTeX formula for interest savings."""
        savings = original_interest - new_interest
        return f"$$\\text{{Interest Savings}} = \\${original_interest:.2f} - \\${new_interest:.2f} = \\${savings:.2f}$$"
    
    def _build_monthly_payment_steps(self, principal: float, annual_rate: float,
                                    num_payments: int, monthly_payment: float) -> List[Dict[str, Any]]:
        """Build structured calculation steps for monthly payment."""
        monthly_rate = (annual_rate / 100) / 12 if annual_rate else 0
        
        steps: List[Dict[str, Any]] = [
            {
                "title": "Monthly payment formula",
                "description": "M = monthly payment, P = principal, r = monthly interest rate, n = total number of payments.",
                "latex": "M = P \\times \\frac{r(1+r)^n}{(1+r)^n - 1}",
                "display": True
            },
            {
                "title": "Plug in your numbers",
                "description": f"P = ${principal:,.2f}, r = {monthly_rate * 100:.3f}% per month, n = {num_payments} payments.",
                "latex": self._build_monthly_payment_latex(principal, monthly_rate, num_payments),
                "display": True
            },
            {
                "title": "Calculated monthly payment",
                "description": f"Your monthly payment comes to approximately ${monthly_payment:,.2f}.",
                "latex": f"M = {monthly_payment:.2f}",
                "display": False
            }
        ]
        
        return steps
    
    def _build_interest_savings_steps(self, original_interest: float, new_interest: float,
                                     savings: float) -> List[Dict[str, Any]]:
        """Build structured steps for interest savings."""
        return [
            {
                "title": "Interest savings formula",
                "description": "Savings = interest without extra payments minus interest with extra payments.",
                "latex": "\\text{Savings} = I_{\\text{original}} - I_{\\text{new}}",
                "display": True
            },
            {
                "title": "Plug in your numbers",
                "description": f"I_{{original}} = ${original_interest:,.2f}, I_{{new}} = ${new_interest:,.2f}.",
                "latex": f"\\text{{Savings}} = \\${original_interest:.2f} - \\${new_interest:.2f} = \\${savings:.2f}",
                "display": True
            }
        ]
    
    def _build_monthly_payment_latex(self, principal: float, monthly_rate: float, num_payments: int) -> str:
        """Build monthly payment formula with substituted values."""
        numerator = f"{monthly_rate:.6f}(1 + {monthly_rate:.6f})^{num_payments}"
        denominator = f"(1 + {monthly_rate:.6f})^{num_payments} - 1"
        return f"M = {principal:.2f} \\times \\frac{{{numerator}}}{{{denominator}}}"
    
    def _generate_standard_recommendations(self, debts: List[Dict[str, Any]], scenario_type: str,
                                         total_savings: float) -> List[str]:
        """Generate recommendations for standard scenarios."""
        recommendations = []
        
        if scenario_type in ["current", "extra_payment"]:
            if total_savings > 0:
                recommendations.append(f"Adding extra payments could save you ${total_savings:,.2f} in interest.")
            
            # Check for high-rate debts
            high_rate_debts = [d for d in debts if d["interest_rate_apr"] > 10.0]
            if high_rate_debts:
                recommendations.append(f"You have {len(high_rate_debts)} high-interest debt(s). Consider refinancing or using the avalanche method.")
            
            # Check for multiple debts
            if len(debts) > 1:
                recommendations.append("Consider debt consolidation or the snowball/avalanche method to pay off debts systematically.")
        
        elif scenario_type == "target_payoff":
            recommendations.append("Aggressive payoff strategies require higher monthly payments but save significant interest.")
            recommendations.append("Ensure the higher payment fits your budget before committing.")
        
        return recommendations
    
    def _generate_consolidation_recommendations(self, monthly_savings: float, total_savings: float,
                                              new_rate: float, break_even: Dict[str, Any]) -> List[str]:
        """Generate recommendations for consolidation."""
        recommendations = []
        
        if monthly_savings > 0:
            recommendations.append(f"✅ Consolidation would save you ${monthly_savings:,.2f} per month and ${total_savings:,.2f} total.")
        else:
            recommendations.append("❌ Consolidation may not provide savings with the current rate.")
        
        if break_even and break_even["profitable"]:
            recommendations.append(f"📈 Break-even point is {break_even['break_even_months']:.1f} months, making this highly profitable.")
        
        if new_rate <= 5.0:
            recommendations.append("🌟 Excellent consolidation rate! This is a great opportunity.")
        
        recommendations.append("💡 Consolidation simplifies payments by combining multiple debts into one.")
        
        return recommendations
    
    def _generate_refinancing_recommendations(self, new_rate: float, total_savings: float,
                                            break_even: Dict[str, Any]) -> List[str]:
        """Generate recommendations for refinancing."""
        recommendations = []
        
        if total_savings > 0:
            recommendations.append(f"✅ Refinancing could save you ${total_savings:,.2f} over the life of your loans.")
        else:
            recommendations.append("❌ Refinancing may not be beneficial with the current rate.")
        
        if break_even and break_even["profitable"]:
            recommendations.append(f"📈 Break-even is {break_even['break_even_months']:.1f} months, making refinancing worthwhile.")
        
        if new_rate <= 4.0:
            recommendations.append("🌟 Excellent rate! Consider locking this in.")
        elif new_rate <= 6.0:
            recommendations.append("👍 Good rate. Refinancing could provide meaningful savings.")
        else:
            recommendations.append("🤔 Consider shopping around for better rates.")
        
        return recommendations

