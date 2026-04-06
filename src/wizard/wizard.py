"""
wizard.py — Main wizard orchestrator.
Runs steps in sequence, supports back-navigation.
Steps return True (continue), False (abort), or "back" (go to previous step).
"""
from rich.console import Console

from wizard.state import WizardState
from wizard.steps import welcome, api_keys, persona, channel, security, backup

console = Console()

STEPS = [
    ("Welcome",   welcome.run),
    ("API Keys",  api_keys.run),
    ("Persona",   persona.run),
    ("Channel",   channel.run),
    ("Security",  security.run),
    ("Backup",    backup.run),
]


def run_wizard() -> WizardState | None:
    """Run all wizard steps with back-navigation support.

    Returns completed WizardState, or None if the user aborted.
    Step return values:
      True   — continue to next step
      False  — abort installation
      "back" — go to previous step
    """
    state = WizardState()
    i = 0

    while i < len(STEPS):
        name, step_fn = STEPS[i]
        total = len(STEPS)
        console.print(f"[dim]Step {i + 1}/{total}: {name}[/dim]")

        result = step_fn(state)

        if result is False:
            console.print("\n[yellow]Installation aborted.[/yellow]")
            return None
        elif result == "back":
            if i > 0:
                i -= 1
                console.print(f"[dim]← Back to: {STEPS[i][0]}[/dim]")
            else:
                console.print("[dim]Already at first step.[/dim]")
            # Don't advance
        else:
            i += 1

    return state
