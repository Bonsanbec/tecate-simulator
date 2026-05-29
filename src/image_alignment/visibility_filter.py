import cv2
import numpy as np
from PIL import Image

def analyze_visibility_quality(pil_img: Image.Image) -> tuple[float, dict]:
    """
    Analyzes a flat perspective observation image using OpenCV to estimate a
    Frontal Visibility Quality Score (0.0 to 1.0) and generates diagnostic masks.
    
    Heuristics applied:
    - Sky detection (top region, high value / blue tint)
    - Pavement detection (bottom region, low variance gray)
    - Horizon suppression (midline zone damping)
    - Vertical edge emphasis (Sobel X edge density)
    - Connected component cleanup (noise suppression)
    - Obstruction penalties (green foliage, horizontal vehicle edges)
    """
    # Convert PIL Image to OpenCV BGR and HSV
    cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    hsv = cv2.cvtColor(cv_img, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    
    H, W = gray.shape
    total_pixels = W * H
    
    # 1. Sky Rejection
    # Sky is expected in the upper 55% of the image.
    # It is typically very bright (high V) or blueish (H in [90, 135])
    sky_mask = np.zeros_like(gray)
    upper_zone = hsv[0:int(0.55*H), 0:W]
    
    # Thresholds: Bright white/grey sky or blue sky
    blue_sky = cv2.inRange(upper_zone, np.array([90, 20, 140]), np.array([135, 255, 255]))
    bright_sky = cv2.inRange(upper_zone, np.array([0, 0, 205]), np.array([180, 50, 255]))
    combined_sky = cv2.bitwise_or(blue_sky, bright_sky)
    sky_mask[0:int(0.55*H), 0:W] = combined_sky
    
    sky_ratio = float(np.sum(sky_mask > 0) / (W * int(0.55*H)))
    sky_ratio = min(1.0, sky_ratio)
    
    # 2. Pavement Rejection
    # Pavement is expected in the bottom 45% of the image.
    # It is typically homogeneous, grey (S < 40), and low-variance.
    pavement_mask = np.zeros_like(gray)
    lower_zone = hsv[int(0.55*H):H, 0:W]
    gray_pavement = cv2.inRange(lower_zone, np.array([0, 0, 50]), np.array([180, 45, 190]))
    pavement_mask[int(0.55*H):H, 0:W] = gray_pavement
    
    # Apply a local variance check to refine pavement (pavement has very low texture variance)
    lower_gray = gray[int(0.55*H):H, 0:W]
    if lower_gray.size > 0:
        kernel = np.ones((5, 5), np.uint8)
        local_mean = cv2.blur(lower_gray, (5, 5))
        local_sq_mean = cv2.blur(lower_gray.astype(np.float32)**2, (5, 5))
        local_var = local_sq_mean - local_mean.astype(np.float32)**2
        low_variance_mask = (local_var < 150.0).astype(np.uint8) * 255
        refined_pavement = cv2.bitwise_and(gray_pavement, low_variance_mask)
        pavement_mask[int(0.55*H):H, 0:W] = refined_pavement
    
    pavement_ratio = float(np.sum(pavement_mask > 0) / (W * (H - int(0.55*H))))
    pavement_ratio = min(1.0, pavement_ratio)
    
    # 3. Vertical Edge Emphasis & Horizon Suppression
    # Calculate vertical edges using Sobel X filter
    sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    abs_sobelx = np.abs(sobelx)
    
    # Threshold to binary edges
    _, v_edges = cv2.threshold(abs_sobelx, 35, 255, cv2.THRESH_BINARY)
    v_edges = v_edges.astype(np.uint8)
    
    # Suppress horizon midline to avoid street-building transition line dominant edges
    horizon_start = int(0.48 * H)
    horizon_end = int(0.53 * H)
    v_edges[horizon_start:horizon_end, :] = 0
    
    # Suppress edges in sky and pavement regions
    v_edges = cv2.bitwise_and(v_edges, cv2.bitwise_not(sky_mask))
    v_edges = cv2.bitwise_and(v_edges, cv2.bitwise_not(pavement_mask))
    
    # 4. Connected Component Cleanup (morphology to keep only significant vertical structures)
    kernel_clean = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 3))
    cleaned_edges = cv2.morphologyEx(v_edges, cv2.MORPH_OPEN, kernel_clean)
    
    # Calculate density of clean vertical edges in the "facade zone" (middle region)
    facade_zone = cleaned_edges[int(0.2*H):int(0.8*H), :]
    edge_density = float(np.sum(facade_zone > 0) / facade_zone.size) if facade_zone.size > 0 else 0.0
    
    # Map raw density to score: densities > 0.04 are excellent facade structures
    edge_score = min(1.0, edge_density / 0.045)
    
    # 5. Obstruction Penalties
    obstruction_penalty = 0.0
    
    # A. Foliage / Tree Detection (Green color checks)
    green_mask = cv2.inRange(hsv, np.array([35, 30, 40]), np.array([85, 255, 220]))
    # Suppress green mask in pavement zone
    green_mask[int(0.75*H):H, :] = 0
    green_ratio = float(np.sum(green_mask > 0) / total_pixels)
    if green_ratio > 0.05:
        # Penalize up to 0.45 for heavy foliage coverage
        obstruction_penalty += min(0.45, green_ratio * 1.5)
        
    # B. Vehicle / Foreground Clutter (dense horizontal edges in bottom region)
    sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    abs_sobely = np.abs(sobely)
    _, h_edges = cv2.threshold(abs_sobely, 30, 255, cv2.THRESH_BINARY)
    h_edges = h_edges.astype(np.uint8)
    
    # Vehicles have dense horizontal edges in y = 0.6*H to 0.85*H
    vehicle_zone = h_edges[int(0.6*H):int(0.85*H), :]
    h_density = float(np.sum(vehicle_zone > 0) / vehicle_zone.size) if vehicle_zone.size > 0 else 0.0
    if h_density > 0.08:
        # Penalize up to 0.35 for large horizontal vehicle profiles
        obstruction_penalty += min(0.35, (h_density - 0.08) * 2.0)
        
    obstruction_penalty = min(0.8, obstruction_penalty)
    
    # 6. Final Combined Quality Score
    # Highly robust multiplicative score
    quality_score = edge_score * (1.0 - 0.7 * sky_ratio) * (1.0 - 0.7 * pavement_ratio) * (1.0 - obstruction_penalty)
    quality_score = float(np.clip(quality_score, 0.01, 1.0))
    
    # Create debug diagnostic overlay image
    # Red = Sky Mask, Blue = Pavement Mask, Green = Detected Facade Edges
    debug_overlay = np.zeros((H, W, 3), dtype=np.uint8)
    debug_overlay[sky_mask > 0] = [0, 0, 180]  # Red for Sky
    debug_overlay[pavement_mask > 0] = [180, 0, 0]  # Blue for Pavement
    debug_overlay[cleaned_edges > 0] = [0, 255, 0]  # Green for Facade Edges
    
    # Blend with original image
    np_orig = np.array(pil_img)
    debug_blended = cv2.addWeighted(np_orig, 0.65, debug_overlay, 0.35, 0)
    
    # Draw quality score label on the debug image
    cv2.putText(
        debug_blended, 
        f"Score: {quality_score:.3f} | Edges: {edge_density:.4f} | Sky: {sky_ratio:.2f}",
        (10, 25), 
        cv2.FONT_HERSHEY_SIMPLEX, 
        0.6, 
        (255, 255, 255), 
        2, 
        cv2.LINE_AA
    )
    
    diagnostics = {
        "quality_score": quality_score,
        "sky_ratio": sky_ratio,
        "pavement_ratio": pavement_ratio,
        "vertical_edge_density": edge_density,
        "obstruction_penalty": obstruction_penalty,
        "debug_img": Image.fromarray(debug_blended)
    }
    
    return quality_score, diagnostics
