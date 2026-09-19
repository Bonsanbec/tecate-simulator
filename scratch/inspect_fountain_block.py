import json

with open("scratch/cache/blocks_cache.json", "r") as f:
    blocks = json.load(f)

b_id = "block_lat_32.57293_lon_-116.62685"
if b_id in blocks:
    print(f"Data for {b_id}:")
    data = blocks[b_id]
    for k, v in data.items():
        if k != "polygon":
            print(f"  {k}: {v}")
        else:
            print(f"  polygon ({len(v)} points): {v}")

with open("scratch/cache/facades_cache.json", "r") as f:
    facades = json.load(f)

matching = {k: v for k, v in facades.items() if b_id in k}
print(f"\nMatching facades for {b_id}: {len(matching)}")
for k, v in list(matching.items())[:10]:
    print(k, v)
