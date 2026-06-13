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

def test_terrain_alignment_correctness():
    """
    Verifies that the metadata terrain alignment matches the TerrainAligner ground truth.
    """
    aligner = TerrainAligner()
    gt_align = aligner.compute_alignment()
    
    s_gt = gt_align['scale']
    tx_gt = gt_align['translation_m'][0]
    ty_gt = gt_align['translation_m'][1]
    
    # Load alignment values from tecate_metadata.json
    metadata_path = "export/minecraft_world/TecateWorld/tecate_metadata.json"
    assert os.path.exists(metadata_path), "tecate_metadata.json must exist"
    
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
        
    align_meta = metadata["terrain_alignment"]
    s_meta = align_meta["scale"]
    tx_meta = align_meta["translation_x"]
    tz_meta = align_meta["translation_z"]
    
    # Scale difference should be near 0
    assert abs(s_gt - s_meta) < 1e-6
    
    # X Translation difference should be near 0
    assert abs(tx_gt - tx_meta) < 1e-6
    
    # Y/Z Translation difference should be near 0 (with correct negative sign)
    assert abs(ty_gt - tz_meta) < 1e-6
    assert tz_meta < 0.0

def test_validation_points_corrected_elevation():
    """
    Verifies that with the corrected exporter coordinates, the elevation errors
    remain near-zero at all validation points (no linear horizontal drift error).
    """
    glb_path = "models/tecate/glb/tecate.glb"
    metadata_path = "export/minecraft_world/TecateWorld/tecate_metadata.json"
    
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    align_meta = metadata["terrain_alignment"]
    
    s_active = align_meta["scale"]
    tx_active = align_meta["translation_x"]
    tz_active = align_meta["translation_z"]
    
    # Initialize active runtime interpolator
    active_interp = TerrainHeightInterpolator(glb_path, s_active, tx_active, tz_active)
    
    # Ground Truth Baseline
    s_gt = 0.8427785648661434
    tx_gt = 28052.404303473268
    ty_gt = -16620.3853885848
    
    gt_interp = TerrainHeightInterpolator(glb_path, s_gt, tx_gt, 0.0)
    raw_x, raw_y, raw_z = load_raw_glb_positions_helper(glb_path)
    gt_interp.x_pts = s_gt * raw_x + tx_gt
    gt_interp.y_pts = s_gt * raw_y
    gt_interp.z_pts = s_gt * (-raw_z) + ty_gt
    
    gt_interp.grid = {}
    for idx in range(len(gt_interp.x_pts)):
        cx = int(math.floor(gt_interp.x_pts[idx] / gt_interp.cell_size))
        cz = int(math.floor(gt_interp.z_pts[idx] / gt_interp.cell_size))
        gt_interp.grid.setdefault((cx, cz), []).append(idx)
    gt_interp.interpolators = {}
    
    # Test points (Center, North, South, East, West)
    lat_center, lon_center = TECATE_LAT_CENTER, TECATE_LON_CENTER
    test_coords = [
        ("Center", lat_center, lon_center),
        ("North", lat_center + 0.003, lon_center),
        ("South", lat_center - 0.005, lon_center),
        ("East", lat_center, lon_center + 0.005),
        ("West", lat_center, lon_center - 0.005)
    ]
    
    for name, lat, lon in test_coords:
        local_x, local_y = gps_to_local(lat, lon)
        
        # Query elevations
        h_gt = gt_interp.query_height(local_x, local_y)
        h_active = active_interp.query_height(local_x, local_y)
        
        error = abs(h_gt - h_active)
        print(f"Point: {name:<10} | GT Height: {h_gt:.1f}m | Active Height: {h_active:.1f}m | Error: {error:.4f}m")
        # All errors should be under 0.1 meters
        assert error < 0.1
