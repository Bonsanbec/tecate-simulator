import json
import os
import math

def main():
    blocks_path = "data/blocks_cache.json"
    facades_path = "data/facades_cache.json"
    panos_path = "data/panoramas_cache.json"

    with open(blocks_path, "r", encoding="utf-8") as f:
        blocks = json.load(f)
    with open(facades_path, "r", encoding="utf-8") as f:
        facades = json.load(f)
    with open(panos_path, "r", encoding="utf-8") as f:
        panos = json.load(f)

    print(f"Total blocks: {len(blocks)}")
    print(f"Total facades: {len(facades)}")
    print(f"Total panoramas: {len(panos)}")

    # 1. Identify Parque Hidalgo block
    # Hidalgo coords: 32.573229, -116.626536
    # In local meters, origin (0,0) is Parque Hidalgo!
    hidalgo_id = None
    min_dist = float('inf')
    for bid, bdata in blocks.items():
        poly = bdata.get("polygon", [])
        if not poly:
            continue
        cx = sum(p[0] for p in poly) / len(poly)
        cy = sum(p[1] for p in poly) / len(poly)
        d = math.hypot(cx, cy)
        if d < min_dist:
            min_dist = d
            hidalgo_id = bid

    print(f"\nParque Hidalgo block ID: {hidalgo_id} (centroid dist from origin: {min_dist:.2f}m)")

    # 2. Find immediately adjacent blocks
    h_poly = blocks[hidalgo_id]["polygon"]
    h_cx = sum(p[0] for p in h_poly) / len(h_poly)
    h_cy = sum(p[1] for p in h_poly) / len(h_poly)

    def poly_min_dist(poly1, poly2):
        min_d = float('inf')
        for p1 in poly1:
            for p2 in poly2:
                d = math.hypot(p1[0] - p2[0], p1[1] - p2[1])
                if d < min_d:
                    min_d = d
        return min_d

    block_distances = []
    for bid, bdata in blocks.items():
        if bid == hidalgo_id or bdata.get("is_external", False):
            continue
        poly = bdata.get("polygon", [])
        if not poly:
            continue
        bcx = sum(p[0] for p in poly) / len(poly)
        bcy = sum(p[1] for p in poly) / len(poly)
        center_dist = math.hypot(bcx - h_cx, bcy - h_cy)
        if center_dist > 300:
            continue
        min_v_dist = poly_min_dist(h_poly, poly)
        block_distances.append((bid, min_v_dist, center_dist, bcx, bcy))

    block_distances.sort(key=lambda x: x[1])

    adjacent_blocks = [b for b in block_distances if b[1] < 45.0]
    print(f"\nFound {len(adjacent_blocks)} immediately adjacent blocks (min vertex dist < 45m):")
    for bid, min_d, c_d, bcx, bcy in adjacent_blocks:
        print(f"  Block: {bid} | Min Vert Dist: {min_d:.2f}m | Centroid Dist: {c_d:.2f}m | Center: ({bcx:.1f}, {bcy:.1f})")

    target_blocks = [hidalgo_id] + [b[0] for b in adjacent_blocks]
    print(f"\nTotal target blocks (Hidalgo + adjacent): {len(target_blocks)}")

    for bid in target_blocks:
        block_facades = []
        for fid, fdata in facades.items():
            if fdata.get("block_id") == bid:
                block_facades.append((fid, fdata))
        
        block_facades.sort(key=lambda x: x[1].get("facade_index", 0))
        print(f"\n--- Block {bid} ---")
        print(f"  Total facades in facades_cache: {len(block_facades)}")
        if block_facades:
            print("  First 3 facades:")
            for fid, fdata in block_facades[:3]:
                p_id = fdata.get("pano_id")
                hdg = fdata.get("heading")
                mid = fdata.get("facade_midpoint_local")
                idx = fdata.get("facade_index")
                print(f"    idx={idx}: fid={fid}, pano_id={p_id}, heading={hdg}, mid={mid}")

if __name__ == "__main__":
    main()
