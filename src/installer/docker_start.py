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
                    return StartResult(ok=True, message="Gateway ready.")
            except Exception:
                pass
            time.sleep(POLL_INTERVAL)

    # Timeout — show last logs
    console.print("[yellow]⚠[/yellow] Gateway did not become healthy within "
                  f"{STARTUP_TIMEOUT}s. Last logs:")
    _show_logs(compose_file, lines=20)
    return StartResult(ok=False, message="Gateway startup timeout.")


def _fix_permissions(openclaw_dir: Path) -> None:
    """Ensure ~/.openclaw is owned by uid 1000 (node user inside container)."""
    result = subprocess.run(
        ["docker", "run", "--rm",
         "-v", f"{openclaw_dir}:/target",
         "busybox", "chown", "-R", "1000:1000", "/target"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        log.info("Permissions fixed: %s owned by uid 1000", openclaw_dir)
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
