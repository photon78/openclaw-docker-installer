"""
logging_setup.py — Installer-wide logging.
Writes to ~/.openclaw/logs/installer.log (rotating, max 1 MB, 3 backups).
Also mirrors INFO+ to stdout via Rich for interactive runs.
"""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from rich.logging import RichHandler

_log_file: Path | None = None


def setup(openclaw_dir: Path | None = None) -> Path:
    """Initialize logging. Call once at startup.

    Args:
        openclaw_dir: Path to ~/.openclaw (or equivalent). Defaults to Path.home() / ".openclaw".

    Returns:
        Path to the log file.
    """
    global _log_file

    base = openclaw_dir or (Path.home() / ".openclaw")
    logs_dir = base / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    log_file = logs_dir / "installer.log"
    _log_file = log_file

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # Rotating file handler — max 1 MB, keeps 3 backups (installer.log, .1, .2, .3)
    fh = RotatingFileHandler(
        log_file,
        maxBytes=1 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        "[%(asctime)s] %(levelname)-8s %(name)s — %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    ))
    root.addHandler(fh)

    # Rich handler — INFO+ to stdout (pretty, no noise)
    # markup=False: prevents Rich from swallowing the leading 'I' in 'INFO'
    # (Rich treats [INFO] as a markup tag, displaying 'NFO' instead)
    rh = RichHandler(
        level=logging.INFO,
        show_time=False,
        show_path=False,
        rich_tracebacks=True,
        markup=False,
    )
    root.addHandler(rh)

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("docker").setLevel(logging.WARNING)

    logging.info("openclaw-installer started — log: %s", log_file)
    return log_file


def get_log_file() -> Path | None:
    return _log_file
