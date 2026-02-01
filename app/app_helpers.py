from __future__ import annotations

import html
import json
import re
import shutil
import time
from pathlib import Path
from typing import Dict, Optional

from converters.idml_to_html import convert_idml_to_html
from app.app_dependencies import (
    WORD_TO_HTML_AVAILABLE,
    convert_to_html,
    create_full_html_page,
    PDF_TO_HTML_AVAILABLE,
    convert_pdf_to_html,
    JSON_METADATA_AVAILABLE,
    load_json_metadata,
)

SUPPORTED_EXTENSIONS = {".docx", ".rtf", ".pdf", ".idml", ".html", ".tex"}

def get_issue_dirs(input_files_dir: Path, issue_name: str) -> Dict[str, Path]:
    issue_dir = input_files_dir / issue_name
    return {
        "issue_dir": issue_dir,
        "raw_dir": issue_dir / "raw",
        "json_dir": issue_dir / "json",
        "xml_dir": issue_dir / "xml",
        "state_dir": issue_dir / "state",
    }


def ensure_issue_dirs(input_files_dir: Path, issue_name: str) -> Dict[str, Path]:
    dirs = get_issue_dirs(input_files_dir, issue_name)
    for key, path in dirs.items():
        if key != "issue_dir":
            path.mkdir(parents=True, exist_ok=True)
    return dirs


