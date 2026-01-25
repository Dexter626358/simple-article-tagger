from __future__ import annotations

import os
from pathlib import Path

from app import create_app


def _resolve_base() -> Path:
    return Path(__file__).parent.resolve()


base_dir = _resolve_base()
json_input_dir = Path(os.getenv("JSON_INPUT_DIR", str(base_dir / "json_input")))
words_input_dir = Path(os.getenv("WORDS_INPUT_DIR", str(base_dir / "words_input")))
xml_output_dir = Path(os.getenv("XML_OUTPUT_DIR", str(base_dir / "xml_output")))
list_of_journals_path = Path(os.getenv("LIST_OF_JOURNALS_PATH", str(base_dir / "data" / "list_of_journals.json")))
input_files_dir = Path(os.getenv("INPUT_FILES_DIR", str(base_dir / "input_files")))

app = create_app(
    json_input_dir=json_input_dir,
    words_input_dir=words_input_dir,
    use_word_reader=False,
    xml_output_dir=xml_output_dir,
    list_of_journals_path=list_of_journals_path,
    input_files_dir=input_files_dir,
)
