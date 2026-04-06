# Agents Architecture — OpenClaw Installer

> Reference for the installer: How agents are structured, why, and what the installer sets up.

---

## 1. Philosophy

### Why Multiple Specialized Agents Instead of One Generalist?

A single agent that can do everything is a single point of failure — and a single point of compromise.

**Specialization brings three concrete benefits:**

1. **Least-Privilege per Agent** — Each agent has only the tools, skills, and allowlist entries it actually needs. A coding agent has no business sending emails. A form-processing agent has no business touching Git.

2. **Better Prompts, Less Hallucination** — A tightly scoped SOUL.md and workspace produce more focused, reliable behavior. The agent isn't context-switching between roles.

3. **Cheaper Models** — Specialized tasks (email triage, form processing) don't need the most powerful model. Route them to cheaper models; reserve expensive ones for complex reasoning.

### The Core Principle

> *Give each agent exactly as much power as it needs — and not a byte more.*

This mirrors the allowlist philosophy in `DESIGN-DECISIONS.md DD-001`.

---

## 2. Standard Agent Types (Installer Default)

| Agent | Role | Model Tier | Allowlist Tier |
|-------|------|------------|----------------|
| `main` | Botmaster, Security Auditor, Heartbeat | Power | Elevated |
| `coding_AGENT` | Code, Website, Git, Deployment | Standard | Standard |
| `buero_AGENT` | Email, Documents, Accounting | Budget | Restricted |
| `formular_AGENT` | Form processing, Notifications | Budget | Restricted |

### main
- Orchestrates other agents via cross-session messaging
- Runs daily health check and morning briefing
- Reviews security alerts, integrity audit results
- Can restart gateway, manage systemd service
- Has broadest allowlist — but still no `rm`, no `pip install`

### coding_AGENT
- Code editing, website builds, Git operations
- Runs npm/astro/python3 builds
- Manages deployment scripts
- Has Git, Node, Python, SSH in allowlist
- No email, no system-level service management

### buero_AGENT
- Reads and sends email (dedicated email skill)
- Handles documents, invoices, correspondence
- No interpreter access — only named script paths in allowlist
- Cannot touch code repositories or system files

### formular_AGENT
- Processes incoming form submissions
- Sends confirmation emails (via shared secret, not free-form)
- Most restricted agent — smallest allowlist
- No web browsing, no file system access beyond workspace

---

## 3. Workspace Structure per Agent

Each agent gets its own workspace directory:

```
~/.openclaw/
  workspace/              ← main agent (primary workspace)
  workspace-coding/       ← coding_AGENT
  workspace-buero/        ← buero_AGENT
  workspace-formular/     ← formular_AGENT
```

### Per-Workspace Layout

```
workspace-<agent>/
  SOUL.md               ← Agent role, character, limits (unique per agent)
  IDENTITY.md           ← Name, emoji, vibe (unique per agent)
  MEMORY.md             ← Long-term memory (unique per agent)
  memory/
    YYYY-MM-DD.md       ← Daily logs
    digest-latest.md    ← Cross-agent digest (written by cron)
    topics/             ← Condensed knowledge per topic
    docs/               ← Permanent documentation references
  tasks/                ← Tasks from HUMAN or other agents
  work/                 ← Active work directories
  skills/               → symlink to ~/.openclaw/workspace/skills/
  skills-private/       ← Agent-specific skills (NOT a symlink)
  AGENTS.md             → symlink to shared AGENTS.md (or own extension)
  USER.md               → symlink to shared USER.md
  HEARTBEAT.md          → symlink to shared HEARTBEAT.md
```

### What Is Shared (Symlinks)

| File | Why Shared |
|------|-----------|
| `skills/` | All agents benefit from web-search, docs-summarize |
| `AGENTS.md` | Same mandatory rules for all agents |
| `USER.md` | Same user context everywhere |
| `HEARTBEAT.md` | Same heartbeat behavior |

### What Is Agent-Private

| File | Why Private |
|------|------------|
| `SOUL.md` | Different roles, different characters |
| `IDENTITY.md` | Different names, emojis |
| `MEMORY.md` | Different long-term knowledge |
| `memory/` | Different daily logs and topics |
| `skills-private/` | Different tool access |
| `tasks/` | Different task queues |

---

## 4. Skill Scoping

See `DESIGN-DECISIONS.md DD-006` for full rationale.

### Two-Tier Skill Structure

```
workspace-<agent>/
  skills/          ← Symlink → shared skills (all agents)
  skills-private/  ← Private skills (this agent only)
```

### Skill Assignment

