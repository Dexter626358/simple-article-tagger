import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
from typing import Dict, Any, Optional, List, Tuple
import journal_config
import logging
import os
import json
import glob
import re
from pathlib import Path


def format_initials(initials: str) -> str:
    """
    Форматирует инициалы, добавляя пробелы между ними
    
    Args:
        initials: Строка с инициалами (например, "И.С." или "I.S.")
        
    Returns:
        str: Отформатированные инициалы с пробелами (например, "И. С." или "I. S.")
    """
    if not initials:
        return initials
    
    # Паттерн для поиска инициалов: буква + точка
    pattern = r'([А-ЯЁA-Z])\.'
    
    # Заменяем каждое вхождение на букву + точка + пробел
    formatted = re.sub(pattern, r'\1. ', initials)
    
    # Убираем лишний пробел в конце, если он есть
    return formatted.rstrip()


def prettify_xml(element: ET.Element) -> str:
    """
    Возвращает красиво отформатированную XML строку с отступами
    
    Args:
        element: XML элемент для форматирования
        
    Returns:
        str: Отформатированная XML строка
    
    Raises:
        ValueError: Если элемент не может быть преобразован в XML
    """
    try:
        rough_string = ET.tostring(element, encoding="utf-8")
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")
    except Exception as e:
        raise ValueError(f"Ошибка при форматировании XML: {e}")


def validate_config(config: Dict[str, Any]) -> None:
    """
    Валидация конфигурации журнала
    
    Args:
        config: Словарь с конфигурацией журнала
        
    Raises:
        ValueError: Если конфигурация содержит ошибки
    """
    required_fields = ["titleid", "journal_titles", "issue"]
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Отсутствует обязательное поле: {field}")
    
    if not config["journal_titles"]:
        raise ValueError("Отсутствуют названия журнала")
    
    issue_config = config["issue"]
    
    # Проверяем обязательные поля
    required_issue_fields = ["year", "pages"]
    for field in required_issue_fields:
        if field not in issue_config or not issue_config[field]:
            raise ValueError(f"Отсутствует обязательное поле выпуска: {field}")
    
    # Проверяем наличие либо volume, либо number (согласно схеме XML)
    # Оба поля опциональны, но хотя бы одно должно быть заполнено
    volume = issue_config.get("volume", "")
    number = issue_config.get("number", "")
    
    # Проверяем, что хотя бы одно поле заполнено и не пустое
    volume_filled = volume and str(volume).strip()
    number_filled = number and str(number).strip()
    
    if not volume_filled and not number_filled:
        raise ValueError("Отсутствует обязательное поле выпуска: необходимо указать либо volume, либо number")


def create_xml_issue(config: Optional[Dict[str, Any]] = None) -> ET.ElementTree:
    """
    Создает XML структуру для выпуска журнала
    
    Args:
        config: Конфигурация журнала (по умолчанию используется автоматическая конфигурация)
        
    Returns:
        ET.ElementTree: XML дерево с данными журнала
        
    Raises:
        ValueError: Если конфигурация содержит ошибки
    """
    if config is None:
        config = journal_config.get_journal_config()
    
    # Валидация конфигурации
    validate_config(config)
    
    try:
        root = ET.Element("journal")

        # titleid (обязательное поле)
        titleid_elem = ET.SubElement(root, "titleid")
        titleid_elem.text = str(config["titleid"])

        # issn и eissn (опциональные)
        if config.get("issn"):
            issn_elem = ET.SubElement(root, "issn")
            issn_elem.text = str(config["issn"])
        
        if config.get("eissn"):
            eissn_elem = ET.SubElement(root, "eissn")
            eissn_elem.text = str(config["eissn"])

        # journalInfo с вложенным title
        journal_titles = config["journal_titles"]
        journal_info = ET.SubElement(root, "journalInfo")
        
        if journal_titles.get("ru"):
            journal_info.set("lang", "RUS")
            title_elem = ET.SubElement(journal_info, "title")
            title_elem.text = journal_titles["ru"]
        elif journal_titles.get("en"):
            journal_info.set("lang", "ENG")
            title_elem = ET.SubElement(journal_info, "title")
            title_elem.text = journal_titles["en"]
        else:
            raise ValueError("Не найдено ни русского, ни английского названия журнала")

        # issue и вложенные элементы
        issue = ET.SubElement(root, "issue")
        issue_config = config["issue"]

        volume_elem = ET.SubElement(issue, "volume")
        volume_elem.text = issue_config.get("volume", "")

        number_elem = ET.SubElement(issue, "number")
        number_elem.text = str(issue_config["number"])

        dateUni_elem = ET.SubElement(issue, "dateUni")
        dateUni_elem.text = str(issue_config["year"])

        pages_elem = ET.SubElement(issue, "pages")
        pages_elem.text = str(issue_config["pages"])

        # articles (пустой контейнер для статей)
        ET.SubElement(issue, "articles")

        return ET.ElementTree(root)
    
    except Exception as e:
        raise ValueError(f"Ошибка при создании XML структуры: {e}")


