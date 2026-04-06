# skills-private/ — Agent-Private Skills

This directory is a **template** for agent-specific skills.

Each agent gets its own `skills-private/` directory (no symlink — private per agent):
```
~/.openclaw/workspace-<agent>/skills-private/
```

## Skill assignment per agent
| Skill | Agent |
|-------|-------|
| `email/` | buero_AGENT only |
| `git-workflows/` | coding_AGENT only |
| `voice-agent/` | main only |

## Adding an agent-private skill
Place it in the agent's own `skills-private/` directory.
Other agents cannot see it.

## Installer Wizard
The wizard asks per agent: "Which private skills should be activated?"
It then deploys the selected skills to `skills-private/` of that agent's workspace.
