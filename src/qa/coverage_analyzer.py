# Purpose: Analyzes texture coverage percentage of the reconstructed facade texture.
# Inputs: Texture PNG file path.
# Outputs: Coverage percentage analysis report.
# Responsibilities: Computes ratio of non-transparent pixels to total pixels in the texture canvas.
# Dependencies: os, numpy, PIL

import os
import numpy as np
from PIL import Image

class CoverageAnalyzer:
    """
    Computes the percentage of the facade texture area that contains valid, non-transparent pixels.
    """
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir

    def analyze_coverage(self, texture_path: str) -> dict:
        """
        Computes the ratio of non-transparent pixels (Alpha > 0) in the texture file.
        """
        if not os.path.exists(texture_path):
            raise FileNotFoundError(f"Texture file not found: {texture_path}")
            
        img = Image.open(texture_path)
        img_np = np.array(img)
        
        # Check if image has an alpha channel
        if img_np.shape[2] == 4:
            alpha = img_np[:, :, 3]
            non_transparent_pixels = int(np.count_nonzero(alpha > 0))
        else:
            # If no alpha, assume fully covered if not plain black or transparent
            gray = np.mean(img_np[:, :, :3], axis=2)
            non_transparent_pixels = int(np.count_nonzero(gray > 0))
            
        total_pixels = int(img_np.shape[0] * img_np.shape[1])
        coverage_pct = float((non_transparent_pixels / total_pixels) * 100.0)
        status = "PASS" if coverage_pct >= 50.0 else "FAIL" # 50% threshold for raw texture, 90% for final rendering
        
        return {
            "coverage_pct": coverage_pct,
            "total_pixels": total_pixels,
            "valid_pixels": non_transparent_pixels,
            "status": status
        }