def load_issue_state(input_files_dir: Path, issue_name: str) -> Dict:
    dirs = get_issue_dirs(input_files_dir, issue_name)
    state_path = dirs["state_dir"] / "progress.json"
    if not state_path.exists():
        return {}
    try:
        return json.loads(state_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_issue_state(input_files_dir: Path, issue_name: str, data: Dict) -> None:
    dirs = ensure_issue_dirs(input_files_dir, issue_name)
    state_path = dirs["state_dir"] / "progress.json"
    state = load_issue_state(input_files_dir, issue_name)
    state.update(data or {})
    state.setdefault("archive", issue_name)
    if "created_at" not in state:
        state["created_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    state["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

def _load_word_to_html_config(config: Optional[Dict]) -> Dict:
    if isinstance(config, dict):
        return config.get("word_to_html", {}) or {}
    try:
        base_dir = Path(__file__).resolve().parents[1]
        config_path = base_dir / "config.json"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                return loaded.get("word_to_html", {}) or {}
    except Exception:
        return {}
    return {}


def _resolve_style_map(style_map_value: object) -> Optional[str]:
    if not style_map_value:
        return None
    if isinstance(style_map_value, list):
        items = [str(item).strip() for item in style_map_value if str(item).strip()]
        return "\n".join(items) if items else None
    if isinstance(style_map_value, str):
        raw = style_map_value.strip()
        if not raw:
            return None
        base_dir = Path(__file__).resolve().parents[1]
        for candidate in (Path(raw), base_dir / raw):
            if candidate.exists() and candidate.is_file():
                try:
                    return candidate.read_text(encoding="utf-8")
                except Exception:
                    pass
        return raw
    return None

def is_json_processed(json_path: Path) -> bool:
    """
    Проверяет, обработан ли JSON файл через веб-интерфейс.
    Файл считается обработанным только если он был сохранен через кнопку "Сохранить"
    (отслеживается через специальное поле в JSON).
    
    Args:
        json_path: Путь к JSON файлу
        
    Returns:
        True, если файл обработан через веб-интерфейс
    """
    if not json_path.exists():
        return False
    
    try:
        if not JSON_METADATA_AVAILABLE:
            return False
        
        json_data = load_json_metadata(json_path)
        
        # Проверяем наличие специального флага, который устанавливается при сохранении через веб-интерфейс
        # Это гарантирует, что файл был обработан именно через веб-форму, а не просто содержит данные
        # Файл считается обработанным ТОЛЬКО если есть этот флаг
        is_processed_flag = json_data.get("_processed_via_web", False)
        
        return is_processed_flag
        
    except Exception:
        # В случае ошибки считаем файл необработанным
        return False


def get_json_files(json_input_dir: Path) -> list[dict]:
    """
    Получает список JSON файлов из указанной директории и всех подпапок.
    JSON файлы ожидаются в структуре input_files/<архив>/json/*.json.
    
    Args:
        json_input_dir: Путь к директории с JSON файлами (обычно input_files)
        
    Returns:
        Список словарей с информацией о файлах (включая относительный путь)
    """
    if not json_input_dir.exists() or not json_input_dir.is_dir():
        return []
    
    files = []
    has_json_subdir = any(p.name == "json" for p in json_input_dir.rglob("json"))
    # Рекурсивный поиск всех JSON файлов
    for file_path in sorted(json_input_dir.rglob("*.json"), key=lambda x: (x.parent.name, x.name)):
        try:
            if has_json_subdir:
                # Работаем только с файлами внутри подпапки "json"
                if "json" not in {p.name for p in file_path.parents}:
                    continue
                if file_path.parent.name != "json":
                    continue
            
            stat = file_path.stat()
            size_kb = stat.st_size / 1024
            modified = time.strftime("%d.%m.%Y %H:%M", time.localtime(stat.st_mtime))
            
            # Относительный путь от json_input_dir
            relative_path = file_path.relative_to(json_input_dir)
            issue_name = file_path.parent.parent.name if file_path.parent.name == "json" else file_path.parent.name
            
            # Проверяем, обработан ли файл
            is_processed = is_json_processed(file_path)
            
            # Извлекаем номера страниц для сортировки
            pages_start = None
            pages_str = ""
            if JSON_METADATA_AVAILABLE:
                try:
                    json_data = load_json_metadata(file_path)
                    pages_str = str(json_data.get("pages", "")).strip()
                    if pages_str:
                        # Парсим формат "5-20" или "21-34" и т.д.
                        match = re.match(r'^(\d+)(?:-(\d+))?', pages_str)
                        if match:
                            pages_start = int(match.group(1))
                except Exception:
                    pass
            
            files.append({
                "name": str(relative_path).replace("\\", "/"),  # Относительный путь для маршрутов Flask (с прямыми слэшами)
                "display_name": file_path.name,  # Только имя файла для отображения
                "path": file_path,  # Полный путь
                "size_kb": f"{size_kb:.1f}",
                "modified": modified,
                "extension": ".json",
                "is_processed": is_processed,  # Флаг обработки
                "pages_start": pages_start,  # Начальная страница для сортировки (None если нет)
                "pages": pages_str,  # Строка с номерами страниц
                "issue_name": issue_name,
            })
        except Exception:
            continue
    
    # Сортируем файлы: сначала по подпапке, затем по номерам страниц (если есть)
    # Файлы без страниц идут в конец
    files.sort(key=lambda x: (
        x.get("issue_name", ""),
        (x["pages_start"] if x["pages_start"] is not None else float('inf')),
        x["display_name"],
    ))
    
    return files


def _sanitize_folder_names(names: list[str]) -> list[str]:
    """Keep only safe folder names (no path separators)."""
    safe = []
    for name in names:
        if not name or not isinstance(name, str):
            continue
        if "/" in name or "\\" in name:
            continue
        if name in {".", ".."}:
            continue
        safe.append(name.strip())
    return [n for n in safe if n]


def cleanup_old_archives(archive_root_dir: Path, retention_days: int) -> int:
    """Remove archive runs older than retention_days (based on mtime)."""
    if retention_days <= 0:
        return 0
    if not archive_root_dir.exists():
        return 0
    cutoff = time.time() - (retention_days * 86400)
    removed = 0
    for entry in archive_root_dir.iterdir():
        try:
            if entry.is_dir() and entry.stat().st_mtime < cutoff:
                shutil.rmtree(entry)
                removed += 1
        except Exception as exc:
            print(f"WARNING: failed to remove old archive {entry}: {exc}")
    return removed


def archive_processed_folders(
    folder_names: list[str],
    archive_root_dir: Path,
    input_files_dir: Path,
) -> dict:
    """Move processed folders into a time-stamped archive run folder."""
    folder_names = _sanitize_folder_names(folder_names)
    if not folder_names:
        return {"archive_dir": "", "moved": []}
    archive_root_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    run_dir = archive_root_dir / stamp
    if run_dir.exists():
        run_dir = archive_root_dir / f"{stamp}_{int(time.time())}"
    moved = []
    for folder_name in folder_names:
        src = input_files_dir / folder_name
        if not src.exists():
            continue
        dest_base = run_dir / "projects"
        dest_base.mkdir(parents=True, exist_ok=True)
        dest = dest_base / folder_name
        try:
            if dest.exists():
                suffix = str(int(time.time()))
                dest = dest_base / f"{folder_name}_{suffix}"
            shutil.move(str(src), str(dest))
            moved.append(str(dest))
        except Exception as exc:
            print(f"WARNING: failed to archive {src}: {exc}")
    return {"archive_dir": str(run_dir), "moved": moved}


def list_archived_projects(archive_root_dir: Path) -> list[dict]:
    """Return list of archive runs with available issue folders."""
    if not archive_root_dir.exists() or not archive_root_dir.is_dir():
        return []
    runs: list[dict] = []
    for run_dir in sorted(archive_root_dir.iterdir(), reverse=True):
        if not run_dir.is_dir():
            continue
        issues: set[str] = set()
        subdir = run_dir / "projects"
        if subdir.exists() and subdir.is_dir():
            for issue_dir in subdir.iterdir():
                if issue_dir.is_dir():
                    issues.add(issue_dir.name)
        if issues:
            runs.append({
                "run": run_dir.name,
                "issues": sorted(issues),
            })
    return runs


def list_current_projects(input_files_dir: Path) -> list[str]:
    if not input_files_dir.exists() or not input_files_dir.is_dir():
        return []
    issues = []
    for entry in sorted(input_files_dir.iterdir()):
        if entry.is_dir():
            issues.append(entry.name)
    return issues


def restore_archived_project(
    archive_root_dir: Path,
    run_name: str,
    issue_name: str,
    input_files_dir: Path,
    overwrite: bool = False,
) -> dict:
    """Restore archived issue folders back into working directories."""
    run_dir = archive_root_dir / run_name
    if not run_dir.exists() or not run_dir.is_dir():
        return {"success": False, "error": f"Архив не найден: {run_name}"}

    moved: list[str] = []
    src = run_dir / "projects" / issue_name
    if not src.exists() or not src.is_dir():
        return {"success": False, "error": f"Папка проекта не найдена: {issue_name}"}
    dest = input_files_dir / issue_name
    if dest.exists():
        if not overwrite:
            return {
                "success": False,
                "error": f"Папка уже существует: {dest}",
                "code": "dest_exists",
            }
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dest))
    moved.append(str(dest))

    if not moved:
        return {
            "success": False,
            "error": f"В архиве нет данных для выпуска: {issue_name}",
        }

    return {"success": True, "moved": moved}

