from __future__ import annotations

from pathlib import Path

from flask import abort, jsonify, render_template_string, request

from app.app_helpers import get_json_files
from app.session_utils import get_current_archive, get_session_input_dir
from app.web_templates import HTML_TEMPLATE

def register_index_routes(app, ctx):
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

    @app.route("/")


    def index():
        """Главная страница со списком JSON файлов."""
        session_input_dir = get_session_input_dir(_input_files_dir)
        files = get_json_files(session_input_dir)
        issue_name = get_current_archive()
        if issue_name:
            files = [f for f in files if f.get("issue_name") == issue_name]
        else:
            files = []
        return render_template_string(
            HTML_TEMPLATE,
            files=files,
            issue_name=issue_name,
        )

    @app.route("/delete-json-file", methods=["POST"])
    def delete_json_file():
        """
        Удаляет JSON статьи и связанные файлы (raw/xml) внутри текущего выпуска.

        Ожидает JSON:
          { "json_filename": "<issue>/json/<name>.json" }
        """
        issue_name = get_current_archive()
        if not issue_name:
            return jsonify({"success": False, "error": "Выпуск не выбран."}), 400

        payload = request.get_json(silent=True) or {}
        json_filename = str(payload.get("json_filename") or "").strip()
        if not json_filename:
            return jsonify({"success": False, "error": "Не указан json_filename."}), 400
        if ".." in json_filename or json_filename.startswith(("/", "\\")):
            abort(404)

        session_input_dir = get_session_input_dir(_input_files_dir)
        json_path = (session_input_dir / json_filename).resolve()
        try:
            json_path.relative_to(session_input_dir.resolve())
        except ValueError:
            abort(404)

        if json_path.suffix.lower() != ".json":
            abort(404)
        if json_path.parent.name != "json":
            abort(404)
        if json_path.parent.parent.name != issue_name:
            # Жёстко ограничиваем удаление текущим выбранным выпуском.
            return jsonify({"success": False, "error": "Файл не относится к выбранному выпуску."}), 400
        if not json_path.exists() or not json_path.is_file():
            return jsonify({"success": False, "error": "JSON файл не найден."}), 404

        issue_dir = json_path.parent.parent
        raw_dir = (issue_dir / "raw") if (issue_dir / "raw").exists() else issue_dir
        xml_dir = issue_dir / "xml"
        stem = json_path.stem

        deleted: list[str] = []
        errors: list[str] = []

        def _try_delete(path: Path) -> None:
            try:
                if path.exists() and path.is_file():
                    path.unlink()
                    deleted.append(str(path.relative_to(session_input_dir)).replace("\\", "/"))
            except Exception as exc:
                errors.append(f"{path.name}: {exc}")

        # 1) JSON
        _try_delete(json_path)

        # 2) Связанные файлы в raw/: <stem>.<ext> (pdf/doc/docx/rtf/idml/html/tex и т.д.)
        if raw_dir.exists() and raw_dir.is_dir():
            for p in raw_dir.iterdir():
                try:
                    if p.is_file() and p.stem == stem:
                        _try_delete(p)
                except Exception:
                    continue

        # 3) Связанные файлы в xml/: <stem>.<ext>
        if xml_dir.exists() and xml_dir.is_dir():
            for p in xml_dir.iterdir():
                try:
                    if p.is_file() and p.stem == stem:
                        _try_delete(p)
                except Exception:
                    continue

        resp = {"success": True, "deleted": deleted}
        if errors:
            resp["warnings"] = errors
        return jsonify(resp)
    

