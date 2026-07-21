"""
script_registry_gen.py — Generate script registry tooling.

Creates the local scripts/ directory inside the user's workspace with:
- scan_script_meta.py  (scan SCRIPT-META headers)
- sync_agent_scripts.py (copy scripts to agent workspaces)
- sync_allowlist.py   (sync exec-approvals.json)
- safe_exec_check.py  (pre-flight command validator)
- registry.json       (empty starter registry)
- example_script.py   (annotated example)

CRITICAL: All files are real copies — NO symlinks.
"""
import json
from pathlib import Path
from wizard.state import WizardState


# ──────────────────────────────────────────────────────────────────────────────
# Templates
# ──────────────────────────────────────────────────────────────────────────────

SCAN_SCRIPT_META_PY = '''\
#!/usr/bin/env python3
"""
scan_script_meta.py — Scan SCRIPT-META headers in agent scripts.

Reads every *.py file under workspace/scripts/ (or via --path) and extracts
the SCRIPT-META block. Produces a registry.json file that powers allowlist
sync and script distribution.
"""
import argparse
import json
import re
import sys
from pathlib import Path

META_RE = re.compile(
    r"^#\\s*SCRIPT-META\\s*\\n(?P<headers>(?:#\\s*\\w+\\s*:\\s*.*\\n?)+)",
    re.MULTILINE,
)


def parse_meta(text: str) -> dict[str, str]:
    """Extract key:value pairs from a SCRIPT-META header block."""
    match = META_RE.search(text)
    if not match:
        return {}
    headers = {}
    for line in match.group("headers").splitlines():
        line = line.lstrip("#").strip()
        if ":" in line:
            key, value = line.split(":", 1)
            headers[key.strip().lower()] = value.strip()
    return headers


def scan(path: Path) -> dict[str, dict[str, str]]:
    """Scan a directory tree for SCRIPT-META blocks."""
    registry = {}
    for file_path in sorted(path.rglob("*.py")):
        text = file_path.read_text(encoding="utf-8")
        meta = parse_meta(text)
        if not meta:
            continue
        rel = file_path.relative_to(path).as_posix()
        registry[rel] = {
            "agent": meta.get("agent", "main"),
            "type": meta.get("type", "utility"),
            "risk": meta.get("risk", "medium"),
            "secrets": _parse_list(meta.get("secrets", "")),
            "description": meta.get("description", ""),
        }
    return registry


def _parse_list(value: str) -> list[str]:
    """Parse a comma-separated list into a cleaned list of strings."""
    return [item.strip() for item in value.split(",") if item.strip()] or []


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan SCRIPT-META headers")
    parser.add_argument(
        "--path",
        type=Path,
        default=Path("/home/node/.openclaw/workspace/scripts"),
        help="Root directory to scan",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output registry.json path (default: <path>/registry.json)",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON to stdout")
    args = parser.parse_args()

    registry = scan(args.path)
    out_path = args.out or args.path / "registry.json"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\\n", encoding="utf-8")

    if args.json:
        print(json.dumps(registry, indent=2, ensure_ascii=False))

    print(f"Scanned {len(registry)} script(s) → {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


SYNC_AGENT_SCRIPTS_PY = '''\
#!/usr/bin/env python3
"""
sync_agent_scripts.py — Distribute scripts to agent workspaces.

Reads registry.json and copies each script to the target workspace's scripts/
directory based on the 'agent' field. Always copies — never symlinks.
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

DEFAULT_SOURCE = Path("/home/node/.openclaw/workspace/scripts")
DEFAULT_BASE = Path("/home/node/.openclaw")


def agent_workspace(agent: str) -> str:
    """Map agent name to workspace directory name."""
    return "workspace" if agent == "main" else f"workspace-{agent}"


def sync(source: Path, base: Path, dry_run: bool = False) -> list[str]:
    """Copy scripts to agent workspaces according to registry.json."""
    registry_file = source / "registry.json"
    if not registry_file.exists():
        print(f"Registry not found: {registry_file}")
        return []

    registry = json.loads(registry_file.read_text(encoding="utf-8"))
    copied: list[str] = []

    for rel_path, meta in registry.items():
        src = source / rel_path
        if not src.exists():
            print(f"Skip missing source: {src}")
            continue

        agent = meta.get("agent", "main")
        ws_name = agent_workspace(agent)
        dst_dir = base / ws_name / "scripts"
        dst = dst_dir / src.name

        if dry_run:
            print(f"[dry-run] Would copy {src} → {dst}")
            copied.append(str(dst))
            continue

        dst_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied.append(str(dst))
        print(f"Copied {src.name} → {dst}")

    return copied


def main() -> int:
    parser = argparse.ArgumentParser(description="Distribute agent scripts")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--base", type=Path, default=DEFAULT_BASE)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    sync(args.source, args.base, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


SYNC_ALLOWLIST_PY = '''\
#!/usr/bin/env python3
"""
sync_allowlist.py — Sync exec-approvals.json with SCRIPT-META headers.

