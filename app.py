#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Веб-приложение для просмотра HTML страниц, сгенерированных word_to_html.
Позволяет выбрать DOCX/RTF файл из папки words_input, конвертировать его в HTML
и отобразить в браузере без сохранения в файл.
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
import time
import webbrowser
import zipfile
from pathlib import Path
from typing import Dict, Optional

from flask import Flask

from app.app_dependencies import WORD_TO_HTML_AVAILABLE
from app.routes.index_routes import register_index_routes
from app.routes.archive_routes import register_archive_routes
from app.routes.pdf_routes import register_pdf_routes
from app.routes.xml_routes import register_xml_routes
from app.routes.markup_routes import register_markup_routes

# ----------------------------
# Константы
# ----------------------------

SUPPORTED_EXTENSIONS = {".docx", ".rtf", ".pdf"}
SUPPORTED_JSON_EXTENSIONS = {".json"}
ARCHIVE_ROOT_DIRNAME = "processed_archives"
ARCHIVE_RETENTION_DAYS = 7







# ----------------------------
# Вспомогательные функции
# ----------------------------

def create_app(json_input_dir: Path, words_input_dir: Path, use_word_reader: bool = False, xml_output_dir: Path = None, list_of_journals_path: Path = None, input_files_dir: Path = None) -> Flask:
    """
    Создает Flask приложение для работы с JSON метаданными.
    
    Args:
        json_input_dir: Путь к директории с JSON файлами
        words_input_dir: Путь к директории с DOCX/RTF файлами
        use_word_reader: Использовать ли word_reader для конвертации
        xml_output_dir: Путь к директории для сохранения XML файлов
        list_of_journals_path: Путь к файлу data/list_of_journals.json
        input_files_dir: Путь к единой директории с входными файлами (PDF, DOCX, RTF и т.д.)
        
    Returns:
        Flask приложение
    """
    app = Flask(__name__)
    
    # Определяем пути по умолчанию, если не указаны
    script_dir = Path(__file__).parent.absolute()
    
    if xml_output_dir is None:
        xml_output_dir = script_dir / "xml_output"
    
    if list_of_journals_path is None:
        list_of_journals_path = script_dir / "data/list_of_journals.json"
    
    # Определяем путь к input_files, если не указан
    if input_files_dir is None:
        input_files_dir = script_dir / "input_files"
    
    archive_root_dir = script_dir / ARCHIVE_ROOT_DIRNAME
    archive_retention_days = ARCHIVE_RETENTION_DAYS
    try:
        config_path = script_dir / "config.json"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            retention_cfg = config.get("archive", {}).get("retention_days")
            if isinstance(retention_cfg, int) and retention_cfg >= 0:
                archive_retention_days = retention_cfg
    except Exception as exc:
        print(f"WARNING: failed to read archive retention from config.json: {exc}")
    
    # Сохраняем путь для использования в endpoint (замыкание)
    _input_files_dir = input_files_dir
    _words_input_dir = words_input_dir

    progress_state = {
        "status": "idle",
        "processed": 0,
        "total": 0,
        "message": "",
        "archive": None
    }
    last_archive = {"name": None}
    progress_lock = threading.Lock()
    
    print(f"DEBUG create_app: input_files_dir = {_input_files_dir}")
    print(f"DEBUG create_app: input_files_dir.exists() = {_input_files_dir.exists()}")

    def find_files_for_json(json_path: Path, input_dir: Path, json_input_dir: Path) -> tuple[Optional[Path], Optional[Path]]:
        """
        Find matching article files inside input_files/<issue>/ based on the JSON path.

        Returns (pdf_path_for_gpt, file_path_for_html):
        - If a matching DOCX/RTF exists, return (None, word_file) and skip PDF viewer.
        - If only a matching PDF exists, return (pdf_file, pdf_file).
        """
        json_stem = json_path.stem
        subdir_name = None

        try:
            relative_path = json_path.relative_to(json_input_dir)
            if len(relative_path.parts) > 1:
                subdir_name = relative_path.parts[0]
        except ValueError:
            return None, None

        if not subdir_name:
            return None, None

        issue_dir = input_dir / subdir_name
        if not issue_dir.exists() or not issue_dir.is_dir():
            return None, None

        pdf_files = list(issue_dir.glob("*.pdf"))
        word_files = list(issue_dir.glob("*.docx")) + list(issue_dir.glob("*.rtf"))

        pdf_for_article = next((p for p in pdf_files if p.stem == json_stem), None)
        word_for_article = next((w for w in word_files if w.stem == json_stem), None)
        word_full_issue = next((w for w in word_files if w.stem == "full_issue"), None)

        if word_full_issue:
            return pdf_for_article, word_full_issue
        if word_for_article:
            return None, word_for_article
        if pdf_for_article:
            return pdf_for_article, pdf_for_article

        return None, None

    def validate_zip_members(zf: zipfile.ZipFile, dest_dir: Path) -> tuple[bool, str | None]:
        for info in zf.infolist():
            if info.is_dir():
                continue
            member_path = Path(info.filename)
            if member_path.is_absolute() or ".." in member_path.parts:
                return False, info.filename
            if len(member_path.parts) > 1:
                return False, info.filename
            try:
                (dest_dir / member_path).resolve().relative_to(dest_dir.resolve())
            except ValueError:
                return False, info.filename
        return True, None

    routes_ctx = {
        "json_input_dir": json_input_dir,
        "words_input_dir": words_input_dir,
        "xml_output_dir": xml_output_dir,
        "list_of_journals_path": list_of_journals_path,
        "input_files_dir": input_files_dir,
        "_input_files_dir": _input_files_dir,
        "_words_input_dir": _words_input_dir,
        "use_word_reader": use_word_reader,
        "archive_root_dir": archive_root_dir,
        "archive_retention_days": archive_retention_days,
        "progress_state": progress_state,
        "progress_lock": progress_lock,
        "last_archive": last_archive,
        "validate_zip_members": validate_zip_members,
        "find_files_for_json": find_files_for_json,
        "SUPPORTED_EXTENSIONS": SUPPORTED_EXTENSIONS,
        "SUPPORTED_JSON_EXTENSIONS": SUPPORTED_JSON_EXTENSIONS,
    }

    register_index_routes(app, routes_ctx)
    register_archive_routes(app, routes_ctx)
    register_pdf_routes(app, routes_ctx)
    register_xml_routes(app, routes_ctx)
    register_markup_routes(app, routes_ctx)


    return app


