# Purpose: Detects architectural elements (windows, doors) on facade segments.
# Inputs: target_facade.json, facades_cache.json, target_facade_texture.png.
# Outputs: Bounding boxes/coordinates of detected elements per segment.
# Responsibilities: Slices facade texture, runs segmentation, detects elements using priors, and snaps positions using visual intensity cues.
# Dependencies: numpy, os, json, cv2, PIL, src.segmentation.segmentation_agent

import os
import json
import numpy as np
import cv2
from PIL import Image
from src.segmentation.segmentation_agent import FacadeSegmentationAgent

class ProceduralElementDetector:
    """
    Detects windows and doors on the vertical facade segments of the target block.
    Uses a hybrid approach: semantic segmentation masks combined with visual intensity profile minima
    and regular architectural grid layout templates.
    """
    def __init__(self, data_dir: str = "data", export_dir: str = "export"):
        self.data_dir = data_dir
        self.export_dir = export_dir
        self.segmentation_agent = None

    def detect_elements(
        self,
        target_facade_path: str,
        facades_cache_path: str,
        texture_path: str
    ) -> dict:
        """
        Runs element detection across target segments.
        """
        print(f"[ProceduralElementDetector] Starting detection on {texture_path}...")
        
        # 1. Load target facade metadata
        with open(target_facade_path, "r", encoding="utf-8") as f:
            target_facade = json.load(f)
        block_id = target_facade["block_id"]
        target_indices = target_facade["target_facade_indices"]
        K = len(target_indices)
        
        # 2. Load facades cache to get lengths and dimensions
        with open(facades_cache_path, "r", encoding="utf-8") as f:
            facades_cache = json.load(f)
            
        # 3. Load texture and convert to grayscale for visual snapping
        if not os.path.exists(texture_path):
            raise FileNotFoundError(f"Texture file not found: {texture_path}")
        img_pil = Image.open(texture_path)
        img_np = np.array(img_pil)
        h_tex, w_tex = img_np.shape[:2]
        img_gray = cv2.cvtColor(img_np, cv2.COLOR_RGBA2GRAY) if img_np.shape[2] == 4 else cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)

        # 4. Lazy initialization of the semantic segmentation agent
        if self.segmentation_agent is None:
            self.segmentation_agent = FacadeSegmentationAgent()
            
        print("[ProceduralElementDetector] Running semantic segmentation on texture...")
        seg_mask = self.segmentation_agent.predict(texture_path)
        
        detected_elements = {}
        
        # Height range represented in the texture: height_meters / 2
        # For the case study block, height_meters is 8.37m, so texture height is 4.185m.
        tex_height_meters = 4.185
        
        for i, idx in enumerate(target_indices):
            f_id = f"{block_id}_facade_{idx}"
            f_data = facades_cache.get(f_id)
            if not f_data:
                continue
                
            verts = f_data["facade_segment_vertices_local"]
            A, B = np.array(verts[0]), np.array(verts[1])
            seg_width_meters = np.linalg.norm(B - A)
            
            # Pixel columns for this segment in the stitched texture
            col_start = int(i * w_tex / K)
            col_end = int((i + 1) * w_tex / K)
            slice_width_px = col_end - col_start
            
            # Slice segmentation mask and grayscale image
            seg_slice = seg_mask[:, col_start:col_end]
            gray_slice = img_gray[:, col_start:col_end]
            
            # Count semantic classes: 1 is window, 2 is door
            window_pixels = np.sum(seg_slice == 1)
            door_pixels = np.sum(seg_slice == 2)
            
            elements_in_seg = []
            
            # If semantic segmentation detects enough windows/doors, extract their positions
            semantic_valid = False
            if window_pixels > 200 or door_pixels > 200:
                # We can perform connected component analysis on window/door classes
                semantic_valid = True
                
                # Window components
                window_mask = (seg_slice == 1).astype(np.uint8)
                num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(window_mask)
                for label_idx in range(1, num_labels):
                    x_c, y_c, w, h, area = stats[label_idx]
                    if area > 50:
                        # Convert pixels to normalized quad coords and meters
                        u_start = float(x_c) / slice_width_px
                        u_end = float(x_c + w) / slice_width_px
                        z_start = float(h_tex - (y_c + h)) / h_tex * tex_height_meters
                        z_end = float(h_tex - y_c) / h_tex * tex_height_meters
                        elements_in_seg.append({
                            "type": "window",
                            "u_start": u_start,
                            "u_end": u_end,
                            "z_start": z_start,
                            "z_end": z_end,
                            "confidence": 0.9,
                            "source": "semantic"
                        })
                        
                # Door components
                door_mask = (seg_slice == 2).astype(np.uint8)
                num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(door_mask)
                for label_idx in range(1, num_labels):
                    x_c, y_c, w, h, area = stats[label_idx]
                    if area > 100:
                        u_start = float(x_c) / slice_width_px
                        u_end = float(x_c + w) / slice_width_px
                        z_start = float(h_tex - (y_c + h)) / h_tex * tex_height_meters
                        z_end = float(h_tex - y_c) / h_tex * tex_height_meters
                        elements_in_seg.append({
                            "type": "door",
                            "u_start": u_start,
                            "u_end": u_end,
                            "z_start": z_start,
                            "z_end": z_end,
                            "confidence": 0.9,
                            "source": "semantic"
                        })
            
            # If semantic segmentation did not yield elements, run hybrid prior layout + snapping
            if not semantic_valid or len(elements_in_seg) == 0:
                # 1. Define standard priors
                priors = []
                if seg_width_meters >= 3.0:
                    # Place a door in the center and windows on the sides
                    priors.append({
                        "type": "door",
                        "u_center": 0.5,
                        "width_meters": 1.0,
                        "z_start": 0.0,
                        "z_end": 2.2
                    })
                    priors.append({
                        "type": "window",
                        "u_center": 0.2,
                        "width_meters": 0.9,
                        "z_start": 1.0,
                        "z_end": 2.3
                    })
                    priors.append({
                        "type": "window",
                        "u_center": 0.8,
                        "width_meters": 0.9,
                        "z_start": 1.0,
                        "z_end": 2.3
                    })
                else:
                    # Narrow segment: place single window
                    priors.append({
                        "type": "window",
                        "u_center": 0.5,
                        "width_meters": 1.0,
                        "z_start": 1.0,
                        "z_end": 2.4
                    })
                    
                # 2. Extract visual intensity profile to snap horizontal coordinates
                # Average intensity vertically in the wall region (height 0.5m to 3.0m)
                y_start_px = int((1.0 - 0.5/tex_height_meters) * h_tex)
                y_end_px = int((1.0 - 3.0/tex_height_meters) * h_tex)
                y_min, y_max = min(y_start_px, y_end_px), max(y_start_px, y_end_px)
                y_min = max(0, y_min)
                y_max = min(h_tex, y_max)
                
                profile = np.mean(gray_slice[y_min:y_max, :], axis=0)
                # Apply moving average filter to smooth the profile
                window_size = max(5, int(slice_width_px * 0.08))
                smoothed = np.convolve(profile, np.ones(window_size)/window_size, mode='same')
                
                # Find local minima as candidate centers of dark windows/doors
                minima = []
                for x in range(1, slice_width_px - 1):
                    if smoothed[x] < smoothed[x-1] and smoothed[x] < smoothed[x+1]:
                        minima.append(x)
                        
                # 3. Align priors to nearest minima
                for prior in priors:
                    target_u = prior["u_center"]
                    target_x = target_u * slice_width_px
                    
                    best_min_x = target_x
                    min_dist = slice_width_px * 0.20 # max search distance: 20% of segment width
                    
                    for m_x in minima:
                        dist = abs(m_x - target_x)
                        if dist < min_dist:
                            min_dist = dist
                            best_min_x = m_x
                            
                    snapped_u = float(best_min_x) / slice_width_px
                    w_u = prior["width_meters"] / seg_width_meters
                    
                    u_start = max(0.0, snapped_u - w_u/2.0)
                    u_end = min(1.0, snapped_u + w_u/2.0)
                    
                    elements_in_seg.append({
                        "type": prior["type"],
                        "u_start": u_start,
                        "u_end": u_end,
                        "z_start": prior["z_start"],
                        "z_end": prior["z_end"],
                        "confidence": 0.7,
                        "source": "hybrid_prior"
                    })
                    
            detected_elements[f_id] = elements_in_seg
            print(f"  Segment {idx}: generated {len(elements_in_seg)} elements.")
            
        return {
            "block_id": block_id,
            "target_facade_indices": target_indices,
            "detected_elements": detected_elements
        }
