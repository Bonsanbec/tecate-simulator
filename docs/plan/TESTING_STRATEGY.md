# TESTING_STRATEGY.md
## Tecate 2009 — Facade Reconstruction Testing Hierarchy

---

## 1. Testing Philosophy

All tests must satisfy these constraints:
- **No live network calls** in unit and integration tests (use fixtures from `tests/fixtures/`)
- **Deterministic** — same inputs must always produce same outputs
- **Self-contained** — each test creates and cleans up its own temp files
- **Explicit failure messages** — test names and assertion messages must describe what failed and why
- **No side effects** — tests must not modify `data/`, `export/`, or any shared cache files

---

## 2. Test Structure

```
tests/
├── __init__.py
├── conftest.py                          # Shared fixtures
├── unit/                                # Fast, isolated, no I/O
│   ├── __init__.py
│   ├── test_coords.py                   # P00-T003
│   ├── test_road_distance.py            # P00-T002
│   ├── test_browser_scraper.py          # P00-T005
│   ├── test_pose_validator.py           # P02-T012
│   ├── test_reprojection_validator.py   # P02-T015
│   ├── test_psnr_evaluator.py           # P07-T023
│   ├── test_segmentation_agent.py       # P04-T020
│   └── test_camera_model.py            # P05-T022
├── integration/                         # Slower, uses disk files
│   ├── __init__.py
│   ├── test_case_study_reconstruction.py  # P02
│   ├── test_pipeline_generalized.py       # P03
│   └── test_sfm_pipeline.py              # P05
├── geospatial/                           # Spatial accuracy tests
│   ├── __init__.py
│   ├── test_block_polygon_accuracy.py
│   ├── test_facade_normal_directions.py
│   └── test_coordinate_coverage.py
├── visual/                               # Image quality tests
│   ├── __init__.py
│   ├── test_texture_coverage.py
│   ├── test_segmentation_overlay.py
│   └── test_reprojection_overlay.py
├── regression/                           # Non-regression tests
│   ├── __init__.py
│   ├── test_coordinate_stability.py     # Ensures coords.py not changed
│   ├── test_cache_schema_stability.py   # Ensures JSON schema not broken
│   └── test_output_path_portability.py  # Ensures no absolute paths in output
└── acceptance/                           # End-to-end case study validation
    ├── __init__.py
    └── test_case_study_acceptance.py     # P07-T025
```

---

## 3. Unit Tests

### UT-01 — Coordinate Round-Trip
**File**: `tests/unit/test_coords.py`  
**Purpose**: Verify GPS ↔ local coordinate accuracy at origin, case study target, and northern direction  
**Inputs**: Hardcoded GPS coordinates (32.573229, -116.626536) and (32.5728966, -116.6245526)  
**Expected outputs**: Round-trip error < 0.5m; test 2 produces x ∈ [185.0, 187.0]  
**Failure condition**: Any assertion fails; test run with no dependencies other than `src/core_io/coords.py`  
**Runtime**: < 0.1s

### UT-02 — Road Distance Correctness
**File**: `tests/unit/test_road_distance.py`  
**Purpose**: Verify perpendicular distance to segment for axis-aligned and diagonal edges  
**Inputs**: Synthetic edge endpoints and query points (hardcoded)  
**Expected outputs**: See P00-T002 implementation notes for 5 exact expected values  
**Failure condition**: Any of 5 assertions fail; specifically the diagonal case (validates P00-T001 bug fix)  
**Runtime**: < 0.1s

### UT-03 — Photometa Response Parsing
**File**: `tests/unit/test_browser_scraper.py`  
**Purpose**: Verify `parse_photometa_response` extracts correct fields from recorded fixture responses  
**Inputs**: `tests/fixtures/photometa/{pano_id}.json` (at least 2 files)  
**Expected outputs**: Non-null dict with pano_id, latitude in [32.5, 32.6], longitude in [-116.7, -116.5], date matching `^\d{4}-\d{2}$`  
**Failure condition**: Any field missing or out of range  
**Runtime**: < 0.1s (no network)

