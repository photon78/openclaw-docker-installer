"""
check_nvidia_ctk.py — Verify NVIDIA Container Toolkit is installed and working.

Used by the installer wizard and can be run standalone before or after install.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass

CTK_TEST_IMAGE = "nvidia/cuda:12.8.0-base-ubuntu24.04"


@dataclass
class CtkStatus:
    """Result of the NVIDIA Container Toolkit check."""
    installed: bool
    docker_gpu_works: bool
    nvidia_smi: str | None = None
    error: str | None = None

    @property
    def ready(self) -> bool:
        """True if the toolkit is installed and Docker can access GPUs."""
        return self.installed and self.docker_gpu_works


def check_nvidia_smi() -> tuple[bool, str | None, str | None]:
    """Check if nvidia-smi is available and return the first GPU line."""
    if not shutil.which("nvidia-smi"):
        return False, None, "nvidia-smi not found in PATH"
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return False, None, result.stderr.strip() or "nvidia-smi failed"
        lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        return True, lines[0] if lines else None, None
    except Exception as exc:  # pragma: no cover
        return False, None, f"nvidia-smi error: {exc}"


def check_docker_gpu() -> tuple[bool, str | None]:
    """Run the NVIDIA Container Toolkit smoke test inside a CUDA container."""
    if not shutil.which("docker"):
        return False, "docker not found in PATH"
    try:
        result = subprocess.run(
            ["docker", "run", "--rm", "--gpus", "all", CTK_TEST_IMAGE, "nvidia-smi"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            return True, None
        return False, result.stderr.strip() or result.stdout.strip() or "docker GPU test failed"
    except Exception as exc:  # pragma: no cover
        return False, f"docker GPU test error: {exc}"


def check_nvidia_ctk() -> CtkStatus:
    """Run the full NVIDIA Container Toolkit readiness check."""
    nvidia_ok, nvidia_line, nvidia_error = check_nvidia_smi()
    if not nvidia_ok:
        return CtkStatus(
            installed=False,
            docker_gpu_works=False,
            error=nvidia_error or "NVIDIA driver not detected",
        )

    docker_gpu_ok, docker_error = check_docker_gpu()
    return CtkStatus(
        installed=True,
        docker_gpu_works=docker_gpu_ok,
        nvidia_smi=nvidia_line,
        error=docker_error if not docker_gpu_ok else None,
    )


if __name__ == "__main__":  # pragma: no cover
    status = check_nvidia_ctk()
    if status.ready:
        print("NVIDIA Container Toolkit is ready")
        if status.nvidia_smi:
            print(f"GPU: {status.nvidia_smi}")
    else:
        print(f"NVIDIA Container Toolkit not ready: {status.error}")
        raise SystemExit(1)
