"""
workspace_bootstrap.py — Bootstrap the OpenClaw workspace from installer templates.
Copies AGENTS.md, SOUL.md, MEMORY.md, USER.md, BOOTSTRAP.md to the workspace.
Skips files that already exist (idempotent).
"""
from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path

from rich.console import Console
from rich.table import Table

from wizard.state import WizardState

console = Console()

# Templates live next to this file
TEMPLATES_DIR = Path(__file__).parent / "templates"

TEMPLATE_FILES = [
    "AGENTS.md",
    "SOUL.md",
    "MEMORY.md",
    "USER.md",
    "BOOTSTRAP.md",
]


@dataclass
class BootstrapResult:
    ok: bool
    written: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def run(state: WizardState) -> BootstrapResult:
    """Copy workspace templates. Skips files that already exist."""
    workspace = state.workspace_dir
    workspace.mkdir(parents=True, exist_ok=True)

    result = BootstrapResult(ok=True)

    for filename in TEMPLATE_FILES:
        src = TEMPLATES_DIR / filename
        dst = workspace / filename

        if not src.exists():
            result.errors.append(f"Template missing: {src}")
            result.ok = False
            continue

        if dst.exists():
            result.skipped.append(filename)
        else:
            shutil.copy2(src, dst)
            result.written.append(filename)

    _print_summary(result)
    return result


def _print_summary(result: BootstrapResult) -> None:
    console.print()
    console.print("[bold]Workspace bootstrap:[/bold]")
    table = Table(show_header=False, box=None, padding=(0, 1))
    for f in result.written:
        table.add_row("[green]✓[/green]", f, "[dim]created[/dim]")
    for f in result.skipped:
        table.add_row("[dim]·[/dim]", f, "[dim]already exists — skipped[/dim]")
    for e in result.errors:
        table.add_row("[red]✗[/red]", e, "")
    console.print(table)
