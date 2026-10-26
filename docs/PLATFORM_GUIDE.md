# Hướng Dẫn Từng Nền Tảng (Platform Guide)

Tài liệu này cung cấp hướng dẫn chi tiết dành cho từng nhóm nghiên cứu khi lựa chọn **1 trong 5 nền tảng mạng xã hội**: YouTube, TikTok, Shopee, Facebook, hoặc Threads.

---

## 1. Nền Tảng YouTube (`youtube`)

YouTube là nền tảng có thời gian lưu trữ bình luận lâu đời nhất (dễ dàng lấy đủ dữ liệu trong 5 năm gần đây từ 2021 đến 2026).

### Cách lấy Target Input:
- Mở video trên trình duyệt, copy toàn bộ URL trên thanh địa chỉ:
  - `https://www.youtube.com/watch?v=k_79q8bE48g`
  - Hoặc dạng rút gọn: `https://youtu.be/k_79q8bE48g`
  - Hoặc YouTube Shorts: `https://www.youtube.com/shorts/k_79q8bE48g`

### Chế độ hoạt động:
1. **Chế độ Scraper không cần API Key (Mặc định):**
   - Tự động bóc tách continuation token và gọi endpoint nội bộ Innertube của YouTube.
   - Thích hợp cho người dùng không muốn đăng ký Google Cloud Console.
2. **Chế độ Google Cloud Data API v3 (Khuyên dùng):**
   - Đăng ký API Key miễn phí tại [Google Cloud Console](https://console.cloud.google.com/).
   - Thiết lập biến môi trường:
     ```powershell
     $env:YOUTUBE_API_KEY="AIzaSyYourAPIKeyHere..."
     python main.py -p youtube -i "URL_VIDEO" --max 1000
     ```

---

## 2. Nền Tảng Shopee (`shopee`)

Shopee là **nền tảng tốt nhất** để thu thập từ viết tắt tiếng Việt của giới trẻ (*ngta, m, cx, k, mik, mn, sp, shop, thik, v, j, đẹp, đc...*) từ các đánh giá mua hàng thực tế.

### Cách lấy Target Input:
- Truy cập bất kỳ sản phẩm nào có từ 500 đánh giá trở lên.
- Copy đường link sản phẩm:
  - `https://shopee.vn/product-name-i.12345678.98765432`
  - Hoặc cú pháp ngắn gọn: `shopid_itemid` (ví dụ: `12345678_98765432`)

### Lệnh thực thi:
```bash
python main.py -p shopee -i "https://shopee.vn/product-name-i.12345678.98765432" --max 1000
```

---

## 3. Nền Tảng TikTok (`tiktok`)

TikTok là cái nôi sản sinh ra nhiều từ lóng và trào lưu viết tắt mới nhất của Gen Z Việt Nam.

### Cách lấy Target Input:
- Copy đường link video TikTok trên máy tính:
  - `https://www.tiktok.com/@vtv24news/video/7328910293849102938`
- Hoặc copy Aweme Video ID (chuỗi 19 chữ số).

### Lưu ý về Anti-bot:
TikTok có cơ chế bảo vệ bot nghiêm ngặt (kiểm tra `msToken` và Captcha). Nếu gặp tình trạng trả về 0 bình luận, hãy copy Cookie từ trình duyệt khi đã đăng nhập TikTok và gán vào biến môi trường:
```powershell
$env:TIKTOK_COOKIE="sessionid=...; ttwid=..."
python main.py -p tiktok -i "LINK_TIKTOK" --max 500
```

---

## 4. Nền Tảng Facebook (`facebook`)

Facebook sở hữu lượng bình luận khổng lồ nhưng có chính sách bảo mật dữ liệu người dùng rất khắt khe.

### Cách thực thi:
- **Phương án 1 (Graph API chính thống cho Fanpage):**
  - Cần Fanpage Page Access Token có quyền `pages_read_engagement`.
  - Thiết lập: `$env:FACEBOOK_ACCESS_TOKEN="EAA..."`
- **Phương án 2 (Mobile Web Parsing):**
  - Cung cấp Cookie tài khoản Facebook: `$env:FACEBOOK_COOKIE="c_user=...; xs=..."`
  ```bash
  python main.py -p facebook -i "https://www.facebook.com/posts/123456789" --max 500
  ```

---

## 5. Nền Tảng Threads (`threads`)

Threads là mạng xã hội chia sẻ văn bản dạng ngắn của Meta, cực kỳ phổ biến với học sinh, sinh viên tại Việt Nam.

### Cách lấy Target Input:
- Copy link bài đăng Threads:
  - `https://www.threads.net/@nguoidung/post/C4XyZaB123`
- Hoặc Shortcode của bài đăng: `C4XyZaB123`.

### Lệnh thực thi:
```bash
python main.py -p threads -i "https://www.threads.net/@nguoidung/post/C4XyZaB123" --max 500
```
