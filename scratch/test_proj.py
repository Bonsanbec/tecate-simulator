import numpy as np
from PIL import Image
from src.image_alignment.virtual_camera import project_rectilinear
import py360convert

# Create a simple synthetic equirectangular panorama of size 2560 x 640
pano_w, pano_h = 2560, 640
pano_data = np.zeros((pano_h, pano_w, 3), dtype=np.uint8)
# Add some vertical stripes at specific angles to check yaw mapping correctness
# Let's add a white stripe (255, 255, 255) at yaw = 90 deg.
# 90 degrees relative to South (180) is: 270 degrees in equirectangular.
# Equirectangular column index = (yaw / 360) * w.
# Since the center is 180 (South), columns are shifted by 180 degrees.
# Let's put a white stripe at col = 1280 (180 deg), a red stripe at col = 640 (90 deg), and a green stripe at col = 1920 (270 deg).
pano_data[:, 1280-10:1280+10, :] = [255, 255, 255] # White at South
pano_data[:, 640-10:640+10, :] = [255, 0, 0] # Red at East
pano_data[:, 1920-10:1920+10, :] = [0, 255, 0] # Green at West

pano_img = Image.fromarray(pano_data)

# Let's test target_yaw = 90.0 (East)
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
    is_sim=True
)

# Relative yaw to center (pano_yaw = 180)
rel_yaw = (target_yaw - pano_yaw) % 360.0
if rel_yaw > 180.0:
    rel_yaw -= 360.0

proj_py360_arr = py360convert.e2p(
    np.array(pano_img),
    fov_deg=fov,
    u_deg=rel_yaw,
    v_deg=0.0,
    out_hw=(height, width),
    mode='bilinear'
)

# Let's check colors in both projections near the center
arr_nn = np.array(proj_nn)
arr_py = proj_py360_arr

# Print center color
center_nn = arr_nn[128, 256]
center_py = arr_py[128, 256]
print("Center pixel in NN:", center_nn)
print("Center pixel in Py360:", center_py)

# Save both
proj_nn.save("nn.png")
Image.fromarray(arr_py).save("py360.png")
