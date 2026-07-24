# OpenClaw Installer — Roadmap

> Last updated: 2026-07-24

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

### v0.3.3 — "The Crew (patch 3)" ✅
*OpenClaw 2026.5.22 compat, CLI agent registration, config hardening.*

- `add_agent.py`: uses `openclaw agents add --non-interactive`; JSON patch as fallback
- Sub-agent bootstrap context documented in AGENTS.md + BOOTSTRAP.md templates
- `restore_gen.py`: stale `daily_digest.py` / `memory_digest.py` entries removed
- `openclaw.json`: `compaction.model: "${LLM_BUDGET}"` + `logging.redactSensitive: "tools"`

---

## Planned

### v0.3.6 — "Script Safety Bundle" 🛡️ ✅
*Agent exec-safety, script registry, allowlist verification.*

- **`safe_exec_check.py`** — bundled in `workspace/scripts/shared/`; AGENTS.md templates already reference it, now ships with the installer
  - Blocks: pipes, chaining (`&&`, `||`, `;`), redirects, subshells, globs, backgrounding, inline-shell (`bash -c`, `python3 -c`), `run`-prefix, Newlines
  - Exit 0 = ok, Exit 1 = reject, Exit 2 = config error
- **script-meta header standard** — generic header for scripts; fields: `agent`, `type`, `risk`, `description`; documented in BOOTSTRAP.md
- **`scan_script_meta.py`** — scans workspace scripts for script-meta headers, writes `scripts/registry.json`; bundled in `workspace/scripts/shared/`
- **`sync_allowlist.py`** — compares registry against `exec-approvals.json`; default mode hides broad-python-covered scripts; `--apply` fills gaps; `--strict` shows all
  - Runs as post-install verification step: 0 real gaps = installation correct
- AGENTS.md templates updated: "Script-Registry & Allowlist-Sync" section

### v1.0.0 — "The Trinity" 🎯
*Production-ready multi-agent setup: Main, Coding, and Research Subagent.*

Goal: the installer creates an OpenClaw instance that contains **two
standalone agents out of the box** plus a ready-to-spawn research subagent,
modeled on our own production setup and its hard-won tweaks.

- **Main** (`main` / Zot) — primary concierge agent, Telegram direct-messages,
  owns the user relationship and dispatches work.
- **Coding** (`coding_zot`) — code, build, deployment tasks; separate workspace
  with coding-specific rules (script-meta, allowlist sync, safe-exec pre-checks).
- **Research** (`research_zot`) — **not a standalone agent**; spawned on demand
  by Main or Coding as a subagent, isolated per task, destroyed on completion.
  The first boot-up prompts Main to suggest creating the Research subagent so
  the user learns the `sessions_spawn` workflow immediately.

Scope for v1.0:
- One installer run creates Main and Coding with consistent security baselines.
- Research subagent template and bootstrap instructions are pre-installed;
  creation is triggered via Main during onboarding, not hard-wired by the installer.
- Each agent gets its own Telegram bot token / workspace / `AGENTS.md` /
  `SOUL.md` / `MEMORY.md` / `HEARTBEAT.md` / `TOOLS.md` skeleton.
- Shared infrastructure: NAS-mount path (configurable), `scripts/`,
  `shared/` skeleton, script-meta header template, `scan_script_meta.py` /
  `sync_allowlist.py` hooks, `check_tasks.py` cron.
- Secrets via SecretRefs (`.env` only); exec-policy / allowlist baseline.

---

## Real-Life Test Notes

### Ubuntu 24.04 + OpenClaw 2026.7.1 — 2026-07-21
*Manual install test by Photon in a fresh VirtualBox.*

- Installer branch: `feature/secretrefs` (after explicit checkout).
- OpenClaw version pinned: `2026.7.1`.
- Result: **successful boot** to interactive agent (`agentZero`).
- Learnings captured for v1.0 polish:
  1. **Branch checkout trap:** `git clone` lands on `main` by default. The
     installer must either default to the intended branch or clearly instruct
     the user to `git checkout feature/secretrefs` (or the release branch)
     before running `run.sh`.
  2. **`BOOTSTRAP.md` lifecycle:** On a truly fresh install `BOOTSTRAP.md` must
     be present. The agent reported it missing; we need to verify the installer
     creates it and does not delete it prematurely.
  3. **`openclaw doctor --lint` output is too long:** the first-run summary
     spans more than two terminal screens. v1.0 should surface only
     actionable, security-critical items and defer the rest to a log file.
  4. **SecretRefs work** when the correct branch is actually checked out and
     the generator runs. The plaintext-secrets finding in the test was caused
     by running the pre-SecretRefs generator from `main`.

## Backlog

- Native Linux installation (systemd, no Docker)
- PyInstaller binaries (no Python required on host)
- Web UI for wizard
- Community skills integration (ClaWHub)
- Multi-server / cluster mode
