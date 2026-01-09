#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Модуль для работы с JSON метаданными в новой структуре.
Загрузка, сохранение и преобразование данных между форматом формы и структурой JSON.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from text_utils import merge_doi_url_with_references
except ImportError:
    def merge_doi_url_with_references(references: List[str]) -> List[str]:
        return references


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
    
    # Маппинг полей формы на структуру JSON
    # Названия
    if "title" in form_data and form_data["title"]:
        result["artTitles"]["RUS"] = str(form_data["title"]).strip()
    if "title_en" in form_data and form_data["title_en"]:
        result["artTitles"]["ENG"] = str(form_data["title_en"]).strip()
    
    # Аннотации
    if "annotation" in form_data and form_data["annotation"]:
        result["abstracts"]["RUS"] = str(form_data["annotation"]).strip()
    if "annotation_en" in form_data and form_data["annotation_en"]:
        result["abstracts"]["ENG"] = str(form_data["annotation_en"]).strip()
    
    # Ключевые слова
    if "keywords" in form_data:
        keywords_ru = form_data["keywords"]
        if isinstance(keywords_ru, str):
            # Разбиваем по разделителям
            if ";" in keywords_ru:
                result["keywords"]["RUS"] = [k.strip() for k in keywords_ru.split(";") if k.strip()]
            elif "," in keywords_ru:
                result["keywords"]["RUS"] = [k.strip() for k in keywords_ru.split(",") if k.strip()]
            else:
                result["keywords"]["RUS"] = [keywords_ru.strip()] if keywords_ru.strip() else []
        elif isinstance(keywords_ru, list):
            result["keywords"]["RUS"] = [str(k).strip() for k in keywords_ru if str(k).strip()]
    
    if "keywords_en" in form_data:
        keywords_en = form_data["keywords_en"]
        if isinstance(keywords_en, str):
            if ";" in keywords_en:
                result["keywords"]["ENG"] = [k.strip() for k in keywords_en.split(";") if k.strip()]
            elif "," in keywords_en:
                result["keywords"]["ENG"] = [k.strip() for k in keywords_en.split(",") if k.strip()]
            else:
                result["keywords"]["ENG"] = [keywords_en.strip()] if keywords_en.strip() else []
        elif isinstance(keywords_en, list):
            result["keywords"]["ENG"] = [str(k).strip() for k in keywords_en if str(k).strip()]
    
    # Список литературы
    if "references_ru" in form_data:
        refs_ru = form_data["references_ru"]
        if isinstance(refs_ru, str):
            refs_list = [r.strip() for r in refs_ru.split("\n") if r.strip()]
        elif isinstance(refs_ru, list):
            refs_list = [str(r).strip() for r in refs_ru if str(r).strip()]
        else:
            refs_list = []
        result["references"]["RUS"] = merge_doi_url_with_references(refs_list)
    
    if "references_en" in form_data:
        refs_en = form_data["references_en"]
        if isinstance(refs_en, str):
            refs_list = [r.strip() for r in refs_en.split("\n") if r.strip()]
        elif isinstance(refs_en, list):
            refs_list = [str(r).strip() for r in refs_en if str(r).strip()]
        else:
            refs_list = []
        result["references"]["ENG"] = merge_doi_url_with_references(refs_list)
    
    # Коды
    if "udc" in form_data and form_data["udc"]:
        result["codes"]["udk"] = str(form_data["udc"]).strip()
    if "doi" in form_data and form_data["doi"]:
        result["codes"]["doi"] = str(form_data["doi"]).strip()
    if "bbk" in form_data and form_data["bbk"]:
        result["codes"]["bbk"] = str(form_data["bbk"]).strip()
    if "edn" in form_data and form_data["edn"]:
        result["codes"]["edn"] = str(form_data["edn"]).strip()
    
    # Даты
    if "received_date" in form_data and form_data["received_date"]:
        # Преобразуем формат даты в YYYY-MM-DD если нужно
        date_str = str(form_data["received_date"]).strip()
        result["dates"]["dateReceived"] = normalize_date(date_str)
    
    if "accepted_date" in form_data and form_data["accepted_date"]:
        date_str = str(form_data["accepted_date"]).strip()
        result["dates"]["dateAccepted"] = normalize_date(date_str)
    
    if "date_publication" in form_data and form_data["date_publication"]:
        date_str = str(form_data["date_publication"]).strip()
        result["dates"]["datePublication"] = normalize_date(date_str)
    
    # Тип статьи и язык публикации
    if "art_type" in form_data and form_data["art_type"]:
        result["artType"] = str(form_data["art_type"]).strip()
    
    if "publ_lang" in form_data and form_data["publ_lang"]:
        result["PublLang"] = str(form_data["publ_lang"]).strip()
    
    # Авторы (обрабатываем данные из раскрывающегося меню)
    if "authors" in form_data and form_data["authors"]:
        authors_data = form_data["authors"]
        if isinstance(authors_data, list) and len(authors_data) > 0:
            result["authors"] = authors_data
    # Если авторов нет в форме, но есть в existing_json, оставляем их как есть
    
    # Страницы
    if "pages" in form_data and form_data["pages"]:
        result["pages"] = str(form_data["pages"]).strip()
    
    # Финансирование
    if "funding" in form_data and form_data["funding"]:
        result["fundings"]["RUS"] = str(form_data["funding"]).strip()
    
    if "funding_en" in form_data and form_data["funding_en"]:
        result["fundings"]["ENG"] = str(form_data["funding_en"]).strip()
    
    # Краткое сообщение
    if "short_message" in form_data and form_data["short_message"]:
        result["shortMessage"]["RUS"] = str(form_data["short_message"]).strip()
    
    if "short_message_en" in form_data and form_data["short_message_en"]:
        result["shortMessage"]["ENG"] = str(form_data["short_message_en"]).strip()
    
    return result


