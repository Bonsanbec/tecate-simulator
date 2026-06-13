#!/bin/bash
# Exit on error
set -e

# Change directory to the root of the project
cd "$(dirname "$0")"

# Activate python virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

echo "Running Minecraft Exporter Pipeline..."
echo ""

PYTHONPATH=. python3 -m src.minecraft_pipeline.exporter

echo ""
echo "Pipeline execution finished successfully!"
