#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Модуль для конвертации PDF в HTML для веб-интерфейса разметки.
Сохраняет структуру (абзацы/служебные строки) и "интеллектуально"
склеивает переносы и разрывы строк.

Основная идея: сначала извлекаем сырые строки, затем:
1) режем строки на смысловые части (метаданные / служебные секции),
2) склеиваем в абзацы по эвристикам,
3) экранируем и оборачиваем в <p>.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple
from collections import Counter
import re
import os

# Попытка импорта библиотек для работы с PDF
PDFPLUMBER_AVAILABLE = False
PYMUPDF_AVAILABLE = False

try:
    import pdfplumber  # type: ignore
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    pass

try:
    import fitz  # type: ignore  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    pass


# ----------------------------
# Regex & правила сегментации
# ----------------------------

@dataclass(frozen=True)
class Patterns:
    # "Токены" внутри строки: DOI / email / url / тип статьи
    doi: re.Pattern
    article_type: re.Pattern
    email: re.Pattern
    url: re.Pattern

    # "Секции", которые почти всегда должны быть отдельным блоком
    annotation_head: re.Pattern
    keywords_head: re.Pattern
    citation_head: re.Pattern
    references_head: re.Pattern

    # Общие признаки служебности/заголовка
    meta_any: re.Pattern
    upper_ratio_min_len: int = 20
    upper_ratio_threshold: float = 0.7


PATTERNS = Patterns(
    doi=re.compile(r"DOI:\s*[0-9]+\.[0-9]+/[A-Z0-9\-]+", re.IGNORECASE),
    article_type=re.compile(
        r"(Оригинальная\s+статья|Original\s+Article|"
        r"Обзорная\s+статья|Review\s+Article|"
        r"Краткое\s+сообщение|Short\s+Message)"
        r"(\s*/\s*(Оригинальная\s+статья|Original\s+Article|"
        r"Обзорная\s+статья|Review\s+Article|"
        r"Краткое\s+сообщение|Short\s+Message))?",
        re.IGNORECASE,
    ),
    email=re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", re.IGNORECASE),
    url=re.compile(r"https?://[^\s]+", re.IGNORECASE),

    annotation_head=re.compile(r"\b(Аннотация|Abstract)\.?\s*", re.IGNORECASE),
    citation_head=re.compile(r"(For\s+citation|Для\s+цитирования|For\s+Citation):\s*", re.IGNORECASE),
    keywords_head=re.compile(
        r"\b(Ключевые\s+слова|Keywords)\s*[.:]?\s*",
        re.IGNORECASE,
    ),
    references_head=re.compile(
        r"^(Источники|Литература|References|Список\s+литературы|Bibliography|Библиография)"
        r"(\s*и\s+источники)?[.:]?\s*",
        re.IGNORECASE,
    ),

    meta_any=re.compile(r"(doi|https?://|@|©|\b\d{4}\s*г\.)", re.IGNORECASE),
)

# Заголовки разделов, которые часто не пишутся КАПСОМ.
SECTION_HEADERS = re.compile(
    r"^(Введение|Методы?|Результаты|Обсуждение|Заключение|Выводы|"
    r"Introduction|Methods?|Results?|Discussion|Conclusion|Background|"
    r"Materials?\s+and\s+Methods?|Acknowledgements?)\.?\s*$",
    re.IGNORECASE,
)

# Единые параметры токенизации для pdfplumber (во всех ветках извлечения).
PDFPLUMBER_X_TOLERANCE = 1.0
PDFPLUMBER_Y_TOLERANCE = 2.0

# Regex для normalize_references_block вынесены на уровень модуля
# (чтобы не компилировать их при каждом вызове).
REFERENCE_BLOCK_REGEX: Dict[str, re.Pattern] = {
    "RE_REF_HEADER": re.compile(
        r"^(СПИСОК\s+ЛИТЕРАТУРЫ|ЛИТЕРАТУРА|REFERENCES|BIBLIOGRAPHY|СПИСОК\s+ИСТОЧНИКОВ)\b",
        re.IGNORECASE,
    ),
    "RE_REF_END": re.compile(
        r"^(Поступила|Рукопись|Received|Accepted|Информация\s+об\s+авторе|Information\s+about\s+the\s+author)\b",
        re.IGNORECASE,
    ),
    "RE_BIB_NUM": re.compile(r"^\s*(\[\d{1,4}\]|\d{1,4}[.)])\s+"),
    "RE_RU_AUTHOR_START": re.compile(
        r"^\s*[А-ЯЁ][а-яё-]+(?:\s+[А-ЯЁ][а-яё-]+){0,2}\s+[А-ЯЁ]\.\s*[А-ЯЁ]\.\b"
    ),
    "RE_EN_AUTHOR_START": re.compile(
        r"^\s*[A-Z][A-Za-z\-']+(?:\s+[A-Z][A-Za-z\-']+){0,2},?\s+(?:[A-Z]\.\s*){1,3}\b"
    ),
    "RE_YEAR": re.compile(r"\b(18|19|20)\d{2}\b"),
    "RE_DOI": re.compile(r"\bdoi\s*:\s*|https?://doi\.org/", re.IGNORECASE),
    "RE_PAGES": re.compile(r"\b(pp?\.\s*\d+([–-]\d+)?|с\.\s*\d+([–-]\d+)?)\b", re.IGNORECASE),
    "RE_VOL_ISS": re.compile(r"\b(т\.\s*\d+|vol\.\s*\d+|№\s*\d+|no\.\s*\d+|issue\s*\d+)\b", re.IGNORECASE),
    "RE_PUBLISHER": re.compile(r"\b(изд\.|издательство|publ\.|press|университет|univ\.)\b", re.IGNORECASE),
    "RE_BIB_CONTINUATION": re.compile(
        r"^\s*(\(|\[|Т\.\s*\d+|Vol\.\s*\d+|\(In\s+Russ\.\)|In\s+Russ\.)",
        re.IGNORECASE,
    ),
    "RE_URL_LABEL": re.compile(r"^\s*URL\s*:?\s*$", re.IGNORECASE),
    "RE_URL_PREFIX": re.compile(r"^https?://\S*$", re.IGNORECASE),
    "RE_URL_LINE": re.compile(r"^https?://\S+$", re.IGNORECASE),
    "RE_DOI_PREFIX_BROKEN": re.compile(r"(DOI:\s*\S+\/)\s*$", re.IGNORECASE),
    "RE_DOI_SUFFIX": re.compile(r"^[A-Z0-9][A-Z0-9\-./]+$", re.IGNORECASE),
    "RE_HEADER_FOOTER_HINT": re.compile(
        r"\b(19|20)\d{2}\b|№\s*\d+|\bpp?\.\b|\bс\.\b|Славяноведение|Slavic Studies",
        re.IGNORECASE,
    ),
}


# ----------------------------
# Утилиты
# ----------------------------

def _escape_html(text: str) -> str:
    """Минимальное экранирование HTML (быстро, без внешних зависимостей)."""
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
    )


def _normalize_spaces(text: str) -> str:
    """Схлопывает множественные пробелы и тримит."""
    return re.sub(r"\s+", " ", text).strip()


def _restore_missing_spaces(text: str) -> str:
    """
    Пытается восстановить пробелы, потерянные при PDF-извлечении.
    Консервативные правила:
    - пробел после знаков препинания перед буквой,
    - пробел на стыке строчная->ЗАГЛАВНАЯ (часто склейка слов/ФИО).
    """
    if not text:
        return text
    t = text
    t = re.sub(r"([,;:!?])([A-Za-zА-Яа-яЁё])", r"\1 \2", t)
    # Более осторожно: разделяем только "слово(2+)->Слово", не трогаем mRNA/pH и похожие токены.
    t = re.sub(r"([a-zа-яё]{2,})([A-ZА-ЯЁ][a-zа-яё])", r"\1 \2", t)
    # Сноски после кавычек/скобок: »1 -> »[1]
    t = re.sub(r'([»"\')\]])\s*(\d{1,2})(?=\s|$)', r"\1[\2]", t)
    return _normalize_spaces(t)


def _upper_ratio(line: str) -> float:
    letters = [c for c in line if c.isalpha()]
    if not letters:
        return 0.0
    upp = sum(1 for c in letters if c.isupper())
    return upp / len(letters)


