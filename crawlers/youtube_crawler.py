"""
YouTube Comment Crawler.
Supports 2 robust modes:
1. YouTube Data API v3 (Official API, high speed, structured)
2. Fallback Web Scraper via YouTube internal innertube API (No API key required)
"""

import os
import re
import json
from typing import List, Dict, Any, Optional
import requests
from core.base_crawler import BaseCrawler
from utils.logger import logger
from utils.helpers import parse_iso_datetime, format_datetime_vn, random_sleep

class YouTubeCrawler(BaseCrawler):
    def __init__(
        self,
        api_key: Optional[str] = None,
        target_teencodes: Optional[List[str]] = None,
        max_years: int = 5
    ):
        super().__init__(
            platform_name="youtube",
            target_teencodes=target_teencodes,
            max_years=max_years,
            rate_limit_delay=0.5
        )
        # Lấy API key từ đối số hoặc biến môi trường
        self.api_key = api_key or os.getenv("YOUTUBE_API_KEY")

    def extract_video_id(self, url_or_id: str) -> str:
        """Trích xuất Video ID từ link YouTube hoặc chuỗi ID."""
        url_or_id = url_or_id.strip()
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'youtu\.be\/([0-9A-Za-z_-]{11})',
            r'youtube\.com\/shorts\/([0-9A-Za-z_-]{11})'
        ]
        for pattern in patterns:
            match = re.search(pattern, url_or_id)
            if match:
                return match.group(1)
        if len(url_or_id) == 11:
            return url_or_id
        return url_or_id

    def fetch_raw_comments(self, target_input: str, max_comments: int = 1000) -> List[Dict[str, Any]]:
        video_id = self.extract_video_id(target_input)
        logger.info(f"[YouTube] Đang thu thập bình luận cho Video ID: [bold]{video_id}[/bold]")

        if self.api_key:
            return self._fetch_via_official_api(video_id, max_comments)
        else:
            logger.info("[YouTube] Không phát hiện API Key, chuyển sang chế độ Scraper Innertube công khai...")
            return self._fetch_via_innertube(video_id, max_comments)

    def _fetch_via_official_api(self, video_id: str, max_comments: int) -> List[Dict[str, Any]]:
        """Thu thập qua YouTube Data API v3 commentThreads."""
        url = "https://www.googleapis.com/youtube/v3/commentThreads"
        all_comments = []
        page_token = None

        while len(all_comments) < max_comments:
            params = {
                "part": "snippet,replies",
                "videoId": video_id,
                "maxResults": min(100, max_comments - len(all_comments)),
                "textFormat": "plainText",
                "key": self.api_key
            }
            if page_token:
                params["pageToken"] = page_token

            try:
                resp = requests.get(url, params=params, timeout=15)
                if resp.status_code != 200:
                    logger.error(f"[YouTube API Error] Status {resp.status_code}: {resp.text}")
                    break

                data = resp.json()
                items = data.get("items", [])
                if not items:
                    break

                for item in items:
                    all_comments.append(item)
                    # Nếu có replies con đi kèm
                    replies = item.get("replies", {}).get("comments", [])
                    for rep in replies:
                        rep["_is_reply"] = True
                        rep["_parent_id"] = item.get("id")
                        all_comments.append(rep)

                page_token = data.get("nextPageToken")
                logger.info(f"[YouTube API] Đã lấy {len(all_comments)}/{max_comments} bình luận...")
                if not page_token:
                    break

                random_sleep(self.rate_limit_delay)

            except Exception as e:
                logger.error(f"[YouTube API] Lỗi request: {e}")
                break

        return all_comments

    def _fetch_via_innertube(self, video_id: str, max_comments: int) -> List[Dict[str, Any]]:
        """
        Fallback Scraper: Sử dụng endpoint API nội bộ YouTubeInnertube
        Không yêu cầu API key, hỗ trợ cào số lượng lớn bình luận công khai.
        """
        all_comments = []
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
        })

        try:
            # Bước 1: Tải HTML trang video để trích xuất API Key và Continuation Token nội bộ
            video_url = f"https://www.youtube.com/watch?v=k_79q8bE48g" if not video_id else f"https://www.youtube.com/watch?v={video_id}"
            res = session.get(video_url, timeout=15)
            html = res.text

            # Trích xuất INNERTUBE_API_KEY
            key_match = re.search(r'"INNERTUBE_API_KEY":\s*"([a-zA-Z0-9_-]+)"', html)
            if not key_match:
                logger.warning("[YouTube Scraper] Không thể trích xuất token nội bộ từ HTML. Hãy cung cấp API Key chính thức để thu thập tối ưu.")
                return []

            inner_api_key = key_match.group(1)

            # Trích xuất continuation token đầu tiên cho bình luận
            token_match = re.search(r'"continuationCommand":\{"token":"([^"]+)"', html)
            if not token_match:
                token_match = re.search(r'"token":"([a-zA-Z0-9_%-]+)"', html)

            if not token_match:
                logger.warning("[YouTube Scraper] Video có thể đã tắt tính năng bình luận hoặc không tìm thấy token.")
                return []

            continuation_token = token_match.group(1)
            api_endpoint = f"https://www.youtube.com/youtubei/v1/next?key={inner_api_key}"

            while len(all_comments) < max_comments and continuation_token:
                payload = {
                    "context": {
                        "client": {
                            "clientName": "WEB",
                            "clientVersion": "2.20240417.01.00",
                            "hl": "vi",
                            "gl": "VN"
                        }
                    },
                    "continuation": continuation_token
                }

                r = session.post(api_endpoint, json=payload, timeout=15)
                if r.status_code != 200:
                    break

                res_json = r.json()
                
                # Trích xuất comment items từ payload JSON phức tạp của YouTube
                items, next_token = self._parse_innertube_response(res_json)
                if not items:
                    break

                all_comments.extend(items)
                continuation_token = next_token
                logger.info(f"[YouTube Scraper] Đã cào được {len(all_comments)}/{max_comments} bình luận...")

                random_sleep(self.rate_limit_delay)

        except Exception as e:
            logger.error(f"[YouTube Scraper] Gặp lỗi: {e}")

        return all_comments

    def _parse_innertube_response(self, data: Dict[str, Any]) -> (List[Dict[str, Any]], Optional[str]):
        """Bóc tách các comment thread từ JSON trả về của Innertube."""
        comments = []
        next_token = None

        def search_actions(obj):
            nonlocal next_token
            if isinstance(obj, dict):
                if "commentRenderer" in obj:
                    comments.append(obj["commentRenderer"])
                if "continuationCommand" in obj:
                    next_token = obj["continuationCommand"].get("token")
                for k, v in obj.items():
                    search_actions(v)
            elif isinstance(obj, list):
                for item in obj:
                    search_actions(item)

        search_actions(data)
        return comments, next_token

    def parse_comment_item(self, item: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Chuẩn hóa dữ liệu bình luận YouTube sang COMMENT_SCHEMA."""
        context = context or {}
        post_url = context.get("post_url", "")
        post_title = context.get("post_title", "")
        video_id = context.get("video_id", "")

        # Trường hợp 1: Dữ liệu từ YouTube Data API v3
        if "snippet" in item and ("topLevelComment" in item["snippet"] or "textDisplay" in item["snippet"]):
            if "topLevelComment" in item["snippet"]:
                c_data = item["snippet"]["topLevelComment"]["snippet"]
                comment_id = item["snippet"]["topLevelComment"]["id"]
                parent_id = None
                reply_count = item["snippet"].get("totalReplyCount", 0)
            else:
                c_data = item["snippet"]
                comment_id = item.get("id")
                parent_id = item.get("_parent_id")
                reply_count = 0

            text = c_data.get("textDisplay", "") or c_data.get("textOriginal", "")
            author_name = c_data.get("authorDisplayName", "Anonymous")
            author_id = c_data.get("authorChannelId", {}).get("value", "")
            author_avatar = c_data.get("authorProfileImageUrl", "")
            likes = c_data.get("likeCount", 0)
            published_str = c_data.get("publishedAt", "")
            dt_obj = parse_iso_datetime(published_str)
            created_at_utc, created_at_vn, year = format_datetime_vn(dt_obj)

            return {
                "comment_id": comment_id,
                "parent_id": parent_id,
                "platform": "youtube",
                "post_id": video_id or c_data.get("videoId", ""),
                "post_url": post_url or f"https://www.youtube.com/watch?v={video_id}",
                "post_title": post_title,
                "author_id": author_id,
                "author_name": author_name,
                "author_avatar_url": author_avatar,
                "comment_text": text,
                "cleaned_text": "",
                "created_at": created_at_utc,
                "created_at_vn": created_at_vn,
                "year": year,
                "likes_count": likes,
                "reply_count": reply_count,
                "has_teencode": False,
                "detected_teencodes": [],
                "teencode_count": 0,
                "teencode_density": 0.0,
                "extra_metadata": {
                    "viewer_rating": c_data.get("viewerRating"),
                    "can_rate": c_data.get("canRate"),
                    "updated_at": c_data.get("updatedAt")
                },
                "_datetime_obj": dt_obj,
            }

        # Trường hợp 2: Dữ liệu từ Innertube Renderer
        if "commentId" in item or "contentText" in item:
            comment_id = item.get("commentId", "")
            text_runs = item.get("contentText", {}).get("runs", [])
            text = "".join([r.get("text", "") for r in text_runs])
            author_name = item.get("authorText", {}).get("simpleText", "Anonymous")
            author_id = item.get("authorEndpoint", {}).get("browseEndpoint", {}).get("browseId", "")
            avatars = item.get("authorThumbnail", {}).get("thumbnails", [])
            author_avatar = avatars[-1].get("url") if avatars else ""
            likes_text = item.get("voteCount", {}).get("simpleText", "0")
            
            # Xử lý text like (vd: "1,2 N", "350")
            likes = 0
            if likes_text.isdigit():
                likes = int(likes_text)

            published_time_text = item.get("publishedTimeText", {}).get("runs", [{}])[0].get("text", "")
            # Ước lượng datetime
            dt_obj = parse_iso_datetime(published_time_text)
            created_at_utc, created_at_vn, year = format_datetime_vn(dt_obj)

            return {
                "comment_id": comment_id,
                "parent_id": None,
                "platform": "youtube",
                "post_id": video_id,
                "post_url": post_url or f"https://www.youtube.com/watch?v={video_id}",
                "post_title": post_title,
                "author_id": author_id,
                "author_name": author_name,
                "author_avatar_url": author_avatar,
                "comment_text": text,
                "cleaned_text": "",
                "created_at": created_at_utc,
                "created_at_vn": created_at_vn,
                "year": year,
                "likes_count": likes,
                "reply_count": 0,
                "has_teencode": False,
                "detected_teencodes": [],
                "teencode_count": 0,
                "teencode_density": 0.0,
                "extra_metadata": {
                    "published_relative": published_time_text
                },
                "_datetime_obj": dt_obj,
            }

        return None
