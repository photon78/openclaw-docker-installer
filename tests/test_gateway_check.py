"""
Tests for checks/gateway_check.py

All tests mock HTTP calls — no real Gateway required.
"""

import urllib.error
import socket
from unittest.mock import MagicMock, patch

from src.checks.gateway_check import GatewayState, check_gateway


class TestGatewayOk:
    def test_returns_ok_on_200(self):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            status = check_gateway(port=18789)

        assert status.ok is True
        assert status.state == GatewayState.OK

    def test_returns_error_on_non_200(self):
        mock_resp = MagicMock()
        mock_resp.status = 503
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            status = check_gateway(port=18789)

        assert status.ok is False
        assert status.state == GatewayState.ERROR


class TestGatewayNotReachable:
    def test_returns_refused_on_connection_refused(self):
        with patch("urllib.request.urlopen",
                   side_effect=urllib.error.URLError(ConnectionRefusedError())):
            status = check_gateway(port=18789)

        assert status.ok is False
        assert status.state == GatewayState.REFUSED

    def test_returns_timeout_on_timeout(self):
        with patch("urllib.request.urlopen",
                   side_effect=urllib.error.URLError(socket.timeout())):
            status = check_gateway(port=18789)

        assert status.ok is False
        assert status.state == GatewayState.TIMEOUT

    def test_returns_error_on_unexpected_exception(self):
        with patch("urllib.request.urlopen", side_effect=RuntimeError("unexpected")):
            status = check_gateway(port=18789)

        assert status.ok is False
        assert status.state == GatewayState.ERROR
