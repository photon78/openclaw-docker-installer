"""Tests for .env generator (env_gen) — v0.5.x features and hygiene."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wizard.state import WizardState
from generator import env_gen

FAKE_HOME = Path("/opt/octest")


def make_state() -> WizardState:
    s = WizardState()
    s.home_dir = FAKE_HOME
    s.openclaw_dir = FAKE_HOME / ".openclaw"
    return s


class TestEnvAuthSecrets:
    def test_auth_dir_written_when_set(self) -> None:
        s = make_state()
        s.auth_profile_secret_dir = str(FAKE_HOME / ".openclaw-auth-secrets")
        content = env_gen.generate(s)
        assert f"OPENCLAW_AUTH_PROFILE_SECRET_DIR={s.auth_profile_secret_dir}" in content

    def test_auth_dir_commented_when_unset(self) -> None:
        content = env_gen.generate(make_state())
        assert "# OPENCLAW_AUTH_PROFILE_SECRET_DIR=" in content

    def test_gateway_bind_is_lan(self) -> None:
        # Inside Docker the gateway must bind 'lan', not loopback —
        # otherwise the published host port is unreachable (P0 fix).
        content = env_gen.generate(make_state())
        assert "OPENCLAW_GATEWAY_BIND=lan" in content


class TestEnvAgentPlaceholders:
    def test_no_internal_agent_names(self) -> None:
        # Internal ops constellation must not leak into the public template
        content = env_gen.generate(make_state())
        assert "VALERE" not in content
        assert "SENTINEL" not in content
        assert "SIONIS" not in content

    def test_generic_agent_examples_present(self) -> None:
        content = env_gen.generate(make_state())
        assert "# TELEGRAM_BOT_TOKEN_CODING=" in content
        assert "# TELEGRAM_BOT_TOKEN_RESEARCH=" in content

    def test_no_hardcoded_username(self) -> None:
        content = env_gen.generate(make_state())
        assert "hummer" not in content
        assert "/home/hummer" not in content
