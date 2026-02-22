from __future__ import annotations

from flask import render_template_string

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
        return render_template_string(HTML_TEMPLATE, files=files)
    

