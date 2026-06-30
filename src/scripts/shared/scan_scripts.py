#!/usr/bin/env python3
"""
scan_scripts.py — Scan workspace scripts for SCRIPT-META headers.

SCRIPT-META:
  agent: shared
  type: utility
  risk: low
  description: "Scan scripts/ for SCRIPT-META headers, write scripts/registry.json"

Usage:
    python3 scan_scripts.py [--scripts-dir <path>]
    Default scripts-dir: same directory as this script's parent (workspace/scripts/)

Output: scripts/registry.json
"""

import argparse
import ast
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def _parse_script_meta(source: str) -> dict | None:
    """Extract SCRIPT-META fields from the module docstring.

    Looks for a block like:
        SCRIPT-META:
          agent: shared
          type: utility
          risk: low
          description: "..."

    Returns a dict with keys: agent, type, risk, description — or None if not found.
    """
    # Try AST parse to get docstring safely
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None

    docstring = ast.get_docstring(tree)
    if not docstring:
        return None

    # Find SCRIPT-META: block
    lines = docstring.splitlines()
    meta_start = None
    for i, line in enumerate(lines):
        if line.strip() == "SCRIPT-META:":
            meta_start = i + 1
            break

    if meta_start is None:
        return None

    # Parse indented key: value pairs until we hit a non-indented line or end
    meta: dict[str, str] = {}
    for line in lines[meta_start:]:
        stripped = line.strip()
        if not stripped:
            continue
        # Stop at next unindented section header (no leading whitespace, ends with :)
        if not line.startswith(" ") and not line.startswith("\t") and stripped.endswith(":"):
            break
        # Stop at lines that aren't indented (after the first real meta line)
        if meta and not line.startswith(" ") and not line.startswith("\t"):
            break
        if ":" in stripped:
            key, _, value = stripped.partition(":")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key in ("agent", "type", "risk", "description"):
                meta[key] = value

    return meta if meta else None


def scan_scripts(scripts_dir: Path) -> tuple[dict, dict]:
    """Scan .py files in scripts_dir (and scripts_dir/shared/) for SCRIPT-META.

    Returns:
        registry: dict keyed by filename with meta + path info
        stats: summary counts
    """
    registry: dict[str, dict] = {}

    # Collect all .py files: scripts_dir/*.py + scripts_dir/shared/*.py
    candidates: list[Path] = []
    for py_file in sorted(scripts_dir.glob("*.py")):
        candidates.append(py_file)
    shared_dir = scripts_dir / "shared"
    if shared_dir.exists():
        for py_file in sorted(shared_dir.glob("*.py")):
            candidates.append(py_file)

    for py_file in candidates:
        try:
            source = py_file.read_text(encoding="utf-8")
        except OSError:
            continue

        meta = _parse_script_meta(source)
        # Compute relative path from scripts_dir's parent (workspace root)
        try:
            rel_path = py_file.relative_to(scripts_dir.parent)
        except ValueError:
            rel_path = py_file

        entry: dict = {
            "path": str(rel_path),
        }
        if meta:
            entry["agent"] = meta.get("agent", "")
            entry["type"] = meta.get("type", "")
            entry["risk"] = meta.get("risk", "")
            entry["description"] = meta.get("description", "")
            entry["has_meta"] = True
        else:
            entry["has_meta"] = False

        registry[py_file.name] = entry

    # Build stats
    total = len(registry)
    with_meta = sum(1 for v in registry.values() if v.get("has_meta"))
    without_meta = total - with_meta

    by_agent: dict[str, int] = {}
    by_risk: dict[str, int] = {}
    for v in registry.values():
        if v.get("has_meta"):
            agent = v.get("agent", "unknown")
            risk = v.get("risk", "unknown")
            by_agent[agent] = by_agent.get(agent, 0) + 1
            by_risk[risk] = by_risk.get(risk, 0) + 1

    stats = {
        "total": total,
        "with_meta": with_meta,
        "without_meta": without_meta,
        "by_agent": by_agent,
        "by_risk": by_risk,
    }

    return registry, stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Scan workspace scripts/ for SCRIPT-META headers and write registry.json."
    )
    parser.add_argument(
        "--scripts-dir",
        type=Path,
        default=None,
        help="Path to scripts/ directory. Defaults to the parent directory of this script.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output path for registry.json. Defaults to <scripts-dir>/registry.json.",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress stats output.",
    )
    args = parser.parse_args(argv)

    # Resolve scripts dir: default = parent of this script (i.e. workspace/scripts/)
    if args.scripts_dir is not None:
        scripts_dir = args.scripts_dir.resolve()
    else:
        scripts_dir = Path(__file__).parent.resolve()

    if not scripts_dir.exists():
        print(f"ERROR: scripts directory not found: {scripts_dir}", file=sys.stderr)
        return 2

    output_path = args.output if args.output else scripts_dir / "registry.json"

    registry, stats = scan_scripts(scripts_dir)

    # Write registry.json
    payload = {
        "version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scripts_dir": str(scripts_dir),
        "scripts": registry,
    }

    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    if not args.quiet:
        print(f"=== scan_scripts report ===")
        print(f"Scripts dir:    {scripts_dir}")
        print(f"Registry:       {output_path}")
        print(f"Total scripts:  {stats['total']}")
        print(f"  With SCRIPT-META:    {stats['with_meta']}")
        print(f"  Without SCRIPT-META: {stats['without_meta']}")
        if stats["by_agent"]:
            print("\nBy agent:")
            for agent, count in sorted(stats["by_agent"].items()):
                print(f"  {agent}: {count}")
        if stats["by_risk"]:
            print("\nBy risk:")
            for risk, count in sorted(stats["by_risk"].items()):
                print(f"  {risk}: {count}")
        if stats["without_meta"] > 0:
            print("\nScripts without SCRIPT-META:")
            for name, entry in sorted(registry.items()):
                if not entry.get("has_meta"):
                    print(f"  {name}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
