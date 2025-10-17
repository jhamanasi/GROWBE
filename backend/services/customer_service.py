"""
Customer Service for Financial Advisory Agent.
Manages customer profiles and assessments for both existing and new users.
"""

import sqlite3
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path

class Customer:
    """Customer model for database operations."""
    def __init__(self, **kwargs):
        self.customer_id = kwargs.get('customer_id')
        self.first_name = kwargs.get('first_name')
        self.last_name = kwargs.get('last_name')
        self.dob = kwargs.get('dob')
        self.country = kwargs.get('country', 'USA')
        self.state = kwargs.get('state')
        self.zip = kwargs.get('zip')
        self.household_id = kwargs.get('household_id')
        self.marital_status = kwargs.get('marital_status')
        self.dependents_cnt = kwargs.get('dependents_cnt')
        self.education_level = kwargs.get('education_level')
        self.student_status = kwargs.get('student_status')
        self.citizenship_status = kwargs.get('citizenship_status')
        self.kyc_verified_bool = kwargs.get('kyc_verified_bool')
        self.consent_data_sharing_bool = kwargs.get('consent_data_sharing_bool')
        self.created_at = kwargs.get('created_at')
        self.savings_rate_target = kwargs.get('savings_rate_target')
        self.base_salary_annual = kwargs.get('base_salary_annual')
        self.fico_baseline = kwargs.get('fico_baseline')
        self.cc_util_baseline = kwargs.get('cc_util_baseline')
        self.persona_type = kwargs.get('persona_type')

class CustomerAssessment:
    """Customer assessment model for database operations."""
    def __init__(self, **kwargs):
        self.customer_id = kwargs.get('customer_id')
        self.email = kwargs.get('email')
        self.phone = kwargs.get('phone')
        self.primary_goal = kwargs.get('primary_goal')
        self.debt_status = kwargs.get('debt_status')
        self.employment_status = kwargs.get('employment_status')
        self.timeline = kwargs.get('timeline')
        self.risk_tolerance = kwargs.get('risk_tolerance')
        self.assessment_date = kwargs.get('assessment_date')

