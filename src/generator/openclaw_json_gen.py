"""
openclaw_json_gen.py — Generate openclaw.json from WizardState.
Uses ${LLM_*} env var references — no hardcoded model names.
"""
import json
from pathlib import Path
from wizard.state import WizardState


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
