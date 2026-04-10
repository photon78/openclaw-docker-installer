# Install Notes — OpenClaw Docker Installer

**Version:** v0.2.0  
**Audience:** Technical — assumes Docker knowledge, no OpenClaw prior knowledge required

---

## Prerequisites

| What | Details |
|------|---------|
| **Docker** | Docker Engine 20.10+ or Docker Desktop. Must be running. |
| **Python** | 3.11 or 3.12. Pre-installed on most Linux/macOS systems. |
| **LLM API Key** | At least one: [Anthropic](https://console.anthropic.com) or [Mistral](https://console.mistral.ai). Both is better. |
| **Messaging channel** | Optional but recommended: Telegram Bot Token (via [@BotFather](https://t.me/BotFather)) |
| **Port 18789** | Must be free (OpenClaw gateway default) |
| **Disk** | ~500 MB for Docker image + workspace |
| **Internet** | Required during install (image pull, GitHub Releases API) |

---

## What Gets Installed

### Files written to `~/.openclaw/`

| File | What it is |
|------|------------|
| `.env` | API keys, LLM tier assignments |
| `openclaw.json` | Gateway + agent configuration |
| `exec-approvals.json` | Security allowlist (which scripts the agent may run) |
| `docker-compose.yml` | Container definition, pinned to latest release |
| `scripts/restore_exec_approvals.py` | Restores allowlist if gateway overwrites it |
| `scripts/restore_config.py` | Restores openclaw.json after gateway update |
| `scripts/daily_backup.py` | Backup script (if backup enabled) |

### Workspace written to `~/.openclaw/workspace/`

| File | What it is |
|------|------------|
| `SOUL.md` | Agent identity, rules, model routing |
| `AGENTS.md` | Tool rules, spawning policy, communication |
| `HEARTBEAT.md` | What the agent does on each scheduled wake |
| `IDENTITY.md` | Agent name and emoji |
| `MEMORY.md` | Long-term memory (agent fills over time) |
| `USER.md` | Your profile: name, timezone, tech level |
| `TOOLS.md` | Available skills and scripts |
| `BOOTSTRAP.md` | First-run guide (delete after setup) |
| `scripts/check_tasks.py` | Task queue checker |
| `tasks/cron-setup.md` | Task: set up recommended cron jobs after install |
| `skills/` | Bundled skills: web-search, docs-summarize, mistral-ocr, mistral-translate, mistral-transcribe |

### Docker container

| What | Details |
|------|---------|
| Image | `ghcr.io/openclaw/openclaw:<latest-release>` |
| Container name | `openclaw-gateway` |
| Port | `18789` (localhost only by default) |
| Restart policy | `unless-stopped` |
| Volume | `~/.openclaw` mounted at `/home/node/.openclaw` |

---

## Setup Wizard — Step by Step

### Step 1: Welcome
Pre-flight check for Docker and Python. Must pass to continue.

### Step 2: API Keys
Enter at least one LLM API key:
- **Anthropic** (`sk-ant-...`) — Claude models
- **Mistral** (`...`) — Mistral models, also needed for OCR/translate/transcribe skills

LLM tiers are assigned automatically:
- Anthropic only → all 4 tiers use Anthropic models
- Mistral only → all 4 tiers use Mistral models
- Both → Budget/Media = Mistral, Standard/Power = Anthropic

Optional: Telegram Bot Token. Skip to configure later.

### Step 3: About You
- **Display name** — how the agent addresses you
- **Timezone** — IANA format (e.g. `Europe/Zurich`)
- **Technical background** — adapts agent communication style

### Step 4: Persona
- Agent name and emoji
- Communication style preset: Direct / Formal / Friendly

### Step 5: Channel
Messaging channel: Telegram, Discord, Signal, or skip.  
For Telegram: enter Bot Token + your Telegram user ID (allowlist).

### Step 6: Security
Security profile: Strict (recommended) / Standard / Custom.  
Strict = minimal allowlist, no shell tools, ask before any new exec.

### Step 7: Backup
Optional. Enter a mount path for the backup target (e.g. `/mnt/backup`).  
Skipping is fine — configure later by editing `docker-compose.yml`.

### After the wizard
1. Config files are generated
2. Docker image is pulled (shows progress)
3. Container starts
4. Gateway health is polled (up to 90s)
5. Completion screen shows gateway token and next steps

---

## After Installation

### Verify it works
```bash
# Check container is running
docker ps | grep openclaw

# Check logs
docker compose -f ~/.openclaw/docker-compose.yml logs -f

# Open Control UI
open http://127.0.0.1:18789
```

Paste your gateway token (shown at end of install, also in `~/.openclaw/openclaw.json` → `gateway.auth.token`).

### Set up cron jobs (once, manually)
The installer cannot set up crons automatically — OpenClaw manages them via CLI after the gateway starts.  
Open `~/.openclaw/workspace/tasks/cron-setup.md` for ready-to-run commands.

### Send your first message
Open Telegram → your bot → send any message.

---

## Do Not Touch (without knowing what you're doing)

| File | Why |
|------|-----|
| `exec-approvals.json` | Controls what the agent can execute. Wrong changes = security hole or broken agent. |
| `exec-approvals.json` → `autoAllowSkills` | Must stay `false`. Setting to `true` silently approves all skill execs. |
| `openclaw.json` → `gateway.auth.token` | This is your master access token. Keep it secret. |
| `workspace/SOUL.md` → Red Lines section | Hard limits for the agent. Don't remove without understanding consequences. |
| `docker-compose.yml` → image tag | Don't change manually — use `./run.sh update` when available. |

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'typer'"
Use the launcher: `./run.sh install` — not `python3 src/main.py install`.  
The launcher sets up the venv automatically.

### Permission denied on `run.sh`
```bash
chmod +x run.sh
```

### Gateway timeout after 90s
Check the logs:
```bash
docker compose -f ~/.openclaw/docker-compose.yml logs --tail 30
```
Common causes:
- Invalid `openclaw.json` (check for typos if edited manually)
- Port 18789 already in use: `lsof -i :18789`
- Docker not running: `docker info`

### Agent doesn't respond on Telegram
1. Verify bot token is correct in `~/.openclaw/.env`
2. Check `dmPolicy` in `openclaw.json` → `channels.telegram.dmPolicy`
3. Check `allowFrom` — your Telegram user ID must be listed
4. Check gateway logs for auth errors

### "Unrecognized key" error in gateway logs
An invalid key was added to `openclaw.json`. Known invalid keys:
- `cron.jobs` (use `openclaw cron add` CLI instead)
- `plugins.entries.<name>.spec`
- `agents.defaults.models` (alias block)

Run `openclaw doctor` to diagnose.

### Gateway token not shown at install end
The token is written to `openclaw.json` by OpenClaw after first start.  
Read it manually:
```bash
python3 -c "import json; d=json.load(open('$HOME/.openclaw/openclaw.json')); print(d['gateway']['auth']['token'])"
```

---

## Updating

```bash
# Pull latest installer changes
git pull

# Restart with new image
./run.sh clean --yes
./run.sh install
```

Or (once implemented): `./run.sh update` — pulls new image without full reinstall.
