#!/usr/bin/env python3
"""
ZOT-META:
  agent: coding_zot
  type: utility
  risk: low
  secrets: none
  description: "Deep allowlist sync — scannt FS pro Agent, fügt jedes .py/.sh als eigenen Eintrag in exec-approvals.json hinzu"
"""
import argparse
import json
import re
from pathlib import Path

APPROVALS_PATH = Path("/home/hummer/.openclaw/exec-approvals.json")
OCLAW_BASE = Path("/home/hummer/.openclaw")

# Workspace-Mapping: Agent -> Verzeichnisse mit FS-Scan-Reihenfolge
WORKSPACE_MAP: dict[str, list[str]] = {
    "main": [
        "workspace/scripts",
        "workspace/scripts/shared",
        "scripts",
    ],
    "coding_zot": [
        "workspace-coding/scripts",
        "workspace-coding/scripts/shared",
    ],
    "valere": [
        "workspace-valere/scripts",
    ],
    "sentinel": [
        "workspace-sentinel/scripts",
    ],
    "sionis": [
        "workspace-sionis/scripts",
    ],
}

# Agent -> Prefix für allowlist ID
AGENT_PREFIX = {
    "main": "m",
    "coding_zot": "cz",
    "valere": "v",
    "sentinel": "s",
    "sionis": "si",
    "research_zot": "rz",
}

TRACKED_AGENTS = set(WORKSPACE_MAP.keys())

# ZOT-META Parser
META_RE = re.compile(
    r'ZOT-META:\s*\n'
    r'((?:\s+\w+:\s*[^\n]*\n)+)',
    re.MULTILINE
)

SHEBANG_RE = re.compile(r'^#!\s*(.+)$', re.MULTILINE)


def parse_meta(content: str) -> dict | None:
    """Extrahiert ZOT-META aus Script-Content."""
    m = META_RE.search(content)
    if not m:
        return None

    meta = {}
    for line in m.group(1).strip().split('\n'):
        line = line.strip()
        if ':' not in line:
            continue
        key, val = line.split(':', 1)
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        meta[key] = val
    return meta


def read_shebang(content: str) -> str | None:
    """Gibt den Interpreter aus dem Shebang zurück."""
    m = SHEBANG_RE.search(content)
    if not m:
        return None
    line = m.group(1).strip()
    # '#!/usr/bin/env python3' -> '/usr/bin/env python3' -> Interpreter-Teil
    parts = line.split()
    if not parts:
        return None
    if parts[0].endswith("/env") and len(parts) > 1:
        # env-Lookup: wir nehmen den kanonischen Pfad an
        env_bin = parts[1]
        if env_bin in {"python3", "python"}:
            return "/usr/bin/python3"
        # Non-standard venv-python via env? eher unüblich
        return env_bin
    return parts[0]


def detect_venv_interpreter(content: str, script_path: Path) -> str | None:
    """Ermittelt den tatsächlichen Venv-Python aus Shebang + Script-Pfad."""
    shebang = read_shebang(content)
    if shebang is None:
        return None

    # Wenn Shebang bereits ein absoluter Pfad außerhalb /usr/bin ist -> Venv
    if shebang.startswith("/") and shebang != "/usr/bin/python3" and "python" in shebang:
        return shebang

    # Wenn Shebang /usr/bin/env python3 -> kein Venv
    if shebang in {"/usr/bin/python3", "/usr/bin/python", "python3", "python"}:
        return None

    # Wenn kein absoluter Pfad, prüfe ob im gleichen Verzeichnis .venv existiert
    venv_candidates = [
        script_path.parent / ".venv" / "bin" / "python",
        script_path.parent.parent / ".venv" / "bin" / "python",
        script_path.parent / ".venv-pdf" / "bin" / "python",
    ]
    for cand in venv_candidates:
        if cand.exists():
            return str(cand.resolve())

    return None


