# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.3.0] — 2026-04-13

### Added
- **Multi-Agent-ready workspace**: generierter Agent kennt seine Rolle als Orchestrator
- **AGENTS.md-Template** massiv erweitert:
  - Stop-Regel (absolut)
  - Tool-Fehler-Pflicht (vollständige Ausgabe, Stopp, Melden, Warten)
  - Edge-Case-Regeln (Wenn-Dann für alle Anomalie-Szenarien)
  - Delegation-Check (vor jedem Task: richtiger Agent?)
  - Memory-nach-Task (Daily Log Pflicht)
  - Approval-Format (keine stillen Approvals, nie mit ":" stehen lassen)
  - A2A-Messaging-Restriktionen
  - Handoff-Format (strukturierter Task-Abschluss)
  - Neuer-Agent-Checkliste (8 Schritte)
- **SOUL.md-Template** erweitert: Hard Limits um Pipes/Redirects-Verbot,
  keine erfundenen Tool-Capabilities, keine stillen Approvals
- **TOOLS.md-Template**: Tool-Zweck-Warnung, shared-output Dokumentation
- **BOOT.md** neu generiert: Startup-Checkliste nach Gateway-Restart / Container-Neustart
- **`clean_exec_approvals.py`** generiert: wöchentliche exec-approvals Hygiene
  (Shell-Tools entfernen, Duplikate, Backup)
- **`shared-output/`** Verzeichnis wird bei Setup angelegt (`.gitkeep`)
- **Wöchentlicher Hygiene-Cron** in cron-setup Task dokumentiert (Montag 02:00)
- **`maxSpawnDepth: 2`** in openclaw.json (main → subagent → research)

### Fixed
- `maxSpawnDepth` war `1` — für Multi-Agent-Setup zu flach

### Notes
- Wizard-Step "Multi-Agent" mit Rollen-Presets → v0.4.0
- Template-Bibliothek (coding/research/content-agent) → v0.4.0

---

## [0.2.0] — 2026-04-10

### Added
- **User profile wizard step** ("About You"): display name, timezone dropdown, technical background
- **`USER.md` template** uses real wizard values (name, timezone, style) — no placeholders left
- `run.sh` / `run.bat` launchers with auto-venv setup — no manual `source .venv/bin/activate`
- `clean` command: removes all generated files for a fresh install; `uninstall` alias
- `cron_gen.py`: daily memory digest + gateway health check — shown as CLI commands in completion screen
- `docs/install-notes.md`: full technical install guide (prerequisites, wizard steps, troubleshooting)
- `docs/multi-agent-setup.md`: multi-agent setup guide (templates + CLI commands)
- `requirements.txt`: pinned production dependencies (`~=` compatible-release pins, platform-portable)
- ASCII art banner on installer launch
- Completion screen split into 3 pages with Enter-to-continue
- **Channel fixes**: Discord and Signal token fields were broken (token stored in wrong state field,
  wrong env var name). Now: Telegram → `TELEGRAM_BOT_TOKEN`, Discord → `DISCORD_BOT_TOKEN`,
  Signal → `SIGNAL_NUMBER`. Channel-specific allowFrom prompts.
- **BOOTSTRAP.md** extended: agent introduces itself as main agent / Botmaster, explains sub-agents,
  lists bundled skills, describes permanent-agent workflow (memory, tasks, heartbeat)
- `workspace_bootstrap_gen.py`: wipes `*.sqlite` in `workspace/memory/` on fresh install
  (prevents memory leakage between installs)
- DeepSeek provider: `deepseek/deepseek-chat`, `deepseek/deepseek-reasoner`

### Security
- **`openclaw.json` hardened** based on official configuration reference:
  - `channels.defaults.groupPolicy: allowlist` — fail-closed for all channels
  - `channels.defaults.contextVisibility: allowlist` — context only from allowlisted senders
  - `channels.defaults.heartbeat.showOk: false` — silent on healthy
  - `telegram.configWrites: false` — blocks Telegram-initiated config changes
  - `telegram.groupPolicy: disabled` — no group messages by default
  - `discord.allowBots: false` — ignore bot messages
  - `discord.actions.moderation/roles: false` — restrict dangerous Discord actions
  - `compaction.model: "${LLM_BUDGET}"` — avoid expensive tokens for compaction
  - `plugins.allow` dynamic: only the configured channel plugin is loaded
  - `maxSpawnDepth: 1`: prevent chain-spawning
