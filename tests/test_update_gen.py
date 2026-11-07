"""Tests for UPDATE.md generator (update_gen)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wizard.state import WizardState
from generator import update_gen

FAKE_HOME = Path("/opt/octest")


def make_state() -> WizardState:
    s = WizardState()
    s.home_dir = FAKE_HOME
    s.openclaw_dir = FAKE_HOME / ".openclaw"
    return s


class TestUpdateGen:
    def test_contains_compose_path(self) -> None:
        content = update_gen.generate(make_state())
        assert "docker-compose.yml" in content

    def test_contains_backup_step(self) -> None:
        # Update flow must include the backup step before pulling
        content = update_gen.generate(make_state())
        assert "daily_backup.py" in content

    def test_contains_skip_onboarding_flag(self) -> None:
        content = update_gen.generate(make_state())
        assert "OPENCLAW_SKIP_ONBOARDING=1" in content

    def test_contains_doctor_step(self) -> None:
        content = update_gen.generate(make_state())
        assert "doctor" in content

    def test_rollback_pins_explicit_version(self) -> None:
        # Rollback must instruct version pinning, not re-pull the same alias
        content = update_gen.generate(make_state())
        assert "image: ghcr.io/openclaw/openclaw:" in content

    def test_write_creates_file(self, tmp_path: Path) -> None:
        s = WizardState()
        s.home_dir = tmp_path
        s.openclaw_dir = tmp_path / ".openclaw"
        result = update_gen.write(s)
        assert result == s.openclaw_dir / "UPDATE.md"
        assert result.exists()
        assert result.read_text(encoding="utf-8").startswith("# OpenClaw Update Guide")