def json_structure_to_form_data(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Преобразует структуру JSON в данные для формы.
    
    Args:
        json_data: JSON данные в новой структуре
        
    Returns:
        Словарь с данными для формы
    """
    form_data = {}
    
    # Названия
    form_data["title"] = json_data.get("artTitles", {}).get("RUS", "")
    form_data["title_en"] = json_data.get("artTitles", {}).get("ENG", "")
    
    # Аннотации
    form_data["annotation"] = json_data.get("abstracts", {}).get("RUS", "")
    form_data["annotation_en"] = json_data.get("abstracts", {}).get("ENG", "")
    
    # Ключевые слова
    keywords_ru = json_data.get("keywords", {}).get("RUS", [])
    form_data["keywords"] = "; ".join(keywords_ru) if isinstance(keywords_ru, list) else str(keywords_ru)
    
    keywords_en = json_data.get("keywords", {}).get("ENG", [])
    form_data["keywords_en"] = "; ".join(keywords_en) if isinstance(keywords_en, list) else str(keywords_en)
    
    # Список литературы
    refs_ru = json_data.get("references", {}).get("RUS", [])
    form_data["references_ru"] = "\n".join(refs_ru) if isinstance(refs_ru, list) else str(refs_ru)
    
    refs_en = json_data.get("references", {}).get("ENG", [])
    form_data["references_en"] = "\n".join(refs_en) if isinstance(refs_en, list) else str(refs_en)
    
    # Коды
    form_data["udc"] = json_data.get("codes", {}).get("udk", "")
    form_data["doi"] = json_data.get("codes", {}).get("doi", "")
    form_data["bbk"] = json_data.get("codes", {}).get("bbk", "")
    form_data["edn"] = json_data.get("codes", {}).get("edn", "")
    
    # Даты
    form_data["received_date"] = json_data.get("dates", {}).get("dateReceived", "")
    form_data["accepted_date"] = json_data.get("dates", {}).get("dateAccepted", "")
    form_data["date_publication"] = json_data.get("dates", {}).get("datePublication", "")
    
    # Тип статьи и язык публикации
    form_data["art_type"] = json_data.get("artType", "")
    form_data["publ_lang"] = json_data.get("PublLang", "")
    
    # Авторы (передаем полную структуру для раскрывающегося меню)
    authors = json_data.get("authors", [])
    if authors and isinstance(authors, list):
        # Передаем полную структуру авторов
        form_data["authors"] = authors
    else:
        form_data["authors"] = []
    
    # Страницы
    form_data["pages"] = json_data.get("pages", "")
    
    # Финансирование (раздельно для русского и английского)
    form_data["funding"] = json_data.get("fundings", {}).get("RUS", "")
    form_data["funding_en"] = json_data.get("fundings", {}).get("ENG", "")
    
    # Краткое сообщение
    form_data["short_message"] = json_data.get("shortMessage", {}).get("RUS", "")
    form_data["short_message_en"] = json_data.get("shortMessage", {}).get("ENG", "")
    
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
    Находит соответствующий DOCX файл для JSON файла.
    Сначала пытается найти отдельный файл для статьи, затем общий файл выпуска.
    Все файлы ищутся в words_input_dir в соответствующей подпапке.
    
    Args:
        json_path: Путь к JSON файлу
        words_input_dir: Директория с DOCX файлами (всегда words_input)
        json_input_dir: Базовая директория JSON файлов для определения подпапки
        
    Returns:
        Путь к DOCX файлу или None, если не найден
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
    
    # Сначала ищем отдельный файл для статьи
    for ext in [".docx", ".rtf"]:
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
        for ext in [".docx", ".rtf"]:
            common_file = same_subdir / f"{name}{ext}"
            if common_file.exists():
                return common_file
    
    # Если не нашли по стандартным именам, ищем любой DOCX/RTF файл в подпапке
    # (если там только один файл, скорее всего это общий файл выпуска)
    docx_files = list(same_subdir.glob("*.docx"))
    rtf_files = list(same_subdir.glob("*.rtf"))
    all_files = docx_files + rtf_files
    
    # Если в подпапке только один файл, считаем его общим файлом выпуска
    if len(all_files) == 1:
        return all_files[0]
    
    return None

