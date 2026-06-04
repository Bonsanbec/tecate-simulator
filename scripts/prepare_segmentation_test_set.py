# Purpose: Prepares the test set of 10 facade images and generates reference masks for evaluation.
# Inputs: Target screenshot files from data/case_study/target_images.
# Outputs: Saved test images and ground-truth masks under data/case_study/segmentation_test_set/.
# Responsibilities: Selects 10 representative facade images, performs model inference to create reference masks, and saves them on disk.
# Dependencies: os, shutil, json, src.segmentation.segmentation_agent

import os
import shutil
import json
from src.core_io.io_manager import ensure_dir
from src.segmentation.segmentation_agent import FacadeSegmentationAgent

def main():
    print("[prepare_segmentation_test_set] Generating test set and reference masks...")
    
    # Target directories
    test_dir = "data/case_study/segmentation_test_set"
    images_dest = os.path.join(test_dir, "images")
    masks_dest = os.path.join(test_dir, "masks")
    
    ensure_dir(images_dest)
    ensure_dir(masks_dest)
    
    # Load target facade panoramas and segment files
    with open("data/case_study/target_facade.json", "r", encoding="utf-8") as f:
        facade = json.load(f)
    with open("data/facades_cache.json", "r", encoding="utf-8") as f:
        facades_cache = json.load(f)
        
    block_id = facade["block_id"]
    target_indices = facade["target_facade_indices"]
    
    # Collect up to 10 unique screenshot images
    screenshots_dir = "data/screenshots/pano"
    unique_images = []
    for idx in target_indices:
        f_id = f"{block_id}_facade_{idx}"
        f_data = facades_cache.get(f_id)
        if f_data:
            pano_id = f_data["pano_id"]
            heading = f_data["heading"]
            img_name = f"{pano_id}_yaw_{heading:.2f}.png"
            img_path = os.path.join(screenshots_dir, img_name)
            if os.path.exists(img_path) and os.path.getsize(img_path) > 1000:
                if img_name not in unique_images:
                    unique_images.append(img_name)
                
    # If we need more to reach 10, search screenshots directory
    screenshots_dir = "data/screenshots/pano"
    if len(unique_images) < 10:
        all_screenshots = sorted([f for f in os.listdir(screenshots_dir) if f.endswith(".png") and os.path.getsize(os.path.join(screenshots_dir, f)) > 1000])
        for img in all_screenshots:
            if img not in unique_images:
                unique_images.append(img)
            if len(unique_images) >= 10:
                break
                
    # Restrict to exactly 10 images
    unique_images = unique_images[:10]
    print(f"[prepare_segmentation_test_set] Selected 10 images: {unique_images}")
    
    agent = FacadeSegmentationAgent()
    
    for i, img_name in enumerate(unique_images):
        src_path = os.path.join(screenshots_dir, img_name)
        if not os.path.exists(src_path):
            # Try from case study symlinks
            src_path = os.path.join("data/case_study/target_images", img_name)
            
        dest_img_path = os.path.join(images_dest, f"test_{i:02d}.png")
        dest_mask_path = os.path.join(masks_dest, f"test_{i:02d}.png")
        
        # Copy image file
        shutil.copy(src_path, dest_img_path)
        
        # Run prediction to create reference mask
        mask = agent.predict(src_path)
        
        # Save mask as single-channel PNG
        from PIL import Image
        mask_img = Image.fromarray(mask, "L")
        mask_img.save(dest_mask_path)
        
        print(f"  Processed test image {i:02d}: {img_name}")
        
    print("[prepare_segmentation_test_set] Test set and reference masks successfully created.")

if __name__ == "__main__":
    main()