def collect_script_files(agent_filter: str | None = None) -> list[Path]:
    """Sammelt alle .py und .sh Files aus den gemappten Workspaces.

    Args:
        agent_filter: Optional nur einen Agent scannen (z. B. nach add_agent.py).
    """
    files: list[Path] = []
    seen: set[Path] = set()

    agents_to_scan = [agent_filter] if agent_filter else WORKSPACE_MAP.keys()
    for agent in agents_to_scan:
        if agent not in WORKSPACE_MAP:
            continue
        for rel_dir in WORKSPACE_MAP[agent]:
            scan_dir = OCLAW_BASE / rel_dir
            if not scan_dir.exists():
                continue
            for ext in ("*.py", "*.sh"):
                for path in scan_dir.glob(ext):
                    try:
                        resolved = path.resolve()
                    except (OSError, RuntimeError):
                        resolved = path
                    if resolved in seen:
                        continue
                    seen.add(resolved)
                    files.append(path)
    return files


def determine_agents(path: Path, meta: dict | None, rel_to_openclaw: str) -> set[str]:
    """Ermittelt alle Agents, denen das Script zugeordnet ist."""
    agents: set[str] = set()

    if meta and "agent" in meta:
        agent_value = meta["agent"].strip().lower()
        # Multi-Agent: komma-getrennt
        for a in agent_value.split(","):
            a = a.strip()
            if a == "shared":
                # shared wird an alle bekannten Agents vergeben
                agents.update(TRACKED_AGENTS)
            elif a in TRACKED_AGENTS:
                agents.add(a)
        if agents:
            return agents

    # Fallback: Workspace-Owner aus Pfad
    parts = rel_to_openclaw.lower().split("/")
    if "workspace-coding" in parts:
        agents.add("coding_zot")
    elif "workspace/scripts/shared" in "/".join(parts):
        agents.add("main")
        agents.add("coding_zot")
    elif "workspace/scripts" in "/".join(parts):
        agents.add("main")
    elif "workspace-valere" in parts:
        agents.add("valere")
    elif "workspace-sentinel" in parts:
        agents.add("sentinel")
    elif "workspace-sionis" in parts:
        agents.add("sionis")
    elif "scripts" in parts and "workspace" not in parts:
        agents.add("main")

    return agents