def save_xml_to_file(tree: ET.ElementTree, 
                     filename: str = "journal.xml", 
                     output_dir: Optional[str] = None) -> Path:
    """
    Сохраняет XML дерево в файл с красивым форматированием
    
    Args:
        tree: XML дерево для сохранения
        filename: Имя файла для сохранения
        output_dir: Директория для сохранения (по умолчанию текущая)
        
    Returns:
        Path: Путь к сохраненному файлу
        
    Raises:
        IOError: Если не удается записать файл
    """
    try:
        if output_dir:
            output_path = Path(output_dir) / filename
            output_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            output_path = Path(filename)
        
        formatted_xml = prettify_xml(tree.getroot())
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(formatted_xml)
        
        return output_path
    
    except Exception as e:
        raise IOError(f"Ошибка при сохранении файла {filename}: {e}")


def get_output_directories() -> List[str]:
    """
    Получает список директорий в папке json_input
    
    Returns:
        List[str]: Список имен директорий
    """
    json_input_path = Path("json_input")
    if not json_input_path.exists():
        return []
    
    directories = [
        d.name for d in json_input_path.iterdir() 
        if d.is_dir()
    ]
    return directories


def detect_issue_from_directory(directory_name: str) -> Optional[str]:
    """
    Определяет параметры выпуска из имени директории
    
    Args:
        directory_name: Имя директории (например, "2500-0047_2024_1")
        
    Returns:
        str: Имя директории или None если не найдена
    """
    outputs_path = Path("outputs") / directory_name
    if outputs_path.exists() and outputs_path.is_dir():
        return directory_name
    return None


def create_xml_with_articles(config: Optional[Dict[str, Any]] = None, 
                           output_directory: Optional[str] = None) -> ET.ElementTree:
    """
    Создает XML структуру журнала с интеграцией статей из JSON файлов
    
    Args:
        config: Конфигурация журнала
        output_directory: Директория с JSON файлами статей
        
    Returns:
        ET.ElementTree: XML дерево с данными журнала и статьями
    """
    # Создаем базовую структуру
    tree = create_xml_issue(config)
    root = tree.getroot()
    
    # Находим элемент articles
    issue_elem = root.find("issue")
    articles_elem = issue_elem.find("articles")
    
    if output_directory:
        # Загружаем и добавляем статьи из JSON файлов
        # JSON файлы находятся в папке json_input с той же структурой подпапок
        articles_path = Path("json_input") / output_directory
        if articles_path.exists():
            json_files = list(articles_path.glob("*.json"))
            logging.info(f"Найдено {len(json_files)} JSON файлов со статьями в {articles_path}")
            
            for json_file in sorted(json_files):
                try:
                    article_elem = json_to_article_xml(json_file)
                    # Проверяем, есть ли авторы в статье
                    authors = article_elem.find("authors")
                    if authors is not None:
                        author_count = len(authors.findall("author"))
                        if author_count == 0:
                            logging.warning(f"Статья из {json_file.name} не содержит авторов!")
                    articles_elem.append(article_elem)
                    logging.info(f"Добавлена статья из {json_file.name}")
                except Exception as e:
                    logging.warning(f"Ошибка при обработке {json_file.name}: {e}")
        else:
            logging.warning(f"Папка с JSON файлами не найдена: {articles_path}")
        
        # Добавляем ссылку на обложку выпуска, если файл существует
        issue_output_path = Path("outputs") / output_directory
        cover_jpeg = issue_output_path / "cover.jpeg"
        cover_jpg = issue_output_path / "cover.jpg"
        
        cover_file = None
        if cover_jpeg.exists():
            cover_file = cover_jpeg.name
        elif cover_jpg.exists():
            cover_file = cover_jpg.name
        
        if cover_file:
            # Проверяем, существует ли уже элемент files
            files_elem = issue_elem.find("files")
            if files_elem is None:
                files_elem = ET.SubElement(issue_elem, "files")
            
            # Добавляем элемент file с атрибутом desc="cover"
            file_elem = ET.SubElement(files_elem, "file")
            file_elem.set("desc", "cover")
            file_elem.text = cover_file
            logging.info(f"Добавлена ссылка на обложку: {cover_file}")
    
    return tree


