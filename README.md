# openclaw-docker-installer

> OpenClaw in a Box — complete, production-ready OpenClaw instance in just a few minutes.

## Status
🚧 Work in progress — Early development phase

## Vision

> *An LLM agent with shell access is a controlled weapon. The capability isn't the problem — uncontrolled capability is. This system gives the agent exactly as much power as it needs, and not a byte more.*

OpenClaw is powerful. Too powerful for an unsecured default installation.

This installer doesn't just set up an OpenClaw instance — it sets up a **secure** one. By default. Without the user needing to know what `exec-approvals`, allowlists, or security levels mean.

**Principles:**
- **Security by Default** — restrictive allowlist, no root access, no dangerous tools
- **Human in the Loop** — preconfigured approval mechanism, irreversible actions require confirmation
- **Guardrails over Convenience** — the wizard explains what each decision means
- **Headless-ready** — runs on Raspberry Pi without a display
- **Clean Separation** — core logic is UI-independent, TUI is an overlay

## Features (planned v1)
- Docker availability check
- API key input (Anthropic, optional Mistral/Telegram)
- Model selection
- `docker-compose.yml` + `.env` generation
- Workspace bootstrapping (AGENTS.md, SOUL.md, MEMORY.md)
- Post-install gateway check

## Requirements
- Python 3.11+
- Docker + Docker Compose

## Stack
- TUI: `rich` + `questionary` (or `textual`)
- Docker: Python Docker SDK
- System: `psutil`, `httpx`, `platformdirs`
- Config: TOML (`tomllib` Stdlib)
- Templates: Jinja2
- Packaging: PyInstaller → single binary

## Structure
```
src/
  main.py              ← Entry point
  tui/
    wizard.py          ← Main wizard
    steps/             ← One step per module
  docker/
    compose_gen.py     ← docker-compose + .env generator
    templates/         ← Jinja2 templates
  bootstrap/
    workspace.py       ← Create workspace structure
    templates/         ← AGENTS.md, SOUL.md, MEMORY.md
  checks/
    docker_check.py    ← Docker available?
    gateway_check.py   ← Post-install ping
tests/
```

## License
MIT — free to use, modify, and distribute.

If this saved you some time — or just made you smile — Photon would love a glass of good Valais red wine. No pressure, just appreciation.

🟥 [paypal.me/photon78](https://paypal.me/photon78) 🍷
