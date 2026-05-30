from PIL import Image
import numpy as np

def find_colors():
    img_path = "data/screenshots/facades/block_19_middle_facade_0.png"
    img = Image.open(img_path)
    np_img = np.array(img)
    H, W, C = np_img.shape
    print(f"Image dimensions: {W}x{H}")
    
    # 1. Sample sky (top 50 rows, middle width)
    sky_samples = np_img[0:50, W//4:3*W//4, :]
    sky_mean = np.mean(sky_samples, axis=(0, 1))
    sky_std = np.std(sky_samples, axis=(0, 1))
    print(f"Sky RGB Mean: {sky_mean}, Std: {sky_std}")
    
    # 2. Sample pavement (bottom 50 rows, middle width)
    pave_samples = np_img[H-50:H, W//4:3*W//4, :]
    pave_mean = np.mean(pave_samples, axis=(0, 1))
    pave_std = np.std(pave_samples, axis=(0, 1))
    print(f"Pavement RGB Mean: {pave_mean}, Std: {pave_std}")
    
    # Let's print some individual pixel values
    print("\nTop rows individual pixels (sky):")
    for y in range(0, 30, 5):
        print(f"  Row {y}: {np_img[y, W//2]}")
        
    print("\nBottom rows individual pixels (pavement):")
    for y in range(H-30, H, 5):
        print(f"  Row {y}: {np_img[y, W//2]}")

if __name__ == "__main__":
    find_colors()
