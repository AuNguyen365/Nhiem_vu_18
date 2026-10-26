"""
Exploratory Data Analysis & Visualization Script for Nhiệm vụ 18.
Phân tích thống kê và vẽ biểu đồ trực quan hóa dữ liệu bình luận chứa từ viết tắt.
Xuất biểu đồ ra thư mục reports/.
"""

import sys
import os

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import json
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from config.settings import PROCESSED_DATA_DIR, OUTPUT_REPORT_DIR
from utils.logger import logger

def analyze_dataset(csv_path: str):
    file_path = Path(csv_path)
    if not file_path.exists():
        logger.error(f"File không tồn tại: {csv_path}")
        return

    logger.info(f"Đang đọc dữ liệu từ: [bold cyan]{file_path}[/bold cyan]")
    df = pd.read_csv(file_path)

    if df.empty:
        logger.warning("File rỗng!")
        return

    print("=" * 60)
    print(f"BÁO CÁO PHÂN TÍCH DỮ LIỆU BÌNH LUẬN TỪ VIẾT TẮT")
    print("=" * 60)
    print(f"Tổng số bình luận: {len(df)}")
    print(f"Số trường thông tin: {len(df.columns)}")
    print(f"Danh sách trường: {', '.join(df.columns.tolist())}\n")

    # 1. Phân bố theo năm
    if "year" in df.columns:
        print("--- Phân bố số lượng bình luận theo năm (5 năm gần nhất) ---")
        year_counts = df["year"].value_counts().sort_index()
        for yr, cnt in year_counts.items():
            print(f"  Năm {yr}: {cnt} comments ({cnt/len(df)*100:.1f}%)")
        print()

    # 2. Thống kê tần suất từ viết tắt
    all_words = []
    if "detected_teencodes" in df.columns:
        for val in df["detected_teencodes"].dropna():
            if isinstance(val, str) and val.startswith("["):
                try:
                    words = json.loads(val)
                    all_words.extend(words)
                except Exception:
                    pass
            elif isinstance(val, list):
                all_words.extend(val)

    if all_words:
        word_series = pd.Series(all_words)
        print("--- Top 10 từ viết tắt / teencode xuất hiện nhiều nhất ---")
        top_10 = word_series.value_counts().head(10)
        for w, c in top_10.items():
            print(f"  Từ '{w}': {c} lần xuất hiện")
        print()

    # 3. Vẽ biểu đồ trực quan hóa
    OUTPUT_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Biểu đồ 1: Top từ viết tắt
    if all_words:
        top_15 = word_series.value_counts().head(12)
        sns.barplot(x=top_15.values, y=top_15.index, ax=axes[0], hue=top_15.index, palette="viridis", legend=False)
        axes[0].set_title("Top 12 Từ Viết Tắt Xuất Hiện Nhiều Nhất", fontsize=12, fontweight="bold")
        axes[0].set_xlabel("Số lần xuất hiện")
        axes[0].set_ylabel("Từ viết tắt")

    # Biểu đồ 2: Phân bố theo năm
    if "year" in df.columns:
        year_data = df["year"].value_counts().sort_index()
        year_labels = year_data.index.astype(str)
        sns.barplot(x=year_labels, y=year_data.values, ax=axes[1], hue=year_labels, palette="crest", legend=False)
        axes[1].set_title("Số Lượng Bình Luận Thu Thập Theo Năm (5 Năm)", fontsize=12, fontweight="bold")
        axes[1].set_xlabel("Năm")
        axes[1].set_ylabel("Số lượng comment")

    plt.tight_layout()
    chart_output = OUTPUT_REPORT_DIR / f"analysis_charts_{file_path.stem}.png"
    plt.savefig(chart_output, dpi=300)
    plt.close()

    logger.info(f"Đã vẽ và lưu biểu đồ phân tích trực quan tại: [bold green]{chart_output}[/bold green]")
    print(f"\n[Xong] Biểu đồ đã lưu tại: {chart_output}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        # Tự động tìm file CSV đầu tiên trong thư mục processed
        csv_candidates = list(PROCESSED_DATA_DIR.glob("**/*.csv"))
        if csv_candidates:
            csv_file = str(csv_candidates[0])
        else:
            print("Chưa có file CSV dữ liệu. Hãy chạy `python main.py --demo` trước để tạo dữ liệu.")
            sys.exit(0)

    analyze_dataset(csv_file)
