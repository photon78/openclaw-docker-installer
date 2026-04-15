"""
openclaw_json_gen.py — Generate openclaw.json from WizardState.
Uses ${LLM_*} env var references — no hardcoded model names.
"""
import json
from pathlib import Path
from wizard.state import WizardState


def _memory_search_config(state: WizardState) -> dict:
    """Return memorySearch config with an explicit provider.

    In Docker, API keys live in .env and are not visible to OpenClaw's
    auto-detection logic at boot time. We must declare the provider explicitly
    so memory_search works out of the box.

    Priority: mistral > openai > anthropic (last resort: disabled).
    """
    if state.mistral_api_key:
        return {
            "provider": "mistral",
            "model": "mistral-embed",
        }
    if state.anthropic_api_key:
        # Anthropic does not offer embeddings — fall through to disabled
        pass
    # No supported embedding provider found — disable gracefully
    return {"enabled": False}


def generate(state: WizardState) -> dict:
    """Return openclaw.json content as dict."""
    config: dict = {
        "agents": {
            "defaults": {
                # Container-internal path — host path is bind-mounted here
                "workspace": "/home/node/.openclaw/workspace",
                # Model refs via env vars — change models by editing .env only
                "model": {
                    "primary": "${LLM_BUDGET}",
                    "fallbacks": ["${LLM_STANDARD}", "${LLM_POWER}"],
                },
                "heartbeat": {
                    "every": "30m",
                    "target": "last",
                    "model": "mistral/mistral-large-latest",
                    "isolatedSession": True,
                    "lightContext": True,
                },
                # Bootstrap: how much workspace context is injected per session
                "bootstrapMaxChars": 20000,
                "bootstrapTotalMaxChars": 100000,
                # Subagents: limit parallel runs, prevent chain-spawning
                "subagents": {
                    "maxConcurrent": 2,
                    "maxSpawnDepth": 1,
                },
                # Memory search: explicit provider so embedding works out of the box
                # Auto-detection fails in Docker when API keys are only in .env
                "memorySearch": _memory_search_config(state),
            },
        },
        "gateway": {
            "mode": "local",
            "bind": "lan",
            "port": 18789,
            "reload": {
                "mode": "hybrid",
            },
            "auth": {
                "rateLimit": {
                    "maxAttempts": 10,
                    "windowMs": 60000,
                    "lockoutMs": 300000,
                }
            },
            "controlUi": {
                "allowedOrigins": [
                    "http://localhost:18789",
                    "http://127.0.0.1:18789",
                ]
            },
        },
        "plugins": {
            # Explicit allow-list: only these plugins are loaded.
            # Channel plugin appended dynamically below based on wizard selection.
            "allow": ["mistral", "anthropic"],
            "entries": {
                # Mistral runs natively via plugin — NO custom models.providers block needed.
                # Adding a custom provider block causes 404 (OpenAI-compat fallback).
                "mistral": {"enabled": True},
                "anthropic": {"enabled": True},
            },
        },
        "session": {
            "dmScope": "per-channel-peer",
            "maintenance": {
                "mode": "warn",
                "pruneAfter": "30d",
                "maxEntries": 500,
                "rotateBytes": "10mb",
            },
        },
        "cron": {
            "enabled": True,
        },
    }

    # Channel defaults: security-hardened baseline for all channels
    channels: dict = {
        "defaults": {
            # Groups: allowlist-only, no open group access
            "groupPolicy": "allowlist",
            # Context: only inject context from allowlisted senders
            "contextVisibility": "allowlist",
            # Heartbeat: silent on healthy, alert on issues
            "heartbeat": {
                "showOk": False,
                "showAlerts": True,
                "useIndicator": True,
            },
        }
    }

    if state.channel == "telegram" and state.telegram_bot_token:
        channel_cfg: dict = {
            "enabled": True,
            "dmPolicy": "allowlist" if state.channel_allow_from else "pairing",
            # Prevent config modifications via Telegram (e.g. /config set, group ID migrations)
            "configWrites": False,
            # Groups: disabled by default — user can open specific groups later
            "groupPolicy": "disabled",
            # Reactions: only notify on bot's own messages
            "reactionNotifications": "own",
        }
        if state.channel_allow_from:
            channel_cfg["allowFrom"] = [int(uid) if uid.lstrip("-").isdigit()
                                         else uid
                                         for uid in state.channel_allow_from]
        channels["telegram"] = channel_cfg

    elif state.channel == "discord" and state.discord_bot_token:
        discord_cfg: dict = {
            "enabled": True,
            "dmPolicy": "allowlist" if state.channel_allow_from else "pairing",
            # Security: ignore bot messages, restrict dangerous actions
            "allowBots": False,
            "actions": {
                "reactions": True,
                "messages": True,
                "threads": True,
                "memberInfo": True,
                # Restricted by default — user enables manually if needed
                "moderation": False,
                "roles": False,
            },
            # Groups: disabled by default
            "groupPolicy": "disabled",
        }
        if state.channel_allow_from:
            discord_cfg["allowFrom"] = [int(uid) if uid.lstrip("-").isdigit()
                                         else uid
                                         for uid in state.channel_allow_from]
        channels["discord"] = discord_cfg

    elif state.channel == "signal" and state.signal_number:
        channels["signal"] = {
            "enabled": True,
            "dmPolicy": "pairing",
        }

    config["channels"] = channels

    # plugins.allow: dynamic based on selected channel
    channel_plugin = {"telegram": "telegram", "discord": "discord", "signal": "signal"}
    if state.channel in channel_plugin:
        config["plugins"]["allow"].append(channel_plugin[state.channel])  # type: ignore[union-attr]

    return config


def write(state: WizardState) -> Path:
    """Write openclaw.json to openclaw_dir. Returns path."""
    target = state.openclaw_dir / "openclaw.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(generate(state), indent=2) + "\n")
    return target
