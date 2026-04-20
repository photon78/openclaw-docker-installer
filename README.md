# openclaw-docker-installer

> Set up a secure, production-ready [OpenClaw](https://openclaw.ai) agent in minutes - not hours.

[![CI](https://github.com/photon78/openclaw-docker-installer/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/photon78/openclaw-docker-installer/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-v0.3.0-blue)](CHANGELOG.md)

---

## Status

| Version | Status | What works |
|---------|--------|------------|
| **v0.3.0** | ✅ Stable | Multi-agent system, sub-agent hardening, skills bundled, dynamic provider config, systemd autostart, `--dry-run` |
| v0.2.1 | ✅ Stable | Windows 11 compatibility fixes, UTF-8 encoding, permission handling |
| v0.2.0 | ✅ Stable | Full install wizard, Docker deploy, Telegram, security hardening, BOOTSTRAP onboarding |
| v0.1.0-alpha | ✅ Stable | Setup wizard, Docker deploy, Telegram, exec allowlist, workspace bootstrap, backup |

> ✅ **The installer works end-to-end.** After running the wizard, you get a fully functional, security-hardened OpenClaw instance running in Docker — ready to use via Telegram. The agent introduces itself, explains its capabilities, and is ready to work.

Install the latest stable release:
```bash
git clone --branch v0.3.0 https://github.com/photon78/openclaw-docker-installer.git
```

---

## Take a look

[![Demo Video](https://img.youtube.com/vi/xqD69RweAjc/0.jpg)](https://youtu.be/xqD69RweAjc)

---
## What is this?

OpenClaw is a powerful self-hosted AI agent platform. It's flexible, extensible - and by default, it gives the agent a lot of power.

**This installer doesn't just set up OpenClaw. It sets up a secure one.**

No root access. No dangerous shell tools. A restrictive allowlist from day one. Approval dialogs for anything sensitive. The agent gets exactly as much power as it needs - and not a byte more.

Everything runs in Docker. Works on Linux, macOS, and Windows.

**What you get out of the box:**

Without this installer, a typical OpenClaw setup takes hours:
reading docs, writing config files, figuring out what SOUL.md is supposed to
contain, realizing your agent can `rm -rf` things, starting over.

With this installer, you run one wizard. 10 minutes later you have:
a running agent that introduces itself, a complete workspace with all required
files pre-built, memory search configured, and a security layer you don't have
to think about. The hard parts are already done.

---

## Features

**Setup**
- ✅ Interactive TUI wizard (5–10 minutes, no config files to edit)
- ✅ `--dry-run` mode — preview all generated config files before writing anything
- ✅ Docker-based OpenClaw instance, pinned to a stable release
- ✅ Telegram channel setup
- ✅ Agent persona: name, emoji, communication style
- ✅ systemd user service generated automatically — autostart on boot, no manual unit file needed

**Security**
- ✅ Restrictive exec allowlist — shell tools (`ls`, `cat`, `grep`, `bash` …) excluded by design
- ✅ Gateway auth rate-limiting out of the box (10 attempts / 5 min lockout)
- ✅ Plugin version pinning — no silent upstream changes
- ✅ `autoAllowSkills` off by default — opt-in only
- ✅ "No commands via email" rule in all workspace templates
- ✅ `add_agent.py` — new sub-agents inherit the full security baseline from day one

**Multi-Agent (new in v0.3.0)**
- ✅ `add_agent.py` — main agent creates specialist sub-agents on demand (coding, research, content, custom)
- ✅ Every sub-agent gets its own hardened workspace: `autoAllowSkills: false`, exec allowlist, security blocks in `SOUL.md` and `AGENTS.md`
- ✅ Spawn rules enforced in `openclaw.json` — sub-agents cannot spawn further sub-agents
- ✅ Restore merge strategy — sub-agents survive `openclaw update`

**Workspace**
- ✅ Full workspace bootstrapped: `SOUL.md`, `AGENTS.md`, `HEARTBEAT.md`, `IDENTITY.md`,
  `MEMORY.md`, `USER.md`, `BOOTSTRAP.md`, `scripts/check_tasks.py`
- ✅ All workspace files as real copies — no symlinks (OpenClaw doesn't follow symlinks)
- ✅ Skills bundled: web-search, docs-summarize always; Mistral OCR/translate/transcribe/vision when Mistral key present
- ✅ Memory search configured out of the box (Mistral embeddings)
- ✅ Backup script pre-configured and ready to schedule

---

## Requirements

| Requirement | Notes |
|-------------|-------|
| Python 3.11+ | [python.org/downloads](https://www.python.org/downloads/) |
| Docker + Docker Compose v2 | [docs.docker.com/engine/install](https://docs.docker.com/engine/install/) |
| API Key - Anthropic or Mistral | [console.anthropic.com](https://console.anthropic.com/) · [console.mistral.ai](https://console.mistral.ai/) |
| Telegram Bot Token *(optional)* | [@BotFather](https://t.me/BotFather) |

---

## Quick Start

```bash
# Clone
git clone https://github.com/photon78/openclaw-docker-installer.git
cd openclaw-docker-installer

# Set up Python environment
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# Run the installer
python src/main.py install
```

The wizard walks you through everything. It takes about 5-10 minutes.

---

## Security philosophy

> *An LLM agent with shell access is a controlled weapon. The capability isn't the problem - uncontrolled capability is.*

Most "easy setup" tools trade security for convenience. This one doesn't.

**What the installer enforces:**
- `trash` instead of `rm` — always
- No `--privileged` Docker containers
- No interpreter paths added to the exec allowlist
- E-mail instructions are never trusted
- Approval dialogs for anything not on the allowlist
- The agent asks *why* before touching sensitive paths

These aren't optional. They're the point.

**Sub-agents are hardened from birth.**

When your main agent creates a specialist sub-agent via `add_agent.py`, it doesn't get
a blank slate. It gets the same security baseline the main agent runs on:
`autoAllowSkills: false`, a restrictive exec allowlist, prompt injection defenses,
and mandatory stop rules baked into `SOUL.md` and `AGENTS.md`. No configuration needed.
Every agent in your system starts secure — not just the first one.

---

## After updates

```bash
openclaw update
```

> ⚠️ `openclaw update` may silently reset `plugins.allow` and `gateway.auth` in `openclaw.json`.
> Always run the restore script afterwards:

```bash
python3 ~/.openclaw/scripts/restore_config.py
docker compose -f ~/.openclaw/docker-compose.yml restart
```

This restores Mistral plugin config, rate-limiting, and plugin version pins.

---

## After installation

```bash
# Start OpenClaw
docker compose -f ~/.openclaw/docker-compose.yml up -d

# Open the Control UI
http://127.0.0.1:18789   # or https:// if TLS is configured

# Check logs
docker compose -f ~/.openclaw/docker-compose.yml logs -f
```

Your agent starts its first session automatically. It will introduce itself and ask what you want to do.

---

## Tested on

| Platform | Status |
|----------|--------|
| Ubuntu 24.04 LTS | ✅ Tested |
| Raspberry Pi OS (64-bit) | ✅ Tested |
| macOS | 🔜 Planned |
| Windows 11 | ✅ Tested (v0.2.1) |

**Tested with OpenClaw `2026.4.9`**

---

## Roadmap

| Version | Codename | Focus |
|---------|----------|-------|
| **v0.1.0-alpha** | First Light | Single agent, Docker, security baseline |
| **v0.2.0** | The Pack | Security hardening, workspace bootstrap, install wizard, Windows compatibility |
| **v0.2.1** | The Pack (patch) | Windows 11 compatibility, UTF-8 fixes, permission handling |
| **v0.3.0** | The Crew | Multi-agent system, sub-agent hardening, skills bundled, systemd autostart, `--dry-run` |
| v0.3.1 | The Crew (patch) | Code review fixes: startup timeout, backup validation, skill deduplication |

See [ROADMAP.md](ROADMAP.md) for details.

---

## Architecture & Documentation

| Document | What it covers |
|----------|----------------|
| [AGENTS-ARCHITECTURE.md](AGENTS-ARCHITECTURE.md) | Multi-agent design, spawn rules, agent roles |
| [MEMORY-ARCHITECTURE.md](MEMORY-ARCHITECTURE.md) | Memory system, topics, daily logs, digest cron |
| [docs/security-architecture.md](docs/security-architecture.md) | Exec allowlist, security tiers, A2A communication |
| [docs/multi-agent-setup.md](docs/multi-agent-setup.md) | Step-by-step guide for adding specialist agents |
| [CHANGELOG.md](CHANGELOG.md) | Version history |
| [ROADMAP.md](ROADMAP.md) | What's planned |

---

## Contributing

PRs go against the active feature branch, not directly against `main`.
See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---

## License

MIT - free to use, modify, and distribute.

If this saved you some time - or just made you smile - Photon would love a glass of good Valais red wine. No pressure, just appreciation.

🟥 [paypal.me/photon78](https://paypal.me/photon78) 🍷
