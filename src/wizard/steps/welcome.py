"""
Step 1: Welcome + Pre-flight checks.
"""
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from checks.docker_check import check_docker
from wizard.state import WizardState

console = Console()


def run(state: WizardState) -> bool:
    """Show welcome screen and run pre-flight checks.

    Returns True if all critical checks pass, False to abort.
    """
    console.print()
    console.print(Panel.fit(
        "[bold cyan]OpenClaw Installer[/bold cyan]\n\n"
        "[dim]Secure by default. Human in the loop.[/dim]\n\n"
        f"[dim]Installing for user:[/dim] [bold]{state.username}[/bold]\n"
        f"[dim]Target directory:[/dim]  [bold]{state.openclaw_dir}[/bold]",
        border_style="cyan",
        title="Welcome",
    ))
    console.print()

    # Pre-flight
    console.print("[bold]Pre-flight checks[/bold]")
    table = Table(show_header=False, box=None, padding=(0, 2))

    docker = check_docker()
    if docker.ready:
        table.add_row("[green]✓[/green]", f"Docker {docker.version}", "ready")
    else:
        table.add_row("[red]✗[/red]", "Docker", docker.error or "not found")

    console.print(table)
    console.print()

    if not docker.ready:
        console.print("[red]Docker is required.[/red]")
        console.print("  Install: [link]https://docs.docker.com/engine/install/[/link]")
        return False

    console.print("[green]All checks passed.[/green] Let's get started.\n")
    return True
