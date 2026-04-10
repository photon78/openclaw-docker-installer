"""Tests for python_check — availability and version detection."""
import sys
from unittest.mock import MagicMock, patch

from src.checks.python_check import check_python


class TestPythonCurrentInterpreter:
    def test_running_interpreter_sufficient(self) -> None:
        # The test runner itself must be Python 3.11+
        status = check_python()
        assert status.installed is True
        assert status.version_ok is True
        assert status.ready is True
        assert status.executable == sys.executable

    def test_version_string_present(self) -> None:
        status = check_python()
        assert status.version is not None
        parts = status.version.split(".")
        assert len(parts) >= 2
        assert int(parts[0]) >= 3


class TestPythonTooOld:
    def test_old_interpreter_fails(self) -> None:
        # Simulate running under Python 3.9
        fake_version = MagicMock()
        fake_version.major = 3
        fake_version.minor = 9
        fake_version.micro = 0
        fake_version.__ge__ = lambda self, other: (self.major, self.minor) >= other

        with patch("src.checks.python_check.sys.version_info", (3, 9, 0)):
            with patch("src.checks.python_check.shutil.which", return_value=None):
                status = check_python()
                assert status.installed is False
                assert status.ready is False


class TestPythonNotFound:
    def test_not_installed(self) -> None:
        with patch("src.checks.python_check.sys.version_info", (3, 9, 0)):
            with patch("src.checks.python_check.shutil.which", return_value=None):
                status = check_python()
                assert status.installed is False
                assert status.ready is False
                assert status.error is not None
