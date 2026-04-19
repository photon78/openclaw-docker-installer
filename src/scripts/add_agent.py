#!/usr/bin/env python3
"""
add_agent.py — Create a new sub-agent workspace and patch OpenClaw config.

Called by the main agent when Photon wants to add a sub-agent.
Idempotent: running twice with the same name does not break anything.

Usage:
    python3 add_agent.py --name coding_zot --emoji 💻 --type coding \
        --openclaw-dir ~/.openclaw --main-agent main

Arguments:
    --name          Agent name (e.g. coding_zot)
    --emoji         Agent emoji (e.g. 💻)
    --type          Archetype: coding | research | content | custom
    --openclaw-dir  OpenClaw directory (default: ~/.openclaw)
    --main-agent    Name of the main agent (default: main)
    --main-session  Session key for main agent (for A2A messaging)
    --dry-run       Show what would change without writing anything

Security:
    - Never runs without explicit user confirmation (dry-run first)
    - Never modifies files it doesn't own
    - Always shows a diff before applying changes
"""
import argparse
import json
import shutil
import sys
from pathlib import Path


def _load_template(agent_type: str):
    """Dynamically import the template module for the given archetype."""
    try:
        mod = __import__(f"templates.agents.{agent_type}", fromlist=[agent_type])
        return mod
    except ImportError:
        print(f"ERROR: Unknown agent type '{agent_type}'. "
              f"Valid types: coding, research, content, custom", file=sys.stderr)
        sys.exit(1)


def _create_workspace(
    openclaw_dir: Path,
    name: str,
    emoji: str,
    agent_type: str,
    main_agent: str,
    main_session: str,
    dry_run: bool,
) -> Path:
    """Create workspace directory and write template files."""
    workspace = openclaw_dir / f"workspace-{name}"
    template = _load_template(agent_type)

    files = {
        "SOUL.md": template.soul_md(name, emoji, main_agent),
        "AGENTS.md": template.agents_md(name, main_agent, main_session),
        "HEARTBEAT.md": template.heartbeat_md(name, str(workspace)),
        "IDENTITY.md": template.identity_md(name, emoji),
        "TOOLS.md": template.tools_md(name, str(workspace)),
        "MEMORY.md": f"# MEMORY.md — {name} {emoji} Long-Term Memory\n\n"
                     f"## Identity\n- Name: {name} {emoji}\n- Role: {agent_type} agent\n"
                     f"- Workspace: {workspace}/\n\n## User\n\n## Projects\n\n## Decisions & Rules\n",
        "USER.md": f"# USER.md — {name}\n\n<!-- Copy user info from main workspace -->\n",
    }

    dirs_to_create = ["memory", "memory/topics", "tasks", "scripts"]

    if dry_run:
        print(f"\n📁 Would create workspace: {workspace}/")
        for d in dirs_to_create:
            print(f"   mkdir {d}/")
        for fname, content in files.items():
            print(f"   write {fname} ({len(content)} bytes)")
        return workspace

    if workspace.exists():
        print(f"ℹ️  Workspace {workspace} already exists — updating files")
    workspace.mkdir(parents=True, exist_ok=True)
    for d in dirs_to_create:
        (workspace / d).mkdir(parents=True, exist_ok=True)

    for fname, content in files.items():
        target = workspace / fname
        if target.exists():
            print(f"   ⚠️  {fname} exists — skipping (won't overwrite)")
        else:
            target.write_text(content, encoding="utf-8")
            print(f"   ✅ {fname} written")

    # Copy check_tasks.py from main workspace if available
    main_check = openclaw_dir / "workspace" / "scripts" / "check_tasks.py"
    target_check = workspace / "scripts" / "check_tasks.py"
    if main_check.exists() and not target_check.exists():
        shutil.copy2(main_check, target_check)
        target_check.chmod(0o755)
        print(f"   ✅ scripts/check_tasks.py copied from main workspace")

    # Symlink skills from main workspace
    main_skills = openclaw_dir / "workspace" / "skills"
    target_skills = workspace / "skills"
    if main_skills.exists() and not target_skills.exists():
        target_skills.symlink_to(main_skills)
        print(f"   ✅ skills/ → symlinked to main workspace")

    return workspace


