#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import sys
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Iterable

import html as _html

# --- optional deps -----------------------------------------------------------

try:
    import mammoth
    MAMMOTH_AVAILABLE = True
except ImportError:
    MAMMOTH_AVAILABLE = False

try:
    import striprtf.striprtf as rtf
    RTF_AVAILABLE = True
except ImportError:
    RTF_AVAILABLE = False

try:
    from converters.word_reader import read_blocks, WordReaderError
    WORD_READER_AVAILABLE = True
except ImportError:
    WORD_READER_AVAILABLE = False


# --- helpers ----------------------------------------------------------------

def escape(s: object) -> str:
    """Безопасное HTML-экранирование (включая None)."""
    return _html.escape(str(s or ""), quote=True)

_TABLE_TAG_RE = re.compile(r"<table(?P<attrs>[^>]*)>", re.IGNORECASE)

def _postprocess_tables(html_content: str) -> str:
    if "<table" not in html_content.lower():
        return html_content

    def _inject_table_class(match: re.Match[str]) -> str:
        attrs = match.group("attrs") or ""
        class_match = re.search(r'class="([^"]*)"', attrs, flags=re.IGNORECASE)
        if class_match:
            classes = class_match.group(1)
            if "docx-table" in classes.split():
                return match.group(0)
            new_classes = f"{classes} docx-table".strip()
            new_attrs = re.sub(
                r'class="([^"]*)"',
                f'class="{new_classes}"',
                attrs,
                flags=re.IGNORECASE,
            )
            return f"<table{new_attrs}>"
        return f'<table class="docx-table"{attrs}>'

    html_content = _TABLE_TAG_RE.sub(_inject_table_class, html_content)
    html_content = re.sub(
        r"(?i)<table\\b",
        '<div class="table-wrap"><table',
        html_content,
    )
    html_content = re.sub(
        r"(?i)</table>",
        "</table></div>",
        html_content,
    )
    return html_content


DEFAULT_STYLE_MAP: list[str] = [
    "p[style-name='Title'] => h1.title:fresh",
    "p[style-name='Subtitle'] => h2.subtitle:fresh",
    "p[style-name='Heading 1'] => h1:fresh",
    "p[style-name='Heading 2'] => h2:fresh",
    "p[style-name='Heading 3'] => h3:fresh",
    "p[style-name='Heading 4'] => h4:fresh",
    "p[style-name='Heading 5'] => h5:fresh",
    "p[style-name='Heading 6'] => h6:fresh",
    "p[style-name='List Paragraph'] => p.list-paragraph",
    "p[style-name='Caption'] => p.caption",
    "r[style-name='Strong'] => strong",
    "r[style-name='Emphasis'] => em",
    "r[style-name='Underline'] => span.underline",
    "r[style-name='Small Caps'] => span.small-caps",
    "r[style-name='Subscript'] => sub",
    "r[style-name='Superscript'] => sup",
    "r[style-name='Code'] => code",
    "p[style-name='Quote'] => blockquote > p:fresh",
    "p[style-name='Intense Quote'] => blockquote.intense > p:fresh",
]


# --- conversions -------------------------------------------------------------

def _normalize_style_map(style_map: str | list[str] | None) -> str | None:
    if style_map is None:
        return None
    if isinstance(style_map, str):
        return style_map
    if isinstance(style_map, list):
        return "\n".join(s for s in style_map if str(s).strip())
    raise TypeError(f"style_map должен быть str|list[str]|None, получен: {type(style_map)}")


def convert_docx_to_html(
    input_file: Path,
    style_map_text: Optional[str] = None,
    include_default_style_map: bool = True,
) -> tuple[str, list[str]]:
    if not MAMMOTH_AVAILABLE:
        raise ImportError("mammoth не установлен. Установите: pip install mammoth")

    if input_file.suffix.lower() != ".docx":
        raise ValueError(f"Ожидается .docx, получено: {input_file.suffix}")

    if not input_file.exists():
        raise FileNotFoundError(f"Файл не найден: {input_file}")

    convert_options = {}

    if style_map_text:
        normalized = _normalize_style_map(style_map_text)
        if include_default_style_map:
            default_map = "\n".join(DEFAULT_STYLE_MAP)
            convert_options["style_map"] = f"{default_map}\n{normalized}" if normalized else default_map
        else:
            convert_options["style_map"] = normalized
    elif include_default_style_map:
        convert_options["style_map"] = "\n".join(DEFAULT_STYLE_MAP)

    try:
        with input_file.open("rb") as f:
            result = mammoth.convert_to_html(f, **convert_options)
    except Exception as e:
        raise RuntimeError(f"Ошибка mammoth при конвертации: {e}") from e

    html_content = result.value if isinstance(result.value, str) else str(result.value)
    messages = result.messages or []
    # mammoth обычно даёт list[dict], но пользователю проще list[str]
    warnings = [str(m) for m in messages] if isinstance(messages, list) else [str(messages)]
    return _postprocess_tables(html_content), warnings


