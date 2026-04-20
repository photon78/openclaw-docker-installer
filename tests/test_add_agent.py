"""Tests for add_agent.py — agent registration via CLI and fallback."""
import json
import shutil
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "scripts"))

# Import functions from add_agent (which lives in src/scripts/)
import add_agent


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def openclaw_dir(tmp_path: Path) -> Path:
    d = tmp_path / ".openclaw"
    d.mkdir()
    return d


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    ws = tmp_path / ".openclaw" / "workspace-test"
    ws.mkdir(parents=True)
    return ws


@pytest.fixture
def openclaw_json(openclaw_dir: Path) -> Path:
    """Minimal openclaw.json with a main agent."""
    config = {
        "agents": {
            "list": {
                "main": {
                    "workspace": str(openclaw_dir / "workspace"),
                    "subagents": {"maxSpawnDepth": 1, "allowAgents": []},
                }
            }
        }
    }
    path = openclaw_dir / "openclaw.json"
    path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    return path


# ── CLI registration tests ─────────────────────────────────────────────────────

class TestRegisterAgentViaCLI:
    def test_calls_openclaw_agents_add(self, openclaw_dir: Path, workspace: Path) -> None:
        """Must call `openclaw agents add <name> --workspace <ws> --non-interactive`."""
        with patch("add_agent.shutil.which", return_value="/usr/bin/openclaw"):
            with patch("add_agent.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
                add_agent._register_agent_via_cli(openclaw_dir, "test", workspace, dry_run=False)

        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "openclaw"
        assert cmd[1] == "agents"
        assert cmd[2] == "add"
        assert "test" in cmd
        assert str(workspace) in cmd
        assert "--non-interactive" in cmd

    def test_dry_run_does_not_call_subprocess(self, openclaw_dir: Path, workspace: Path) -> None:
        """Dry-run must not invoke the CLI."""
        with patch("add_agent.shutil.which", return_value="/usr/bin/openclaw"):
            with patch("add_agent.subprocess.run") as mock_run:
                add_agent._register_agent_via_cli(openclaw_dir, "test", workspace, dry_run=True)
        mock_run.assert_not_called()

    def test_cli_not_found_skips_gracefully(self, openclaw_dir: Path, workspace: Path, capsys) -> None:
        """If openclaw CLI is missing, warn and skip (no crash)."""
        with patch("add_agent.shutil.which", return_value=None):
            add_agent._register_agent_via_cli(openclaw_dir, "test", workspace, dry_run=False)
        out = capsys.readouterr().out
        assert "not found" in out.lower() or "skipping" in out.lower()

    def test_cli_failure_triggers_fallback(self, openclaw_dir: Path, workspace: Path, openclaw_json: Path) -> None:
        """If CLI returns non-zero and not 'already exists', fall through to JSON fallback."""
        with patch("add_agent.shutil.which", return_value="/usr/bin/openclaw"):
            with patch("add_agent.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="some unexpected error")
                add_agent._register_agent_via_cli(openclaw_dir, "test", workspace, dry_run=False)

        # Fallback should have patched the JSON
        config = json.loads(openclaw_json.read_text())
        assert "test" in config["agents"]["list"]

    def test_already_registered_no_fallback(self, openclaw_dir: Path, workspace: Path, capsys) -> None:
        """If CLI reports 'already exists', do not trigger fallback."""
        with patch("add_agent.shutil.which", return_value="/usr/bin/openclaw"):
            with patch("add_agent.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=1, stdout="", stderr="agent already exists"
                )
                add_agent._register_agent_via_cli(openclaw_dir, "test", workspace, dry_run=False)
        out = capsys.readouterr().out
        assert "already registered" in out or "skipping" in out.lower()


# ── Fallback JSON patch tests ──────────────────────────────────────────────────

class TestPatchOpenclawJsonFallback:
    def test_adds_agent_entry(self, openclaw_dir: Path, workspace: Path, openclaw_json: Path) -> None:
        add_agent._patch_openclaw_json_fallback(openclaw_dir, "newagent", workspace)
        config = json.loads(openclaw_json.read_text())
        assert "newagent" in config["agents"]["list"]
        assert config["agents"]["list"]["newagent"]["workspace"] == str(workspace)

    def test_skips_if_already_present(self, openclaw_dir: Path, workspace: Path, openclaw_json: Path) -> None:
        add_agent._patch_openclaw_json_fallback(openclaw_dir, "newagent", workspace)
        add_agent._patch_openclaw_json_fallback(openclaw_dir, "newagent", workspace)
        config = json.loads(openclaw_json.read_text())
        # Should still only have one entry
        assert list(config["agents"]["list"].keys()).count("newagent") == 1

    def test_no_config_file_skips_gracefully(self, openclaw_dir: Path, workspace: Path) -> None:
        """Missing openclaw.json must not crash."""
        add_agent._patch_openclaw_json_fallback(openclaw_dir, "newagent", workspace)
        # No crash = pass


# ── Exec-approvals tests ───────────────────────────────────────────────────────

class TestPatchExecApprovals:
    def test_adds_agent_with_auto_allow_skills_false(self, openclaw_dir: Path) -> None:
        path = openclaw_dir / "exec-approvals.json"
        path.write_text(json.dumps({"agents": {}, "defaults": {}}), encoding="utf-8")

        add_agent._patch_exec_approvals(openclaw_dir, "myagent", dry_run=False)

        config = json.loads(path.read_text())
        assert "myagent" in config["agents"]
        assert config["agents"]["myagent"]["autoAllowSkills"] is False

    def test_dry_run_does_not_write(self, openclaw_dir: Path) -> None:
        path = openclaw_dir / "exec-approvals.json"
        original = json.dumps({"agents": {}, "defaults": {}})
        path.write_text(original, encoding="utf-8")

        add_agent._patch_exec_approvals(openclaw_dir, "myagent", dry_run=True)

        assert path.read_text() == original

    def test_skips_if_already_present(self, openclaw_dir: Path) -> None:
        path = openclaw_dir / "exec-approvals.json"
        path.write_text(
            json.dumps({"agents": {"myagent": {"autoAllowSkills": True}}, "defaults": {}}),
            encoding="utf-8",
        )
        add_agent._patch_exec_approvals(openclaw_dir, "myagent", dry_run=False)
        config = json.loads(path.read_text())
        # Must not have overwritten the existing entry
        assert config["agents"]["myagent"]["autoAllowSkills"] is True
