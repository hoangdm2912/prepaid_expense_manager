# Hướng dẫn Backup & Restore với Phiên bản

## 🎯 Tính năng mới

### ✅ Đã cập nhật:
1. **Backup với timestamp**: Mỗi lần backup sẽ tạo file mới với tên chứa ngày giờ
2. **Lưu trữ 10 phiên bản**: Tự động giữ 10 bản backup gần nhất, xóa bản cũ
3. **Chọn phiên bản restore**: Hiển thị danh sách tất cả phiên bản để chọn
4. **Mật khẩu riêng cho restore**: Bảo mật cao hơn với mật khẩu `tckt1234`

---

## 📦 Cách hoạt động

### 1. Backup (Sao lưu)

**Trước đây**:
- File backup: `expenses.db` (ghi đè mỗi lần)
- Chỉ có 1 phiên bản duy nhất

**Bây giờ**:
- File backup: `expenses_YYYYMMDD_HHMMSS.db`
- Ví dụ: `expenses_20260209_103045.db` (9/2/2026 lúc 10:30:45)
- Giữ tối đa 10 phiên bản gần nhất
- Tự động xóa backup cũ hơn

**Cách sử dụng**:
1. Vào **⚙️ Cài Đặt**
2. Kéo xuống phần **🗄️ Quản lý Dữ liệu**
3. Click **☁️ Sao lưu ngay (Backup)**
4. Hệ thống sẽ tạo file backup mới và tự động dọn dẹp file cũ

---

### 2. Restore (Khôi phục)

**Giao diện mới**:
```
📦 Tìm thấy 5 phiên bản backup

Chọn phiên bản để khôi phục:
┌─────────────────────────────────────────────────┐
│ 09/02/2026 10:30:45 - expenses_20260209_103045.db │ ← Mới nhất
│ 08/02/2026 15:20:30 - expenses_20260208_152030.db │
│ 07/02/2026 09:15:00 - expenses_20260207_091500.db │
│ 06/02/2026 14:45:20 - expenses_20260206_144520.db │
│ 05/02/2026 11:00:10 - expenses_20260205_110010.db │
└─────────────────────────────────────────────────┘

Mật khẩu khôi phục: [••••••••]
⚠️ Mật khẩu khôi phục khác với mật khẩu đăng nhập
```

**Cách sử dụng**:
1. Vào **⚙️ Cài Đặt**
2. Click **🔄 Khôi phục từ Drive (Restore)**
3. Chọn phiên bản muốn khôi phục từ danh sách
4. Nhập mật khẩu khôi phục: `tckt1234`
5. Click **✅ ĐỒNG Ý KHÔI PHỤC**
6. Hệ thống tự động tải lại

---

## 🔐 Bảo mật

### Mật khẩu phân cấp:

| Chức năng | Mật khẩu | Mục đích |
|-----------|----------|----------|
| **Đăng nhập** | `tckt123` | Truy cập ứng dụng |
| **Khôi phục** | `tckt1234` | Restore database (nguy hiểm hơn) |

**Lý do**:
- Tránh nhầm lẫn restore nhầm phiên bản
- Bảo vệ dữ liệu khỏi thao tác nguy hiểm
- Chỉ admin/người có quyền mới biết mật khẩu restore

---

## ❓ Câu hỏi thường gặp

### Q1: Restore phiên bản cũ có ảnh hưởng đến tài liệu đã upload không?

**Trả lời**: **KHÔNG**

- Tài liệu (PDF, Excel, ...) được lưu độc lập trên Google Drive
- Database chỉ lưu `drive_file_id` (link đến file)
- Khi restore, chỉ thay database local, file trên Drive vẫn nguyên vẹn
- Bạn vẫn xem được tất cả tài liệu đã upload

**Ví dụ**:
1. **Ngày 1**: Upload hợp đồng.pdf → File ID: `abc123`
2. **Ngày 3**: Backup → `expenses_20260203.db` (chứa link `abc123`)
3. **Ngày 5**: Xóa nhầm chi phí, backup → `expenses_20260205.db`
4. **Ngày 6**: Restore về ngày 3 → Chi phí xuất hiện lại, file `abc123` vẫn còn!

