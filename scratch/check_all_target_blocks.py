import json
import math
import os
import subprocess

def poly_min_dist(poly1, poly2):
    min_d = float('inf')
    for p1 in poly1:
        for p2 in poly2:
            d = math.hypot(p1[0] - p2[0], p1[1] - p2[1])
            if d < min_d:
                min_d = d
    return min_d

def main():
    with open("data/blocks_cache.json", "r") as f:
        blocks = json.load(f)
    with open("data/facades_cache.json", "r") as f:
        facades = json.load(f)

    # 1. Identify Parque Hidalgo block
    hidalgo_id = "block_lat_32.57293_lon_-116.62685"
    if hidalgo_id not in blocks:
        # Fallback to closest block to origin (0,0)
        min_d = float('inf')
        for bid, bdata in blocks.items():
            poly = bdata["polygon"]
            cx = sum(p[0] for p in poly) / len(poly)
            cy = sum(p[1] for p in poly) / len(poly)
            d = math.hypot(cx, cy)
            if d < min_d:
                min_d = d
                hidalgo_id = bid

    h_poly = blocks[hidalgo_id]["polygon"]
    h_cx = sum(p[0] for p in h_poly) / len(h_poly)
    h_cy = sum(p[1] for p in h_poly) / len(h_poly)

    print(f"Parque Hidalgo block ID: {hidalgo_id}")
    print(f"Parque Hidalgo centroid: ({h_cx:.1f}, {h_cy:.1f})")

    # 2. Find immediately adjacent blocks
    # Immediately adjacent manzanas share a street or border (min vertex distance <= 35m)
    adjacent_blocks = []
    for bid, bdata in blocks.items():
        if bid == hidalgo_id or bdata.get("is_external", False):
            continue
        poly = bdata.get("polygon", [])
        if not poly:
            continue
        bcx = sum(p[0] for p in poly) / len(poly)
        bcy = sum(p[1] for p in poly) / len(poly)
        if math.hypot(bcx - h_cx, bcy - h_cy) > 250:
            continue
        min_d = poly_min_dist(h_poly, poly)
        if min_d <= 35.0:
            adjacent_blocks.append((bid, min_d, bcx, bcy))

    adjacent_blocks.sort(key=lambda x: x[1])

    target_block_ids = [hidalgo_id] + [b[0] for b in adjacent_blocks]
    print(f"\nTotal target blocks (Hidalgo + {len(adjacent_blocks)} adjacent): {len(target_block_ids)}")

    total_images_needed = set()

    for idx, bid in enumerate(target_block_ids):
        prefix = f"{bid}_facade_"
        facade_keys = [k for k in facades if k.startswith(prefix)]
        facade_keys.sort(key=lambda k: int(k.split("_facade_")[1]))

        raw_imgs = []
        for k in facade_keys:
            fdata = facades[k]
            pid = fdata.get("pano_id")
            hdg = fdata.get("heading", 0.0)
            img_name = f"{pid}_yaw_{hdg:.2f}.png"
            raw_imgs.append(img_name)

        dedup_imgs = []
        for img in raw_imgs:
            if not dedup_imgs or dedup_imgs[-1] != img:
                dedup_imgs.append(img)
        if len(dedup_imgs) > 1 and dedup_imgs[0] == dedup_imgs[-1]:
            dedup_imgs.pop()

        for img in dedup_imgs:
            total_images_needed.add(img)

        label = "PARQUE HIDALGO" if bid == hidalgo_id else f"Adjacent block {idx}"
        print(f"[{idx+1:02d}/{len(target_block_ids)}] {bid} ({label})")
        print(f"     Facades: {len(facade_keys)} | Deduped panos: {len(dedup_imgs)}")

    print(f"\nTotal unique panorama screenshots needed across all {len(target_block_ids)} blocks: {len(total_images_needed)}")

if __name__ == "__main__":
    main()
