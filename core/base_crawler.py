"""
Abstract Base Crawler: Defines standard interface and pipeline for all social media crawlers.
Orchestrates fetching, 5-year filtering, teencode detection, and multi-format export.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from config.settings import TIME_FILTER_CONFIG, COMMENT_SCHEMA
from core.teencode_filter import TeencodeFilter
from core.data_exporter import DataExporter
from utils.logger import logger
from utils.helpers import is_within_last_n_years, clean_comment_text, random_sleep

class BaseCrawler(ABC):
    def __init__(
        self,
        platform_name: str,
        target_teencodes: Optional[List[str]] = None,
        max_years: int = 5,
        rate_limit_delay: float = 1.0,
    ):
        """
        Khởi tạo Crawler cơ sở.
        :param platform_name: Tên nền tảng (youtube, facebook, tiktok, shopee)
        :param target_teencodes: Danh sách từ viết tắt cần lọc (mặc định lấy theo teencode_dict)
        :param max_years: Số năm gần nhất cần thu thập (mặc định 5 năm)
        :param rate_limit_delay: Thời gian nghỉ giữa các request
        """
        self.platform_name = platform_name
        self.max_years = max_years
        self.rate_limit_delay = rate_limit_delay
        
        # Khởi tạo bộ lọc teencode
        self.teencode_filter = TeencodeFilter(target_words_only=target_teencodes)
        # Khởi tạo bộ xuất dữ liệu
        self.exporter = DataExporter(platform_name=platform_name)

    @abstractmethod
    def fetch_raw_comments(self, target_input: str, max_comments: int = 1000) -> List[Dict[str, Any]]:
        """
        Phương thức trừu tượng: Thu thập dữ liệu bình luận thô từ nền tảng.
        :param target_input: URL bài viết/video/sản phẩm hoặc ID/từ khóa
        :param max_comments: Số lượng bình luận tối đa cần cào
        :return: Danh sách dict thô từ API/Scraper
        """
        pass

    @abstractmethod
    def parse_comment_item(self, item: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Phương thức trừu tượng: Trích xuất và ánh xạ các trường từ dữ liệu thô sang COMMENT_SCHEMA.
        :param item: 1 bản ghi bình luận thô
        :param context: Thông tin bổ sung (tiêu đề video, url post,...)
        :return: Dict đã chuẩn hóa các trường thông tin hoặc None nếu không hợp lệ
        """
        pass

    def filter_and_enrich(self, raw_comments: List[Dict[str, Any]], context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Pipeline xử lý:
        1. Phân tích trích xuất trường thông tin
        2. Kiểm tra mốc thời gian 5 năm
        3. Phân tích bộ lọc từ viết tắt (ngta, m, cx, ...)
        4. Làm giàu dữ liệu với độ dài, mật độ teencode, thời gian Việt Nam
        """
        processed_comments = []
        total_raw = len(raw_comments)
        passed_time = 0
        passed_teencode = 0

        logger.info(f"Bắt đầu xử lý [bold cyan]{total_raw}[/bold cyan] bình luận thô từ [bold yellow]{self.platform_name}[/bold yellow]...")

        for item in raw_comments:
            parsed = self.parse_comment_item(item, context=context)
            if not parsed:
                continue

            # 1. Lọc theo mốc thời gian 5 năm gần nhất
            created_dt = parsed.get("_datetime_obj")
            if created_dt and not is_within_last_n_years(created_dt, years=self.max_years):
                continue
            passed_time += 1

            # 2. Làm sạch nội dung & Phân tích từ viết tắt teencode
            comment_text = parsed.get("comment_text", "")
            cleaned_text = clean_comment_text(comment_text)
            parsed["cleaned_text"] = cleaned_text

            teencode_analysis = self.teencode_filter.analyze_text(cleaned_text)

            # Chỉ giữ lại bình luận CÓ từ viết tắt theo yêu cầu bài toán
            if not teencode_analysis["has_teencode"]:
                continue

            passed_teencode += 1

            # 3. Gán kết quả phân tích teencode vào bản ghi
            parsed["has_teencode"] = True
            parsed["detected_teencodes"] = teencode_analysis["detected_teencodes"]
            parsed["teencode_count"] = teencode_analysis["teencode_count"]
            parsed["teencode_density"] = teencode_analysis["teencode_density"]

            # Xóa trường tạm thời dùng nội bộ
            parsed.pop("_datetime_obj", None)

            processed_comments.append(parsed)

        logger.info(
            f"Kết quả lọc: Thô={total_raw} | "
            f"Trong 5 năm={passed_time} | "
            f"[bold green]Chứa từ viết tắt teencode={passed_teencode}[/bold green]"
        )

        return processed_comments

    def run(
        self,
        target_input: str,
        max_comments: int = 1000,
        export_formats: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Hàm thực thi toàn diện (Orchestrator):
        Thu thập -> Làm sạch & Lọc -> Lưu file thô -> Xuất file thành phẩm (CSV/JSONL/SQLite) -> Tạo báo cáo
        """
        logger.info(f"==> Bắt đầu cào dữ liệu [{self.platform_name}] cho mục tiêu: {target_input}")

        # 1. Thu thập dữ liệu thô
        raw_items = self.fetch_raw_comments(target_input, max_comments=max_comments)
        if not raw_items:
            logger.warning(f"Không thu thập được dữ liệu thô nào từ {target_input}")
            return []

        # 2. Lưu backup dữ liệu thô
        self.exporter.save_raw_json(raw_items, filename_prefix="raw_crawled")

        # 3. Lọc 5 năm + Lọc từ viết tắt
        processed = self.filter_and_enrich(raw_items, context=context)

        # 4. Xuất dữ liệu đa định dạng
        formats = export_formats or ["csv", "jsonl", "sqlite"]
        saved_paths = self.exporter.export_processed_data(processed, formats=formats)

        # 5. Tạo báo cáo tóm tắt
        summary = self.exporter.generate_summary_report(processed)
        logger.info(f"Báo cáo hoàn thành:\n{summary}")

        return processed