def generate_id(agent: str, script_name: str, existing_ids: set[str]) -> str:
    """Generiert eine eindeutige allowlist-ID."""
    prefix = AGENT_PREFIX.get(agent, agent[:2])
    slug = Path(script_name).stem.replace("_", "-").replace(".", "-")
    base = f"{prefix}-{slug}-01"
    if base not in existing_ids:
        return base
    n = 2
    while True:
        candidate = f"{prefix}-{slug}-{n:02d}"
        if candidate not in existing_ids:
            return candidate
        n += 1
        if n > 99:
            raise RuntimeError(f"Konnte keine eindeutige ID für {script_name} generieren")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Deep allowlist sync — jedes .py/.sh bekommt eigenen Eintrag"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Fehlende Einträge direkt in exec-approvals.json schreiben",
    )
    parser.add_argument(
        "--agent",
        type=str,
        default=None,
        metavar="NAME",
        help="Nur Workspaces dieses Agents scannen",
    )
    args = parser.parse_args()

    approvals = load_json(APPROVALS_PATH)

    # Bestehende Patterns + IDs pro Agent sammeln
    agent_patterns: dict[str, set[str]] = {}
    agent_ids: dict[str, set[str]] = {}
    for agent, agent_data in approvals.get("agents", {}).items():
        agent_patterns[agent] = {e.get("pattern", "") for e in agent_data.get("allowlist", [])}
        agent_ids[agent] = {e.get("id", "") for e in agent_data.get("allowlist", [])}

    # Scripts sammeln
    script_files = collect_script_files(agent_filter=args.agent)

    # Fehlende Einträge pro Agent
    missing: dict[str, list[dict]] = {}
    venv_extra: dict[str, list[dict]] = {}

    for script_path in sorted(script_files, key=lambda p: str(p)):
        try:
            content = script_path.read_text(encoding="utf-8", errors="replace")
        except (OSError, IOError):
            continue

        meta = parse_meta(content)
        try:
            rel_to_openclaw = str(script_path.relative_to(OCLAW_BASE))
        except ValueError:
            rel_to_openclaw = str(script_path)

        agents = determine_agents(script_path, meta, rel_to_openclaw)
        if not agents:
            continue

        # Venv-Interpreter falls non-standard
        venv_python = None
        if script_path.suffix == ".py":
            venv_python = detect_venv_interpreter(content, script_path)

        for agent in agents:
            patterns = agent_patterns.setdefault(agent, set())
            ids = agent_ids.setdefault(agent, set())

            abs_path = str(script_path.resolve())
            if abs_path not in patterns:
                missing.setdefault(agent, []).append({
                    "path": abs_path,
                    "name": script_path.name,
                })

            if venv_python and venv_python not in patterns:
                venv_extra.setdefault(agent, []).append({
                    "path": venv_python,
                    "name": Path(venv_python).name,
                })

            # Für .sh Scripts sicherstellen, dass /bin/bash erlaubt ist
            if script_path.suffix == ".sh":
                for bash_path in ("/bin/bash", "/usr/bin/bash"):
                    if bash_path not in patterns:
                        # globaler Bash-Eintrag wird pro Agent nur einmal vermerkt
                        bash_key = (agent, bash_path)
                        if not hasattr(main, "_bash_reported"):
                            main._bash_reported = set()
                        if bash_key not in main._bash_reported:
                            main._bash_reported.add(bash_key)
                            missing.setdefault(agent, []).append({
                                "path": bash_path,
                                "name": "bash",
                            })

    # Deduplizieren innerhalb missing (falls .sh + bash zusammenfallen)
    for agent in missing:
        seen: set[str] = set()
        deduped: list[dict] = []
        for item in missing[agent]:
            if item["path"] not in seen:
                seen.add(item["path"])
                deduped.append(item)
        missing[agent] = deduped

    # Bash-Einträge aus missing entfernen, da sie in existing approvals bereits
    # vorhanden sein sollten; wir wollen hier keine neuen Bash-Patterns erzeugen.
    for agent in list(missing.keys()):
        missing[agent] = [e for e in missing[agent] if e["name"] != "bash"]
        if not missing[agent]:
            del missing[agent]

    # Report
    mode = "apply" if args.apply else "dry-run"
    print(f"=== sync_allowlist_deep report [{mode}] ===")
    print(f"Gescannte Scripts: {len(script_files)}")

    total_missing = 0
    for agent in sorted(missing.keys()):
        entries = missing[agent]
        print(f"\nAgent: {agent} — {len(entries)} fehlend")
        for e in sorted(entries, key=lambda x: x["path"]):
            print(f"  {e['path']}")
        total_missing += len(entries)

    if not total_missing:
        print("\n✅ Keine fehlenden Einträge gefunden.")

    # --apply
    if args.apply:
        added = 0
        for agent in sorted(missing.keys()):
            agent_block = approvals.setdefault("agents", {}).setdefault(
                agent, {"allowlist": []}
            )
            allowlist = agent_block.setdefault("allowlist", [])
            patterns = agent_patterns.setdefault(agent, set())
            ids = agent_ids.setdefault(agent, set())

            for e in sorted(missing[agent], key=lambda x: x["path"]):
                path = e["path"]
                if path in patterns:
                    continue
                entry_id = generate_id(agent, e["name"], ids)
                allowlist.append({"pattern": path, "id": entry_id})
                patterns.add(path)
                ids.add(entry_id)
                added += 1

        APPROVALS_PATH.write_text(
            json.dumps(approvals, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"\n✅ {added} Einträge in {APPROVALS_PATH} geschrieben.")
        return 0

    print(f"\nTotal fehlende Einträge: {total_missing}")
    print("(Keine Änderungen vorgenommen — verwende --apply zum Schreiben)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
