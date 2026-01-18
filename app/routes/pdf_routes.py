from __future__ import annotations

import io
import json
import re
from pathlib import Path

from flask import render_template_string, jsonify, request, send_file, abort

from app.app_dependencies import PDF_TO_HTML_AVAILABLE, extract_text_from_pdf
from app.app_helpers import get_source_files

def register_pdf_routes(app, ctx):
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

    @app.route("/api/pdf-files")
    def api_pdf_files():
        """API endpoint для получения списка PDF файлов из input_files (рекурсивно во всех подпапках)."""
        try:
            pdf_files = []
            
            # Проверяем input_files_dir (используем сохраненную переменную из замыкания)
            try:
                input_dir = _input_files_dir
                print(f"DEBUG: Проверяем input_files_dir: {input_dir}")
                print(f"DEBUG: input_files_dir type: {type(input_dir)}")
                print(f"DEBUG: input_files_dir exists: {input_dir.exists() if input_dir else 'None'}")
                print(f"DEBUG: input_files_dir is_dir: {input_dir.is_dir() if input_dir else 'None'}")
                
                if not input_dir or not input_dir.exists() or not input_dir.is_dir():
                    error_msg = f"Директория input_files не найдена или недоступна: {input_dir}"
                    print(f"ERROR: {error_msg}")
                    return jsonify({
                        "error": error_msg,
                        "input_files_dir": str(input_dir) if input_dir else "не определен"
                    }), 404
                
                # Проверяем, есть ли файлы
                pdf_count = len(list(input_dir.rglob("*.pdf")))
                print(f"DEBUG: ✅ Найдено PDF файлов в input_files: {pdf_count}")
                
            except NameError as ne:
                error_msg = f"input_files_dir не определен: {ne}"
                print(f"ERROR: {error_msg}")
                return jsonify({"error": error_msg}), 500
            except Exception as e:
                error_msg = f"Ошибка при проверке input_files_dir: {e}"
                print(f"ERROR: {error_msg}")
                import traceback
                print(traceback.format_exc())
                return jsonify({"error": error_msg}), 500
            
            # Ищем PDF файлы в input_files
            print(f"DEBUG: 🔍 Ищем PDF файлы в input_files: {input_dir}")
            print(f"DEBUG: Абсолютный путь: {input_dir.resolve()}")
            file_count = 0
            for file_path in input_dir.rglob("*.pdf"):
                try:
                    file_count += 1
                    # Получаем относительный путь от корневой директории
                    relative = file_path.relative_to(input_dir)
                    file_entry = str(relative.as_posix())
                    pdf_files.append(file_entry)
                    print(f"DEBUG: ✅ Найден файл #{file_count}: {file_entry} (полный путь: {file_path})")
                except ValueError as ve:
                    print(f"DEBUG: ❌ Пропущен файл {file_path} из-за ValueError: {ve}")
                    continue
            
            print(f"DEBUG: 📊 В input_files найдено {file_count} PDF файлов")
            
            print(f"DEBUG: 🎯 Всего найдено {len(pdf_files)} PDF файлов")
            if len(pdf_files) == 0:
                print(f"DEBUG: ⚠️ ВНИМАНИЕ: Файлы не найдены! Проверьте путь:")
                print(f"DEBUG:   - input_files: {input_dir} (exists={input_dir.exists()}, is_dir={input_dir.is_dir()})")
            # Сортируем для удобства
            result = sorted(pdf_files)
            print(f"DEBUG: 📤 Отправляем список из {len(result)} файлов")
            return jsonify(result)
        except Exception as e:
            import traceback
            error_msg = f"Ошибка при получении списка PDF файлов: {str(e)}\n{traceback.format_exc()}"
            print(f"ERROR: {error_msg}")
            return jsonify({"error": str(e), "details": traceback.format_exc()}), 500
    

    @app.route("/pdf-bbox")
    def pdf_bbox_form():
        """Веб-форма для поиска bbox в PDF файлах."""
        return render_template_string(PDF_BBOX_TEMPLATE)
    

    @app.route("/api/pdf-bbox", methods=["POST"])
    def api_pdf_bbox():
        """API endpoint для поиска блоков в PDF по ключевым словам."""
        try:
            data = request.get_json()
            pdf_filename = data.get("pdf_file")
            search_terms = data.get("terms", [])
            find_annotation = data.get("annotation", False)
            
            if not pdf_filename:
                return jsonify({"error": "Не указан файл PDF"}), 400
            
            # Безопасность: проверяем путь
            if ".." in pdf_filename or pdf_filename.startswith("/") or pdf_filename.startswith("\\"):
                return jsonify({"error": "Недопустимый путь к файлу"}), 400
            
            # Файл из input_files
            pdf_path = _input_files_dir / pdf_filename
            base_dir = _input_files_dir
            
            if not pdf_path.exists() or not pdf_path.is_file():
                return jsonify({"error": f"Файл не найден: {pdf_filename}"}), 404
            
            if pdf_path.suffix.lower() != ".pdf":
                return jsonify({"error": "Файл должен быть PDF"}), 400
            
            # Проверяем, что файл находится внутри базовой директории
            try:
                pdf_path.resolve().relative_to(base_dir.resolve())
            except ValueError:
                return jsonify({"error": "Недопустимый путь к файлу"}), 400
            
            # Импортируем функции для работы с bbox
            try:
                from converters.pdf_to_html import find_text_blocks_with_bbox, find_annotation_bbox_auto
            except ImportError:
                return jsonify({"error": "Функции для работы с bbox недоступны"}), 500
            
            if find_annotation:
                # Автоматический поиск аннотации
                result = find_annotation_bbox_auto(pdf_path)
                if result:
                    return jsonify({
                        "success": True,
                        "blocks": [result]
                    })
                else:
                    return jsonify({
                        "success": False,
                        "message": "Аннотация не найдена"
                    })
            else:
                # Поиск по ключевым словам
                if not search_terms:
                    search_terms = ["Резюме", "Аннотация", "Abstract", "Annotation", "Ключевые слова", "Keywords"]
                
                blocks = find_text_blocks_with_bbox(
                    pdf_path,
                    search_terms=search_terms,
                    expand_bbox=(0, -10, 0, 100)
                )
                
                return jsonify({
                    "success": True,
                    "blocks": blocks
                })
        
        except Exception as e:
            return jsonify({"error": f"Ошибка при обработке: {str(e)}"}), 500
    

    @app.route("/api/pdf-info", methods=["POST"])
    def api_pdf_info():
        """API endpoint для получения информации о PDF (количество страниц, размеры)."""
        try:
            data = request.get_json()
            pdf_filename = data.get("pdf_file")
            
            if not pdf_filename:
                return jsonify({"error": "Не указан файл PDF"}), 400
            
            # Безопасность: проверяем путь
            if ".." in pdf_filename or pdf_filename.startswith("/") or pdf_filename.startswith("\\"):
                return jsonify({"error": "Недопустимый путь к файлу"}), 400
            
            # Файл из input_files
            pdf_path = _input_files_dir / pdf_filename
            base_dir = _input_files_dir
            
            if not pdf_path.exists() or not pdf_path.is_file():
                return jsonify({"error": f"Файл не найден: {pdf_filename}"}), 404
            
            if pdf_path.suffix.lower() != ".pdf":
                return jsonify({"error": "Файл должен быть PDF"}), 400
            
            # Проверяем, что файл находится внутри базовой директории
            try:
                pdf_path.resolve().relative_to(base_dir.resolve())
            except ValueError:
                return jsonify({"error": "Недопустимый путь к файлу"}), 400
            
            # Получаем информацию о PDF через pdfplumber
            try:
                import pdfplumber
                print(f"DEBUG: Открываю PDF: {pdf_path}")
                with pdfplumber.open(str(pdf_path)) as pdf:
                    pages_info = []
                    for page in pdf.pages:
                        pages_info.append({
                            "width": page.width,
                            "height": page.height
                        })
                    
                    print(f"DEBUG: PDF содержит {len(pages_info)} страниц")
                    return jsonify({
                        "success": True,
                        "pdf_file": pdf_filename,
                        "total_pages": len(pages_info),
                        "pages": pages_info
                    })
            except ImportError as e:
                print(f"ERROR: pdfplumber не установлен: {e}")
                return jsonify({"error": "pdfplumber не установлен"}), 500
            except Exception as e:
                import traceback
                error_msg = f"Ошибка при чтении PDF: {str(e)}\n{traceback.format_exc()}"
                print(f"ERROR: {error_msg}")
                return jsonify({"error": f"Ошибка при чтении PDF: {str(e)}"}), 500
        
        except Exception as e:
            return jsonify({"error": f"Ошибка: {str(e)}"}), 500
    

    @app.route("/api/pdf-image/<path:pdf_filename>")
    def api_pdf_image(pdf_filename: str):
        """API endpoint для получения изображения страницы PDF."""
        try:
            # Безопасность: проверяем путь
            if ".." in pdf_filename or pdf_filename.startswith("/") or pdf_filename.startswith("\\"):
                print(f"ERROR: Недопустимый путь: {pdf_filename}")
                abort(404)
            
            # Файл из input_files
            pdf_path = _input_files_dir / pdf_filename
            base_dir = _input_files_dir
            
            if not pdf_path.exists() or not pdf_path.is_file():
                print(f"ERROR: Файл не найден: {pdf_path}")
                abort(404)
            
            if pdf_path.suffix.lower() != ".pdf":
                print(f"ERROR: Не PDF файл: {pdf_path}")
                abort(404)
            
            # Проверяем, что файл находится внутри базовой директории
            try:
                pdf_path.resolve().relative_to(base_dir.resolve())
            except ValueError:
                print(f"ERROR: Файл вне базовой директории: {pdf_path}")
                abort(404)
            
            # Получаем номер страницы из query параметра
            page_num = request.args.get('page', '0')
            try:
                page_num = int(page_num)
            except ValueError:
                page_num = 0
            
            print(f"DEBUG: Запрос изображения страницы {page_num} из {pdf_filename}")
            
            # Конвертируем страницу PDF в изображение
            try:
                from pdf2image import convert_from_path
                print(f"DEBUG: pdf2image доступен, конвертирую страницу {page_num + 1}")
                images = convert_from_path(
                    str(pdf_path),
                    first_page=page_num + 1,
                    last_page=page_num + 1,
                    dpi=150
                )
                
                if not images:
                    print(f"ERROR: Не удалось получить изображение для страницы {page_num + 1}")
                    abort(404)
                
                print(f"DEBUG: Получено изображение размером {images[0].size}")
                
                # Сохраняем изображение во временный буфер
                from io import BytesIO
                img_buffer = BytesIO()
                images[0].save(img_buffer, format='PNG')
                img_buffer.seek(0)
                
                return send_file(img_buffer, mimetype='image/png')
            except ImportError as e:
                print(f"ERROR: pdf2image не установлен: {e}")
                # Возвращаем пустое изображение 1x1 пиксель вместо ошибки
                from io import BytesIO
                from PIL import Image
                img = Image.new('RGB', (1, 1), color='white')
                img_buffer = BytesIO()
                img.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                return send_file(img_buffer, mimetype='image/png')
            except Exception as e:
                import traceback
                error_msg = f"Ошибка при конвертации: {str(e)}\n{traceback.format_exc()}"
                print(f"ERROR: {error_msg}")
                # Возвращаем пустое изображение вместо ошибки
                from io import BytesIO
                from PIL import Image
                img = Image.new('RGB', (1, 1), color='white')
                img_buffer = BytesIO()
                img.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                return send_file(img_buffer, mimetype='image/png')
        
        except Exception as e:
            import traceback
            error_msg = f"Ошибка: {str(e)}\n{traceback.format_exc()}"
            print(f"ERROR: {error_msg}")
            # Возвращаем пустое изображение вместо ошибки
            try:
                from io import BytesIO
                from PIL import Image
                img = Image.new('RGB', (1, 1), color='white')
                img_buffer = BytesIO()
                img.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                return send_file(img_buffer, mimetype='image/png')
            except:
                abort(500)
    

    @app.route("/api/pdf-extract-text", methods=["POST"])
    def api_pdf_extract_text():
        """API endpoint для извлечения текста из выделенных областей PDF."""
        try:
            data = request.get_json()
            pdf_filename = data.get("pdf_file")
            selections = data.get("selections", [])
            
            print(f"DEBUG: Запрос извлечения текста из {len(selections)} областей")
            print(f"DEBUG: PDF файл: {pdf_filename}")
            
            if not pdf_filename:
                return jsonify({"error": "Не указан файл PDF"}), 400
            
            if not selections:
                return jsonify({"error": "Нет выделенных областей"}), 400
            
            # Безопасность: проверяем путь
            if ".." in pdf_filename or pdf_filename.startswith("/") or pdf_filename.startswith("\\"):
                return jsonify({"error": "Недопустимый путь к файлу"}), 400
            
            pdf_path = _input_files_dir / pdf_filename
            
            if not pdf_path.exists() or not pdf_path.is_file():
                print(f"ERROR: Файл не найден: {pdf_path}")
                return jsonify({"error": f"Файл не найден: {pdf_filename}"}), 404
            
            # Проверяем, что файл находится внутри input_files_dir
            try:
                pdf_path.resolve().relative_to(_input_files_dir.resolve())
            except ValueError:
                return jsonify({"error": "Недопустимый путь к файлу"}), 400
            
            # Извлекаем текст из выделенных областей
            try:
                import pdfplumber
                extracted = []
                
                print(f"DEBUG: Открываю PDF: {pdf_path}")
                with pdfplumber.open(str(pdf_path)) as pdf:
                    print(f"DEBUG: PDF содержит {len(pdf.pages)} страниц")
                    
                    for idx, selection in enumerate(selections):
                        page_num = selection.get("page", 0)
                        field_id = selection.get("field_id")
                        is_rus_field = field_id in {
                            "title",
                            "annotation",
                            "keywords",
                            "references_ru",
                            "funding",
                            "author_surname_rus",
                            "author_initials_rus",
                            "author_org_rus",
                            "author_address_rus",
                            "author_other_rus",
                        }
                        is_eng_field = field_id in {
                            "title_en",
                            "annotation_en",
                            "keywords_en",
                            "references_en",
                            "funding_en",
                            "author_surname_eng",
                            "author_initials_eng",
                            "author_org_eng",
                            "author_address_eng",
                            "author_other_eng",
                        }
                        print(f"DEBUG: Обработка выделения {idx + 1}: страница {page_num}")
                        print(f"DEBUG: Координаты: x1={selection.get('pdf_x1')}, y1={selection.get('pdf_y1')}, x2={selection.get('pdf_x2')}, y2={selection.get('pdf_y2')}")
                        
                        if page_num >= len(pdf.pages):
                            print(f"WARNING: Страница {page_num} не существует (всего страниц: {len(pdf.pages)})")
                            continue
                        
                        page = pdf.pages[page_num]
                        page_height = page.height
                        print(f"DEBUG: Размер страницы: {page.width}x{page_height}")
                        
                        # Проверяем координаты
                        pdf_x1 = float(selection.get("pdf_x1", 0))
                        pdf_y1 = float(selection.get("pdf_y1", 0))  # Это уже инвертированная координата (top)
                        pdf_x2 = float(selection.get("pdf_x2", 0))
                        pdf_y2 = float(selection.get("pdf_y2", 0))  # Это уже инвертированная координата (bottom)
                        
                        # Нормализуем координаты
                        pdf_x1, pdf_x2 = min(pdf_x1, pdf_x2), max(pdf_x1, pdf_x2)
                        # pdf_y1 и pdf_y2 уже инвертированы в JavaScript, поэтому используем их напрямую
                        # Но нужно убедиться, что top < bottom
                        top = min(pdf_y1, pdf_y2)
                        bottom = max(pdf_y1, pdf_y2)
                        
                        # Ограничиваем координаты границами страницы
                        pdf_x1 = max(0, min(pdf_x1, page.width))
                        pdf_x2 = max(0, min(pdf_x2, page.width))
                        top = max(0, min(top, page.height))
                        bottom = max(0, min(bottom, page.height))
                        
                        # Убеждаемся, что x1 < x2 и top < bottom
                        if pdf_x1 >= pdf_x2:
                            pdf_x1, pdf_x2 = 0, page.width
                        if top >= bottom:
                            top, bottom = 0, page.height
                        
                        print(f"DEBUG: Область crop: x1={pdf_x1}, top={top}, x2={pdf_x2}, bottom={bottom}")
                        print(f"DEBUG: Размер страницы: {page.width}x{page.height}")
                        
                        # Используем crop для извлечения текста из области
                        try:
                            cropped = page.crop((pdf_x1, top, pdf_x2, bottom))
                            
                            # Извлекаем текст разными способами для диагностики
                            text_simple = cropped.extract_text()
                            
                            # Также пробуем извлечь через слова (words) для более точного контроля
                            words = cropped.extract_words()
                            
                            print(f"DEBUG: Извлеченный текст (простой метод): {text_simple[:100] if text_simple else '(пусто)'}")
                            print(f"DEBUG: Найдено слов: {len(words)}")
                            
                            # Если есть слова, можем собрать текст из них
                            if words:
                                # Сортируем слова по координатам (сверху вниз, слева направо)
                                words_sorted = sorted(words, key=lambda w: (w['top'], w['x0']))
                                text_from_words = ' '.join([w['text'] for w in words_sorted])
                                print(f"DEBUG: Текст из слов (первые 100 символов): {text_from_words[:100]}")
                                
                                # Пробуем определить, какой текст нужен (русский или английский)
                                # Если есть кириллица, предпочитаем русский текст
                                has_cyrillic = any(ord(c) >= 0x0400 and ord(c) <= 0x04FF for c in text_from_words)
                                has_latin = any(c.isalpha() and ord(c) < 0x0400 for c in text_from_words)
                                
                                print(f"DEBUG: Есть кириллица: {has_cyrillic}, есть латиница: {has_latin}")
                                
                                # Если есть и русский, и английский текст, определяем, какой преобладает
                                if has_cyrillic and has_latin:
                                    # Разделяем на русские и английские слова
                                    cyrillic_words = [w for w in words_sorted if any(ord(c) >= 0x0400 and ord(c) <= 0x04FF for c in w['text'])]
                                    latin_words = [w for w in words_sorted if not any(ord(c) >= 0x0400 and ord(c) <= 0x04FF for c in w['text']) and any(c.isalpha() for c in w['text'])]
                                    
                                    # Подсчитываем количество символов в каждом языке
                                    cyrillic_chars = sum(len(w['text']) for w in cyrillic_words)
                                    latin_chars = sum(len(w['text']) for w in latin_words)
                                    
                                    print(f"DEBUG: Кириллица: {len(cyrillic_words)} слов, {cyrillic_chars} символов")
                                    print(f"DEBUG: Латиница: {len(latin_words)} слов, {latin_chars} символов")
                                    
                                    # Выбираем язык с большим количеством символов
                                    if cyrillic_chars >= latin_chars:
                                        if cyrillic_words:
                                            text_from_words = ' '.join([w['text'] for w in cyrillic_words])
                                            print(f"DEBUG: Выбран русский текст (преобладает кириллица: {cyrillic_chars} > {latin_chars}): {text_from_words[:100]}")
                                    else:
                                        if latin_words:
                                            text_from_words = ' '.join([w['text'] for w in latin_words])
                                            print(f"DEBUG: Выбран английский текст (преобладает латиница: {latin_chars} > {cyrillic_chars}): {text_from_words[:100]}")
                            
                            # Используем текст из слов, если он есть, иначе простой метод
                            if words and len(words) > 0:
                                # Проверяем, есть ли кириллица в извлеченном тексте
                                has_cyrillic_in_simple = any(ord(c) >= 0x0400 and ord(c) <= 0x04FF for c in text_simple) if text_simple else False
                                
                                if has_cyrillic_in_simple:
                                    # Если в простом методе есть кириллица, используем его
                                    text = text_simple
                                    print(f"DEBUG: Используется простой метод (есть кириллица)")
                                elif 'text_from_words' in locals() and text_from_words:
                                    # Используем текст из слов
                                    text = text_from_words
                                    print(f"DEBUG: Используется метод из слов")
                                else:
                                    text = text_simple
                            else:
                                text = text_simple
                            
                            if is_rus_field:
                                ru_text = None
                                if words:
                                    cyrillic_words = [
                                        w for w in words_sorted
                                        if any(ord(c) >= 0x0400 and ord(c) <= 0x04FF for c in w["text"])
                                    ]
                                    if cyrillic_words:
                                        ru_text = " ".join([w["text"] for w in cyrillic_words])
                                if not ru_text and text_simple and any(ord(c) >= 0x0400 and ord(c) <= 0x04FF for c in text_simple):
                                    ru_text = text_simple
                                if ru_text:
                                    text = ru_text
                                    print(f"DEBUG: ??????? ????????? ??? ???? {field_id}: {text[:100]}")

                            if is_eng_field:
                                en_text = None
                                if words:
                                    latin_words = [
                                        w for w in words_sorted
                                        if any(c.isalpha() and ord(c) < 0x0400 for c in w["text"])
                                    ]
                                    if latin_words:
                                        en_text = " ".join([w["text"] for w in latin_words])
                                if not en_text and text_simple and any(c.isalpha() and ord(c) < 0x0400 for c in text_simple):
                                    en_text = text_simple
                                if en_text:
                                    text = en_text
                                    print(f"DEBUG: ??????? ????????? ??? ???? {field_id}: {text[:100]}")

                            if text:
                                text = text.strip()
                            else:
                                text = "(Текст не найден)"
                            
                            print(f"DEBUG: Финальный извлеченный текст (первые 100 символов): {text[:100]}")
                            
                            # Дополнительная проверка: если в тексте есть и русский, и английский,
                            # определяем преобладающий язык и выбираем соответствующий текст
                            if text and text != "(Текст не найден)":
                                has_cyrillic = any(ord(c) >= 0x0400 and ord(c) <= 0x04FF for c in text)
                                has_latin = any(c.isalpha() and ord(c) < 0x0400 for c in text)
                                
                                if has_cyrillic and has_latin:
                                    # Подсчитываем общее количество символов каждого языка
                                    total_cyrillic = sum(1 for c in text if ord(c) >= 0x0400 and ord(c) <= 0x04FF)
                                    total_latin = sum(1 for c in text if c.isalpha() and ord(c) < 0x0400)
                                    
                                    print(f"DEBUG: Финальная проверка - кириллица: {total_cyrillic} символов, латиница: {total_latin} символов")
                                    
                                    # Разделяем текст на слова для более точного анализа
                                    import re
                                    # Разбиваем на слова, сохраняя пробелы и переносы строк
                                    words_list = re.findall(r'\S+|\s+', text)
                                    
                                    # Определяем язык каждого слова
                                    cyrillic_parts = []
                                    latin_parts = []
                                    current_cyrillic = []
                                    current_latin = []
                                    
                                    for word in words_list:
                                        word_cyrillic = sum(1 for c in word if ord(c) >= 0x0400 and ord(c) <= 0x04FF)
                                        word_latin = sum(1 for c in word if c.isalpha() and ord(c) < 0x0400)
                                        
                                        if word_cyrillic > word_latin:
                                            # Преимущественно кириллица
                                            if current_latin:
                                                latin_parts.append(''.join(current_latin))
                                                current_latin = []
                                            current_cyrillic.append(word)
                                        elif word_latin > 0:
                                            # Преимущественно латиница
                                            if current_cyrillic:
                                                cyrillic_parts.append(''.join(current_cyrillic))
                                                current_cyrillic = []
                                            current_latin.append(word)
                                        else:
                                            # Пробелы, знаки препинания - добавляем к текущей группе
                                            if current_cyrillic:
                                                current_cyrillic.append(word)
                                            elif current_latin:
                                                current_latin.append(word)
                                    
                                    # Добавляем оставшиеся части
                                    if current_cyrillic:
                                        cyrillic_parts.append(''.join(current_cyrillic))
                                    if current_latin:
                                        latin_parts.append(''.join(current_latin))
                                    
                                    # Выбираем преобладающий язык
                                    cyrillic_text = ' '.join(cyrillic_parts).strip()
                                    latin_text = ' '.join(latin_parts).strip()
                                    
                                    print(f"DEBUG: Русские части: {len(cyrillic_parts)}, Английские части: {len(latin_parts)}")
                                    
                                    if total_cyrillic > total_latin:
                                        # Преобладает русский - используем русские части
                                        if cyrillic_text:
                                            text = cyrillic_text
                                            print(f"DEBUG: Выбран русский текст (преобладает кириллица: {total_cyrillic} > {total_latin})")
                                    else:
                                        # Преобладает английский - используем английские части
                                        if latin_text:
                                            text = latin_text
                                            print(f"DEBUG: Выбран английский текст (преобладает латиница: {total_latin} > {total_cyrillic})")
                                    
                                    # Если разделение не помогло, используем старый метод по строкам
                                    if not text or text == "(Текст не найден)":
                                        lines = text.split('\\n') if text else []
                                        filtered_lines = []
                                        for line in lines:
                                            line_cyrillic = sum(1 for c in line if ord(c) >= 0x0400 and ord(c) <= 0x04FF)
                                            line_latin = sum(1 for c in line if c.isalpha() and ord(c) < 0x0400)
                                            
                                            # Выбираем строки с преобладающим языком
                                            if total_latin > total_cyrillic:
                                                # Преобладает английский - выбираем строки с латиницей
                                                if line_latin > line_cyrillic or (line_latin > 0 and line_cyrillic == 0):
                                                    filtered_lines.append(line)
                                            else:
                                                # Преобладает русский - выбираем строки с кириллицей
                                                if line_cyrillic > line_latin or (line_cyrillic > 0 and line_latin == 0):
                                                    filtered_lines.append(line)
                                        
                                        if filtered_lines:
                                            text = '\n'.join(filtered_lines).strip()
                            
                            extracted.append({
                                "bbox": {
                                    "x1": pdf_x1,
                                    "y1": pdf_y1,
                                    "x2": pdf_x2,
                                    "y2": pdf_y2
                                },
                                "text": text
                            })
                        except Exception as crop_error:
                            import traceback
                            error_msg = f"Ошибка при crop: {str(crop_error)}\n{traceback.format_exc()}"
                            print(f"ERROR: {error_msg}")
                            extracted.append({
                                "bbox": {
                                    "x1": pdf_x1,
                                    "y1": pdf_y1,
                                    "x2": pdf_x2,
                                    "y2": pdf_y2
                                },
                                "text": f"(Ошибка извлечения: {str(crop_error)})"
                            })
                
                print(f"DEBUG: Извлечено текста из {len(extracted)} областей")
                return jsonify({
                    "success": True,
                    "extracted": extracted
                })
            except ImportError as e:
                print(f"ERROR: pdfplumber не установлен: {e}")
                return jsonify({"error": "pdfplumber не установлен"}), 500
            except Exception as e:
                import traceback
                error_msg = f"Ошибка при извлечении текста: {str(e)}\n{traceback.format_exc()}"
                print(f"ERROR: {error_msg}")
                return jsonify({"error": f"Ошибка при извлечении текста: {str(e)}"}), 500
        
        except Exception as e:
            import traceback
            error_msg = f"Ошибка: {str(e)}\n{traceback.format_exc()}"
            print(f"ERROR: {error_msg}")
            return jsonify({"error": f"Ошибка: {str(e)}"}), 500
    

    @app.route("/api/pdf-save-coordinates", methods=["POST"])
    def api_pdf_save_coordinates():
        """API endpoint для сохранения координат выделенных областей в JSON файл."""
        try:
            data = request.get_json()
            pdf_filename = data.get("pdf_file")
            total_pages = data.get("total_pages", 0)
            selections = data.get("selections", [])
            
            if not pdf_filename:
                return jsonify({"error": "Не указан файл PDF"}), 400
            
            if not selections:
                return jsonify({"error": "Нет выделенных областей для сохранения"}), 400
            
            # Создаем имя файла для сохранения координат
            pdf_path = Path(pdf_filename)
            output_filename = pdf_path.stem + "_bbox.json"
            output_path = json_input_dir / output_filename
            
            # Подготавливаем данные для сохранения
            output_data = {
                "pdf_file": pdf_filename,
                "total_pages": total_pages,
                "selections": []
            }
            
            for selection in selections:
                output_data["selections"].append({
                    "page": selection["page"],
                    "bbox": {
                        "x1": round(selection["pdf_x1"], 2),
                        "y1": round(selection["pdf_y1"], 2),
                        "x2": round(selection["pdf_x2"], 2),
                        "y2": round(selection["pdf_y2"], 2)
                    },
                    "text": selection.get("text", ""),
                    "field_id": selection.get("field_id")
                })
            
            # Сохраняем в JSON
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            return jsonify({
                "success": True,
                "file_path": str(output_path),
                "file_name": output_filename
            })
        
        except Exception as e:
            return jsonify({"error": f"Ошибка при сохранении: {str(e)}"}), 500
    

    @app.route("/pdf/<path:pdf_filename>")
    def serve_pdf(pdf_filename: str):
        """Маршрут для отдачи PDF файлов."""
        # Безопасность: проверяем, что путь не содержит опасные символы
        if ".." in pdf_filename or pdf_filename.startswith("/") or pdf_filename.startswith("\\"):
            abort(404)
        
        pdf_path = input_files_dir / pdf_filename
        
        if not pdf_path.exists() or not pdf_path.is_file():
            abort(404)
        
        # Проверяем расширение
        if pdf_path.suffix.lower() != ".pdf":
            abort(404)
        
        # Проверяем, что файл находится внутри input_files_dir
        try:
            pdf_path.resolve().relative_to(_input_files_dir.resolve())
        except ValueError:
            abort(404)
        
        return send_file(pdf_path, mimetype='application/pdf')
    

