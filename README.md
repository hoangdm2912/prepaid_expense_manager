# Ứng Dụng Quản Lý Chi Phí Trả Trước (TK 242)

Ứng dụng web Streamlit để quản lý chi phí trả trước với tính năng phân bổ theo quý, tích hợp Google Drive, và thông báo qua Email/Zalo.

## ✨ Tính Năng Chính

### 1. Nhập Liệu & Phân Loại Tự Động
- Nhập số tài khoản (242xxx), tên khoản mục, tổng tiền, ngày bắt đầu
- **Tự động phân loại**:
  - Mã phụ **9995**: Thời gian phân bổ ≤ 12 tháng
  - Mã phụ **9996**: Thời gian phân bổ > 12 tháng

### 2. Thuật Toán Phân Bổ Chính Xác
- Phân bổ theo **quý** (mặc định)
- Tính toán **pro-rata theo số ngày thực tế** trong mỗi quý
- Xử lý chính xác các quý không đầy đủ (đầu/cuối kỳ)

### 3. Lưu Trữ & Quản Lý File
- Upload hóa đơn/hợp đồng lên **Google Drive**
- Tạo link chia sẻ tự động
- Quản lý tài liệu theo từng khoản chi phí

### 4. Hệ Thống Thông Báo
- Nhắc nhở đến hạn phân bổ qua **Email**
- Thông báo qua **Zalo API**
- Cấu hình số ngày nhắc trước

### 5. Xuất Báo Cáo Excel
- Xuất chi tiết từng khoản chi phí
- Xuất tổng hợp tất cả chi phí
- Định dạng chuyên nghiệp với màu sắc và border

### 6. Bảng Kế Hoạch Phân Bổ
- Hiển thị chi tiết phân bổ theo từng quý
- Tính toán tỷ lệ phần trăm
- Tổng hợp số ngày và số tiền

## 🚀 Cài Đặt

### Yêu Cầu Hệ Thống
- Python 3.8+
- pip

### Các Bước Cài Đặt

1. **Clone hoặc tải project**
```bash
cd prepaid_expense_manager
```

2. **Cài đặt dependencies**
```bash
pip install -r requirements.txt
```

3. **Cấu hình môi trường**

Tạo file `.env` từ template:
```bash
copy .env.example .env
```

Chỉnh sửa file `.env` với thông tin của bạn:
```env
# Database
DATABASE_URL=sqlite:///./data/expenses.db

# Google Drive
GOOGLE_DRIVE_CREDENTIALS_FILE=credentials.json
GOOGLE_DRIVE_FOLDER_ID=your_folder_id_here

# Email (SMTP)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_FROM=your_email@gmail.com

# Zalo API
ZALO_APP_ID=your_app_id
ZALO_SECRET_KEY=your_secret_key
ZALO_ACCESS_TOKEN=your_access_token
```

4. **Chạy ứng dụng**
```bash
streamlit run app.py
```

Ứng dụng sẽ mở tại: `http://localhost:8501`

## ⚙️ Cấu Hình Dịch Vụ

### Google Drive

