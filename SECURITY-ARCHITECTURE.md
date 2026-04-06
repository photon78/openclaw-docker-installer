# Security Architecture — OpenClaw Installer

## Design Philosophy

**An LLM agent with shell access is a controlled weapon.** The issue isn't capability — it's uncontrolled capability. This system grants the agent exactly as much power as it needs, not a byte more.

We harbor no illusions: An agent with an allowlist is **not** unbreakable. But it is *observable*, *restricted*, and *auditable*. That's the difference between an open barn door and a door with a lock, camera, and alarm.

---

## Layer 1: Exec-Approvals (Allowlist System)

### Architecture

```
exec-approvals.json
├── defaults          ← applies to ALL sessions (including Crons, isolated)
├── agents
│   ├── main          ← Botmaster, broadest rights
│   ├── coding_bot    ← Dev tools, Git, Node
│   ├── buero_bot     ← only specific script paths
│   └── formular_bot  ← only specific script paths
```

### Principle: Deny-by-Default, Allowlist-Only

```json
{
  "security": "allowlist",
  "ask": "on-miss",
  "askFallback": "deny"
}
```

- **`security: allowlist`** — only explicitly listed commands allowed. `security: full` is never offered.
- **`ask: on-miss`** — anything not on the list prompts the user
- **`askFallback: deny`** — if no user responds: deny

### Permission Tiers

| Tier | Agents | Bare Interpreter | What's Allowed |
|------|--------|-----------------|----------------|
| **Restricted** | buero_bot, formular_bot | ❌ No python3, no bash | Only named script paths + read tools (ls, cat, grep, etc.) |
| **Standard** | coding_bot | ✅ python3 + bash | Dev tools, Git, Node, SSH, but no systemctl, no openclaw CLI |
| **Elevated** | main | ✅ python3 + bash | System tools, gateway management, but no rm, no pip3, no root |
| **Cron/Isolated** | defaults | ❌ No bash | python3 + read tools + health/digest scripts |

### Why No Bare Interpreter for Restricted Agents?

`/usr/bin/python3` in the allowlist means: the agent can execute **any** Python — `python3 -c "import os; os.system('rm -rf /')"` matches. For agents that should only execute skills, we list the specific script paths instead:

```json
// ❌ Too broad
{"pattern": "/usr/bin/python3"}

// ✅ Precise
{"pattern": "/home/user/.openclaw/workspace/skills/web-search/search.py"}
{"pattern": "/home/user/.openclaw/workspace/skills/email/send_mail.py"}
```

**Known Limitation:** Agents with bare python3 or bash can bypass these restrictions. This is a conscious compromise — dev agents *need* general interpreter access. Security here lies in observability (integrity audit), not restriction.

---

## Layer 2: Restore Mechanism

### The Problem

`openclaw gateway install` and `openclaw update` can overwrite `exec-approvals.json` with defaults. All manual adjustments would be lost.

### The Solution

```
systemd ExecStartPost → restore_exec_approvals.py
```

After each gateway start:
1. Wait 2 seconds (socket must be ready)
2. Write complete allowlist from the Python script
3. Log entry in `logs/restore-exec-approvals.log`

**The allowlist lives in code, not in the file.** `exec-approvals.json` is generated, not manually edited. Changes belong in the restore script.

### Installer Context

The wizard generates `restore_exec_approvals.py` based on:
- Which agents were configured
- Which permission tier was chosen per agent
- Which skills are installed (→ script paths)

---

## Layer 3: Integrity Monitoring

### `audit_integrity.py` — Standalone Audit Script

```bash
python3 audit_integrity.py              # Full report
python3 audit_integrity.py --silent     # Only on changes
python3 audit_integrity.py --json       # Machine-readable
python3 audit_integrity.py --reset      # Reset baselines
```

**What is checked:**

| Check | Method | Detects |
|-------|--------|---------|
| exec-approvals.json | SHA256 hash vs. baseline | Manipulation, unexpected updates |
| scripts/ inventory | File list + individual hashes | New scripts, deleted scripts, modified scripts |

**Important:** Baselines are **not** automatically overwritten when changes are detected. Requires conscious `--reset` after legitimate changes.

**Exit codes:** 0 = OK, 1 = changes, 2 = critical (files missing)

### Integration in Health Check

```
health_check.py
├── Disk, Gateway, Backup          ← System
├── Errors, Packages, Logins       ← Security
├── API keys in service file       ← Secret leak detection
└── audit_integrity.py --silent    ← Integrity
```