# ----------------------------
# CLI / Запуск
# ----------------------------

def open_browser_later(url: str, delay_sec: float = 1.2) -> None:
    """Открывает браузер с задержкой."""
    def _open():
        time.sleep(delay_sec)
        webbrowser.open(url)
    
    threading.Thread(target=_open, daemon=True).start()


def main() -> int:
    """Главная функция для запуска приложения."""
    if not WORD_TO_HTML_AVAILABLE:
        print("❌ Ошибка: word_to_html недоступен.")
        print("   Убедитесь, что converters/word_to_html.py доступен.")
        return 1
    
    parser = argparse.ArgumentParser(
        description="Веб-приложение для просмотра DOCX/RTF документов через word_to_html"
    )
    parser.add_argument(
        "--json-input-dir",
        default=None,
        help="Путь к папке с JSON файлами (по умолчанию: json_input)"
    )
    parser.add_argument(
        "--words-input-dir",
        default=None,
        help="Путь к папке с DOCX/RTF файлами (по умолчанию: words_input)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5001,
        help="Порт для веб-сервера (по умолчанию: 5001)"
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Не открывать браузер автоматически"
    )
    parser.add_argument(
        "--use-word-reader",
        action="store_true",
        help="Использовать word_reader для конвертации"
    )
    parser.add_argument(
        "--no-debug",
        action="store_true",
        help="Отключить режим отладки (по умолчанию включен для разработки)"
    )
    
    args = parser.parse_args()
    
    script_dir = Path(__file__).parent.resolve()
    
    # Определяем директорию с JSON файлами
    if args.json_input_dir:
        json_input_dir = Path(args.json_input_dir)
        if not json_input_dir.is_absolute():
            json_input_dir = script_dir / json_input_dir
    else:
        json_input_dir = script_dir / "json_input"
    
    if not json_input_dir.exists():
        json_input_dir.mkdir(parents=True, exist_ok=True)
        print(f"⚠ Создана папка: {json_input_dir}")
        print("   Поместите JSON файлы в подпапки вида: issn_год_том_номер или issn_год_номер")
    
    # Определяем директорию с DOCX/RTF файлами
    if args.words_input_dir:
        words_input_dir = Path(args.words_input_dir)
        if not words_input_dir.is_absolute():
            words_input_dir = script_dir / words_input_dir
    else:
        words_input_dir = script_dir / "words_input"
    
    if not words_input_dir.exists():
        words_input_dir.mkdir(parents=True, exist_ok=True)
        print(f"⚠ Создана папка: {words_input_dir}")
        print("   Поместите DOCX или RTF файлы в подпапки вида: issn_год_том_номер или issn_год_номер")
    
    # Определяем пути для генерации XML
    xml_output_dir = script_dir / "xml_output"
    list_of_journals_path = script_dir / "data/list_of_journals.json"
    
    # Определяем единую директорию с входными файлами (PDF, DOCX, RTF и т.д.)
    input_files_dir = script_dir / "input_files"
    
    if not input_files_dir.exists():
        input_files_dir.mkdir(parents=True, exist_ok=True)
        print(f"⚠ Создана папка: {input_files_dir}")
        print("   Поместите файлы (PDF, DOCX, RTF) в подпапки вида: issn_год_том_номер или issn_год_номер")
    
    app = create_app(
        json_input_dir, 
        words_input_dir, 
        use_word_reader=args.use_word_reader,
        xml_output_dir=xml_output_dir,
        list_of_journals_path=list_of_journals_path,
        input_files_dir=input_files_dir
    )
    
    # Формируем URL главной страницы
    url = f"http://127.0.0.1:{args.port}/"
    
    if not args.no_browser:
        open_browser_later(url)
    
    print("\n" + "=" * 80)
    print("🌐 Веб-приложение для работы с метаданными")
    print("=" * 80)
    print(f"📁 Папка с JSON файлами: {json_input_dir}")
    print(f"📁 Папка с DOCX/RTF файлами: {words_input_dir}")
    print(f"📁 Единая папка с входными файлами (PDF, DOCX, RTF): {input_files_dir}")
    if args.use_word_reader:
        print("🔧 Используется word_reader для конвертации")
    print(f"🔗 URL: {url}")
    print("Для остановки: Ctrl+C")
    # По умолчанию debug=True для удобства разработки
    # Можно отключить через --no-debug для продакшена
    debug_mode = not args.no_debug
    if debug_mode:
        print("⚠️  Режим отладки включен (автоперезагрузка при изменении кода)")
    print("=" * 80 + "\n")
    
    try:
        app.run(host="127.0.0.1", port=args.port, debug=debug_mode)
    except KeyboardInterrupt:
        print("\n\nПриложение остановлено.")
        return 0
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

