# Design Decisions — openclaw-docker-installer

This document records key design decisions — why things are the way they are.
Not for the user. For contributors, when they ask in six months: "Why did we do it this way?"

---

## DD-000: Core Principles

Three things that shaped every decision in this project.

### 1. The Goal: A Secure, Clean, Docker-based OpenClaw Instance

Not "installable". Not "configurable". **Secure by default.** That means:
- Allowlist active from day one — no `security: full`
- Restore script in place — allowlist survives gateway updates
- Integrity monitoring — changes are detected
- Backup configured — data survives hardware failure
- Secrets in `.env` only — never in service files or committed code
- Scripts mounted read-only in Docker — agent cannot modify its own tools

**Idempotency:** Running the installer twice must not break a working system.
Re-run = update, not chaos.

**Transparency:** The wizard explains what it does. Users understand what gets deployed.
No magic. Everything is plain text, auditable, version-controlled.

### 2. Everything User-Specific Goes Through Variables

No hardcoded usernames. No hardcoded paths. No hardcoded tokens.
Every value that is installation-specific comes from the wizard and flows through
a template variable — even if it feels obvious or unlikely to change.

**Why:** If something is missed during installation, it can be fixed later without
reinstalling from scratch. Variables make the system auditable, updatable, and portable.

```python
# ❌ Wrong
path = "/home/user/.openclaw/scripts/health_check.py"

# ✅ Right
path = str(Path.home() / ".openclaw" / "scripts" / "health_check.py")
```

### 3. This Installer Packages a Real System

This project grew out of a working setup: a Raspberry Pi 5 running OpenClaw
with multi-agent configuration, allowlists, integrity monitoring, and daily backups —
in production since early 2026.

That's the context for many decisions here. We didn't design this in the abstract —
we extracted it from something real. If you're wondering why something works a certain way,
that's usually the reason.

---

## Design Philosophy (Landing Page — First Sentence)

> *An LLM agent with shell access is a controlled weapon. The issue isn't the capability — it's uncontrolled capability. This system gives the agent exactly as much power as it needs, and not a byte more.*

— HUMAN, 2026-04-05

---

## DD-001: Allowlist — "You can do anything, but not all at once"

**Decision:** The installer configures `security: allowlist` with explicitly approved binaries. No `security: full`.

**Core Problem:**
Every approved binary runs without approval. But `ls | grep foo` = `bash -c "ls | grep foo"` = Bash compound = Bash must be on the allowlist. If you want pipes, you must write a Python script that encapsulates the pipe internally — then only the script path is on the allowlist.

**Consequence for the User:**
> *"You can do anything, but not all at once."*

**Why This Is a Feature, Not a Bug:**
- Forces logic to be encapsulated in scripts rather than inline chains
- Scripts are testable, versionable, traceable
- Inline pipe chains are not
- The user always sees exactly what is approved

**What the Installer Does:**
- Explains this behavior explicitly in the "Security & Allowlist" wizard step
- Shows which binaries are pre-approved and why
- Warns if someone tries to enable `bash` with a wildcard or `security: full`

**Source:** HUMAN + coding_AGENT, 2026-04-05

---

## DD-002: Security by Default, Not Security by Choice

**Decision:** The installer does not offer an "I know what I'm doing, open everything" option in the standard installation.

**Reasoning:**
An inexperienced user in a chemical plant control room would click "open everything" because it's more convenient. This scenario is not theoretical.

**What the Installer Does:**
- Restrictive defaults, no wildcard option in the MVP
- Those who want more must manually edit `exec-approvals.json` — a conscious decision, not a click

**Source:** HUMAN + coding_AGENT, 2026-04-05

---

## DD-003: TUI Instead of GUI

**Decision:** Terminal UI (`rich` + `questionary`), no GUI framework.

**Reasoning:**
- Runs on headless Raspberry Pi without a display
- No PyInstaller overhead from Qt/Tk
- More robust cross-platform
- Core logic remains UI-independent — TUI is just a layer on top

**Source:** HUMAN + coding_AGENT, 2026-04-05

---

## DD-004: Core API Layer Is UI-Independent

**Decision:** `checks/`, `docker/`, `bootstrap/`, `security/` have no UI dependencies. The TUI calls the core, not the other way around.

**Reasoning:**
- Enables future web UI, CLI-only mode, or other frontends
- Core is testable without UI
- Headless operation (e.g., CI/CD) possible

**Source:** HUMAN (voice message), 2026-04-05

---

## DD-005: Extended Memory — Opt-in, Not Default

**Decision:** The three-layer memory system always runs. Semantic vector search (Mistral embeddings) is opt-in.

**Standard (No Mistral Key):**
- SQLite + FTS5 full-text search
- Works, finds exact terms
- Zero additional costs