def _is_upper_header_fragment(line: str) -> bool:
    """
    Короткий фрагмент заголовка в верхнем регистре.
    Нужен, чтобы склеивать многострочные CAPS-заголовки.
    """
    s = _normalize_spaces(line)
    if not s:
        return False
    if len(s) < 8 or len(s) > 140:
        return False
    if s.endswith((".", "!", "?", ";", ":")):
        return False
    return _upper_ratio(s) >= 0.75


def _extract_words_pdfplumber(obj) -> List[Dict[str, object]]:
    """Единая конфигурация extract_words для всех веток pdfplumber."""
    try:
        return obj.extract_words(
            x_tolerance=PDFPLUMBER_X_TOLERANCE,
            y_tolerance=PDFPLUMBER_Y_TOLERANCE,
            keep_blank_chars=False,
            use_text_flow=False,
        ) or []
    except Exception:
        return []


def _find_header_boundary(words: List[Dict[str, object]], page_height: float) -> float:
    """
    Динамически оценивает границу шапки: ищет максимальный вертикальный gap
    в верхней половине страницы.
    """
    if not words or page_height <= 0:
        return max(0.0, page_height * 0.2)

    tops = sorted({round(float(w.get("top", 0) or 0), 1) for w in words})
    if len(tops) < 2:
        return max(0.0, page_height * 0.2)

    max_gap = 0.0
    boundary = page_height * 0.2
    upper_limit = page_height * 0.5
    min_gap = max(6.0, page_height * 0.01)

    for i in range(1, len(tops)):
        if tops[i] > upper_limit:
            break
        gap = tops[i] - tops[i - 1]
        if gap > max_gap and gap >= min_gap:
            max_gap = gap
            boundary = tops[i - 1]

    return max(0.0, min(page_height * 0.45, boundary))


def _is_strict_standalone_metadata(line: str) -> bool:
    """
    Строки, которые почти всегда должны быть отдельным блоком и не накапливать продолжение.
    """
    s = line.strip()
    return bool(
        PATTERNS.doi.search(s)
        or PATTERNS.email.search(s)
        or PATTERNS.url.search(s)
        or PATTERNS.article_type.search(s)
    )


def _is_editorial_date_line(line: str) -> bool:
    s = _normalize_spaces(line)
    if not s:
        return False
    return bool(
        re.match(
            r"^(Поступила|Поступил|После доработки|Принята к публикации|Received|Revised|Accepted)\b",
            s,
            re.IGNORECASE,
        )
    )


def _is_author_line(line: str) -> bool:
    s = _normalize_spaces(line)
    if not s or PATTERNS.email.search(s) or PATTERNS.url.search(s):
        return False

    initials_count = len(re.findall(r"[A-ZА-ЯЁ]\.", s))
    surname_count = len(re.findall(r"\b[A-ZА-ЯЁ][a-zа-яё-]{2,}\b", s))
    has_separator = "," in s or ";" in s or " и " in s.lower() or " and " in s.lower()

    if initials_count >= 2 and surname_count >= 2 and has_separator:
        return True
    if initials_count >= 4 and surname_count >= 2:
        return True
    return False


def _is_affiliation_line(line: str) -> bool:
    s = _normalize_spaces(line)
    if not s:
        return False

    lower = s.lower()
    affiliation_keywords = (
        "институт",
        "универс",
        "академ",
        "лаборатор",
        "центр",
        "музей",
        "факульт",
        "кафедр",
        "отдел",
        "department",
        "faculty",
        "institute",
        "university",
        "academy",
        "laborator",
        "centre",
        "center",
        "school",
        "museum",
        "research",
    )

    if not any(keyword in lower for keyword in affiliation_keywords):
        return False
    if len(s.split()) > 28:
        return False
    if re.match(r"^[\d*#,\.\s]+", s):
        return True
    return "," in s or PATTERNS.meta_any.search(s) is None


def _is_front_matter_standalone(line: str) -> bool:
    s = _normalize_spaces(line)
    if not s:
        return False
    if _is_strict_standalone_metadata(s):
        return True
    if _is_editorial_date_line(s):
        return True
    if _is_author_line(s):
        return True
    if _is_affiliation_line(s):
        return True
    if re.match(r"^\*?\s*e-?mail\s*[:\-]?\s*", s, re.IGNORECASE):
        return True
    return False


def _is_reference_heading(line: str) -> bool:
    return bool(REFERENCE_BLOCK_REGEX["RE_REF_HEADER"].match(_normalize_spaces(line)))


def _is_reference_end_marker(line: str) -> bool:
    return bool(REFERENCE_BLOCK_REGEX["RE_REF_END"].match(_normalize_spaces(line)))


def _is_reference_entry_start(line: str) -> bool:
    s = _normalize_spaces(line)
    if not s:
        return False
    if REFERENCE_BLOCK_REGEX["RE_BIB_NUM"].match(s):
        return True
    if (
        REFERENCE_BLOCK_REGEX["RE_RU_AUTHOR_START"].match(s)
        or REFERENCE_BLOCK_REGEX["RE_EN_AUTHOR_START"].match(s)
    ) and (
        REFERENCE_BLOCK_REGEX["RE_YEAR"].search(s)
        or REFERENCE_BLOCK_REGEX["RE_DOI"].search(s)
        or REFERENCE_BLOCK_REGEX["RE_VOL_ISS"].search(s)
        or REFERENCE_BLOCK_REGEX["RE_PAGES"].search(s)
    ):
        return True
    return False


def _is_safe_header_footer_candidate(line: str) -> bool:
    s = _normalize_spaces(line)
    if not s:
        return False
    if len(s) > 80:
        return False
    if _is_front_matter_standalone(s):
        return False
    if _is_reference_heading(s) or _is_reference_end_marker(s):
        return False
    if PATTERNS.doi.search(s) or PATTERNS.email.search(s) or PATTERNS.url.search(s):
        return False
    if len(s.split()) >= 8 and _upper_ratio(s) < 0.55:
        return False
    return True


# ----------------------------
# Интеллектуальная сегментация
# ----------------------------

def _is_likely_metadata_or_header(line: str) -> bool:
    """
    Грубая эвристика: служебные строки (метаданные, заголовки, шапки секций).
    """
    line = line.strip()
    if not line:
        return True

    # Очень короткие строки часто служебные (номер страницы, колонтитулы, и т.п.)
    if len(line) < 10:
        return True

    if PATTERNS.meta_any.search(line):
        return True

    # Тип статьи
    if PATTERNS.article_type.search(line):
        return True

    # For citation / Для цитирования
    if PATTERNS.citation_head.search(line):
        return True

    # Источники / Литература / References
    if PATTERNS.references_head.search(line):
        return True

    # Стандартные заголовки разделов (без КАПСА)
    if SECTION_HEADERS.match(line):
        return True

    # В основном ВЕРХНИЙ РЕГИСТР → похоже на заголовок
    if len(line) >= PATTERNS.upper_ratio_min_len and _upper_ratio(line) >= PATTERNS.upper_ratio_threshold:
        return True

    return False


def _extract_tail_section(line: str, head_pattern: re.Pattern) -> Optional[Tuple[str, str]]:
    """
    Если в строке встречается "голова" секции, возвращает:
    (prefix_before_head, tail_from_head)
    """
    m = head_pattern.search(line)
    if not m:
        return None
    start = m.start()
    prefix = line[:start].strip()
    tail = line[start:].strip()
    return prefix, tail


def _find_inline_tokens(line: str) -> List[Tuple[int, int, str]]:
    """
    Находит "токены" внутри строки (email/url/doi/тип статьи) и возвращает
    список (start, end, text) отсортированный по start.

    Важно: это НЕ "секции", а именно inline-элементы.
    """
    spans: List[Tuple[int, int, str]] = []

    for pat in (PATTERNS.email, PATTERNS.url, PATTERNS.doi, PATTERNS.article_type):
        for m in pat.finditer(line):
            spans.append((m.start(), m.end(), m.group(0).strip()))

    # Убираем перекрытия: оставляем более "длинные" на совпадающих стартах
    spans.sort(key=lambda x: (x[0], -(x[1] - x[0])))
    filtered: List[Tuple[int, int, str]] = []
    last_end = -1
    for s, e, t in spans:
        if s < last_end:
            continue
        filtered.append((s, e, t))
        last_end = e

    return filtered


