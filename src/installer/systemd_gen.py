"""
systemd_gen.py — Generate a systemd user service for OpenClaw Docker.

Writes ~/.config/systemd/user/openclaw.service so the gateway starts
automatically on boot (requires loginctl enable-linger).

User service (not system service) — no sudo needed.
Docker must be running before this service starts:
  WantedBy=default.target + After=docker.service

Limitations:
  - User services only start after login (or linger). For headless servers
    with linger enabled, this works without any session.
  - If Docker runs as root (default on Pi), the user must be in the docker group.
  - Rootless Docker users can use this as-is.
"""
from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path

from wizard.state import WizardState

log = logging.getLogger("installer.systemd_gen")


def _service_content(state: WizardState) -> str:
    compose_file = state.openclaw_dir / "docker-compose.yml"
    # Use absolute path to docker compose — avoids PATH issues in systemd env
    docker_bin = "/usr/bin/docker"

    return f"""\
[Unit]
Description=OpenClaw Gateway (Docker)
Documentation=https://docs.openclaw.ai
# Start after Docker socket is available
After=docker.service docker.socket
Requires=docker.socket
# Restart if Docker daemon restarts
PartOf=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes

ExecStartPre={docker_bin} compose -f {compose_file} pull --quiet
ExecStart={docker_bin} compose -f {compose_file} up -d
ExecStop={docker_bin} compose -f {compose_file} down

# Restart policy: if docker compose up fails, retry after 10s
Restart=on-failure
RestartSec=10s

[Install]
WantedBy=default.target
"""


def write(state: WizardState) -> Path | None:
    """Write the systemd user service file. Returns path or None if not Linux."""
    if sys.platform != "linux":
        log.info("systemd_gen: skipped on %s (Linux only)", sys.platform)
        return None

    service_dir = Path.home() / ".config" / "systemd" / "user"
    service_dir.mkdir(parents=True, exist_ok=True)
    service_path = service_dir / "openclaw.service"
    service_path.write_text(_service_content(state), encoding="utf-8")
    log.info("systemd user service written: %s", service_path)
    return service_path


def try_enable(service_path: Path) -> bool:
    """Attempt to reload systemd and enable the service. Non-fatal on failure."""
    cmds = [
        ["systemctl", "--user", "daemon-reload"],
        ["systemctl", "--user", "enable", "openclaw.service"],
    ]
    for cmd in cmds:
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            log.warning("%s failed (non-fatal): %s", " ".join(cmd), r.stderr.strip())
            return False
    log.info("systemd user service enabled.")
    return True


def linger_hint(user: str) -> str:
    """Return the loginctl enable-linger command for this user."""
    return f"sudo loginctl enable-linger {user}"
