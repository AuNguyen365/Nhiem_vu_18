"""
Helper utilities: Timezone conversion, date parsing, text cleaning, rate limit sleeping.
"""

import re
import time
import random
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from dateutil import parser as date_parser

VN_TZ = timezone(timedelta(hours=7))

def parse_iso_datetime(dt_str: str) -> Optional[datetime]:
    """Parse various datetime string formats into UTC datetime."""
    if not dt_str:
        return None
    try:
        # If timestamp is integer/float (epoch)
        if str(dt_str).isdigit() or (isinstance(dt_str, (int, float))):
            ts = float(dt_str)
            # If timestamp in milliseconds
            if ts > 1e11:
                ts = ts / 1000.0
            return datetime.fromtimestamp(ts, tz=timezone.utc)

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
        return True  # Mặc định giữ lại nếu không rõ ngày để không bỏ sót, hoặc có thể tùy chỉnh
    now = datetime.now(timezone.utc)
    threshold = now - timedelta(days=years * 365)
    return dt >= threshold

def clean_comment_text(text: str) -> str:
    """Clean extra spaces, newlines, tabs while preserving Vietnamese teencode words."""
    if not text:
        return ""
    # Thay nhiều khoảng trắng hoặc xuống dòng bằng khoảng trắng đơn
    text = re.sub(r'[\r\n\t]+', ' ', str(text))
    text = re.sub(r'\s{2,}', ' ', text)
    return text.strip()

def random_sleep(base_delay: float = 1.0, jitter: float = 0.5):
    """Sleep with random jitter to mimic human behavior and avoid anti-bot detection."""
    actual_delay = max(0.2, base_delay + random.uniform(-jitter, jitter))
    time.sleep(actual_delay)
