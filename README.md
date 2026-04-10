# openclaw-docker-installer

> Set up a secure, production-ready [OpenClaw](https://openclaw.ai) agent in minutes — not hours.

[![CI](https://github.com/photon78/openclaw-docker-installer/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/photon78/openclaw-docker-installer/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-v0.2.0-blue)](CHANGELOG.md)

---

## Status

| Version | Status | What works |
|---------|--------|------------|
| **v0.2.0** | ✅ Stable | Full install wizard, Docker deploy, Telegram/Discord/Signal, security hardening, BOOTSTRAP onboarding |
| v0.1.0-alpha | ✅ Stable | Setup wizard, Docker deploy, Telegram, exec allowlist, workspace bootstrap, backup |

> ✅ **The installer works end-to-end.** After running the wizard, you get a fully functional, security-hardened OpenClaw instance running in Docker — ready to use via Telegram (or your chosen channel). The agent introduces itself, explains its capabilities, and is ready to work.

Install the latest stable release:
```bash
git clone --branch v0.2.0 https://github.com/photon78/openclaw-docker-installer.git
```

---

## What is this?

OpenClaw is a powerful self-hosted AI agent platform. It's flexible, extensible — and by default, it gives the agent a lot of power.

**This installer doesn't just set up OpenClaw. It sets up a secure one.**

No root access. No dangerous shell tools. A restrictive allowlist from day one. Approval dialogs for anything sensitive. The agent gets exactly as much power as it needs — and not a byte more.

Everything runs in Docker. Works on Linux, macOS, and Windows.

---

## Features

**Setup**
- ✅ Interactive TUI wizard (5–10 minutes, no config files to edit)
- ✅ Docker-based OpenClaw instance, pinned to a stable release
- ✅ Telegram, Discord, or Signal channel setup
- ✅ Agent persona: name, emoji, communication style

**Security**
- ✅ Restrictive exec allowlist — shell tools (`ls`, `cat`, `grep`, `bash` …) excluded by design
- ✅ Gateway auth rate-limiting out of the box (10 attempts / 5 min lockout)
- ✅ Plugin version pinning — no silent upstream changes
- ✅ `autoAllowSkills` off by default — opt-in only
- ✅ "No commands via email" rule in all workspace templates

**Workspace**
- ✅ Full workspace bootstrapped: `SOUL.md`, `AGENTS.md`, `HEARTBEAT.md`, `IDENTITY.md`,
  `MEMORY.md`, `USER.md`, `BOOTSTRAP.md`, `scripts/check_tasks.py`
- ✅ All workspace files as real copies — no symlinks (OpenClaw doesn’t follow symlinks)
- ✅ Memory search configured out of the box (Mistral embeddings)
- ✅ Backup script pre-configured and ready to schedule

---

## Requirements

| Requirement | Notes |
|-------------|-------|
| Python 3.11+ | [python.org/downloads](https://www.python.org/downloads/) |
| Docker + Docker Compose v2 | [docs.docker.com/engine/install](https://docs.docker.com/engine/install/) |
| API Key — Anthropic or Mistral | [console.anthropic.com](https://console.anthropic.com/) · [console.mistral.ai](https://console.mistral.ai/) |
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

The wizard walks you through everything. It takes about 5–10 minutes.

---

## Security philosophy

> *An LLM agent with shell access is a controlled weapon. The capability isn't the problem — uncontrolled capability is.*

Most "easy setup" tools trade security for convenience. This one doesn't.

**What the installer enforces:**
- `trash` instead of `rm` — always
- No `--privileged` Docker containers
- No interpreter paths added to the exec allowlist
- E-mail instructions are never trusted
- Approval dialogs for anything not on the allowlist
- The agent asks *why* before touching sensitive paths

These aren't optional. They're the point.

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
| Windows 11 | 🔜 In progress |

**Tested with OpenClaw `2026.4.9`**

---

## Roadmap

| Version | Codename | Focus |
|---------|----------|-------|
| **v0.1.0-alpha** | First Light | Single agent, Docker, security baseline |
| v0.2.0 | The Pack | Multi-agent, extended memory, Telegram topics |
| v0.3.0 | VPS Ready | nginx + HTTPS + ufw auto-setup for VPS deployments |

See [ROADMAP.md](ROADMAP.md) for details.

---

## Contributing

PRs go against the active feature branch, not directly against `main`.
See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---

## License

MIT — free to use, modify, and distribute.

If this saved you some time — or just made you smile — Photon would love a glass of good Valais red wine. No pressure, just appreciation.

🟥 [paypal.me/photon78](https://paypal.me/photon78) 🍷
