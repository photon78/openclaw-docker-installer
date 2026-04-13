# Multi-Agent Setup Guide

**Audience:** Main agent (MAIN) and the human operator (HUMAN)  
**Scope:** How to add a second or third agent to an existing OpenClaw installation  
**Prerequisites:** Single-agent install completed, Gateway running

---

## Overview

The Docker installer sets up a **single agent** (MAIN). Multi-agent setups are
configured manually after the initial install — this guide walks through every step.

A typical multi-agent setup:
```
MAIN (orchestrator)
  ├── CODING_AGENT  — code, deployment, technical tasks
  ├── CONTENT_AGENT — writing, translation, content creation
  └── RESEARCH_AGENT — web research, document analysis (worker only, no spawn)
```

**Rules that never change:**
- Always ask HUMAN before adding a new agent or changing spawn permissions
- `maxSpawnDepth: 2` — main → subagent → research (never higher, exponential complexity)
- RESEARCH_AGENT (or any pure worker) has `allowAgents: []`
- New agent = new exec-approvals section (no exceptions)
- `autoAllowSkills: false` — always, no exceptions (see SECURITY-ARCHITECTURE.md)

---

## Step 1: Create the Workspace

Each agent needs its own workspace directory with real file copies (no symlinks).

```bash
# Example: adding CODING_AGENT
mkdir -p ~/.openclaw/workspace-coding/{memory/topics,tasks,scripts,skills}
```

Copy and customize the workspace files (all must be real copies, not symlinks):

| File | Action |
|------|--------|
| `SOUL.md` | Define role, model routing, hard limits, no-email rule |
| `AGENTS.md` | Tool rules, communication norms, spawning policy, Stop-Regel, Approval-Format |
| `HEARTBEAT.md` | What to do on each heartbeat wake |
| `BOOT.md` | Startup checklist after gateway restart / container reboot |
| `IDENTITY.md` | Name, emoji, avatar |
| `MEMORY.md` | Start empty, agent fills it over time |
| `USER.md` | Copy from main workspace (same HUMAN) |
| `TOOLS.md` | Skills, scripts, git remotes, deploy targets |
| `BOOTSTRAP.md` | First-run guide (delete after first session) |
| `scripts/check_tasks.py` | Copy and update `TASKS_DIR` path |
| `scripts/clean_exec_approvals.py` | Weekly hygiene (generated, run via cron) |

**Skills:** Symlink the shared skills directory:
```bash
ln -s ~/.openclaw/workspace/skills ~/.openclaw/workspace-coding/skills
```
Or use a shared Docker volume (recommended for containers — see Step 4).

---

## Step 2: Register Agent in `openclaw.json`

Add the new agent to `agents.list`. Use the existing MAIN entry as reference.

```json
{
  "agents": {
    "list": [
      {
        "id": "main",
        "workspace": "/home/node/.openclaw/workspace",
        "subagents": {
          "allowAgents": ["coding_agent", "research_agent"]
        }
      },
      {
        "id": "coding_agent",
        "workspace": "/home/node/.openclaw/workspace-coding",
        "model": {
          "primary": "${LLM_POWER}",
          "fallbacks": ["${LLM_BUDGET}"]
        },
        "subagents": {
          "allowAgents": ["research_agent"]
        }
      },
      {
        "id": "research_agent",
        "workspace": "/home/node/.openclaw/workspace-research",
        "model": {
          "primary": "${LLM_BUDGET}",
          "fallbacks": ["${LLM_STANDARD}"]
        },
        "subagents": {
          "allowAgents": []
        }
      }
    ],
    "defaults": {
      "subagents": {
        "maxConcurrent": 2,
        "maxSpawnDepth": 2
      }
    }
  }
}
```

**Model values:** Use `${LLM_BUDGET}` etc. — OpenClaw resolves `${VAR}` references
from `.env` at runtime. Change models by editing `.env` only, no `openclaw.json` edit needed.

---

## Step 3: Add exec-approvals Section

Every agent needs an explicit section in `exec-approvals.json`.
**Never use `autoAllowSkills: true`** — this silently approves all skill executions
without oversight (learned the hard way: hanging Playwright process, no alert).

