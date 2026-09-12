#!/usr/bin/env python3
"""
gather_lingbot_map_dataset.py

Gathers all necessary panorama screenshots for Parque Hidalgo and all immediately
adjacent manzanas (blocks) into a dataset structured for 3D rebuilding with lingbot-map:
    lingbot-map/{block_id}/0001.png, 0002.png, ..., N.png

The script extracts block geometry and facade metadata from cache files, orders
the panoramas sequentially along each block's facade perimeter to form a right-cyclic
scan, and exports the dataset.
"""

import os
import sys
import json
import math
import shutil
import argparse
import subprocess

def load_env():
    """Loads environment variables from .env file if present."""
    env_paths = [".env", os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")]
    for path in env_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k, v = k.strip(), v.strip()
                            if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                                v = v[1:-1]
                            os.environ[k] = v
                break
            except Exception as e:
                print(f"[Warning] Error reading .env at {path}: {e}")

def poly_min_dist(poly1, poly2):
    """Computes minimum Euclidean distance between vertices of two 2D polygons."""
    min_d = float('inf')
    for p1 in poly1:
        for p2 in poly2:
            d = math.hypot(p1[0] - p2[0], p1[1] - p2[1])
            if d < min_d:
                min_d = d
    return min_d

def get_block_cyclic_panos(block_id, facades_data):
    """
    Extracts the sequence of panorama images for a block ordered by facade_index.
    Collapses consecutive duplicate camera perspectives to form a right-cyclic sequence.
    Returns list of dicts: [{'facade_index': idx, 'pano_id': pid, 'heading': hdg, 'img_name': img}]
    """
    prefix = f"{block_id}_facade_"
    keys = [k for k in facades_data if k.startswith(prefix)]
    keys.sort(key=lambda k: int(k.split("_facade_")[1]))

    raw_items = []
    for k in keys:
        fdata = facades_data[k]
        pid = fdata.get("pano_id")
        hdg = fdata.get("heading", 0.0)
        img_name = f"{pid}_yaw_{hdg:.2f}.png"
        raw_items.append({
            "facade_key": k,
            "facade_index": int(k.split("_facade_")[1]),
            "pano_id": pid,
            "heading": hdg,
            "img_name": img_name
        })

    if not raw_items:
        return []

    # Collapse consecutive identical images
    deduped = []
    for item in raw_items:
        if not deduped or deduped[-1]["img_name"] != item["img_name"]:
            deduped.append(item)

    # If first and last images are identical (loop boundary overlap), remove trailing duplicate
    if len(deduped) > 1 and deduped[0]["img_name"] == deduped[-1]["img_name"]:
        deduped.pop()

    return deduped

def main():
    load_env()

    parser = argparse.ArgumentParser(
        description="Gather Parque Hidalgo and adjacent block panoramas for lingbot-map 3D reconstruction."
    )
    parser.add_argument("--output-dir", default="lingbot-map",
                        help="Output directory for lingbot-map dataset.")
    parser.add_argument("--dist-threshold", type=float, default=35.0,
                        help="Max vertex distance (meters) to identify immediately adjacent blocks.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Run spatial analysis and print sequence counts without writing files.")

    args = parser.parse_args()

    blocks_cache_file = "data/blocks_cache.json"
    facades_cache_file = "data/facades_cache.json"
    panoramas_cache_file = "data/panoramas_cache.json"

    for fpath in [blocks_cache_file, facades_cache_file, panoramas_cache_file]:
        if not os.path.exists(fpath):
            print(f"[Error] Required cache file not found: {fpath}")
            sys.exit(1)

    print("============================================================")
    print("  GATHER LINGBOT-MAP DATASET: PARQUE HIDALGO & ADJACENT BLOCKS")
    print("============================================================")

    with open(blocks_cache_file, "r", encoding="utf-8") as f:
        blocks_data = json.load(f)
    with open(facades_cache_file, "r", encoding="utf-8") as f:
        facades_data = json.load(f)
    with open(panoramas_cache_file, "r", encoding="utf-8") as f:
        panoramas_data = json.load(f)

    # 1. Identify Parque Hidalgo block
    hidalgo_id = "block_lat_32.57293_lon_-116.62685"
    if hidalgo_id not in blocks_data:
        # Fallback to block closest to origin (0,0)
        min_d = float('inf')
        for bid, bdata in blocks_data.items():
            poly = bdata.get("polygon", [])
            if not poly:
                continue
            cx = sum(p[0] for p in poly) / len(poly)
            cy = sum(p[1] for p in poly) / len(poly)
            d = math.hypot(cx, cy)
            if d < min_d:
                min_d = d
                hidalgo_id = bid

    h_poly = blocks_data[hidalgo_id]["polygon"]
    h_cx = sum(p[0] for p in h_poly) / len(h_poly)
    h_cy = sum(p[1] for p in h_poly) / len(h_poly)

    print(f"[1/4] Parque Hidalgo block identified: {hidalgo_id}")
    print(f"      Centroid in local meters: ({h_cx:.2f}, {h_cy:.2f})")

    # 2. Find immediately adjacent blocks
    adjacent_blocks = []
    for bid, bdata in blocks_data.items():
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
        if min_d <= args.dist_threshold:
            adjacent_blocks.append((bid, min_d, bcx, bcy))

    adjacent_blocks.sort(key=lambda x: x[1])
    target_block_ids = [hidalgo_id] + [b[0] for b in adjacent_blocks]

    print(f"[2/4] Identified {len(adjacent_blocks)} immediately adjacent blocks (distance <= {args.dist_threshold}m).")
    print(f"      Total target blocks to process: {len(target_block_ids)}")

    # 3. Extract cyclic panorama sequences for each block
    block_sequences = {}
    all_required_files = set()

    for bid in target_block_ids:
        seq = get_block_cyclic_panos(bid, facades_data)
        block_sequences[bid] = seq
        for item in seq:
            all_required_files.add(f"data/screenshots/pano/{item['img_name']}")

    print(f"[3/4] Extracted panorama sequences for {len(block_sequences)} blocks.")
    print(f"      Total unique raw images required: {len(all_required_files)}")

    if args.dry_run:
        print("\n--- DRY RUN SUMMARY ---")
        for idx, bid in enumerate(target_block_ids, 1):
            lbl = "PARQUE HIDALGO" if bid == hidalgo_id else f"Adjacent block #{idx-1}"
            seq_len = len(block_sequences[bid])
            print(f"  [{idx:02d}/{len(target_block_ids)}] {bid} ({lbl}): {seq_len} right-cyclic panos")
        print("\nDry run completed. No files created.")
        return

    # 4. Check for missing / incomplete local screenshot files
    missing_files = []
    for fpath in sorted(list(all_required_files)):
        needs_fetch = False
        if not os.path.exists(fpath):
            needs_fetch = True
        else:
            if os.path.getsize(fpath) < 1000:  # LFS pointer or empty file
                needs_fetch = True
        if needs_fetch:
            missing_files.append(fpath)

    if missing_files:
        print(f"[Warning] {len(missing_files)} panorama images are missing or are Git LFS pointers locally in data/screenshots/pano/.")

    # 5. Export dataset to lingbot-map/{block_id}/0001.png, 0002.png, ..., N.png
    print(f"\n[4/4] Exporting dataset to '{args.output_dir}'...")
    os.makedirs(args.output_dir, exist_ok=True)

    manifest_blocks = {}
    total_exported_count = 0

    for idx, bid in enumerate(target_block_ids, 1):
        block_dir = os.path.join(args.output_dir, bid)
        os.makedirs(block_dir, exist_ok=True)
        seq = block_sequences[bid]
        
        exported_imgs = []
        for seq_idx, item in enumerate(seq, 1):
            src_img_name = item["img_name"]
            src_path = os.path.join("data/screenshots/pano", src_img_name)
            dst_filename = f"{seq_idx:04d}.png"
            dst_path = os.path.join(block_dir, dst_filename)

            if os.path.exists(src_path) and os.path.getsize(src_path) >= 1000:
                shutil.copy2(src_path, dst_path)
                exported_imgs.append({
                    "seq_num": dst_filename,
                    "pano_id": item["pano_id"],
                    "heading": item["heading"],
                    "source_image": src_img_name
                })
            else:
                print(f"[Warning] Source image missing/invalid: {src_path}")

        poly = blocks_data[bid]["polygon"]
        bcx = sum(p[0] for p in poly) / len(poly)
        bcy = sum(p[1] for p in poly) / len(poly)

        manifest_blocks[bid] = {
            "block_id": bid,
            "is_parque_hidalgo": (bid == hidalgo_id),
            "centroid_local": [round(bcx, 2), round(bcy, 2)],
            "pano_count": len(exported_imgs),
            "images": exported_imgs
        }

        total_exported_count += len(exported_imgs)
        lbl = "PARQUE HIDALGO" if bid == hidalgo_id else f"Adjacent block #{idx-1}"
        print(f"  [{idx:02d}/{len(target_block_ids)}] {bid} ({lbl}) -> Exported {len(exported_imgs)} panos (0001.png .. {len(exported_imgs):04d}.png)")

    manifest_path = os.path.join(args.output_dir, "dataset_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump({
            "target_blocks_count": len(target_block_ids),
            "total_exported_images": total_exported_count,
            "parque_hidalgo_block_id": hidalgo_id,
            "dist_threshold_meters": args.dist_threshold,
            "blocks": manifest_blocks
        }, f, indent=2)

    print("\n============================================================")
    print(f"  SUCCESS! Lingbot-Map dataset generated at: {os.path.abspath(args.output_dir)}")
    print(f"  Total target blocks: {len(target_block_ids)}")
    print(f"  Total exported panoramas: {total_exported_count}")
    print(f"  Manifest file: {manifest_path}")
    print("============================================================")

if __name__ == "__main__":
    main()
