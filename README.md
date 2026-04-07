# openclaw-docker-installer

> Set up a secure, production-ready [OpenClaw](https://openclaw.ai) agent in minutes — not hours.

[![CI](https://github.com/photon78/openclaw-docker-installer/actions/workflows/ci.yml/badge.svg)](https://github.com/photon78/openclaw-docker-installer/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-v0.1.0--alpha-blue)](CHANGELOG.md)

---

## What is this?

OpenClaw is a powerful self-hosted AI agent platform. It's flexible, extensible — and by default, it gives the agent a lot of power.

**This installer doesn't just set up OpenClaw. It sets up a secure one.**

No root access. No dangerous shell tools. A restrictive allowlist from day one. Approval dialogs for anything sensitive. The agent gets exactly as much power as it needs — and not a byte more.

Everything runs in Docker. Works on Linux, macOS, and Windows.

---

## What you get

- ✅ Interactive setup wizard (5–10 minutes)
- ✅ Docker-based OpenClaw instance, pinned to a stable release
- ✅ Restrictive exec allowlist — no `rm`, no root, no shell wildcards
- ✅ Workspace bootstrapped: `AGENTS.md`, `SOUL.md`, `MEMORY.md`, `BOOTSTRAP.md`
- ✅ Memory search configured out of the box (Mistral embeddings)
- ✅ Telegram, Discord, or Signal channel setup
- ✅ Backup script pre-configured and ready to schedule
- ✅ Agent persona: name, emoji, communication style

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

## After installation

```bash
# Start OpenClaw
docker compose -f ~/.openclaw/docker-compose.yml up -d

# Open the Control UI
http://127.0.0.1:18789

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
