# Railway deploy

## Quick start
1. Push this repo to GitHub.
2. Create a new Railway project from the repo.
3. Set service start command (if needed) to:

   gunicorn wsgi:app --bind 0.0.0.0:$PORT

Railway will use `requirements.txt` and install `gunicorn`.

## Python version (Railpack / mise)

The repo pins **Python 3.12.8** via `.python-version` and `runtime.txt`. Without this, Railpack may default to a very new Python (for example 3.13.x); if the corresponding prebuilt binary is missing from [python-build-standalone](https://github.com/astral-sh/python-build-standalone/releases), the build fails with HTTP 404 during `mise install`. You can override with the Railway variable `RAILPACK_PYTHON_VERSION` (for example `3.12`).

## Optional env vars
- `JSON_INPUT_DIR`
- `WORDS_INPUT_DIR`
- `XML_OUTPUT_DIR`
- `LIST_OF_JOURNALS_PATH`
- `INPUT_FILES_DIR`

Defaults are folders inside the project root.
