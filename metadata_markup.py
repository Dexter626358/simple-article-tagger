#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Модуль для разметки метаданных статей.
Содержит общую логику для работы с метаданными, которую можно использовать
в разных приложениях (app.py, web_extract.py).
"""

from __future__ import annotations

import json
import re
import html
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

try:
    from text_utils import merge_doi_url_with_references
except ImportError:
    # Запасной вариант, если text_utils недоступен
    def merge_doi_url_with_references(references: List[str]) -> List[str]:
        return references


# ----------------------------
# Константы
# ----------------------------

METADATA_FIELDS: Sequence[str] = (
    "title",
    "title_en",
    "doi",
    "annotation",
    "annotation_en",
    "keywords",
    "keywords_en",
    "references_ru",
    "references_en",
    "year",
    "issue",
    "article_number",
    "url",
    "url_en",
    "pages",
    "udc",
    "received_date",
    "reviewed_date",
    "accepted_date",
    "funding",
)

LIST_FIELDS = {"references_ru", "references_en"}  # список строк
INT_FIELDS = {"year"}  # целые числа

REFERENCE_HEADING_MARKERS = {
    "references",
    "литература",
    "список литературы",
    "библиографический список",
}
REFERENCE_END_MARKERS = {
    "информация об авторе",
    "информация об авторах",
    "information about the author",
    "information about the authors",
    "авторы сделали эквивалентный вклад в подготовку публикации и заявляют об отсутствии конфликта интересов",
    "the authors made equivalent contributions to the publication and declare no conflict of interest",
}
NUMBERED_REFERENCE_PATTERN = re.compile(r"^\s*(?:\[\d{1,3}\]|\d{1,3}[.)])\s*")


# ----------------------------
# Функции для работы с метаданными
# ----------------------------

def build_metadata(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Приводит JSON из браузера к ожидаемой структуре:
    - гарантирует наличие всех ключей;
    - list-поля всегда список строк;
    - int-поля старается привести к int.
    
    Args:
        payload: Словарь с данными из формы
        
    Returns:
        Нормализованный словарь метаданных
    """
    out: Dict[str, Any] = {}

    for key in METADATA_FIELDS:
        if key in LIST_FIELDS:
            v = payload.get(key, [])
            if v is None:
                out[key] = []
            elif isinstance(v, list):
                refs = [str(x).strip() for x in v if str(x).strip()]
            elif isinstance(v, str):
                refs = [s.strip() for s in v.splitlines() if s.strip()]
            else:
                refs = [str(v).strip()] if str(v).strip() else []
            
            # Объединяем DOI/URL с предыдущими источниками для списка литературы
            if key in {"references_ru", "references_en"}:
                out[key] = merge_doi_url_with_references(refs)
            else:
                out[key] = refs
            continue

        if key in INT_FIELDS:
            v = payload.get(key)
            if v in (None, "", []):
                out[key] = None
            else:
                try:
                    out[key] = int(v)
                except Exception:
                    out[key] = v  # оставим как есть
            continue

        # обычные строки/nullable
        v = payload.get(key)
        if v is None or v == "":
            out[key] = None
        else:
            out[key] = str(v)

    return out