def json_to_article_xml(json_file: Path) -> ET.Element:
    """
    Преобразует JSON файл статьи в XML элемент
    
    Args:
        json_file: Путь к JSON файлу
        
    Returns:
        ET.Element: XML элемент статьи
    """
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Проверяем, что data является словарем
    if not isinstance(data, dict):
        raise ValueError(f"JSON файл {json_file.name} содержит данные неверного типа: {type(data)}")
    
    article = ET.Element("article")

    # pages
    ET.SubElement(article, "pages").text = data.get("pages", "")
    
    # artType
    ET.SubElement(article, "artType").text = data.get("artType", "")
    
    # langPubl (язык публикации статьи согласно схеме РИНЦ)
    # Значение должно быть в трехбуквенном коде ISO 639: RUS или ENG
    publ_lang = data.get("PublLang", "")
    if publ_lang:
        ET.SubElement(article, "langPubl").text = publ_lang

    # authors
    authors_elem = ET.SubElement(article, "authors")
    for author in data.get("authors", []):
        # Проверяем, что author является словарем
        if not isinstance(author, dict):
            logging.warning(f"Пропускаем автора неверного типа: {type(author)}")
            continue
            
        # Создаем элемент автора с атрибутом num
        author_elem = ET.SubElement(authors_elem, "author", num=str(author.get("num", "")))
        
        # Добавляем элемент correspondent согласно схеме
        if author.get("correspondence") is True:
            ET.SubElement(author_elem, "correspondent").text = "1"  # Автор, отвечающий за переписку
        elif author.get("correspondence") is False:
            ET.SubElement(author_elem, "correspondent").text = "0"  # Автор
        # Если correspondence не указан, элемент correspondent не добавляем
        
        # authorCodes - создаем только если есть хотя бы один непустой код
        ac_rus = author.get("individInfo", {}).get("RUS", {}).get("authorCodes", {})
        ac_eng = author.get("individInfo", {}).get("ENG", {}).get("authorCodes", {})
        
        # Проверяем, есть ли хотя бы один непустой код
        has_codes = False
        codes_to_add = {}
        
        if ac_rus:
            for code_type in ["spin", "orcid", "scopusid", "researcherid"]:
                code_value = ac_rus.get(code_type)
                if code_value and str(code_value).strip():
                    has_codes = True
                    codes_to_add[code_type] = str(code_value).strip()
        
        if ac_eng and not has_codes:
            for code_type in ["spin", "orcid", "scopusid", "researcherid"]:
                code_value = ac_eng.get(code_type)
                if code_value and str(code_value).strip():
                    has_codes = True
                    codes_to_add[code_type] = str(code_value).strip()
        
        # Создаем authorCodes только если есть хотя бы один непустой код
        if has_codes:
            authorCodes = ET.SubElement(author_elem, "authorCodes")
            for code_type, code_value in codes_to_add.items():
                ET.SubElement(authorCodes, code_type).text = code_value

        # individInfo для RUS и ENG
        for lang in ["RUS", "ENG"]:
            info = author.get("individInfo", {}).get(lang, {})
            if info:
                ii = ET.SubElement(author_elem, "individInfo", lang=lang)
                for tag in ["surname", "initials", "orgName", "address", "email", "otherInfo"]:
                    if tag in info and info[tag]:
                        value = str(info[tag])
                        # Форматируем инициалы, добавляя пробелы
                        # if tag == "initials":
                        #     value = format_initials(value)
                        ET.SubElement(ii, tag).text = value

    # artTitles
    artTitles_elem = ET.SubElement(article, "artTitles")
    for lang in ["RUS", "ENG"]:
        if lang in data.get("artTitles", {}):
            ET.SubElement(artTitles_elem, "artTitle", lang=lang).text = data["artTitles"][lang]

    # abstracts
    abstracts_elem = ET.SubElement(article, "abstracts")
    for lang in ["RUS", "ENG"]:
        if lang in data.get("abstracts", {}):
            ET.SubElement(abstracts_elem, "abstract", lang=lang).text = data["abstracts"][lang]

    # codes
    codes_elem = ET.SubElement(article, "codes")
    for code in ["udk", "bbk", "doi", "edn"]:
        if code in data.get("codes", {}) and data["codes"][code]:
            ET.SubElement(codes_elem, code).text = str(data["codes"][code])

    # keywords
    keywords_elem = ET.SubElement(article, "keywords")
    for lang in ["RUS", "ENG"]:
        group = data.get("keywords", {}).get(lang, [])
        if group:
            group_elem = ET.SubElement(keywords_elem, "kwdGroup", lang=lang)
            for kw in group:
                ET.SubElement(group_elem, "keyword").text = str(kw)

    # references
    references_elem = ET.SubElement(article, "references")
    references_data = data.get("references", [])
    
    # Проверяем, является ли references словарем с языковыми ключами
    if isinstance(references_data, dict):
        # Обрабатываем структуру {"RUS": [...], "ENG": [...]}
        for lang in ["RUS", "ENG"]:
            refs_list = references_data.get(lang, [])
            for ref in refs_list:
                reference_elem = ET.SubElement(references_elem, "reference")
                refInfo_elem = ET.SubElement(reference_elem, "refInfo", lang=lang)
                ET.SubElement(refInfo_elem, "text").text = str(ref)
    else:
        # Обрабатываем старую структуру - простой список
        for ref in references_data:
            reference_elem = ET.SubElement(references_elem, "reference")
            
            # Проверяем, что ref является словарем
            if isinstance(ref, dict):
                refInfo = ref.get("refInfo", {})
                refInfo_elem = ET.SubElement(reference_elem, "refInfo", lang=refInfo.get("lang", "ANY"))
                ET.SubElement(refInfo_elem, "text").text = refInfo.get("text", "")
            else:
                # Если ref - это строка, создаем простую ссылку
                refInfo_elem = ET.SubElement(reference_elem, "refInfo", lang="ANY")
                ET.SubElement(refInfo_elem, "text").text = str(ref)

    # files
    # Пробуем получить имя файла из разных полей JSON
    file_name = data.get("file") or data.get("pdf_url") or data.get("file_metadata", {}).get("name")
    if file_name:
        # Извлекаем только имя файла, если это полный путь
        if "/" in str(file_name) or "\\" in str(file_name):
            file_name = Path(file_name).name
        files_elem = ET.SubElement(article, "files")
        ET.SubElement(files_elem, "file", desc="fullText").text = str(file_name).strip()

    # dates
    dates_elem = ET.SubElement(article, "dates")
    for date in ["dateReceived", "dateAccepted", "datePublication"]:
        if date in data.get("dates", {}):
            ET.SubElement(dates_elem, date).text = data["dates"][date]

    # artFunding
    art_funding_elem = ET.SubElement(article, "artFunding")
    for lang in ["RUS", "ENG"]:
        if lang in data.get("fundings", {}):
            ET.SubElement(art_funding_elem, "funding", lang=lang).text = data["fundings"][lang]


    return article


