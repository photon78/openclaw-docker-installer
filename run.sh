#!/bin/sh
# OpenClaw Installer — launcher for Linux/macOS
# Activates venv automatically, creates it if missing.
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$SCRIPT_DIR/.venv"
PYTHON=python3

# Create venv if missing
if [ ! -f "$VENV/bin/python3" ]; then
    echo "Setting up virtual environment..."
    "$PYTHON" -m venv "$VENV"
    "$VENV/bin/pip" install --quiet -e "$SCRIPT_DIR[dev]"
    echo "Done."
fi

exec "$VENV/bin/python3" "$SCRIPT_DIR/src/main.py" "$@"
