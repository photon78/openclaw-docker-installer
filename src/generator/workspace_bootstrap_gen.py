"""
workspace_bootstrap_gen.py — Create workspace directory with template files.

Generates SOUL.md, AGENTS.md, HEARTBEAT.md, IDENTITY.md, MEMORY.md, USER.md,
BOOTSTRAP.md, TOOLS.md, and scripts/check_tasks.py from Jinja2 templates.

CRITICAL: All files are real copies — NO symlinks.
OpenClaw does not follow symlinks during Project Context Injection.
Symlinked files are reported as [MISSING] and never injected into the agent context.
The only exception: skills/ (directory symlink) is acceptable.
"""
import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from wizard.state import WizardState

# Bundled skills live next to the installer package
_SKILLS_SRC = Path(__file__).parent.parent / "installer" / "templates" / "skills"
_TEMPLATES_DIR = Path(__file__).parent.parent / "installer" / "templates" / "workspace"

_PERSONA_DESCRIPTIONS = {
    "direct":   "Direct and technical — no dumbing down. Gets to the point.",
    "formal":   "Professional and structured — formal language, precise.",
    "friendly": "Warm and encouraging — approachable, helpful.",
    "skip":     "Neutral assistant — balanced and straightforward.",
}

_STYLE_MAP = {
    "direct": "Direct and technical — no dumbing down",
    "formal": "Formal and professional",
    "friendly": "Warm and approachable",
    "skip": "Neutral",
}


def _jinja_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(_TEMPLATES_DIR),
        autoescape=select_autoescape(default_for_string=False),
        keep_trailing_newline=True,
    )


def _render(template_name: str, **context) -> str:
    env = _jinja_env()
    template = env.get_template(template_name)
    return template.render(**context)


def _soul_md(state: WizardState) -> str:
    persona_desc = _PERSONA_DESCRIPTIONS.get(state.persona_style, "Neutral assistant.")
    channel_hint = state.channel if state.channel else "your configured channel"
    check_tasks = state.container_scripts_dir / "check_tasks.py"
    skills_dir = state.container_workspace_dir / "skills"
    mistral_skills_hint = ""
    if state.mistral_api_key:
        mistral_skills_hint = (
            f"- **mistral-ocr** → `python3 {skills_dir}/mistral-ocr/ocr.py`\n"
            f"- **mistral-translate** → `python3 {skills_dir}/mistral-translate/translate.py`\n"
            f"- **mistral-transcribe** → `python3 {skills_dir}/mistral-transcribe/transcribe.py`\n"
            f"- **mistral-vision** → `python3 {skills_dir}/mistral-vision/vision.py`\n"
        )
    return _render(
        "SOUL.md.j2",
        state=state,
        persona_desc=persona_desc,
        channel_hint=channel_hint,
        check_tasks=check_tasks,
        skills_dir=skills_dir,
        mistral_skills_hint=mistral_skills_hint,
    )


def _agents_md(state: WizardState) -> str:
    check_tasks = state.container_scripts_dir / "check_tasks.py"
    scripts_shared = state.container_scripts_dir / "shared"
    return _render(
        "AGENTS.md.j2",
        state=state,
        check_tasks=check_tasks,
        scripts_shared=scripts_shared,
    )


def _heartbeat_md(state: WizardState) -> str:
    check_tasks = state.container_scripts_dir / "check_tasks.py"
    return _render("HEARTBEAT.md.j2", state=state, check_tasks=check_tasks)


def _identity_md(state: WizardState) -> str:
    persona_desc = _PERSONA_DESCRIPTIONS.get(state.persona_style, "Neutral")
    return _render(
        "IDENTITY.md.j2",
        state=state,
        persona_desc=persona_desc,
    )


def _memory_md(state: WizardState) -> str:
    return _render("MEMORY.md.j2", state=state)


def _user_md(state: WizardState) -> str:
    name = state.user_display_name or state.username
    tz = state.user_timezone or "UTC"
    tech = state.user_tech_level or "<!-- add your technical background -->"
    style = _STYLE_MAP.get(state.persona_style, "Neutral")
    return _render(
        "USER.md.j2",
        state=state,
        name=name,
        tz=tz,
        tech=tech,
        style=style,
    )


