from __future__ import annotations

import io
import json
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from flask import render_template_string, jsonify, request, send_file, abort

from app.app_dependencies import PDF_TO_HTML_AVAILABLE, extract_text_from_pdf
from app.app_helpers import get_source_files
from app.session_utils import get_session_input_dir


def _split_merged_words(text: str) -> str:
    """
    Минимальная постобработка для случаев, когда слова всё равно слиплись.
    Применяется только к ОЧЕНЬ длинным словам (>50 символов).
    """
    if not text or len(text) < 50:
        return text
    
    # Проверяем, есть ли ОЧЕНЬ длинные слова (>50 символов)
    words = text.split()
    very_long = [w for w in words if len(w) > 50]
    
    if not very_long:
        return text
    
    result = text
    
    # Только самые очевидные случаи: "слово.Слово" → "слово. Слово"
    result = re.sub(r'([а-яёa-z])\.([А-ЯЁA-Z])', r'\1. \2', result)
    
    # Убираем множественные пробелы
    result = re.sub(r' +', ' ', result)
    
    return result.strip()


def _find_annotation_block(page, lang: str, options: dict) -> tuple[float, float] | None:
    """
    Ищет блок аннотации на странице по ключевым словам:
    - RU: "Аннотация" и до "Ключевые слова"
    - EN: "Abstract" и до "Keywords"
    Возвращает (top, bottom) в координатах PDF (top/bottom).
    """
    try:
        words = page.extract_words(x_tolerance=1, y_tolerance=3, keep_blank_chars=False)
    except Exception:
        words = []

    if not words:
        return None

    line_tolerance = 3
    lines = []
    current_line = []
    current_top = None

    words_sorted = sorted(words, key=lambda w: (round(w["top"] / line_tolerance), w["x0"]))
    for w in words_sorted:
        if current_top is None:
            current_top = w["top"]
            current_line = [w]
        elif abs(w["top"] - current_top) <= line_tolerance:
            current_line.append(w)
        else:
            if current_line:
                line_top = min(x["top"] for x in current_line)
                line_bottom = max(x["bottom"] for x in current_line)
                line_text = " ".join(x["text"] for x in current_line)
                lines.append({"text": line_text, "top": line_top, "bottom": line_bottom})
            current_line = [w]
            current_top = w["top"]

    if current_line:
        line_top = min(x["top"] for x in current_line)
        line_bottom = max(x["bottom"] for x in current_line)
        line_text = " ".join(x["text"] for x in current_line)
        lines.append({"text": line_text, "top": line_top, "bottom": line_bottom})

    def _simplify_text(value: str) -> str:
        value = re.sub(r"\s+", " ", value).strip().lower()
        value = re.sub(r"[^\w\s]", " ", value, flags=re.UNICODE)
        return re.sub(r"\s+", " ", value).strip()

    heading_idx = None
    for i, line in enumerate(lines):
        text = _simplify_text(line["text"])
        if lang == "ru" and re.search(r"\bаннотация\b", text):
            heading_idx = i
            break
        if lang == "en" and re.search(r"\babstract\b", text):
            heading_idx = i
            break

    if heading_idx is None:
        return None

    start_top = lines[heading_idx]["bottom"] + 2

    end_bottom = None
    for j in range(heading_idx + 1, len(lines)):
        text = _simplify_text(lines[j]["text"])
        if lang == "ru" and re.search(r"\bключев\w*\s*слов\w*\b", text):
            end_bottom = lines[j]["top"] - 1
            break
        if lang == "en" and re.search(r"\bkeywords?\b|\bkey\s*words?\b|\bindex\s*terms?\b", text):
            end_bottom = lines[j]["top"] - 1
            break

    max_ratio = float(options.get("annotation_max_height_ratio", 0.6))
    min_ratio = float(options.get("annotation_min_height_ratio", 0.12))
    min_height = page.height * min_ratio

    if end_bottom is not None:
        if (end_bottom - start_top) < min_height:
            end_bottom = None

    if end_bottom is None:
        footer_threshold = page.height * 0.85
        for line in reversed(lines[heading_idx + 1:]):
            if line["top"] < footer_threshold:
                break
            text = _simplify_text(line["text"])
            if re.fullmatch(r"\d{1,4}", text) or re.search(r"\bpage\b|\bстр\b", text):
                end_bottom = line["top"] - 1
                break

    if end_bottom is None:
        end_bottom = min(page.height, start_top + page.height * max_ratio)

    if end_bottom <= start_top:
        return None

    return start_top, end_bottom


def _is_garbled_text(text: str, lang: str | None = None) -> bool:
    """
    Грубая эвристика: определяет, что текст "каша".
    Основано на:
    - средней длине слова
    - наличии заглавных букв внутри слова
    - доле слов без гласных
    """
    if not text:
        return False

    words = [w for w in re.split(r"\s+", text) if w]
    if not words:
        return False

    avg_len = sum(len(w) for w in words) / len(words)
    if avg_len > 15:
        return True

    vowels_ru = set("аеёиоуыэюя")
    vowels_en = set("aeiouy")

    internal_caps = 0
    mixed_case = 0
    no_vowel = 0
    low_vowel = 0

    for w in words:
        if len(w) > 3 and any(c.isupper() for c in w[1:]):
            internal_caps += 1
        if len(w) > 3 and any(c.isupper() for c in w[1:]) and any(c.islower() for c in w[1:]):
            mixed_case += 1

        lw = w.lower()
        has_ru = any(c in vowels_ru for c in lw)
        has_en = any(c in vowels_en for c in lw)
        if not (has_ru or has_en):
            no_vowel += 1
        else:
            vcount = sum(1 for c in lw if c in vowels_ru or c in vowels_en)
            if len(lw) >= 5 and (vcount / len(lw)) < 0.2:
                low_vowel += 1

    caps_ratio = internal_caps / len(words)
    mixed_ratio = mixed_case / len(words)
    no_vowel_ratio = no_vowel / len(words)

    if caps_ratio > 0.05:
        return True
    if mixed_ratio > 0.05:
        return True
    if no_vowel_ratio > 0.3:
        return True
    if (low_vowel / len(words)) > 0.3:
        return True

    if lang == "ru" and no_vowel_ratio > 0.25:
        return True
    if lang == "en" and no_vowel_ratio > 0.3:
        return True

    return False


def _ocr_extract_text(page, bbox: tuple[float, float, float, float], lang: str) -> str | None:
    """OCR fallback. Требует установленный pytesseract и Tesseract OCR."""
    try:
        import pytesseract  # type: ignore
    except Exception:
        return None

    try:
        cropped = page.crop(bbox)
        img = cropped.to_image(resolution=300).original
        text = pytesseract.image_to_string(img, lang=lang)
        return text
    except Exception:
        return None


