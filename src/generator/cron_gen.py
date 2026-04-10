"""
cron_gen.py — Generate cron job definitions for openclaw.json from WizardState.

Generates the two critical crons for v1.0:
  1. Daily Memory Digest  — runs memory_digest.py at 03:05 daily
  2. Gateway Health Check — runs every 2 hours, silent unless problem

All cron prompts use the budget LLM tier — cheap, fast, no reasoning needed.
Prompts follow AIM format: Actor → Input → Mission.

NOTE: Cron config is injected into openclaw.json under the "crons" key.
The main generator (generator.py) calls cron_gen.generate() and merges the result.
"""
from wizard.state import WizardState

# Container-internal paths
_OPENCLAW = "/home/node/.openclaw"
_SCRIPTS  = f"{_OPENCLAW}/scripts"


def _daily_digest_cron(state: WizardState) -> dict:
    """Daily Memory Digest — 03:05 every day.

    Runs memory_digest.py which writes digest-latest.md to all workspaces.
    Uses budget tier — pure Python script output, no LLM reasoning needed.
    Silent on success, reports only on error.
    """
    return {
        "name": "Daily Memory Digest",
        "schedule": {
            "kind": "cron",
            "expr": "5 3 * * *",
        },
        "payload": {
            "kind": "agentTurn",
            "model": state.llm_budget,
            "timeoutSeconds": 120,
            "message": (
                f"Actor: You are the Memory Digest Writer for an OpenClaw setup.\n"
                f"Input: Run this script: python3 {_SCRIPTS}/memory_digest.py\n"
                f"Mission: Print the full output of the script. "
                f"If the script exits with an error, report it clearly. "
                f"If it succeeds, output the result and nothing else. No commentary."
            ),
        },
        "sessionTarget": "isolated",
        "delivery": {
            "mode": "none",
        },
    }


def _health_check_cron(state: WizardState) -> dict:
    """Gateway Health Check — every 2 hours.

    Uses session_status tool to verify the gateway is running.
    Completely silent on success — only speaks on real problems.
    Notifies user via Telegram if something is wrong.
    """
    notify_target = _notify_target(state)

    return {
        "name": "Gateway Health Check",
        "schedule": {
            "kind": "every",
            "everyMs": 2 * 60 * 60 * 1000,  # 2 hours
        },
        "payload": {
            "kind": "agentTurn",
            "model": state.llm_budget,
            "timeoutSeconds": 60,
            "message": (
                "Actor: You are a System Monitor for an OpenClaw Gateway.\n"
                "Input: Use the session_status tool to check the current session.\n"
                "Mission: Verify the gateway is running normally. "
                "If everything is fine: output nothing at all — complete silence. "
                "Only if there is a real problem: output exactly one line starting with "
                "⚠️ followed by a brief description. No other output. No confirmations. "
                "No 'everything is fine' messages."
            ),
        },
        "sessionTarget": "isolated",
        "delivery": notify_target,
    }


def _notify_target(state: WizardState) -> dict:
    """Build delivery config for user notification.

    If Telegram is configured and we have an allow_from list,
    use the first entry as the notification target.
    Otherwise: announce to default channel.
    """
    if state.channel == "telegram" and state.channel_allow_from:
        return {
            "mode": "announce",
            "channel": "telegram",
            "to": str(state.channel_allow_from[0]),
        }
    return {"mode": "announce"}


def generate(state: WizardState) -> list[dict]:
    """Return list of cron job dicts to be merged into openclaw.json."""
    return [
        _daily_digest_cron(state),
        _health_check_cron(state),
    ]