def _split_metadata_line(line: str, _depth: int = 0) -> List[str]:
    """
    Разбивает строку на смысловые части.
    Приоритет:
    1) "Хвостовые секции" (Аннотация/Abstract, For citation, References/Литература) → отдельный блок.
    2) Inline-токены (email/url/doi/тип статьи) → выделяются, но без агрессивного дробления.
    """
    line = line.strip()
    if not line:
        return []
    if _depth > 10:
        return [line]

    # 1) Хвостовые секции — если встретились, режем на prefix + tail (tail отдельным блоком)
    # Приоритет: аннотация и ключевые слова обрабатываются первыми, чтобы гарантировать их отделение
    for head in (PATTERNS.annotation_head, PATTERNS.keywords_head, PATTERNS.citation_head, PATTERNS.references_head):
        tail = _extract_tail_section(line, head)
        if tail:
            prefix, section = tail
            parts: List[str] = []
            if prefix:
                # prefix еще может содержать inline-токены → обработаем ниже
                parts.extend(_split_metadata_line(prefix, _depth + 1))
            parts.append(section)
            return [p for p in parts if p.strip()]

    # 2) Inline токены
    spans = _find_inline_tokens(line)
    if not spans:
        return [line]

    parts: List[str] = []
    cursor = 0
    for s, e, token in spans:
        before = line[cursor:s].strip()
        if before:
            parts.append(before)
        parts.append(token)
        cursor = e

    after = line[cursor:].strip()
    if after:
        parts.append(after)

    # Финальная чистка
    return [p for p in (p.strip() for p in parts) if p]


def _should_merge_with_previous(prev: str, cur: str) -> bool:
    """
    Эвристика склейки строк внутри одного абзаца.
    """
    prev = prev.rstrip()
    cur = cur.lstrip()

    # Если текущая строка сама по себе служебная — не склеиваем
    if _is_likely_metadata_or_header(cur):
        return False

    # Примечания в скобках на отдельной строке (In Russ.), (In English), (На рус. яз.) и т.п.
    if re.match(r'^\([^)]+\)\.?\s*$', cur, re.IGNORECASE):
        return True

    # Библиографические данные: номера страниц, год, том (например: "103/104. 2002. S. 194–202.")
    # Паттерны: номер/номер, год, страницы
    if re.match(r'^\s*\d+/\d+\.\s*\d{4}\.', cur) or re.match(r'^\s*\d{4}\.\s*[Ss]\.\s*\d+', cur):
        return True
    # Только страницы: "S. 194–202." или "с. 194–202." или "S. 270–282." или "Pp. 10-20."
    if re.match(r'^\s*[SsCcPp]+\.?\s*\d+[–-]\d+\.?\s*$', cur, re.IGNORECASE):
        return True
    # Страницы с одним числом: "S. 194." или "с. 194."
    if re.match(r'^\s*[SsCcPp]+\.?\s*\d+\.?\s*$', cur, re.IGNORECASE):
        return True
    # Количество страниц: "386 p." или "200 с." или "150 pp."
    if re.match(r'^\s*\d+\s*[PpСс]+\.?\s*$', cur, re.IGNORECASE):
        return True
    # Номера страниц без префикса: "419–434." или "10-20." или "194–202."
    if re.match(r'^\s*\d+[–-]\d+\.?\s*$', cur):
        return True
    # Только том/номер: "103/104." или "Vol. 1, No. 2."
    if re.match(r'^\s*\d+/\d+\.', cur) or re.match(r'^\s*(Vol\.|Т\.|№)\s*\d+', cur, re.IGNORECASE):
        return True

    # Отдельное короткое слово (1-2 слова) с маленькой буквы — всегда присоединяем
    cur_words = cur.split()
    if len(cur_words) <= 2 and cur and cur[0].islower():
        return True

    # Если предыдущее НЕ заканчивается на конец предложения/абзаца
    if not prev.endswith((".", "!", "?", ":", ";")):
        if len(cur) < 40:
            return True
        if cur and cur[0].islower():
            return True

    # Если предыдущее заканчивается на запятую/двоеточие/точку с запятой
    if prev.endswith((",", ":", ";")):
        if len(cur) < 50 or (cur and cur[0].islower()):
            return True

    # Если предыдущее заканчивается на точку, но следующая начинается со строчной и короткая
    if prev.endswith(".") and len(cur) < 30 and cur and cur[0].islower():
        return True

    return False


def _should_start_new_paragraph(prev: str, cur: str, current_len: int) -> bool:
    """
    Эвристика начала нового абзаца.
    """
    cur = cur.strip()
    if _is_likely_metadata_or_header(cur):
        return True

    prev = prev.rstrip()

    # Конец предложения + следом "нормальная" новая фраза с заглавной и достаточной длиной
    if prev.endswith((".", "!", "?")):
        if cur and cur[0].isupper() and len(cur) > 20 and current_len > 150:
            return True

    # Слишком длинный абзац → резать при начале новой фразы
    if current_len > 500 and cur and cur[0].isupper():
        return True

    return False


def _pre_glue_special_pairs(lines: List[str]) -> List[str]:
    """
    До умной сегментации склеиваем заведомо связанные пары строк.
    """
    out: List[str] = []
    i = 0
    while i < len(lines):
        cur = lines[i].strip()
        nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""

        # "Ссылка" + "для цитирования: ..."
        if re.fullmatch(r"Ссылка", cur, re.IGNORECASE) and re.match(r"для\s+цитирования\s*:", nxt, re.IGNORECASE):
            out.append(f"{cur} {nxt}")
            i += 2
            continue

        # "URL:" + следующая строка с http(s)://
        if re.fullmatch(r"URL\s*:", cur, re.IGNORECASE) and re.match(r"https?://", nxt, re.IGNORECASE):
            out.append(f"{cur} {nxt}")
            i += 2
            continue

        # "DOI: 10.7868/" + "S294..."  (встречается часто)
        if re.search(r"\bDOI:\s*[0-9]+\.[0-9]+/\s*$", cur, re.IGNORECASE) and re.fullmatch(r"[A-Z0-9\-]+", nxt):
            out.append(f"{cur}{nxt}")
            i += 2
            continue

        out.append(cur)
        i += 1

    return out


def _merge_lines_into_paragraphs(lines: List[str]) -> List[str]:
    """
    Основная функция "интеллектуального форматирования":
    - пустая строка завершает абзац
    - каждую строку сначала делим на смысловые части (_split_metadata_line)
    - переносы слов (конец на '-') склеиваем
    - метаданные/шапки секций всегда отдельными абзацами
    """
    if not lines:
        return []
    
    # Предварительная склейка специальных пар строк
    lines = _pre_glue_special_pairs(lines)

    paragraphs: List[str] = []
    current: List[str] = []
    in_references = False

    def flush_current() -> None:
        nonlocal current
        if not current:
            return
        text = _normalize_spaces(" ".join(current))
        if text:
            paragraphs.append(text)
        current = []

    for raw in lines:
        raw = raw.strip()

        # Пустая строка → граница абзаца
        if not raw:
            flush_current()
            continue

        # Разбиваем строку на части (метаданные / секции / inline токены)
        parts = _split_metadata_line(raw)

        for part in parts:
            part = part.strip()
            if not part:
                continue

            if _is_reference_heading(part):
                flush_current()
                paragraphs.append(_normalize_spaces(part))
                current = []
                in_references = True
                continue

            if in_references:
                if _is_reference_end_marker(part):
                    flush_current()
                    in_references = False
                elif _is_reference_entry_start(part):
                    flush_current()
                    current = [part]
                    continue
                else:
                    if not current:
                        current = [part]
                    else:
                        current.append(part)
                    continue

            if _is_front_matter_standalone(part):
                flush_current()
                paragraphs.append(_normalize_spaces(part))
                current = []
                continue

            # Перенос слова: "обрезаем" дефис и не флашим, ждём следующую часть/строку
            if part.endswith("-") and len(part) > 1:
                current.append(part[:-1].strip())
                continue

            # Если начинается Аннотация/Abstract — строго отдельным абзацем
            # Проверяем как match (начало строки), так и search (внутри строки)
            if PATTERNS.annotation_head.match(part) or PATTERNS.annotation_head.search(part):
                flush_current()
                current = [part]
                continue
            
            # Если начинается Ключевые слова/Keywords — строго отдельным абзацем
            if PATTERNS.keywords_head.match(part) or PATTERNS.keywords_head.search(part):
                flush_current()
                current = [part]
                continue

            if not current:
                current = [part]
                continue

            prev = current[-1]
            cur_text = _normalize_spaces(" ".join(current))
            cur_len = len(cur_text)

            if _is_likely_metadata_or_header(part):
                # Склеиваем последовательные CAPS-заголовки в один абзац.
                flush_current()
                if paragraphs and _is_upper_header_fragment(paragraphs[-1]) and _is_upper_header_fragment(part):
                    paragraphs[-1] = _normalize_spaces(f"{paragraphs[-1]} {part}")
                    continue
                if _is_strict_standalone_metadata(part):
                    paragraphs.append(_normalize_spaces(part))
                    current = []
                    continue
                current = [part]
                continue

            if _should_start_new_paragraph(prev, part, cur_len):
                flush_current()
                current = [part]
                continue

            if _should_merge_with_previous(prev, part):
                current.append(part)
            else:
                flush_current()
                current = [part]

    flush_current()
    return paragraphs


