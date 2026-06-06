#!/bin/bash
# Run pipeline for target case study block using a small radius of 120 meters from Parque Hidalgo
echo "[run_case_study] Running Tecate Simulator Facade MVP pipeline..."
PYTHONPATH=. venv/bin/python src/main.py --skip-scraper --radius 150 --reprocess
