#!/usr/bin/env python3
"""
utils.py — Shared utilities for mistral-* skills.
"""

import base64
import os
import shutil
import subprocess
import sys
from pathlib import Path

SHARED_OUTPUT = Path.home() / ".openclaw" / "workspace" / "shared-output"


def encode_file(path: str) -> str:
    """File → Base64 string."""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def decode_b64_to_file(b64: str, output_path: str) -> str:
    """Base64 string → Datei."""
    with open(output_path, "wb") as f:
        f.write(base64.b64decode(b64))
    return output_path


def is_url(s: str) -> bool:
    return s.startswith("http://") or s.startswith("https://")


def send_telegram(image_path: str, target: str = "8620748747") -> bool:
    """Bild via openclaw message send an Telegram schicken."""
    SHARED_OUTPUT.mkdir(parents=True, exist_ok=True)
    shared_path = SHARED_OUTPUT / Path(image_path).name
    shutil.copy(image_path, shared_path)

    cmd = [
        "openclaw", "message", "send",
        "--channel", "telegram",
        "--target", target,
        "--media", str(shared_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅ Gesendet via Telegram: {result.stdout.strip()}")
        return True
    else:
        print(f"❌ Telegram-Fehler: {result.stderr.strip()}", file=sys.stderr)
        return False
