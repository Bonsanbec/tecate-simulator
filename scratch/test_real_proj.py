import numpy as np
from PIL import Image
from src.image_alignment.virtual_camera import project_rectilinear
import py360convert

# Create a simulated real cropped panorama of size 2560x640
w_pano, h_pano = 2560, 640
pano_data = np.zeros((h_pano, w_pano, 3), dtype=np.uint8)
# Let's draw a white line at the horizon in the legacy projection
# In legacy projection for real format, the horizon is ray_pitch = 0
# row = 1280.0 * 0.16796875 = 215. Let's draw a white line at row 215.
pano_data[215-5:215+5, :, :] = [255, 255, 255]
pano_img = Image.fromarray(pano_data)

target_yaw = 90.0
pano_yaw = 180.0
fov = 80.0
width, height = 512, 256

proj_nn = project_rectilinear(
    pano_img=pano_img,
    yaw_deg=target_yaw,
    pitch_deg=0.0,
    fov_deg=fov,
    width=width,
    height=height,
    pano_yaw=pano_yaw,
    is_sim=False
)

# Now let's try to project using py360convert.e2p
# Since the legacy projection maps row = 1280 * (0.16796875 - pitch/pi),
# this means the top row of the 2560x1280 full panorama corresponds to 0,
# and the 640-height image starts at row 0 of the full panorama and ends at row 640.
# Wait, let's check: if row starts at 0 and ends at 640, then the cropped image is exactly the top half of the full 2560x1280 panorama!
# Let's verify: if it is the top half, then the bottom of the cropped image is row 640, which is the exact equator (horizon) of a standard panorama!
# But wait, in standard panoramas, the equator is at the center (row 640).
# In our legacy projection, the horizon is at row 215!
# This means the cropped image is offset by some amount.
# Specifically, the row in the full panorama is `row_full = row_cropped + offset`.
# Let's find the exact offset:
# In legacy projection: row = 1280 * (0.16796875 - pitch/pi)
# In standard equirectangular: row_std = 1280 * (0.5 - pitch/pi)
# So: row_std = row_legacy + 1280 * (0.5 - 0.16796875) = row_legacy + 1280 * 0.33203125 = row_legacy + 425!
# Oh! This is beautiful!
# The standard panorama row is `row_legacy + 425`.
# This means our cropped 640-height image is located from row 425 to row 1065 in the standard 1280-height panorama!
# So to pad it to a standard 2560x1280 panorama, we can:
# - Create a blank 2560x1280 canvas.
# - Paste our 2560x640 cropped image at y-offset = 425!
# - Then pass this padded 2560x1280 image to py360convert!
# Let's verify this mathematically:
# If y-offset is 425, then row 215 in the cropped image maps to row 215 + 425 = 640 in the padded image, which is the exact center/equator of the 1280-height standard panorama!
# This is mathematically 100% correct!
# Let's test this in Python!

padded_data = np.zeros((1280, 2560, 3), dtype=np.uint8)
padded_data[425:425+640, :, :] = np.array(pano_img)
padded_img = Image.fromarray(padded_data)

rel_yaw = (target_yaw - pano_yaw) % 360.0
if rel_yaw > 180.0:
    rel_yaw -= 360.0

proj_py = py360convert.e2p(
    padded_data,
    fov_deg=fov,
    u_deg=rel_yaw,
    v_deg=0.0,
    out_hw=(height, width),
    mode='bilinear'
)

# Check center pixel color (should be white [255, 255, 255] in both!)
center_nn = np.array(proj_nn)[128, 256]
center_py = proj_py[128, 256]
print("NN center color:", center_nn)
print("Py360 center color:", center_py)

proj_nn.save("real_nn.png")
Image.fromarray(proj_py).save("real_py360.png")