def generate_xml_for_issue(issue_name: Optional[str] = None) -> int:
    """
    Генерирует XML файл для конкретного выпуска или первого найденного
    
    Args:
        issue_name: Имя выпуска (папки в outputs). Если None, используется первый найденный
    
    Returns:
        int: Код возврата (0 - успех, 1 - ошибка)
    """
    try:
        # Настройка логирования
        logging.basicConfig(level=logging.INFO, 
                          format='%(asctime)s - %(levelname)s - %(message)s')
        
        # Определяем директорию для обработки
        if issue_name:
            # Проверяем, что указанная директория существует
            issue_path = Path("outputs") / issue_name
            if not issue_path.exists() or not issue_path.is_dir():
                print(f"❌ Директория выпуска не найдена: {issue_name}")
                return 1
            selected_dir = issue_name
            logging.info(f"Используется указанная директория выпуска: {selected_dir}")
        else:
            # Ищем доступные директории с выпусками
            output_dirs = get_output_directories()
            
            if not output_dirs:
                logging.info("Создание простого XML без статей...")
                tree = create_xml_issue()
                output_path = save_xml_to_file(tree, "journal.xml")
                return 0
            
            # Используем первую найденную директорию
            selected_dir = output_dirs[0]
            logging.info(f"Найдена директория с выпуском: {selected_dir}")
        
        # Загружаем конфигурацию журнала для конкретного выпуска
        print("🔧 Инициализация конфигурации журнала...")
        print(f"📁 Имя папки выпуска: {selected_dir}")
        
        # Извлекаем информацию из названия папки
        folder_name = Path(selected_dir).name
        issue_info = None
        try:
            from services.xml_generator_helper import parse_folder_name
            issue_info = parse_folder_name(folder_name)
            if issue_info:
                print(f"✅ Парсинг имени папки успешен:")
                print(f"   ISSN: {issue_info.get('issn', 'НЕ НАЙДЕН')}")
                print(f"   Год: {issue_info.get('year', 'НЕ НАЙДЕН')}")
                print(f"   Том: {issue_info.get('volume', 'НЕ НАЙДЕН')}")
                print(f"   Номер: {issue_info.get('number', 'НЕ НАЙДЕН')}")
            else:
                print(f"⚠️ Не удалось распарсить имя папки: {folder_name}")
                print("💡 Ожидаемый формат: ISSN_ГОД_НОМЕР или ISSN_ГОД_ТОМ_НОМЕР")
                print("   Пример: 2687-0185_2025_3 или 2687-0185_2025_10_3")
        except Exception as e:
            print(f"⚠️ Ошибка при парсинге имени папки: {e}")
        
        try:
            # Загружаем конфигурацию по умолчанию
            config = journal_config.load_config()
            
            # Если удалось распарсить папку, обновляем конфигурацию данными из папки
            if issue_info:
                # Обновляем год из названия папки
                if issue_info.get('year'):
                    if 'issue' not in config:
                        config['issue'] = {}
                    config['issue']['year'] = issue_info['year']
                
                # Обновляем номер из названия папки
                if issue_info.get('number'):
                    if 'issue' not in config:
                        config['issue'] = {}
                    config['issue']['number'] = issue_info['number']
                
                # Обновляем том из названия папки (если есть)
                if issue_info.get('volume'):
                    if 'issue' not in config:
                        config['issue'] = {}
                    config['issue']['volume'] = issue_info['volume']
                elif 'issue' in config and 'volume' not in config['issue']:
                    # Если тома нет, добавляем пустую строку
                    config['issue']['volume'] = ""
        except Exception as e:
            print(f"⚠️ Ошибка при создании конфигурации для {selected_dir}: {e}")
            print("💡 Используется конфигурация по умолчанию")
            config = journal_config.load_config()
        
        # Отладочный вывод конфигурации
        print(f"\n📋 Загруженная конфигурация:")
        print(f"   ISSN: {config.get('issn', 'НЕ ЗАДАН')}")
        print(f"   Журнал: {config.get('journal_titles', {}).get('ru', 'НЕ ЗАДАН')}")
        print(f"   Год: {config.get('issue', {}).get('year', 'НЕ ЗАДАН')}")
        print(f"   Том: {config.get('issue', {}).get('volume', 'НЕТ')}")
        print(f"   Номер: {config.get('issue', {}).get('number', 'НЕ ЗАДАН')}")
        print(f"   Страницы: {config.get('issue', {}).get('pages', 'НЕ ЗАДАН')}")
        print()
        
        # Создаем XML с интеграцией статей
        logging.info("Создание XML структуры журнала с статьями...")
        tree = create_xml_with_articles(config=config, output_directory=selected_dir)
        
        # Сохраняем XML в папку xml_output с той же структурой подпапок
        filename = f"{selected_dir}.xml"
        xml_output_dir = Path("xml_output") / selected_dir
        xml_output_dir.mkdir(parents=True, exist_ok=True)
        output_path = save_xml_to_file(tree, filename, str(xml_output_dir))
        
        logging.info(f"XML файл успешно создан: {output_path}")
        print("XML файл успешно создан с красивым форматированием!")
        print(f"Файл сохранен: {output_path}")
        
        # Показываем статистику
        root = tree.getroot()
        articles = root.find(".//articles")
        if articles is not None:
            article_count = len(list(articles.findall("article")))
            print(f"Добавлено статей: {article_count}")
        
        # Генерируем HTML отчет
        print("\n📊 Создание HTML отчета...")
        try:
            from report_generator import generate_html_report
            html_file = generate_html_report(output_path)
            print(f"✅ HTML отчет создан: {html_file}")
        except Exception as e:
            print(f"⚠️ Ошибка при создании HTML отчета: {e}")
            logging.warning(f"Не удалось создать HTML отчет: {e}")
        
        # Валидация XML файла
        print("\n🔍 Валидация XML файла...")
        is_valid, errors = xml_validator(output_path)
        
        if is_valid:
            print("✅ XML файл прошел валидацию успешно!")
            print("Все проверки пройдены, структура корректна.")
        else:
            print("❌ XML файл содержит ошибки:")
            print("-" * 40)
            for i, error in enumerate(errors, 1):
                print(f"{i}. {error}")
            print("-" * 40)
            print(f"Всего найдено ошибок: {len(errors)}")
            print("⚠️ Рекомендуется исправить ошибки перед использованием файла.")
        
        # Показываем примерное содержимое
        formatted_xml = prettify_xml(tree.getroot())
        print("\nПример содержимого:")
        print("-" * 50)
        
        # Выводим первые несколько строк для демонстрации
        lines = formatted_xml.split('\n')[:15]
        for line in lines:
            if line.strip():  # пропускаем пустые строки
                print(line)
        if len(formatted_xml.split('\n')) > 15:
            print("...")
            
        return 0
            
    except Exception as e:
        logging.error(f"Ошибка при создании XML файла: {e}")
        print(f"Ошибка: {e}")
        return 1


