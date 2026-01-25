# Railway deploy

## Quick start
1. Push this repo to GitHub.
2. Create a new Railway project from the repo.
3. Set service start command (if needed) to:

   gunicorn wsgi:app --bind 0.0.0.0:$PORT

Railway will use `requirements.txt` and install `gunicorn`.

## Optional env vars
- `JSON_INPUT_DIR`
- `WORDS_INPUT_DIR`
- `XML_OUTPUT_DIR`
- `LIST_OF_JOURNALS_PATH`
- `INPUT_FILES_DIR`

Defaults are folders inside the project root.