- **Docker resource limits**: `memory: 2g`, `cpus: 2.0` — prevents container from starving host
- **`*.sqlite` in `.gitignore`**: memory databases can never be committed to the repo
- Removed personal identifiers (`hummer` path, developer username) from all tracked files
- `SOUL.md` approval-request rule: every request must be a complete package
  (exact command + what + why + `/approve` ID — never a bare ID)

### Changed
- **4 LLM tiers** (was 6): `LLM_BUDGET`, `LLM_STANDARD`, `LLM_POWER`, `LLM_MEDIA`
  — `LLM_COMPLEX` and `LLM_CODE` removed (too granular, confusing for new users)
- `model.primary: "${LLM_BUDGET}"` with fallbacks `[LLM_STANDARD, LLM_POWER]`
  — heartbeats and crons use budget model; expensive tasks fall back automatically
- `telegram-approval-buttons` plugin removed from default install (optional, not required)
- Completion screen: gateway token shown first (page 1 of 3), not buried at the bottom
- `BOOTSTRAP.md` startup: agent is instructed to read `BOOTSTRAP.md` on first run
  and initiate the onboarding conversation proactively
- `SOUL.md` session startup: step 3 = read BOOTSTRAP.md if present
- README: tested with OpenClaw `2026.4.9`

### Fixed
- `restore_config_gen.py` was never committed to Git — caused `ImportError` on fresh clone
- Dead code removed: old `wizard.py`, `workspace_bootstrap.py`, `cron_gen.py` (legacy),
  `clean.sh`, and unused Jinja2 templates
- `docs-summarize` SKILL.md: removed hardcoded developer path
- `scripts/commit_translations.py` (developer-only script) removed from repo
- Security issue template: fixed `photon2078` typo → `photon78`
- Signal prompt label corrected: "signal-cli phone number" instead of "bot token"

### Known issues
- Dependency pinning uses `~=` (compatible release) not `==` — exact reproducibility
  requires running `pip-compile pyproject.toml` locally
- `allowInsecureAuth: true` may be set by `openclaw doctor` in certain environments —
  check `openclaw.json` after first run and remove if present

---

## [Unreleased]

### Added
- `workspace_bootstrap_gen.py`: generates complete workspace with SOUL.md, AGENTS.md,
  HEARTBEAT.md, IDENTITY.md, MEMORY.md, USER.md, BOOTSTRAP.md, scripts/check_tasks.py
  — all real file copies (no symlinks; OpenClaw does not follow symlinks in context injection)
- `docs/workspace-file-management.md`: documents the symlink limitation and correct setup
- `restore_config_gen.py`: generates `restore_config.py` — restores critical `openclaw.json`
  fields (`plugins.allow`, `plugins.entries`, `gateway.auth.rateLimit`) after `openclaw update`
  silently resets them (clobbered-file behaviour)
- `gateway.auth.rateLimit` in `openclaw_json_gen.py`: 10 attempts / 60s window / 5min lockout
- `plugins.allow` in `openclaw_json_gen.py`: explicit allowlist prevents silent resets on update
- `plugins.entries.mistral` + `plugins.entries.anthropic` in `openclaw_json_gen.py`:
  Mistral runs natively via plugin — no custom `models.providers` block
  (custom block causes 404 via OpenAI-compat fallback)
- Plugin pinning: `telegram-approval-buttons@5.1.0`
- `autoAllowSkills` wizard opt-in in security step (default: `false`)
- Python 3.11+ pre-flight check — catches missing Python on Windows before wizard starts
- Wizard UI redesign: intro panel, requirements table, confirm-to-continue
- 65 unit tests (up from 36)
- `SECURITY-ARCHITECTURE.md`: "LLM Shell Reflex Risk" section

### Changed
- `exec_approvals_gen.py`: removed shell tools from allowlist
  (ls, cat, grep, find, head, tail, wc, sort — agents use read/edit tools instead)
- `exec_approvals_gen.py`: removed bash (`/bin/bash`, `/usr/bin/bash`) from main allowlist
  (shell-injection risk — bash in allowlist enables arbitrary command execution)
