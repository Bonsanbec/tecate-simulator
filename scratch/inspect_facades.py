import json

def main():
    with open("data/facades_cache.json", "r") as f:
        facades = json.load(f)
    
    print(f"Total facades: {len(facades)}")
    sample_keys = list(facades.keys())[:10]
    print("Sample facade keys:")
    for k in sample_keys:
        print(" ", k)
        print("   block_id field:", facades[k].get("block_id"))

    # Search for keys containing '32.57293' or '116.62' or 'block_lat_32.57'
    matching_keys = [k for k in facades if "32.57293" in k or "32.57" in k]
    print(f"\nMatching keys for '32.57': {len(matching_keys)}")
    for k in matching_keys[:10]:
        print(" ", k, "-> block_id:", facades[k].get("block_id"))

if __name__ == "__main__":
    main()
