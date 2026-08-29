# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Notes
- Real-life install test on **Ubuntu 24.04 (VirtualBox)** with OpenClaw **2026.7.1**
  completed successfully after checking out the correct installer branch.
  Captured in `ROADMAP.md` under *Real-Life Test Notes*.

### Roadmap
- v1.0.0 target defined: **"The Trinity"** — Main, Coding, and Research
  (subagent) setup modeled on our production configuration.
  See `ROADMAP.md` for scope and exclusions.

---

## [0.4.0] — 2026-08-29 "vLLM Local GPU"

### Added
- **vLLM local GPU provider support** — run a local LLM inside Docker with NVIDIA GPU passthrough.
  - Wizard step: "vLLM (local GPU)" provider option with VRAM detection via `nvidia-smi`.
  - VRAM-based `--max-model-len` recommendation (conservative defaults from RTX 5090 32 GB test).
  - Configurable HuggingFace cache path (default: `~/.cache/huggingface`).
  - NVIDIA Container Toolkit smoke test (`docker run --rm --gpus all nvidia/cuda:12.8.0-base-ubuntu24.04 nvidia-smi`).
  - Docker Compose service `vllm-qwen` using `vllm/vllm-openai:nightly` with memory-optimising flags:
    `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`, `--kv-cache-dtype fp8`, `--enforce-eager`,
    `--gpu-memory-utilization 0.90`.
  - OpenClaw provider config `vllm-local` pointing at `http://vllm-qwen:8000/v1`.
  - Qwen3 thinking mode toggle (default disabled).
- **`src/checks/check_nvidia_ctk.py`** — verify NVIDIA Container Toolkit installation and Docker GPU access.
- **`src/checks/check_vllm_ready.py`** — probe `http://localhost:8000/v1/models` to confirm vLLM is live.

### Changed
- Bumped version to `v0.4.0`.

---

## [0.5.1] — 2026-07-01 "Dedicated Update Cron"

### Changed
- **HEARTBEAT.md templates** (main + all 4 sub-agent types): update check removed from
  heartbeat. Heartbeat now ends silently when nothing to report (no visible `HEARTBEAT_OK`
  message). Explicit rule added: `No update checks in heartbeat`.
- **AGENTS.md template**: update procedure extended with allowlist sync (step 3) and
  gateway restart (step 5). Rule clarified: update only runs on explicit user request;
  the `Daily OpenClaw Update Check` cron sends the summary.
- **BOOTSTRAP.md Block 7**: wording updated — references dedicated daily cron instead
  of heartbeat for update monitoring.
- **`docs/day2-operations.md`**: new “Update Design Principles” section; “How the Daily
  Update Check Works” step-by-step; gateway restart added to standard flow.

### Added
- **`scripts/check_openclaw_update.py`** generated in every new workspace: standalone
  daily update check script. Calls `openclaw update status --json` + `npm view openclaw
  time --json`. Waits 4 days, gathers GitHub community feedback, prints summary.
  Exit 0 = silent, Exit 1 = summary available, Exit 2 = error.
- **`tasks/cron-setup.md`** extended: documents `Daily OpenClaw Update Check` cron
  (isolated agentTurn at 08:00 local time) alongside the existing Gateway Health Check.

---

## [0.5.0] — 2026-06-30 "Day 2"

### Added
- **HEARTBEAT.md template:** `openclaw update status --json` on every heartbeat; notifies user when `updateAvailable: true`. Never auto-updates.
- **AGENTS.md template:** new `## Update & Backup Flow` section — backup → update → doctor, with explicit rules (never without backup, never automatic, repair fallback).
- **BOOTSTRAP.md:** Block 7 "Backup & Updates" explains backup/update/heartbeat flow. Final Step instructs agent to delete `BOOTSTRAP.md` after onboarding.
- **`docs/day2-operations.md`:** reference guide for standard and power-user update flows, backup commands, recovery steps, update channels.

---

## [0.3.6] — 2026-06-30 "Script Safety Bundle"

### Added
- **`safe_exec_check.py`** bundled in `workspace/scripts/shared/` — pre-flight exec safety check for all agents.
  Blocks pipes, chaining, redirects, subshells, globs, backgrounding, inline-shell, `run`-prefix, newlines.
  Exit 0 = ok, Exit 1 = reject, Exit 2 = config/IO error.
- **SCRIPT-META header standard** — generic script metadata (renamed from ZOT-META).
  Fields: `agent`, `type`, `risk`, `description`. Documented in BOOTSTRAP.md template.
- **`scan_scripts.py`** bundled in `workspace/scripts/shared/` — scans SCRIPT-META headers, writes `scripts/registry.json`.
- **`sync_allowlist.py`** bundled in `workspace/scripts/shared/` — compares registry vs. `exec-approvals.json`.
  Default: hides broad-python-covered scripts. `--apply` fills gaps. `--strict` shows all.
  Runs as post-install verification step (0 real gaps = config correct).

### Changed
- AGENTS.md templates: new section "Script-Registry & Allowlist-Sync" with scan + sync workflow.

