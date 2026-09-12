import json

def main():
    with open("data/blocks_cache.json", "r") as f:
        blocks = json.load(f)
    with open("data/facades_cache.json", "r") as f:
        facades = json.load(f)
    with open("data/panoramas_cache.json", "r") as f:
        panos = json.load(f)

    # Find blocks near center (0,0)
    print("--- Blocks near local origin (0,0) ---")
    hidalgo_candidates = []
    for bid, bdata in blocks.items():
        poly = bdata["polygon"]
        cx = sum(p[0] for p in poly) / len(poly)
        cy = sum(p[1] for p in poly) / len(poly)
        if abs(cx) < 150 and abs(cy) < 150:
            hidalgo_candidates.append((bid, cx, cy, len(poly)))
            print(f"  {bid} | Center: ({cx:.1f}, {cy:.1f}) | Vertices: {len(poly)}")

    # Check facades for one candidate block
    first_bid = hidalgo_candidates[0][0]
    print(f"\n--- Facades for {first_bid} ---")
    matching_facades = [k for k in facades if k.startswith(first_bid + "_facade_")]
    print(f"Total matching facades: {len(matching_facades)}")

    if matching_facades:
        sample_f = facades[matching_facades[0]]
        print("Sample facade dict keys:", list(sample_f.keys()))
        print("Sample facade details:", json.dumps(sample_f, indent=2))
        pano_id = sample_f.get("pano_id")
        if pano_id in panos:
            print(f"\nPano details for {pano_id}:", json.dumps(panos[pano_id], indent=2))
        else:
            print(f"\nPano {pano_id} NOT found in panoramas_cache.json!")

if __name__ == "__main__":
    main()
