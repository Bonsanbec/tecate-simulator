import os
import json
import numpy as np
import pytest

from src.reconstruction.terrain_aligner import TerrainAligner

def test_terrain_aligner_initialization():
    aligner = TerrainAligner()
    assert aligner.geojson_path == "reference/tecate-polygon.json"
    assert aligner.glb_path == "models/tecate/glb/tecate.glb"

def test_terrain_aligner_geojson_load():
    aligner = TerrainAligner()
    geojson_pts = aligner.load_geojson_boundary()
    assert len(geojson_pts) > 0
    assert geojson_pts.shape[1] == 2  # longitude, latitude

def test_terrain_aligner_glb_load():
    aligner = TerrainAligner()
    loop_pts = aligner.extract_glb_boundary_loop()
    assert len(loop_pts) > 0
    assert loop_pts.shape[1] == 2  # X, Z coordinates

def test_terrain_aligner_compute_alignment():
    aligner = TerrainAligner()
    result = aligner.compute_alignment()
    
    assert "scale" in result
    assert "rotation_matrix" in result
    assert "rotation_angle_degrees" in result
    assert "translation_m" in result
    assert "rmse_m" in result
    
    # We expect scale to be very close to cos(32.573229 degrees) = 0.842718
    assert abs(result["scale"] - 0.8427) < 0.005
    
    # We expect rotation angle to be close to 0 degrees
    assert abs(result["rotation_angle_degrees"]) < 0.1
    
    # We expect RMSE to be small (< 30 meters)
    assert result["rmse_m"] < 30.0

def test_terrain_aligner_save_to_json(tmp_path):
    aligner = TerrainAligner()
    export_file = tmp_path / "alignment.json"
    aligner.save_alignment_to_json(export_path=str(export_file))
    
    assert os.path.exists(export_file)
    with open(export_file, "r") as f:
        data = json.load(f)
    assert "scale" in data
    assert "rmse_m" in data
