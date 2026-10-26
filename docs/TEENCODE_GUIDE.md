# Cơ Chế Nhận Diện & Xử Lý Teencode (Teencode Detection Engine)

Tài liệu này giải thích thuật toán nhận diện từ viết tắt tiếng Việt, phương pháp giải quyết hiện tượng *False Positive*, và cách tính toán các chỉ số thống kê ngữ liệu.

---

## 1. Bài Toán Ranh Giới Từ (The Word Boundary Problem)

Trong tiếng Việt và ngôn ngữ mạng, các từ viết tắt rất ngắn, thậm chí chỉ là một chữ cái đơn lẻ:
- `m` $\rightarrow$ *mày / mình*
- `k` $\rightarrow$ *không*
- `v` $\rightarrow$ *vậy*
- `j` $\rightarrow$ *gì*
- `cx` $\rightarrow$ *cũng*
- `ngta` $\rightarrow$ *người ta*

### Nguy cơ False Positive (Bắt nhầm):
Nếu sử dụng tìm kiếm chuỗi thông thường (`if "m" in text` hoặc `re.search("m", text)`), hệ thống sẽ gặp sai số nghiêm trọng:
- Chữ `m` sẽ bị phát hiện nhầm trong các từ như: `làm`, `tìm`, `mua`, `cảm ơn`...
- Chữ `k` sẽ bị bắt nhầm trong: `like`, `okay`, `kem`...
- Chữ `cx` có thể bị bắt nhầm nếu nằm trong một mã sản phẩm hoặc đường link.

---

## 2. Giải Pháp Biểu Thức Chính Quy (Unicode Word Boundary Regex)

Hệ thống sử dụng cơ chế **Negative Lookbehind** và **Negative Lookahead**:

```python
pattern = re.compile(rf'(?<!\w){escaped_word}(?!\w)', re.IGNORECASE)
```

### Ý nghĩa của cơ chế:
- `(?<!\w)`: Phía trước từ viết tắt **không được phép** là bất kỳ ký tự chữ hay số nào (chỉ chấp nhận khoảng trắng, dấu câu hoặc đầu dòng).
- `(?!\w)`: Phía sau từ viết tắt **không được phép** là bất kỳ ký tự chữ hay số nào.
- `re.IGNORECASE`: Chấp nhận mọi biến thể viết hoa/thường: `Ngta`, `ngta`, `NGTA`.

### Bảng Kiểm Thử Thực Nghiệm:
| Câu bình luận đầu vào | Từ viết tắt mục tiêu | Kết quả phân tích | Trạng thái |
| :--- | :---: | :---: | :---: |
| `"Hôm nay m đi đâu thế?"` | `m` | Phát hiện: `['m']` | Chuẩn xác |
| `"Tôi đang làm bài tập"` | `m` | Không phát hiện | Tránh bắt nhầm từ `làm` |
| `"k bt ngta lm ntn mà đỉnh v"` | `k, ngta, lm, ntn, v` | Phát hiện: 5 từ | Trích xuất đầy đủ |
| `"Video này hay quá like nha"` | `k` | Không phát hiện | Tránh bắt nhầm từ `like` |

---

## 3. Các Chỉ Số Đánh Giá (Metrics)

1. **Tổng số từ viết tắt (`teencode_count`):**
   $$C = \sum_{i=1}^{n} \text{count}(w_i)$$
   Trong đó $w_i$ là từ viết tắt thứ $i$ xuất hiện trong câu.

2. **Mật độ từ viết tắt (`teencode_density`):**
   $$D = \frac{C}{T} \times 100\%$$
   Với $T$ là tổng số từ (word count) của toàn bộ câu bình luận. Chỉ số này phản ánh mức độ "đậm đặc" ngôn ngữ mạng của người bình luận.

3. **Từ điển ngữ nghĩa tương đương:**
   File cấu hình [teencode_dict.json](file:///d:/HKDN/Nhiem_vu_18/config/teencode_dict.json) chứa bản đồ ánh xạ từ viết tắt sang dạng chuẩn tiếng Việt, hỗ trợ bài toán chuẩn hóa văn bản (Text Normalization) phục vụ các mô hình học máy (BERT/PhoBERT).
