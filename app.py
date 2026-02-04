"""Main Streamlit application for Prepaid Expense Management."""
import streamlit as st
import pandas as pd
from datetime import date, datetime
from sqlalchemy.orm import Session
import os

# Import models and services
from models.database import init_db, SessionLocal, Expense, Allocation, Document
from models.expense import ExpenseCreate
from services.allocation import AllocationService
from services.storage import GoogleDriveService
from services.notification import NotificationService
from services.export import ExportService
from services.import_service import ImportService
from utils.validators import validate_account_number, validate_amount, validate_file_type
from utils.helpers import format_currency, format_quarter, get_quarter
from config.settings import settings

# Page configuration
st.set_page_config(
    page_title=settings.app_title,
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize services first (needed for auto-restore)
drive_service = GoogleDriveService()
notification_service = NotificationService()
allocation_service = AllocationService()
export_service = ExportService()
import_service = ImportService()

# Auto-Restore from Drive if connected and local db missing
if drive_service.is_configured() and not os.path.exists("./data/expenses.db"):
    if settings.google_drive_folder_id:
        try:
            print("Checking for remote database backup...")
            query = f"name = 'expenses.db' and '{settings.google_drive_folder_id}' in parents and trashed = false"
            files = drive_service.list_files(query)
            if files:
                file_id = files[0]['id']
                print(f"Found remote database: {files[0]['modifiedTime']}")
                # Ensure directory exists (redundant with storage service check but safe)
                os.makedirs("./data", exist_ok=True)
                if drive_service.download_file(file_id, "./data/expenses.db"):
                    print("Database restored from Drive successfully.")
                else:
                    print("Failed to download database.")
        except Exception as e:
            print(f"Auto-restore failed: {e}")

# Initialize database (after potential restore)
init_db()

# Verify write access on startup
try:
    db_path = settings.database_url.replace("sqlite:///", "")
    db_dir = os.path.dirname(os.path.abspath(db_path))
    test_file = os.path.join(db_dir, ".write_test")
    with open(test_file, "w") as f:
        f.write("test")
    os.remove(test_file)
except Exception as e:
    st.error(f"❌ LỖI HỆ THỐNG: Môi trường hiện tại không cho phép ghi dữ liệu (Read-only filesystem).")
    st.error(f"Chi tiết: {e}")
    st.warning("Gợi ý: Hãy kiểm tra xem thư mục 'data/' có bị khóa hoặc commit vào GitHub không.")
    st.stop()


def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == "tckt123":
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.title("🔒 Đăng nhập hệ thống")
        st.text_input(
            "Vui lòng nhập mật khẩu để sử dụng phần mềm:", 
            type="password", 
            on_change=password_entered, 
            key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.title("🔒 Đăng nhập hệ thống")
        st.text_input(
            "Vui lòng nhập mật khẩu để sử dụng phần mềm:", 
            type="password", 
            on_change=password_entered, 
            key="password"
        )
        st.error("❌ Mật khẩu không chính xác")
        return False
    else:
        # Password correct.
        return True


def main():
    """Main application entry point."""
    if not check_password():
        st.stop()
    
    # Sidebar navigation
    st.sidebar.title("📊 Menu")
    page = st.sidebar.radio(
        "Chọn chức năng:",
        ["📝 Nhập Chi Phí", "📥 Import Hàng Loạt", "📋 Danh Sách Chi Phí", "📊 Kế Hoạch Phân Bổ", "⚙️ Cài Đặt"]
    )
    
    # Display service status
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔌 Trạng Thái Dịch Vụ")
    
    if drive_service.is_configured():
        st.sidebar.success("✅ Google Drive")
    else:
        st.sidebar.warning("⚠️ Google Drive chưa cấu hình")
    
    configured_channels = notification_service.get_configured_channels()
    if 'email' in configured_channels:
        st.sidebar.success("✅ Email")
    else:
        st.sidebar.warning("⚠️ Email chưa cấu hình")
    
    if 'zalo' in configured_channels:
        st.sidebar.success("✅ Zalo")
    else:
        st.sidebar.warning("⚠️ Zalo chưa cấu hình")
    
    # Sidebar Info
    st.sidebar.markdown("---")
    st.sidebar.info("Phần mềm Quản lý Chi phí Trả trước")
    
    # Navigation
    if page == "📝 Nhập Chi Phí":
        page_create_expense()
    elif page == "📥 Import Hàng Loạt":
        page_bulk_import()
    elif page == "📋 Danh Sách Chi Phí":
        page_list_expenses()
    elif page == "📊 Kế Hoạch Phân Bổ":
        page_allocation_schedule()
    elif page == "⚙️ Cài Đặt":
        page_settings()


def page_create_expense():
    """Page for creating new expense."""
    st.title("📝 Nhập Chi Phí Trả Trước Mới")
    
    db = SessionLocal()
    
    with st.form("expense_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            account_number = st.text_input("Tài khoản chi phí (*)", value="242")
            name = st.text_input("Tên khoản chi phí (*)")
            document_code = st.text_input("Mã chứng từ / Hóa đơn")
            total_amount = st.number_input("Tổng số tiền (*)", min_value=0.0, step=1000.0, format="%f")
        
        with col2:
            start_date = st.date_input("Ngày bắt đầu (*)", value=date.today())
            end_date = st.date_input("Ngày kết thúc phân bổ (*)", value=date.today())
            
            # Auto-calculate sub-code
            months = allocation_service.calculate_months_between_dates(start_date, end_date)
            suggested_sub_code = allocation_service.determine_sub_code(months)
            
            sub_code = st.text_input("Mã chi phí phụ (*)", value=suggested_sub_code, disabled=True, help="Tự động chọn dựa trên thời gian phân bổ")
            st.caption(f"Thời gian phân bổ: {months} tháng -> {suggested_sub_code} ({'Ngắn hạn' if suggested_sub_code == '9995' else 'Dài hạn'})")
            
            uploaded_files = st.file_uploader(
                "Tài liệu đính kèm", 
                accept_multiple_files=True,
                type=['pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx', 'xls', 'xlsx']
            )
        
        submitted = st.form_submit_button("Lưu Chi Phí")
        
        if submitted:
            # Validation
            if not account_number or not name or total_amount <= 0:
                st.error("Vui lòng điền đầy đủ các trường bắt buộc (*)")
                return
            
            is_valid_acc, acc_error = validate_account_number(account_number)
            if not is_valid_acc:
                st.error(f"❌ {acc_error}")
                return
            
            if end_date <= start_date:
                st.error("Ngày kết thúc phải sau ngày bắt đầu")
                return

            try:
                # Calculate allocation months for compatibility
                months = allocation_service.calculate_months_between_dates(start_date, end_date)
                
                # Check for existing
                existing = db.query(Expense).filter(
                    Expense.account_number == account_number, 
                    # Expense.sub_code == sub_code  # Allow same account number with different sub codes? usually unique combination
                ).first()
                
                # Create Expense Record
                new_expense = Expense(
                    account_number=account_number,
                    name=name,
                    document_code=document_code,
                    total_amount=total_amount,
                    start_date=start_date,
                    end_date=end_date,
                    sub_code=sub_code,
                    allocation_months=months
                )
                
                # Calculate allocations
                allocations_data = allocation_service.calculate_quarterly_allocations(
                    total_amount, start_date, end_date
                )
                
                # Create Allocation Records
                for alloc_data in allocations_data:
                    allocation = Allocation(
                        quarter=alloc_data['quarter'],
                        year=alloc_data['year'],
                        amount=alloc_data['amount'],
                        days_in_quarter=alloc_data['days_in_quarter'],
                        start_date=alloc_data['start_date'],
                        end_date=alloc_data['end_date']
                    )
                    new_expense.allocations.append(allocation)
                
                # Upload Documents
                if uploaded_files and drive_service.is_configured():
                    progress_text = "Đang tải lên tài liệu..."
                    my_bar = st.progress(0, text=progress_text)
                    
                    for idx, uploaded_file in enumerate(uploaded_files):
                        file_content = uploaded_file.getvalue()
                        success, file_id, link = drive_service.upload_file(
                            file_content=file_content,
                            filename=uploaded_file.name,
                            mime_type=uploaded_file.type
                        )
                        
                        if success:
                            doc = Document(
                                filename=uploaded_file.name,
                                drive_url=link,
                                drive_file_id=file_id
                            )
                            new_expense.documents.append(doc)
                        else:
                            st.warning(f"Không thể tải lên {uploaded_file.name}: {link}")
                        
                        my_bar.progress((idx + 1) / len(uploaded_files), text=progress_text)
                    
                    my_bar.empty()
                
                db.add(new_expense)
                db.commit()
                db.refresh(new_expense)
                
                st.success(f"✅ Đã thêm chi phí '{name}' thành công!")
                
                # Show allocation plan preview
                st.info(f"Đã lập kế hoạch phân bổ trong {months} tháng ({len(allocations_data)} quý)")
                
            except Exception as e:
                db.rollback()
                st.error(f"Lỗi khi lưu dữ liệu: {str(e)}")
            finally:
                db.close()


def page_bulk_import():
    """Page for bulk importing expenses from Excel."""
    st.title("📥 Import Hàng Loạt")
    
    st.markdown("""
    Sử dụng chức năng này để nhập nhiều khoản chi phí cùng lúc từ file Excel.
    """)
    
    # Step 1: Download Template
    st.subheader("1. Tải Template Mẫu")
    
    buffer = import_service.export_template()
    st.download_button(
        label="⬇️ Tải file Excel mẫu",
        data=buffer,
        file_name="template_nhap_lieu_242.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

    # Step 2: Upload File
    st.subheader("2. Tải lên dữ liệu")
    uploaded_file = st.file_uploader("Chọn file Excel đã nhập liệu", type=['xlsx'])
    
    if uploaded_file:
        try:
            # Read and validate
            df = pd.read_excel(uploaded_file)
            st.dataframe(df.head(), use_container_width=True)
            
            is_valid, validation_errors = import_service.validate_import_data(df)
            
            if not is_valid:
                st.error("⚠️ File dữ liệu có lỗi:")
                for error in validation_errors:
                    st.warning(error)
            else:
                st.success("✅ Dữ liệu hợp lệ! Sẵn sàng import.")
                
                if st.button("🚀 Bắt đầu Import", type="primary"):
                    expenses_data = import_service.parse_import_data(df)
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    db = SessionLocal()
                    success_count = 0
                    error_count = 0
                    
                    for i, expense_data in enumerate(expenses_data):
                        status_text.text(f"Đang xử lý dòng {i+1}/{len(expenses_data)}: {expense_data['name']}")
                        
                        try:
                            # Create DB objects
                            new_expense = Expense(
                                account_number=expense_data['account_number'],
                                name=expense_data['name'],
                                document_code=expense_data['document_code'],
                                total_amount=expense_data['total_amount'],
                                start_date=expense_data['start_date'],
                                end_date=expense_data['end_date'],
                                sub_code=expense_data['sub_code'],
                                allocation_months=expense_data['allocation_months']
                            )
                            
                            # Calculate allocations
                            allocations_data = allocation_service.calculate_quarterly_allocations(
                                expense_data['total_amount'],
                                expense_data['start_date'],
                                expense_data['end_date']
                            )
                            
                            for alloc in allocations_data:
                                allocation = Allocation(
                                    quarter=alloc['quarter'],
                                    year=alloc['year'],
                                    amount=alloc['amount'],
                                    days_in_quarter=alloc['days_in_quarter'],
                                    start_date=alloc['start_date'],
                                    end_date=alloc['end_date']
                                )
                                new_expense.allocations.append(allocation)
                            
                            db.add(new_expense)
                            db.commit()
                            success_count += 1
                            
                        except Exception as e:
                            db.rollback()
                            st.error(f"Lỗi dòng {i+1}: {str(e)}")
                            error_count += 1
                        
                        progress_bar.progress((i + 1) / len(expenses_data))
                    
                    db.close()
                    status_text.empty()
                    st.success(f"🎉 Hoàn tất! Thành công: {success_count}, Lỗi: {error_count}")
                    
        except Exception as e:
            st.error(f"Lỗi đọc file: {str(e)}")


def page_list_expenses():
    """Page for listing all expenses."""
    st.title("📋 Danh Sách Chi Phí")
    
    db = SessionLocal()
    expenses = db.query(Expense).order_by(Expense.created_at.desc()).all()
    
    if not expenses:
        st.info("📭 Chưa có chi phí nào được nhập.")
        db.close()
        return
    
    # Display expenses
    for expense in expenses:
        with st.expander(f"**{expense.name}** - {format_currency(expense.total_amount)}", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Số tài khoản", expense.account_number)
                st.metric("Mã phụ", expense.sub_code)
                if expense.document_code:
                    st.metric("Mã chứng từ", expense.document_code)
            
            with col2:
                st.metric("Tổng tiền", format_currency(expense.total_amount))
                st.metric("Số tháng", f"{expense.allocation_months} tháng")
            
            with col3:
                st.metric("Ngày bắt đầu", expense.start_date.strftime("%d/%m/%Y"))
                st.metric("Ngày kết thúc", expense.end_date.strftime("%d/%m/%Y"))
                st.metric("Số quý", len(expense.allocations))
            
            # Show allocations
            if expense.allocations:
                st.markdown("#### 📊 Kế hoạch phân bổ theo quý")
                alloc_data = []
                for alloc in expense.allocations:
                    alloc_data.append({
                        'quarter': alloc.quarter,
                        'year': alloc.year,
                        'amount': alloc.amount,
                        'days_in_quarter': alloc.days_in_quarter,
                        'start_date': alloc.start_date,
                        'end_date': alloc.end_date,
                        'total_days': sum(a.days_in_quarter for a in expense.allocations)
                    })
                display_allocation_table(alloc_data, expense.total_amount)
            
            # Show documents
            if expense.documents:
                st.markdown("#### 📎 Tài liệu đính kèm")
                for doc in expense.documents:
                    if doc.drive_url:
                        st.markdown(f"- [{doc.filename}]({doc.drive_url})")
                    else:
                        st.markdown(f"- {doc.filename}")
            
            # Export button
            col_export, col_delete = st.columns([3, 1])
            with col_export:
                if st.button(f"📥 Xuất Excel", key=f"export_{expense.id}"):
                    export_expense_to_excel(expense, alloc_data)
            
            with col_delete:
                if st.button(f"🗑️ Xóa", key=f"delete_{expense.id}", type="secondary"):
                    db.delete(expense)
                    db.commit()
                    st.success("✅ Đã xóa chi phí")
                    st.rerun()
    
    db.close()


def page_allocation_schedule():
    """Page for viewing allocation schedule."""
    st.title("📊 Kế Hoạch Phân Bổ Tổng Hợp")
    
    db = SessionLocal()
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        year_filter = st.selectbox(
            "Chọn năm",
            options=["Tất cả"] + list(range(date.today().year - 2, date.today().year + 5))
        )
    
    with col2:
        quarter_filter = st.selectbox(
            "Chọn quý",
            options=["Tất cả", "Q1", "Q2", "Q3", "Q4"]
        )
    
    # Get all allocations
    query = db.query(Allocation).join(Expense)
    
    if year_filter != "Tất cả":
        query = query.filter(Allocation.year == year_filter)
    
    if quarter_filter != "Tất cả":
        quarter_num = int(quarter_filter[1])
        query = query.filter(Allocation.quarter == quarter_num)
    
    allocations = query.all()
    
    if not allocations:
        st.info("📭 Không có dữ liệu phân bổ.")
        db.close()
        return
    
    # Create summary table
    summary_data = []
    for alloc in allocations:
        summary_data.append({
            'Khoản mục': alloc.expense.name,
            'Số TK': alloc.expense.account_number,
            'Mã phụ': alloc.expense.sub_code,
            'Quý': format_quarter(alloc.quarter, alloc.year),
            'Năm': alloc.year,
            'Ngày BĐ': alloc.start_date.strftime("%d/%m/%Y"),
            'Ngày KT': alloc.end_date.strftime("%d/%m/%Y"),
            'Số ngày': alloc.days_in_quarter,
            'Số tiền': alloc.amount
        })
    
    df = pd.DataFrame(summary_data)
    
    # Display summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Tổng số khoản mục", len(set(a.expense_id for a in allocations)))
    with col2:
        st.metric("Tổng số quý", len(allocations))
    with col3:
        total_amount = sum(a.amount for a in allocations)
        st.metric("Tổng tiền phân bổ", format_currency(total_amount))
    
    # Display table
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )
    
    # Export all button
    if st.button("📥 Xuất toàn bộ ra Excel", use_container_width=True):
        export_all_to_excel(db)
    
    db.close()


def page_settings():
    """Page for application settings."""
    st.title("⚙️ Cài Đặt")
    
    st.markdown("### 🔌 Kết nối Google Drive")
    
    if drive_service.is_configured():
        st.success("✅ Google Drive đã được kết nối!")
        if settings.google_drive_folder_id:
            st.info(f"📁 Thư mục lưu trữ: **{settings.google_drive_folder_name}** (ID: {settings.google_drive_folder_id})")
        else:
            st.warning("⚠️ Đã kết nối nhưng chưa xác định được thư mục lưu trữ.")
    else:
        st.warning("⚠️ Google Drive chưa được kết nối.")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Kết nối Tài khoản mới:**")
        if st.button("🔗 Lấy Link Xác Thực (Manual Flow)"):
            auth_url, error = drive_service.get_auth_url()
            if auth_url:
                st.session_state['auth_url'] = auth_url
                st.session_state['show_auth_input'] = True
            else:
                st.error(f"❌ Lỗi: {error}")
        
        if st.session_state.get('show_auth_input'):
            st.info(f"1. [Nhấn vào đây để cấp quyền]({st.session_state['auth_url']})\n2. Copy mã xác thực và dán vào ô bên dưới.")
            
            with st.form("auth_form"):
                auth_code = st.text_input("Mã xác thực (Auth Code):")
                submit_code = st.form_submit_button("✅ Xác thực")
                
                if submit_code and auth_code:
                    with st.spinner("Đang xác thực..."):
                        success, message = drive_service.authenticate_with_code(auth_code)
                        if success:
                            st.success(message)
                            st.session_state['show_auth_input'] = False
                            st.rerun()
                        else:
                            st.error(message)

                st.error("❌ Không thể kết nối. Vui lòng cấp quyền lại.")
    
    # --- Persistence Section ---
    st.markdown("---")
    st.markdown("### 🔒 Duy trì kết nối lâu dài (Persistence)")
    
    with st.expander("Hướng dẫn duy trì kết nối (Dành cho Streamlit Cloud)"):
        st.markdown("""
        Để tránh việc phải đăng nhập lại mỗi 7 ngày hoặc khi ứng dụng khởi động lại, bạn hãy thực hiện:
        
        1. **Chế độ Production**: Đảm bảo dự án Google Cloud của bạn đã chuyển sang trạng thái **"In Production"** (OAuth consent screen).
        2. **Lưu Token vào Secrets**: Copy nội dung Token bên dưới và dán vào phần **Secrets** của Streamlit.
        """)
        
        token_path = settings.google_drive_token_file
        token_content = None
        
        if os.path.exists(token_path):
            with open(token_path, 'r') as f:
                token_content = f.read()
        elif "GOOGLE_TOKEN_JSON" in st.secrets:
            token_content = st.secrets["GOOGLE_TOKEN_JSON"]
            
        if token_content:
            st.success("✅ Đã tìm thấy Token!")
            st.markdown("Copy nội dung này dán vào biến `GOOGLE_TOKEN_JSON` trong Secrets:")
            st.code(token_content, language="json")
        else:
            st.warning("⚠️ Chưa có Token. Hãy thực hiện kết nối ở trên trước.")

    # --- Database Management Section ---
    st.markdown("---")
    st.markdown("### 🗄️ Quản lý Dữ liệu (Backup & Restore)")
    st.info("Sao lưu file Database (`expenses.db`) lên Google Drive để tránh mất dữ liệu khi ứng dụng khởi động lại.")

    col_bk, col_rs = st.columns(2)
    
    with col_bk:
        if st.button("☁️ Sao lưu ngay (Backup)", type="primary", use_container_width=True):
            if not drive_service.is_configured():
                st.error("Vui lòng kết nối Google Drive trước.")
            else:
                db_path = settings.database_url.replace("sqlite:///", "")
                if os.path.exists(db_path):
                    with st.spinner("Đang sao lưu database lên Drive..."):
                        success, msg = drive_service.upload_database(db_path)
                        if success:
                            st.success(f"{msg}")
                        else:
                            st.error(f"Lỗi: {msg}")
                else:
                    st.error("Không tìm thấy file database local.")

    with col_rs:
        if st.button("🔄 Khôi phục từ Drive (Restore)", type="secondary", use_container_width=True):
             if not drive_service.is_configured():
                st.error("Vui lòng kết nối Google Drive trước.")
             else:
                # This warning is just visual, the actual restore logic is below it.
                # Streamlit buttons trigger a rerun, so the warning will show, then the spinner.
                st.warning("⚠️ Cảnh báo: Dữ liệu hiện tại trên App sẽ bị ghi đè bởi bản backup từ Drive. Bạn có chắc chắn không?")
                    
                with st.spinner("Đang tìm và tải bản backup mới nhất..."):
                    # Find backup file
                    if settings.google_drive_folder_id:
                        query = f"name = 'expenses.db' and '{settings.google_drive_folder_id}' in parents and trashed = false"
                        files = drive_service.list_files(query)
                        if files:
                            file_id = files[0]['id']
                            updated_time = files[0]['modifiedTime']
                            db_path = settings.database_url.replace("sqlite:///", "")
                            
                            if drive_service.download_file(file_id, db_path):
                                st.success(f"✅ Đã khôi phục thành công bản backup ngày {updated_time}")
                                st.info("Vui lòng tải lại trang để thấy dữ liệu mới.")
                            else:
                                st.error("Không thể tải file về.")
                        else:
                            st.error("Không tìm thấy file `expenses.db` nào trên Drive (trong thư mục Ke_Toan_242).")
                    else:
                        st.error("Chưa xác định được thư mục lưu trữ.")

    st.markdown("---")
    st.markdown("""
    ### 📝 Hướng dẫn cấu hình
    
    Để sử dụng đầy đủ các tính năng, vui lòng cấu hình các dịch vụ sau:
    
    #### 1. Google Drive (Dùng Streamlit Secrets - Khuyên dùng)
    - Truy cập Google Cloud Console, tạo OAuth 2.0 Client ID (Desktop app).
    - Tải file JSON cấu hình.
    - Copy nội dung file JSON này dán vào biến **`GOOGLE_CLIENT_SECRETS_JSON`** trong phần **Secrets** của Streamlit Cloud (hoặc `.streamlit/secrets.toml` nếu chạy local).
    - Nhấn nút **"Kết nối Tài khoản Cá nhân"** ở trên.
    - Ứng dụng sẽ tự tạo thư mục `Ke_Toan_242` trên Drive của bạn.
    
    #### 2. Email (SMTP)
    - Sử dụng Gmail hoặc SMTP server khác.
    - Với Gmail: Bật "App Password" trong cài đặt bảo mật.
    - Cấu hình SMTP server, port, username, password.
    
    ### 📄 Cấu hình Secrets (Ví dụ)
    
    Dán nội dung sau vào phần Secrets của Streamlit:
    """)
    
    st.code("""
GOOGLE_CLIENT_SECRETS_JSON = '''
{
  "installed": {
    "client_id": "your_id",
    "project_id": "your_project",
    ...
  }
}
'''

DATABASE_URL="sqlite:///./data/expenses.db"
SMTP_SERVER="smtp.gmail.com"
SMTP_PORT=587
SMTP_USERNAME="your_email@gmail.com"
SMTP_PASSWORD="your_app_password"
EMAIL_FROM="your_email@gmail.com"
    """, language="toml")
    
    st.markdown("---")
    st.markdown("### 📊 Thông tin ứng dụng")
    st.info(f"**Phiên bản:** 1.0.0\n\n**Database:** {settings.database_url}")


def display_allocation_table(allocations: list, total_amount: float):
    """Display allocation table with formatting and cumulative balance."""
    df_data = []
    cumulative_allocated = 0
    
    for alloc in allocations:
        percentage = (alloc['days_in_quarter'] / alloc['total_days']) * 100
        cumulative_allocated += alloc['amount']
        remaining_balance = total_amount - cumulative_allocated
        
        df_data.append({
            'Quý': format_quarter(alloc['quarter'], alloc['year']),
            'Ngày BĐ': alloc['start_date'].strftime("%d/%m/%Y"),
            'Ngày KT': alloc['end_date'].strftime("%d/%m/%Y"),
            'Số ngày': alloc['days_in_quarter'],
            'Tỷ lệ (%)': f"{percentage:.2f}%",
            'Số tiền': format_currency(alloc['amount']),
            'Lũy kế phân bổ': format_currency(cumulative_allocated),
            'Còn lại': format_currency(remaining_balance)
        })
    
    # Add total row
    df_data.append({
        'Quý': '**TỔNG CỘNG**',
        'Ngày BĐ': '',
        'Ngày KT': '',
        'Số ngày': sum(a['days_in_quarter'] for a in allocations),
        'Tỷ lệ (%)': '100.00%',
        'Số tiền': format_currency(sum(a['amount'] for a in allocations)),
        'Lũy kế phân bổ': format_currency(total_amount),
        'Còn lại': format_currency(0)
    })
    
    df = pd.DataFrame(df_data)
    st.dataframe(df, use_container_width=True, hide_index=True)


def export_expense_to_excel(expense: Expense, allocations: list):
    """Export single expense to Excel."""
    expense_data = {
        'account_number': expense.account_number,
        'name': expense.name,
        'document_code': expense.document_code,
        'total_amount': expense.total_amount,
        'start_date': expense.start_date,
        'end_date': expense.end_date,
        'sub_code': expense.sub_code,
        'allocation_months': expense.allocation_months
    }
    
    output_path = f"data/export_{expense.account_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    os.makedirs("data", exist_ok=True)
    
    if export_service.export_allocation_report(expense_data, allocations, output_path):
        with open(output_path, 'rb') as f:
            st.download_button(
                label="📥 Tải xuống file Excel",
                data=f,
                file_name=os.path.basename(output_path),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )


def export_all_to_excel(db: Session):
    """Export all expenses to Excel."""
    expenses = db.query(Expense).all()
    
    expenses_data = []
    for expense in expenses:
        alloc_data = []
        for alloc in expense.allocations:
            alloc_data.append({
                'quarter': alloc.quarter,
                'year': alloc.year,
                'amount': alloc.amount,
                'days_in_quarter': alloc.days_in_quarter,
                'start_date': alloc.start_date,
                'end_date': alloc.end_date
            })
        
        expenses_data.append({
            'account_number': expense.account_number,
            'name': expense.name,
            'sub_code': expense.sub_code,
            'allocations': alloc_data
        })
    
    output_path = f"data/export_all_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    os.makedirs("data", exist_ok=True)
    
    if export_service.export_multiple_expenses(expenses_data, output_path):
        with open(output_path, 'rb') as f:
            st.download_button(
                label="📥 Tải xuống file Excel",
                data=f,
                file_name=os.path.basename(output_path),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )


if __name__ == "__main__":
    main()
