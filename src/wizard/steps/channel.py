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

    # Token input — required, loop until valid or back
    while True:
        token = questionary.password(
            f"{info['label']} bot token: (required — type 'back' to go back)"
        ).ask()
        if token is None:
            # Ctrl+C / Ctrl+D
            return False
        if token.strip().lower() == "back":
            return "back"
        if token.strip():
            break
        console.print("[yellow]Token cannot be empty.[/yellow]")

    state.telegram_bot_token = token.strip()

    # allowFrom — who can talk to the agent
    console.print()
    console.print("[bold]Who should be able to reach the agent?[/bold]")
    console.print(
        "[dim]Enter your Telegram user ID (find it via @userinfobot).\n"
        "Leave empty to skip — you can configure this in openclaw.json later.[/dim]\n"
    )

    allow_from = questionary.text(
        "Your user ID (e.g. 123456789):",
        validate=lambda v: True if not v or v.strip().lstrip("-").isdigit()
        else "Must be a numeric ID or empty",
    ).ask()

    if allow_from and allow_from.strip():
        state.channel_allow_from = [allow_from.strip()]

    console.print()
    console.print(f"[green]✓[/green] Channel: {info['label']} configured.\n")
    return True
