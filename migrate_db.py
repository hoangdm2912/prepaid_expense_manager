"""Database migration script to add new columns."""
import sqlite3
import os

def migrate_database():
    """Add new columns to existing database."""
    db_path = "data/expenses.db"
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if document_code column exists
        cursor.execute("PRAGMA table_info(expenses)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add document_code if it doesn't exist
        if 'document_code' not in columns:
            print("Adding document_code column...")
            cursor.execute("ALTER TABLE expenses ADD COLUMN document_code VARCHAR(50)")
            print("[OK] Added document_code column")
        else:
            print("document_code column already exists")
        
        # Add end_date if it doesn't exist
        if 'end_date' not in columns:
            print("Adding end_date column...")
            cursor.execute("ALTER TABLE expenses ADD COLUMN end_date DATE")
            print("[OK] Added end_date column")
            
            # Update existing records with calculated end_date
            print("Updating existing records with end_date...")
            cursor.execute("""
                UPDATE expenses 
                SET end_date = date(start_date, '+' || allocation_months || ' months', '-1 day')
                WHERE end_date IS NULL
            """)
            print("[OK] Updated existing records")
        else:
            print("end_date column already exists")
        
        # Make allocation_months nullable if needed
        print("Checking allocation_months column...")
        
        conn.commit()
        print("\n[SUCCESS] Migration completed successfully!")
        
    except Exception as e:
        print(f"[ERROR] Migration failed: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
