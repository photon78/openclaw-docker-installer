"""
docker_check.py — Prüft ob Docker verfügbar und läuft
"""

import subprocess
import shutil


def is_docker_installed() -> bool:
    return shutil.which("docker") is not None


def is_docker_running() -> bool:
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


def is_compose_available() -> bool:
    """Prüft ob 'docker compose' (v2) verfügbar ist."""
    try:
        result = subprocess.run(
            ["docker", "compose", "version"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


def get_docker_status() -> dict:
    return {
        "installed": is_docker_installed(),
        "running": is_docker_running(),
        "compose": is_compose_available(),
    }
