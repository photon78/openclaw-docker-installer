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
import typer
from rich.console import Console
from rich.panel import Panel

from checks.docker_check import check_docker
from checks.gateway_check import check_gateway, DEFAULT_PORT
from wizard.wizard import run_wizard
from generator.generator import run as run_generator
from installer.docker_start import run as docker_start
from installer.workspace_bootstrap import run as bootstrap_workspace
from installer.logging_setup import setup as setup_logging, get_log_file
from wizard.steps import completion

log = logging.getLogger("installer")

app = typer.Typer(
    name="openclaw-installer",
    help="OpenClaw in a Box — secure, production-ready OpenClaw setup.",
    add_completion=False,
)
console = Console()


@app.command()
def install() -> None:
    """Run the interactive setup wizard."""
    # Setup logging first — before wizard so all output is captured
    log_file = setup_logging()
    console.print(f"[dim]Install log: {log_file}[/dim]\n")
    log.info("=== openclaw-installer: install started ===")

    state = run_wizard()
    if state is None:
        log.info("Installation aborted by user.")
        raise typer.Exit(code=1)

    log.info("Wizard complete — channel=%s security=%s backup=%s",
             state.channel, state.security_profile, state.backup_mount_path)

    result = run_generator(state)
    if not result.success:
        log.error("Configuration generation failed.")
        console.print(f"[red]Configuration generation failed.[/red]")
        console.print(f"[dim]See log for details: {get_log_file()}[/dim]")
        raise typer.Exit(code=1)

    log.info("Config generated — image=%s", result.image)

    # Bootstrap workspace templates
    console.print("\n[bold]Bootstrapping workspace...[/bold]")
    bootstrap_workspace(state)
    log.info("Workspace bootstrapped at %s", state.workspace_dir)

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
def uninstall(
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
) -> None:
    """Remove the OpenClaw installation."""
    if not confirm:
        confirmed = typer.confirm(
            "This will remove the OpenClaw installation. Are you sure?",
            default=False,
        )
        if not confirmed:
            console.print("[dim]Aborted.[/dim]")
            raise typer.Exit()

    console.print("[bold red]Uninstall[/bold red]")
    console.print("[yellow]Not yet implemented.[/yellow]")


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
