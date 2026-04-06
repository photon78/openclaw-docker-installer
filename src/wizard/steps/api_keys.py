"""
Step 2: LLM provider selection, API keys, and model tiers.

Follows the OpenClaw onboarding approach: pick a provider, authenticate,
then configure model tiers. Mistral is recommended as a second provider
for skills (translate, OCR, transcribe) and budget/media tasks.
"""
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from wizard.state import WizardState

console = Console()

# Main LLM providers (the most common ones)
PROVIDERS = [
    {
        "id": "anthropic",
        "label": "Anthropic (Claude)",
        "key_hint": "Starts with sk-ant-  →  https://console.anthropic.com/",
        "key_prefix": "sk-ant-",
        "models": [
            ("anthropic/claude-sonnet-4-6", "Claude Sonnet 4.6 — recommended"),
            ("anthropic/claude-opus-4-6",   "Claude Opus 4.6   — most powerful"),
            ("anthropic/claude-haiku-4-5",  "Claude Haiku 4.5  — fast & cheap"),
        ],
        "default_model": "anthropic/claude-sonnet-4-6",
    },
    {
        "id": "openai",
        "label": "OpenAI (ChatGPT / GPT-4)",
        "key_hint": "Starts with sk-  →  https://platform.openai.com/",
        "key_prefix": "sk-",
        "models": [
            ("openai/gpt-4o",        "GPT-4o — recommended"),
            ("openai/gpt-4o-mini",   "GPT-4o Mini — fast & cheap"),
            ("openai/o3",            "o3 — advanced reasoning"),
        ],
        "default_model": "openai/gpt-4o",
    },
    {
        "id": "google",
        "label": "Google (Gemini)",
        "key_hint": "→  https://aistudio.google.com/",
        "key_prefix": None,
        "models": [
            ("google/gemini-2.5-pro",   "Gemini 2.5 Pro — recommended"),
            ("google/gemini-2.5-flash", "Gemini 2.5 Flash — fast & cheap"),
        ],
        "default_model": "google/gemini-2.5-pro",
    },
    {
        "id": "xai",
        "label": "xAI (Grok)",
        "key_hint": "→  https://console.x.ai/",
        "key_prefix": "xai-",
        "models": [
            ("xai/grok-3",      "Grok 3 — recommended"),
            ("xai/grok-3-mini", "Grok 3 Mini — fast & cheap"),
        ],
        "default_model": "xai/grok-3",
    },
    {
        "id": "mistral",
        "label": "Mistral",
        "key_hint": "→  https://console.mistral.ai/",
        "key_prefix": None,
        "models": [
            ("mistral/mistral-large-latest", "Mistral Large — recommended"),
            ("mistral/mistral-small-latest", "Mistral Small — fast & cheap"),
        ],
        "default_model": "mistral/mistral-large-latest",
    },
    {
        "id": "openrouter",
        "label": "OpenRouter (access to many providers)",
        "key_hint": "Starts with sk-or-  →  https://openrouter.ai/",
        "key_prefix": "sk-or-",
        "models": [],  # user enters manually
        "default_model": "",
    },
    {
        "id": "ollama",
        "label": "Ollama (local models, no API key needed)",
        "key_hint": None,
        "key_prefix": None,
        "models": [
            ("ollama/llama3.3", "Llama 3.3 — recommended local model"),
            ("ollama/qwen2.5",  "Qwen 2.5  — strong multilingual"),
        ],
        "default_model": "ollama/llama3.3",
    },
    {
        "id": "custom",
        "label": "Other / Custom provider",
        "key_hint": "Enter model ID manually (format: provider/model)",
        "key_prefix": None,
        "models": [],
        "default_model": "",
    },
]


def _ask_model(provider: dict) -> str:
    """Ask user to select or enter a model for the given provider."""
    if provider["models"]:
        choices = [questionary.Choice(label, value=mid) for mid, label in provider["models"]]
        choices.append(questionary.Choice("Enter manually...", value="__manual__"))
        choice = questionary.select("Select model:", choices=choices,
                                    default=provider["default_model"]).ask()
        if choice == "__manual__":
            return questionary.text("Model ID (e.g. provider/model-name):").ask() or ""
        return choice or provider["default_model"]
    else:
        return questionary.text(
            "Model ID (e.g. openrouter/anthropic/claude-sonnet):",
            default=provider.get("default_model", ""),
        ).ask() or ""


BACK = "back"