# ----------------------------
# Удаление колонтитулов
# ----------------------------

def _remove_headers_footers(lines_by_page: List[List[str]]) -> List[str]:
    """
    Удаляет колонтитулы (headers/footers) из извлеченных строк.
    
    Колонтитулы определяются по:
    1. Частоте повторения на разных страницах
    2. Позиции на странице (первые/последние строки)
    3. Паттернам (номера страниц, названия журналов)
    
    Args:
        lines_by_page: Список списков строк, где каждый внутренний список - строки одной страницы
        
    Returns:
        Плоский список строк без колонтитулов
    """
    if not lines_by_page:
        return []
    
    # Если только одна страница, не фильтруем (может быть ошибкой)
    if len(lines_by_page) < 2:
        return [line for page_lines in lines_by_page for line in page_lines]
    
    # Нормализуем строки для частотного анализа (убираем лишние пробелы, приводим к нижнему регистру)
    def normalize_for_freq(s: str) -> str:
        return re.sub(r'\s+', ' ', s).strip().lower()
    
    # Считаем частоту появления каждой строки на разных страницах
    line_frequency: dict[str, int] = Counter()
    line_positions: dict[str, List[Tuple[int, int]]] = {}  # (page_idx, line_idx_in_page)
    
    for page_idx, page_lines in enumerate(lines_by_page):
        for line_idx, line in enumerate(page_lines):
            normalized = normalize_for_freq(line)
            if normalized:
                line_frequency[normalized] += 1
                if normalized not in line_positions:
                    line_positions[normalized] = []
                line_positions[normalized].append((page_idx, line_idx))
    
    # Определяем порог частоты для колонтитулов.
    # Используем "большинство страниц", чтобы не удалять полезные строки в коротких документах.
    min_pages_for_header = max(3, (len(lines_by_page) + 1) // 2)
    
    # Паттерны для колонтитулов
    # Паттерны для номеров страниц (их оставляем только первый)
    page_number_patterns = [
        re.compile(r'^\s*\d+\s*$', re.IGNORECASE),  # Только номер страницы
        re.compile(r'^стр\.\s*\d+', re.IGNORECASE),  # "стр. 123"
        re.compile(r'^page\s+\d+', re.IGNORECASE),  # "Page 123"
        re.compile(r'^\d+\s*/\s*\d+', re.IGNORECASE),  # "123 / 456"
    ]
    
    # Паттерны для других колонтитулов (удаляем все)
    other_header_footer_patterns = [
        re.compile(r'^№\s*\d+', re.IGNORECASE),  # "№ 123"
        re.compile(r'^no\.\s*\d+', re.IGNORECASE),  # "No. 123"
        re.compile(r'^\d{4}\s*г\.', re.IGNORECASE),  # "2024 г."
        re.compile(r'^\d{4}\s*$', re.IGNORECASE),  # Только год
    ]
    
    # Собираем строки для удаления
    lines_to_remove: set[Tuple[int, int]] = set()
    # Отслеживаем, оставили ли мы уже первый колонтитул с номером страницы
    first_page_number_kept = False
    
    # Сначала обрабатываем номера страниц - оставляем только первый
    for normalized_line, freq in line_frequency.items():
        # Проверяем, является ли это номером страницы
        is_page_number = any(pattern.match(normalized_line) for pattern in page_number_patterns)
        
        if is_page_number and freq >= min_pages_for_header:
            # Находим первое вхождение (самая ранняя страница, самая ранняя позиция)
            positions = sorted(line_positions[normalized_line])
            if positions and not first_page_number_kept:
                # Оставляем только первое вхождение
                first_page_number_kept = True
                # Удаляем все остальные вхождения этого номера страницы
                for page_idx, line_idx in positions[1:]:
                    lines_to_remove.add((page_idx, line_idx))
            elif positions:
                # Если уже оставили первый, удаляем все вхождения
                for page_idx, line_idx in positions:
                    lines_to_remove.add((page_idx, line_idx))
    
    # Теперь обрабатываем остальные колонтитулы
    for normalized_line, freq in line_frequency.items():
        # Пропускаем номера страниц (уже обработали)
        is_page_number = any(pattern.match(normalized_line) for pattern in page_number_patterns)
        if is_page_number:
            continue
        
        # Проверяем частоту
        if freq >= min_pages_for_header and _is_safe_header_footer_candidate(normalized_line):
            # Проверяем позицию на странице (первые 2 или последние 2 строки)
            for page_idx, line_idx in line_positions[normalized_line]:
                page_lines = lines_by_page[page_idx]
                if len(page_lines) > 0:
                    # Первые 2 строки или последние 2 строки страницы
                    if line_idx < 2 or line_idx >= len(page_lines) - 2:
                        lines_to_remove.add((page_idx, line_idx))
        
        # Проверяем паттерны других колонтитулов (не номера страниц) - удаляем все
        for pattern in other_header_footer_patterns:
            if pattern.match(normalized_line) and _is_safe_header_footer_candidate(normalized_line):
                for page_idx, line_idx in line_positions[normalized_line]:
                    lines_to_remove.add((page_idx, line_idx))
    
    # Собираем результат, исключая удаленные строки
    result: List[str] = []
    for page_idx, page_lines in enumerate(lines_by_page):
        for line_idx, line in enumerate(page_lines):
            if (page_idx, line_idx) not in lines_to_remove:
                result.append(line)
    
    return result


# ----------------------------
# Извлечение текста из PDF
# ----------------------------

def _detect_columns_pdfplumber_page(
    page,
    min_words_per_column: int = 10,
    gutter_ratio: float = 0.1,
) -> int:
    """Detect whether the page uses one or two text columns."""
    words = _extract_words_pdfplumber(page)

    width = float(getattr(page, "width", 0) or 0)
    if not words or width <= 0:
        return 1
    return _detect_columns_pdfplumber_words(
        words,
        width,
        min_words_per_column=min_words_per_column,
        gutter_ratio=gutter_ratio,
    )


def _detect_columns_pdfplumber_words(
    words: List[Dict[str, object]],
    width: float,
    min_words_per_column: int = 10,
    gutter_ratio: float = 0.1,
) -> int:
    if not words or width <= 0:
        return 1

    effective_min_words = min_words_per_column
    if len(words) < (min_words_per_column * 2):
        effective_min_words = max(3, len(words) // 4)

    center = width / 2.0
    gutter = max(0.0, min(0.4, float(gutter_ratio)))
    left_border = center * (1.0 - gutter)
    right_border = center * (1.0 + gutter)

    # Если в гаттере много слов, это скорее таблица/плотная верстка, а не 2 колонки.
    gutter_words = [
        w for w in words
        if left_border < float(w.get("x0", 0) or 0) < right_border
    ]
    if len(gutter_words) > len(words) * 0.15:
        return 1

    left_words = [w for w in words if float(w.get("x1", 0)) <= left_border]
    right_words = [w for w in words if float(w.get("x0", width)) >= right_border]
    if len(left_words) >= int(effective_min_words) and len(right_words) >= int(effective_min_words):
        return 2
    return 1


def _extract_page_lines_pdfplumber_smart(page) -> List[str]:
    """Extract page lines preserving reading order for two-column layouts."""
    def _lines_from_words(
        words: List[Dict[str, object]],
        y_tolerance: float = PDFPLUMBER_Y_TOLERANCE,
    ) -> List[str]:
        if not words:
            return []
        rows: List[List[Dict[str, object]]] = []
        for word in sorted(words, key=lambda w: (float(w.get("top", 0) or 0), float(w.get("x0", 0) or 0))):
            top = float(word.get("top", 0) or 0)
            if not rows:
                rows.append([word])
                continue
            last_row = rows[-1]
            last_top = float(last_row[0].get("top", 0) or 0)
            if abs(top - last_top) <= y_tolerance:
                last_row.append(word)
            else:
                rows.append([word])

        lines: List[str] = []
        for row in rows:
            row_sorted = sorted(row, key=lambda w: float(w.get("x0", 0) or 0))
            tokens = [str(w.get("text") or "").strip() for w in row_sorted]
            text = _restore_missing_spaces(" ".join(tok for tok in tokens if tok))
            if text:
                lines.append(text)
        return lines

    all_words = _extract_words_pdfplumber(page)
    width = float(getattr(page, "width", 0) or 0)
    height = float(getattr(page, "height", 0) or 0)

    if width <= 0 or height <= 0:
        text = page.extract_text() or ""
        return [ln.strip() for ln in text.split("\n") if ln.strip()]

    header_height = _find_header_boundary(all_words, height)
    body_top = min(height, header_height + PDFPLUMBER_Y_TOLERANCE)
    body_words = [
        word for word in all_words
        if float(word.get("top", 0) or 0) > body_top
    ]
    columns = _detect_columns_pdfplumber_words(body_words or all_words, width)

    if columns != 2:
        words = all_words
        lines = _lines_from_words(words)
        if lines:
            return lines
        text = page.extract_text() or ""
        out_lines: List[str] = []
        for ln in text.split("\n"):
            fixed = _restore_missing_spaces(ln)
            if fixed:
                out_lines.append(fixed)
        return out_lines

    header_zone = page.crop((0, 0, width, header_height))

    header_words = _extract_words_pdfplumber(header_zone)
    header_lines = _lines_from_words(header_words)

    if not header_lines:
        header_text = header_zone.extract_text() or ""
        tmp_lines: List[str] = []
        for ln in header_text.split("\n"):
            fixed = _restore_missing_spaces(ln)
            if fixed:
                tmp_lines.append(fixed)
        header_lines = tmp_lines

    center = width / 2.0
    left_col = page.crop((0, body_top, center, height))
    right_col = page.crop((center, body_top, width, height))
    left_words = _extract_words_pdfplumber(left_col)
    right_words = _extract_words_pdfplumber(right_col)

    left_lines = _lines_from_words(left_words)
    right_lines = _lines_from_words(right_words)
    merged_lines = [*header_lines, *left_lines, *right_lines]
    if merged_lines:
        return merged_lines

    left_text = left_col.extract_text() or ""
    right_text = right_col.extract_text() or ""
    header_text = "\n".join(header_lines)
    merged = f"{header_text}\n{left_text}\n{right_text}"
    out_lines: List[str] = []
    for ln in merged.split("\n"):
        fixed = _restore_missing_spaces(ln)
        if fixed:
            out_lines.append(fixed)
    return out_lines


def _extract_lines_pdfplumber(pdf_path: Path) -> List[str]:
    """Извлекает строки из PDF с помощью pdfplumber, возвращает плоский список."""
    if not PDFPLUMBER_AVAILABLE:
        raise ImportError("pdfplumber не установлен. Установите: pip install pdfplumber")

    lines_by_page: List[List[str]] = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_lines = _extract_page_lines_pdfplumber_smart(page)
                lines_by_page.append(page_lines)
    except Exception as e:
        msg = str(e).lower()
        if "encrypted" in msg or "password" in msg:
            raise RuntimeError(
                "PDF зашифрован или защищен паролем. Снимите защиту и повторите попытку."
            ) from e
        raise RuntimeError(
            f"Не удалось прочитать PDF через pdfplumber: {e}. Файл может быть поврежден."
        ) from e
    
    # Удаляем колонтитулы перед объединением
    filtered_lines = _remove_headers_footers(lines_by_page)
    return filtered_lines


def _extract_lines_pymupdf(pdf_path: Path) -> List[str]:
    """Извлекает строки из PDF с помощью PyMuPDF, возвращает плоский список."""
    if not PYMUPDF_AVAILABLE:
        raise ImportError("PyMuPDF не установлен. Установите: pip install pymupdf")

    lines_by_page: List[List[str]] = []
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        msg = str(e).lower()
        if "encrypted" in msg or "password" in msg:
            raise RuntimeError(
                "PDF зашифрован или защищен паролем. Снимите защиту и повторите попытку."
            ) from e
        raise RuntimeError(
            f"Не удалось открыть PDF через PyMuPDF: {e}. Файл может быть поврежден."
        ) from e
    try:
        for i in range(len(doc)):
            try:
                text = doc[i].get_text("text")
            except Exception as e:
                raise RuntimeError(f"Ошибка чтения страницы {i + 1} через PyMuPDF: {e}") from e
            if not text:
                lines_by_page.append([])
                continue
            page_lines: List[str] = []
            for ln in text.split("\n"):
                fixed = _restore_missing_spaces(ln)
                if fixed:
                    page_lines.append(fixed)
            lines_by_page.append(page_lines)
    finally:
        doc.close()
    
    # Удаляем колонтитулы перед объединением
    filtered_lines = _remove_headers_footers(lines_by_page)
    return filtered_lines


# ----------------------------
# Функции для работы с bbox (bounding box)
# ----------------------------

def find_text_blocks_with_bbox(
    pdf_path: Path,
    search_terms: Optional[List[str]] = None,
    expand_bbox: Tuple[float, float, float, float] = (0, 0, 0, 0)
) -> List[Dict[str, Any]]:
    """
    Находит текстовые блоки в PDF по ключевым словам и возвращает их bbox.
    
    Args:
        pdf_path: Путь к PDF файлу
        search_terms: Список ключевых слов для поиска (по умолчанию: ["Резюме", "Аннотация", "Abstract", "Annotation"])
        expand_bbox: Расширение bbox (left, top, right, bottom) в пунктах
        
    Returns:
        Список словарей с информацией о найденных блоках:
        {
            "term": "Резюме",
            "page": 1,
            "bbox": (x0, y0, x1, y1),
            "text": "текст блока",
            "expanded_bbox": (x0, y0, x1, y1)
        }
    """
    if not PDFPLUMBER_AVAILABLE:
        raise ImportError("pdfplumber не установлен. Установите: pip install pdfplumber")
    
    if search_terms is None:
        search_terms = ["Резюме", "Аннотация", "Abstract", "Annotation", "Ключевые слова", "Keywords"]
    
    results = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            # Получаем все слова с их координатами
            words = page.extract_words()
            
            if not words:
                continue
            
            # Получаем текст страницы для поиска
            page_text = page.extract_text() or ""
            page_text_lower = page_text.lower()
            
            # Ищем каждое ключевое слово
            for term in search_terms:
                term_lower = term.lower()
                
                # Проверяем, есть ли слово на странице
                if term_lower not in page_text_lower:
                    continue
                
                # Находим все вхождения слова
                for word in words:
                    word_text = word.get("text", "").lower()
                    if term_lower in word_text:
                        # Получаем bbox слова
                        x0, top, x1, bottom = word["x0"], word["top"], word["x1"], word["bottom"]
                        
                        # Расширяем bbox для захвата всего блока
                        expanded_x0 = max(0, x0 - expand_bbox[0])
                        expanded_top = max(0, top - expand_bbox[1])
                        expanded_x1 = min(page.width, x1 + expand_bbox[2])
                        expanded_bottom = min(page.height, bottom + expand_bbox[3])
                        
                        # Извлекаем текст из расширенной области
                        try:
                            cropped = page.crop((expanded_x0, expanded_top, expanded_x1, expanded_bottom))
                            block_text = cropped.extract_text() or ""
                        except Exception:
                            # Если не удалось извлечь из области, используем текст после слова
                            block_text = page_text[page_text.lower().find(term_lower) + len(term):][:500]
                        
                        results.append({
                            "term": term,
                            "page": page_num,
                            "bbox": (x0, top, x1, bottom),
                            "expanded_bbox": (expanded_x0, expanded_top, expanded_x1, expanded_bottom),
                            "text": block_text.strip()
                        })
                        
                        # Находим только первое вхождение каждого термина на странице
                        break
    
    return results


def find_annotation_bbox_auto(pdf_path: Path) -> Optional[Dict[str, Any]]:
    """
    Автоматически находит bbox для аннотации/резюме в PDF.
    Ищет ключевые слова и возвращает координаты блока.
    
    Args:
        pdf_path: Путь к PDF файлу
        
    Returns:
        Словарь с информацией о найденном блоке или None
    """
    search_terms = ["Резюме", "Аннотация", "Abstract", "Annotation"]
    
    blocks = find_text_blocks_with_bbox(
        pdf_path,
        search_terms=search_terms,
        expand_bbox=(0, -10, 0, 100)  # Расширяем вниз на 100 пунктов
    )
    
    if blocks:
        # Возвращаем первый найденный блок
        return blocks[0]
    
    return None


def print_bbox_info(pdf_path: Path, search_terms: Optional[List[str]] = None):
    """
    Печатает информацию о bbox для найденных блоков.
    Удобно для отладки и получения координат.
    
    Args:
        pdf_path: Путь к PDF файлу
        search_terms: Список ключевых слов для поиска (опционально)
    """
    blocks = find_text_blocks_with_bbox(pdf_path, search_terms=search_terms)
    
    if not blocks:
        print(f"Блоки не найдены в PDF: {pdf_path}")
        return
    
    print(f"\n{'='*80}")
    print(f"Найдено блоков: {len(blocks)}")
    print(f"{'='*80}\n")
    
    for i, block in enumerate(blocks, 1):
        print(f"Блок {i}:")
        print(f"  Ключевое слово: {block['term']}")
        print(f"  Страница: {block['page']}")
        print(f"  Bbox (оригинал): ({block['bbox'][0]:.2f}, {block['bbox'][1]:.2f}, {block['bbox'][2]:.2f}, {block['bbox'][3]:.2f})")
        print(f"  Bbox (расширенный): ({block['expanded_bbox'][0]:.2f}, {block['expanded_bbox'][1]:.2f}, {block['expanded_bbox'][2]:.2f}, {block['expanded_bbox'][3]:.2f})")
        text_preview = block['text'][:100].replace('\n', ' ')
        print(f"  Текст (первые 100 символов): {text_preview}...")
        print()
    
    # Выводим координаты в формате для копирования
    print(f"{'='*80}")
    print("Координаты для использования:")
    print(f"{'='*80}\n")
    for block in blocks:
        bbox = block['expanded_bbox']
        print(f"# {block['term']} (страница {block['page']})")
        print(f"bbox = ({bbox[0]:.2f}, {bbox[1]:.2f}, {bbox[2]:.2f}, {bbox[3]:.2f})")
        print()


# ----------------------------
# Публичный API
# ----------------------------

def _to_html_paragraphs(paragraphs: Iterable[str]) -> str:
    html_lines: List[str] = []
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        html_lines.append(f"<p>{_escape_html(para)}</p>")
    return "\n".join(html_lines) if html_lines else "<div></div>"


def convert_pdf_to_html_with_mistral(
    pdf_path: Path,
    prefer_pdfplumber: bool = True,
    api_key: Optional[str] = None,
    model: str = "mistral-large-latest",
    base_url: str = "https://api.mistral.ai/v1",
    config: Optional[Dict] = None
) -> Tuple[str, List[str]]:
    """
    Конвертирует PDF в HTML с помощью Mistral AI для улучшения структуры и форматирования.

    Args:
        pdf_path: путь к PDF
        prefer_pdfplumber: предпочитать pdfplumber для извлечения текста
        api_key: API ключ Mistral AI (если не указан, берется из переменной окружения или config)
        model: модель Mistral AI для использования
        base_url: базовый URL API Mistral
        config: конфигурация (опционально)

    Returns:
        (html_content, warnings)
    """
    warnings: List[str] = []
    
    # Получаем настройки из конфига
    # Приоритет: pdf_to_html (специфичные настройки) > llm (общие настройки) > mistral (старый формат)
    if config:
        # Проверяем ключ, исключая значения-заглушки
        def is_valid_key(key):
            if not key:
                return False
            key_str = str(key).strip()
            return key_str and key_str not in ("YOUR_MISTRAL_API_KEY_HERE", "YOUR_OPENAI_API_KEY_HERE", "")
        
        # Сначала проверяем специфичные настройки для PDF to HTML
        if not api_key or not is_valid_key(api_key):
            api_key = config.get("pdf_to_html", {}).get("mistral_api_key")
            if not is_valid_key(api_key):
                api_key = config.get("llm", {}).get("api_key")
                if not is_valid_key(api_key):
                    api_key = config.get("mistral", {}).get("api_key")
        
        # Аналогично для модели и base_url
        pdf_model = config.get("pdf_to_html", {}).get("mistral_model")
        llm_model = config.get("llm", {}).get("model")
        mistral_model = config.get("mistral", {}).get("model")
        model = pdf_model or llm_model or mistral_model or model
        
        pdf_base_url = config.get("pdf_to_html", {}).get("mistral_base_url")
        llm_base_url = config.get("llm", {}).get("base_url")
        mistral_base_url = config.get("mistral", {}).get("base_url")
        base_url = pdf_base_url or llm_base_url or mistral_base_url or base_url
    
    # Получаем API ключ из переменной окружения, если не указан
    if not api_key:
        api_key = os.getenv('MISTRAL_API_KEY')
    
    if not api_key:
        warnings.append("API ключ Mistral AI не указан. Используется стандартная конвертация без Mistral.")
        return convert_pdf_to_html(pdf_path, prefer_pdfplumber=prefer_pdfplumber)
    
    # Отладочный вывод (можно убрать после проверки)
    if api_key:
        # Показываем только первые и последние 4 символа ключа для безопасности
        key_preview = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "***"
        print(f"DEBUG Mistral: Используется API ключ: {key_preview}, модель: {model}, base_url: {base_url}")
    
    # Проверяем доступность OpenAI клиента (Mistral использует совместимый API)
    try:
        from openai import OpenAI
    except ImportError:
        warnings.append("Библиотека openai не установлена. Используется стандартная конвертация. Установите: pip install openai")
        return convert_pdf_to_html(pdf_path, prefer_pdfplumber=prefer_pdfplumber)
    
    # Сначала извлекаем текст из PDF стандартным способом
    try:
        extractor: Optional[Callable[[Path], List[str]]] = None
        if prefer_pdfplumber and PDFPLUMBER_AVAILABLE:
            extractor = _extract_lines_pdfplumber
        elif PYMUPDF_AVAILABLE:
            extractor = _extract_lines_pymupdf
        elif PDFPLUMBER_AVAILABLE:
            extractor = _extract_lines_pdfplumber
        
        if extractor is None:
            raise ImportError(
                "Не установлена ни одна библиотека для работы с PDF. "
                "Установите одну из: pip install pdfplumber или pip install pymupdf"
            )
        
        raw_lines = extractor(pdf_path)
        paragraphs = _merge_lines_into_paragraphs(raw_lines)
        initial_html = _to_html_paragraphs(paragraphs)
        
        # Извлекаем текст для отправки в Mistral (без HTML тегов)
        text_content = "\n".join(paragraphs)
        
        # Если текст слишком длинный, разбиваем на части
        # Уменьшено до 30k символов для избежания таймаутов
        max_chunk_size = 30000  # Примерно 30k символов (было 50k, изначально 100k)
        if len(text_content) > max_chunk_size:
            warnings.append(f"Текст PDF слишком длинный ({len(text_content)} символов). Обрабатывается первая часть ({max_chunk_size} символов) для избежания таймаутов.")
            text_content = text_content[:max_chunk_size]
        
    except Exception as e:
        warnings.append(f"Ошибка при извлечении текста из PDF: {e}")
        return "<div></div>", warnings
    
    # Логируем начало обработки
    import time
    start_time = time.time()
    text_length = len(text_content)
    print(f"DEBUG Mistral: Начинаем обработку через Mistral AI. Размер текста: {text_length} символов")
    
    # Создаем упрощённый промпт для более быстрой обработки
    try:
        from prompts import Prompts
        prompt = Prompts.get_pdf_to_html_prompt(text_content)
        system_message = Prompts.SYSTEM_PDF_TO_HTML
    except Exception as e:
        raise RuntimeError(f"Prompts module unavailable for PDF->HTML: {e}")
    
    try:
        # Создаем клиент Mistral AI (использует OpenAI-совместимый API)
        # Увеличен таймаут до 180 секунд (3 минуты) для больших документов
        client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=180.0  # Таймаут 180 секунд (3 минуты)
        )
        
        print(f"DEBUG Mistral: Отправляем запрос к API (модель: {model})...")
        
        # Отправляем запрос
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": system_message
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,  # Низкая температура для более детерминированного результата
            max_tokens=8000,  # Ограничиваем размер ответа для ускорения
        )
        
        elapsed_time = time.time() - start_time
        print(f"DEBUG Mistral: Получен ответ от API за {elapsed_time:.2f} секунд")
        
        improved_html = response.choices[0].message.content.strip()
        
        # Извлекаем HTML из ответа (может быть обернут в markdown код блоки)
        import re
        # Убираем markdown код блоки, если есть
        html_match = re.search(r'```(?:html)?\s*(.*?)\s*```', improved_html, re.DOTALL)
        if html_match:
            improved_html = html_match.group(1)
        
        # Проверяем, что результат валидный HTML
        if not improved_html.strip().startswith('<'):
            warnings.append("Mistral AI вернул неожиданный формат, используется исходный HTML")
            return initial_html, warnings
        
        return improved_html, warnings
        
    except Exception as e:
        error_msg = str(e)
        elapsed_time = time.time() - start_time
        
        # Более детальная обработка различных ошибок
        if "401" in error_msg or "Unauthorized" in error_msg:
            warnings.append(
                f"Ошибка авторизации Mistral AI (401 Unauthorized). "
                f"Проверьте правильность API ключа в config.json. "
                f"Используется исходный HTML. Ошибка: {e}"
            )
        elif "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
            warnings.append(
                f"Таймаут при обработке через Mistral AI (обработка заняла {elapsed_time:.1f} сек, превышен лимит 180 сек). "
                f"Документ слишком большой или API медленно отвечает. Используется исходный HTML. "
                f"Рекомендуется отключить Mistral (use_mistral: false) для быстрой обработки."
            )
            print(f"DEBUG Mistral: Таймаут после {elapsed_time:.2f} секунд обработки")
        else:
            warnings.append(f"Ошибка при обработке через Mistral AI: {e}, используется исходный HTML")
        
        return initial_html, warnings


