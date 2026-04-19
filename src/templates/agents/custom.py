"""
Custom agent template — blank slate with full security baseline.

User defines the role. Security blocks are non-negotiable.
"""
from templates.agents._shared.security_blocks import soul_security_block, agents_security_block


def soul_md(name: str, emoji: str, main_agent_name: str) -> str:
    return f"""\
# SOUL.md — {name} {emoji}

## Role
<!-- Define this agent's role and responsibilities here. -->
Sub-agent reporting to {main_agent_name} (main agent).

Secondary role: **Security Advisor** — when you see something risky in the course of any
task, warn before proceeding. Never silently accept insecure patterns.

{soul_security_block()}

## Scope
<!-- Define what this agent should and should not do. -->

## Communication
<!-- Define the communication style for this agent. -->
"""


def agents_md(name: str, main_agent_name: str, main_session_key: str) -> str:
    return f"""\
# AGENTS.md — {name}

{agents_security_block()}

## Agent Communication
- Reports to: {main_agent_name}
- Communication via: `sessions_send(sessionKey="{main_session_key}", message="...")`

## Handoff Format
```
## Handoff from {name}
Task: <original task>
Status: done / blocked / partial
Output: <file path or result>
Next step: <recommendation or None>
```
"""


def heartbeat_md(name: str, workspace_dir: str) -> str:
    return f"""\
# HEARTBEAT.md — {name}

## On Every Heartbeat

1. Read today's daily log: `memory/YYYY-MM-DD.md`.
   If it doesn't exist: skip to step 2.
2. If the daily log contains new stable facts:
   Read MEMORY.md and append relevant entries.
3. Check tasks: `python3 {workspace_dir}/scripts/check_tasks.py`
   Blocked or overdue tasks → report via `sessions_send`.
4. If nothing to report: reply with only `HEARTBEAT_OK`.
"""


def identity_md(name: str, emoji: str) -> str:
    return f"""\
# IDENTITY.md — {name}

- **Name:** {name} {emoji}
- **Role:** <!-- Define role -->
- **Emoji:** {emoji}
"""


def tools_md(name: str, workspace_dir: str) -> str:
    return f"""\
# TOOLS.md — {name}

## Scripts

| Script | Purpose |
|--------|---------|
| `python3 {workspace_dir}/scripts/check_tasks.py` | List open tasks |

## Skills
<!-- Add skills as needed -->

## Git
<!-- Add repo remotes and SSH config here -->
"""