def main(issue_name: Optional[str] = None):
    """
    Основная функция для создания XML файла журнала с автоматической обработкой статей
    
    Args:
        issue_name: Имя выпуска (папки в outputs). Если None, используется первый найденный
    """
    return generate_xml_for_issue(issue_name)

def xml_validator(xml_file: Path, schema_file: Optional[Path] = None) -> Tuple[bool, List[str]]:
    """
    Валидирует XML файл на соответствие схеме
    
    Args:
        xml_file: Путь к XML файлу
        schema_file: Путь к XSD схеме (по умолчанию data/xml_schema.xsd)
        
    Returns:
        Tuple[bool, List[str]]: (валиден ли файл, список ошибок)
    """
    if schema_file is None:
        project_root = Path(__file__).resolve().parents[1]
        schema_file = project_root / "data" / "xml_schema.xsd"
    
    errors = []
    
    try:
        # Проверяем существование файлов
        if not xml_file.exists():
            errors.append(f"XML файл не найден: {xml_file}")
            return False, errors
        
        if not schema_file.exists():
            errors.append(f"XSD схема не найдена: {schema_file}")
            return False, errors
        
        # Парсим XML файл
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
        except ET.ParseError as e:
            errors.append(f"Ошибка парсинга XML: {e}")
            return False, errors
        
        # Проверяем базовую структуру
        if root.tag != "journal":
            errors.append("Корневой элемент должен быть 'journal'")
            return False, errors
        
        # Проверяем обязательные элементы
        required_elements = ["titleid", "journalInfo", "issue"]
        for elem_name in required_elements:
            if root.find(elem_name) is None:
                errors.append(f"Отсутствует обязательный элемент: {elem_name}")
        
        # Проверяем journalInfo
        journal_info = root.find("journalInfo")
        if journal_info is not None:
            if not journal_info.get("lang"):
                errors.append("Элемент journalInfo должен иметь атрибут 'lang'")
            
            title = journal_info.find("title")
            if title is None:
                errors.append("journalInfo должен содержать элемент 'title'")
        
        # Проверяем issue
        issue = root.find("issue")
        if issue is not None:
            issue_required = ["volume", "number", "dateUni", "pages", "articles"]
            for elem_name in issue_required:
                if issue.find(elem_name) is None:
                    errors.append(f"issue должен содержать элемент: {elem_name}")
        
        # Проверяем статьи
        articles = root.find(".//articles")
        if articles is not None:
            for article in articles.findall("article"):
                article_errors = validate_article(article)
                errors.extend(article_errors)
        
        # Если есть ошибки, возвращаем False
        if errors:
            return False, errors
        
        # Если все проверки пройдены, файл валиден
        return True, []
        
    except Exception as e:
        errors.append(f"Неожиданная ошибка при валидации: {e}")
        return False, errors


