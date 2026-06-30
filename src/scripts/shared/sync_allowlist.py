#!/usr/bin/env python3
"""
sync_allowlist.py — Sync SCRIPT-META registry with exec-approvals.json.

SCRIPT-META:
  agent: shared
  type: utility
  risk: low
  description: "Sync SCRIPT-META registry with exec-approvals.json — shows missing scripts per agent, optional --apply"

Usage:
    python3 sync_allowlist.py [--apply] [--strict]
    python3 sync_allowlist.py --registry <path> --approvals <path>

Defaults (relative to this script's location):
    registry:  <scripts_dir>/registry.json
    approvals: <scripts_dir>/../../exec-approvals.json
               (i.e. workspace root ../../ = openclaw_dir)
"""

import json
import argparse
from pathlib import Path

# scripts_dir = directory containing this script
_SCRIPTS_DIR = Path(__file__).parent.resolve()

DEFAULT_REGISTRY = _SCRIPTS_DIR / "registry.json"
DEFAULT_APPROVALS = _SCRIPTS_DIR.parent.parent / "exec-approvals.json"

# Agents that need an allowlist (shared = no dedicated agent)
TRACKED_AGENTS = {"main", "coding_zot", "valere", "sionis", "sentinel", "research_zot"}


def load_json(path: Path) -> dict | None:
    if not path.exists():
        print(f"ERROR: {path} nicht gefunden")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: Ungültiges JSON in {path}: {e}")
        return None


def generate_id(agent: str, script_name: str) -> str:
    """Generate an allowlist ID from agent prefix + script name."""
    prefixes = {
        "main": "m",
        "coding_zot": "cz",
        "valere": "v",
        "sionis": "si",
        "sentinel": "s",
        "research_zot": "rz",
    }
    prefix = prefixes.get(agent, agent[:2])
    slug = Path(script_name).stem.replace("_", "-")
    return f"{prefix}-{slug}-01"


# Patterns that signal broad python3 access
BROAD_PYTHON_PATTERNS = {
    "/usr/bin/python3", "/usr/bin/python3.13", "/usr/bin/python",
    "python3", "python",
}


def has_broad_python(agent_data: dict) -> bool:
    """True if the agent already has a broad python3 pattern."""
    for entry in agent_data.get("allowlist", []):
        if entry.get("pattern", "") in BROAD_PYTHON_PATTERNS:
            return True
    return False


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Compare SCRIPT-META registry with exec-approvals.json"
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=DEFAULT_REGISTRY,
        help=f"Path to registry.json (default: {DEFAULT_REGISTRY})",
    )
    parser.add_argument(
        "--approvals",
        type=Path,
        default=DEFAULT_APPROVALS,
        help=f"Path to exec-approvals.json (default: {DEFAULT_APPROVALS})",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write missing entries directly into exec-approvals.json",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Show all missing scripts, even if broad python3 is present (default: hide covered scripts)",
    )
    args = parser.parse_args(argv)

    registry = load_json(args.registry)
    approvals = load_json(args.approvals)
    if registry is None or approvals is None:
        return 1

    # Determine openclaw base from approvals path (parent of exec-approvals.json)
    oclaw_base = args.approvals.parent

    # Collect allowlist patterns + broad-python flag per agent
    allowlist_patterns: dict[str, set[str]] = {}
    broad_python_agents: set[str] = set()
    for agent, agent_data in approvals.get("agents", {}).items():
        patterns = {e["pattern"] for e in agent_data.get("allowlist", [])}
        allowlist_patterns[agent] = patterns
        if has_broad_python(agent_data):
            broad_python_agents.add(agent)

    # Find missing scripts grouped by agent
    missing: dict[str, list[dict]] = {}
    covered: dict[str, int] = {}  # agent -> count of scripts covered by broad-python
    total_missing = 0

    for script_name, meta in registry.get("scripts", {}).items():
        agent = meta.get("agent", "")
        if agent not in TRACKED_AGENTS:
            continue  # shared or unknown — skip

        rel_path = meta.get("path", "")
        if not rel_path:
            continue

        # Registry stores paths relative to scripts_dir's parent → resolve to absolute
        script_path = str(oclaw_base / rel_path)

        agent_patterns = allowlist_patterns.get(agent, set())
        if script_path not in agent_patterns:
            # Covered by broad python3?
            if agent in broad_python_agents and not args.strict:
                covered[agent] = covered.get(agent, 0) + 1
                continue
            missing.setdefault(agent, []).append({
                "name": script_name,
                "path": script_path,
                "risk": meta.get("risk", "?"),
                "type": meta.get("type", "?"),
            })
            total_missing += 1

    # Print report
    mode = "strict" if args.strict else "default"
    print(f"=== sync_allowlist report [{mode}] ===")

    if not args.strict and broad_python_agents:
        covered_agents = sorted(broad_python_agents)
        print(f"\nℹ️  Broad python3 aktiv: {', '.join(covered_agents)}")
        for agent in covered_agents:
            n = covered.get(agent, 0)
            if n:
                print(f"   ✅ {agent}: {n} Scripts gedeckt (--strict zeigt alle)")

    if not missing:
        print("\n✅ Keine echten Lücken gefunden.")
    else:
        for agent in sorted(missing.keys()):
            scripts = missing[agent]
            print(f"\nAgent: {agent} — {len(scripts)} fehlend")
            for s in sorted(scripts, key=lambda x: x["risk"]):
                print(f"  [{s['risk']:8}] {s['name']:40} {s['path']}")
    print(f"\nTotal echte Lücken: {total_missing}")

    # --apply: write missing entries
    if args.apply and missing:
        added = 0
        for agent, scripts in missing.items():
            agent_block = approvals.setdefault("agents", {}).setdefault(
                agent, {"allowlist": []}
            )
            for s in scripts:
                entry = {"pattern": s["path"], "id": generate_id(agent, s["name"])}
                agent_block["allowlist"].append(entry)
                added += 1
        args.approvals.write_text(json.dumps(approvals, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\n✅ {added} Einträge in {args.approvals} geschrieben.")
    elif args.apply:
        print("\nNichts zu tun.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
