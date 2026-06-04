import json
import os
import sys
import numpy as np
from PIL import Image
import cv2
import networkx as nx

from src.reconstruction.prism_generator import UrbanBlockReconstructor
from src.core_io.coords import gps_to_local
from src.core_io.io_manager import ensure_dir

def main():
    print("[extract_case_study_texture] Starting multi-view texture extraction...")
    
    # 1. Load target facade details
    with open("data/case_study/target_facade.json", "r", encoding="utf-8") as f:
        target_facade = json.load(f)
    block_id = target_facade["block_id"]
    target_indices = target_facade["target_facade_indices"]
    
    # 2. Instantiate reconstructor
    G = nx.MultiGraph()
    reconstructor = UrbanBlockReconstructor(G, export_dir="export", data_dir="data")
    
    # Load blocks
    block_data = reconstructor.blocks_cache[block_id]
    height_meters = block_data["height_meters"]
    
    K = len(target_indices)
    print(f"[extract_case_study_texture] Stitching {K} segments horizontally...")
    
    # Initialize final canvas
    canvas = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    
    for i, idx in enumerate(target_indices):
        f_id = f"{block_id}_facade_{idx}"
        f_data = reconstructor.facades_cache.get(f_id)
        if not f_data:
            print(f"[Warning] Facade {f_id} not found in cache. Skipping segment.")
            continue
            
        verts = f_data["facade_segment_vertices_local"]
        A_seg = verts[0]
        B_seg = verts[1]
        normal_seg = np.array(f_data["camera_alignment_diagnostics"]["facade_normal"])
        mx_seg = f_data["facade_midpoint_local"][0]
        my_seg = f_data["facade_midpoint_local"][1]
        
        pano_id = f_data["pano_id"]
        heading_val = f_data["heading"]
        
        pano_filename = f"{pano_id}_yaw_{heading_val:.2f}.png"
        pano_screenshot_path = os.path.abspath(os.path.join("data/screenshots/pano", pano_filename))
        
        if not os.path.exists(pano_screenshot_path):
            print(f"[Warning] Screenshot {pano_filename} not found. Skipping segment.")
            continue
            
        p_data = reconstructor.panoramas_cache[pano_id]
        cx_pano, cy_pano = gps_to_local(p_data["latitude"], p_data["longitude"])
        
        segment_group = [{
            "A": A_seg,
            "B": B_seg,
            "normal": normal_seg,
            "mx": mx_seg,
            "my": my_seg
        }]
        
        # Mask sky locally
        masked_img = reconstructor.mask_sky_in_panorama(
            image_path=pano_screenshot_path,
            cx=cx_pano,
            cy=cy_pano,
            heading=heading_val,
            height_meters=height_meters / 2.0,
            group_segments=segment_group
        )
        
        obs = {
            "image_path": masked_img,
            "projection": {
                "camera_x": cx_pano,
                "camera_y": cy_pano,
                "camera_z": 2.5,
                "yaw_degrees": heading_val,
                "fov_degrees": 75.0,
                "image_width": 1280,
                "image_height": 720
            }
        }
        
        # Calculate target slice in 512x512 texture
        col_start = int(i * 512 / K)
        col_end = int((i + 1) * 512 / K)
        slice_width = col_end - col_start
        
        # Project and warp this segment to its slice
        # First warp to full 512x512
        warped_full = reconstructor.extract_rectified_facade_observation_texture(
            obs,
            A=A_seg,
            B=B_seg,
            height_meters=height_meters / 2.0,
            width=slice_width,
            height=512
        )
        
        # Paste into canvas
        canvas.paste(warped_full, (col_start, 0))
        print(f"  Segment {idx} (slice {col_start}..{col_end}) pasted from {pano_id}.")
        
    # Calculate final coverage
    np_canvas = np.array(canvas)
    alpha = np_canvas[:, :, 3]
    total_pixels = 512 * 512
    non_transparent_pixels = np.count_nonzero(alpha > 0)
    coverage_pct = float((non_transparent_pixels / total_pixels) * 100.0)
    
    status = "PASS" if coverage_pct >= 50.0 else "FAIL"
    
    ensure_dir("export/case_study")
    texture_path = "export/case_study/target_facade_texture.png"
    canvas.save(texture_path, "PNG")
    print(f"[extract_case_study_texture] Wrote target facade texture to {texture_path}")
    
    report = {
        "width": 512,
        "height": 512,
        "coverage_pct": coverage_pct,
        "status": status
    }
    
    report_path = "export/case_study/texture_extraction_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)
        
    print(f"[extract_case_study_texture] Wrote report to {report_path}")
    print(f"  Final Coverage: {coverage_pct:.2f}% (Status: {status})")

if __name__ == "__main__":
    main()
