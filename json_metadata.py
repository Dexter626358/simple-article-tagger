#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Модуль для работы с JSON метаданными в новой структуре.
Загрузка, сохранение и преобразование данных между форматом формы и структурой JSON.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from html import escape, unescape
from html.parser import HTMLParser

try:
    from text_utils import merge_doi_url_with_references
except ImportError:
    def merge_doi_url_with_references(references: List[str]) -> List[str]:
        return references

try:
    from search_publications import normalize_keywords_separators
except ImportError:
    def normalize_keywords_separators(raw: str) -> str:
        return (raw or "").strip()


ALLOWED_ANNOTATION_TAGS = {"b", "i", "em", "strong", "sup", "sub", "br"}


class _AnnotationHtmlSanitizer(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: List[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        tag_l = (tag or "").lower()
        if tag_l not in ALLOWED_ANNOTATION_TAGS:
            return
        if tag_l == "br":
            self._parts.append("<br>")
            return
        self._parts.append(f"<{tag_l}>")

    def handle_endtag(self, tag: str) -> None:
        tag_l = (tag or "").lower()
        if tag_l in ALLOWED_ANNOTATION_TAGS and tag_l != "br":
            self._parts.append(f"</{tag_l}>")

    def handle_data(self, data: str) -> None:
        if not data:
            return
        normalized = data.replace("\r\n", "\n").replace("\r", "\n")
        parts = normalized.split("\n")
        for idx, part in enumerate(parts):
            if part:
                self._parts.append(escape(part))
            if idx < len(parts) - 1:
                self._parts.append("<br>")

    def get_html(self) -> str:
        html = "".join(self._parts)
        html = re.sub(r"(?:<br>\s*){3,}", "<br><br>", html, flags=re.IGNORECASE).strip()
        html = re.sub(r"^(?:<br>\s*)+|(?:<br>\s*)+$", "", html, flags=re.IGNORECASE)
        return html.strip()


def sanitize_annotation_html(html_text: Any) -> str:
    if not html_text:
        return ""
    parser = _AnnotationHtmlSanitizer()
    parser.feed(str(html_text))
    parser.close()
    return parser.get_html()


def annotation_html_to_plain_text(html_text: Any) -> str:
    if not html_text:
        return ""
    text = str(html_text)
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</(div|p|li)>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = unescape(text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


def _normalize_empty_field(value: Any) -> str:
    """
    Прочерки (—, –, -) и пустые значения не подставляем в поля — возвращаем пустую строку.
    """
    if value is None:
        return ""
    s = str(value).strip()
    if not s:
        return ""
    if re.match(r"^[\s\-–—\u2013\u2014]+$", s):
        return ""
    return s


def load_json_metadata(json_path: Path) -> Dict[str, Any]:
    """
    Загружает JSON файл с метаданными.
    
    Args:
        json_path: Путь к JSON файлу
        
    Returns:
        Словарь с метаданными
    """
    if not json_path.exists():
        raise FileNotFoundError(f"JSON файл не найден: {json_path}")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json_metadata(metadata: Dict[str, Any], json_path: Path) -> None:
    """
    Сохраняет метаданные в JSON файл.
    
    Args:
        metadata: Словарь с метаданными
        json_path: Путь к JSON файлу для сохранения
    """
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)


def form_data_to_json_structure(form_data: Dict[str, Any], existing_json: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Преобразует данные из формы в структуру JSON.
    Обновляет существующий JSON новыми данными из формы.
    
    Args:
        form_data: Данные из формы разметки
        existing_json: Существующий JSON (если есть)
        
    Returns:
        Обновленный JSON в правильной структуре
    """
    if existing_json is None:
        existing_json = {}
    
    # Создаем копию существующего JSON
    result = json.loads(json.dumps(existing_json))  # Глубокая копия
    
    # Инициализируем структуру, если её нет
    if "artTitles" not in result:
        result["artTitles"] = {"RUS": "", "ENG": ""}
    if "abstracts" not in result:
        result["abstracts"] = {"RUS": "", "ENG": ""}
    if "keywords" not in result:
        result["keywords"] = {"RUS": [], "ENG": []}
    if "references" not in result:
        result["references"] = {"RUS": [], "ENG": []}
    if "codes" not in result:
        result["codes"] = {"udk": "", "bbk": "", "doi": "", "edn": ""}
    if "dates" not in result:
        result["dates"] = {"dateReceived": "", "dateAccepted": "", "datePublication": ""}
    if "fundings" not in result:
        result["fundings"] = {"RUS": "", "ENG": ""}
    if "shortMessage" not in result:
        result["shortMessage"] = {"RUS": "", "ENG": ""}
    if "artType" not in result:
        result["artType"] = ""
    if "PublLang" not in result:
        result["PublLang"] = ""
    if "pages" not in result:
        result["pages"] = ""
    
    # Маппинг полей формы на структуру JSON (прочерки — не сохраняем, оставляем поле пустым)
    # Названия
    if "title" in form_data:
        v = _normalize_empty_field(form_data["title"])
        if v:
            result["artTitles"]["RUS"] = v
    if "title_en" in form_data:
        v = _normalize_empty_field(form_data["title_en"])
        if v:
            result["artTitles"]["ENG"] = v
    
    # Аннотации
    if "annotation" in form_data:
        v = _normalize_empty_field(form_data["annotation"])
        if v:
            result["abstracts"]["RUS"] = v
    if "annotation_en" in form_data:
        v = _normalize_empty_field(form_data["annotation_en"])
        if v:
            result["abstracts"]["ENG"] = v
    if "annotation_html" in form_data:
        sanitized = sanitize_annotation_html(form_data.get("annotation_html"))
        if sanitized and _normalize_empty_field(sanitized):
            result["abstracts"]["RUS"] = sanitized
    if "annotation_en_html" in form_data:
        sanitized = sanitize_annotation_html(form_data.get("annotation_en_html"))
        if sanitized and _normalize_empty_field(sanitized):
            result["abstracts"]["ENG"] = sanitized
    # Удаляем legacy-ключ, если был создан ранее.
    if "abstractsHtml" in result:
        result.pop("abstractsHtml", None)
    
    # Ключевые слова (прочерки не сохраняем)
    if "keywords" in form_data:
        keywords_ru = form_data["keywords"]
        if isinstance(keywords_ru, str):
            norm = normalize_keywords_separators(keywords_ru)
            result["keywords"]["RUS"] = [k.strip() for k in norm.split(";") if _normalize_empty_field(k)] if norm else []
        elif isinstance(keywords_ru, list):
            result["keywords"]["RUS"] = [str(k).strip() for k in keywords_ru if _normalize_empty_field(k)]
    if "keywords_en" in form_data:
        keywords_en = form_data["keywords_en"]
        if isinstance(keywords_en, str):
            norm = normalize_keywords_separators(keywords_en)
            result["keywords"]["ENG"] = [k.strip() for k in norm.split(";") if _normalize_empty_field(k)] if norm else []
        elif isinstance(keywords_en, list):
            result["keywords"]["ENG"] = [str(k).strip() for k in keywords_en if _normalize_empty_field(k)]
    
    # Список литературы (строки только из прочерков не сохраняем)
    if "references_ru" in form_data:
        refs_ru = form_data["references_ru"]
        if isinstance(refs_ru, str):
            refs_list = [r.strip() for r in refs_ru.split("\n") if _normalize_empty_field(r)]
        elif isinstance(refs_ru, list):
            refs_list = [str(r).strip() for r in refs_ru if _normalize_empty_field(r)]
        else:
            refs_list = []
        result["references"]["RUS"] = merge_doi_url_with_references(refs_list)
    if "references_en" in form_data:
        refs_en = form_data["references_en"]
        if isinstance(refs_en, str):
            refs_list = [r.strip() for r in refs_en.split("\n") if _normalize_empty_field(r)]
        elif isinstance(refs_en, list):
            refs_list = [str(r).strip() for r in refs_en if _normalize_empty_field(r)]
        else:
            refs_list = []
        result["references"]["ENG"] = merge_doi_url_with_references(refs_list)
    
    # Коды
    if "udc" in form_data:
        v = _normalize_empty_field(form_data["udc"])
        if v:
            result["codes"]["udk"] = v
    if "doi" in form_data:
        v = _normalize_empty_field(form_data["doi"])
        if v:
            result["codes"]["doi"] = v
    if "bbk" in form_data:
        v = _normalize_empty_field(form_data["bbk"])
        if v:
            result["codes"]["bbk"] = v
    if "edn" in form_data:
        v = _normalize_empty_field(form_data["edn"])
        if v:
            result["codes"]["edn"] = v
    
    # Даты
    if "received_date" in form_data:
        date_str = _normalize_empty_field(form_data["received_date"])
        if date_str:
            result["dates"]["dateReceived"] = normalize_date(date_str)
    if "accepted_date" in form_data:
        date_str = _normalize_empty_field(form_data["accepted_date"])
        if date_str:
            result["dates"]["dateAccepted"] = normalize_date(date_str)
    if "date_publication" in form_data:
        date_str = _normalize_empty_field(form_data["date_publication"])
        if date_str:
            result["dates"]["datePublication"] = normalize_date(date_str)
    
    # Тип статьи и язык публикации
    if "art_type" in form_data:
        v = _normalize_empty_field(form_data["art_type"])
        if v:
            result["artType"] = v
    if "publ_lang" in form_data:
        v = _normalize_empty_field(form_data["publ_lang"])
        if v:
            result["PublLang"] = v
    
    # Авторы (обрабатываем данные из раскрывающегося меню)
    if "authors" in form_data and form_data["authors"]:
        authors_data = form_data["authors"]
        if isinstance(authors_data, list) and len(authors_data) > 0:
            result["authors"] = authors_data
    # Если авторов нет в форме, но есть в existing_json, оставляем их как есть
    
    # Страницы
    if "pages" in form_data:
        v = _normalize_empty_field(form_data["pages"])
        if v:
            result["pages"] = v
    
    # Финансирование
    if "funding" in form_data:
        v = _normalize_empty_field(form_data["funding"])
        if v:
            result["fundings"]["RUS"] = v
    if "funding_en" in form_data:
        v = _normalize_empty_field(form_data["funding_en"])
        if v:
            result["fundings"]["ENG"] = v
    
    # Краткое сообщение
    if "short_message" in form_data:
        v = _normalize_empty_field(form_data["short_message"])
        if v:
            result["shortMessage"]["RUS"] = v
    if "short_message_en" in form_data:
        v = _normalize_empty_field(form_data["short_message_en"])
        if v:
            result["shortMessage"]["ENG"] = v
    
    return result


def json_structure_to_form_data(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Преобразует структуру JSON в данные для формы.
    
    Args:
        json_data: JSON данные в новой структуре
        
    Returns:
        Словарь с данными для формы
    """
    if not isinstance(json_data, dict):
        if isinstance(json_data, list):
            json_data = {"references": {"RUS": json_data, "ENG": []}}
        else:
            json_data = {}

    form_data = {}
    
    # Названия (прочерки не подставляем — оставляем поле пустым)
    form_data["title"] = _normalize_empty_field(json_data.get("artTitles", {}).get("RUS", ""))
    form_data["title_en"] = _normalize_empty_field(json_data.get("artTitles", {}).get("ENG", ""))
    
    # Аннотации
    abstracts_ru = str(json_data.get("abstracts", {}).get("RUS", "") or "")
    abstracts_en = str(json_data.get("abstracts", {}).get("ENG", "") or "")
    if _normalize_empty_field(abstracts_ru) == "":
        abstracts_ru = ""
    if _normalize_empty_field(abstracts_en) == "":
        abstracts_en = ""
    form_data["annotation"] = annotation_html_to_plain_text(abstracts_ru) if "<" in abstracts_ru else _normalize_empty_field(abstracts_ru)
    form_data["annotation_en"] = annotation_html_to_plain_text(abstracts_en) if "<" in abstracts_en else _normalize_empty_field(abstracts_en)
    form_data["annotation_html"] = sanitize_annotation_html(abstracts_ru)
    form_data["annotation_en_html"] = sanitize_annotation_html(abstracts_en)
    
    # Ключевые слова
    keywords_ru = json_data.get("keywords", {}).get("RUS", [])
    form_data["keywords"] = _normalize_empty_field("; ".join(keywords_ru) if isinstance(keywords_ru, list) else str(keywords_ru))
    keywords_en = json_data.get("keywords", {}).get("ENG", [])
    form_data["keywords_en"] = _normalize_empty_field("; ".join(keywords_en) if isinstance(keywords_en, list) else str(keywords_en))
    
    # Список литературы
    refs_ru = json_data.get("references", {}).get("RUS", [])
    form_data["references_ru"] = "\n".join(r for r in (refs_ru if isinstance(refs_ru, list) else []) if _normalize_empty_field(r))
    refs_en = json_data.get("references", {}).get("ENG", [])
    form_data["references_en"] = "\n".join(r for r in (refs_en if isinstance(refs_en, list) else []) if _normalize_empty_field(r))
    
    # Коды
    form_data["udc"] = _normalize_empty_field(json_data.get("codes", {}).get("udk", ""))
    form_data["doi"] = _normalize_empty_field(json_data.get("codes", {}).get("doi", ""))
    form_data["bbk"] = _normalize_empty_field(json_data.get("codes", {}).get("bbk", ""))
    form_data["edn"] = _normalize_empty_field(json_data.get("codes", {}).get("edn", ""))
    
    # Даты
    form_data["received_date"] = _normalize_empty_field(json_data.get("dates", {}).get("dateReceived", ""))
    form_data["accepted_date"] = _normalize_empty_field(json_data.get("dates", {}).get("dateAccepted", ""))
    form_data["date_publication"] = _normalize_empty_field(json_data.get("dates", {}).get("datePublication", ""))
    
    # Тип статьи и язык публикации
    form_data["art_type"] = _normalize_empty_field(json_data.get("artType", ""))
    form_data["publ_lang"] = _normalize_empty_field(json_data.get("PublLang", ""))
    
    # Авторы (передаем полную структуру для раскрывающегося меню)
    authors = json_data.get("authors", [])
    if authors and isinstance(authors, list):
        form_data["authors"] = authors
    else:
        form_data["authors"] = []
    
    # Страницы
    form_data["pages"] = _normalize_empty_field(json_data.get("pages", ""))
    
    # Финансирование
    form_data["funding"] = _normalize_empty_field(json_data.get("fundings", {}).get("RUS", ""))
    form_data["funding_en"] = _normalize_empty_field(json_data.get("fundings", {}).get("ENG", ""))
    
    # Краткое сообщение
    form_data["short_message"] = _normalize_empty_field(json_data.get("shortMessage", {}).get("RUS", ""))
    form_data["short_message_en"] = _normalize_empty_field(json_data.get("shortMessage", {}).get("ENG", ""))
    
    return form_data


def normalize_date(date_str: str) -> str:
    """
    Нормализует дату в формат YYYY-MM-DD.
    
    Args:
        date_str: Дата в различных форматах
        
    Returns:
        Дата в формате YYYY-MM-DD
    """
    if not date_str:
        return ""
    
    date_str = date_str.strip()
    
    # Если уже в формате YYYY-MM-DD
    if len(date_str) == 10 and date_str.count("-") == 2:
        return date_str
    
    # Пытаемся распарсить различные форматы
    import re
    # DD.MM.YYYY или DD/MM/YYYY
    match = re.match(r'(\d{1,2})[./](\d{1,2})[./](\d{4})', date_str)
    if match:
        day, month, year = match.groups()
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    
    # YYYY.MM.DD
    match = re.match(r'(\d{4})[./](\d{1,2})[./](\d{1,2})', date_str)
    if match:
        year, month, day = match.groups()
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    
    # Если не удалось распарсить, возвращаем как есть
    return date_str


def find_docx_for_json(json_path: Path, words_input_dir: Path, json_input_dir: Optional[Path] = None) -> Optional[Path]:
    """
    Находит соответствующий файл (DOCX/RTF/PDF) для JSON файла.
    Сначала пытается найти отдельный файл для статьи, затем общий файл выпуска.
    Все файлы ищутся в words_input_dir в соответствующей подпапке.
    
    Args:
        json_path: Путь к JSON файлу
        words_input_dir: Директория с файлами статей (DOCX/RTF/PDF) (всегда words_input)
        json_input_dir: Базовая директория JSON файлов для определения подпапки
        
    Returns:
        Путь к файлу (DOCX/RTF/PDF) или None, если не найден
    """
    json_stem = json_path.stem
    subdir_name = None
    
    # Определяем подпапку JSON файла
    if json_input_dir:
        try:
            # Получаем относительный путь от json_input_dir
            relative_path = json_path.relative_to(json_input_dir)
            # Если есть подпапка (больше одного компонента пути)
            if len(relative_path.parts) > 1:
                subdir_name = relative_path.parts[0]  # Имя подпапки
        except ValueError:
            # Если не удалось определить относительный путь, возвращаем None
            return None
    
    # Если не удалось определить подпапку, не можем искать файл
    if not subdir_name:
        return None
    
    # Ищем файлы в подпапке words_input/подпапка/
    same_subdir = words_input_dir / subdir_name
    if not same_subdir.exists() or not same_subdir.is_dir():
        return None
    
    # Сначала ищем отдельный файл для статьи (DOCX, RTF, PDF)
    for ext in [".docx", ".rtf", ".pdf"]:
        docx_path = same_subdir / f"{json_stem}{ext}"
        if docx_path.exists():
            return docx_path
    
    # Если не найден отдельный файл, ищем общий файл выпуска
    # Варианты имен общего файла выпуска
    common_names = [
        subdir_name,  # Имя подпапки (например, "2658-7475_2019_1")
        "issue",      # Стандартное имя
        "выпуск",     # Русское имя
        "release",    # Английское имя
        "journal",    # Альтернативное имя
    ]
    
    for name in common_names:
        for ext in [".docx", ".rtf", ".pdf"]:
            common_file = same_subdir / f"{name}{ext}"
            if common_file.exists():
                return common_file
    
    # Если не нашли по стандартным именам, ищем любой файл (DOCX/RTF/PDF) в подпапке
    # (если там только один файл, скорее всего это общий файл выпуска)
    docx_files = list(same_subdir.glob("*.docx"))
    rtf_files = list(same_subdir.glob("*.rtf"))
    pdf_files = list(same_subdir.glob("*.pdf"))
    all_files = docx_files + rtf_files + pdf_files
    
    # Если в подпапке только один файл, считаем его общим файлом выпуска
    if len(all_files) == 1:
        return all_files[0]
    
    return None
