"""
Tests for generator/backup_gen.py

Verifies that the generated daily_backup.py:
- Contains correct rsync excludes (venv/, __pycache__/, .venv/, .git/ etc.)
- Uses the configured backup mount path
- Is written as an executable file
- Returns None when backup is not configured
"""
import stat
import sys
from pathlib import Path

import pytest

from src.generator.backup_gen import generate, write
from wizard.state import WizardState


def _make_state(tmp_path: Path, backup_mount: str = "/mnt/backup") -> WizardState:
    state = WizardState()
    state.home_dir = tmp_path
    state.openclaw_dir = tmp_path / ".openclaw"
    state.openclaw_dir.mkdir(parents=True, exist_ok=True)
    state.backup_mount_path = backup_mount
    return state


# ── RSYNC_EXCLUDES in generated script ────────────────────────────────────────

class TestRsyncExcludes:
    """Verify that generated script contains all required exclude entries."""

    def test_dotenv_venv_excluded(self, tmp_path):
        content = generate(_make_state(tmp_path))
        assert "--exclude=.venv/" in content

    def test_plain_venv_excluded(self, tmp_path):
        """venv/ (without dot) must be excluded — NAS cannot store its symlinks."""
        content = generate(_make_state(tmp_path))
        assert "--exclude=venv/" in content

    def test_pycache_excluded(self, tmp_path):
        """__pycache__/ must be excluded — NAS cannot store special files."""
        content = generate(_make_state(tmp_path))
        assert "--exclude=__pycache__/" in content

    def test_git_dir_excluded(self, tmp_path):
        content = generate(_make_state(tmp_path))
        assert "--exclude=.git/" in content

    def test_node_modules_excluded(self, tmp_path):
        content = generate(_make_state(tmp_path))
        assert "--exclude=node_modules/" in content

    def test_dist_excluded(self, tmp_path):
        content = generate(_make_state(tmp_path))
        assert "--exclude=dist/" in content

    def test_log_files_excluded(self, tmp_path):
        content = generate(_make_state(tmp_path))
        assert "--exclude=*.log" in content


# ── generate() content ────────────────────────────────────────────────────────

class TestGenerate:
    def test_returns_valid_python_header(self, tmp_path):
        content = generate(_make_state(tmp_path))
        assert content.startswith("#!/usr/bin/env python3")

    def test_uses_configured_mount_path(self, tmp_path):
        state = _make_state(tmp_path, backup_mount="/mnt/usb")
        content = generate(state)
        assert "/mnt/usb" in content

    def test_fallback_mount_when_empty(self, tmp_path):
        state = _make_state(tmp_path, backup_mount="")
        content = generate(state)
        assert "/mnt/backup" in content

    def test_contains_main_function(self, tmp_path):
        content = generate(_make_state(tmp_path))
        assert "def main()" in content

    def test_handles_sunday_full_backup(self, tmp_path):
        content = generate(_make_state(tmp_path))
        assert "Sunday" in content or "sunday" in content.lower() or "isoweekday" in content

    def test_no_dotenv_reference(self, tmp_path):
        """Generated script must never reference .env (API keys)."""
        content = generate(_make_state(tmp_path))
        assert "API_KEY" not in content
        assert ".env" not in content


# ── write() filesystem behaviour ──────────────────────────────────────────────

class TestWrite:
    def test_returns_none_when_backup_not_configured(self, tmp_path):
        state = _make_state(tmp_path)
        state.backup_mount_path = None
        result = write(state)
        assert result is None

    def test_returns_none_when_mount_path_empty_string(self, tmp_path):
        state = _make_state(tmp_path, backup_mount="")
        # backup_gen.write() checks state.backup_mount_path — empty string is falsy
        state.backup_mount_path = ""
        result = write(state)
        assert result is None

    def test_writes_script_to_scripts_dir(self, tmp_path):
        state = _make_state(tmp_path)
        result = write(state)
        assert result is not None
        assert result.name == "daily_backup.py"
        assert result.parent == state.openclaw_dir / "scripts"

    def test_written_file_exists(self, tmp_path):
        state = _make_state(tmp_path)
        result = write(state)
        assert result.exists()

    @pytest.mark.skipif(sys.platform == "win32", reason="chmod executable bits not supported on Windows")
    def test_written_file_is_executable(self, tmp_path):
        state = _make_state(tmp_path)
        result = write(state)
        mode = result.stat().st_mode
        assert mode & stat.S_IXUSR, "daily_backup.py should be owner-executable"

    def test_written_content_matches_generate(self, tmp_path):
        state = _make_state(tmp_path)
        expected = generate(state)
        result = write(state)
        assert result.read_text(encoding="utf-8") == expected

    def test_write_is_idempotent(self, tmp_path):
        state = _make_state(tmp_path)
        result1 = write(state)
        result2 = write(state)
        assert result1 == result2
        assert result2.read_text(encoding="utf-8") == generate(state)
