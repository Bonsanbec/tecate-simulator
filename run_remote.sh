#!/usr/bin/env bash

# run_remote.sh
# Usage: ./run_remote.sh [REMOTE_SSH_HOST]
# Default host: HakkinDavid@hakkin.tail4b53f5.ts.net

set -euo pipefail

# 1. Determine remote host
REMOTE_HOST="${1:-HakkinDavid@hakkin.tail4b53f5.ts.net}"
REMOTE_PATH="~/tecate-simulator"

echo "============================================================"
echo "  Executing remote WSL pipeline run.sh                       "
echo "  Remote Host: ${REMOTE_HOST}                               "
echo "  Remote Path: ${REMOTE_PATH}                               "
echo "============================================================"

# 2. Execute the remote script with pseudo-terminal allocation
# The -t option allocates a pseudo-terminal, forwarding signals (Ctrl+C, etc.)
ssh -t "${REMOTE_HOST}" "wsl bash -c \"cd ${REMOTE_PATH} && ./run.sh\""
