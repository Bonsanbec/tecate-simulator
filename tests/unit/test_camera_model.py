# Purpose: Unit tests for camera model heading conversions and projection round-trips.
# Inputs: Test cases for yaw-to-quaternion mapping and synthetic projection points.
# Outputs: Pytest assertion verification.
# Responsibilities: Asserts mathematical correctness of rotation mapping and geometric consistency.
# Dependencies: pytest, src.sfm.camera_model

import pytest
import math
from src.sfm.camera_model import yaw_to_quaternion, project_point, unproject_pixel

def test_yaw_to_quaternion_0():
    """Verify heading=0° maps to identity rotation."""
    qw, qx, qy, qz = yaw_to_quaternion(0.0)
    assert abs(qw - 1.0) < 1e-7, f"Expected qw=1.0, got {qw}"
    assert abs(qx) < 1e-7
    assert abs(qy) < 1e-7
    assert abs(qz) < 1e-7

def test_yaw_to_quaternion_90():
    """Verify heading=90° maps to 90° yaw left."""
    qw, qx, qy, qz = yaw_to_quaternion(90.0)
    assert abs(qw - 0.70710678) < 1e-5, f"Expected qw≈0.707, got {qw}"
    assert abs(qx) < 1e-7
    assert abs(qy) < 1e-7
    assert abs(qz - (-0.70710678)) < 1e-5, f"Expected qz≈-0.707, got {qz}"

def test_yaw_to_quaternion_180():
    """Verify heading=180° maps to facing South."""
    qw, qx, qy, qz = yaw_to_quaternion(180.0)
    assert abs(qw) < 1e-7, f"Expected qw≈0.0, got {qw}"
    assert abs(qx) < 1e-7
    assert abs(qy) < 1e-7
    assert abs(qz - (-1.0)) < 1e-7, f"Expected qz≈-1.0, got {qz}"

def test_projection_round_trip():
    """Verify that projection and unprojection round-trip successfully."""
    camera_pos = (186.0, -37.0, 2.5)
    yaw_deg = 266.40
    f = 833.0
    cx = 639.5
    cy = 359.5
    
    # 3D Point: 10 meters in front of the camera, offset 2 meters right and 1 meter up
    # Since yaw is 266.40 (looks West-ish), let's project it first
    world_pt = (180.0, -35.0, 3.5)
    
    pixel = project_point(world_pt, camera_pos, yaw_deg, f, cx, cy)
    assert pixel is not None, "Point should project in front of camera"
    
    u, v = pixel
    
    # We need the camera-space depth z_c to unproject
    # Construct look vector
    cam_yaw = math.radians(yaw_deg)
    v_look = [math.sin(cam_yaw), math.cos(cam_yaw), 0.0]
    dx = world_pt[0] - camera_pos[0]
    dy = world_pt[1] - camera_pos[1]
    dz = world_pt[2] - camera_pos[2]
    z_c = dx * v_look[0] + dy * v_look[1] + dz * v_look[2]
    
    # Unproject
    world_pt_rt = unproject_pixel(u, v, z_c, camera_pos, yaw_deg, f, cx, cy)
    
    assert abs(world_pt_rt[0] - world_pt[0]) < 1e-5
    assert abs(world_pt_rt[1] - world_pt[1]) < 1e-5
    assert abs(world_pt_rt[2] - world_pt[2]) < 1e-5
