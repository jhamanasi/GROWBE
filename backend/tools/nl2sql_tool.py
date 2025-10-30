"""
NL2SQL Tool for Financial Advisory Agent.

This tool converts natural language questions to SQLite SQL queries for the financial database,
handling all financial use cases including customer profiles, loans, accounts, transactions, and assessments.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from .base_tool import BaseTool
from .sqlite_tool import SQLiteTool
from pathlib import Path
import sqlite3

# Comprehensive system prompt for financial database queries
FINANCIAL_SQL_SYSTEM_PROMPT = (
    "You are a senior financial data analyst generating safe, correct SQLite SQL queries for a financial advisory database. "
    "You are given a database schema and a user question. "
    "Respond ONLY with a SQLite SQL statement suitable for SQLite. "
    
    "CRITICAL FINANCIAL DATABASE RULES: "
    
    "1. TABLE STRUCTURE: "
    "   - customers: Core customer profiles with persona_type, base_salary_annual, fico_baseline "
    "   - debts_loans: All loans and debts (student, auto, credit_card, personal) "
    "   - accounts: Financial accounts (checking, savings, credit) with balances and institutions "
    "   - transactions: Individual transactions with amounts, merchants, categories "
    "   - credit_reports: Monthly credit score snapshots with utilization and history "
    "   - employment_income: Employment details and income information "
    "   - assets: Customer assets (cash, investments, property) with liquidity tiers "
    "   - customer_assessments: New customer assessment data (goals, risk tolerance, etc.) "
    "   - monthly_cashflow: Monthly income/expense summaries (if available) "
    
    "2. CURRENCY HANDLING: "
    "   - All monetary amounts are stored as REAL (dollars, not cents) "
    "   - Use ROUND(amount, 2) for currency formatting "
    "   - Format large numbers with commas: printf('%,.2f', amount) "
    
    "3. DATE HANDLING: "
    "   - Dates are stored as TEXT in YYYY-MM-DD format "
    "   - Use date() function for date comparisons: date('2024-01-01') "
    "   - For monthly data, use LIKE '2024-01%' for month matching "
    "   - Use strftime('%Y-%m', date_column) for month grouping "
    
    "4. CUSTOMER IDENTIFICATION: "
    "   - Customer IDs are TEXT format (e.g., 'C001', 'C002') "
    "   - Always use exact matches: customer_id = 'C001' "
    "   - For multiple customers, use IN ('C001', 'C002') "
    
    "5. FINANCIAL CALCULATIONS: "
    "   - Use SUM() for total amounts across multiple records "
    "   - Use AVG() for average rates, scores, or amounts "
    "   - Use COUNT(DISTINCT customer_id) for unique customer counts "
    "   - Use MAX()/MIN() for highest/lowest values "
    "   - Calculate debt-to-income: SUM(debt_payments) / annual_income * 100 "
    
    "6. RELATIONSHIP RULES: "
    "   - customers -> debts_loans: customers.customer_id = debts_loans.customer_id "
    "   - customers -> accounts: customers.customer_id = accounts.customer_id "
    "   - accounts -> transactions: accounts.account_id = transactions.account_id "
    "   - customers -> credit_reports: customers.customer_id = credit_reports.customer_id "
    "   - customers -> employment_income: customers.customer_id = employment_income.customer_id "
    "   - customers -> assets: customers.customer_id = assets.customer_id "
    "   - customers -> customer_assessments: customers.customer_id = customer_assessments.customer_id "
    
    "7. COMMON FINANCIAL QUERIES: "
    "   - Customer profile: SELECT * FROM customers WHERE customer_id = 'C001' "
    "   - All customer loans: SELECT * FROM debts_loans WHERE customer_id = 'C001' "
    "   - Student loans only: SELECT * FROM debts_loans WHERE customer_id = 'C001' AND type = 'student' "
    "   - Loan tenure/term: SELECT term_months, origination_date, original_principal FROM debts_loans WHERE customer_id = 'C001' AND type = 'student' "
    "   - Original loan amount: SELECT original_principal, origination_date FROM debts_loans WHERE customer_id = 'C001' "
    "   - Account balances: SELECT SUM(current_balance) FROM accounts WHERE customer_id = 'C001' "
    "   - Recent transactions: SELECT * FROM transactions t JOIN accounts a ON t.account_id = a.account_id WHERE a.customer_id = 'C001' ORDER BY posted_date DESC LIMIT 10 "
    "   - Credit score history: SELECT * FROM credit_reports WHERE customer_id = 'C001' ORDER BY as_of_month DESC "
    "   - Debt summary: SELECT type, SUM(current_principal), AVG(interest_rate_apr) FROM debts_loans WHERE customer_id = 'C001' GROUP BY type "
    
    "   IMPORTANT SYNONYMS: "
    "   - 'tenure', 'term', 'term months', 'loan term', 'repayment period', 'original tenure' → term_months column "
    "   - 'original amount', 'original loan', 'how much did I borrow' → original_principal column "
    "   - 'current balance', 'how much do I owe', 'remaining balance' → current_principal column "
    "   - 'monthly payment', 'minimum payment', 'required payment' → min_payment_mo column "
    
    "8. AGGREGATION PATTERNS: "
    "   - Customer totals: GROUP BY customer_id "
    "   - Loan types: GROUP BY type "
    "   - Account types: GROUP BY account_type "
    "   - Time periods: GROUP BY strftime('%Y-%m', date_column) "
    "   - Always use meaningful aliases: AS total_debt, AS avg_rate, AS customer_count "
    
    "9. FILTERING PATTERNS: "
    "   - High debt: current_principal > 50000 "
    "   - High interest: interest_rate_apr > 10 "
    "   - Recent dates: posted_date >= '2024-01-01' "
    "   - Specific types: type IN ('student', 'auto', 'credit_card') "
    "   - Active accounts: status = 'open' "
    
    "10. SAFETY RULES: "
    "    - Only use SELECT, WITH, and read-only operations "
    "    - Never use INSERT, UPDATE, DELETE, DROP, or ALTER "
    "    - Always use LIMIT for large result sets (default 100) "
    "    - Use parameterized queries for user input "
    "    - Validate table and column names exist "
    
    "11. ERROR HANDLING: "
    "    - If a table doesn't exist, suggest alternative queries "
    "    - If data is missing, use LEFT JOIN and handle NULLs "
    "    - For complex queries, break into multiple simpler queries "
    
    "12. COMPLETENESS RULES: "
    "    - For debt/loan questions, ALWAYS include balance, interest rate, payment amount, and loan terms "
    "    - For account questions, include balance, account type, and institution "
    "    - For transaction questions, include amount, date, merchant, and category "
    "    - For customer questions, include all relevant profile information "
    "    - Use SELECT * when comprehensive information is needed "
    "    - Don't be overly restrictive - provide complete financial details "
    
    "13. CONTEXT AWARENESS: "
    "    - If user asks 'what type of debt', they want complete debt information "
    "    - If user asks 'how much do I owe', include all debt details with amounts "
    "    - If user asks 'what are my accounts', include balances and types "
    "    - Always provide actionable, complete financial information "
    
    "14. RESPONSE FORMAT: "
    "    - Return ONLY the SQL statement "
    "    - No explanations, no markdown, no code blocks "
    "    - Clean, readable SQL with proper indentation "
    "    - Use semicolon only for multiple statements "
)

def _load_financial_schema() -> str:
    """Load the financial database schema."""
    try:
        # Connect to the financial database and get schema
        conn = sqlite3.connect("data/financial_data.db")
        cursor = conn.cursor()
        
        schema_parts = []
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            schema_parts.append(f"-- {table_name.upper()} TABLE")
            schema_parts.append(f"CREATE TABLE {table_name} (")
            
            column_defs = []
            for col in columns:
                col_id, col_name, col_type, not_null, default_val, pk = col
                col_def = f"  {col_name} {col_type}"
                if pk:
                    col_def += " PRIMARY KEY"
                if not_null:
                    col_def += " NOT NULL"
                if default_val:
                    col_def += f" DEFAULT {default_val}"
                column_defs.append(col_def)
            
            schema_parts.append(",\n".join(column_defs))
            schema_parts.append(");")
            schema_parts.append("")
        
        # Get foreign key relationships
        cursor.execute("SELECT * FROM sqlite_master WHERE type='table' AND sql LIKE '%FOREIGN KEY%'")
        fk_tables = cursor.fetchall()
        
        if fk_tables:
            schema_parts.append("-- FOREIGN KEY RELATIONSHIPS")
            for table in fk_tables:
                schema_parts.append(f"-- {table[1]}: {table[4]}")
        
        conn.close()
        
        return "\n".join(schema_parts)
        
    except Exception as e:
        print(f"Warning: Could not load schema from database: {e}")
        # Fallback to basic schema
        return """
