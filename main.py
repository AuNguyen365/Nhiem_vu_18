"""
Main CLI Controller for Social Media Comment Crawler Framework (Nhiệm vụ 18).
Cho phép nhóm chọn 1 nền tảng bất kỳ để cào comment trong 5 năm gần nhất và lọc từ viết tắt (ngta, m, cx...).
"""

import sys
import os

# Fix UTF-8 encoding on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import argparse
from typing import List
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from crawlers import YouTubeCrawler, TikTokCrawler, ShopeeCrawler, FacebookCrawler, ThreadsCrawler
from utils.logger import logger
from config.settings import TIME_FILTER_CONFIG

console = Console(force_terminal=True, legacy_windows=False)

def display_welcome_banner():
    """Hiển thị banner thông tin nhiệm vụ."""
    banner_text = (
        "[bold cyan]HỆ THỐNG THU THẬP BÌNH LUẬN MẠNG XÃ HỘI (NHIỆM VỤ 18)[/bold cyan]\n"
        "[yellow]Mục tiêu:[/yellow] Lọc comment chứa từ viết tắt ([bold red]ngta, m, cx, k, mik, mn, dc...[/bold red])\n"
        "[green]Phạm vi thời gian:[/green] 5 năm gần nhất ("
        f"{TIME_FILTER_CONFIG['start_year']} -> {TIME_FILTER_CONFIG['end_year']})\n"
        "[magenta]Hỗ trợ các nền tảng:[/magenta] YouTube | TikTok | Shopee | Facebook | Threads\n"
        "[white]Xuất dữ liệu:[/white] CSV (UTF-8 with BOM), JSON Lines, SQLite Database, Excel"
    )
    console.print(Panel(banner_text, expand=False, border_style="blue"))

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Bộ khung thu thập comment và lọc từ viết tắt teencode mạng xã hội (5 năm gần nhất)"
    )
    parser.add_argument(
        "-p", "--platform",
        type=str,
        choices=["youtube", "tiktok", "shopee", "facebook", "threads"],
        default="youtube",
        help="Chọn 1 nền tảng để thu thập (Mỗi nhóm chọn 1 nền tảng)"
    )
    parser.add_argument(
        "-i", "--input",
        type=str,
        help="URL hoặc ID của bài viết, video, sản phẩm cần cào bình luận"
    )
    parser.add_argument(
        "-m", "--max",
        type=int,
        default=500,
        help="Số lượng bình luận tối đa cần cào (Mặc định: 500)"
    )
    parser.add_argument(
        "-y", "--years",
        type=int,
        default=5,
        help="Thời gian giới hạn tính bằng năm (Mặc định: 5 năm gần nhất)"
    )
    parser.add_argument(
        "-w", "--words",
        type=str,
        default="ngta,m,cx,k,ko,dc,đc,mik,mn,bt,v,j,z,h,vs,ntn,nma,t",
        help="Danh sách các từ viết tắt cần lọc, ngăn cách bằng dấu phẩy (vd: ngta,m,cx)"
    )
    parser.add_argument(
        "-f", "--formats",
        type=str,
        default="csv,jsonl,sqlite",
        help="Các định dạng file xuất ra, ngăn cách bằng dấu phẩy (csv,jsonl,sqlite,excel)"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Chạy chế độ mô phỏng dữ liệu mẫu để kiểm thử nhanh toàn bộ pipeline"
    )
    return parser.parse_args()

