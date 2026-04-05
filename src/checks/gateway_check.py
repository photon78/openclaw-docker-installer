"""
gateway_check.py — Checks if the OpenClaw Gateway is reachable after installation.
"""

from __future__ import annotations

import socket
import urllib.error
import urllib.request
from dataclasses import dataclass
from enum import Enum

DEFAULT_PORT = 18789  # OpenClaw Gateway default port
DEFAULT_TIMEOUT = 10


class GatewayState(Enum):
    OK = "ok"
    TIMEOUT = "timeout"
    REFUSED = "refused"
    ERROR = "error"


@dataclass
class GatewayStatus:
    """Result of a gateway reachability check."""
    state: GatewayState
    port: int
    message: str

    @property
    def ok(self) -> bool:
        return self.state == GatewayState.OK


def check_gateway(port: int = DEFAULT_PORT, timeout: int = DEFAULT_TIMEOUT) -> GatewayStatus:
    """Check if the OpenClaw Gateway responds on the given port.

    Tries HTTP GET on http://127.0.0.1:<port>/health.
    Returns a GatewayStatus with state OK, TIMEOUT, REFUSED, or ERROR.
    """
    url = f"http://127.0.0.1:{port}/health"

    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            if resp.status == 200:
                return GatewayStatus(
                    state=GatewayState.OK,
                    port=port,
                    message=f"Gateway is running on port {port}.",
                )
            return GatewayStatus(
                state=GatewayState.ERROR,
                port=port,
                message=f"Gateway responded with HTTP {resp.status}.",
            )

    except urllib.error.URLError as e:
        reason = e.reason
        if isinstance(reason, socket.timeout) or "timed out" in str(reason).lower():
            return GatewayStatus(
                state=GatewayState.TIMEOUT,
                port=port,
                message=f"Gateway did not respond within {timeout}s. Is Docker running?",
            )
        if isinstance(reason, ConnectionRefusedError) or "refused" in str(reason).lower():
            return GatewayStatus(
                state=GatewayState.REFUSED,
                port=port,
                message=f"Connection refused on port {port}. Gateway may not be started yet.",
            )
        return GatewayStatus(
            state=GatewayState.ERROR,
            port=port,
            message=f"Unexpected error: {e}",
        )

    except Exception as e:
        return GatewayStatus(
            state=GatewayState.ERROR,
            port=port,
            message=f"Unexpected error: {e}",
        )
