"""Tests for config file generators."""
import json
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wizard.state import WizardState
from generator import env_gen, openclaw_json_gen, exec_approvals_gen


@pytest.fixture
def state(tmp_path: Path) -> WizardState:
    s = WizardState()
    s.home_dir = tmp_path
    s.openclaw_dir = tmp_path / ".openclaw"
    s.anthropic_api_key = "sk-ant-test-key"
    s.mistral_api_key = "mistral-test-key"
    s.telegram_bot_token = "123456:TEST-TOKEN"
    s.channel = "telegram"
    s.channel_allow_from = ["8620748747"]
    s.security_profile = "strict"
    s.llm_standard = "anthropic/claude-sonnet-4-6"
    s.llm_power = "anthropic/claude-opus-4-6"
    s.llm_budget = "mistral/mistral-large-latest"
    s.llm_media = "mistral/mistral-large-latest"
    return s


class TestEnvGen:
    def test_contains_anthropic_key(self, state: WizardState) -> None:
        content = env_gen.generate(state)
        assert "ANTHROPIC_API_KEY=sk-ant-test-key" in content

    def test_contains_mistral_key(self, state: WizardState) -> None:
        content = env_gen.generate(state)
        assert "MISTRAL_API_KEY=mistral-test-key" in content

    def test_contains_llm_tiers(self, state: WizardState) -> None:
        content = env_gen.generate(state)
        assert "LLM_STANDARD=anthropic/claude-sonnet-4-6" in content
        assert "LLM_POWER=anthropic/claude-opus-4-6" in content
        assert "LLM_BUDGET=mistral/mistral-large-latest" in content

    def test_username_from_state(self, state: WizardState) -> None:
        # Username must come from state, not be hardcoded
        state.username = "testuser"
        content = env_gen.generate(state)
        assert "USER_NAME=testuser" in content
        assert "USER_NAME=hummer" not in content

    def test_file_permissions(self, state: WizardState) -> None:
        path = env_gen.write(state)
        assert oct(path.stat().st_mode)[-3:] == "600"


class TestOpenClawJsonGen:
    def test_uses_env_vars_not_hardcoded_models(self, state: WizardState) -> None:
        config = openclaw_json_gen.generate(state)
        primary = config["agents"]["defaults"]["model"]["primary"]
        assert primary == "${LLM_STANDARD}"

    def test_telegram_channel_configured(self, state: WizardState) -> None:
        config = openclaw_json_gen.generate(state)
        assert "telegram" in config.get("channels", {})
        assert config["channels"]["telegram"]["enabled"] is True

    def test_allowfrom_set(self, state: WizardState) -> None:
        config = openclaw_json_gen.generate(state)
        allow = config["channels"]["telegram"].get("allowFrom", [])
        assert len(allow) == 1

    def test_workspace_from_state(self, state: WizardState, tmp_path: Path) -> None:
        # Workspace path must come from state
        content = json.dumps(openclaw_json_gen.generate(state))
        assert str(state.workspace_dir) in content

    def test_cron_enabled(self, state: WizardState) -> None:
        config = openclaw_json_gen.generate(state)
        assert config.get("cron", {}).get("enabled") is True


class TestExecApprovalsGen:
    def test_security_allowlist(self, state: WizardState) -> None:
        config = exec_approvals_gen.generate(state)
        assert config["defaults"]["security"] == "allowlist"

    def test_no_security_full(self, state: WizardState) -> None:
        content = json.dumps(exec_approvals_gen.generate(state))
        assert '"full"' not in content

    def test_socket_token_present(self, state: WizardState) -> None:
        config = exec_approvals_gen.generate(state)
        assert len(config["socket"]["token"]) > 20

    def test_paths_from_state(self, state: WizardState) -> None:
        # All paths must use state.openclaw_dir, not hardcoded /home/hummer
        content = json.dumps(exec_approvals_gen.generate(state))
        assert str(state.openclaw_dir) in content
        assert "/home/hummer" not in content

    def test_main_agent_has_allowlist(self, state: WizardState) -> None:
        config = exec_approvals_gen.generate(state)
        main = config["agents"]["main"]
        assert len(main["allowlist"]) > 0

    def test_file_permissions(self, state: WizardState) -> None:
        path = exec_approvals_gen.write(state)
        assert oct(path.stat().st_mode)[-3:] == "600"
