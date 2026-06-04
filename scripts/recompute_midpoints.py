import json
import os
import tempfile

def main():
    print("[recompute_midpoints] Loading facades cache...")
    facades_cache_path = "data/facades_cache.json"
    if not os.path.exists(facades_cache_path):
        raise FileNotFoundError(f"Facades cache not found at {facades_cache_path}")
        
    with open(facades_cache_path, "r", encoding="utf-8") as f:
        facades = json.load(f)
        
    updated_count = 0
    total_count = 0
    
    for f_id, f_data in facades.items():
        verts = f_data.get("facade_segment_vertices_local")
        if verts and len(verts) >= 2:
            total_count += 1
            A = verts[0]
            B = verts[1]
            mx = (A[0] + B[0]) / 2.0
            my = (A[1] + B[1]) / 2.0
            
            old_mid = f_data.get("facade_midpoint_local")
            new_mid = [mx, my]
            
            if old_mid is None or abs(old_mid[0] - new_mid[0]) > 1e-5 or abs(old_mid[1] - new_mid[1]) > 1e-5:
                f_data["facade_midpoint_local"] = new_mid
                updated_count += 1
                
    # Atomic write
    print(f"[recompute_midpoints] Recomputed {total_count} midpoints. {updated_count} required updates.")
    dir_name = os.path.dirname(facades_cache_path)
    
    # Create temp file in the same directory to ensure atomic replace on the same filesystem
    with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, encoding="utf-8") as tmp_f:
        json.dump(facades, tmp_f, indent=4)
        tmp_name = tmp_f.name
        
    os.replace(tmp_name, facades_cache_path)
    print(f"[recompute_midpoints] Facades cache successfully saved to {facades_cache_path}")

if __name__ == "__main__":
    main()
