"""
Step 3: Channel selection.
Choose how OpenClaw communicates with you.
"""
import questionary
from rich.console import Console
from rich.panel import Panel

from wizard.state import WizardState

console = Console()

CHANNELS = {
    "telegram": {
        "label": "Telegram (recommended)",
        "description": "Fast, reliable, full approval UI. Requires a bot token from @BotFather.",
        "guide": "1. Open Telegram → search @BotFather\n"
                 "2. Send /newbot → follow instructions\n"
                 "3. Copy the token (looks like 123456:ABC-DEF...)",
    },
    "discord": {
        "label": "Discord",
        "description": "Good for team setups. Requires a bot application.",
        "guide": "1. Go to https://discord.com/developers/applications\n"
                 "2. Create application → Bot → copy token",
    },
    "signal": {
        "label": "Signal",
        "description": "Most private. Requires signal-cli setup.",
        "guide": "See: https://docs.openclaw.ai/channels/signal",
    },
}


def run(state: WizardState) -> bool | str:
    """Prompt for channel selection and credentials.

    Returns True to continue, False to abort, "back" to go to previous step.
    """
    console.print(Panel.fit(
        "[bold]Channel Setup[/bold]\n\n"
        "Choose how you'll communicate with your OpenClaw agent.\n"
        "[dim]You can add more channels later via openclaw.json.[/dim]",
        border_style="blue",
    ))
    console.print()

    choices = [
        questionary.Choice(v["label"], value=k)
        for k, v in CHANNELS.items()
    ]
    choices.append(questionary.Choice("⏭  Skip — configure later via openclaw.json", value="__skip__"))
    choices.append(questionary.Choice("← Back", value="__back__"))

    channel_choice = questionary.select(
        "Which channel do you want to use?",
        choices=choices,
    ).ask()

    if not channel_choice:
        return False
    if channel_choice == "__back__":
        return "back"
    if channel_choice == "__skip__":
        console.print("[dim]Channel skipped. Add it later in openclaw.json.[/dim]")
        state.channel = None
        return True

    state.channel = channel_choice
    info = CHANNELS[channel_choice]

    console.print()
    console.print(f"[bold]{info['label']}[/bold]")
    console.print(f"[dim]{info['description']}[/dim]\n")
    console.print(info["guide"])
    console.print()

    # Token / credential input — required, loop until valid or back
    _labels = {
        "telegram": "Telegram bot token",
        "discord": "Discord bot token",
        "signal": "signal-cli phone number (e.g. +41791234567)",
    }
    _prompt = _labels.get(channel_choice, f"{info['label']} token")
    while True:
        console.print(f"[bold cyan]› {_prompt}:[/bold cyan] [dim](required, 'back' to go back)[/dim]")
        token = questionary.password("").ask()
        if token is None:
            # Ctrl+C / Ctrl+D
            return False
        if token.strip().lower() == "back":
            return "back"
        if token.strip():
            break
        console.print("[yellow]Token cannot be empty.[/yellow]")

    # Save token to the correct field
    if channel_choice == "telegram":
        state.telegram_bot_token = token.strip()
    elif channel_choice == "discord":
        state.discord_bot_token = token.strip()
    elif channel_choice == "signal":
        state.signal_number = token.strip()

    # allowFrom — who can talk to the agent (Telegram + Discord only)
    if channel_choice in ("telegram", "discord"):
        console.print()
        console.print("[bold]Who should be able to reach the agent?[/bold]")
        if channel_choice == "telegram":
            console.print(
                "[dim]Enter your Telegram user ID (find it via @userinfobot).\n"
                "Leave empty to skip — you can configure this in openclaw.json later.[/dim]\n"
            )
            id_hint = "Your Telegram user ID (e.g. 123456789):"
        else:
            console.print(
                "[dim]Enter your Discord user ID (right-click your name → Copy User ID).\n"
                "Leave empty to skip — you can configure this in openclaw.json later.[/dim]\n"
            )
            id_hint = "Your Discord user ID (e.g. 123456789012345678):"

        allow_from = questionary.text(
            id_hint,
            validate=lambda v: True if not v or v.strip().lstrip("-").isdigit()
            else "Must be a numeric ID or empty",
        ).ask()

        if allow_from and allow_from.strip():
            state.channel_allow_from = [allow_from.strip()]

    console.print()
    console.print(f"[green]✓[/green] Channel: {info['label']} configured.\n")
    return True
