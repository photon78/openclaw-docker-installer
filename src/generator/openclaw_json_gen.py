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
                "model": {
                    "primary": state.llm_standard,
                    "fallbacks": [state.llm_power],
                },
                "models": {
                    state.llm_budget:   {"alias": "budget"},
                    state.llm_standard: {"alias": "standard"},
                    state.llm_power:    {"alias": "power"},
                    state.llm_media:    {"alias": "media"},
                },
                "heartbeat": {
                    "every": "30m",
                    "target": "last",
                },
                # Bootstrap: how much workspace context is injected per session
                "bootstrapMaxChars": 20000,
                "bootstrapTotalMaxChars": 100000,
                # Subagents: limit parallel runs
                "subagents": {
                    "maxConcurrent": 2,
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
            "controlUi": {
                "allowedOrigins": [
                    "http://localhost:18789",
                    "http://127.0.0.1:18789",
                ]
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

    # Channel config
    if state.channel == "telegram" and state.telegram_bot_token:
        channel_cfg: dict = {
            "enabled": True,
            "dmPolicy": "allowlist" if state.channel_allow_from else "pairing",
        }
        if state.channel_allow_from:
            channel_cfg["allowFrom"] = [int(uid) if uid.lstrip("-").isdigit()
                                         else uid
                                         for uid in state.channel_allow_from]
        config["channels"] = {"telegram": channel_cfg}

    elif state.channel == "discord":
        config["channels"] = {
            "discord": {
                "enabled": True,
                "dmPolicy": "pairing",
            }
        }

    elif state.channel == "signal":
        config["channels"] = {
            "signal": {
                "enabled": True,
                "dmPolicy": "pairing",
            }
        }

    return config


def write(state: WizardState) -> Path:
    """Write openclaw.json to openclaw_dir. Returns path."""
    target = state.openclaw_dir / "openclaw.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(generate(state), indent=2) + "\n")
    return target
