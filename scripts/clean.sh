#!/usr/bin/env bash
# clean.sh — Remove OpenClaw Docker installation for fresh re-test.
# Usage: ./scripts/clean.sh [--yes]
set -euo pipefail

COMPOSE_FILE="${HOME}/.openclaw/docker-compose.yml"
OPENCLAW_DIR="${HOME}/.openclaw"

# Confirmation unless --yes passed
if [[ "${1:-}" != "--yes" ]]; then
    read -rp "Remove OpenClaw container, image and config in ${OPENCLAW_DIR}? [y/N] " confirm
    [[ "${confirm}" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 0; }
fi

# Stop and remove container
if [[ -f "${COMPOSE_FILE}" ]]; then
    echo "→ Stopping container..."
    docker compose -f "${COMPOSE_FILE}" down --remove-orphans 2>/dev/null || true
else
    echo "→ No docker-compose.yml found, skipping container teardown."
fi

# Remove image (all openclaw tags)
echo "→ Removing OpenClaw images..."
docker images --format '{{.Repository}}:{{.Tag}}' \
    | grep 'ghcr.io/openclaw/openclaw' \
    | xargs -r docker rmi 2>/dev/null || true

# Remove config
echo "→ Removing ${OPENCLAW_DIR}..."
rm -rf "${OPENCLAW_DIR}"

echo ""
echo "✓ Clean. Run 'python src/main.py install' to start fresh."
