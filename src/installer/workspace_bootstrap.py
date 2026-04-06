"""
workspace_bootstrap.py — Bootstrap the OpenClaw workspace with safe defaults.
Writes AGENTS.md, SOUL.md, MEMORY.md, USER.md if they don't exist.
These are templates — the user/agent will fill them in on first run.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from rich.console import Console
from rich.table import Table

from wizard.state import WizardState

console = Console()

# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

AGENTS_MD = """\
# AGENTS.md

## Identity
- Name: *(set by agent on first run)*
- Role: Personal assistant

## Behaviour
- Language: *(set by user)*
- Tone: direct, helpful, no fluff

## Security
- exec policy: allowlist (see exec-approvals.json)
- No `rm`, `dd`, `chmod 777` — use `trash` instead
- No deployment without explicit user approval
- No Apache/nginx reload without user confirmation

## Skills
Shared skills live in `workspace/skills/` — loaded automatically by the agent.
Private skills live in `workspace/skills-private/` — not shared.
"""

SOUL_MD = """\
# SOUL.md

*Edit this file to define your agent's personality and working style.*

## Role
*(Describe what this agent does — assistant, coder, researcher, ...)*

## Character
*(How does it communicate? Direct? Warm? Technical? Casual?)*

## Language
*(Default language for replies)*

## Boundaries
- *(Add any hard rules here)*
"""

MEMORY_MD = """\
# MEMORY.md — Long-term memory

## About me
- Name: *(set on first run)*
- Workspace: /home/node/.openclaw/workspace/

## About the user
- Name: *(set on first run)*

## Projects
*(Add active projects here)*

## Decisions & Rules
*(Add important decisions here)*
"""

USER_MD = """\
# USER.md — About the user

- Name: *(fill in)*
- Timezone: *(fill in)*
- Preferred language: *(fill in)*
- Notes: *(fill in)*
"""

BOOTSTRAP_MD = """\
# BOOTSTRAP.md

You just started for the first time. Introduce yourself and ask the user:
1. What should I call you?
2. What's your name?
3. What language do you prefer?
4. What do you want me to help with?

After the conversation, update IDENTITY.md, USER.md, and SOUL.md.
Then delete this file.
"""

TEMPLATES: dict[str, str] = {
    "AGENTS.md":    AGENTS_MD,
    "SOUL.md":      SOUL_MD,
    "MEMORY.md":    MEMORY_MD,
    "USER.md":      USER_MD,
    "BOOTSTRAP.md": BOOTSTRAP_MD,
}


@dataclass
class BootstrapResult:
    ok: bool
    written: list[str]
    skipped: list[str]


def run(state: WizardState) -> BootstrapResult:
    """Write workspace template files. Skips files that already exist."""
    workspace = state.workspace_dir
    workspace.mkdir(parents=True, exist_ok=True)

    written: list[str] = []
    skipped: list[str] = []

    for filename, content in TEMPLATES.items():
        target = workspace / filename
        if target.exists():
            skipped.append(filename)
        else:
            target.write_text(content)
            written.append(filename)

    # Summary
    console.print()
    table = Table(show_header=False, box=None, padding=(0, 1))
    for f in written:
        table.add_row("[green]✓[/green]", f, "[dim]created[/dim]")
    for f in skipped:
        table.add_row("[dim]·[/dim]", f, "[dim]already exists — skipped[/dim]")
    console.print(table)

    return BootstrapResult(ok=True, written=written, skipped=skipped)