---

### Q2: Tại sao chỉ giữ 10 phiên bản?

**Trả lời**:
- Tiết kiệm dung lượng Google Drive (mỗi file ~1-5MB)
- 10 phiên bản đủ để rollback trong hầu hết trường hợp
- Có thể thay đổi số lượng trong code nếu cần

**Tính toán**:
- Backup mỗi ngày: 10 phiên bản = 10 ngày lịch sử
- Backup mỗi tuần: 10 phiên bản = 10 tuần (2.5 tháng)
- Database ~2MB × 10 = ~20MB (rất nhỏ)

---

### Q3: Nếu muốn giữ nhiều hơn 10 phiên bản?

**Trả lời**: Sửa trong file `services/storage.py`:

```python
# Dòng 340
self._cleanup_old_backups(max_versions=10)  # Đổi 10 thành số bạn muốn
```

Ví dụ: Giữ 20 phiên bản → `max_versions=20`

---

### Q4: Có thể tắt tự động xóa backup cũ không?

**Trả lời**: Có, comment dòng cleanup:

```python
# Dòng 340
# self._cleanup_old_backups(max_versions=10)  # Thêm # ở đầu dòng
```

**Lưu ý**: Drive sẽ chứa ngày càng nhiều file backup!

---

## 🚀 Best Practices

### 1. Backup thường xuyên
- Trước khi import hàng loạt
- Sau khi nhập dữ liệu quan trọng
- Cuối mỗi ngày/tuần làm việc

### 2. Kiểm tra backup
- Thỉnh thoảng vào Drive kiểm tra file backup
- Đảm bảo có đủ phiên bản gần đây

### 3. Test restore
- Thử restore 1 lần để đảm bảo hoạt động
- Backup trước khi test restore!

### 4. Bảo mật mật khẩu
- Không chia sẻ mật khẩu restore
- Chỉ cấp cho người có trách nhiệm

---

## 🛠️ Xử lý sự cố

### Lỗi: "Không tìm thấy file backup nào"

**Nguyên nhân**: Chưa backup lần nào hoặc file bị xóa

**Giải pháp**:
1. Thực hiện backup ngay
2. Kiểm tra thư mục `Ke_Toan_242` trên Drive

---

### Lỗi: "Mật khẩu khôi phục không chính xác"

**Nguyên nhân**: Nhập sai mật khẩu

**Giải pháp**:
- Mật khẩu restore là: `tckt1234` (có số 4 ở cuối)
- Khác với mật khẩu đăng nhập `tckt123`

---

### Restore xong nhưng dữ liệu không đúng

**Nguyên nhân**: Chọn sai phiên bản

**Giải pháp**:
1. Backup ngay trạng thái hiện tại
2. Restore lại phiên bản khác
3. Kiểm tra kỹ ngày giờ của phiên bản

---

## 📊 Thống kê

**Lợi ích của hệ thống mới**:
- ✅ An toàn hơn: Có thể rollback về bất kỳ thời điểm nào (trong 10 phiên bản)
- ✅ Linh hoạt hơn: Chọn chính xác phiên bản muốn restore
- ✅ Bảo mật hơn: Mật khẩu riêng cho restore
- ✅ Tự động hóa: Tự động dọn dẹp backup cũ
- ✅ Tiết kiệm: Chỉ giữ phiên bản cần thiết

**So với hệ thống cũ**:
- Trước: 1 phiên bản, ghi đè, mất lịch sử
- Sau: 10 phiên bản, có lịch sử, rollback được

---

## 📝 Ghi chú kỹ thuật

### Định dạng tên file:
```
expenses_YYYYMMDD_HHMMSS.db

Trong đó:
- YYYY: Năm (4 chữ số)
- MM: Tháng (01-12)
- DD: Ngày (01-31)
- HH: Giờ (00-23)
- MM: Phút (00-59)
- SS: Giây (00-59)
```

### Ví dụ:
- `expenses_20260209_103045.db` = 9/2/2026 lúc 10:30:45
- `expenses_20260208_152030.db` = 8/2/2026 lúc 15:20:30

---

**Phiên bản tài liệu**: 1.0
**Ngày cập nhật**: 09/02/2026
