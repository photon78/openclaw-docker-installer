# OpenClaw Installer — Roadmap

> Last updated: 2026-04-23

## Principles

1. **Every version is stable in itself** — no "only works with v0.3"
2. **Secure by Default** — every version, every feature
3. **Backward compatible** — config from v0.1 works in later versions
4. **Wizard prevents poor decisions** — friction for risk
5. **All Python** — wizard, scripts, skills, tests
6. **Docker first** — native installation as a future option

---

## Released

### v0.1.0-alpha — "First Light" ✅
*Single agent, Docker, security baseline.*

- Interactive TUI wizard (Anthropic, Mistral, OpenAI, Ollama)
- Docker-based OpenClaw deployment with pinned release
- Telegram channel setup
- Restrictive exec allowlist (no shell tools, no bash)
- Full workspace bootstrap (SOUL.md, AGENTS.md, HEARTBEAT.md, MEMORY.md, …)
- Gateway rate-limiting, plugin version pinning
- `autoAllowSkills: false` by default
- Skills bundled: web-search, docs-summarize, Mistral suite

### v0.2.0 — "The Pack" ✅
*Security hardening, workspace quality, Windows support.*

- Security profile tightening (no shell tools in any allowlist)
- BOOTSTRAP.md onboarding file
- Windows 11 compatibility
- UTF-8 encoding fixes across all generators
- Headless-Docker warning (no channel configured)
- Signal + Discord removed from wizard (Telegram only)

### v0.2.1 — "The Pack (patch)" ✅
*Windows 11 compatibility fixes, permission handling.*

### v0.3.0 — "The Crew" ✅
*Multi-agent system, sub-agent hardening, dynamic config.*

- `add_agent.py` — main agent creates specialist sub-agents on demand
- 4 archetypes: coding, research, content, custom
- Sub-agents inherit full security baseline from day one
- Spawn rules enforced: `maxSpawnDepth: 1`, no chain-spawning
- Merge-based restore strategy (sub-agents survive `openclaw update`)
- Dynamic plugin config (Mistral plugin only if key present)
- systemd user service generator (autostart on boot)
- `--dry-run` mode — preview all config before writing
- Skill deduplication (`always/` + `mistral/` only)
- CI: Node.js 24 compatible actions

### v0.3.1 — "The Crew (patch)" ✅
*Code review fixes.*

- STARTUP_TIMEOUT 90→180s (Pi/SD-card first pull)
- `backup_mount_path` validation with retry option
- Stale skill duplicates removed (13 files)
- README updated: multi-agent features, sub-agent security philosophy
- 5 CI test failures resolved (container paths, dynamic plugin config)

### v0.3.2 — "Clean Slate" ✅
*UX fixes from real-world install test.*

- Welcome screen: version number in Bootsplash (aus `VERSION`-Datei)
- Requirements: Discord + Signal entfernt — nur Telegram
- Ollama aus Wizard entfernt — via `openclaw configure` konfigurierbar
- Completion screen: `/start`-Hinweis → Bootstrap-Prompt als Kopiervorlage
- BOOTSTRAP.md Block 2: Skills aus TOOLS.md statt hardcodierter Liste
- BOOTSTRAP.md Block 4: Ablenkungsfrage entfernt
- Backup: Hinweis dass Mount verfügbar sein muss + Verzeichnis auto-erstellt
- CI: Windows-skip für `chmod`-Test

---

## In Progress

### v0.3.3 — "The Crew (patch 3)" 🔧
*Agent registration via CLI — resilient to config shape changes.*

- `add_agent.py`: use `openclaw agents add --non-interactive` instead of direct JSON patching
- JSON patch kept as fallback if CLI unavailable
- 11 new tests for CLI registration, fallback, exec-approvals
- Real-world validation required before merge

---

## Planned

### v0.4.0 — "Open House" 🏠
*Stability, UX polish, CLI commands.*

- `openclaw agents add` real-world validation and cleanup
- CLI: `start` / `stop` / `status` subcommands
- Integration tests for full install → healthcheck flow
- macOS launchd service (alongside existing systemd)
- CONTRIBUTING.md review and update

### v0.5.0 — "Shape Shifter" 🔄
*Updates, migration, backup.*

- `openclaw-installer update` — backup before update, health check after
- `openclaw-installer backup` / `restore`
- Migration path: Docker → native

### v0.6.0 — "VPS Ready" 🖥️
*One-command VPS deployment.*

- nginx reverse proxy config
- Let's Encrypt / Certbot setup
- UFW firewall rules
- Resource limits (RAM-aware docker-compose)

---

## Backlog

- Native Linux installation (systemd, no Docker)
- PyInstaller binaries (no Python required on host)
- Web UI for wizard
- Community skills integration (ClaWHub)
- Multi-server / cluster mode
