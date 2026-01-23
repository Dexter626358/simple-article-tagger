from __future__ import annotations

import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def _load_app_module():
    app_path = ROOT_DIR / "app.py"
    spec = spec_from_file_location("app_main", app_path)
    assert spec and spec.loader
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def app_context(tmp_path: Path):
    module = _load_app_module()
    json_input_dir = tmp_path / "json_input"
    words_input_dir = tmp_path / "words_input"
    xml_output_dir = tmp_path / "xml_output"
    input_files_dir = tmp_path / "input_files"
    for path in (json_input_dir, words_input_dir, xml_output_dir, input_files_dir):
        path.mkdir(parents=True, exist_ok=True)
    app = module.create_app(
        json_input_dir=json_input_dir,
        words_input_dir=words_input_dir,
        xml_output_dir=xml_output_dir,
        input_files_dir=input_files_dir,
    )
    app.config.update(TESTING=True)
    return {
        "client": app.test_client(),
        "tmp_path": tmp_path,
        "input_files_dir": input_files_dir,
    }
