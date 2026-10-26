# Hướng Dẫn Đóng Góp (Contribution Guidelines)

Chào mừng bạn đã tham gia đóng góp cho dự án **Social Media Comment Crawler & Teencode Analytics Framework** (Nhiệm vụ 18)!

---

## 1. Quy Trình Làm Việc (Git Workflow)

1. **Fork** repository về tài khoản cá nhân hoặc tạo branch mới từ `main`:
   ```bash
   git checkout -b feature/ten-tinh-nang-moi
   ```
2. Thực hiện các chỉnh sửa, viết code tuân theo chuẩn PEP 8.
3. Chạy kiểm thử toàn bộ pipeline với lệnh demo:
   ```bash
   python main.py --demo
   python analyze.py
   ```
4. Commit với thông điệp rõ ràng theo định dạng [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat: thêm cơ chế phân trang cho TikTok crawler`
   - `fix: sửa lỗi regex ranh giới từ tiếng Việt`
   - `docs: cập nhật tài liệu hướng dẫn Shopee API`
5. Push lên branch của bạn và tạo **Pull Request (PR)** vào branch `main`.

---

## 2. Tiêu Chuẩn Viết Code

- **Ngôn ngữ:** Python 3.10+
- **Type Hinting:** Tất cả các hàm và phương thức mới phải có đầy đủ chú thích kiểu dữ liệu (`typing.List`, `typing.Dict`, `typing.Optional`,...).
- **Docstrings:** Viết docstring giải thích mục đích, tham số đầu vào và kiểu dữ liệu trả về theo chuẩn Google Style / Sphinx.
- **Xử lý ngoại lệ:** Sử dụng `try...except` và ghi log qua `utils.logger` thay vì dùng hàm `print()` trần.
- **Bảo mật:** Không bao giờ commit hard-code API Key, Access Token hay Session Cookie vào mã nguồn. Luôn đọc từ biến môi trường (`os.getenv(...)`).

---

## 3. Báo Cáo Sự Cố & Đóng Góp Từ Điển Teencode

Nếu bạn phát hiện các từ viết tắt / từ lóng mới của giới trẻ chưa có trong từ điển:
- Mở file `config/teencode_dict.json`
- Bổ sung cặp key-value: `"từ_viết_tắt": "nghĩa_đầy_đủ"`
- Tạo Pull Request kèm theo câu ví dụ thực tế.
