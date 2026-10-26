"""
Configuration settings for Social Media Comment Crawler Framework.
Includes time range filters (5-year window), file paths, and platform configs.
"""

from datetime import datetime, timezone, timedelta
from pathlib import Path

# Thư mục gốc dự án
BASE_DIR = Path(__file__).resolve().parent.parent

# Thư mục dữ liệu
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
CONFIG_DIR = BASE_DIR / "config"
OUTPUT_REPORT_DIR = BASE_DIR / "reports"

# Đảm bảo các thư mục luôn tồn tại
for d in [RAW_DATA_DIR, PROCESSED_DATA_DIR, CONFIG_DIR, OUTPUT_REPORT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Đường dẫn từ điển Teencode
TEENCODE_DICT_PATH = CONFIG_DIR / "teencode_dict.json"

# Cấu hình mốc thời gian 5 năm gần nhất
# Lấy mốc thời gian hiện tại và lùi lại đúng 5 năm (365 * 5 = 1825 ngày)
CURRENT_DATETIME = datetime.now(timezone.utc)
FIVE_YEARS_AGO = CURRENT_DATETIME - timedelta(days=5 * 365)

TIME_FILTER_CONFIG = {
    "start_date": FIVE_YEARS_AGO,
    "end_date": CURRENT_DATETIME,
    "start_year": FIVE_YEARS_AGO.year,
    "end_year": CURRENT_DATETIME.year,
}

# User-Agent xoay vòng để tránh bị chặn
DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
]

# Cấu hình Rate Limiting (giây) giữa các request
RATE_LIMIT_DELAY = {
    "youtube": 0.5,
    "tiktok": 1.5,
    "shopee": 1.0,
    "facebook": 2.0,
}

# Cấu hình schema chuẩn cho comment (Đầy đủ nhất có thể)
COMMENT_SCHEMA = [
    "comment_id",          # ID định danh bình luận
    "parent_id",           # ID bình luận cha (nếu là reply)
    "platform",            # Nền tảng (youtube/facebook/tiktok/shopee)
    "post_id",             # ID video/bài viết/sản phẩm
    "post_url",            # Link gốc bài viết/video/sản phẩm
    "post_title",          # Tiêu đề bài viết/video
    "author_id",           # ID định danh người viết
    "author_name",         # Tên người viết
    "author_avatar_url",   # Link ảnh đại diện
    "comment_text",        # Nội dung bình luận thô
    "cleaned_text",        # Nội dung sau khi chuẩn hóa
    "created_at",          # Thời điểm đăng (ISO 8601 UTC)
    "created_at_vn",       # Thời điểm đăng (Giờ Việt Nam: UTC+7)
    "year",                # Năm (2021, 2022, 2023, 2024, 2025, 2026)
    "likes_count",         # Số lượt thích / thả tim
    "reply_count",         # Số phản hồi con
    "has_teencode",        # True nếu chứa từ viết tắt cần tìm
    "detected_teencodes",  # Danh sách từ viết tắt phát hiện được (ngta, m, cx...)
    "teencode_count",      # Tổng số từ viết tắt trong câu
    "teencode_density",    # Tỷ lệ từ viết tắt trên tổng số từ (%)
    "extra_metadata",      # Metadata mở rộng dạng JSON (rating sao, device, badge...)
]
