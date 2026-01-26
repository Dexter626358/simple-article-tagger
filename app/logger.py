from __future__ import annotations

import json
import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Any, Dict

from flask import Flask, g, request


def _summarize_request() -> Dict[str, Any]:
    info: Dict[str, Any] = {
        "method": request.method,
        "path": request.path,
        "ip": request.headers.get("X-Forwarded-For", request.remote_addr),
        "ua": request.headers.get("User-Agent"),
    }

    if request.args:
        info["query_keys"] = list(request.args.keys())

    if request.is_json:
        payload = request.get_json(silent=True)
        if isinstance(payload, dict):
            info["json_keys"] = list(payload.keys())
        elif isinstance(payload, list):
            info["json_items"] = len(payload)

    if request.form:
        info["form_keys"] = list(request.form.keys())

    if request.files:
        info["files"] = [
            {"field": k, "filename": f.filename}
            for k, f in list(request.files.items())[:5]
        ]

    return info


def _load_logging_config(base_dir: Path) -> Dict[str, Any]:
    cfg: Dict[str, Any] = {}
    config_path = base_dir / "config.json"
    if config_path.exists():
        try:
            cfg = json.loads(config_path.read_text(encoding="utf-8"))
        except Exception:
            cfg = {}
    return cfg.get("logging", {}) if isinstance(cfg, dict) else {}


def setup_logging(app: Flask, base_dir: Path) -> None:
    log_dir = base_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("word_parser")
    if logger.handlers:
        app.logger = logger
        return

    cfg = _load_logging_config(base_dir)

    level_name = str(
        cfg.get("level", app.config.get("LOG_LEVEL", "INFO"))
    ).upper()
    level = getattr(logging, level_name, logging.INFO)
    logger.setLevel(level)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    when = str(cfg.get("when", "midnight")).lower()
    interval = int(cfg.get("interval", 1))
    backup_count = int(cfg.get("backup_count", 14))
    use_utc = bool(cfg.get("utc", False))
    filename = cfg.get("filename", "app.log")

    file_handler = TimedRotatingFileHandler(
        log_dir / filename,
        when=when,
        interval=interval,
        backupCount=backup_count,
        encoding="utf-8",
        utc=use_utc,
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.propagate = False

    app.logger = logger

    @app.before_request
    def _log_request_start() -> None:
        g._req_start = None
        if request.path.startswith("/static/"):
            return
        g._req_start = __import__("time").time()
        app.logger.info("USER %s", _summarize_request())

    @app.after_request
    def _log_request_end(response):
        if request.path.startswith("/static/"):
            return response
        start = getattr(g, "_req_start", None)
        if start is not None:
            duration_ms = int((__import__("time").time() - start) * 1000)
            app.logger.info(
                "SYSTEM response status=%s ms=%s path=%s",
                response.status_code,
                duration_ms,
                request.path,
            )
        return response