Runs daily at 07:45 via crontab. On changes: alert via Telegram.

---

## Layer 4: Secret Management

### Principle: Secrets Only in `.env`, Nowhere Else

```
~/.openclaw/.env          ← only location for secrets
├── ANTHROPIC_API_KEY
├── MISTRAL_API_KEY
├── EMAIL_PASSWD
├── TELEGRAM_BOT_TOKEN
└── LLM_BUDGET / LLM_STANDARD / LLM_POWER / LLM_MEDIA
```

- **systemd:** `EnvironmentFile=%h/.openclaw/.env` — never `Environment=KEY=...` in the service file
- **Health check:** verifies on each run whether API keys are in the service file
- **Workspace files:** never commit secrets. `.gitignore` includes `.env`

### Docker Context

```yaml
volumes:
  - ${OPENCLAW_DATA}/.env:/data/.env:ro    # ← read-only!
```

`.env` is mounted read-only. The agent can read secrets (needs them for API calls) but cannot overwrite them.

---

## Layer 5: Process Isolation (Docker)

### Bind Mounts: Read-Write vs. Read-Only

```yaml
volumes:
  # Read-Write (agent needs write access)
  - ${OPENCLAW_DATA}/workspace:/data/workspace
  - ${OPENCLAW_DATA}/logs:/data/logs
  - ${OPENCLAW_DATA}/memory:/data/memory

  # Read-Only (agent must not modify)
  - ${OPENCLAW_DATA}/scripts:/data/scripts:ro
  - ${OPENCLAW_DATA}/.env:/data/.env:ro
  - ${OPENCLAW_DATA}/openclaw.json:/data/openclaw.json:ro
```

**Why scripts read-only?** If the agent could create a new script and it were in the allowlist, the allowlist would be worthless. Scripts are only modified by the installer or the user — never by the agent at runtime.

### Native Installation (Linux)

No container = no process isolation. Security relies entirely on:
- Allowlist (what can be executed)
- User separation (agent runs as a dedicated user, not as root)
- Integrity monitoring (what has changed)
- Approval mechanism (user confirms unknown commands)

---

## Threat Model — Honest Assessment

### What the System Prevents

✅ Agent executes arbitrary destructive commands (`rm`, `dd`)
✅ Agent installs packages (`pip3`, `apt`)
✅ Agent escalates to root
✅ Agent modifies its own allowlist (Docker: scripts read-only)
✅ Unnoticed allowlist manipulation (integrity audit)
✅ Secret leaks into service file (health check)
✅ Allowlist loss after gateway update (restore script)

### What the System Does NOT Prevent

⚠️ **Agent with bash/python3 can generate and execute code** — the allowlist only protects the interpreter path, not the content.

⚠️ **Agent can read all files the user has access to** — `read` tool is always available, regardless of the allowlist.

⚠️ **Social engineering** — the agent could trick the user into approving harmful commands.

⚠️ **Data exfiltration via API calls** — the agent has API keys and can send data to LLM providers.

### Conscious Compromises

| Compromise | Why |
|-----------|-----|
| bash/python3 for dev agents | Dev work without an interpreter is impractical |
| `read` tool always available | Agent needs file access for its core function |
| Approval UI instead of automatic blocking | Human-in-the-loop > automatic decisions |
| Secrets in `.env` readable by agent | Agent needs API keys for functionality |

---

## Layer 5: Input Channel Trust & Sender Verification

### Problem: Not All Input Channels Are Equal

An LLM agent can receive instructions from multiple sources:
- **Telegram DM / Group Topics** — sender ID is verified by Telegram's servers. Hard to spoof.
- **E-Mail** — sender address is trivially spoofable. SMTP `From:` has no cryptographic guarantee without DKIM + strict policy.
- **Webhooks / API** — depends on authentication mechanism.

### Current State (this installation)

| Channel | Trust Level | Mechanism |
|---------|-------------|----------|
| Telegram | ✅ High | `allowFrom: [user_id]` — Telegram ID is platform-verified |
| E-Mail (read) | ⚠️ Low | No sender whitelist, no shared secret — passive only |
| E-Mail (instructions) | ❌ Not implemented | Should not be trusted without verification |

### Threat: Prompt Injection via E-Mail

If an agent polls a mailbox and acts on email content:
1. Attacker sends email to agent's address with crafted instructions
2. Agent reads email, interprets as legitimate command
3. Agent executes — potentially destructive actions if allowlist is too broad

