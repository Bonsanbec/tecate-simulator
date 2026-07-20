#!/usr/bin/env python3
import json
import os

def generate_manifest():
    print("=" * 60)
    print("  STEP 3: GENERATE MANZANA METADATA & IN-GAME TAGS PIPELINE")
    print("=" * 60)

    mapping_file = "data/building_manzana_mapping.json"
    blocks_cache_file = "data/blocks_cache.json"
    output_manifest = "godot_project/assets/blocks/manzana_manifest.json"

    if not os.path.exists(mapping_file):
        print(f"Error: {mapping_file} not found! Run Step 1 first.")
        return

    with open(mapping_file, "r") as f:
        mapping_data = json.load(f)

    blocks_cache = {}
    if os.path.exists(blocks_cache_file):
        with open(blocks_cache_file, "r") as f:
            blocks_cache = json.load(f)

    manzanas_map = mapping_data.get("manzanas", {})
    manifest = {}

    total_tags = 0

    for manzana_id, buildings in manzanas_map.items():
        # Parse lat/lon from manzana_id e.g. block_lat_32.56181_lon_-116.57077
        parts = manzana_id.split("_")
        lat = float(parts[2]) if len(parts) > 2 else 0.0
        lon = float(parts[4]) if len(parts) > 4 else 0.0

        # Calculate manzana centroid
        if buildings:
            m_cx = sum(b["centroid"][0] for b in buildings) / len(buildings)
            m_cy = sum(b["centroid"][1] for b in buildings) / len(buildings)
            m_cz = sum(b["centroid"][2] for b in buildings) / len(buildings)
        else:
            m_cx = m_cy = m_cz = 0.0

        building_tags = []
        for b in buildings:
            b_name = b["building_name"]
            centroid = b["centroid"] # [x, y, z_min]
            height = b["height"]
            
            # Position tag slightly above the building roof
            tag_pos = [centroid[0], centroid[2] + height + 1.5, -centroid[1]] # Converting to Godot coordinates (X, Y=Height, Z=-Y_local)
            
            tag_label = b_name
            # If building has a nice material or custom name, format tag nicely
            materials = b.get("materials", [])
            mat_str = ", ".join(materials) if materials else "Building"
            
            building_tags.append({
                "building_name": b_name,
                "label": tag_label,
                "type": mat_str,
                "height_m": height,
                "tag_position": tag_pos
            })
            total_tags += 1

        rel_gltf_path = f"res://assets/blocks/manzanas/{manzana_id}.gltf"

        manifest[manzana_id] = {
            "gltf_path": rel_gltf_path,
            "lat": lat,
            "lon": lon,
            "centroid": [m_cx, m_cy, m_cz],
            "building_count": len(buildings),
            "buildings": building_tags
        }

    os.makedirs(os.path.dirname(output_manifest), exist_ok=True)
    with open(output_manifest, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"Manifest generated successfully!")
    print(f"  Total Manzanas: {len(manifest)}")
    print(f"  Total Building Tags: {total_tags}")
    print(f"  Output path: {output_manifest}")
    print("=" * 60)

if __name__ == "__main__":
    generate_manifest()
