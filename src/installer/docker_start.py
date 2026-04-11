"""
docker_start.py — Start the OpenClaw gateway via docker compose and verify it comes up.
Polls /healthz until the gateway is ready or times out.
"""
from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

import logging
import httpx
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from wizard.state import WizardState

log = logging.getLogger("installer.docker_start")

console = Console()

HEALTHZ_URL = "http://127.0.0.1:18789/readyz"  # readiness probe (gateway fully up)
POLL_INTERVAL = 2      # seconds between health checks
STARTUP_TIMEOUT = 90   # max seconds to wait (Docker image may need to initialize)


@dataclass
class StartResult:
    ok: bool
    message: str = ""


def run(state: WizardState) -> StartResult:
    compose_file = state.openclaw_dir / "docker-compose.yml"

    if not compose_file.exists():
        return StartResult(ok=False, message=f"docker-compose.yml not found: {compose_file}")

    console.print("\n[bold]Starting OpenClaw gateway...[/bold]")

    # Pull image first — show progress to user
    console.print("[dim]Pulling OpenClaw image...[/dim]")
    pull = subprocess.run(
        ["docker", "compose", "-f", str(compose_file), "pull"],
        # No capture_output — let Docker show pull progress directly
    )
    if pull.returncode != 0:
        log.warning("docker compose pull failed (non-fatal) — will try up anyway")

    # docker compose up -d
    result = subprocess.run(
        ["docker", "compose", "-f", str(compose_file), "up", "-d"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        log.error("docker compose up failed:\n%s", result.stderr)
        console.print(f"[red]✗ docker compose up failed:[/red]\n{result.stderr}")
        return StartResult(ok=False, message=result.stderr.strip())

    log.info("Container started.")
    console.print("[green]✓[/green] Container started.")

    # Fix permissions: container runs as node (uid 1000)
    _fix_permissions(state.openclaw_dir)

    # Poll /readyz
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task("Waiting for gateway...", total=None)
        deadline = time.monotonic() + STARTUP_TIMEOUT

        while time.monotonic() < deadline:
            try:
                resp = httpx.get(HEALTHZ_URL, timeout=3)
                if resp.status_code == 200:
                    progress.stop()
                    log.info("Gateway healthy at %s", HEALTHZ_URL)
                    console.print("[green]✓[/green] Gateway is healthy.")
                    _run_post_gateway_fix(state)
                    return StartResult(ok=True, message="Gateway ready.")
            except Exception:
                pass
            time.sleep(POLL_INTERVAL)

    # Timeout — show last logs
    console.print("[yellow]⚠[/yellow] Gateway did not become healthy within "
                  f"{STARTUP_TIMEOUT}s. Last logs:")
    _show_logs(compose_file, lines=20)
    return StartResult(ok=False, message="Gateway startup timeout.")


def _run_post_gateway_fix(state: WizardState) -> None:
    """Run post_gateway_fix.py in background to patch models.json after gateway start.

    Runs as a background process (non-blocking) — watches models.json for 30s.
    Non-fatal if script is missing or fails.
    """
    import sys
    script = state.workspace_dir / "scripts" / "post_gateway_fix.py"
    if not script.exists():
        log.warning("post_gateway_fix.py not found at %s — skipping", script)
        return
    try:
        subprocess.Popen(
            [sys.executable, str(script)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        log.info("post_gateway_fix.py started in background")
    except Exception as exc:
        log.warning("post_gateway_fix.py failed to start (non-fatal): %s", exc)


def _fix_permissions(openclaw_dir: Path) -> None:
    """Ensure ~/.openclaw is owned by uid 1000 (node user inside container).

    The OpenClaw Docker image runs as the 'node' user (uid 1000, gid 1000).
    Mounted volumes must be owned by that uid so the container can write to them.

    Side effect: if the host user has a different uid, they may lose direct
    write access to openclaw_dir. This is intentional — the installer and
    generated scripts are the only writers.
    """
    import os
    host_uid = os.getuid()
    if host_uid != 1000:
        log.warning(
            "Host user uid is %d (not 1000). Files in %s will be owned by uid 1000 "
            "(Docker container user). Use sudo or re-run as uid 1000 if direct access needed.",
            host_uid, openclaw_dir,
        )

    result = subprocess.run(
        ["docker", "run", "--rm",
         "-v", f"{openclaw_dir}:/target",
         "busybox", "chown", "-R", "1000:1000", "/target"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        log.info("Permissions fixed: %s owned by uid 1000 (container user)", openclaw_dir)
    else:
        log.warning("chown failed (non-fatal): %s", result.stderr.strip())


def _show_logs(compose_file: Path, lines: int = 20) -> None:
    result = subprocess.run(
        ["docker", "compose", "-f", str(compose_file), "logs", "--tail", str(lines)],
        capture_output=True,
        text=True,
    )
    if result.stdout:
        console.print(result.stdout)
    if result.stderr:
        console.print(result.stderr)
