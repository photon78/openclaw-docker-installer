"""
logging_setup.py — Installer-wide logging.
Writes to ~/.openclaw/logs/install-YYYY-MM-DD.log
Also mirrors to stdout via Rich for interactive runs.
"""
from __future__ import annotations

import logging
import sys
from datetime import datetime
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

    date_str = datetime.now().strftime("%Y-%m-%d")
    log_file = logs_dir / f"install-{date_str}.log"
    _log_file = log_file

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # File handler — full debug output
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        "[%(asctime)s] %(levelname)-8s %(name)s — %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    ))
    root.addHandler(fh)

    # Rich handler — INFO+ to stdout (pretty, no noise)
    rh = RichHandler(
        level=logging.INFO,
        show_time=False,
        show_path=False,
        rich_tracebacks=True,
    )
    root.addHandler(rh)

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("docker").setLevel(logging.WARNING)

    logging.info("openclaw-installer started — log: %s", log_file)
    return log_file


def get_log_file() -> Path | None:
    return _log_file
