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
        
        # Add already_allocated if it doesn't exist
        if 'already_allocated' not in columns:
            print("Adding already_allocated column...")
            cursor.execute("ALTER TABLE expenses ADD COLUMN already_allocated FLOAT DEFAULT 0.0")
            print("[OK] Added already_allocated column")
        
        # Add past_quarter_year if it doesn't exist
        if 'past_quarter_year' not in columns:
            print("Adding past_quarter_year column...")
            cursor.execute("ALTER TABLE expenses ADD COLUMN past_quarter_year VARCHAR(20)")
            print("[OK] Added past_quarter_year column")
        

        # Add tags if it doesn't exist
        if 'tags' not in columns:
            print("Adding tags column...")
            cursor.execute("ALTER TABLE expenses ADD COLUMN tags VARCHAR(255)")
            print("[OK] Added tags column")
            
        # Add note if it doesn't exist
        if 'note' not in columns:
            print("Adding note column...")
            cursor.execute("ALTER TABLE expenses ADD COLUMN note TEXT")
            print("[OK] Added note column")
            
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
    fix_already_allocated_total_amount()


def fix_already_allocated_total_amount():
    """
    FIX: Các expense được import trước bản fix sẽ có:
      - total_amount = giá GỐC (ví dụ 24M)
      - already_allocated = phần quá khứ (ví dụ 5M)
      - quarterly allocations = tổng 24M (SAI, phải là 19M)

    Hàm này sẽ:
    1. Tìm các expense có already_allocated > 0
    2. Kiểm tra nếu SUM(quarterly allocs) ≈ total_amount → đây là data CŨ
    3. Sửa: total_amount = total_amount - already_allocated
    4. Nhân lại tất cả quarterly allocation amounts theo tỷ lệ (remaining / original)
    """
    import sqlite3
    import os

    db_path = "data/expenses.db"
    if not os.path.exists(db_path):
        print("[FIX] DB not found, skipping.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Lấy tất cả expense có already_allocated > 0
        cursor.execute("""
            SELECT id, total_amount, already_allocated
            FROM expenses
            WHERE already_allocated > 0
        """)
        expenses = cursor.fetchall()

        fixed_count = 0
        skipped_count = 0

        for exp_id, total_amount, already_allocated in expenses:
            # Tính tổng quarterly allocations (days_in_quarter > 0)
            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0)
                FROM allocations
                WHERE expense_id = ? AND days_in_quarter > 0
            """, (exp_id,))
            sum_quarterly = cursor.fetchone()[0] or 0

            remaining = total_amount - already_allocated

            # Kiểm tra: nếu SUM(quarterly) ≈ total_amount → data CŨ (cần fix)
            # Nếu SUM(quarterly) ≈ remaining → data MỚI (đã đúng rồi, bỏ qua)
            tol = max(1.0, total_amount * 0.001)  # Tolerence 0.1%

            diff_old = abs(sum_quarterly - total_amount)   # So sánh với giá gốc
            diff_new = abs(sum_quarterly - remaining)      # So sánh với phần còn lại

            if diff_old <= tol and diff_new > tol and remaining > 0:
                # DATA CŨ: cần fix
                ratio = remaining / total_amount  # Tỷ lệ co lại

                # 1. Cập nhật total_amount = remaining
                cursor.execute("""
                    UPDATE expenses
                    SET total_amount = ?
                    WHERE id = ?
                """, (remaining, exp_id))

                # 2. Scale lại tất cả quarterly allocation amounts
                cursor.execute("""
                    SELECT id, amount FROM allocations
                    WHERE expense_id = ? AND days_in_quarter > 0
                """, (exp_id,))
                quarterly_allocs = cursor.fetchall()

                for alloc_id, alloc_amount in quarterly_allocs:
                    new_amount = round(alloc_amount * ratio)
                    cursor.execute("""
                        UPDATE allocations SET amount = ? WHERE id = ?
                    """, (new_amount, alloc_id))

                # 3. Fix rounding: điều chỉnh kỳ cuối để tổng khớp với remaining
                if quarterly_allocs:
                    cursor.execute("""
                        SELECT id, amount FROM allocations
                        WHERE expense_id = ? AND days_in_quarter > 0
                        ORDER BY year DESC, quarter DESC LIMIT 1
                    """, (exp_id,))
                    last_alloc = cursor.fetchone()
                    if last_alloc:
                        cursor.execute("""
                            SELECT COALESCE(SUM(amount), 0) FROM allocations
                            WHERE expense_id = ? AND days_in_quarter > 0
                        """, (exp_id,))
                        new_sum = cursor.fetchone()[0] or 0
                        diff = int(remaining) - int(new_sum)
                        if diff != 0:
                            cursor.execute("""
                                UPDATE allocations SET amount = amount + ? WHERE id = ?
                            """, (diff, last_alloc[0]))

                fixed_count += 1
                print(f"  [FIX] expense_id={exp_id}: total {total_amount:.0f} → {remaining:.0f} "
                      f"(already_allocated={already_allocated:.0f})")
            else:
                skipped_count += 1
                print(f"  [OK ] expense_id={exp_id}: total={total_amount:.0f}, "
                      f"sum_quarterly={sum_quarterly:.0f} → đã đúng, bỏ qua")

        conn.commit()
        print(f"\n[FIX DONE] Đã sửa {fixed_count} record, bỏ qua {skipped_count} record đã đúng.")

    except Exception as e:
        print(f"[FIX ERROR] {e}")
        conn.rollback()
    finally:
        conn.close()
