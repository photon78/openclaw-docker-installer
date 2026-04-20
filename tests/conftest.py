"""
conftest.py — pytest session setup.

Adds src/ to sys.path so installer-internal imports work correctly in tests.
Modules inside src/ import each other without the 'src.' prefix (e.g.
`from wizard.state import WizardState`). Tests import from `src.*`, which
works because pytest adds the project root to sys.path. But transitive
internal imports need src/ directly on sys.path too.
"""
import sys
from pathlib import Path

_SRC = str(Path(__file__).parent.parent / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)
