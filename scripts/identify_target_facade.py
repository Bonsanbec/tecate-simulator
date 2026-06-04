import json
import math
import os
import numpy as np
from src.core_io.io_manager import ensure_dir

def main():
    print("[identify_target_facade] Loading facades cache...")
    facades_cache_path = "data/facades_cache.json"
    if not os.path.exists(facades_cache_path):
        raise FileNotFoundError(f"Facades cache not found at {facades_cache_path}")
        
    with open(facades_cache_path, "r", encoding="utf-8") as f:
        facades = json.load(f)
        
    block_id = "block_lat_32.57255_lon_-116.62529"
    ref_heading = 263.88
    ref_heading_rad = math.radians(ref_heading)
    # Coordinate system: X is East (sin), Y is North (cos)
    v_ref = np.array([math.sin(ref_heading_rad), math.cos(ref_heading_rad)])
    
    # Reference target position:
    target_pos = np.array([180.0663, -39.0099])
    
    print(f"[identify_target_facade] Filtering facades for block {block_id}...")
    candidate_facades = []
    
    for f_id, f_data in facades.items():
        if not f_id.startswith(block_id):
            continue
            
        road_rel = f_data.get("road_relation")
        if not road_rel:
            continue
            
        road_name = road_rel.get("road_name", "")
        if "Abelardo" not in road_name and "Rodriguez" not in road_name:
            continue
            
        # Get normal vector
        diag = f_data.get("camera_alignment_diagnostics", {})
        normal = diag.get("facade_normal")
        if not normal:
            verts = f_data.get("facade_segment_vertices_local")
            if verts and len(verts) >= 2:
                A, B = np.array(verts[0]), np.array(verts[1])
                dx, dy = B[0] - A[0], B[1] - A[1]
                normal = np.array([dy, -dx])
                norm_len = np.linalg.norm(normal)
                if norm_len > 1e-5:
                    normal = normal / norm_len
                else:
                    normal = np.array([0.0, 1.0])
            else:
                continue
                
        # Use absolute dot product to check alignment along the line of sight (East-West)
        dot_prod = abs(float(np.dot(v_ref, normal)))
        
        if dot_prod > 0.7:
            candidate_facades.append({
                "facade_id": f_id,
                "facade_index": f_data["facade_index"],
                "heading": f_data["heading"],
                "dot_product": dot_prod,
                "road_name": road_name,
                "midpoint": f_data.get("facade_midpoint_local")
            })
            
    if not candidate_facades:
        raise ValueError("No target facades found matching criteria!")
        
    candidate_facades.sort(key=lambda x: x["facade_index"])
    
    # Group into contiguous index ranges
    groups = []
    current_group = [candidate_facades[0]]
    
    for item in candidate_facades[1:]:
        if item["facade_index"] - current_group[-1]["facade_index"] == 1:
            current_group.append(item)
        else:
            groups.append(current_group)
            current_group = [item]
    groups.append(current_group)
    
    print(f"[identify_target_facade] Found {len(groups)} contiguous facade groups:")
    best_group = None
    min_dist = float("inf")
    
    for idx, g in enumerate(groups):
        indices = [item["facade_index"] for item in g]
        midpoints = [item["midpoint"] for item in g if item.get("midpoint")]
        if midpoints:
            group_centroid = np.mean(midpoints, axis=0)
            dist = np.linalg.norm(group_centroid - target_pos)
        else:
            dist = float("inf")
            
        print(f"  Group {idx}: indices {indices[0]}..{indices[-1]} (size={len(g)}), dist={dist:.2f}m")
        if dist < min_dist and len(g) >= 5 and len(g) <= 20:
            min_dist = dist
            best_group = g
            
    if best_group is None:
        min_dist = float("inf")
        for g in groups:
            midpoints = [item["midpoint"] for item in g if item.get("midpoint")]
            if midpoints:
                group_centroid = np.mean(midpoints, axis=0)
                dist = np.linalg.norm(group_centroid - target_pos)
            else:
                dist = float("inf")
            if dist < min_dist:
                min_dist = dist
                best_group = g
                
    indices = [item["facade_index"] for item in best_group]
    mean_heading = float(np.mean([item["heading"] for item in best_group]))
    mean_dot = float(np.mean([item["dot_product"] for item in best_group]))
    road_name = best_group[0]["road_name"]
    
    output_data = {
        "block_id": block_id,
        "target_facade_indices": indices,
        "heading_to_face_facade": mean_heading,
        "alignment_dot_product": mean_dot,
        "associated_road_name": road_name
    }
    
    ensure_dir("data/case_study")
    output_path = "data/case_study/target_facade.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=4)
        
    print(f"[identify_target_facade] Successfully wrote target facade to {output_path}")
    print(f"  Indices: {indices}")
    print(f"  Heading: {mean_heading:.2f}")
    print(f"  Dot Product: {mean_dot:.4f}")

if __name__ == "__main__":
    main()