def run(state: WizardState) -> bool | str:
    """Prompt for LLM provider, API key, and model tiers.

    Returns True to continue, False to abort, "back" to go to previous step.
    """
    console.print(Panel.fit(
        "[bold]LLM Provider & API Keys[/bold]\n\n"
        "[dim]Choose which AI provider powers your agent.\n"
        "Keys are stored in [bold].env[/bold] only — never in config files or logs.[/dim]",
        border_style="blue",
    ))
    console.print()

    # ── Primary provider ────────────────────────────────────────────────────
    console.print("[bold]Primary provider[/bold] [dim](powers your main agent)[/dim]\n")

    choices = [questionary.Choice(p["label"], value=p["id"]) for p in PROVIDERS]
    choices.append(questionary.Choice("← Back", value="__back__"))

    provider_choice = questionary.select(
        "Which LLM provider?",
        choices=choices,
    ).ask()

    if not provider_choice:
        return False
    if provider_choice == "__back__":
        return BACK

    provider = next(p for p in PROVIDERS if p["id"] == provider_choice)

    # API key (skip for Ollama)
    if provider["key_hint"]:
        console.print()
        console.print(f"[dim]{provider['key_hint']}[/dim]\n")

        def validate_key(v: str) -> bool | str:
            if not v.strip():
                return "Key cannot be empty"
            if provider["key_prefix"] and not v.strip().startswith(provider["key_prefix"]):
                return f"Key should start with {provider['key_prefix']}"
            return True

        key = questionary.password("API key: (or type 'back' to go back)").ask()
        if not key:
            return False
        if key.strip().lower() == "back":
            return BACK
        key = key.strip()

        # Store in correct state field
        if provider["id"] == "anthropic":
            state.anthropic_api_key = key
        elif provider["id"] == "mistral":
            state.mistral_api_key = key
        else:
            # Generic: store as primary_api_key for config generator
            state.primary_provider_id = provider["id"]
            state.primary_api_key = key

    # Model selection
    console.print()
    console.print("[bold]Model selection[/bold]\n")
    primary_model = _ask_model(provider)
    if not primary_model:
        return False

    state.llm_standard = primary_model
    state.llm_power = primary_model  # user can refine later

    # ── Mistral as skills provider (if not already chosen) ─────────────────
    if provider["id"] != "mistral":
        console.print()
        console.print(Panel(
            "[bold]Mistral as skills provider[/bold] [dim](optional — recommended)[/dim]\n\n"
            "Mistral excels at specific tasks that other providers handle poorly or expensively:\n\n"
            "  [cyan]• OCR[/cyan]         Extract text from images, scans, photos — fast and accurate\n"
            "  [cyan]• Translate[/cyan]   Document/text translation across 30+ languages\n"
            "  [cyan]• Transcribe[/cyan]  Speech-to-text for audio files\n"
            "  [cyan]• Memory[/cyan]      Semantic search in your agent\'s memory (embeddings)\n"
            "  [cyan]• Budget[/cyan]      Cheap model for cron jobs, digests, summaries\n\n"
            "[dim]Without Mistral: OCR, translation and transcription skills won\'t work.\n"
            "Cost: ~10× cheaper than Claude/GPT for bulk tasks.[/dim]",
            border_style="blue",
            padding=(1, 2),
        ))
        console.print()

        want_mistral = questionary.confirm(
            "Add Mistral as skills/budget provider? (recommended) [Enter=yes, n=no, b=back]",
            default=True,
        ).ask()

        if want_mistral is None:
            return BACK

        if want_mistral:
            console.print("[dim]→  https://console.mistral.ai/[/dim]\n")
            mistral_key = questionary.password("Mistral API key: (or type 'back' to skip)").ask()
            if mistral_key and mistral_key.strip().lower() != "back" and mistral_key.strip():
                state.mistral_api_key = mistral_key.strip()
                state.llm_budget = "mistral/mistral-large-latest"
                state.llm_media = "mistral/mistral-large-latest"
            else:
                _set_fallback_budget(state, primary_model)
        else:
            _set_fallback_budget(state, primary_model)
            console.print(
                "[yellow]Note:[/yellow] Skills requiring Mistral (translate, OCR, transcribe)\n"
                "[dim]will not be available. You can add a Mistral key later in .env.[/dim]\n"
            )
    else:
        # Mistral IS the primary — use it for everything
        state.llm_budget = primary_model
        state.llm_media = primary_model

    # ── Summary ─────────────────────────────────────────────────────────────
    console.print()
    console.print("[green]✓[/green] Provider configured.\n")

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_row("[dim]Primary provider[/dim]", f"[bold]{provider['label']}[/bold]")
    table.add_row("[dim]Standard model[/dim]",   f"[bold]{state.llm_standard}[/bold]")
    table.add_row("[dim]Power model[/dim]",       f"[bold]{state.llm_power}[/bold]")
    table.add_row("[dim]Budget model[/dim]",      f"[bold]{state.llm_budget}[/bold]")
    table.add_row("[dim]Media model[/dim]",       f"[bold]{state.llm_media}[/bold]")
    if state.mistral_api_key:
        table.add_row("[dim]Skills provider[/dim]", "[bold]Mistral[/bold] [green]✓[/green]")
    console.print(table)
    console.print()

    return True


def _set_fallback_budget(state: WizardState, primary_model: str) -> None:
    """Set budget/media to cheapest available tier from primary provider."""
    state.llm_budget = primary_model
    state.llm_media = primary_model
