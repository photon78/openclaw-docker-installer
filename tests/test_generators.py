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

    def test_no_hardcoded_values(self, state: WizardState, tmp_path: Path) -> None:
        # All values must come from state — no hardcoded paths or usernames
        state.username = "ghostuser"
        state.home_dir = tmp_path / "ghostuser"
        state.openclaw_dir = state.home_dir / ".openclaw"
        content = env_gen.generate(state)
        assert "USER_NAME=ghostuser" in content
        assert "hummer" not in content
        assert "/home/" not in content  # no absolute paths in .env

    def test_file_permissions(self, state: WizardState) -> None:
        path = env_gen.write(state)
        assert oct(path.stat().st_mode)[-3:] == "600"


class TestOpenClawJsonGen:
    def test_model_primary_uses_env_var_ref(self, state: WizardState) -> None:
        config = openclaw_json_gen.generate(state)
        primary = config["agents"]["defaults"]["model"]["primary"]
        # primary must use ${LLM_BUDGET} env var ref — model changes only require .env edit
        assert primary == "${LLM_BUDGET}"

    def test_model_fallbacks_use_env_var_refs(self, state: WizardState) -> None:
        config = openclaw_json_gen.generate(state)
        fallbacks = config["agents"]["defaults"]["model"]["fallbacks"]
        assert "${LLM_STANDARD}" in fallbacks
        assert "${LLM_POWER}" in fallbacks

    def test_no_models_alias_block(self, state: WizardState) -> None:
        # agents.defaults.models is not a valid OpenClaw config key — must not be set
        config = openclaw_json_gen.generate(state)
        assert "models" not in config["agents"]["defaults"]

    def test_telegram_channel_configured(self, state: WizardState) -> None:
        config = openclaw_json_gen.generate(state)
        assert "telegram" in config.get("channels", {})
        assert config["channels"]["telegram"]["enabled"] is True

    def test_allowfrom_set(self, state: WizardState) -> None:
        config = openclaw_json_gen.generate(state)
        allow = config["channels"]["telegram"].get("allowFrom", [])
        assert len(allow) == 1

    def test_workspace_uses_container_path(self, state: WizardState) -> None:
        # workspace must be the container-internal path, not the host path
        config = openclaw_json_gen.generate(state)
        workspace = config["agents"]["defaults"]["workspace"]
        assert workspace == "/home/node/.openclaw/workspace"
        assert "hummer" not in workspace
        assert "vboxuser" not in workspace

    def test_cron_enabled(self, state: WizardState) -> None:
        config = openclaw_json_gen.generate(state)
        assert config.get("cron", {}).get("enabled") is True

    def test_memory_search_provider_mistral(self, state: WizardState) -> None:
        # Mistral key present — should use mistral-embed
        state.mistral_api_key = "mistral-test-key"
        config = openclaw_json_gen.generate(state)
        ms = config["agents"]["defaults"]["memorySearch"]
        assert ms["provider"] == "mistral"
        assert ms["model"] == "mistral-embed"

    def test_memory_search_disabled_without_provider(self, state: WizardState) -> None:
        # No supported embedding provider — should disable gracefully
        state.mistral_api_key = ""
        config = openclaw_json_gen.generate(state)
        ms = config["agents"]["defaults"]["memorySearch"]
        assert ms.get("enabled") is False


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

    def test_no_hardcoded_values(self, state: WizardState) -> None:
        # All paths must come from state — no hardcoded /home/hummer or similar
        fake_home = Path("/opt/octest")
        state.home_dir = fake_home
        state.openclaw_dir = fake_home / ".openclaw"
        content = json.dumps(exec_approvals_gen.generate(state))
        assert "/opt/octest/.openclaw" in content
        assert "/home/hummer" not in content

    def test_main_agent_has_allowlist(self, state: WizardState) -> None:
        config = exec_approvals_gen.generate(state)
        main = config["agents"]["main"]
        assert len(main["allowlist"]) > 0

    def test_file_permissions(self, state: WizardState) -> None:
        path = exec_approvals_gen.write(state)
        assert oct(path.stat().st_mode)[-3:] == "600"

    def test_no_shell_tools_in_allowlists(self, state: WizardState) -> None:
        """Shell tools must never appear in any allowlist."""
        content = json.dumps(exec_approvals_gen.generate(state))
        forbidden = ["/usr/bin/bash", "/bin/bash", "/usr/bin/ls",
                     "/usr/bin/cat", "/usr/bin/grep", "/usr/bin/find",
                     "/usr/bin/sed", "/usr/bin/awk"]
        for tool in forbidden:
            assert tool not in content, f"Shell tool {tool!r} must not be in allowlist"

    def test_auto_allow_skills_default_false(self, state: WizardState) -> None:
        config = exec_approvals_gen.generate(state)
        assert config["agents"]["main"]["autoAllowSkills"] is False


class TestCronConfig:
    def test_crons_in_openclaw_json(self, state: WizardState) -> None:
        # cron.jobs is not injected into openclaw.json — OpenClaw does not
        # support this key. Crons are managed via the OpenClaw API post-install.
        config = openclaw_json_gen.generate(state)
        assert config["cron"]["enabled"] is True
        assert "jobs" not in config["cron"]
