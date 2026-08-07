"""Tests enforcing the exec-approvals allowlist security policy.

The allowlist model is only effective if the agent cannot invoke a generic
interpreter, shell, or network tool. This test locks in that policy and fails
whenever a forbidden binary is added to any generated allowlist.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from generator import exec_approvals_gen
from shared.security_policy import FORBIDDEN_ALLOWLIST_BASES
from wizard.state import WizardState


def _state(tmp_path: Path) -> WizardState:
    """Minimal wizard state usable for exec-approvals generation."""
    s = WizardState()
    s.home_dir = tmp_path
    s.openclaw_dir = tmp_path / ".openclaw"
    s.auto_allow_skills = False
    return s


def _all_allowlists(state: WizardState):
    """Yield every allowlist entry from every generated agent profile."""
    config = exec_approvals_gen.generate(state)
    yield from config["defaults"]["allowlist"]
    for agent in config["agents"].values():
        yield from agent["allowlist"]


class TestAllowlistForbiddenBins:
    """No forbidden binary basename may appear in any generated allowlist."""

    def test_no_forbidden_basename_in_defaults(self, tmp_path: Path) -> None:
        state = _state(tmp_path)
        for entry in exec_approvals_gen.generate(state)["defaults"]["allowlist"]:
            basename = Path(entry["pattern"]).name
            assert basename not in FORBIDDEN_ALLOWLIST_BASES, (
                f"defaults allowlist contains forbidden binary: {entry['pattern']!r}"
            )

    def test_no_forbidden_basename_in_main(self, tmp_path: Path) -> None:
        state = _state(tmp_path)
        for entry in exec_approvals_gen.generate(state)["agents"]["main"]["allowlist"]:
            basename = Path(entry["pattern"]).name
            assert basename not in FORBIDDEN_ALLOWLIST_BASES, (
                f"main allowlist contains forbidden binary: {entry['pattern']!r}"
            )

    def test_no_forbidden_basename_in_any_profile(self, tmp_path: Path) -> None:
        state = _state(tmp_path)
        for entry in _all_allowlists(state):
            basename = Path(entry["pattern"]).name
            assert basename not in FORBIDDEN_ALLOWLIST_BASES, (
                f"allowlist contains forbidden binary: {entry['pattern']!r}"
            )

    def test_policy_list_covers_interpreters_and_network_tools(self) -> None:
        # Guard against accidentally shrinking the forbidden set.
        assert "python3" in FORBIDDEN_ALLOWLIST_BASES
        assert "bash" in FORBIDDEN_ALLOWLIST_BASES
        assert "curl" in FORBIDDEN_ALLOWLIST_BASES
        assert "rsync" in FORBIDDEN_ALLOWLIST_BASES
        assert "ln" in FORBIDDEN_ALLOWLIST_BASES


class TestSecurityProfileRemoved:
    """The security_profile tier concept must no longer exist in code or state."""

    def test_no_security_profile_in_state(self) -> None:
        assert not hasattr(WizardState, "security_profile")


class TestAllowlistContainsOnlyExpectedEntries:
    """Generated allowlists must use specific, registered scripts for workarounds."""

    def test_main_allowlist_has_no_full_interpreter_pattern(self, tmp_path: Path) -> None:
        state = _state(tmp_path)
        main = exec_approvals_gen.generate(state)["agents"]["main"]["allowlist"]
        patterns = {e["pattern"] for e in main}
        assert "/usr/bin/python3" not in patterns
        assert "/usr/bin/curl" not in patterns
        assert "/usr/bin/rsync" not in patterns
        assert "/usr/bin/ln" not in patterns
