from __future__ import annotations

from pathlib import Path
import threading

from flask import jsonify, send_file, abort

from app.app_helpers import save_issue_state
from app.session_utils import (
    get_current_archive,
    get_session_id,
    get_session_input_dir,
    set_current_archive,
)

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
    progress_states = ctx.get("progress_states")
    progress_locks = ctx.get("progress_locks")
    progress_global_lock = ctx.get("progress_global_lock")
    validate_zip_members = ctx.get("validate_zip_members")
    find_files_for_json = ctx.get("find_files_for_json")
    SUPPORTED_EXTENSIONS = ctx.get("SUPPORTED_EXTENSIONS")
    SUPPORTED_JSON_EXTENSIONS = ctx.get("SUPPORTED_JSON_EXTENSIONS")

    def _default_progress_state() -> dict:
        return {
            "status": "idle",
            "processed": 0,
            "total": 0,
            "message": "",
            "archive": None,
        }

    def _get_progress_state(session_id: str) -> dict:
        with progress_global_lock:
            state = progress_states.get(session_id)
            if not state:
                state = _default_progress_state()
                progress_states[session_id] = state
            return state

    def _get_progress_lock(session_id: str):
        with progress_global_lock:
            lock = progress_locks.get(session_id)
            if not lock:
                lock = threading.Lock()
                progress_locks[session_id] = lock
            return lock

    @app.route("/generate-xml", methods=["POST"])
    def generate_xml():
        """Генерация XML файла для текущего выпуска."""
        try:
            from services.xml_generator_helper import generate_xml_for_archive_dir

            if not list_of_journals_path.exists():
                return jsonify({
                    "success": False,
                    "error": f"Файл data/list_of_journals.json не найден: {list_of_journals_path}"
                }), 400

            session_id = get_session_id()
            session_input_dir = get_session_input_dir(_input_files_dir)
            progress_state = _get_progress_state(session_id)
            progress_lock = _get_progress_lock(session_id)
            archive_name = get_current_archive()
            if not archive_name:
                return jsonify({
                    "success": False,
                    "error": "Не выбран текущий выпуск."
                }), 400

            archive_dir = (session_input_dir / archive_name).resolve()
            xml_path = generate_xml_for_archive_dir(
                archive_dir=archive_dir,
                list_of_journals_path=list_of_journals_path,
            )

            if not xml_path:
                return jsonify({
                    "success": False,
                    "error": "Не удалось сгенерировать XML файлы. Проверьте наличие JSON файлов и конфигурацию."
                }), 400

            files_info = []
            if xml_path.exists() and xml_path.is_file():
                try:
                    relative_path = xml_path.relative_to(session_input_dir)
                    url_path = str(relative_path).replace("\\", "/")
                    files_info.append({
                        "name": xml_path.name,
                        "url": f"/download-xml/{url_path}"
                    })
                except ValueError:
                    files_info.append({
                        "name": xml_path.name,
                        "url": f"/download-xml/{xml_path.name}"
                    })

            save_issue_state(
                session_input_dir,
                archive_name,
                {"status": "xml", "message": "XML сформирован"},
            )
            # Reset current archive state so UI can start a new issue
            set_current_archive(None)
            try:
                with progress_lock:
                    progress_state.update({
                        "status": "idle",
                        "processed": 0,
                        "total": 0,
                        "message": "",
                        "archive": None,
                    })
            except Exception:
                pass

            # Сбрасываем прогресс после генерации XML
            try:
                with progress_lock:
                    progress_state.update({
                        "status": "idle",
                        "processed": 0,
                        "total": 0,
                        "message": "",
                    })
            except Exception:
                pass

            return jsonify({
                "success": True,
                "message": f"XML файл сгенерирован: {xml_path.name}",
                "files": files_info,
                "folders": [archive_name],
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

            session_input_dir = get_session_input_dir(_input_files_dir)
            xml_path = (session_input_dir / xml_filename).resolve()

            if not xml_path.exists() or not xml_path.is_file():
                abort(404)

            try:
                xml_path.resolve().relative_to(session_input_dir.resolve())
            except ValueError:
                abort(404)

            return send_file(
                str(xml_path),
                mimetype='application/xml',
                as_attachment=True,
                download_name=xml_path.name
            )
        except Exception:
            abort(404)
    

