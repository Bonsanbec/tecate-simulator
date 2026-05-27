import os
import json

def ensure_dir(path: str):
    """Ensures that a directory exists, creating it if necessary."""
    os.makedirs(path, exist_ok=True)

def save_json(data: dict, filepath: str):
    """Saves a dictionary as a formatted JSON file."""
    dirpath = os.path.dirname(filepath)
    if dirpath:
        ensure_dir(dirpath)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def load_json(filepath: str) -> dict:
    """Loads a JSON file as a dictionary."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)