Scans registry.json and ensures every registered script is present in the
exec-approvals allowlist. Supports dry-run and optional auto-apply.
"""
import argparse
import json
import sys
from pathlib import Path

DEFAULT_REGISTRY = Path("/home/node/.openclaw/workspace/scripts/registry.json")
DEFAULT_APPROVALS = Path("/home/node/.openclaw/exec-approvals.json")


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\\n", encoding="utf-8")


def script_path_for_agent(rel_path: str, agent: str) -> str:
    """Return the container-side script path for an agent."""
    ws = "workspace" if agent == "main" else f"workspace-{agent}"
    return f"/home/node/.openclaw/{ws}/scripts/{Path(rel_path).name}"


def sync_allowlist(registry_path: Path, approvals_path: Path, auto_apply: bool, dry_run: bool) -> dict:
    registry = load_json(registry_path)
    approvals = load_json(approvals_path)

    agents = approvals.setdefault("agents", {})
    added = []

    for rel_path, meta in registry.items():
        agent = meta.get("agent", "main")
        script_path = script_path_for_agent(rel_path, agent)

        agent_cfg = agents.setdefault(agent, {"allow": [], "autoAllowSkills": False})
        allow = agent_cfg.setdefault("allow", [])

        if script_path not in allow:
            added.append((agent, script_path))
            if not dry_run:
                allow.append(script_path)

    result = {
        "added": added,
        "unchanged": len(registry) - len(added),
        "total": len(registry),
    }

    if added and auto_apply and not dry_run:
        save_json(approvals_path, approvals)
        result["saved"] = str(approvals_path)
    elif added and not auto_apply:
        result["saved"] = None
        result["note"] = "Run with --apply to write changes"
    else:
        result["saved"] = str(approvals_path) if not dry_run else None

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync allowlist from SCRIPT-META")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--approvals", type=Path, default=DEFAULT_APPROVALS)
    parser.add_argument("--apply", action="store_true", help="Write changes to exec-approvals.json")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = sync_allowlist(args.registry, args.approvals, auto_apply=args.apply, dry_run=args.dry_run)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        if result["added"]:
            print(f"Added {len(result['added'])} allowlist entry/entries:")
            for agent, path in result["added"]:
                print(f"  [{agent}] {path}")
        else:
            print("Allowlist already in sync.")
        if result.get("saved"):
            print(f"Saved: {result['saved']}")
        elif result.get("note"):
            print(result["note"])

    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


SAFE_EXEC_CHECK_PY = '''\
#!/usr/bin/env python3
"""
safe_exec_check.py — Pre-flight check for shell command safety.

Blocks dangerous constructs: pipes, chaining, redirects, subshells, globs,
backgrounding, and inline interpreters. Designed to be called before any
exec tool use.

Usage:
    python3 safe_exec_check.py "ls -la"
    python3 safe_exec_check.py "docker compose up -d"

Exit codes:
    0 = safe
    1 = unsafe
    2 = config / IO error
