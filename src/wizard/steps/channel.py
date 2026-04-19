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
        console.print()
        console.print(
            "[yellow]⚠ No channel configured.[/yellow]\n\n"
            "You can still use your agent via the [bold]OpenClaw WebUI[/bold]:\n"
            "  http://localhost:3000  (or your server's IP)\n\n"
            "[bold red]Headless setup?[/bold red] Without a channel you have NO way to reach\n"
            "your agent remotely. Configure Telegram before going headless:\n"
            "  https://docs.openclaw.ai/channels/telegram\n"
        )
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

    # allowFrom — who can talk to the agent
    if channel_choice == "telegram":
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

        console.print(f"[bold cyan]\u203a {id_hint}[/bold cyan] [dim](optional, leave empty to skip)[/dim]")
        while True:
            allow_from = questionary.password("").ask()
            if allow_from is None:
                return False
            if not allow_from.strip() or allow_from.strip().lstrip("-").isdigit():
                break
            console.print("[yellow]Must be a numeric ID or leave empty.[/yellow]")

        if allow_from and allow_from.strip():
            state.channel_allow_from = [allow_from.strip()]

    console.print()
    console.print(f"[green]✓[/green] Channel: {info['label']} configured.\n")
    return True
