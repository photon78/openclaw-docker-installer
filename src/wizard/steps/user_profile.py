"""
Step: User Profile — collect basic facts about the person using the agent.
Populates USER.md so the agent knows who it's talking to from the first message.
"""
import questionary
from rich.console import Console
from rich.panel import Panel

from wizard.state import WizardState

console = Console()

TIMEZONES = [
    "Europe/Zurich", "Europe/Berlin", "Europe/London", "Europe/Paris",
    "Europe/Vienna", "Europe/Rome", "Europe/Amsterdam",
    "America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles",
    "America/Toronto", "America/Sao_Paulo",
    "Asia/Tokyo", "Asia/Shanghai", "Asia/Singapore", "Asia/Kolkata",
    "Australia/Sydney", "Pacific/Auckland",
    "UTC",
    "Other (enter manually)",
]

TECH_LEVELS = [
    "Developer / Linux power user",
    "Technical (comfortable with CLI)",
    "Semi-technical (some experience)",
    "Non-technical",
]


def run(state: WizardState) -> bool | str:
    console.print(Panel(
        "Your agent will use this to address you correctly and adapt its style.\n"
        "This becomes [cyan]USER.md[/cyan] in your workspace.",
        title="[bold]About You[/bold]",
        border_style="blue",
        padding=(1, 2),
    ))

    # Name
    name = questionary.text(
        "What should your agent call you?",
        default=state.username or "",
    ).ask()
    if name is None:
        return False
    state.user_display_name = name.strip() or state.username

    # Timezone
    tz_choice = questionary.select(
        "Your timezone:",
        choices=TIMEZONES,
        default="Europe/Zurich",
    ).ask()
    if tz_choice is None:
        return False

    if tz_choice == "Other (enter manually)":
        tz_choice = questionary.text(
            "Enter timezone (IANA format, e.g. America/Toronto):",
            default="UTC",
        ).ask()
        if tz_choice is None:
            return False

    state.user_timezone = tz_choice.strip()

    # Tech level
    tech = questionary.select(
        "Technical background:",
        choices=TECH_LEVELS,
        default=TECH_LEVELS[0],
    ).ask()
    if tech is None:
        return False
    state.user_tech_level = tech

    return True