class CustomerService:
    """Service class for managing customers and assessments in the database."""
    
    def __init__(self, db_path: str = "data/financial_data.db"):
        self.db_path = db_path
        self._ensure_db_exists()
    
    def _ensure_db_exists(self):
        """Ensure the database file exists."""
        db_file = Path(self.db_path)
        if not db_file.exists():
            raise FileNotFoundError(f"Database file not found: {self.db_path}")
    
    def _get_connection(self):
        """Get a database connection."""
        return sqlite3.connect(self.db_path)
    
    def _row_to_customer(self, row) -> Customer:
        """Convert database row to Customer model."""
        return Customer(
            customer_id=row[0],
            first_name=row[1],
            last_name=row[2],
            dob=row[3],
            country=row[4],
            state=row[5],
            zip=row[6],
            household_id=row[7],
            marital_status=row[8],
            dependents_cnt=row[9],
            education_level=row[10],
            student_status=row[11],
            citizenship_status=row[12],
            kyc_verified_bool=bool(row[13]) if row[13] is not None else None,
            consent_data_sharing_bool=bool(row[14]) if row[14] is not None else None,
            created_at=row[15],
            savings_rate_target=row[16],
            base_salary_annual=row[17],
            fico_baseline=row[18],
            cc_util_baseline=row[19],
            persona_type=row[20]
        )
    
    def _row_to_assessment(self, row) -> CustomerAssessment:
        """Convert database row to CustomerAssessment model."""
        return CustomerAssessment(
            customer_id=row[0],
            email=row[1],
            phone=row[2],
            primary_goal=row[3],
            debt_status=row[4],
            employment_status=row[5],
            timeline=row[6],
            risk_tolerance=row[7],
            assessment_date=row[8]
        )
    
    def _generate_customer_id(self) -> str:
        """Generate a new customer ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT customer_id FROM customers ORDER BY customer_id DESC LIMIT 1")
            last_customer = cursor.fetchone()
            
            if last_customer:
                # Extract number from last customer ID (e.g., C018 -> 18)
                last_number = int(last_customer[0][1:])  # Remove 'C' prefix
                new_number = last_number + 1
            else:
                new_number = 1
            
            return f"C{new_number:03d}"
    
    def create_customer(self, customer_data: Dict[str, Any]) -> Customer:
        """Create a new customer from assessment form data."""
        customer_id = self._generate_customer_id()
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO customers (
                    customer_id, first_name, last_name, country, created_at, base_salary_annual
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                customer_id,
                customer_data.get('first_name'),
                customer_data.get('last_name'),
                customer_data.get('country', 'USA'),
                datetime.now().strftime('%Y-%m-%d'),
                customer_data.get('annual_income')
            ))
            conn.commit()
        
        return self.get_customer(customer_id)
    
    def create_assessment(self, customer_id: str, assessment_data: Dict[str, Any]) -> CustomerAssessment:
        """Create a new customer assessment."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO customer_assessments (
                    customer_id, email, phone, primary_goal, debt_status, 
                    employment_status, assessment_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                customer_id,
                assessment_data.get('email'),
                assessment_data.get('phone'),
                assessment_data.get('primary_goal'),
                assessment_data.get('debt_status'),
                assessment_data.get('employment_status'),
                datetime.now().strftime('%Y-%m-%d')
            ))
            conn.commit()
        
        return self.get_customer_assessment(customer_id)
    
    def get_customer(self, customer_id: str) -> Optional[Customer]:
        """Get a customer by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM customers WHERE customer_id = ?", (customer_id,))
            row = cursor.fetchone()
            
            if row:
                return self._row_to_customer(row)
            return None
    
    def get_customer_by_session_id(self, session_id: str) -> Optional[Customer]:
        """Get a customer by session ID (for existing users)."""
        # For now, we'll use customer_id as session_id
        # In a real system, you'd have a separate session management
        return self.get_customer(session_id)
    
    def get_customer_assessment(self, customer_id: str) -> Optional[CustomerAssessment]:
        """Get customer assessment by customer ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM customer_assessments WHERE customer_id = ?", (customer_id,))
            row = cursor.fetchone()
            
            if row:
                return self._row_to_assessment(row)
            return None
    
    def update_customer(self, customer_id: str, update_data: Dict[str, Any]) -> Optional[Customer]:
        """Update customer information."""
        # Build dynamic update query
        update_fields = []
        values = []
        
        for field, value in update_data.items():
            if value is not None:
                update_fields.append(f"{field} = ?")
                values.append(value)
        
        if not update_fields:
            return self.get_customer(customer_id)
        
        values.append(customer_id)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE customers 
                SET {', '.join(update_fields)}
                WHERE customer_id = ?
            """, values)
            conn.commit()
        
        return self.get_customer(customer_id)
    
    def update_assessment(self, customer_id: str, update_data: Dict[str, Any]) -> Optional[CustomerAssessment]:
        """Update customer assessment information."""
        # Build dynamic update query
        update_fields = []
        values = []
        
        for field, value in update_data.items():
            if value is not None:
                update_fields.append(f"{field} = ?")
                values.append(value)
        
        if not update_fields:
            return self.get_customer_assessment(customer_id)
        
        values.append(customer_id)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE customer_assessments 
                SET {', '.join(update_fields)}
                WHERE customer_id = ?
            """, values)
            conn.commit()
        
        return self.get_customer_assessment(customer_id)
    
    def assign_persona(self, customer_id: str) -> str:
        """Automatically assign persona based on customer profile and assessment."""
        customer = self.get_customer(customer_id)
        assessment = self.get_customer_assessment(customer_id)
        
        if not customer:
            return "general"
        
        # If customer has assessment data (new user), use assessment logic
        if assessment:
            return self._assign_persona_from_assessment(customer, assessment)
        else:
            # If customer has full financial data (existing user), use data-driven logic
            return self._assign_persona_from_data(customer)
    
    def _assign_persona_from_assessment(self, customer: Customer, assessment: CustomerAssessment) -> str:
        """Assign persona based on assessment data for new users."""
        # Simple rules-based assignment
        if (assessment.primary_goal == "student_loans" and 
            assessment.debt_status == "high" and 
            customer.base_salary_annual and customer.base_salary_annual < 70000):
            return "high_spending_student_debtor"
        
        elif (assessment.primary_goal == "home_buying" and 
              customer.base_salary_annual and customer.base_salary_annual < 80000):
            return "aspiring_homebuyer_moderate_savings"
        
        elif (assessment.debt_status == "high" and 
              "credit" in assessment.primary_goal.lower()):
            return "credit_card_juggler"
        
        elif (assessment.debt_status == "none" and 
              customer.base_salary_annual and customer.base_salary_annual > 100000):
            return "consistent_saver_idle_cash"
        
        elif assessment.employment_status in ["freelancer", "contract", "part_time"]:
            return "freelancer_income_volatility"
        
        else:
            return "general"
    
    def _assign_persona_from_data(self, customer: Customer) -> str:
        """Assign persona based on existing financial data for existing users."""
        # For existing users, we already have persona assigned in the database
        return customer.persona_type or "general"
    
    def get_customer_context(self, customer_id: str) -> str:
        """Get customer context for the agent."""
        customer = self.get_customer(customer_id)
        assessment = self.get_customer_assessment(customer_id)
        
        if not customer:
            return "Customer not found"
        
        # Check if this is an existing user with full financial data
        has_financial_data = self._has_financial_data(customer_id)
        
        if has_financial_data:
            # Existing user with full financial profile
            return self._get_existing_user_context(customer)
        else:
            # New user with assessment data
            return self._get_new_user_context(customer, assessment)
    
    def _has_financial_data(self, customer_id: str) -> bool:
        """Check if customer has financial data in related tables."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if customer has accounts, debts, or assets
            cursor.execute("SELECT COUNT(*) FROM accounts WHERE customer_id = ?", (customer_id,))
            account_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM debts_loans WHERE customer_id = ?", (customer_id,))
            debt_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM assets WHERE customer_id = ?", (customer_id,))
            asset_count = cursor.fetchone()[0]
            
            return account_count > 0 or debt_count > 0 or asset_count > 0
    
    def _get_existing_user_context(self, customer: Customer) -> str:
        """Get context for existing users with full financial data."""
        # Get financial summary from database
        financial_summary = self._get_financial_summary(customer.customer_id)
        
        return f"""
