#!/usr/bin/env python3
import json
import os

def generate_manifest():
    print("=" * 60)
    print("  STEP 4: GENERATE MANZANA METADATA & PER-BUILDING LABELS PIPELINE")
    print("=" * 60)

    mapping_file = "data/building_manzana_mapping.json"
    output_manifest = "godot_project/assets/blocks/manzana_manifest.json"

    if not os.path.exists(mapping_file):
        print(f"Error: {mapping_file} not found! Run Step 1 first.")
        return

    with open(mapping_file, "r") as f:
        mapping_data = json.load(f)

    manzanas_map = mapping_data.get("manzanas", {})
    manifest = {}

    total_building_labels = 0

    for manzana_id, b_primitives in manzanas_map.items():
        parts = manzana_id.split("_")
        lat = float(parts[2]) if len(parts) > 2 else 0.0
        lon = float(parts[4]) if len(parts) > 4 else 0.0

        if not b_primitives:
            continue

        # Group primitives by horizontal spatial proximity to identify distinct physical buildings
        building_groups = []
        for prim in b_primitives:
            cx, cy, cz = prim["centroid"]
            h = prim["height"]
            street = prim.get("street_name", "Tecate")
            
            # Check if this primitive belongs to an existing building group in this manzana
            assigned = False
            for bg in building_groups:
                bg_cx, bg_cy = bg["cx"], bg["cy"]
                if math.hypot(cx - bg_cx, cy - bg_cy) < 15.0:  # Within 15m radius is same building entity
                    bg["primitives"].append(prim)
                    bg["max_h"] = max(bg["max_h"], h)
                    bg["max_z"] = max(bg["max_z"], cz + h)
                    assigned = True
                    break
            
            if not assigned:
                building_groups.append({
                    "cx": cx,
                    "cy": cy,
                    "min_z": cz,
                    "max_h": h,
                    "max_z": cz + h,
                    "street": street,
                    "primitives": [prim]
                })

        building_tags = []
        for idx, bg in enumerate(building_groups, 1):
            bg_cx = bg["cx"]
            bg_cy = bg["cy"]
            bg_h = bg["max_h"]
            street = bg["street"]
            
            # Generate human-readable per-building label
            if "Juárez" in street or "BBVA" in street:
                label_text = f"BBVA — {street}"
            elif "Defensores" in street or "Calimax" in street:
                label_text = f"Calimax — {street}"
            elif "Hidalgo" in street:
                label_text = "Parque Miguel Hidalgo"
            elif bg_h > 12.0:
                label_text = f"Edificio {street} #{idx}"
            else:
                label_text = f"Edificio {street}"

            # Tag position in Godot coordinates: (X, Y=Height, Z=-Y_local)
            tag_pos = [round(bg_cx, 3), round(bg_h + 2.5, 3), round(-bg_cy, 3)]

            building_tags.append({
                "building_id": f"{manzana_id}_B{idx}",
                "label": label_text,
                "street": street,
                "height_m": round(bg_h, 2),
                "tag_position": tag_pos,
                "primitive_count": len(bg["primitives"])
            })
            total_building_labels += 1

        rel_gltf_path = f"res://assets/blocks/manzanas/{manzana_id}.gltf"

        m_cx = sum(bg["cx"] for bg in building_groups) / len(building_groups)
        m_cy = sum(bg["cy"] for bg in building_groups) / len(building_groups)

        manifest[manzana_id] = {
            "gltf_path": rel_gltf_path,
            "lat": lat,
            "lon": lon,
            "centroid": [round(m_cx, 3), round(m_cy, 3)],
            "building_count": len(building_tags),
            "buildings": building_tags
        }

    os.makedirs(os.path.dirname(output_manifest), exist_ok=True)
    with open(output_manifest, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"Manifest generated successfully!")
    print(f"  Total Manzanas: {len(manifest)}")
    print(f"  Total Distinct Per-Building Labels: {total_building_labels}")
    print(f"  Output path: {output_manifest}")
    print("=" * 60)

if __name__ == "__main__":
    import math
    generate_manifest()
