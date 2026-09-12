import json
import math

def main():
    with open("data/blocks_cache.json", "r") as f:
        blocks = json.load(f)
    with open("data/facades_cache.json", "r") as f:
        facades = json.load(f)
    with open("data/panoramas_cache.json", "r") as f:
        panos = json.load(f)

    hidalgo_id = "block_lat_32.57293_lon_-116.62685"
    h_poly = blocks[hidalgo_id]["polygon"]
    h_cx = sum(p[0] for p in h_poly) / len(h_poly)
    h_cy = sum(p[1] for p in h_poly) / len(h_poly)

    print(f"Parque Hidalgo ({hidalgo_id}): Polygon vertices count: {len(h_poly)}")

    # Facades for Hidalgo
    h_facade_keys = [k for k in facades if k.startswith(hidalgo_id + "_facade_")]
    # Extract integer index
    h_facade_keys.sort(key=lambda k: int(k.split("_facade_")[1]))
    print(f"Total facade keys for Parque Hidalgo: {len(h_facade_keys)}")

    print("\nFirst 5 facades for Parque Hidalgo:")
    for k in h_facade_keys[:5]:
        idx = int(k.split("_facade_")[1])
        fdata = facades[k]
        pid = fdata["pano_id"]
        hdg = fdata["heading"]
        img_name = f"{pid}_yaw_{hdg:.2f}.png"
        print(f"  facade index {idx:04d}: key={k}, img={img_name}, heading={hdg:.2f}")

    # Check image filename pattern: pano_id_yaw_heading.2f.png
    # Let's check how many images actually exist on remote WSL or if we can query them!

if __name__ == "__main__":
    main()
