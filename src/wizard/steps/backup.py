"""
backup.py — Wizard step: backup medium configuration.
Backup is a core feature — not optional.
"""
from pathlib import Path

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
        "Mon–Sat: [bold]incremental[/bold] backup (changed files only)\n"
        "Sunday:  [bold]full backup[/bold] + versioned snapshot (30-day retention)\n"
        "Runs at 04:10 daily inside the container.\n\n"
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
        while True:
            custom = questionary.text(
                "Enter mount path:",
                default="/mnt/backup",
            ).ask()
            if not custom:
                return False
            path = Path(custom.strip())
            if path.exists() and path.is_dir():
                state.backup_mount_path = str(path)
                break
            console.print(f"[yellow]⚠[/yellow]  Path [cyan]{custom.strip()}[/cyan] does not exist or is not a directory.")
            console.print("[dim]Make sure the backup medium is mounted before continuing, or choose Skip.[/dim]")
    else:
        # Predefined path — validate before accepting
        path = Path(choice)
        if not path.exists() or not path.is_dir():
            console.print(f"[yellow]⚠[/yellow]  [cyan]{choice}[/cyan] is not mounted or does not exist.")
            console.print("[dim]Mount your backup medium first, or choose a different path.[/dim]")
            retry = questionary.select(
                "What would you like to do?",
                choices=[
                    questionary.Choice("Enter a custom path", value="custom"),
                    questionary.Choice(“⏭  Skip backup for now", value="skip"),
                ],
            ).ask()
            if retry == "skip":
                state.backup_mount_path = None
                return True
            # Fall through to custom input
            custom = questionary.text("Enter mount path:", default="/mnt/backup").ask()
            if not custom:
                return False
            state.backup_mount_path = custom.strip()
        else:
            state.backup_mount_path = str(path)

    console.print(f"[green]✓[/green] Backup mount: [cyan]{state.backup_mount_path}[/cyan]")

    # Crontab hint
    console.print(
        "\n[dim]Add to host crontab (runs backup daily at 04:10):[/dim]\n"
        "[cyan]10 4 * * * docker compose -f ~/.openclaw/docker-compose.yml "
        "exec -T openclaw-gateway python3 /home/node/.openclaw/scripts/daily_backup.py[/cyan]"
    )

    return True
