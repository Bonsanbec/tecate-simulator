#!/usr/bin/env bash

# run_remote.sh
# Usage: ./run_remote.sh [REMOTE_SSH_HOST]
# Default host: HakkinDavid@hakkin.tail4b53f5.ts.net

set -euo pipefail

# Load environment variables from .env if it exists
if [ -f .env ]; then
    while IFS= read -r line || [ -n "$line" ]; do
        if [[ ! "$line" =~ ^# ]] && [[ ! "$line" =~ ^[[:space:]]*$ ]]; then
            line="${line%$'\r'}"
            export "$line"
        fi
    done < .env
fi

# 1. Determine remote host and arguments
REMOTE_HOST="${REMOTE_HOST:-HakkinDavid@hakkin.tail4b53f5.ts.net}"
if [[ "${1:-}" == *@* || "${1:-}" == *.ts.net* ]]; then
    REMOTE_HOST="$1"
    shift
fi

REMOTE_PATH="${REMOTE_PATH:-~/tecate-simulator}"
ARGS=("$@")

echo "============================================================"
echo "  Executing remote WSL pipeline run.sh                       "
echo "  Remote Host: ${REMOTE_HOST}                               "
echo "  Remote Path: ${REMOTE_PATH}                               "
if [ ${#ARGS[@]} -gt 0 ]; then
echo "  Arguments:   ${ARGS[*]}                                    "
fi
echo "============================================================"

# 2. Execute the remote script with pseudo-terminal allocation
# The -t option allocates a pseudo-terminal, forwarding signals (Ctrl+C, etc.)
ssh -t "${REMOTE_HOST}" "wsl bash -c \"cd ${REMOTE_PATH} && ./run.sh ${ARGS[*]:-}\""
