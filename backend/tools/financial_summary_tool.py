"""
Financial Summary Tool for Comprehensive Financial Health Analysis.

Provides a one-glance dashboard of the user's complete financial picture including:
- Debt-to-Income Ratio (front-end and back-end)
- Net Worth (total and liquid)
- Monthly Surplus/Deficit
- Loan Payoff Progress
- Credit Health Metrics
- Income vs Expense Trends
- Alerts and Insights
- Benchmark Comparisons
"""

import sqlite3
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from .base_tool import BaseTool


class FinancialSummaryTool(BaseTool):
    """
    Comprehensive financial health summary and analysis tool.
    
    Aggregates data from all financial tables to provide a complete snapshot
    of the user's financial health with actionable insights and benchmarks.
    """
    
    name: str = "financial_summary"
    description: str = """
    Generates a comprehensive financial health summary for the user.
    
    This tool provides:
    - Debt-to-Income Ratios (front-end housing DTI and back-end total DTI)
    - Net Worth calculation (total and liquid)
    - Monthly Surplus/Deficit analysis
    - Loan Payoff Progress (percentage paid, time remaining, interest paid)
    - Credit Health Metrics (FICO score, utilization, trends)
    - Income vs Expense Trends (last 3, 6, or 12 months)
    - Financial Health Alerts (high DTI, negative surplus, low emergency fund)
    - Benchmark Comparisons (vs. recommended thresholds)
    
    Best used when user asks:
    - "How am I doing financially?"
    - "Give me a financial overview"
    - "What's my financial health?"
    - "Show me my complete financial picture"
    
    Args:
        customer_id: Customer ID for existing users (Scenario A) - REQUIRED
        period: Analysis period - "3m" (3 months), "6m" (6 months), "12m" (12 months), "ytd" (year-to-date)
                Default: "3m"
        include_trends: Whether to include historical trends (default: True)
        include_benchmarks: Whether to include benchmark comparisons (default: True)
    
    Returns:
        Comprehensive JSON with all financial metrics, trends, alerts, and formatted summary.
    """
    
    def __init__(self):
        self.db_path = Path(__file__).parent.parent / "data" / "financial_data.db"
        
        # Financial health benchmarks
        self.BENCHMARKS = {
            'dti_front_end_ideal': 0.28,      # 28% front-end DTI
            'dti_back_end_ideal': 0.36,       # 36% back-end DTI
            'dti_back_end_max': 0.43,         # 43% back-end DTI (lender limit)
            'credit_utilization_ideal': 0.30,  # 30% credit utilization
            'emergency_fund_months': 3,        # 3 months expenses minimum
            'savings_rate_ideal': 0.20,        # 20% savings rate
        }
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute comprehensive financial summary analysis."""
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
            
            # Extract parameters
            customer_id = kwargs.get('customer_id')
            period = str(kwargs.get('period', '3m')).lower()
            include_trends = kwargs.get('include_trends', True)
            include_benchmarks = kwargs.get('include_benchmarks', True)
            
            print(f"\n[FinancialSummaryTool] Generating summary for {customer_id}, period: {period}")
            
            # Validate customer_id
            if not customer_id:
                return {
                    "status": "error",
                    "error": "customer_id is required for financial summary"
                }
            
            # Connect to database
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Calculate period dates
            period_months = self._parse_period(period)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=period_months * 30)
            
            # Gather all financial data
            customer_data = self._get_customer_data(cursor, customer_id)
            if not customer_data:
                conn.close()
                return {
                    "status": "error",
                    "error": f"Customer {customer_id} not found in database"
                }
            
            debt_data = self._get_debt_data(cursor, customer_id)
            account_data = self._get_account_data(cursor, customer_id)
            asset_data = self._get_asset_data(cursor, customer_id)
            transaction_data = self._get_transaction_data(cursor, customer_id, start_date, end_date)
            credit_data = self._get_credit_data(cursor, customer_id)
            cashflow_data = self._get_cashflow_data(cursor, customer_id, period_months)
            
            conn.close()
            
            # Calculate all metrics
            dti_metrics = self._calculate_dti(customer_data, debt_data, transaction_data, cashflow_data)
            net_worth_metrics = self._calculate_net_worth(account_data, asset_data, debt_data)
            surplus_metrics = self._calculate_surplus_deficit(customer_data, transaction_data, cashflow_data, debt_data)
            loan_progress = self._calculate_loan_progress(debt_data)
            credit_metrics = self._calculate_credit_health(credit_data, account_data)
            income_expense_trends = self._calculate_income_expense_trends(
                transaction_data, cashflow_data, period_months, include_trends
            )
            
            # Generate alerts
            alerts = self._generate_alerts(
                dti_metrics, surplus_metrics, credit_metrics, net_worth_metrics, customer_data
            )
            
            # Generate benchmarks
            benchmarks = None
            if include_benchmarks:
                benchmarks = self._generate_benchmarks(
                    dti_metrics, credit_metrics, surplus_metrics, net_worth_metrics
                )
            
            # Generate formatted summary
            formatted_summary = self._format_summary(
                customer_data, dti_metrics, net_worth_metrics, surplus_metrics,
                loan_progress, credit_metrics, alerts
            )
            
            # Build result
            result = {
                "status": "success",
                "customer_id": customer_id,
                "as_of_date": datetime.now().strftime("%Y-%m-%d"),
                "period": period,
                "period_months": period_months,
                
                # Core Metrics
                "debt_to_income": dti_metrics,
                "net_worth": net_worth_metrics,
                "monthly_surplus_deficit": surplus_metrics,
                "loan_progress": loan_progress,
                "credit_health": credit_metrics,
                "income_expense_trends": income_expense_trends,
                
                # Insights
                "alerts": alerts,
                "benchmarks": benchmarks,
                
                # Formatted output
                "formatted_summary": formatted_summary,
                
                # Raw data for LLM reasoning
                "customer_profile": {
                    "annual_income": customer_data.get('annual_income'),
                    "monthly_income": customer_data.get('annual_income', 0) / 12 if customer_data.get('annual_income') else 0,
                    "fico_score": customer_data.get('fico_score'),
                    "age": customer_data.get('age'),
                    "location": customer_data.get('location', 'DMV')
                }
            }
            
            print(f"✅ [FinancialSummaryTool] Summary generated successfully")
            print(f"   - Net Worth: ${net_worth_metrics.get('total', 0):,.2f}")
            print(f"   - Back-end DTI: {dti_metrics.get('back_end_ratio', 0)*100:.1f}%")
            print(f"   - Monthly Surplus: ${surplus_metrics.get('average_surplus', 0):,.2f}")
            print(f"   - Alerts: {len(alerts)}")
            
            return result
        
        except Exception as e:
            import traceback
            return {
                "status": "error",
                "error": f"Financial summary failed: {str(e)}",
                "traceback": traceback.format_exc()
            }
    
    def _parse_period(self, period: str) -> int:
        """Parse period string to number of months."""
        period = period.lower()
        if period == '3m':
            return 3
        elif period == '6m':
            return 6
        elif period == '12m' or period == '1y':
            return 12
        elif period == 'ytd':
            return datetime.now().month
        else:
            return 3  # Default
    
    def _get_customer_data(self, cursor, customer_id: str) -> Optional[Dict[str, Any]]:
        """Fetch customer profile data."""
        cursor.execute("""
            SELECT c.customer_id, c.persona_type, c.base_salary_annual as annual_income,
                   c.fico_baseline as fico_score, c.dob, c.state,
                   ei.employer_name, ei.role, ei.status as employment_status,
                   ei.base_salary_annual as employment_income,
                   ei.variable_income_avg_mo
            FROM customers c
            LEFT JOIN employment_income ei ON c.customer_id = ei.customer_id
            WHERE c.customer_id = ?
        """, (customer_id,))
        
        row = cursor.fetchone()
        if row:
            data = dict(row)
            # Calculate age from DOB
            if data.get('dob'):
                try:
                    dob = datetime.strptime(data['dob'], "%Y-%m-%d")
                    age = datetime.now().year - dob.year
                    if datetime.now().month < dob.month or (datetime.now().month == dob.month and datetime.now().day < dob.day):
                        age -= 1
                    data['age'] = age
                except:
                    data['age'] = None
            else:
                data['age'] = None
            
            # Use employment_income if available, else fallback to base_salary_annual
            if data.get('employment_income'):
                data['annual_income'] = data['employment_income']
            # Add variable income (monthly * 12)
            total_income = data.get('annual_income', 0) or 0
            variable_monthly = data.get('variable_income_avg_mo', 0) or 0
            total_income += variable_monthly * 12
            data['annual_income'] = total_income
            
            # Set location based on state or default to DMV
            data['location'] = data.get('state', 'DMV')
            
            return data
        return None
    
    def _get_debt_data(self, cursor, customer_id: str) -> List[Dict[str, Any]]:
        """Fetch all debt/loan data."""
        cursor.execute("""
            SELECT debt_id, type, origination_date, original_principal,
                   current_principal, interest_rate_apr, term_months,
                   min_payment_mo, status
            FROM debts_loans
            WHERE customer_id = ? AND status IN ('open', 'current')
        """, (customer_id,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def _get_account_data(self, cursor, customer_id: str) -> List[Dict[str, Any]]:
        """Fetch all account balance data."""
        cursor.execute("""
            SELECT account_id, account_type, institution, opened_date,
                   interest_rate_apr, credit_limit, current_balance, status
            FROM accounts
            WHERE customer_id = ? AND status = 'open'
        """, (customer_id,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def _get_asset_data(self, cursor, customer_id: str) -> List[Dict[str, Any]]:
        """Fetch all asset data."""
        cursor.execute("""
            SELECT asset_id, type as asset_type, current_value as estimated_value,
                   liquidity_tier
            FROM assets
            WHERE customer_id = ?
        """, (customer_id,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def _get_transaction_data(self, cursor, customer_id: str, 
                             start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Fetch transaction data for the specified period."""
        cursor.execute("""
            SELECT t.txn_id, t.posted_date, t.amount, t.merchant,
                   t.category_lvl1, t.category_lvl2
            FROM transactions t
            JOIN accounts a ON t.account_id = a.account_id
            WHERE a.customer_id = ?
              AND t.posted_date >= ?
              AND t.posted_date <= ?
            ORDER BY t.posted_date DESC
        """, (customer_id, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def _get_credit_data(self, cursor, customer_id: str) -> List[Dict[str, Any]]:
        """Fetch credit report history."""
        cursor.execute("""
            SELECT credit_report_id, as_of_month, fico_score, 
                   credit_utilization_pct as utilization_pct,
                   total_open_accounts as num_open_accounts, 
                   hard_inquiries_12m as num_hard_inquiries_6mo,
                   avg_account_age_months as oldest_account_age_mo
            FROM credit_reports
            WHERE customer_id = ?
            ORDER BY as_of_month DESC
            LIMIT 12
        """, (customer_id,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def _get_cashflow_data(self, cursor, customer_id: str, 
                          months: int) -> List[Dict[str, Any]]:
        """Fetch monthly cashflow data if available."""
        cursor.execute("""
            SELECT month, 
                   gross_income_mo as total_income, 
                   spend_total_mo as total_expenses,
                   (gross_income_mo - spend_total_mo) as net_cashflow
            FROM monthly_cashflow
            WHERE customer_id = ?
            ORDER BY month DESC
            LIMIT ?
        """, (customer_id, months))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def _calculate_dti(self, customer_data: Dict, debt_data: List[Dict],
                       transaction_data: List[Dict], cashflow_data: List[Dict]) -> Dict[str, Any]:
        """Calculate front-end and back-end DTI ratios."""
        annual_income = customer_data.get('annual_income', 0) or 0
        monthly_income = annual_income / 12 if annual_income > 0 else 0
        
        if monthly_income == 0:
            return {
                "front_end_ratio": 0,
                "back_end_ratio": 0,
                "monthly_income": 0,
                "monthly_housing_payment": 0,
                "monthly_total_debt_payment": 0,
                "status": "insufficient_data"
            }
        
        # Calculate total monthly debt payments
        total_monthly_payment = sum(debt.get('min_payment_mo', 0) or 0 for debt in debt_data)
        
        # Calculate housing costs (from transactions or debts)
        housing_payment = 0
        
        # Try to get housing costs from transactions (rent or mortgage)
        if transaction_data:
            housing_transactions = [
                t for t in transaction_data 
                if t.get('category_lvl1') == 'Housing' and t.get('category_lvl2') in ['Rent', 'Mortgage']
            ]
            if housing_transactions:
                # Average over the period
                months = len(set(t['posted_date'][:7] for t in housing_transactions))
                total_housing = abs(sum(t.get('amount', 0) for t in housing_transactions))
                housing_payment = total_housing / months if months > 0 else 0
        
        # If no housing transactions, check for mortgage in debts
        if housing_payment == 0:
            mortgage_debts = [d for d in debt_data if d.get('type') == 'mortgage']
            if mortgage_debts:
                housing_payment = sum(d.get('min_payment_mo', 0) or 0 for d in mortgage_debts)
        
        # Calculate ratios
        front_end_ratio = housing_payment / monthly_income if monthly_income > 0 else 0
        back_end_ratio = total_monthly_payment / monthly_income if monthly_income > 0 else 0
        
        return {
            "front_end_ratio": round(front_end_ratio, 4),
            "front_end_percentage": round(front_end_ratio * 100, 1),
            "back_end_ratio": round(back_end_ratio, 4),
            "back_end_percentage": round(back_end_ratio * 100, 1),
            "monthly_income": round(monthly_income, 2),
            "monthly_housing_payment": round(housing_payment, 2),
            "monthly_total_debt_payment": round(total_monthly_payment, 2),
            "status": "calculated"
        }
    
    def _calculate_net_worth(self, account_data: List[Dict], asset_data: List[Dict],
                            debt_data: List[Dict]) -> Dict[str, Any]:
        """Calculate total and liquid net worth."""
        # Sum all account balances
        total_accounts = sum(acc.get('current_balance', 0) or 0 for acc in account_data)
        
        # Sum all assets
        total_assets = sum(asset.get('estimated_value', 0) or 0 for asset in asset_data)
        
        # Sum liquid assets only (liquidity_tier in ['1', '2'] or [1, 2])
        liquid_assets = sum(
            asset.get('estimated_value', 0) or 0 
            for asset in asset_data 
            if str(asset.get('liquidity_tier', '3')) in ['1', '2']
        )
        
        # Sum all outstanding debt
        total_debt = sum(debt.get('current_principal', 0) or 0 for debt in debt_data)
        
        # Calculate net worth
        total_net_worth = total_accounts + total_assets - total_debt
        liquid_net_worth = total_accounts + liquid_assets - total_debt
        
        return {
            "total": round(total_net_worth, 2),
            "liquid": round(liquid_net_worth, 2),
            "assets": {
                "accounts": round(total_accounts, 2),
                "other_assets": round(total_assets, 2),
                "total_assets": round(total_accounts + total_assets, 2),
                "liquid_assets": round(total_accounts + liquid_assets, 2)
            },
            "liabilities": {
                "total_debt": round(total_debt, 2)
            },
            "status": "calculated"
        }
    
    def _calculate_surplus_deficit(self, customer_data: Dict, transaction_data: List[Dict],
                                   cashflow_data: List[Dict], debt_data: List[Dict]) -> Dict[str, Any]:
        """Calculate monthly surplus/deficit."""
        # Try to use cashflow data first
        if cashflow_data:
            avg_income = sum(cf.get('total_income', 0) or 0 for cf in cashflow_data) / len(cashflow_data)
            avg_expenses = sum(cf.get('total_expenses', 0) or 0 for cf in cashflow_data) / len(cashflow_data)
            avg_surplus = sum(cf.get('net_cashflow', 0) or 0 for cf in cashflow_data) / len(cashflow_data)
            
            return {
                "average_surplus": round(avg_surplus, 2),
                "average_monthly_income": round(avg_income, 2),
                "average_monthly_expenses": round(avg_expenses, 2),
                "surplus_percentage": round((avg_surplus / avg_income * 100) if avg_income > 0 else 0, 1),
                "status": "calculated_from_cashflow"
            }
        
        # Calculate from transactions
        if transaction_data:
            # Group by month
            months = {}
            for txn in transaction_data:
                month = txn['posted_date'][:7]  # YYYY-MM
                if month not in months:
                    months[month] = {'income': 0, 'expenses': 0}
                
                amount = txn.get('amount', 0)
                if txn.get('category_lvl1') == 'Income':
                    months[month]['income'] += abs(amount)
                else:
                    months[month]['expenses'] += abs(amount)
            
            if months:
                avg_income = sum(m['income'] for m in months.values()) / len(months)
                avg_expenses = sum(m['expenses'] for m in months.values()) / len(months)
                avg_surplus = avg_income - avg_expenses
                
                return {
                    "average_surplus": round(avg_surplus, 2),
                    "average_monthly_income": round(avg_income, 2),
                    "average_monthly_expenses": round(avg_expenses, 2),
                    "surplus_percentage": round((avg_surplus / avg_income * 100) if avg_income > 0 else 0, 1),
                    "months_analyzed": len(months),
                    "status": "calculated_from_transactions"
                }
        
        # Fallback: use annual income
        annual_income = customer_data.get('annual_income', 0) or 0
        monthly_income = annual_income / 12
        monthly_debt_payments = sum(debt.get('min_payment_mo', 0) or 0 for debt in debt_data)
        
        # Estimate expenses (80% of income after debt payments as a rough estimate)
        estimated_expenses = monthly_income * 0.80
        estimated_surplus = monthly_income - estimated_expenses
        
        return {
            "average_surplus": round(estimated_surplus, 2),
            "average_monthly_income": round(monthly_income, 2),
            "average_monthly_expenses": round(estimated_expenses, 2),
            "surplus_percentage": round((estimated_surplus / monthly_income * 100) if monthly_income > 0 else 0, 1),
            "status": "estimated_from_income"
        }
    
    def _calculate_loan_progress(self, debt_data: List[Dict]) -> List[Dict[str, Any]]:
        """Calculate payoff progress for each loan."""
        progress = []
        
        for debt in debt_data:
            original = debt.get('original_principal', 0) or 0
            current = debt.get('current_principal', 0) or 0
            
            if original == 0:
                continue
            
            paid_amount = original - current
            percent_paid = (paid_amount / original) * 100 if original > 0 else 0
            
            # Calculate months elapsed and remaining
            origination_date = debt.get('origination_date')
            term_months = debt.get('term_months', 0) or 0
            
            months_elapsed = 0
            months_remaining = term_months
            
            if origination_date:
                try:
                    orig_date = datetime.strptime(origination_date, "%Y-%m-%d")
                    months_elapsed = (datetime.now().year - orig_date.year) * 12 + (datetime.now().month - orig_date.month)
                    months_remaining = max(0, term_months - months_elapsed)
                except:
                    pass
            
            # Estimate interest paid (rough calculation)
            interest_rate = debt.get('interest_rate_apr', 0) or 0
            # Simple interest approximation: principal * rate * time
            interest_paid = paid_amount * (interest_rate / 100) * (months_elapsed / 12) if months_elapsed > 0 else 0
            
            progress.append({
                "debt_id": debt.get('debt_id'),
                "type": debt.get('type'),
                "original_principal": round(original, 2),
                "current_principal": round(current, 2),
                "amount_paid": round(paid_amount, 2),
                "percent_paid": round(percent_paid, 1),
                "months_elapsed": months_elapsed,
                "months_remaining": months_remaining,
                "estimated_interest_paid": round(interest_paid, 2),
                "interest_rate": interest_rate,
                "monthly_payment": debt.get('min_payment_mo', 0) or 0
            })
        
        return progress
    
    def _calculate_credit_health(self, credit_data: List[Dict],
                                 account_data: List[Dict]) -> Dict[str, Any]:
        """Calculate credit health metrics and trends."""
        if not credit_data:
            return {
                "current_fico_score": None,
                "fico_trend": None,
                "credit_utilization": None,
                "status": "no_credit_data"
            }
        
        # Most recent credit report
        current = credit_data[0]
        current_score = current.get('fico_score')
        current_utilization = current.get('utilization_pct', 0) or 0
        
        # 3-month trend
        trend = None
        trend_direction = None
        if len(credit_data) >= 3:
            three_months_ago = credit_data[2].get('fico_score')
            if current_score and three_months_ago:
                trend = current_score - three_months_ago
                trend_direction = "up" if trend > 0 else ("down" if trend < 0 else "stable")
        
        # Calculate total available credit from accounts
        credit_accounts = [acc for acc in account_data if acc.get('account_type') == 'credit']
        
        return {
            "current_fico_score": current_score,
            "fico_trend_3m": trend,
            "fico_trend_direction": trend_direction,
            "credit_utilization": round(current_utilization, 2),
            "num_open_accounts": current.get('num_open_accounts'),
            "num_hard_inquiries_6mo": current.get('num_hard_inquiries_6mo', 0),
            "oldest_account_age_months": current.get('oldest_account_age_mo'),
            "status": "calculated"
        }
    
    def _calculate_income_expense_trends(self, transaction_data: List[Dict],
                                        cashflow_data: List[Dict], 
                                        period_months: int,
                                        include_trends: bool) -> Dict[str, Any]:
        """Calculate income vs expense trends."""
        if not include_trends:
            return {"status": "trends_disabled"}
        
        # Use cashflow data if available
        if cashflow_data:
            trends = []
            for cf in sorted(cashflow_data, key=lambda x: x['month']):
                trends.append({
                    "month": cf['month'],
                    "income": round(cf.get('total_income', 0) or 0, 2),
                    "expenses": round(cf.get('total_expenses', 0) or 0, 2),
                    "net": round(cf.get('net_cashflow', 0) or 0, 2)
                })
            
            return {
                "monthly_trends": trends,
                "status": "calculated_from_cashflow"
            }
        
        # Calculate from transactions
        if transaction_data:
            months = {}
            for txn in transaction_data:
                month = txn['posted_date'][:7]
                if month not in months:
                    months[month] = {'income': 0, 'expenses': 0}
                
                amount = txn.get('amount', 0)
                if txn.get('category_lvl1') == 'Income':
                    months[month]['income'] += abs(amount)
                else:
                    months[month]['expenses'] += abs(amount)
            
            trends = []
            for month in sorted(months.keys()):
                income = months[month]['income']
                expenses = months[month]['expenses']
                trends.append({
                    "month": month,
                    "income": round(income, 2),
                    "expenses": round(expenses, 2),
                    "net": round(income - expenses, 2)
                })
            
            return {
                "monthly_trends": trends,
                "status": "calculated_from_transactions"
            }
        
        return {"status": "insufficient_data"}
    
    def _generate_alerts(self, dti_metrics: Dict, surplus_metrics: Dict,
                        credit_metrics: Dict, net_worth_metrics: Dict,
                        customer_data: Dict) -> List[Dict[str, Any]]:
        """Generate financial health alerts."""
        alerts = []
        
        # DTI Alerts
        back_end_dti = dti_metrics.get('back_end_ratio', 0)
        if back_end_dti > self.BENCHMARKS['dti_back_end_max']:
            alerts.append({
                "severity": "high",
                "category": "debt_to_income",
                "message": f"Your debt-to-income ratio is {back_end_dti*100:.1f}%, which exceeds the recommended 43% limit. Lenders may view this as high risk.",
                "recommendation": "Consider debt consolidation or refinancing to lower your monthly payments."
            })
        elif back_end_dti > self.BENCHMARKS['dti_back_end_ideal']:
            alerts.append({
                "severity": "medium",
                "category": "debt_to_income",
                "message": f"Your debt-to-income ratio is {back_end_dti*100:.1f}%, which is above the ideal 36% threshold.",
                "recommendation": "Work on reducing debt or increasing income to improve your financial flexibility."
            })
        
        # Surplus/Deficit Alerts
        avg_surplus = surplus_metrics.get('average_surplus', 0)
        if avg_surplus < 0:
            alerts.append({
                "severity": "high",
                "category": "cash_flow",
                "message": f"You're spending ${abs(avg_surplus):,.2f} more than you earn each month on average.",
                "recommendation": "Review your budget and identify areas to cut expenses or increase income."
            })
        elif avg_surplus < 500:
            alerts.append({
                "severity": "medium",
                "category": "cash_flow",
                "message": f"Your monthly surplus is only ${avg_surplus:,.2f}, which provides limited financial cushion.",
                "recommendation": "Aim to save at least 20% of your income for emergencies and future goals."
            })
        
        # Credit Utilization Alerts
        utilization = credit_metrics.get('credit_utilization', 0)
        if utilization and utilization > self.BENCHMARKS['credit_utilization_ideal'] * 100:
            alerts.append({
                "severity": "medium",
                "category": "credit_health",
                "message": f"Your credit utilization is {utilization:.1f}%, which is above the recommended 30% threshold.",
                "recommendation": "Pay down credit card balances to improve your credit score."
            })
        
        # Emergency Fund Alert
        monthly_expenses = surplus_metrics.get('average_monthly_expenses', 0)
        liquid_net_worth = net_worth_metrics.get('liquid', 0)
        if monthly_expenses > 0:
            emergency_fund_months = liquid_net_worth / monthly_expenses
            if emergency_fund_months < self.BENCHMARKS['emergency_fund_months']:
                alerts.append({
                    "severity": "medium",
                    "category": "emergency_fund",
                    "message": f"Your liquid assets cover {emergency_fund_months:.1f} months of expenses. Recommended: 3-6 months.",
                    "recommendation": "Build your emergency fund by setting aside a portion of your monthly surplus."
                })
        
        # Negative Net Worth Alert
        total_net_worth = net_worth_metrics.get('total', 0)
        if total_net_worth < 0:
            alerts.append({
                "severity": "high",
                "category": "net_worth",
                "message": f"Your net worth is negative (${total_net_worth:,.2f}). Your liabilities exceed your assets.",
                "recommendation": "Focus on paying down high-interest debt while building your emergency fund."
            })
        
        return alerts
    
    def _generate_benchmarks(self, dti_metrics: Dict, credit_metrics: Dict,
                            surplus_metrics: Dict, net_worth_metrics: Dict) -> Dict[str, Any]:
        """Generate benchmark comparisons."""
        benchmarks = {}
        
        # DTI Benchmark
        back_end_dti = dti_metrics.get('back_end_ratio', 0)
        benchmarks['dti'] = {
            "your_value": round(back_end_dti * 100, 1),
            "ideal_threshold": round(self.BENCHMARKS['dti_back_end_ideal'] * 100, 1),
            "max_threshold": round(self.BENCHMARKS['dti_back_end_max'] * 100, 1),
            "status": "healthy" if back_end_dti <= self.BENCHMARKS['dti_back_end_ideal'] else (
                "acceptable" if back_end_dti <= self.BENCHMARKS['dti_back_end_max'] else "high"
            )
        }
        
        # Credit Utilization Benchmark
        utilization = credit_metrics.get('credit_utilization', 0)
        if utilization is not None:
            benchmarks['credit_utilization'] = {
                "your_value": round(utilization, 1),
                "ideal_threshold": round(self.BENCHMARKS['credit_utilization_ideal'] * 100, 1),
                "status": "healthy" if utilization <= self.BENCHMARKS['credit_utilization_ideal'] * 100 else "high"
            }
        
        # Savings Rate Benchmark
        avg_surplus = surplus_metrics.get('average_surplus', 0)
        avg_income = surplus_metrics.get('average_monthly_income', 0)
        if avg_income > 0:
            savings_rate = avg_surplus / avg_income
            benchmarks['savings_rate'] = {
                "your_value": round(savings_rate * 100, 1),
                "ideal_threshold": round(self.BENCHMARKS['savings_rate_ideal'] * 100, 1),
                "status": "healthy" if savings_rate >= self.BENCHMARKS['savings_rate_ideal'] else "needs_improvement"
            }
        
        # Net Worth Status
        total_net_worth = net_worth_metrics.get('total', 0)
        benchmarks['net_worth'] = {
            "your_value": round(total_net_worth, 2),
            "status": "positive" if total_net_worth > 0 else "negative"
        }
        
        return benchmarks
    
    def _format_summary(self, customer_data: Dict, dti_metrics: Dict,
                       net_worth_metrics: Dict, surplus_metrics: Dict,
                       loan_progress: List[Dict], credit_metrics: Dict,
                       alerts: List[Dict]) -> str:
        """Format a human-readable summary."""
        lines = []
        
        # Header
        customer_id = customer_data.get('customer_id', 'User')
        lines.append(f"## Financial Health Summary for {customer_id}")
        lines.append("")
        
        # Net Worth
        net_worth = net_worth_metrics.get('total', 0)
        liquid = net_worth_metrics.get('liquid', 0)
        lines.append(f"**Net Worth:** ${net_worth:,.2f} (Liquid: ${liquid:,.2f})")
        lines.append("")
        
        # DTI
        back_end = dti_metrics.get('back_end_percentage', 0)
        front_end = dti_metrics.get('front_end_percentage', 0)
        lines.append(f"**Debt-to-Income Ratio:**")
        lines.append(f"- Front-end (Housing): {front_end:.1f}%")
        lines.append(f"- Back-end (Total): {back_end:.1f}%")
        lines.append("")
        
        # Monthly Cash Flow
        surplus = surplus_metrics.get('average_surplus', 0)
        income = surplus_metrics.get('average_monthly_income', 0)
        expenses = surplus_metrics.get('average_monthly_expenses', 0)
        lines.append(f"**Monthly Cash Flow:**")
        lines.append(f"- Income: ${income:,.2f}")
        lines.append(f"- Expenses: ${expenses:,.2f}")
        lines.append(f"- Surplus: ${surplus:,.2f}")
        lines.append("")
        
        # Credit Health
        fico = credit_metrics.get('current_fico_score')
        utilization = credit_metrics.get('credit_utilization', 0)
        trend = credit_metrics.get('fico_trend_direction')
        if fico:
            trend_emoji = "📈" if trend == "up" else ("📉" if trend == "down" else "➡️")
            lines.append(f"**Credit Health:**")
            lines.append(f"- FICO Score: {fico} {trend_emoji}")
            lines.append(f"- Credit Utilization: {utilization:.1f}%")
            lines.append("")
        
        # Loan Progress
        if loan_progress:
            lines.append(f"**Loan Progress:**")
            total_debt = 0
            for loan in loan_progress:
                current_balance = loan.get('current_principal', 0)
                interest_rate = loan.get('interest_rate', 0)
                monthly_payment = loan.get('monthly_payment', 0)
                percent_paid = loan.get('percent_paid', 0)
                months_remaining = loan.get('months_remaining', 0)

                total_debt += current_balance

                lines.append(f"- **{loan['type'].title()}**: ${current_balance:,.2f} at {interest_rate:.2f}% APR (${monthly_payment:,.2f}/mo) - {percent_paid:.1f}% paid, {months_remaining} months remaining")

            # Add total debt summary
            lines.append(f"- **Total Debt**: ${total_debt:,.2f}")
            lines.append("")
        
        # Alerts
        if alerts:
            high_alerts = [a for a in alerts if a['severity'] == 'high']
            if high_alerts:
                lines.append(f"**⚠️ Critical Alerts:**")
                for alert in high_alerts:
                    lines.append(f"- {alert['message']}")
                lines.append("")
        
        return "\n".join(lines)