-- FINANCIAL DATABASE SCHEMA
-- customers: Core customer profiles
CREATE TABLE customers (
  customer_id TEXT PRIMARY KEY,
  first_name TEXT,
  last_name TEXT,
  base_salary_annual INTEGER,
  fico_baseline INTEGER,
  persona_type TEXT
);

-- debts_loans: All loans and debts
CREATE TABLE debts_loans (
  debt_id TEXT PRIMARY KEY,
  customer_id TEXT,
  type TEXT,
  current_principal REAL,
  interest_rate_apr REAL,
  min_payment_mo REAL,
  status TEXT
);

-- accounts: Financial accounts
CREATE TABLE accounts (
  account_id INTEGER PRIMARY KEY,
  customer_id TEXT,
  account_type TEXT,
  current_balance REAL,
  institution TEXT,
  status TEXT
);

-- transactions: Individual transactions
CREATE TABLE transactions (
  txn_id TEXT PRIMARY KEY,
  account_id INTEGER,
  posted_date TEXT,
  amount REAL,
  merchant TEXT,
  category_lvl1 TEXT
);

-- credit_reports: Credit score history
CREATE TABLE credit_reports (
  credit_report_id TEXT PRIMARY KEY,
  customer_id TEXT,
  as_of_month TEXT,
  fico_score INTEGER,
  credit_utilization_pct REAL
);
"""

def _generate_financial_sql(question: str, schema: str) -> str:
    """Generate SQL for financial database queries."""
    try:
        from strands import Agent
        from strands.models.openai import OpenAIModel
        import os
        
        # Create OpenAI model for SQL generation
        openai_model = OpenAIModel(
            client_args={
                "api_key": os.getenv("OPENAI_API_KEY"),
            },
            model_id="gpt-4o",  # Using gpt-4o for best SQL generation
            params={
                "max_tokens": 1500,  # Increased for complex SQL queries
                "temperature": 0.05,  # Very low temperature for maximum consistency
            }
        )
        
        # Create SQL generation agent
        sql_agent = Agent(
            model=openai_model,
            system_prompt=FINANCIAL_SQL_SYSTEM_PROMPT
        )
        
        # Prepare user prompt with enhanced context
        user_prompt = (
            f"FINANCIAL DATABASE SCHEMA:\n{schema}\n\n"
            f"USER QUESTION: {question}\n\n"
            "Generate a COMPLETE SQLite SQL query that provides comprehensive information to answer this question. "
            "For financial questions, include ALL relevant details (amounts, rates, terms, dates, etc.). "
            "Use SELECT * or SELECT with multiple fields to provide complete, actionable information. "
            "The user needs complete financial details, not just basic information. "
            "Do not include explanations, markdown, or code blocks. "
            "Return only the clean SQL statement."
        )
        
        # Generate SQL
        result = sql_agent(user_prompt)
        content = getattr(result, "content", str(result)).strip()
        
        # Clean up the response
        if content.startswith("```"):
            lines = content.split("\n")
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            content = "\n".join(lines).strip()
            
        # Remove any leading/trailing whitespace and ensure it ends properly
        content = content.strip()
        if not content.endswith(';'):
            content += ';'
            
        return content

    except Exception as e:
        print(f"Error generating SQL: {e}")
        # Re-raise the exception so the class method can handle the fallback
        raise e

def _generate_fallback_sql(question: str) -> str:
    """Generate fallback SQL based on keywords with improved logic."""
    question_lower = question.lower()
    
    # Extract customer ID if mentioned
    customer_id = None
    if 'c001' in question_lower or 'maya' in question_lower:
        customer_id = 'C001'
    elif 'c002' in question_lower or 'aisha' in question_lower:
        customer_id = 'C002'
    elif 'c003' in question_lower or 'lucas' in question_lower:
        customer_id = 'C003'
    
    # Loan/debt queries (check this first as it's more specific)
    if any(word in question_lower for word in ['loan', 'debt', 'student', 'credit card', 'auto', 'personal']):
        if customer_id:
            if 'student' in question_lower:
                return f"SELECT * FROM debts_loans WHERE customer_id = '{customer_id}' AND type = 'student';"
            elif 'credit' in question_lower:
                return f"SELECT * FROM debts_loans WHERE customer_id = '{customer_id}' AND type = 'credit_card';"
            else:
                return f"SELECT * FROM debts_loans WHERE customer_id = '{customer_id}';"
        elif 'student' in question_lower:
            return "SELECT * FROM debts_loans WHERE type = 'student' LIMIT 10;"
        elif 'total' in question_lower and 'debt' in question_lower:
            if customer_id:
                return f"SELECT SUM(current_principal) as total_debt FROM debts_loans WHERE customer_id = '{customer_id}';"
            else:
                return "SELECT customer_id, SUM(current_principal) as total_debt FROM debts_loans GROUP BY customer_id LIMIT 10;"
        else:
            return "SELECT * FROM debts_loans LIMIT 10;"
    
    # Customer profile queries
    elif any(word in question_lower for word in ['customer', 'profile', 'person', 'who is']):
        if customer_id:
            return f"SELECT * FROM customers WHERE customer_id = '{customer_id}';"
        else:
            return "SELECT * FROM customers LIMIT 10;"
    
    # Account queries
    elif any(word in question_lower for word in ['account', 'balance', 'checking', 'savings', 'bank']):
        if customer_id:
            if 'total' in question_lower or 'sum' in question_lower:
                return f"SELECT SUM(current_balance) as total_balance FROM accounts WHERE customer_id = '{customer_id}';"
            else:
                return f"SELECT * FROM accounts WHERE customer_id = '{customer_id}';"
        else:
            return "SELECT * FROM accounts LIMIT 10;"
    
    # Transaction queries
    elif any(word in question_lower for word in ['transaction', 'spending', 'expense', 'income', 'recent']):
        if customer_id:
            if 'recent' in question_lower:
                return f"SELECT t.*, a.customer_id FROM transactions t JOIN accounts a ON t.account_id = a.account_id WHERE a.customer_id = '{customer_id}' ORDER BY t.posted_date DESC LIMIT 10;"
            else:
                return f"SELECT t.*, a.customer_id FROM transactions t JOIN accounts a ON t.account_id = a.account_id WHERE a.customer_id = '{customer_id}' LIMIT 10;"
        else:
            return "SELECT t.*, a.customer_id FROM transactions t JOIN accounts a ON t.account_id = a.account_id LIMIT 10;"
    
    # Credit score queries
    elif any(word in question_lower for word in ['credit', 'fico', 'score']):
        if customer_id:
            return f"SELECT * FROM credit_reports WHERE customer_id = '{customer_id}' ORDER BY as_of_month DESC;"
        else:
            return "SELECT * FROM credit_reports LIMIT 10;"
    
    # Employment/income queries
    elif any(word in question_lower for word in ['employment', 'income', 'salary', 'job', 'employer']):
        if customer_id:
            return f"SELECT * FROM employment_income WHERE customer_id = '{customer_id}';"
        else:
            return "SELECT * FROM employment_income LIMIT 10;"
    
    # Assets queries
    elif any(word in question_lower for word in ['asset', 'investment', 'cash', 'property']):
        if customer_id:
            return f"SELECT * FROM assets WHERE customer_id = '{customer_id}';"
        else:
            return "SELECT * FROM assets LIMIT 10;"
    
    # Assessment queries
    elif any(word in question_lower for word in ['assessment', 'goal', 'risk', 'tolerance']):
        if customer_id:
            return f"SELECT * FROM customer_assessments WHERE customer_id = '{customer_id}';"
        else:
            return "SELECT * FROM customer_assessments LIMIT 10;"
    
    # Default fallback
    else:
        return "SELECT * FROM customers LIMIT 5;"

LAST_SQL_DETAILS: Dict[str, Any] = {}


def get_last_sql_details(clear: bool = True) -> Optional[Dict[str, Any]]:
    global LAST_SQL_DETAILS
    details = LAST_SQL_DETAILS.copy() if LAST_SQL_DETAILS else None
    if clear:
        LAST_SQL_DETAILS = {}
    return details


class NL2SQLTool(BaseTool):
    """Convert natural language questions to SQLite SQL for financial database queries."""
    
    @property
    def name(self) -> str:
        return "nl2sql_query"
    
    @property
    def description(self) -> str:
        return """Convert natural language questions to SQLite SQL queries for the financial database.

        This tool can answer questions about:
        - Customer profiles and personal information
        - Student loans, debts, and payment history
        - Bank accounts and balances
        - Transaction history and spending patterns
        - Credit scores and credit reports
        - Employment and income information
        - Assets and investments
        - Customer assessments and goals

        Args:
            question: Natural language question about financial data
            limit: Maximum number of rows to return (default: 100)
            allow_writes: Whether to allow write operations (default: False)
            
        Returns:
            Dictionary with 'sql' (the generated query) and 'result' (query results)
        """
    
    def _generate_sql(self, question: str, schema: str) -> str:
        """Generate SQL query from natural language question using OpenAI."""
        try:
            # Use OpenAI for all SQL generation - it should be perfect now
            return _generate_financial_sql(question, schema)
        except Exception as e:
            print(f"OpenAI SQL generation failed: {e}")
            print("Falling back to keyword-based SQL generation...")
            return self._generate_fallback_sql(question)
    
    def execute(self, question: str, limit: Optional[int] = 100, allow_writes: bool = False) -> Dict[str, Any]:
        """Execute natural language to SQL conversion and query execution."""
        if not question or not question.strip():
            raise ValueError("question is required and cannot be empty")

        try:
            # Guard: only allow predefined demo users C001–C018
            import re
            m = re.search(r"\bC(\d{3,})\b", question.upper())
            if not m:
                return "I can only access financial data for existing customers with valid customer IDs. Please use the assessment flow for new users."
            try:
                if int(m.group(1)) > 18:
                    return "I can only access financial data for existing customers with valid customer IDs. Please use the assessment flow for new users."
            except ValueError:
                return "I can only access financial data for existing customers with valid customer IDs. Please use the assessment flow for new users."

            # Load financial database schema
            schema = _load_financial_schema()
            
            # Generate SQL query
            sql = self._generate_sql(question.strip(), schema)

            # Validate SQL for safety
            if not self._validate_sql(sql):
                raise ValueError("Generated SQL query is not safe for execution")
            
            # Execute query via SQLite tool
            sqlite_tool = SQLiteTool()
            result = sqlite_tool.execute(sql=sql, limit=limit, write=allow_writes)
            
            # Generate formatted response based on query type and results
            formatted_response = self._generate_formatted_response(question, result, sql)

            # Build structured SQL details for UI consumption
            sql_details = self._build_sql_details(sql, result)

            # Store globally so the API can attach it to responses
            global LAST_SQL_DETAILS
            LAST_SQL_DETAILS = sql_details

            # Return both the formatted response for the agent AND structured data
            return {
                "formatted_response": formatted_response,
                "sql": sql,
                "result": result,
                "sql_details": sql_details
            }
            
        except Exception as e:
            return f"I encountered an error while accessing your financial data: {str(e)}. Please try rephrasing your question or contact support if the issue persists."
    
    def _generate_formatted_response(self, question: str, result: Dict[str, Any], sql: str) -> str:
        """Generate a human-readable response based on the query results."""
        try:
            # Check if query was successful
            if not result or not result.get('ok', False):
                return "I encountered an issue accessing your financial data. Please try rephrasing your question."
            
            rows = result.get('rows', [])
            if not rows:
                return self._handle_no_data_response(question)
            
            # Determine query type and format response accordingly
            question_lower = question.lower()
            
            if any(keyword in question_lower for keyword in ['debt', 'loan', 'type of debt', 'what debt']):
                return self._format_debt_response(rows)
            elif any(keyword in question_lower for keyword in ['account', 'balance', 'accounts']):
                return self._format_account_response(rows)
            elif any(keyword in question_lower for keyword in ['transaction', 'spending', 'expense']):
                return self._format_transaction_response(rows)
            elif any(keyword in question_lower for keyword in ['credit', 'fico', 'score']):
                return self._format_credit_response(rows)
            elif any(keyword in question_lower for keyword in ['income', 'salary', 'employment']):
                return self._format_income_response(rows)
            else:
                return self._format_generic_response(rows, question)
                
        except Exception as e:
            return f"I found your financial data but encountered an issue formatting the response. Please try rephrasing your question."
    
    def _handle_no_data_response(self, question: str) -> str:
        """Handle cases where no data is found."""
        question_lower = question.lower()
        
        if any(keyword in question_lower for keyword in ['debt', 'loan']):
            return "I don't see any debt or loan records in your financial profile. This could mean you're debt-free or the records haven't been loaded yet."
        elif any(keyword in question_lower for keyword in ['account', 'balance']):
            return "I don't see any account records in your financial profile. This could mean the account information hasn't been loaded yet."
        else:
            return "I don't see any records matching your request in your financial profile. Please try rephrasing your question or contact support if you believe this is an error."
    
    def _format_debt_response(self, rows: List[Dict[str, Any]]) -> str:
        """Format debt/loan information."""
        if not rows:
            return "I don't see any debt or loan records in your financial profile."
        
        debt_types = []
        total_balance = 0
        
        for row in rows:
            debt_type = row.get('type', 'Unknown')
            balance = row.get('current_principal', 0)
            rate = row.get('interest_rate_apr', 0)
            payment = row.get('min_payment_mo', 0)
            
            total_balance += balance
            
            if debt_type == 'student':
                debt_types.append(f"**Student loan** with a current balance of **${balance:,.2f}** at **{rate}%** interest rate and a minimum monthly payment of **${payment:,.2f}**")
            elif debt_type == 'credit_card':
                debt_types.append(f"**Credit card debt** with a current balance of **${balance:,.2f}** at **{rate}%** interest rate and a minimum monthly payment of **${payment:,.2f}**")
            elif debt_type == 'auto':
                debt_types.append(f"**Auto loan** with a current balance of **${balance:,.2f}** at **{rate}%** interest rate and a minimum monthly payment of **${payment:,.2f}**")
            elif debt_type == 'personal':
                debt_types.append(f"**Personal loan** with a current balance of **${balance:,.2f}** at **{rate}%** interest rate and a minimum monthly payment of **${payment:,.2f}**")
            else:
                debt_types.append(f"**{debt_type.title()} debt** with a current balance of **${balance:,.2f}** at **{rate}%** interest rate and a minimum monthly payment of **${payment:,.2f}**")
        
        if len(debt_types) == 1:
            return f"You have a {debt_types[0]}."
        else:
            response = f"You have {len(debt_types)} types of debt:\n\n"
            for i, debt in enumerate(debt_types, 1):
                response += f"{i}. {debt}\n"
            response += f"\n**Total debt balance: ${total_balance:,.2f}**"
            return response
    
    def _format_account_response(self, rows: List[Dict[str, Any]]) -> str:
        """Format account information."""
        if not rows:
            return "I don't see any account records in your financial profile."
        
        accounts = []
        total_balance = 0
        
        for row in rows:
            account_type = row.get('account_type', 'Unknown')
            balance = row.get('current_balance', 0)
            institution = row.get('institution', 'Unknown')
            
            total_balance += balance
            
            if account_type == 'checking':
                accounts.append(f"**Checking account** at {institution} with a balance of **${balance:,.2f}**")
            elif account_type == 'savings':
                accounts.append(f"**Savings account** at {institution} with a balance of **${balance:,.2f}**")
            elif account_type == 'credit':
                accounts.append(f"**Credit account** at {institution} with a balance of **${balance:,.2f}**")
            else:
                accounts.append(f"**{account_type.title()} account** at {institution} with a balance of **${balance:,.2f}**")
        
        if len(accounts) == 1:
            return f"You have a {accounts[0]}."
        else:
            response = f"You have {len(accounts)} accounts:\n\n"
            for i, account in enumerate(accounts, 1):
                response += f"{i}. {account}\n"
            response += f"\n**Total account balance: ${total_balance:,.2f}**"
            return response
    
    def _format_transaction_response(self, rows: List[Dict[str, Any]]) -> str:
        """Format transaction information."""
        if not rows:
            return "I don't see any transaction records in your financial profile."
        
        # For now, just return a summary
        total_amount = sum(row.get('amount', 0) for row in rows)
        return f"I found {len(rows)} transactions in your profile with a total amount of **${total_amount:,.2f}**. Would you like me to break this down by category or time period?"
    
    def _format_credit_response(self, rows: List[Dict[str, Any]]) -> str:
        """Format credit score information."""
        if not rows:
            return "I don't see any credit score records in your financial profile."
        
        # Get the most recent credit score
        latest_row = max(rows, key=lambda x: x.get('as_of_month', ''))
        score = latest_row.get('fico_score', 0)
        utilization = latest_row.get('credit_utilization_pct', 0)
        
        return f"Your most recent **FICO credit score is {score}** with a credit utilization of **{utilization:.1f}%**."
    
    def _format_income_response(self, rows: List[Dict[str, Any]]) -> str:
        """Format income information."""
        if not rows:
            return "I don't see any income records in your financial profile."
        
        # Get the most recent income
        latest_row = max(rows, key=lambda x: x.get('as_of_month', ''))
        salary = latest_row.get('base_salary_annual', 0)
        
        return f"Your annual income is **${salary:,.2f}**."
    
    def _format_generic_response(self, rows: List[Dict[str, Any]], question: str) -> str:
        """Format generic response for other queries."""
        if not rows:
            return "I don't see any records matching your request in your financial profile."
        
        return f"I found {len(rows)} record(s) in your financial profile. Would you like me to provide more specific details about any particular aspect?"

    def _build_sql_details(self, sql: str, result: Dict[str, Any]) -> Dict[str, Any]:
        try:
            rows = result.get('rows', []) if isinstance(result, dict) else []
            columns = result.get('columns', []) if isinstance(result, dict) else []
            if not columns and rows and isinstance(rows[0], dict):
                columns = list(rows[0].keys())
            result_count = len(rows)

            return {
                "query": sql.strip() if isinstance(sql, str) else "",
                "result_count": result_count,
                "columns": columns,
                "rows": rows[:100] if rows else [],
                "total_rows": result_count,
                "execution_time": result.get('execution_time') if isinstance(result, dict) else None,
                "truncated": result_count > 100
            }
        except Exception as build_exc:
            print(f"Failed to build SQL details: {build_exc}")
            return {
                "query": sql.strip() if isinstance(sql, str) else "",
                "result_count": 0,
                "columns": [],
                "rows": [],
                "total_rows": 0,
                "execution_time": None,
                "truncated": False
            }

    def _validate_sql(self, sql: str) -> bool:
        """Validate SQL query for safety."""
        if not sql or not sql.strip():
            return False
        
        sql_upper = sql.upper().strip()
        
        # Check for dangerous operations
        dangerous_keywords = [
            'INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'CREATE', 'TRUNCATE',
            'EXEC', 'EXECUTE', 'CALL', 'GRANT', 'REVOKE', 'COMMIT', 'ROLLBACK'
        ]
        
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                print(f"Warning: Dangerous keyword '{keyword}' found in SQL query")
                return False
        
        # Check for valid SQL structure
        if not sql_upper.startswith(('SELECT', 'WITH')):
            print("Warning: SQL query does not start with SELECT or WITH")
            return False
        
        return True
    
    def _generate_fallback_sql(self, question: str) -> str:
        """Generate fallback SQL based on keywords."""
        question_lower = question.lower()
        
        # Extract customer ID if mentioned
        customer_id = None
        if 'c001' in question_lower or 'maya' in question_lower:
            customer_id = 'C001'
        elif 'c002' in question_lower or 'aisha' in question_lower:
            customer_id = 'C002'
        elif 'c003' in question_lower or 'lucas' in question_lower:
            customer_id = 'C003'
        
        # Loan/debt queries (check first as they're more specific)
        if any(word in question_lower for word in ['loan', 'debt', 'student', 'credit card', 'auto', 'personal']):
            if customer_id:
                if 'student' in question_lower:
                    return f"SELECT * FROM debts_loans WHERE customer_id = '{customer_id}' AND type = 'student';"
                elif 'credit' in question_lower:
                    return f"SELECT * FROM debts_loans WHERE customer_id = '{customer_id}' AND type = 'credit_card';"
                else:
                    return f"SELECT * FROM debts_loans WHERE customer_id = '{customer_id}';"
            elif 'student' in question_lower:
                return "SELECT * FROM debts_loans WHERE type = 'student' LIMIT 10;"
            elif 'total' in question_lower and 'debt' in question_lower:
                if customer_id:
                    return f"SELECT SUM(current_principal) as total_debt FROM debts_loans WHERE customer_id = '{customer_id}';"
                else:
                    return "SELECT customer_id, SUM(current_principal) as total_debt FROM debts_loans GROUP BY customer_id LIMIT 10;"
            else:
                return "SELECT * FROM debts_loans LIMIT 10;"
        
        # Account queries
        elif any(word in question_lower for word in ['account', 'balance', 'checking', 'savings', 'bank']):
            if customer_id:
                if 'total' in question_lower or 'sum' in question_lower:
                    return f"SELECT SUM(current_balance) as total_balance FROM accounts WHERE customer_id = '{customer_id}';"
                else:
                    return f"SELECT * FROM accounts WHERE customer_id = '{customer_id}';"
            else:
                return "SELECT * FROM accounts LIMIT 10;"
        
        # Transaction queries
        elif any(word in question_lower for word in ['transaction', 'spending', 'expense', 'income', 'recent']):
            if customer_id:
                if 'recent' in question_lower:
                    return f"SELECT t.*, a.customer_id FROM transactions t JOIN accounts a ON t.account_id = a.account_id WHERE a.customer_id = '{customer_id}' ORDER BY t.posted_date DESC LIMIT 10;"
                else:
                    return f"SELECT t.*, a.customer_id FROM transactions t JOIN accounts a ON t.account_id = a.account_id WHERE a.customer_id = '{customer_id}' LIMIT 10;"
            else:
                return "SELECT t.*, a.customer_id FROM transactions t JOIN accounts a ON t.account_id = a.account_id LIMIT 10;"
        
        # Credit score queries
        elif any(word in question_lower for word in ['credit', 'fico', 'score']):
            if customer_id:
                return f"SELECT * FROM credit_reports WHERE customer_id = '{customer_id}' ORDER BY as_of_month DESC;"
            else:
                return "SELECT * FROM credit_reports LIMIT 10;"
        
        # Employment/income queries
        elif any(word in question_lower for word in ['employment', 'income', 'salary', 'job', 'employer']):
            if customer_id:
                return f"SELECT * FROM employment_income WHERE customer_id = '{customer_id}';"
            else:
                return "SELECT * FROM employment_income LIMIT 10;"
        
        # Assets queries
        elif any(word in question_lower for word in ['asset', 'investment', 'cash', 'property']):
            if customer_id:
                return f"SELECT * FROM assets WHERE customer_id = '{customer_id}';"
            else:
                return "SELECT * FROM assets LIMIT 10;"
        
        # Assessment queries
        elif any(word in question_lower for word in ['assessment', 'goal', 'risk', 'tolerance']):
            if customer_id:
                return f"SELECT * FROM customer_assessments WHERE customer_id = '{customer_id}';"
            else:
                return "SELECT * FROM customer_assessments LIMIT 10;"
        
        # Customer profile queries (check last as it's most general)
        elif any(word in question_lower for word in ['customer', 'profile', 'person', 'who is']):
            if customer_id:
                return f"SELECT * FROM customers WHERE customer_id = '{customer_id}';"
            else:
                return "SELECT * FROM customers LIMIT 10;"
        
        # Default fallback
        else:
            return "SELECT * FROM customers LIMIT 5;"