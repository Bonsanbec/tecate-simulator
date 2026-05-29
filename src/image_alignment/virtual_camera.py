import math
import numpy as np
from PIL import Image

def project_rectilinear(
    pano_img: Image.Image,
    yaw_deg: float,
    pitch_deg: float,
    fov_deg: float,
    width: int = 512,
    height: int = 512,
    pano_yaw: float = 180.0,
    is_sim: bool = False
) -> Image.Image:
    """
    Vectorized perspective projection using py360convert's cubemap projection (e2c)
    to cleanly project equirectangular panoramas into perfect cubical face textures.
    Reduces vertical distortions and pixelation, providing clean planar textures.
    """
    import py360convert
    
    np_pano = np.array(pano_img)
    H, W = np_pano.shape[:2]
    
    # We pad the cropped panorama to the full standard 2:1 aspect ratio equirectangular format
    full_h = int(W // 2)
    padded_pano = np.zeros((full_h, W, np_pano.shape[2]), dtype=np_pano.dtype)
    
    if is_sim:
        y_offset = int(full_h // 2 - H // 2)  # Horizon is at exact equator
    else:
        # Standard cropped Google Street View vertical alignment offset
        y_offset = int(full_h * (0.5 - 0.16796875))
        
    y_offset = max(0, min(y_offset, full_h - H))
    padded_pano[y_offset:y_offset+H, :, :] = np_pano
    
    # Calculate the face width
    face_w = max(width, height)
    
    # Project to cubemap using e2c in dict format
    cube_dict = py360convert.e2c(padded_pano, face_w=face_w, mode='bilinear', cube_format='dict')
    
    # Normalize horizontal viewing angle relative to the panorama yaw to [-180, 180]
    rel_yaw = (yaw_deg - pano_yaw) % 360.0
    if rel_yaw > 180.0:
        rel_yaw -= 360.0
        
    # Map relative yaw to the closest face:
    # F: -45 to 45
    # R: 45 to 135
    # B: 135 to 180 or -180 to -135
    # L: -135 to -45
    if -45.0 <= rel_yaw < 45.0:
        face_key = 'F'
    elif 45.0 <= rel_yaw < 135.0:
        face_key = 'R'
    elif -135.0 <= rel_yaw < -45.0:
        face_key = 'L'
    else:
        face_key = 'B'
        
    face_arr = cube_dict[face_key]
    
    # Resize to out_hw (height, width) if it's different from face_w
    face_img = Image.fromarray(face_arr)
    if face_img.width != width or face_img.height != height:
        face_img = face_img.resize((width, height), Image.Resampling.BILINEAR)
        
    return face_img
