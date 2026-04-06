"""
Tests for checks/docker_check.py

All tests use mocks — no real Docker required.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.checks.docker_check import DockerStatus, check_docker


class TestDockerNotInstalled:
    def test_returns_not_installed_when_binary_missing(self):
        with patch("shutil.which", return_value=None):
            status = check_docker()
        assert status.installed is False
        assert status.running is False
        assert status.ready is False
        assert status.error is not None
        assert "Install it from" in status.error


class TestDockerNotRunning:
    def test_returns_not_running_when_daemon_down(self):
        with patch("shutil.which", return_value="/usr/bin/docker"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=1)
                status = check_docker()
        assert status.installed is True
        assert status.running is False
        assert status.ready is False
        assert "not running" in status.error.lower()

    def test_returns_error_when_subprocess_raises(self):
        with patch("shutil.which", return_value="/usr/bin/docker"):
            with patch("subprocess.run", side_effect=Exception("timeout")):
                status = check_docker()
        assert status.installed is True
        assert status.running is False
        assert status.ready is False


class TestDockerReady:
    def _make_run(self, returncode=0, stdout="26.1.0"):
        mock = MagicMock()
        mock.returncode = returncode
        mock.stdout = stdout
        return mock

    def test_returns_ready_when_all_ok(self):
        with patch("shutil.which", return_value="/usr/bin/docker"):
            with patch("subprocess.run", return_value=self._make_run()):
                status = check_docker()
        assert status.installed is True
        assert status.running is True
        assert status.compose_available is True
        assert status.version_ok is True
        assert status.ready is True
        assert status.error is None

    def test_version_too_old(self):
        with patch("shutil.which", return_value="/usr/bin/docker"):
            with patch("subprocess.run") as mock_run:
                # docker info ok, compose ok, version too old
                responses = [
                    self._make_run(0),   # docker info
                    self._make_run(0),   # docker compose version
                    self._make_run(0, stdout="19.03.0"),  # docker version
                ]
                mock_run.side_effect = responses
                status = check_docker()
        assert status.version_ok is False
        assert status.ready is False