def _normalize_extracted_text(text: str, field_id: str | None, options: dict) -> str:
    if not text or text == "(Текст не найден)":
        return text
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n")

    cleaned = _split_merged_words(cleaned)

    fix_hyphenation = options.get("fix_hyphenation", True)
    if fix_hyphenation:
        cleaned = re.sub(
            r"([A-Za-zА-Яа-яЁё])[-‑–—]\s*\n\s*([a-zа-яё])",
            r"\1\2",
            cleaned,
        )
        cleaned = re.sub(
            r"([A-Za-zА-Яа-яЁё])[-‑–—]\s+([a-zа-яё])",
            r"\1\2",
            cleaned,
        )

    strip_prefix = options.get("strip_prefix", True)
    if strip_prefix:
        if field_id in {"annotation", "annotation_en"}:
            cleaned = re.sub(r"^(аннотация|abstract)\s*[:\-]\s*", "", cleaned, flags=re.IGNORECASE)
        if field_id in {"keywords", "keywords_en"}:
            cleaned = re.sub(r"^(ключевые слова|keywords)\s*[:\-]\s*", "", cleaned, flags=re.IGNORECASE)

    join_lines = options.get("join_lines")
    if join_lines is None:
        join_lines = field_id not in {"references_ru", "references_en"}
    if join_lines:
        cleaned = re.sub(r"[ \t]*\n[ \t]*", " ", cleaned)

    cleaned = re.sub(
        r'\b([A-ZА-ЯЁ])\s+(орг|общ|max|min|opt|eff|tot|org|obs|calc|exp|теор|эксп|ср|мин|макс)\b',
        r'\1_\2',
        cleaned,
        flags=re.IGNORECASE
    )
    cleaned = re.sub(
        r'\b([CNPKС])(\s*)(орг|общ|org|tot)\b',
        r'\1_\3',
        cleaned,
        flags=re.IGNORECASE
    )

    cleaned = re.sub(r"[ \t]+", " ", cleaned).strip()
    return cleaned


class Language(Enum):
    """Язык текста."""

    RUSSIAN = "ru"
    ENGLISH = "en"
    MIXED = "mixed"
    UNKNOWN = "unknown"


@dataclass
class BBox:
    """Прямоугольная область в PDF."""

    x1: float
    y1: float
    x2: float
    y2: float

    def normalize(self) -> "BBox":
        """Нормализует координаты (x1 < x2, y1 < y2)."""
        return BBox(
            x1=min(self.x1, self.x2),
            y1=min(self.y1, self.y2),
            x2=max(self.x1, self.x2),
            y2=max(self.y1, self.y2),
        )

    def add_padding(self, padding_x: float, padding_y: float, page_width: float, page_height: float) -> "BBox":
        """Добавляет отступы к области."""
        return BBox(
            x1=max(0, self.x1 - padding_x),
            y1=max(0, self.y1 - padding_y),
            x2=min(page_width, self.x2 + padding_x),
            y2=min(page_height, self.y2 + padding_y),
        )

    def is_valid(self) -> bool:
        """Проверяет валидность области."""
        return self.x1 < self.x2 and self.y1 < self.y2

    def to_tuple(self) -> Tuple[float, float, float, float]:
        """Возвращает кортеж координат для pdfplumber."""
        return (self.x1, self.y1, self.x2, self.y2)


@dataclass
class ExtractionOptions:
    """Опции извлечения текста."""

    merge_by_field: bool = False
    annotation_by_heading: bool = True
    use_ocr_if_garbled: bool = False
    force_ocr: bool = False
    ocr_lang: Optional[str] = None
    fix_hyphenation: bool = True
    strip_prefix: bool = True
    join_lines: Optional[bool] = None
    annotation_max_height_ratio: float = 0.6
    annotation_min_height_ratio: float = 0.12
    padding_x: float = 5.0
    padding_y: float = 3.0
    line_tolerance: float = 5.0

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "ExtractionOptions":
        """Создает из словаря."""
        if not data:
            return cls()
        return cls(
            merge_by_field=bool(data.get("merge_by_field", False)),
            annotation_by_heading=bool(data.get("annotation_by_heading", True)),
            use_ocr_if_garbled=bool(data.get("use_ocr_if_garbled", False)),
            force_ocr=bool(data.get("force_ocr", False)),
            ocr_lang=data.get("ocr_lang"),
            fix_hyphenation=bool(data.get("fix_hyphenation", True)),
            strip_prefix=bool(data.get("strip_prefix", True)),
            join_lines=data.get("join_lines"),
            annotation_max_height_ratio=float(data.get("annotation_max_height_ratio", 0.6)),
            annotation_min_height_ratio=float(data.get("annotation_min_height_ratio", 0.12)),
            padding_x=float(data.get("padding_x", 5.0)),
            padding_y=float(data.get("padding_y", 3.0)),
            line_tolerance=float(data.get("line_tolerance", 5.0)),
        )


class LanguageDetector:
    """Определение языка текста."""

    @staticmethod
    def detect(text: str) -> Language:
        """Определяет основной язык текста."""
        if not text:
            return Language.UNKNOWN

        cyrillic_count = sum(1 for c in text if 0x0400 <= ord(c) <= 0x04FF)
        latin_count = sum(1 for c in text if c.isalpha() and ord(c) < 0x0400)

        if cyrillic_count == 0 and latin_count == 0:
            return Language.UNKNOWN

        if cyrillic_count > 0 and latin_count > 0:
            return Language.RUSSIAN if cyrillic_count > latin_count else Language.ENGLISH

        if cyrillic_count > 0:
            return Language.RUSSIAN
        if latin_count > 0:
            return Language.ENGLISH

        return Language.UNKNOWN

    @staticmethod
    def has_cyrillic(text: str) -> bool:
        """Проверяет наличие кириллицы."""
        return any(0x0400 <= ord(c) <= 0x04FF for c in text)

    @staticmethod
    def has_latin(text: str) -> bool:
        """Проверяет наличие латиницы."""
        return any(c.isalpha() and ord(c) < 0x0400 for c in text)


