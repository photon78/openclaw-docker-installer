# skills/ — Shared Skills

This directory contains skills available to **all agents**.

The installer creates a symlink in each agent workspace:
```
~/.openclaw/workspace-<agent>/skills -> ~/.openclaw/workspace/skills/
```

## Skills installed here by default
| Skill | Description |
|-------|-------------|
| `web-search/` | DuckDuckGo search via ddgs |
| `docs-summarize/` | Fetch + summarize documentation URLs |

## Adding a shared skill
Place it in this directory. All agents see it immediately via the symlink.
