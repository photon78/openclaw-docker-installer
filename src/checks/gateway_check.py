"""
gateway_check.py — Ping auf OpenClaw Gateway nach Installation
"""

import urllib.request
import urllib.error


def ping_gateway(port: int = 3000, timeout: int = 10) -> bool:
    """Prüft ob das Gateway auf dem angegebenen Port antwortet."""
    url = f"http://127.0.0.1:{port}/health"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False
