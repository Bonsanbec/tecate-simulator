import json
import math
import os
import numpy as np

class PoseValidator:
    """
    Validates camera pose alignment and distance against target facade segments.
    """
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.facades_cache_path = os.path.join(data_dir, "facades_cache.json")
        self.facades_cache = {}
        if os.path.exists(self.facades_cache_path):
            with open(self.facades_cache_path, "r", encoding="utf-8") as f:
                self.facades_cache = json.load(f)

    def _gps_to_local(self, lat: float, lon: float) -> tuple[float, float]:
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

    def validate(self, p: dict, facade: dict) -> dict:
        """
        Validates if the panorama camera pose is suitable for capturing the target facade.
        """
        pano_id = p["pano_id"]
        block_id = facade["block_id"]
        target_indices = facade["target_facade_indices"]
        
        cx, cy = self._gps_to_local(p["latitude"], p["longitude"])
        
        valid_segments_count = 0
        best_dot = 0.0  # We want the most negative dot product (max alignment facing facade)
        
        for idx in target_indices:
            f_id = f"{block_id}_facade_{idx}"
            f_data = self.facades_cache.get(f_id)
            if not f_data:
                continue
                
            mid = f_data.get("facade_midpoint_local")
            if not mid:
                continue
                
            # Compute camera look vector to facade midpoint
            look_vec = np.array([mid[0] - cx, mid[1] - cy])
            dist = np.linalg.norm(look_vec)
            if dist < 1e-5:
                continue
                
            norm_look = look_vec / dist
            
            # Get facade normal
            normal = None
            diag = f_data.get("camera_alignment_diagnostics", {})
            if diag and diag.get("facade_normal"):
                normal = np.array(diag["facade_normal"])
            else:
                verts = f_data.get("facade_segment_vertices_local")
                if verts and len(verts) >= 2:
                    A, B = np.array(verts[0]), np.array(verts[1])
                    dx, dy = B[0] - A[0], B[1] - A[1]
                    normal = np.array([dy, -dx])
                    norm_len = np.linalg.norm(normal)
                    if norm_len > 1e-5:
                        normal = normal / norm_len
                        
            if normal is not None:
                dot = float(np.dot(norm_look, normal))
                # For validation, we want the camera looking at the facade (opposite directions, dot < -0.5)
                # and camera close enough to the facade (< 50 meters)
                if dot < -0.5 and dist < 50.0:
                    valid_segments_count += 1
                    if dot < best_dot:
                        best_dot = dot
                        
        status = "VALID" if valid_segments_count > 0 else "INVALID"
        
        return {
            "pano_id": pano_id,
            "status": status,
            "alignment_dot_product": best_dot,
            "valid_segments_count": valid_segments_count
        }
