"""
Helper utilities: Timezone conversion, date parsing, text cleaning, rate limit sleeping.
"""

import re
import time
import random
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, Any
from dateutil import parser as date_parser

VN_TZ = timezone(timedelta(hours=7))

def parse_relative_datetime(text: str) -> Optional[datetime]:
    """
    Parse relative datetime strings in Vietnamese or English into approximate UTC datetime.
    Supports YouTube, TikTok, Facebook relative time displays.
    """
    if not text:
        return None
    now = datetime.now(timezone.utc)
    raw = str(text).lower().strip()

    if "vừa xong" in raw or "mới xong" in raw or "just now" in raw or "moment ago" in raw:
        return now

    # Match Vietnamese relative formats (e.g., '6 năm trước', '4 tháng trước', '2 tuần trước')
    m_vn = re.search(r'(\d+)\s*(năm|tháng|tuần|ngày|giờ|phút|giây)\s*trước', raw)
    if m_vn:
        val = int(m_vn.group(1))
        unit = m_vn.group(2)
        if unit == 'năm':
            return now - timedelta(days=val * 365)
        elif unit == 'tháng':
            return now - timedelta(days=val * 30)
        elif unit == 'tuần':
            return now - timedelta(days=val * 7)
        elif unit == 'ngày':
            return now - timedelta(days=val)
        elif unit == 'giờ':
            return now - timedelta(hours=val)
        elif unit == 'phút':
            return now - timedelta(minutes=val)
        elif unit == 'giây':
            return now - timedelta(seconds=val)

    # Match English relative formats (e.g., '6 years ago', '4 months ago', '2 weeks ago')
    m_en = re.search(r'(\d+)\s*(year|month|week|day|hour|minute|second)s?\s*ago', raw)
    if m_en:
        val = int(m_en.group(1))
        unit = m_en.group(2)
        if unit == 'year':
            return now - timedelta(days=val * 365)
        elif unit == 'month':
            return now - timedelta(days=val * 30)
        elif unit == 'week':
            return now - timedelta(days=val * 7)
        elif unit == 'day':
            return now - timedelta(days=val)
        elif unit == 'hour':
            return now - timedelta(hours=val)
        elif unit == 'minute':
            return now - timedelta(minutes=val)
        elif unit == 'second':
            return now - timedelta(seconds=val)

    return None

def parse_iso_datetime(dt_str: Any) -> Optional[datetime]:
    """Parse various datetime string formats into UTC datetime (supports epoch, ISO, and relative time)."""
    if not dt_str:
        return None
    try:
        # If timestamp is integer/float (epoch)
        if str(dt_str).isdigit() or isinstance(dt_str, (int, float)):
            ts = float(dt_str)
            # If timestamp in milliseconds
            if ts > 1e11:
                ts = ts / 1000.0
            return datetime.fromtimestamp(ts, tz=timezone.utc)

        # Check relative time strings (e.g. YouTube Innertube '6 năm trước', '1 year ago')
        rel_dt = parse_relative_datetime(str(dt_str))
        if rel_dt:
            return rel_dt

        parsed = date_parser.parse(str(dt_str))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        else:
            parsed = parsed.astimezone(timezone.utc)
        return parsed
    except Exception:
        return None

def format_datetime_vn(dt: Optional[datetime]) -> Tuple[str, str, int]:
    """
    Format UTC datetime to:
    - ISO 8601 UTC string
    - Vietnam time string (YYYY-MM-DD HH:MM:SS)
    - Year integer
    """
    if not dt:
        now = datetime.now(timezone.utc)
        return now.isoformat(), now.astimezone(VN_TZ).strftime("%Y-%m-%d %H:%M:%S"), now.year

    utc_iso = dt.isoformat()
    vn_time = dt.astimezone(VN_TZ).strftime("%Y-%m-%d %H:%M:%S")
    year = dt.astimezone(VN_TZ).year
    return utc_iso, vn_time, year

def is_within_last_n_years(dt: Optional[datetime], years: int = 5) -> bool:
    """Check if the given datetime is within the last N years from now."""
    if not dt:
        return False  # Không xác định được ngày mà không rõ mốc thời gian thì không bảo đảm trong 5 năm
    now = datetime.now(timezone.utc)
    threshold = now - timedelta(days=years * 365)
    return dt >= threshold

def clean_comment_text(text: str, remove_mentions: bool = True) -> str:
    """Clean extra spaces, newlines, tabs, URLs, and optional mentions while preserving Vietnamese teencode words."""
    if not text:
        return ""
    text = str(text)
    if remove_mentions:
        # Loại bỏ các tag mention @username để tránh bắt nhầm chữ cái đơn như @m, @t, @a
        text = re.sub(r'@[A-Za-z0-9_.-]+', ' ', text)
    # Loại bỏ URL
    text = re.sub(r'https?://\S+|www\.\S+', ' ', text)
    # Thay nhiều khoảng trắng hoặc xuống dòng bằng khoảng trắng đơn
    text = re.sub(r'[\r\n\t]+', ' ', text)
    text = re.sub(r'\s{2,}', ' ', text)
    return text.strip()

def random_sleep(base_delay: float = 1.0, jitter: float = 0.5):
    """Sleep with random jitter to mimic human behavior and avoid anti-bot detection."""
    actual_delay = max(0.2, base_delay + random.uniform(-jitter, jitter))
    time.sleep(actual_delay)
