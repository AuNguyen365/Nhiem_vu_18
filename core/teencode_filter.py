"""
Teencode & Abbreviation Filter for Vietnamese Social Media Comments.
Accurately detects teencode abbreviations (ngta, m, cx, k, mik, mn, dc...) using regex word boundaries.
"""

import json
import re
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path
from config.settings import TEENCODE_DICT_PATH
from utils.helpers import clean_comment_text

class TeencodeFilter:
    def __init__(self, dict_path: Optional[Path] = None, target_words_only: Optional[List[str]] = None):
        """
        Khởi tạo bộ lọc từ viết tắt / teencode tiếng Việt.
        :param dict_path: Đường dẫn tới file JSON chứa từ điển viết tắt.
        :param target_words_only: Nếu truyền vào danh sách cụ thể (vd: ['ngta', 'm', 'cx']),
                                  chỉ coi comment là hợp lệ nếu chứa ít nhất một trong các từ này.
        """
        self.dict_path = dict_path or TEENCODE_DICT_PATH
        self.abbreviations: Dict[str, str] = {}
        self.priority_targets: List[str] = []
        self._compiled_patterns: Dict[str, re.Pattern] = {}
        self.target_filter: Optional[set] = set(w.lower() for w in target_words_only) if target_words_only else None
        
        self._load_dictionary()
        self._compile_regexes()

    def _load_dictionary(self):
        """Tải từ điển teencode từ file JSON."""
        if Path(self.dict_path).exists():
            with open(self.dict_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.abbreviations = data.get("abbreviations", {})
                self.priority_targets = data.get("priority_targets", ["ngta", "m", "cx", "k", "dc", "mik", "mn"])
        else:
            # Fallback dictionary cơ bản
            self.abbreviations = {
                "ngta": "người ta",
                "m": "mày/mình",
                "cx": "cũng",
                "k": "không",
                "ko": "không",
                "dc": "được",
                "đc": "được",
                "mik": "mình",
                "mn": "mọi người",
                "bt": "biết/bình thường",
                "v": "vậy",
                "j": "gì",
                "z": "vậy",
                "h": "giờ",
                "vs": "với",
            }
            self.priority_targets = list(self.abbreviations.keys())

    def _compile_regexes(self):
        """
        Biên dịch Regex ranh giới từ (Word Boundary) để phát hiện chính xác:
        - Với từ 1 ký tự (m, t, k, v...): Chặn thêm dấu nháy đơn (i'm), dấu chấm (m.n) và gạch nối để tránh false positives.
        - Với từ đa ký tự (ngta, cx, mik...): Sử dụng unicode word boundary (?<!\\w)...(?!\\w).
        """
        for word in self.abbreviations.keys():
            escaped_word = re.escape(word)
            if len(word) == 1:
                # Từ đơn: tránh bắt dính vào dấu nháy đơn ' (i'm), dấu chấm . (m.n), dấu gạch nối -
                pattern = re.compile(rf'(?<![\w\'\’\.\-]){escaped_word}(?![\w\'\’\.\-])', re.IGNORECASE)
            else:
                pattern = re.compile(rf'(?<!\w){escaped_word}(?!\w)', re.IGNORECASE)
            self._compiled_patterns[word.lower()] = pattern

    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Phân tích chuyên sâu văn bản bình luận:
        - Loại bỏ mention rác (@username) và URL trước khi phân tích
        - Phát hiện các từ viết tắt
        - Đếm số lần xuất hiện
        - Tính mật độ viết tắt (teencode density)
        - Trả về chi tiết nghĩa mở rộng
        """
        if not text or not isinstance(text, str):
            return {
                "has_teencode": False,
                "detected_teencodes": [],
                "teencode_count": 0,
                "teencode_density": 0.0,
                "expanded_meanings": {},
            }

        # Làm sạch mention và URL trước khi phân tích
        cleaned = clean_comment_text(text, remove_mentions=True)
        if not cleaned:
            return {
                "has_teencode": False,
                "detected_teencodes": [],
                "teencode_count": 0,
                "teencode_density": 0.0,
                "expanded_meanings": {},
            }

        words = re.findall(r'\b\w+\b', cleaned, re.UNICODE)
        total_words = len(words)

        detected_words = []
        occurrences_count = 0
        expanded_meanings = {}

        for abbr, pattern in self._compiled_patterns.items():
            matches = pattern.findall(cleaned)
            if matches:
                detected_words.append(abbr)
                count = len(matches)
                occurrences_count += count
                expanded_meanings[abbr] = {
                    "count": count,
                    "meaning": self.abbreviations.get(abbr, ""),
                    "raw_matches": matches
                }

        # Nếu có đặt target filter (vd chỉ lấy comment có 'ngta', 'm', 'cx'...)
        if self.target_filter:
            has_teencode = any(w in self.target_filter for w in detected_words)
        else:
            has_teencode = len(detected_words) > 0

        density = round((occurrences_count / total_words * 100), 2) if total_words > 0 else 0.0

        return {
            "has_teencode": has_teencode,
            "detected_teencodes": detected_words,
            "teencode_count": occurrences_count,
            "teencode_density": density,
            "expanded_meanings": expanded_meanings,
        }

    def contains_teencode(self, text: str) -> bool:
        """Hàm kiểm tra nhanh xem text có chứa teencode thỏa mãn hay không."""
        return self.analyze_text(text)["has_teencode"]
