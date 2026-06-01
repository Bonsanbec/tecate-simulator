# QUALITY_GATES.md
## Tecate 2009 — Facade Reconstruction Quality Gates

**Purpose**: Define mandatory quality checkpoints that must pass before subsequent phases may begin.  
**Enforcement**: Each gate is evaluated by a specific script/test. No manual judgment is allowed unless explicitly noted.

---

## Gate Evaluation Protocol

1. For each gate: the listed validation script/command is run
2. Output is written to a gate report file: `data/case_study/QG{N:02d}_report.json`
3. The report file must exist and contain `"status": "PASS"` before the blocked phase begins
4. A gate in FAIL state halts the pipeline and requires remediation before retry

Gate report schema:
```json
{
  "gate_id": "QG-NN",
  "status": "PASS" | "FAIL",
  "evaluation_timestamp": "ISO8601",
  "metrics": { ... gate-specific metrics ... },
  "threshold": { ... gate-specific thresholds ... },
  "blocking_phases": ["PXX"],
  "notes": "string"
}
```

---

## QG-01 — Coordinate System Accuracy

**Gate ID**: QG-01  
**Description**: Verify that `gps_to_local` and `local_to_gps` in `src/core_io/coords.py` satisfy the accuracy contract.

**Evaluation command**:
```bash
pytest tests/unit/test_coords.py -v --json-report --json-report-file=data/case_study/QG01_report.json
```

**Pass criteria**:
- `test_origin`: `gps_to_local(32.573229, -116.626536)` returns `(x, y)` with `abs(x) < 0.001` AND `abs(y) < 0.001`
- `test_case_study_target`: `gps_to_local(32.5728966, -116.6245526)` returns `x ∈ [185.0, 187.0]` AND `y ∈ [-38.0, -36.0]`
- `test_round_trip_target`: round-trip GPS error at target location < 0.5m
- `test_round_trip_origin`: round-trip GPS error at origin < 0.001m
- All 5 tests in `test_coords.py` pass

**Fail criteria**: Any single test case fails.

**Remediation if fail**:
- Verify `TECATE_LAT_CENTER = 32.573229` (not 32.57322 or other variant) in `coords.py`
- Verify `EARTH_RADIUS = 6378137.0` (not 6371000)
- Verify formula: `dx = R * radians(lon - LON_C) * cos(radians(LAT_C))`

**Blocks**: Phase 1 (P01-T007 cannot begin)

**Produced by**: P00-T003

---

## QG-02 — Case Study Dataset Completeness

**Gate ID**: QG-02  
**Description**: Verify that all required case study dataset components are assembled and internally consistent.

**Evaluation command**:
```bash
python3 scripts/evaluate_qg02.py  # writes data/case_study/QG02_report.json
```

**Pass criteria** (all must be true):
1. `data/case_study/target_facade.json` exists AND `len(target_facade_indices) >= 1`
2. `data/case_study/target_panoramas.json` exists AND `len(panoramas) >= 1`
3. At least 1 file exists in `data/case_study/target_images/`
4. All 193 facade entries for `block_lat_32.57293_lon_-116.62389` in `data/facades_cache.json` have non-null `facade_midpoint_local`
5. `target_facade.json.alignment_dot_product > 0.5`
6. At least 1 panorama in `target_panoramas.json` has `date <= "2022-12"` (not a far-future date)
7. `data/case_study/case_study_manifest.json` exists

**Fail criteria**: Any single criterion fails.

**Remediation if fail**:
1. Re-run P01-T007 (facade identification)
2. Re-run P01-T008 (midpoint recomputation)
3. Re-run P01-T009 / P01-T010 (image collection)

**Blocks**: Phase 2 (P02-T012 cannot begin)

**Produced by**: P01-T011

---

## QG-03 — Mesh Reprojection Accuracy

**Gate ID**: QG-03  
**Description**: The reconstructed 3D mesh of the Caseta Telefónica facade reprojects into source camera images with acceptable pixel error.

**Evaluation command**:
```bash
python3 -c "
import json
r = json.load(open('export/case_study/reprojection_report.json'))
assert r['rms_reprojection_error_px'] < 5.0, f'FAIL: rms={r[\"rms_reprojection_error_px\"]}'
print(f'QG-03 PASS: rms={r[\"rms_reprojection_error_px\"]:.3f}px')
"
```

**Pass criteria**:
- `rms_reprojection_error_px < 5.0`
- `max_reprojection_error_px < 15.0`
- At least 4 face corners are visible in the source image (not all behind camera)

**Fail criteria**: RMS error ≥ 5.0px

**Remediation if fail**:
- Verify camera heading convention (may be off by 180°)
- Verify local coordinate sign conventions (x=East or x=West)
- Verify focal length computation
- If systematic offset in one direction: check `cx`, `cy` principal point values

**Blocks**: Phase 3 (P03-T017 cannot begin)

**Produced by**: P02-T015

---

## QG-04 — Generalized Pipeline Format Compatibility

**Gate ID**: QG-04  
**Description**: The refactored pipeline produces output that is schema-compatible with the original `reconstruction_export.json` schema AND uses relative paths.

**Evaluation command**:
```bash
pytest tests/integration/test_pipeline_generalized.py -v
```

**Pass criteria**:
- Pipeline runs on 5 different blocks without errors
- Output `reconstruction_export.json` validates against `src/reconstruction/config_schema.json`
- No `facade_textures` values start with `/` (Unix absolute) or match `^[A-Z]:\\` (Windows absolute)
- All referenced texture files exist relative to `export/` directory

