# Day 2 Operations

> This guide is for power users who want to adopt the full hardening setup
> (SCRIPT-META, allowlist sync, custom update flow). For standard users,
> your agent handles updates and backups — just ask it.

## Update Design Principles

- **Never autonomous.** The agent never runs `openclaw update` on its own.
- **4-day wait.** New releases are monitored but not acted on until ≥ 4 days old.
- **Dedicated daily cron.** Update checks run once daily at 08:00 via the
  `Daily OpenClaw Update Check` cron — **not** in the heartbeat.
- **Explicit command required.** Say “run the update” in a normal session.

## How the Daily Update Check Works

1. At 08:00 the `Daily OpenClaw Update Check` cron runs an isolated agent session.
2. It calls `openclaw update status --json` and `npm view openclaw time --json`.
3. If release < 4 days old: logs internally, stays silent.
4. If release ≥ 4 days old: fetches open GitHub issues tagged `bug/crash/regression`
   and sends you a summary (version, age, open issues).
5. You decide when to update — the agent never updates automatically.

Set up this cron after installation — see `tasks/cron-setup.md` in your workspace.

## Standard Update Flow (all users)

1. **Backup:** `openclaw backup create --verify`
2. **Update:** `openclaw update --yes`
3. **Gateway restart:** `openclaw gateway restart`
4. **Healthcheck (only if issues):** `openclaw doctor`

## Power User: Extended Update Flow

If you have adopted SCRIPT-META headers and the allowlist sync setup:

1. `openclaw backup create --verify`
2. `openclaw update --yes`
3. `python3 workspace/scripts/shared/sync_allowlist.py` — verify 0 gaps
4. `openclaw doctor` (only if issues)
5. `openclaw gateway restart`

## Backup

`openclaw backup create` archives:
- `~/.openclaw/` (state, config, credentials)
- All configured workspace directories
- Agent auth profiles

Output: timestamped `.tar.gz` in current directory.

**Verify:** `openclaw backup create --verify` or `openclaw backup verify <archive>`

**Config only:** `openclaw backup create --only-config`

## Recovery

If an update breaks something:
```bash
openclaw update repair
```

If Gateway won't start:
```bash
openclaw gateway restart
openclaw doctor
```

## Channels

- `stable` (default) — production releases
- `beta` — preview features, may break
- `dev` — latest, requires git checkout

Switch: `openclaw update --channel beta`
