# Hướng dẫn Chống Ngủ (Keep-Alive) cho Streamlit App

## ⚠️ Hiểu đúng về Streamlit Sleep

**Streamlit Cloud Free Tier** sẽ đặt app vào chế độ ngủ sau **~5 phút không có tương tác từ browser**.

> **Quan trọng:** HTTP ping thông thường (curl, GitHub Actions) **KHÔNG** đủ để giữ app thức.  
> Streamlit Cloud chỉ wake up khi có người dùng thực sự mở trình duyệt vào app.

## 🥇 Giải pháp 1: UptimeRobot (Khuyến nghị - Miễn phí)

UptimeRobot giả lập browser ping, hiệu quả hơn curl thuần.

### Các bước thiết lập:

1. Tạo tài khoản miễn phí tại [uptimerobot.com](https://uptimerobot.com)
2. Click **Add New Monitor**
3. Chọn loại: **HTTP(s)**
4. Điền:
   - **Friendly Name**: `Prepaid Expense App`
   - **URL**: URL Streamlit app của bạn (ví dụ: `https://your-app.streamlit.app`)
   - **Monitoring Interval**: **5 minutes** ← quan trọng, phải ≤ 5 phút
5. Click **Create Monitor**

> Với interval 5 phút, UptimeRobot sẽ ping trước khi Streamlit kịp ngủ.

---

## 🥈 Giải pháp 2: Cron-job.org (Miễn phí, backup)

1. Tạo tài khoản tại [cron-job.org](https://cron-job.org)
2. Tạo cronjob mới:
   - **URL**: URL Streamlit app
   - **Schedule**: Mỗi 5 phút (`*/5 * * * *`)
3. Lưu và bật cronjob

---

## 🥉 Giải pháp 3: GitHub Actions (Hỗ trợ thêm)

GitHub Actions **KHÔNG thể** giữ Streamlit thức một mình, nhưng hữu ích để:
- Đảm bảo app không bị **xóa** vì inactive quá lâu (>30 ngày)
- Trigger wake-up nếu kết hợp với UptimeRobot

File `.github/workflows/keep-alive.yml` hiện tại đã được cấu hình ping mỗi 30 phút.  
Bước thiết lập: Thêm secret `STREAMLIT_APP_URL` vào GitHub repo:
1. Vào **Settings** → **Secrets and variables** → **Actions**
2. **New repository secret** → Name: `STREAMLIT_APP_URL`, Value: URL app
3. Push code lên GitHub

---

## 📊 So sánh các giải pháp

| Giải pháp | Chi phí | Hiệu quả giữ thức | Dễ thiết lập |
|---|---|---|---|
| UptimeRobot (5 phút) | Miễn phí | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| cron-job.org (5 phút) | Miễn phí | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| GitHub Actions (30 phút) | Miễn phí | ⭐⭐ (quá chậm) | ⭐⭐⭐ |
| Streamlit Cloud trả phí | ~$25/tháng | ⭐⭐⭐⭐⭐ (không ngủ) | ⭐⭐⭐⭐⭐ |

---

## ✅ Kiểm tra sau khi thiết lập

1. Để app idle 10 phút không dùng
2. Mở URL app trên browser → nếu vào được ngay (không có màn hình "Waking up...") = thành công
3. Kiểm tra UptimeRobot dashboard xem logs ping có thành công không

---

**Kết luận:** Dùng **UptimeRobot** với interval **5 phút** là cách đơn giản và hiệu quả nhất để giữ Streamlit Free không ngủ.
