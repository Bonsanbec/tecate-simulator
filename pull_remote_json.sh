#!/usr/bin/env bash

# pull_remote_json.sh
# Usage: ./pull_remote_json.sh [REMOTE_SSH_HOST]
# Default host: HakkinDavid@hakkin.tail4b53f5.ts.net

set -euo pipefail

# Load environment variables from .env if it exists
if [ -f .env ]; then
    # Ignore comments, empty lines, and handle Windows CR line endings gracefully
    export $(cat .env | grep -v '^#' | sed 's/\r$//' | xargs)
fi

# 1. Determine remote host
REMOTE_HOST="${1:-${REMOTE_HOST:-HakkinDavid@hakkin.tail4b53f5.ts.net}}"
REMOTE_PATH="${REMOTE_PATH:-~/tecate-simulator}"

echo "============================================================"
echo "  Pulling JSON files from remote WSL instance to local       "
echo "  Remote Host: ${REMOTE_HOST}                               "
echo "  Remote Path: ${REMOTE_PATH}                               "
echo "============================================================"

# 2. Verify SSH connection
echo "[1/3] Testing SSH connection to ${REMOTE_HOST}..."
if ! ssh -o ConnectTimeout=5 "${REMOTE_HOST}" "echo 'SSH connection verified.'" >/dev/null 2>&1; then
    echo "Error: Cannot connect to remote server ${REMOTE_HOST} via SSH."
    echo "Please ensure Tailscale is active and you are authenticated."
    exit 1
fi

# 3. Stream and extract JSON files
echo "[2/3] Fetching recursive JSON files from remote WSL (excluding venv, .git, etc.)..."
# Exclude: venv, .venv, .git, .pytest_cache, __pycache__
FIND_CMD="cd ${REMOTE_PATH} && find . -type d \( -name '.git' -o -name 'venv' -o -name '.venv' -o -name '.pytest_cache' -o -name '__pycache__' \) -prune -o -name '*.json' -type f -print0 | xargs -0 tar -czf -"

if ssh "${REMOTE_HOST}" "wsl bash -c \"${FIND_CMD}\"" | tar -xzvf -; then
    echo "[3/3] Sync complete! All JSON files downloaded successfully."
else
    echo "Error: Failed to fetch JSON files."
    exit 1
fi
echo "============================================================"
