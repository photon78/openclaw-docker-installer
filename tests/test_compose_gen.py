"""Tests for docker-compose.yml generator."""
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wizard.state import WizardState
from generator import compose_gen

FAKE_HOME = Path("/opt/octest")
IMAGE = "ghcr.io/openclaw/openclaw:v2026.4.2"


@pytest.fixture
def state() -> WizardState:
    s = WizardState()
    s.home_dir = FAKE_HOME
    s.openclaw_dir = FAKE_HOME / ".openclaw"
    return s


class TestComposeGen:
    def test_image_pinned(self, state: WizardState) -> None:
        content = compose_gen.generate(state, IMAGE)
        assert IMAGE in content

    def test_scripts_readonly(self, state: WizardState) -> None:
        content = compose_gen.generate(state, IMAGE)
        assert "scripts:ro" in content

    def test_env_file_referenced(self, state: WizardState) -> None:
        content = compose_gen.generate(state, IMAGE)
        assert ".env" in content

    def test_config_readonly(self, state: WizardState) -> None:
        content = compose_gen.generate(state, IMAGE)
        assert "openclaw.json:ro" in content
        assert "exec-approvals.json:ro" in content

    def test_no_hardcoded_username(self, state: WizardState) -> None:
        content = compose_gen.generate(state, IMAGE)
        assert "hummer" not in content
        assert "/home/hummer" not in content

    def test_paths_from_state(self, state: WizardState) -> None:
        content = compose_gen.generate(state, IMAGE)
        assert str(state.workspace_dir) in content
        assert str(state.scripts_dir) in content

    def test_no_new_privileges(self, state: WizardState) -> None:
        content = compose_gen.generate(state, IMAGE)
        assert "no-new-privileges:true" in content

    def test_healthcheck_present(self, state: WizardState) -> None:
        content = compose_gen.generate(state, IMAGE)
        assert "healthcheck" in content
        assert "/healthz" in content

    def test_port_loopback_only(self, state: WizardState) -> None:
        # Port must be bound to loopback, not 0.0.0.0
        content = compose_gen.generate(state, IMAGE)
        assert "127.0.0.1:18789" in content
        assert "0.0.0.0" not in content
