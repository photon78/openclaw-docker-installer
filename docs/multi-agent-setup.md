# Multi-Agent Setup Guide

**Audience:** Main agent (MAIN) and the human operator (HUMAN)  
**Scope:** How to add a second or third agent to an existing OpenClaw installation  
**Prerequisites:** Single-agent install completed with the Docker installer, Gateway running

---

## Overview

The Docker installer sets up a **single main agent** (MAIN). Additional agents are added with the bundled `add_agent.py` script after the initial install.

A typical multi-agent setup:

```
MAIN (orchestrator)
  ├── CODING  — code, deployment, technical tasks
  ├── RESEARCH — web research, document analysis (worker only, no spawn)
  └── CONTENT — writing, translation, content creation
```

**Rules that never change:**
- Always ask HUMAN before adding a new agent or changing spawn permissions
- `maxSpawnDepth: 1` — spawned agents cannot spawn further agents
- Pure worker agents (e.g. RESEARCH) have `allowAgents: []`
- Every new agent gets its own `exec-approvals` section with `autoAllowSkills: false`

---

## Step 1: Run `add_agent.py`

The installer copies `add_agent.py` into `~/.openclaw/scripts/`. Run it from inside the OpenClaw container (or from the host if `openclaw` CLI is available):

```bash
python3 ~/.openclaw/scripts/add_agent.py \
  --name coding \
  --emoji 💻 \
  --type coding \
  --dry-run
```

Available archetypes:

| Type | Purpose |
|------|---------|
| `coding` | Code, build, deployment, technical tasks |
| `research` | Web research, summarisation, fact-checking |
| `content` | Writing, translation, formatting |
| `custom` | Generic template, configure role manually in `SOUL.md` |

**Always use `--dry-run` first.** Review the output, then remove the flag to apply changes.

### What `add_agent.py` does

1. Creates `~/.openclaw/workspace-<name>/` with:
   - `SOUL.md`, `AGENTS.md`, `HEARTBEAT.md`, `IDENTITY.md`
   - `TOOLS.md`, `MEMORY.md`, `USER.md`
   - Directories: `memory/`, `memory/topics/`, `tasks/`, `scripts/`
2. Copies `scripts/check_tasks.py` from the main workspace
3. Symlinks `skills/` to the main workspace skills directory
4. Registers the agent via `openclaw agents add --non-interactive`
5. Falls back to a manual JSON patch if the CLI is unavailable
6. Adds a minimal `exec-approvals.json` section with `autoAllowSkills: false`

---

## Step 2: Add Telegram Bot Token

Each agent needs its own Telegram bot. One token = one bot = one agent.

