#!/usr/bin/env python3
"""
Database population script for Financial Advisory Agent.
Loads CSV data into SQLite database.
"""

import sqlite3
import pandas as pd
import os
from pathlib import Path
from datetime import datetime

def load_csv_data(db_path, data_dir="data"):
    """Load CSV data into the database."""
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        print("Please run db_setup.py first to create the database.")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("📊 Loading CSV data into database...")
    
    # Define CSV file mappings
    csv_files = {
        'customers': 'user.csv',
        'employment_income': 'income_and_employment.csv',
        'accounts': 'account.csv',
        'transactions': 'transaction.csv',
        'credit_reports': 'credit_report.csv',
        'debts_loans': 'debt.csv',
        'assets': 'asset.csv'
        # Note: monthly_cashflow.csv not available in current dataset
    }
    
    loaded_tables = []
    failed_tables = []
    
    for table_name, csv_file in csv_files.items():
        csv_path = os.path.join(data_dir, csv_file)
        
        if not os.path.exists(csv_path):
            print(f"⚠️  CSV file not found: {csv_path}")
            failed_tables.append(table_name)
            continue
        
        try:
            print(f"📥 Loading {table_name} from {csv_file}...")
            
            # Read CSV file
            df = pd.read_csv(csv_path)
            
            # Handle data type conversions
            df = handle_data_conversions(df, table_name)
            
            # Insert data into database (replace existing data)
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            
            print(f"✅ Loaded {len(df)} rows into {table_name} (total: {row_count})")
            loaded_tables.append(table_name)
            
        except Exception as e:
            print(f"❌ Error loading {table_name}: {str(e)}")
            failed_tables.append(table_name)
    
    conn.commit()
    conn.close()
    
    # Summary
    print(f"\n📋 Data Loading Summary:")
    print(f"✅ Successfully loaded: {len(loaded_tables)} tables")
    print(f"❌ Failed to load: {len(failed_tables)} tables")
    
    if loaded_tables:
        print(f"   Loaded tables: {', '.join(loaded_tables)}")
    
    if failed_tables:
        print(f"   Failed tables: {', '.join(failed_tables)}")
    
    return len(failed_tables) == 0

def handle_data_conversions(df, table_name):
    """Handle data type conversions for different tables."""
    
    if table_name == 'customers':
        # Convert boolean columns
        bool_columns = ['kyc_verified_bool', 'consent_data_sharing_bool']
        for col in bool_columns:
            if col in df.columns:
                df[col] = df[col].map({'True': True, 'False': False, True: True, False: False})
        
        # Convert date columns
        date_columns = ['dob', 'created_at']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d')
    
    elif table_name == 'employment_income':
        # Convert date columns
        date_columns = ['start_date']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d')
    
    elif table_name == 'accounts':
        # Convert date columns
        date_columns = ['opened_date']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d')
    
    elif table_name == 'transactions':
        # Convert date columns
        date_columns = ['posted_date']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d')
        
        # Convert boolean columns
        bool_columns = ['is_recurring_bool']
        for col in bool_columns:
            if col in df.columns:
                df[col] = df[col].map({'True': True, 'False': False, True: True, False: False})
    
    elif table_name == 'debts_loans':
        # Convert date columns
        date_columns = ['origination_date']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d')
    
    # Handle NaN values - replace with None for SQLite
    df = df.where(pd.notnull(df), None)
    
    return df

def verify_data_loading(db_path):
    """Verify that data was loaded correctly."""
    print(f"\n🔍 Verifying data loading: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check row counts for each table
    tables = [
        'customers', 'employment_income', 'accounts', 'transactions',
        'credit_reports', 'debts_loans', 'assets', 'monthly_cashflow'
    ]
    
    print("📊 Row counts by table:")
    total_rows = 0
    
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   • {table}: {count:,} rows")
            total_rows += count
        except Exception as e:
            print(f"   • {table}: Error - {str(e)}")
    
    print(f"\n📈 Total rows loaded: {total_rows:,}")
    
    # Check persona distribution
    print(f"\n👥 Persona distribution:")
    cursor.execute("""
        SELECT persona_type, COUNT(*) as count 
        FROM customers 
        GROUP BY persona_type 
        ORDER BY count DESC
    """)
    
    persona_counts = cursor.fetchall()
    for persona, count in persona_counts:
        print(f"   • {persona}: {count} customers")
    
    # Check some sample data
    print(f"\n🔍 Sample customer data:")
    cursor.execute("""
        SELECT customer_id, first_name, last_name, persona_type, base_salary_annual, fico_baseline
        FROM customers 
        LIMIT 5
    """)
    
    sample_data = cursor.fetchall()
    for row in sample_data:
        print(f"   • {row[0]}: {row[1]} {row[2]} ({row[3]}) - Salary: ${row[4]:,}, FICO: {row[5]}")
    
    conn.close()
    return total_rows > 0

def check_data_relationships(db_path):
    """Check that foreign key relationships are working."""
    print(f"\n🔗 Checking data relationships...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check customer-account relationships
    cursor.execute("""
        SELECT COUNT(*) 
        FROM customers c 
        LEFT JOIN accounts a ON c.customer_id = a.customer_id
        WHERE a.customer_id IS NULL
    """)
    customers_without_accounts = cursor.fetchone()[0]
    print(f"   • Customers without accounts: {customers_without_accounts}")
    
    # Check account-transaction relationships
    cursor.execute("""
        SELECT COUNT(*) 
        FROM accounts a 
        LEFT JOIN transactions t ON a.account_id = t.account_id
        WHERE t.account_id IS NULL
    """)
    accounts_without_transactions = cursor.fetchone()[0]
    print(f"   • Accounts without transactions: {accounts_without_transactions}")
    
    # Check customer-debt relationships
    cursor.execute("""
        SELECT COUNT(*) 
        FROM customers c 
        LEFT JOIN debts_loans d ON c.customer_id = d.customer_id
        WHERE d.customer_id IS NULL
    """)
    customers_without_debts = cursor.fetchone()[0]
    print(f"   • Customers without debts: {customers_without_debts}")
    
    # Check customer-asset relationships
    cursor.execute("""
        SELECT COUNT(*) 
        FROM customers c 
        LEFT JOIN assets a ON c.customer_id = a.customer_id
        WHERE a.customer_id IS NULL
    """)
    customers_without_assets = cursor.fetchone()[0]
    print(f"   • Customers without assets: {customers_without_assets}")
    
    conn.close()

if __name__ == "__main__":
    print("🚀 Starting Database Population")
    print("=" * 50)
    
    db_path = "data/financial_data.db"
    
    try:
        # Load CSV data
        success = load_csv_data(db_path)
        
        if success:
            # Verify data loading
            if verify_data_loading(db_path):
                # Check relationships
                check_data_relationships(db_path)
                print("\n✅ Database population completed successfully!")
                print(f"📁 Database location: {os.path.abspath(db_path)}")
            else:
                print("\n❌ Data verification failed")
        else:
            print("\n❌ Database population failed")
            
    except Exception as e:
        print(f"\n❌ Error during database population: {str(e)}")
        raise
