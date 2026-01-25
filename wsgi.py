from __future__ import annotations

import os
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _load_create_app() -> callable:
    base_dir = Path(__file__).parent.resolve()
    app_path = base_dir / "app.py"
    spec = spec_from_file_location("app_main", app_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load app.py for create_app")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "create_app"):
        raise RuntimeError("create_app not found in app.py")
    return module.create_app


base_dir = Path(__file__).parent.resolve()
json_input_dir = Path(os.getenv("JSON_INPUT_DIR", str(base_dir / "json_input")))
words_input_dir = Path(os.getenv("WORDS_INPUT_DIR", str(base_dir / "words_input")))
xml_output_dir = Path(os.getenv("XML_OUTPUT_DIR", str(base_dir / "xml_output")))
list_of_journals_path = Path(os.getenv("LIST_OF_JOURNALS_PATH", str(base_dir / "data" / "list_of_journals.json")))
input_files_dir = Path(os.getenv("INPUT_FILES_DIR", str(base_dir / "input_files")))

create_app = _load_create_app()
app = create_app(
    json_input_dir=json_input_dir,
    words_input_dir=words_input_dir,
    use_word_reader=False,
    xml_output_dir=xml_output_dir,
    list_of_journals_path=list_of_journals_path,
    input_files_dir=input_files_dir,
)
