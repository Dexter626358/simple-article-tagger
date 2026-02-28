from __future__ import annotations

import json
import re
import os
import time
from pathlib import Path
from html import unescape

from flask import render_template_string, jsonify, request, abort, send_file, current_app

from app.app_dependencies import (
    METADATA_MARKUP_AVAILABLE,
    JSON_METADATA_AVAILABLE,
    extract_text_from_html,
    extract_text_from_pdf,
    load_json_metadata,
    save_json_metadata,
    form_data_to_json_structure,
    json_structure_to_form_data,
    find_docx_for_json,
)
from app.app_helpers import convert_file_to_html, merge_doi_url_in_html, save_issue_state, is_json_processed
from app.web_templates import VIEWER_TEMPLATE, MARKUP_TEMPLATE
from app.session_utils import get_session_input_dir

def register_markup_routes(app, ctx):
    json_input_dir = ctx.get("json_input_dir")
    words_input_dir = ctx.get("words_input_dir")
    xml_output_dir = ctx.get("xml_output_dir")
    list_of_journals_path = ctx.get("list_of_journals_path")
    input_files_dir = ctx.get("input_files_dir")
    _input_files_dir = ctx.get("_input_files_dir")
    _words_input_dir = ctx.get("_words_input_dir")
    use_word_reader = ctx.get("use_word_reader")
    archive_root_dir = ctx.get("archive_root_dir")
    archive_retention_days = ctx.get("archive_retention_days")
    validate_zip_members = ctx.get("validate_zip_members")
    find_files_for_json = ctx.get("find_files_for_json")
    SUPPORTED_EXTENSIONS = ctx.get("SUPPORTED_EXTENSIONS")
    SUPPORTED_JSON_EXTENSIONS = ctx.get("SUPPORTED_JSON_EXTENSIONS")

    @app.route("/view/<path:filename>")
    def view_file(filename: str):
        """Конвертация и отображение выбранного файла."""
        # Безопасность: проверяем, что путь не содержит опасные символы
        if ".." in filename or filename.startswith("/") or filename.startswith("\\"):
            abort(404)
        
        session_input_dir = get_session_input_dir(_input_files_dir)
        base_dirs = [session_input_dir, words_input_dir]
        file_path = None
        base_dir = None
        for candidate_base in base_dirs:
            if not candidate_base:
                continue
            candidate_path = candidate_base / filename
            if candidate_path.exists() and candidate_path.is_file():
                file_path = candidate_path
                base_dir = candidate_base
                break
        
        if not file_path:
            abort(404)
        
        # Проверяем расширение
        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            abort(404)
        
        # Проверяем, что файл находится внутри words_input_dir
        try:
            file_path.resolve().relative_to(base_dir.resolve())
        except ValueError:
            abort(404)
        
        requested_mode = (request.args.get("mode") or "").lower()
        pdf_url = None
        if file_path.suffix.lower() == ".pdf":
            pdf_candidate = file_path
        else:
            pdf_candidate = file_path.with_suffix(".pdf")
            if not pdf_candidate.exists():
                pdf_candidate = None
                try:
                    rel_path = file_path.relative_to(words_input_dir)
                    candidate = (session_input_dir / rel_path).with_suffix(".pdf")
                    if candidate.exists():
                        pdf_candidate = candidate
                except Exception:
                    pass
        if pdf_candidate and pdf_candidate.exists():
            try:
                rel_pdf = pdf_candidate.relative_to(session_input_dir)
                rel_pdf_url = str(rel_pdf).replace("\\", "/")
                pdf_url = f"/pdf/{rel_pdf_url}"
            except Exception:
                pdf_url = None

        view_mode = requested_mode or ("pdf" if pdf_url else "html")
        if view_mode not in ("html", "pdf"):
            view_mode = "pdf" if pdf_url else "html"
        if view_mode == "pdf" and not pdf_url:
            view_mode = "html"

        try:
            html_body, warnings = convert_file_to_html(file_path, use_word_reader=use_word_reader)
            
            # Если есть предупреждения, можно их отобразить (опционально)
            if warnings:
                print(f"Предупреждения для {filename}: {warnings}")
            
            html_url = f"/view/{filename}"
            pdf_view_url = f"/view/{filename}?mode=pdf"
            return render_template_string(
                VIEWER_TEMPLATE,
                filename=filename,
                content=html_body,
                view_mode=view_mode,
                html_url=html_url,
                pdf_view_url=pdf_view_url,
                pdf_url=pdf_url,
            )
        except Exception as e:
            error_msg = f"Ошибка при конвертации файла: {e}"
            print(error_msg)
            return error_msg, 500
    

    @app.route("/markup/<path:json_filename>")
    def markup_file(json_filename: str):
        """Страница разметки метаданных для выбранного JSON файла."""
        if not METADATA_MARKUP_AVAILABLE or not JSON_METADATA_AVAILABLE:
            return "Ошибка: необходимые модули недоступны", 500
        
        # Безопасность: проверяем, что путь не содержит опасные символы
        if ".." in json_filename or json_filename.startswith("/") or json_filename.startswith("\\"):
            abort(404)
        session_input_dir = get_session_input_dir(_input_files_dir)
        session_json_input_dir = session_input_dir
        json_path = session_json_input_dir / json_filename
        
        if not json_path.exists() or not json_path.is_file():
            abort(404)
        
        # Проверяем расширение
        if json_path.suffix.lower() != ".json":
            abort(404)
        
        # Проверяем, что файл находится внутри json_input_dir
        try:
            json_path.resolve().relative_to(session_json_input_dir.resolve())
        except ValueError:
            abort(404)
        
        try:
            # Загружаем существующий JSON
            json_data = load_json_metadata(json_path)
            
            # Преобразуем JSON в данные для формы
            form_data = json_structure_to_form_data(json_data)
            
            # Находим соответствующие файлы в input_files
            # Логика: PDF для GPT, Word для HTML (если есть), иначе PDF для HTML
            pdf_for_gpt, file_for_html = find_files_for_json(json_path, session_input_dir, session_json_input_dir)
            
            if not file_for_html:
                # Определяем подпапку для более информативного сообщения
                try:
                    relative_path = json_path.relative_to(session_json_input_dir)
                    if len(relative_path.parts) > 1:
                        subdir_name = relative_path.parts[0]
                        error_msg = (
                            f"Ошибка: не найден файл для {json_filename}<br><br>"
                            f"Ожидается в папке input_files/{subdir_name}/:<br>"
                            f"- {json_path.stem}.pdf / {json_path.stem}.docx / {json_path.stem}.rtf / {json_path.stem}.idml / {json_path.stem}.html / {json_path.stem}.tex<br><br>"
                            f"- full_issue.docx / full_issue.rtf / full_issue.html / full_issue.tex (полный выпуск)<br><br>"
                            f"Проверьте папку: input_files/{subdir_name}/"
                        )
                    else:
                        error_msg = f"Ошибка: не найден соответствующий файл для {json_filename}"
                except ValueError:
                    error_msg = f"Ошибка: не найден соответствующий файл для {json_filename}"
                return error_msg, 404
            
            # Проверяем, является ли файл для HTML PDF или Word
            is_pdf_for_html = file_for_html.suffix.lower() == ".pdf"
            is_common_file = file_for_html.stem != json_path.stem
            
            # Загружаем конфиг (используется и для Word, и для PDF режима)
            config = None
            try:
                config_path = Path("config.json")
                if config_path.exists():
                    with open(config_path, "r", encoding="utf-8") as f:
                        config = json.load(f)
            except Exception:
                pass

            use_mistral = False
            render_pdf_to_html = False
            if config:
                use_mistral = config.get("pdf_to_html", {}).get("use_mistral", False)
                render_pdf_to_html = bool(config.get("markup", {}).get("pdf_html_for_markup", False))

            # Для HTML: используем Word файл если есть, иначе PDF
            if is_pdf_for_html:
                pdf_path_for_html = file_for_html
                warnings = []
                if render_pdf_to_html:
                    # Полноценный PDF -> HTML даёт более корректную структуру (абзацы/колонки).
                    html_body, warnings = convert_file_to_html(
                        pdf_path_for_html,
                        use_word_reader=use_word_reader,
                        use_mistral=use_mistral,
                        config=config,
                    )
                    lines = extract_text_from_html(html_body)
                else:
                    # Быстрый fallback: плоское извлечение строк из PDF.
                    html_body = ""
                    lines = extract_text_from_pdf(pdf_path_for_html)
            else:
                # Конвертируем Word файл в HTML
                html_body, warnings = convert_file_to_html(
                    file_for_html,
                    use_word_reader=use_word_reader,
                    use_mistral=use_mistral,
                    config=config
                )
                
                # Извлекаем текст из HTML для разметки
                lines = extract_text_from_html(html_body)
                pdf_path_for_html = None

            for line in lines:
                if "text" in line:
                    line["text"] = unescape(str(line.get("text", "")))
            
            # Для GPT используем PDF файл (если есть), иначе None
            pdf_path = None
            if pdf_for_gpt:
                try:
                    pdf_path = pdf_for_gpt.resolve().relative_to(session_input_dir.resolve())
                except ValueError:
                    pdf_path = pdf_for_gpt
            
            # Опциональный отладочный вывод (можно включить через переменную окружения DEBUG_LITERATURE=1)
            import os
            if not is_pdf_for_html and os.getenv("DEBUG_LITERATURE") == "1" and ("Литература" in html_body or "литература" in html_body.lower()):
                lit_pos = html_body.lower().find("литература")
                if lit_pos != -1:
                    debug_html = html_body[max(0, lit_pos-100):lit_pos+2000]
                    print("=" * 80)
                    print("DEBUG: HTML вокруг слова 'Литература':")
                    print("=" * 80)
                    print(debug_html)
                    print("=" * 80)
                
                print("=" * 80)
                print(f"DEBUG: Всего извлечено строк: {len(lines)}")
                lit_lines = [line for line in lines if "литература" in line.get("text", "").lower() or 
                             (line.get("text", "").strip() and 
                              re.match(r'^\d+\.', line.get("text", "").strip()))]
                print(f"DEBUG: Найдено строк, связанных с литературой: {len(lit_lines)}")
                if lit_lines:
                    print("DEBUG: Примеры строк литературы:")
                    for i, line in enumerate(lit_lines[:5], 1):
                        print(f"  {i}. Строка {line.get('line_number')}: {line.get('text', '')[:100]}...")
                print("=" * 80)
            
            if warnings:
                print(f"Предупреждения для {json_filename}: {warnings}")
            
            # Если используется общий файл, пытаемся найти начало статьи по названию и/или фамилии автора
            article_start_line = None
            if is_common_file:
                # Получаем название статьи из JSON (приоритет: RUS, затем ENG)
                art_titles = json_data.get("artTitles", {})
                title_rus = str(art_titles.get("RUS", "")).strip()
                title_eng = str(art_titles.get("ENG", "")).strip()
                search_title = title_rus if title_rus else title_eng
                
                # Получаем фамилию первого автора из JSON (приоритет: RUS, затем ENG)
                author_surname = None
                authors = json_data.get("authors", [])
                if authors and isinstance(authors, list) and len(authors) > 0:
                    first_author = authors[0]
                    if isinstance(first_author, dict):
                        individ_info = first_author.get("individInfo", {})
                        rus_info = individ_info.get("RUS", {})
                        eng_info = individ_info.get("ENG", {})
                        surname_rus = str(rus_info.get("surname", "")).strip()
                        surname_eng = str(eng_info.get("surname", "")).strip()
                        author_surname = surname_rus if surname_rus else surname_eng
                
                # Используем название или фамилию автора для поиска
                search_terms = []
                if search_title:
                    search_terms.append(("title", search_title))
                if author_surname and len(author_surname) >= 2:
                    search_terms.append(("author", author_surname))
                
                if search_terms:
                    # Определяем конец содержания (оглавления)
                    # Ищем маркеры содержания: "Содержание", "Оглавление", "Contents", "Table of Contents"
                    content_end_line = 0
                    content_markers = [
                        r'содержание',
                        r'оглавление',
                        r'contents',
                        r'table of contents',
                        r'содержание\s*$',
                        r'оглавление\s*$',
                    ]
                    
                    # Ищем последнее вхождение маркера содержания
                    for idx, line in enumerate(lines):
                        line_text = line.get("text", "").lower().strip()
                        for marker in content_markers:
                            if re.search(marker, line_text, re.IGNORECASE):
                                # Найдено содержание, запоминаем строку
                                # Обычно содержание занимает несколько страниц, пропускаем еще 20-30 строк
                                content_end_line = idx + 30
                                break
                        if content_end_line > 0:
                            break
                    
                    # Если не нашли маркеры, пропускаем первые 50 строк (где обычно находится содержание)
                    if content_end_line == 0:
                        content_end_line = min(50, len(lines))
                    
                    print(f"Поиск статьи начинается со строки {content_end_line + 1} (пропущено содержание)")
                    if search_title:
                        print(f"  Ищем по названию: '{search_title[:50]}...'")
                    if author_surname:
                        print(f"  Ищем по фамилии автора: '{author_surname}'")
                    
                    # Функция для проверки, не является ли строка частью содержания
                    def is_content_line(line_text):
                        """Проверяет, не является ли строка частью содержания"""
                        text = line_text.strip()
                        # Исключаем очень короткие строки
                        if len(text) < 5:
                            return True
                        # Исключаем строки, заканчивающиеся только числом (номер страницы)
                        if re.search(r'^\s*\S+.*\d+\s*$', text) and len(re.findall(r'\d+', text)) <= 2:
                            return True
                        return False
                    
                    # Ищем по всем доступным терминам (сначала фамилия автора, затем название)
                    # Фамилия автора обычно более надежный маркер
                    search_order = sorted(search_terms, key=lambda x: 0 if x[0] == "author" else 1)
                    
                    for search_type, search_term in search_order:
                        if article_start_line:
                            break
                        
                        # Нормализуем термин для поиска
                        search_term_normalized = re.sub(r'\s+', ' ', search_term.lower().strip())
                        
                        # Ищем точное совпадение или частичное
                        for idx in range(content_end_line, len(lines)):
                            line = lines[idx]
                            line_text = line.get("text", "")
                            line_text_normalized = re.sub(r'\s+', ' ', line_text.lower().strip())
                            
                            # Для фамилии автора ищем точное совпадение или начало строки
                            if search_type == "author":
                                # Фамилия должна быть отдельным словом или в начале строки
                                if (search_term_normalized == line_text_normalized or
                                    line_text_normalized.startswith(search_term_normalized + " ") or
                                    re.search(r'\b' + re.escape(search_term_normalized) + r'\b', line_text_normalized)):
                                    if not is_content_line(line_text):
                                        article_start_line = idx + 1
                                        print(f"✓ Найдено начало статьи по фамилии автора '{search_term[:30]}...' на строке {article_start_line}")
                                        break
                            
                            # Для названия ищем точное совпадение или частичное (минимум 10 символов)
                            elif search_type == "title":
                                if (search_term_normalized == line_text_normalized or 
                                    (len(search_term_normalized) >= 10 and search_term_normalized in line_text_normalized)):
                                    if not is_content_line(line_text):
                                        article_start_line = idx + 1
                                        print(f"✓ Найдено начало статьи по названию '{search_term[:50]}...' на строке {article_start_line}")
                                        break
                        
                        # Если не нашли точное совпадение для названия, ищем по первым словам
                        if not article_start_line and search_type == "title" and len(search_term.split()) >= 3:
                            title_words = search_term.split()
                            # Берем первые 3-5 слов для поиска
                            search_phrase = " ".join(title_words[:min(5, len(title_words))])
                            search_phrase_normalized = re.sub(r'\s+', ' ', search_phrase.lower().strip())
                            
                            for idx in range(content_end_line, len(lines)):
                                line = lines[idx]
                                line_text = line.get("text", "")
                                line_text_normalized = re.sub(r'\s+', ' ', line_text.lower().strip())
                                
                                if search_phrase_normalized in line_text_normalized:
                                    if not is_content_line(line_text):
                                        article_start_line = idx + 1
                                        print(f"✓ Найдено начало статьи по первым словам названия '{search_phrase[:50]}...' на строке {article_start_line}")
                                        break
            
            # Передаем данные формы в шаблон для предзаполнения
            # Добавляем информацию о том, используется ли общий файл
            # Определяем, что показывать:
            # - Если есть только PDF (is_pdf_for_html == True) → показываем только PDF viewer
            # - Если есть Word файл (is_pdf_for_html == False) → показываем только HTML (текстовую панель)
            pdf_path_for_viewer = None
            if pdf_for_gpt:
                try:
                    pdf_relative = pdf_for_gpt.relative_to(session_input_dir)
                    pdf_path_for_viewer = str(pdf_relative.as_posix())
                except ValueError:
                    pdf_path_for_viewer = pdf_for_gpt.name
            elif pdf_path_for_html:
                try:
                    pdf_relative = pdf_path_for_html.relative_to(session_input_dir)
                    pdf_path_for_viewer = str(pdf_relative.as_posix())
                except ValueError:
                    pdf_path_for_viewer = pdf_path_for_html.name

            show_pdf_viewer = pdf_path_for_viewer is not None
            show_text_panel = True

            view_mode = (request.args.get("view") or ("pdf" if show_pdf_viewer else "html")).lower()
            if view_mode not in ("html", "pdf"):
                view_mode = "pdf" if show_pdf_viewer else "html"
            if view_mode == "pdf" and not show_pdf_viewer:
                view_mode = "html"

            # Извлекаем ISSN из имени папки (формат: issn_год_том_номер или issn_год_номер)
            journal_issn = ""
            journal_name = ""
            try:
                relative_path = json_path.relative_to(session_json_input_dir)
                if len(relative_path.parts) > 1:
                    folder_name = relative_path.parts[0]
                    # Пробуем извлечь ISSN из имени папки
                    parts = folder_name.split("_")
                    if len(parts) >= 2:
                        # ISSN может быть в формате XXXX-XXXX или XXXXXXXX
                        potential_issn = parts[0]
                        if re.match(r'^\d{4}[-]?\d{3}[\dXx]$', potential_issn):
                            journal_issn = potential_issn
                            # Форматируем ISSN: добавляем дефис если нет
                            if len(journal_issn) == 8 and '-' not in journal_issn:
                                journal_issn = f"{journal_issn[:4]}-{journal_issn[4:]}"
            except ValueError:
                pass

            print(f"DEBUG: is_pdf_for_html={is_pdf_for_html}, show_pdf_viewer={show_pdf_viewer}, show_text_panel={show_text_panel}, view_mode={view_mode}, issn={journal_issn}")

            return render_template_string(
                MARKUP_TEMPLATE, 
                filename=json_filename, 
                lines=lines,
                form_data=form_data or {},
                is_common_file=is_common_file,
                common_file_name=file_for_html.name if is_common_file else None,
                article_start_line=article_start_line,
                pdf_path=pdf_path_for_viewer,
                show_pdf_viewer=show_pdf_viewer,
                show_text_panel=show_text_panel,
                view_mode=view_mode,
                journal_issn=journal_issn,
                journal_name=journal_name
            )
        except Exception as e:
            error_msg = f"Ошибка при подготовке разметки: {e}"
            print(error_msg)
            return error_msg, 500
    

    @app.route("/api/article/<path:json_filename>")
    def api_get_article(json_filename: str):
        """API endpoint для получения данных статьи через AJAX."""
        # Явно указываем, что используем глобальный модуль re
        global re
        if not METADATA_MARKUP_AVAILABLE or not JSON_METADATA_AVAILABLE:
            return jsonify(error="Необходимые модули недоступны"), 500
        
        # Безопасность: проверяем, что путь не содержит опасные символы
        if ".." in json_filename or json_filename.startswith("/") or json_filename.startswith("\\"):
            abort(404)
        
        session_input_dir = get_session_input_dir(_input_files_dir)
        session_json_input_dir = session_input_dir
        json_path = session_json_input_dir / json_filename
        
        if not json_path.exists() or not json_path.is_file():
            abort(404)
        
        # Проверяем расширение
        if json_path.suffix.lower() != ".json":
            abort(404)
        
        # Проверяем, что файл находится внутри json_input_dir
        try:
            json_path.resolve().relative_to(session_json_input_dir.resolve())
        except ValueError:
            abort(404)
        
        try:
            # Загружаем существующий JSON
            json_data = load_json_metadata(json_path)
            
            # Преобразуем JSON в данные для формы
            form_data = json_structure_to_form_data(json_data)
            
            # Находим соответствующий DOCX файл
            pdf_for_gpt, file_for_html = find_files_for_json(json_path, session_input_dir, session_json_input_dir)

            if not file_for_html:
                return jsonify(error="Ошибка: файл не найден в input_files"), 404

            docx_path = file_for_html
            
            # Проверяем, является ли найденный файл общим файлом выпуска
            is_common_file = docx_path.stem != json_path.stem
            
            # Проверяем, является ли файл PDF
            is_pdf = docx_path.suffix.lower() == ".pdf"
            
            # Загружаем конфиг (используется и для Word, и для PDF режима)
            config = None
            try:
                config_path = Path("config.json")
                if config_path.exists():
                    with open(config_path, "r", encoding="utf-8") as f:
                        config = json.load(f)
            except Exception:
                pass

            use_mistral = False
            render_pdf_to_html = False
            if config:
                use_mistral = config.get("pdf_to_html", {}).get("use_mistral", False)
                render_pdf_to_html = bool(config.get("markup", {}).get("pdf_html_for_markup", False))

            if is_pdf:
                pdf_path = docx_path
                warnings = []
                if render_pdf_to_html:
                    html_body, warnings = convert_file_to_html(
                        pdf_path,
                        use_word_reader=use_word_reader,
                        use_mistral=use_mistral,
                        config=config,
                    )
                    lines = extract_text_from_html(html_body)
                else:
                    html_body = ""
                    lines = extract_text_from_pdf(pdf_path)
            else:
                # Конвертируем файл (DOCX/RTF) в HTML
                html_body, warnings = convert_file_to_html(
                    docx_path,
                    use_word_reader=use_word_reader,
                    use_mistral=use_mistral,
                    config=config
                )
                
                # Извлекаем текст из HTML для разметки
                lines = extract_text_from_html(html_body)
                pdf_path = None
            
            for line in lines:
                if "text" in line:
                    line["text"] = unescape(str(line.get("text", "")))

            # Если используется общий файл, пытаемся найти начало статьи
            article_start_line = None
            if is_common_file:
                art_titles = json_data.get("artTitles", {})
                title_rus = str(art_titles.get("RUS", "")).strip()
                title_eng = str(art_titles.get("ENG", "")).strip()
                search_title = title_rus if title_rus else title_eng
                
                author_surname = None
                authors = json_data.get("authors", [])
                if authors and isinstance(authors, list) and len(authors) > 0:
                    first_author = authors[0]
                    if isinstance(first_author, dict):
                        individ_info = first_author.get("individInfo", {})
                        rus_info = individ_info.get("RUS", {})
                        eng_info = individ_info.get("ENG", {})
                        surname_rus = str(rus_info.get("surname", "")).strip()
                        surname_eng = str(eng_info.get("surname", "")).strip()
                        author_surname = surname_rus if surname_rus else surname_eng
                
                search_terms = []
                if search_title:
                    search_terms.append(("title", search_title))
                if author_surname and len(author_surname) >= 2:
                    search_terms.append(("author", author_surname))
                
                if search_terms:
                    content_end_line = 0
                    content_markers = [
                        r'содержание',
                        r'оглавление',
                        r'contents',
                        r'table of contents',
                    ]
                    
                    for idx, line in enumerate(lines):
                        line_text = line.get("text", "").lower().strip()
                        for marker in content_markers:
                            if re.search(marker, line_text, re.IGNORECASE):
                                content_end_line = idx + 30
                                break
                        if content_end_line > 0:
                            break
                    
                    if content_end_line == 0:
                        content_end_line = min(50, len(lines))
                    
                    def is_content_line(line_text):
                        text = line_text.strip()
                        if len(text) < 5:
                            return True
                        if re.search(r'^\s*\S+.*\d+\s*$', text) and len(re.findall(r'\d+', text)) <= 2:
                            return True
                        return False
                    
                    search_order = sorted(search_terms, key=lambda x: 0 if x[0] == "author" else 1)
                    
                    for search_type, search_term in search_order:
                        if article_start_line:
                            break
                        
                        search_term_normalized = re.sub(r'\s+', ' ', search_term.lower().strip())
                        
                        for idx in range(content_end_line, len(lines)):
                            line = lines[idx]
                            line_text = line.get("text", "")
                            line_text_normalized = re.sub(r'\s+', ' ', line_text.lower().strip())
                            
                            if search_type == "author":
                                if (search_term_normalized == line_text_normalized or
                                    line_text_normalized.startswith(search_term_normalized + " ") or
                                    re.search(r'\b' + re.escape(search_term_normalized) + r'\b', line_text_normalized)):
                                    if not is_content_line(line_text):
                                        article_start_line = idx + 1
                                        break
                            
                            elif search_type == "title":
                                if (search_term_normalized == line_text_normalized or 
                                    (len(search_term_normalized) >= 10 and search_term_normalized in line_text_normalized)):
                                    if not is_content_line(line_text):
                                        article_start_line = idx + 1
                                        break
            
            # Генерируем HTML для текста статьи (только строки для выделения)
            from html import escape
            text_html = '<div class="search-box" style="margin-bottom: 15px; position: sticky; top: 0; background: white; padding: 10px 0; z-index: 100; border-bottom: 1px solid #e0e0e0;"><input type="text" id="searchInput" placeholder="🔍 Поиск в тексте..." style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;"></div><div id="textContent">'
            for line in lines:
                line_text = escape(str(line.get("text", "")))
                line_id = escape(str(line.get("id", "")))
                line_number = escape(str(line.get("line_number", "")))
                # Добавляем класс для начала статьи, если это нужная строка
                start_class = ' article-start-marker' if article_start_line and line.get("line_number") == article_start_line else ''
                text_html += f'<div class="line{start_class}" data-id="{line_id}" data-line="{line_number}"><span class="line-number">{line_number}</span><span class="line-text">{line_text}</span><button class="line-copy-btn" data-action="open-copy" title="Копировать фрагмент">✏️</button></div>'
            text_html += '</div>'
            
            # Генерируем HTML для формы (используем упрощенную версию MARKUP_TEMPLATE)
            # Извлекаем только форму из MARKUP_TEMPLATE
            from jinja2 import Template
            form_template = Template(MARKUP_TEMPLATE)
            form_html = form_template.render(
                filename=json_filename,
                form_data=form_data,
                lines=lines,
                is_common_file=is_common_file,
                article_start_line=article_start_line,
                common_file_name=docx_path.name if is_common_file else None
            )
            
            # Извлекаем только часть формы (без всего шаблона)
            # Находим начало формы
            form_start = form_html.find('<form id="metadataForm">')
            form_end = form_html.find('</form>') + 7
            
            if form_start != -1 and form_end > form_start:
                # Извлекаем форму и инструкции
                instructions_start = form_html.find('<div class="instructions">')
                instructions_end = form_html.find('</div>', instructions_start) + 6 if instructions_start != -1 else -1
                
                form_section = ''
                if instructions_start != -1 and instructions_end > instructions_start:
                    form_section += form_html[instructions_start:instructions_end]
                form_section += form_html[form_start:form_end]
                
                # Добавляем панель выбора полей
                selection_panel_start = form_html.find('<div id="selectionPanel"')
                if selection_panel_start != -1:
                    # Находим закрывающий тег для selectionPanel (может быть вложен)
                    depth = 0
                    pos = selection_panel_start
                    selection_panel_end = len(form_html)
                    while pos < len(form_html):
                        if form_html[pos:pos+4] == '<div':
                            depth += 1
                        elif form_html[pos:pos+6] == '</div>':
                            depth -= 1
                            if depth == 0:
                                selection_panel_end = pos + 6
                                break
                        pos += 1
                    form_section += form_html[selection_panel_start:selection_panel_end]
                
                # НЕ извлекаем JavaScript из MARKUP_TEMPLATE, чтобы избежать синтаксических ошибок
                # Все необходимые функции уже определены в главном шаблоне HTML_TEMPLATE
                # JavaScript из MARKUP_TEMPLATE может содержать сложные конструкции, которые ломаются при извлечении
            else:
                form_section = '<p>Ошибка генерации формы</p>'
            
            return jsonify({
                "html_content": text_html,
                "form_html": form_section,
                "filename": json_filename,
                "article_start_line": article_start_line
            })
            
        except Exception as e:
            error_msg = f"Ошибка при загрузке статьи: {e}"
            print(error_msg)
            import traceback
            error_details = traceback.format_exc()
            print(error_details)
            return jsonify(error=error_msg, details=error_details), 500
    

    @app.route("/process-references-ai", methods=["POST"])
    def process_references_ai():
        """Обрабатывает список литературы с помощью ИИ прямо в веб-форме."""
        try:
            request_start = time.time()
            data = request.get_json()
            field_id = data.get("field_id")  # "references_ru" или "references_en"
            raw_text = data.get("text", "")
            
            if not raw_text or not raw_text.strip():
                return jsonify(success=False, error="Текст для обработки пуст"), 400
            
            # Определяем язык
            language = "RUS" if field_id == "references_ru" else "ENG"
            
            # Загружаем конфигурацию
            config = None
            try:
                config_path = Path("config.json")
                if config_path.exists():
                    with open(config_path, "r", encoding="utf-8") as f:
                        config = json.load(f)
            except Exception:
                pass
            
            # Настройки чанкинга
            references_cfg = (config or {}).get("references_ai", {})
            chunk_size = references_cfg.get("chunk_size", 25)
            max_chunk_chars = references_cfg.get("max_chunk_chars", 8000)
            try:
                chunk_size = int(chunk_size)
            except Exception:
                chunk_size = 25
            if chunk_size <= 0:
                chunk_size = 25
            try:
                max_chunk_chars = int(max_chunk_chars)
            except Exception:
                max_chunk_chars = 8000
            if max_chunk_chars <= 1000:
                max_chunk_chars = 8000

            # Railway: более строгие лимиты - уменьшаем чанки
            if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY_PROJECT_ID"):
                chunk_size = min(chunk_size, 5)
                max_chunk_chars = min(max_chunk_chars, 3000)
                current_app.logger.info(
                    "SYSTEM references ai railway limits chunk_size=%s max_chunk_chars=%s",
                    chunk_size,
                    max_chunk_chars,
                )

            def _chunk_references(text: str) -> list[str]:
                lines = [line.strip() for line in text.splitlines() if line.strip()]
                if len(lines) >= 2:
                    if len(lines) <= chunk_size:
                        return ["\n".join(lines)]
                    return [
                        "\n".join(lines[i:i + chunk_size])
                        for i in range(0, len(lines), chunk_size)
                    ]
                # fallback: очень длинная строка без переводов
                text = text.strip()
                if len(text) <= max_chunk_chars:
                    return [text]
                chunks = []
                while text:
                    if len(text) <= max_chunk_chars:
                        chunks.append(text)
                        break
                    cut = text.rfind(".", 0, max_chunk_chars)
                    if cut < int(max_chunk_chars * 0.6):
                        cut = max_chunk_chars
                    chunks.append(text[:cut].strip())
                    text = text[cut:].lstrip()
                return chunks

            chunks = _chunk_references(raw_text)
            current_app.logger.info(
                "USER references ai start field=%s chunks=%s chars=%s",
                field_id,
                len(chunks),
                len(raw_text),
            )

            # Получаем промпт из prompts.py
            try:
                from prompts import Prompts
                base_prompt = Prompts.get_references_prompt(language)
            except Exception as e:
                return jsonify(success=False, error="Prompts module unavailable."), 500

            # Используем GPT для обработки
            from services.gpt_extraction import extract_metadata_with_gpt

            model = config.get("gpt_extraction", {}).get("model", "gpt-4o-mini") if config else "gpt-4o-mini"
            api_key = config.get("gpt_extraction", {}).get("api_key") if config else None

            def _build_prompt(template: str, text: str) -> str:
                if "{references_text}" in template:
                    return template.replace("{references_text}", text)
                return f"{template}\n\n{text}"

            def _looks_like_token_error(err: Exception) -> bool:
                msg = str(err).lower()
                return "token" in msg or "context" in msg or "too large" in msg

            def _split_lines_further(text: str, target: int) -> list[str]:
                lines = [line.strip() for line in text.splitlines() if line.strip()]
                if not lines:
                    return []
                if len(lines) <= target:
                    return ["\n".join(lines)]
                return [
                    "\n".join(lines[i:i + target])
                    for i in range(0, len(lines), target)
                ]

            def _run_chunk(chunk_text: str, chunk_index: int, retry_count: int = 0) -> list[str]:
                chunk_start = time.time()
                current_app.logger.info(
                    "SYSTEM references ai chunk start field=%s chunk=%s size=%s model=%s retry=%s",
                    field_id,
                    chunk_index,
                    len(chunk_text),
                    model,
                    retry_count,
                )
                prompt = _build_prompt(base_prompt, chunk_text)

                # Быстрая оценка размера промпта (токены ~ символы/4)
                estimated_tokens = max(1, len(prompt) // 4)
                current_app.logger.info(
                    "SYSTEM references ai prompt size chars=%s est_tokens=%s",
                    len(prompt),
                    estimated_tokens,
                )

                # Если слишком большой, просим внешний разбиение
                if estimated_tokens > 15000:
                    raise Exception("Prompt too large; needs splitting")

                # На повторах чуть уменьшаем температуру
                temp = max(0.1, 0.3 - (retry_count * 0.1))
                result = extract_metadata_with_gpt(
                    prompt,
                    model=model,
                    temperature=temp,
                    api_key=api_key,
                    raw_prompt=True,
                    config=config,
                )

                # Извлекаем нормализованный список
                references = []
                if isinstance(result, dict) and "references" in result:
                    references = result["references"]
                elif isinstance(result, list):
                    references = result
                else:
                    # Пытаемся извлечь из текста ответа
                    response_text = str(result)
                    # Ищем JSON в ответе
                    import re
                    json_match = re.search(r'\{.*"references".*\}', response_text, re.DOTALL)
                    if json_match:
                        try:
                            parsed = json.loads(json_match.group(0))
                            references = parsed.get("references", [])
                        except Exception:
                            pass
                    
                    # Если не нашли JSON, разбиваем по строкам
                    if not references:
                        references = [
                            line.strip()
                            for line in response_text.split("\n")
                            if line.strip() and not line.strip().startswith("{") and not line.strip().startswith("}")
                        ]

                if not isinstance(references, list):
                    references = [str(references)]

                cleaned = [r for r in references if str(r).strip()]
                elapsed = time.time() - chunk_start
                current_app.logger.info(
                    "SYSTEM references ai chunk done field=%s chunk=%s elapsed=%.2fs count=%s",
                    field_id,
                    chunk_index,
                    elapsed,
                    len(cleaned),
                )
                if elapsed > 20:
                    current_app.logger.warning(
                        "SYSTEM references ai slow chunk field=%s chunk=%s elapsed=%.2fs",
                        field_id,
                        chunk_index,
                        elapsed,
                    )
                return cleaned

            all_references = []
            max_prompt_chars = int(references_cfg.get("max_prompt_chars", 20000))
            for idx, chunk in enumerate(chunks, start=1):
                if len(chunk) > max_prompt_chars:
                    current_app.logger.warning(
                        "SYSTEM references ai chunk too large; splitting field=%s chunk=%s size=%s",
                        field_id,
                        idx,
                        len(chunk),
                    )
                    sub_chunks = _split_lines_further(chunk, max(5, chunk_size // 2))
                else:
                    sub_chunks = [chunk]

                for sub_idx, sub in enumerate(sub_chunks, start=1):
                    try:
                        refs = _run_chunk(sub, idx, retry_count=0)
                        all_references.extend(refs)
                    except Exception as exc:
                        if _looks_like_token_error(exc):
                            current_app.logger.warning(
                                "SYSTEM references ai token error; retrying smaller field=%s chunk=%s size=%s",
                                field_id,
                                idx,
                                len(sub),
                            )
                            smaller = _split_lines_further(sub, max(3, chunk_size // 3))
                            for sub2 in smaller:
                                refs2 = _run_chunk(sub2, idx, retry_count=1)
                                all_references.extend(refs2)
                        else:
                            raise

                # Небольшая пауза на Railway, чтобы избегать rate-limit
                if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY_PROJECT_ID"):
                    time.sleep(0)

            # Объединяем в строку с переносами
            normalized_text = "\n".join(all_references)
            total_elapsed = time.time() - request_start
            current_app.logger.info(
                "SYSTEM references ai done field=%s count=%s total_time=%.2fs",
                field_id,
                len(all_references),
                total_elapsed,
            )
            
            return jsonify(
                success=True,
                text=normalized_text,
                count=len(all_references),
                chunks=len(chunks),
                processing_time=round(total_elapsed, 2),
            )
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            try:
                total_elapsed = time.time() - request_start
                current_app.logger.exception(
                    "SYSTEM references ai error after %.2fs: %s",
                    total_elapsed,
                    e,
                )
            except Exception:
                pass
            current_app.logger.exception("SYSTEM references ai error: %s", e)
            return jsonify(success=False, error=str(e), details=error_details), 500

    @app.route("/process-annotation-ai", methods=["POST"])
    def process_annotation_ai():
        """Очищает аннотацию от технических артефактов с помощью ИИ без изменения смысла."""
        try:
            data = request.get_json(silent=True) or {}
            field_id = str(data.get("field_id") or "").strip()
            raw_text = str(data.get("text") or "")

            if field_id not in {"annotation", "annotation_en"}:
                return jsonify(success=False, error="Некорректный field_id."), 400
            if not raw_text.strip():
                return jsonify(success=False, error="Текст для обработки пуст."), 400

            config = None
            try:
                config_path = Path("config.json")
                if config_path.exists():
                    with open(config_path, "r", encoding="utf-8") as f:
                        config = json.load(f)
            except Exception:
                config = None

            model = (config or {}).get("gpt_extraction", {}).get("model", "gpt-4o-mini")
            api_key = (config or {}).get("gpt_extraction", {}).get("api_key")

            prompt = (
                "Ты инструмент очистки текста. Твоя единственная задача — убрать технические "
                "артефакты и привести специальные символы к читаемому формату.\n\n"
                "СТРОГО ЗАПРЕЩЕНО:\n"
                "- менять слова, термины, аббревиатуры\n"
                "- переформулировать предложения\n"
                "- исправлять грамматику или стиль\n"
                "- добавлять или убирать смысловые части\n"
                "- менять порядок предложений\n"
                "- переводить текст\n\n"
                "РАЗРЕШЕНО только:\n\n"
                "1. Артефакты копирования из PDF:\n"
                "- склеить слово, разорванное переносом: \"ис-\\nследование\" → \"исследование\"\n"
                "- убрать мягкие переносы (­)\n"
                "- убрать лишние переводы строк внутри одного абзаца\n"
                "- схлопнуть множественные пробелы в один\n"
                "- убрать табуляции\n"
                "- убрать префикс в самом начале: \"Аннотация.\", \"Abstract:\", \"Резюме.\" — только если это первое слово\n"
                "- сохранить абзацы (двойной перенос = граница абзаца)\n\n"
                "2. Индексы и степени:\n"
                "- нижний индекс оборачивать в <sub>...</sub>: \"H2O\" → \"H<sub>2</sub>O\"\n"
                "- верхний индекс оборачивать в <sup>...</sup>: \"м2\" → \"м<sup>2</sup>\"\n"
                "- диапазоны индексов: \"CO2, NO2\" — каждый индекс отдельно\n"
                "- если индекс неоднозначен — оставить как есть, не угадывать\n\n"
                "3. Формулы:\n"
                "- простые inline-формулы приводить к читаемому Unicode-тексту:\n"
                "  \"a^2 + b^2 = c^2\" → \"a² + b² = c²\"\n"
                "  \"x_1 + x_2\" → \"x₁ + x₂\"\n"
                "- дроби в тексте: \"1/2\" оставить как есть, не трогать\n"
                "- сложные многострочные формулы (интегралы, матрицы) — оставить как есть,\n"
                "  не пытаться интерпретировать\n"
                "- греческие буквы прописью → символ: \"alpha\" → \"α\", \"beta\" → \"β\",\n"
                "  \"mu\" → \"μ\", \"delta\" → \"Δ\" и т.д. — только если контекст научный\n"
                "  и написание прописью явно означает символ\n\n"
                "4. Спецсимволы:\n"
                "- градус: \"36.6 C\" → \"36.6°C\"\n"
                "- плюс-минус: \"+/-\" → \"±\"\n"
                "- умножение: \"5 x 10^3\" → \"5×10³\"\n"
                "- стрелки: \"->\" → \"→\", \"<-\" → \"←\"\n\n"
                "Верни ТОЛЬКО очищенный текст. Без объяснений, без комментариев,\n"
                "без кавычек вокруг текста.\n\n"
                "Текст для очистки:\n"
                f"{raw_text}"
            )

            from services.gpt_extraction import extract_metadata_with_gpt

            result = extract_metadata_with_gpt(
                prompt,
                model=model,
                temperature=0.0,
                api_key=api_key,
                raw_prompt=True,
                config=config,
            )

            cleaned = ""
            if isinstance(result, dict):
                cleaned = str(result.get("text") or result.get("cleaned_text") or "").strip()
                if not cleaned:
                    for value in result.values():
                        if isinstance(value, str) and value.strip():
                            cleaned = value.strip()
                            break
            else:
                cleaned = str(result or "").strip()

            if not cleaned:
                return jsonify(success=False, error="ИИ не вернул очищенный текст."), 500

            return jsonify(success=True, text=cleaned)
        except Exception as e:
            current_app.logger.exception("SYSTEM annotation ai error: %s", e)
            return jsonify(success=False, error=str(e)), 500

    @app.route("/crossref-update", methods=["POST"])
    def crossref_update():
        data = request.get_json(silent=True) or {}
        doi = (data.get("doi") or "").strip()
        if not doi:
            return jsonify(success=False, error="DOI не указан."), 400
        try:
            from crossref_updater import update_article_by_doi
        except Exception as e:
            current_app.logger.exception("SYSTEM crossref import error: %s", e)
            return jsonify(success=False, error="Crossref модуль недоступен."), 500
        try:
            payload = update_article_by_doi(doi)
            raw_payload = payload.get("raw")
            if isinstance(raw_payload, dict):
                session_input_dir = get_session_input_dir(_input_files_dir)
                state_dir = session_input_dir / "state" / "crossref"
                state_dir.mkdir(parents=True, exist_ok=True)
                safe_doi = re.sub(r"[^A-Za-z0-9._-]+", "_", doi)
                timestamp = int(time.time())
                raw_path = state_dir / f"crossref_{safe_doi}_{timestamp}.json"
                with raw_path.open("w", encoding="utf-8") as handle:
                    json.dump(raw_payload, handle, ensure_ascii=False, indent=2)

            def _format_reference_line(ref: dict) -> str:
                unstructured = str(ref.get("unstructured") or "").strip()
                if unstructured:
                    return unstructured
                parts = []
                for key in (
                    "author",
                    "title",
                    "journal",
                    "series_title",
                    "volume_title",
                    "publisher",
                    "edition",
                    "volume",
                    "issue",
                    "first_page",
                    "year",
                    "doi",
                    "isbn",
                    "issn",
                ):
                    value = ref.get(key)
                    if value is None:
                        continue
                    text = str(value).strip()
                    if text:
                        parts.append(text)
                return ". ".join(parts)

            references = []
            for ref in payload.get("references") or []:
                if not isinstance(ref, dict):
                    continue
                line = _format_reference_line(ref)
                if line:
                    references.append(line)
            return jsonify(
                success=True,
                doi=payload.get("doi"),
                title=payload.get("title"),
                original_title=payload.get("original_title"),
                abstract=payload.get("abstract"),
                authors=payload.get("authors") or [],
                references=references,
            )
        except Exception as e:
            current_app.logger.exception("SYSTEM crossref update error: %s", e)
            return jsonify(success=False, error=str(e)), 500
    

    @app.route("/markup/<path:json_filename>/save", methods=["POST"])
    def save_metadata(json_filename: str):
        """Сохранение метаданных обратно в JSON файл."""
        if not JSON_METADATA_AVAILABLE:
            return jsonify(success=False, error="Модуль json_metadata недоступен"), 500
        
        # Безопасность: проверяем, что путь не содержит опасные символы
        if ".." in json_filename or json_filename.startswith("/") or json_filename.startswith("\\"):
            abort(404)
        
        session_input_dir = get_session_input_dir(_input_files_dir)
        session_json_input_dir = session_input_dir
        json_path = session_json_input_dir / json_filename
        
        if not json_path.exists() or not json_path.is_file():
            abort(404)
        
        # Проверяем, что файл находится внутри json_input_dir
        try:
            json_path.resolve().relative_to(session_json_input_dir.resolve())
        except ValueError:
            abort(404)
        
        try:
            payload = request.get_json(force=True, silent=False)
            if not isinstance(payload, dict):
                return jsonify(success=False, error="Ожидался JSON-объект."), 400
            
            # Загружаем существующий JSON
            existing_json = load_json_metadata(json_path)
            
            # Преобразуем данные формы в структуру JSON и обновляем существующий JSON
            updated_json = form_data_to_json_structure(payload, existing_json)
            
            # Устанавливаем флаг, что файл был обработан через веб-интерфейс
            updated_json["_processed_via_web"] = True
            
            # Сохраняем обновленный JSON обратно в исходный файл в json_input
            save_json_metadata(updated_json, json_path)

            try:
                relative = json_path.relative_to(session_json_input_dir)
                issue_name = relative.parts[0] if relative.parts else ""
            except Exception:
                issue_name = ""
            if issue_name:
                json_dir = session_json_input_dir / issue_name / "json"
                total = len(list(json_dir.glob("*.json"))) if json_dir.exists() else 0
                processed = 0
                if json_dir.exists():
                    for path in json_dir.glob("*.json"):
                        if is_json_processed(path):
                            processed += 1
                save_issue_state(
                    session_input_dir,
                    issue_name,
                    {
                        "status": "markup",
                        "processed": processed,
                        "total": total,
                        "message": "Разметка обновлена",
                    },
                )
            
            return jsonify(success=True, filename=str(json_path))
        except Exception as e:
            error_msg = f"Ошибка при сохранении метаданных: {e}"
            print(error_msg)
            return jsonify(success=False, error=error_msg), 500
    
