# Hướng dẫn giải quyết vấn đề App ngủ và mất dữ liệu

## 🔍 Vấn đề

1. **App vẫn ngủ sau 2 ngày** mặc dù đã setup GitHub Actions keep-alive
2. **Dữ liệu bị mất** khi app thức dậy từ chế độ ngủ

---

## ✅ Giải pháp đã implement

### 1. Auto-Restore khi app khởi động

**Đã cập nhật** (commit mới nhất):
- Tự động tìm backup mới nhất trên Drive
- Restore database khi app khởi động và phát hiện không có dữ liệu local
- Logging rõ ràng để debug

**Cách hoạt động**:
```
App khởi động → Kiểm tra ./data/expenses.db
                ↓
        Không có file local?
                ↓
        Tìm backup mới nhất trên Drive
                ↓
        Download về ./data/expenses.db
                ↓
        App sẵn sàng với dữ liệu đầy đủ ✅
```

---

## 🔧 Kiểm tra và sửa lỗi Keep-Alive

### Bước 1: Kiểm tra GitHub Actions có chạy không

1. Truy cập: https://github.com/hoangdm2912/prepaid_expense_manager/actions
2. Tìm workflow **"Keep Streamlit App Alive"**
3. Kiểm tra:
   - ✅ Có workflow runs gần đây không?
   - ✅ Status là "Success" hay "Failed"?
   - ✅ Thời gian chạy cuối cùng?

### Bước 2: Kiểm tra Secret đã được thiết lập chưa

1. Truy cập: https://github.com/hoangdm2912/prepaid_expense_manager/settings/secrets/actions
2. Kiểm tra có secret **`STREAMLIT_APP_URL`** không?
3. Nếu chưa có:
   - Click **"New repository secret"**
   - Name: `STREAMLIT_APP_URL`
   - Secret: `https://quanly242.streamlit.app`
   - Click **"Add secret"**

### Bước 3: Kiểm tra Repository visibility

**QUAN TRỌNG**: GitHub Actions chỉ chạy miễn phí trên **public repositories**!

1. Truy cập: https://github.com/hoangdm2912/prepaid_expense_manager/settings
2. Kéo xuống phần **"Danger Zone"**
3. Kiểm tra repository là **Public** hay **Private**?

**Nếu là Private**:
- ❌ GitHub Actions bị giới hạn 2000 phút/tháng (free tier)
- ❌ Workflow có thể không chạy nếu hết quota

**Giải pháp**:
- **Option A**: Chuyển repository sang Public
  - Settings → Danger Zone → Change visibility → Make public
- **Option B**: Nâng cấp GitHub Pro ($4/tháng, 3000 phút Actions)
- **Option C**: Dùng UptimeRobot thay vì GitHub Actions (xem bên dưới)

---

## 🆘 Giải pháp thay thế: UptimeRobot (Miễn phí)

Nếu GitHub Actions không hoạt động, dùng UptimeRobot:

### Ưu điểm:
- ✅ Hoàn toàn miễn phí
- ✅ Không cần GitHub Pro
- ✅ Ping mỗi 5 phút (tốt hơn 6 tiếng)
- ✅ Gửi email thông báo nếu app down

### Cách thiết lập:

1. **Đăng ký tài khoản**:
   - Truy cập: https://uptimerobot.com
   - Click **"Sign Up Free"**
   - Xác nhận email

2. **Tạo Monitor**:
   - Click **"+ Add New Monitor"**
   - Monitor Type: **HTTP(s)**
   - Friendly Name: `Streamlit App - QuanLy242`
   - URL: `https://quanly242.streamlit.app`
   - Monitoring Interval: **5 minutes** (miễn phí)
   - Click **"Create Monitor"**

3. **Xong!** UptimeRobot sẽ tự động ping app mỗi 5 phút

### So sánh:

| Phương án | Tần suất | Miễn phí? | Yêu cầu |
|-----------|----------|-----------|---------|
| GitHub Actions | Mỗi 6 tiếng | ✅ (Public repo) | Repository public |
| UptimeRobot | Mỗi 5 phút | ✅ | Đăng ký tài khoản |
| Streamlit Pro | Không ngủ | ❌ $20/tháng | Trả phí |

**Khuyến nghị**: Dùng **UptimeRobot** vì:
- Miễn phí hoàn toàn
- Ping thường xuyên hơn (5 phút vs 6 tiếng)
- Không phụ thuộc GitHub repository visibility

---

## 🧪 Test Auto-Restore

Để test xem auto-restore có hoạt động không:

### Cách 1: Test local

```bash
# 1. Backup database hiện tại
cp ./data/expenses.db ./data/expenses_backup.db

# 2. Xóa database local
rm ./data/expenses.db

# 3. Chạy app
streamlit run app.py

# 4. Kiểm tra logs
# Bạn sẽ thấy:
# 🔍 Checking for remote database backup...
# 📦 Found latest backup: expenses_20260211_100530.db
# ✅ Database restored successfully from: expenses_20260211_100530.db
```

### Cách 2: Test trên Streamlit Cloud

1. Vào Streamlit Cloud dashboard
2. Click **"Reboot app"** (restart app)
3. Đợi app khởi động lại
4. Kiểm tra logs (Settings → Logs)
5. Xem có thông báo restore thành công không

---

## 📋 Checklist khắc phục

- [ ] **Backup thường xuyên**: Vào Settings → Backup mỗi ngày
- [ ] **Kiểm tra GitHub Actions**: Xem workflow có chạy không
- [ ] **Thiết lập UptimeRobot**: Ping mỗi 5 phút (khuyến nghị)
- [ ] **Test auto-restore**: Reboot app và kiểm tra
- [ ] **Kiểm tra logs**: Xem có lỗi gì không

---

## 🎯 Kết quả mong đợi

Sau khi thiết lập đúng:

1. **App không ngủ nữa** (nhờ UptimeRobot hoặc GitHub Actions)
2. **Dữ liệu tự động restore** khi app khởi động
3. **Không cần restore thủ công** nữa

---

## ❓ FAQ

### Q: Tại sao app vẫn ngủ dù đã setup GitHub Actions?

**A**: Có thể do:
- Repository là private → GitHub Actions bị giới hạn
- Secret `STREAMLIT_APP_URL` chưa được thiết lập
- Workflow bị lỗi → Kiểm tra logs

**Giải pháp**: Dùng UptimeRobot thay thế

---

### Q: Dữ liệu có bị mất vĩnh viễn không?

**A**: **KHÔNG!** Miễn là bạn đã backup lên Drive:
- Dữ liệu vẫn an toàn trên Google Drive
- Auto-restore sẽ tự động khôi phục khi app khởi động
- Hoặc restore thủ công qua Settings

---

### Q: Nên dùng GitHub Actions hay UptimeRobot?

**A**: **UptimeRobot** tốt hơn vì:
- Miễn phí hoàn toàn
- Ping thường xuyên hơn (5 phút)
- Không phụ thuộc repository visibility
- Có thông báo email nếu app down

---

### Q: Có cần cả 2 không?

**A**: Có thể dùng cả 2 để đảm bảo:
- UptimeRobot: Ping chính (mỗi 5 phút)
- GitHub Actions: Backup (mỗi 6 tiếng)

Nhưng chỉ UptimeRobot cũng đủ rồi!

---

## 📞 Hỗ trợ

Nếu vẫn gặp vấn đề:
1. Kiểm tra logs trên Streamlit Cloud
2. Kiểm tra GitHub Actions logs
3. Chụp màn hình lỗi để debug

---

**Cập nhật**: 11/02/2026
**Phiên bản**: 2.0
