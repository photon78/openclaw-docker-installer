"""
check_vllm_ready.py — Probe the local vLLM OpenAI-compatible endpoint.

Returns ready once /v1/models responds with HTTP 200 and contains at least
one model entry.
"""

from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass

DEFAULT_URL = "http://localhost:8000/v1/models"
TIMEOUT_SECONDS = 5


@dataclass
class VllmStatus:
    """Result of the vLLM readiness probe."""
    ready: bool
    model: str | None = None
    error: str | None = None


def check_vllm_ready(url: str = DEFAULT_URL, timeout: float = TIMEOUT_SECONDS) -> VllmStatus:
    """Probe the vLLM /v1/models endpoint.

    Returns ready=True if the endpoint is reachable and returns a non-empty
    list of models.
    """
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            if response.status != 200:
                return VllmStatus(
                    ready=False,
                    error=f"HTTP {response.status}",
                )
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        return VllmStatus(ready=False, error=f"Cannot reach vLLM: {exc}")
    except json.JSONDecodeError as exc:
        return VllmStatus(ready=False, error=f"Invalid JSON from vLLM: {exc}")
    except Exception as exc:  # pragma: no cover
        return VllmStatus(ready=False, error=f"Unexpected error: {exc}")

    models = data.get("data", []) if isinstance(data, dict) else data
    if not models:
        return VllmStatus(ready=False, error="vLLM returned no models")

    first_id = models[0].get("id") if isinstance(models[0], dict) else None
    return VllmStatus(ready=True, model=first_id)


if __name__ == "__main__":  # pragma: no cover
    status = check_vllm_ready()
    if status.ready:
        print(f"vLLM is ready — model: {status.model}")
    else:
        print(f"vLLM not ready: {status.error}")
        raise SystemExit(1)
