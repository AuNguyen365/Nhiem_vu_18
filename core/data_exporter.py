"""
Data Exporter: Exports crawled comments to CSV, JSONL, SQLite, and Excel.
Includes data summary, deduplication, and schema validation.
"""

import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
from utils.logger import logger
from config.settings import PROCESSED_DATA_DIR, RAW_DATA_DIR, OUTPUT_REPORT_DIR, COMMENT_SCHEMA

class DataExporter:
    def __init__(self, platform_name: str):
        self.platform = platform_name
        self.raw_dir = RAW_DATA_DIR / platform_name
        self.processed_dir = PROCESSED_DATA_DIR / platform_name
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def save_raw_json(self, raw_data: List[Dict[str, Any]], filename_prefix: str = "raw") -> Path:
        """Lưu toàn bộ payload thô chưa qua lọc để làm dữ liệu lưu trữ / audit."""
        file_path = self.raw_dir / f"{filename_prefix}_{self.platform}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(raw_data, f, ensure_ascii=False, indent=2)
        logger.info(f"Đã lưu [green]{len(raw_data)}[/green] bản ghi thô vào: {file_path}")
        return file_path

    def export_processed_data(
        self,
        comments: List[Dict[str, Any]],
        output_prefix: str = "comments_teencode",
        formats: Optional[List[str]] = None
    ) -> Dict[str, Path]:
        """
        Xuất dữ liệu đã lọc và chuẩn hóa ra nhiều định dạng: CSV, JSONL, SQLite, Excel.
        Hỗ trợ khử trùng lặp (deduplication) theo `comment_id`.
        """
        if not comments:
            logger.warning(f"Không có bình luận nào để xuất cho nền tảng {self.platform}!")
            return {}

        formats = formats or ["csv", "jsonl", "sqlite"]
        df = pd.DataFrame(comments)

        # Đảm bảo có đầy đủ các cột theo schema
        for col in COMMENT_SCHEMA:
            if col not in df.columns:
                df[col] = None

        # Khử trùng lặp theo comment_id nếu có
        if "comment_id" in df.columns and df["comment_id"].notna().any():
            initial_count = len(df)
            df = df.drop_duplicates(subset=["comment_id"])
            if len(df) < initial_count:
                logger.info(f"Đã loại bỏ {initial_count - len(df)} bình luận trùng lặp.")

        saved_files = {}

        # 1. Xuất CSV
        if "csv" in formats:
            csv_path = self.processed_dir / f"{output_prefix}_{self.platform}.csv"
            # Chuyển list hoặc dict sang chuỗi json để lưu vào CSV đẹp
            df_csv = df.copy()
            if "detected_teencodes" in df_csv.columns:
                df_csv["detected_teencodes"] = df_csv["detected_teencodes"].apply(
                    lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, (list, dict)) else str(x)
                )
            df_csv.to_csv(csv_path, index=False, encoding="utf-8-sig")
            saved_files["csv"] = csv_path
            logger.info(f"Xuất CSV thành công: [bold cyan]{csv_path}[/bold cyan] ({len(df)} dòng)")

        # 2. Xuất JSON Lines (Phổ biến cho NLP, Data Mining)
        if "jsonl" in formats:
            jsonl_path = self.processed_dir / f"{output_prefix}_{self.platform}.jsonl"
            with open(jsonl_path, "w", encoding="utf-8") as f:
                for record in df.to_dict(orient="records"):
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
            saved_files["jsonl"] = jsonl_path
            logger.info(f"Xuất JSONL thành công: [bold cyan]{jsonl_path}[/bold cyan]")

        # 3. Xuất SQLite Database (Dễ truy vấn SQL)
        if "sqlite" in formats:
            db_path = self.processed_dir / f"{self.platform}_comments.db"
            conn = sqlite3.connect(db_path)
            # Lưu mảng dưới dạng text
            df_sql = df.copy()
            for col in ["detected_teencodes", "extra_metadata"]:
                if col in df_sql.columns:
                    df_sql[col] = df_sql[col].apply(
                        lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, (list, dict)) else str(x)
                    )
            df_sql.to_sql("comments", conn, if_exists="replace", index=False)
            conn.close()
            saved_files["sqlite"] = db_path
            logger.info(f"Xuất SQLite DB thành công: [bold cyan]{db_path}[/bold cyan]")

        # 4. Xuất Excel nếu được yêu cầu
        if "excel" in formats or "xlsx" in formats:
            excel_path = self.processed_dir / f"{output_prefix}_{self.platform}.xlsx"
            df.to_excel(excel_path, index=False)
            saved_files["excel"] = excel_path
            logger.info(f"Xuất Excel thành công: [bold cyan]{excel_path}[/bold cyan]")

        return saved_files

    def generate_summary_report(self, comments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Tạo báo cáo thống kê nhanh về các bình luận thu thập được."""
        if not comments:
            return {"total_comments": 0}

        df = pd.DataFrame(comments)
        total = len(df)
        years_dist = df["year"].value_counts().to_dict() if "year" in df.columns else {}

        # Thống kê từ viết tắt phổ biến nhất
        all_teencodes = []
        for row in df.get("detected_teencodes", []):
            if isinstance(row, list):
                all_teencodes.extend(row)
            elif isinstance(row, str) and row.startswith("["):
                try:
                    all_teencodes.extend(json.loads(row))
                except Exception:
                    pass

        teencode_counts = pd.Series(all_teencodes).value_counts().to_dict() if all_teencodes else {}

        report = {
            "platform": self.platform,
            "total_crawled_comments": total,
            "years_distribution": years_dist,
            "top_teencodes_detected": dict(list(teencode_counts.items())[:15]),
            "avg_teencode_density": round(float(df["teencode_density"].mean()), 2) if "teencode_density" in df.columns else 0.0,
            "total_likes_sum": int(df["likes_count"].fillna(0).sum()) if "likes_count" in df.columns else 0,
        }

        # Lưu báo cáo JSON
        report_file = OUTPUT_REPORT_DIR / f"summary_report_{self.platform}.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        return report
