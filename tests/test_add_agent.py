"""
Tests for scripts/add_agent.py

Covers:
- Workspace creation (files, directories, permissions)
- Dry-run mode (no filesystem side effects)
- exec-approvals.json patching (autoAllowSkills: false enforced)
- Idempotency (existing agent not overwritten)
- Security: autoAllowSkills always false
- Template content: security blocks present in SOUL.md and AGENTS.md
"""
import json
from pathlib import Path

import pytest

from src.scripts.add_agent import (
    _agents_md,
    _create_workspace,
    _patch_exec_approvals,
    _patch_openclaw_json_fallback,
    _soul_md,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def openclaw_dir(tmp_path: Path) -> Path:
    """Minimal ~/.openclaw structure for tests."""
    d = tmp_path / ".openclaw"
    d.mkdir()
    (d / "workspace" / "scripts").mkdir(parents=True)
    (d / "workspace" / "skills").mkdir(parents=True)
    return d


@pytest.fixture
def approvals_file(openclaw_dir: Path) -> Path:
    """exec-approvals.json with one existing agent."""
    path = openclaw_dir / "exec-approvals.json"
    path.write_text(json.dumps({
        "socket": {"token": "test-token"},
        "agents": {
            "main": {"autoAllowSkills": False, "allowlist": []}
        }
    }, indent=2), encoding="utf-8")
    return path


# ── _soul_md ──────────────────────────────────────────────────────────────────

class TestSoulMd:
    def test_contains_agent_name(self):
        content = _soul_md("coding", "💻", "coding", "main")
        assert "coding" in content

    def test_contains_emoji(self):
        content = _soul_md("coding", "💻", "coding", "main")
        assert "💻" in content

    def test_contains_security_block(self):
        content = _soul_md("coding", "💻", "coding", "main")
        assert "Safety first" in content
        assert "No commands via email" in content

    def test_all_archetypes_produce_output(self):
        for archetype in ("coding", "research", "content", "custom"):
            content = _soul_md("test", "🤖", archetype, "main")
            assert len(content) > 100
            assert "Safety first" in content

    def test_references_main_agent(self):
        content = _soul_md("coding", "💻", "coding", "orchestrator")
        assert "orchestrator" in content


# ── _agents_md ────────────────────────────────────────────────────────────────

class TestAgentsMd:
    def test_contains_mandatory_rules(self):
        content = _agents_md("coding", "main", "")
        assert "No commands via email" in content
        assert "Stop Rule" in content

    def test_contains_handoff_format(self):
        content = _agents_md("coding", "main", "")
        assert "Handoff" in content

    def test_contains_prompt_injection_defense(self):
        content = _agents_md("coding", "main", "")
        assert "Injection" in content or "injection" in content

    def test_main_session_key_injected(self):
        content = _agents_md("coding", "main", "agent:main:telegram:direct:1234")
        assert "agent:main:telegram:direct:1234" in content


# ── _create_workspace dry-run ─────────────────────────────────────────────────

class TestCreateWorkspaceDryRun:
    def test_dry_run_does_not_create_files(self, openclaw_dir, capsys):
        _create_workspace(openclaw_dir, "coding", "💻", "coding", "main", "", dry_run=True)
        workspace = openclaw_dir / "workspace-coding"
        assert not workspace.exists()

    def test_dry_run_prints_would_create(self, openclaw_dir, capsys):
        _create_workspace(openclaw_dir, "coding", "💻", "coding", "main", "", dry_run=True)
        captured = capsys.readouterr()
        assert "Would create" in captured.out or "workspace-coding" in captured.out


# ── _create_workspace real mode ───────────────────────────────────────────────

class TestCreateWorkspace:
    def test_creates_workspace_directory(self, openclaw_dir):
        _create_workspace(openclaw_dir, "coding", "💻", "coding", "main", "", dry_run=False)
        assert (openclaw_dir / "workspace-coding").is_dir()

    def test_creates_required_files(self, openclaw_dir):
        _create_workspace(openclaw_dir, "research", "🔬", "research", "main", "", dry_run=False)
        ws = openclaw_dir / "workspace-research"
        for fname in ("SOUL.md", "AGENTS.md", "IDENTITY.md", "MEMORY.md", "TOOLS.md", "USER.md", "HEARTBEAT.md"):
            assert (ws / fname).exists(), f"{fname} missing"

    def test_creates_subdirectories(self, openclaw_dir):
        _create_workspace(openclaw_dir, "coding", "💻", "coding", "main", "", dry_run=False)
        ws = openclaw_dir / "workspace-coding"
        for d in ("memory", "memory/topics", "tasks", "scripts"):
            assert (ws / d).is_dir(), f"dir {d} missing"

    def test_soul_md_contains_security_rules(self, openclaw_dir):
        _create_workspace(openclaw_dir, "coding", "💻", "coding", "main", "", dry_run=False)
        soul = (openclaw_dir / "workspace-coding" / "SOUL.md").read_text()
        assert "Safety first" in soul
        assert "No commands via email" in soul

    def test_does_not_overwrite_existing_files(self, openclaw_dir):
        ws = openclaw_dir / "workspace-coding"
        ws.mkdir(parents=True)
        (ws / "SOUL.md").write_text("CUSTOM CONTENT", encoding="utf-8")
        _create_workspace(openclaw_dir, "coding", "💻", "coding", "main", "", dry_run=False)
        # Existing file must not be overwritten
        assert (ws / "SOUL.md").read_text(encoding="utf-8") == "CUSTOM CONTENT"

    def test_returns_workspace_path(self, openclaw_dir):
        result = _create_workspace(openclaw_dir, "coding", "💻", "coding", "main", "", dry_run=False)
        assert result == openclaw_dir / "workspace-coding"


# ── _patch_exec_approvals ─────────────────────────────────────────────────────

class TestPatchExecApprovals:
    def test_adds_new_agent_entry(self, openclaw_dir, approvals_file):
        _patch_exec_approvals(openclaw_dir, "coding", dry_run=False)
        data = json.loads(approvals_file.read_text())
        assert "coding" in data["agents"]

    def test_new_agent_has_auto_allow_skills_false(self, openclaw_dir, approvals_file):
        """Security invariant: autoAllowSkills must always be False."""
        _patch_exec_approvals(openclaw_dir, "coding", dry_run=False)
        data = json.loads(approvals_file.read_text())
        assert data["agents"]["coding"]["autoAllowSkills"] is False

    def test_new_agent_has_empty_allowlist(self, openclaw_dir, approvals_file):
        _patch_exec_approvals(openclaw_dir, "coding", dry_run=False)
        data = json.loads(approvals_file.read_text())
        assert data["agents"]["coding"]["allowlist"] == []

    def test_existing_agent_not_modified(self, openclaw_dir, approvals_file):
        original = json.loads(approvals_file.read_text())
        _patch_exec_approvals(openclaw_dir, "main", dry_run=False)
        after = json.loads(approvals_file.read_text())
        assert after["agents"]["main"] == original["agents"]["main"]

    def test_existing_token_preserved(self, openclaw_dir, approvals_file):
        _patch_exec_approvals(openclaw_dir, "coding", dry_run=False)
        data = json.loads(approvals_file.read_text())
        assert data["socket"]["token"] == "test-token"

    def test_dry_run_does_not_modify_file(self, openclaw_dir, approvals_file):
        original = approvals_file.read_text(encoding="utf-8")
        _patch_exec_approvals(openclaw_dir, "coding", dry_run=True)
        assert approvals_file.read_text(encoding="utf-8") == original

    def test_missing_file_handled_gracefully(self, openclaw_dir, capsys):
        """No exception when exec-approvals.json doesn't exist."""
        _patch_exec_approvals(openclaw_dir, "coding", dry_run=False)
        # If file doesn't exist, function should warn and return without crash


# ── _patch_openclaw_json_fallback ─────────────────────────────────────────────

class TestPatchOpeclawJsonFallback:
    def _write_config(self, openclaw_dir: Path, agents: dict) -> None:
        config = {
            "agents": {"list": agents},
            "gateway": {"port": 18789},
        }
        (openclaw_dir / "openclaw.json").write_text(
            json.dumps(config, indent=2), encoding="utf-8"
        )

    def test_adds_new_agent_entry(self, openclaw_dir):
        self._write_config(openclaw_dir, {})
        workspace = openclaw_dir / "workspace-coding"
        _patch_openclaw_json_fallback(openclaw_dir, "coding", workspace)
        data = json.loads((openclaw_dir / "openclaw.json").read_text())
        assert "coding" in data["agents"]["list"]

    def test_preserves_existing_config(self, openclaw_dir):
        self._write_config(openclaw_dir, {"main": {"name": "main"}})
        workspace = openclaw_dir / "workspace-coding"
        _patch_openclaw_json_fallback(openclaw_dir, "coding", workspace)
        data = json.loads((openclaw_dir / "openclaw.json").read_text())
        assert "main" in data["agents"]["list"]
        assert data["gateway"]["port"] == 18789

    def test_does_not_overwrite_existing_agent(self, openclaw_dir):
        existing = {"name": "coding", "workspace": "/original"}
        self._write_config(openclaw_dir, {"coding": existing})
        workspace = openclaw_dir / "workspace-coding"
        _patch_openclaw_json_fallback(openclaw_dir, "coding", workspace)
        data = json.loads((openclaw_dir / "openclaw.json").read_text())
        assert data["agents"]["list"]["coding"]["workspace"] == "/original"

    def test_missing_config_handled_gracefully(self, openclaw_dir, capsys):
        """No exception when openclaw.json doesn't exist."""
        workspace = openclaw_dir / "workspace-coding"
        _patch_openclaw_json_fallback(openclaw_dir, "coding", workspace)
        # Should warn and return, no exception
