# Purpose: Integration tests for SfM ColmapRunner pipeline.
# Inputs: Case study screenshots, target panoramas, target facade indices.
# Outputs: Reconstruction point files.
# Responsibilities: Executes ColmapRunner and verifies that sparse models and PLY files are successfully generated.
# Dependencies: pytest, os, src.sfm.colmap_runner

import os
import pytest
from src.sfm.colmap_runner import ColmapRunner

def test_colmap_runner_integration():
    """Verify that ColmapRunner executes on the target image set and produces the required output files."""
    image_dir = "data/case_study/target_images"
    target_panoramas_path = "data/case_study/target_panoramas.json"
    target_facade_path = "data/case_study/target_facade.json"
    workspace_dir = "data/case_study/sfm"
    
    # Verify input files exist
    assert os.path.exists(image_dir), f"Image dir not found: {image_dir}"
    assert os.path.exists(target_panoramas_path), f"Panoramas path not found: {target_panoramas_path}"
    assert os.path.exists(target_facade_path), f"Facade path not found: {target_facade_path}"
    
    runner = ColmapRunner()
    result = runner.run_reconstruction(
        image_dir=image_dir,
        target_panoramas_path=target_panoramas_path,
        target_facade_path=target_facade_path,
        workspace_dir=workspace_dir
    )
    
    # 1. Verify result status and point count
    assert result["status"] == "PASS"
    assert result["point_count"] >= 500, f"Expected at least 500 points, got {result['point_count']}"
    
    # 2. Verify files are written to disk
    pts3d_file = os.path.join(workspace_dir, "sparse", "0", "points3D.txt")
    point_cloud_ply = os.path.join(os.path.dirname(workspace_dir), "point_cloud.ply")
    dense_cloud_ply = os.path.join(os.path.dirname(workspace_dir), "dense_cloud.ply")
    
    assert os.path.exists(pts3d_file), f"points3D.txt not found at {pts3d_file}"
    assert os.path.exists(point_cloud_ply), f"point_cloud.ply not found at {point_cloud_ply}"
    assert os.path.exists(dense_cloud_ply), f"dense_cloud.ply not found at {dense_cloud_ply}"
    
    # 3. Verify points3D.txt contains non-comment data lines
    with open(pts3d_file, "r", encoding="utf-8") as f:
        lines = [l for l in f if not l.startswith("#") and l.strip()]
    assert len(lines) == result["point_count"], f"Line count in points3D.txt ({len(lines)}) mismatch with result point count ({result['point_count']})"
