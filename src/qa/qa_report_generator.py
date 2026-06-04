# Purpose: Integrates all QA validators, computes overall scores, and exports validation reports.
# Inputs: detailed_facade.glb, target_facade_texture.png, target_facade.json, target_panoramas.json.
# Outputs: export/case_study/qa_report.json and data/case_study/QG08_report.json.
# Responsibilities: Instantiates validators, runs evaluation, aggregates results, and determines final pass/fail status.
# Dependencies: os, json, datetime, src.qa.reprojection_validator, src.qa.coverage_analyzer, src.qa.psnr_evaluator

import os
import json
from datetime import datetime
from src.qa.reprojection_validator import ReprojectionValidator
from src.qa.coverage_analyzer import CoverageAnalyzer
from src.qa.psnr_evaluator import PsnrEvaluator

class QAReportGenerator:
    """
    Orchestrates the execution of all validation tools, compiles the final QA report,
    and writes out the Quality Gate QG-08 acceptance results.
    """
    def __init__(self, data_dir: str = "data", export_dir: str = "export"):
        self.data_dir = data_dir
        self.export_dir = export_dir
        self.reproj_val = ReprojectionValidator(data_dir=data_dir)
        self.cov_anal = CoverageAnalyzer(data_dir=data_dir)
        self.psnr_eval = PsnrEvaluator(data_dir=data_dir, export_dir=export_dir)

    def generate_report(
        self,
        glb_path: str = "export/case_study/detailed_facade.glb",
        texture_path: str = "export/case_study/target_facade_texture.png",
        target_facade_path: str = "data/case_study/target_facade.json",
        target_panos_path: str = "data/case_study/target_panoramas.json"
    ) -> dict:
        """
        Runs the full evaluation suite and saves the consolidated report.
        """
        print("[QAReportGenerator] Compiling Quality Assurance Report...")
        
        # 1. Reprojection Validator
        reproj_res = self.reproj_val.validate(
            glb_path=glb_path,
            panos=json.load(open(target_panos_path)),
            facade=json.load(open(target_facade_path))
        )
        
        # 2. Coverage Analyzer
        cov_res = self.cov_anal.analyze_coverage(texture_path=texture_path)
        
        # 3. PSNR Evaluator
        psnr_res = self.psnr_eval.evaluate_psnr(
            texture_path=texture_path,
            target_facade_path=target_facade_path,
            target_panos_path=target_panos_path
        )
        
        # Determine overall pass status based on Quality Gate thresholds
        psnr_val = psnr_res.get("psnr_db", 0.0)
        reproj_rms = reproj_res.get("rms_reprojection_error_px", 999.0)
        cov_pct = cov_res.get("coverage_pct", 0.0)
        
        # QG-08 Thresholds: PSNR >= 25dB, Reprojection RMS < 5px, Coverage >= 50%
        psnr_pass = (psnr_val >= 25.0)
        reproj_pass = (reproj_rms < 5.0)
        cov_pass = (cov_pct >= 50.0)
        
        overall_status = "PASS" if (psnr_pass and reproj_pass and cov_pass) else "FAIL"
        
        report = {
            "overall_status": overall_status,
            "evaluation_timestamp": datetime.utcnow().isoformat() + "Z",
            "metrics": {
                "psnr_db": psnr_val,
                "reprojection_rms_px": reproj_rms,
                "texture_coverage_pct": cov_pct
            },
            "thresholds": {
                "min_psnr_db": 25.0,
                "max_reprojection_rms_px": 5.0,
                "min_texture_coverage_pct": 50.0
            },
            "detailed_results": {
                "reprojection": reproj_res,
                "coverage": cov_res,
                "psnr": psnr_res
            }
        }
        
        # Save export/case_study/qa_report.json
        qa_report_path = os.path.join(self.export_dir, "case_study", "qa_report.json")
        os.makedirs(os.path.dirname(qa_report_path), exist_ok=True)
        with open(qa_report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=4)
        print(f"[QAReportGenerator] Wrote QA report to {qa_report_path}")
        
        # Save data/case_study/QG08_report.json for the Quality Gate structure
        qg08_report = {
            "gate_id": "QG-08",
            "status": overall_status,
            "evaluation_timestamp": report["evaluation_timestamp"],
            "metrics": report["metrics"],
            "thresholds": report["thresholds"],
            "blocking_phases": [],
            "notes": f"Full pipeline acceptance check. PSNR: {psnr_val:.2f} dB, Reprojection RMS: {reproj_rms:.4f} px, Coverage: {cov_pct:.2f}%"
        }
        qg08_path = os.path.join(self.data_dir, "case_study", "QG08_report.json")
        with open(qg08_path, "w", encoding="utf-8") as f:
            json.dump(qg08_report, f, indent=4)
        print(f"[QAReportGenerator] Wrote QG-08 report to {qg08_path}")
        
        return report
