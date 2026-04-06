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

# Files that are copied as-is (no substitution)
STATIC_FILES = ["AGENTS.md", "MEMORY.md", "USER.md", "BOOTSTRAP.md"]

# Files that get variable substitution
TEMPLATED_FILES = ["SOUL.md"]

TEMPLATE_FILES = STATIC_FILES + TEMPLATED_FILES

# Character descriptions per persona style
PERSONA_DESCRIPTIONS = {
    "direct": (
        "- **Direct:** No hedging, no filler sentences\n"
        "- **Opinionated:** If something is unsafe — say so, with reasoning\n"
        "- **Honest:** \"I don't know\" beats inventing an answer\n"
        "- **Arrogance:** User has expertise — no dumbing-down\n"
        "- **Errors:** Admit them, don't hide them"
    ),
    "formal": (
        "- **Professional:** Structured, precise, measured\n"
        "- **Polite:** Clear and respectful, not warm\n"
        "- **Honest:** Acknowledge uncertainty explicitly\n"
        "- **Errors:** Report them factually without drama"
    ),
    "friendly": (
        "- **Warm:** Approachable, casual, easy to talk to\n"
        "- **Helpful:** Proactive with suggestions\n"
        "- **Honest:** \"I don't know\" is fine — just say so\n"
        "- **Errors:** Own them quickly, move on"
    ),
    "skip": "- *(Edit this section in SOUL.md to define your agent's character)*",
}


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
        elif filename in TEMPLATED_FILES:
            content = src.read_text(encoding="utf-8")
            content = _apply_substitutions(content, state)
            dst.write_text(content, encoding="utf-8")
            shutil.copystat(src, dst)
            result.written.append(filename)
        else:
            shutil.copy2(src, dst)
            result.written.append(filename)

    # Skills: copy template skills into workspace/skills/ (idempotent)
    _bootstrap_skills(workspace, result)

    _print_summary(result)
    return result


def _bootstrap_skills(workspace: Path, result: BootstrapResult) -> None:
    """Copy bundled skills to workspace/skills/. Skip existing."""
    skills_src = TEMPLATES_DIR / "skills"
    if not skills_src.exists():
        return
    skills_dst = workspace / "skills"
    skills_dst.mkdir(parents=True, exist_ok=True)

    for skill_dir in sorted(skills_src.iterdir()):
        if not skill_dir.is_dir():
            continue
        target = skills_dst / skill_dir.name
        if target.exists():
            result.skipped.append(f"skills/{skill_dir.name}")
        else:
            shutil.copytree(skill_dir, target)
            result.written.append(f"skills/{skill_dir.name}")


def _apply_substitutions(content: str, state: WizardState) -> str:
    """Replace template placeholders with values from WizardState."""
    style = getattr(state, "persona_style", "direct")
    char_block = PERSONA_DESCRIPTIONS.get(style, PERSONA_DESCRIPTIONS["direct"])

    replacements = {
        "{{AGENT_NAME}}": state.agent_name or "main",
        "{{AGENT_EMOJI}}": state.agent_emoji or "🤖",
        "{{LLM_STANDARD}}": state.llm_standard,
        "{{LLM_POWER}}": state.llm_power,
        "{{LLM_BUDGET}}": state.llm_budget,
        "{{LLM_MEDIA}}": state.llm_media,
        "{{CHARACTER_BLOCK}}": char_block,
    }
    for key, value in replacements.items():
        content = content.replace(key, value)
    return content


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
