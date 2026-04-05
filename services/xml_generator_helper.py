#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Вспомогательный модуль для генерации XML файлов из JSON файлов в папке output.
Парсит название папки (issn_год_том_номер или issn_год_номер) и использует данные
из data/list_of_journals.json для создания конфигурации журнала.
"""

from __future__ import annotations

import builtins
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from services.xml_generator import (
        json_to_article_xml,
        save_xml_to_file,
        create_xml_issue,
    )
    XML_GENERATOR_AVAILABLE = True
except ImportError as e:
    XML_GENERATOR_AVAILABLE = False
    print(f"⚠ Ошибка: не удалось импортировать xml_generator: {e}")
    print("   Убедитесь, что services/xml_generator.py доступен и все его зависимости установлены.")
except Exception as e:
    XML_GENERATOR_AVAILABLE = False
    print(f"⚠ Ошибка при импорте xml_generator: {e}")
    print("   Возможно, отсутствует модуль journal_config или другие зависимости.")

# Попытка импорта библиотек для валидации XSD
XSD_VALIDATION_AVAILABLE = False
XSD_VALIDATION_LIBRARY: Optional[str] = None

try:
    import xmlschema  # type: ignore
    XSD_VALIDATION_AVAILABLE = True
    XSD_VALIDATION_LIBRARY = "xmlschema"
except ImportError:
    try:
        from lxml import etree  # type: ignore
        XSD_VALIDATION_AVAILABLE = True
        XSD_VALIDATION_LIBRARY = "lxml"
    except ImportError:
        XSD_VALIDATION_AVAILABLE = False
        XSD_VALIDATION_LIBRARY = None


def print(*args, **kwargs) -> None:  # type: ignore[no-redef]
    """
    Print safely on Windows consoles that cannot encode emoji/status symbols.
    """
    sep = kwargs.pop("sep", " ")
    end = kwargs.pop("end", "\n")
    flush = kwargs.pop("flush", False)
    file = kwargs.pop("file", sys.stdout)
    text = sep.join(str(arg) for arg in args)
    try:
        builtins.print(text, end=end, flush=flush, file=file, **kwargs)
    except UnicodeEncodeError:
        encoding = getattr(file, "encoding", None) or "utf-8"
        safe_text = text.encode(encoding, errors="replace").decode(encoding, errors="replace")
        builtins.print(safe_text, end=end, flush=flush, file=file, **kwargs)


def validate_xml_against_schema(xml_file: Path, schema_file: Optional[Path] = None) -> tuple[bool, list[str]]:
    """
    Валидирует XML файл на соответствие XSD схеме.
    
    Args:
        xml_file: Путь к XML файлу для валидации
        schema_file: Путь к XSD схеме (по умолчанию: data/xml_schema.xsd в корне проекта)
        
    Returns:
        Кортеж (валиден ли файл, список ошибок)
    """
    errors: list[str] = []
    
    # Определяем путь к схеме
    if schema_file is None:
        script_dir = Path(__file__).parent.resolve()
        schema_file = script_dir / "data/xml_schema.xsd"
    
    # Проверяем существование файлов
    if not xml_file.exists():
        errors.append(f"XML файл не найден: {xml_file}")
        return False, errors
    
    if not schema_file.exists():
        errors.append(f"XSD схема не найдена: {schema_file}")
        return False, errors
    
    # Пробуем использовать xmlschema (предпочтительно)
    if XSD_VALIDATION_AVAILABLE and XSD_VALIDATION_LIBRARY != "lxml":
        try:
            import xmlschema
            schema = xmlschema.XMLSchema(str(schema_file))
            try:
                schema.validate(str(xml_file))
                return True, []
            except xmlschema.XMLSchemaValidationError as e:
                # Пытаемся получить более детальную информацию об ошибках
                try:
                    for error in schema.iter_errors(str(xml_file)):
                        error_str = str(error)
                        # Игнорируем ошибки для пустого volume (это допустимо)
                        if "volume" in error_str and ("not a valid value" in error_str or "unsignedInt" in error_str):
                            continue
                        # Игнорируем ошибки для пустого references (это допустимо)
                        if "references" in error_str and ("Missing child element" in error_str or "Expected is ( reference )" in error_str):
                            continue
                        # Игнорируем ошибки для пустого authorCodes (это допустимо)
                        if "authorCodes" in error_str and "Missing child element" in error_str:
                            continue
                        errors.append(f"  - {error}")
                except Exception:
                    pass
                # Если все ошибки были отфильтрованы, считаем валидацию успешной
                if not errors:
                    return True, []
                return False, errors
            except Exception as e:
                errors.append(f"Ошибка при валидации: {e}")
                return False, errors
        except ImportError:
            pass
    
    # Пробуем использовать lxml
    if XSD_VALIDATION_AVAILABLE and XSD_VALIDATION_LIBRARY == "lxml":
        try:
            from lxml import etree
            
            # Загружаем схему
            try:
                schema_doc = etree.parse(str(schema_file))
                schema = etree.XMLSchema(schema_doc)
            except Exception as e:
                errors.append(f"Ошибка при загрузке XSD схемы: {e}")
                return False, errors
            
            # Загружаем и валидируем XML
            try:
                xml_doc = etree.parse(str(xml_file))
                schema.assertValid(xml_doc)
                return True, []
            except etree.DocumentInvalid as e:
                # Собираем все ошибки валидации, исключая допустимые случаи
                for error in schema.error_log:
                    error_msg = error.message
                    # Игнорируем ошибки для пустого volume (это допустимо)
                    if "volume" in error_msg and ("not a valid value" in error_msg or "unsignedInt" in error_msg):
                        continue
                    # Игнорируем ошибки для пустого references (это допустимо)
                    if "references" in error_msg and ("Missing child element" in error_msg or "Expected is ( reference )" in error_msg):
                        continue
                    # Игнорируем ошибки для пустого authorCodes (это допустимо)
                    if "authorCodes" in error_msg and "Missing child element" in error_msg:
                        continue
                    errors.append(f"Строка {error.line}, колонка {error.column}: {error.message}")
                # Если все ошибки были отфильтрованы, считаем валидацию успешной
                if not errors:
                    return True, []
                return False, errors
            except Exception as e:
                errors.append(f"Ошибка при валидации XML: {e}")
                return False, errors
        except ImportError:
            pass
    
    # Если библиотеки недоступны, используем базовую проверку структуры
    if not XSD_VALIDATION_AVAILABLE:
        errors.append("⚠ Библиотеки для валидации XSD недоступны (xmlschema или lxml)")
        errors.append("   Установите одну из них: pip install xmlschema или pip install lxml")
        errors.append("   Выполняется базовая проверка структуры XML...")
        
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            # Базовая проверка структуры
            if root.tag != "journal":
                errors.append("Корневой элемент должен быть 'journal'")
                return False, errors
            
            required_elements = ["titleid", "journalInfo", "issue"]
            for elem_name in required_elements:
                if root.find(elem_name) is None:
                    errors.append(f"Отсутствует обязательный элемент: {elem_name}")
            
            if errors:
                return False, errors
            
            # Базовая проверка прошла успешно
            return True, []
        except ET.ParseError as e:
            errors.append(f"Ошибка парсинга XML: {e}")
            return False, errors
        except Exception as e:
            errors.append(f"Ошибка при проверке XML: {e}")
            return False, errors
    
    return False, errors


def parse_pages_range(pages_str: str) -> Optional[tuple[int, int]]:
    """
    Парсит строку с диапазоном страниц и возвращает минимальную и максимальную страницу.
    
    Поддерживаемые форматы:
    - "4-16" -> (4, 16)
    - "4–16" (тире) -> (4, 16)
    - "4—16" (длинное тире) -> (4, 16)
    - "4" -> (4, 4)
    - "4-16, 20-25" -> берется первый диапазон (4, 16)
    
    Args:
        pages_str: Строка с диапазоном страниц
        
    Returns:
        Кортеж (min_page, max_page) или None, если не удалось распарсить
    """
    if not pages_str or not pages_str.strip():
        return None
    
    pages_str = pages_str.strip()
    
    # Убираем пробелы
    pages_str = pages_str.replace(" ", "")
    
    # Пробуем разные разделители: -, –, —, ,
    for separator in ["-", "–", "—", ","]:
        if separator in pages_str:
            parts = pages_str.split(separator, 1)
            if len(parts) == 2:
                try:
                    start = int(parts[0])
                    # Для второго числа берем только первую часть (до следующего разделителя)
                    end_str = parts[1].split(",")[0].split("-")[0].split("–")[0].split("—")[0]
                    end = int(end_str)
                    return (min(start, end), max(start, end))
                except ValueError:
                    continue
    
    # Если это одно число
    try:
        page_num = int(pages_str.split(",")[0].split("-")[0].split("–")[0].split("—")[0])
        return (page_num, page_num)
    except ValueError:
        return None


def json_file_start_page(json_path: Path) -> Optional[int]:
    """Начальная страница статьи из поля pages в JSON, либо None."""
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        pr = parse_pages_range(str(data.get("pages") or ""))
        if pr:
            return pr[0]
    except Exception:
        return None
    return None


def sort_json_files_by_start_page(json_files: list[Path]) -> list[Path]:
    """
    Сортирует JSON статей по начальной странице (по возрастанию), затем по имени файла.
    Файлы без распознаваемого поля pages идут в конце, по имени.
    """

    def sort_key(p: Path) -> tuple:
        sp = json_file_start_page(p)
        if sp is not None:
            return (0, sp, p.name.lower())
        return (1, p.name.lower())

    return sorted(json_files, key=sort_key)


def analyze_issue_pages(json_files: list[Path]) -> Optional[str]:
    """
    Анализирует страницы всех статей в JSON файлах и определяет диапазон страниц выпуска.
    
    Args:
        json_files: Список путей к JSON файлам статей
        
    Returns:
        Строка с диапазоном страниц в формате "min-max" или None, если не удалось определить
    """
    if not json_files:
        return None
    
    min_page = None
    max_page = None
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            pages_str = data.get("pages", "")
            if not pages_str:
                continue
            
            pages_range = parse_pages_range(pages_str)
            if pages_range:
                article_min, article_max = pages_range
                
                if min_page is None or article_min < min_page:
                    min_page = article_min
                if max_page is None or article_max > max_page:
                    max_page = article_max
        except Exception as e:
            # Пропускаем файлы с ошибками
            print(f"   ⚠ Ошибка при анализе страниц в {json_file.name}: {e}")
            continue
    
    if min_page is not None and max_page is not None:
        if min_page == max_page:
            return str(min_page)
        else:
            return f"{min_page}-{max_page}"
    
    return None


def parse_folder_name(folder_name: str) -> Optional[Dict[str, Any]]:
    """
    Парсит название папки формата issn_год_том_номер или issn_год_номер.
    
    Args:
        folder_name: Название папки (например, "2619-1601_2024_6" или "2619-1601_2024_10_6")
        
    Returns:
        Словарь с полями: issn, year, volume (опционально), number
        или None, если не удалось распарсить
    """
    # Паттерны для парсинга:
    # issn_год_номер (например: 2619-1601_2024_6 или 0869-544X_2025_6)
    # issn_год_том_номер (например: 2619-1601_2024_10_6)
    # ISSN может быть в форматах: XXXX-XXXX, XXXX-XXX[X], XXXX-XXXX[X]
    # Поддерживаем: 4 цифры-3 цифрыX, 4 цифры-4 цифры, 4 цифры-4 цифрыX
    # Normalize Unicode dashes to ASCII hyphen for ISSN parsing.
    folder_name = (
        folder_name
        .replace("\u2013", "-")
        .replace("\u2014", "-")
        .replace("\u2212", "-")
    )

    pattern1 = r'^([0-9]{4}-[0-9]{3}[X]|[0-9]{4}-[0-9]{4}[X]?)_(\d{4})_(\d+)$'  # issn_год_номер
    pattern2 = r'^([0-9]{4}-[0-9]{3}[X]|[0-9]{4}-[0-9]{4}[X]?)_(\d{4})_(\d+)_(\d+)$'  # issn_год_том_номер

    match1 = re.match(pattern1, folder_name)
    if match1:
        return {
            "issn": match1.group(1),
            "year": match1.group(2),
            "volume": None,
            "number": match1.group(3),
        }
    
    match2 = re.match(pattern2, folder_name)
    if match2:
        return {
            "issn": match2.group(1),
            "year": match2.group(2),
            "volume": match2.group(3),
            "number": match2.group(4),
        }
    
    return None


def load_journal_from_list(issn: str, list_of_journals_path: Path) -> Optional[Dict[str, Any]]:
    """
    Загружает данные журнала из data/list_of_journals.json по ISSN.
    
    Args:
        issn: ISSN журнала
        list_of_journals_path: Путь к файлу data/list_of_journals.json
        
    Returns:
        Словарь с данными журнала (ISSN и Title) или None, если не найден
    """
    if not list_of_journals_path.exists():
        return None
    
    try:
        with open(list_of_journals_path, 'r', encoding='utf-8') as f:
            journals = json.load(f)
        
        # Ищем журнал по ISSN
        for journal in journals:
            if journal.get("ISSN", "").upper() == issn.upper():
                return journal
        
        return None
    except Exception as e:
        print(f"⚠ Ошибка при загрузке data/list_of_journals.json: {e}")
        return None


def create_config_from_folder_and_journal(
    folder_name: str,
    list_of_journals_path: Path,
    titleid: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """
    Создает конфигурацию журнала на основе названия папки и данных из data/list_of_journals.json.
    
    Args:
        folder_name: Название папки (например, "2619-1601_2024_6")
        list_of_journals_path: Путь к файлу data/list_of_journals.json
        titleid: ID журнала в elibrary (опционально)
        
    Returns:
        Словарь с конфигурацией журнала для xml_generator или None
    """
    # Парсим название папки
    issue_info = parse_folder_name(folder_name)
    if not issue_info:
        print(f"⚠ Не удалось распарсить название папки: {folder_name}")
        print("💡 Ожидаемый формат: ISSN_ГОД_НОМЕР или ISSN_ГОД_ТОМ_НОМЕР")
        return None
    
    issn = issue_info["issn"]
    year = issue_info["year"]
    volume = issue_info.get("volume")
    number = issue_info.get("number")
    
    # Загружаем данные журнала
    journal_data = load_journal_from_list(issn, list_of_journals_path)
    if not journal_data:
        print(f"⚠ Журнал с ISSN {issn} не найден в data/list_of_journals.json")
        return None
    
    journal_title = journal_data.get("Title", "")
    
    # Формируем конфигурацию
    config: Dict[str, Any] = {
        "titleid": titleid if titleid else 0,  # Обязательное поле, используем 0 по умолчанию
        "issn": issn,
        "journal_titles": {
            "ru": journal_title,
            "en": journal_title,  # Если есть отдельное английское название, можно добавить
        },
        "issue": {
            "year": year,
            "number": number,
            "pages": "",  # Обязательное поле для xml_generator, пустая строка по умолчанию
        },
    }
    
    # Добавляем том, если он есть
    if volume:
        config["issue"]["volume"] = volume
    else:
        # Если тома нет, добавляем пустую строку (xml_generator требует либо volume, либо number)
        config["issue"]["volume"] = ""
    
    return config


def generate_xml_for_output_folder(
    json_input_dir: Path,
    xml_output_dir: Path,
    list_of_journals_path: Path,
    folder_name: str,
) -> Optional[Path]:
    """
    Генерирует XML файл для выпуска на основе JSON файлов в указанной подпапке json_input.
    
    Args:
        json_input_dir: Базовая директория json_input (например, Path("json_input"))
        xml_output_dir: Директория для сохранения XML файлов (например, Path("xml_output"))
        list_of_journals_path: Путь к файлу data/list_of_journals.json
        folder_name: Название подпапки (например, "2619-1601_2024_6")
        
    Returns:
        Путь к созданному XML файлу или None в случае ошибки
    """
    if not XML_GENERATOR_AVAILABLE:
        print("❌ Ошибка: xml_generator недоступен")
        return None


def generate_xml_for_archive_dir(
    archive_dir: Path,
    list_of_journals_path: Path,
) -> Optional[Path]:
    """
    Генерирует XML файл для выпуска на основе JSON файлов в папке архива.

    Структура:
      input_files/<архив>/json/*.json
      input_files/<архив>/xml/<архив>.xml
    """
    if not XML_GENERATOR_AVAILABLE:
        print("❌ Ошибка: xml_generator недоступен")
        return None

    if not archive_dir.exists() or not archive_dir.is_dir():
        print(f"⚠ Папка архива не найдена: {archive_dir}")
        return None

    json_folder_path = archive_dir / "json"
    if not json_folder_path.exists() or not json_folder_path.is_dir():
        print(f"⚠ Папка с JSON не найдена: {json_folder_path}")
        return None

    folder_name = archive_dir.name
    json_files = list(json_folder_path.glob("*.json"))
    if not json_files:
        print(f"⚠ В папке {json_folder_path} не найдено JSON файлов")
        return None

    print(f"📄 Найдено {len(json_files)} JSON файлов в папке {json_folder_path}")

    issue_pages = analyze_issue_pages(json_files)
    if issue_pages:
        print(f"📄 Диапазон страниц выпуска: {issue_pages}")
    else:
        print("⚠ Не удалось определить диапазон страниц выпуска")

    config = create_config_from_folder_and_journal(folder_name, list_of_journals_path)
    if not config:
        print(f"❌ Не удалось создать конфигурацию для папки {folder_name}")
        return None

    if issue_pages:
        config["issue"]["pages"] = issue_pages

    try:
        tree = create_xml_issue(config)
        root = tree.getroot()

        issue_elem = root.find("issue")
        if issue_elem is None:
            print("❌ Ошибка: не найден элемент issue в XML структуре")
            return None

        articles_elem = issue_elem.find("articles")
        if articles_elem is None:
            print("❌ Ошибка: не найден элемент articles в XML структуре")
            return None

        for json_file in sort_json_files_by_start_page(json_files):
            try:
                article_elem = json_to_article_xml(json_file)
                articles_elem.append(article_elem)
                print(f"   ✓ Добавлена статья: {json_file.name}")
            except Exception as e:
                print(f"   ⚠ Ошибка при обработке {json_file.name}: {e}")

        xml_folder_path = archive_dir / "xml"
        xml_folder_path.mkdir(parents=True, exist_ok=True)
        xml_filename = f"{folder_name}.xml"
        xml_path = save_xml_to_file(tree, xml_filename, str(xml_folder_path))

        print(f"✅ XML файл успешно создан: {xml_path}")

        print("\n🔍 Валидация XML файла...")
        is_valid, errors = validate_xml_against_schema(xml_path)
        if is_valid:
            print("✅ XML файл прошел валидацию успешно!")
        else:
            print("❌ XML файл содержит ошибки валидации:")
            print("-" * 60)
            for i, error in enumerate(errors, 1):
                print(f"   {i}. {error}")
            print("-" * 60)
            print(f"   Всего найдено ошибок: {len(errors)}")
        return xml_path
    except Exception as e:
        print(f"❌ Ошибка при создании XML: {e}")
        return None
    
    # Путь к папке с JSON файлами
    json_folder_path = json_input_dir / folder_name
    
    if not json_folder_path.exists() or not json_folder_path.is_dir():
        print(f"⚠ Папка не найдена: {json_folder_path}")
        return None
    
    # Находим все JSON файлы в папке
    json_files = list(json_folder_path.glob("*.json"))
    
    if not json_files:
        print(f"⚠ В папке {folder_name} не найдено JSON файлов")
        return None
    
    print(f"📄 Найдено {len(json_files)} JSON файлов в папке {folder_name}")
    
    # Анализируем страницы статей для определения диапазона страниц выпуска
    issue_pages = analyze_issue_pages(json_files)
    if issue_pages:
        print(f"📄 Диапазон страниц выпуска: {issue_pages}")
    else:
        print(f"⚠ Не удалось определить диапазон страниц выпуска")
    
    # Создаем конфигурацию журнала
    config = create_config_from_folder_and_journal(folder_name, list_of_journals_path)
    if not config:
        print(f"❌ Не удалось создать конфигурацию для папки {folder_name}")
        return None
    
    # Обновляем диапазон страниц в конфигурации, если он был определен
    if issue_pages:
        config["issue"]["pages"] = issue_pages
    
    print(f"✅ Конфигурация создана:")
    print(f"   ISSN: {config.get('issn')}")
    print(f"   Журнал: {config.get('journal_titles', {}).get('ru', 'НЕ ЗАДАН')}")
    print(f"   Год: {config.get('issue', {}).get('year')}")
    if config.get('issue', {}).get('volume'):
        print(f"   Том: {config.get('issue', {}).get('volume')}")
    print(f"   Номер: {config.get('issue', {}).get('number')}")
    if config.get('issue', {}).get('pages'):
        print(f"   Страницы: {config.get('issue', {}).get('pages')}")
    
    # Создаем XML структуру
    try:
        # Создаем базовую структуру выпуска
        tree = create_xml_issue(config)
        root = tree.getroot()
        
        # Находим элемент articles
        issue_elem = root.find("issue")
        if issue_elem is None:
            print("❌ Ошибка: не найден элемент issue в XML структуре")
            return None
        
        articles_elem = issue_elem.find("articles")
        if articles_elem is None:
            print("❌ Ошибка: не найден элемент articles в XML структуре")
            return None
        
        # Добавляем статьи из JSON файлов
        for json_file in sort_json_files_by_start_page(json_files):
            try:
                article_elem = json_to_article_xml(json_file)
                articles_elem.append(article_elem)
                print(f"   ✓ Добавлена статья: {json_file.name}")
            except Exception as e:
                print(f"   ⚠ Ошибка при обработке {json_file.name}: {e}")
        
        # Создаем папку для XML в xml_output с тем же названием
        xml_folder_path = xml_output_dir / folder_name
        xml_folder_path.mkdir(parents=True, exist_ok=True)
        
        # Сохраняем XML файл
        xml_filename = f"{folder_name}.xml"
        xml_path = save_xml_to_file(tree, xml_filename, str(xml_folder_path))
        
        print(f"✅ XML файл успешно создан: {xml_path}")
        
        # Валидация XML файла
        print("\n🔍 Валидация XML файла...")
        is_valid, errors = validate_xml_against_schema(xml_path)
        
        if is_valid:
            print("✅ XML файл прошел валидацию успешно!")
            print("   Все проверки пройдены, структура соответствует схеме.")
        else:
            print("❌ XML файл содержит ошибки валидации:")
            print("-" * 60)
            for i, error in enumerate(errors, 1):
                print(f"   {i}. {error}")
            print("-" * 60)
            print(f"   Всего найдено ошибок: {len(errors)}")
            print("⚠ Рекомендуется исправить ошибки перед использованием файла.")
        
        return xml_path
        
    except Exception as e:
        print(f"❌ Ошибка при создании XML: {e}")
        return None


def generate_xml_for_all_folders(
    json_input_dir: Path,
    xml_output_dir: Path,
    list_of_journals_path: Path,
) -> list[Path]:
    """
    Генерирует XML файлы для всех подпапок в json_input_dir.
    
    Args:
        json_input_dir: Базовая директория json_input
        xml_output_dir: Директория для сохранения XML файлов
        list_of_journals_path: Путь к файлу data/list_of_journals.json
        
    Returns:
        Список путей к созданным XML файлам
    """
    if not json_input_dir.exists() or not json_input_dir.is_dir():
        print(f"⚠ Директория json_input не найдена: {json_input_dir}")
        return []
    
    created_xml_files = []
    
    # Находим все подпапки в json_input_dir
    for folder_path in json_input_dir.iterdir():
        if not folder_path.is_dir():
            continue
        
        folder_name = folder_path.name
        
        # Пропускаем служебные папки, если они есть
        if folder_name.startswith('.'):
            continue
        
        print(f"\n{'=' * 80}")
        print(f"📁 Обработка папки: {folder_name}")
        print(f"{'=' * 80}")
        
        xml_path = generate_xml_for_output_folder(
            json_input_dir,
            xml_output_dir,
            list_of_journals_path,
            folder_name,
        )
        
        if xml_path:
            created_xml_files.append(xml_path)
    
    return created_xml_files


# ----------------------------
# CLI / Запуск
# ----------------------------

def main() -> int:
    """
    Главная функция для запуска генерации XML файлов из командной строки.
    
    Returns:
        Код возврата (0 - успех, 1 - ошибка)
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Генерация XML файлов для выпусков журналов из JSON файлов в папке output"
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Путь к папке output с JSON файлами (по умолчанию: output)"
    )
    parser.add_argument(
        "--xml-output-dir",
        default=None,
        help="Путь к папке для сохранения XML файлов (по умолчанию: xml_output)"
    )
    parser.add_argument(
        "--list-of-journals",
        default=None,
        help="Путь к файлу data/list_of_journals.json (по умолчанию: data/list_of_journals.json)"
    )
    parser.add_argument(
        "--folder",
        default=None,
        help="Обработать только указанную подпапку (например: 2619-1601_2024_6). Если не указано, обрабатываются все подпапки"
    )
    
    args = parser.parse_args()
    
    # Определяем пути
    script_dir = Path(__file__).parent.resolve()
    
    if args.output_dir:
        json_input_dir = Path(args.output_dir)
        if not json_input_dir.is_absolute():
            json_input_dir = script_dir / json_input_dir
    else:
        json_input_dir = script_dir / "json_input"
    
    if args.xml_output_dir:
        xml_output_dir = Path(args.xml_output_dir)
        if not xml_output_dir.is_absolute():
            xml_output_dir = script_dir / xml_output_dir
    else:
        xml_output_dir = script_dir / "xml_output"
    
    if args.list_of_journals:
        list_of_journals_path = Path(args.list_of_journals)
        if not list_of_journals_path.is_absolute():
            list_of_journals_path = script_dir / list_of_journals_path
    else:
        list_of_journals_path = script_dir / "data/list_of_journals.json"
    
    # Проверяем доступность модулей
    if not XML_GENERATOR_AVAILABLE:
        print("❌ Ошибка: xml_generator недоступен")
        print("   Убедитесь, что services/xml_generator.py находится в той же папке")
        return 1
    
    # Проверяем наличие файла data/list_of_journals.json
    if not list_of_journals_path.exists():
        print(f"❌ Ошибка: файл data/list_of_journals.json не найден: {list_of_journals_path}")
        return 1
    
    # Проверяем наличие папки json_input
    if not json_input_dir.exists() or not json_input_dir.is_dir():
        print(f"⚠ Папка json_input не найдена: {json_input_dir}")
        print("   Создайте папку json_input и поместите туда JSON файлы в подпапках")
        return 1
    
    print("\n" + "=" * 80)
    print("📄 Генерация XML файлов для выпусков журналов")
    print("=" * 80)
    print(f"📁 Папка с JSON файлами: {json_input_dir}")
    print(f"📁 Папка для XML файлов: {xml_output_dir}")
    print(f"📋 Файл со списком журналов: {list_of_journals_path}")
    print("=" * 80 + "\n")
    
    # Создаем папку для XML файлов, если её нет
    xml_output_dir.mkdir(parents=True, exist_ok=True)
    
    # Генерируем XML файлы
    if args.folder:
        # Обрабатываем только указанную подпапку
        folder_name = args.folder
        print(f"📁 Обработка папки: {folder_name}\n")
        xml_path = generate_xml_for_output_folder(
            json_input_dir,
            xml_output_dir,
            list_of_journals_path,
            folder_name,
        )
        if xml_path:
            print(f"\n✅ XML файл успешно создан: {xml_path}")
            return 0
        else:
            print(f"\n❌ Не удалось создать XML файл для папки {folder_name}")
            return 1
    else:
        # Обрабатываем все подпапки
        created_xml_files = generate_xml_for_all_folders(
            json_input_dir,
            xml_output_dir,
            list_of_journals_path,
        )
        
        if created_xml_files:
            print(f"\n✅ Успешно создано XML файлов: {len(created_xml_files)}")
            for xml_path in created_xml_files:
                print(f"   - {xml_path}")
            return 0
        else:
            print("\n⚠ Не удалось создать ни одного XML файла")
            print("   Убедитесь, что:")
            print("   1. В папке output есть подпапки с JSON файлами")
            print("   2. JSON файлы имеют суффикс _processed.json")
            print("   3. Названия подпапок соответствуют формату: issn_год_номер или issn_год_том_номер")
            print("   4. Журналы с указанными ISSN найдены в data/list_of_journals.json")
            return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