class TextQualityAnalyzer:
    """Анализ качества извлеченного текста."""

    IDEAL_WORD_LENGTH = {
        Language.RUSSIAN: 6.5,
        Language.ENGLISH: 5.5,
        Language.MIXED: 6.0,
        Language.UNKNOWN: 6.0,
    }

    MIN_WORD_LENGTH = 3.0
    MAX_WORD_LENGTH = 15.0

    @staticmethod
    def calculate_average_word_length(text: str) -> float:
        """Вычисляет среднюю длину слова."""
        if not text:
            return float("inf")

        words = text.split()
        if not words:
            return float("inf")

        return sum(len(w) for w in words) / len(words)

    @staticmethod
    def calculate_short_words_ratio(text: str, threshold: int = 2) -> float:
        """Вычисляет долю коротких слов."""
        if not text:
            return 1.0

        words = text.split()
        if not words:
            return 1.0

        short_count = sum(1 for w in words if len(w) <= threshold)
        return short_count / len(words)

    @classmethod
    def calculate_quality_score(cls, text: str, language: Language) -> float:
        """
        Вычисляет оценку качества текста.
        Меньше = лучше. 0 = идеально.
        """
        if not text or text == "(Текст не найден)":
            return float("inf")

        avg_length = cls.calculate_average_word_length(text)
        ideal_length = cls.IDEAL_WORD_LENGTH.get(language, 6.0)

        if cls.MIN_WORD_LENGTH <= avg_length <= cls.MAX_WORD_LENGTH:
            score = abs(avg_length - ideal_length)
        else:
            score = 50.0 + abs(avg_length - ideal_length)

        short_ratio = cls.calculate_short_words_ratio(text)
        if short_ratio > 0.3:
            score += short_ratio * 20

        return score


