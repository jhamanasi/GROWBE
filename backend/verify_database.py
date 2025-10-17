#!/usr/bin/env python3
"""
Database verification script for Financial Advisory Agent.
Comprehensive verification of data accuracy and relationships.
"""

import sqlite3
import os

def verify_database(db_path="data/financial_data.db"):
    """Comprehensive database verification."""
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔍 Comprehensive Database Verification")
    print("=" * 50)
    
    # 1. Basic table verification
    print("\n📊 1. Table Structure Verification")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    
    expected_tables = [
        'accounts', 'assets', 'credit_reports', 'customers', 
        'debts_loans', 'employment_income', 'transactions'
    ]
    
    for table in expected_tables:
        if table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   ✅ {table}: {count:,} rows")
        else:
            print(f"   ❌ {table}: Missing")
    
    # 2. Persona verification
    print("\n👥 2. Persona Distribution Verification")
    cursor.execute("""
        SELECT persona_type, COUNT(*) as count 
        FROM customers 
        GROUP BY persona_type 
        ORDER BY count DESC
    """)
    
    persona_data = cursor.fetchall()
    total_customers = sum(count for _, count in persona_data)
    
    print(f"   Total customers: {total_customers}")
    for persona, count in persona_data:
        percentage = (count / total_customers) * 100
        print(f"   • {persona}: {count} customers ({percentage:.1f}%)")
    
    # 3. Specific persona customer verification
    print("\n🎯 3. Specific Persona Customer Verification")
    persona_customers = {
        'high_spending_student_debtor': ['C011', 'C014'],
        'aspiring_homebuyer_moderate_savings': ['C002', 'C015'],
        'credit_card_juggler': ['C008', 'C013'],
        'consistent_saver_idle_cash': ['C009', 'C017'],
        'freelancer_income_volatility': ['C010', 'C012']
    }
    
    for persona, expected_customers in persona_customers.items():
        cursor.execute("""
            SELECT customer_id, first_name, last_name 
            FROM customers 
            WHERE persona_type = ?
        """, (persona,))
        
        actual_customers = [row[0] for row in cursor.fetchall()]
        
        print(f"   {persona}:")
        print(f"     Expected: {expected_customers}")
        print(f"     Actual:   {actual_customers}")
        
        if set(expected_customers) == set(actual_customers):
            print(f"     ✅ Match")
        else:
            print(f"     ❌ Mismatch")
    
    # 4. Financial data verification
    print("\n💰 4. Financial Data Verification")
    
    # Check debt data
    cursor.execute("""
        SELECT 
            COUNT(*) as total_debts,
            COUNT(DISTINCT customer_id) as customers_with_debt,
            SUM(current_principal) as total_debt_amount,
            AVG(current_principal) as avg_debt_amount
        FROM debts_loans
    """)
    debt_stats = cursor.fetchone()
    print(f"   Debt Statistics:")
    print(f"     • Total debts: {debt_stats[0]}")
    print(f"     • Customers with debt: {debt_stats[1]}")
    print(f"     • Total debt amount: ${debt_stats[2]:,.2f}")
    print(f"     • Average debt: ${debt_stats[3]:,.2f}")
    
    # Check asset data
    cursor.execute("""
        SELECT 
            COUNT(*) as total_assets,
            COUNT(DISTINCT customer_id) as customers_with_assets,
            SUM(current_value) as total_asset_value,
            AVG(current_value) as avg_asset_value
        FROM assets
    """)
    asset_stats = cursor.fetchone()
    print(f"   Asset Statistics:")
    print(f"     • Total assets: {asset_stats[0]}")
    print(f"     • Customers with assets: {asset_stats[1]}")
    print(f"     • Total asset value: ${asset_stats[2]:,.2f}")
    print(f"     • Average asset: ${asset_stats[3]:,.2f}")
    
    # Check transaction data
    cursor.execute("""
        SELECT 
            COUNT(*) as total_transactions,
            COUNT(DISTINCT account_id) as accounts_with_transactions,
            SUM(amount) as total_transaction_amount,
            AVG(amount) as avg_transaction_amount
        FROM transactions
    """)
    transaction_stats = cursor.fetchone()
    print(f"   Transaction Statistics:")
    print(f"     • Total transactions: {transaction_stats[0]:,}")
    print(f"     • Accounts with transactions: {transaction_stats[1]}")
    print(f"     • Total transaction amount: ${transaction_stats[2]:,.2f}")
    print(f"     • Average transaction: ${transaction_stats[3]:,.2f}")
    
    # 5. Relationship verification
    print("\n🔗 5. Relationship Verification")
    
    # Customer-Account relationships
    cursor.execute("""
        SELECT COUNT(*) 
        FROM customers c 
        LEFT JOIN accounts a ON c.customer_id = a.customer_id
        WHERE a.customer_id IS NULL
    """)
    customers_without_accounts = cursor.fetchone()[0]
    print(f"   • Customers without accounts: {customers_without_accounts}")
    
    # Account-Transaction relationships
    cursor.execute("""
        SELECT COUNT(*) 
        FROM accounts a 
        LEFT JOIN transactions t ON a.account_id = t.account_id
        WHERE t.account_id IS NULL
    """)
    accounts_without_transactions = cursor.fetchone()[0]
    print(f"   • Accounts without transactions: {accounts_without_transactions}")
    
    # Customer-Debt relationships
    cursor.execute("""
        SELECT COUNT(*) 
        FROM customers c 
        LEFT JOIN debts_loans d ON c.customer_id = d.customer_id
        WHERE d.customer_id IS NULL
    """)
    customers_without_debts = cursor.fetchone()[0]
    print(f"   • Customers without debts: {customers_without_debts}")
    
    # Customer-Asset relationships
    cursor.execute("""
        SELECT COUNT(*) 
        FROM customers c 
        LEFT JOIN assets a ON c.customer_id = a.customer_id
        WHERE a.customer_id IS NULL
    """)
    customers_without_assets = cursor.fetchone()[0]
    print(f"   • Customers without assets: {customers_without_assets}")
    
    # 6. Sample data verification
    print("\n🔍 6. Sample Data Verification")
    
    # Show sample customers with their personas
    cursor.execute("""
        SELECT 
            c.customer_id, 
            c.first_name, 
            c.last_name, 
            c.persona_type,
            c.base_salary_annual,
            c.fico_baseline,
            COUNT(a.account_id) as account_count,
            COUNT(d.debt_id) as debt_count,
            COUNT(ast.asset_id) as asset_count
        FROM customers c
        LEFT JOIN accounts a ON c.customer_id = a.customer_id
        LEFT JOIN debts_loans d ON c.customer_id = d.customer_id
        LEFT JOIN assets ast ON c.customer_id = ast.customer_id
        GROUP BY c.customer_id
        ORDER BY c.persona_type, c.customer_id
        LIMIT 10
    """)
    
    sample_data = cursor.fetchall()
    print("   Sample customer profiles:")
    for row in sample_data:
        print(f"     • {row[0]}: {row[1]} {row[2]} ({row[3]})")
        print(f"       Salary: ${row[4]:,}, FICO: {row[5]}")
        print(f"       Accounts: {row[6]}, Debts: {row[7]}, Assets: {row[8]}")
    
    # 7. NL2SQL test queries
    print("\n🔧 7. NL2SQL Test Queries")
    
    # Test query 1: Get customer persona
    cursor.execute("SELECT persona_type FROM customers WHERE customer_id = 'C011'")
    persona = cursor.fetchone()[0]
    print(f"   Query 1 - C011 persona: {persona}")
    
    # Test query 2: Get customer debt summary
    cursor.execute("""
        SELECT 
            type, 
            current_principal, 
            interest_rate_apr, 
            min_payment_mo 
        FROM debts_loans 
        WHERE customer_id = 'C011'
    """)
    debts = cursor.fetchall()
    print(f"   Query 2 - C011 debts: {len(debts)} debts")
    for debt in debts:
        print(f"     • {debt[0]}: ${debt[1]:,.2f} at {debt[2]}% APR, min payment: ${debt[3]:,.2f}")
    
    # Test query 3: Get customer financial summary
    cursor.execute("""
        SELECT 
            c.base_salary_annual,
            SUM(d.current_principal) as total_debt,
            SUM(a.current_value) as total_assets,
            cr.fico_score
        FROM customers c
        LEFT JOIN debts_loans d ON c.customer_id = d.customer_id
        LEFT JOIN assets a ON c.customer_id = a.customer_id
        LEFT JOIN credit_reports cr ON c.customer_id = cr.customer_id
        WHERE c.customer_id = 'C011'
        GROUP BY c.customer_id
    """)
    summary = cursor.fetchone()
    print(f"   Query 3 - C011 financial summary:")
    print(f"     • Salary: ${summary[0]:,}")
    print(f"     • Total debt: ${summary[1] or 0:,.2f}")
    print(f"     • Total assets: ${summary[2] or 0:,.2f}")
    print(f"     • FICO score: {summary[3]}")
    
    conn.close()
    
    print("\n✅ Database verification completed!")
    return True

if __name__ == "__main__":
    verify_database()