---

## [0.3.5] — 2026-06-30

### Fixed
- **`openclaw.json`: `tools.exec.mode`** — generated config now includes the full
  `tools` block with `exec.mode: "allowlist"`, matching the production OpenClaw
  configuration on `hummer`. Previously this block was missing after generation,
  causing exec approvals to fall back to manual review instead of the allowlist.
- **Tests:** updated assertions now verify the `tools` block presence and
  `tools.exec.mode` value.

## [0.3.4] — 2026-06-02 "LLM Providers Expansion"

### Added
- **Kimi K2.6 support** — new LLM provider via Moonshot AI (`moonshot/kimi-k2.6`).
  Requires `KIMI_API_KEY` in `.env`.
- **Ollama support** — local LLM provider with configurable host (`OLLAMA_HOST`,
  default `localhost:11434`). Supports `gemma4`, `qwen3`, and other Ollama models.
- **GPT-5.5 Codex support** — OpenAI Codex as optional provider (`openai/gpt-5.5`).
  Requires `OPENAI_API_KEY` in `.env`.
- **Gateway Token generation** — installer now generates a random
  `OPENCLAW_GATEWAY_TOKEN` and writes it to both `.env` and `openclaw.json`.
  Fixes container authentication issues.
- **Ollama Host configuration** — interactive prompt for Ollama host IP during
  install with warning for external hosts.

### Fixed
- **BOOTSTRAP.md creation** — corrected `workspace_bootstrap_gen.generate()` call
  (was incorrectly calling `.write()` which no longer exists). BOOTSTRAP.md is
  now properly created in the workspace.
- **OpenAI dependencies removed** — all OpenAI-specific code removed from installer.
  Codex is now optional via user-provided API key.

### Changed
- **Version bump** — `v0.3.3` → `v0.3.4`.
- **LLM provider selection** — installer now asks for preferred provider
  (Kimi / Ollama / Codex) with appropriate API key prompts.

---
=======
## [0.3.5] — 2026-06-30

### Fixed
- **`openclaw.json`: `tools.exec.mode`** — generated config now includes the full
  `tools` block with `exec.mode: "allowlist"`, matching the production OpenClaw
  configuration on `hummer`. Previously this block was missing after generation,
  causing exec approvals to fall back to manual review instead of the allowlist.
- **Tests:** updated assertions now verify the `tools` block presence and
  `tools.exec.mode` value.

## [0.3.3] — 2026-05-27 "The Crew (patch 3)"

### Added
- **Sub-agent bootstrap context note** — `AGENTS.md` template and `BOOTSTRAP.md` Block 3 now
  document OpenClaw 2026.5.22 breaking change: sub-agents spawned via `sessions_spawn` only
  receive `AGENTS.md` + `TOOLS.md` by default. Spawn `task:` prompts must include all needed
  context explicitly; use `context: "fork"` only when full session history is required.
- **`openclaw.json`: `compaction.model`** — generated config now sets
  `agents.defaults.compaction.model: "${LLM_BUDGET}"` so compaction summarisation uses
  the budget model, not the power model.
- **`openclaw.json`: `logging.redactSensitive`** — generated config now sets
  `logging.redactSensitive: "tools"` to mask sensitive values in logs and transcripts.
- **`add_agent.py`: CLI registration** — agent registration now uses
  `openclaw agents add --non-interactive` as primary path; direct JSON patching kept as
  fallback when the CLI is unavailable. Resilient to config schema changes.

### Fixed
- **`restore_gen.py`: stale allowlist entries removed** — `daily_digest.py` and
  `memory_digest.py` were removed from the project in v0.3.0 but remained in the generated
  `restore_exec_approvals.py` defaults allowlist. Entries now match `exec_approvals_gen.py`.
  `check_tasks.py` added to defaults; `morning_briefing.py`, `check_tasks.py`, and
  `add_agent.py` added to main agent allowlist for consistency.

### Compatibility
- Requires OpenClaw ≥ 2026.5.22 for sub-agent bootstrap behaviour.
  Earlier versions still work; the new context note in templates is informational only.
- `add_agent.py` CLI path requires `openclaw agents add --non-interactive` support
  (available since OpenClaw 2026.4.x). Falls back to JSON patch on older installs.

---

## [0.3.2] — 2026-04-23 “Clean Slate”

### Fixed
- **Welcome screen: Discord + Signal entfernt** — Messaging-Channel auf Telegram beschränkt; Discord/Signal waren nicht implementiert.
- **Completion screen: /start-Hinweis ersetzt** — Telegram-Abschluss zeigt jetzt den konkreten Bootstrap-Prompt statt generischem `/start`.
- **BOOTSTRAP.md Block 2: Skills aus TOOLS.md** — Agent liest TOOLS.md statt hardcodierter Skill-Liste; bleibt automatisch aktuell.
- **BOOTSTRAP.md Block 4: Ablenkungsfrage entfernt** — "Any questions about how I work?" → "Ready for the next part?" (verhindert Off-Topic-Diskussionen im Onboarding).
- **Backup-Step: Pfad-Hinweis ergänzt** — Explizite Bestätigung dass `openclaw-backup/` beim ersten Lauf automatisch erstellt wird.

