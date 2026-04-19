#!/usr/bin/env python3
"""
openclaw-installer — CLI entry point.

Commands:
  install    Run the setup wizard (interactive)
  status     Show current OpenClaw installation status
  start      Start the OpenClaw gateway (docker-compose up)
  stop       Stop the OpenClaw gateway (docker-compose down)
  uninstall  Remove the OpenClaw installation
"""

import logging
try:
    import typer
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
except ImportError:
    import sys
    import os
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _venv_sh  = os.path.join(_root, "run.sh")
    _venv_bat = os.path.join(_root, "run.bat")
    print("\nError: dependencies not installed.")
    print("Use the launcher instead of calling main.py directly:\n")
    if sys.platform == "win32":
        print(f"  {_venv_bat} install")
    else:
        print(f"  chmod +x {_venv_sh} && {_venv_sh} install")
    print()
    sys.exit(1)

from checks.docker_check import check_docker
from checks.gateway_check import check_gateway, DEFAULT_PORT
from checks.python_check import check_python
from wizard.wizard import run_wizard
from generator.generator import run as run_generator
from installer.docker_start import run as docker_start
from installer.logging_setup import setup as setup_logging, get_log_file
from wizard.steps import completion

log = logging.getLogger("installer")

app = typer.Typer(
    name="openclaw-installer",
    help="OpenClaw in a Box — secure, production-ready OpenClaw setup.",
    add_completion=False,
)
console = Console()


ASCII_ART = (
    "  ___  ____  _____ _   _  ____  _       _     __        __\n"
    " / _ \\|  _ \\| ____| \\ | |/ ___|| |     / \\   \\ \\  /\\  / /\n"
    "| | | | |_) |  _| |  \\| | |   | |    / _ \\   \\ \\/  \\/ /\n"
    "| |_| |  __/| |___| |\\  | |___| |___/ ___ \\   \\  /\\  /\n"
    " \\___/|_|   |_____|_| \\_|\\____|_____/_/   \\_\\   \\/  \\/\n"
)


@app.command()
def install(
    dry_run: bool = typer.Option(
        False, "--dry-run",
        help="Preview generated config files in a temp dir — no files written to ~/.openclaw, Docker not started."
    ),
) -> None:
    """Run the interactive setup wizard."""
    console.print()
    console.print(ASCII_ART, style="bold cyan")
    info = Text.assemble(
        ("\U0001f512 Secure by Default", "bold"),
        "  |  ",
        ("Multi-Agent AI Setup", "bold"),
        "\n",
        "v0.3.0 \"The Crew\"",
        "  |  ",
        ("https://openclaw.ai", "cyan underline"),
    )
    console.print(Panel(info, style="cyan", expand=False))
    console.print()

    # Setup logging first — before wizard so all output is captured
    log_file = setup_logging()
    console.print(f"[dim]Install log: {log_file}[/dim]\n")
    log.info("=== openclaw-installer: install started ===")

    # Pre-flight: Python version (relevant on Windows)
    py = check_python()
    if not py.ready:
        console.print(f"[red]\u2717 Python 3.11+ required.[/red] {py.error}")
        raise typer.Exit(code=1)
    log.info("Python OK: %s (%s)", py.version, py.executable)

    state = run_wizard()
    if state is None:
        log.info("Installation aborted by user.")
        raise typer.Exit(code=1)

    state.dry_run = dry_run
    log.info("Wizard complete — channel=%s security=%s backup=%s dry_run=%s",
             state.channel, state.security_profile, state.backup_mount_path, dry_run)

    result = run_generator(state)
    if not result.success:
        log.error("Configuration generation failed.")
        console.print("[red]Configuration generation failed.[/red]")
        console.print(f"[dim]See log for details: {get_log_file()}[/dim]")
        raise typer.Exit(code=1)

    log.info("Config generated — image=%s", result.image)

    if dry_run:
        console.print()
        console.print("[bold yellow]🔍 Dry run complete.[/bold yellow] No files were written to [cyan]~/.openclaw[/cyan].")
        console.print(f"Generated files are in: [cyan]{state.openclaw_dir}[/cyan]")
        console.print("[dim]Inspect the files, then re-run without --dry-run to install.[/dim]")
        raise typer.Exit()

    # Start gateway
    start = docker_start(state)
    if not start.ok:
        log.error("Gateway failed to start: %s", start.message)
        console.print(f"[red]Gateway failed to start:[/red] {start.message}")
        console.print("[dim]Fix the issue and run: docker compose -f "
                      f"{state.openclaw_dir}/docker-compose.yml up -d[/dim]")
        console.print(f"[dim]See log: {get_log_file()}[/dim]")
        raise typer.Exit(code=1)

    log.info("=== openclaw-installer: install complete ===")
    completion.show(state, result.image)


