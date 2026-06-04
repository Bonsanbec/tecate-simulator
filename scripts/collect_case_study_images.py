import json
import os
import subprocess
import sys
from src.core_io.io_manager import ensure_dir

def load_env():
    """Loads environment variables from .env file if it exists."""
    possible_paths = [
        ".env",
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    ]
    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        if "=" in line:
                            key, val = line.split("=", 1)
                            key = key.strip()
                            val = val.strip()
                            # Strip quotes if any
                            if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                                val = val[1:-1]
                            os.environ[key] = val
                break
            except Exception as e:
                print(f"[Warning] Failed to read .env file at {path}: {e}")

def main():
    print("[collect_case_study_images] Starting...")
    
    # 1. Load target facade indices
    target_facade_path = "data/case_study/target_facade.json"
    if not os.path.exists(target_facade_path):
        raise FileNotFoundError(f"Target facade description not found: {target_facade_path}")
    with open(target_facade_path, "r", encoding="utf-8") as f:
        target_facade = json.load(f)
        
    block_id = target_facade["block_id"]
    target_indices = target_facade["target_facade_indices"]
    
    # 2. Load caches
    with open("data/facades_cache.json", "r", encoding="utf-8") as f:
        facades_cache = json.load(f)
    with open("data/panoramas_cache.json", "r", encoding="utf-8") as f:
        panoramas_cache = json.load(f)
        
    unique_panos = {}
    required_images = set()
    
    # 3. Collect required panoramas and images
    for idx in target_indices:
        f_id = f"{block_id}_facade_{idx}"
        f_data = facades_cache.get(f_id)
        if not f_data:
            print(f"[Warning] Facade {f_id} not found in facades_cache.json")
            continue
            
        pano_id = f_data["pano_id"]
        heading = f_data["heading"]
        img_name = f"{pano_id}_yaw_{heading:.2f}.png"
        required_images.add(img_name)
        
        if pano_id not in unique_panos:
            p_data = panoramas_cache.get(pano_id)
            if p_data:
                p_copy = p_data.copy()
                p_copy["pano_id"] = pano_id
                unique_panos[pano_id] = p_copy
            else:
                print(f"[Warning] Panorama {pano_id} metadata not found in panoramas_cache.json")
                
    # Save target_panoramas.json
    target_panos_data = {
        "panoramas": list(unique_panos.values())
    }
    target_panos_path = "data/case_study/target_panoramas.json"
    with open(target_panos_path, "w", encoding="utf-8") as f:
        json.dump(target_panos_data, f, indent=4)
    print(f"[collect_case_study_images] Wrote target panoramas metadata to {target_panos_path}")
    
    # 4. Check for missing images or LFS pointer files
    to_fetch = []
    for img in sorted(list(required_images)):
        local_path = os.path.join("data/screenshots/pano", img)
        needs_fetch = False
        if not os.path.exists(local_path):
            needs_fetch = True
        else:
            # Check size: LFS pointers are 132 bytes
            sz = os.path.getsize(local_path)
            if sz < 1000:
                needs_fetch = True
                
        if needs_fetch:
            to_fetch.append(f"data/screenshots/pano/{img}")
            
    if to_fetch:
        load_env()
        
        store_remote = os.environ.get("store_remote")
        store_remote_path = os.environ.get("store_remote_path", "~/tecate-simulator")
        store_remote_wsl = os.environ.get("store_remote_wsl", "1")
        
        if not store_remote:
            print("[collect_case_study_images] Error: Missing screenshots and no remote host configured in .env (store_remote).")
            print("[collect_case_study_images] Treating as local. Please ensure Git LFS screenshots are pulled locally.")
            sys.exit(1)
            
        print(f"[collect_case_study_images] Need to fetch {len(to_fetch)} screenshot files from remote {store_remote}...")
        
        files_arg = " ".join(to_fetch)
        tar_cmd = f"tar -C {store_remote_path} -czf - {files_arg}"
        
        if store_remote_wsl in ("1", "true", "True"):
            tar_cmd = f"wsl {tar_cmd}"
            
        cmd = f'ssh {store_remote} "{tar_cmd}" | tar -xzf -'
        
        print(f"Running command: {cmd}")
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            print("[collect_case_study_images] Successfully fetched screenshots over SSH!")
        else:
            print(f"[Error] Failed to fetch screenshots. Return code: {res.returncode}")
            print(f"Stderr: {res.stderr}")
            sys.exit(1)
    else:
        print("[collect_case_study_images] All screenshots are already present locally and are real files.")
        
    # 5. Create symlinks in data/case_study/target_images/
    ensure_dir("data/case_study/target_images")
    for img in sorted(list(required_images)):
        link_path = os.path.join("data/case_study/target_images", img)
        target_src = os.path.join("../../screenshots/pano", img)
        
        if os.path.exists(link_path) or os.path.islink(link_path):
            os.remove(link_path)
            
        os.symlink(target_src, link_path)
        
    print(f"[collect_case_study_images] Created {len(required_images)} symlinks in data/case_study/target_images/")
    
if __name__ == "__main__":
    main()
