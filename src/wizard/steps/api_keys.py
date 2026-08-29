"""
Step 2: LLM provider selection, API keys, and model tiers.

Follows the OpenClaw onboarding approach: pick a provider, authenticate,
then configure model tiers. Mistral is recommended as a second provider
for skills (translate, OCR, transcribe) and budget/media tasks.
"""
from __future__ import annotations

import shutil
import subprocess
from typing import Any

import questionary
from rich.console import Console
from wizard.ui import confirm_select
from rich.panel import Panel
from rich.table import Table

from wizard.state import WizardState

console = Console()

# Main LLM providers (the most common ones)
PROVIDERS: list[dict[str, Any]] = [
    {
        "id": "moonshot",
        "label": "Moonshot (Kimi K2.6)",
        "key_hint": "Starts with sk-  →  https://platform.moonshot.ai/",
        "key_prefix": "sk-",
        "models": [
            ("moonshot/kimi-k2.6", "Kimi K2.6 — recommended"),
        ],
        "default_model": "moonshot/kimi-k2.6",
    },
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
        "label": "OpenAI (GPT-5.5 Codex)",
        "key_hint": "Starts with sk-  →  https://platform.openai.com/",
        "key_prefix": "sk-",
        "models": [
            ("openai/gpt-5.5",       "GPT-5.5 — recommended"),
            ("openai/gpt-4o",        "GPT-4o — legacy"),
            ("openai/gpt-4o-mini",   "GPT-4o Mini — fast & cheap"),
        ],
        "default_model": "openai/gpt-5.5",
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
        "id": "ollama",
        "label": "Ollama (Local)",
        "key_hint": "No API key needed — enter Ollama host URL",
        "key_prefix": None,
        "models": [
            ("ollama/gemma4_26_Q5KS", "Gemma 4 26B Q5KS — recommended"),
            ("ollama/qwen3.6_27b",    "Qwen 3.6 27B — alternative"),
        ],
        "default_model": "ollama/gemma4_26_Q5KS",
    },
    {
        "id": "vllm",
        "label": "vLLM (local GPU)",
        "key_hint": "No API key needed — runs inside Docker on a local NVIDIA GPU",
        "key_prefix": None,
        "models": [
            ("unsloth/Qwen3.8-27B-NVFP4", "Qwen 3.8 27B NVFP4 — recommended"),
        ],
        "default_model": "unsloth/Qwen3.8-27B-NVFP4",
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

    # API key or host (skip for Ollama / vLLM)
    if provider["id"] == "vllm":
        return _run_vllm_setup(state, provider)
    if provider["id"] == "ollama":
        console.print()
        console.print("[yellow]⚠ Ollama runs externally — not inside the Docker container.[/yellow]")
        console.print("[dim]Enter the host URL where Ollama is running (e.g. http://192.168.1.100:11434)[/dim]\n")
        ollama_host = questionary.text(
            "Ollama host URL:",
            default="http://localhost:11434",
        ).ask()
        if ollama_host is None:
            return False
        if ollama_host.strip().lower() == "back":
            return BACK
        state.ollama_host = ollama_host.strip()
        key = ""  # No API key for Ollama
    elif provider["key_hint"]:
        console.print()
        console.print(f"[dim]{provider['key_hint']}[/dim]\n")

        def validate_key(v: str) -> bool | str:
            if not v.strip():
                return "Key cannot be empty"
            if provider["key_prefix"] and not v.strip().startswith(provider["key_prefix"]):
                return f"Key should start with {provider['key_prefix']}"
            return True

        while True:
            console.print("[bold cyan]› Enter API key:[/bold cyan]")
            key = questionary.password("").ask()
            if key is None:
                return False
            if key.strip().lower() == "back":
                return BACK
            if key.strip():
                break
            console.print("[yellow]API key cannot be empty.[/yellow]")
        key = key.strip()

        # Store in correct state field
        if provider["id"] == "anthropic":
            state.anthropic_api_key = key
        elif provider["id"] == "mistral":
            state.mistral_api_key = key
        elif provider["id"] == "moonshot":
            state.kimi_api_key = key
        elif provider["id"] == "openai":
            state.openai_api_key = key
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

        want_mistral = confirm_select(
            "Add Mistral as skills/budget provider? (recommended)",
            default=True,
        )

        if want_mistral is None:
            return BACK

        if want_mistral:
            console.print("[dim]→  https://console.mistral.ai/[/dim]\n")
            console.print("[bold cyan]› Enter Mistral API key:[/bold cyan] [dim](Enter to skip, 'back' to go back)[/dim]")
            mistral_key = questionary.password("").ask()
            if mistral_key is None:
                _set_fallback_budget(state, primary_model)
            elif mistral_key.strip().lower() == "back":
                return BACK
            elif mistral_key.strip():
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
    elif provider["id"] == "moonshot":
        # Kimi IS the primary — use it for everything
        state.llm_budget = primary_model
        state.llm_media = primary_model
    elif provider["id"] == "ollama":
        # Ollama IS the primary — use it for everything
        state.llm_budget = primary_model
        state.llm_media = primary_model
    else:
        # Mistral IS the primary — use it for everything
        state.llm_budget = primary_model
        state.llm_media = primary_model

    # ── Optional: Aki / Kimi API key ───────────────────────────────────────
    console.print()
    console.print(Panel(
        "[bold]Aki / Kimi K2.7-code[/bold] [dim](optional)[/dim]\n\n"
        "Aki/Kimi ist ein starker Coding-Modell-Provider.\n"
        "Wenn du einen API-Key hast, kannst du ihn hier hinterlegen.\n"
        "[dim]→  https://aki.trl / Entwickler-Doku[/dim]",
        border_style="blue",
        padding=(1, 2),
    ))
    console.print("[bold cyan]› Aki / Kimi API key:[/bold cyan] [dim](optional, Enter to skip, 'back' to go back)[/dim]")
    aki_key = questionary.password("").ask()
    if aki_key is None:
        aki_key = ""
    if aki_key.strip().lower() == "back":
        return BACK
    if aki_key.strip():
        state.aki_api_key = aki_key.strip()

    # ── Optional: Brave web-search API key ───────────────────────────────────
    console.print()
    console.print(Panel(
        "[bold]Brave Web Search[/bold] [dim](optional)[/dim]\n\n"
        "Brave bietet eine schnelle Web-Suche als OpenClaw-Plugin.\n"
        "Wenn du einen API-Key hast, wird das Plugin automatisch aktiviert.\n"
        "[dim]→  https://brave.com/search/api/[/dim]",
        border_style="blue",
        padding=(1, 2),
    ))
    console.print("[bold cyan]› Brave Web Search API key:[/bold cyan] [dim](optional, Enter to skip, 'back' to go back)[/dim]")
    brave_key = questionary.password("").ask()
    if brave_key is None:
        brave_key = ""
    if brave_key.strip().lower() == "back":
        return BACK
    if brave_key.strip():
        state.brave_web_search_api_key = brave_key.strip()

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
    if state.kimi_api_key:
        table.add_row("[dim]Kimi[/dim]", "[bold]Moonshot[/bold] [green]✓[/green]")
    if state.openai_api_key:
        table.add_row("[dim]OpenAI[/dim]", "[bold]GPT-5.5[/bold] [green]✓[/green]")
    if state.ollama_host:
        table.add_row("[dim]Ollama[/dim]", f"[bold]{state.ollama_host}[/bold] [green]✓[/green]")
    if state.vllm_enabled:
        table.add_row("[dim]vLLM[/dim]", f"[bold]{state.vllm_model}[/bold] [green]✓[/green]")
    if state.aki_api_key:
        table.add_row("[dim]Coding provider[/dim]", "[bold]Aki/Kimi[/bold] [green]✓[/green]")
    if state.brave_web_search_api_key:
        table.add_row("[dim]Web search[/dim]", "[bold]Brave[/bold] [green]✓[/green]")
    console.print(table)
    console.print()

    return True


def _detect_vram_mb() -> tuple[int | None, str | None]:
    """Detect total VRAM in MiB via nvidia-smi.

    Returns (vram_mb, error_message). vram_mb is None if nvidia-smi is
    unavailable or the query fails.
    """
    if not shutil.which("nvidia-smi"):
        return None, "nvidia-smi not found in PATH."
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return None, result.stderr.strip() or "nvidia-smi returned non-zero."
        # Use the first GPU's total memory
        lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        if not lines:
            return None, "nvidia-smi returned empty memory info."
        vram_mb = int(float(lines[0].strip()))
        return vram_mb, None
    except Exception as exc:  # pragma: no cover
        return None, f"VRAM detection failed: {exc}"


def _recommend_max_model_len(vram_mb: int | None) -> int:
    """Recommend a safe --max-model-len based on detected VRAM.

    Defaults derived from real-world tests on RTX 5090 32 GB with
    Qwen3.8-27B-NVFP4, fp8 KV-cache and --enforce-eager enabled:
    - <24 GiB: 8192
    - >=24 GiB: 32768
    """
    if vram_mb is None:
        return 8192
    vram_gb = vram_mb / 1024
    if vram_gb < 24:
        return 8192
    return 32768


def _run_vllm_setup(state: WizardState, provider: dict) -> bool | str:
    """Configure the local vLLM provider.

    Runs GPU detection, NVIDIA Container Toolkit smoke test, model selection,
    HF cache path, and max-model-len recommendation.
    """
    console.print(Panel(
        "[bold]vLLM (local GPU) setup[/bold] [dim](optional NVIDIA GPU required)[/dim]\n\n"
        "vLLM runs inside Docker with GPU passthrough.\n"
        "Make sure NVIDIA drivers and the NVIDIA Container Toolkit are installed.",
        border_style="blue",
        padding=(1, 2),
    ))

    # GPU + VRAM detection
    vram_mb, vram_error = _detect_vram_mb()
    if vram_mb is not None:
        vram_gb = vram_mb / 1024
        console.print(f"[green]✓[/green] NVIDIA GPU detected — [bold]{vram_gb:.1f} GiB[/bold] VRAM")
    else:
        console.print(f"[yellow]⚠[/yellow] GPU detection failed: {vram_error}")
        console.print("[dim]Continuing with conservative defaults. You can adjust values later in .env[/dim]")

    # NVIDIA Container Toolkit quick check
    console.print()
    console.print("[dim]Testing NVIDIA Container Toolkit via Docker...[/dim]")
    if shutil.which("docker"):
        try:
            result = subprocess.run(
                [
                    "docker", "run", "--rm", "--gpus", "all",
                    "nvidia/cuda:12.8.0-base-ubuntu24.04", "nvidia-smi",
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode == 0:
                console.print("[green]✓[/green] NVIDIA Container Toolkit is working")
            else:
                console.print("[yellow]⚠[/yellow] NVIDIA Container Toolkit test failed:")
                console.print(result.stderr.strip() or result.stdout.strip())
        except Exception as exc:  # pragma: no cover
            console.print(f"[yellow]⚠[/yellow] Could not run Docker GPU test: {exc}")
    else:
        console.print("[yellow]⚠[/yellow] docker not found — skipping Container Toolkit test")

    # Model selection
    console.print()
    console.print("[bold]vLLM model[/bold] [dim](HuggingFace model ID)[/dim]")
    vllm_model = _ask_model(provider)
    if not vllm_model:
        return False

    # Max model length recommendation
    recommended = _recommend_max_model_len(vram_mb)
    console.print()
    console.print(
        f"[dim]Recommended --max-model-len for your GPU: [bold]{recommended}[/bold][/dim]"
    )
    if vram_mb and vram_mb / 1024 > 32:
        console.print(
            "[dim]Note: even with >32 GiB, 32768 may OOM depending on the model.\n"
            "The conservative default is used.[/dim]"
        )
    max_len_input = questionary.text(
        "Max model length:",
        default=str(recommended),
        validate=lambda v: v.isdigit() and int(v) > 0 or "Must be a positive integer",
    ).ask()
    if max_len_input is None:
        return False
    if max_len_input.strip().lower() == "back":
        return BACK
    max_model_len = int(max_len_input.strip())

    # HuggingFace cache path
    console.print()
    default_hf_cache = state.vllm_hf_cache
    hf_cache = questionary.text(
        "HuggingFace cache path on the host:",
        default=default_hf_cache,
    ).ask()
    if hf_cache is None:
        return False
    if hf_cache.strip().lower() == "back":
        return BACK

    # Enable thinking? Default off for normal usage
    console.print()
    console.print(
        "[dim]Qwen3 models support a thinking mode. Disable it for normal chat.[/dim]"
    )
    enable_thinking = confirm_select("Enable thinking mode?", default=False)
    if enable_thinking is None:
        return False

    # Persist state
    state.vllm_enabled = True
    state.vllm_model = vllm_model
    state.vllm_max_model_len = max_model_len
    state.vllm_hf_cache = hf_cache.strip()
    state.vllm_enable_thinking = bool(enable_thinking)

    # vLLM becomes the primary local provider
    state.llm_standard = "vllm-local"
    state.llm_power = "vllm-local"
    state.llm_budget = "vllm-local"
    state.llm_media = "vllm-local"
    state.llm_vllm = vllm_model

    return True


def _set_fallback_budget(state: WizardState, primary_model: str) -> None:
    """Set budget/media to cheapest available tier from primary provider."""
    state.llm_budget = primary_model
    state.llm_media = primary_model
