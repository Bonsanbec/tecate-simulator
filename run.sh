#!/usr/bin/env bash

# Resolve the correct Python interpreter to use
PYTHON_CMD="python3"
if [ -f "./venv/bin/python" ]; then
    if ./venv/bin/python -c "import sys" &>/dev/null; then
        PYTHON_CMD="./venv/bin/python"
    else
        echo "[run.sh] ./venv/bin/python is not compatible with this environment. Trying system python3..."
    fi
elif [ -f "./.venv/bin/python" ]; then
    if ./.venv/bin/python -c "import sys" &>/dev/null; then
        PYTHON_CMD="./.venv/bin/python"
    fi
fi

# Collect arguments, default to --headless if none are provided
ARGS=("$@")
if [ ${#ARGS[@]} -eq 0 ]; then
    ARGS=("--headless")
fi

echo "===== USING PYTHON INTERPRETER: $PYTHON_CMD ====="

while true; do
    echo "===== STARTING CRAWLER ====="

    PYTHONPATH=. "$PYTHON_CMD" src/main.py "${ARGS[@]}"

    echo "===== CRAWLER FINISHED ====="

    rm tecate_reconstruction.blend1

    git add .

    git commit -m "Incremental Street View archival $(date)" || true

    git push origin master

    echo "===== SLEEPING ====="

    sleep 1
done