"""
Step 4: Security profile selection.
Strict = recommended. Standard = more flexibility. Custom = for experts.
"""
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from wizard.state import WizardState

console = Console()

PROFILES = {
    "strict": {
        "label": "Strict (recommended)",
        "description": (
            "Allowlist only. Non-dev agents get named script paths, "
            "no bare interpreter access. Integrity monitoring active."
        ),
    },
    "standard": {
        "label": "Standard",
        "description": (
            "Allowlist with python3 + bash for all agents. "
            "More flexible, slightly less isolated."
        ),
    },
    "custom": {
        "label": "Custom",
        "description": "Configure per agent individually. For experienced users.",
    },
}


def run(state: WizardState) -> bool:
    """Prompt for security profile.

    Returns True to continue, False to abort.
    """
    console.print(Panel.fit(
        "[bold]Security Profile[/bold]\n\n"
        "[dim]This controls what commands your agent is allowed to run.\n"
        "You can adjust this later by editing exec-approvals.json.[/dim]",
        border_style="yellow",
    ))
    console.print()

    # Show what each profile means
    table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    table.add_column("Profile")
    table.add_column("What it means")

    for key, info in PROFILES.items():
        table.add_row(
            f"[bold]{info['label']}[/bold]",
            info["description"],
        )

    console.print(table)
    console.print()

    console.print(
        "[dim]Note: 'Full access' (security: full) is intentionally not offered.\n"
        "If you need it, you can set it manually in exec-approvals.json.[/dim]\n"
    )

    profile = questionary.select(
        "Choose a security profile:",
        choices=[
            questionary.Choice(v["label"], value=k)
            for k, v in PROFILES.items()
        ],
        default="strict",
    ).ask()

    if not profile:
        return False

    state.security_profile = profile

    console.print()
    console.print(f"[green]✓[/green] Security profile: [bold]{PROFILES[profile]['label']}[/bold]\n")
    return True
