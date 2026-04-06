"""
python_check.py — Checks if Python 3.11+ is available on the current system.

Relevant mainly on Windows where Python is not pre-installed.
On Linux/macOS this check is usually a no-op (Python ships with the OS or distro).
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass

PYTHON_INSTALL_URL = "https://www.python.org/downloads/"
MIN_PYTHON_VERSION = (3, 11)

# Candidate executable names — order matters
PYTHON_CANDIDATES = ["python3", "python"]


@dataclass
class PythonStatus:
    """Result of a Python availability check."""
    installed: bool
    version: str | None = None
    version_ok: bool = False
    executable: str | None = None
    error: str | None = None

    @property
    def ready(self) -> bool:
        return self.installed and self.version_ok


def check_python() -> PythonStatus:
    """Check if Python 3.11+ is available.

    First checks the currently running interpreter (works when the installer
    is launched via a venv or explicit python3 call). Falls back to PATH lookup.
    """
    # Running interpreter first — most reliable
    current = sys.version_info
    if current >= MIN_PYTHON_VERSION:
        return PythonStatus(
            installed=True,
            version=f"{current.major}.{current.minor}.{current.micro}",
            version_ok=True,
            executable=sys.executable,
        )

    # Try candidates from PATH
    for candidate in PYTHON_CANDIDATES:
        executable = shutil.which(candidate)
        if not executable:
            continue
        try:
            result = subprocess.run(
                [executable, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            raw = (result.stdout or result.stderr).strip()
            # "Python 3.11.4" → (3, 11, 4)
            parts = raw.replace("Python ", "").split(".")
            major, minor = int(parts[0]), int(parts[1])
            version_ok = (major, minor) >= MIN_PYTHON_VERSION
            return PythonStatus(
                installed=True,
                version=raw.replace("Python ", ""),
                version_ok=version_ok,
                executable=executable,
                error=None if version_ok else (
                    f"Python {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}+ required, "
                    f"found {major}.{minor}"
                ),
            )
        except Exception as e:
            continue

    return PythonStatus(
        installed=False,
        error=f"Python not found. Install from {PYTHON_INSTALL_URL}",
    )
