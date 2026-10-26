"""
Logger utility using Rich for colorful, structured console and file logging.
"""

import logging
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from pathlib import Path
from rich.logging import RichHandler

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "crawler.log"

def setup_logger(name: str = "CommentCrawler", level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(level)

    from rich.console import Console
    rich_console = Console(force_terminal=True, legacy_windows=False)
    # Console handler with Rich
    rich_handler = RichHandler(console=rich_console, rich_tracebacks=True, markup=True)
    rich_handler.setLevel(level)
    logger.addHandler(rich_handler)

    # File handler
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)

    return logger

logger = setup_logger()
