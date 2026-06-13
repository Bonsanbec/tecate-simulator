import os
import json
import math
import struct
import numpy as np
import pytest

from src.core_io.coords import gps_to_local, TECATE_LAT_CENTER, TECATE_LON_CENTER
from src.reconstruction.terrain_aligner import TerrainAligner
from src.minecraft_pipeline.exporter import TerrainHeightInterpolator

def load_raw_glb_positions_helper(glb_path):
    with open(glb_path, "rb") as f:
        f.read(12)
        chunk_len, chunk_type = struct.unpack('<II', f.read(8))
        gltf = json.loads(f.read(chunk_len).decode('utf-8'))
        f.seek(12 + 8 + chunk_len)
        f.read(8)
        binary_data = f.read()
    mesh = gltf['meshes'][1]
    pos_idx = mesh['primitives'][0]['attributes']['POSITION']
    pos_acc = gltf['accessors'][pos_idx]
    pos_bv = gltf['bufferViews'][pos_acc['bufferView']]
    pos_offset = pos_bv.get('byteOffset', 0) + pos_acc.get('byteOffset', 0)
    pos_count = pos_acc['count']
    positions = np.frombuffer(binary_data[pos_offset:pos_offset + pos_count * 12], dtype=np.float32).reshape(pos_count, 3)
    return positions[:, 0], positions[:, 1], positions[:, 2]

def test_terrain_alignment_discrepancy():
    """
    Verifies that the current exporter constants mirror and translate the terrain
    by about 33.2 km, while the TerrainAligner ground truth provides correct alignment.
    """
    aligner = TerrainAligner()
    gt_align = aligner.compute_alignment()
    
    s_gt = gt_align['scale']
    tx_gt = gt_align['translation_m'][0]
    ty_gt = gt_align['translation_m'][1]
    
    # Exporter parameters
    s_exp = 0.84277856
    tx_exp = 28057.9043
    tz_exp = 16614.8854
    
    # Discrepancy checks
    # Scale difference should be small
    assert abs(s_gt - s_exp) < 0.001
    
    # X Translation difference should be small (< 10 meters)
    assert abs(tx_gt - tx_exp) < 10.0
    
    # Z-Axis Mirror Check:
    # Instead of matching ty_gt (which is around -16620), tz_exp is +16614.
    # This represents a massive shift of about 33.2 km.
    shift_distance = abs(tz_exp - ty_gt)
    print(f"Z-Axis translation discrepancy: {shift_distance:.1f} meters")
    assert shift_distance > 33000.0

def test_validation_points_error_analysis():
    """
    Verifies that the elevation error at Parque Hidalgo (center of projection) is minimal,
    but scales linearly with distance north or south due to the Z-axis mirroring.
    """
    glb_path = "models/tecate/glb/tecate.glb"
    
    s_gt = 0.8427785648661434
    tx_gt = 28052.404303473268
    ty_gt = -16620.3853885848
    
    s_exp = 0.84277856
    tx_exp = 28057.9043
    tz_exp = 16614.8854
    
    # 1. Central Point: Parque Hidalgo (Center)
    lat_center, lon_center = TECATE_LAT_CENTER, TECATE_LON_CENTER
    lx_c, ly_c = gps_to_local(lat_center, lon_center)
    
    # 2. Northern Point: US Border (approx 300m North)
    lx_n, ly_n = gps_to_local(lat_center + 0.003, lon_center)
    
    # Initialize both interpolators
    exp_interp = TerrainHeightInterpolator(glb_path, s_exp, tx_exp, tz_exp)
    gt_interp = TerrainHeightInterpolator(glb_path, s_gt, tx_gt, 0.0)
    
    # Manually correct GT Z coordinates
    raw_x, raw_y, raw_z = load_raw_glb_positions_helper(glb_path)
    gt_interp.x_pts = s_gt * raw_x + tx_gt
    gt_interp.y_pts = s_gt * raw_y
    gt_interp.z_pts = s_gt * (-raw_z) + ty_gt
    
    # Clear grid cache and rebuild
    gt_interp.grid = {}
    for idx in range(len(gt_interp.x_pts)):
        cx = int(math.floor(gt_interp.x_pts[idx] / gt_interp.cell_size))
        cz = int(math.floor(gt_interp.z_pts[idx] / gt_interp.cell_size))
        gt_interp.grid.setdefault((cx, cz), []).append(idx)
    gt_interp.interpolators = {}
    
    # Query elevations
    h_gt_c = gt_interp.query_height(lx_c, ly_c)
    h_exp_c = exp_interp.query_height(lx_c, ly_c)
    
    h_gt_n = gt_interp.query_height(lx_n, ly_n)
    h_exp_n = exp_interp.query_height(lx_n, ly_n)
    
    # Center error should be extremely small (< 1 meter)
    c_err = abs(h_gt_c - h_exp_c)
    print(f"Parque Hidalgo Center Elevation Error: {c_err:.2f} meters")
    assert c_err < 1.0
    
    # North error should be significant due to mirroring shift of ~600m
    n_err = abs(h_gt_n - h_exp_n)
    print(f"Northern Border Elevation Error: {n_err:.2f} meters")
    assert n_err > 10.0
