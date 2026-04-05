#!/usr/bin/env python3
"""
openclaw-docker-installer — entry point.

Prototype: runs Docker and Gateway checks, prints results.
TUI wizard comes in a later feature branch.
"""

import sys

from checks.docker_check import check_docker
from checks.gateway_check import check_gateway, DEFAULT_PORT


def main() -> int:
    """Run pre-flight checks and report results.

    Returns exit code: 0 = all ok, 1 = check failed.
    """
    print("openclaw-docker-installer — pre-flight check\n")

    # Docker check
    docker = check_docker()
    if docker.ready:
        print(f"[OK] Docker {docker.version} is ready.")
    else:
        print(f"[FAIL] Docker check failed.")
        if docker.error:
            print(f"       {docker.error}")
        return 1

    # Gateway check (only relevant after installation)
    gateway = check_gateway(port=DEFAULT_PORT)
    if gateway.ok:
        print(f"[OK] Gateway is reachable on port {gateway.port}.")
    else:
        # Not a hard failure at this stage — gateway may not be installed yet
        print(f"[INFO] Gateway: {gateway.message}")

    print("\nAll checks passed. Ready to proceed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
