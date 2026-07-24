"""Tests for the post-install sync_allowlist_deep hook in main.py."""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from main import _run_allowlist_sync


@pytest.fixture
def fake_state(tmp_path: Path):
    state = MagicMock()
    state.agent_name = "main"
    state.openclaw_dir = tmp_path
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir(parents=True)
    return state


def test_run_allowlist_sync_success(fake_state, caplog):
    script = fake_state.openclaw_dir / "scripts" / "sync_allowlist_deep.py"
    script.write_text("#!/usr/bin/env python3\nprint('sync ok')\n", encoding="utf-8")

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "sync ok\n"
        mock_run.return_value.stderr = ""
        _run_allowlist_sync(fake_state)

    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    assert args[0] == "python3"
    assert args[2] == "--agent"
    assert args[3] == "main"
    assert args[4] == "--apply"


def test_run_allowlist_sync_missing_script(fake_state):
    with patch("subprocess.run") as mock_run:
        _run_allowlist_sync(fake_state)
        mock_run.assert_not_called()


def test_run_allowlist_sync_failure_non_fatal(fake_state):
    script = fake_state.openclaw_dir / "scripts" / "sync_allowlist_deep.py"
    script.write_text("#!/usr/bin/env python3\n", encoding="utf-8")

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = "some warning"
        _run_allowlist_sync(fake_state)

    mock_run.assert_called_once()
    # Failure must not raise — hook is non-fatal