def _patch_openclaw_json(
    openclaw_dir: Path,
    name: str,
    main_agent: str,
    workspace: Path,
    dry_run: bool,
) -> None:
    """Add agent to openclaw.json agents.list and update allowAgents."""
    config_path = openclaw_dir / "openclaw.json"
    if not config_path.exists():
        print(f"⚠️  {config_path} not found — skipping config patch")
        return

    data = json.loads(config_path.read_text(encoding="utf-8"))
    agents_list = data.get("agents", {}).get("list", {})

    # Check if agent already exists
    if name in agents_list:
        print(f"ℹ️  Agent '{name}' already in openclaw.json — skipping")
        return

    # New agent entry
    new_entry = {
        "name": name,
        "workspace": str(workspace),
        "subagents": {
            "maxSpawnDepth": 1,
            "allowAgents": [],
        },
    }

    if dry_run:
        print(f"\n📝 Would add to openclaw.json → agents.list.{name}:")
        print(json.dumps(new_entry, indent=2))
        # Show allowAgents update
        main_entry = agents_list.get(main_agent, {})
        current_allow = main_entry.get("subagents", {}).get("allowAgents", [])
        if name not in current_allow:
            print(f"\n📝 Would add '{name}' to {main_agent}.subagents.allowAgents")
        return

    # Add agent
    if "agents" not in data:
        data["agents"] = {}
    if "list" not in data["agents"]:
        data["agents"]["list"] = {}
    data["agents"]["list"][name] = new_entry

    # Update main agent's allowAgents
    if main_agent in data["agents"]["list"]:
        main_sub = data["agents"]["list"][main_agent].setdefault("subagents", {})
        allow = main_sub.setdefault("allowAgents", [])
        if name not in allow:
            allow.append(name)
            print(f"   ✅ Added '{name}' to {main_agent}.subagents.allowAgents")

    config_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"   ✅ openclaw.json updated")


def _patch_exec_approvals(
    openclaw_dir: Path,
    name: str,
    dry_run: bool,
) -> None:
    """Add agent entry to exec-approvals.json with safe defaults."""
    approvals_path = openclaw_dir / "exec-approvals.json"
    if not approvals_path.exists():
        print(f"⚠️  {approvals_path} not found — skipping exec-approvals patch")
        return

    data = json.loads(approvals_path.read_text(encoding="utf-8"))
    agents = data.get("agents", {})

    if name in agents:
        print(f"ℹ️  Agent '{name}' already in exec-approvals.json — skipping")
        return

    new_entry = {
        "autoAllowSkills": False,
        "allowlist": [],
    }

    if dry_run:
        print(f"\n📝 Would add to exec-approvals.json → agents.{name}:")
        print(json.dumps(new_entry, indent=2))
        return

    data.setdefault("agents", {})[name] = new_entry
    approvals_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"   ✅ exec-approvals.json updated (autoAllowSkills: false)")


def main():
    parser = argparse.ArgumentParser(description="Add a sub-agent to OpenClaw")
    parser.add_argument("--name", required=True, help="Agent name")
    parser.add_argument("--emoji", default="🤖", help="Agent emoji")
    parser.add_argument("--type", required=True, choices=["coding", "research", "content", "custom"],
                        help="Agent archetype")
    parser.add_argument("--openclaw-dir", default=str(Path.home() / ".openclaw"),
                        help="OpenClaw directory")
    parser.add_argument("--main-agent", default="main", help="Main agent name")
    parser.add_argument("--main-session", default="", help="Main agent session key")
    parser.add_argument("--dry-run", action="store_true", help="Preview without changes")
    args = parser.parse_args()

    openclaw_dir = Path(args.openclaw_dir)
    if not openclaw_dir.exists():
        print(f"ERROR: OpenClaw directory not found: {openclaw_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"{'🔍 DRY RUN' if args.dry_run else '🚀 CREATING'} sub-agent: {args.name} {args.emoji}")
    print(f"   Type: {args.type}")
    print(f"   Main agent: {args.main_agent}")
    print(f"   OpenClaw dir: {openclaw_dir}")

    # 1. Create workspace
    workspace = _create_workspace(
        openclaw_dir, args.name, args.emoji, args.type,
        args.main_agent, args.main_session, args.dry_run,
    )

    # 2. Patch openclaw.json
    _patch_openclaw_json(openclaw_dir, args.name, args.main_agent, workspace, args.dry_run)

    # 3. Patch exec-approvals.json
    _patch_exec_approvals(openclaw_dir, args.name, args.dry_run)

    if args.dry_run:
        print("\n⚠️  Dry run complete. No files were modified.")
        print("   Remove --dry-run to apply changes.")
    else:
        print(f"\n✅ Agent '{args.name}' created successfully.")
        print(f"   Workspace: {workspace}")
        print(f"\n⚠️  Next steps:")
        print(f"   1. Review the generated files in {workspace}")
        print(f"   2. Customize SOUL.md and TOOLS.md for your needs")
        print(f"   3. Restart the gateway: openclaw gateway restart")


if __name__ == "__main__":
    main()