def run_demo_simulation(target_words: List[str]):
    """Chạy mô phỏng dữ liệu với tập dữ liệu mẫu chuẩn thực tế có lẫn teencode và không teencode."""
    from datetime import datetime, timezone, timedelta
    from core.teencode_filter import TeencodeFilter
    from core.data_exporter import DataExporter
    from utils.helpers import format_datetime_vn

    console.print("\n[bold green]>>> ĐANG KHỞI CHẠY CHẾ ĐỘ MÔ PHỎNG DỮ LIỆU TEST (DEMO MODE)...[/bold green]")

    now = datetime.now(timezone.utc)
    # Tạo 10 comment mẫu đại diện từ các năm từ 2021 đến 2026
    sample_raw_comments = [
        {
            "id": "c1",
            "author": "Nguyen Van A",
            "text": "Video hay quá ngta nói đúng ghê á m ơi, cx thấy chuẩn luôn",
            "time": (now - timedelta(days=30)).isoformat(),
            "likes": 120
        },
        {
            "id": "c2",
            "author": "Trần Thị B",
            "text": "Nội dung rất bổ ích và mang lại nhiều giá trị tích cực.",
            "time": (now - timedelta(days=120)).isoformat(),
            "likes": 45
        },
        {
            "id": "c3",
            "author": "Minh Anh",
            "text": "k bt ngta lm ntn mà đỉnh v, mik cx muốn thử ghê á",
            "time": (now - timedelta(days=400)).isoformat(),
            "likes": 88
        },
        {
            "id": "c4",
            "author": "Quốc Bảo",
            "text": "dc của nó đấy mn ơi, xem mà cười xỉu vs bà này",
            "time": (now - timedelta(days=800)).isoformat(),
            "likes": 310
        },
        {
            "id": "c5",
            "author": "Old User (Ngoài 5 năm)",
            "text": "ngta comment từ lâu lắm rồi m ơi",
            "time": (now - timedelta(days=2200)).isoformat(),  # ~6 năm trước (sẽ bị lọc bỏ)
            "likes": 10
        },
        {
            "id": "c6",
            "author": "Linh Dan",
            "text": "Ủa z là xong r đó hả mn? Nhanh v",
            "time": (now - timedelta(days=50)).isoformat(),
            "likes": 15
        },
        {
            "id": "c7",
            "author": "Thanh Tùng",
            "text": "nhma t thấy cx bth thui k có j đặc sắc",
            "time": (now - timedelta(days=600)).isoformat(),
            "likes": 5
        }
    ]

    filter_engine = TeencodeFilter(target_words_only=target_words)
    exporter = DataExporter(platform_name="demo_platform")

    processed = []
    for item in sample_raw_comments:
        from utils.helpers import parse_iso_datetime, is_within_last_n_years
        dt = parse_iso_datetime(item["time"])
        if not is_within_last_n_years(dt, years=5):
            continue

        analysis = filter_engine.analyze_text(item["text"])
        if not analysis["has_teencode"]:
            continue

        utc_time, vn_time, yr = format_datetime_vn(dt)
        processed.append({
            "comment_id": item["id"],
            "parent_id": None,
            "platform": "demo",
            "post_id": "demo_post_001",
            "post_url": "https://example.com/demo/post_001",
            "post_title": "Video Demo Mẫu",
            "author_id": f"user_{item['id']}",
            "author_name": item["author"],
            "author_avatar_url": "https://example.com/avatar.jpg",
            "comment_text": item["text"],
            "cleaned_text": item["text"],
            "created_at": utc_time,
            "created_at_vn": vn_time,
            "year": yr,
            "likes_count": item["likes"],
            "reply_count": 0,
            "has_teencode": True,
            "detected_teencodes": analysis["detected_teencodes"],
            "teencode_count": analysis["teencode_count"],
            "teencode_density": analysis["teencode_density"],
            "extra_metadata": {"demo": True}
        })

    saved = exporter.export_processed_data(processed, output_prefix="demo_output", formats=["csv", "jsonl", "sqlite"])
    summary = exporter.generate_summary_report(processed)

    # In kết quả dạng bảng đẹp
    table = Table(title="Kết quả lọc bình luận mẫu (Demo Pipeline)")
    table.add_column("ID", style="cyan")
    table.add_column("Tác giả", style="magenta")
    table.add_column("Bình luận", style="white")
    table.add_column("Từ viết tắt tìm thấy", style="green")
    table.add_column("Năm", style="yellow")
    table.add_column("Mật độ (%)", style="blue")

    for p in processed:
        table.add_row(
            p["comment_id"],
            p["author_name"],
            p["comment_text"],
            ", ".join(p["detected_teencodes"]),
            str(p["year"]),
            f"{p['teencode_density']}%"
        )

    console.print(table)
    console.print(f"\n[bold green]✓ Demo hoàn tất thành công! Đã lưu file tại thư mục data/processed/demo_platform[/bold green]")

def main():
    display_welcome_banner()
    args = parse_arguments()

    target_words = [w.strip() for w in args.words.split(",") if w.strip()]
    export_formats = [f.strip().lower() for f in args.formats.split(",") if f.strip()]

    if args.demo:
        run_demo_simulation(target_words)
        return

    if not args.input:
        console.print(
            "[bold red]Lỗi:[/bold red] Bạn chưa cung cấp link bài viết / video / sản phẩm cần cào (tham số `-i` hoặc `--input`)."
        )
        console.print("[yellow]Gợi ý ví dụ sử dụng:[/yellow]")
        console.print("  [cyan]python main.py -p youtube -i \"https://www.youtube.com/watch?v=VIDEO_ID\" --max 500[/cyan]")
        console.print("  [cyan]python main.py -p shopee -i \"https://shopee.vn/product-name-i.12345.67890\" --max 500[/cyan]")
        console.print("  [cyan]python main.py -p tiktok -i \"https://www.tiktok.com/@user/video/7123456789\" --max 500[/cyan]")
        console.print("  [cyan]python main.py --demo (để chạy thử nghiệm ngay lập tức)[/cyan]")
        sys.exit(1)

    platform = args.platform.lower()

    # Khởi tạo Crawler theo nền tảng được nhóm lựa chọn
    if platform == "youtube":
        crawler = YouTubeCrawler(target_teencodes=target_words, max_years=args.years)
    elif platform == "tiktok":
        crawler = TikTokCrawler(target_teencodes=target_words, max_years=args.years)
    elif platform == "shopee":
        crawler = ShopeeCrawler(target_teencodes=target_words, max_years=args.years)
    elif platform == "facebook":
        crawler = FacebookCrawler(target_teencodes=target_words, max_years=args.years)
    elif platform == "threads":
        crawler = ThreadsCrawler(target_teencodes=target_words, max_years=args.years)
    else:
        logger.error(f"Nền tảng '{platform}' không hợp lệ.")
        sys.exit(1)

    console.print(f"\n[bold blue]Bắt đầu quy trình cào cho nền tảng:[/bold blue] [bold yellow]{platform.upper()}[/bold yellow]")
    console.print(f"[white]- Giới hạn thời gian:[/white] [green]{args.years} năm gần nhất[/green]")
    console.print(f"[white]- Từ viết tắt mục tiêu:[/white] [red]{', '.join(target_words[:10])}...[/red]")
    console.print(f"[white]- Số bình luận tối đa:[/white] [cyan]{args.max}[/cyan]\n")

    results = crawler.run(
        target_input=args.input,
        max_comments=args.max,
        export_formats=export_formats
    )

    console.print(f"\n[bold green]Hoàn thành thu thập! Tổng cộng {len(results)} bình luận thỏa mãn tiêu chí đã được trích xuất và xuất file.[/bold green]")

if __name__ == "__main__":
    main()
