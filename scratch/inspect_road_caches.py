import json
import os

print("Checking road metadata caches...")
if os.path.exists("data/road_metadata.json"):
    with open("data/road_metadata.json", "r") as f:
        rmeta = json.load(f)
    print("road_metadata.json count:", len(rmeta))
    k1 = list(rmeta.keys())[0]
    print("Sample road_metadata entry:", k1, rmeta[k1])

if os.path.exists("reconstruction_export.json"):
    with open("reconstruction_export.json", "r") as f:
        rexp = json.load(f)
    print("reconstruction_export.json keys:", list(rexp.keys()))

