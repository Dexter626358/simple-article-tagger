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
    Разбивает HTML на параграфы и возвращает их как список элементов.
    
    Args:
        html_content: HTML содержимое
        
    Returns:
        Список словарей с информацией о параграфах
    """
    # Находим все параграфы <p>...</p>
    pattern = r'<p[^>]*>(.*?)</p>'
    matches = re.finditer(pattern, html_content, re.DOTALL)
    
    lines = []
    for idx, match in enumerate(matches, 1):
        content = match.group(1)
        # Убираем HTML теги для отображения
        text_clean = re.sub(r'<[^>]+>', '', content)
        text_clean = text_clean.strip()
        
        if text_clean:  # Пропускаем пустые параграфы
            lines.append({
                "id": idx,
                "text": text_clean,
                "line_number": idx,
                "html": content  # Сохраняем оригинальный HTML для точного выделения
            })
    
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