**Fail criteria**: Any pipeline run fails OR any path is absolute.

**Blocks**: Phases 4, 5, 6 (cannot begin until generalized pipeline is stable)

**Produced by**: P03-T017, P03-T018

---

## QG-05 — Segmentation Model Accuracy

**Gate ID**: QG-05  
**Description**: The semantic segmentation model achieves sufficient IoU on Tecate facade imagery.

**Evaluation command**:
```bash
python3 scripts/evaluate_segmentation.py --test-dir data/case_study/segmentation_test_set/ --output data/case_study/QG05_report.json
```

**Note**: Requires a manually labeled test set of ≥10 Tecate facade images. Creating this test set is task P04-T019 (Segmentation Model Selection) — annotation is part of that task.

**Pass criteria**:
- Mean IoU across test set > 0.70 averaged over classes: wall, window, door, sky
- Inference time per image < 30 seconds on CPU
- Model output shape matches input image shape (H×W)

**Fail criteria**: Mean IoU ≤ 0.70 OR inference time > 30s.

**Remediation if fail**:
- Try alternative model from P04-T019 selection
- If no model exceeds IoU > 0.60: reduce threshold and document limitation; proceed with reduced threshold

**Blocks**: Phase 6 (P06 procedural detail requires segmentation masks)

**Produced by**: P04-T020

---

## QG-06 — SfM Sparse Point Cloud Density

**Gate ID**: QG-06  
**Description**: COLMAP produces a usable sparse point cloud from Street View images of the target facade.

**Evaluation command**:
```bash
python3 -c "
# Count points in COLMAP sparse reconstruction output
import pathlib
pts_file = pathlib.Path('data/case_study/sfm/sparse/0/points3D.txt')
with open(pts_file) as f:
    lines = [l for l in f if not l.startswith('#') and l.strip()]
n_points = len(lines)
print(f'Points: {n_points}')
assert n_points >= 500, f'FAIL: only {n_points} points (threshold: 500)'
print('QG-06 PASS')
"
```

**Pass criteria**:
- Sparse point cloud contains ≥ 500 3D points
- Point cloud bounding box in local coordinates intersects the target block polygon (within 5m)

**Fail criteria**: < 500 points OR bounding box does not intersect block polygon.

**Remediation if fail**:
- If < 50 points: COLMAP matching failed entirely — switch to monocular depth estimation (MiDaS/DPT) as fallback
- If 50–500 points: try sequential matcher instead of exhaustive; try adjusting COLMAP feature extraction parameters
- Document in `SFM_FEASIBILITY_REPORT.md` and proceed with monocular depth fallback

**Blocks**: Phase 6 mesh reconstruction from point cloud

**Produced by**: P05-T021, P05-T022

---

## QG-07 — Procedural Completion Coverage

**Gate ID**: QG-07  
**Description**: The procedural detail agent successfully identifies and fills ≥ 90% of detected missing architectural elements.

**Evaluation command**:
```bash
python3 -c "
import json
r = json.load(open('export/case_study/element_detection_report.json'))
pct = r['completion_percentage']
print(f'Completion: {pct:.1f}%')
assert pct >= 90.0, f'FAIL: {pct:.1f}% (threshold: 90%)'
print('QG-07 PASS')
"
```

**Pass criteria**:
- `completion_percentage >= 90.0`
- Final GLB passes `gltf-validator` with 0 errors (warnings allowed)

**Fail criteria**: Completion < 90% OR GLB fails validation.

**Remediation if fail**:
- Inspect `element_detection_report.json` to identify which element categories are failing
- Adjust pattern_filler minimum confidence threshold

**Blocks**: Phase 7 (QA cannot run until procedural detail is complete)

**Produced by**: Phase 6 tasks

---

## QG-08 — End-to-End Visual Quality (PSNR)

**Gate ID**: QG-08  
**Description**: The full pipeline output achieves PSNR ≥ 25 dB compared to the source imagery, and all other QA metrics pass.

**Evaluation command**:
```bash
pytest tests/acceptance/test_case_study_acceptance.py -v
```

**Pass criteria**:
- `psnr_db >= 25.0` (per `docs/research.md` Section 7)
- `reprojection_rms_px < 5.0`
- `texture_coverage_pct >= 90.0`
- `qa_report.json.overall_status == "PASS"`
- Acceptance test passes all 5 assertions

**Fail criteria**: Any metric below threshold.

**Remediation if fail**:
- PSNR < 25 dB: investigate texture extraction quality, consider better image selection
- Coverage < 90%: check for sky masking failures, re-run with different masking parameters

**Blocks**: Program complete — this is the terminal gate.

**Produced by**: P07-T024, P07-T025

---

## Gate Dependency Map

```
QG-01 ─── blocks ──→ Phase 1 ─── blocks ──→ QG-02
                                              │
                                              ▼
                                           Phase 2 ─── blocks ──→ QG-03
                                                                    │
                                                                    ▼
                                                                 Phase 3 ─── blocks ──→ QG-04
                                                                                         │
                                              ┌──────────────────────────────────────────┤
                                              ▼                    ▼                     ▼
                                           Phase 4             Phase 5              Phase 6
                                           (QG-05)             (QG-06)             (QG-07)
                                              └──────────────────────────────────────────┘
                                                                                         │
                                                                                         ▼
                                                                                      Phase 7
                                                                                      (QG-08)
```
