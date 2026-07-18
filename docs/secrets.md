# Secret Management

This installer stores all secrets in a single `.env` file next to `openclaw.json`.
The generated `openclaw.json` never contains plaintext API keys or bot tokens.
Instead, it uses **SecretRefs** that resolve values from the env-provider at runtime.

## What is a SecretRef?

A SecretRef is a value in `openclaw.json` that tells OpenClaw to look up the actual
secret from an external provider (in our case: environment variables).

This installer uses the shorthand syntax:

```json5
"token": "${OPENCLAW_GATEWAY_AUTH_TOKEN}"
```

or, for plugin API keys:

```json5
"apiKey": "$ANTHROPIC_API_KEY"
```

You can also use the long form if you edit the config manually:

```json5
"token": {
  "source": "env",
  "provider": "default",
  "id": "OPENCLAW_GATEWAY_AUTH_TOKEN"
}
```

## Generated `.env`

The installer creates `~/.openclaw/.env` with `chmod 600` (owner read/write only).
Example:

```bash
USER_NAME=alice
OPENCLAW_GATEWAY_AUTH_TOKEN=a3b9c2d4...
ANTHROPIC_API_KEY=sk-ant-...
MISTRAL_API_KEY=...
AKI_API_KEY=...
BRAVE_WEB_SEARCH_API_KEY=...
TELEGRAM_BOT_TOKEN_DEFAULT=123456:ABC...
LLM_BUDGET=mistral/mistral-large-latest
LLM_STANDARD=anthropic/claude-sonnet-4-6
LLM_POWER=anthropic/claude-opus-4-6
LLM_MEDIA=mistral/mistral-large-latest
BACKUP_MOUNT=/mnt/backup
```

Multi-agent Telegram tokens are included as commented placeholders:

```bash
# TELEGRAM_BOT_TOKEN_VALERE=<Valère_content_agent_(optional)>
# TELEGRAM_BOT_TOKEN_SENTINEL=<Sentinel_security_agent_(optional)>
# TELEGRAM_BOT_TOKEN_CODING=<Coding_agent_(optional)>
# TELEGRAM_BOT_TOKEN_SIONIS=<Sionis_finance_agent_(optional)>
```

Uncomment and fill the ones you need, then run:

```bash
openclaw secrets reload
```

## Why not plain text in `openclaw.json`?

1. **Security**: `openclaw.json` may be copied, backed up, or committed by mistake.
   Secrets in `.env` are never logged by OpenClaw and are mounted read-only into the container.
2. **Rotation**: Change a secret by editing `.env` only; no JSON editing required.
3. **doctor compliance**: OpenClaw 2026.7.1+ flags plaintext secrets in config files.
   SecretRefs keep `openclaw doctor --lint` clean.

## How `openclaw.json` references the env provider

The installer adds this block to `openclaw.json`:

```json5
"secrets": {
  "providers": {
    "default": { "source": "env" }
  },
  "defaults": {
    "env": "default"
  }
}
```

This registers the `.env` file as the default secret provider and enables
shorthand refs like `$VAR_NAME` or `${VAR_NAME}` anywhere in the config.

## Troubleshooting

### `openclaw doctor --lint` reports a plaintext secret

1. Move the value to `~/.openclaw/.env` as `VAR_NAME=value`.
2. Replace the plaintext value in `openclaw.json` with `$VAR_NAME` or `${VAR_NAME}`.
3. Run:

   ```bash
   openclaw secrets reload
   openclaw doctor --lint
   ```

### `openclaw secrets audit --check` reports missing secrets

Make sure the variable is exported in `.env` and the container is using it:

```bash
# On the Docker host
docker compose exec openclaw-gateway env | grep -E 'API_KEY|TOKEN'
```

If a variable is missing, add it to `.env` and restart:

```bash
docker compose down
docker compose up -d
```

### Gateway auth fails after reinstall

`OPENCLAW_GATEWAY_AUTH_TOKEN` is generated randomly on each fresh install.
If you reinstall, update any external scripts or clients that call the gateway
API with the new token from `~/.openclaw/.env`.

### I accidentally committed `.env`

1. Rotate every secret that was in the file.
2. Add `.env` to `.gitignore` if it isn't already.
3. Run `chmod 600 ~/.openclaw/.env`.
4. Consider the committed token/key compromised and revoke it in the provider console.
