from __future__ import annotations

import json
import re
from pathlib import Path
from html import unescape

from flask import render_template_string, jsonify, request, abort, send_file

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
from app.app_helpers import convert_file_to_html, merge_doi_url_in_html
from app.web_templates import VIEWER_TEMPLATE, MARKUP_TEMPLATE

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
    progress_state = ctx.get("progress_state")
    progress_lock = ctx.get("progress_lock")
    last_archive = ctx.get("last_archive")
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
        
        base_dirs = [_input_files_dir, words_input_dir]
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
        
        view_mode = (request.args.get("mode") or "html").lower()
        pdf_url = None
        if file_path.suffix.lower() == ".pdf":
            pdf_candidate = file_path
        else:
            pdf_candidate = file_path.with_suffix(".pdf")
            if not pdf_candidate.exists():
                pdf_candidate = None
                try:
                    rel_path = file_path.relative_to(words_input_dir)
                    candidate = (_input_files_dir / rel_path).with_suffix(".pdf")
                    if candidate.exists():
                        pdf_candidate = candidate
                except Exception:
                    pass
        if pdf_candidate and pdf_candidate.exists():
            try:
                rel_pdf = pdf_candidate.relative_to(_input_files_dir)
                rel_pdf_url = str(rel_pdf).replace("\\", "/")
                pdf_url = f"/pdf/{rel_pdf_url}"
            except Exception:
                pdf_url = None

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
        
        json_path = json_input_dir / json_filename
        
        if not json_path.exists() or not json_path.is_file():
            abort(404)
        
        # Проверяем расширение
        if json_path.suffix.lower() != ".json":
            abort(404)
        
        # Проверяем, что файл находится внутри json_input_dir
        try:
            json_path.resolve().relative_to(json_input_dir.resolve())
        except ValueError:
            abort(404)
        
        try:
            # Загружаем существующий JSON
            json_data = load_json_metadata(json_path)
            
            # Преобразуем JSON в данные для формы
            form_data = json_structure_to_form_data(json_data)
            
            # Находим соответствующие файлы в input_files
            # Логика: PDF для GPT, Word для HTML (если есть), иначе PDF для HTML
            pdf_for_gpt, file_for_html = find_files_for_json(json_path, _input_files_dir, json_input_dir)
            
            if not file_for_html:
                # Определяем подпапку для более информативного сообщения
                try:
                    relative_path = json_path.relative_to(json_input_dir)
                    if len(relative_path.parts) > 1:
                        subdir_name = relative_path.parts[0]
                        error_msg = (
                            f"??????: ?? ?????? ???? ??? {json_filename}<br><br>"
                            f"?????? ? ????? input_files/{subdir_name}/:<br>"
                            f"- {json_path.stem}.pdf / {json_path.stem}.docx / {json_path.stem}.rtf / {json_path.stem}.idml / {json_path.stem}.html / {json_path.stem}.tex<br><br>"
                            f"- full_issue.docx / full_issue.rtf / full_issue.html / full_issue.tex (полный выпуск)<br><br>"
                            f"????????? ???? ?: input_files/{subdir_name}/"
                        )
                    else:
                        error_msg = f"Ошибка: не найден соответствующий файл для {json_filename}"
                except ValueError:
                    error_msg = f"Ошибка: не найден соответствующий файл для {json_filename}"
                return error_msg, 404
            
            # Проверяем, является ли файл для HTML PDF или Word
            is_pdf_for_html = file_for_html.suffix.lower() == ".pdf"
            is_common_file = file_for_html.stem != json_path.stem
            
            # Для HTML: используем Word файл если есть, иначе PDF
            if is_pdf_for_html:
                # Для PDF файлов извлекаем текст для разметки
                pdf_path_for_html = file_for_html
                warnings = []
                html_body = ""
                # Извлекаем текст из PDF для разметки
                lines = extract_text_from_pdf(pdf_path_for_html)
            else:
                # Загружаем конфигурацию для определения использования Mistral
                config = None
                try:
                    config_path = Path("config.json")
                    if config_path.exists():
                        with open(config_path, "r", encoding="utf-8") as f:
                            config = json.load(f)
                except Exception:
                    pass
                
                # Определяем, использовать ли Mistral из конфига
                use_mistral = False
                if config:
                    use_mistral = config.get("pdf_to_html", {}).get("use_mistral", False)
                
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
                    pdf_path = pdf_for_gpt.resolve().relative_to(_input_files_dir.resolve())
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
                    pdf_relative = pdf_for_gpt.relative_to(_input_files_dir)
                    pdf_path_for_viewer = str(pdf_relative.as_posix())
                except ValueError:
                    pdf_path_for_viewer = pdf_for_gpt.name
            elif pdf_path_for_html:
                try:
                    pdf_relative = pdf_path_for_html.relative_to(_input_files_dir)
                    pdf_path_for_viewer = str(pdf_relative.as_posix())
                except ValueError:
                    pdf_path_for_viewer = pdf_path_for_html.name

            show_pdf_viewer = pdf_path_for_viewer is not None
            show_text_panel = True

            view_mode = (request.args.get("view") or "html").lower()
            if view_mode not in ("html", "pdf"):
                view_mode = "html"
            if view_mode == "pdf" and not show_pdf_viewer:
                view_mode = "html"

            print(f"DEBUG: is_pdf_for_html={is_pdf_for_html}, show_pdf_viewer={show_pdf_viewer}, show_text_panel={show_text_panel}, view_mode={view_mode}")

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
                view_mode=view_mode
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
        
        json_path = json_input_dir / json_filename
        
        if not json_path.exists() or not json_path.is_file():
            abort(404)
        
        # Проверяем расширение
        if json_path.suffix.lower() != ".json":
            abort(404)
        
        # Проверяем, что файл находится внутри json_input_dir
        try:
            json_path.resolve().relative_to(json_input_dir.resolve())
        except ValueError:
            abort(404)
        
        try:
            # Загружаем существующий JSON
            json_data = load_json_metadata(json_path)
            
            # Преобразуем JSON в данные для формы
            form_data = json_structure_to_form_data(json_data)
            
            # Находим соответствующий DOCX файл
            pdf_for_gpt, file_for_html = find_files_for_json(json_path, _input_files_dir, json_input_dir)

            if not file_for_html:
                return jsonify(error="???? ?????? ?? ?????? ? input_files"), 404

            docx_path = file_for_html
            
            # Проверяем, является ли найденный файл общим файлом выпуска
            is_common_file = docx_path.stem != json_path.stem
            
            # Проверяем, является ли файл PDF
            is_pdf = docx_path.suffix.lower() == ".pdf"
            
            if is_pdf:
                # Для PDF файлов извлекаем текст для разметки
                pdf_path = docx_path  # Сохраняем путь к PDF
                warnings = []  # Пустой список предупреждений для PDF
                html_body = ""  # Пустое тело HTML для PDF
                # Извлекаем текст из PDF для разметки
                lines = extract_text_from_pdf(pdf_path)
            else:
                # Загружаем конфигурацию для определения использования Mistral
                config = None
                try:
                    config_path = Path("config.json")
                    if config_path.exists():
                        with open(config_path, "r", encoding="utf-8") as f:
                            config = json.load(f)
                except Exception:
                    pass
                
                # Определяем, использовать ли Mistral из конфига
                use_mistral = False
                if config:
                    use_mistral = config.get("pdf_to_html", {}).get("use_mistral", False)
                
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
            data = request.get_json()
            field_id = data.get("field_id")  # "references_ru" или "references_en"
            raw_text = data.get("text", "")
            
            if not raw_text or not raw_text.strip():
                return jsonify(success=False, error="Текст для обработки пуст"), 400
            
            # Определяем язык и выбираем промпт
            language = "RUS" if field_id == "references_ru" else "ENG"
            prompt_type = "references_formatting_rus" if language == "RUS" else "references_formatting_eng"
            
            # Загружаем конфигурацию
            config = None
            try:
                config_path = Path("config.json")
                if config_path.exists():
                    with open(config_path, "r", encoding="utf-8") as f:
                        config = json.load(f)
            except Exception:
                pass
            
            # Получаем промпт из prompts.py
            try:
                from prompts import Prompts
                base_prompt = Prompts.get_prompt(prompt_type)
                prompt = base_prompt.format(references_text=raw_text)
            except Exception as e:
                # Если не удалось загрузить промпт, используем базовый
                lang_name = "Русский" if language == "RUS" else "English"
                prompt = f"""Ты помощник для нормализации библиографических списков научных статей.

Задача: Разбери предоставленный текст списка литературы и верни нормализованный список, где каждая библиографическая запись находится на отдельной строке.

Правила:
1. Убери лишние пробелы внутри слов, фамилий, инициалов
2. Объедини разорванные записи (если автор, название, год, страницы разбиты на несколько строк)
3. Исправь переносы внутри слов
4. Сохрани все важные элементы: авторы, название, год, издательство, страницы, DOI, URL
5. Не объединяй разные источники в одну запись
6. Верни результат в формате JSON: {{"references": ["запись 1", "запись 2", ...]}}

Язык: {lang_name}

Текст для обработки:
{raw_text}

Верни только валидный JSON без дополнительных комментариев."""
            
            # Используем GPT для обработки
            from services.gpt_extraction import extract_metadata_with_gpt
            
            result = extract_metadata_with_gpt(
                prompt,
                model=config.get("gpt_extraction", {}).get("model", "gpt-4o-mini") if config else "gpt-4o-mini",
                temperature=0.3,
                api_key=config.get("gpt_extraction", {}).get("api_key") if config else None,
                config=config
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
                    except:
                        pass
                
                # Если не нашли JSON, разбиваем по строкам
                if not references:
                    references = [line.strip() for line in response_text.split("\n") if line.strip() and not line.strip().startswith("{") and not line.strip().startswith("}")]
            
            # Объединяем в строку с переносами
            normalized_text = "\n".join(references)
            
            return jsonify(success=True, text=normalized_text, count=len(references))
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            return jsonify(success=False, error=str(e), details=error_details), 500
    

    @app.route("/markup/<path:json_filename>/save", methods=["POST"])
    def save_metadata(json_filename: str):
        """Сохранение метаданных обратно в JSON файл."""
        if not JSON_METADATA_AVAILABLE:
            return jsonify(success=False, error="Модуль json_metadata недоступен"), 500
        
        # Безопасность: проверяем, что путь не содержит опасные символы
        if ".." in json_filename or json_filename.startswith("/") or json_filename.startswith("\\"):
            abort(404)
        
        json_path = json_input_dir / json_filename
        
        if not json_path.exists() or not json_path.is_file():
            abort(404)
        
        # Проверяем, что файл находится внутри json_input_dir
        try:
            json_path.resolve().relative_to(json_input_dir.resolve())
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
            
            return jsonify(success=True, filename=str(json_path))
        except Exception as e:
            error_msg = f"Ошибка при сохранении метаданных: {e}"
            print(error_msg)
            return jsonify(success=False, error=error_msg), 500
    

