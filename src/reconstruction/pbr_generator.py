import os
import json
import cv2
import numpy as np
from PIL import Image

class PBRGenerator:
    """
    Generates height, normal, and roughness maps, and packs them into Godot-compatible PNG channels:
      1. Texture_Albedo_Roughness: RGB = Albedo, Alpha = Roughness
      2. Texture_Normal_Height: RGB = Normal, Alpha = Height
    Supports per-facade config overrides.
    """
    def __init__(self, config_dir="data/case_study"):
        self.config_dir = config_dir
        
        # Default PBR heuristics mapping (class_name -> dict)
        self.default_heuristics = {
            "wall": {"height": 1.0, "roughness": 0.8, "metallic": 0.0},
            "window": {"height": 0.85, "roughness": 0.1, "metallic": 0.2},
            "door": {"height": 0.90, "roughness": 0.6, "metallic": 0.0}
        }
        
        # Mapping from ADE20K label IDs to our simplified categories
        # 0: wall, 1: building, 8: window, 14: door, 58: door/gate
        self.label_mapping = {
            0: "wall",
            1: "wall",
            8: "window",
            14: "door",
            58: "door"
        }

    def load_material_config(self, facade_id: str) -> dict:
        """
        Loads optional material overrides for a specific facade.
        """
        config_path = os.path.join(self.config_dir, f"{facade_id}_material_config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                print(f"[PBRGenerator] Loaded material overrides for facade '{facade_id}': {config}")
                return config
            except Exception as e:
                print(f"[Warning] Failed to load material config at {config_path}: {e}")
        return {}

    def generate_maps(self, albedo_img: Image.Image, mask: np.ndarray, facade_id: str = None) -> tuple[Image.Image, Image.Image]:
        """
        Given the albedo PIL image and semantic segmentation mask (numpy array of same size),
        generates and returns (albedo_roughness_img, normal_height_img).
        """
        width, height = albedo_img.size
        
        # 1. Load config overrides
        overrides = {}
        if facade_id:
            overrides = self.load_material_config(facade_id)
            
        # Determine base heuristics
        heuristics = {k: v.copy() for k, v in self.default_heuristics.items()}
        if "heuristics" in overrides:
            for cat, vals in overrides["heuristics"].items():
                if cat in heuristics:
                    heuristics[cat].update(vals)

        # 2. Check if a custom height mask is provided in the config
        custom_height_map = None
        if "custom_height_mask_path" in overrides:
            custom_path = overrides["custom_height_mask_path"]
            if os.path.exists(custom_path):
                try:
                    custom_img = Image.open(custom_path).convert("L")
                    # Resize to match
                    if custom_img.size != (width, height):
                        custom_img = custom_img.resize((width, height), Image.Resampling.BILINEAR)
                    custom_height_map = np.array(custom_img, dtype=np.float32) / 255.0
                    print(f"[PBRGenerator] Loaded custom height mask from {custom_path}")
                except Exception as e:
                    print(f"[Warning] Failed to load custom height mask: {e}")

        # 3. Create Height and Roughness maps
        height_map = np.ones((height, width), dtype=np.float32)
        roughness_map = np.ones((height, width), dtype=np.float32) * 0.8  # Default to wall roughness
        
        if custom_height_map is not None:
            height_map = custom_height_map
        else:
            # Map semantic mask labels to heights & roughness
            for label, category in self.label_mapping.items():
                cat_heuristics = heuristics[category]
                height_map[mask == label] = cat_heuristics["height"]
                roughness_map[mask == label] = cat_heuristics["roughness"]
                
            # Default fallback for unmapped classes (everything else is wall)
            unmapped = ~np.isin(mask, list(self.label_mapping.keys()))
            height_map[unmapped] = heuristics["wall"]["height"]
            roughness_map[unmapped] = heuristics["wall"]["roughness"]

        # 4. Generate Normal Map from Height Map using Sobel filter
        # Sobel operations require standard 8-bit image or normalized float
        # Scale to [0, 255] for OpenCV Sobel
        h_uint8 = (height_map * 255.0).astype(np.uint8)
        
        # Compute horizontal and vertical gradients
        # Use cv2.Sobel with CV_32F to maintain precision
        sobel_x = cv2.Sobel(h_uint8, cv2.CV_32F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(h_uint8, cv2.CV_32F, 0, 1, ksize=3)
        
        # Calculate normal vectors. Scale factor adjusts depth perception.
        scale = overrides.get("normal_strength", 1.0)
        # Gradient specifies slope; normals are perpendicular
        # nx = -dx, ny = -dy, nz = 1.0 / scale
        nz_factor = 255.0 / scale if scale > 0 else 255.0
        
        nx = -sobel_x
        ny = -sobel_y
        nz = np.ones_like(nx) * nz_factor
        
        # Normalize to unit vectors
        norm = np.sqrt(nx**2 + ny**2 + nz**2)
        norm[norm == 0] = 1.0
        
        nx /= norm
        ny /= norm
        nz /= norm
        
        # Map normal range [-1.0, 1.0] to [0, 255]
        normal_r = ((nx + 1.0) * 127.5).astype(np.uint8)
        normal_g = ((ny + 1.0) * 127.5).astype(np.uint8)
        normal_b = ((nz + 1.0) * 127.5).astype(np.uint8)
        
        normal_rgb = np.stack([normal_r, normal_g, normal_b], axis=-1)

        # 5. Pack textures
        albedo_np = np.array(albedo_img.convert("RGB"))
        roughness_uint8 = (roughness_map * 255.0).astype(np.uint8)
        
        # Pack Albedo & Roughness: RGB = Albedo, Alpha = Roughness
        albedo_roughness = np.zeros((height, width, 4), dtype=np.uint8)
        albedo_roughness[..., :3] = albedo_np
        albedo_roughness[..., 3] = roughness_uint8
        
        # Pack Normal & Height: RGB = Normal, Alpha = Height
        normal_height = np.zeros((height, width, 4), dtype=np.uint8)
        normal_height[..., :3] = normal_rgb
        normal_height[..., 3] = h_uint8
        
        # Convert back to PIL Images
        albedo_roughness_img = Image.fromarray(albedo_roughness, "RGBA")
        normal_height_img = Image.fromarray(normal_height, "RGBA")
        
        return albedo_roughness_img, normal_height_img
