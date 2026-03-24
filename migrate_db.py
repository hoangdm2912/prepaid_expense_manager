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
    MIGRATION: Chuan hoa data cu ve cau truc moi.

    CAU TRUC CU (truoc ban fix):
      - total_amount = NGUYEN GIA GOC (vi du: 83,805,633)
      - already_allocated = luy ke phan bo qua khu (co the > total_amount!)
      - Cac historical alloc (days=0): amount = tung ky QK
      - Cac future alloc (days>0): amount tinh tu NGUYEN GIA (da dung)
      - sum_future approx total_amount (vi future alloc tinh tren nguyen gia)
      - DISPLAY CU: total_amount + already_allocated = DOUBLE COUNT!

    CAU TRUC MOI (sau ban fix):
      - total_amount = PHAN CON LAI = nguyen_gia - sum_QK
      - already_allocated = sum_QK (giu nguyen)
      - Cac future alloc (days>0): amount tinh tu PHAN CON LAI
      - sum_future approx total_amount
      - Display: total_amount + already_allocated = nguyen gia

    NHAN BIET DATA CU vs DATA MOI:
      Data cu: sum_future approx total_amount VA sum_hist KHONG bang already_allocated
               (vi data cu: total_amount = nguyen gia, sum_hist = QK thuc, nhung
                already_allocated co the la gia tri thu cong nhap sai)
      Data moi: sum_future approx total_amount VA sum_hist approx already_allocated
               (vi ca hai deu nhat quan: already_allocated duoc tinh tu hist allocs)

    KEY FIX: Them dieu kien kiem tra sum_hist == already_allocated de nhan dang chinh xac.
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

            # Tolerance cho so sanh
            tol = max(1.0, total_amount * 0.01)  # 1% tolerance

            # Kiem tra tinh nhat quan cua hist allocs voi already_allocated:
            # DATA MOI DUNG: sum_hist (alloc QK trong DB) phai xap xi already_allocated
            # vi already_allocated duoc tinh chinh xac tu hist allocs khi nhap moi.
            # DATA CU SAI: already_allocated la gia tri thu cong nhap, khac sum_hist.
            tol_hist = max(1.0, already_allocated * 0.01)  # 1% tolerance cho hist
            is_hist_consistent = (sum_hist > 0 and abs(sum_hist - already_allocated) <= tol_hist)

            # Neu sum_hist nhat quan voi already_allocated: data da dung, skip
            # Du sum_future == total_amount (dieu nay luon dung voi ca 2 cau truc),
            # neu sum_hist == already_allocated thi chac chan la cau truc moi dung.
            if is_hist_consistent:
                skipped_count += 1
                print(f"  [OK ] id={exp_id}: total={total_amount:,.0f}, "
                      f"already={already_allocated:,.0f}, sum_hist={sum_hist:,.0f} "
                      f"-> hist nhat quan, da dung cau truc moi")
                continue

            # DATA CU: sum_hist KHONG nhat quan -> can fix
            # (hoac sum_hist=0 nhung already_allocated>0: nhap thu cong khong co hist alloc)
            is_old_struct = abs(sum_future - total_amount) <= tol

            if not is_old_struct:
                # Khong xac dinh duoc cau truc - bo qua an toan
                skipped_count += 1
                print(f"  [??] id={exp_id}: total={total_amount:,.0f}, "
                      f"sum_future={sum_future:,.0f}, already={already_allocated:,.0f}, "
                      f"sum_hist={sum_hist:,.0f} -> khong ro, bo qua")
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

