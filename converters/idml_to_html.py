from __future__ import annotations

import html
import re
import zipfile
from pathlib import Path
from urllib.parse import unquote
import xml.etree.ElementTree as ET


def _extract_story_order(designmap_xml: bytes) -> list[str]:
    root = ET.fromstring(designmap_xml)
    story_list = root.attrib.get("StoryList", "")
    return [s.strip() for s in story_list.split() if s.strip()]


def _wrap_with_tag(text: str, tag: str) -> str:
    if not text:
        return text
    return f"<{tag}>{text}</{tag}>"


def _extract_character_text(csr: ET.Element) -> str:
    parts: list[str] = []
    for elem in csr.iter():
        tag = elem.tag.rsplit("}", 1)[-1]
        if tag == "Content" and elem.text:
            parts.append(html.escape(elem.text, quote=False))
        elif tag == "Br":
            parts.append("<br/>")
    return "".join(parts)


def _render_character_range(csr: ET.Element) -> str:
    text = _extract_character_text(csr)
    if not text:
        return ""
    applied = (csr.attrib.get("AppliedCharacterStyle") or "").upper()
    font_style = (csr.attrib.get("FontStyle") or "").upper()
    position = (csr.attrib.get("Position") or "").upper()

    is_bold = "BOLD" in applied or "BOLD" in font_style
    is_italic = "ITALIC" in applied or "ITALIC" in font_style or "OBLIQUE" in font_style
    is_sup = "SUPERSCRIPT" in applied or position == "SUPERSCRIPT"
    is_sub = "SUBSCRIPT" in applied or position == "SUBSCRIPT"

    if is_sup:
        text = _wrap_with_tag(text, "sup")
    if is_sub:
        text = _wrap_with_tag(text, "sub")
    if is_bold:
        text = _wrap_with_tag(text, "strong")
    if is_italic:
        text = _wrap_with_tag(text, "em")
    return text


def _normalize_text(value: str) -> str:
    cleaned = value.replace("\u00ad", "")
    cleaned = cleaned.replace("\u00a0", " ")
    cleaned = cleaned.replace("\t", " ")
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = re.sub(
        r"([A-Za-zА-Яа-яЁё])[-‐‑‒–—]\s*(<br/>|\n)\s*([a-zа-яё])",
        r"\1\3",
        cleaned,
    )
    cleaned = re.sub(r"•\s*\t\s*", "• ", cleaned)
    cleaned = re.sub(r"\t+", " ", cleaned)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\s*<br/>\s*", "<br/>", cleaned)
    cleaned = re.sub(r" {2,}", " ", cleaned)
    return cleaned.strip()


def _iter_paragraphs(story_xml: bytes) -> list[tuple[str, str]]:
    root = ET.fromstring(story_xml)
    paragraphs: list[tuple[str, str]] = []
    for psr in root.iter():
        if not psr.tag.endswith("ParagraphStyleRange"):
            continue
        style = psr.attrib.get("AppliedParagraphStyle", "")
        parts: list[str] = []
        for child in psr:
            tag = child.tag.rsplit("}", 1)[-1]
            if tag == "CharacterStyleRange":
                rendered = _render_character_range(child)
                if rendered:
                    parts.append(rendered)
            elif tag == "Content" and child.text:
                parts.append(html.escape(child.text, quote=False))
            elif tag == "Br":
                parts.append("<br/>")
        text = _normalize_text("".join(parts))
        if text:
            paragraphs.append((style, text))
    return paragraphs


def _style_to_tag(style_name: str) -> tuple[str, str | None, str | None]:
    normalized = style_name.upper()
    if "ЗАГОЛОВОК" in normalized or "TITLE" in normalized or "ТИТУЛЬНИК СТАТЬИ" in normalized:
        return "h1", None, None
    if "ПОДЗАГОЛОВОК" in normalized or "HEADING" in normalized:
        return "h2", None, None
    if "АННОТАЦ" in normalized or "ABSTRACT" in normalized:
        return "p", "abstract", None
    if "КЛЮЧ" in normalized or "KEYWORD" in normalized:
        return "p", "keywords", None
    if "ЛИТЕРАТУР" in normalized or "REFERENCES" in normalized:
        return "p", "references", None
    if "АВТОР" in normalized or "AUTHOR" in normalized:
        return "p", "authors", None
    if "ТАБЛИЦ" in normalized or "TABLE" in normalized:
        return "p", "table-caption", None
    if "РИС" in normalized or "FIGURE" in normalized:
        return "p", "figure-caption", None
    if "СПИСОК" in normalized or "LIST" in normalized or "BULLET" in normalized:
        return "li", "list-item", "ul"
    if "НУМЕР" in normalized or "NUMBER" in normalized:
        return "li", "list-item", "ol"
    return "p", None, None


def _sort_story_files(story_files: list[str]) -> list[str]:
    def key(name: str) -> tuple[int, str]:
        stem = Path(name).stem
        if "_" in stem:
            _, suffix = stem.split("_", 1)
            if suffix.isdigit():
                return int(suffix), name
        return 10**9, name
    return sorted(story_files, key=key)


def _merge_numbered_references(lines: list[str]) -> list[str]:
    cleaned = "\n".join(line.strip() for line in lines if line.strip())
    if not cleaned:
        return []
    matches = list(re.finditer(r"(^|\n)\s*(\d{1,3})\s*[).]", cleaned))
    if not matches:
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


def convert_idml_to_html(idml_path: Path) -> str:
    """Convert IDML (InDesign) into a simple HTML body with headings and paragraphs."""
    if not idml_path.exists():
        raise FileNotFoundError(f"IDML file not found: {idml_path}")
    if idml_path.suffix.lower() != ".idml":
        raise ValueError("convert_idml_to_html expects a .idml file")

    html_parts: list[str] = ['<div class="idml-content">']
    with zipfile.ZipFile(idml_path) as zf:
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

        def flush_references() -> None:
            if not ref_lines:
                return
            refs = _merge_numbered_references(ref_lines)
            if refs:
                html_parts.append('<ol class="references">')
                for ref in refs:
                    html_parts.append(f"<li>{ref}</li>")
                html_parts.append("</ol>")
            ref_lines.clear()

        for story_file in story_files:
            if story_file not in zf.namelist():
                continue
            story_xml = zf.read(story_file)
            for style_raw, text in _iter_paragraphs(story_xml):
                style_name = ""
                if style_raw:
                    style_name = style_raw.split("/")[-1]
                    style_name = unquote(style_name)
                tag, css_class, list_type = _style_to_tag(style_name)
                class_attr = f' class="{css_class}"' if css_class else ""

                if css_class == "references":
                    ref_lines.append(text)
                    continue

                flush_references()

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

    html_parts.append("</div>")
    return "\n".join(html_parts)