def get_source_files(input_dir: Path) -> list[dict]:
    """
    Получает список DOCX/RTF файлов из указанной директории и всех подпапок.
    Файлы могут находиться в подпапках вида issn_год_том_номер или issn_год_номер.
    
    Args:
        input_dir: Путь к директории с исходными файлами
        
    Returns:
        Список словарей с информацией о файлах (включая относительный путь)
    """
    if not input_dir.exists() or not input_dir.is_dir():
        return []
    
    files = []
    # Рекурсивный поиск всех DOCX/RTF файлов
    for ext in SUPPORTED_EXTENSIONS:
        for file_path in sorted(input_dir.rglob(f"*{ext}"), key=lambda x: (x.parent.name, x.name)):
            try:
                # Пропускаем файлы в корне words_input (если они там есть)
                # Работаем только с файлами в подпапках
                if file_path.parent == input_dir:
                    continue
                
                stat = file_path.stat()
                size_kb = stat.st_size / 1024
                modified = time.strftime("%d.%m.%Y %H:%M", time.localtime(stat.st_mtime))
                
                # Относительный путь от input_dir
                relative_path = file_path.relative_to(input_dir)
                
                files.append({
                    "name": str(relative_path),  # Путь вида "подпапка/файл.docx"
                    "path": file_path,  # Полный путь
                    "size_kb": f"{size_kb:.1f}",
                    "modified": modified,
                    "extension": ext,
                })
            except Exception:
                continue
    
    return files