@app.command()
def status() -> None:
    """Show current OpenClaw installation status."""
    console.print("[bold]OpenClaw Status[/bold]\n")

    docker = check_docker()
    if docker.ready:
        console.print(f"[green]✓[/green] Docker {docker.version} — ready")
    else:
        console.print(f"[red]✗[/red] Docker — {docker.error or 'not available'}")

    gateway = check_gateway(port=DEFAULT_PORT)
    if gateway.ok:
        console.print(f"[green]✓[/green] Gateway — reachable on port {gateway.port}")
    else:
        console.print(f"[yellow]·[/yellow] Gateway — {gateway.message}")


@app.command()
def start() -> None:
    """Start the OpenClaw gateway (docker-compose up -d)."""
    console.print("[bold]Starting OpenClaw...[/bold]")
    console.print("[yellow]Not yet implemented.[/yellow]")
    console.print("[dim]Will run: docker compose up -d[/dim]")


@app.command()
def stop() -> None:
    """Stop the OpenClaw gateway (docker-compose down)."""
    console.print("[bold]Stopping OpenClaw...[/bold]")
    console.print("[yellow]Not yet implemented.[/yellow]")
    console.print("[dim]Will run: docker compose down[/dim]")


@app.command()
def clean(
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
) -> None:
    """Remove generated OpenClaw files for a fresh install (keeps Docker + repo)."""
    import shutil
    import subprocess as sp
    from pathlib import Path

    openclaw_dir = Path.home() / ".openclaw"

    generated = [
        openclaw_dir / "docker-compose.yml",
        openclaw_dir / ".env",
        openclaw_dir / "openclaw.json",
        openclaw_dir / "exec-approvals.json",
        openclaw_dir / "workspace",
        openclaw_dir / "scripts",
        openclaw_dir / "logs",
    ]

    existing = [p for p in generated if p.exists()]
    if not existing:
        console.print("[dim]Nothing to clean — no generated files found.[/dim]")
        raise typer.Exit()

    console.print("[bold]Files to remove:[/bold]")
    for p in existing:
        console.print(f"  [red]-[/red] {p}")

    if not yes:
        confirmed = typer.confirm(
            "\nRemove all generated files? (Container will be stopped first)",
            default=False,
        )
        if not confirmed:
            console.print("[dim]Aborted.[/dim]")
            raise typer.Exit()

    # Stop container if running
    compose_file = openclaw_dir / "docker-compose.yml"
    if compose_file.exists():
        console.print("[dim]Stopping container...[/dim]")
        sp.run(
            ["docker", "compose", "-f", str(compose_file), "down"],
            capture_output=True,
        )

    # Remove files
    for p in existing:
        if p.is_dir():
            shutil.rmtree(p)
        else:
            p.unlink()
        console.print(f"  [green]✓[/green] Removed {p}")

    console.print("\n[green]Clean complete.[/green] Run [cyan]python3 src/main.py install[/cyan] to start fresh.")


@app.command()
def uninstall(
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
) -> None:
    """Remove the OpenClaw installation (alias for clean)."""
    clean(yes=confirm)


def _run_preflight() -> bool:
    """Run pre-flight checks. Returns True if all critical checks pass."""
    docker = check_docker()
    if docker.ready:
        console.print(f"[green]✓[/green] Docker {docker.version} — ready")
    else:
        console.print(f"[red]✗[/red] Docker — {docker.error or 'not available'}")
        console.print("\n[red]Docker is required. Please install Docker first.[/red]")
        console.print("  https://docs.docker.com/engine/install/")
        return False

    console.print("\n[green]Pre-flight checks passed.[/green]")
    return True


if __name__ == "__main__":
    app()
