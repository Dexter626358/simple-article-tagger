from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import sys
import threading
import zipfile
from pathlib import Path

from flask import jsonify, request, send_file

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
from app.session_utils import (
    get_current_archive,
    get_session_archive_root,
    get_session_id,
    get_session_input_dir,
    set_current_archive,
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
    progress_states = ctx.get("progress_states")
    progress_locks = ctx.get("progress_locks")
    progress_global_lock = ctx.get("progress_global_lock")

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

    def _get_progress_lock(session_id: str) -> threading.Lock:
        with progress_global_lock:
            lock = progress_locks.get(session_id)
            if not lock:
                lock = threading.Lock()
                progress_locks[session_id] = lock
            return lock
    validate_zip_members = ctx.get("validate_zip_members")
    find_files_for_json = ctx.get("find_files_for_json")
    SUPPORTED_EXTENSIONS = ctx.get("SUPPORTED_EXTENSIONS")
    SUPPORTED_JSON_EXTENSIONS = ctx.get("SUPPORTED_JSON_EXTENSIONS")

    def _config_path() -> Path:
        return Path(__file__).resolve().parents[2] / "config.json"

    def _load_config() -> dict:
        path = _config_path()
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save_config(config: dict) -> None:
        path = _config_path()
        path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    def _get_latest_issue_dir(base: Path) -> str | None:
        candidates = []
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
            session_input_dir = get_session_input_dir(_input_files_dir)
            archive_name = get_current_archive()
            if archive_name:
                target_dir = (session_input_dir / archive_name / "json").resolve()
            else:
                target_dir = session_input_dir.resolve()
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

    @app.route("/settings-get")
    def settings_get():
        config = _load_config()
        gpt_cfg = (config.get("gpt_extraction") or {}) if isinstance(config, dict) else {}
        pdf_cfg = (config.get("pdf_reader") or {}) if isinstance(config, dict) else {}
        return jsonify({
            "success": True,
            "gpt_extraction": {
                "model": gpt_cfg.get("model", "gpt-4.1-mini"),
                "extract_abstracts": bool(gpt_cfg.get("extract_abstracts", True)),
                "extract_references": bool(gpt_cfg.get("extract_references", True)),
            },
            "pdf_reader": {
                "first_pages": int(pdf_cfg.get("first_pages", 3) or 0),
                "last_pages": int(pdf_cfg.get("last_pages", 3) or 0),
                "extract_all_pages": bool(pdf_cfg.get("extract_all_pages", True)),
            }
        })

    @app.route("/settings-save", methods=["POST"])
    def settings_save():
        data = request.get_json(silent=True) or {}
        gpt_cfg = data.get("gpt_extraction") or {}
        pdf_cfg = data.get("pdf_reader") or {}
        model = str(gpt_cfg.get("model", "")).strip()
        extract_abstracts = bool(gpt_cfg.get("extract_abstracts", False))
        extract_references = bool(gpt_cfg.get("extract_references", False))
        first_pages = pdf_cfg.get("first_pages", 3)
        last_pages = pdf_cfg.get("last_pages", 3)
        extract_all_pages = bool(pdf_cfg.get("extract_all_pages", False))
        if not model:
            return jsonify({"success": False, "error": "Модель не указана."}), 400
        try:
            first_pages = max(0, int(first_pages))
            last_pages = max(0, int(last_pages))
        except (TypeError, ValueError):
            return jsonify({"success": False, "error": "Некорректные значения страниц."}), 400

        config = _load_config()
        if not isinstance(config, dict):
            config = {}
        if not isinstance(config.get("gpt_extraction"), dict):
            config["gpt_extraction"] = {}
        config["gpt_extraction"]["model"] = model
        config["gpt_extraction"]["extract_abstracts"] = extract_abstracts
        config["gpt_extraction"]["extract_references"] = extract_references
        if not isinstance(config.get("pdf_reader"), dict):
            config["pdf_reader"] = {}
        config["pdf_reader"]["first_pages"] = first_pages
        config["pdf_reader"]["last_pages"] = last_pages
        config["pdf_reader"]["extract_all_pages"] = extract_all_pages
        _save_config(config)

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
            session_input_dir = get_session_input_dir(_input_files_dir)
            is_valid, bad_name = validate_zip_members(zf, session_input_dir)
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

            session_input_dir.mkdir(parents=True, exist_ok=True)
            archive_stem = Path(archive_file.filename).stem.strip()
            if not archive_stem:
                return jsonify({"success": False, "error": "Не удалось определить имя архива."}), 400
            archive_dirs = ensure_issue_dirs(session_input_dir, archive_stem)
            archive_dir = archive_dirs["issue_dir"].resolve()
            raw_dir = archive_dirs["raw_dir"]
            set_current_archive(archive_stem)
            session_id = get_session_id()
            progress_state = _get_progress_state(session_id)
            progress_lock = _get_progress_lock(session_id)
            with progress_lock:
                progress_state.update({
                    "status": "idle",
                    "processed": 0,
                    "total": 0,
                    "message": "",
                    "archive": archive_stem
                })
            save_issue_state(
                session_input_dir,
                archive_stem,
                {
                    "status": "uploaded",
                    "processed": 0,
                    "total": 0,
                    "message": "",
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
                "message": "",
                "archive": archive_stem,
            },
        )
        return jsonify({
            "success": True,
            "message": "Архив загружен.",
            "archive": archive_stem,
        })

    @app.route("/process-archive", methods=["POST"])
    def process_archive():
        data = request.get_json(silent=True) or {}
        session_id = get_session_id()
        session_input_dir = get_session_input_dir(_input_files_dir)
        archive_name = data.get("archive") or get_current_archive()
        if not archive_name:
            return jsonify({"success": False, "error": "Архив не выбран."}), 400
        logger.info("USER process archive start name=%s", archive_name)
        archive_dir = (session_input_dir / archive_name).resolve()
        if not archive_dir.exists() or not archive_dir.is_dir():
            # Fallback for session drift between upload and process request.
            sessions_root = (_input_files_dir / "_sessions").resolve()
            recovered_from = None
            if sessions_root.exists() and sessions_root.is_dir():
                for candidate in sessions_root.glob(f"*/{archive_name}"):
                    if candidate.is_dir():
                        recovered_from = candidate.resolve()
                        break
            if recovered_from:
                try:
                    session_input_dir.mkdir(parents=True, exist_ok=True)
                    restored_dir = (session_input_dir / archive_name).resolve()
                    if restored_dir.exists():
                        shutil.rmtree(restored_dir, ignore_errors=True)
                    shutil.copytree(recovered_from, restored_dir)
                    archive_dir = restored_dir
                    logger.warning(
                        "SYSTEM process archive recovered name=%s from=%s to_session=%s",
                        archive_name,
                        recovered_from,
                        session_id,
                    )
                except Exception:
                    return jsonify({"success": False, "error": f"Папка архива не найдена: {archive_name}"}), 404
            else:
                return jsonify({"success": False, "error": f"Папка архива не найдена: {archive_name}"}), 404
        raw_dir = archive_dir / "raw"
        json_dir = archive_dir / "json"
        if raw_dir.exists():
            pdf_root = raw_dir
        else:
            pdf_root = archive_dir
        # Preflight checks for AI processing in production.
        # Fail fast here instead of starting background thread and failing silently later.
        try:
            from config import get_config
            from services.gpt_extraction import OPENAI_AVAILABLE
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Не удалось инициализировать модуль ИИ: {e}",
            }), 500
        if not OPENAI_AVAILABLE:
            return jsonify({
                "success": False,
                "error": "Пакет openai не установлен на сервере. Установите зависимость и перезапустите сервис.",
            }), 500
        config = None
        try:
            config = get_config()
        except Exception:
            config = None
        if config and not config.get("gpt_extraction.enabled", True):
            return jsonify({
                "success": False,
                "error": "ИИ-обработка отключена в конфигурации (gpt_extraction.enabled=false).",
            }), 400
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key and config:
            api_key = (config.get("gpt_extraction.api_key", "") or "").strip()
        if not api_key:
            return jsonify({
                "success": False,
                "error": "Не настроен OPENAI_API_KEY на сервере (или пустой gpt_extraction.api_key).",
            }), 400
        set_current_archive(archive_name)
        progress_state = _get_progress_state(session_id)
        progress_lock = _get_progress_lock(session_id)
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
                        session_input_dir,
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
                        session_input_dir,
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
                    session_input_dir,
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
                    session_input_dir,
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
        session_id = get_session_id()
        session_input_dir = get_session_input_dir(_input_files_dir)
        progress_state = _get_progress_state(session_id)
        progress_lock = _get_progress_lock(session_id)
        archive_name = None
        with progress_lock:
            archive_name = progress_state.get("archive") or get_current_archive()
        status_payload = {
            "status": progress_state.get("status"),
            "processed": progress_state.get("processed", 0),
            "total": progress_state.get("total", 0),
            "message": progress_state.get("message", ""),
            "archive": archive_name,
        }
        if archive_name:
            archive_dir = (session_input_dir / archive_name).resolve()
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
                    state = load_issue_state(session_input_dir, archive_name)
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
        session_id = get_session_id()
        session_input_dir = get_session_input_dir(_input_files_dir)
        session_archive_root = get_session_archive_root(archive_root_dir)
        progress_state = _get_progress_state(session_id)
        progress_lock = _get_progress_lock(session_id)
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
            last_name = get_current_archive()
            if last_name:
                folder_names = [last_name]
        
        if not folder_names:
            return jsonify({"success": False, "error": "Не указаны папки для архивации."}), 400
        
        result = archive_processed_folders(
            folder_names=folder_names,
            archive_root_dir=session_archive_root,
            input_files_dir=session_input_dir,
        )
        removed_old = cleanup_old_archives(session_archive_root, retention_days)

        # Reset current archive state so UI can start a new issue
        set_current_archive(None)
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
        session_id = get_session_id()
        session_input_dir = get_session_input_dir(_input_files_dir)
        session_archive_root = get_session_archive_root(archive_root_dir)
        progress_state = _get_progress_state(session_id)
        progress_lock = _get_progress_lock(session_id)
        issue = (data.get("issue") or get_current_archive() or "").strip()
        if not issue:
            return jsonify({"success": False, "error": "Не указан выпуск."}), 400
        issue_names = _sanitize_folder_names([issue])
        if not issue_names:
            return jsonify({"success": False, "error": "Недопустимое имя выпуска."}), 400
        result = archive_processed_folders(
            folder_names=issue_names,
            archive_root_dir=session_archive_root,
            input_files_dir=session_input_dir,
        )
        # Reset current archive state so UI can start a new issue
        set_current_archive(None)
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
        session_input_dir = get_session_input_dir(_input_files_dir)
        session_archive_root = get_session_archive_root(archive_root_dir)
        current_issues = list_current_projects(session_input_dir)
        snapshots = list_archived_projects(session_archive_root)
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
        session_input_dir = get_session_input_dir(_input_files_dir)
        session_archive_root = get_session_archive_root(archive_root_dir)
        run_names = _sanitize_folder_names([run_name])
        issue_names = _sanitize_folder_names([issue])
        if not run_names or not issue_names:
            return jsonify({"success": False, "error": "Недопустимое имя архива или выпуска."}), 400
        if run_names[0] == "current":
            set_current_archive(issue_names[0])
            return jsonify({"success": True, "moved": [], "issue": issue_names[0]})
        result = restore_archived_project(
            archive_root_dir=session_archive_root,
            run_name=run_names[0],
            issue_name=issue_names[0],
            input_files_dir=session_input_dir,
            overwrite=overwrite,
        )
        status = 200 if result.get("success") else 400
        return jsonify(result), status

    @app.route("/project-delete", methods=["POST"])
    def project_delete():
        data = request.get_json(silent=True) or {}
        session_input_dir = get_session_input_dir(_input_files_dir)
        issue = (data.get("issue") or get_current_archive() or "").strip()
        if not issue:
            return jsonify({"success": False, "error": "Не указан выпуск."}), 400
        issue_names = _sanitize_folder_names([issue])
        if not issue_names:
            return jsonify({"success": False, "error": "Недопустимое имя выпуска."}), 400
        issue_name = issue_names[0]

        removed = []
        base_dir = session_input_dir
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

        if get_current_archive() == issue_name:
            set_current_archive(None)
        logger.info("SYSTEM project delete issue=%s removed=%s", issue_name, len(removed))
        return jsonify({"success": True, "issue": issue_name, "removed": removed})

    @app.route("/session-reset", methods=["POST"])
    def session_reset():
        session_id = get_session_id()
        session_input_dir = get_session_input_dir(_input_files_dir)
        progress_state = _get_progress_state(session_id)
        progress_lock = _get_progress_lock(session_id)

        removed = []
        if session_input_dir.exists() and session_input_dir.is_dir():
            for child in session_input_dir.iterdir():
                try:
                    if child.is_dir():
                        shutil.rmtree(child)
                    else:
                        child.unlink()
                    removed.append(child.name)
                except Exception as exc:
                    logger.warning("SYSTEM session reset failed remove=%s err=%s", child, exc)

        set_current_archive(None)
        with progress_lock:
            progress_state["status"] = "idle"
            progress_state["processed"] = 0
            progress_state["total"] = 0
            progress_state["message"] = ""
            progress_state["archive"] = None

        logger.info("SYSTEM session reset session=%s removed=%s", session_id, len(removed))
        return jsonify({"success": True, "removed": removed})

    @app.route("/project-download", methods=["GET"])
    def project_download():
        session_input_dir = get_session_input_dir(_input_files_dir)
        issue = (request.args.get("issue") or get_current_archive() or "").strip()
        if not issue:
            return jsonify({"success": False, "error": "Не указан выпуск."}), 400
        issue_names = _sanitize_folder_names([issue])
        if not issue_names:
            return jsonify({"success": False, "error": "Недопустимое имя выпуска."}), 400
        issue_name = issue_names[0]
        issue_dir = (session_input_dir / issue_name).resolve()
        try:
            issue_dir.relative_to(session_input_dir.resolve())
        except ValueError:
            return jsonify({"success": False, "error": "Недопустимый путь выпуска."}), 400
        if not issue_dir.exists() or not issue_dir.is_dir():
            return jsonify({"success": False, "error": f"Выпуск не найден: {issue_name}"}), 404

        archive_buffer = io.BytesIO()
        with zipfile.ZipFile(archive_buffer, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for path in issue_dir.rglob("*"):
                if not path.is_file():
                    continue
                rel = path.relative_to(session_input_dir)
                zf.write(path, arcname=str(rel).replace("\\", "/"))

        archive_buffer.seek(0)
        filename = f"{issue_name}_project.zip"
        logger.info("SYSTEM project download issue=%s", issue_name)
        return send_file(
            archive_buffer,
            mimetype="application/zip",
            as_attachment=True,
            download_name=filename,
        )

    @app.route("/project-upload-archive", methods=["POST"])
    def project_upload_archive():
        session_input_dir = get_session_input_dir(_input_files_dir)
        archive_file = request.files.get("archive")
        if not archive_file or not archive_file.filename:
            return jsonify({"success": False, "error": "Файл архива не выбран."}), 400

        overwrite_raw = (request.form.get("overwrite") or "").strip().lower()
        overwrite = overwrite_raw in {"1", "true", "yes", "on"}
        data = archive_file.read()
        if not data:
            return jsonify({"success": False, "error": "Файл архива пуст."}), 400

        buffer = io.BytesIO(data)
        if not zipfile.is_zipfile(buffer):
            return jsonify({"success": False, "error": "Загруженный файл не является ZIP архивом."}), 400

        buffer.seek(0)
        with zipfile.ZipFile(buffer) as zf:
            names = [n for n in zf.namelist() if n and not n.endswith("/")]
            if not names:
                return jsonify({"success": False, "error": "Архив не содержит файлов."}), 400

            top_folders = sorted({Path(n).parts[0] for n in names if Path(n).parts})
            if len(top_folders) != 1:
                return jsonify({
                    "success": False,
                    "error": "Архив проекта должен содержать одну верхнюю папку выпуска.",
                }), 400

            issue_name_raw = top_folders[0]
            issue_names = _sanitize_folder_names([issue_name_raw])
            if not issue_names:
                return jsonify({"success": False, "error": "Недопустимое имя выпуска в архиве."}), 400
            issue_name = issue_names[0]

            issue_dir = (session_input_dir / issue_name).resolve()
            try:
                issue_dir.relative_to(session_input_dir.resolve())
            except ValueError:
                return jsonify({"success": False, "error": "Недопустимый путь выпуска в архиве."}), 400

            if issue_dir.exists():
                if not overwrite:
                    return jsonify({
                        "success": False,
                        "code": "dest_exists",
                        "issue": issue_name,
                        "error": f"Выпуск уже существует: {issue_name}",
                    }), 409
                shutil.rmtree(issue_dir)

            extracted = 0
            for info in zf.infolist():
                if info.is_dir():
                    continue
                rel = Path(info.filename)
                if not rel.parts:
                    continue
                if rel.parts[0] != issue_name_raw:
                    continue
                if any(part in {"..", ""} for part in rel.parts):
                    return jsonify({"success": False, "error": "Недопустимая структура архива."}), 400
                target_path = (session_input_dir / Path(*rel.parts)).resolve()
                try:
                    target_path.relative_to(session_input_dir.resolve())
                except ValueError:
                    return jsonify({"success": False, "error": "Недопустимый путь в архиве."}), 400
                target_path.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(info) as src, open(target_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                extracted += 1

        set_current_archive(issue_name)
        session_id = get_session_id()
        progress_state = _get_progress_state(session_id)
        progress_lock = _get_progress_lock(session_id)
        with progress_lock:
            progress_state["status"] = "idle"
            progress_state["processed"] = 0
            progress_state["total"] = 0
            progress_state["message"] = ""
            progress_state["archive"] = issue_name

        logger.info("SYSTEM project upload archive issue=%s extracted=%s", issue_name, extracted)
        return jsonify({
            "success": True,
            "issue": issue_name,
            "archive": issue_name,
            "extracted": extracted,
        })
