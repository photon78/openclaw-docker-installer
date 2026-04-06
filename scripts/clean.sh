#!/usr/bin/env bash
# clean.sh — Remove OpenClaw installation for fresh re-test.
#
# Usage:
#   ./scripts/clean.sh                  # interactive, removes everything
#   ./scripts/clean.sh --yes            # non-interactive, removes everything
#   ./scripts/clean.sh --keep-image     # keeps Docker image (faster re-test)
#   ./scripts/clean.sh --yes --keep-image
set -euo pipefail

COMPOSE_FILE="${HOME}/.openclaw/docker-compose.yml"
OPENCLAW_DIR="${HOME}/.openclaw"
KEEP_IMAGE=false
SKIP_CONFIRM=false

# Parse args
for arg in "$@"; do
    case "${arg}" in
        --yes)         SKIP_CONFIRM=true ;;
        --keep-image)  KEEP_IMAGE=true ;;
    esac
done

# Confirmation
if [[ "${SKIP_CONFIRM}" != "true" ]]; then
    if [[ "${KEEP_IMAGE}" == "true" ]]; then
        msg="Remove OpenClaw container and config (image kept)?"
    else
        msg="Remove OpenClaw container, image and config?"
    fi
    read -rp "${msg} [y/N] " confirm
    [[ "${confirm}" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 0; }
fi

# Stop and remove container
if [[ -f "${COMPOSE_FILE}" ]]; then
    echo "→ Stopping container..."
    docker compose -f "${COMPOSE_FILE}" down --remove-orphans 2>/dev/null || true
else
    echo "→ No docker-compose.yml found, skipping container teardown."
fi

# Remove image (optional)
if [[ "${KEEP_IMAGE}" == "true" ]]; then
    echo "→ Keeping Docker image (--keep-image)."
else
    echo "→ Removing OpenClaw images..."
    docker images --format '{{.Repository}}:{{.Tag}}' \
        | grep 'ghcr.io/openclaw/openclaw' \
        | xargs -r docker rmi 2>/dev/null || true
fi

# Remove config
echo "→ Removing ${OPENCLAW_DIR}..."
rm -rf "${OPENCLAW_DIR}"

echo ""
if [[ "${KEEP_IMAGE}" == "true" ]]; then
    echo "✓ Clean (image cached). Run 'python src/main.py install' to start fresh."
else
    echo "✓ Clean. Run 'python src/main.py install' to start fresh."
fi
