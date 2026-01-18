from __future__ import annotations

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

SUPPORTED_EXTENSIONS = {".docx", ".rtf", ".pdf", ".idml", ".html"}

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
    JSON файлы могут находиться в подпапках вида issn_год_том_номер или issn_год_номер.
    
    Args:
        json_input_dir: Путь к директории с JSON файлами
        
    Returns:
        Список словарей с информацией о файлах (включая относительный путь)
    """
    if not json_input_dir.exists() or not json_input_dir.is_dir():
        return []
    
    files = []
    # Рекурсивный поиск всех JSON файлов
    for file_path in sorted(json_input_dir.rglob("*.json"), key=lambda x: (x.parent.name, x.name)):
        try:
            # Пропускаем файлы в корне json_input (если они там есть)
            # Работаем только с файлами в подпапках
            if file_path.parent == json_input_dir:
                continue
            
            stat = file_path.stat()
            size_kb = stat.st_size / 1024
            modified = time.strftime("%d.%m.%Y %H:%M", time.localtime(stat.st_mtime))
            
            # Относительный путь от json_input_dir
            relative_path = file_path.relative_to(json_input_dir)
            
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
            })
        except Exception:
            continue
    
    # Сортируем файлы: сначала по подпапке, затем по номерам страниц (если есть)
    # Файлы без страниц идут в конец
    files.sort(key=lambda x: (
        x["path"].parent.name,  # Сначала по подпапке
        (x["pages_start"] if x["pages_start"] is not None else float('inf')),  # Затем по начальной странице
        x["display_name"]  # В конце по имени файла
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
    json_input_dir: Path,
    xml_output_dir: Path,
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
        for base_dir, subdir in (
            (input_files_dir, "input_files"),
            (json_input_dir, "json_input"),
            (xml_output_dir, "xml_output"),
        ):
            src = base_dir / folder_name
            if not src.exists():
                continue
            dest_base = run_dir / subdir
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
            "Поддерживаются: .docx, .rtf, .pdf, .html"
        )
    
    if not WORD_TO_HTML_AVAILABLE:
        raise RuntimeError("word_to_html недоступен")
    
    try:
        html_body, warnings = convert_to_html(
            file_path,
            style_map_text=None,
            include_default_style_map=True,
            use_word_reader=use_word_reader,
            include_metadata=False,
        )
        
        # Объединяем параграфы с DOI/URL с предыдущими
        html_body = merge_doi_url_in_html(html_body)
        
        return html_body, warnings
    except Exception as e:
        raise RuntimeError(f"Ошибка конвертации: {e}") from e


# ----------------------------
# Flask приложение
# ----------------------------
