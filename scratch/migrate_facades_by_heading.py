import os
import json
import shutil

facades_dir = "data/screenshots/facades"
pano_dir = "data/screenshots/pano"

# Clean the directory first
if os.path.exists(pano_dir):
    shutil.rmtree(pano_dir)
os.makedirs(pano_dir, exist_ok=True)

# Load existing caches
facades_cache_path = "data/facades_cache.json"
facades_cache = {}
if os.path.exists(facades_cache_path):
    with open(facades_cache_path, "r", encoding="utf-8") as f:
        facades_cache = json.load(f)

# Load provenance from metadata.json in export
provenance = {}
meta_json_path = "export/metadata.json"
if os.path.exists(meta_json_path):
    try:
        with open(meta_json_path, "r", encoding="utf-8") as f:
            meta_data = json.load(f)
        provenance = meta_data.get("provenance", {})
    except Exception as e:
        print(f"[Warning] Failed to load metadata.json: {e}")

files = [f for f in os.listdir(facades_dir) if f.endswith(".png")]
print(f"Found {len(files)} original facade screenshots in {facades_dir}.")

migrated_panos = set()
copied_count = 0
missing_data = 0

for f in files:
    facade_id = f[:-4]
    
    # 1. Retrieve pano_id and heading
    pano_id = None
    heading = None
    
    # Try facades_cache first
    f_data = facades_cache.get(facade_id)
    if f_data:
        pano_id = f_data.get("pano_id")
        heading = f_data.get("heading")
        
    # Try provenance metadata next
    if not pano_id or heading is None:
        prov_data = provenance.get(facade_id)
        if prov_data:
            pano_id = prov_data.get("source_pano_id")
            # If heading is not explicitly named, we can derive it from the normal or heading in metadata
            normal = prov_data.get("facade_normal", [0.0, 1.0])
            import math
            heading = math.degrees(math.atan2(-normal[0], -normal[1])) % 360.0
            
    if pano_id and heading is not None:
        # Format heading to two decimal places of precision, just like Google Maps URLs
        heading_str = f"{heading:.2f}"
        unique_img_key = f"{pano_id}_yaw_{heading_str}"
        
        src_path = os.path.join(facades_dir, f)
        dest_path = os.path.join(pano_dir, f"{unique_img_key}.png")
        
        if unique_img_key not in migrated_panos:
            shutil.copy2(src_path, dest_path)
            copied_count += 1
            migrated_panos.add(unique_img_key)
    else:
        missing_data += 1

print(f"\nMigration Summary (By Heading - 2 Decimals):")
print(f"Total facade screenshots processed: {len(files)}")
print(f"Unique panorama-heading screenshots registered: {len(migrated_panos)}")
print(f"New panorama-heading screenshot files copied: {copied_count}")
print(f"Facade screenshots with missing pano/heading data: {missing_data}")
