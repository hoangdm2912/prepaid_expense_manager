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
    MIGRATION: Chuẩn hoá data cũ về cấu trúc mới.

    CẤU TRÚC CŨ (trước bản fix):
      - total_amount = NGUYÊN GIÁ GỐC (ví dụ: 83,805,633)
      - already_allocated = lũy kế phân bổ quá khứ (có thể > total_amount!)
      - Các historical alloc (days=0): amount = từng kỳ QK
      - Các future alloc (days>0): amount tính từ NGUYÊN GIÁ (đã đúng)
      - sum_future ≈ total_amount (vì future alloc tính trên nguyên giá)
      ⚠️ Display mới: total_amount + already_allocated = DOUBLE COUNT!

    CẤU TRÚC MỚI (sau bản fix):
      - total_amount = PHẦN CÒN LẠI = nguyên_giá - sum_QK
      - already_allocated = sum_QK (giữ nguyên)
      - Các future alloc (days>0): amount tính từ PHẦN CÒN LẠI
      - sum_future ≈ total_amount ✓
      - Display: total_amount + already_allocated = nguyên giá ✓

    NHẬN BIẾT DATA CŨ:
      sum_future ≈ total_amount VÀ already_allocated > 0

    FIX:
      1. Tính sum_QK = sum(alloc.amount where days=0)
      2. remaining = total_amount - sum_QK  (có thể âm nếu QK > nguyên giá)
      3. Nếu remaining < 0: total_amount = 0 (nguyên giá nhỏ hơn phân bổ QK - đã hết)
         Nếu remaining >= 0: total_amount = remaining
      4. Scale lại future allocs: nhân theo tỷ lệ (remaining / sum_future)
         (vì sum_future hiện tại = total_amount cũ, cần co lại về remaining)
      5. already_allocated = sum_QK (cập nhật lại chính xác từ hist allocs)
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
            SELECT id, name, total_amount, already_allocated
            FROM expenses
            WHERE already_allocated > 0
        """)
        expenses = cursor.fetchall()

        fixed_count = 0
        skipped_count = 0

        for exp_id, name, total_amount, already_allocated in expenses:
            name_safe = (name or '').encode('ascii', 'replace').decode()[:40]

            # Tổng future allocs (days > 0)
            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0)
                FROM allocations
                WHERE expense_id = ? AND days_in_quarter > 0
            """, (exp_id,))
            sum_future = cursor.fetchone()[0] or 0.0

            # Tổng historical allocs (days = 0) - tổng QK thực tế
            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0)
                FROM allocations
                WHERE expense_id = ? AND days_in_quarter = 0
            """, (exp_id,))
            sum_hist = cursor.fetchone()[0] or 0.0

            # Tolerance cho so sánh
            tol = max(1.0, total_amount * 0.01)   # 1% tolerance

            # Nhận biết DATA CŨ: sum_future ≈ total_amount (nghĩa là future alloc
            # được tính từ nguyên giá, không phải remaining)
            is_old_struct = abs(sum_future - total_amount) <= tol

            # Nhận biết DATA MỚI: sum_future ≈ (total_amount - already_allocated)
            remaining_check = total_amount - already_allocated
            is_new_struct = (remaining_check >= 0 and
                             abs(sum_future - remaining_check) <= tol)

            if is_new_struct and not is_old_struct:
                # Data mới đã đúng
                skipped_count += 1
                print(f"  [OK ] id={exp_id}: total={total_amount:,.0f} (remaining), "
                      f"already={already_allocated:,.0f} → đã đúng cấu trúc mới")
                continue

            if not is_old_struct:
                # Không xác định được cấu trúc - bỏ qua an toàn
                skipped_count += 1
                print(f"  [??] id={exp_id}: total={total_amount:,.0f}, "
                      f"sum_future={sum_future:,.0f}, already={already_allocated:,.0f} → không rõ, bỏ qua")
                continue

            # --- DATA CŨ: cần fix ---
            # sum_QK từ hist allocs là nguồn sự thật cho already_allocated
            # Nếu sum_hist = 0 nhưng already_allocated > 0: dùng already_allocated
            real_already = sum_hist if sum_hist > 0 else already_allocated

            # remaining = nguyên giá - tổng QK
            remaining = total_amount - real_already

            if remaining < 0:
                # QK > nguyên giá: toàn bộ đã phân bổ hết, future = 0
                new_total = 0.0
                scale_ratio = 0.0
                print(f"  [FIX-ZERO] id={exp_id}: '{name_safe}'")
                print(f"    sum_QK={real_already:,.0f} > nguyen_gia={total_amount:,.0f} → remaining=0, xoa future allocs")
            else:
                new_total = remaining
                scale_ratio = remaining / sum_future if sum_future > 0 else 0.0
                print(f"  [FIX] id={exp_id}: '{name_safe}'")
                print(f"    nguyen_gia={total_amount:,.0f}, sum_QK={real_already:,.0f}, remaining={remaining:,.0f}")
                print(f"    scale_ratio={scale_ratio:.6f}")

            # 1. Cập nhật total_amount = remaining
            cursor.execute("""
                UPDATE expenses SET total_amount = ?, already_allocated = ?
                WHERE id = ?
            """, (new_total, real_already, exp_id))

            # 2. Scale lại hoặc xóa future allocs
            cursor.execute("""
                SELECT id, amount FROM allocations
                WHERE expense_id = ? AND days_in_quarter > 0
                ORDER BY year ASC, quarter ASC
            """, (exp_id,))
            future_allocs = cursor.fetchall()

            if remaining <= 0:
                # Xóa tất cả future allocs (đã phân bổ hết rồi)
                cursor.execute("""
                    DELETE FROM allocations
                    WHERE expense_id = ? AND days_in_quarter > 0
                """, (exp_id,))
            else:
                # Scale lại theo tỷ lệ
                scaled_total = 0
                for i, (alloc_id, alloc_amount) in enumerate(future_allocs):
                    if i < len(future_allocs) - 1:
                        new_amount = round(alloc_amount * scale_ratio)
                    else:
                        # Kỳ cuối: bù lại phần làm tròn
                        new_amount = int(remaining) - scaled_total
                    cursor.execute("""
                        UPDATE allocations SET amount = ? WHERE id = ?
                    """, (new_amount, alloc_id))
                    scaled_total += new_amount

            fixed_count += 1

        conn.commit()
        print(f"\n[FIX DONE] Da sua {fixed_count} record, bo qua {skipped_count} record da dung.")

    except Exception as e:
        print(f"[FIX ERROR] {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        conn.close()

