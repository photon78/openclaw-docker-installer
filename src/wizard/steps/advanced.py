"""
advanced.py — Optional advanced configuration step.
Covers: custom OpenClaw image tag, extra APT packages.
"""
import questionary
from rich.console import Console
from rich.panel import Panel

from wizard.state import WizardState

console = Console()

# Known-good image choices
_IMAGE_CHOICES = [
    questionary.Choice(
        "extended-stable  (recommended — slow-moving, well-tested)",
        value="",
    ),
    questionary.Choice(
        "latest           (tracks stable releases)",
        value="ghcr.io/openclaw/openclaw:latest",
    ),
    questionary.Choice(
        "Custom image ref …",
        value="__custom__",
    ),
]


def run(state: WizardState) -> bool | str:
    """Ask for advanced options. Returns True to continue, False to abort, 'back'."""
    console.print()
    console.print(Panel(
        "[bold]Advanced options[/bold]\n\n"
        "These settings are optional. Press Enter to accept defaults.\n\n"
        "[dim]• Image tag: which OpenClaw Docker image to use\n"
        "• APT packages: extra packages installed into the container at start[/dim]",
        border_style="magenta",
        padding=(1, 2),
    ))

    # ── Image tag ──────────────────────────────────────────────────────────
    img_choice = questionary.select(
        "OpenClaw image:",
        choices=_IMAGE_CHOICES,
        default=_IMAGE_CHOICES[0],
    ).ask()

    if img_choice is None:
        return False

    if img_choice == "__custom__":
        custom_img = questionary.text(
            "Full image reference (e.g. ghcr.io/openclaw/openclaw:2026.9.2):",
        ).ask()
        if not custom_img:
            return False
        state.openclaw_image_override = custom_img.strip()
        console.print(f"[green]✓[/green] Image override: [cyan]{state.openclaw_image_override}[/cyan]")
    else:
        state.openclaw_image_override = img_choice  # "" = use extended-stable default
        if img_choice:
            console.print(f"[green]✓[/green] Image: [cyan]{img_choice}[/cyan]")
        else:
            console.print("[green]✓[/green] Image: [cyan]extended-stable[/cyan] (default)")

    # ── APT packages ───────────────────────────────────────────────────────
    console.print()
    want_pkgs = questionary.confirm(
        "Install extra APT packages into the container? (e.g. wacli, ffmpeg, git-lfs)",
        default=False,
    ).ask()

    if want_pkgs is None:
        return False

    if want_pkgs:
        raw = questionary.text(
            "Package names (space-separated):",
            instruction="e.g. wacli ffmpeg git-lfs",
        ).ask()
        if not raw:
            return False
        state.apt_packages = raw.strip().split()
        console.print(f"[green]✓[/green] APT packages: [cyan]{' '.join(state.apt_packages)}[/cyan]")
        console.print(
            "[dim]These will be passed as OPENCLAW_IMAGE_APT_PACKAGES to the container.\n"
            "The container installs them on every start.[/dim]"
        )
    else:
        state.apt_packages = []

    return True
