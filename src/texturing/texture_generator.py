import math
import os
import cv2
import numpy as np
from PIL import Image

class TextureGenerator:
    """
    Builds a unified texture atlas per urban block (manzana) using only 
    temporally consistent (2009-validated) imagery. Projects perspective facades,
    evaluates quality (angle of incidence, distance, sharpness), and maps UV coordinates.
    """
    def __init__(self, export_dir: str = "export/textures"):
        self.export_dir = export_dir
        os.makedirs(export_dir, exist_ok=True)
        # Dimensions of each facade patch in the atlas (in pixels)
        self.patch_w = 256
        self.patch_h = 128

    def calculate_wall_normal(self, p1: list[float], p2: list[float], centroid: list[float]) -> tuple[float, float]:
        """
        Computes the outward-facing 2D normal vector of a facade wall.
        """
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        
        # Normals are (-dy, dx) and (dy, -dx)
        n1 = (-dy, dx)
        n2 = (dy, -dx)
        
        # We choose the normal that points away from the block centroid (outward normal)
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

    def crop_facade_patch(self, 
                          pano_img: Image.Image, 
                          side: str, 
                          is_2009: bool) -> Image.Image:
        """
        Crops the perspective facade patch from the equirectangular panorama.
        - 'left': centered at West direction (theta ≈ 270 deg, pixel column ≈ 2240)
        - 'right': centered at East direction (theta ≈ 90 deg, pixel column ≈ 960)
        We extract the perspective viewpoint quadrant and scale it to our target patch dimensions.
        """
        width, height = pano_img.size
        
        # Left wall lies in the 270 heading quadrant: pixels [1920, 2560]
        # Right wall lies in the 90 heading quadrant: pixels [640, 1280]
        if side == "left":
            crop_box = (1920, 160, 2560, 480)
        else:
            crop_box = (640, 160, 1280, 480)
            
        cropped = pano_img.crop(crop_box)
        
        # Further crop the central facade strip (the walls run horizontally)
        # Standard wall elevation is centered on the horizon line
        facade_crop = cropped.crop((0, 80, 640, 320))
        
        # Resize to standard patch dimensions
        return facade_crop.resize((self.patch_w, self.patch_h), Image.Resampling.BILINEAR)

    def evaluate_sharpness(self, img: Image.Image) -> float:
        """Computes the sharpness of an image patch using the variance of the Laplacian."""
        np_img = np.array(img.convert("L"))
        return float(cv2.Laplacian(np_img, cv2.CV_64F).var())

    def process_block_textures(self, 
                              block: dict, 
                              pano_registry: dict) -> dict:
        """
        Creates a texture atlas for a single urban block.
        Iterates over the block polygon segments (walls), matches candidate cameras,
        selects the best 2009-consistent viewpoint, and stiches the atlas.
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
        draw_def = Image.new("RGB", (self.patch_w, self.patch_h), (210, 200, 190))
        # Draw a simple brick-like joint pattern on placeholder
        for y in range(0, self.patch_h, 16):
            for x in range(0, self.patch_w, 32):
                draw_def.paste(Image.new("RGB", (30, 14), (220, 210, 200)), (x, y))
        default_patch = draw_def
        
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
            
            # Evaluate all cameras that are assigned to this block
            for cam in cameras:
                s_id = cam["station_id"]
                pano_data = pano_registry.get(s_id)
                
                if not pano_data:
                    continue
                    
                # Strict Temporal Constraint: only use 2009-consistent images
                if pano_data.get("temporal_probability", 0.0) < 0.70:
                    continue
                    
                # 1. Angle of incidence score
                # Optical axis direction of the viewpoint looking at the block
                cam_heading_rad = math.radians(cam["camera_heading"])
                opt_axis = (math.cos(cam_heading_rad), math.sin(cam_heading_rad))
                
                # Dot product between outward wall normal and camera view vector (should be negative because they face each other)
                # Cosine of angle: n . (-opt_axis)
                cos_phi = wall_normal[0]*(-opt_axis[0]) + wall_normal[1]*(-opt_axis[1])
                
                # The camera faces the wall if cos_phi > 0.0
                if cos_phi <= 0.15: # Skip highly oblique views (angle > 80 degrees)
                    continue
                    
                # 2. Distance score
                dx = wall_mid_x - cam["x"]
                dy = wall_mid_y - cam["y"]
                dist = math.sqrt(dx*dx + dy*dy)
                dist_score = 1.0 / (dist + 1.0)
                
                # Crop candidate patch to evaluate sharpness
                candidate_patch = self.crop_facade_patch(pano_data["image"], cam["side"], True)
                sharpness_score = self.evaluate_sharpness(candidate_patch)
                
                # Aggregate quality score (Angle * Distance * Sharpness)
                score = cos_phi * dist_score * (sharpness_score + 1.0)
                
                if score > best_score:
                    best_score = score
                    best_patch = candidate_patch
                    best_obs_meta = {
                        "pano_id": pano_data.get("pano_id"),
                        "station_id": s_id,
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
        # Size will be: width = patch_w, height = num_walls * patch_h
        atlas_w = self.patch_w
        atlas_h = max(1, num_walls) * self.patch_h
        atlas_img = Image.new("RGB", (atlas_w, atlas_h), (80, 80, 80))
        
        for idx, patch in enumerate(facade_patches):
            atlas_img.paste(patch, (0, idx * self.patch_h))
            
        # Add a flat stucco texture for the roof (top face of the block extrusion)
        # Stored as the last row in the atlas
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
        # An extruded block mesh has:
        # - num_walls vertical facade faces
        # - 1 horizontal roof face (top polygon)
        # Each face is made of vertices.
        # Let's map UV coordinate loops:
        # In UV space, coordinates are [0.0, 1.0] from bottom-left corner.
        # Our atlas has (num_walls + 1) rows. Row index 0 is first wall at y-top of the image,
        # Row index num_walls is the roof.
        # Height of each row is 1.0 / (num_walls + 1)
        total_rows = num_walls + 1
        uv_mappings = {}
        
        for w_idx in range(num_walls):
            surface_id = f"{block_id}_facade_{w_idx}"
            
            # Row bounding box in UV space
            # Note: PIL y increases downwards, but Blender UV y increases upwards!
            # Let's write Blender-compatible UV coordinates:
            # y_bottom = (total_rows - 1 - w_idx) / total_rows
            # y_top = (total_rows - w_idx) / total_rows
            # We map the 4 corners of the rectangular facade face (vertex loop: Bottom-Left, Bottom-Right, Top-Right, Top-Left)
            y_b = (total_rows - 1 - w_idx) / total_rows
            y_t = (total_rows - w_idx) / total_rows
            
            uv_mappings[surface_id] = [
                [0.0, y_b], # Bottom-Left
                [1.0, y_b], # Bottom-Right
                [1.0, y_t], # Top-Right
                [0.0, y_t]  # Top-Left
            ]
            
        # Roof UV mapping (mapping to the roof patch at the very bottom of the image, row index = num_walls)
        # Maps the entire top polygon vertices into the roof patch
        y_b = 0.0
        y_t = 1.0 / total_rows
        roof_uvs = []
        for idx in range(num_walls + 1):
            # Map polygon vertices circular-wise inside the [0.0, 1.0] roof UV patch
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
