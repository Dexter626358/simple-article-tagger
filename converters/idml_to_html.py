from __future__ import annotations

import html
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import unquote
import xml.etree.ElementTree as ET


# Предкомпилированные регулярные выражения для производительности
HYPHEN_REGEX = re.compile(
    r"([A-Za-zА-Яа-яЁё])[-‐‑‒–—]\s*(<br/>|\n)\s*([a-zа-яё])"
)
BULLET_REGEX = re.compile(r"•\s*\t\s*")
WHITESPACE_REGEX = re.compile(r"[ \t]+")
MULTI_SPACE_REGEX = re.compile(r" {2,}")
BR_SPACE_REGEX = re.compile(r"\s*<br/>\s*")
# Паттерн для номеров в списке литературы: 1. или 1) или [1]
REF_NUMBER_PATTERN = re.compile(r"(^|\n)\s*(\d{1,3})\s*[).:\]]|\[(\d{1,3})\]")


@dataclass
class IDMLParseResult:
    """Структурированный результат парсинга IDML."""
    html: str = ""
    title: str = ""
    authors: list[str] = field(default_factory=list)
    abstract: str = ""
    abstract_en: str = ""
    keywords: str = ""
    keywords_en: str = ""
    body: str = ""
    references: list[str] = field(default_factory=list)
    footnotes: list[str] = field(default_factory=list)
    tables: list[str] = field(default_factory=list)
    raw_sections: dict[str, list[str]] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Преобразует результат в словарь."""
        return {
            "html": self.html,
            "title": self.title,
            "authors": self.authors,
            "abstract": self.abstract,
            "abstract_en": self.abstract_en,
            "keywords": self.keywords,
            "keywords_en": self.keywords_en,
            "body": self.body,
            "references": self.references,
            "footnotes": self.footnotes,
            "tables": self.tables,
            "raw_sections": self.raw_sections,
        }


def _extract_hyperlinks(zf: zipfile.ZipFile) -> dict[str, str]:
    """
    Извлечь словарь {source_id: url} для гиперссылок из IDML.
    
    IDML хранит гиперссылки в нескольких местах:
    - XML/BackingStory.xml
    - Resources/Hyperlinks.xml
    - Внутри Story файлов как HyperlinkTextSource
    """
    links = {}
    try:
        # Ищем все файлы с гиперссылками
        hyperlink_files = [n for n in zf.namelist() 
                          if ("Hyperlink" in n or "hyperlink" in n.lower()) 
                          and n.endswith(".xml")]
        
        for hf in hyperlink_files:
            try:
                xml_data = zf.read(hf)
                root = ET.fromstring(xml_data)
                
                # Ищем HyperlinkURLDestination для получения URL
                for dest in root.iter():
                    dest_tag = dest.tag.rsplit("}", 1)[-1]
                    if dest_tag == "HyperlinkURLDestination":
                        dest_id = dest.attrib.get("Self", "")
                        dest_url = dest.attrib.get("DestinationURL", "")
                        if dest_id and dest_url:
                            links[dest_id] = dest_url
                
                # Ищем элементы Hyperlink и связываем Source с Destination
                for hyperlink in root.iter():
                    tag = hyperlink.tag.rsplit("}", 1)[-1]
                    if tag == "Hyperlink":
                        source = hyperlink.attrib.get("Source", "")
                        dest_ref = hyperlink.attrib.get("Destination", "")
                        name = hyperlink.attrib.get("Name", "")
                        
                        # Если Destination ссылается на известный URL
                        if dest_ref in links:
                            url = links[dest_ref]
                            if source:
                                links[source] = url
                            if name:
                                links[name] = url
                        
                        # Также проверяем вложенные элементы
                        for child in hyperlink:
                            child_tag = child.tag.rsplit("}", 1)[-1]
                            if child_tag in ("HyperlinkURLDestination", "HyperlinkExternalPageDestination"):
                                url = child.attrib.get("DestinationURL", "")
                                if url:
                                    if source:
                                        links[source] = url
                                    if name:
                                        links[name] = url
                            
            except ET.ParseError:
                continue
                
    except Exception:
        pass
    
    return links


def _extract_story_order(designmap_xml: bytes) -> list[str]:
    """Извлекает порядок Stories из designmap.xml."""
    root = ET.fromstring(designmap_xml)
    story_list = root.attrib.get("StoryList", "")
    return [s.strip() for s in story_list.split() if s.strip()]


def _wrap_with_tag(text: str, tag: str) -> str:
    """Оборачивает текст в HTML тег."""
    if not text:
        return text
    return f"<{tag}>{text}</{tag}>"


def _extract_character_text(csr: ET.Element, footnote_counter: list[int] | None = None) -> tuple[str, list[str]]:
    """
    Извлекает текст из CharacterStyleRange.
    
    Args:
        csr: XML элемент CharacterStyleRange
        footnote_counter: список с одним элементом [n] для подсчёта сносок
        
    Returns:
        Кортеж (текст, список_сносок)
    """
    parts: list[str] = []
    footnotes: list[str] = []
    
    for elem in csr.iter():
        tag = elem.tag.rsplit("}", 1)[-1]
        
        if tag == "Content" and elem.text:
            parts.append(html.escape(elem.text, quote=False))
        elif tag == "Br":
            parts.append("<br/>")
        elif tag == "Footnote":
            # Обрабатываем сноску
            if footnote_counter is not None:
                footnote_counter[0] += 1
                fn_num = footnote_counter[0]
                # Добавляем маркер сноски в текст
                parts.append(f'<sup class="footnote-ref"><a href="#fn{fn_num}" id="fnref{fn_num}">[{fn_num}]</a></sup>')
                # Извлекаем текст сноски
                fn_text = _extract_footnote_text(elem)
                if fn_text:
                    footnotes.append(f'<li id="fn{fn_num}">{fn_text} <a href="#fnref{fn_num}">↩</a></li>')
        elif tag == "TextVariableInstance":
            # Обрабатываем текстовые переменные (автонумерация, даты и т.д.)
            result_text = elem.attrib.get("ResultText", "")
            if result_text:
                parts.append(html.escape(result_text, quote=False))
        elif tag == "PageReference":
            # Обрабатываем ссылки на страницы
            result_text = elem.attrib.get("ResultText", "")
            if result_text:
                parts.append(html.escape(result_text, quote=False))
                
    # Обрабатываем Processing Instructions (<?ACE ...?>)
    # ElementTree не парсит PI напрямую, но мы можем проверить tail
    
    return "".join(parts), footnotes


def _extract_footnote_text(footnote_elem: ET.Element) -> str:
    """Извлекает текст из элемента Footnote."""
    parts: list[str] = []
    for elem in footnote_elem.iter():
        tag = elem.tag.rsplit("}", 1)[-1]
        if tag == "Content" and elem.text:
            parts.append(html.escape(elem.text, quote=False))
        elif tag == "Br":
            parts.append(" ")
    text = " ".join("".join(parts).split())
    return text.strip()


def _find_hyperlink_in_element(elem: ET.Element, hyperlinks: dict[str, str]) -> str | None:
    """
    Ищет гиперссылку в элементе.
    
    Возвращает URL если найден, иначе None.
    """
    # Проверяем атрибуты элемента
    for attr_name, attr_value in elem.attrib.items():
        if "Hyperlink" in attr_name or "hyperlink" in attr_name.lower():
            if attr_value in hyperlinks:
                return hyperlinks[attr_value]
    
    # Проверяем Self атрибут
    self_id = elem.attrib.get("Self", "")
    if self_id in hyperlinks:
        return hyperlinks[self_id]
    
    # Ищем вложенные элементы HyperlinkTextSource
    for child in elem.iter():
        child_tag = child.tag.rsplit("}", 1)[-1]
        if child_tag == "HyperlinkTextSource":
            source_id = child.attrib.get("Self", "")
            name = child.attrib.get("Name", "")
            
            if source_id in hyperlinks:
                return hyperlinks[source_id]
            if name in hyperlinks:
                return hyperlinks[name]
    
    return None


def _render_character_range(
    csr: ET.Element, 
    hyperlinks: dict[str, str] | None = None,
    footnote_counter: list[int] | None = None
) -> tuple[str, list[str]]:
    """
    Рендерит CharacterStyleRange в HTML с форматированием и гиперссылками.
    
    Args:
        csr: XML элемент CharacterStyleRange
        hyperlinks: словарь {source_id: url} с гиперссылками
        footnote_counter: счётчик сносок
        
    Returns:
        Кортеж (html_текст, список_сносок)
    """
    text, footnotes = _extract_character_text(csr, footnote_counter)
    if not text:
        return "", footnotes
    
    applied = (csr.attrib.get("AppliedCharacterStyle") or "").upper()
    font_style = (csr.attrib.get("FontStyle") or "").upper()
    position = (csr.attrib.get("Position") or "").upper()

    is_bold = "BOLD" in applied or "BOLD" in font_style
    is_italic = "ITALIC" in applied or "ITALIC" in font_style or "OBLIQUE" in font_style
    is_sup = "SUPERSCRIPT" in applied or position == "SUPERSCRIPT"
    is_sub = "SUBSCRIPT" in applied or position == "SUBSCRIPT"

    # Применяем форматирование
    if is_sup:
        text = _wrap_with_tag(text, "sup")
    if is_sub:
        text = _wrap_with_tag(text, "sub")
    if is_bold:
        text = _wrap_with_tag(text, "strong")
    if is_italic:
        text = _wrap_with_tag(text, "em")
    
    # Оборачиваем в гиперссылку если есть
    if hyperlinks:
        url = _find_hyperlink_in_element(csr, hyperlinks)
        if url:
            safe_url = html.escape(url, quote=True)
            text = f'<a href="{safe_url}" target="_blank" rel="noopener">{text}</a>'
    
    return text, footnotes


def _normalize_text(value: str) -> str:
    """Нормализует текст: убирает soft hyphen, обрабатывает переносы и пробелы."""
    cleaned = value.replace("\u00ad", "")  # soft hyphen
    cleaned = cleaned.replace("\u00a0", " ")  # non-breaking space
    cleaned = cleaned.replace("\u2028", "<br/>")  # line separator
    cleaned = cleaned.replace("\u2029", "<br/><br/>")  # paragraph separator
    cleaned = cleaned.replace("\t", " ")
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")
    
    # Склеиваем слова с переносами
    cleaned = HYPHEN_REGEX.sub(r"\1\3", cleaned)
    
    # Нормализуем маркеры списков
    cleaned = BULLET_REGEX.sub("• ", cleaned)
    
    # Убираем лишние пробелы и табы
    cleaned = WHITESPACE_REGEX.sub(" ", cleaned)
    
    # Нормализуем переводы строк вокруг <br/>
    cleaned = BR_SPACE_REGEX.sub("<br/>", cleaned)
    
    # Убираем множественные пробелы
    cleaned = MULTI_SPACE_REGEX.sub(" ", cleaned)
    
    return cleaned.strip()


def _parse_table(table_elem: ET.Element, hyperlinks: dict[str, str] | None = None) -> str:
    """
    Парсит таблицу из IDML в HTML.
    
    Args:
        table_elem: XML элемент Table
        hyperlinks: словарь гиперссылок
        
    Returns:
        HTML строка с таблицей
    """
    rows: list[list[str]] = []
    current_row: list[str] = []
    
    # IDML таблицы содержат Cell элементы
    for elem in table_elem.iter():
        tag = elem.tag.rsplit("}", 1)[-1]
        
        if tag == "Cell":
            # Извлекаем текст из ячейки
            cell_parts: list[str] = []
            for child in elem.iter():
                child_tag = child.tag.rsplit("}", 1)[-1]
                if child_tag == "Content" and child.text:
                    cell_parts.append(html.escape(child.text, quote=False))
                elif child_tag == "Br":
                    cell_parts.append("<br/>")
            
            cell_text = _normalize_text("".join(cell_parts))
            
            # Проверяем атрибуты ячейки для определения конца строки
            col_span = int(elem.attrib.get("ColumnSpan", "1"))
            row_span = int(elem.attrib.get("RowSpan", "1"))
            
            # Формируем атрибуты ячейки
            attrs = ""
            if col_span > 1:
                attrs += f' colspan="{col_span}"'
            if row_span > 1:
                attrs += f' rowspan="{row_span}"'
            
            current_row.append(f"<td{attrs}>{cell_text}</td>")
            
        elif tag == "Row" or (current_row and tag == "Table"):
            # Начало новой строки или конец таблицы
            if current_row:
                rows.append(current_row)
                current_row = []
    
    # Добавляем последнюю строку если есть
    if current_row:
        rows.append(current_row)
    
    if not rows:
        return ""
    
    # Собираем HTML таблицу
    html_parts = ['<table class="idml-table">']
    for row in rows:
        html_parts.append("<tr>")
        html_parts.extend(row)
        html_parts.append("</tr>")
    html_parts.append("</table>")
    
    return "\n".join(html_parts)


def _iter_paragraphs(
    story_xml: bytes, 
    hyperlinks: dict[str, str] | None = None,
    footnote_counter: list[int] | None = None
) -> tuple[list[tuple[str, str]], list[str], list[str]]:
    """
    Итерирует по абзацам в Story XML.
    
    Args:
        story_xml: XML содержимое Story файла
        hyperlinks: словарь {source_id: url} с гиперссылками
        footnote_counter: счётчик сносок
        
    Returns:
        Кортеж (список_абзацев, список_сносок, список_таблиц)
        где список_абзацев = [(style, text), ...]
    """
    root = ET.fromstring(story_xml)
    paragraphs: list[tuple[str, str]] = []
    all_footnotes: list[str] = []
    all_tables: list[str] = []
    
    for elem in root.iter():
        tag = elem.tag.rsplit("}", 1)[-1]
        
        # Обрабатываем таблицы
        if tag == "Table":
            table_html = _parse_table(elem, hyperlinks)
            if table_html:
                all_tables.append(table_html)
                # Добавляем placeholder в поток абзацев
                paragraphs.append(("__TABLE__", table_html))
            continue
        
        if tag != "ParagraphStyleRange":
            continue
            
        style = elem.attrib.get("AppliedParagraphStyle", "")
        
        # Проверяем атрибуты нумерации
        numbering_level = elem.attrib.get("NumberingLevel", "")
        
        parts: list[str] = []
        para_footnotes: list[str] = []
        
        for child in elem:
            child_tag = child.tag.rsplit("}", 1)[-1]
            
            if child_tag == "CharacterStyleRange":
                rendered, fn = _render_character_range(child, hyperlinks, footnote_counter)
                if rendered:
                    parts.append(rendered)
                para_footnotes.extend(fn)
            elif child_tag == "Content" and child.text:
                parts.append(html.escape(child.text, quote=False))
            elif child_tag == "Br":
                parts.append("<br/>")
            elif child_tag == "Table":
                # Таблица внутри абзаца
                table_html = _parse_table(child, hyperlinks)
                if table_html:
                    all_tables.append(table_html)
                    parts.append(f'<div class="inline-table">{table_html}</div>')
        
        text = _normalize_text("".join(parts))
        if text:
            paragraphs.append((style, text))
        
        all_footnotes.extend(para_footnotes)
    
    return paragraphs, all_footnotes, all_tables


def _classify_style(style_name: str) -> tuple[str, str | None, str | None, str | None]:
    """
    Классифицирует стиль абзаца.
    
    Args:
        style_name: имя стиля
        
    Returns:
        Кортеж (html_tag, css_class, list_type, section_type)
        section_type: "title", "authors", "abstract", "keywords", "references", "body", None
    """
    normalized = style_name.upper()
    
    # Заголовки
    if any(kw in normalized for kw in ("ЗАГОЛОВОК", "TITLE", "ТИТУЛЬНИК", "HEADING1", "H1")):
        return "h1", "title", None, "title"
    if any(kw in normalized for kw in ("ПОДЗАГОЛОВОК", "HEADING2", "H2", "SUBTITLE")):
        return "h2", "subtitle", None, None
    if any(kw in normalized for kw in ("HEADING3", "H3")):
        return "h3", None, None, None
    
    # Авторы
    if any(kw in normalized for kw in ("АВТОР", "AUTHOR", "AUTHORS")):
        return "p", "authors", None, "authors"
    
    # Аннотация
    if any(kw in normalized for kw in ("АННОТАЦ", "ABSTRACT", "SUMMARY", "РЕЗЮМЕ")):
        # Проверяем язык
        if "EN" in normalized or "ENG" in normalized or "ENGLISH" in normalized:
            return "p", "abstract-en", None, "abstract_en"
        return "p", "abstract", None, "abstract"
    
    # Ключевые слова
    if any(kw in normalized for kw in ("КЛЮЧ", "KEYWORD", "KEYWORDS")):
        if "EN" in normalized or "ENG" in normalized or "ENGLISH" in normalized:
            return "p", "keywords-en", None, "keywords_en"
        return "p", "keywords", None, "keywords"
    
    # Список литературы
    if any(kw in normalized for kw in ("ЛИТЕРАТУР", "REFERENCE", "BIBLIOGRAPHY", "БИБЛИОГРАФ", "ИСТОЧНИК")):
        return "p", "references", None, "references"
    
    # Таблицы и рисунки
    if any(kw in normalized for kw in ("ТАБЛИЦ", "TABLE")):
        return "p", "table-caption", None, None
    if any(kw in normalized for kw in ("РИС", "FIGURE", "FIG", "ИЛЛЮСТРАЦ")):
        return "p", "figure-caption", None, None
    
    # Списки
    if any(kw in normalized for kw in ("СПИСОК", "LIST", "BULLET", "МАРКИР")):
        return "li", "list-item", "ul", None
    if any(kw in normalized for kw in ("НУМЕР", "NUMBER", "ORDERED")):
        return "li", "list-item", "ol", None
    
    # По умолчанию — обычный абзац (часть body)
    return "p", None, None, "body"


def _style_to_tag(style_name: str) -> tuple[str, str | None, str | None]:
    """
    Конвертирует имя стиля в HTML тег и CSS класс.
    Для обратной совместимости.
    """
    tag, css_class, list_type, _ = _classify_style(style_name)
    return tag, css_class, list_type


def _merge_numbered_references(lines: list[str]) -> list[str]:
    """
    Объединяет пронумерованные строки в отдельные записи списка литературы.
    
    Обрабатывает форматы: "1. ", "1) ", "[1] "
    """
    cleaned = "\n".join(line.strip() for line in lines if line.strip())
    if not cleaned:
        return []
    
    # Ищем номера в разных форматах
    matches = list(REF_NUMBER_PATTERN.finditer(cleaned))
    
    if not matches:
        # Нет нумерации — каждая строка это отдельная запись
        return [re.sub(r"\s+", " ", line).strip() for line in lines if line.strip()]
    
    refs: list[str] = []
    for i, match in enumerate(matches):
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(cleaned)
        entry = cleaned[start:end]
        entry = re.sub(r"\s*\n\s*", " ", entry).strip()
        if entry:
            refs.append(entry)
    
    return refs


def _sort_story_files(story_files: list[str]) -> list[str]:
    """Сортирует файлы Stories по номеру."""
    def key(name: str) -> tuple[int, str]:
        stem = Path(name).stem
        if "_" in stem:
            _, suffix = stem.split("_", 1)
            if suffix.isdigit():
                return int(suffix), name
        return 10**9, name
    return sorted(story_files, key=key)


def convert_idml_to_html(idml_path: Path, structured: bool = False) -> str | IDMLParseResult:
    """
    Конвертирует IDML (InDesign) в HTML.
    
    Args:
        idml_path: путь к IDML файлу
        structured: если True, возвращает IDMLParseResult со структурированными данными
        
    Returns:
        HTML строка или IDMLParseResult
    """
    if not idml_path.exists():
        raise FileNotFoundError(f"IDML file not found: {idml_path}")
    if idml_path.suffix.lower() != ".idml":
        raise ValueError("convert_idml_to_html expects a .idml file")

    result = IDMLParseResult()
    html_parts: list[str] = ['<div class="idml-content">']
    footnote_counter = [0]  # Используем список для мутабельности
    
    # Секции для структурированного вывода
    sections: dict[str, list[str]] = {
        "title": [],
        "authors": [],
        "abstract": [],
        "abstract_en": [],
        "keywords": [],
        "keywords_en": [],
        "references": [],
        "body": [],
    }
    
    with zipfile.ZipFile(idml_path) as zf:
        # Извлекаем гиперссылки
        hyperlinks = _extract_hyperlinks(zf)
        
        try:
            designmap = zf.read("designmap.xml")
            story_ids = _extract_story_order(designmap)
        except KeyError:
            story_ids = []

        story_files = (
            [f"Stories/Story_{sid}.xml" for sid in story_ids]
            if story_ids
            else _sort_story_files([n for n in zf.namelist() if n.startswith("Stories/")])
        )

        open_list: str | None = None
        ref_lines: list[str] = []
        all_footnotes: list[str] = []
        all_tables: list[str] = []

        def flush_references() -> None:
            nonlocal ref_lines
            if not ref_lines:
                return
            refs = _merge_numbered_references(ref_lines)
            if refs:
                html_parts.append('<ol class="references">')
                for ref in refs:
                    html_parts.append(f"<li>{ref}</li>")
                html_parts.append("</ol>")
                result.references.extend(refs)
            ref_lines = []

        for story_file in story_files:
            if story_file not in zf.namelist():
                continue
            
            story_xml = zf.read(story_file)
            paragraphs, footnotes, tables = _iter_paragraphs(story_xml, hyperlinks, footnote_counter)
            
            all_footnotes.extend(footnotes)
            all_tables.extend(tables)
            
            for style_raw, text in paragraphs:
                # Обрабатываем таблицы как есть
                if style_raw == "__TABLE__":
                    flush_references()
                    if open_list:
                        html_parts.append(f"</{open_list}>")
                        open_list = None
                    html_parts.append(text)
                    continue
                
                style_name = ""
                if style_raw:
                    style_name = style_raw.split("/")[-1]
                    style_name = unquote(style_name)
                
                tag, css_class, list_type, section_type = _classify_style(style_name)
                class_attr = f' class="{css_class}"' if css_class else ""

                # Собираем секции для структурированного вывода
                if section_type and section_type in sections:
                    sections[section_type].append(text)

                # Обрабатываем список литературы особым образом
                if css_class == "references":
                    ref_lines.append(text)
                    continue

                flush_references()

                # Обрабатываем списки
                if list_type:
                    if open_list != list_type:
                        if open_list:
                            html_parts.append(f"</{open_list}>")
                        html_parts.append(f"<{list_type}>")
                        open_list = list_type
                    html_parts.append(f"<li{class_attr}>{text}</li>")
                    continue

                if open_list:
                    html_parts.append(f"</{open_list}>")
                    open_list = None

                html_parts.append(f"<{tag}{class_attr}>{text}</{tag}>")

        flush_references()

        if open_list:
            html_parts.append(f"</{open_list}>")
        
        # Добавляем сноски в конец
        if all_footnotes:
            html_parts.append('<section class="footnotes"><hr/><ol>')
            html_parts.extend(all_footnotes)
            html_parts.append('</ol></section>')
            result.footnotes = [fn for fn in all_footnotes]

    html_parts.append("</div>")
    result.html = "\n".join(html_parts)
    
    # Заполняем структурированный результат
    if sections["title"]:
        result.title = " ".join(sections["title"])
    if sections["authors"]:
        result.authors = sections["authors"]
    if sections["abstract"]:
        result.abstract = " ".join(sections["abstract"])
    if sections["abstract_en"]:
        result.abstract_en = " ".join(sections["abstract_en"])
    if sections["keywords"]:
        result.keywords = ", ".join(sections["keywords"])
    if sections["keywords_en"]:
        result.keywords_en = ", ".join(sections["keywords_en"])
    if sections["body"]:
        result.body = "\n".join(f"<p>{p}</p>" for p in sections["body"])
    
    result.tables = all_tables
    result.raw_sections = sections
    
    if structured:
        return result
    
    return result.html
