#!/bin/sh
# OpenClaw Installer — launcher for Linux/macOS
# Activates venv automatically, creates it if missing.
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$SCRIPT_DIR/.venv"
PYTHON=python3

# Create venv if missing or requirements changed
if [ ! -f "$VENV/bin/python3" ]; then
    echo "Setting up virtual environment..."
    "$PYTHON" -m venv "$VENV"
    if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
        "$VENV/bin/pip" install --quiet -r "$SCRIPT_DIR/requirements.txt"
    fi
    "$VENV/bin/pip" install --quiet -e "$SCRIPT_DIR[dev]"
    echo "Done."
fi

exec "$VENV/bin/python3" "$SCRIPT_DIR/src/main.py" "$@"