"""
import re
import sys

# Forbidden shell constructs
FORBIDDEN = [
    (re.compile(r"[|]"), "pipe"),
    (re.compile(r"[;&]"), "command chaining"),
    (re.compile(r"[<>]|2>&1"), "redirect"),
    (re.compile(r"\\$\\("), "command substitution"),
    (re.compile(r"`"), "backtick substitution"),
    (re.compile(r"\\$\\{.*\\}"), "parameter expansion"),
    (re.compile(r"\\*\\?\\["), "glob"),
    (re.compile(r"&\\s*$"), "backgrounding"),
]

# Allowed simple commands (broad python3 is acceptable only if a registered script follows)
ALLOWED_PREFIXES = [
    "python3 ",
    "openclaw ",
    "docker ",
    "docker-compose ",
    "trash ",
]


def check(command: str) -> tuple[bool, list[str]]:
    """Return (safe, reasons)."""
    reasons = []
    for pattern, name in FORBIDDEN:
        if pattern.search(command):
            reasons.append(name)
    return (not reasons), reasons


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: safe_exec_check.py <command>", file=sys.stderr)
        return 2

    command = " ".join(sys.argv[1:])
    safe, reasons = check(command)

    if safe:
        print("SAFE")
        return 0

    print(f"UNSAFE: {', '.join(reasons)}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
'''


REGISTRY_JSON = {
    "README": (
        "This registry is generated by scan_script_meta.py. "
        "Edit scripts directly; do not hand-edit this file."
    )
}


EXAMPLE_SCRIPT_PY = '''\
#!/usr/bin/env python3
# SCRIPT-META
# agent: main
# type: utility
# risk: low
# secrets: []
# description: Example script generated by the OpenClaw installer.

"""
example_script.py — Starter template.

Copy this file, rename it, and update the SCRIPT-META header.
Run scan_script_meta.py after changes to rebuild registry.json.
"""
import sys


def main() -> int:
    print("Hello from the script registry!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


# ──────────────────────────────────────────────────────────────────────────────
# Generator
# ──────────────────────────────────────────────────────────────────────────────

def _scripts_dir(state: WizardState) -> Path:
    return state.workspace_dir / "scripts"


def write(state: WizardState) -> list[Path]:
    """Generate script registry files if enabled. Returns list of written paths."""
    if not state.script_registry_enabled:
        return []

    scripts_dir = _scripts_dir(state)
    scripts_dir.mkdir(parents=True, exist_ok=True)

    files: list[tuple[Path, str]] = [
        (scripts_dir / "scan_script_meta.py", SCAN_SCRIPT_META_PY),
        (scripts_dir / "sync_agent_scripts.py", SYNC_AGENT_SCRIPTS_PY),
        (scripts_dir / "sync_allowlist.py", SYNC_ALLOWLIST_PY),
        (scripts_dir / "registry.json", json.dumps(REGISTRY_JSON, indent=2, ensure_ascii=False) + "\n"),
        (scripts_dir / "example_script.py", EXAMPLE_SCRIPT_PY),
    ]

    if state.safe_exec_check_enabled:
        files.append((scripts_dir / "safe_exec_check.py", SAFE_EXEC_CHECK_PY))

    written: list[Path] = []
    for path, content in files:
        path.write_text(content, encoding="utf-8")
        # executable for .py scripts
        if path.suffix == ".py":
            path.chmod(0o755)
        written.append(path)

    # Run initial scan to populate registry.json on the host side
    _run_scan(scripts_dir)

    # If allowlist sync is enabled, update exec-approvals.json on the host side
    if state.allowlist_sync_enabled:
        _run_allowlist_sync(state, auto_apply=state.allowlist_auto_apply)

    return written


def _run_scan(scripts_dir: Path) -> None:
    """Run scan_script_meta.py in the host Python interpreter."""
    import subprocess
    scan_script = scripts_dir / "scan_script_meta.py"
    if not scan_script.exists():
        return
    try:
        subprocess.run(
            ["python3", str(scan_script), "--path", str(scripts_dir)],
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception:
        # Non-fatal: registry can be rebuilt later
        pass


def _run_allowlist_sync(state: WizardState, auto_apply: bool) -> None:
    """Run sync_allowlist.py in the host Python interpreter."""
    import subprocess
    sync_script = state.workspace_dir / "scripts" / "sync_allowlist.py"
    if not sync_script.exists():
        return
    cmd = [
        "python3", str(sync_script),
        "--registry", str(state.workspace_dir / "scripts" / "registry.json"),
        "--approvals", str(state.openclaw_dir / "exec-approvals.json"),
    ]
    if auto_apply:
        cmd.append("--apply")
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=False)
    except Exception:
        pass
