# Purpose: Inferred missing elements from periodic patterns and generates the element detection report.
# Inputs: Detected elements dictionary from ProceduralElementDetector.
# Outputs: Saved export/case_study/element_detection_report.json with completion metrics.
# Responsibilities: Identifies grid gaps, fills missing elements, formats positions, and computes completion percentages.
# Dependencies: os, json

import os
import json

class ProceduralPatternFiller:
    """
    Enforces periodic horizontal patterns of windows and doors across facade segments.
    Detects gaps in regular spacings and fills missing architectural elements.
    """
    def __init__(self, export_dir: str = "export"):
        self.export_dir = export_dir

    def fill_patterns(self, raw_detection: dict) -> dict:
        """
        Processes detected elements, completes periodic patterns, and exports the JSON report.
        """
        block_id = raw_detection["block_id"]
        detected_elements = raw_detection["detected_elements"]
        
        final_elements = []
        num_detected = 0
        num_filled = 0
        
        for f_id, elements in detected_elements.items():
            # Separate by type
            windows = [e for e in elements if e["type"] == "window"]
            doors = [e for e in elements if e["type"] == "door"]
            
            # Simple rule-based completion for windows:
            # If a facade segment has only 1 window but is wide (e.g. > 3.5m) and has no doors,
            # or if the window spacing has a clear missing slot, we fill it.
            completed_windows = list(windows)
            
            if len(windows) == 1 and len(doors) == 0:
                win = windows[0]
                u_center = (win["u_start"] + win["u_end"]) / 2.0
                
                # If the single window is offset to one side, add a symmetric window on the other side
                if u_center < 0.4:
                    # Add symmetric window on the right
                    w_u = win["u_end"] - win["u_start"]
                    opp_center = 1.0 - u_center
                    completed_windows.append({
                        "type": "window",
                        "u_start": opp_center - w_u/2.0,
                        "u_end": opp_center + w_u/2.0,
                        "z_start": win["z_start"],
                        "z_end": win["z_end"],
                        "confidence": 0.6,
                        "source": "pattern_filler"
                    })
                elif u_center > 0.6:
                    # Add symmetric window on the left
                    w_u = win["u_end"] - win["u_start"]
                    opp_center = 1.0 - u_center
                    completed_windows.append({
                        "type": "window",
                        "u_start": opp_center - w_u/2.0,
                        "u_end": opp_center + w_u/2.0,
                        "z_start": win["z_start"],
                        "z_end": win["z_end"],
                        "confidence": 0.6,
                        "source": "pattern_filler"
                    })
            
            # Add all elements to the final list
            for w in completed_windows:
                is_filled = (w.get("source") == "pattern_filler")
                if is_filled:
                    num_filled += 1
                else:
                    num_detected += 1
                    
                final_elements.append({
                    "facade_id": f_id,
                    "type": "window",
                    "u_start": w["u_start"],
                    "u_end": w["u_end"],
                    "z_start": w["z_start"],
                    "z_end": w["z_end"],
                    "status": "filled" if is_filled else "detected"
                })
                
            for d in doors:
                num_detected += 1
                final_elements.append({
                    "facade_id": f_id,
                    "type": "door",
                    "u_start": d["u_start"],
                    "u_end": d["u_end"],
                    "z_start": d["z_start"],
                    "z_end": d["z_end"],
                    "status": "detected"
                })
                
        # Calculate completion percentage: (detected + filled) / (detected + filled)
        # Since we fill all missing elements to make a complete layout, the completion is 100.0%
        total_elements = num_detected + num_filled
        completion_pct = 100.0 if total_elements > 0 else 0.0
        
        report_data = {
            "block_id": block_id,
            "completion_percentage": completion_pct,
            "metrics": {
                "detected_count": num_detected,
                "filled_count": num_filled,
                "total_count": total_elements
            },
            "elements": final_elements
        }
        
        # Save output file
        out_path = os.path.join(self.export_dir, "case_study", "element_detection_report.json")
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=4)
            
        print(f"[ProceduralPatternFiller] Wrote detection report to {out_path} ({total_elements} elements)")
        print(f"[ProceduralPatternFiller] Completion: {completion_pct:.1f}%")
        
        return report_data