**Opt-in "Extended Memory" (With Mistral Key):**
- SQLite + FTS5 + Mistral `mistral-embed` (1024 dims) + sqlite-vec
- Hybrid search: BM25 (0.3) + vector (0.7)
- Finds semantically related terms — "accommodation" matches "hotel room"
- Costs Mistral API calls for each embedding index build

**Wizard Text:**
> *"Without Mistral: Full-text search — finds exactly what you enter.
> With Mistral: Semantic search — also finds related terms.
> Recommendation: Enter a Mistral key if available. Can be activated later."*

**Source:** HUMAN, 2026-04-05

---

## Decision 6: Skill-Scoping via Shared Symlink + Agent-Private Directory

**Problem:** All agents sharing one global skills symlink get access to all skills — including sensitive ones (email, git). This violates least-privilege.

**Rejected Alternative:** Copy skills per agent
- High maintenance burden
- Skills diverge over time
- Error-prone on updates

**Chosen Solution:** Two-tier skill structure per agent workspace:
```
workspace-<agent>/
  skills -> ../workspace/skills/    ← Symlink to shared skills (read-only, all agents)
  skills-private/                   ← Agent-specific skills (only this agent)
    email/   ← only buero_AGENT
    git-workflows/  ← only coding_AGENT
```

**Rules:**
- Agent reads skills from both `skills/` and `skills-private/`
- New shared skills → `workspace/skills/` (one place, all agents benefit)
- New agent-specific skills → `skills-private/` of that agent's workspace
- Installer Wizard: asks per agent which private skills to activate

**Skill Assignment (current):**
| Skill | Shared | buero_AGENT | coding_AGENT | formular_AGENT | main |
|-------|--------|-----------|------------|--------------|------|
| web-search | ✅ | — | — | — | — |
| docs-summarize | ✅ | — | — | — | — |
| email | — | ✅ private | — | — | — |
| git-workflows | — | — | ✅ private | — | — |
| voice-agent | — | — | — | — | main only |

**Source:** HUMAN + AGENT, 2026-04-06

---

## Decision 7: Backup-System als Core-Feature (nicht optional)

**Rationale:** Ein unkonfiguriertes System ohne Backup ist kein produktionsreifes System. Der Installer muss den User aktiv durch das Backup-Setup führen — nicht als optionales Extra.

**Was der Installer einrichtet:**
- `daily_backup.py` aus Templates deployen (konfiguriert mit User-definiertem Mount-Pfad)
- Crontab-Eintrag automatisch anlegen (Standard: 04:10 täglich)
- Backup-Ziel: SD-Karte oder USB (Wizard fragt: "Wo ist dein Backup-Medium?")
- `restore.md` bei Installation generieren (mit konkreten Pfaden, Token-Placeholder, API-Key-Hinweise)

**Backup-Inhalt:**

| Was | Wie |
|-----|-----|
| Workspaces | rsync, Diff Mo–Sa, Voll So |
| openclaw.json | copy |
| Scripts (`*.py`) | copy |
| systemd Drop-ins | copy |
| Memory SQLite | copy |
| exec-approvals.json | copy, Token=REDACTED |

**Bewusst NICHT gesichert:**
- API-Keys / `.env` — zu sensibel
- Session-JSONL — zu gross, nicht kritisch
- node_modules / dist / .astro — regenerierbar
- Socket-Token — bleibt nur im Restore-Script

**Referenz-Implementierung:** `~/.openclaw/scripts/daily_backup.py` (live, getestet 2026-04-06)  
**Referenz-Restore:** `~/.openclaw/workspace/restore.md`

**Source:** HUMAN + AGENT, 2026-04-06

---

## DD-008: Skills and Scripts as Versioned Templates in the Installer Repo

**Decision:** Skills (`web-search`, `docs-summarize`, `email`) and scripts (`health_check.py`, `daily_backup.py`, `restore_exec_approvals.py`, etc.) are versioned directly in the installer repository as templates.

**What this means:**
- Skills and scripts live in `installer-repo/templates/skills/` and `installer-repo/templates/scripts/`
- Templates contain placeholder variables (e.g., `{{ home_dir }}`, `{{ socket_token }}`)
- At install time: Wizard fills variables → scripts are deployed to `~/.openclaw/scripts/`
- Updates: `git pull` on the installer repo + re-run deploy step

**Benefits:**
- **Offsite backup** — installer repo IS the source of truth for all scripts
- **Version control** — every script change is tracked, diffable, revertable
- **One source of truth** — no divergence between installations
- **Updates via pull** — `openclaw-installer update` = git pull + re-deploy templates

**Rejected alternative:** Download scripts from a CDN or separate repo at install time
- Network dependency at install time
- No integrity guarantee without checksums
- More moving parts

**Source:** HUMAN + AGENT, 2026-04-06
