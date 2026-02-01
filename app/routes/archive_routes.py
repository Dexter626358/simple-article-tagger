from __future__ import annotations

import io
import os
import shutil
import subprocess
import sys
import threading
import zipfile
from pathlib import Path

from flask import jsonify, request

from app.app_dependencies import RTF_CONVERT_AVAILABLE, convert_rtf_to_docx
from app.app_helpers import (
    archive_processed_folders,
    cleanup_old_archives,
    list_archived_projects,
    restore_archived_project,
    _sanitize_folder_names,
    ensure_issue_dirs,
    save_issue_state,
    load_issue_state,
    list_current_projects,
)

def register_archive_routes(app, ctx):
    logger = app.logger
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

    def _get_latest_issue_dir() -> str | None:
        candidates = []
        base = _input_files_dir
        if not base or not base.exists() or not base.is_dir():
            return None
        for entry in base.iterdir():
            if entry.is_dir():
                try:
                    mtime = entry.stat().st_mtime
                except Exception:
                    mtime = 0
                candidates.append((mtime, entry.name))
        if not candidates:
            return None
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]

    @app.route("/open-json-input", methods=["GET", "POST"])
    def open_json_input():
        try:
            archive_name = last_archive.get("name")
            if archive_name:
                target_dir = (_input_files_dir / archive_name / "json").resolve()
            else:
                target_dir = _input_files_dir.resolve()
            target_dir.mkdir(parents=True, exist_ok=True)
            if sys.platform.startswith("win"):
                os.startfile(target_dir)  # type: ignore[attr-defined]
            elif sys.platform.startswith("darwin"):
                subprocess.Popen(["open", str(target_dir)])
            else:
                subprocess.Popen(["xdg-open", str(target_dir)])
        except Exception as exc:
            logger.exception("Failed to open project folder: %s", exc)
            return jsonify({"success": False, "error": "Не удалось открыть папку проекта."}), 500
        return jsonify({"success": True})

    @app.route("/upload-input-archive", methods=["POST"])
    def upload_input_archive():
        logger.info("USER upload archive start")
        if "archive" not in request.files:
            return jsonify({"success": False, "error": "Файл архива не найден в запросе."}), 400
        archive_file = request.files["archive"]
        if not archive_file or not archive_file.filename:
            return jsonify({"success": False, "error": "Файл архива не выбран."}), 400

        data = archive_file.read()
        if not data:
            return jsonify({"success": False, "error": "Файл архива пуст."}), 400
        logger.info(
            "SYSTEM upload archive received filename=%s size=%s",
            archive_file.filename,
            len(data),
        )

        buffer = io.BytesIO(data)
        if not zipfile.is_zipfile(buffer):
            return jsonify({"success": False, "error": "Загруженный файл не является ZIP архивом."}), 400

        buffer.seek(0)
        with zipfile.ZipFile(buffer) as zf:
            is_valid, bad_name = validate_zip_members(zf, _input_files_dir)
            if not is_valid:
                logger.warning("SYSTEM upload archive invalid structure bad_name=%s", bad_name)
                return jsonify({
                    "success": False,
                    "error": (
                        "Недопустимая структура архива. "
                        "Варианты: файлы в корне или в одной верхней папке (вложенные подпапки теперь допускаются). "
                        f"Проблемный элемент: {bad_name}"
                    )
                }), 400

            _input_files_dir.mkdir(parents=True, exist_ok=True)
            archive_stem = Path(archive_file.filename).stem.strip()
            if not archive_stem:
                return jsonify({"success": False, "error": "Не удалось определить имя архива."}), 400
            archive_dirs = ensure_issue_dirs(_input_files_dir, archive_stem)
            archive_dir = archive_dirs["issue_dir"].resolve()
            raw_dir = archive_dirs["raw_dir"]
            last_archive["name"] = archive_stem
            with progress_lock:
                progress_state.update({
                    "status": "idle",
                    "processed": 0,
                    "total": 0,
                    "message": "",
                    "archive": archive_stem
                })
            save_issue_state(
                _input_files_dir,
                archive_stem,
                {
                    "status": "uploaded",
                    "processed": 0,
                    "total": 0,
                    "message": "Архив распакован",
                    "archive": archive_stem,
                },
            )
            extracted = 0
            converted = 0
            for info in zf.infolist():
                if info.is_dir():
                    continue
                member_name = Path(info.filename).name
                target_path = (raw_dir / member_name).resolve()
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

        logger.info(
            "SYSTEM upload archive done name=%s extracted=%s converted=%s",
            archive_stem,
            extracted,
            converted,
        )
        save_issue_state(
            _input_files_dir,
            archive_stem,
            {
                "status": "uploaded",
                "processed": 0,
                "total": extracted,
                "message": "Архив распакован",
                "archive": archive_stem,
            },
        )
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
        logger.info("USER process archive start name=%s", archive_name)
        archive_dir = (_input_files_dir / archive_name).resolve()
        if not archive_dir.exists() or not archive_dir.is_dir():
            return jsonify({"success": False, "error": f"Папка архива не найдена: {archive_name}"}), 404
        raw_dir = archive_dir / "raw"
        json_dir = archive_dir / "json"
        if raw_dir.exists():
            pdf_root = raw_dir
        else:
            pdf_root = archive_dir
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
                pdf_files = sorted(pdf_root.glob("*.pdf"))
                total = len(pdf_files)
                logger.info(
                    "SYSTEM process archive files name=%s pdf_count=%s",
                    archive_name,
                    total,
                )
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
                    save_issue_state(
                        _input_files_dir,
                        archive_name,
                        {
                            "status": "running",
                            "processed": idx - 1,
                            "total": total,
                            "message": f"Обработка: {pdf_path.name}",
                            "archive": archive_name,
                        },
                    )
                    extract_metadata_from_pdf(pdf_path, config=config, json_output_dir=json_dir)
                    with progress_lock:
                        progress_state["processed"] = idx
                    save_issue_state(
                        _input_files_dir,
                        archive_name,
                        {
                            "status": "running",
                            "processed": idx,
                            "total": total,
                            "message": "Обработка в процессе",
                            "archive": archive_name,
                        },
                    )
                logger.info(
                    "SYSTEM process archive done name=%s processed=%s",
                    archive_name,
                    total,
                )
                with progress_lock:
                    progress_state.update({
                        "status": "done",
                        "message": "Обработка завершена."
                    })
                save_issue_state(
                    _input_files_dir,
                    archive_name,
                    {
                        "status": "done",
                        "processed": total,
                        "total": total,
                        "message": "Обработка завершена",
                        "archive": archive_name,
                    },
                )
            except Exception as e:
                with progress_lock:
                    progress_state.update({
                        "status": "error",
                        "message": f"Ошибка обработки: {e}"
                    })
                save_issue_state(
                    _input_files_dir,
                    archive_name,
                    {
                        "status": "error",
                        "message": f"Ошибка обработки: {e}",
                        "archive": archive_name,
                    },
                )

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        return jsonify({"success": True})

    @app.route("/process-archive-status")
    def process_archive_status():
        archive_name = None
        with progress_lock:
            archive_name = progress_state.get("archive") or last_archive.get("name")
        status_payload = {
            "status": progress_state.get("status"),
            "processed": progress_state.get("processed", 0),
            "total": progress_state.get("total", 0),
            "message": progress_state.get("message", ""),
            "archive": archive_name,
        }
        if archive_name:
            archive_dir = (_input_files_dir / archive_name).resolve()
            if archive_dir.exists() and archive_dir.is_dir():
                raw_dir = archive_dir / "raw"
                pdf_root = raw_dir if raw_dir.exists() else archive_dir
                pdf_files = list(pdf_root.glob("*.pdf"))
                extra_files = [
                    p for p in pdf_root.iterdir()
                    if p.is_file() and p.suffix.lower() != ".pdf"
                ]
                status_payload["pdf_count"] = len(pdf_files)
                status_payload["extra_count"] = len(extra_files)
                if status_payload["status"] in (None, "idle"):
                    state = load_issue_state(_input_files_dir, archive_name)
                    if state:
                        status_payload["status"] = state.get("status") or status_payload["status"]
                        status_payload["processed"] = state.get("processed", status_payload["processed"])
                        status_payload["total"] = state.get("total", status_payload["total"])
                        status_payload["message"] = state.get("message", status_payload["message"])
        return jsonify(status_payload)

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
        )
        removed_old = cleanup_old_archives(archive_root_dir, retention_days)

        # Reset current archive state so UI can start a new issue
        last_archive["name"] = None
        if progress_state is not None:
            with progress_lock:
                progress_state["status"] = "idle"
                progress_state["processed"] = 0
                progress_state["total"] = 0
                progress_state["message"] = ""
                progress_state["archive"] = None
        
        return jsonify({
            "success": True,
            "archive_dir": result.get("archive_dir"),
            "moved": result.get("moved", []),
            "removed_old": removed_old,
            "folders": folder_names
        })
    

    @app.route("/project-save", methods=["POST"])
    def project_save():
        data = request.get_json(silent=True) or {}
        issue = (data.get("issue") or last_archive.get("name") or "").strip()
        if not issue:
            return jsonify({"success": False, "error": "Не указан выпуск."}), 400
        issue_names = _sanitize_folder_names([issue])
        if not issue_names:
            return jsonify({"success": False, "error": "Недопустимое имя выпуска."}), 400
        result = archive_processed_folders(
            folder_names=issue_names,
            archive_root_dir=archive_root_dir,
            input_files_dir=_input_files_dir,
        )
        # Reset current archive state so UI can start a new issue
        last_archive["name"] = None
        if progress_state is not None:
            with progress_lock:
                progress_state["status"] = "idle"
                progress_state["processed"] = 0
                progress_state["total"] = 0
                progress_state["message"] = ""
                progress_state["archive"] = None
        return jsonify({
            "success": True,
            "archive_dir": result.get("archive_dir"),
            "moved": result.get("moved", []),
            "issue": issue_names[0],
        })

    @app.route("/project-snapshots")
    def project_snapshots():
        current_issues = list_current_projects(_input_files_dir)
        snapshots = list_archived_projects(archive_root_dir)
        if current_issues:
            snapshots.insert(0, {"run": "current", "issues": current_issues})
        return jsonify({
            "success": True,
            "snapshots": snapshots,
        })

    @app.route("/project-restore", methods=["POST"])
    def project_restore():
        data = request.get_json(silent=True) or {}
        run_name = (data.get("run") or "").strip()
        issue = (data.get("issue") or "").strip()
        overwrite = bool(data.get("overwrite", False))
        if not run_name or not issue:
            return jsonify({"success": False, "error": "Не указан архив и выпуск."}), 400
        run_names = _sanitize_folder_names([run_name])
        issue_names = _sanitize_folder_names([issue])
        if not run_names or not issue_names:
            return jsonify({"success": False, "error": "Недопустимое имя архива или выпуска."}), 400
        if run_names[0] == "current":
            last_archive["name"] = issue_names[0]
            return jsonify({"success": True, "moved": [], "issue": issue_names[0]})
        result = restore_archived_project(
            archive_root_dir=archive_root_dir,
            run_name=run_names[0],
            issue_name=issue_names[0],
            input_files_dir=_input_files_dir,
            overwrite=overwrite,
        )
        status = 200 if result.get("success") else 400
        return jsonify(result), status

    @app.route("/project-delete", methods=["POST"])
    def project_delete():
        data = request.get_json(silent=True) or {}
        issue = (data.get("issue") or last_archive.get("name") or "").strip()
        if not issue:
            return jsonify({"success": False, "error": "Не указан выпуск."}), 400
        issue_names = _sanitize_folder_names([issue])
        if not issue_names:
            return jsonify({"success": False, "error": "Недопустимое имя выпуска."}), 400
        issue_name = issue_names[0]

        removed = []
        base_dir = _input_files_dir
        target = (base_dir / issue_name).resolve()
        try:
            target.resolve().relative_to(base_dir.resolve())
        except ValueError:
            target = None
        if target and target.exists() and target.is_dir():
            shutil.rmtree(target)
            removed.append(f"input_files/{issue_name}")

        if not removed:
            return jsonify({"success": False, "error": f"Выпуск не найден: {issue_name}"}), 404

        if last_archive.get("name") == issue_name:
            last_archive["name"] = None
        logger.info("SYSTEM project delete issue=%s removed=%s", issue_name, len(removed))
        return jsonify({"success": True, "issue": issue_name, "removed": removed})