CUSTOMER: {customer.first_name} {customer.last_name}
PERSONA: {customer.persona_type or 'Not assigned'}
ANNUAL INCOME: ${customer.base_salary_annual:,}
FICO SCORE: {customer.fico_baseline}

FULL FINANCIAL PROFILE AVAILABLE:
{financial_summary}

This customer has complete financial data including accounts, transactions, debts, and assets.
Use NL2SQL to query specific financial information as needed.
"""
    
    def _get_new_user_context(self, customer: Customer, assessment: CustomerAssessment) -> str:
        """Get context for new users with assessment data."""
        if not assessment:
            return f"""
CUSTOMER: {customer.first_name} {customer.last_name}
PERSONA: {customer.persona_type or 'Not assigned yet'}
ANNUAL INCOME: ${customer.base_salary_annual:,}

This is a new customer with limited information.
Ask assessment questions to gather more details about their financial situation.
"""
        
        return f"""
CUSTOMER: {customer.first_name} {customer.last_name}
PERSONA: {customer.persona_type or 'Not assigned yet'}
ANNUAL INCOME: ${customer.base_salary_annual:,}

ASSESSMENT DATA:
- Primary Goal: {assessment.primary_goal or 'Not specified'}
- Debt Status: {assessment.debt_status or 'Not specified'}
- Employment: {assessment.employment_status or 'Not specified'}
- Timeline: {assessment.timeline or 'Not specified'}
- Risk Tolerance: {assessment.risk_tolerance or 'Not specified'}
- Email: {assessment.email or 'Not provided'}
- Phone: {assessment.phone or 'Not provided'}

This is a new customer. Continue gathering assessment information and provide personalized advice.
"""
    
    def _get_financial_summary(self, customer_id: str) -> str:
        """Get financial summary for existing users."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Get debt summary
            cursor.execute("""
                SELECT 
                    COUNT(*) as debt_count,
                    SUM(current_principal) as total_debt,
                    AVG(interest_rate_apr) as avg_rate
                FROM debts_loans 
                WHERE customer_id = ?
            """, (customer_id,))
            debt_data = cursor.fetchone()
            
            # Get asset summary
            cursor.execute("""
                SELECT 
                    COUNT(*) as asset_count,
                    SUM(current_value) as total_assets
                FROM assets 
                WHERE customer_id = ?
            """, (customer_id,))
            asset_data = cursor.fetchone()
            
            # Get account summary
            cursor.execute("""
                SELECT 
                    COUNT(*) as account_count,
                    SUM(current_balance) as total_balance
                FROM accounts 
                WHERE customer_id = ?
            """, (customer_id,))
            account_data = cursor.fetchone()
            
            summary = f"""- Total Debt: ${debt_data[1] or 0:,.2f} ({debt_data[0]} accounts, avg rate: {debt_data[2] or 0:.2f}%)
- Total Assets: ${asset_data[1] or 0:,.2f} ({asset_data[0]} assets)
- Account Balance: ${account_data[1] or 0:,.2f} ({account_data[0]} accounts)"""
            
            return summary
    
    def get_all_customers(self) -> List[Customer]:
        """Get all customers."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM customers ORDER BY created_at DESC")
            rows = cursor.fetchall()
            
            return [self._row_to_customer(row) for row in rows]
    
    def get_customers_by_persona(self, persona_type: str) -> List[Customer]:
        """Get customers by persona type."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM customers WHERE persona_type = ? ORDER BY created_at DESC", (persona_type,))
            rows = cursor.fetchall()
            
            return [self._row_to_customer(row) for row in rows]
    
    def delete_customer(self, customer_id: str) -> bool:
        """Delete a customer and all associated data."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Delete assessment first (foreign key constraint)
            cursor.execute("DELETE FROM customer_assessments WHERE customer_id = ?", (customer_id,))
            
            # Delete customer
            cursor.execute("DELETE FROM customers WHERE customer_id = ?", (customer_id,))
            
            conn.commit()
            return cursor.rowcount > 0


# Global customer service instance
customer_service = CustomerService()
