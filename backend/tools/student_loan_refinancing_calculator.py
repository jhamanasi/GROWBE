"""
Student Loan Refinancing Calculator Tool for Financial Advisory Agent.

This tool compares current vs. refinanced loan terms, handles consolidation scenarios,
and provides comprehensive refinancing analysis with break-even calculations.
"""

import sqlite3
import math
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from .base_tool import BaseTool
from pathlib import Path

class StudentLoanRefinancingCalculator(BaseTool):
    """Calculate and compare student loan refinancing scenarios with comprehensive analysis."""
    
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
        
        # Rate qualification matrix based on credit score
        self.rate_qualification = {
            "excellent": {"min_score": 740, "rate_adjustment": 0.0, "description": "Excellent credit"},
            "good": {"min_score": 680, "rate_adjustment": 0.25, "description": "Good credit"},
            "fair": {"min_score": 620, "rate_adjustment": 0.75, "description": "Fair credit"},
            "poor": {"min_score": 580, "rate_adjustment": 1.5, "description": "Poor credit"}
        }
    
    @property
    def name(self) -> str:
        """Return the tool name."""
        return "student_loan_refinancing_calculator"
    
    @property
    def description(self) -> str:
        """Return the tool description."""
        return """Compare current vs. refinanced student loan terms with comprehensive analysis.

        This tool handles:
        1. Existing customer loan refinancing analysis
        2. Multiple loan consolidation scenarios
        3. Rate comparison and qualification
        4. Break-even analysis with fees
        5. Selective vs. full consolidation
        6. Risk assessment and recommendations

        Args:
            customer_id: Customer ID to fetch existing loans (optional)
            current_loans: List of current loan details (required if no customer_id)
            new_rate: New interest rate for refinancing (required)
            new_term_years: New loan term in years (optional, default: weighted average of current terms)
            refinancing_fee: Origination/closing costs (optional, default: 0)
            credit_score: Customer's credit score for rate qualification (optional)
            consolidate_all: Whether to consolidate all loans (optional, default: true)
            rate_threshold: Minimum rate difference to consider refinancing (optional, default: 0.5%)
            include_fees: Whether to include refinancing costs in analysis (optional, default: true)
            scenario_type: Type of analysis - consolidate/selective/compare_rates (optional, default: consolidate)
            
        Returns:
            Comprehensive refinancing analysis with scenarios, savings, and recommendations
        """
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the student loan refinancing analysis."""
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
            current_loans = kwargs.get('current_loans')
            new_rate = kwargs.get('new_rate')
            new_term_years = kwargs.get('new_term_years')
            refinancing_fee = kwargs.get('refinancing_fee', 0)
            credit_score = kwargs.get('credit_score')
            consolidate_all = kwargs.get('consolidate_all', True)
            rate_threshold = kwargs.get('rate_threshold', 0.5)
            include_fees = kwargs.get('include_fees', True)
            scenario_type = kwargs.get('scenario_type', 'consolidate')
            
            # Validate required parameters
            if not new_rate:
                return {
                    "status": "error",
                    "error": "new_rate is required for refinancing analysis"
                }
            
            # Get current loans
            if customer_id:
                loans = self._get_customer_student_loans(customer_id)
                if not loans:
                    return {
                        "status": "error",
                        "error": f"No student loans found for customer {customer_id}"
                    }
            elif current_loans:
                loans = current_loans
            else:
                return {
                    "status": "error",
                    "error": "Either customer_id or current_loans must be provided"
                }
            
            # Adjust rate based on credit score if provided
            if credit_score:
                new_rate = self._adjust_rate_for_credit_score(new_rate, credit_score)
            
            # Calculate default term if not provided
            if not new_term_years:
                new_term_years = self._calculate_weighted_average_term(loans)
            
            # Perform refinancing analysis
            return self._analyze_refinancing_scenarios(
                loans, new_rate, new_term_years, refinancing_fee, 
                consolidate_all, rate_threshold, include_fees, scenario_type
            )
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Refinancing analysis failed: {str(e)}"
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
                ORDER BY d.interest_rate_apr DESC
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
    
    def _adjust_rate_for_credit_score(self, base_rate: float, credit_score: int) -> float:
        """Adjust refinancing rate based on credit score."""
        for tier, criteria in self.rate_qualification.items():
            if credit_score >= criteria["min_score"]:
                adjusted_rate = base_rate + criteria["rate_adjustment"]
                return round(adjusted_rate, 2)
        
        # If credit score is below all tiers, use highest adjustment
        return base_rate + self.rate_qualification["poor"]["rate_adjustment"]
    
    def _calculate_weighted_average_term(self, loans: List[Dict[str, Any]]) -> int:
        """Calculate weighted average term based on loan balances."""
        total_balance = sum(loan["current_principal"] for loan in loans)
        weighted_term = 0
        
        for loan in loans:
            weight = loan["current_principal"] / total_balance
            term_years = loan["term_months"] / 12
            weighted_term += weight * term_years
        
        return round(weighted_term)
    
    def _analyze_refinancing_scenarios(self, loans: List[Dict[str, Any]], new_rate: float, 
                                     new_term_years: int, refinancing_fee: float,
                                     consolidate_all: bool, rate_threshold: float,
                                     include_fees: bool, scenario_type: str) -> Dict[str, Any]:
        """Analyze different refinancing scenarios."""
        
        # Calculate current situation
        current_situation = self._calculate_current_situation(loans)
        
        results = {
            "status": "success",
            "current_situation": current_situation,
            "refinancing_scenarios": {},
            "rate_comparison": {},
            "recommendations": [],
            "risks_and_considerations": []
        }
        
        # Scenario 1: Consolidate All Loans
        if consolidate_all or scenario_type == "consolidate":
            consolidate_scenario = self._calculate_consolidation_scenario(
                loans, new_rate, new_term_years, refinancing_fee, include_fees
            )
            results["refinancing_scenarios"]["consolidate_all"] = consolidate_scenario
        
        # Scenario 2: Selective Refinancing
        if scenario_type == "selective" or not consolidate_all:
            selective_scenario = self._calculate_selective_refinancing(
                loans, new_rate, new_term_years, rate_threshold, refinancing_fee, include_fees
            )
            results["refinancing_scenarios"]["selective_refinance"] = selective_scenario
        
        # Scenario 3: Rate Comparison
        if scenario_type == "compare_rates":
            rate_comparison = self._calculate_rate_comparison(loans, new_term_years)
            results["rate_comparison"] = rate_comparison
        
        # Generate recommendations
        results["recommendations"] = self._generate_recommendations(
            current_situation, results["refinancing_scenarios"], new_rate
        )
        
        # Generate risk analysis
        results["risks_and_considerations"] = self._generate_risk_analysis(
            current_situation, new_rate, new_term_years
        )
        
        return results
    
    def _calculate_current_situation(self, loans: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate current loan situation summary."""
        total_balance = sum(loan["current_principal"] for loan in loans)
        total_payment = sum(loan["min_payment_mo"] for loan in loans)
        
        # Calculate weighted average rate
        weighted_rate = 0
        for loan in loans:
            weight = loan["current_principal"] / total_balance
            weighted_rate += weight * loan["interest_rate_apr"]
        
        # Calculate total remaining interest
        total_remaining_interest = 0
        for loan in loans:
            remaining_months = loan["term_months"]  # Simplified - would need actual remaining months
            monthly_rate = loan["interest_rate_apr"] / 100 / 12
            remaining_interest = loan["current_principal"] * monthly_rate * remaining_months
            total_remaining_interest += remaining_interest
        
        return {
            "total_loans": len(loans),
            "total_balance": total_balance,
            "total_monthly_payment": total_payment,
            "weighted_average_rate": round(weighted_rate, 2),
            "highest_rate": max(loan["interest_rate_apr"] for loan in loans),
            "lowest_rate": min(loan["interest_rate_apr"] for loan in loans),
            "total_remaining_interest": total_remaining_interest,
            "loans": loans
        }
    
    def _calculate_consolidation_scenario(self, loans: List[Dict[str, Any]], new_rate: float,
                                       new_term_years: int, refinancing_fee: float,
                                       include_fees: bool) -> Dict[str, Any]:
        """Calculate full consolidation scenario."""
        total_balance = sum(loan["current_principal"] for loan in loans)
        current_total_payment = sum(loan["min_payment_mo"] for loan in loans)
        
        # Calculate new payment
        new_monthly_payment = self._calculate_monthly_payment(total_balance, new_rate, new_term_years)
        
        # Calculate savings
        monthly_savings = current_total_payment - new_monthly_payment
        total_new_cost = new_monthly_payment * new_term_years * 12
        
        # Calculate current total cost (simplified)
        current_total_cost = current_total_payment * new_term_years * 12  # Simplified calculation
        
        total_savings = current_total_cost - total_new_cost
        
        # Break-even analysis
        break_even = self._calculate_break_even(monthly_savings, refinancing_fee, include_fees)
        
        return {
            "new_rate": new_rate,
            "new_term_years": new_term_years,
            "new_monthly_payment": new_monthly_payment,
            "current_total_payment": current_total_payment,
            "monthly_savings": monthly_savings,
            "total_savings": total_savings,
            "refinancing_fee": refinancing_fee,
            "break_even_analysis": break_even,
            "profitable": break_even["profitable"] if break_even else True
        }
    
    def _calculate_selective_refinancing(self, loans: List[Dict[str, Any]], new_rate: float,
                                       new_term_years: int, rate_threshold: float,
                                       refinancing_fee: float, include_fees: bool) -> Dict[str, Any]:
        """Calculate selective refinancing scenario."""
        # Identify loans worth refinancing (rate difference > threshold)
        refinance_candidates = [
            loan for loan in loans 
            if loan["interest_rate_apr"] - new_rate > rate_threshold
        ]
        
        keep_current = [
            loan for loan in loans 
            if loan["interest_rate_apr"] - new_rate <= rate_threshold
        ]
        
        if not refinance_candidates:
            return {
                "refinanced_loans": 0,
                "kept_loans": len(loans),
                "new_total_payment": sum(loan["min_payment_mo"] for loan in loans),
                "savings": 0,
                "message": "No loans meet the refinancing threshold"
            }
        
        # Calculate new payment for refinanced loans
        refinanced_balance = sum(loan["current_principal"] for loan in refinance_candidates)
        new_refinanced_payment = self._calculate_monthly_payment(refinanced_balance, new_rate, new_term_years)
        
        # Calculate total new payment
        kept_payments = sum(loan["min_payment_mo"] for loan in keep_current)
        new_total_payment = new_refinanced_payment + kept_payments
        
        # Calculate current total payment
        current_total_payment = sum(loan["min_payment_mo"] for loan in loans)
        
        # Calculate savings
        monthly_savings = current_total_payment - new_total_payment
        
        # Break-even analysis
        break_even = self._calculate_break_even(monthly_savings, refinancing_fee, include_fees)
        
        return {
            "refinanced_loans": len(refinance_candidates),
            "kept_loans": len(keep_current),
            "refinanced_balance": refinanced_balance,
            "new_refinanced_payment": new_refinanced_payment,
            "kept_payments": kept_payments,
            "new_total_payment": new_total_payment,
            "current_total_payment": current_total_payment,
            "monthly_savings": monthly_savings,
            "refinancing_fee": refinancing_fee,
            "break_even_analysis": break_even,
            "refinance_candidates": refinance_candidates,
            "keep_current": keep_current
        }
    
    def _calculate_rate_comparison(self, loans: List[Dict[str, Any]], new_term_years: int) -> Dict[str, Any]:
        """Compare multiple refinancing rates."""
        total_balance = sum(loan["current_principal"] for loan in loans)
        current_total_payment = sum(loan["min_payment_mo"] for loan in loans)
        
        comparison_rates = [3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0]
        rate_comparison = {}
        
        for rate in comparison_rates:
            new_payment = self._calculate_monthly_payment(total_balance, rate, new_term_years)
            monthly_savings = current_total_payment - new_payment
            total_savings = monthly_savings * new_term_years * 12
            
            rate_comparison[f"{rate}%"] = {
                "monthly_payment": new_payment,
                "monthly_savings": monthly_savings,
                "total_savings": total_savings,
                "savings_percentage": (monthly_savings / current_total_payment * 100) if current_total_payment > 0 else 0
            }
        
        return rate_comparison
    
    def _calculate_monthly_payment(self, principal: float, annual_rate: float, term_years: int) -> float:
        """Calculate monthly payment using amortization formula."""
        if annual_rate == 0:
            return principal / (term_years * 12)
        
        monthly_rate = annual_rate / 100 / 12
        total_payments = term_years * 12
        
        monthly_payment = principal * (monthly_rate * (1 + monthly_rate)**total_payments) / ((1 + monthly_rate)**total_payments - 1)
        return round(monthly_payment, 2)
    
    def _calculate_break_even(self, monthly_savings: float, refinancing_fee: float, include_fees: bool) -> Dict[str, Any]:
        """Calculate break-even analysis for refinancing."""
        if not include_fees or refinancing_fee == 0:
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
            "profitable": break_even_months < 24,  # Profitable if break-even within 2 years
            "message": f"Break-even in {break_even_months:.1f} months"
        }
    
    def _generate_recommendations(self, current_situation: Dict[str, Any], 
                                scenarios: Dict[str, Any], new_rate: float) -> List[str]:
        """Generate personalized recommendations."""
        recommendations = []
        
        # Check if refinancing makes sense
        if new_rate >= current_situation["weighted_average_rate"]:
            recommendations.append("⚠️ The new rate is not lower than your current weighted average rate. Refinancing may not be beneficial.")
            return recommendations
        
        # Analyze consolidation scenario
        if "consolidate_all" in scenarios:
            consolidate = scenarios["consolidate_all"]
            if consolidate["profitable"]:
                recommendations.append(f"✅ Consolidating all loans at {new_rate}% would save you ${consolidate['monthly_savings']:,.2f} per month and ${consolidate['total_savings']:,.2f} total.")
                
                if consolidate["break_even_analysis"]["profitable"]:
                    recommendations.append(f"📈 Break-even point is {consolidate['break_even_analysis']['break_even_months']:.1f} months, making this highly profitable.")
            else:
                recommendations.append("❌ Consolidation may not be profitable due to refinancing fees or other factors.")
        
        # Analyze selective refinancing
        if "selective_refinance" in scenarios:
            selective = scenarios["selective_refinance"]
            if selective["monthly_savings"] > 0:
                recommendations.append(f"🎯 Selective refinancing would save you ${selective['monthly_savings']:,.2f} per month by refinancing {selective['refinanced_loans']} high-rate loans.")
            else:
                recommendations.append("💡 Consider keeping your current loans as they already have competitive rates.")
        
        # Rate-specific recommendations
        if new_rate <= 4.0:
            recommendations.append("🌟 Excellent rate! This is a great time to refinance with rates this low.")
        elif new_rate <= 5.0:
            recommendations.append("👍 Good rate. Refinancing could provide meaningful savings.")
        else:
            recommendations.append("🤔 Consider shopping around for better rates or waiting for rate improvements.")
        
        # Multiple loan recommendations
        if current_situation["total_loans"] > 1:
            recommendations.append("📋 Consolidating multiple loans will simplify your payments and potentially reduce your overall rate.")
        
        return recommendations
    
    def _generate_risk_analysis(self, current_situation: Dict[str, Any], 
                              new_rate: float, new_term_years: int) -> List[str]:
        """Generate risk analysis and considerations."""
        risks = []
        
        # Rate risk
        if new_rate <= 4.0:
            risks.append("📉 Rate Risk: Current rates are historically low. Consider locking in this rate.")
        else:
            risks.append("📈 Rate Risk: Rates might continue to drop. Consider waiting if you're not in a hurry.")
        
        # Credit risk
        risks.append("💳 Credit Risk: Your credit score affects refinancing rates. Monitor and improve your credit before applying.")
        
        # Income risk
        risks.append("💰 Income Risk: Ensure your income is stable and sufficient to cover the new payment.")
        
        # Life risk
        risks.append("🏠 Life Risk: Consider your life circumstances (job stability, family plans) before committing to a new loan term.")
        
        # Forgiveness risk
        if current_situation["total_loans"] > 0:
            risks.append("🎓 Forgiveness Risk: If you're pursuing loan forgiveness programs, refinancing may disqualify you from federal programs.")
        
        # Term risk
        if new_term_years > 15:
            risks.append("⏰ Term Risk: Longer terms mean lower monthly payments but more total interest. Consider shorter terms if affordable.")
        
        return risks
