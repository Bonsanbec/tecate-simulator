import json

with open("data/blocks_cache.json", "r") as f:
    blocks = json.load(f)

# Find Parque Hidalgo block (block_lat_32.57293_lon_-116.62685)
bid = "block_lat_32.57293_lon_-116.62685"
if bid in blocks:
    poly = blocks[bid]["polygon"]
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    cx = sum(xs) / len(xs)
    cy = sum(ys) / len(ys)
    print(f"Parque Hidalgo block '{bid}':")
    print(f"  Centroid Local X: {cx:.2f}, Local Y: {cy:.2f}")
    print(f"  Godot 3D Position: X = {cx:.2f}, Z = {-cy:.2f}")

# Also find overall city center across all blocks
all_xs = []
all_ys = []
for bdata in blocks.values():
    for p in bdata["polygon"]:
        all_xs.append(p[0])
        all_ys.append(p[1])

print(f"\nOverall Tecate City Center across all 4,239 blocks:")
print(f"  Centroid Local X: {(min(all_xs)+max(all_xs))/2:.2f}, Local Y: {(min(all_ys)+max(all_ys))/2:.2f}")
print(f"  Godot 3D Position: X = {(min(all_xs)+max(all_xs))/2:.2f}, Z = {-(min(all_ys)+max(all_ys))/2:.2f}")

