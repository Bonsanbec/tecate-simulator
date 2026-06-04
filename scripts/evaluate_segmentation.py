# Purpose: Evaluates the semantic segmentation agent against the test set and outputs the QG-05 quality report.
# Inputs: Test directory containing images/ and masks/, output report file path.
# Outputs: Generates QG05_report.json detailing mean IoU and inference speed.
# Responsibilities: Executes inference, validates output shapes, computes Intersection-over-Union (IoU) metrics per class, and writes the validation status.
# Dependencies: argparse, os, json, time, numpy, PIL, datetime, src.segmentation.segmentation_agent

import argparse
import os
import json
import time
from datetime import datetime
import numpy as np
from PIL import Image
from src.segmentation.segmentation_agent import FacadeSegmentationAgent

def compute_iou(pred: np.ndarray, target: np.ndarray, class_id: int) -> float:
    """Computes Intersection-over-Union (IoU) for a specific class ID."""
    pred_mask = (pred == class_id)
    target_mask = (target == class_id)
    
    intersection = np.logical_and(pred_mask, target_mask).sum()
    union = np.logical_or(pred_mask, target_mask).sum()
    
    if union == 0:
        return 1.0  # Perfect match for absence of class
    return float(intersection) / float(union)

def main():
    parser = argparse.ArgumentParser(description="Evaluate semantic segmentation model (QG-05)")
    parser.add_argument("--test-dir", type=str, default="data/case_study/segmentation_test_set",
                        help="Path to segmentation test set directory")
    parser.add_argument("--output", type=str, default="data/case_study/QG05_report.json",
                        help="Path to save QG05 report JSON")
    args = parser.parse_args()
    
    print(f"[evaluate_segmentation] Evaluating test set under: {args.test_dir}...")
    
    images_dir = os.path.join(args.test_dir, "images")
    masks_dir = os.path.join(args.test_dir, "masks")
    
    if not os.path.exists(images_dir) or not os.path.exists(masks_dir):
        raise FileNotFoundError(f"Test folders not found in {args.test_dir}")
        
    image_files = sorted([f for f in os.listdir(images_dir) if f.endswith(".png")])
    if len(image_files) < 10:
        print(f"[evaluate_segmentation] Warning: expected >= 10 test images, found {len(image_files)}.")
        
    agent = FacadeSegmentationAgent()
    
    inference_times = []
    class_ious = {
        "wall": [],
        "window": [],
        "door": [],
        "sky": []
    }
    
    shape_match_ok = True
    
    for img_file in image_files:
        img_path = os.path.join(images_dir, img_file)
        mask_path = os.path.join(masks_dir, img_file)
        
        # Load image & target mask
        img = Image.open(img_path)
        w, h = img.size
        
        target_mask = np.array(Image.open(mask_path))
        
        # Run prediction and measure time
        start_time = time.time()
        pred_mask = agent.predict(img_path)
        elapsed = time.time() - start_time
        inference_times.append(elapsed)
        
        # Check shape match
        if pred_mask.shape != (h, w):
            shape_match_ok = False
            print(f"[Error] Prediction shape {pred_mask.shape} does not match image shape {(h, w)} for {img_file}!")
            
        # Compute IoUs (0: wall, 1: window, 2: door, 3: sky)
        class_ious["wall"].append(compute_iou(pred_mask, target_mask, 0))
        class_ious["window"].append(compute_iou(pred_mask, target_mask, 1))
        class_ious["door"].append(compute_iou(pred_mask, target_mask, 2))
        class_ious["sky"].append(compute_iou(pred_mask, target_mask, 3))
        
    # Calculate average metrics
    avg_inference_time = float(np.mean(inference_times))
    mean_class_ious = {c: float(np.mean(vals)) for c, vals in class_ious.items()}
    mean_iou = float(np.mean(list(mean_class_ious.values())))
    
    # Check pass criteria
    iou_passed = mean_iou > 0.70
    speed_passed = avg_inference_time < 30.0
    
    status = "PASS" if (iou_passed and speed_passed and shape_match_ok) else "FAIL"
    
    report = {
        "gate_id": "QG-05",
        "status": status,
        "evaluation_timestamp": datetime.utcnow().isoformat() + "Z",
        "metrics": {
            "mean_iou": mean_iou,
            "class_ious": mean_class_ious,
            "mean_inference_time_s": avg_inference_time,
            "shape_match": shape_match_ok
        },
        "thresholds": {
            "min_mean_iou": 0.70,
            "max_inference_time_s": 30.0
        },
        "blocking_phases": ["P06"],
        "notes": f"Segmentation evaluation completed. Mean IoU: {mean_iou:.4f}, Mean Speed: {avg_inference_time:.4f}s per image."
    }
    
    # Ensure directory for output exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)
        
    print(f"[evaluate_segmentation] Saved QG-05 report to {args.output}")
    print(f"[evaluate_segmentation] Overall status: {status} (Mean IoU: {mean_iou:.4f}, Speed: {avg_inference_time:.4f}s)")

if __name__ == "__main__":
    main()