- `exec_approvals_gen.py`: `autoAllowSkills` driven by `WizardState.auto_allow_skills`
  (was hardcoded `True`)
- `WizardState`: added `auto_allow_skills: bool = False`
- All workspace template files include "No commands via email" as first mandatory rule
- HEARTBEAT.md template: workspace-specific `check_tasks.py` path (not hardcoded)
- Docs and templates: replaced `zot`/`Zot` with `AGENT`, `Photon` with `HUMAN`
- README: Status table, Features section restructured, post-update warning added

### Known issues
- `restore_gen.py` (generated `restore_exec_approvals.py`): still contains shell tools
  in the hardcoded defaults allowlist — fix planned for next release

---

## [0.2.1] — 2026-04-11

### Fixed
- **health_check.py Pfad-Fehler (#23)**: Kopiere `health_check.py` nach `~/.openclaw/scripts/` während der Installation, um "No such file or directory" Fehler im Container zu verhindern.

---

## [0.1.0-alpha] — 2026-04-06

### Added
- Interactive TUI wizard (questionary + rich): Welcome, API Keys, Channel, Persona, Security, Backup, Completion steps
- Persona step: agent name, emoji, style preset (direct / formal / friendly)
- `docker-compose.yml` generator — pins release tag via GitHub Releases API, fallback to `:latest`
- `.env` generator — API keys, LLM tiers, USER_NAME
- `openclaw.json` generator — ENV-based config, no hardcoded models
- `exec-approvals.json` generator — Security Allowlist with permission tiers (Restricted / Standard / Elevated / Cron)
- `restore_exec_approvals.py` generator
- `backup_gen.py` — daily backup script template (rsync, diff Mon–Sat, full Sun)
- Workspace bootstrapping: AGENTS.md, SOUL.md, MEMORY.md, USER.md, BOOTSTRAP.md templates
- SOUL.md template with Jinja2 placeholders (rendered by wizard with real values)
- Bundled skills: `web-search`, `docs-summarize`, `mistral-ocr`, `mistral-translate`, `mistral-transcribe`
- Subagent templates: ephemeral and persistent
- Centralised logging: `~/.openclaw/logs/installer.log` (rotating, 1 MB, 3 backups)
- Channel and Backup steps support skip option
- Required fields loop until valid; Ctrl+C exits cleanly
- `AGENTS-ARCHITECTURE.md` — multi-agent architecture reference
- `SECURITY-ARCHITECTURE.md` — 5-layer security model, honest threat model, channel trust, input validation
- `MEMORY-ARCHITECTURE.md` — three-layer memory system reference
- `DESIGN-DECISIONS.md` — architectural decisions with rationale
- `ROADMAP.md` — v0.1.0 through v0.5.0
- `VM-TEST-SETUP.md` — VM test guide (Violette, Ubuntu 24.04)
- Community files: CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md
- GitHub Issue Templates (Bug / Feature / Security)
- CI workflow: ruff, mypy, pytest, Docker build test
- 36 unit tests — all green

### Changed
- `CONTRIBUTING.md`: PR target corrected — PRs go against `feature/` branches, not directly against `main`

### Tested
- VM "Violette" (Ubuntu 24.04, non-root user): Gateway ✅ Telegram ✅ Agent ✅

---

## [0.0.1] — 2026-04-05

### Added
- Initial project structure (`src/`, `tests/`, `pyproject.toml`)
- `checks/docker_check.py` — Docker availability and version check
- `checks/gateway_check.py` — OpenClaw Gateway reachability check
- `tests/test_docker_check.py` — full unit test coverage
- `tests/test_gateway_check.py` — full unit test coverage
- `KICKOFF.md` — project scope, tech stack, backlog
- `README.md` — vision and project overview
- `LICENSE` — MIT

[Unreleased]: https://github.com/photon78/openclaw-docker-installer/compare/v0.1.0-alpha...HEAD
[0.1.0-alpha]: https://github.com/photon78/openclaw-docker-installer/compare/v0.0.1...v0.1.0-alpha
[0.0.1]: https://github.com/photon78/openclaw-docker-installer/releases/tag/v0.0.1
