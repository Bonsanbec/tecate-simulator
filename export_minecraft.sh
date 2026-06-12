#!/bin/bash
# Activate virtual environment
source venv/bin/activate

# Set PYTHONPATH to the current directory
export PYTHONPATH=.

# Execute the minecraft exporter pipeline
./venv/bin/python -m src.minecraft_pipeline.exporter \
  --import-json export/reconstruction_export.json \
  --glb-path models/tecate/glb/tecate.glb \
  --output-dir export/minecraft_world