def convert_pdf_to_html(
    pdf_path: Path,
    prefer_pdfplumber: bool = True,
    use_mistral: bool = False,
    mistral_config: Optional[Dict] = None
) -> Tuple[str, List[str]]:
    """
    Конвертирует PDF в HTML, используя доступную библиотеку.

    Args:
        pdf_path: путь к PDF
        prefer_pdfplumber: предпочитать pdfplumber (часто лучше сохраняет "структуру")
        use_mistral: использовать ли Mistral AI для улучшения результата
        mistral_config: конфигурация для Mistral AI

    Returns:
        (html_content, warnings)

    Raises:
        ImportError: если не установлена ни одна библиотека
    """
    if use_mistral:
        return convert_pdf_to_html_with_mistral(
            pdf_path,
            prefer_pdfplumber=prefer_pdfplumber,
            config=mistral_config
        )
    
    warnings: List[str] = []

    extractor: Optional[Callable[[Path], List[str]]] = None
    if prefer_pdfplumber and PDFPLUMBER_AVAILABLE:
        extractor = _extract_lines_pdfplumber
    elif PYMUPDF_AVAILABLE:
        extractor = _extract_lines_pymupdf
    elif PDFPLUMBER_AVAILABLE:
        extractor = _extract_lines_pdfplumber

    if extractor is None:
        raise ImportError(
            "Не установлена ни одна библиотека для работы с PDF. "
            "Установите одну из: pip install pdfplumber или pip install pymupdf"
        )

    try:
        raw_lines = extractor(pdf_path)
        paragraphs = _merge_lines_into_paragraphs(raw_lines)
        html = _to_html_paragraphs(paragraphs)
        return html, warnings
    except Exception as e:
        warnings.append(f"Ошибка при обработке PDF: {e}")
        return "<div></div>", warnings