class CharacterGapAnalyzer:
    """Анализ расстояний между символами для определения оптимального x_tolerance."""

    @dataclass
    class GapStatistics:
        """Статистика расстояний между символами."""

        median: float
        p75: float
        p90: float
        min_gap: float
        max_gap: float
        suggested_x_tolerance: float
        suggested_space_threshold: Optional[float]

    @classmethod
    def analyze_gaps(cls, chars: List[Dict[str, Any]]) -> Optional["CharacterGapAnalyzer.GapStatistics"]:
        """Анализирует расстояния между символами."""
        if not chars or len(chars) < 2:
            return None

        gaps = cls._extract_gaps(chars)
        if not gaps:
            return None

        gaps_sorted = sorted(gaps)
        n = len(gaps_sorted)

        stats = cls.GapStatistics(
            median=gaps_sorted[n // 2],
            p75=gaps_sorted[int(n * 0.75)],
            p90=gaps_sorted[int(n * 0.90)],
            min_gap=gaps_sorted[0],
            max_gap=gaps_sorted[-1],
            suggested_x_tolerance=0.0,
            suggested_space_threshold=None,
        )

        stats.suggested_x_tolerance, stats.suggested_space_threshold = cls._calculate_x_tolerance(
            stats, gaps_sorted
        )

        return stats

    @staticmethod
    def _extract_gaps(chars: List[Dict[str, Any]]) -> List[float]:
        """Извлекает расстояния между соседними символами на одной строке."""
        chars_sorted = sorted(chars, key=lambda c: (c.get("top", 0), c.get("x0", 0)))
        gaps = []

        for i in range(1, len(chars_sorted)):
            prev_char = chars_sorted[i - 1]
            curr_char = chars_sorted[i]
            if abs(prev_char.get("top", 0) - curr_char.get("top", 0)) < 5:
                gap = curr_char.get("x0", 0) - prev_char.get("x1", 0)
                if 0 < gap < 50:
                    gaps.append(gap)

        return gaps

    @staticmethod
    def _calculate_x_tolerance(
        stats: "CharacterGapAnalyzer.GapStatistics", gaps_sorted: List[float]
    ) -> Tuple[float, Optional[float]]:
        """Вычисляет оптимальный x_tolerance и порог пробела."""
        median = stats.median
        large_gaps = [g for g in gaps_sorted if g > median * 2.5]

        if large_gaps and len(large_gaps) >= 3:
            max_letter_gap = max(g for g in gaps_sorted if g <= median * 2.5)
            min_word_gap = min(large_gaps)
            space_threshold = (max_letter_gap + min_word_gap) / 2

            x_tolerance = min(space_threshold * 0.8, min_word_gap * 0.5)
            x_tolerance = max(0.5, x_tolerance)
            return x_tolerance, space_threshold

        x_tolerance = max(1.0, min(10.0, median * 1.5))
        return x_tolerance, None


class TextExtractor:
    """Извлечение текста из PDF области."""

    def __init__(self, options: ExtractionOptions):
        self.options = options
        self.quality_analyzer = TextQualityAnalyzer()

    def extract_from_crop(self, cropped_page, language_hint: Optional[Language] = None) -> str:
        """Извлекает текст из обрезанной страницы PDF."""
        chars = getattr(cropped_page, "chars", None) or []
        gap_stats = CharacterGapAnalyzer.analyze_gaps(chars)

        if gap_stats:
            x_tolerance = gap_stats.suggested_x_tolerance
            print(f"DEBUG: x_tolerance={x_tolerance:.2f}, median_gap={gap_stats.median:.2f}")
        else:
            x_tolerance = 3.0
            print(f"DEBUG: x_tolerance={x_tolerance:.2f} (default)")

        candidates = self._try_extraction_methods(cropped_page, x_tolerance)
        best_text = self._select_best_candidate(candidates, language_hint)

        if gap_stats and self.quality_analyzer.calculate_average_word_length(best_text) > 20:
            reconstructed = self._reconstruct_from_chars(chars, gap_stats)
            if reconstructed:
                avg_reconstructed = self.quality_analyzer.calculate_average_word_length(reconstructed)
                avg_best = self.quality_analyzer.calculate_average_word_length(best_text)
                if avg_reconstructed < avg_best and avg_reconstructed < 25:
                    print(f"DEBUG: Используем реконструированный текст (avg={avg_reconstructed:.1f})")
                    best_text = reconstructed

        return best_text or "(Текст не найден)"

    def _try_extraction_methods(self, cropped_page, x_tolerance: float) -> List[Tuple[str, str]]:
        """Пробует разные методы извлечения текста."""
        candidates = []

        try:
            try:
                text = cropped_page.extract_text(x_tolerance=x_tolerance, y_tolerance=5)
            except TypeError:
                text = cropped_page.extract_text()
            if text:
                candidates.append(("adaptive", text))
        except Exception as e:
            print(f"DEBUG: Метод 'adaptive' failed: {e}")

        try:
            try:
                text = cropped_page.extract_text(layout=True, x_tolerance=3, y_tolerance=5)
            except TypeError:
                text = cropped_page.extract_text()
            if text:
                text = re.sub(r" +", " ", text)
                text = re.sub(r"\n\s*\n+", "\n", text)
                candidates.append(("layout", text))
        except Exception as e:
            print(f"DEBUG: Метод 'layout' failed: {e}")

        try:
            try:
                text = cropped_page.extract_text(use_text_flow=True, x_tolerance=2, y_tolerance=5)
            except TypeError:
                text = cropped_page.extract_text()
            if text:
                candidates.append(("text_flow", text))
        except Exception as e:
            print(f"DEBUG: Метод 'text_flow' failed: {e}")

        try:
            try:
                text = cropped_page.extract_text(x_tolerance=0.5, y_tolerance=5)
            except TypeError:
                text = cropped_page.extract_text()
            if text:
                candidates.append(("tight", text))
        except Exception as e:
            print(f"DEBUG: Метод 'tight' failed: {e}")

        return candidates

    def _select_best_candidate(self, candidates: List[Tuple[str, str]], language_hint: Optional[Language]) -> str:
        """Выбирает лучший результат из кандидатов."""
        if not candidates:
            return ""

        if language_hint is None:
            language_hint = LanguageDetector.detect(candidates[0][1])

        best_text = ""
        best_score = float("inf")
        best_method = ""

        for method, text in candidates:
            score = self.quality_analyzer.calculate_quality_score(text, language_hint)
            if _is_garbled_text(text, language_hint.value if language_hint != Language.UNKNOWN else None):
                score += 100

            if score < best_score:
                best_score = score
                best_text = text
                best_method = method

        avg_len = self.quality_analyzer.calculate_average_word_length(best_text)
        print(f"DEBUG: Лучший метод: {best_method}, avg_word_len={avg_len:.1f}, score={best_score:.1f}")

        return best_text

    def _reconstruct_from_chars(
        self, chars: List[Dict[str, Any]], gap_stats: "CharacterGapAnalyzer.GapStatistics"
    ) -> Optional[str]:
        """Реконструирует текст из символов вручную."""
        if not chars or not gap_stats.suggested_space_threshold:
            return None

        space_threshold = gap_stats.p90

        chars_sorted = sorted(chars, key=lambda c: (c.get("top", 0), c.get("x0", 0)))
        lines = []
        current_line = []
        current_top = None
        prev_char = None

        for char in chars_sorted:
            char_text = char.get("text", "")
            char_top = char.get("top", 0)
            char_x0 = char.get("x0", 0)

            if current_top is None or abs(char_top - current_top) > 5:
                if current_line:
                    lines.append("".join(current_line))
                current_line = [char_text]
                current_top = char_top
                prev_char = char
                continue

            if prev_char:
                gap = char_x0 - prev_char.get("x1", char_x0)
                if gap > space_threshold:
                    current_line.append(" ")

            current_line.append(char_text)
            prev_char = char

        if current_line:
            lines.append("".join(current_line))

        return "\n".join(lines)


class LanguageFilter:
    """Фильтрация текста по языку."""

    @staticmethod
    def filter_by_language(
        text: str,
        words: List[Dict[str, Any]],
        target_language: Language,
        skip_filter: bool = False,
        line_tolerance: float = 5.0,
    ) -> str:
        """
        Фильтрует текст, оставляя только слова на целевом языке.
        """
        if skip_filter or target_language == Language.UNKNOWN:
            return text

        if not words:
            return text

        detected = LanguageDetector.detect(text)
        if detected == target_language:
            return text

        if target_language == Language.RUSSIAN:
            filtered_words = [
                w
                for w in words
                if LanguageDetector.has_cyrillic(w["text"]) or not any(c.isalpha() for c in w["text"])
            ]
        elif target_language == Language.ENGLISH:
            filtered_words = [
                w
                for w in words
                if LanguageDetector.has_latin(w["text"]) or not any(c.isalpha() for c in w["text"])
            ]
        else:
            return text

        if not filtered_words:
            return text

        return LanguageFilter._reconstruct_text_from_words(filtered_words, line_tolerance=line_tolerance)

    @staticmethod
    def _reconstruct_text_from_words(words: List[Dict[str, Any]], line_tolerance: float = 5.0) -> str:
        """Восстанавливает текст из списка слов с учетом строк."""
        lines = []
        current_line = []
        current_top = None

        words_sorted = sorted(words, key=lambda w: (round(w["top"] / line_tolerance), w["x0"]))

        for word in words_sorted:
            word_top = word["top"]

            if current_top is None or abs(word_top - current_top) > line_tolerance:
                if current_line:
                    current_line.sort(key=lambda w: w["x0"])
                    lines.append(current_line)
                current_line = [word]
                current_top = word_top
            else:
                current_line.append(word)

        if current_line:
            current_line.sort(key=lambda w: w["x0"])
            lines.append(current_line)

        return "\n".join([" ".join([w["text"] for w in line]) for line in lines])


class PDFTextExtractor:
    """Главный класс для извлечения текста из областей PDF."""

    RUSSIAN_FIELDS = {
        "title",
        "annotation",
        "keywords",
        "references_ru",
        "funding",
        "author_surname_rus",
        "author_initials_rus",
        "author_org_rus",
        "author_address_rus",
        "author_other_rus",
    }

    ENGLISH_FIELDS = {
        "title_en",
        "annotation_en",
        "keywords_en",
        "references_en",
        "funding_en",
        "author_surname_eng",
        "author_initials_eng",
        "author_org_eng",
        "author_address_eng",
        "author_other_eng",
    }

    MIXED_LANGUAGE_FIELDS = {"references_ru", "references_en", "annotation", "annotation_en"}

    def __init__(self, options: ExtractionOptions):
        self.options = options
        self.text_extractor = TextExtractor(options)
        self.language_filter = LanguageFilter()

    def extract_from_selection(self, page, selection: Dict[str, Any]) -> Dict[str, Any]:
        """Извлекает текст из одной выделенной области."""
        field_id = selection.get("field_id")
        page_num = selection.get("page", 0)

        target_language = self._get_target_language(field_id)
        skip_language_filter = field_id in self.MIXED_LANGUAGE_FIELDS

        bbox = self._get_bbox_from_selection(page, selection, field_id)

        if not bbox.is_valid():
            print(f"WARNING: Невалидная область для {field_id}")
            return self._create_result(field_id, page_num, bbox, "(Невалидная область)")

        print(f"DEBUG: Обработка {field_id} на странице {page_num}")
        print(f"DEBUG: Область: {bbox.to_tuple()}")

        try:
            cropped = page.crop(bbox.to_tuple())
        except Exception as e:
            print(f"ERROR: Ошибка crop: {e}")
            return self._create_result(field_id, page_num, bbox, f"(Ошибка: {e})")

        text = self.text_extractor.extract_from_crop(cropped, target_language)

        try:
            try:
                words = cropped.extract_words(x_tolerance=3.0, y_tolerance=5.0, keep_blank_chars=False)
            except TypeError:
                words = cropped.extract_words()
        except Exception as e:
            print(f"DEBUG: Не удалось извлечь слова: {e}")
            words = []

        if words and target_language != Language.UNKNOWN:
            text = self.language_filter.filter_by_language(
                text,
                words,
                target_language,
                skip_language_filter,
                line_tolerance=self.options.line_tolerance,
            )

        if self._should_use_ocr(text, field_id):
            ocr_text = self._apply_ocr(page, bbox, field_id)
            if ocr_text:
                text = ocr_text

        text = _normalize_extracted_text(text, field_id, self.options.__dict__)

        return self._create_result(field_id, page_num, bbox, text)

    def _snap_bbox_to_line(self, page, bbox: BBox) -> Optional[BBox]:
        """Пытается расширить выделение до границ одной текстовой строки."""
        try:
            try:
                words = page.extract_words(x_tolerance=2.0, y_tolerance=3.0, keep_blank_chars=False)
            except TypeError:
                words = page.extract_words()
        except Exception:
            words = []

        if not words:
            return None

        line_tol = max(1.0, float(self.options.line_tolerance))
        lines: list[dict[str, float]] = []
        for w in sorted(words, key=lambda item: (round(item["top"] / line_tol), item["x0"])):
            if not lines or abs(w["top"] - lines[-1]["top"]) > line_tol:
                lines.append({
                    "top": w["top"],
                    "bottom": w["bottom"],
                    "x0": w["x0"],
                    "x1": w["x1"],
                })
            else:
                line = lines[-1]
                line["top"] = min(line["top"], w["top"])
                line["bottom"] = max(line["bottom"], w["bottom"])
                line["x0"] = min(line["x0"], w["x0"])
                line["x1"] = max(line["x1"], w["x1"])

        center_y = (bbox.y1 + bbox.y2) / 2
        best_line = None
        best_score = None
        for line in lines:
            line_center = (line["top"] + line["bottom"]) / 2
            if abs(line_center - center_y) > line_tol * 3:
                continue
            overlap = max(0.0, min(line["bottom"], bbox.y2) - max(line["top"], bbox.y1))
            score = (-overlap, abs(line_center - center_y))
            if best_score is None or score < best_score:
                best_score = score
                best_line = line

        if not best_line:
            return None

        return BBox(
            x1=float(best_line["x0"]),
            y1=float(best_line["top"]),
            x2=float(best_line["x1"]),
            y2=float(best_line["bottom"]),
        )

    def _get_target_language(self, field_id: Optional[str]) -> Language:
        """Определяет целевой язык для поля."""
        if not field_id:
            return Language.UNKNOWN

        if field_id in self.RUSSIAN_FIELDS:
            return Language.RUSSIAN
        if field_id in self.ENGLISH_FIELDS:
            return Language.ENGLISH
        return Language.UNKNOWN

    def _get_bbox_from_selection(self, page, selection: Dict[str, Any], field_id: Optional[str]) -> BBox:
        """Получает область из данных выделения."""
        def _has_manual_bbox(sel: Dict[str, Any]) -> bool:
            try:
                x1 = float(sel.get("pdf_x1", 0))
                y1 = float(sel.get("pdf_y1", 0))
                x2 = float(sel.get("pdf_x2", 0))
                y2 = float(sel.get("pdf_y2", 0))
            except (TypeError, ValueError):
                return False
            return abs(x2 - x1) > 1.0 and abs(y2 - y1) > 1.0

        has_manual = _has_manual_bbox(selection)

        if field_id in {"annotation", "annotation_en"} and self.options.annotation_by_heading and not has_manual:
            lang = "ru" if field_id == "annotation" else "en"
            block = _find_annotation_block(page, lang, self.options.__dict__)
            if block:
                top, bottom = block
                bbox = BBox(x1=0.0, y1=top, x2=page.width, y2=bottom)
                # Если пользователь выделял область, расширяем низ блока до границ выделения
                try:
                    sel_bbox = BBox(
                        x1=float(selection.get("pdf_x1", 0)),
                        y1=float(selection.get("pdf_y1", 0)),
                        x2=float(selection.get("pdf_x2", 0)),
                        y2=float(selection.get("pdf_y2", 0)),
                    ).normalize()
                    if sel_bbox.is_valid():
                        bbox = BBox(
                            x1=0.0,
                            y1=bbox.y1,
                            x2=page.width,
                            y2=max(bbox.y2, sel_bbox.y2),
                        )
                except Exception:
                    pass
                print(f"DEBUG: Аннотация по заголовку: {bbox.to_tuple()}")
                return bbox.add_padding(self.options.padding_x, self.options.padding_y, page.width, page.height)

        bbox = BBox(
            x1=float(selection.get("pdf_x1", 0)),
            y1=float(selection.get("pdf_y1", 0)),
            x2=float(selection.get("pdf_x2", 0)),
            y2=float(selection.get("pdf_y2", 0)),
        )

        bbox = bbox.normalize()
        bbox_height = bbox.y2 - bbox.y1
        if field_id in {"references_ru", "references_en"} and bbox_height <= max(18.0, self.options.line_tolerance * 4):
            snapped = self._snap_bbox_to_line(page, bbox)
            if snapped and snapped.is_valid():
                bbox = snapped
        bbox = bbox.add_padding(self.options.padding_x, self.options.padding_y, page.width, page.height)
        return bbox

    def _should_use_ocr(self, text: str, field_id: Optional[str]) -> bool:
        """Определяет, нужно ли использовать OCR."""
        if self.options.force_ocr:
            return True

        if not self.options.use_ocr_if_garbled:
            if field_id not in {"annotation", "annotation_en", "references_ru", "references_en"}:
                return False

        target_lang = self._get_target_language(field_id)
        lang_hint = target_lang.value if target_lang != Language.UNKNOWN else None
        return _is_garbled_text(text, lang_hint)

    def _apply_ocr(self, page, bbox: BBox, field_id: Optional[str]) -> Optional[str]:
        """Применяет OCR к области."""
        ocr_lang = self.options.ocr_lang
        if not ocr_lang:
            target_lang = self._get_target_language(field_id)
            if target_lang == Language.RUSSIAN:
                ocr_lang = "rus+eng"
            elif target_lang == Language.ENGLISH:
                ocr_lang = "eng+rus"
            else:
                ocr_lang = "rus+eng"

        print(f"DEBUG: Применяем OCR (lang={ocr_lang})")
        try:
            ocr_text = _ocr_extract_text(page, bbox.to_tuple(), ocr_lang)
            if ocr_text and ocr_text.strip():
                print(f"DEBUG: OCR успешно: {ocr_text[:100]}")
                return ocr_text.strip()
        except Exception as e:
            print(f"DEBUG: OCR failed: {e}")

        return None

    @staticmethod
    def _create_result(field_id: Optional[str], page_num: int, bbox: BBox, text: str) -> Dict[str, Any]:
        """Создает словарь результата."""
        return {
            "field_id": field_id,
            "page": page_num,
            "bbox": {"x1": bbox.x1, "y1": bbox.y1, "x2": bbox.x2, "y2": bbox.y2},
            "text": text,
        }

def register_pdf_routes(app, ctx):
    json_input_dir = ctx.get("json_input_dir")
    words_input_dir = ctx.get("words_input_dir")
    xml_output_dir = ctx.get("xml_output_dir")
    list_of_journals_path = ctx.get("list_of_journals_path")
    input_files_dir = ctx.get("input_files_dir")
    _input_files_dir = ctx.get("_input_files_dir")
    _words_input_dir = ctx.get("_words_input_dir")
    use_word_reader = ctx.get("use_word_reader")
    archive_root_dir = ctx.get("archive_root_dir")
    archive_retention_days = ctx.get("archive_retention_days")
    validate_zip_members = ctx.get("validate_zip_members")
    find_files_for_json = ctx.get("find_files_for_json")
    SUPPORTED_EXTENSIONS = ctx.get("SUPPORTED_EXTENSIONS")
    SUPPORTED_JSON_EXTENSIONS = ctx.get("SUPPORTED_JSON_EXTENSIONS")

    def _session_input_dir() -> Path:
        return get_session_input_dir(_input_files_dir)

    @app.route("/api/pdf-files")
    def api_pdf_files():
        """API endpoint для получения списка PDF файлов из input_files (рекурсивно во всех подпапках)."""
        try:
            pdf_files = []
            
            # Проверяем input_files_dir (используем сохраненную переменную из замыкания)
            try:
                input_dir = _session_input_dir()
                print(f"DEBUG: Проверяем input_files_dir: {input_dir}")
                print(f"DEBUG: input_files_dir type: {type(input_dir)}")
                print(f"DEBUG: input_files_dir exists: {input_dir.exists() if input_dir else 'None'}")
                print(f"DEBUG: input_files_dir is_dir: {input_dir.is_dir() if input_dir else 'None'}")
                
                if not input_dir or not input_dir.exists() or not input_dir.is_dir():
                    error_msg = f"Директория input_files не найдена или недоступна: {input_dir}"
                    print(f"ERROR: {error_msg}")
                    return jsonify({
                        "error": error_msg,
                        "input_files_dir": str(input_dir) if input_dir else "не определен"
                    }), 404
                
                # Проверяем, есть ли файлы
                pdf_count = len(list(input_dir.rglob("*.pdf")))
                print(f"DEBUG: ✅ Найдено PDF файлов в input_files: {pdf_count}")
                
            except NameError as ne:
                error_msg = f"input_files_dir не определен: {ne}"
                print(f"ERROR: {error_msg}")
                return jsonify({"error": error_msg}), 500
            except Exception as e:
                error_msg = f"Ошибка при проверке input_files_dir: {e}"
                print(f"ERROR: {error_msg}")
                import traceback
                print(traceback.format_exc())
                return jsonify({"error": error_msg}), 500
            
            # Ищем PDF файлы в input_files
            print(f"DEBUG: 🔍 Ищем PDF файлы в input_files: {input_dir}")
            print(f"DEBUG: Абсолютный путь: {input_dir.resolve()}")
            file_count = 0
            for file_path in input_dir.rglob("*.pdf"):
                try:
                    file_count += 1
                    # Получаем относительный путь от корневой директории
                    relative = file_path.relative_to(input_dir)
                    file_entry = str(relative.as_posix())
                    pdf_files.append(file_entry)
                    print(f"DEBUG: ✅ Найден файл #{file_count}: {file_entry} (полный путь: {file_path})")
                except ValueError as ve:
                    print(f"DEBUG: ❌ Пропущен файл {file_path} из-за ValueError: {ve}")
                    continue
            
            print(f"DEBUG: 📊 В input_files найдено {file_count} PDF файлов")
            
            print(f"DEBUG: 🎯 Всего найдено {len(pdf_files)} PDF файлов")
            if len(pdf_files) == 0:
                print(f"DEBUG: ⚠️ ВНИМАНИЕ: Файлы не найдены! Проверьте путь:")
                print(f"DEBUG:   - input_files: {input_dir} (exists={input_dir.exists()}, is_dir={input_dir.is_dir()})")
            # Сортируем для удобства
            result = sorted(pdf_files)
            print(f"DEBUG: 📤 Отправляем список из {len(result)} файлов")
            return jsonify(result)
        except Exception as e:
            import traceback
            error_msg = f"Ошибка при получении списка PDF файлов: {str(e)}\n{traceback.format_exc()}"
            print(f"ERROR: {error_msg}")
            return jsonify({"error": str(e), "details": traceback.format_exc()}), 500
    

    @app.route("/pdf-bbox")
    def pdf_bbox_form():
        """Веб-форма для поиска bbox в PDF файлах."""
        return render_template_string(PDF_BBOX_TEMPLATE)
    

    @app.route("/api/pdf-bbox", methods=["POST"])
    def api_pdf_bbox():
        """API endpoint для поиска блоков в PDF по ключевым словам."""
        try:
            data = request.get_json()
            pdf_filename = data.get("pdf_file")
            search_terms = data.get("terms", [])
            find_annotation = data.get("annotation", False)
            
            if not pdf_filename:
                return jsonify({"error": "Не указан файл PDF"}), 400
            
            # Безопасность: проверяем путь
            if ".." in pdf_filename or pdf_filename.startswith("/") or pdf_filename.startswith("\\"):
                return jsonify({"error": "Недопустимый путь к файлу"}), 400
            
            # Файл из input_files
            session_input_dir = _session_input_dir()
            pdf_path = session_input_dir / pdf_filename
            base_dir = session_input_dir
            
            if not pdf_path.exists() or not pdf_path.is_file():
                return jsonify({"error": f"Файл не найден: {pdf_filename}"}), 404
            
            if pdf_path.suffix.lower() != ".pdf":
                return jsonify({"error": "Файл должен быть PDF"}), 400
            
            # Проверяем, что файл находится внутри базовой директории
            try:
                pdf_path.resolve().relative_to(base_dir.resolve())
            except ValueError:
                return jsonify({"error": "Недопустимый путь к файлу"}), 400
            
            # Импортируем функции для работы с bbox
            try:
                from converters.pdf_to_html import find_text_blocks_with_bbox, find_annotation_bbox_auto
            except ImportError:
                return jsonify({"error": "Функции для работы с bbox недоступны"}), 500
            
            if find_annotation:
                # Автоматический поиск аннотации
                result = find_annotation_bbox_auto(pdf_path)
                if result:
                    return jsonify({
                        "success": True,
                        "blocks": [result]
                    })
                else:
                    return jsonify({
                        "success": False,
                        "message": "Аннотация не найдена"
                    })
            else:
                # Поиск по ключевым словам
                if not search_terms:
                    search_terms = ["Резюме", "Аннотация", "Abstract", "Annotation", "Ключевые слова", "Keywords"]
                
                blocks = find_text_blocks_with_bbox(
                    pdf_path,
                    search_terms=search_terms,
                    expand_bbox=(0, -10, 0, 100)
                )
                
                return jsonify({
                    "success": True,
                    "blocks": blocks
                })
        
        except Exception as e:
            return jsonify({"error": f"Ошибка при обработке: {str(e)}"}), 500
    

    @app.route("/api/pdf-info", methods=["POST"])
    def api_pdf_info():
        """API endpoint для получения информации о PDF (количество страниц, размеры)."""
        try:
            data = request.get_json()
            pdf_filename = data.get("pdf_file")
            
            if not pdf_filename:
                return jsonify({"error": "Не указан файл PDF"}), 400
            
            # Безопасность: проверяем путь
            if ".." in pdf_filename or pdf_filename.startswith("/") or pdf_filename.startswith("\\"):
                return jsonify({"error": "Недопустимый путь к файлу"}), 400
            
            # Файл из input_files
            session_input_dir = _session_input_dir()
            pdf_path = session_input_dir / pdf_filename
            base_dir = session_input_dir
            
            if not pdf_path.exists() or not pdf_path.is_file():
                return jsonify({"error": f"Файл не найден: {pdf_filename}"}), 404
            
            if pdf_path.suffix.lower() != ".pdf":
                return jsonify({"error": "Файл должен быть PDF"}), 400
            
            # Проверяем, что файл находится внутри базовой директории
            try:
                pdf_path.resolve().relative_to(base_dir.resolve())
            except ValueError:
                return jsonify({"error": "Недопустимый путь к файлу"}), 400
            
            # Получаем информацию о PDF через pdfplumber
            try:
                import pdfplumber
                print(f"DEBUG: Открываю PDF: {pdf_path}")
                with pdfplumber.open(str(pdf_path)) as pdf:
                    pages_info = []
                    for page in pdf.pages:
                        pages_info.append({
                            "width": page.width,
                            "height": page.height
                        })
                    
                    print(f"DEBUG: PDF содержит {len(pages_info)} страниц")
                    return jsonify({
                        "success": True,
                        "pdf_file": pdf_filename,
                        "total_pages": len(pages_info),
                        "pages": pages_info
                    })
            except ImportError as e:
                print(f"ERROR: pdfplumber не установлен: {e}")
                return jsonify({"error": "pdfplumber не установлен"}), 500
            except Exception as e:
                import traceback
                error_msg = f"Ошибка при чтении PDF: {str(e)}\n{traceback.format_exc()}"
                print(f"ERROR: {error_msg}")
                return jsonify({"error": f"Ошибка при чтении PDF: {str(e)}"}), 500
        
        except Exception as e:
            return jsonify({"error": f"Ошибка: {str(e)}"}), 500
    

    @app.route("/api/pdf-image/<path:pdf_filename>")
    def api_pdf_image(pdf_filename: str):
        """API endpoint для получения изображения страницы PDF."""
        try:
            # Безопасность: проверяем путь
            if ".." in pdf_filename or pdf_filename.startswith("/") or pdf_filename.startswith("\\"):
                print(f"ERROR: Недопустимый путь: {pdf_filename}")
                abort(404)
            
            # Файл из input_files
            session_input_dir = _session_input_dir()
            pdf_path = session_input_dir / pdf_filename
            base_dir = session_input_dir
            
            if not pdf_path.exists() or not pdf_path.is_file():
                print(f"ERROR: Файл не найден: {pdf_path}")
                abort(404)
            
            if pdf_path.suffix.lower() != ".pdf":
                print(f"ERROR: Не PDF файл: {pdf_path}")
                abort(404)
            
            # Проверяем, что файл находится внутри базовой директории
            try:
                pdf_path.resolve().relative_to(base_dir.resolve())
            except ValueError:
                print(f"ERROR: Файл вне базовой директории: {pdf_path}")
                abort(404)
            
            # Получаем номер страницы из query параметра
            page_num = request.args.get('page', '0')
            try:
                page_num = int(page_num)
            except ValueError:
                page_num = 0
            
            print(f"DEBUG: Запрос изображения страницы {page_num} из {pdf_filename}")
            
            # Конвертируем страницу PDF в изображение
            try:
                from pdf2image import convert_from_path
                print(f"DEBUG: pdf2image доступен, конвертирую страницу {page_num + 1}")
                images = convert_from_path(
                    str(pdf_path),
                    first_page=page_num + 1,
                    last_page=page_num + 1,
                    dpi=150
                )
                
                if not images:
                    print(f"ERROR: Не удалось получить изображение для страницы {page_num + 1}")
                    abort(404)
                
                print(f"DEBUG: Получено изображение размером {images[0].size}")
                
                # Сохраняем изображение во временный буфер
                from io import BytesIO
                img_buffer = BytesIO()
                images[0].save(img_buffer, format='PNG')
                img_buffer.seek(0)
                
                return send_file(img_buffer, mimetype='image/png')
            except ImportError as e:
                print(f"ERROR: pdf2image не установлен: {e}")
                # Возвращаем пустое изображение 1x1 пиксель вместо ошибки
                from io import BytesIO
                from PIL import Image
                img = Image.new('RGB', (1, 1), color='white')
                img_buffer = BytesIO()
                img.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                return send_file(img_buffer, mimetype='image/png')
            except Exception as e:
                import traceback
                error_msg = f"Ошибка при конвертации: {str(e)}\n{traceback.format_exc()}"
                print(f"ERROR: {error_msg}")
                # Возвращаем пустое изображение вместо ошибки
                from io import BytesIO
                from PIL import Image
                img = Image.new('RGB', (1, 1), color='white')
                img_buffer = BytesIO()
                img.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                return send_file(img_buffer, mimetype='image/png')
        
        except Exception as e:
            import traceback
            error_msg = f"Ошибка: {str(e)}\n{traceback.format_exc()}"
            print(f"ERROR: {error_msg}")
            # Возвращаем пустое изображение вместо ошибки
            try:
                from io import BytesIO
                from PIL import Image
                img = Image.new('RGB', (1, 1), color='white')
                img_buffer = BytesIO()
                img.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                return send_file(img_buffer, mimetype='image/png')
            except:
                abort(500)
    

    @app.route("/api/pdf-extract-text", methods=["POST"])
    def api_pdf_extract_text():
        """API endpoint для извлечения текста из выделенных областей PDF."""
        try:
            data = request.get_json()
            pdf_filename = data.get("pdf_file")
            selections = data.get("selections", [])
            options_dict = data.get("options", {}) or {}

            print(f"DEBUG: Обработка выделенного текста из {len(selections)} областей")
            print(f"DEBUG: PDF файл: {pdf_filename}")

            if not pdf_filename:
                return jsonify({"error": "Не указан файл PDF"}), 400

            if not selections:
                return jsonify({"error": "Нет выделенных областей"}), 400

            if ".." in pdf_filename or pdf_filename.startswith("/") or pdf_filename.startswith("\\"):
                return jsonify({"error": "Недопустимый путь к файлу"}), 400

            session_input_dir = _session_input_dir()
            pdf_path = session_input_dir / pdf_filename

            if not pdf_path.exists() or not pdf_path.is_file():
                print(f"ERROR: Файл не найден: {pdf_path}")
                return jsonify({"error": f"Файл не найден: {pdf_filename}"}), 404

            try:
                pdf_path.resolve().relative_to(session_input_dir.resolve())
            except ValueError:
                return jsonify({"error": "Недопустимый путь к файлу"}), 400

            options = ExtractionOptions.from_dict(options_dict)

            try:
                import pdfplumber

                extractor = PDFTextExtractor(options)
                extracted = []

                print(f"DEBUG: Открываем PDF: {pdf_path}")
                with pdfplumber.open(str(pdf_path)) as pdf:
                    print(f"DEBUG: PDF содержит {len(pdf.pages)} страниц")

                    for selection in selections:
                        page_num = selection.get("page", 0)
                        if page_num >= len(pdf.pages):
                            print(f"WARNING: Страница {page_num} вне диапазона")
                            continue

                        page = pdf.pages[page_num]
                        result = extractor.extract_from_selection(page, selection)
                        extracted.append(result)

                print(f"DEBUG: Извлечено текста из {len(extracted)} областей")

                merged = {}
                if options.merge_by_field:
                    for item in sorted(
                        extracted, key=lambda i: (i.get("field_id") or "", i.get("page", 0))
                    ):
                        field = item.get("field_id")
                        text = item.get("text")
                        if not field or not text or text == "(Текст не найден)":
                            continue
                        merged.setdefault(field, [])
                        merged[field].append(text)
                    merged = {k: "\n".join(v).strip() for k, v in merged.items()}

                return jsonify(
                    {
                        "success": True,
                        "extracted": extracted,
                        "merged": merged if options.merge_by_field else None,
                    }
                )

            except ImportError as e:
                print(f"ERROR: pdfplumber не установлен: {e}")
                return jsonify({"error": "pdfplumber не установлен"}), 500
            except Exception as e:
                import traceback

                error_msg = f"Ошибка при извлечении текста: {str(e)}\n{traceback.format_exc()}"
                print(f"ERROR: {error_msg}")
                return jsonify({"error": f"Ошибка при извлечении текста: {str(e)}"}), 500

        except Exception as e:
            import traceback

            error_msg = f"Ошибка: {str(e)}\n{traceback.format_exc()}"
            print(f"ERROR: {error_msg}")
            return jsonify({"error": f"Ошибка: {str(e)}"}), 500

    @app.route("/api/pdf-save-coordinates", methods=["POST"])
    def api_pdf_save_coordinates():
        """API endpoint для сохранения координат выделенных областей в JSON файл."""
        try:
            data = request.get_json()
            pdf_filename = data.get("pdf_file")
            total_pages = data.get("total_pages", 0)
            selections = data.get("selections", [])
            
            if not pdf_filename:
                return jsonify({"error": "Не указан файл PDF"}), 400
            
            if not selections:
                return jsonify({"error": "Нет выделенных областей для сохранения"}), 400
            
            # Создаем имя файла для сохранения координат
            pdf_path = Path(pdf_filename)
            output_filename = pdf_path.stem + "_bbox.json"
            issue_name = pdf_path.parts[0] if pdf_path.parts else "unknown"
            output_path = (input_files_dir / issue_name / "state" / output_filename)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Подготавливаем данные для сохранения
            output_data = {
                "pdf_file": pdf_filename,
                "total_pages": total_pages,
                "selections": []
            }
            
            for selection in selections:
                output_data["selections"].append({
                    "page": selection["page"],
                    "bbox": {
                        "x1": round(selection["pdf_x1"], 2),
                        "y1": round(selection["pdf_y1"], 2),
                        "x2": round(selection["pdf_x2"], 2),
                        "y2": round(selection["pdf_y2"], 2)
                    },
                    "text": selection.get("text", ""),
                    "field_id": selection.get("field_id")
                })
            
            # Сохраняем в JSON
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            return jsonify({
                "success": True,
                "file_path": str(output_path),
                "file_name": output_filename
            })
        
        except Exception as e:
            return jsonify({"error": f"Ошибка при сохранении: {str(e)}"}), 500
    

    @app.route("/pdf/<path:pdf_filename>")
    def serve_pdf(pdf_filename: str):
        """Маршрут для отдачи PDF файлов."""
        # Безопасность: проверяем, что путь не содержит опасные символы
        if ".." in pdf_filename or pdf_filename.startswith("/") or pdf_filename.startswith("\\"):
            abort(404)
        
        session_input_dir = _session_input_dir()
        pdf_path = session_input_dir / pdf_filename
        
        if not pdf_path.exists() or not pdf_path.is_file():
            abort(404)
        
        # Проверяем расширение
        if pdf_path.suffix.lower() != ".pdf":
            abort(404)
        
        # Проверяем, что файл находится внутри input_files_dir
        try:
            pdf_path.resolve().relative_to(session_input_dir.resolve())
        except ValueError:
            abort(404)
        
        return send_file(pdf_path, mimetype='application/pdf')
    
    # ==================== BBOX Templates API ====================
    
    def _bbox_templates_disabled_response():
        return jsonify(
            {
                "success": False,
                "disabled": True,
                "error": "Функция шаблонов bbox отключена.",
            }
        ), 410

    @app.route("/api/bbox-templates/suggestions", methods=["GET"])
    def get_bbox_suggestions():
        return _bbox_templates_disabled_response()

    @app.route("/api/bbox-templates/save", methods=["POST"])
    def save_bbox_template():
        return _bbox_templates_disabled_response()

    @app.route("/api/bbox-templates/list", methods=["GET"])
    def list_bbox_templates():
        return _bbox_templates_disabled_response()

    @app.route("/api/bbox-templates/delete", methods=["POST"])
    def delete_bbox_template():
        return _bbox_templates_disabled_response()

    @app.route("/api/bbox-templates/reset-field", methods=["POST"])
    def reset_field_template():
        return _bbox_templates_disabled_response()

    @app.route("/api/bbox-templates/apply", methods=["POST"])
    def apply_bbox_template():
        return _bbox_templates_disabled_response()


