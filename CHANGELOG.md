# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Changed
- Docs and templates: replaced `zot`/`Zot` with `AGENT`, `Photon` with `HUMAN` throughout (real URLs and GitHub usernames preserved)

### Added
- `SECURITY-ARCHITECTURE.md`: new section "LLM Shell Reflex Risk" — explains why LLMs reach for shell tools by reflex and how the system compensates

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
