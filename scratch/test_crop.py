from PIL import Image
import numpy as np
import os

def test_crop():
    img_path = "data/screenshots/facades/block_19_middle_facade_0.png"
    img = Image.open(img_path)
    np_img = np.array(img)
    H, W, C = np_img.shape
    
    # Define color-based detectors
    def is_sky(r, g, b):
        return (b > r + 25) and (b > g + 10) and (r < 120) and (g < 150) and (b > 110)
        
    def is_pavement(r, g, b):
        return (abs(r - g) < 20) and (abs(g - b) < 30) and (110 < r < 210) and (105 < g < 200) and (95 < b < 190)
        
    # Scan from top downwards for sky
    y_top = 0
    for y in range(H):
        row = np_img[y, :, 0:3]
        sky_mask = [is_sky(p[0], p[1], p[2]) for p in row]
        sky_pct = sum(sky_mask) / W
        if sky_pct < 0.15:
            y_top = y
            break
            
    # Scan from bottom upwards for pavement
    y_bottom = H - 1
    for y in range(H - 1, -1, -1):
        row = np_img[y, :, 0:3]
        pave_mask = [is_pavement(p[0], p[1], p[2]) for p in row]
        pave_pct = sum(pave_mask) / W
        if pave_pct < 0.15:
            y_bottom = y
            break
            
    # Apply padding
    y_top_crop = max(0, y_top - 15)
    y_bottom_crop = min(H - 1, y_bottom + 15)
    
    print(f"Detected Sky End Row: {y_top} -> Crop Top: {y_top_crop}")
    print(f"Detected Pavement End Row: {y_bottom} -> Crop Bottom: {y_bottom_crop}")
    
    # Perform crop
    cropped_img = img.crop((0, y_top_crop, W, y_bottom_crop))
    cropped_path = "data/screenshots/facades/block_19_middle_facade_0_test_cropped.png"
    cropped_img.save(cropped_path)
    print(f"Saved test cropped image to: {cropped_path}")

if __name__ == "__main__":
    test_crop()