def blocks_to_html(blocks: Iterable[object], include_metadata: bool = False) -> str:
    paragraphs: list[str] = []

    for b in blocks:
        text = getattr(b, "text", "")
        if not str(text).strip():
            continue

        attrs: list[str] = []
        if include_metadata:
            attrs.append(f'data-source="{escape(getattr(b, "source", ""))}"')
            attrs.append(f'data-block-type="{escape(getattr(b, "block_type", ""))}"')
            attrs.append(f'data-order="{escape(getattr(b, "order", ""))}"')

        attr_str = (" " + " ".join(attrs)) if attrs else ""
        paragraphs.append(f"<p{attr_str}>{escape(text)}</p>")

    return "\n".join(paragraphs) if paragraphs else "<div></div>"


def convert_with_word_reader(
    input_file: Path,
    include_metadata: bool = False,
) -> tuple[str, list[str]]:
    if not WORD_READER_AVAILABLE:
        raise ImportError("word_reader недоступен. Проверьте, что word_reader.py рядом со скриптом.")

    if not input_file.exists():
        raise FileNotFoundError(f"Файл не найден: {input_file}")

    try:
        blocks = read_blocks(input_file)
    except WordReaderError as e:
        raise RuntimeError(f"word_reader: ошибка чтения: {e}") from e
    except Exception as e:
        raise RuntimeError(f"word_reader: ошибка конвертации: {e}") from e

    if not blocks:
        return "<div></div>", ["Файл не содержит текста или текст не удалось извлечь"]

    return blocks_to_html(blocks, include_metadata=include_metadata), []


def convert_rtf_to_html(input_file: Path) -> tuple[str, list[str]]:
    if not RTF_AVAILABLE:
        raise ImportError("striprtf не установлен. Установите: pip install striprtf")

    if input_file.suffix.lower() != ".rtf":
        raise ValueError(f"Ожидается .rtf, получено: {input_file.suffix}")

    if not input_file.exists():
        raise FileNotFoundError(f"Файл не найден: {input_file}")

    warnings: list[str] = []
    content: Optional[str] = None
    for enc in ("utf-8", "cp1251", "windows-1251", "latin-1"):
        try:
            content = input_file.read_text(encoding=enc, errors="ignore")
            if content:
                break
        except Exception:
            pass

    if not content:
        raise RuntimeError("Не удалось прочитать RTF файл с доступными кодировками")

    try:
        plain = rtf.rtf_to_text(content) or ""
    except Exception as e:
        raise RuntimeError(f"Ошибка striprtf при разборе RTF: {e}") from e

    if not plain.strip():
        warnings.append("RTF файл не содержит текста")
        return "<div></div>", warnings

    lines = [line.strip() for line in plain.splitlines()]
    html_lines = [f"<p>{escape(line)}</p>" for line in lines if line]
    return ("\n".join(html_lines) if html_lines else "<div></div>"), warnings


def convert_to_html(
    input_file: Path,
    style_map_text: Optional[str] = None,
    include_default_style_map: bool = True,
    use_word_reader: bool = False,
    include_metadata: bool = False,
) -> tuple[str, list[str]]:
    suffix = input_file.suffix.lower()

    if use_word_reader:
        return convert_with_word_reader(input_file, include_metadata=include_metadata)

    if suffix == ".docx":
        return convert_docx_to_html(
            input_file,
            style_map_text=style_map_text,
            include_default_style_map=include_default_style_map,
        )
    if suffix == ".rtf":
        return convert_rtf_to_html(input_file)

    raise ValueError(f"Неподдерживаемый формат: {suffix}. Поддерживаются .docx и .rtf")


# --- html page ---------------------------------------------------------------

