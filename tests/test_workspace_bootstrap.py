"""Tests for workspace_bootstrap_gen."""
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wizard.state import WizardState
from generator import workspace_bootstrap_gen


@pytest.fixture
def state(tmp_path: Path) -> WizardState:
    s = WizardState()
    s.home_dir = tmp_path
    s.openclaw_dir = tmp_path / ".openclaw"  # workspace_dir + scripts_dir are computed from this
    s.agent_name = "test_agent"
    s.agent_emoji = "🤖"
    s.persona_style = "direct"
    s.channel = "telegram"
    s.username = "testuser"
    return s


class TestWorkspaceBootstrapGen:
    def test_creates_workspace_directory(self, state: WizardState) -> None:
        workspace_bootstrap_gen.write(state)
        assert state.workspace_dir.is_dir()

    def test_creates_required_subdirectories(self, state: WizardState) -> None:
        workspace_bootstrap_gen.write(state)
        assert (state.workspace_dir / "memory").is_dir()
        assert (state.workspace_dir / "tasks").is_dir()
        assert (state.workspace_dir / "scripts").is_dir()
        assert (state.workspace_dir / "memory" / "topics").is_dir()

    def test_creates_all_required_files(self, state: WizardState) -> None:
        workspace_bootstrap_gen.write(state)
        required = [
            "SOUL.md",
            "AGENTS.md",
            "HEARTBEAT.md",
            "IDENTITY.md",
            "MEMORY.md",
            "USER.md",
            "BOOTSTRAP.md",
            "scripts/check_tasks.py",
        ]
        for filename in required:
            assert (state.workspace_dir / filename).is_file(), f"Missing: {filename}"

    def test_no_symlinks_for_workspace_files(self, state: WizardState) -> None:
        """All workspace files must be real copies — never symlinks."""
        workspace_bootstrap_gen.write(state)
        for md_file in state.workspace_dir.glob("*.md"):
            assert not md_file.is_symlink(), f"{md_file.name} must not be a symlink"
        check_tasks = state.workspace_dir / "scripts" / "check_tasks.py"
        assert not check_tasks.is_symlink()

    def test_soul_md_contains_no_email_rule(self, state: WizardState) -> None:
        workspace_bootstrap_gen.write(state)
        content = (state.workspace_dir / "SOUL.md").read_text()
        assert "email" in content.lower() or "e-mail" in content.lower()

    def test_agents_md_contains_no_email_rule(self, state: WizardState) -> None:
        workspace_bootstrap_gen.write(state)
        content = (state.workspace_dir / "AGENTS.md").read_text(encoding="utf-8")
        assert "email" in content.lower() or "e-mail" in content.lower()

    def test_soul_md_contains_agent_name(self, state: WizardState) -> None:
        workspace_bootstrap_gen.write(state)
        content = (state.workspace_dir / "SOUL.md").read_text()
        assert state.agent_name in content

    def test_heartbeat_md_contains_workspace_specific_path(self, state: WizardState) -> None:
        """HEARTBEAT.md must reference the workspace-specific check_tasks.py path."""
        workspace_bootstrap_gen.write(state)
        content = (state.workspace_dir / "HEARTBEAT.md").read_text()
        expected_path = str(state.workspace_dir / "scripts" / "check_tasks.py")
        assert expected_path in content

    def test_heartbeat_md_uses_state_paths(self, state: WizardState) -> None:
        """HEARTBEAT.md must reference paths derived from state, not hardcoded values."""
        workspace_bootstrap_gen.write(state)
        content = (state.workspace_dir / "HEARTBEAT.md").read_text()
        # Path must be based on state.workspace_dir, not any hardcoded value
        assert str(state.workspace_dir) in content
        assert str(state.workspace_dir / "scripts" / "check_tasks.py") in content

    def test_check_tasks_py_references_correct_tasks_dir(self, state: WizardState) -> None:
        workspace_bootstrap_gen.write(state)
        content = (state.workspace_dir / "scripts" / "check_tasks.py").read_text()
        expected_tasks_dir = str(state.workspace_dir / "tasks")
        assert expected_tasks_dir in content

    @pytest.mark.skipif(sys.platform == "win32", reason="Unix file permissions not supported on Windows")
    def test_check_tasks_py_is_executable(self, state: WizardState) -> None:
        workspace_bootstrap_gen.write(state)
        check_tasks = state.workspace_dir / "scripts" / "check_tasks.py"
        mode = oct(check_tasks.stat().st_mode)
        assert mode[-3:] in ("755", "744", "775"), f"Expected executable, got {mode}"

    def test_user_md_contains_state_username(self, state: WizardState) -> None:
        """USER.md must contain the username from WizardState, not a hardcoded value."""
        workspace_bootstrap_gen.write(state)
        content = (state.workspace_dir / "USER.md").read_text()
        assert state.username in content

    def test_memory_md_contains_state_username(self, state: WizardState) -> None:
        """MEMORY.md must reference state.username."""
        workspace_bootstrap_gen.write(state)
        content = (state.workspace_dir / "MEMORY.md").read_text()
        assert state.username in content

    def test_write_returns_list_of_paths(self, state: WizardState) -> None:
        result = workspace_bootstrap_gen.write(state)
        assert isinstance(result, list)
        assert len(result) > 0
        for path in result:
            assert isinstance(path, Path)
            assert path.exists()