def save_metadata(metadata: Dict[str, Any], output_path: Path) -> None:
    """
    Сохраняет метаданные в JSON файл.
    
    Args:
        metadata: Словарь с метаданными
        output_path: Путь к выходному JSON файлу
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def extract_text_from_html(html_content: str) -> List[Dict[str, Any]]:
    """
    Извлекает текст из HTML контента для разметки.
    Разбивает HTML на параграфы и другие блочные элементы, возвращает их как список элементов.
    Обрабатывает: списки (li), параграфы (p), заголовки (h1-h6), div элементы.
    Сохраняет порядок элементов в документе.
    
    Args:
        html_content: HTML содержимое
        
    Returns:
        Список словарей с информацией о параграфах и других блочных элементах
    """
    lines = []
    idx = 1
    
    # Создаем список всех блочных элементов с их позициями в документе
    # Это позволяет обработать их в правильном порядке
    elements = []

    def _is_inside_ranges(pos: int, ranges: List[tuple[int, int]]) -> bool:
        return any(start <= pos < end for start, end in ranges)

    def _html_to_text(fragment: str) -> str:
        if not fragment:
            return ""
        # Preserve natural text boundaries from block tags to avoid glued words.
        fragment = re.sub(r'(?i)<br\\s*/?>', "\n", fragment)
        fragment = re.sub(r'(?i)</(p|div|li|h[1-6]|tr|td|th)>', "\n", fragment)
        fragment = re.sub(r'<[^>]+>', ' ', fragment)
        fragment = html.unescape(fragment)
        fragment = fragment.replace("\xa0", " ")
        fragment = fragment.replace("\r\n", "\n").replace("\r", "\n")
        # Remove soft hyphens and normalize whitespace.
        fragment = fragment.replace("\u00ad", "")
        cleaned_lines = []
        for line in fragment.split("\n"):
            line = re.sub(r"\s+", " ", line).strip()
            if line:
                cleaned_lines.append(line)
        return " ".join(cleaned_lines).strip()

    table_ranges: List[tuple[int, int]] = []
    table_pattern = r'<table[^>]*>(.*?)</table>'
    for tmatch in re.finditer(table_pattern, html_content, re.DOTALL | re.IGNORECASE):
        table_start, table_end = tmatch.start(), tmatch.end()
        table_ranges.append((table_start, table_end))
        table_html = tmatch.group(0)

        row_pattern = r'<tr[^>]*>(.*?)</tr>'
        for rmatch in re.finditer(row_pattern, table_html, re.DOTALL | re.IGNORECASE):
            row_html = rmatch.group(0)
            cell_pattern = r'<t[hd][^>]*>(.*?)</t[hd]>'
            cells = [
                _html_to_text(cmatch.group(1))
                for cmatch in re.finditer(cell_pattern, row_html, re.DOTALL | re.IGNORECASE)
            ]
            if not cells:
                continue
            cells = [c for c in cells if c]
            if not cells:
                continue
            row_text = " | ".join(cells)
            elements.append({
                'start': table_start + rmatch.start(),
                'end': table_start + rmatch.end(),
                'type': 'table-row',
                'content': row_text
            })
    
    # 1. Находим все элементы списков <li>
    list_pattern = r'<li[^>]*>(.*?)</li>'
    for match in re.finditer(list_pattern, html_content, re.DOTALL | re.IGNORECASE):
        if _is_inside_ranges(match.start(), table_ranges):
            continue
        elements.append({
            'start': match.start(),
            'end': match.end(),
            'type': 'li',
            'content': match.group(1)
        })
    
    # 2. Находим все параграфы <p>
    paragraph_pattern = r'<p[^>]*>(.*?)</p>'
    for match in re.finditer(paragraph_pattern, html_content, re.DOTALL | re.IGNORECASE):
        if _is_inside_ranges(match.start(), table_ranges):
            continue
        content = match.group(1)
        # Пропускаем параграфы, которые содержат списки (они будут обработаны через <li>)
        if not re.search(r'<li[^>]*>', content, re.IGNORECASE):
            elements.append({
                'start': match.start(),
                'end': match.end(),
                'type': 'p',
                'content': content
            })
    
    # 3. Находим все заголовки <h1>-<h6>
    heading_pattern = r'<h[1-6][^>]*>(.*?)</h[1-6]>'
    for match in re.finditer(heading_pattern, html_content, re.DOTALL | re.IGNORECASE):
        if _is_inside_ranges(match.start(), table_ranges):
            continue
        elements.append({
            'start': match.start(),
            'end': match.end(),
            'type': 'h',
            'content': match.group(1)
        })
    
    # 4. Находим div элементы (только те, что не содержат других блочных элементов)
    div_pattern = r'<div[^>]*>(.*?)</div>'
    for match in re.finditer(div_pattern, html_content, re.DOTALL | re.IGNORECASE):
        if _is_inside_ranges(match.start(), table_ranges):
            continue
        content = match.group(1)
        # Пропускаем div, если внутри есть другие блочные элементы
        if not re.search(r'<(p|ul|ol|li|h[1-6])[^>]*>', content, re.IGNORECASE):
            elements.append({
                'start': match.start(),
                'end': match.end(),
                'type': 'div',
                'content': content
            })
    
    # Сортируем элементы по их позиции в документе (сохраняем порядок)
    elements.sort(key=lambda x: x['start'])
    
    # Обрабатываем элементы в порядке их появления
    for elem in elements:
        content = elem['content']
        if elem.get('type') == 'table-row':
            text_clean = str(content).strip()
        else:
            text_clean = _html_to_text(content)
        
        if text_clean:
            lines.append({
                "id": idx,
                "text": text_clean,
                "line_number": idx,
                "html": content,  # Сохраняем оригинальный HTML для точного выделения
                "block_type": elem.get("type"),
            })
            idx += 1

    def _norm_marker(text: str) -> str:
        value = html.unescape(str(text or "")).replace("\xa0", " ").lower().replace("ё", "е")
        value = re.sub(r"\s+", " ", value).strip(" .:;-–—")
        return value

    def _is_reference_heading(text: str) -> bool:
        return _norm_marker(text) in REFERENCE_HEADING_MARKERS

    def _is_reference_end(text: str) -> bool:
        marker = _norm_marker(text)
        if marker in REFERENCE_END_MARKERS:
            return True
        return marker.startswith("информация об автор") or marker.startswith("information about the author")

    def _is_running_header_footer(text: str) -> bool:
        marker = _norm_marker(text)
        if marker.startswith(("2.5.4", "2.5.5", "2.5.6", "2.5.7")):
            return True
        if "роботы, мехатроника и робототехнические системы" in marker:
            return True
        if marker.startswith("вестник мгту") and ("2025" in marker or "2026" in marker):
            return True
        return False

    merged_lines: List[Dict[str, Any]] = []
    in_references = False
    pending_ref: Optional[Dict[str, Any]] = None

    def _flush_pending() -> None:
        nonlocal pending_ref
        if pending_ref:
            merged_lines.append(pending_ref)
            pending_ref = None

    for line in lines:
        text = str(line.get("text") or "").strip()
        block_type = str(line.get("block_type") or "")

        if _is_running_header_footer(text):
            _flush_pending()
            continue

        if _is_reference_heading(text):
            _flush_pending()
            in_references = True
            merged_lines.append(line)
            continue

        if in_references and _is_reference_end(text):
            _flush_pending()
            in_references = False
            merged_lines.append(line)
            continue

        if not in_references:
            merged_lines.append(line)
            continue

        if block_type == "li":
            _flush_pending()
            merged_lines.append(line)
            continue

        starts_new_reference = bool(NUMBERED_REFERENCE_PATTERN.match(text))
        if pending_ref is None:
            pending_ref = dict(line)
            continue

        if starts_new_reference:
            _flush_pending()
            pending_ref = dict(line)
            continue

        pending_ref["text"] = f'{pending_ref["text"].rstrip()} {text.lstrip()}'.strip()
        pending_ref["html"] = f'{pending_ref.get("html", "")}<br/>{line.get("html", "")}'

    _flush_pending()

    for idx, line in enumerate(merged_lines, start=1):
        line["id"] = idx
        line["line_number"] = idx

    return merged_lines


def extract_text_from_pdf(pdf_path: Path, include_bbox: bool = False) -> List[Dict[str, Any]]:
    """
    Извлекает текст из PDF для разметки.
    Аналогично extract_text_from_html, но для PDF файлов.
    
    Args:
        pdf_path: Путь к PDF файлу
        include_bbox: Если True, сохраняет координаты (bbox) для каждой строки
        
    Returns:
        Список словарей с информацией о строках текста для разметки
    """
    lines = []
    idx = 1
    
    try:
        # Если нужно сохранять bbox, используем pdfplumber напрямую
        if include_bbox:
            from converters.pdf_to_html import PDFPLUMBER_AVAILABLE
            if PDFPLUMBER_AVAILABLE:
                import pdfplumber
                
                with pdfplumber.open(pdf_path) as pdf:
                    for page_num, page in enumerate(pdf.pages, start=1):
                        # Извлекаем слова с координатами
                        words = page.extract_words()
                        
                        if not words:
                            continue
                        
                        # Группируем слова по строкам (по координате top)
                        lines_by_y = {}
                        for word in words:
                            y = round(word['top'], 1)  # Округляем для группировки
                            if y not in lines_by_y:
                                lines_by_y[y] = []
                            lines_by_y[y].append(word)
                        
                        # Сортируем строки по вертикальной позиции (сверху вниз)
                        for y in sorted(lines_by_y.keys(), reverse=True):  # reverse=True т.к. y растет вниз
                            words_in_line = sorted(lines_by_y[y], key=lambda w: w['x0'])
                            
                            if not words_in_line:
                                continue
                            
                            # Объединяем текст строки
                            line_text = " ".join(w['text'] for w in words_in_line)
                            
                            if not line_text.strip():
                                continue
                            
                            # Вычисляем bbox для всей строки
                            x0 = min(w['x0'] for w in words_in_line)
                            top = words_in_line[0]['top']
                            x1 = max(w['x1'] for w in words_in_line)
                            bottom = words_in_line[0]['bottom']
                            
                            lines.append({
                                "id": idx,
                                "text": line_text.strip(),
                                "line_number": idx,
                                "page": page_num,
                                "bbox": (x0, top, x1, bottom),
                                "y_position": y
                            })
                            idx += 1
                
                return lines
        
        # Обычное извлечение без bbox
        # Импортируем функции извлечения из pdf_to_html
        from converters.pdf_to_html import (
            _extract_lines_pdfplumber,
            _extract_lines_pymupdf,
            PDFPLUMBER_AVAILABLE,
            PYMUPDF_AVAILABLE
        )
        
        # Выбираем экстрактор (предпочитаем pdfplumber)
        extractor = None
        if PDFPLUMBER_AVAILABLE:
            extractor = _extract_lines_pdfplumber
        elif PYMUPDF_AVAILABLE:
            extractor = _extract_lines_pymupdf
        
        if not extractor:
            # Если нет доступных библиотек, возвращаем пустой список
            return []
        
        # Извлекаем строки из PDF
        raw_lines = extractor(pdf_path)
        
        # Преобразуем в нужный формат (аналогично extract_text_from_html)
        for line_text in raw_lines:
            if line_text and line_text.strip():
                lines.append({
                    "id": idx,
                    "text": line_text.strip(),
                    "line_number": idx
                })
                idx += 1
        
    except Exception as e:
        # В случае ошибки возвращаем пустой список
        print(f"Ошибка при извлечении текста из PDF {pdf_path}: {e}")
        return []
    
    return lines


def get_default_output_path(input_file: Path, output_dir: Optional[Path] = None) -> Path:
    """
    Генерирует путь к выходному JSON файлу на основе входного файла.
    
    Args:
        input_file: Путь к исходному файлу
        output_dir: Директория для сохранения (по умолчанию: output/)
        
    Returns:
        Путь к выходному JSON файлу
    """
    if output_dir is None:
        output_dir = input_file.parent / "output"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / f"{input_file.stem}_metadata.json"

