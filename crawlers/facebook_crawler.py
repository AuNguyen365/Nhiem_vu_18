"""
Facebook Comment Crawler.
Supports Graph API (Page posts) and mobile web endpoint parsing (with Facebook Cookie).
"""

import re
import os
import json
from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup
from core.base_crawler import BaseCrawler
from utils.logger import logger
from utils.helpers import parse_iso_datetime, format_datetime_vn, random_sleep

class FacebookCrawler(BaseCrawler):
    def __init__(
        self,
        access_token: Optional[str] = None,
        cookie: Optional[str] = None,
        target_teencodes: Optional[List[str]] = None,
        max_years: int = 5
    ):
        super().__init__(
            platform_name="facebook",
            target_teencodes=target_teencodes,
            max_years=max_years,
            rate_limit_delay=2.0
        )
        self.access_token = access_token or os.getenv("FACEBOOK_ACCESS_TOKEN", "")
        self.cookie = cookie or os.getenv("FACEBOOK_COOKIE", "")

    def extract_post_id(self, input_str: str) -> Optional[str]:
        """Trích xuất Post ID hoặc Fbid từ link bài viết Facebook."""
        input_str = input_str.strip()
        # Dạng: /posts/123456789 hoặc /story.php?story_fbid=123456789
        match = re.search(r'(?:posts\/|story_fbid=|fbid=)(\d+)', input_str)
        if match:
            return match.group(1)
        if input_str.isdigit() and len(input_str) >= 8:
            return input_str
        return None

    def fetch_raw_comments(self, target_input: str, max_comments: int = 1000) -> List[Dict[str, Any]]:
        post_id = self.extract_post_id(target_input)
        if not post_id:
            logger.error(f"[Facebook] Không trích xuất được Post ID từ: {target_input}")
            return []

        logger.info(f"[Facebook] Thu thập bình luận cho Post ID: [bold]{post_id}[/bold]")

        if self.access_token:
            return self._fetch_via_graph_api(post_id, max_comments)
        else:
            return self._fetch_via_mobile_web(post_id, target_input, max_comments)

    def _fetch_via_graph_api(self, post_id: str, max_comments: int) -> List[Dict[str, Any]]:
        """Thu thập chính thống qua Facebook Graph API cho Fanpage."""
        all_comments = []
        url = f"https://graph.facebook.com/v19.0/{post_id}/comments"
        params = {
            "fields": "id,message,created_time,from{id,name,picture},like_count,comment_count,parent",
            "limit": 100,
            "access_token": self.access_token
        }

        while len(all_comments) < max_comments and url:
            try:
                resp = requests.get(url, params=params if url.startswith("https://graph.facebook.com") and "?" not in url else {}, timeout=15)
                if resp.status_code != 200:
                    logger.error(f"[Facebook Graph API Error] Status {resp.status_code}: {resp.text}")
                    break

                data = resp.json()
                items = data.get("data", [])
                if not items:
                    break

                all_comments.extend(items)
                logger.info(f"[Facebook Graph API] Đã thu thập {len(all_comments)}/{max_comments} bình luận...")

                paging = data.get("paging", {})
                url = paging.get("next")
                random_sleep(self.rate_limit_delay)

            except Exception as e:
                logger.error(f"[Facebook Graph API] Lỗi: {e}")
                break

        return all_comments

    def _fetch_via_mobile_web(self, post_id: str, original_url: str, max_comments: int) -> List[Dict[str, Any]]:
        """
        Thu thập qua mbasic/m.facebook.com khi không có Token (Yêu cầu Cookie Facebook).
        """
        all_comments = []
        if not self.cookie:
            logger.warning(
                "[Facebook] Cần cấu hình FACEBOOK_ACCESS_TOKEN hoặc FACEBOOK_COOKIE để cào Facebook "
                "do cơ chế chống bot nghiêm ngặt của Meta."
            )
            return []

        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
            "Cookie": self.cookie,
            "Accept-Language": "vi-VN,vi;q=0.9",
        })

        current_url = f"https://mbasic.facebook.com/{post_id}"

        while len(all_comments) < max_comments and current_url:
            try:
                resp = session.get(current_url, timeout=15)
                if resp.status_code != 200:
                    break

                soup = BeautifulSoup(resp.text, "lxml")
                comment_divs = soup.select("div[id^='composer'] ~ div div[id]")
                
                found_on_page = 0
                for c_div in comment_divs:
                    author_tag = c_div.select_one("h3 a")
                    text_div = c_div.select_one("div:nth-of-type(1)")
                    
                    if author_tag and text_div:
                        author_name = author_tag.get_text(strip=True)
                        comment_text = text_div.get_text(strip=True)
                        comment_id = c_div.get("id", "")
                        
                        all_comments.append({
                            "id": comment_id,
                            "message": comment_text,
                            "from": {"name": author_name, "id": author_tag.get("href", "")},
                            "created_time": None,
                            "_post_id": post_id,
                            "_post_url": original_url,
                        })
                        found_on_page += 1

                logger.info(f"[Facebook Mobile] Đã lấy được {len(all_comments)}/{max_comments} bình luận...")

                # Tìm link phân trang 'Xem thêm bình luận...'
                next_page_link = soup.select_one("div[id*='see_next'] a, a[href*='see_more_comments']")
                if next_page_link and next_page_link.get("href"):
                    href = next_page_link.get("href")
                    current_url = f"https://mbasic.facebook.com{href}" if href.startswith("/") else href
                    random_sleep(self.rate_limit_delay)
                else:
                    break

            except Exception as e:
                logger.error(f"[Facebook Web] Lỗi cào web: {e}")
                break

        return all_comments

    def parse_comment_item(self, item: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        context = context or {}
        comment_id = str(item.get("id", ""))
        text = item.get("message", "")
        if not text:
            return None

        from_user = item.get("from", {})
        author_id = str(from_user.get("id", ""))
        author_name = from_user.get("name", "Facebook User")
        author_pic = from_user.get("picture", {}).get("data", {}).get("url", "")

        created_time_str = item.get("created_time")
        dt_obj = parse_iso_datetime(created_time_str)
        created_at_utc, created_at_vn, year = format_datetime_vn(dt_obj)

        post_id = item.get("_post_id") or context.get("post_id", "")
        post_url = item.get("_post_url") or context.get("post_url", f"https://facebook.com/{post_id}")

        parent_info = item.get("parent")
        parent_id = parent_info.get("id") if isinstance(parent_info, dict) else None

        return {
            "comment_id": f"fb_{comment_id}",
            "parent_id": parent_id,
            "platform": "facebook",
            "post_id": post_id,
            "post_url": post_url,
            "post_title": context.get("post_title", f"Facebook Post #{post_id}"),
            "author_id": author_id,
            "author_name": author_name,
            "author_avatar_url": author_pic,
            "comment_text": text,
            "cleaned_text": "",
            "created_at": created_at_utc,
            "created_at_vn": created_at_vn,
            "year": year,
            "likes_count": item.get("like_count", 0),
            "reply_count": item.get("comment_count", 0),
            "has_teencode": False,
            "detected_teencodes": [],
            "teencode_count": 0,
            "teencode_density": 0.0,
            "extra_metadata": {
                "permalink_url": item.get("permalink_url")
            },
            "_datetime_obj": dt_obj,
        }
