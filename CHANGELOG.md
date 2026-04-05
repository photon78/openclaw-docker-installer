# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Pre-flight checks: Docker availability, version, Compose v2
- Gateway reachability check (HTTP ping)
- Unit tests for `docker_check` and `gateway_check` (mock-based, no Docker required)
- `ROADMAP.md` — v0.1.0 through v0.5.0
- `SECURITY-ARCHITECTURE.md` — 5-layer security model, honest threat model
- `MEMORY-ARCHITECTURE.md` — three-layer memory system reference
- `DESIGN-DECISIONS.md` — architectural decisions with rationale
- Community files: CONTRIBUTING.md, CHANGELOG.md, CODE_OF_CONDUCT.md, SECURITY.md
- GitHub Issue Templates (Bug / Feature / Security)
- CI workflow: ruff, mypy, pytest, Docker build test

### Planned for v0.1.0
- Interactive TUI wizard (questionary + rich)
- `docker-compose.yml` + `.env` generation
- `exec-approvals.json` generation (Security-Profil: Strict / Standard)
- `restore_exec_approvals.py` generation
- Workspace bootstrapping (AGENTS.md, SOUL.md, MEMORY.md templates)
- Post-install Gateway check

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

[Unreleased]: https://github.com/photon78/openclaw-docker-installer/compare/v0.0.1...HEAD
[0.0.1]: https://github.com/photon78/openclaw-docker-installer/releases/tag/v0.0.1