def create_full_html_page(html_body: str, title: str = "Документ", css: str = "") -> str:
    default_css = """
<style>
  body { font-family: Segoe UI, Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6;
         max-width: 900px; margin: 0 auto; padding: 20px; color: #333; background: #fff; }
  p { margin: 1em 0; text-align: justify; }
  blockquote { border-left: 4px solid #3498db; margin: 1em 0; padding-left: 1em; color: #555; font-style: italic; }
  .table-wrap { overflow-x: auto; }
  table.docx-table { width: 100%; border-collapse: collapse; margin: 1em 0; font-size: 0.95em; }
  table.docx-table th, table.docx-table td { border: 1px solid #d9dbe2; padding: 6px 8px; vertical-align: top; }
  table.docx-table thead th { background: #f2f4f8; font-weight: 600; }
</style>
"""
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escape(title)}</title>
  {default_css}{css}
</head>
<body>
{html_body}
</body>
</html>
"""


# --- cli --------------------------------------------------------------------

def main() -> None:
    script_dir = Path(__file__).resolve().parent
    default_input_dir = script_dir / "words_input"
    default_output_dir = script_dir / "html_output"

    p = argparse.ArgumentParser(description="Конвертация DOCX/RTF в HTML")
    p.add_argument("input_path", nargs="?", default=str(default_input_dir))
    p.add_argument("-o", "--output", default=None)
    p.add_argument("--output-dir", default=None)
    p.add_argument("--full-page", action="store_true")
    p.add_argument("--title", default=None)
    p.add_argument("--style-map", default=None)
    p.add_argument("--no-default-styles", action="store_true")
    p.add_argument("-r", "--recursive", action="store_true")
    p.add_argument("--use-word-reader", action="store_true")
    p.add_argument("--include-metadata", action="store_true")
    args = p.parse_args()

    input_path = Path(args.input_path)
    if not input_path.is_absolute():
        input_path = script_dir / input_path

    if not input_path.exists():
        print(f"Ошибка: путь не существует: {input_path}", file=sys.stderr)
        sys.exit(1)

    style_map_text = None
    if args.style_map:
        style_path = Path(args.style_map)
        if not style_path.is_absolute():
            style_path = script_dir / style_path
        try:
            style_map_text = style_path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"Предупреждение: не удалось загрузить style-map: {e}", file=sys.stderr)

    def finalize_html(body: str, src: Path) -> str:
        if args.full_page:
            return create_full_html_page(body, title=(args.title or src.stem))
        return body

    if input_path.is_file():
        out_file = Path(args.output) if args.output else (default_output_dir / f"{input_path.stem}.html")
        if not out_file.is_absolute():
            out_file = script_dir / out_file

        html_body, warnings = convert_to_html(
            input_path,
            style_map_text=style_map_text,
            include_default_style_map=not args.no_default_styles,
            use_word_reader=args.use_word_reader,
            include_metadata=args.include_metadata,
        )
        html_content = finalize_html(html_body, input_path)

        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(html_content, encoding="utf-8")

        print(f"✓ Успешно сохранено: {out_file}")
        if warnings:
            print("Предупреждения:")
            for w in warnings:
                print(f"  - {w}")
        return

    # directory
    output_dir = Path(args.output_dir) if args.output_dir else default_output_dir
    if not output_dir.is_absolute():
        output_dir = script_dir / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    patterns = ["*.docx", "*.rtf"]
    files: list[Path] = []
    for pat in patterns:
        files += list(input_path.rglob(pat) if args.recursive else input_path.glob(pat))
    files = sorted(files, key=lambda x: x.name)

    if not files:
        print(f"В директории {input_path} не найдено DOCX/RTF файлов", file=sys.stderr)
        sys.exit(1)

    ok = 0
    bad = 0
    for i, fp in enumerate(files, 1):
        try:
            html_body, warnings = convert_to_html(
                fp,
                style_map_text=style_map_text,
                include_default_style_map=not args.no_default_styles,
                use_word_reader=args.use_word_reader,
                include_metadata=args.include_metadata,
            )
            html_content = finalize_html(html_body, fp)
            rel = fp.relative_to(input_path)
            out = output_dir / rel.with_suffix(".html")
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(html_content, encoding="utf-8")
            ok += 1
            print(f"[{i}/{len(files)}] {fp.name} ✓" + (f" (warn: {len(warnings)})" if warnings else ""))
        except Exception as e:
            bad += 1
            print(f"[{i}/{len(files)}] {fp.name} ✗ {e}", file=sys.stderr)

    print(f"\nУспешно: {ok}, Ошибок: {bad}, Выход: {output_dir}")


if __name__ == "__main__":
    main()