1. Truy cập [Google Cloud Console](https://console.cloud.google.com/)
2. Tạo project mới hoặc chọn project có sẵn
3. Bật Google Drive API
4. Tạo Service Account:
   - IAM & Admin → Service Accounts → Create Service Account
   - Tải file JSON credentials
5. Tạo folder trên Google Drive
6. Chia sẻ folder với email của Service Account (với quyền Editor)
7. Lấy Folder ID từ URL: `https://drive.google.com/drive/folders/[FOLDER_ID]`
8. Đặt file credentials.json vào thư mục gốc
9. Cập nhật `.env` với đường dẫn file và Folder ID

### Email (Gmail)

1. Đăng nhập Gmail
2. Bật xác thực 2 bước
3. Tạo App Password:
   - Google Account → Security → 2-Step Verification → App passwords
   - Chọn "Mail" và "Windows Computer"
   - Copy mật khẩu 16 ký tự
4. Cập nhật `.env` với email và app password

### Zalo API

1. Đăng ký [Zalo Official Account](https://oa.zalo.me/)
2. Tạo ứng dụng tại [Zalo Developers](https://developers.zalo.me/)
3. Lấy App ID, Secret Key, Access Token
4. Cập nhật `.env` với thông tin Zalo

## 📖 Hướng Dẫn Sử Dụng

### 1. Nhập Chi Phí Mới

1. Chọn **"📝 Nhập Chi Phí"** từ menu
2. Điền thông tin:
   - Số tài khoản (bắt đầu bằng 242)
   - Tên khoản mục
   - Tổng tiền
   - Ngày bắt đầu
   - Số tháng phân bổ
3. Upload file hóa đơn/hợp đồng (tùy chọn)
4. Nhấn **"💾 Lưu Chi Phí"**
5. Xem trước kế hoạch phân bổ

### 2. Xem Danh Sách Chi Phí

1. Chọn **"📋 Danh Sách Chi Phí"**
2. Xem chi tiết từng khoản chi phí
3. Xem bảng phân bổ theo quý
4. Tải tài liệu đính kèm
5. Xuất Excel hoặc xóa chi phí

### 3. Xem Kế Hoạch Phân Bổ Tổng Hợp

1. Chọn **"📊 Kế Hoạch Phân Bổ"**
2. Lọc theo năm và quý
3. Xem tổng hợp tất cả chi phí
4. Xuất toàn bộ ra Excel

### 4. Cài Đặt

1. Chọn **"⚙️ Cài Đặt"**
2. Xem hướng dẫn cấu hình chi tiết
3. Kiểm tra trạng thái dịch vụ

## 📊 Ví Dụ Tính Toán

**Ví dụ**: Chi phí 36,000,000 VNĐ, bắt đầu 15/01/2024, phân bổ 12 tháng

- **Mã phụ**: 9995 (≤12 tháng)
- **Kỳ phân bổ**: 15/01/2024 → 14/01/2025

**Phân bổ theo quý**:

| Quý | Ngày BĐ | Ngày KT | Số ngày | Tỷ lệ | Số tiền |
|-----|---------|---------|---------|-------|---------|
| Q1/2024 | 15/01/2024 | 31/03/2024 | 77 | 21.04% | 7,574,400 ₫ |
| Q2/2024 | 01/04/2024 | 30/06/2024 | 91 | 24.86% | 8,949,600 ₫ |
| Q3/2024 | 01/07/2024 | 30/09/2024 | 92 | 25.14% | 9,050,400 ₫ |
| Q4/2024 | 01/10/2024 | 31/12/2024 | 92 | 25.14% | 9,050,400 ₫ |
| Q1/2025 | 01/01/2025 | 14/01/2025 | 14 | 3.82% | 1,375,200 ₫ |
| **TỔNG** | | | **366** | **100%** | **36,000,000 ₫** |

## 🗂️ Cấu Trúc Project

```
prepaid_expense_manager/
├── app.py                      # Ứng dụng Streamlit chính
├── requirements.txt            # Dependencies
├── .env.example               # Template cấu hình
├── README.md                  # Tài liệu này
├── config/
│   ├── __init__.py
│   └── settings.py            # Quản lý cấu hình
├── models/
│   ├── __init__.py
│   ├── database.py            # Models SQLAlchemy
│   └── expense.py             # Pydantic models
├── services/
│   ├── __init__.py
│   ├── allocation.py          # Thuật toán phân bổ
│   ├── storage.py             # Google Drive
│   ├── notification.py        # Email & Zalo
│   └── export.py              # Xuất Excel
├── utils/
│   ├── __init__.py
│   ├── validators.py          # Validation
│   └── helpers.py             # Helper functions
└── data/
    └── expenses.db            # SQLite database (tự động tạo)
```

## 🔧 Troubleshooting

### Lỗi Google Drive
- Kiểm tra file credentials.json có đúng vị trí
- Đảm bảo Service Account có quyền truy cập folder
- Kiểm tra Folder ID trong .env

### Lỗi Email
- Kiểm tra App Password (không phải mật khẩu Gmail thông thường)
- Đảm bảo đã bật 2-Step Verification
- Kiểm tra SMTP server và port

### Lỗi Database
- Xóa file `data/expenses.db` và chạy lại ứng dụng
- Kiểm tra quyền ghi vào thư mục `data/`

## 📝 Ghi Chú

- Ứng dụng sử dụng SQLite để lưu trữ dữ liệu cục bộ
- Có thể chuyển sang PostgreSQL hoặc MySQL bằng cách thay đổi `DATABASE_URL`
- Tất cả tính năng Google Drive và Zalo là tùy chọn
- Ứng dụng vẫn hoạt động bình thường nếu không cấu hình các dịch vụ này

## 📄 License

MIT License - Tự do sử dụng và chỉnh sửa

## 🤝 Hỗ Trợ

Nếu gặp vấn đề, vui lòng:
1. Kiểm tra phần Troubleshooting
2. Xem lại cấu hình trong file .env
3. Kiểm tra trạng thái dịch vụ trong sidebar

---

**Phiên bản**: 1.0.0  
**Ngày cập nhật**: 02/02/2026
