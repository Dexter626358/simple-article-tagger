from __future__ import annotations

import json
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
            from services.xml_generator_helper import (
                create_config_from_folder_and_journal,
                generate_xml_for_archive_dir,
            )

            if not list_of_journals_path.exists():
                return jsonify({
                    "success": False,
                    "error": f"Файл data/list_of_journals.json не найден: {list_of_journals_path}",
                    "error_code": "journals_list_missing",
                    "details": {
                        "stage": "preflight",
                        "path": str(list_of_journals_path),
                        "hint": "Проверьте наличие файла data/list_of_journals.json и его доступность на запись/чтение.",
                    },
                }), 400

            session_id = get_session_id()
            session_input_dir = get_session_input_dir(_input_files_dir)
            progress_state = _get_progress_state(session_id)
            progress_lock = _get_progress_lock(session_id)
            archive_name = get_current_archive()
            if not archive_name:
                return jsonify({
                    "success": False,
                    "error": "Не выбран текущий выпуск.",
                    "error_code": "archive_not_selected",
                    "details": {
                        "stage": "preflight",
                        "hint": "Загрузите/выберите выпуск и повторите генерацию XML.",
                    },
                }), 400

            archive_dir = (session_input_dir / archive_name).resolve()
            if not archive_dir.exists() or not archive_dir.is_dir():
                return jsonify({
                    "success": False,
                    "error": f"Папка выпуска не найдена: {archive_name}",
                    "error_code": "archive_dir_missing",
                    "details": {
                        "stage": "preflight",
                        "archive": archive_name,
                        "path": str(archive_dir),
                        "hint": "Выпуск мог быть удалён или перемещён. Обновите страницу и загрузите проект заново.",
                    },
                }), 400

            json_dir = archive_dir / "json"
            if not json_dir.exists() or not json_dir.is_dir():
                return jsonify({
                    "success": False,
                    "error": f"Папка JSON не найдена: {json_dir}",
                    "error_code": "json_dir_missing",
                    "details": {
                        "stage": "preflight",
                        "archive": archive_name,
                        "path": str(json_dir),
                        "hint": "Проверьте структуру проекта: в выпуске должна быть папка json/ с файлами статей.",
                    },
                }), 400

            json_files = sorted(json_dir.glob("*.json"))
            if not json_files:
                return jsonify({
                    "success": False,
                    "error": f"В папке выпуска нет JSON файлов: {json_dir}",
                    "error_code": "json_files_missing",
                    "details": {
                        "stage": "preflight",
                        "archive": archive_name,
                        "path": str(json_dir),
                        "hint": "Добавьте JSON статьи в папку json/ и повторите генерацию XML.",
                    },
                }), 400

            invalid_json_files: list[dict] = []
            for file_path in json_files:
                try:
                    _ = json.loads(file_path.read_text(encoding="utf-8"))
                except Exception as exc:
                    invalid_json_files.append({
                        "name": file_path.name,
                        "error": str(exc),
                    })

            if invalid_json_files:
                return jsonify({
                    "success": False,
                    "error": "Обнаружены некорректные JSON файлы в выпуске.",
                    "error_code": "invalid_json_files",
                    "details": {
                        "stage": "preflight",
                        "archive": archive_name,
                        "invalid_json_files": invalid_json_files,
                        "hint": "Исправьте синтаксис JSON-файлов и повторите генерацию XML.",
                    },
                }), 400

            config_preview = create_config_from_folder_and_journal(archive_name, list_of_journals_path)
            if not config_preview:
                issn_guess = archive_name.split("_", 1)[0] if "_" in archive_name else archive_name
                return jsonify({
                    "success": False,
                    "error": f"Не удалось собрать конфигурацию выпуска для {archive_name}.",
                    "error_code": "journal_config_not_found",
                    "details": {
                        "stage": "preflight",
                        "archive": archive_name,
                        "issn": issn_guess,
                        "hint": "Проверьте ISSN в названии папки выпуска и наличие этого ISSN в data/list_of_journals.json.",
                    },
                }), 400

            xml_path = generate_xml_for_archive_dir(
                archive_dir=archive_dir,
                list_of_journals_path=list_of_journals_path,
            )

            if not xml_path:
                return jsonify({
                    "success": False,
                    "error": "Не удалось сгенерировать XML файлы.",
                    "error_code": "xml_generation_failed",
                    "details": {
                        "stage": "xml_build",
                        "archive": archive_name,
                        "json_count": len(json_files),
                        "hint": "Проверьте поля статей (обязательные данные, DOI, авторов, ссылки) и повторите генерацию.",
                    },
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
                "error": f"Модуль xml_generator_helper недоступен: {e}",
                "error_code": "xml_helper_import_error",
                "details": {
                    "stage": "server",
                    "hint": "Проверьте установку зависимостей и доступность services/xml_generator_helper.py.",
                },
            }), 500
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Ошибка при генерации XML: {str(e)}",
                "error_code": "xml_generation_exception",
                "details": {
                    "stage": "server",
                    "exception": str(e),
                },
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
    

