# Environment Setup and Verification

This document describes the verified environment for running the Tecate 2009 historical urban reconstruction pipeline.

## System Configuration
- **Operating System**: macOS (darwin arm64)
- **Python Version**: 3.14.5

## Core Python Dependencies
The following dependencies have been verified to import and execute correctly:
- `numpy`
- `opencv-python` (cv2)
- `networkx`
- `pillow` (PIL)
- `requests`
- `pytest`
- `playwright`
- `py360convert`

## Setup Instructions
1. Create and activate virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the unit test suite:
   ```bash
   PYTHONPATH=. pytest tests/unit/
   ```