def _bootstrap_md(state: WizardState) -> str:
    check_tasks = state.container_scripts_dir / "check_tasks.py"
    return _render("BOOTSTRAP.md.j2", state=state, check_tasks=check_tasks)


def _tools_md(state: WizardState) -> str:
    skills_dir = state.container_workspace_dir / "skills"
    scripts_dir = state.container_scripts_dir
    mistral_block = ""
    if state.mistral_api_key:
        mistral_block = (
            f"\n\n### Mistral Skills\n\n"
            f"| Skill | Command | Purpose |\n"
            f"|-------|---------|--------|\n"
            f"| **mistral-translate** | `python3 {skills_dir}/mistral-translate/translate.py` | Translations |\n"
            f"| **mistral-ocr** | `python3 {skills_dir}/mistral-ocr/ocr.py` | Image → text |\n"
            f"| **mistral-transcribe** | `python3 {skills_dir}/mistral-transcribe/transcribe.py` | Audio → text |\n"
            f"| **mistral-vision** | `python3 {skills_dir}/mistral-vision/vision.py` | Image analysis |\n\n"
            f"> Mistral skills require MISTRAL_API_KEY in .env. Always prefer for media tasks."
        )
    return _render(
        "TOOLS.md.j2",
        state=state,
        skills_dir=skills_dir,
        scripts_dir=scripts_dir,
        mistral_block=mistral_block,
    )


def _check_tasks_py(state: WizardState) -> str:
    """Generate check_tasks.py — preserve Python f-strings, only replace tasks_dir."""
    tasks_dir = state.container_workspace_dir / "tasks"
    template_path = _TEMPLATES_DIR / "check_tasks.py.j2"
    template = template_path.read_text(encoding="utf-8")
    return template.replace("{tasks_dir}", str(tasks_dir))


def _cron_setup_task_md(state: WizardState) -> str:  # noqa: ARG001
    return _render("cron-setup-task.md.j2")


def _health_check_py(state: WizardState) -> str:
    """Generate health_check.py — preserve Python f-strings, only replace openclaw_dir."""
    openclaw_dir = state.CONTAINER_OPENCLAW_DIR
    template_path = _TEMPLATES_DIR / "health_check.py.j2"
    template = template_path.read_text(encoding="utf-8")
    return template.replace("{openclaw_dir}", str(openclaw_dir))


_FILE_GENERATORS = [
    ("SOUL.md", _soul_md),
    ("AGENTS.md", _agents_md),
    ("HEARTBEAT.md", _heartbeat_md),
    ("IDENTITY.md", _identity_md),
    ("MEMORY.md", _memory_md),
    ("USER.md", _user_md),
    ("BOOTSTRAP.md", _bootstrap_md),
    ("TOOLS.md", _tools_md),
    ("tasks/cron-setup.md", _cron_setup_task_md),
]

_SCRIPT_GENERATORS = [
    ("scripts/check_tasks.py", _check_tasks_py, 0o755),
    ("scripts/health_check.py", _health_check_py, 0o755),
]


def _copy_skills(target: Path) -> None:
    """Copy bundled skills into workspace/skills as real files via directory symlink."""
    skills_target = target / "skills"
    if skills_target.exists() or skills_target.is_symlink():
        return
    if _SKILLS_SRC.exists():
        shutil.copytree(_SKILLS_SRC, skills_target, symlinks=False)


def generate(state: WizardState) -> list[Path]:
    """Create workspace directory and write all workspace files. Returns list of paths."""
    return write(state)


def write(state: WizardState) -> list[Path]:
    """Write all workspace files to state.workspace_dir. Returns list of paths."""
    workspace = state.workspace_dir
    workspace.mkdir(parents=True, exist_ok=True)

    # Ensure required subdirectories exist even when empty
    for subdir in ("memory/topics", "tasks", "scripts"):
        (workspace / subdir).mkdir(parents=True, exist_ok=True)

    written: list[Path] = []

    for rel, fn in _FILE_GENERATORS:
        path = workspace / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(fn(state), encoding="utf-8")
        written.append(path)

    for rel, fn, mode in _SCRIPT_GENERATORS:
        path = workspace / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(fn(state), encoding="utf-8")
        path.chmod(mode)
        written.append(path)

    _copy_skills(workspace)
    return written