**This attack requires no hacking — just sending an email.**

### Required Safeguards for E-Mail Instructions

Before an agent may act on instructions received by e-mail:

1. **Sender Whitelist** — only pre-configured addresses may issue commands
2. **Shared Secret** — a secret keyword/passphrase in the email body that the agent verifies before acting
3. **DKIM Verification (recommended)** — verify the cryptographic signature of the sending domain
4. **Scope Limitation** — e-mail instructions may only trigger predefined actions (no free-form exec)
5. **Audit Trail** — every e-mail instruction logged with sender, subject, action taken

### Installer Requirements

- Wizard must ask: "Will this agent act on e-mail instructions?"
- If yes: require sender whitelist + shared secret before generating email skill config
- Document clearly: E-mail reading (passive) ≠ E-mail instructions (active, needs verification)
- `check_mail.py` skill: reading is safe, acting on content requires the safeguards above

### Conscious Compromise

| Compromise | Why |
|-----------|-----|
| No DKIM verification by default | Complex to implement, requires DNS access |
| Shared secret in plaintext email | Weaker than DKIM but practical for most users |

---

## LLM Shell Reflex Risk

### The Problem

LLMs are trained on billions of shell examples. `find`, `grep`, `ls`, `curl` are deeply ingrained patterns — deeper than any instruction in `AGENTS.md` or `SOUL.md`. When an agent "quickly looks something up", the trained reflex fires before the security rule kicks in.

**This is not an OpenClaw-specific problem.** It affects every LLM system with shell access.

### Why This Matters for Installer Users

- Harmless reflexes (`find`, `ls`) and dangerous ones (`rm`, `curl | bash`, `chmod 777`) come from the **same pattern family**
- Users often don't read approval dialogs carefully — they approve reflexively
- A poorly configured allowlist turns the approval dialog into **security theater**

The agent is not malicious. It's doing what it was trained to do. The system must compensate for this.

### Mitigations (Implemented / To Verify)

| Measure | Where | Status |
|---------|-------|--------|
| Tight allowlist — only what's actually needed | `exec-approvals.json` | ✅ Layer 1 |
| Explicit shell-equivalent prohibition in `AGENTS.md` | `read` instead of `cat`, `edit` instead of `sed` | ✅ Generated by installer |
| `SOUL.md`: Security as core identity, not just a rule list | Agent persona | ✅ Template includes this |
| User education in setup wizard: "Read approval dialogs" | Wizard completion screen | ⬜ To implement |

### Recommended Wizard Warning (Completion Screen)

```
⚠️  A note on approval dialogs:

Your agent has shell access. When it wants to run a command
that's not on its allowlist, you'll see an approval dialog
showing the exact command.

Please read it. The agent means well — but LLMs are trained
on billions of shell examples and occasionally reach for
familiar tools out of habit. The allowlist catches most of
this. The approval dialog is your second line of defense.

If a command looks wrong: deny it, then tell the agent which
tool to use instead.
```

### The Deeper Fix

Rules in `AGENTS.md` help, but they fight against training. The more reliable approach:

1. **Allowlist makes the reflex fail safely** — the command gets blocked or requires approval
2. **Identity-level security in `SOUL.md`** — "I reach for `read`/`edit` tools, not shell commands" becomes part of who the agent *is*, not just what it's told
3. **Tight allowlist forces the right habits** — if `cat` isn't on the allowlist, the agent learns to use `read`

---

## Installer Wizard: Security Setup

```
🔒 Choose security profile:

  [Strict]    Recommended. Allowlist for all agents.
              Only named scripts, no bare interpreter
              for non-dev agents.

  [Standard]  Allowlist with bare python3/bash for all agents.
              More flexibility, less isolation.

  [Custom]    Configure per agent individually.
              For experienced users.

  ⚠️ "Full Access" is intentionally not offered.
```

---

## Installer Checklist

```
[ ] exec-approvals.json generated (per agent, per tier)
[ ] restore_exec_approvals.py generated (from wizard config)
[ ] systemd ExecStartPost / Docker ENTRYPOINT configured
[ ] audit_integrity.py installed + baselines set
[ ] health_check.py with audit integration
[ ] .env created (secrets, LLM tiers)
[ ] .env mounted read-only (Docker)
[ ] scripts/ mounted read-only (Docker)
[ ] Service file without API keys
[ ] sudoers entry (only specific commands via NOPASSWD)
[ ] Approval buttons active (Telegram/Discord)
```
