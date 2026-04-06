"""
Step 2: API key input.
Anthropic is required. Mistral is optional (enables semantic memory search).
"""
import questionary
from rich.console import Console
from rich.panel import Panel

from wizard.state import WizardState

console = Console()


def run(state: WizardState) -> bool:
    """Prompt for API keys.

    Returns True to continue, False to abort.
    """
    console.print(Panel.fit(
        "[bold]API Keys[/bold]\n\n"
        "OpenClaw needs at least one LLM provider key.\n"
        "[dim]Keys are stored in [bold].env[/bold] only — never in config files or logs.[/dim]",
        border_style="blue",
    ))
    console.print()

    # Anthropic — required
    console.print("[bold]Anthropic API Key[/bold] [red](required)[/red]")
    console.print("[dim]Get yours at: https://console.anthropic.com/[/dim]\n")

    anthropic_key = questionary.password(
        "Anthropic API key:",
        validate=lambda v: True if v.startswith("sk-ant-") else "Must start with sk-ant-",
    ).ask()

    if not anthropic_key:
        return False

    state.anthropic_api_key = anthropic_key.strip()

    # Mistral — optional
    console.print()
    console.print("[bold]Mistral API Key[/bold] [dim](optional)[/dim]")
    console.print(
        "[dim]Enables semantic memory search (finds related topics, not just exact matches).\n"
        "Without it: full-text search only. Can be added later.[/dim]\n"
    )

    want_mistral = questionary.confirm(
        "Add a Mistral API key now?",
        default=False,
    ).ask()

    if want_mistral:
        mistral_key = questionary.password("Mistral API key:").ask()
        if mistral_key:
            state.mistral_api_key = mistral_key.strip()

    console.print()
    console.print("[green]✓[/green] API keys saved.\n")
    return True
