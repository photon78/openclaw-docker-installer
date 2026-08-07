"""Tests for shipped skill templates — security and interface contracts."""
import re
import subprocess
import sys
from pathlib import Path

import pytest

TEMPLATES_DIR = Path(__file__).parent.parent / "src" / "installer" / "templates"
SKILL_MISTRAL_DIR = TEMPLATES_DIR / "skills" / "mistral"


def _python_files_under(path: Path) -> list[Path]:
    return list(path.rglob("*.py"))


def _markdown_files_under(path: Path) -> list[Path]:
    return list(path.rglob("*.md"))


class TestNoHardcodedChatIds:
    """Any shipped template must not contain fixed private identifiers."""

    @pytest.mark.parametrize("path", _python_files_under(TEMPLATES_DIR) + _markdown_files_under(TEMPLATES_DIR))
    def test_no_long_numeric_literals(self, path: Path) -> None:
        """Numeric literals with 9+ digits are almost certainly chat IDs/phone numbers."""
        content = path.read_text(encoding="utf-8")
        matches = re.findall(r"\b\d{9,}\b", content)
        assert not matches, f"{path.relative_to(TEMPLATES_DIR)} contains numeric literal(s): {matches}"


class TestOcrSendRequiresTarget:
    """ocr.py --send must require an explicit --target; no default chat ID."""

    def test_send_without_target_exits_nonzero(self, tmp_path: Path) -> None:
        ocr_py = SKILL_MISTRAL_DIR / "mistral-ocr" / "ocr.py"
        # Create a dummy input so argument parsing is the only thing tested.
        dummy = tmp_path / "dummy.txt"
        dummy.write_text("dummy")
        result = subprocess.run(
            [sys.executable, str(ocr_py), "--input", str(dummy), "--send"],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0, "ocr.py --send without --target must exit with an error"
        assert "--target" in result.stderr or "target" in result.stderr.lower(), (
            "error message should mention --target"
        )


class TestVisionExtractSendRequiresTarget:
    """vision extract.py --send must require an explicit --target."""

    def test_send_without_target_exits_nonzero(self, tmp_path: Path) -> None:
        extract_py = SKILL_MISTRAL_DIR / "mistral-vision" / "extract.py"
        result = subprocess.run(
            [sys.executable, str(extract_py), "--image", str(tmp_path / "dummy.jpg"), "--send"],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0, "extract.py --send without --target must exit with an error"
