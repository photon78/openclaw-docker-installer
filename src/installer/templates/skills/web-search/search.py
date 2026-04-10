#!/usr/bin/env python3
"""
DDG Search Wrapper — direkter Python-Einstiegspunkt (ersetzt search.sh)
Usage: python3 search.py "<query>" [--max-results N] [--type web|news|images|videos] [--time-range d|w|m|y] [--format text|markdown|json]
"""
import sys
import os
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
VENV_PYTHON = SCRIPT_DIR / ".venv" / "bin" / "python"
SEARCH_SCRIPT = SCRIPT_DIR / "scripts" / "search.py"

if not VENV_PYTHON.exists():
    print(f"Error: venv not found at {VENV_PYTHON}", file=sys.stderr)
    sys.exit(1)

os.execv(str(VENV_PYTHON), [str(VENV_PYTHON), str(SEARCH_SCRIPT)] + sys.argv[1:])
