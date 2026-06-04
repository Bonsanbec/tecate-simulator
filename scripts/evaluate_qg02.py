import json
import os
import math
import numpy as np

def gps_to_local(lat: float, lon: float) -> tuple[float, float]:
    # parque hidalgo center
    TECATE_LAT_CENTER = 32.573229
    TECATE_LON_CENTER = -116.626536
    EARTH_RADIUS = 6378137.0
    
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    lat_c_rad = math.radians(TECATE_LAT_CENTER)
    lon_c_rad = math.radians(TECATE_LON_CENTER)
    
    dx = EARTH_RADIUS * (lon_rad - lon_c_rad) * math.cos(lat_c_rad)
    dy = EARTH_RADIUS * (lat_rad - lat_c_rad)
    return dx, dy

def main():
    print("[evaluate_qg02] Validating dataset for QG-02...")
    
    report = {
        "status": "FAIL",
        "checks": {}
    }
    
    # 1. Manifest verification
    manifest_path = "data/case_study/case_study_manifest.json"
    if not os.path.exists(manifest_path):
        report["checks"]["manifest_exists"] = {"status": "FAIL", "reason": "case_study_manifest.json not found"}
    else:
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            report["checks"]["manifest_exists"] = {"status": "PASS"}
        except Exception as e:
            report["checks"]["manifest_exists"] = {"status": "FAIL", "reason": f"Failed to parse manifest: {e}"}
            
    if report["checks"]["manifest_exists"]["status"] == "FAIL":
        save_report(report)
        return
        
    # 2. Target facade verification
    target_facade_path = manifest["target_facade_file"]
    if not os.path.exists(target_facade_path):
        report["checks"]["target_facade_exists"] = {"status": "FAIL", "reason": "target_facade.json not found"}
    else:
        try:
            with open(target_facade_path, "r", encoding="utf-8") as f:
                target_facade = json.load(f)
            report["checks"]["target_facade_exists"] = {"status": "PASS"}
        except Exception as e:
            report["checks"]["target_facade_exists"] = {"status": "FAIL", "reason": f"Failed to parse target_facade: {e}"}
            
    if report["checks"]["target_facade_exists"]["status"] == "FAIL":
        save_report(report)
        return
        
    # 3. Target panoramas verification
    target_panos_path = manifest["target_panoramas_file"]
    if not os.path.exists(target_panos_path):
        report["checks"]["target_panoramas_exists"] = {"status": "FAIL", "reason": "target_panoramas.json not found"}
    else:
        try:
            with open(target_panos_path, "r", encoding="utf-8") as f:
                target_panos = json.load(f)
            report["checks"]["target_panoramas_exists"] = {"status": "PASS"}
        except Exception as e:
            report["checks"]["target_panoramas_exists"] = {"status": "FAIL", "reason": f"Failed to parse target_panoramas: {e}"}
            
    if report["checks"]["target_panoramas_exists"]["status"] == "FAIL":
        save_report(report)
        return
        
    # 4. Check distance constraint
    ref_gps = manifest["reference_gps"]
    ref_local = gps_to_local(ref_gps[0], ref_gps[1])
    
    with open("data/facades_cache.json", "r", encoding="utf-8") as f:
        facades_cache = json.load(f)
        
    block_id = target_facade["block_id"]
    target_indices = target_facade["target_facade_indices"]
    
    distances = []
    for idx in target_indices:
        f_id = f"{block_id}_facade_{idx}"
        f_data = facades_cache.get(f_id)
        if f_data and f_data.get("facade_midpoint_local"):
            mid = f_data["facade_midpoint_local"]
            d = math.sqrt((mid[0] - ref_local[0])**2 + (mid[1] - ref_local[1])**2)
            distances.append(d)
            
    if not distances:
        report["checks"]["distance_constraint"] = {"status": "FAIL", "reason": "No facade midpoints found to compute distance"}
    else:
        min_dist = min(distances)
        if min_dist < 10.0:
            report["checks"]["distance_constraint"] = {"status": "PASS", "min_distance_meters": min_dist}
        else:
            report["checks"]["distance_constraint"] = {"status": "FAIL", "reason": f"Minimum distance from reference is {min_dist:.2f}m (must be <10m)"}
            
    # 5. Check panorama alignment and date constraints
    panos_list = target_panos.get("panoramas", [])
    valid_pano_found = False
    
    for p in panos_list:
        # Check date: date should be <= 2009
        date_str = p.get("date", "")
        if not date_str:
            continue
            
        try:
            year = int(date_str.split("-")[0])
        except ValueError:
            continue
            
        if year > 2009:
            continue
            
        # Check if there is an associated facade segment pointing towards the facade
        cx, cy = gps_to_local(p["latitude"], p["longitude"])
        
        # Check all target facade segments
        for idx in target_indices:
            f_id = f"{block_id}_facade_{idx}"
            f_data = facades_cache.get(f_id)
            if not f_data or f_data.get("pano_id") != p["pano_id"]:
                continue
                
            diag = f_data.get("camera_alignment_diagnostics", {})
            look = diag.get("look_vector")
            normal = diag.get("facade_normal")
            
            if look and normal:
                norm_look = np.array(look) / np.linalg.norm(look)
                dot = float(np.dot(norm_look, normal))
                if dot < -0.5:
                    valid_pano_found = True
                    break
                    
        if valid_pano_found:
            break
            
    if valid_pano_found:
        report["checks"]["historical_aligned_panorama"] = {"status": "PASS"}
    else:
        report["checks"]["historical_aligned_panorama"] = {"status": "FAIL", "reason": "No panorama with date <= 2009 and alignment dot product < -0.5 was found"}
        
    # 6. Check image files on disk
    image_dir = manifest["target_images_dir"]
    images_ok = True
    missing_images = []
    
    unique_images = set()
    for idx in target_indices:
        f_id = f"{block_id}_facade_{idx}"
        f_data = facades_cache.get(f_id)
        if f_data:
            pano_id = f_data["pano_id"]
            heading = f_data["heading"]
            img_name = f"{pano_id}_yaw_{heading:.2f}.png"
            unique_images.add(img_name)
            
    for img in unique_images:
        img_path = os.path.join(image_dir, img)
        if not os.path.exists(img_path):
            images_ok = False
            missing_images.append(img)
        else:
            # Check size: must be a real image, not LFS pointer
            if os.path.getsize(img_path) < 1000:
                images_ok = False
                missing_images.append(f"{img} (LFS pointer)")
                
    if images_ok:
        report["checks"]["images_on_disk"] = {"status": "PASS"}
    else:
        report["checks"]["images_on_disk"] = {"status": "FAIL", "reason": f"Missing or pointer images: {missing_images}"}
        
    # Determine overall status
    all_passed = all(check["status"] == "PASS" for check in report["checks"].values())
    if all_passed:
        report["status"] = "PASS"
        print("[evaluate_qg02] Quality Gate QG-02: PASS")
    else:
        report["status"] = "FAIL"
        print("[evaluate_qg02] Quality Gate QG-02: FAIL")
        
    save_report(report)

def save_report(report):
    output_path = "data/case_study/QG02_report.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)
    print(f"[evaluate_qg02] Saved QG-02 report to {output_path}")

if __name__ == "__main__":
    main()