1. Create a bot via [@BotFather](https://t.me/BotFather) → `/newbot`
2. Add the token to `~/.openclaw/.env`:
   ```env
   TELEGRAM_BOT_TOKEN_CODING=<token>
   ```
3. Map the token in `openclaw.json` under the new agent's `channels.telegram.botToken` — use the SecretRef pattern from the main agent as a template.

> The installer sets up SecretRefs by default; never paste raw tokens into `openclaw.json`.

---

## Step 3: Add Docker Volume (if containerized)

If you run OpenClaw in Docker, mount the new workspace into `docker-compose.yml`:

```yaml
services:
  openclaw-gateway:
    volumes:
      - ~/.openclaw:/home/node/.openclaw
      - ~/.openclaw/workspace-coding:/home/node/.openclaw/workspace-coding
      - ~/.openclaw/workspace-research:/home/node/.openclaw/workspace-research
```

`add_agent.py` creates the workspace on the host filesystem. The Docker volume mount makes it visible inside the container.

---

## Step 4: Restart the Gateway

```bash
docker compose -f ~/.openclaw/docker-compose.yml restart openclaw-gateway
```

Or via the OpenClaw CLI:

```bash
openclaw gateway restart
```

Verify the new agent appears in `/status` or the web UI.

---

## Spawn Configuration

`add_agent.py` registers each new agent with a safe default:

```json
{
  "subagents": {
    "maxSpawnDepth": 1,
    "allowAgents": []
  }
}
```

After creation, edit `openclaw.json` (or use `openclaw agents update`) to grant spawn permissions:

- MAIN may spawn CODING and RESEARCH
- CODING may spawn RESEARCH
- RESEARCH has `allowAgents: []` — it cannot spawn anything

**Ask HUMAN before changing `allowAgents` or `maxSpawnDepth`.**

---

## Workspace Files

All files created by `add_agent.py` are real copies. The only symlink is `skills/` pointing to the main workspace skills directory — this is intentional because skills are shared across agents and OpenClaw follows this specific symlink.

| File | Purpose |
|------|---------|
| `SOUL.md` | Role, model routing, hard limits, no-email rule |
| `AGENTS.md` | Tool rules, communication norms, spawn policy |
| `HEARTBEAT.md` | What to do on each heartbeat wake |
| `IDENTITY.md` | Name, emoji, role |
| `MEMORY.md` | Long-term memory (starts empty) |
| `USER.md` | Copy/adapt user info from main workspace |
| `TOOLS.md` | Scripts, skills, git/deployment targets |
| `BOOTSTRAP.md` | First-run guide (created by installer for MAIN only) |

Copy `USER.md` from the main workspace and adjust it for the new agent.

---

## exec-approvals.json

`add_agent.py` adds a minimal section:

```json
{
  "agents": {
    "coding": {
      "autoAllowSkills": false,
      "allowlist": []
    }
  }
}
```

**Never set `autoAllowSkills: true`.** After the agent is running, approve commands on first use via the chat approval flow, then run `sync_allowlist.py --apply` (bundled in `workspace/scripts/shared/`) to persist the approved entries.

---

## Sicherheitshinweis: Task-Files statt direktem A2A-Messaging

**Direktes Agent-zu-Agent-Messaging über Message-Kanäle ist ein Sicherheitsrisiko.**

Wenn Agents strukturierte Daten direkt per `sessions_send` austauschen, können sensible Informationen — API-Keys, Nutzerdaten, interner State — unkontrolliert in fremde LLM-Kontexte gelangen. Das empfangende LLM sieht den gesamten Nachrichteninhalt.

**Empfohlen: Task-Files** in `workspace/tasks/YYYY-MM-DD-<name>.md`
- Strukturierte Aufgabenübergabe ohne LLM-Kontextleak
- Asynchron, auditierbar, im Dateisystem nachvollziehbar
- Empfangender Agent liest via `check_tasks.py` nur was er braucht

`sessions_send` bleibt erlaubt für kurze Status-Updates und Eskalationen an den Operator — nicht für strukturierte Daten oder Credentials.

---

## Checklist: New Agent

- [ ] `add_agent.py --dry-run` reviewed and looks correct
- [ ] Agent created with `add_agent.py` (without `--dry-run`)
- [ ] Telegram bot created and token added to `.env`
- [ ] SecretRef for bot token configured in `openclaw.json`
- [ ] Docker volume mount added (if containerized)
- [ ] Spawn permissions reviewed and limited (`maxSpawnDepth: 1`, worker agents `allowAgents: []`)
- [ ] `exec-approvals.json` section present with `autoAllowSkills: false`
- [ ] Gateway restarted
- [ ] `/status` confirms new agent is active
- [ ] Test message sent to new agent via Telegram

---

## Troubleshooting

**`openclaw agents add` fails**
- Ensure the Gateway container is running
- Check that `openclaw` CLI is in `PATH`
- `add_agent.py` falls back to manual JSON patching — verify `openclaw.json` was updated

**Agent does not appear in `/status`**
- Verify the workspace path in `openclaw.json`
- Check Docker volume mount
- Look at Gateway logs: `docker compose logs -f openclaw-gateway`

**Skills are missing**
- `skills/` is a symlink to the main workspace skills directory
- Ensure the main workspace has skills installed
- In Docker, both workspaces must be mounted from the same host path

---

*This guide is maintained by the installer project. Re-run the installer after major OpenClaw version upgrades to regenerate base configs.*