def merge_doi_url_in_html(html_content: str) -> str:
    """
    Объединяет параграфы с DOI/URL с предыдущими параграфами в HTML.
    
    Если параграф содержит только DOI/URL (начинается с http и содержит doi.org),
    он объединяется с предыдущим параграфом.
    
    Args:
        html_content: HTML содержимое
        
    Returns:
        Обработанный HTML с объединенными параграфами
    """
    def is_doi_url_paragraph(text: str) -> bool:
        """Проверяет, является ли текст параграфа DOI/URL."""
        # Убираем HTML теги для проверки
        text_clean = re.sub(r'<[^>]+>', '', text).strip()
        if not text_clean:
            return False
        
        # Проверяем, начинается ли с http и содержит doi.org
        line_lower = text_clean.lower()
        return (
            text_clean.startswith("http") and 
            ("doi.org" in line_lower or "dx.doi.org" in line_lower)
        )
    
    # Паттерн для поиска параграфов <p>...</p> с возможными атрибутами
    pattern = r'(<p[^>]*>)(.*?)(</p>)'
    
    # Находим все параграфы
    matches = list(re.finditer(pattern, html_content, re.DOTALL))
    
    if not matches:
        return html_content
    
    # Собираем результат
    result_parts = []
    last_end = 0
    
    for i, match in enumerate(matches):
        # Текст до текущего параграфа
        if match.start() > last_end:
            result_parts.append(html_content[last_end:match.start()])
        
        open_tag = match.group(1)  # <p> или <p attr="...">
        content = match.group(2)    # содержимое параграфа
        close_tag = match.group(3)  # </p>
        
        # Проверяем, является ли это DOI/URL параграфом
        if is_doi_url_paragraph(content) and result_parts:
            # Объединяем с предыдущим параграфом
            # Ищем последний добавленный параграф
            last_part = result_parts[-1]
            
            # Если последняя часть заканчивается на </p>, объединяем
            if last_part.rstrip().endswith('</p>'):
                # Находим последний </p> в последней части
                last_p_end = last_part.rfind('</p>')
                if last_p_end != -1:
                    # Берем всё до </p>, добавляем пробел, DOI/URL и закрывающий тег
                    before_close = last_part[:last_p_end]
                    result_parts[-1] = before_close + " " + content + close_tag
                else:
                    result_parts.append(match.group(0))
            else:
                result_parts.append(match.group(0))
        else:
            # Обычный параграф, добавляем как есть
            result_parts.append(match.group(0))
        
        last_end = match.end()
    
    # Добавляем остаток после последнего параграфа
    if last_end < len(html_content):
        result_parts.append(html_content[last_end:])
    
    return ''.join(result_parts)


def _strip_latex_comments(text: str) -> str:
    lines = []
    for line in text.splitlines():
        cleaned = []
        escaped = False
        for ch in line:
            if ch == "\\" and not escaped:
                escaped = True
                cleaned.append(ch)
                continue
            if ch == "%" and not escaped:
                break
            escaped = False
            cleaned.append(ch)
        lines.append("".join(cleaned))
    return "\n".join(lines)


def _strip_latex_command(text: str, command: str) -> str:
    pattern = re.compile(rf"\\{command}\*?(?:\[[^\]]*\])?\{{([^{{}}]*)\}}")
    prev = None
    while prev != text:
        prev = text
        text = pattern.sub(lambda m: m.group(1) if m.groups() else m.group(0), text)
    return text


