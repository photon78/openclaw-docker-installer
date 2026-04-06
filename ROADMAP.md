# OpenClaw Installer — Roadmap

> Status: 2026-04-06
> Principle: Every version is stable in itself. Secure by Default. All Python.

---

## v0.1.0 — "First Light" 🔦
*Single Agent, Docker, functional.*

### Infrastructure
- [x] Python project structure (pyproject.toml, src/, tests/)
- [x] CLI framework (typer): install / status / start / stop / uninstall
- [x] CI: Linting (ruff), Type-Check (mypy), Docker Build Test

### Wizard
- [ ] Interactive wizard (questionary + rich)
- [ ] Welcome + platform detection
- [ ] Request API key(s) (Anthropic, optional Mistral)
- [ ] Select channel (Telegram / Discord / Signal)
- [ ] Request channel credentials (bot token, etc.)
- [ ] Security profile: Strict / Standard / Custom

### Generation
- [ ] docker-compose.yml (bind mounts, .env + scripts read-only)
- [ ] .env (API keys, LLM tiers)
- [ ] openclaw.json (bootstrapMaxChars, subagents, sessions)
- [ ] exec-approvals.json (from security profile, per-agent tiers)
- [ ] restore_exec_approvals.py (from wizard config)
- [ ] Workspace bootstrapping (AGENTS.md, SOUL.md, IDENTITY.md, MEMORY.md templates)

### Security Baseline
- [x] Bundle health_check.py
- [x] Bundle audit_integrity.py + set baselines
- [ ] API keys only in .env, never in service file

### Backup Setup (Core Feature — not optional)
- [ ] Wizard: "Where is your backup medium?" (SD card / USB mount path)
- [ ] Deploy `daily_backup.py` from template (configured with user-defined mount path)
- [ ] Crontab entry: daily at 04:10
- [ ] Generate `restore.md` with concrete paths + token placeholder
- [ ] What is backed up: workspaces (rsync diff Mon–Sat, full Sun), openclaw.json, scripts (*.py), systemd drop-ins, memory SQLite, exec-approvals.json (token=REDACTED)
- [ ] What is NOT backed up: .env / API keys, session JSONL, node_modules / dist / .astro
- [x] Reference implementation: `~/.openclaw/scripts/daily_backup.py` (live, tested 2026-04-06)

### Post-Install
- [ ] docker-compose up via CLI
- [ ] Gateway ping (health check)
- [ ] Summary + next steps

### Docs & Community
- [x] README.md (Vision, Quick Start, Screenshots)
- [x] LICENSE (MIT)
- [x] CHANGELOG.md (Keep a Changelog)
- [x] CONTRIBUTING.md (DCO, Code Style, PR process)
- [x] CODE_OF_CONDUCT.md (Contributor Covenant)
- [x] SECURITY.md (Responsible Disclosure)
- [x] GitHub issue templates (Bug / Feature / Security Report)

---

## v0.2.0 — "The Pack" 🐺
*Multi-Agent, Extended Memory, Telegram Topics.*

### Multi-Agent
- [ ] Wizard: "How many agents?" + define roles
- [ ] Per agent: Name, emoji, workspace, permission tier
- [ ] Generate Telegram group + topic bindings
- [ ] Generate per-agent allowlist
- [ ] Automatically create symlinks

### Extended Memory (Opt-in)
- [ ] Wizard prompt: Basic vs. Extended
- [ ] Generate topics folder + _template.md + index.md
- [ ] Generate daily_digest.py (atomic writing)
- [ ] Cron jobs: Log writer (hourly), Weekly Maintenance (Fri)
- [ ] extraPaths for cross-agent memory
- [ ] HEARTBEAT.md with guards (line limit, log compactness, digest age)

### LLM Tiers
- [ ] Budget / Standard / Power / Media in .env
- [ ] openclaw.json with ${LLM_*} variables

### Agent Management
- [ ] openclaw-installer add-agent (post-installation)
- [ ] openclaw-installer remove-agent

---

## v0.3.0 — "Unleash the Beast" 🐧
*Native Linux, systemd, no Docker.*

### Native Installation
- [ ] Wizard: Native vs. Docker selection
- [ ] Check/install Node.js (fnm)
- [ ] Install openclaw via npm globally
- [ ] Generate systemd user service
- [ ] ExecStartPost for restore_exec_approvals.py
- [ ] loginctl enable-linger
- [ ] Generate sudoers entry (specific, no wildcard)

### System Integration
- [ ] FTS5 check (Node + SQLite)
- [ ] Generate crontab (instead of Docker-internal crons)
- [ ] Generate backup script (daily_backup.py)
- [ ] Generate morning briefing
- [ ] openclaw-installer doctor (diagnostics)

---

## v0.4.0 — "Shape Shifter" 🔄
*Migration, Updates, Portability.*

- [ ] openclaw-installer migrate docker-to-native
- [ ] openclaw-installer migrate native-to-docker
- [ ] openclaw-installer update (check version, backup before update, post-update check)
- [ ] openclaw-installer backup / restore
- [ ] platformdirs integration (no hardcoded ~/...)

---

## v0.5.0 — "All Platforms" 🌐
*macOS + Windows Support.*

- [ ] macOS: launchd service (~/Library/LaunchAgents/)
- [ ] macOS: Docker Desktop integration
- [ ] Windows: NSSM Service Manager
- [ ] Windows: Docker Desktop integration
- [ ] PyInstaller binaries (no Python required on host)
- [ ] Cross-platform tests (GitHub Actions Matrix)

---

## Backlog / Long-term

- [ ] Web UI for wizard (Textual TUI or browser-based)
- [ ] Plugin system (install skills via wizard)
- [ ] Auto-discovery: detect existing OpenClaw installation
- [ ] Telemetry (opt-in, anonymized): installation success rate
- [ ] Community Skills Repository integration (ClaWHub)
- [ ] Cluster mode (multiple servers)

---

## Principles

1. **Every version is stable in itself** — no "only works with v0.3"
2. **Secure by Default** — every version, every feature
3. **Backward compatible** — config from v0.1 works in v0.5
4. **Wizard prevents poor decisions** — friction for risk
5. **All Python** — wizard, scripts, skills, tests
6. **Docker first, Native second** — but native is first-class, not an afterthought
