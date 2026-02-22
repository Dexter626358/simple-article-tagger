from __future__ import annotations

import secrets
from pathlib import Path

from flask import session

SESSION_ID_KEY = "session_id"
CURRENT_ARCHIVE_KEY = "current_archive"


def get_session_id() -> str:
    session_id = session.get(SESSION_ID_KEY)
    if not session_id:
        session_id = secrets.token_urlsafe(16)
        session[SESSION_ID_KEY] = session_id
    return session_id


def get_session_input_dir(base_input_dir: Path) -> Path:
    session_id = get_session_id()
    return base_input_dir / "_sessions" / session_id


def get_session_archive_root(base_archive_root: Path) -> Path:
    session_id = get_session_id()
    return base_archive_root / session_id


def get_current_archive() -> str:
    return str(session.get(CURRENT_ARCHIVE_KEY) or "").strip()


def set_current_archive(name: str | None) -> None:
    if name:
        session[CURRENT_ARCHIVE_KEY] = name
    else:
        session.pop(CURRENT_ARCHIVE_KEY, None)