def _latex_to_html(latex_source: str) -> str:
    source = _strip_latex_comments(latex_source)
    source = source.replace("\r\n", "\n").replace("\r", "\n")
    source = source.lstrip("\ufeff")
    if "\\begin{document}" in source and "\\end{document}" in source:
        body = source.split("\\begin{document}", 1)[1]
        source = body.split("\\end{document}", 1)[0]

    source = re.sub(r"\\begin\{abstract\}", "\n<<ABSTRACT>>\n", source, flags=re.IGNORECASE)
    source = re.sub(r"\\end\{abstract\}", "\n<<ENDABSTRACT>>\n", source, flags=re.IGNORECASE)
    source = re.sub(r"\\begin\{keywords\}", "\n<<KEYWORDS>>\n", source, flags=re.IGNORECASE)
    source = re.sub(r"\\end\{keywords\}", "\n<<ENDKEYWORDS>>\n", source, flags=re.IGNORECASE)
    source = re.sub(
        r"\\keywords?\*?\{([^{}]*)\}",
        lambda m: "\n<<KEYWORDS>>" + (m.group(1) if m.groups() else "") + "\n",
        source,
        flags=re.IGNORECASE,
    )

    source = re.sub(r"\\begin\{itemize\}", "\n<<UL>>\n", source)
    source = re.sub(r"\\end\{itemize\}", "\n<<ENDUL>>\n", source)
    source = re.sub(r"\\begin\{enumerate\}", "\n<<OL>>\n", source)
    source = re.sub(r"\\end\{enumerate\}", "\n<<ENDOL>>\n", source)

    def _replace_item(match: re.Match) -> str:
        label = match.group(1) if match.groups() else None
        if label:
            return f"\n<<LI>> {label} "
        return "\n<<LI>> "

    source = re.sub(r"\\item(?:\[(.*?)\])?", _replace_item, source)

    source = re.sub(
        r"\\section\*?\{([^{}]*)\}",
        lambda m: "\n<<H2>>" + (m.group(1) if m.groups() else "") + "\n",
        source,
    )
    source = re.sub(
        r"\\subsection\*?\{([^{}]*)\}",
        lambda m: "\n<<H3>>" + (m.group(1) if m.groups() else "") + "\n",
        source,
    )
    source = re.sub(
        r"\\subsubsection\*?\{([^{}]*)\}",
        lambda m: "\n<<H4>>" + (m.group(1) if m.groups() else "") + "\n",
        source,
    )
    source = re.sub(
        r"\\paragraph\*?\{([^{}]*)\}",
        lambda m: "\n<<H5>>" + (m.group(1) if m.groups() else "") + "\n",
        source,
    )
    source = re.sub(
        r"\\title\*?\{([^{}]*)\}",
        lambda m: "\n<<H1>>" + (m.group(1) if m.groups() else "") + "\n",
        source,
    )

    source = source.replace("~", " ")
    source = re.sub(r"\\\\\s*(\[[^\]]*\])?", "\n", source)
    source = source.replace("\\par", "\n")

    for cmd in (
        "textbf",
        "textit",
        "emph",
        "underline",
        "textrm",
        "texttt",
        "textsc",
        "textsf",
        "textsl",
        "mathrm",
        "mathbf",
        "mathit",
    ):
        source = _strip_latex_command(source, cmd)

    source = re.sub(r"\\cite\*?(?:\[[^\]]*\])?\{[^{}]*\}", "", source)
    source = re.sub(r"\\ref\*?(?:\[[^\]]*\])?\{[^{}]*\}", "", source)
    source = re.sub(r"\\eqref\*?(?:\[[^\]]*\])?\{[^{}]*\}", "", source)

    source = re.sub(r"\\begin\{[^}]+\}", "", source)
    source = re.sub(r"\\end\{[^}]+\}", "", source)

    source = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?", "", source)
    source = source.replace("{", "").replace("}", "")
    source = re.sub(
        r"\$\$\s*(.*?)\s*\$\$",
        lambda m: m.group(1) if m.groups() else m.group(0),
        source,
        flags=re.DOTALL,
    )
    source = re.sub(
        r"\$(.*?)\$",
        lambda m: m.group(1) if m.groups() else m.group(0),
        source,
    )
    source = re.sub(r"[ \\t]+", " ", source)
    source = re.sub(r"\n{3,}", "\n\n", source)

    html_parts = ['<div class="latex-content">']
    paragraph: list[str] = []
    block_mode: str | None = None
    block_lines: list[str] = []
    in_list: str | None = None

    def flush_paragraph() -> None:
        if paragraph:
            text = " ".join(paragraph).strip()
            if text:
                html_parts.append(f"<p>{html.escape(text)}</p>")
            paragraph.clear()

    def close_list() -> None:
        nonlocal in_list
        if in_list == "ul":
            html_parts.append("</ul>")
        elif in_list == "ol":
            html_parts.append("</ol>")
        in_list = None

    for raw_line in source.split("\n"):
        line = raw_line.strip()
        if "<<ABSTRACT>>" in line:
            flush_paragraph()
            close_list()
            block_mode = "abstract"
            block_lines = []
            tail = line.replace("<<ABSTRACT>>", "").strip()
            if tail:
                block_lines.append(tail)
            continue
        if "<<KEYWORDS>>" in line:
            flush_paragraph()
            close_list()
            tail = line.replace("<<KEYWORDS>>", "").strip()
            if tail and "<<ENDKEYWORDS>>" not in line:
                html_parts.append(f'<p class="keywords">{html.escape(tail)}</p>')
                block_mode = None
                block_lines = []
                continue
            block_mode = "keywords"
            block_lines = []
            if tail:
                block_lines.append(tail)
            continue
        if "<<ENDABSTRACT>>" in line or "<<ENDKEYWORDS>>" in line:
            if block_mode and block_lines:
                text = " ".join(block_lines).strip()
                if text:
                    html_parts.append(f'<p class="{block_mode}">{html.escape(text)}</p>')
            block_mode = None
            block_lines = []
            remainder = line.replace("<<ENDABSTRACT>>", "").replace("<<ENDKEYWORDS>>", "").strip()
            if remainder:
                paragraph.append(remainder)
            continue
        if block_mode:
            if line:
                block_lines.append(line)
            continue
        if not line:
            flush_paragraph()
            continue

        if line == "<<UL>>":
            flush_paragraph()
            close_list()
            html_parts.append("<ul>")
            in_list = "ul"
            continue
        if line == "<<ENDUL>>":
            flush_paragraph()
            close_list()
            continue
        if line == "<<OL>>":
            flush_paragraph()
            close_list()
            html_parts.append("<ol>")
            in_list = "ol"
            continue
        if line == "<<ENDOL>>":
            flush_paragraph()
            close_list()
            continue

        for marker, tag in (
            ("<<H1>>", "h1"),
            ("<<H2>>", "h2"),
            ("<<H3>>", "h3"),
            ("<<H4>>", "h4"),
            ("<<H5>>", "h5"),
        ):
            if line.startswith(marker):
                flush_paragraph()
                close_list()
                title = line[len(marker):].strip()
                if title:
                    html_parts.append(f"<{tag}>{html.escape(title)}</{tag}>")
                break
        else:
            if line.startswith("<<LI>>"):
                flush_paragraph()
                if not in_list:
                    html_parts.append("<ul>")
                    in_list = "ul"
                item_text = line[len("<<LI>>"):].strip()
                if item_text:
                    html_parts.append(f"<li>{html.escape(item_text)}</li>")
                continue

            if in_list:
                html_parts.append(f"<li>{html.escape(line)}</li>")
            else:
                paragraph.append(line)

    flush_paragraph()
    if block_mode and block_lines:
        text = " ".join(block_lines).strip()
        if text:
            html_parts.append(f'<p class="{block_mode}">{html.escape(text)}</p>')
    close_list()
    html_parts.append("</div>")
    return "".join(html_parts)