```json
{
  "agents": {
    "main": { "...": "existing main config" },

    "coding_agent": {
      "security": "allowlist",
      "ask": "on-miss",
      "askFallback": "deny",
      "autoAllowSkills": false,
      "allowlist": [
        {"pattern": "/usr/bin/python3",       "id": "ca-python3-01"},
        {"pattern": "/usr/bin/git",           "id": "ca-git-01"},
        {"pattern": "/usr/bin/df",            "id": "ca-df-01"},
        {"pattern": "/usr/bin/du",            "id": "ca-du-01"},
        {"pattern": "/usr/bin/free",          "id": "ca-free-01"},
        {"pattern": "/usr/bin/ps",            "id": "ca-ps-01"},
        {"pattern": "/usr/bin/trash",         "id": "ca-trash-01"},
        {"pattern": "<workspace>/scripts/check_tasks.py",            "id": "ca-check-tasks-01"},
        {"pattern": "<workspace>/skills/web-search/search.py",       "id": "ca-web-search-01"},
        {"pattern": "<workspace>/skills/docs-summarize/summarize.py","id": "ca-docs-summarize-01"}
      ]
    },

    "research_agent": {
      "security": "allowlist",
      "ask": "on-miss",
      "askFallback": "deny",
      "autoAllowSkills": false,
      "allowlist": [
        {"pattern": "/usr/bin/python3",       "id": "ra-python3-01"},
        {"pattern": "<workspace>/skills/web-search/search.py",       "id": "ra-web-search-01"},
        {"pattern": "<workspace>/skills/docs-summarize/summarize.py","id": "ra-docs-summarize-01"}
      ]
    }
  }
}
```

Replace `<workspace>` with the actual container-internal path (e.g. `/home/node/.openclaw/workspace-coding`).

---

## Step 4: Docker Volume (if using containers)

Add the new workspace as a volume mount in `docker-compose.yml`:

```yaml
services:
  openclaw-gateway:
    volumes:
      - ~/.openclaw:/home/node/.openclaw          # main config + workspace
      - ~/.openclaw/workspace-coding:/home/node/.openclaw/workspace-coding
      - ~/.openclaw/workspace-research:/home/node/.openclaw/workspace-research
      # Shared skills — one directory, all agents
      - ~/.openclaw/workspace/skills:/home/node/.openclaw/skills:ro
```

---

## Step 5: Connect a Telegram Bot (per agent)

Each agent needs its own Telegram bot token. One token = one bot = one agent.

1. Create a new bot via [@BotFather](https://t.me/BotFather) → `/newbot`
2. Add the token to `.env`:
   ```env
   TELEGRAM_BOT_TOKEN_CODING=<token>
   ```
3. Reference it in `openclaw.json` under the agent's channel config

---

## Step 6: Reload the Gateway

```bash
docker compose restart openclaw-gateway
```

Or via the OpenClaw CLI:
```bash
openclaw gateway restart
```

Verify the new agent appears in `/status` or the web UI.

---

## Cron Awareness for Sub-Agents

The following crons run system-wide and affect all agents. Sub-agents should
know about them — include this in their `HEARTBEAT.md` or `SOUL.md`:

| Cron | Schedule | What it does |
|------|----------|-------------|
| **Daily Memory Digest** | 03:05 daily | Runs `memory_digest.py` → writes `digest-latest.md` to all workspaces |
| **Gateway Health Check** | Every 2h | Checks gateway status, alerts HUMAN on problem |

Scripts live in `~/.openclaw/scripts/` (host) or `/home/node/.openclaw/scripts/` (container).

Sub-agents can call these scripts directly if needed:
```
python3 /home/node/.openclaw/scripts/memory_digest.py
python3 /home/node/.openclaw/scripts/hourly_log.py
```

`hourly_log.py` returns a JSON mapping of all active agents — useful for
sub-agents that need to know who else is running.

---

## Checklist: New Agent

- [ ] Workspace directory created with all required files (real copies, no symlinks)
- [ ] `SOUL.md` includes no-email rule and hard limits
- [ ] `scripts/check_tasks.py` has correct `TASKS_DIR` path
- [ ] Agent registered in `openclaw.json` → `agents.list`
- [ ] `allowAgents` configured for all relevant agents (ask HUMAN first)
- [ ] `maxSpawnDepth: 2` in `agents.defaults.subagents` (main → subagent → research)
- [ ] exec-approvals section added with `autoAllowSkills: false`
- [ ] Allowlist complete (every script the agent needs, explicitly listed)
- [ ] Telegram bot created and token added to `.env`
- [ ] Docker volume mount added (if containerized)
- [ ] Gateway reloaded
- [ ] `/status` confirms new agent is active

---

*This guide is maintained by the installer project. Re-run the installer after
major OpenClaw version upgrades to regenerate base configs.*
