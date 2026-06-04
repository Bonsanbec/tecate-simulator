# Purpose: Unit tests for ProceduralElementDetector and ProceduralPatternFiller.
# Inputs: target_facade.json, facades_cache.json, target_facade_texture.png.
# Outputs: Test pass/fail status.
# Responsibilities: Assures horizontal profile snapping, regular prior grids, and gap filling.
# Dependencies: pytest, os, src.procedural.element_detector, src.procedural.pattern_filler

import os
import pytest
import json
from src.procedural.element_detector import ProceduralElementDetector
from src.procedural.pattern_filler import ProceduralPatternFiller

def test_element_detector_and_filler():
    """Test that the element detector generates grids and pattern filler completes them."""
    target_facade_path = "data/case_study/target_facade.json"
    facades_cache_path = "data/facades_cache.json"
    texture_path = "export/case_study/target_facade_texture.png"
    
    assert os.path.exists(target_facade_path)
    assert os.path.exists(facades_cache_path)
    assert os.path.exists(texture_path)
    
    detector = ProceduralElementDetector()
    raw_result = detector.detect_elements(
        target_facade_path=target_facade_path,
        facades_cache_path=facades_cache_path,
        texture_path=texture_path
    )
    
    # Check detector output schema
    assert "block_id" in raw_result
    assert "target_facade_indices" in raw_result
    assert "detected_elements" in raw_result
    
    # Check that each facade segment has elements detected/generated
    detected_elements = raw_result["detected_elements"]
    assert len(detected_elements) > 0
    
    for f_id, elements in detected_elements.items():
        assert isinstance(elements, list)
        for elem in elements:
            assert "type" in elem
            assert elem["type"] in ["window", "door"]
            assert "u_start" in elem
            assert "u_end" in elem
            assert "z_start" in elem
            assert "z_end" in elem
            
    # Test pattern filler
    filler = ProceduralPatternFiller()
    report = filler.fill_patterns(raw_result)
    
    # Verify report schema
    assert "block_id" in report
    assert "completion_percentage" in report
    assert report["completion_percentage"] >= 90.0
    assert "elements" in report
    
    # Verify that the report was written to disk
    report_file = "export/case_study/element_detection_report.json"
    assert os.path.exists(report_file)
    with open(report_file, "r") as f:
        saved_data = json.load(f)
    assert saved_data["completion_percentage"] >= 90.0
