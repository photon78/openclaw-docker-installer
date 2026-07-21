"""Tests for script_registry_gen dry-run output."""
import tempfile
from pathlib import Path

from generator import script_registry_gen
from wizard.state import WizardState


def _state() -> WizardState:
    state = WizardState()
    state.script_registry_enabled = True
    state.script_sync_enabled = True
    state.allowlist_sync_enabled = True
    state.allowlist_auto_apply = True
    state.safe_exec_check_enabled = True
    return state


def test_registry_files_written() -> None:
    state = _state()
    with tempfile.TemporaryDirectory() as tmp:
        state.openclaw_dir = Path(tmp) / ".openclaw"
        state.home_dir = Path(tmp)
        # WizardState.__post_init__ already set openclaw_dir; override after init
        state.openclaw_dir = Path(tmp) / ".openclaw"
        written = script_registry_gen.write(state)
        names = {p.name for p in written}
        assert "scan_script_meta.py" in names
        assert "sync_agent_scripts.py" in names
        assert "sync_allowlist.py" in names
        assert "safe_exec_check.py" in names
        assert "registry.json" in names
        assert "example_script.py" in names


def test_registry_disabled_writes_nothing() -> None:
    state = _state()
    state.script_registry_enabled = False
    with tempfile.TemporaryDirectory() as tmp:
        state.openclaw_dir = Path(tmp) / ".openclaw"
        state.home_dir = Path(tmp)
        state.openclaw_dir = Path(tmp) / ".openclaw"
        written = script_registry_gen.write(state)
        assert written == []


def test_scan_script_meta_populates_registry() -> None:
    state = _state()
    with tempfile.TemporaryDirectory() as tmp:
        state.openclaw_dir = Path(tmp) / ".openclaw"
        state.home_dir = Path(tmp)
        state.openclaw_dir = Path(tmp) / ".openclaw"
        written = script_registry_gen.write(state)
        registry_path = state.workspace_dir / "scripts" / "registry.json"
        assert registry_path.exists()
        content = registry_path.read_text()
        assert "example_script.py" in content


def test_allowlist_sync_adds_entries() -> None:
    state = _state()
    with tempfile.TemporaryDirectory() as tmp:
        state.openclaw_dir = Path(tmp) / ".openclaw"
        state.home_dir = Path(tmp)
        state.openclaw_dir = Path(tmp) / ".openclaw"
        approvals_path = state.openclaw_dir / "exec-approvals.json"
        approvals_path.parent.mkdir(parents=True, exist_ok=True)
        approvals_path.write_text('{"agents": {}}')
        script_registry_gen.write(state)
        data = __import__("json").loads(approvals_path.read_text())
        assert "main" in data["agents"]
        assert "/home/node/.openclaw/workspace/scripts/example_script.py" in data["agents"]["main"]["allow"]
