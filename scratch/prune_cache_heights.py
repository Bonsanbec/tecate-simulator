import json
import os

cache_path = "data/blocks_cache.json"
if os.path.exists(cache_path):
    with open(cache_path, "r") as f:
        cache = json.load(f)
    
    count = 0
    for b_id, b_data in cache.items():
        if "height_meters" in b_data:
            del b_data["height_meters"]
            count += 1
            
    with open(cache_path, "w") as f:
        json.dump(cache, f, indent=4)
        
    print(f"Successfully pruned legacy heights from {count} blocks in blocks_cache.json!")
else:
    print("blocks_cache.json not found.")
