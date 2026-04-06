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
                "workspace": str(state.workspace_dir),
                "model": {
                    "primary": "${LLM_STANDARD}",
                    "fallbacks": ["${LLM_POWER}"],
                },
                "models": {
                    "budget": "${LLM_BUDGET}",
                    "standard": "${LLM_STANDARD}",
                    "power": "${LLM_POWER}",
                    "media": "${LLM_MEDIA}",
                },
                "heartbeat": {
                    "every": "30m",
                    "target": "last",
                },
            }
        },
        "gateway": {
            "bind": "loopback",
            "port": 18789,
            "reload": {
                "mode": "hybrid",
            },
        },
        "session": {
            "dmScope": "per-channel-peer",
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
