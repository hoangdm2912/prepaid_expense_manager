# Hướng dẫn thiết lập Keep-Alive cho Streamlit App

## 🎯 Mục đích
Tự động "đánh thức" ứng dụng Streamlit mỗi 6 tiếng để tránh chế độ ngủ, đảm bảo người dùng luôn truy cập được.

## 📋 Yêu cầu
- Repository GitHub đã có code của ứng dụng
- Ứng dụng đã deploy lên Streamlit Cloud
- Có quyền admin trên repository GitHub

## 🚀 Các bước thiết lập

### Bước 1: Lấy URL của ứng dụng Streamlit
1. Truy cập [Streamlit Cloud](https://share.streamlit.io/)
2. Tìm ứng dụng của bạn
3. Copy URL (dạng: `https://your-app-name.streamlit.app`)

### Bước 2: Thêm URL vào GitHub Secrets
1. Truy cập repository GitHub của bạn
2. Vào **Settings** > **Secrets and variables** > **Actions**
3. Click **New repository secret**
4. Điền:
   - **Name**: `STREAMLIT_APP_URL`
   - **Secret**: Paste URL ứng dụng Streamlit (ví dụ: `https://your-app-name.streamlit.app`)
5. Click **Add secret**

### Bước 3: Push code lên GitHub
File workflow đã được tạo tại `.github/workflows/keep-alive.yml`

```bash
# Thêm file mới vào git
git add .github/workflows/keep-alive.yml

# Commit
git commit -m "Add GitHub Actions workflow to keep Streamlit app alive"

# Push lên GitHub
git push origin main
```

### Bước 4: Kiểm tra workflow
1. Truy cập repository GitHub
2. Vào tab **Actions**
3. Bạn sẽ thấy workflow "Keep Streamlit App Alive"
4. Click vào workflow và chọn **Run workflow** để test thủ công

## ⏰ Lịch chạy tự động
Workflow sẽ tự động chạy:
- **Mỗi 6 tiếng**: 0:00, 6:00, 12:00, 18:00 UTC
- Tương đương: 7:00, 13:00, 19:00, 1:00 giờ Việt Nam (UTC+7)

## 🔍 Kiểm tra hoạt động

### Xem logs của workflow:
1. Vào tab **Actions** trên GitHub
2. Click vào workflow run gần nhất
3. Click vào job "keep-alive"
4. Xem output để kiểm tra:
   - ✅ "App is alive and responding!" = Thành công
   - ⚠️ Các thông báo lỗi khác = Cần kiểm tra

### Test thủ công:
1. Vào tab **Actions**
2. Chọn workflow "Keep Streamlit App Alive"
3. Click **Run workflow** > **Run workflow**
4. Đợi vài giây và kiểm tra kết quả

## 🛠️ Tùy chỉnh

### Thay đổi tần suất ping:
Sửa file `.github/workflows/keep-alive.yml`, dòng `cron`:

```yaml
# Mỗi 4 tiếng
- cron: '0 */4 * * *'

# Mỗi 3 tiếng
- cron: '0 */3 * * *'

# Mỗi 2 tiếng
- cron: '0 */2 * * *'

# Mỗi giờ
- cron: '0 * * * *'
```

**Lưu ý**: GitHub Actions có giới hạn 2000 phút/tháng cho tài khoản miễn phí. Mỗi lần chạy mất ~1 phút, nên:
- Mỗi 6 tiếng = 120 lần/tháng = ~120 phút ✅ An toàn
- Mỗi giờ = 720 lần/tháng = ~720 phút ✅ Vẫn OK
- Mỗi 30 phút = 1440 lần/tháng = ~1440 phút ⚠️ Gần giới hạn

## ❓ Xử lý sự cố

### Lỗi: "STREAMLIT_APP_URL secret chưa được thiết lập"
- Kiểm tra lại Bước 2, đảm bảo đã thêm secret với tên chính xác

### Lỗi: "App returned unexpected status code"
- Kiểm tra URL có đúng không
- Kiểm tra ứng dụng Streamlit có đang hoạt động không
- Thử truy cập URL trực tiếp trên trình duyệt

### Workflow không chạy tự động
- Đảm bảo repository là **public** hoặc có GitHub Pro/Team (private repos cần trả phí)
- Kiểm tra tab Actions có bật không (Settings > Actions > General)

## 📊 Giám sát

Để theo dõi hiệu quả:
1. Kiểm tra tab Actions hàng tuần
2. Xem Streamlit Cloud analytics (nếu có)
3. Nhờ người dùng báo cáo nếu gặp lỗi truy cập

## 🎉 Hoàn thành!

Sau khi thiết lập xong, ứng dụng của bạn sẽ được "đánh thức" tự động mỗi 6 tiếng, đảm bảo luôn sẵn sàng phục vụ người dùng!

---

**Lưu ý quan trọng**: 
- Giải pháp này chỉ hoạt động nếu repository GitHub là **public** hoặc bạn có GitHub Pro/Team
- Nếu repository là private và dùng tài khoản free, bạn cần nâng cấp hoặc chuyển sang giải pháp khác (UptimeRobot)
