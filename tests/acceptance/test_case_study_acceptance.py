# Purpose: Acceptance test for the Caseta Telefónica case study reconstruction MVP.
# Inputs: QG02_report.json, target_facade_texture.png, detailed_facade.glb, qa_report.json.
# Outputs: Test pass/fail acceptance results.
# Responsibilities: Performs final end-to-end assertions against the reconstructed assets, ensuring PSNR, reprojection, and coverage bounds.
# Dependencies: pytest, os, json

import os
import json
import pytest

def test_dataset_manifest_qg02_pass():
    """Verify that dataset preparation Quality Gate QG-02 passed."""
    qg02_path = "data/case_study/QG02_report.json"
    assert os.path.exists(qg02_path), f"QG-02 report not found: {qg02_path}"
    with open(qg02_path, "r", encoding="utf-8") as f:
        r = json.load(f)
    assert r.get("status") == "PASS", f"QG-02 status is {r.get('status')}"

def test_facade_texture_exists_and_covered():
    """Verify that the extracted texture exists and has coverage >= 50%."""
    texture_path = "export/case_study/target_facade_texture.png"
    report_path = "export/case_study/texture_extraction_report.json"
    
    assert os.path.exists(texture_path), f"Texture file not found: {texture_path}"
    assert os.path.exists(report_path), f"Texture report not found: {report_path}"
    
    with open(report_path, "r", encoding="utf-8") as f:
        r = json.load(f)
    cov = r.get("coverage_pct", 0.0)
    assert cov >= 50.0, f"Texture coverage {cov:.2f}% is below 50.0% threshold"

def test_mesh_file_exists_and_valid():
    """Verify that the procedural 3D detailed GLB mesh exists, is non-trivial in size, and starts with magic header 'glTF'."""
    glb_path = "export/case_study/detailed_facade.glb"
    assert os.path.exists(glb_path), f"Detailed GLB file not found: {glb_path}"
    
    sz = os.path.getsize(glb_path)
    assert sz > 10240, f"Detailed GLB is too small: {sz} bytes (expected > 10KB)"
    
    with open(glb_path, "rb") as f:
        header = f.read(4)
    assert header == b"glTF", f"Invalid GLB magic header: {header} (expected b'glTF')"

def test_reprojection_error_within_threshold():
    """Verify that the reprojection RMS error is within acceptable limits (< 5.0px)."""
    qa_report_path = "export/case_study/qa_report.json"
    assert os.path.exists(qa_report_path), f"QA report not found: {qa_report_path}"
    
    with open(qa_report_path, "r", encoding="utf-8") as f:
        r = json.load(f)
    rms = r.get("metrics", {}).get("reprojection_rms_px", 999.0)
    assert rms < 5.0, f"Reprojection RMS error {rms:.4f}px exceeds 5.0px threshold"

def test_qa_report_overall_pass():
    """Verify that the final QA report overall status is PASS."""
    qa_report_path = "export/case_study/qa_report.json"
    assert os.path.exists(qa_report_path), f"QA report not found: {qa_report_path}"
    
    with open(qa_report_path, "r", encoding="utf-8") as f:
        r = json.load(f)
    assert r.get("overall_status") == "PASS", f"Overall QA status is {r.get('overall_status')}"
