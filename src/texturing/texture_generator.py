import math
import os
import cv2
import numpy as np
from PIL import Image, ImageDraw

from src.core_io.coords import gps_to_local

class TextureGenerator:
    """
    Builds a unified, perspective-rectified texture atlas per urban block (manzana)
    using exclusively temporally consistent (2009-validated) Street View observations.
    Projects equirectangular spheres onto 3D planes to eliminate curved distortions.
    """
    def __init__(self, export_dir: str = "export/textures"):
        self.export_dir = export_dir
        os.makedirs(export_dir, exist_ok=True)
        # Dimensions of each facade patch in the atlas (in pixels)
        self.patch_w = 256
        self.patch_h = 128

    def calculate_wall_normal(self, p1: list[float], p2: list[float], centroid: list[float]) -> tuple[float, float]:
        """Computes the outward-facing 2D normal vector of a facade wall."""
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        
        # Normals are (-dy, dx) and (dy, -dx)
        n1 = (-dy, dx)
        n2 = (dy, -dx)
        
        # Choose the normal that points away from the block centroid (outward normal)
        mid_x = (p1[0] + p2[0]) / 2.0
        mid_y = (p1[1] + p2[1]) / 2.0
        
        v_out_x = mid_x - centroid[0]
        v_out_y = mid_y - centroid[1]
        
        # Dot product
        dot1 = n1[0]*v_out_x + n1[1]*v_out_y
        
        chosen_n = n1 if dot1 > 0 else n2
        mag = math.sqrt(chosen_n[0]**2 + chosen_n[1]**2)
        if mag < 1e-5:
            return (0.0, 1.0)
        return (chosen_n[0]/mag, chosen_n[1]/mag)

    def rectify_facade_patch(self, 
                             pano_img: Image.Image, 
                             pano_x: float, 
                             pano_y: float, 
                             pano_heading: float, 
                             heading_correction: float, 
                             p1: list[float], 
                             p2: list[float], 
                             height_meters: float) -> Image.Image:
        """
        Performs mathematically rigorous spherical-to-planar perspective rectification.
        Given a georeferenced wall segment, it projects the equirectangular panorama 
        onto the 3D wall plane, straightening curved walls and correcting heading errors.
        """
        W_pano, H_pano = pano_img.size
        img_np = np.array(pano_img)
        
        # Create coordinate grids
        v_coords, u_coords = np.meshgrid(np.arange(self.patch_h), np.arange(self.patch_w), indexing='ij')
        
        # Normalized texture coordinates (0.0 to 1.0)
        u = u_coords / (self.patch_w - 1)
        v = (self.patch_h - 1 - v_coords) / (self.patch_h - 1)  # Flip Y: v=0 is ground, v=1 is top
        
        # 3D points on the planar facade facade segment
        X = p1[0] + u * (p2[0] - p1[0])
        Y = p1[1] + u * (p2[1] - p1[1])
        Z = v * height_meters
        
        # Camera center coordinates (height z_c = 2.5 meters above road center)
        z_c = 2.5
        
        # 3D offset relative to camera
        dx = X - pano_x
        dy = Y - pano_y
        dz = Z - z_c
        
        # Radial distance in the horizontal plane
        r_2d = np.sqrt(dx**2 + dy**2)
        r_2d = np.maximum(r_2d, 1e-3)  # Prevent division by zero
        
        # Spherical mapping
        theta = np.arctan2(dy, dx)
        phi = np.arctan2(dz, r_2d)
        
        # Global camera heading (corrected by VP heading offset)
        theta_heading = math.radians((pano_heading + heading_correction) % 360.0)
        
        # Relative yaw angle mapping to [-\pi, \pi]
        theta_rel = (theta - theta_heading + np.pi) % (2 * np.pi) - np.pi
        
        # Map spherical angles to pixel coordinates in equirectangular image
        U = ((theta_rel + np.pi) / (2 * np.pi)) * W_pano
        # Assuming the vertical field of view is 90 degrees (cropped $\pm 45^\circ$)
        V = H_pano * (0.5 - phi / (np.pi / 2.0))
        
        # Wrap horizontal and clamp vertical bounds
        U = np.mod(U, W_pano)
        V = np.clip(V, 0, H_pano - 1)
        
        # Vectorized bilinear interpolation for high visual quality
        U0 = np.floor(U).astype(np.int32)
        U1 = np.mod(U0 + 1, W_pano)
        V0 = np.floor(V).astype(np.int32)
        V1 = np.clip(V0 + 1, 0, H_pano - 1)
        
        wu = U - U0
        wv = V - V0
        
        # Add channel dimension for NumPy broadcasting
        wu = np.expand_dims(wu, axis=-1)
        wv = np.expand_dims(wv, axis=-1)
        
        # Sample the 4 neighboring pixels
        c00 = img_np[V0, U0]
        c10 = img_np[V0, U1]
        c01 = img_np[V1, U0]
        c11 = img_np[V1, U1]
        
        # Perform interpolation
        patch_np = (1 - wv) * ((1 - wu) * c00 + wu * c10) + wv * ((1 - wu) * c01 + wu * c11)
        
        return Image.fromarray(patch_np.astype(np.uint8))

    def evaluate_sharpness(self, img: Image.Image) -> float:
        """Computes the sharpness of an image patch using the variance of the Laplacian."""
        np_img = np.array(img.convert("L"))
        return float(cv2.Laplacian(np_img, cv2.CV_64F).var())

    def crop_facade_patch(self, 
                          pano_img: Image.Image, 
                          side: str, 
                          is_2009: bool) -> Image.Image:
        """Fallback quadrant crop for backwards compatibility with tests."""
        width, height = pano_img.size
        if side == "left":
            crop_box = (1920, 160, 2560, 480)
        else:
            crop_box = (640, 160, 1280, 480)
        cropped = pano_img.crop(crop_box)
        facade_crop = cropped.crop((0, 80, 640, 320))
        return facade_crop.resize((self.patch_w, self.patch_h), Image.Resampling.BILINEAR)

    def process_block_textures(self, 
                              block: dict, 
                              pano_registry: dict) -> dict:
        """
        Creates a texture atlas for a single urban block.
        Iterates over the block polygon segments (walls), matches candidate cameras,
        selects the best 2009-consistent viewpoint, and rectifies the facade.
        """
        polygon = block["polygon"]
        centroid = block["centroid"]
        block_id = block["block_id"]
        cameras = block["camera_assignments"]
        
        # Number of facade walls
        num_walls = len(polygon) - 1
        facade_patches = []
        traceability_log = []
        
        print(f"[Texturing] Processing textures for {block_id} (num_walls={num_walls})...")
        
        # Default placeholder patch (neutral stucco wall color)
        default_patch = Image.new("RGB", (self.patch_w, self.patch_h), (210, 200, 190))
        draw_def = ImageDraw.Draw(default_patch)
        # Draw a simple brick-like joint pattern on placeholder
        for y in range(0, self.patch_h, 16):
            draw_def.line([0, y, self.patch_w, y], fill=(225, 215, 205), width=1)
            offset = 16 if (y % 32 == 0) else 0
            for x in range(offset, self.patch_w, 32):
                draw_def.line([x, y, x, y + 16], fill=(225, 215, 205), width=1)
        
        # Map unique accepted panoramas from registry to their local Cartesian positions
        pano_positions = {}
        for p_id, p_data in pano_registry.items():
            px, py = gps_to_local(p_data["latitude"], p_data["longitude"])
            pano_positions[p_id] = {
                "x": px,
                "y": py,
                "pano_id": p_data["pano_id"],
                "heading": p_data.get("corrected_road_heading", p_data.get("road_heading", 0.0)),
                "heading_correction": p_data.get("heading_correction", 0.0),
                "image": p_data["image"],
                "temporal_probability": p_data.get("temporal_probability", 1.0)
            }
            
        for w_idx in range(num_walls):
            p1 = polygon[w_idx]
            p2 = polygon[w_idx + 1]
            surface_id = f"{block_id}_facade_{w_idx}"
            
            # Wall properties
            wall_mid_x = (p1[0] + p2[0]) / 2.0
            wall_mid_y = (p1[1] + p2[1]) / 2.0
            wall_normal = self.calculate_wall_normal(p1, p2, centroid)
            
            best_score = -1.0
            best_patch = None
            best_obs_meta = {}
            
            # Find the best observing panorama in the entire local Cartesian space!
            # (Observation-Driven Sparse Reconstruction: any nearby panorama can observe the facade)
            for p_id, p_meta in pano_positions.items():
                # Strict Temporal Constraint: only use 2009-consistent images
                if p_meta["temporal_probability"] < 0.70:
                    continue
                    
                # 1. Distance check
                dx = wall_mid_x - p_meta["x"]
                dy = wall_mid_y - p_meta["y"]
                dist = math.sqrt(dx*dx + dy*dy)
                if dist > 40.0:  # Skip panoramas that are too far
                    continue
                    
                # 2. Angle of incidence score (visibility check)
                # Outward normal and ray from wall mid to camera should face each other
                v_cam = (p_meta["x"] - wall_mid_x, p_meta["y"] - wall_mid_y)
                mag_v = math.sqrt(v_cam[0]**2 + v_cam[1]**2)
                if mag_v < 1e-5:
                    continue
                v_cam_norm = (v_cam[0]/mag_v, v_cam[1]/mag_v)
                
                # Dot product (should be positive because wall normal points OUTWARD,
                # and camera is OUTSIDE looking inward at the wall facade)
                cos_phi = wall_normal[0]*v_cam_norm[0] + wall_normal[1]*v_cam_norm[1]
                
                if cos_phi <= 0.15:  # Skip highly oblique views (angle > 80 degrees)
                    continue
                    
                dist_score = 1.0 / (dist + 1.0)
                
                # Perform exact perspective rectification!
                candidate_patch = self.rectify_facade_patch(
                    pano_img=p_meta["image"],
                    pano_x=p_meta["x"],
                    pano_y=p_meta["y"],
                    pano_heading=p_meta["heading"],
                    heading_correction=p_meta["heading_correction"],
                    p1=p1,
                    p2=p2,
                    height_meters=block.get("height", 6.5)
                )
                
                sharpness_score = self.evaluate_sharpness(candidate_patch)
                
                # Aggregate quality score
                score = cos_phi * dist_score * (sharpness_score + 1.0)
                
                if score > best_score:
                    best_score = score
                    best_patch = candidate_patch
                    best_obs_meta = {
                        "pano_id": p_meta["pano_id"],
                        "station_id": p_id,
                        "angle_deg": math.degrees(math.acos(np.clip(cos_phi, -1.0, 1.0))),
                        "distance_meters": dist,
                        "sharpness_val": sharpness_score
                    }
                    
            # Wrap up optimal choice
            if best_patch is not None:
                facade_patches.append(best_patch)
                traceability_log.append({
                    "surface_id": surface_id,
                    "source": "image",
                    **best_obs_meta
                })
            else:
                facade_patches.append(default_patch)
                traceability_log.append({
                    "surface_id": surface_id,
                    "source": "procedural_fallback",
                    "pano_id": "fallback_stucco",
                    "station_id": "none",
                    "angle_deg": 0.0,
                    "distance_meters": 0.0,
                    "sharpness_val": 0.0
                })
                
        # 3. Stitch facade patches into a single vertical Texture Atlas for this block
        atlas_w = self.patch_w
        atlas_h = max(1, num_walls) * self.patch_h
        atlas_img = Image.new("RGB", (atlas_w, atlas_h), (80, 80, 80))
        
        for idx, patch in enumerate(facade_patches):
            atlas_img.paste(patch, (0, idx * self.patch_h))
            
        # Add a flat stucco texture for the roof
        roof_img = Image.new("RGB", (self.patch_w, self.patch_h), (160, 160, 160)) # Grey flat roof
        atlas_img_extended = Image.new("RGB", (atlas_w, atlas_h + self.patch_h), (80, 80, 80))
        atlas_img_extended.paste(atlas_img, (0, 0))
        atlas_img_extended.paste(roof_img, (0, atlas_h))
        atlas_img = atlas_img_extended
        
        # Save Atlas Image
        atlas_filename = f"{block_id}_atlas.png"
        atlas_path = os.path.join(self.export_dir, atlas_filename)
        atlas_img.save(atlas_path)
        
        # 4. Generate UV Mappings coordinates
        total_rows = num_walls + 1
        uv_mappings = {}
        
        for w_idx in range(num_walls):
            surface_id = f"{block_id}_facade_{w_idx}"
            
            y_b = (total_rows - 1 - w_idx) / total_rows
            y_t = (total_rows - w_idx) / total_rows
            
            uv_mappings[surface_id] = [
                [0.0, y_b], # Bottom-Left
                [1.0, y_b], # Bottom-Right
                [1.0, y_t], # Top-Right
                [0.0, y_t]  # Top-Left
            ]
            
        # Roof UV mapping
        y_b = 0.0
        y_t = 1.0 / total_rows
        roof_uvs = []
        for idx in range(num_walls + 1):
            angle = 2 * math.pi * idx / (num_walls + 1)
            ru = 0.5 + 0.5 * math.cos(angle)
            rv = y_b + (y_t - y_b) * (0.5 + 0.5 * math.sin(angle))
            roof_uvs.append([ru, rv])
            
        uv_mappings[f"{block_id}_roof"] = roof_uvs
        
        return {
            "block_id": block_id,
            "atlas_filename": atlas_filename,
            "atlas_path": os.path.abspath(atlas_path),
            "uv_mappings": uv_mappings,
            "traceability": traceability_log
        }
