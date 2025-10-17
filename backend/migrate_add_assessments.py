#!/usr/bin/env python3
"""
Migration script to add customer_assessments table to existing financial database.
This script safely adds the new table without affecting existing data.
"""

import sqlite3
import os
from datetime import datetime

def migrate_add_assessments_table(db_path="data/financial_data.db"):
    """Add customer_assessments table to existing database."""
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        print("Please ensure the financial database exists before running migration.")
        return False
    
    # Backup the database first
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"📋 Creating backup: {backup_path}")
    
    try:
        # Create backup
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✅ Backup created successfully")
    except Exception as e:
        print(f"❌ Failed to create backup: {str(e)}")
        return False
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔧 Starting migration...")
    
    try:
        # Check if table already exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='customer_assessments'
        """)
        
        if cursor.fetchone():
            print("⚠️  customer_assessments table already exists. Skipping creation.")
            conn.close()
            return True
        
        # Create customer_assessments table
        cursor.execute("""
            CREATE TABLE customer_assessments (
                customer_id VARCHAR(10) PRIMARY KEY,
                email TEXT,
                phone TEXT,
                primary_goal VARCHAR(50),
                debt_status VARCHAR(20),
                employment_status VARCHAR(20),
                timeline VARCHAR(20),
                risk_tolerance VARCHAR(20),
                assessment_date DATE,
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
            )
        """)
        print("✅ Created customer_assessments table")
        
        # Create index for better performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_assessments_customer 
            ON customer_assessments(customer_id)
        """)
        print("✅ Created index on customer_assessments")
        
        # Verify table creation
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='customer_assessments'
        """)
        
        if cursor.fetchone():
            print("✅ customer_assessments table verified")
        else:
            print("❌ customer_assessments table creation failed")
            return False
        
        # Show table structure
        cursor.execute("PRAGMA table_info(customer_assessments)")
        columns = cursor.fetchall()
        
        print(f"\n📊 customer_assessments table structure:")
        for col in columns:
            print(f"   • {col[1]} ({col[2]})")
        
        # Commit changes
        conn.commit()
        print("✅ Migration completed successfully")
        
        # Show current table count
        cursor.execute("SELECT COUNT(*) FROM customers")
        customer_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM customer_assessments")
        assessment_count = cursor.fetchone()[0]
        
        print(f"\n📈 Current data:")
        print(f"   • customers: {customer_count} records")
        print(f"   • customer_assessments: {assessment_count} records")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        conn.rollback()
        conn.close()
        
        # Restore from backup
        print(f"🔄 Restoring from backup...")
        try:
            shutil.copy2(backup_path, db_path)
            print(f"✅ Database restored from backup")
        except Exception as restore_error:
            print(f"❌ Failed to restore from backup: {str(restore_error)}")
        
        return False

def verify_migration(db_path="data/financial_data.db"):
    """Verify the migration was successful."""
    print(f"\n🔍 Verifying migration...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='customer_assessments'
        """)
        
        if not cursor.fetchone():
            print("❌ customer_assessments table not found")
            return False
        
        # Check table structure
        cursor.execute("PRAGMA table_info(customer_assessments)")
        columns = cursor.fetchall()
        
        expected_columns = [
            'customer_id', 'email', 'phone', 'primary_goal', 
            'debt_status', 'employment_status', 'timeline', 
            'risk_tolerance', 'assessment_date'
        ]
        
        actual_columns = [col[1] for col in columns]
        
        print(f"📋 Table columns: {actual_columns}")
        
        missing_columns = set(expected_columns) - set(actual_columns)
        if missing_columns:
            print(f"❌ Missing columns: {missing_columns}")
            return False
        
        # Check foreign key constraint
        cursor.execute("PRAGMA foreign_key_list(customer_assessments)")
        foreign_keys = cursor.fetchall()
        
        if foreign_keys:
            print(f"✅ Foreign key constraint verified")
        else:
            print(f"⚠️  No foreign key constraints found")
        
        # Test insert/delete (with rollback)
        cursor.execute("BEGIN TRANSACTION")
        cursor.execute("""
            INSERT INTO customer_assessments 
            (customer_id, email, primary_goal, assessment_date) 
            VALUES ('TEST001', 'test@example.com', 'test_goal', '2025-01-13')
        """)
        cursor.execute("DELETE FROM customer_assessments WHERE customer_id = 'TEST001'")
        cursor.execute("ROLLBACK")
        
        print(f"✅ Table operations test passed")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {str(e)}")
        conn.close()
        return False

if __name__ == "__main__":
    print("🚀 Starting Customer Assessments Migration")
    print("=" * 50)
    
    db_path = "data/financial_data.db"
    
    try:
        # Run migration
        success = migrate_add_assessments_table(db_path)
        
        if success:
            # Verify migration
            if verify_migration(db_path):
                print("\n🎉 Migration completed successfully!")
                print(f"📁 Database location: {os.path.abspath(db_path)}")
                print("\n📝 Next steps:")
                print("   1. Create CustomerService to manage assessments")
                print("   2. Create Customer Profile Tool for conversation updates")
                print("   3. Update main.py to handle new user flow")
            else:
                print("\n❌ Migration verification failed")
        else:
            print("\n❌ Migration failed")
            
    except Exception as e:
        print(f"\n❌ Error during migration: {str(e)}")
        raise
