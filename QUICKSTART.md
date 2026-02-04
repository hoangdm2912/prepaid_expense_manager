# Quick Start Guide

## Chạy Ứng Dụng Nhanh

### 1. Cài đặt dependencies
```bash
pip install streamlit sqlalchemy pandas openpyxl python-dotenv pydantic pydantic-settings requests schedule google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

### 2. Chạy ứng dụng
```bash
cd C:\Users\hoang\.gemini\antigravity\scratch\prepaid_expense_manager
streamlit run app.py
```

### 3. Truy cập
Mở trình duyệt tại: `http://localhost:8501`

## Sử Dụng Cơ Bản (Không Cần Cấu Hình)

Ứng dụng có thể sử dụng ngay **không cần cấu hình** Google Drive, Email, hay Zalo:

1. **Nhập chi phí**: Chọn "📝 Nhập Chi Phí"
   - Nhập số tài khoản (ví dụ: 242001)
   - Nhập tên khoản mục
   - Nhập tổng tiền
   - Chọn ngày bắt đầu
   - Chọn số tháng phân bổ
   - Nhấn "Lưu Chi Phí"

2. **Xem kế hoạch phân bổ**: Chọn "📋 Danh Sách Chi Phí"
   - Xem chi tiết từng khoản chi phí
   - Xem bảng phân bổ theo quý
   - Xuất Excel

3. **Xem tổng hợp**: Chọn "📊 Kế Hoạch Phân Bổ"
   - Lọc theo năm/quý
   - Xem tổng hợp tất cả chi phí
   - Xuất toàn bộ ra Excel

## Cấu Hình Nâng Cao (Tùy Chọn)

Nếu muốn sử dụng Google Drive, Email, Zalo:

1. Copy file cấu hình mẫu:
```bash
copy .env.example .env
```

2. Chỉnh sửa file `.env` với thông tin của bạn

3. Xem hướng dẫn chi tiết trong:
   - README.md
   - Trang "⚙️ Cài Đặt" trong ứng dụng

## Lưu Ý

- Database SQLite tự động tạo tại `data/expenses.db`
- File Excel xuất ra sẽ lưu trong thư mục `data/`
- Tất cả tính năng cơ bản hoạt động mà không cần cấu hình thêm
