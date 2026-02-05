# 🚨 HƯỚNG DẪN XỬ LÝ TOKEN.JSON TRÊN GIT/GITHUB

## 📊 TÌNH TRẠNG HIỆN Tại

### ✅ TIN TỐT:
Sau khi kiểm tra, tôi phát hiện:
- ✅ `token.json` **CHƯA** được track bởi Git (không có trong `git ls-files`)
- ✅ File chỉ tồn tại ở local
- ✅ `.gitignore` đã có `*.json` nên sẽ tự động ignore

### ⚠️ CẦN KIỂM TRA:
Tuy nhiên, để **CHẮC CHẮN 100%**, bạn cần kiểm tra trên GitHub:

---

## 🔍 BƯỚC 1: KIỂM TRA TRÊN GITHUB

### Cách 1: Qua Web Browser
1. Truy cập: https://github.com/hoangdm2912/prepaid_expense_manager
2. Tìm file `token.json` trong danh sách file
3. Nếu **THẤY** file này → Token đã bị lộ (chuyển sang BƯỚC 2)
4. Nếu **KHÔNG THẤY** → An toàn (chuyển sang BƯỚC 3)

### Cách 2: Qua Git Command
```bash
# Kiểm tra file có trong remote không
git ls-tree -r origin/main --name-only | findstr "token"
```

Nếu lệnh trả về **rỗng** → An toàn ✅
Nếu lệnh trả về **token.json** → Nguy hiểm ⚠️

---

## 🚨 BƯỚC 2: NẾU TOKEN ĐÃ BỊ COMMIT LÊN GITHUB

### ⚠️ NGUY HIỂM:
- Token đã công khai trên Internet
- Bất kỳ ai cũng có thể truy cập Google Drive của bạn
- Cần hành động NGAY LẬP TỨC

### 🔥 HÀNH ĐỘNG KHẨN CẤP:

#### A. Revoke Token Cũ (QUAN TRỌNG NHẤT!)

1. **Xóa token hiện tại:**
   ```bash
   # Xóa file token local
   rm token.json
   ```

2. **Revoke quyền truy cập trên Google:**
   - Truy cập: https://myaccount.google.com/permissions
   - Tìm ứng dụng "Prepaid Expense Manager" (hoặc tên project của bạn)
   - Click **"Remove Access"** hoặc **"Revoke"**
   - Xác nhận xóa

3. **Kết nối lại:**
   - Chạy app: `streamlit run app.py`
   - Vào trang **Cài đặt**
   - Click **"Kết nối Tài khoản Cá nhân"**
   - Làm theo hướng dẫn để tạo token mới

#### B. Xóa Token Khỏi Git History

**⚠️ LƯU Ý:** Thao tác này sẽ **VIẾT LẠI LỊCH SỬ GIT**!

##### Phương án 1: Dùng BFG Repo-Cleaner (Khuyến nghị)

```bash
# 1. Tải BFG
# Truy cập: https://rtyley.github.io/bfg-repo-cleaner/
# Tải file bfg.jar

# 2. Backup repo
git clone --mirror https://github.com/hoangdm2912/prepaid_expense_manager.git

# 3. Xóa file
java -jar bfg.jar --delete-files token.json prepaid_expense_manager.git

# 4. Cleanup
cd prepaid_expense_manager.git
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# 5. Force push
git push --force
```

##### Phương án 2: Dùng git filter-branch

```bash
# Xóa token.json khỏi toàn bộ history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch token.json" \
  --prune-empty --tag-name-filter cat -- --all

# Force push
git push origin --force --all
```

##### Phương án 3: Dùng git filter-repo (Hiện đại nhất)

```bash
# Cài đặt git-filter-repo
pip install git-filter-repo

# Xóa file
git filter-repo --path token.json --invert-paths

# Force push
git push origin --force --all
```

#### C. Đảm Bảo Không Commit Lại

```bash
# Kiểm tra .gitignore
cat .gitignore | findstr "json"

# Nếu chưa có, thêm vào:
echo "token.json" >> .gitignore
echo "*.json" >> .gitignore

# Commit .gitignore
git add .gitignore
git commit -m "Add token.json to gitignore"
git push
```

---

## ✅ BƯỚC 3: NẾU TOKEN CHƯA BỊ COMMIT (AN TOÀN)

Nếu kiểm tra và **KHÔNG THẤY** `token.json` trên GitHub:

### Bạn đã an toàn! Chỉ cần:

1. **Đảm bảo .gitignore đúng:**
   ```bash
   # Kiểm tra
   cat .gitignore | findstr "json"
   
   # Kết quả mong đợi:
   # *.json
   # credentials.json
   ```

2. **Test thử:**
   ```bash
   # Thử add token.json
   git add token.json
   
   # Nếu thấy warning "ignored by .gitignore" → OK ✅
   # Nếu file được add → Cần sửa .gitignore
   ```

3. **Commit các thay đổi hiện tại:**
   ```bash
   git add .
   git commit -m "Remove email notification module and fix security issues"
   git push
   ```

---

## 🔒 BƯỚC 4: BẢO MẬT TƯƠNG LAI

### Checklist Bảo Mật:

- [ ] `token.json` đã được ignore bởi `.gitignore`
- [ ] `credentials.json` đã được ignore
- [ ] `.env` đã được ignore
- [ ] Không có thông tin nhạy cảm trong code
- [ ] Token được lưu trong Streamlit Secrets (nếu deploy)

### Quy tắc Vàng:

1. **KHÔNG BAO GIỜ** commit file chứa:
   - Token
   - API Keys
   - Passwords
   - Credentials
   - Private Keys

2. **LUÔN LUÔN** kiểm tra trước khi commit:
   ```bash
   git status
   git diff
   ```

3. **SỬ DỤNG** Streamlit Secrets cho production:
   - Lưu token vào Settings > Secrets
   - Không lưu trong file

---

## 📋 SCRIPT TỰ ĐỘNG KIỂM TRA

Tôi đã tạo script để kiểm tra nhanh:

```bash
# Chạy script này để kiểm tra
python check_token_security.py
```

Script sẽ:
- ✅ Kiểm tra token.json có trong Git không
- ✅ Kiểm tra .gitignore có đúng không
- ✅ Kiểm tra token có trên remote không
- ✅ Đưa ra khuyến nghị

---

## 🆘 CẦN GIÚP ĐỠ?

Nếu bạn:
- ❓ Không chắc token đã bị lộ chưa
- ❓ Không biết cách revoke token
- ❓ Cần giúp xóa khỏi Git history

→ **Hãy cho tôi biết kết quả kiểm tra trên GitHub!**

---

## 📞 LIÊN HỆ KHẨN CẤP

Nếu xác nhận token đã bị lộ:
1. **NGAY LẬP TỨC** revoke token (Bước 2A)
2. **SAU ĐÓ** xóa khỏi Git history (Bước 2B)
3. **CUỐI CÙNG** tạo token mới

**Thời gian:** Càng nhanh càng tốt (trong vòng 1 giờ)

---

**Cập nhật:** 2026-02-05 18:48
**Trạng thái:** Đang chờ kiểm tra từ người dùng
