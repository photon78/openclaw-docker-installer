"""
Step 4: Security profile selection.
Strict = recommended. Standard = more flexibility. Custom = for experts.
"""
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from wizard.ui import confirm_select

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


def run(state: WizardState) -> bool | str:
    """Prompt for security profile.

    Returns True to continue, False to abort, "back" to go to previous step.
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

    choices = [
        questionary.Choice(v["label"], value=k)
        for k, v in PROFILES.items()
    ]
    choices.append(questionary.Choice("← Back", value="__back__"))

    profile = questionary.select(
        "Choose a security profile:",
        choices=choices,
        default="strict",
    ).ask()

    if not profile:
        return False
    if profile == "__back__":
        return "back"

    state.security_profile = profile

    console.print()
    console.print(f"[green]\u2713[/green] Security profile: [bold]{PROFILES[profile]['label']}[/bold]\n")

    # autoAllowSkills opt-in
    console.print(
        "[dim]Auto-allow skills: automatically trusts scripts inside the skills/ directory.\n"
        "Recommended: [bold]No[/bold] (you can whitelist specific skill scripts later).[/dim]\n"
    )
    auto_allow = confirm_select(
        "Enable auto-allow for skill scripts? (not recommended)",
        default=False,
    )
    if auto_allow is None:
        return False
    state.auto_allow_skills = auto_allow
    if auto_allow:
        console.print("[yellow]![/yellow] autoAllowSkills enabled — skills/ directory is fully trusted.\n")
    else:
        console.print("[green]\u2713[/green] autoAllowSkills disabled — skill scripts need explicit allowlist entries.\n")

    return True
