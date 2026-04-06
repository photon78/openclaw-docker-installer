"""
backup.py — Wizard step: backup medium configuration.
Backup is a core feature — not optional.
"""
import questionary
from rich.console import Console
from rich.panel import Panel

from wizard.state import WizardState

console = Console()

DEFAULT_MOUNTS = [
    "/mnt/backup",
    "/mnt/sdcard",
    "/mnt/usb",
    "/mnt/nas",
    "Custom path...",
]


def run(state: WizardState) -> bool | str:
    """Ask user for backup mount path. Returns False to abort, 'back' to go back."""
    console.print()
    console.print(Panel(
        "[bold]Backup setup[/bold]\n\n"
        "Daily backups protect your workspace, config and memory.\n"
        "Backup runs at 04:10 daily inside the container.\n\n"
        "[dim]What is backed up:[/dim] workspace/, openclaw.json, scripts/, exec-approvals.json (token redacted)\n"
        "[dim]What is NOT backed up:[/dim] .env / API keys, session logs, node_modules, dist/",
        border_style="blue",
        padding=(1, 2),
    ))

    choices = DEFAULT_MOUNTS + [
        "⏭  Skip — configure backup later",
        "← Back",
    ]

    choice = questionary.select(
        "Where is your backup medium mounted?",
        choices=choices,
    ).ask()

    if choice is None:
        return False
    if choice == "← Back":
        return "back"
    if choice == "⏭  Skip — configure backup later":
        console.print("[yellow]⚠[/yellow]  Backup skipped. Configure [cyan]daily_backup.py[/cyan] manually later.")
        state.backup_mount_path = None
        return True

    if choice == "Custom path...":
        custom = questionary.text(
            "Enter mount path:",
            default="/mnt/backup",
        ).ask()
        if not custom:
            return False
        state.backup_mount_path = custom.strip()
    else:
        state.backup_mount_path = choice

    console.print(f"[green]✓[/green] Backup mount: [cyan]{state.backup_mount_path}[/cyan]")

    # Crontab hint
    console.print(
        "\n[dim]Add to host crontab (runs backup daily at 04:10):[/dim]\n"
        "[cyan]10 4 * * * docker compose -f ~/.openclaw/docker-compose.yml "
        "exec -T openclaw-gateway python3 /home/node/.openclaw/scripts/daily_backup.py[/cyan]"
    )

    return True
