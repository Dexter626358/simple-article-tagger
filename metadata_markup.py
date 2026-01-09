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
    
    # 1. Находим все элементы списков <li>
    list_pattern = r'<li[^>]*>(.*?)</li>'
    for match in re.finditer(list_pattern, html_content, re.DOTALL | re.IGNORECASE):
        elements.append({
            'start': match.start(),
            'end': match.end(),
            'type': 'li',
            'content': match.group(1)
        })
    
    # 2. Находим все параграфы <p>
    paragraph_pattern = r'<p[^>]*>(.*?)</p>'
    for match in re.finditer(paragraph_pattern, html_content, re.DOTALL | re.IGNORECASE):
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
        elements.append({
            'start': match.start(),
            'end': match.end(),
            'type': 'h',
            'content': match.group(1)
        })
    
    # 4. Находим div элементы (только те, что не содержат других блочных элементов)
    div_pattern = r'<div[^>]*>(.*?)</div>'
    for match in re.finditer(div_pattern, html_content, re.DOTALL | re.IGNORECASE):
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
        text_clean = re.sub(r'<[^>]+>', '', content)
        text_clean = text_clean.strip()
        
        if text_clean:
            lines.append({
                "id": idx,
                "text": text_clean,
                "line_number": idx,
                "html": content  # Сохраняем оригинальный HTML для точного выделения
            })
            idx += 1
    
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

