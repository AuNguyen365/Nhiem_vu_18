"""
Shopee Product Reviews & Comments Crawler.
Collects customer comments from Shopee's public ratings API.
Extremely rich in Vietnamese teencode & abbreviations (đc, k, mik, mn, cx, shop, sp, thik...).
"""

import re
import json
from typing import List, Dict, Any, Optional, Tuple
import requests
from core.base_crawler import BaseCrawler
from utils.logger import logger
from utils.helpers import parse_iso_datetime, format_datetime_vn, random_sleep

class ShopeeCrawler(BaseCrawler):
    def __init__(
        self,
        target_teencodes: Optional[List[str]] = None,
        max_years: int = 5
    ):
        super().__init__(
            platform_name="shopee",
            target_teencodes=target_teencodes,
            max_years=max_years,
            rate_limit_delay=1.0
        )

    def extract_item_and_shop_id(self, input_str: str) -> Tuple[Optional[int], Optional[int]]:
        """
        Trích xuất shopid và itemid từ URL sản phẩm Shopee hoặc chuỗi shopid_itemid:
        Ví dụ: https://shopee.vn/product-name-i.123456.7891011
        hoặc: 123456_7891011
        """
        input_str = input_str.strip()

        # Định dạng URL: i.SHOP_ID.ITEM_ID
        match = re.search(r'i\.(\d+)\.(\d+)', input_str)
        if match:
            return int(match.group(1)), int(match.group(2))

        # Định dạng URL tham số: sp_atk=...&shopid=...&itemid=...
        shop_match = re.search(r'shopid=(\d+)', input_str)
        item_match = re.search(r'itemid=(\d+)', input_str)
        if shop_match and item_match:
            return int(shop_match.group(1)), int(item_match.group(1))

        # Định dạng phân cách dấu gạch dưới: SHOPID_ITEMID
        if "_" in input_str:
            parts = input_str.split("_")
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                return int(parts[0]), int(parts[1])

        return None, None

    def fetch_raw_comments(self, target_input: str, max_comments: int = 1000) -> List[Dict[str, Any]]:
        shop_id, item_id = self.extract_item_and_shop_id(target_input)
        if not shop_id or not item_id:
            logger.error(
                f"[Shopee] Không phân tích được shop_id và item_id từ: '{target_input}'. "
                f"Định dạng hợp lệ: URL Shopee (vd: https://shopee.vn/ao-thun-i.123.456) hoặc cú pháp: shopid_itemid"
            )
            return []

        logger.info(f"[Shopee] Thu thập bình luận đánh giá cho ShopID={shop_id}, ItemID={item_id}")

        all_ratings = []
        limit = 50
        offset = 0
        api_url = "https://shopee.vn/api/v2/item/get_ratings"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Referer": f"https://shopee.vn/product/{shop_id}/{item_id}",
            "Accept": "application/json",
            "X-Shopee-Language": "vi",
        }

        while len(all_ratings) < max_comments:
            params = {
                "itemid": item_id,
                "shopid": shop_id,
                "offset": offset,
                "limit": limit,
                "type": 0,    # 0 = Tất cả đánh giá
                "filter": 1,  # 1 = Đánh giá có kèm nhận xét text
                "flag": 1
            }

            try:
                resp = requests.get(api_url, headers=headers, params=params, timeout=15)
                if resp.status_code != 200:
                    logger.error(f"[Shopee API Error] Status {resp.status_code}: {resp.text[:200]}")
                    break

                data = resp.json()
                data_obj = data.get("data", {})
                ratings = data_obj.get("ratings", []) if isinstance(data_obj, dict) else []

                if not ratings:
                    logger.info("[Shopee] Đã hết dữ liệu bình luận từ sản phẩm.")
                    break

                for r in ratings:
                    r["_product_url"] = f"https://shopee.vn/product/{shop_id}/{item_id}"
                    r["_shop_id"] = shop_id
                    r["_item_id"] = item_id
                    all_ratings.append(r)

                offset += len(ratings)
                logger.info(f"[Shopee API] Đã thu thập {len(all_ratings)}/{max_comments} đánh giá...")

                if len(ratings) < limit:
                    break

                random_sleep(self.rate_limit_delay)

            except Exception as e:
                logger.error(f"[Shopee API] Lỗi ngoại lệ: {e}")
                break

        return all_ratings

    def parse_comment_item(self, item: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Chuyển đổi bản ghi đánh giá Shopee sang COMMENT_SCHEMA."""
        context = context or {}
        comment_id = str(item.get("cmtid", ""))
        author_id = str(item.get("userid", ""))
        author_name = item.get("author_username", "") or "Shopee Customer"
        author_avatar = item.get("author_portrait", "")
        if author_avatar and not author_avatar.startswith("http"):
            author_avatar = f"https://cf.shopee.vn/file/{author_avatar}"

        text = item.get("comment", "")
        if not text:
            return None

        # Thời gian dạng timestamp epoch seconds
        ctime = item.get("ctime", 0)
        dt_obj = parse_iso_datetime(ctime)
        created_at_utc, created_at_vn, year = format_datetime_vn(dt_obj)

        shop_id = item.get("_shop_id") or context.get("shop_id")
        item_id = item.get("_item_id") or context.get("item_id")
        post_url = item.get("_product_url") or context.get("post_url", f"https://shopee.vn/product/{shop_id}/{item_id}")

        return {
            "comment_id": f"shopee_{comment_id}",
            "parent_id": None,
            "platform": "shopee",
            "post_id": f"{shop_id}_{item_id}",
            "post_url": post_url,
            "post_title": context.get("post_title", f"Sản phẩm Shopee #{item_id}"),
            "author_id": author_id,
            "author_name": author_name,
            "author_avatar_url": author_avatar,
            "comment_text": text,
            "cleaned_text": "",
            "created_at": created_at_utc,
            "created_at_vn": created_at_vn,
            "year": year,
            "likes_count": item.get("like_count", 0),
            "reply_count": 1 if item.get("ItemRatingReply") else 0,
            "has_teencode": False,
            "detected_teencodes": [],
            "teencode_count": 0,
            "teencode_density": 0.0,
            "extra_metadata": {
                "rating_star": item.get("rating_star"),
                "product_variation": item.get("model_name"),
                "has_images": bool(item.get("images")),
                "has_videos": bool(item.get("videos")),
                "anonymous": item.get("anonymous"),
            },
            "_datetime_obj": dt_obj,
        }
