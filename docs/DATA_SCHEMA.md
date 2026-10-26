# Đặc Tả Dữ Liệu Chi Tiết (Data Schema Specification)

Tài liệu này cung cấp định nghĩa chi tiết của **21 trường thông tin** được trích xuất cho mỗi bình luận mạng xã hội, kèm theo kiểu dữ liệu, ví dụ minh họa và quy tắc nghiệp vụ.

---

## 1. Bảng Từ Điển Dữ Liệu (Data Dictionary)

| STT | Tên trường (`Field Name`) | Kiểu dữ liệu (`Type`) | Nullable | Mô tả chi tiết & Ví dụ |
| :---: | :--- | :---: | :---: | :--- |
| **1** | `comment_id` | `VARCHAR(64)` | ❌ Không | Mã định danh duy nhất của bình luận. Có tiền tố nền tảng để tránh xung đột (vd: `shopee_19283746`, `yt_Ugx7a8b...`). |
| **2** | `parent_id` | `VARCHAR(64)` | ✔️ Có | ID của bình luận cha nếu đây là câu trả lời (reply). Là `NULL` nếu là bình luận cấp cao nhất (top-level). |
| **3** | `platform` | `VARCHAR(16)` | ❌ Không | Tên nền tảng mạng xã hội: `youtube`, `tiktok`, `shopee`, `facebook`, `threads`. |
| **4** | `post_id` | `VARCHAR(64)` | ❌ Không | Mã ID của video, bài đăng hoặc sản phẩm chứa bình luận. |
| **5** | `post_url` | `TEXT` | ❌ Không | Đường dẫn URL truy cập trực tiếp tới bài viết/video/sản phẩm trên mạng xã hội. |
| **6** | `post_title` | `TEXT` | ✔️ Có | Tiêu đề của video hoặc nội dung mở đầu bài đăng gốc. |
| **7** | `author_id` | `VARCHAR(64)` | ✔️ Có | ID định danh tác giả bình luận (Channel ID, User ID, Shopee Buyer ID). |
| **8** | `author_name` | `VARCHAR(128)` | ❌ Không | Tên hiển thị công khai của người bình luận (DisplayName / Nickname). |
| **9** | `author_avatar_url` | `TEXT` | ✔️ Có | Đường dẫn URL tải ảnh đại diện của người dùng. |
| **10** | `comment_text` | `TEXT` | ❌ Không | Nội dung bình luận thô ban đầu bao gồm cả emoji, ký tự xuống dòng. |
| **11** | `cleaned_text` | `TEXT` | ❌ Không | Nội dung đã được chuẩn hóa (loại bỏ xuống dòng thừa, khoảng trắng kép). |
| **12** | `created_at` | `TIMESTAMP` | ❌ Không | Thời điểm đăng theo chuẩn ISO 8601 UTC (vd: `2024-05-12T14:30:00Z`). |
| **13** | `created_at_vn` | `VARCHAR(19)` | ❌ Không | Thời điểm đăng theo múi giờ Việt Nam UTC+7 định dạng `YYYY-MM-DD HH:MM:SS`. |
| **14** | `year` | `SMALLINT` | ❌ Không | Năm đăng bình luận (2021, 2022, 2023, 2024, 2025, 2026) để phục vụ gom nhóm phân tích theo mốc 5 năm. |
| **15** | `likes_count` | `INTEGER` | ❌ Không | Số lượt thích (like/tim) của bình luận. Mặc định là `0`. |
| **16** | `reply_count` | `INTEGER` | ❌ Không | Số lượng câu trả lời con bên dưới bình luận này. |
| **17** | `has_teencode` | `BOOLEAN` | ❌ Không | Cờ xác nhận bình luận có chứa từ viết tắt (`True`/`False`). |
| **18** | `detected_teencodes` | `JSON / ARRAY` | ❌ Không | Danh sách các từ viết tắt tìm thấy (vd: `["ngta", "m", "cx", "đc"]`). |
| **19** | `teencode_count` | `SMALLINT` | ❌ Không | Tổng số lần xuất hiện của các từ viết tắt trong nội dung bình luận. |
| **20** | `teencode_density` | `DECIMAL(5,2)` | ❌ Không | Mật độ phần trăm từ viết tắt trên tổng số từ của câu (vd: `28.57%`). |
| **21** | `extra_metadata` | `JSON` | ✔️ Có | Thuộc tính mở rộng đặc thù của từng nền tảng (sao đánh giá Shopee, phân loại hàng, huy hiệu tác giả, tick xanh...). |

---

## 2. Bản Ghi Mẫu Hoàn Chỉnh (Sample JSON Record)

```json
{
  "comment_id": "shopee_2849102847",
  "parent_id": null,
  "platform": "shopee",
  "post_id": "1948201_849201948",
  "post_url": "https://shopee.vn/product/1948201/849201948",
  "post_title": "Áo Thun Cotton Form Rộng Unisex phong cách Hàn Quốc",
  "author_id": "38491029",
  "author_name": "minh_anh_2004",
  "author_avatar_url": "https://cf.shopee.vn/file/vn-11134207-7r98o-lsth94...",
  "comment_text": "Áo giao nhanh xỉu, ngta mặc lên form đẹp lắm nha m ơi, mik cx tính mua thêm cái nữa nè, mn nên thử",
  "cleaned_text": "Áo giao nhanh xỉu, ngta mặc lên form đẹp lắm nha m ơi, mik cx tính mua thêm cái nữa nè, mn nên thử",
  "created_at": "2024-08-15T09:42:15Z",
  "created_at_vn": "2024-08-15 16:42:15",
  "year": 2024,
  "likes_count": 14,
  "reply_count": 1,
  "has_teencode": true,
  "detected_teencodes": ["ngta", "m", "mik", "cx", "mn"],
  "teencode_count": 5,
  "teencode_density": 21.74,
  "extra_metadata": {
    "rating_star": 5,
    "product_variation": "Màu Đen - Size L",
    "has_images": true,
    "has_videos": false,
    "anonymous": false
  }
}
```
