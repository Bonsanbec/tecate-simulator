# Purpose: Computes Peak Signal-to-Noise Ratio (PSNR) for reconstructed facade views.
# Inputs: target_facade_texture.png, target_facade.json, facades_cache.json, target panoramas, source screenshots.
# Outputs: PSNR metric in decibels (dB).
# Responsibilities: Projects textured facade segments back to camera views, masks non-facade pixels, and calculates PSNR vs. ground truth.
# Dependencies: numpy, cv2, json, os, PIL, src.core_io.coords

import os
import json
import math
import numpy as np
import cv2
from PIL import Image
from src.core_io.coords import gps_to_local

class PsnrEvaluator:
    """
    Computes Peak Signal-to-Noise Ratio (PSNR) of the reconstructed facade
    by warping the texture back to camera views and comparing it to the source imagery.
    """
    def __init__(self, data_dir: str = "data", export_dir: str = "export"):
        self.data_dir = data_dir
        self.export_dir = export_dir

    def evaluate_psnr(self, texture_path: str, target_facade_path: str, target_panos_path: str) -> dict:
        """
        Computes PSNR across all target segments and observations.
        """
        if not os.path.exists(texture_path):
            raise FileNotFoundError(f"Texture file not found: {texture_path}")
            
        # Load texture
        tex_img = Image.open(texture_path).convert("RGBA")
        tex_np = np.array(tex_img)
        
        # Load target details
        with open(target_facade_path, "r", encoding="utf-8") as f:
            target_facade = json.load(f)
        block_id = target_facade["block_id"]
        target_indices = target_facade["target_facade_indices"]
        K = len(target_indices)
        
        with open(os.path.join(self.data_dir, "facades_cache.json"), "r", encoding="utf-8") as f:
            facades_cache = json.load(f)
            
        with open(os.path.join(self.data_dir, "blocks_cache.json"), "r", encoding="utf-8") as f:
            blocks_cache = json.load(f)
        block_data = blocks_cache.get(block_id)
        height_meters = block_data.get("height_meters", 8.37) if block_data else 8.37
        tex_height_meters = height_meters / 2.0
        
        psnrs = []
        
        # We evaluate PSNR for each segment against its corresponding panorama screenshot
        for i, idx in enumerate(target_indices):
            f_id = f"{block_id}_facade_{idx}"
            f_data = facades_cache.get(f_id)
            if not f_data:
                continue
                
            pano_id = f_data["pano_id"]
            heading_val = f_data["heading"]
            
            pano_filename = f"{pano_id}_yaw_{heading_val:.2f}.png"
            pano_screenshot_path = os.path.join(self.data_dir, "screenshots/pano", pano_filename)
            
            if not os.path.exists(pano_screenshot_path):
                continue
                
            # Load original screenshot
            orig_img = cv2.imread(pano_screenshot_path)
            if orig_img is None:
                continue
            h_obs, w_obs = orig_img.shape[:2]
            
            # Setup projection model
            cam_fov = 75.0
            f_len = (w_obs - 1) / (2.0 * math.tan(math.radians(cam_fov) / 2.0))
            
            # Load camera positions
            with open(target_panos_path, "r", encoding="utf-8") as f:
                target_panos = json.load(f)
            
            p_data = None
            for p in target_panos["panoramas"]:
                if p["pano_id"] == pano_id:
                    p_data = p
                    break
            if not p_data:
                continue
                
            cx_pano, cy_pano = gps_to_local(p_data["latitude"], p_data["longitude"])
            cam_pos = (cx_pano, cy_pano, 2.5)
            
            # Segment corners in 3D (BL, BR, TR, TL)
            verts = f_data["facade_segment_vertices_local"]
            A, B = np.array(verts[0]), np.array(verts[1])
            
            corners_3d = [
                (A[0], A[1], 0.0),
                (B[0], B[1], 0.0),
                (B[0], B[1], tex_height_meters),
                (A[0], A[1], tex_height_meters)
            ]
            
            # Project corners to 2D image coordinates
            pts_img = []
            cam_yaw = math.radians(heading_val)
            v_look = np.array([math.sin(cam_yaw), math.cos(cam_yaw), 0.0])
            v_right = np.array([math.cos(cam_yaw), -math.sin(cam_yaw), 0.0])
            v_up = np.array([0.0, 0.0, 1.0])
            
            for mx, my, mz in corners_3d:
                dx = mx - cam_pos[0]
                dy = my - cam_pos[1]
                dz = mz - cam_pos[2]
                
                x_c = dx * v_right[0] + dy * v_right[1] + dz * v_right[2]
                y_c = dx * v_up[0] + dy * v_up[1] + dz * v_up[2]
                z_c = dx * v_look[0] + dy * v_look[1] + dz * v_look[2]
                
                if z_c > 0.01:
                    px = (w_obs - 1) / 2.0 + f_len * (x_c / z_c)
                    py = (h_obs - 1) / 2.0 - f_len * (y_c / z_c)
                    pts_img.append([px, py])
                else:
                    break
                    
            if len(pts_img) < 4:
                continue
                
            pts_img = np.array(pts_img, dtype=np.float32)
            
            # Texture source slice corners in target_facade_texture.png (512x512)
            col_start = int(i * 512 / K)
            col_end = int((i + 1) * 512 / K)
            
            # Texture corners: BL, BR, TR, TL (in texture coordinates, Y is down in numpy)
            pts_tex = np.array([
                [col_start, 511],
                [col_end - 1, 511],
                [col_end - 1, 0],
                [col_start, 0]
            ], dtype=np.float32)
            
            # Compute homography to warp texture slice back to original image coordinates
            H, _ = cv2.findHomography(pts_tex, pts_img)
            if H is None:
                continue
                
            # Warp texture slice
            warped_slice = cv2.warpPerspective(tex_np, H, (w_obs, h_obs))
            
            # Create mask for segment quad in the image
            mask = np.zeros((h_obs, w_obs), dtype=np.uint8)
            cv2.fillPoly(mask, [pts_img.astype(np.int32)], 255)
            
            # Exclude sky region if masked out in the texture
            alpha_mask = (warped_slice[:, :, 3] > 0).astype(np.uint8) * 255
            combined_mask = cv2.bitwise_and(mask, alpha_mask)
            
            # Compare color channels
            orig_rgb = cv2.cvtColor(orig_img, cv2.COLOR_BGR2RGB)
            warped_rgb = warped_slice[:, :, :3]
            
            # Compute MSE over masked pixels
            indices = np.where(combined_mask > 0)
            if len(indices[0]) < 10:
                continue
                
            diff = orig_rgb[indices] - warped_rgb[indices]
            mse = np.mean(diff ** 2)
            
            if mse < 1e-6:
                psnr = 99.0
            else:
                psnr = 20 * math.log10(255.0) - 10 * math.log10(mse)
                
            psnrs.append(psnr)
            
        if not psnrs:
            return {
                "psnr_db": 0.0,
                "status": "FAIL",
                "reason": "No valid observations reprojected for PSNR evaluation"
            }
            
        avg_psnr = float(np.mean(psnrs))
        status = "PASS" if avg_psnr >= 25.0 else "FAIL"
        
        return {
            "psnr_db": avg_psnr,
            "status": status,
            "segment_psnrs": psnrs
        }
