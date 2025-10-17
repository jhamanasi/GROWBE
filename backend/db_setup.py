#!/usr/bin/env python3
"""
Database setup script for Financial Advisory Agent.
Creates SQLite database with financial schema including persona_type column.
"""

import sqlite3
import os
from pathlib import Path

def create_financial_database():
    """Create the financial database with all required tables."""
    
    # Database file path
    db_path = "data/financial_data.db"
    
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    # Remove existing database if it exists
    if os.path.exists(db_path):
        print(f"⚠️  Removing existing database: {db_path}")
        os.remove(db_path)
    
    # Create new database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🏗️  Creating financial database schema...")
    
    # Create customers table (updated with persona_type)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id        VARCHAR(10)    PRIMARY KEY,
            first_name         TEXT            NOT NULL,
            last_name          TEXT            NOT NULL,
            dob                DATE,
            country            TEXT            DEFAULT 'USA',
            state              VARCHAR(2),
            zip                VARCHAR(10),
            household_id       VARCHAR(10),
            marital_status     VARCHAR(20),
            dependents_cnt     INTEGER,
            education_level    VARCHAR(30),
            student_status     VARCHAR(20),
            citizenship_status VARCHAR(30),
            kyc_verified_bool  BOOLEAN,
            consent_data_sharing_bool BOOLEAN,
            created_at         DATE,
            savings_rate_target NUMERIC(5,3),
            base_salary_annual INTEGER,
            fico_baseline      INTEGER,
            cc_util_baseline   NUMERIC(5,3),
            persona_type       VARCHAR(50)
        )
    """)
    print("✅ Created customers table with persona_type column")
    
    # Create employment_income table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employment_income (
            customer_id            VARCHAR(10)   NOT NULL,
            status                 VARCHAR(20),
            employer_name          TEXT,
            industry               VARCHAR(50),
            role                   VARCHAR(50),
            base_salary_annual     INTEGER,
            pay_frequency          VARCHAR(20),
            variable_income_avg_mo INTEGER,
            start_date             DATE,
            PRIMARY KEY (customer_id, start_date),
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        )
    """)
    print("✅ Created employment_income table")
    
    # Create accounts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            account_id        VARCHAR(16)   PRIMARY KEY,
            customer_id       VARCHAR(10)   NOT NULL,
            account_type      VARCHAR(20),
            institution       VARCHAR(100),
            opened_date       DATE,
            interest_rate_apr NUMERIC(6,3),
            credit_limit      NUMERIC(14,2),
            current_balance   NUMERIC(14,2),
            status            VARCHAR(20),
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        )
    """)
    print("✅ Created accounts table")
    
    # Create transactions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            txn_id         VARCHAR(10)   PRIMARY KEY,
            account_id     VARCHAR(16)   NOT NULL,
            posted_date    DATE           NOT NULL,
            amount         NUMERIC(14,2)  NOT NULL,
            merchant       TEXT,
            mcc            VARCHAR(10),
            category_lvl1  VARCHAR(50),
            category_lvl2  VARCHAR(50),
            is_recurring_bool BOOLEAN,
            FOREIGN KEY (account_id) REFERENCES accounts(account_id)
        )
    """)
    print("✅ Created transactions table")
    
    # Create credit_reports table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS credit_reports (
            credit_report_id  VARCHAR(8)   PRIMARY KEY,
            customer_id       VARCHAR(10)  NOT NULL,
            as_of_month       VARCHAR(7)   NOT NULL,
            fico_score        INTEGER,
            credit_utilization_pct NUMERIC(5,2),
            total_open_accounts INTEGER,
            derogatory_marks_cnt INTEGER,
            hard_inquiries_12m  INTEGER,
            avg_account_age_months INTEGER,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        )
    """)
    print("✅ Created credit_reports table")
    
    # Create debts_loans table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS debts_loans (
            debt_id            VARCHAR(8)   PRIMARY KEY,
            customer_id        VARCHAR(10)  NOT NULL,
            type               VARCHAR(30),
            origination_date   DATE,
            original_principal NUMERIC(14,2),
            current_principal  NUMERIC(14,2),
            interest_rate_apr  NUMERIC(6,3),
            term_months        INTEGER,
            min_payment_mo     NUMERIC(14,2),
            status             VARCHAR(20),
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        )
    """)
    print("✅ Created debts_loans table")
    
    # Create assets table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assets (
            asset_id       VARCHAR(8)   PRIMARY KEY,
            customer_id    VARCHAR(10)  NOT NULL,
            type           VARCHAR(30),
            current_value  NUMERIC(14,2),
            liquidity_tier VARCHAR(20),
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        )
    """)
    print("✅ Created assets table")
    
    # Create monthly_cashflow table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS monthly_cashflow (
            customer_id         VARCHAR(10) NOT NULL,
            month               VARCHAR(7)  NOT NULL,
            gross_income_mo     NUMERIC(14,2),
            net_income_mo       NUMERIC(14,2),
            spend_total_mo      NUMERIC(14,2),
            spend_essentials_mo NUMERIC(14,2),
            spend_discretionary_mo NUMERIC(14,2),
            debt_service_mo     NUMERIC(14,2),
            savings_mo          NUMERIC(14,2),
            subscriptions_mo    NUMERIC(14,2),
            largest_category    VARCHAR(50),
            volatility_income_pct NUMERIC(8,4),
            volatility_income_3m_pct NUMERIC(8,4),
            PRIMARY KEY (customer_id, month),
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        )
    """)
    print("✅ Created monthly_cashflow table")
    
    # Create indexes for better performance
    print("🔍 Creating indexes...")
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_customers_persona ON customers(persona_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_customers_state_zip ON customers(state, zip)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_emp_customer ON employment_income(customer_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_accounts_customer ON accounts(customer_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_accounts_type ON accounts(account_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tx_account ON transactions(account_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tx_posted_date ON transactions(posted_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tx_account_posted ON transactions(account_id, posted_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_credit_customer_month ON credit_reports(customer_id, as_of_month)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_credit_customer ON credit_reports(customer_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_debt_customer ON debts_loans(customer_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_debt_type ON debts_loans(type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_assets_customer ON assets(customer_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_assets_liquidity ON assets(liquidity_tier)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cashflow_customer_month ON monthly_cashflow(customer_id, month)")
    
    print("✅ Created all indexes")
    
    # Commit and close
    conn.commit()
    conn.close()
    
    print(f"🎉 Database created successfully: {db_path}")
    return db_path

def verify_database_structure(db_path):
    """Verify the database structure was created correctly."""
    print(f"\n🔍 Verifying database structure: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    
    print(f"📋 Found {len(tables)} tables:")
    for table in tables:
        print(f"   • {table[0]}")
    
    # Check if persona_type column exists in customers table
    cursor.execute("PRAGMA table_info(customers)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    
    if 'persona_type' in column_names:
        print("✅ persona_type column found in customers table")
    else:
        print("❌ persona_type column NOT found in customers table")
    
    # Show customers table structure
    print(f"\n📊 Customers table structure:")
    for col in columns:
        print(f"   • {col[1]} ({col[2]})")
    
    conn.close()
    return len(tables) == 8  # Should have 8 tables

if __name__ == "__main__":
    print("🚀 Starting Financial Database Setup")
    print("=" * 50)
    
    try:
        # Create database
        db_path = create_financial_database()
        
        # Verify structure
        if verify_database_structure(db_path):
            print("\n✅ Database setup completed successfully!")
            print(f"📁 Database location: {os.path.abspath(db_path)}")
            print("\n📝 Next steps:")
            print("   1. Run populate_database.py to load CSV data")
            print("   2. Verify data loading with verification script")
        else:
            print("\n❌ Database setup failed - structure verification failed")
            
    except Exception as e:
        print(f"\n❌ Error during database setup: {str(e)}")
        raise