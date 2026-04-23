"""
Step 1: Welcome, requirements overview, and pre-flight checks.
"""
from rich.console import Console
from wizard.ui import confirm_select
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table

from checks.docker_check import check_docker
from checks.python_check import check_python
from wizard.state import WizardState

console = Console()

REQUIREMENTS = [
    (
        "Python 3.11+",
        "Required to run this installer.",
        "https://www.python.org/downloads/",
    ),
    (
        "Docker Desktop / Docker Engine",
        "Runs the OpenClaw container.",
        "https://docs.docker.com/engine/install/",
    ),
    (
        "Docker Compose v2",
        "Usually bundled with Docker Desktop.",
        "https://docs.docker.com/compose/install/",
    ),
    (
        "LLM API Key",
        "Powers your agent. Any supported provider works.",
        "Anthropic, Mistral, OpenAI, Google, xAI, DeepSeek …",
    ),
    (
        "Messaging channel (optional)",
        "To chat with your agent. Telegram recommended.",
        "https://t.me/BotFather  |  Discord  |  Signal",
    ),
]


def run(state: WizardState) -> bool:
    """Show welcome screen, requirements, and run pre-flight checks.

    Returns True if all critical checks pass, False to abort.
    """
    # ── Intro screen ──────────────────────────────────────────────────────
    from pathlib import Path as _Path
    _version = "0.3.2"
    _version_file = _Path(__file__).parent.parent.parent.parent / "VERSION"
    if _version_file.exists():
        _version = _version_file.read_text().strip()

    console.print()
    console.print(Panel(
        f"[bold cyan]Welcome to the OpenClaw Installer[/bold cyan]  [dim]v{_version}[/dim]\n\n"
        "This wizard sets up a [bold]secure, production-ready[/bold] OpenClaw instance\n"
        "running in Docker — with a restrictive allowlist, approval dialogs,\n"
        "and sane defaults out of the box.\n\n"
        "[dim]It takes about 5–10 minutes. Have your API key ready.[/dim]\n\n"
        f"[dim]User:[/dim]      [bold]{state.username}[/bold]\n"
        f"[dim]Target:[/dim]    [bold]{state.openclaw_dir}[/bold]",
        border_style="cyan",
        padding=(1, 2),
    ))
    console.print()

    cont = confirm_select("Ready to start?", default=True)
    if not cont:
        return False

    # ── Requirements overview ─────────────────────────────────────────────
    console.print()
    console.print(Rule("[bold]Requirements[/bold]"))
    console.print()

    table = Table(show_header=True, box=None, padding=(0, 2))
    table.add_column("Requirement", style="bold")
    table.add_column("Why")
    table.add_column("Where to get it", style="dim")

    for name, reason, url in REQUIREMENTS:
        table.add_row(name, reason, url)

    console.print(table)
    console.print()

    cont2 = confirm_select("Got everything? Continue to pre-flight checks?", default=True)
    if not cont2:
        return False

    # ── Pre-flight checks ─────────────────────────────────────────────────
    console.print()
    console.print(Rule("[bold]Pre-flight checks[/bold]"))
    console.print()

    check_table = Table(show_header=False, box=None, padding=(0, 2))
    all_ok = True

    py = check_python()
    if py.ready:
        check_table.add_row("[green]✓[/green]", f"Python {py.version}", "[green]ready[/green]")
    else:
        check_table.add_row("[red]✗[/red]", "Python 3.11+", f"[red]{py.error}[/red]")
        all_ok = False

    docker = check_docker()
    if docker.ready:
        check_table.add_row("[green]✓[/green]", f"Docker {docker.version}", "[green]ready[/green]")
    else:
        check_table.add_row("[red]✗[/red]", "Docker", f"[red]{docker.error or 'not found'}[/red]")
        all_ok = False

    console.print(check_table)
    console.print()

    if not all_ok:
        console.print("[red]One or more requirements are missing.[/red]")
        console.print("[dim]Fix the issues above and re-run the installer.[/dim]")
        return False

    console.print("[green]All checks passed.[/green] Let's set up your agent.\n")
    return True