| Skill | Shared | main | coding_AGENT | buero_AGENT | formular_AGENT |
|-------|--------|------|------------|-----------|--------------|
| `web-search` | ✅ | — | — | — | — |
| `docs-summarize` | ✅ | — | — | — | — |
| `email` | — | — | — | ✅ private | — |
| `git-workflows` | — | — | ✅ private | — | — |
| `voice-agent` | — | ✅ private | — | — | — |

### Installer Wizard

The wizard asks per agent:
> *"Which private skills should be activated for this agent?"*

Selected skills are deployed to `workspace-<agent>/skills-private/`.

---

## 5. Task System

Agents coordinate via a simple file-based task system — no database, no message broker.

### Convention

```
workspace-<agent>/tasks/YYYY-MM-DD-<short-description>.md
```

### Task File Format

```markdown
# Task: <Title>
**Created:** YYYY-MM-DD HH:MM | **By:** <agent or HUMAN> | **For:** <agent>

## Mission
What needs to be done and why.

## Steps
1. ...
2. ...

## Completion
- Update daily log
- Notify HUMAN if needed
```

### Workflow

1. **Session startup:** Agent checks `tasks/` for new files
2. **Execution:** Agent works through tasks one by one
3. **Completion:** Task file gets a completion note appended — never deleted
4. **Cross-agent:** main can write tasks into other agents' `tasks/` directories

### Why File-Based?

- Zero infrastructure (no Redis, no queue service)
- Survives restarts
- Human-readable and auditable
- Fits the "everything is Markdown" philosophy

---

## 6. AGENTS.md as Installer Template

The installer generates `AGENTS.md` from a template. It is the **law** for all agents — no exceptions.

### Mandatory Sections

| Section | Content |
|---------|---------|
| Mandatory Rules | Tool-tuple table (read/write/edit vs shell), Python over Bash |
| Red Lines | What agents must never do without explicit confirmation |
| Session Startup | What to read at the start of every session |
| Memory Workflow | When and how to use memory_search / memory_get |
| Communication Format | How to report status, blockers, errors |
| Heartbeat | Frequency and conditions |

### Customization

The installer fills in agent-specific details:
- Workspace paths
- Allowed tool patterns
- Agent-specific Red Lines (e.g., "no Git operations" for buero_AGENT)

### Shared via Symlink

All agents share the same `AGENTS.md` via symlink from their workspace.
If an agent needs extensions (additional rules), it gets its own `AGENTS.md` that imports the shared one via a reference comment at the top.

---

## 7. Channel Trust

| Channel | Trust | Notes |
|---------|-------|-------|
| Telegram DM / Group Topics | ✅ High | Platform-verified sender IDs |
| Email (read) | ⚠️ Low | Passive only — summarize, never act |
| Email (instructions) | ❌ Not trusted | See `SECURITY-ARCHITECTURE.md Layer 5` |
| Webhooks | Depends | Requires authentication token |

> **Rule:** E-mail content may be read and summarized. It may never directly trigger actions.
> Every action derived from email content must be confirmed by HUMAN via Telegram.

---

## 8. Installer Wizard: Agent Setup

```
🤖 Which agents should be installed?

  [✅] main          — Required. Botmaster and security auditor.
  [✅] coding_AGENT    — Code, website, Git.
  [ ] buero_AGENT     — Email, documents. (requires email credentials)
  [ ] formular_AGENT  — Form processing. (requires email + webhook config)

For each selected agent:
  → Name and emoji
  → Model tier (Budget / Standard / Power)
  → Allowlist tier (Restricted / Standard / Elevated)
  → Private skills to activate
  → Channel binding (Telegram topic ID)
```

### What the Installer Generates

For each agent:
- `workspace-<agent>/` directory with full structure
- `SOUL.md` from template (user fills name, role, character)
- `IDENTITY.md` stub
- `MEMORY.md` minimal template
- `memory/` directory with today's log + topics/ + docs/
- `tasks/` directory
- Symlinks: `skills/`, `AGENTS.md`, `USER.md`, `HEARTBEAT.md`
- `skills-private/` with selected skills deployed
- Allowlist section in `exec-approvals.json`
- Channel binding in `openclaw.json`

---

## Reference Implementation

This setup is live and tested:

```
~/.openclaw/
  workspace/        ← main (AGENT)
  workspace-coding/ ← coding_AGENT
  workspace-buero/  ← buero_AGENT (planned)
  workspace-formular/ ← formular_AGENT (planned)
```

See `~/.openclaw/workspace/AGENTS.md` for the shared AGENTS.md template.
See `~/.openclaw/scripts/restore_exec_approvals.py` for the allowlist reference.
