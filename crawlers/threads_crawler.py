"""
Threads (Meta) Comment Crawler.
Collects replies/comments from Threads posts.
Threads is a major hub of Gen Z discussions, containing high volumes of Vietnamese teencode.
"""

import re
import os
import json
from typing import List, Dict, Any, Optional
import requests
from core.base_crawler import BaseCrawler
from utils.logger import logger
from utils.helpers import parse_iso_datetime, format_datetime_vn, random_sleep

class ThreadsCrawler(BaseCrawler):
    def __init__(
        self,
        target_teencodes: Optional[List[str]] = None,
        max_years: int = 5
    ):
        super().__init__(
            platform_name="threads",
            target_teencodes=target_teencodes,
            max_years=max_years,
            rate_limit_delay=1.5
        )

    def extract_post_code(self, input_str: str) -> Optional[str]:
        """Trích xuất mã bài viết Threads (Shortcode). Ví dụ: C3abcXYZ từ https://www.threads.net/@user/post/C3abcXYZ"""
        input_str = input_str.strip()
        match = re.search(r'post\/([A-Za-z0-9_-]+)', input_str)
        if match:
            return match.group(1)
        if re.match(r'^[A-Za-z0-9_-]{9,15}$', input_str):
            return input_str
        return None

    def fetch_raw_comments(self, target_input: str, max_comments: int = 1000) -> List[Dict[str, Any]]:
        post_code = self.extract_post_code(target_input)
        if not post_code:
            logger.error(f"[Threads] Không trích xuất được Post code từ: {target_input}")
            return []

        logger.info(f"[Threads] Thu thập bình luận cho Post Code: [bold]{post_code}[/bold]")
        
        all_replies = []
        target_url = f"https://www.threads.net/t/{post_code}" if not target_input.startswith("http") else target_input

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
            "Sec-Fetch-Site": "same-origin",
        }

        try:
            resp = requests.get(target_url, headers=headers, timeout=15)
            if resp.status_code != 200:
                logger.error(f"[Threads] Status {resp.status_code} khi tải bài viết {target_url}")
                return []

            html = resp.text
            # Tìm các khối dữ liệu JSON nhúng trong trang Threads HTML
            # Thường nằm trong <script type="application/json" data-sjs>
            script_matches = re.findall(r'<script type="application\/json" data-sjs>(.*?)<\/script>', html)
            
            for script_content in script_matches:
                try:
                    data = json.loads(script_content)
                    extracted = self._extract_threads_replies(data)
                    for item in extracted:
                        item["_post_code"] = post_code
                        item["_post_url"] = target_url
                        all_replies.append(item)
                except Exception:
                    continue

            logger.info(f"[Threads] Trích xuất được {len(all_replies)} bình luận từ bài viết Threads.")

        except Exception as e:
            logger.error(f"[Threads] Lỗi kết nối: {e}")

        return all_replies[:max_comments]

    def _extract_threads_replies(self, data: Any) -> List[Dict[str, Any]]:
        """Duyệt đệ quy JSON của Threads để tìm các reply node."""
        results = []

        def recurse(node):
            if isinstance(node, dict):
                # Kiểm tra cấu trúc post thread của Meta
                if "post" in node and isinstance(node["post"], dict):
                    p = node["post"]
                    if "caption" in p or "text" in p.get("caption", {}):
                        results.append(p)
                for v in node.values():
                    recurse(v)
            elif isinstance(node, list):
                for item in node:
                    recurse(item)

        recurse(data)
        return results

    def parse_comment_item(self, item: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        context = context or {}
        comment_id = str(item.get("id", item.get("pk", "")))
        
        # Lấy caption / text
        caption_obj = item.get("caption", {})
        if isinstance(caption_obj, dict):
            text = caption_obj.get("text", "")
        else:
            text = str(caption_obj) if caption_obj else ""

        if not text:
            return None

        user = item.get("user", {})
        author_id = str(user.get("pk", user.get("id", "")))
        author_name = user.get("username", "Threads User")
        author_avatar = user.get("profile_pic_url", "")

        # Thời gian
        taken_at = item.get("taken_at", 0)
        dt_obj = parse_iso_datetime(taken_at)
        created_at_utc, created_at_vn, year = format_datetime_vn(dt_obj)

        post_code = item.get("_post_code") or context.get("post_code", "")
        post_url = item.get("_post_url") or context.get("post_url", f"https://www.threads.net/t/{post_code}")

        return {
            "comment_id": f"threads_{comment_id}",
            "parent_id": None,
            "platform": "threads",
            "post_id": post_code,
            "post_url": post_url,
            "post_title": context.get("post_title", f"Threads Post #{post_code}"),
            "author_id": author_id,
            "author_name": author_name,
            "author_avatar_url": author_avatar,
            "comment_text": text,
            "cleaned_text": "",
            "created_at": created_at_utc,
            "created_at_vn": created_at_vn,
            "year": year,
            "likes_count": item.get("like_count", 0),
            "reply_count": 0,
            "has_teencode": False,
            "detected_teencodes": [],
            "teencode_count": 0,
            "teencode_density": 0.0,
            "extra_metadata": {
                "is_verified": user.get("is_verified", False),
                "taken_at_timestamp": taken_at,
            },
            "_datetime_obj": dt_obj,
        }
