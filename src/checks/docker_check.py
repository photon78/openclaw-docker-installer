"""
docker_check.py — Checks if Docker is installed, running, and usable.

Uses the Docker Python SDK where possible, falls back to subprocess
for cases where the SDK is not available (e.g. before install).
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass

DOCKER_INSTALL_URL = "https://docs.docker.com/get-docker/"
MIN_DOCKER_VERSION = (20, 10)  # minimum supported version


@dataclass
class DockerStatus:
    """Result of a Docker availability check."""
    installed: bool
    running: bool
    compose_available: bool
    version: str | None = None
    version_ok: bool = False
    error: str | None = None

    @property
    def ready(self) -> bool:
        """True if Docker is fully ready for use."""
        return self.installed and self.running and self.compose_available and self.version_ok


def _get_docker_version() -> tuple[str | None, bool]:
    """Returns (version_string, is_compatible).

    Parses 'docker version --format {{.Server.Version}}'.
    Returns (None, False) on any error.
    """
    try:
        result = subprocess.run(
            ["docker", "version", "--format", "{{.Server.Version}}"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return None, False
        version_str = result.stdout.strip()
        parts = version_str.split(".")
        major, minor = int(parts[0]), int(parts[1])
        ok = (major, minor) >= MIN_DOCKER_VERSION
        return version_str, ok
    except Exception:
        return None, False


def check_docker() -> DockerStatus:
    """Run all Docker checks and return a DockerStatus.

    Checks in order:
    1. Is the 'docker' binary in PATH?
    2. Is the Docker daemon running? (docker info)
    3. Is 'docker compose' (v2) available?
    4. Is the version >= MIN_DOCKER_VERSION?
    """
    # 1. Binary in PATH?
    if not shutil.which("docker"):
        return DockerStatus(
            installed=False,
            running=False,
            compose_available=False,
            error=f"Docker not found. Install it from: {DOCKER_INSTALL_URL}",
        )

    # 2. Daemon running?
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=10,
        )
        running = result.returncode == 0
    except Exception as e:
        return DockerStatus(
            installed=True,
            running=False,
            compose_available=False,
            error=f"Docker daemon not reachable: {e}",
        )

    if not running:
        return DockerStatus(
            installed=True,
            running=False,
            compose_available=False,
            error="Docker is installed but the daemon is not running. Start Docker and try again.",
        )

    # 3. Docker Compose v2?
    try:
        compose_result = subprocess.run(
            ["docker", "compose", "version"],
            capture_output=True,
            timeout=5,
        )
        compose_ok = compose_result.returncode == 0
    except Exception:
        compose_ok = False

    # 4. Version check
    version_str, version_ok = _get_docker_version()

    error = None
    if not compose_ok:
        error = "Docker Compose v2 not available. Update Docker to a recent version."
    elif not version_ok and version_str:
        error = (
            f"Docker version {version_str} is below minimum "
            f"{'.'.join(str(v) for v in MIN_DOCKER_VERSION)}. Please update."
        )

    return DockerStatus(
        installed=True,
        running=True,
        compose_available=compose_ok,
        version=version_str,
        version_ok=version_ok,
        error=error,
    )
