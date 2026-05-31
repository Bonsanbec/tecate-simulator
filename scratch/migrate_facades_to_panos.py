import os
import json
import shutil

facades_dir = "data/screenshots/facades"
pano_dir = "data/screenshots/pano"
os.makedirs(pano_dir, exist_ok=True)

# Load existing caches
facades_cache_path = "data/facades_cache.json"
metadata_cache_path = "data/metadata_cache.json" # in case some are in legacy format

facades_cache = {}
if os.path.exists(facades_cache_path):
    with open(facades_cache_path, "r", encoding="utf-8") as f:
        facades_cache = json.load(f)

# If facades_cache is empty, let's also try loading other metadata caches
legacy_cache = {}
if os.path.exists("data/blocks_cache.json"): # let's check legacy metadata inside blocks
    pass

# We will scan data/screenshots/facades
if not os.path.exists(facades_dir):
    print(f"Directory {facades_dir} does not exist.")
    exit(0)
    
files = [f for f in os.listdir(facades_dir) if f.endswith(".png")]
print(f"Found {len(files)} facade screenshots in {facades_dir}.")

migrated_panos = set()
missing_pano_ids = 0
copied_count = 0

for f in files:
    facade_id = f[:-4] # remove .png
    # Look up in facades_cache
    facade_data = facades_cache.get(facade_id)
    pano_id = None
    if facade_data:
        pano_id = facade_data.get("pano_id")
        
    if not pano_id:
        # Try to find in metadata.json in export
        meta_json_path = "export/metadata.json"
        if os.path.exists(meta_json_path):
            try:
                with open(meta_json_path, "r", encoding="utf-8") as mf:
                    meta_data = json.load(mf)
                prov = meta_data.get("provenance", {})
                if facade_id in prov:
                    pano_id = prov[facade_id].get("source_pano_id")
            except Exception:
                pass
                
    if pano_id:
        src_path = os.path.join(facades_dir, f)
        dest_path = os.path.join(pano_dir, f"{pano_id}.png")
        
        if pano_id not in migrated_panos:
            if not os.path.exists(dest_path):
                shutil.copy2(src_path, dest_path)
                copied_count += 1
            migrated_panos.add(pano_id)
    else:
        missing_pano_ids += 1

print(f"\nMigration Summary:")
print(f"Total facade screenshots processed: {len(files)}")
print(f"Unique panorama screenshots registered: {len(migrated_panos)}")
print(f"New panorama screenshot files copied: {copied_count}")
print(f"Facade screenshots with missing pano_id: {missing_pano_ids}")