def convert_file_to_html(
    file_path: Path,
    use_word_reader: bool = False,
    use_mistral: bool = False,
    config: Optional[Dict] = None
) -> tuple[str, list[str]]:
    """
    Конвертирует файл (DOCX/RTF/PDF) в HTML.
    
    Args:
        file_path: Путь к исходному файлу
        use_word_reader: Использовать ли word_reader для конвертации (только для Word файлов)
        use_mistral: Использовать ли Mistral AI для улучшения PDF конвертации
        config: Конфигурация (для получения настроек Mistral)
        
    Returns:
        Кортеж (HTML содержимое, список предупреждений)
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Файл не найден: {file_path}")
    
    suffix = file_path.suffix.lower()
    warnings: list[str] = []
    
    # Обработка HTML файлов
    if suffix == ".html":
        try:
            try:
                html_body = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                html_body = file_path.read_text(encoding="cp1251", errors="ignore")
            html_body = merge_doi_url_in_html(html_body)
            return html_body, warnings
        except Exception as e:
            raise RuntimeError(f"Ошибка чтения HTML: {e}") from e

    # Обработка LaTeX файлов
    if suffix == ".tex":
        try:
            try:
                latex_source = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                latex_source = file_path.read_text(encoding="cp1251", errors="ignore")
            html_body = _latex_to_html(latex_source)
            return html_body, warnings
        except Exception as e:
            raise RuntimeError(f"Ошибка чтения LaTeX: {e}") from e

    # Обработка PDF файлов
    if suffix == ".pdf":
        if not PDF_TO_HTML_AVAILABLE:
            raise RuntimeError(
                "PDF поддержка недоступна. "
                "Установите одну из библиотек: pip install pdfplumber или pip install pymupdf"
            )
        try:
            # Определяем, использовать ли Mistral из конфига
            if config and not use_mistral:
                use_mistral = config.get("pdf_to_html", {}).get("use_mistral", False)
            
            html_body, warnings = convert_pdf_to_html(
                file_path,
                prefer_pdfplumber=True,
                use_mistral=use_mistral,
                mistral_config=config
            )
            # Объединяем параграфы с DOI/URL с предыдущими (как для Word файлов)
            html_body = merge_doi_url_in_html(html_body)
            return html_body, warnings
        except Exception as e:
            raise RuntimeError(f"Ошибка конвертации PDF: {e}") from e
    
    # Обработка Word файлов (DOCX/RTF)
    if suffix == ".idml":
        html_body = convert_idml_to_html(file_path)
        html_body = merge_doi_url_in_html(html_body)
        return html_body, warnings

    if suffix not in {".docx", ".rtf"}:
        raise ValueError(
            f"Неподдерживаемый формат: {suffix}. "
            "Поддерживаются: .docx, .rtf, .pdf, .html, .idml, .tex"
        )
    
    if not WORD_TO_HTML_AVAILABLE:
        raise RuntimeError("word_to_html недоступен")
    
    try:
        word_cfg = _load_word_to_html_config(config)
        style_map_text = _resolve_style_map(word_cfg.get("style_map"))
        include_default_style_map = bool(word_cfg.get("include_default_style_map", True))
        include_metadata = bool(word_cfg.get("include_metadata", False))

        html_body, warnings = convert_to_html(
            file_path,
            style_map_text=style_map_text,
            include_default_style_map=include_default_style_map,
            use_word_reader=use_word_reader,
            include_metadata=include_metadata,
        )
        
        # Объединяем параграфы с DOI/URL с предыдущими
        html_body = merge_doi_url_in_html(html_body)
        
        return html_body, warnings
    except Exception as e:
        raise RuntimeError(f"Ошибка конвертации: {e}") from e


# ----------------------------
# Flask приложение
# ----------------------------