def validate_article(article: ET.Element) -> List[str]:
    """
    Валидирует отдельную статью
    
    Args:
        article: XML элемент статьи
        
    Returns:
        List[str]: Список ошибок валидации
    """
    errors = []
    
    # Проверяем обязательные элементы статьи
    article_required = ["pages", "artType", "authors", "artTitles"]
    for elem_name in article_required:
        if article.find(elem_name) is None:
            errors.append(f"Статья должна содержать элемент: {elem_name}")
    
    # Проверяем langPubl (если присутствует, должно быть валидным значением)
    lang_publ = article.find("langPubl")
    if lang_publ is not None and lang_publ.text:
        valid_langs = ["RUS", "ENG"]
        if lang_publ.text not in valid_langs:
            errors.append(f"langPubl содержит недопустимое значение: {lang_publ.text}. Допустимые значения: {', '.join(valid_langs)}")
    
    # Проверяем авторов
    authors = article.find("authors")
    if authors is not None:
        author_list = authors.findall("author")
        if not author_list:
            errors.append("Статья должна содержать хотя бы одного автора")
        
        for author in author_list:
            author_errors = validate_author(author)
            errors.extend(author_errors)
    
    # Проверяем названия статьи
    art_titles = article.find("artTitles")
    if art_titles is not None:
        title_list = art_titles.findall("artTitle")
        if not title_list:
            errors.append("artTitles должен содержать хотя бы одно название")
        
        for title in title_list:
            if not title.get("lang"):
                errors.append("artTitle должен иметь атрибут 'lang'")
    
    return errors


def validate_author(author: ET.Element) -> List[str]:
    """
    Валидирует автора
    
    Args:
        author: XML элемент автора
        
    Returns:
        List[str]: Список ошибок валидации
    """
    errors = []
    
    # Проверяем individInfo
    individ_info_list = author.findall("individInfo")
    if not individ_info_list:
        errors.append("Автор должен содержать хотя бы один элемент individInfo")
    
    for individ_info in individ_info_list:
        if not individ_info.get("lang"):
            errors.append("individInfo должен иметь атрибут 'lang'")
    
    return errors

if __name__ == "__main__":
    import sys
    # Поддержка аргументов командной строки
    issue_name = None
    if len(sys.argv) > 1:
        issue_name = sys.argv[1]
        print(f"📁 Генерация XML для выпуска: {issue_name}")
    exit(main(issue_name))

