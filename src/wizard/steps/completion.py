"""
completion.py — Post-installation instructions screen.
Shows the user exactly how to start OpenClaw and what to do next.
"""
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule

from wizard.state import WizardState

console = Console()


def show(state: WizardState, image: str) -> None:
    """Print post-installation next-steps screen."""
    compose_file = state.openclaw_dir / "docker-compose.yml"
    dashboard_url = "http://127.0.0.1:18789"

    console.print()
    console.print(Rule("[bold green]Installation complete[/bold green]"))
    console.print()

    # Start instructions
    console.print(Panel(
        f"""[bold]1. Start OpenClaw[/bold]

  [cyan]docker compose -f {compose_file} up -d[/cyan]

[bold]2. Check status[/bold]

  [cyan]docker compose -f {compose_file} ps[/cyan]
  [cyan]docker compose -f {compose_file} logs -f[/cyan]

[bold]3. Open Control UI[/bold]

  [link={dashboard_url}]{dashboard_url}[/link]
  → Paste your gateway token (from [cyan]{state.openclaw_dir}/.env[/cyan])

[bold]4. Add to autostart (optional)[/bold]

  systemd:
  [cyan]sudo systemctl enable docker[/cyan]
  Then add a systemd unit or use [cyan]restart: unless-stopped[/cyan] (already set).

[bold]5. Restore exec-approvals (if needed)[/bold]

  If the gateway ever overwrites exec-approvals.json via doctor mode:
  [cyan]docker compose exec openclaw-gateway python3 /home/node/.openclaw/scripts/restore_exec_approvals.py[/cyan]

[bold]6. Update later[/bold]

  [cyan]openclaw-installer update[/cyan]
  Pulls the latest image and restarts the container.
""",
        title="[bold green]Next steps[/bold green]",
        border_style="green",
        padding=(1, 2),
    ))

    # Image info
    console.print(
        f"[dim]Pinned image: [cyan]{image}[/cyan] — "
        f"run [cyan]openclaw-installer update[/cyan] to upgrade.[/dim]"
    )
    console.print()

    # Channel-specific hint
    if state.channel == "telegram":
        console.print(
            "[yellow]Telegram:[/yellow] Make sure your bot token is active. "
            "Send [cyan]/start[/cyan] to your bot to verify the connection."
        )
    elif state.channel == "discord":
        console.print(
            "[yellow]Discord:[/yellow] Invite your bot to a server and check "
            "that it has message permissions in the target channel."
        )
    elif state.channel == "signal":
        console.print(
            "[yellow]Signal:[/yellow] Link your Signal account via the Control UI "
            "after the gateway is running."
        )

    # INSTALLER NOTE hint
    soul_path = state.workspace_dir / "SOUL.md"
    agents_path = state.workspace_dir / "AGENTS.md"
    console.print(Panel(
        f"""Your workspace files contain [bold]<!-- INSTALLER NOTE -->[/bold] comments.

They explain what each section does and what to customize.
Read and edit these files to make your agent truly yours:

  [cyan]{soul_path}[/cyan]
  [cyan]{agents_path}[/cyan]

The agent will walk you through the rest on first run ([cyan]BOOTSTRAP.md[/cyan]).""",
        title="📝 Customize your agent",
        border_style="yellow",
        padding=(1, 2),
    ))

    console.print()
    console.print("[bold green]OpenClaw is ready. Have fun.[/bold green]")
    console.print()
