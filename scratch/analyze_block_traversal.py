import json
import math

def get_block_facade_images(block_id, facades_dict, deduplicate_consecutive=True):
    # Find all facade keys for this block
    prefix = f"{block_id}_facade_"
    matching_keys = [k for k in facades_dict if k.startswith(prefix)]
    # Sort by facade index
    matching_keys.sort(key=lambda k: int(k.split("_facade_")[1]))
    
    raw_images = []
    for k in matching_keys:
        fdata = facades_dict[k]
        pid = fdata.get("pano_id")
        hdg = fdata.get("heading", 0.0)
        img_name = f"{pid}_yaw_{hdg:.2f}.png"
        raw_images.append({
            "facade_key": k,
            "facade_idx": int(k.split("_facade_")[1]),
            "pano_id": pid,
            "heading": hdg,
            "img_name": img_name
        })

    if not deduplicate_consecutive:
        return raw_images

    # Deduplicate consecutive identical images in sequence
    deduped = []
    for item in raw_images:
        if not deduped or deduped[-1]["img_name"] != item["img_name"]:
            deduped.append(item)
            
    # Check if first and last are identical (loop wrap-around)
    if len(deduped) > 1 and deduped[0]["img_name"] == deduped[-1]["img_name"]:
        deduped.pop()

    return deduped

def main():
    with open("data/blocks_cache.json", "r") as f:
        blocks = json.load(f)
    with open("data/facades_cache.json", "r") as f:
        facades = json.load(f)

    hidalgo_id = "block_lat_32.57293_lon_-116.62685"
    
    raw = get_block_facade_images(hidalgo_id, facades, deduplicate_consecutive=False)
    dedup = get_block_facade_images(hidalgo_id, facades, deduplicate_consecutive=True)

    print(f"Parque Hidalgo ({hidalgo_id}):")
    print(f"  Raw facade segments: {len(raw)}")
    print(f"  Deduped consecutive images sequence length: {len(dedup)}")
    print("\nDeduped sequence:")
    for i, item in enumerate(dedup, 1):
        print(f"  {i:04d}.png <- {item['img_name']} (from facade_idx {item['facade_idx']})")

if __name__ == "__main__":
    main()
