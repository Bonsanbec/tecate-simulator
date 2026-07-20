import json
import os

print("--- Inspecting blocks_cache.json ---")
if os.path.exists("data/blocks_cache.json"):
    with open("data/blocks_cache.json", "r") as f:
        data = json.load(f)
    print("Type:", type(data))
    if isinstance(data, dict):
        print("Keys:", list(data.keys())[:10])
        first_key = list(data.keys())[0]
        print(f"Sample key '{first_key}':", type(data[first_key]))
        if isinstance(data[first_key], dict):
            print("  Sample dict keys:", list(data[first_key].keys())[:10])
        elif isinstance(data[first_key], list):
            print("  Sample list len:", len(data[first_key]))
            if len(data[first_key]) > 0:
                print("  Sample item:", data[first_key][0])
    elif isinstance(data, list):
        print("Length:", len(data))
        if len(data) > 0:
            print("Sample item 0 keys:", list(data[0].keys()) if isinstance(data[0], dict) else type(data[0]))

print("\n--- Inspecting tecate_osm_cache.json ---")
if os.path.exists("data/tecate_osm_cache.json"):
    with open("data/tecate_osm_cache.json", "r") as f:
        data_osm = json.load(f)
    print("Type:", type(data_osm))
    if isinstance(data_osm, dict):
        print("Keys:", list(data_osm.keys())[:10])
    elif isinstance(data_osm, list):
        print("Length:", len(data_osm))
