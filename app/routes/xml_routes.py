from __future__ import annotations

from pathlib import Path

from flask import jsonify, send_file, abort

def register_xml_routes(app, ctx):
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

    @app.route("/generate-xml", methods=["POST"])
    def generate_xml():
        """Генерация XML файлов для всех выпусков."""
        try:
            from services.xml_generator_helper import generate_xml_for_all_folders
            
            if not list_of_journals_path.exists():
                return jsonify({
                    "success": False,
                    "error": f"Файл data/list_of_journals.json не найден: {list_of_journals_path}"
                }), 400
            
            # Генерируем XML для всех папок
            results = generate_xml_for_all_folders(
                json_input_dir=json_input_dir,
                xml_output_dir=xml_output_dir,
                list_of_journals_path=list_of_journals_path
            )
            
            if not results:
                return jsonify({
                    "success": False,
                    "error": "Не удалось сгенерировать XML файлы. Проверьте наличие JSON файлов в подпапках."
                }), 400
            
            # Возвращаем список файлов для скачивания
            files_info = []
            for xml_file_path in results:
                if xml_file_path.exists() and xml_file_path.is_file():
                    # Создаем относительный путь от xml_output_dir для URL
                    try:
                        relative_path = xml_file_path.relative_to(xml_output_dir)
                        # Заменяем обратные слеши на прямые для URL
                        url_path = str(relative_path).replace('\\', '/')
                        files_info.append({
                            "name": xml_file_path.name,
                            "url": f"/download-xml/{url_path}"
                        })
                    except ValueError:
                        # Если файл не находится внутри xml_output_dir, используем полный путь
                        files_info.append({
                            "name": xml_file_path.name,
                            "url": f"/download-xml/{xml_file_path.name}"
                        })
            
            return jsonify({
                "success": True,
                "message": f"Успешно сгенерировано XML файлов: {len(files_info)}",
                "files": files_info,
                "folders": sorted({Path(item["name"]).stem for item in files_info})
            })
                
        except ImportError as e:
            return jsonify({
                "success": False,
                "error": f"Модуль xml_generator_helper недоступен: {e}"
            }), 500
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Ошибка при генерации XML: {str(e)}"
            }), 500

    @app.route("/download-xml/<path:xml_filename>")
    def download_xml(xml_filename: str):
        """Скачивание XML файла."""
        try:
            # Безопасность: проверяем, что путь не содержит опасные символы
            if ".." in xml_filename or xml_filename.startswith("/") or xml_filename.startswith("\\"):
                abort(404)
            
            xml_path = xml_output_dir / xml_filename
            
            # Проверяем, что файл существует и находится внутри xml_output_dir
            if not xml_path.exists() or not xml_path.is_file():
                abort(404)
            
            try:
                xml_path.resolve().relative_to(xml_output_dir.resolve())
            except ValueError:
                abort(404)
            
            return send_file(
                str(xml_path),
                mimetype='application/xml',
                as_attachment=True,
                download_name=xml_path.name
            )
        except Exception as e:
            abort(404)
    

