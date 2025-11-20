"""
Visualization Tool for Financial Advisory Agent.

Intelligently generates charts and visualizations for financial data including:
- Debt breakdown and comparisons
- Payoff timelines and projections
- Income vs expense analysis
- Net worth composition
- Credit score trends
- Budget breakdowns

Supports multiple chart types: bar, pie, line, area, stacked bar
"""

import sqlite3
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
from .base_tool import BaseTool

# Module-level variable to store last chart data for frontend display
_last_chart_data: Optional[Dict[str, Any]] = None

def get_last_chart_data() -> Optional[Dict[str, Any]]:
    """Retrieve the last captured chart data."""
    return _last_chart_data

def clear_chart_data():
    """Clear the captured chart data."""
    global _last_chart_data
    _last_chart_data = None


class VisualizationTool(BaseTool):
    """
    Smart visualization tool that generates appropriate charts for financial data.
    
    This tool:
    1. Accepts data from other tools or direct queries
    2. Determines the best chart type for the data
    3. Formats data for Recharts library
    4. Returns chart configuration with styling
    """
    
    # Chart color palettes
    COLOR_PALETTES = {
        "debt": ["#EF4444", "#F97316", "#F59E0B", "#EAB308", "#84CC16"],  # Red to green gradient
        "income_expense": ["#10B981", "#EF4444"],  # Green and red
        "category": ["#3B82F6", "#8B5CF6", "#EC4899", "#F59E0B", "#10B981", "#06B6D4", "#6366F1", "#F97316"],
        "timeline": ["#3B82F6", "#10B981", "#F59E0B"],  # Blue, green, orange
        "comparison": ["#3B82F6", "#10B981"],  # Blue and green
        "progress": ["#10B981", "#D1D5DB"],  # Green and gray
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
        return "create_visualization"
    
    @property
    def description(self) -> str:
        """Return the tool description."""
        return """Create financial visualizations and charts from data.
        
        This tool generates appropriate charts for financial data visualization.
        
        WHEN TO USE THIS TOOL:
        - User explicitly asks for a chart, graph, or visual representation
        - Data would be clearer with visual representation (e.g., debt breakdown, spending by category)
        - Comparing multiple values or showing trends over time
        - After retrieving financial data that benefits from visualization
        
        CHART TYPES SUPPORTED:
        1. "debt_breakdown" - Pie chart showing debt balances by type
        2. "debt_comparison" - Bar chart comparing debt metrics (balance, interest rate, payments)
        3. "payoff_timeline" - Line/bar chart showing debt payoff projection
        4. "spending_by_category" - Pie or bar chart of expenses by category
        5. "income_vs_expense" - Bar chart comparing income and expenses
        6. "net_worth_composition" - Pie chart of assets and liabilities
        7. "credit_score_trend" - Line chart of credit score over time
        8. "payment_comparison" - Bar chart comparing different payment scenarios
        9. "strategy_comparison" - Side-by-side bar charts (avalanche vs snowball)
        
        PARAMETERS:
        - chart_type: Type of chart to generate (required)
        - customer_id: Customer ID for data retrieval (required for Scenario A)
        - data: Direct data to visualize (optional, if already fetched)
        - title: Chart title (optional, auto-generated if not provided)
        - timeframe: For trend charts, specify period (e.g., "6m", "1y")
        
        EXAMPLES:
        - create_visualization(chart_type="debt_breakdown", customer_id="C001")
        - create_visualization(chart_type="payoff_timeline", customer_id="C001", data={...})
        - create_visualization(chart_type="spending_by_category", customer_id="C001", timeframe="3m")
        
        ERROR HANDLING:
        If the tool returns an error with 'status': 'error', DO NOT retry.
        Check the 'error' field for details and inform the user that visualization is unavailable.
        
        Returns: Chart configuration with data formatted for Recharts library
        """
    
    def execute(
        self,
        chart_type: str,
        customer_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        title: Optional[str] = None,
        timeframe: str = "3m"
    ) -> Dict[str, Any]:
        """Execute chart generation.
        
        Args:
            chart_type: Type of chart to generate (e.g., "debt_breakdown", "debt_comparison")
            customer_id: Customer ID for data retrieval (required for most chart types)
            data: Optional pre-fetched data to visualize
            title: Optional custom chart title
            timeframe: Time period for trend charts (e.g., "3m", "6m", "1y")
        
        Returns:
            Dictionary with chart configuration and data
        """
        try:
            print(f"\n📊 [DEBUG] create_visualization called")
            print(f"   - chart_type: {chart_type}")
            print(f"   - customer_id: {customer_id}")
            print(f"   - data: {data is not None}")
            print(f"   - title: {title}")
            print(f"   - timeframe: {timeframe}")
            
            if not chart_type:
                return {
                    "status": "error",
                    "error": "chart_type is required. Specify the type of visualization needed.",
                    "stop_retrying": True
                }
            
            # For most chart types, customer_id is required
            charts_needing_customer_id = [
                "debt_breakdown", "debt_comparison", "spending_by_category",
                "income_vs_expense", "net_worth_composition", "credit_score_trend"
            ]
            
            if chart_type in charts_needing_customer_id and not customer_id:
                return {
                    "status": "error",
                    "error": f"customer_id is required for {chart_type} chart. This chart requires database access.",
                    "stop_retrying": True
                }
            
            # Route to appropriate chart generator
            if chart_type == "debt_breakdown":
                result = self._create_debt_breakdown(customer_id, data, title)
            elif chart_type == "debt_comparison":
                result = self._create_debt_comparison(customer_id, data, title)
            elif chart_type == "payoff_timeline":
                result = self._create_payoff_timeline(customer_id, data, title)
            elif chart_type == "spending_by_category":
                result = self._create_spending_by_category(customer_id, timeframe, title)
            elif chart_type == "income_vs_expense":
                result = self._create_income_vs_expense(customer_id, timeframe, title)
            elif chart_type == "net_worth_composition":
                result = self._create_net_worth_composition(customer_id, data, title)
            elif chart_type == "credit_score_trend":
                result = self._create_credit_score_trend(customer_id, timeframe, title)
            elif chart_type == "payment_comparison":
                result = self._create_payment_comparison(data, title)
            elif chart_type == "strategy_comparison":
                result = self._create_strategy_comparison(data, title)
            else:
                return {
                    "status": "error",
                    "error": f"Unsupported chart_type: {chart_type}. Supported types: debt_breakdown, debt_comparison, payoff_timeline, spending_by_category, income_vs_expense, net_worth_composition, credit_score_trend, payment_comparison, strategy_comparison",
                    "stop_retrying": True
                }
            
            # Store chart data globally for frontend display
            if result and result.get("status") == "success":
                global _last_chart_data
                _last_chart_data = result
                print(f"\n✅ [VisualizationTool] Chart generated: {chart_type}")
                print(f"   - Title: {result.get('title', 'N/A')}")
                print(f"   - Chart type: {result.get('chart_config', {}).get('type', 'N/A')}")
                
                # Add a display message for the agent
                result["_display_message"] = (
                    f"✅ Chart created: {result.get('title')}. "
                    "The chart will be displayed automatically in the chat interface."
                )
            
            return result
        
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"\n❌ [ERROR] create_visualization exception: {str(e)}")
            print(f"Full traceback:\n{error_details}")
            return {
                "status": "error",
                "error": f"Visualization generation failed: {str(e)}",
                "details": error_details
            }
    
    def _create_debt_breakdown(self, customer_id: str, data: Optional[Dict], title: Optional[str]) -> Dict[str, Any]:
        """Create pie chart of debt balances by type."""
        if data:
            # Use provided data
            debts = data.get('debts', [])
        else:
            # Fetch from database
            if not customer_id:
                return {"status": "error", "error": "customer_id required when data not provided"}
            
            debts = self._fetch_customer_debts(customer_id)
        
        if not debts:
            return {"status": "error", "error": "No debt data found"}
        
        # Aggregate by debt type
        debt_by_type = {}
        for debt in debts:
            debt_type = debt.get('type', debt.get('debt_type', 'Other'))
            balance = debt.get('current_principal', debt.get('principal', 0))
            if debt_type in debt_by_type:
                debt_by_type[debt_type] += balance
            else:
                debt_by_type[debt_type] = balance
        
        # Format for pie chart
        chart_data = [
            {
                "name": debt_type.replace('_', ' ').title(),
                "value": round(balance, 2),
                "percentage": round((balance / sum(debt_by_type.values())) * 100, 1)
            }
            for debt_type, balance in debt_by_type.items()
        ]
        
        total_debt = sum(debt_by_type.values())
        
        return {
            "status": "success",
            "chart_type": "debt_breakdown",
            "title": title or f"Debt Breakdown (Total: ${total_debt:,.2f})",
            "chart_config": {
                "type": "pie",
                "data": chart_data,
                "dataKey": "value",
                "nameKey": "name",
                "colors": self.COLOR_PALETTES["debt"][:len(chart_data)],
                "legend": True,
                "tooltip": True,
                "labelFormat": "percentage"  # Show percentage in labels
            },
            "summary": {
                "total_debt": round(total_debt, 2),
                "debt_count": len(debts),
                "largest_debt": max(chart_data, key=lambda x: x['value'])
            }
        }
    
    def _create_debt_comparison(self, customer_id: str, data: Optional[Dict], title: Optional[str]) -> Dict[str, Any]:
        """Create bar chart comparing debt metrics."""
        if data:
            debts = data.get('debts', [])
        else:
            if not customer_id:
                return {"status": "error", "error": "customer_id required when data not provided"}
            debts = self._fetch_customer_debts(customer_id)
        
        if not debts:
            return {"status": "error", "error": "No debt data found"}
        
        # Format for bar chart
        chart_data = [
            {
                "name": debt.get('type', debt.get('debt_type', 'Other')).replace('_', ' ').title(),
                "balance": round(debt.get('current_principal', debt.get('principal', 0)), 2),
                "interest_rate": round(debt.get('interest_rate_apr', 0), 2),
                "monthly_payment": round(debt.get('min_payment_mo', 0), 2)
            }
            for debt in debts
        ]
        
        return {
            "status": "success",
            "chart_type": "debt_comparison",
            "title": title or "Debt Comparison",
            "chart_config": {
                "type": "bar",
                "data": chart_data,
                "bars": [
                    {"dataKey": "balance", "name": "Balance ($)", "color": "#EF4444"},
                    {"dataKey": "monthly_payment", "name": "Monthly Payment ($)", "color": "#F59E0B"}
                ],
                "xAxisKey": "name",
                "legend": True,
                "tooltip": True,
                "grid": True
            },
            "summary": {
                "total_balance": round(sum(d['balance'] for d in chart_data), 2),
                "total_monthly_payment": round(sum(d['monthly_payment'] for d in chart_data), 2),
                "avg_interest_rate": round(sum(d['interest_rate'] for d in chart_data) / len(chart_data), 2)
            }
        }
    
    def _create_payoff_timeline(self, customer_id: str, data: Optional[Dict], title: Optional[str]) -> Dict[str, Any]:
        """Create line chart showing debt payoff projection."""
        if not data:
            return {"status": "error", "error": "Payoff timeline requires data from debt_optimizer tool"}
        
        # Extract timeline data from debt_optimizer results
        if 'payoff_timeline' in data:
            timeline = data['payoff_timeline']
            chart_data = [
                {
                    "month": item.get('month_paid_off', idx + 1),
                    "debt": item.get('debt_type', f"Debt {idx + 1}").replace('_', ' ').title(),
                    "cumulative_paid": round(item.get('amount_paid', 0), 2)
                }
                for idx, item in enumerate(timeline)
            ]
        elif 'strategy_scenario' in data:
            # Avalanche/snowball scenario
            strategy = data['strategy_scenario']
            payoff_order = strategy.get('payoff_order', [])
            chart_data = [
                {
                    "month": item.get('month_paid_off', idx + 1),
                    "debt": item.get('debt_type', f"Debt {idx + 1}").replace('_', ' ').title(),
                }
                for idx, item in enumerate(payoff_order)
            ]
        else:
            return {"status": "error", "error": "No timeline data found in provided data"}
        
        return {
            "status": "success",
            "chart_type": "payoff_timeline",
            "title": title or "Debt Payoff Timeline",
            "chart_config": {
                "type": "line",
                "data": chart_data,
                "lines": [{"dataKey": "month", "name": "Months to Payoff", "color": "#3B82F6"}],
                "xAxisKey": "debt",
                "yAxisLabel": "Months",
                "legend": False,
                "tooltip": True,
                "grid": True
            },
            "summary": {
                "total_months": max((d.get('month', 0) for d in chart_data), default=0),
                "total_debts": len(chart_data)
            }
        }
    
    def _create_spending_by_category(self, customer_id: str, timeframe: str, title: Optional[str]) -> Dict[str, Any]:
        """Create pie chart of spending by category."""
        if not customer_id:
            return {"status": "error", "error": "customer_id required"}
        
        # Fetch spending data
        spending = self._fetch_spending_by_category(customer_id, timeframe)
        
        if not spending:
            return {"status": "error", "error": "No spending data found"}
        
        total_spending = sum(spending.values())
        chart_data = [
            {
                "name": category.replace('_', ' ').title(),
                "value": round(amount, 2),
                "percentage": round((amount / total_spending) * 100, 1)
            }
            for category, amount in spending.items()
        ]
        
        return {
            "status": "success",
            "chart_type": "spending_by_category",
            "title": title or f"Spending Breakdown ({timeframe})",
            "chart_config": {
                "type": "pie",
                "data": chart_data,
                "dataKey": "value",
                "nameKey": "name",
                "colors": self.COLOR_PALETTES["category"][:len(chart_data)],
                "legend": True,
                "tooltip": True,
                "labelFormat": "percentage"
            },
            "summary": {
                "total_spending": round(total_spending, 2),
                "top_category": max(chart_data, key=lambda x: x['value']),
                "timeframe": timeframe
            }
        }
    
    def _create_income_vs_expense(self, customer_id: str, timeframe: str, title: Optional[str]) -> Dict[str, Any]:
        """Create bar chart comparing income vs expenses."""
        if not customer_id:
            return {"status": "error", "error": "customer_id required"}
        
        # Fetch income and expense data
        monthly_data = self._fetch_income_expense_data(customer_id, timeframe)
        
        if not monthly_data:
            return {"status": "error", "error": "No income/expense data found"}
        
        return {
            "status": "success",
            "chart_type": "income_vs_expense",
            "title": title or f"Income vs Expenses ({timeframe})",
            "chart_config": {
                "type": "bar",
                "data": monthly_data,
                "bars": [
                    {"dataKey": "income", "name": "Income", "color": "#10B981"},
                    {"dataKey": "expenses", "name": "Expenses", "color": "#EF4444"}
                ],
                "xAxisKey": "month",
                "legend": True,
                "tooltip": True,
                "grid": True
            },
            "summary": {
                "avg_income": round(sum(d['income'] for d in monthly_data) / len(monthly_data), 2),
                "avg_expenses": round(sum(d['expenses'] for d in monthly_data) / len(monthly_data), 2),
                "avg_surplus": round(sum(d['income'] - d['expenses'] for d in monthly_data) / len(monthly_data), 2)
            }
        }
    
    def _create_net_worth_composition(self, customer_id: str, data: Optional[Dict], title: Optional[str]) -> Dict[str, Any]:
        """Create pie chart of net worth components."""
        if data:
            # Use provided data from financial_summary_tool
            net_worth = data.get('net_worth', {})
            assets = net_worth.get('total_assets', 0)
            liabilities = net_worth.get('total_liabilities', 0)
        else:
            if not customer_id:
                return {"status": "error", "error": "customer_id required when data not provided"}
            # Fetch from database
            assets, liabilities = self._fetch_net_worth_data(customer_id)
        
        chart_data = [
            {"name": "Assets", "value": round(assets, 2)},
            {"name": "Liabilities", "value": round(abs(liabilities), 2)}
        ]
        
        net_worth_value = assets - abs(liabilities)
        
        return {
            "status": "success",
            "chart_type": "net_worth_composition",
            "title": title or f"Net Worth: ${net_worth_value:,.2f}",
            "chart_config": {
                "type": "pie",
                "data": chart_data,
                "dataKey": "value",
                "nameKey": "name",
                "colors": ["#10B981", "#EF4444"],
                "legend": True,
                "tooltip": True,
                "labelFormat": "value"
            },
            "summary": {
                "net_worth": round(net_worth_value, 2),
                "assets": round(assets, 2),
                "liabilities": round(abs(liabilities), 2)
            }
        }
    
    def _create_credit_score_trend(self, customer_id: str, timeframe: str, title: Optional[str]) -> Dict[str, Any]:
        """Create line chart of credit score over time."""
        if not customer_id:
            return {"status": "error", "error": "customer_id required"}
        
        # Fetch credit score history
        credit_history = self._fetch_credit_score_history(customer_id, timeframe)
        
        if not credit_history:
            return {"status": "error", "error": "No credit score history found"}
        
        return {
            "status": "success",
            "chart_type": "credit_score_trend",
            "title": title or f"Credit Score Trend ({timeframe})",
            "chart_config": {
                "type": "line",
                "data": credit_history,
                "lines": [{"dataKey": "score", "name": "Credit Score", "color": "#3B82F6"}],
                "xAxisKey": "month",
                "yAxisLabel": "FICO Score",
                "yAxisDomain": [300, 850],
                "legend": False,
                "tooltip": True,
                "grid": True
            },
            "summary": {
                "current_score": credit_history[-1]['score'] if credit_history else 0,
                "change": credit_history[-1]['score'] - credit_history[0]['score'] if len(credit_history) > 1 else 0,
                "trend": "up" if len(credit_history) > 1 and credit_history[-1]['score'] > credit_history[0]['score'] else "down"
            }
        }
    
    def _create_payment_comparison(self, data: Dict, title: Optional[str]) -> Dict[str, Any]:
        """Create bar chart comparing different payment scenarios."""
        if not data:
            return {"status": "error", "error": "Payment comparison requires data"}
        
        # Extract comparison data (e.g., from debt_optimizer)
        scenarios = []
        
        if 'current_payment' in data and 'new_payment' in data:
            scenarios = [
                {"scenario": "Current", "payment": round(data['current_payment'], 2)},
                {"scenario": "Proposed", "payment": round(data['new_payment'], 2)}
            ]
        
        if not scenarios:
            return {"status": "error", "error": "No payment comparison data found"}
        
        return {
            "status": "success",
            "chart_type": "payment_comparison",
            "title": title or "Payment Comparison",
            "chart_config": {
                "type": "bar",
                "data": scenarios,
                "bars": [{"dataKey": "payment", "name": "Monthly Payment ($)", "color": "#3B82F6"}],
                "xAxisKey": "scenario",
                "legend": False,
                "tooltip": True,
                "grid": True
            },
            "summary": {
                "difference": round(scenarios[1]['payment'] - scenarios[0]['payment'], 2) if len(scenarios) > 1 else 0
            }
        }
    
    def _create_strategy_comparison(self, data: Dict, title: Optional[str]) -> Dict[str, Any]:
        """Create side-by-side comparison of debt payoff strategies."""
        if not data:
            return {"status": "error", "error": "Strategy comparison requires data"}
        
        # Extract strategy data (avalanche vs snowball)
        min_scenario = data.get('minimum_payment_scenario', {})
        strategy_scenario = data.get('strategy_scenario', {})
        strategy_name = data.get('strategy', 'Strategy')
        
        chart_data = [
            {
                "name": "Minimum Payments",
                "months": min_scenario.get('total_months', 0),
                "interest": round(min_scenario.get('total_interest', 0), 2)
            },
            {
                "name": strategy_name.title(),
                "months": strategy_scenario.get('total_months', 0),
                "interest": round(strategy_scenario.get('total_interest', 0), 2)
            }
        ]
        
        return {
            "status": "success",
            "chart_type": "strategy_comparison",
            "title": title or f"{strategy_name.title()} Strategy Comparison",
            "chart_config": {
                "type": "bar",
                "data": chart_data,
                "bars": [
                    {"dataKey": "months", "name": "Payoff Time (Months)", "color": "#3B82F6"},
                    {"dataKey": "interest", "name": "Total Interest ($)", "color": "#EF4444"}
                ],
                "xAxisKey": "name",
                "legend": True,
                "tooltip": True,
                "grid": True
            },
            "summary": {
                "months_saved": chart_data[0]['months'] - chart_data[1]['months'],
                "interest_saved": round(chart_data[0]['interest'] - chart_data[1]['interest'], 2)
            }
        }
    
    # Helper methods for database queries
    
    def _fetch_customer_debts(self, customer_id: str) -> List[Dict[str, Any]]:
        """Fetch customer debts from database."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT type, current_principal, interest_rate_apr, min_payment_mo, status
                FROM debts_loans
                WHERE customer_id = ? AND status = 'current'
                ORDER BY interest_rate_apr DESC
            """, (customer_id,))
            
            debts = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return debts
        except Exception as e:
            print(f"Error fetching debts: {e}")
            return []
    
    def _fetch_spending_by_category(self, customer_id: str, timeframe: str) -> Dict[str, float]:
        """Fetch spending aggregated by category."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Parse timeframe to months
            months = 3  # default
            if timeframe == '6m':
                months = 6
            elif timeframe == '12m' or timeframe == '1y':
                months = 12
            
            cursor.execute("""
                SELECT t.category_lvl1, SUM(ABS(t.amount)) as total
                FROM transactions t
                JOIN accounts a ON t.account_id = a.account_id
                WHERE a.customer_id = ?
                AND t.posted_date >= date('now', '-' || ? || ' months')
                AND t.amount < 0
                AND t.category_lvl1 != 'Income'
                GROUP BY t.category_lvl1
                ORDER BY total DESC
            """, (customer_id, months))
            
            result = {row[0]: row[1] for row in cursor.fetchall()}
            conn.close()
            return result
        except Exception as e:
            print(f"Error fetching spending: {e}")
            return {}
    
    def _fetch_income_expense_data(self, customer_id: str, timeframe: str) -> List[Dict[str, Any]]:
        """Fetch monthly income vs expense data."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Parse timeframe
            months = 3
            if timeframe == '6m':
                months = 6
            elif timeframe == '12m' or timeframe == '1y':
                months = 12
            
            cursor.execute("""
                SELECT 
                    strftime('%Y-%m', t.posted_date) as month,
                    SUM(CASE WHEN t.amount > 0 THEN t.amount ELSE 0 END) as income,
                    SUM(CASE WHEN t.amount < 0 THEN ABS(t.amount) ELSE 0 END) as expenses
                FROM transactions t
                JOIN accounts a ON t.account_id = a.account_id
                WHERE a.customer_id = ?
                AND t.posted_date >= date('now', '-' || ? || ' months')
                GROUP BY strftime('%Y-%m', t.posted_date)
                ORDER BY month ASC
            """, (customer_id, months))
            
            result = [
                {
                    "month": row[0],
                    "income": round(row[1], 2),
                    "expenses": round(row[2], 2)
                }
                for row in cursor.fetchall()
            ]
            conn.close()
            return result
        except Exception as e:
            print(f"Error fetching income/expense data: {e}")
            return []
    
    def _fetch_net_worth_data(self, customer_id: str) -> tuple:
        """Fetch total assets and liabilities."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get total assets
            cursor.execute("""
                SELECT COALESCE(SUM(current_value), 0) as total_assets
                FROM assets
                WHERE customer_id = ?
            """, (customer_id,))
            assets = cursor.fetchone()[0]
            
            # Get total liabilities (debts)
            cursor.execute("""
                SELECT COALESCE(SUM(current_principal), 0) as total_debt
                FROM debts_loans
                WHERE customer_id = ? AND status = 'current'
            """, (customer_id,))
            liabilities = cursor.fetchone()[0]
            
            conn.close()
            return assets, liabilities
        except Exception as e:
            print(f"Error fetching net worth: {e}")
            return 0, 0
    
    def _fetch_credit_score_history(self, customer_id: str, timeframe: str) -> List[Dict[str, Any]]:
        """Fetch credit score history."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Parse timeframe
            months = 3
            if timeframe == '6m':
                months = 6
            elif timeframe == '12m' or timeframe == '1y':
                months = 12
            
            cursor.execute("""
                SELECT as_of_month, fico_score
                FROM credit_reports
                WHERE customer_id = ?
                AND as_of_month >= date('now', '-' || ? || ' months')
                ORDER BY as_of_month ASC
            """, (customer_id, months))
            
            result = [
                {
                    "month": row[0],
                    "score": row[1]
                }
                for row in cursor.fetchall()
            ]
            conn.close()
            return result
        except Exception as e:
            print(f"Error fetching credit history: {e}")
            return []

