"""
completion.py — Post-installation instructions screen.
Shows the user exactly how to start OpenClaw and what to do next.
Split into 3 pages with press-Enter-to-continue between them.
"""
import json
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text

from wizard.state import WizardState


def _read_gateway_token(state: WizardState) -> str | None:
    """Read gateway token from openclaw.json after first start."""
    config_file = state.openclaw_dir / "openclaw.json"
    try:
        data = json.loads(config_file.read_text())
        token = data.get("gateway", {}).get("auth", {}).get("token")
        if token and not token.startswith("${"):
            return token
    except Exception:
        pass
    return None


def _pause(console: Console, label: str = "next") -> None:
    """Wait for Enter before showing the next page."""
    console.print()
    console.input(f"[dim]  Press Enter for {label} →[/dim]")
    console.print()


console = Console()


def show(state: WizardState, image: str) -> None:
    """Print post-installation next-steps screen (3 pages)."""
    compose_file = state.openclaw_dir / "docker-compose.yml"
    dashboard_url = "http://127.0.0.1:18789"

    console.print()
    console.print(Rule("[bold green]Installation complete[/bold green]"))
    console.print()

    # ── Page 1: Gateway Token ────────────────────────────────────────────────
    console.print(
        f"[bold green]✓ Gateway is running[/bold green]  "
        f"[dim]image: {image}[/dim]"
    )
    console.print()

    token = _read_gateway_token(state)
    if token:
        token_text = Text.assemble(
            ("Your gateway token — keep this secret!\n\n", "bold"),
            (f"  {token}", "bold cyan"),
            "\n\n",
            ("Use this to log into the Control UI and connect mobile apps.\n", "dim"),
            ("Anyone with this token has full access to your agent.", "red"),
        )
        console.print(Panel(
            token_text,
            title="[bold yellow]🔑 Gateway Token  (Page 1 / 3)[/bold yellow]",
            border_style="yellow",
            padding=(1, 2),
        ))
    else:
        console.print(Panel(
            "[dim]Token not yet available.\n\n"
            "Check after first start:\n"
            "  [cyan]openclaw.json[/cyan] → [cyan]gateway.auth.token[/cyan][/dim]",
            title="[bold yellow]🔑 Gateway Token  (Page 1 / 3)[/bold yellow]",
            border_style="yellow",
            padding=(1, 2),
        ))

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

    _pause(console, "next steps")

    # ── Page 2: Next Steps ──────────────────────────────────────────────────
    console.print(Panel(
        f"""[bold]1. Open Control UI[/bold]

  [link={dashboard_url}]{dashboard_url}[/link]
  → Paste your gateway token (see above ↑)

[bold]2. Start the onboarding conversation[/bold]

  Send your agent this message:
  [cyan]Lies bitte BOOTSTRAP.md und mach den Onboarding-Ablauf.[/cyan]
  (or in English: [cyan]Please read BOOTSTRAP.md and start the onboarding.[/cyan])
  The agent will introduce itself, explain its skills, and set up your profile.

[bold]3. Check status / logs[/bold]

  [cyan]docker compose -f {compose_file} ps[/cyan]
  [cyan]docker compose -f {compose_file} logs -f[/cyan]

[bold]4. Add to autostart (optional)[/bold]

  Docker restarts the container automatically ([cyan]restart: unless-stopped[/cyan]).
  Make sure Docker itself starts on boot:
  [cyan]sudo systemctl enable docker[/cyan]

[bold]5. Change providers / add API keys later[/bold]

  Run OpenClaw's native configure wizard inside the container:
  [cyan]docker compose exec -it openclaw-gateway openclaw configure[/cyan]
  This handles provider changes, model tiers, and new channels
  without re-running the installer.

[bold]6. Restore exec-approvals (if needed)[/bold]

  If the gateway overwrites exec-approvals.json via doctor mode:
  [cyan]docker compose exec openclaw-gateway \\
    python3 /home/node/.openclaw/scripts/restore_exec_approvals.py[/cyan]

[bold]7. Restart / stop[/bold]

  [cyan]docker compose -f {compose_file} restart[/cyan]
  [cyan]docker compose -f {compose_file} down[/cyan]
""",
        title="[bold green]Next steps  (Page 2 / 3)[/bold green]",
        border_style="green",
        padding=(1, 2),
    ))

    _pause(console, "cron jobs & customization")

    # ── Page 3: Cron + Customize ────────────────────────────────────────────
    console.print(Panel(
        """Cron jobs are managed via the OpenClaw CLI [italic]after[/italic] the gateway is running.

[bold]Memory sync is handled automatically by the heartbeat[/bold] — no extra cron needed.
The heartbeat runs in an isolated session, reads the daily log, and updates MEMORY.md.

[bold]Gateway health check[/bold] (every 2h — recommended):
  [cyan]openclaw cron add --name "Gateway Health Check" --cron "0 */2 * * *" \\
    --session main --system-event "HEARTBEAT: gateway health check"[/cyan]

[dim]Or let your agent set this up automatically on first run.[/dim]""",
        title="[bold cyan]⏰ Recommended cron jobs  (Page 3 / 3)[/bold cyan]",
        border_style="cyan",
        padding=(1, 2),
    ))

    console.print()

    soul_path = state.workspace_dir / "SOUL.md"
    agents_path = state.workspace_dir / "AGENTS.md"
    console.print(Panel(
        f"""Your workspace files contain [bold]<!-- INSTALLER NOTE -->[/bold] comments.

Read and edit these to make your agent truly yours:

  [cyan]{soul_path}[/cyan]
  [cyan]{agents_path}[/cyan]

The agent will walk you through the rest on first run ([cyan]BOOTSTRAP.md[/cyan]).""",
        title="[bold yellow]📝 Customize your agent[/bold yellow]",
        border_style="yellow",
        padding=(1, 2),
    ))

    console.print()
    console.print("[bold green]OpenClaw is ready. Have fun.[/bold green]")
    console.print()
