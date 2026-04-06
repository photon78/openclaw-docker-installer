"""
wizard.py — Main wizard orchestrator.
Runs steps in sequence, carries state through, returns completed WizardState.
"""
from rich.console import Console

from wizard.state import WizardState
from wizard.steps import welcome, api_keys, channel, security, backup

console = Console()

STEPS = [
    ("Welcome",   welcome.run),
    ("API Keys",  api_keys.run),
    ("Channel",   channel.run),
    ("Security",  security.run),
    ("Backup",    backup.run),
]


def run_wizard() -> WizardState | None:
    """Run all wizard steps in sequence.

    Returns completed WizardState, or None if the user aborted.
    """
    state = WizardState()

    for i, (name, step_fn) in enumerate(STEPS, start=1):
        console.print(f"[dim]Step {i}/{len(STEPS)}: {name}[/dim]")
        ok = step_fn(state)
        if not ok:
            console.print("\n[yellow]Installation aborted.[/yellow]")
            return None

    return state
