import os
import glob
import sys
from PIL import Image
import numpy as np

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.reconstruction.segmentation_processor import SegmentationProcessor
from src.reconstruction.pbr_generator import PBRGenerator

def main():
    assets_dir = "godot_project/assets/blocks/"
    print(f"[PBR Generator] Scanning for missing normal/height maps in {assets_dir}...")
    
    # Find all virtual facade textures
    pattern = os.path.join(assets_dir, "block_lat_*_virtual_*.png")
    all_textures = sorted(glob.glob(pattern))
    
    # Filter out normal_height maps
    base_textures = [t for t in all_textures if not t.endswith("_normal_height.png") and not t.endswith("_roughness.png")]
    
    print(f"[PBR Generator] Found {len(base_textures)} base facade textures.")
    
    missing_textures = []
    for tex_path in base_textures:
        normal_path = tex_path.replace(".png", "_normal_height.png")
        if not os.path.exists(normal_path):
            missing_textures.append(tex_path)
            
    print(f"[PBR Generator] {len(missing_textures)} textures are missing normal/height maps.")
    if not missing_textures:
        print("[PBR Generator] No missing normal/height maps. Everything is up to date!")
        return
        
    print("[PBR Generator] Initializing HuggingFace SegFormer model and PBR generator...")
    try:
        processor = SegmentationProcessor()
        pbr_gen = PBRGenerator()
    except Exception as init_err:
        print(f"[Error] Failed to initialize model or generator: {init_err}")
        return
        
    success_count = 0
    for idx, tex_path in enumerate(missing_textures):
        normal_path = tex_path.replace(".png", "_normal_height.png")
        print(f"[{idx+1}/{len(missing_textures)}] Processing: {os.path.basename(tex_path)}...")
        try:
            # Load image
            img = Image.open(tex_path).convert("RGB")
            
            # Segment image
            mask = processor.segment_image(img)
            
            # Generate PBR maps
            albedo_rough, normal_height = pbr_gen.generate_maps(img, mask)
            
            # Save packed maps (overwrite albedo with packed albedo+roughness, save normal+height)
            albedo_rough.save(tex_path)
            normal_height.save(normal_path)
            
            success_count += 1
        except Exception as e:
            print(f"[Warning] Failed to generate maps for {tex_path}: {e}")
            
    print(f"[PBR Generator] Finished! Successfully generated {success_count} normal/height maps.")

if __name__ == "__main__":
    main()
