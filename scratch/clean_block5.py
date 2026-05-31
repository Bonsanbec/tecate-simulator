import os
import json
import glob

def clean_block5():
    data_dir = "data"
    textures_dir = "export/textures"
    screenshots_dir = "data/screenshots/facades"
    
    # 1. Load relational cache files
    blocks_path = os.path.join(data_dir, "blocks_cache.json")
    facades_path = os.path.join(data_dir, "facades_cache.json")
    panoramas_path = os.path.join(data_dir, "panoramas_cache.json")
    stitching_path = os.path.join(data_dir, "stitching_cache.json")
    
    print("=" * 60)
    print("           BLOCK_5 GEOSPATIAL PURGE ENGINE")
    print("=" * 60)
    
    # Clean blocks_cache.json
    if os.path.exists(blocks_path):
        with open(blocks_path, "r", encoding="utf-8") as f:
            blocks = json.load(f)
        if "block_5" in blocks:
            del blocks["block_5"]
            print(f"[Purge] Removed 'block_5' entry from {blocks_path}.")
            with open(blocks_path, "w", encoding="utf-8") as f:
                json.dump(blocks, f, indent=4)
        else:
            print(f"[Info] 'block_5' not found in {blocks_path}.")
            
    # Clean facades_cache.json and gather referenced panoramas to clean up orphaned ones
    removed_panos = set()
    if os.path.exists(facades_path):
        with open(facades_path, "r", encoding="utf-8") as f:
            facades = json.load(f)
            
        initial_count = len(facades)
        cleaned_facades = {}
        for f_id, f_data in facades.items():
            if f_id.startswith("block_5_") or f_data.get("block_id") == "block_5":
                p_id = f_data.get("pano_id")
                if p_id:
                    removed_panos.add(p_id)
            else:
                cleaned_facades[f_id] = f_data
                
        removed_count = initial_count - len(cleaned_facades)
        if removed_count > 0:
            print(f"[Purge] Removed {removed_count} facade entries belonging to block_5 from {facades_path}.")
            with open(facades_path, "w", encoding="utf-8") as f:
                json.dump(cleaned_facades, f, indent=4)
                
            # Verify if the panoramas are still used by other active facades
            if os.path.exists(panoramas_path):
                with open(panoramas_path, "r", encoding="utf-8") as f:
                    panos = json.load(f)
                
                # Check active references
                active_panos = set(f_data.get("pano_id") for f_data in cleaned_facades.values())
                orphaned_panos = removed_panos - active_panos
                
                purged_panos = 0
                for op in orphaned_panos:
                    if op in panos:
                        del panos[op]
                        purged_panos += 1
                        
                if purged_panos > 0:
                    print(f"[Purge] Purged {purged_panos} orphaned panoramas from {panoramas_path}.")
                    with open(panoramas_path, "w", encoding="utf-8") as f:
                        json.dump(panos, f, indent=4)
        else:
            print(f"[Info] No block_5 facades found in {facades_path}.")

    # Clean stitching_cache.json
    if os.path.exists(stitching_path):
        with open(stitching_path, "r", encoding="utf-8") as f:
            stitching = json.load(f)
            
        cleaned_stitching = {k: v for k, v in stitching.items() if not k.startswith("block_5_")}
        removed_stitch = len(stitching) - len(cleaned_stitching)
        if removed_stitch > 0:
            print(f"[Purge] Removed {removed_stitch} stitching cache keys from {stitching_path}.")
            with open(stitching_path, "w", encoding="utf-8") as f:
                json.dump(cleaned_stitching, f, indent=4)
        else:
            print(f"[Info] No block_5 stitching keys found in {stitching_path}.")

    # 2. Purge physical files on disk
    purged_files = 0
    
    # Screenshots
    screenshot_patterns = [
        os.path.join(screenshots_dir, "block_5_facade_*.png"),
        os.path.join(screenshots_dir, "block_5_*_facade.png")
    ]
    for pattern in screenshot_patterns:
        for filepath in glob.glob(pattern):
            try:
                os.remove(filepath)
                purged_files += 1
            except Exception as e:
                print(f"[Warning] Failed to delete file {filepath}: {e}")
                
    # Textures
    texture_patterns = [
        os.path.join(textures_dir, "block_5_facade_*.png"),
        os.path.join(textures_dir, "block_5_*_facade.png")
    ]
    for pattern in texture_patterns:
        for filepath in glob.glob(pattern):
            try:
                os.remove(filepath)
                purged_files += 1
            except Exception as e:
                print(f"[Warning] Failed to delete file {filepath}: {e}")
                
    if purged_files > 0:
        print(f"[Purge] Successfully deleted {purged_files} physical PNG image files from data/ and export/ directories.")
    else:
        print("[Info] No physical image files matching block_5 pattern were found on disk.")
        
    print("=" * 60)
    print("           PURGE OPERATIONS COMPLETED SUCCESSFULLY")
    print("=" * 60)

if __name__ == "__main__":
    clean_block5()
