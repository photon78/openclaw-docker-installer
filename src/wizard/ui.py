"""
ui.py — Shared UI helpers for the wizard.

confirm_select() replaces questionary.confirm() to avoid the backspace bug
in TTY environments where typing anything other than y/n breaks the prompt.
Uses arrow-key selection instead — no typing, no backspace issues.
"""
import questionary


def confirm_select(message: str, default: bool = True) -> bool | None:
    """Arrow-key Yes/No prompt. Returns True/False/None (None = Ctrl+C / abort)."""
    choices = ["Yes", "No"] if default else ["No", "Yes"]
    result = questionary.select(message, choices=choices).ask()
    if result is None:
        return None
    return result == "Yes"
