# Purpose: Implements camera geometry, projection, unprojection, and coordinate mapping for SfM.
# Inputs: 3D point local coordinates, camera position, orientation yaw (heading), focal length, principal point.
# Outputs: 2D pixel coordinates, unprojected 3D coordinates, and COLMAP quaternions.
# Responsibilities: Implements the pinhole camera projection and inverse unprojection formulas.
# Dependencies: math

import math

def yaw_to_quaternion(yaw_deg: float) -> tuple[float, float, float, float]:
    """
    Converts camera heading yaw angle (degrees) to a COLMAP-style world-to-camera unit quaternion (qw, qx, qy, qz).
    Assumes rotation is around the Z axis by angle theta = -yaw (radians).
    """
    theta = -math.radians(yaw_deg)
    qw = math.cos(theta / 2.0)
    qx = 0.0
    qy = 0.0
    qz = math.sin(theta / 2.0)
    return qw, qx, qy, qz

def project_point(
    world_pt: tuple[float, float, float],
    camera_pos: tuple[float, float, float],
    yaw_deg: float,
    f: float,
    cx: float,
    cy: float
) -> tuple[float, float] | None:
    """
    Projects a 3D local Cartesian coordinate to a 2D pixel coordinate.
    Returns (px, py) or None if the point is behind the camera.
    """
    mx, my, mz = world_pt
    cx_val, cy_val, cz_val = camera_pos
    
    # Translate
    dx = mx - cx_val
    dy = my - cy_val
    dz = mz - cz_val
    
    # Construct camera axes from heading
    cam_yaw = math.radians(yaw_deg)
    v_look = [math.sin(cam_yaw), math.cos(cam_yaw), 0.0]
    v_right = [math.cos(cam_yaw), -math.sin(cam_yaw), 0.0]
    v_up = [0.0, 0.0, 1.0]
    
    # Project onto camera axes
    x_c = dx * v_right[0] + dy * v_right[1] + dz * v_right[2]
    y_c = dx * v_up[0] + dy * v_up[1] + dz * v_up[2]
    z_c = dx * v_look[0] + dy * v_look[1] + dz * v_look[2]
    
    if z_c <= 0.001:
        return None # behind camera
        
    px = cx + f * (x_c / z_c)
    py = cy - f * (y_c / z_c)
    
    return px, py

def unproject_pixel(
    u: float,
    v: float,
    z: float,
    camera_pos: tuple[float, float, float],
    yaw_deg: float,
    f: float,
    cx: float,
    cy: float
) -> tuple[float, float, float]:
    """
    Unprojects a 2D pixel coordinate (u, v) with camera depth z (meters) to 3D local Cartesian meters.
    """
    cx_val, cy_val, cz_val = camera_pos
    
    # Camera space coordinates
    x_c = (u - cx) * z / f
    y_c = (cy - v) * z / f
    z_c = z
    
    # Transform back to local Cartesian space
    cam_yaw = math.radians(yaw_deg)
    mx = x_c * math.cos(cam_yaw) + z_c * math.sin(cam_yaw) + cx_val
    my = -x_c * math.sin(cam_yaw) + z_c * math.cos(cam_yaw) + cy_val
    mz = y_c + cz_val
    
    return mx, my, mz
