# Kiến Trúc Hệ Thống (System Architecture)

Tài liệu này mô tả chi tiết kiến trúc tổng thể, luồng xử lý dữ liệu (Data Pipeline), và các nguyên tắc thiết kế được áp dụng trong dự án.

---

## 1. Sơ Đồ Kiến Trúc Tổng Thể

Hệ thống được thiết kế theo mô hình **Pipeline-driven Modular Architecture**:

```mermaid
flowchart TD
    subgraph Sources ["Nguồn Dữ Liệu Mạng Xã Hội"]
        YT["YouTube (API / Innertube)"]
        TT["TikTok (Web API)"]
        SP["Shopee (Ratings API)"]
        FB["Facebook (Graph / Mobile)"]
    end

    subgraph Crawlers ["Tầng Crawler (Inherit BaseCrawler)"]
        C_YT["YouTubeCrawler"]
        C_TT["TikTokCrawler"]
        C_SP["ShopeeCrawler"]
        C_FB["FacebookCrawler"]
    end

    subgraph Pipeline ["Pipeline Xử Lý & Làm Giàu Dữ Liệu"]
        RAW_SAVE["1. Lưu Payload Thô (JSON Backup)"]
        TIME_FILTER["2. Bộ Lọc Thời Gian (5 Năm Gần Nhất)"]
        NORM["3. Chuẩn Hóa Văn Bản (Clean Whitespace/Unicode)"]
        TEEN_FILTER["4. Bộ Lọc Teencode (Regex Word Boundary)"]
        ENRICH["5. Làm Giàu Metadata (Tỷ Lệ %, Giờ VN UTC+7)"]
    end

    subgraph Storage ["Tầng Lưu Trữ & Xuất Dữ Liệu"]
        CSV_OUT["File CSV (UTF-8 with BOM)"]
        JSONL_OUT["File JSON Lines (NLP / Big Data)"]
        SQLITE_OUT["Cơ Sở Dữ Liệu SQLite"]
        EXCEL_OUT["Bảng Tính Excel (.xlsx)"]
    end

    subgraph Analytics ["Tầng Phân Tích & Báo Cáo (EDA)"]
        STATS["Thống Kê Tần Suất & Tỷ Lệ"]
        CHARTS["Biểu Đồ Trực Quan Hóa (Seaborn/Matplotlib)"]
        JSON_REPORT["Báo Cáo Tóm Tắt (summary_report.json)"]
    end

    YT --> C_YT
    TT --> C_TT
    SP --> C_SP
    FB --> C_FB

    C_YT & C_TT & C_SP & C_FB --> RAW_SAVE
    RAW_SAVE --> TIME_FILTER
    TIME_FILTER --> NORM
    NORM --> TEEN_FILTER
    TEEN_FILTER --> ENRICH

    ENRICH --> CSV_OUT & JSONL_OUT & SQLITE_OUT & EXCEL_OUT
    CSV_OUT & SQLITE_OUT --> STATS
    STATS --> CHARTS & JSON_REPORT
```

---

## 2. Các Thành Phần Cốt Lõi (Core Modules)

### 2.1. `core.base_crawler.BaseCrawler`
Lớp cha trừu tượng định nghĩa khung sườn xử lý nhất quán cho tất cả các nền tảng:
- Áp dụng mẫu thiết kế **Template Method Pattern**: Phương thức `run()` điều phối tuần tự quy trình `fetch -> backup -> filter -> enrich -> export -> report`.
- Các lớp con chỉ cần cài đặt logic đặc thù của nền tảng trong `fetch_raw_comments()` và `parse_comment_item()`.

### 2.2. `core.teencode_filter.TeencodeFilter`
Module xử lý ngôn ngữ tự nhiên (NLP) nhẹ chuyên biệt cho tiếng Việt:
- Tải từ điển từ `config/teencode_dict.json`.
- Biên dịch sẵn các biểu thức chính quy (Regex) với cơ chế ranh giới từ `(?<!\w)từ(?!\w)` đảm bảo hiệu năng cao khi duyệt hàng chục nghìn bình luận.
- Tính toán mật độ teencode:
  $$\text{Teencode Density} = \frac{\text{Số từ viết tắt phát hiện}}{\text{Tổng số từ trong bình luận}} \times 100\%$$

### 2.3. `core.data_exporter.DataExporter`
Chịu trách nhiệm lưu trữ và định dạng dữ liệu:
- Tự động khử trùng lặp (Deduplication) theo `comment_id`.
- Đảm bảo tính toàn vẹn của schema 21 trường thông tin.
- Xuất đồng thời đa định dạng phục vụ nhiều mục đích khác nhau (phân tích bảng biểu, huấn luyện mô hình học máy, hoặc lưu trữ quan hệ).
