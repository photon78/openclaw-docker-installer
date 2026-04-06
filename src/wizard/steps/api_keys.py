"""
Step 2: API keys + model selection.

Anthropic is required. Mistral is optional but recommended:
- Several skills depend on it (translate, OCR, transcribe)
- Strong in language, multimedia, and summarization
- Significantly cheaper for budget/media tasks
"""
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from wizard.state import WizardState

console = Console()

ANTHROPIC_MODELS = {
    "anthropic/claude-sonnet-4-6": "Claude Sonnet 4.6 — recommended (fast, capable, balanced cost)",
    "anthropic/claude-opus-4-6":   "Claude Opus 4.6   — most powerful, higher cost",
}

MISTRAL_MODELS = {
    "mistral/mistral-large-latest": "Mistral Large — recommended (strong reasoning + language)",
    "mistral/mistral-small-latest": "Mistral Small — faster, cheaper, good for simple tasks",
}


def run(state: WizardState) -> bool:
    """Prompt for API keys and model selection.

    Returns True to continue, False to abort.
    """
    console.print(Panel.fit(
        "[bold]LLM Providers & API Keys[/bold]\n\n"
        "[dim]Keys are stored in [bold].env[/bold] only.\n"
        "Never in config files, logs, or Docker images.[/dim]",
        border_style="blue",
    ))
    console.print()

    # ── Anthropic (required) ────────────────────────────────────────────────
    console.print("[bold]Anthropic[/bold] [red](required)[/red]")
    console.print("[dim]Get your key at: https://console.anthropic.com/[/dim]\n")

    anthropic_key = questionary.password(
        "Anthropic API key:",
        validate=lambda v: True if v.strip().startswith("sk-ant-")
        else "Key must start with sk-ant-",
    ).ask()

    if not anthropic_key:
        return False
    state.anthropic_api_key = anthropic_key.strip()

    # Model selection for standard/power tier
    console.print()
    console.print("[bold]Primary model[/bold] [dim](used for standard tasks)[/dim]")
    primary = questionary.select(
        "Choose your primary model:",
        choices=[
            questionary.Choice(desc, value=key)
            for key, desc in ANTHROPIC_MODELS.items()
        ],
        default=list(ANTHROPIC_MODELS.keys())[0],
    ).ask()

    if not primary:
        return False

    state.llm_standard = primary
    state.llm_power = "anthropic/claude-opus-4-6"

    # ── Mistral (optional but recommended) ─────────────────────────────────
    console.print()
    console.print("[bold]Mistral[/bold] [dim](optional — but recommended)[/dim]")

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_row("[green]✓[/green]", "Required by skills: translate, OCR, transcribe")
    table.add_row("[green]✓[/green]", "Strong in language and multimedia tasks")
    table.add_row("[green]✓[/green]", "Much cheaper for budget/media workloads")
    table.add_row("[green]✓[/green]", "Powers semantic memory search (hybrid mode)")
    console.print(table)
    console.print("[dim]Get your key at: https://console.mistral.ai/[/dim]\n")

    want_mistral = questionary.confirm(
        "Add a Mistral API key? (recommended)",
        default=True,
    ).ask()

    if want_mistral:
        mistral_key = questionary.password("Mistral API key:").ask()
        if mistral_key and mistral_key.strip():
            state.mistral_api_key = mistral_key.strip()

            console.print()
            console.print("[bold]Mistral model[/bold] [dim](used for budget/media/skills)[/dim]")
            mistral_model = questionary.select(
                "Choose Mistral model tier:",
                choices=[
                    questionary.Choice(desc, value=key)
                    for key, desc in MISTRAL_MODELS.items()
                ],
                default=list(MISTRAL_MODELS.keys())[0],
            ).ask()

            if mistral_model:
                state.llm_budget = mistral_model
                state.llm_media = mistral_model
        else:
            # No Mistral — fall back to Anthropic Haiku for budget tasks
            state.llm_budget = "anthropic/claude-haiku-4-5"
            state.llm_media = "anthropic/claude-haiku-4-5"
    else:
        # Explicitly skipped — use Anthropic Haiku as budget fallback
        state.llm_budget = "anthropic/claude-haiku-4-5"
        state.llm_media = "anthropic/claude-haiku-4-5"
        console.print(
            "[yellow]Note:[/yellow] Some skills (translate, OCR, transcribe) require Mistral.\n"
            "[dim]You can add a Mistral key later by editing .env.[/dim]\n"
        )

    console.print()
    console.print("[green]✓[/green] API keys and models configured.\n")

    # Summary
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_row("[dim]Standard[/dim]", f"[bold]{state.llm_standard}[/bold]")
    table.add_row("[dim]Power[/dim]",    f"[bold]{state.llm_power}[/bold]")
    table.add_row("[dim]Budget[/dim]",   f"[bold]{state.llm_budget}[/bold]")
    table.add_row("[dim]Media[/dim]",    f"[bold]{state.llm_media}[/bold]")
    console.print(table)
    console.print()

    return True
