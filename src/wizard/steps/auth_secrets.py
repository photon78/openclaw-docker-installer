"""
auth_secrets.py — Wizard step: auth profile secrets directory.

OpenClaw stores OAuth credentials and legacy encrypted profile data in a
directory separate from ~/.openclaw. This directory is mounted read-only
into the container at /home/node/.config/openclaw/.

It must be:
  • separate from the main openclaw_dir
  • included in backups
  • accessible only by the user running the container (chmod 700)
"""
from pathlib import Path

import questionary
from rich.console import Console
from rich.panel import Panel

from wizard.state import WizardState

console = Console()


def run(state: WizardState) -> bool | str:
    """Ask for the auth profile secrets directory. Returns True/False/'back'."""
    default_path = str(state.home_dir / ".openclaw-auth-profile-secrets")

    console.print()
    console.print(Panel(
        "[bold]Auth Profile Secrets[/bold]\n\n"
        "OpenClaw stores OAuth credentials and encrypted profile data in a\n"
        "directory [bold]separate[/bold] from your main config.\n\n"
        "This directory is mounted [bold]read-only[/bold] into the container at:\n"
        "  [cyan]/home/node/.config/openclaw/[/cyan]\n\n"
        "[dim]It must be backed up separately from ~/.openclaw.\n"
        "If you don't use OAuth integrations, you can keep the default.[/dim]",
        border_style="blue",
        padding=(1, 2),
    ))

    choices = [
        questionary.Choice(
            f"Use default: {default_path}",
            value=default_path,
        ),
        questionary.Choice("Custom path…", value="__custom__"),
        questionary.Choice("← Back", value="__back__"),
    ]

    choice = questionary.select(
        "Auth profile secrets directory:",
        choices=choices,
    ).ask()

    if choice is None:
        return False
    if choice == "__back__":
        return "back"

    if choice == "__custom__":
        custom = questionary.text(
            "Enter directory path:",
            default=default_path,
        ).ask()
        if not custom:
            return False
        secret_dir = custom.strip()
    else:
        secret_dir = choice

    # Create the directory if it doesn't exist
    path = Path(secret_dir)
    try:
        path.mkdir(parents=True, exist_ok=True)
        path.chmod(0o700)
        console.print(f"[green]✓[/green] Created: [cyan]{secret_dir}[/cyan] (chmod 700)")
    except Exception as e:
        console.print(f"[yellow]⚠[/yellow] Could not create [cyan]{secret_dir}[/cyan]: {e}")
        console.print("[dim]The directory will be created at container start if it doesn't exist.[/dim]")

    state.auth_profile_secret_dir = secret_dir
    console.print(
        f"\n[dim]Mounted into container as: [cyan]/home/node/.config/openclaw/[/cyan] (read-only)\n"
        f"Add this path to your backup configuration.[/dim]"
    )

    return True