### Added
- **VERSION-Datei** — `VERSION` im Repo-Root; Welcome-Screen liest daraus die Versionsnummer (Fallback: hardcoded).
- **Versionsnummer im Bootsplash** — Welcome-Panel zeigt jetzt `v0.3.2` (aus VERSION-Datei).

---

## [0.3.1] — 2026-04-20 "The Crew (patch)"

### Fixed
- **STARTUP_TIMEOUT 90→180s** — prevents false timeout on Raspberry Pi with SD card; improved timeout message with recovery hint.
- **`backup_mount_path` validation** — `Path.exists()` check for predefined and custom paths; prompts to re-enter or skip if path is not mounted.
- **Skill duplicates removed** — 13 stale flat-copy files deleted from `src/installer/templates/skills/`; only `always/` and `mistral/` structure remains.

### Added
- **systemd user service generator** — writes `~/.config/systemd/user/openclaw.service` at install time; attempts `systemctl --user enable` automatically; completion screen shows `loginctl enable-linger` hint for headless servers.
- **`--dry-run` mode** — `python3 src/main.py install --dry-run` runs the full wizard but writes all generated files to a temp dir. Docker not started. Useful for previewing config before committing to install.

### Docs
- README updated for v0.3.0: status table, multi-agent features, sub-agent security philosophy (*"hardened from birth"*).

---

## [0.3.0] — 2026-04-19 "The Crew"

### Added
- **Active Memory Plugin** — automatic `memory_search` before every reply, out of the box. Agents no longer need a manual recall step at session start.
- **Multi-Agent Templates** — `add_agent.py` + archetypes (`coding`, `research`, `content`, `custom`) for main-agent-driven sub-agent setup.
- **AGENTS.md Sub-Agent Checklist** — 7-step guide for adding specialist agents, including exec-approvals, spawn rules, and security requirements.
- **MMR + Temporal Decay** — memory search now uses Maximal Marginal Relevance and temporal decay for better recall quality (requires Mistral key).
- **Restore Merge Strategy** — `restore_exec_approvals.py` merges instead of overriding: baseline agents always restored, additional agents preserved.
- **A2A Security Rationale** — documented why task-files are preferred over direct agent-to-agent messaging (LLM context leak prevention).
- **`check_tasks.py` in exec-approvals** — registered in defaults + main allowlist, no approval needed.

### Removed
- **`daily_digest.py` / `memory_digest.py`** — OpenClaw indexes `memory/topics/` recursively and automatically; no digest step needed.
- **Daily Digest cron** — removed from BOOTSTRAP.md template.
- **VPS support** — removed from scope (issues #7, #15 closed).

### Documentation
- `MEMORY-ARCHITECTURE.md` — Active Memory Plugin, digest decision, automation table updated.
- `docs/security-architecture.md` — A2A communication security section.
- `docs/multi-agent-setup.md` — security note on task-files.
- `README.md` — Architecture & Documentation section added.

---

## [0.2.1] — 2026-04-15

### Fixed
- **Windows compatibility: CRLF line endings** — all files consumed by Docker/WSL2
  (`docker-compose.yml`, `.env`, `start.sh`, `restore_exec_approvals.py`, `openclaw.json`,
  `daily_backup.py`) now written with `write_bytes()` to force LF endings on Windows.
  CRLF in `docker-compose.yml` entrypoint path caused `start.sh: no such file or directory`.
- **Windows: `os.getuid()` crash** — `_fix_permissions()` in `docker_start.py` now skips
  on Windows (`sys.platform == 'win32'`). Docker Desktop on Windows handles volume
  permissions via WSL2 automatically.
- **Windows: username default showing 'agent'** — `WizardState.username` now uses
  `getpass.getuser()` instead of `Path.home().name` for correct cross-platform username.
- **`.env` parser error: key cannot contain a space** — removed comment lines with `=`
  at end-of-line and `${...}` syntax that confused Docker Compose's env_file parser.
- **Telegram/Discord user ID visible during input** — user ID prompt now uses
  `questionary.password()` (masked input) instead of `questionary.text()`.
- **Banner version string** — corrected from `v1.0.0` to `v0.2.0`.
- **Heartbeat architecture** — generated `HEARTBEAT.md` template updated to match new
  isolated-session heartbeat model (`isolatedSession: true`, `lightContext: true`,
  `model: mistral/mistral-large-latest`). Template now correctly reads daily log and
  updates `MEMORY.md` (not the other way around).
- **Dead `hourly_log.py` references** removed from `exec_approvals_gen.py`,
  `restore_gen.py`, and `workspace_bootstrap_gen.py` (Hourly Log Writer cron replaced
  by Heartbeat Memory Sync).

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
- `docker-compose.yml` generator — resolves `extended-stable` tag via GitHub Tags API, fallback to `:extended-stable`
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
