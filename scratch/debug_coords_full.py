import json
import os
import sys
import math

# 1. Inspect blocks_cache.json coordinates
with open("data/blocks_cache.json", "r") as f:
    blocks = json.load(f)

print("--- BLOCKS_CACHE.JSON ---")
all_xs = []
all_ys = []
for bid, bdata in blocks.items():
    for p in bdata["polygon"]:
        all_xs.append(p[0])
        all_ys.append(p[1])

print(f"Blocks Cache count: {len(blocks)}")
print(f"  X range: [{min(all_xs):.2f}, {max(all_xs):.2f}] -> Center X = {(min(all_xs)+max(all_xs))/2:.2f}")
print(f"  Y range: [{min(all_ys):.2f}, {max(all_ys):.2f}] -> Center Y = {(min(all_ys)+max(all_ys))/2:.2f}")

# Find Parque Hidalgo block
parque_block = "block_lat_32.57293_lon_-116.62685"
if parque_block in blocks:
    pxs = [p[0] for p in blocks[parque_block]["polygon"]]
    pys = [p[1] for p in blocks[parque_block]["polygon"]]
    print(f"\nParque Hidalgo Block ({parque_block}):")
    print(f"  Polygon X range: [{min(pxs):.2f}, {max(pxs):.2f}]")
    print(f"  Polygon Y range: [{min(pys):.2f}, {max(pys):.2f}]")

# 2. Inspect building_manzana_mapping.json
mapping_file = "data/building_manzana_mapping.json"
if os.path.exists(mapping_file):
    with open(mapping_file, "r") as f:
        mapping = json.load(f)
    print("\n--- BUILDING MANZANA MAPPING ---")
    m_buildings = mapping.get("manzanas", {}).get(parque_block, [])
    print(f"Buildings mapped to Parque Hidalgo block: {len(m_buildings)}")
    for b in m_buildings:
        print(" ", b["building_name"], "centroid:", b["centroid"])

