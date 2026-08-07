"""Tests for installer template files."""
import re
import subprocess
import sys
from pathlib import Path

import pytest

TEMPLATE_DIR = Path(__file__).parent.parent / "src" / "installer" / "templates"


class TestNoHardcodedChatIds:
    """Ensure no hardcoded identifiers such as Telegram chat IDs ship in templates."""

    @pytest.fixture(params=list(TEMPLATE_DIR.rglob("*")))
    def path(self, request: pytest.FixtureRequest) -> Path:
        p = request.param
        if p.is_dir() or p.name.startswith("."):
            pytest.skip("not a file")
        return p

    def test_no_long_numeric_literals(self, path: Path) -> None:
        """Numeric literals with 9 or more digits are a strong signal for
        phone/chat IDs. They must not appear in shipped templates.
        """
        # read as bytes to avoid encoding issues, decode lossily
        text = path.read_bytes().decode("utf-8", errors="replace")
        matches = re.findall(r"(?<!\d)\d{9,}(?!\d)", text)
        # Allow Unix timestamps in JSON metadata files.
        if path.suffix == ".json" and matches:
            return
        assert not matches, f"Found hardcoded numeric literal(s) in {path}: {matches}"


class TestOcrSendRequiresTarget:
    def test_send_without_target_exits_nonzero(self) -> None:
        ocr = TEMPLATE_DIR / "skills" / "mistral" / "mistral-ocr" / "ocr.py"
        result = subprocess.run(
            [sys.executable, str(ocr), "--send"],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0, "ocr.py --send without --target must fail"


class TestVisionExtractSendRequiresTarget:
    def test_send_without_target_exits_nonzero(self) -> None:
        extract = TEMPLATE_DIR / "skills" / "mistral" / "mistral-vision" / "extract.py"
        result = subprocess.run(
            [sys.executable, str(extract), "--send"],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0, "extract.py --send without --target must fail"
