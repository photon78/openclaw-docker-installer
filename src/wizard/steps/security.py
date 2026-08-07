"""
Step 4: Security settings.

The security-profile tier concept has been removed because it produced
identical configuration regardless of the chosen profile. A single,
well-defined allowlist is enforced instead. This step now only asks whether
to opt into auto-allowing skill scripts.
"""
from rich.console import Console
from rich.panel import Panel

from wizard.ui import confirm_select
from wizard.state import WizardState

console = Console()


def run(state: WizardState) -> bool | str:
    """Prompt for security settings.

    Returns True to continue, False to abort, "back" to go to previous step.
    """
    console.print(Panel.fit(
        "[bold]Security Settings[/bold]\n\n"
        "[dim]The installer uses a single, hardened allowlist for all agents.\n"
        "Shell interpreters and generic network tools are excluded by default.[/dim]",
        border_style="yellow",
    ))
    console.print()

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
