"""
persona.py — Wizard step: agent name, emoji, and communication style.
"""
import questionary
from rich.console import Console
from rich.panel import Panel

console = Console()

BACK = "back"

STYLE_PRESETS = {
    "direct": {
        "label": "Direct & technical — no fluff, assumes competence",
        "description": "Direct and honest. Technical competence assumed. No hedging, no filler sentences. "
                       "Errors are admitted, not hidden. Arrogance: user has expertise — no dumbing-down.",
    },
    "formal": {
        "label": "Formal & professional — structured, measured, polite",
        "description": "Professional and precise. Structured responses. Polite but not warm. "
                       "Suitable for business or mixed audiences.",
    },
    "friendly": {
        "label": "Friendly & approachable — warm, casual, helpful",
        "description": "Warm and approachable. Casual tone. Still competent — just easier to talk to. "
                       "Good for personal or family setups.",
    },
}


def run(state) -> bool | str:
    console.print(Panel(
        "[bold]Step: Agent Identity[/bold]\n\n"
        "Give your agent a name and pick a communication style.\n"
        "You can always change this later in [cyan]SOUL.md[/cyan].",
        border_style="blue",
    ))

    # Agent name
    while True:
        name = questionary.text(
            "Agent name:",
            default=state.agent_name or "main",
        ).ask()
        if name is None:
            return False
        name = name.strip()
        if name.lower() == "back":
            return BACK
        if name:
            break
        console.print("[yellow]Name cannot be empty.[/yellow]")

    # Emoji
    emoji = questionary.text(
        "Agent emoji (optional):",
        default=state.agent_emoji or "🤖",
    ).ask()
    if emoji is None:
        return False
    if emoji.strip().lower() == "back":
        return BACK

    # Communication style
    choices = [
        questionary.Choice(title=v["label"], value=k)
        for k, v in STYLE_PRESETS.items()
    ]
    choices.append(questionary.Choice(title="⏭  Skip — I'll edit SOUL.md myself", value="skip"))

    style = questionary.select(
        "Communication style:",
        choices=choices,
    ).ask()
    if style is None:
        return False

    state.agent_name = name
    state.agent_emoji = emoji.strip() or "🤖"
    state.persona_style = style  # "direct" | "formal" | "friendly" | "skip"

    if style != "skip":
        style_info = STYLE_PRESETS[style]
        console.print(f"\n[green]✓[/green] Style: [bold]{style_info['label']}[/bold]")

    return True