# Совместимость со старым API (если где-то уже импортируется)
def convert_pdf_to_html_pdfplumber(pdf_path: Path) -> Tuple[str, List[str]]:
    raw_lines = _extract_lines_pdfplumber(pdf_path)
    paragraphs = _merge_lines_into_paragraphs(raw_lines)
    return _to_html_paragraphs(paragraphs), []


def convert_pdf_to_html_pymupdf(pdf_path: Path) -> Tuple[str, List[str]]:
    raw_lines = _extract_lines_pymupdf(pdf_path)
    paragraphs = _merge_lines_into_paragraphs(raw_lines)
    return _to_html_paragraphs(paragraphs), []


# ----------------------------
# Обработка списка литературы
# ----------------------------

def normalize_references_block(lines: List[str]) -> Tuple[List[str], float]:
    """
    Нормализует блок 'СПИСОК ЛИТЕРАТУРЫ / REFERENCES' после PDF→text:
    - находит границы блока литературы,
    - удаляет частые колонтитулы/повторы,
    - склеивает разрывы URL/DOI,
    - объединяет переносы внутри одной библиографической записи,
    - возвращает список записей (по одной строке на запись) и score качества [0..1].

    Args:
        lines: список строк, извлечённых из PDF (в порядке следования).

    Returns:
        (entries, score)
        entries: список нормализованных библиографических записей
        score: эвристическая оценка качества результата (0..1).
    """
    _re_cache = REFERENCE_BLOCK_REGEX

    # -------------------------
    # 1) PATTERNS (внутри одной функции)
    # -------------------------
    RE_REF_HEADER = _re_cache["RE_REF_HEADER"]
    RE_REF_END = _re_cache["RE_REF_END"]

    # Начало новой записи
    RE_BIB_NUM = _re_cache["RE_BIB_NUM"]
    RE_RU_AUTHOR_START = _re_cache["RE_RU_AUTHOR_START"]
    RE_EN_AUTHOR_START = _re_cache["RE_EN_AUTHOR_START"]

    # Признаки "внутри записи"
    RE_YEAR = _re_cache["RE_YEAR"]
    RE_DOI = _re_cache["RE_DOI"]
    RE_PAGES = _re_cache["RE_PAGES"]
    RE_VOL_ISS = _re_cache["RE_VOL_ISS"]
    RE_PUBLISHER = _re_cache["RE_PUBLISHER"]

    # Продолжение/служебные хвосты
    RE_BIB_CONTINUATION = _re_cache["RE_BIB_CONTINUATION"]

    # URL/DOI склейки
    RE_URL_LABEL = _re_cache["RE_URL_LABEL"]
    RE_URL_PREFIX = _re_cache["RE_URL_PREFIX"]
    RE_URL_LINE = _re_cache["RE_URL_LINE"]

    RE_DOI_PREFIX_BROKEN = _re_cache["RE_DOI_PREFIX_BROKEN"]
    RE_DOI_SUFFIX = _re_cache["RE_DOI_SUFFIX"]

    # Колонтитулы (часто встречающиеся строки) — используется вместе с частотным фильтром
    RE_HEADER_FOOTER_HINT = _re_cache["RE_HEADER_FOOTER_HINT"]

    # -------------------------
    # 2) helpers (nested, чтобы осталась "одна функция")
    # -------------------------
    def norm_space(s: str) -> str:
        return re.sub(r"\s+", " ", s).strip()

    _CYR = r"А-Яа-яЁё"
    _LAT = r"A-Za-z"

    def fix_intra_word_breaks(s: str) -> str:
        """Чинит 'ко митетов' → 'комитетов', 'Mod ern' → 'Modern' (осторожно)."""
        t = s

        # Кириллица: 1-4 буквы + пробел + 2+ буквы → слить
        t = re.sub(rf"(?<!\.)\b([{_CYR}]{{1,4}})\s+([{_CYR}]{{2,}})\b", r"\1\2", t)

        # Латиница: 1-3 буквы + пробел + 2+ буквы → слить
        t = re.sub(rf"(?<!\.)\b([{_LAT}]{{1,3}})\s+([{_LAT}]{{2,}})\b", r"\1\2", t)

        # Склейка перед дефисом: 'Smo lensk-' → 'Smolensk-'
        t = re.sub(rf"\b([{_LAT}]{{1,3}})\s+([{_LAT}]{{2,}})-", r"\1\2-", t)
        t = re.sub(rf"\b([{_CYR}]{{1,4}})\s+([{_CYR}]{{2,}})-", r"\1\2-", t)

        return t

    def is_new_entry(line: str) -> bool:
        return bool(RE_BIB_NUM.match(line) or RE_RU_AUTHOR_START.match(line) or RE_EN_AUTHOR_START.match(line))

    def looks_like_header_footer(line: str) -> bool:
        # Быстрый эвристический фильтр (помогает не "прилипать" к записям)
        return bool(RE_HEADER_FOOTER_HINT.search(line)) and len(line) < 120

    def quality_score(entries: List[str]) -> float:
        if not entries:
            return 0.0
        has_year = sum(1 for e in entries if RE_YEAR.search(e))
        has_pages_or_doi = sum(1 for e in entries if (RE_PAGES.search(e) or RE_DOI.search(e)))
        too_short = sum(1 for e in entries if len(e.strip()) < 20)
        broken_url = sum(1 for e in entries if re.search(r"https?://\S*\s+\S+", e))

        score = 0.0
        score += (has_year / len(entries)) * 0.45
        score += (has_pages_or_doi / len(entries)) * 0.35
        score += max(0.0, 1.0 - too_short / len(entries)) * 0.10
        score += max(0.0, 1.0 - broken_url / max(1, len(entries))) * 0.10
        return max(0.0, min(1.0, score))

    # -------------------------
    # 3) input cleanup
    # -------------------------
    raw = [norm_space(x) for x in (lines or []) if x and norm_space(x)]
    if not raw:
        return [], 0.0

    # -------------------------
    # 4) locate references block
    # -------------------------
    start_idx = None
    for i, s in enumerate(raw):
        if RE_REF_HEADER.match(s):
            start_idx = i
            break

    if start_idx is None:
        return [], 0.0  # блока литературы нет

    end_idx = len(raw)
    for j in range(start_idx + 1, len(raw)):
        if RE_REF_END.match(raw[j]):
            end_idx = j
            break

    ref_lines = raw[start_idx + 1 : end_idx]
    if not ref_lines:
        return [], 0.0

    # -------------------------
    # 5) remove repeated headers/footers by frequency
    # -------------------------
    def normalize_for_freq(s: str) -> str:
        return re.sub(r"\s+", " ", s).strip().lower()

    freq = Counter(normalize_for_freq(x) for x in ref_lines if len(x) >= 8)
    # Часто достаточно 3; если список короткий — уменьшаем порог
    min_freq = 3 if len(ref_lines) >= 40 else 2

    filtered = []
    for s in ref_lines:
        ns = normalize_for_freq(s)
        if freq[ns] >= min_freq and looks_like_header_footer(s):
            continue
        filtered.append(s)

    ref_lines = filtered

    # -------------------------
    # 6) pre-glue special pairs (URL:, URL split, DOI split)
    # -------------------------
    glued: List[str] = []
    i = 0
    while i < len(ref_lines):
        cur = ref_lines[i]
        nxt = ref_lines[i + 1] if i + 1 < len(ref_lines) else ""

        # URL: + http...
        if RE_URL_LABEL.match(cur) and nxt and RE_URL_PREFIX.match(nxt):
            glued.append(norm_space(f"{cur} {nxt}"))
            i += 2
            continue

        # DOI broken: "DOI: 10.xxx/" + "S294..."
        if RE_DOI_PREFIX_BROKEN.search(cur) and nxt and RE_DOI_SUFFIX.match(nxt):
            glued.append(norm_space(f"{cur}{nxt}"))
            i += 2
            continue

        # URL split: "https://www." + "domain/..." OR "https://.../" + "file.pdf"
        if cur.lower().startswith(("http://", "https://")) and nxt:
            # если текущая строка выглядит как URL-префикс, а следующая — продолжение без пробелов
            if RE_URL_PREFIX.match(cur) and not nxt.lower().startswith(("http://", "https://")):
                # Склеиваем без пробела, если текущая заканчивается на '.' или '/' или '-' (часто так рвётся)
                if cur.endswith((".", "/", "-")):
                    glued.append(norm_space(cur + nxt))
                    i += 2
                    continue

        glued.append(cur)
        i += 1

    # лёгкая внутрисловная починка на уровне строк
    ref_lines = [fix_intra_word_breaks(x) for x in glued]

    # -------------------------
    # 7) build entries
    # -------------------------
    entries: List[str] = []
    current: List[str] = []

    for s in ref_lines:
        s = norm_space(s)
        if not s:
            continue

        # отсечём явный мусор-колонтитул, если вдруг проскочил
        if looks_like_header_footer(s) and (not is_new_entry(s)) and len(s) < 120:
            continue

        s = fix_intra_word_breaks(s)

        if is_new_entry(s):
            if current:
                entries.append(norm_space(" ".join(current)))
            current = [s]
            continue

        # если запись ещё не началась — пропускаем шум до первой записи
        if not current:
            continue

        # Явные продолжения: "(In Russ.)", "Т. 1–4.", и т.п.
        if RE_BIB_CONTINUATION.match(s):
            current.append(s)
            continue

        # Если строка выглядит как часть библиографического описания — приклеиваем
        if (RE_YEAR.search(s) or RE_PAGES.search(s) or RE_DOI.search(s) or RE_VOL_ISS.search(s)
                or RE_PUBLISHER.search(s) or RE_URL_LINE.match(s)):
            current.append(s)
            continue

        # Библиографические данные: номера страниц/том, год, страницы (например: "103/104. 2002. S. 194–202.")
        # Такие строки всегда являются продолжением записи, а не новым источником
        if (re.match(r'^\s*\d+/\d+\.\s*\d{4}\.', s) or 
            re.match(r'^\s*\d{4}\.\s*[Ss]\.\s*\d+', s) or
            re.match(r'^\s*[SsCcPp]+\.?\s*\d+[–-]\d+\.?\s*$', s, re.IGNORECASE) or  # "S. 270–282." или "Pp. 10-20."
            re.match(r'^\s*[SsCcPp]+\.?\s*\d+\.?\s*$', s, re.IGNORECASE) or  # "S. 194." или "с. 194."
            re.match(r'^\s*\d+\s*[PpСс]+\.?\s*$', s, re.IGNORECASE) or  # "386 p." или "200 с." или "150 pp."
            re.match(r'^\s*\d+/\d+\.', s) or
            re.match(r'^\s*(Vol\.|Т\.|№)\s*\d+', s, re.IGNORECASE) or
            re.match(r'^\s*\d+[–-]\d+\.?\s*$', s)):  # Номера страниц без префикса: "419–434."
            current.append(s)
            continue

        # В остальных случаях: чаще всего это всё равно перенос внутри записи,
        # если строка не похожа на самостоятельную (короткую "шапку")
        if len(s) < 80:
            current.append(s)
        else:
            # длинные строки тоже обычно продолжение записи
            current.append(s)

    if current:
        entries.append(norm_space(" ".join(current)))

    # -------------------------
    # 8) final cleanup
    # -------------------------
    cleaned = []
    for e in entries:
        e2 = fix_intra_word_breaks(e)
        e2 = norm_space(e2)

        # Чистим "URL :"
        e2 = re.sub(r"\bURL\s*:\s*", "URL: ", e2, flags=re.IGNORECASE)

        # Убираем двойные пробелы вокруг знаков препинания
        e2 = re.sub(r"\s+([,.;:])", r"\1", e2)
        e2 = re.sub(r"([(/])\s+", r"\1", e2)
        e2 = re.sub(r"\s+([)])", r"\1", e2)

        if e2:
            cleaned.append(e2)

    score = quality_score(cleaned)
    return cleaned, score
