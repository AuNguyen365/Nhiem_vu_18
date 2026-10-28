"""
TikTok Comment Crawler.
Collects comments from TikTok videos via Web Comment API.
Extracts rich metadata: user id, nickname, unique_id, digg_count (likes), reply count, timestamp.
"""

import re
import os
import json
from typing import List, Dict, Any, Optional
import requests
from core.base_crawler import BaseCrawler
from utils.logger import logger
from utils.helpers import parse_iso_datetime, format_datetime_vn, random_sleep

class TikTokCrawler(BaseCrawler):
    def __init__(
        self,
        session_cookie: Optional[str] = None,
        target_teencodes: Optional[List[str]] = None,
        max_years: int = 5
    ):
        super().__init__(
            platform_name="tiktok",
            target_teencodes=target_teencodes,
            max_years=max_years,
            rate_limit_delay=1.5
        )
        self.session_cookie = session_cookie or os.getenv("TIKTOK_COOKIE", "")

    def extract_video_id(self, input_str: str) -> Optional[str]:
        """Trích xuất Aweme ID (Video ID) từ link TikTok."""
        input_str = input_str.strip()
        # Dạng: /video/7123456789012345678
        match = re.search(r'video\/(\d{15,22})', input_str)
        if match:
            return match.group(1)
        # Nếu nhập trực tiếp ID số
        if input_str.isdigit() and len(input_str) >= 15:
            return input_str

        # Nếu là link rút gọn (vt.tiktok.com hoặc vm.tiktok.com)
        if "tiktok.com" in input_str:
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                }
                # Theo dõi redirect để lấy URL đầy đủ
                resp = requests.head(input_str, allow_redirects=True, timeout=10, headers=headers)
                match = re.search(r'video\/(\d{15,22})', resp.url)
                if match:
                    return match.group(1)
                # Đôi khi TikTok chặn HEAD method, thử dùng GET
                resp = requests.get(input_str, allow_redirects=True, timeout=10, headers=headers)
                match = re.search(r'video\/(\d{15,22})', resp.url)
                if match:
                    return match.group(1)
            except Exception as e:
                logger.warning(f"[TikTok] Không thể giải mã link rút gọn qua redirect: {e}")

        return None

    def fetch_raw_comments(self, target_input: str, max_comments: int = 1000) -> List[Dict[str, Any]]:
        video_id = self.extract_video_id(target_input)
        if not video_id:
            logger.error(f"[TikTok] Không trích xuất được Video ID từ: {target_input}. Hãy dùng link dạng: https://www.tiktok.com/@user/video/7123456789012345678")
            return []

        logger.info(f"[TikTok] Thu thập bình luận cho Video ID: [bold]{video_id}[/bold]")

        all_comments = []
        cursor = 0
        count_per_req = 20
        api_url = "https://www.tiktok.com/api/comment/list/"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Referer": f"https://www.tiktok.com/@tiktok/video/{video_id}",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        if self.session_cookie:
            headers["Cookie"] = self.session_cookie

        session = requests.Session()

        while len(all_comments) < max_comments:
            params = {
                "aweme_id": video_id,
                "cursor": cursor,
                "count": count_per_req,
                "current_region": "VN",
                "aid": "1988",
                "app_language": "vi-VN",
            }

            try:
                resp = session.get(api_url, headers=headers, params=params, timeout=15)
                if resp.status_code != 200:
                    logger.error(f"[TikTok API Error] Status {resp.status_code}: {resp.text[:200]}")
                    break

                data = resp.json()
                comments = data.get("comments", [])
                has_more = data.get("has_more", 0)

                if not comments:
                    logger.info("[TikTok] Hết bình luận hoặc TikTok yêu cầu xác thực bot (Captcha/msToken).")
                    break

                for c in comments:
                    c["_video_id"] = video_id
                    c["_post_url"] = f"https://www.tiktok.com/@user/video/{video_id}"
                    all_comments.append(c)

                cursor = data.get("cursor", cursor + count_per_req)
                logger.info(f"[TikTok API] Đã thu thập {len(all_comments)}/{max_comments} bình luận...")

                if has_more != 1 or len(all_comments) >= max_comments:
                    break

                random_sleep(self.rate_limit_delay)

            except Exception as e:
                logger.error(f"[TikTok API] Lỗi ngoại lệ: {e}")
                break

        return all_comments

    def parse_comment_item(self, item: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Chuyển đổi dữ liệu bình luận TikTok sang COMMENT_SCHEMA chuẩn."""
        context = context or {}
        comment_id = str(item.get("cid", ""))
        text = item.get("text", "")
        if not text:
            return None

        user_info = item.get("user", {})
        author_id = str(user_info.get("uid", ""))
        author_name = user_info.get("nickname", "") or user_info.get("unique_id", "TikToker")
        
        # Avatar
        avatar_thumb = user_info.get("avatar_thumb", {})
        avatar_url = avatar_thumb.get("url_list", [""])[0] if isinstance(avatar_thumb, dict) else ""

        # Thời gian
        create_time = item.get("create_time", 0)
        dt_obj = parse_iso_datetime(create_time)
        created_at_utc, created_at_vn, year = format_datetime_vn(dt_obj)

        video_id = item.get("_video_id") or context.get("video_id", "")
        post_url = item.get("_post_url") or context.get("post_url", f"https://www.tiktok.com/@user/video/{video_id}")

        return {
            "comment_id": f"tiktok_{comment_id}",
            "parent_id": None,
            "platform": "tiktok",
            "post_id": video_id,
            "post_url": post_url,
            "post_title": context.get("post_title", f"TikTok Video #{video_id}"),
            "author_id": author_id,
            "author_name": author_name,
            "author_avatar_url": avatar_url,
            "comment_text": text,
            "cleaned_text": "",
            "created_at": created_at_utc,
            "created_at_vn": created_at_vn,
            "year": year,
            "likes_count": item.get("digg_count", 0),
            "reply_count": item.get("reply_comment_total", 0),
            "has_teencode": False,
            "detected_teencodes": [],
            "teencode_count": 0,
            "teencode_density": 0.0,
            "extra_metadata": {
                "unique_id": user_info.get("unique_id"),
                "sec_uid": user_info.get("sec_uid"),
                "is_author_liked": item.get("is_author_liked", False),
            },
            "_datetime_obj": dt_obj,
        }