### UT-04 — Camera Pose Validation Logic
**File**: `tests/unit/test_pose_validator.py`  
**Purpose**: Verify PoseValidator correctly classifies VALID/BEHIND/OBLIQUE/OUT_OF_FOV poses  
**Inputs**: Synthetic camera and facade dictionaries  
**Test cases**:
1. Camera directly in front (heading opposing normal) → VALID
2. Camera behind facade (heading same as normal) → BEHIND
3. Camera at 80° oblique → OBLIQUE
4. Camera far to the side (facade outside 75° FOV) → OUT_OF_FOV  
**Expected outputs**: Exactly one status per test case  
**Failure condition**: Wrong status or exception  
**Runtime**: < 0.1s

### UT-05 — PSNR Computation
**File**: `tests/unit/test_psnr_evaluator.py`  
**Purpose**: Verify PSNR formula correctness  
**Test cases**:
1. Identical images (numpy zeros) → `float('inf')` or > 100 dB
2. Image vs random noise → PSNR in range [5, 15] dB
3. Known difference: 1-pixel offset → mathematically verifiable PSNR
4. ROI subset: only compare a central 256×256 region  
**Runtime**: < 0.5s

### UT-06 — Reprojection Validator Geometry
**File**: `tests/unit/test_reprojection_validator.py`  
**Purpose**: Verify projection formula for known 3D point positions  
**Test cases**:
1. Camera at (0, 0, 2.5) facing North (heading=0°), point at (0, 10, 2.5) — must project to image center (639.5, 359.5)
2. Point 5m to the right of center — must project to `639.5 + 833.7 * (5/10) ≈ 1056.4` pixels  
**Runtime**: < 0.1s

### UT-07 — Segmentation Output Format
**File**: `tests/unit/test_segmentation_agent.py`  
**Purpose**: Verify SegmentationAgent produces correct output format  
**Inputs**: Synthetic 1280×720 RGB image (uniform gray, created in-memory)  
**Expected outputs**: numpy array of shape (720, 1280), dtype uint8, values in [0, 7]  
**Failure condition**: Wrong shape, wrong dtype, values outside range  
**Runtime**: < 30s (model inference)

### UT-08 — Camera Model Quaternion
**File**: `tests/unit/test_camera_model.py`  
**Purpose**: Verify COLMAP-format camera/image parameters from heading metadata  
**Test cases**:
1. heading=0° → qw=1.0, qx=0, qy=0, qz=0 (identity rotation, camera facing North)
2. heading=90° → qw≈0.707, qz≈-0.707 (90° yaw left)
3. heading=180° → qw≈0, qz≈-1.0 (facing South)  
**Runtime**: < 0.1s

---

## 4. Integration Tests

### IT-01 — Case Study Single Block Reconstruction
**File**: `tests/integration/test_case_study_reconstruction.py`  
**Purpose**: Verify that the complete texture extraction pipeline produces expected files for the case study block  
**Inputs**: `data/case_study/` directory (must exist from Phase 1)  
**Expected outputs**: `export/case_study/target_facade_texture.png` with coverage ≥ 50%  
**Failure condition**: Missing output files, coverage < 50%, or any exception during pipeline  
**Runtime**: 30–120s (image processing)  
**Note**: Skipped if `data/case_study/` not present (Phase 1 not completed)

### IT-02 — Generalized Pipeline on 5 Random Blocks
**File**: `tests/integration/test_pipeline_generalized.py`  
**Purpose**: Verify generalized pipeline from Phase 3 runs on arbitrary blocks  
**Inputs**: `data/blocks_cache.json` (5 randomly selected blocks, seeded with `random.seed(42)`)  
**Expected outputs**: `export/textures/{block_id}_virtual_*.png` for each block (≥1 texture file per block)  
**Failure condition**: Any block fails to produce at least 1 texture file  
**Runtime**: 5–20 minutes (depends on screenshot availability)  
**Note**: Uses `--skip-scraper` mode (offline from cache)

