import json
import os
import math

def inspect_blocks():
    reconstruction_path = "export/reconstruction_export.json"
    if not os.path.exists(reconstruction_path):
        print("Reconstruction export not found yet. Task is still running.")
        return
        
    with open(reconstruction_path, "r") as f:
        data = json.load(f)
        
    blocks = data.get("blocks", [])
    print(f"Total blocks extracted: {len(blocks)}")
    
    # Let's find block_19 and any other blocks near the target coordinates
    target_x = -69.1
    target_y = 28.3
    
    nearby_blocks = []
    for b in blocks:
        poly = b["polygon"]
        centroid = b["centroid"]
        dist = math.sqrt((centroid[0] - target_x)**2 + (centroid[1] - target_y)**2)
        nearby_blocks.append((b["block_id"], centroid, dist, len(poly)))
        
    nearby_blocks.sort(key=lambda x: x[2])
    print("\nClosest blocks to target:")
    for b_id, centroid, dist, num_verts in nearby_blocks[:10]:
        print(f"ID: {b_id}, Centroid: ({centroid[0]:.2f}, {centroid[1]:.2f}), Distance: {dist:.2f}m, Vertices: {num_verts}")

if __name__ == "__main__":
    inspect_blocks()
