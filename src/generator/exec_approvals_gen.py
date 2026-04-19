"""
exec_approvals_gen.py — Generate exec-approvals.json from WizardState.
Security profile determines allowlist tier.
All paths use Path.home() — no hardcoded usernames.
"""
import json
import secrets
from pathlib import Path
from wizard.state import WizardState

def _script(name: str, state: "WizardState") -> str:
    return str(state.scripts_dir / name)


def _skill(path: str, state: "WizardState") -> str:
    return str(state.workspace_dir / "skills" / path)


def _defaults_allowlist(state: WizardState) -> list[dict]:
    """Minimal allowlist for cron/isolated sessions.

    Shell tools (ls, cat, grep, find, head, tail, wc, sort …) are intentionally
    excluded. Agents use read/edit/write tools instead of shell commands.
    Shell tools in the allowlist are an unnecessary attack surface.
    """
    return [
        {"pattern": "/usr/bin/python3",      "id": "d-python3-01"},
        {"pattern": "/usr/bin/df",            "id": "d-df-01"},
        {"pattern": "/usr/bin/curl",          "id": "d-curl-01"},
        {"pattern": _script("health_check.py", state),    "id": "d-health-check-01"},
        {"pattern": _script("morning_briefing.py", state),"id": "d-morning-briefing-01"},
        {"pattern": _script("daily_digest.py", state),    "id": "d-daily-digest-01"},
        {"pattern": _script("memory_digest.py", state),   "id": "d-memory-digest-01"},
        {"pattern": _script("audit_integrity.py", state), "id": "d-audit-integrity-01"},
        {"pattern": _script("check_tasks.py", state),     "id": "d-check-tasks-01"},
    ]


def _main_allowlist(profile: str, state: WizardState) -> list[dict]:
    """Allowlist for the main agent (elevated tier).

    Shell tools (ls, cat, grep, find, head, tail, wc, sort, bash …) are
    intentionally excluded. Agents use read/edit/write tools instead.
    Bash in the allowlist is a shell-injection risk.
    """
    base = [
        {"pattern": "/usr/bin/python3",   "id": "m-python3-01"},
        {"pattern": "/usr/bin/git",       "id": "m-git-01"},
        {"pattern": "/usr/bin/df",        "id": "m-df-01"},
        {"pattern": "/usr/bin/du",        "id": "m-du-01"},
        {"pattern": "/usr/bin/free",      "id": "m-free-01"},
        {"pattern": "/usr/bin/ps",        "id": "m-ps-01"},
        {"pattern": "/usr/bin/uptime",    "id": "m-uptime-01"},
        {"pattern": "/usr/bin/curl",      "id": "m-curl-01"},
        {"pattern": "/usr/bin/systemctl", "id": "m-systemctl-01"},
        {"pattern": "/usr/bin/journalctl","id": "m-journalctl-01"},
        {"pattern": "/usr/bin/rsync",     "id": "m-rsync-01"},
        {"pattern": "/usr/bin/trash",     "id": "m-trash-01"},
        {"pattern": "/usr/bin/mkdir",     "id": "m-mkdir-01"},
        {"pattern": "/usr/bin/ln",        "id": "m-ln-01"},
        {"pattern": "/usr/bin/jq",        "id": "m-jq-01"},
        {"pattern": _script("health_check.py", state),    "id": "m-health-check-01"},
        {"pattern": _script("audit_integrity.py", state), "id": "m-audit-integrity-01"},
        {"pattern": _script("morning_briefing.py", state),"id": "m-morning-briefing-01"},
        {"pattern": _script("check_tasks.py", state),     "id": "m-check-tasks-01"},
        {"pattern": _skill("web-search/search.py", state),     "id": "m-web-search-01"},
        {"pattern": _skill("docs-summarize/summarize.py", state), "id": "m-docs-summarize-01"},
    ]
    return base


def generate(state: WizardState) -> dict:
    """Return exec-approvals.json content as dict."""
    # Generate a secure random socket token
    # INSTALLER: this token is generated once at install time
    socket_token = secrets.token_urlsafe(32)

    config = {
        "version": 1,
        "socket": {
            "path": str(state.openclaw_dir / "exec-approvals.sock"),
            "token": socket_token,  # INSTALLER: generated at installation
        },
        "defaults": {
            "security": "allowlist",
            "ask": "on-miss",
            "askFallback": "deny",
            "allowlist": _defaults_allowlist(state),
        },
        "agents": {
            "main": {
                "security": "allowlist",
                "ask": "on-miss",
                "askFallback": "deny",
                "autoAllowSkills": state.auto_allow_skills,
                "allowlist": _main_allowlist(state.security_profile, state),
            }
        },
    }

    return config


def write(state: WizardState) -> Path:
    """Write exec-approvals.json to openclaw_dir. Returns path."""
    target = state.openclaw_dir / "exec-approvals.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(generate(state), indent=2) + "\n")
    target.chmod(0o600)
    return target