### IT-03 — SfM Pipeline (COLMAP Wrapper)
**File**: `tests/integration/test_sfm_pipeline.py`  
**Purpose**: Verify that `src/sfm/colmap_runner.py` can run COLMAP on a minimal 2-image dataset and produce a sparse reconstruction  
**Inputs**: `data/case_study/target_images/` (at least 2 images)  
**Expected outputs**: `data/case_study/sfm/sparse/0/points3D.txt` with any content  
**Failure condition**: COLMAP not found, or output file empty/missing  
**Runtime**: 2–10 minutes  
**Skip condition**: COLMAP not installed (test is marked `pytest.mark.requires_colmap`)

---

## 5. Geospatial Validation Tests

### GV-01 — Block Polygon Area Plausibility
**File**: `tests/geospatial/test_block_polygon_accuracy.py`  
**Purpose**: Verify that all block polygons have plausible areas for a city block  
**Inputs**: `data/blocks_cache.json`  
**Expected outputs**: All blocks have area in [50, 2,500,000] m² (as filtered by extraction pipeline)  
**Failure condition**: Any block has area outside this range  
**Additional check**: The case study block `block_lat_32.57293_lon_-116.62389` has `area_sq_meters` ≈ 19,435 (within 500m² of this value)  
**Runtime**: < 5s

### GV-02 — Facade Normal Directions
**File**: `tests/geospatial/test_facade_normal_directions.py`  
**Purpose**: Verify that facade normals for the target block are outward-pointing (not inward)  
**Method**: For each facade normal [nx, ny], compute the dot product with the vector from block centroid to facade midpoint. Must be > 0 (normal points away from centroid).  
**Inputs**: `data/case_study/recomputed_midpoints.json`, block centroid  
**Expected outputs**: All normals have positive dot product with centroid-to-midpoint vector  
**Failure condition**: Any facade normal has negative dot product (pointing inward)  
**Runtime**: < 1s

### GV-03 — Case Study Facade GPS Coverage
**File**: `tests/geospatial/test_coordinate_coverage.py`  
**Purpose**: Verify that target facade midpoint GPS is within 200m of the reference GPS (32.5728966, -116.6245526)  
**Inputs**: `data/case_study/target_facade.json`  
**Expected**: Haversine distance from `midpoint_gps` to reference ≤ 200m  
**Failure condition**: Distance > 200m (indicates wrong block was selected)  
**Runtime**: < 0.1s

---

## 6. Visual Validation Tests

### VV-01 — Texture Coverage
**File**: `tests/visual/test_texture_coverage.py`  
**Purpose**: Verify that facade textures have sufficient non-transparent pixel coverage  
**Inputs**: `export/case_study/target_facade_texture.png`  
**Expected**: Non-transparent pixel count ≥ 50% of total pixels  
**Failure condition**: Coverage < 50%  
**Runtime**: < 1s

### VV-02 — Segmentation Overlay Validity
**File**: `tests/visual/test_segmentation_overlay.py`  
**Purpose**: Verify that the segmentation overlay image is non-trivial (not all one label)  
**Inputs**: `export/case_study/segmentation_overlay.png`, `data/segmentation_cache/{pano_id}_mask.png`  
**Expected**: At least 2 distinct label IDs present in the mask; mask shape matches source image shape  
**Failure condition**: Single label ID or shape mismatch  
**Runtime**: < 1s

### VV-03 — Reprojection Overlay Visibility
**File**: `tests/visual/test_reprojection_overlay.py`  
**Purpose**: Verify that reprojection overlay has at least 4 visible colored dots  
**Inputs**: `export/case_study/reprojection_validation.png`  
**Method**: Detect red pixels (R>200, G<100, B<100) and green pixels (R<100, G>200, B<100); count connected components  
**Expected**: ≥ 4 red dot regions AND ≥ 4 green dot regions  
**Failure condition**: Fewer than 4 regions of either color (indicates mesh projection is outside image)  
**Runtime**: < 2s

---

## 7. Regression Tests

