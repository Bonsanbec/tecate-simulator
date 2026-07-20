import json
import math
import sys
import os

sys.path.append(os.path.abspath("scripts"))
from spatial import gps_to_local, gps_to_minecraft_3d

# Parque Hidalgo (Center of Tecate)
lat = 32.573229
lon = -116.626536

x_local, y_local = gps_to_local(lat, lon)
x_mc, y_mc, z_mc = gps_to_minecraft_3d(lat, lon, 523)

print("Parque Hidalgo GPS (32.573229, -116.626536):")
print(f"  x_local = {x_local:.2f}, y_local = {y_local:.2f}")
print(f"  Minecraft 3D: x = {x_mc}, y = {y_mc}, z = {z_mc}")

# Find closest block in blocks_cache.json
with open("data/blocks_cache.json", "r") as f:
    blocks = json.load(f)

best_block_id = None
best_dist = float('inf')

for block_id, block_data in blocks.items():
    poly = block_data["polygon"]
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    cx = (min(xs) + max(xs)) / 2.0
    cy = (min(ys) + max(ys)) / 2.0
    
    dist = math.hypot(cx - x_local, cy - y_local)
    if dist < best_dist:
        best_dist = dist
        best_block_id = block_id

print(f"\nClosest Manzana block to Parque Hidalgo:")
print(f"  ID: {best_block_id}")
print(f"  Distance: {best_dist:.2f}m")
print(f"  Block Polygon bounds: X=[{min(p[0] for p in blocks[best_block_id]['polygon']):.2f}, {max(p[0] for p in blocks[best_block_id]['polygon']):.2f}], Y=[{min(p[1] for p in blocks[best_block_id]['polygon']):.2f}, {max(p[1] for p in blocks[best_block_id]['polygon']):.2f}]")

# Check if this block is in manzana_manifest.json
manifest_path = "godot_project/assets/blocks/manzana_manifest.json"
if os.path.exists(manifest_path):
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
    print(f"\nIs {best_block_id} in manzana_manifest.json?")
    if best_block_id in manifest:
        print("YES!", json.dumps(manifest[best_block_id], indent=2))
    else:
        print("NO!")

