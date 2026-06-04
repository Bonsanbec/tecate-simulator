# Purpose: Runs reprojection and texture verification, then generates the final Phase 2 quality report.
# Inputs: export/case_study/target_block.glb, data/case_study/target_panoramas.json, data/case_study/target_facade.json, export/case_study/texture_extraction_report.json.
# Outputs: export/case_study/reprojection_report.json, export/case_study/phase2_quality_report.json.
# Responsibilities: Runs the reprojection validator, aggregates texture and geometry metrics, and outputs the overall Phase 2 status.
# Dependencies: json, os, datetime, src.qa.reprojection_validator

import json
import os
from datetime import datetime
from src.qa.reprojection_validator import ReprojectionValidator

def main():
    print("[generate_phase2_report] Starting Phase 2 quality assessment...")
    
    # 1. Run reprojection validation
    glb_path = "export/case_study/target_block.glb"
    panos_path = "data/case_study/target_panoramas.json"
    facade_path = "data/case_study/target_facade.json"
    texture_report_path = "export/case_study/texture_extraction_report.json"
    
    if not os.path.exists(glb_path):
        raise FileNotFoundError(f"GLB file not found: {glb_path}")
    if not os.path.exists(panos_path):
        raise FileNotFoundError(f"Panoramas file not found: {panos_path}")
    if not os.path.exists(facade_path):
        raise FileNotFoundError(f"Facade file not found: {facade_path}")
    if not os.path.exists(texture_report_path):
        raise FileNotFoundError(f"Texture report file not found: {texture_report_path}")
        
    with open(panos_path, "r", encoding="utf-8") as f:
        panos = json.load(f)
    with open(facade_path, "r", encoding="utf-8") as f:
        facade = json.load(f)
    with open(texture_report_path, "r", encoding="utf-8") as f:
        texture_report = json.load(f)
        
    validator = ReprojectionValidator()
    reproj_result = validator.validate(glb_path, panos, facade)
    
    reproj_report_path = "export/case_study/reprojection_report.json"
    with open(reproj_report_path, "w", encoding="utf-8") as f:
        json.dump(reproj_result, f, indent=4)
    print(f"[generate_phase2_report] Wrote reprojection report to {reproj_report_path}")
    
    # 2. Compile aggregated Phase 2 report
    rms = reproj_result.get("rms_reprojection_error_px", 999.0)
    coverage = texture_report.get("coverage_pct", 0.0)
    
    reproj_ok = rms < 5.0 and reproj_result.get("status") == "PASS"
    texture_ok = coverage >= 50.0
    
    overall_status = "PASS" if (reproj_ok and texture_ok) else "FAIL"
    
    quality_report = {
        "gate_id": "QG-03",
        "overall_status": overall_status,
        "evaluation_timestamp": datetime.utcnow().isoformat() + "Z",
        "metrics": {
            "rms_reprojection_error_px": rms,
            "texture_coverage_pct": coverage,
            "num_matched_corners": reproj_result.get("num_matched_corners", 0),
            "texture_width": texture_report.get("width"),
            "texture_height": texture_report.get("height")
        },
        "thresholds": {
            "max_rms_reprojection_error_px": 5.0,
            "min_texture_coverage_pct": 50.0
        },
        "checks": {
            "reprojection_accuracy": "PASS" if reproj_ok else "FAIL",
            "texture_coverage": "PASS" if texture_ok else "FAIL"
        },
        "notes": f"Phase 2 verification completed. Reprojection RMS error: {rms:.4f}px, texture coverage: {coverage:.2f}%."
    }
    
    phase2_report_path = "export/case_study/phase2_quality_report.json"
    with open(phase2_report_path, "w", encoding="utf-8") as f:
        json.dump(quality_report, f, indent=4)
    
    print(f"[generate_phase2_report] Saved Phase 2 quality report to {phase2_report_path}")
    print(f"[generate_phase2_report] Overall Phase 2 status: {overall_status}")
    
    if overall_status == "FAIL":
        print("[generate_phase2_report] WARNING: Phase 2 quality check failed!")
        
if __name__ == "__main__":
    main()