### RG-01 — Coordinate Stability
**File**: `tests/regression/test_coordinate_stability.py`  
**Purpose**: Prevent silent changes to `coords.py` constants (e.g., LAT_CENTER drift)  
**Method**: Hash the content of `src/core_io/coords.py` and compare against a stored baseline hash  
**Expected**: SHA256 of `coords.py` matches stored value in `tests/regression/coord_hash.txt`  
**Update procedure**: If an intentional change is made, run `python3 scripts/update_regression_hashes.py` and commit the new hash  
**Failure condition**: Hash mismatch (indicates unexpected modification)  
**Runtime**: < 0.1s

### RG-02 — Cache Schema Stability
**File**: `tests/regression/test_cache_schema_stability.py`  
**Purpose**: Verify that the top-level keys of `blocks_cache.json`, `facades_cache.json`, and `panoramas_cache.json` have not changed (schema migration must be explicit)  
**Method**: Load a sample entry from each cache and verify required fields are present  
**Required fields per cache**:
- `blocks_cache`: `polygon`, `area_sq_meters`, `is_external`, `height_meters`
- `facades_cache`: `pano_id`, `heading`, `facade_index`
- `panoramas_cache`: `latitude`, `longitude`, `date`  
**Failure condition**: Any required field is missing from a cache entry  
**Runtime**: < 2s

### RG-03 — Output Path Portability
**File**: `tests/regression/test_output_path_portability.py`  
**Purpose**: Verify that `reconstruction_export.json` contains no absolute filesystem paths  
**Method**: Load `export/reconstruction_export.json`; for each block, scan all values in `facade_textures` dict; assert none start with `/` (Unix) or match `^[A-Z]:\\` (Windows)  
**Failure condition**: Any path is absolute (regression against gap D-2 from UNKNOWNS_AND_GAPS)  
**Runtime**: < 5s

---

## 8. Acceptance Tests

### AT-01 — Caseta Telefónica Full Pipeline Acceptance
**File**: `tests/acceptance/test_case_study_acceptance.py`  
**Purpose**: Final end-to-end validation of all case study outputs  
**Inputs**: All files in `data/case_study/` and `export/case_study/`  
**Test functions (each is separate)**:

| Function | Assert |
|----------|--------|
| `test_dataset_manifest_qg02_pass` | `data/case_study/QG02_report.json.status == "PASS"` |
| `test_facade_texture_exists_and_covered` | File exists; coverage_pct ≥ 50% |
| `test_mesh_file_exists_and_valid` | `export/case_study/target_block.glb` > 10KB; magic bytes valid |
| `test_reprojection_error_within_threshold` | `rms_reprojection_error_px < 5.0` |
| `test_qa_report_overall_pass` | `export/case_study/qa_report.json.overall_status == "PASS"` |

**Expected outputs**: All 5 functions pass  
**Failure condition**: Any function fails  
**Runtime**: < 10s (no computation — reads pre-existing files only)

---

## 9. Test Execution Order

```
Phase 0: pytest tests/unit/ -v                          # Must pass before Phase 1
Phase 1: pytest tests/unit/ tests/geospatial/ -v        # Must pass before Phase 2
Phase 2: pytest tests/unit/ tests/integration/test_case_study* -v
Phase 3: pytest tests/unit/ tests/integration/ tests/regression/ -v
Phase 4+: pytest tests/ -v --ignore=tests/acceptance/  # Full suite except acceptance
Final:   pytest tests/acceptance/ -v                    # QG-08 evaluation
```

**CI/CD recommendation**: Phases 0–3 tests run on every commit; Phase 4+ tests require explicit trigger.

---

## 10. Test Data Management

| Category | Storage | Included in Git |
|----------|---------|----------------|
| Fixture JSON files | `tests/fixtures/` | YES (≤10KB each) |
| Test images (synthetic) | Generated in-memory | NO |
| Test images (real) | `data/case_study/target_images/` | NO (listed in `.gitignore`) |
| Regression hashes | `tests/regression/*.txt` | YES |
| Acceptance outputs | `export/case_study/` | NO |
