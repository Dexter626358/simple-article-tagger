from __future__ import annotations

import io
import shutil
import threading
import zipfile
from pathlib import Path

from flask import jsonify, request

from app.app_dependencies import RTF_CONVERT_AVAILABLE, convert_rtf_to_docx
from app.app_helpers import archive_processed_folders, cleanup_old_archives, _sanitize_folder_names

def register_archive_routes(app, ctx):
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

    @app.route("/upload-input-archive", methods=["POST"])
    def upload_input_archive():
        if "archive" not in request.files:
            return jsonify({"success": False, "error": "Файл архива не найден в запросе."}), 400
        archive_file = request.files["archive"]
        if not archive_file or not archive_file.filename:
            return jsonify({"success": False, "error": "Файл архива не выбран."}), 400

        data = archive_file.read()
        if not data:
            return jsonify({"success": False, "error": "Файл архива пуст."}), 400

        buffer = io.BytesIO(data)
        if not zipfile.is_zipfile(buffer):
            return jsonify({"success": False, "error": "Загруженный файл не является ZIP архивом."}), 400

        buffer.seek(0)
        with zipfile.ZipFile(buffer) as zf:
            is_valid, bad_name = validate_zip_members(zf, _input_files_dir)
            if not is_valid:
                return jsonify({
                    "success": False,
                    "error": f"Недопустимая структура архива: {bad_name}"
                }), 400

            _input_files_dir.mkdir(parents=True, exist_ok=True)
            archive_stem = Path(archive_file.filename).stem.strip()
            if not archive_stem:
                return jsonify({"success": False, "error": "Не удалось определить имя архива."}), 400
            archive_dir = (_input_files_dir / archive_stem).resolve()
            archive_dir.mkdir(parents=True, exist_ok=True)
            last_archive["name"] = archive_stem
            with progress_lock:
                progress_state.update({
                    "status": "idle",
                    "processed": 0,
                    "total": 0,
                    "message": "",
                    "archive": archive_stem
                })
            extracted = 0
            converted = 0
            for info in zf.infolist():
                if info.is_dir():
                    continue
                member_name = Path(info.filename).name
                target_path = (archive_dir / member_name).resolve()
                with zf.open(info) as src, open(target_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                extracted += 1
                if target_path.suffix.lower() == ".rtf":
                    if not RTF_CONVERT_AVAILABLE:
                        return jsonify({
                            "success": False,
                            "error": "Конвертация RTF недоступна. Установите зависимости для convert_rtf_to_docx."
                        }), 500
                    try:
                        docx_path = convert_rtf_to_docx(target_path)
                        target_path.unlink(missing_ok=True)
                        if docx_path.exists():
                            converted += 1
                    except Exception as e:
                        return jsonify({
                            "success": False,
                            "error": f"Ошибка конвертации RTF файла {member_name}: {e}"
                        }), 500

        return jsonify({
            "success": True,
            "message": f"Архив распакован в папку {archive_stem}, файлов: {extracted}, RTF->DOCX: {converted}.",
            "archive": archive_stem,
        })

    @app.route("/process-archive", methods=["POST"])
    def process_archive():
        data = request.get_json(silent=True) or {}
        archive_name = data.get("archive") or last_archive.get("name")
        if not archive_name:
            return jsonify({"success": False, "error": "Архив не выбран."}), 400
        archive_dir = (_input_files_dir / archive_name).resolve()
        if not archive_dir.exists() or not archive_dir.is_dir():
            return jsonify({"success": False, "error": f"Папка архива не найдена: {archive_name}"}), 404
        with progress_lock:
            if progress_state.get("status") == "running":
                return jsonify({"success": False, "error": "Обработка уже выполняется."}), 409
            progress_state.update({
                "status": "running",
                "processed": 0,
                "total": 0,
                "message": "Подготовка...",
                "archive": archive_name
            })

        def worker():
            try:
                from services.gpt_extraction import extract_metadata_from_pdf
                from config import get_config
            except Exception as e:
                with progress_lock:
                    progress_state.update({
                        "status": "error",
                        "message": f"Не удалось запустить обработку: {e}"
                    })
                return
            try:
                config = None
                try:
                    config = get_config()
                except Exception:
                    config = None
                pdf_files = sorted(archive_dir.glob("*.pdf"))
                total = len(pdf_files)
                with progress_lock:
                    progress_state["total"] = total
                    progress_state["message"] = "Запуск обработки..."
                if total == 0:
                    with progress_lock:
                        progress_state.update({
                            "status": "error",
                            "message": "В архиве не найдено PDF файлов."
                        })
                    return
                for idx, pdf_path in enumerate(pdf_files, 1):
                    with progress_lock:
                        progress_state["processed"] = idx - 1
                        progress_state["message"] = f"Обработка: {pdf_path.name}"
                    extract_metadata_from_pdf(pdf_path, config=config)
                    with progress_lock:
                        progress_state["processed"] = idx
                with progress_lock:
                    progress_state.update({
                        "status": "done",
                        "message": "Обработка завершена."
                    })
            except Exception as e:
                with progress_lock:
                    progress_state.update({
                        "status": "error",
                        "message": f"Ошибка обработки: {e}"
                    })

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        return jsonify({"success": True})

    @app.route("/process-archive-status")
    def process_archive_status():
        with progress_lock:
            return jsonify({
                "status": progress_state.get("status"),
                "processed": progress_state.get("processed", 0),
                "total": progress_state.get("total", 0),
                "message": progress_state.get("message", ""),
                "archive": progress_state.get("archive") or last_archive.get("name")
            })

    @app.route("/finalize-archive", methods=["POST"])
    def finalize_archive():
        """Move processed folders to archive storage and clean old runs."""
        data = request.get_json(silent=True) or {}
        folders = data.get("folders") or []
        retention_days = data.get("retention_days")
        if isinstance(retention_days, (int, float)):
            retention_days = int(retention_days)
        else:
            retention_days = archive_retention_days
        if retention_days < 0:
            retention_days = archive_retention_days
        folder_names = _sanitize_folder_names(folders)
        if not folder_names:
            last_name = last_archive.get("name")
            if last_name:
                folder_names = [last_name]
        
        if not folder_names:
            return jsonify({"success": False, "error": "Не указаны папки для архивации."}), 400
        
        result = archive_processed_folders(
            folder_names=folder_names,
            archive_root_dir=archive_root_dir,
            input_files_dir=_input_files_dir,
            json_input_dir=json_input_dir,
            xml_output_dir=xml_output_dir
        )
        removed_old = cleanup_old_archives(archive_root_dir, retention_days)
        
        return jsonify({
            "success": True,
            "archive_dir": result.get("archive_dir"),
            "moved": result.get("moved", []),
            "removed_old": removed_old,
            "folders": folder_names
        })
    

