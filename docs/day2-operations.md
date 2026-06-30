# Day 2 Operations

> This guide is for power users who want to adopt the full hardening setup
> (SCRIPT-META, allowlist sync, custom update flow). For standard users,
> your agent handles updates and backups — just ask it.

## Standard Update Flow (all users)

1. **Backup:** `openclaw backup create --verify`
2. **Update:** `openclaw update --yes`
3. **Healthcheck (only if issues):** `openclaw doctor`

Your agent monitors new versions on every heartbeat. It waits **4 days** after a release before notifying you — allowing time for critical bugs to surface in the community. After 4 days without major incidents, it notifies you that the update appears stable.

## Power User: Extended Update Flow

If you have adopted SCRIPT-META headers and the allowlist sync setup, an update
may require additional steps to keep your config consistent:

1. `openclaw backup create --verify`
2. `openclaw update --yes`
3. `python3 workspace/scripts/shared/sync_allowlist.py` — verify 0 gaps
4. `openclaw doctor`

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