class TestWorkspaceBootstrapSecurityFeatures:
    def test_exec_approvals_auto_allow_skills_default_false(self, state: WizardState) -> None:
        """autoAllowSkills must default to False in WizardState."""
        assert state.auto_allow_skills is False

    def test_exec_approvals_auto_allow_skills_respects_state(self, state: WizardState) -> None:
        from generator import exec_approvals_gen
        state.auto_allow_skills = True
        config = exec_approvals_gen.generate(state)
        assert config["agents"]["main"]["autoAllowSkills"] is True

        state.auto_allow_skills = False
        config = exec_approvals_gen.generate(state)
        assert config["agents"]["main"]["autoAllowSkills"] is False

    def test_exec_approvals_no_shell_tools_in_defaults(self, state: WizardState) -> None:
        """Shell tools must not appear in the defaults allowlist."""
        from generator import exec_approvals_gen
        config = exec_approvals_gen.generate(state)
        defaults_patterns = [e["pattern"] for e in config["defaults"]["allowlist"]]
        forbidden = ["/usr/bin/ls", "/usr/bin/cat", "/usr/bin/grep",
                     "/usr/bin/find", "/usr/bin/head", "/usr/bin/tail",
                     "/usr/bin/wc"]
        for tool in forbidden:
            assert tool not in defaults_patterns, f"{tool} must not be in defaults allowlist"

    def test_exec_approvals_no_bash_in_main(self, state: WizardState) -> None:
        """Bash must not appear in the main allowlist."""
        from generator import exec_approvals_gen
        config = exec_approvals_gen.generate(state)
        main_patterns = [e["pattern"] for e in config["agents"]["main"]["allowlist"]]
        assert "/bin/bash" not in main_patterns
        assert "/usr/bin/bash" not in main_patterns

    def test_exec_approvals_no_shell_tools_in_main(self, state: WizardState) -> None:
        """Shell tools must not appear in the main allowlist."""
        from generator import exec_approvals_gen
        config = exec_approvals_gen.generate(state)
        main_patterns = [e["pattern"] for e in config["agents"]["main"]["allowlist"]]
        forbidden = ["/usr/bin/ls", "/usr/bin/cat", "/usr/bin/grep",
                     "/usr/bin/find", "/usr/bin/head", "/usr/bin/tail",
                     "/usr/bin/wc", "/usr/bin/sort"]
        for tool in forbidden:
            assert tool not in main_patterns, f"{tool} must not be in main allowlist"

    def test_openclaw_json_has_rate_limit(self, state: WizardState) -> None:
        from generator import openclaw_json_gen
        config = openclaw_json_gen.generate(state)
        rate_limit = config["gateway"]["auth"]["rateLimit"]
        assert rate_limit["maxAttempts"] == 10
        assert rate_limit["windowMs"] == 60000
        assert rate_limit["lockoutMs"] == 300000

    def test_openclaw_json_no_approval_buttons_plugin(self, state: WizardState) -> None:
        from generator import openclaw_json_gen
        config = openclaw_json_gen.generate(state)
        # telegram-approval-buttons is an optional plugin — not installed by default
        entries = config["plugins"]["entries"]
        assert "telegram-approval-buttons" not in entries

    def test_openclaw_json_mistral_plugin_enabled(self, state: WizardState) -> None:
        """Mistral must run via plugin — no custom models.providers block."""
        from generator import openclaw_json_gen
        import json
        config = openclaw_json_gen.generate(state)
        # Plugin entry must exist and be enabled
        assert config["plugins"]["entries"]["mistral"]["enabled"] is True
        # No custom provider block (causes 404)
        config_str = json.dumps(config)
        assert "models.providers" not in config_str
        assert "auth.profiles" not in config_str

    def test_openclaw_json_plugins_allow_list(self, state: WizardState) -> None:
        """plugins.allow must be set to prevent silent resets on openclaw update."""
        from generator import openclaw_json_gen
        config = openclaw_json_gen.generate(state)
        allow = config["plugins"]["allow"]
        assert "mistral" in allow
        assert "anthropic" in allow
