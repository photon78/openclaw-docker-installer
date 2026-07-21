"""
Step 7: Script Registry configuration.

Controls whether the installer sets up a local scripts/ directory with
SCRIPT-META-based registry tooling, automatic allowlist syncing, and the
safe-exec pre-check template.
"""
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from wizard.state import WizardState
from wizard.ui import confirm_select

console = Console()


def run(state: WizardState) -> bool | str:
    """Prompt for Script Registry options.

    Returns True to continue, False to abort, "back" to go to previous step.
    """
    console.print(Panel.fit(
        "[bold]Script Registry[/bold]\n\n"
        "[dim]The script registry keeps your agent scripts organized:\n"
        "- A local scripts/ folder inside your workspace\n"
        "- SCRIPT-META headers so the installer knows agent, risk, and secrets\n"
        "- Automatic allowlist sync so new scripts are pre-approved\n"
        "- Optional safe-exec pre-check template for command validation[/dim]",
        border_style="cyan",
    ))
    console.print()

    # Enable / disable registry entirely
    enabled = confirm_select(
        "Set up a local script registry?",
        default=True,
    )
    if enabled is None:
        return False
    state.script_registry_enabled = enabled

    if not enabled:
        console.print("[dim]Script registry skipped. You can set it up manually later.[/dim]\n")
        state.script_sync_enabled = False
        state.allowlist_sync_enabled = False
        state.allowlist_auto_apply = False
        state.safe_exec_check_enabled = False
        return True

    console.print("[green]✓[/green] Script registry enabled.\n")

    # Sync options
    console.print(
        "[dim]The registry can keep your exec-approvals.json in sync with SCRIPT-META headers.\n"
        "Recommended: enabled with auto-apply, so you don't have to approve every new script.[/dim]\n"
    )

    sync_enabled = confirm_select(
        "Enable script registry sync?",
        default=True,
    )
    if sync_enabled is None:
        return False
    state.script_sync_enabled = sync_enabled

    if not sync_enabled:
        console.print("[dim]Registry sync disabled. Scripts will be copied, but allowlist is not updated.[/dim]\n")
        state.allowlist_sync_enabled = False
        state.allowlist_auto_apply = False
        state.safe_exec_check_enabled = False
        return True

    allowlist_sync = confirm_select(
        "Sync allowlist entries from SCRIPT-META headers?",
        default=True,
    )
    if allowlist_sync is None:
        return False
    state.allowlist_sync_enabled = allowlist_sync

    if allowlist_sync:
        auto_apply = confirm_select(
            "Auto-apply missing allowlist entries? (Opt-out)",
            default=True,
        )
        if auto_apply is None:
            return False
        state.allowlist_auto_apply = auto_apply
    else:
        state.allowlist_auto_apply = False

    safe_exec = confirm_select(
        "Install safe-exec pre-check template?",
        default=True,
    )
    if safe_exec is None:
        return False
    state.safe_exec_check_enabled = safe_exec

    # Summary
    console.print()
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_row("[dim]Registry[/dim]", "[bold]enabled[/bold]")
    table.add_row("[dim]Sync[/dim]", "[bold]enabled[/bold]" if state.script_sync_enabled else "[dim]disabled[/dim]")
    table.add_row("[dim]Allowlist sync[/dim]", "[bold]enabled[/bold]" if state.allowlist_sync_enabled else "[dim]disabled[/dim]")
    table.add_row("[dim]Auto-apply[/dim]", "[bold]enabled[/bold]" if state.allowlist_auto_apply else "[dim]disabled[/dim]")
    table.add_row("[dim]Safe-exec check[/dim]", "[bold]enabled[/bold]" if state.safe_exec_check_enabled else "[dim]disabled[/dim]")
    console.print(table)
    console.print()

    return True
