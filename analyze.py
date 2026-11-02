"""
Exploratory Data Analysis & Visualization Script for Nhiệm vụ 18.
Phân tích thống kê và vẽ biểu đồ trực quan hóa dữ liệu bình luận chứa từ viết tắt.
Hỗ trợ phân tích đơn lẻ 1 nền tảng hoặc so sánh đối chứng giữa 2 nền tảng (TikTok vs YouTube).
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

def extract_teencode_series(df: pd.DataFrame) -> pd.Series:
    """Trích xuất tất cả từ viết tắt trong DataFrame thành pandas Series."""
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
    return pd.Series(all_words) if all_words else pd.Series(dtype=str)

def analyze_dataset(csv_path: str):
    """Phân tích dữ liệu bình luận từ 1 file CSV."""
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
    print(f"Mật độ teencode TB: {df['teencode_density'].mean():.2f}%" if "teencode_density" in df.columns else "")
    print(f"Danh sách trường: {', '.join(df.columns.tolist())}\n")

    # 1. Phân bố theo năm
    if "year" in df.columns:
        print("--- Phân bố số lượng bình luận theo năm (5 năm gần nhất) ---")
        year_counts = df["year"].value_counts().sort_index()
        for yr, cnt in year_counts.items():
            print(f"  Năm {yr}: {cnt} comments ({cnt/len(df)*100:.1f}%)")
        print()

    # 2. Thống kê tần suất từ viết tắt
    word_series = extract_teencode_series(df)
    if not word_series.empty:
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
    if not word_series.empty:
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

def compare_two_datasets(csv1: str, csv2: str):
    """Phân tích so sánh đối chứng giữa 2 nền tảng (ví dụ: YouTube vs TikTok)."""
    p1 = Path(csv1)
    p2 = Path(csv2)
    if not p1.exists() or not p2.exists():
        logger.error(f"Một trong 2 file không tồn tại: {csv1} hoặc {csv2}")
        return

    df1 = pd.read_csv(p1)
    df2 = pd.read_csv(p2)

    name1 = p1.stem.replace("comments_teencode_", "").capitalize()
    name2 = p2.stem.replace("comments_teencode_", "").capitalize()

    print("=" * 65)
    print(f"BÁO CÁO SO SÁNH ĐỐI CHỨNG: {name1.upper()} vs {name2.upper()}")
    print("=" * 65)
    print(f"Tổng bình luận: {name1} = {len(df1)} | {name2} = {len(df2)}")
    den1 = df1['teencode_density'].mean() if 'teencode_density' in df1.columns else 0.0
    den2 = df2['teencode_density'].mean() if 'teencode_density' in df2.columns else 0.0
    print(f"Mật độ từ viết tắt TB: {name1} = {den1:.2f}% | {name2} = {den2:.2f}%\n")

    w1 = extract_teencode_series(df1)
    w2 = extract_teencode_series(df2)

    OUTPUT_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    if not w1.empty:
        t1 = w1.value_counts().head(10)
        sns.barplot(x=t1.values, y=t1.index, ax=axes[0], hue=t1.index, palette="mako", legend=False)
        axes[0].set_title(f"Top 10 Từ Viết Tắt Trên {name1}", fontsize=12, fontweight="bold")
        axes[0].set_xlabel("Số lần")

    if not w2.empty:
        t2 = w2.value_counts().head(10)
        sns.barplot(x=t2.values, y=t2.index, ax=axes[1], hue=t2.index, palette="rocket", legend=False)
        axes[1].set_title(f"Top 10 Từ Viết Tắt Trên {name2}", fontsize=12, fontweight="bold")
        axes[1].set_xlabel("Số lần")

    plt.tight_layout()
    comp_output = OUTPUT_REPORT_DIR / f"comparative_{name1.lower()}_vs_{name2.lower()}.png"
    plt.savefig(comp_output, dpi=300)
    plt.close()
    logger.info(f"Đã xuất biểu đồ so sánh: [bold green]{comp_output}[/bold green]")
    print(f"\n[Xong] Biểu đồ so sánh đã lưu tại: {comp_output}")

if __name__ == "__main__":
    if len(sys.argv) == 3:
        # Chế độ so sánh 2 file
        compare_two_datasets(sys.argv[1], sys.argv[2])
    elif len(sys.argv) == 2:
        analyze_dataset(sys.argv[1])
    else:
        csv_candidates = list(PROCESSED_DATA_DIR.glob("**/*.csv"))
        if csv_candidates:
            analyze_dataset(str(csv_candidates[0]))
        else:
            print("Chưa có file CSV dữ liệu. Hãy chạy `python main.py --demo` trước để tạo dữ liệu.")
