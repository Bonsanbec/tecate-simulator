# AGENT_EXECUTION_GUIDE.md
## Tecate 2009 — Autonomous Agent Execution Guide

**Audience**: An autonomous coding agent with no prior knowledge of this project.  
**Purpose**: Everything you need to read before executing any task from `TASK_BACKLOG.md`.  
**Assumption**: You have read access to the repository at `/Users/hakkindavid/Documents/GitHub/tecate-simulator` and write access to the artifact directory.

---

## PART 1 — PROJECT ORIENTATION

### 1.1 What This Project Is

This is a pipeline that reconstructs a historical 3D city model of Tecate, Baja California, Mexico using archived Google Street View imagery from 2009. The pipeline:

1. Downloads OpenStreetMap road data
2. Extracts city block polygons (manzanas)
3. Queries Google Street View metadata to find historical panoramas
4. Captures screenshots via a headless browser
5. Warps the screenshots onto 3D building facade geometry using perspective projection
6. Exports the result as a textured 3D GLB/glTF file for use in Blender or a web viewer

Your job is to extend this pipeline with semantic segmentation, SfM-based depth estimation, procedural architectural detail, and automated quality assurance — as specified in `docs/research.md` and planned in `TASK_BACKLOG.md`.

### 1.2 Where Everything Lives

| Path | Contents |
|------|----------|
| `/Users/hakkindavid/Documents/GitHub/tecate-simulator/` | **Repository root** — all source code and data |
| `src/` | Python source modules |
| `src/core_io/coords.py` | **CRITICAL** — GPS ↔ local coordinate conversion. Do not modify without tests. |
| `src/reconstruction/prism_generator.py` | Core reconstruction engine (2,673 lines) |
| `src/data_acquisition/browser_scraper.py` | Playwright scraper + photometa API |
| `data/blocks_cache.json` | 4,239 city block polygons |
| `data/facades_cache.json` | 22,289 facade observations |
| `data/panoramas_cache.json` | 3,906 panorama metadata records |
| `export/reconstruction_export.json` | Current 3D scene document (159 blocks) |
| `docs/` | All planning and discovery documents |
| `docs/research.md` | **Target architecture** — the authoritative specification |
| `blender_script.py` | Headless Blender assembler |

### 1.3 The Coordinate System Contract

**This is the most important fact to know before writing any spatial code.**

All geometry in this project uses a **local Cartesian coordinate system** in **meters**:
- **Origin**: Parque Hidalgo, Tecate — GPS (32.573229°N, 116.626536°W)
- **X axis**: East (positive = East)
- **Y axis**: North (positive = North)
- **Z axis**: Up (positive = Up)
- **Units**: meters

The only two functions that convert between GPS and this system are:
- `src.core_io.coords.gps_to_local(lat, lon) → (x_meters, y_meters)`
- `src.core_io.coords.local_to_gps(x_meters, y_meters) → (lat, lon)`

**Never compute spatial distances or positions from GPS coordinates directly.** Always convert to local first.

The case study target (Caseta Telefónica) is at local coordinates approximately **(186m East, 37m South)** of the origin, i.e., `(186.06, -37.00)`.

### 1.4 The Case Study Target

All Phase 0–2 work is focused on a single building:

- **Name**: Caseta Telefónica LA PANZA
- **Street**: Pdte. Abelardo L. Rodríguez
- **Block ID**: `block_lat_32.57293_lon_-116.62389`
- **Reference camera GPS**: (32.5728966, -116.6245526)
- **Reference heading**: 263.88° (camera pointing nearly due West; facade faces East)
- **Block height**: 8.37m (from `blocks_cache.json`)
- **Facades in block**: 193 (all already textured in `reconstruction_export.json`)

This block **already exists** in the current output — the case study work re-runs it with explicit validation and documentation, not from scratch.

---

## PART 2 — ENVIRONMENT SETUP

### 2.1 Required Before Executing Any Task

Run these commands from the repository root and verify their output:

```bash
# 1. Verify Python version (must be 3.9+)
python3 --version

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Verify the coordinate module works
PYTHONPATH=. python3 -c "
from src.core_io.coords import gps_to_local, local_to_gps
x, y = gps_to_local(32.5728966, -116.6245526)
print(f'Target local: x={x:.2f}m, y={y:.2f}m')
# Expected: x≈186m, y≈-37m
"

# 4. Verify data files exist
ls data/blocks_cache.json data/facades_cache.json data/panoramas_cache.json

# 5. Verify target block in blocks_cache
PYTHONPATH=. python3 -c "
import json
d = json.load(open('data/blocks_cache.json'))
b = d.get('block_lat_32.57293_lon_-116.62389')
print('Block found:', b is not None)
print('Height:', b.get('height_meters'))
print('Vertices:', len(b.get('polygon', [])))
"
# Expected: Block found: True, Height: 8.369..., Vertices: 194
```

If any of these fail, stop and resolve the environment issue before proceeding. Do not attempt to execute tasks without a working environment.

### 2.2 Playwright Setup (Required for Image Capture Tasks Only)

Tasks that capture screenshots (P01-T010) require Playwright:

```bash
playwright install chromium
# Verify:
python3 -c "from playwright.sync_api import sync_playwright; print('Playwright OK')"
```

### 2.3 COLMAP Setup (Required for Phase 5 Tasks Only)

COLMAP is an external binary. Check if it's installed:

```bash
which colmap || echo "COLMAP NOT FOUND"
colmap --version
```

If not found, COLMAP must be installed before any P05-T0XX task begins. On macOS:
```bash
brew install colmap
```

### 2.4 Blender Setup (Required for Mesh Assembly Tasks Only)

Blender must be accessible at one of these paths:
- macOS: `/Applications/Blender.app/Contents/MacOS/Blender`
- Windows: `C:/Program Files/Blender Foundation/Blender 5.1/blender.exe`

Verify:
```bash
/Applications/Blender.app/Contents/MacOS/Blender --version
```

---

## PART 3 — TASK EXECUTION PROTOCOL

### 3.1 Before Starting Any Task

1. **Read the full task entry** in `TASK_BACKLOG.md` — do not skip any field
2. **Verify all prerequisites** are met (check that prerequisite task IDs are complete)
3. **Check quality gate status** — if the task is blocked by a gate, verify the gate report file shows PASS
4. **Verify all input files exist** (listed in "Input artifacts")
5. **Create the output directory** if it does not exist:
   ```bash
   mkdir -p data/case_study export/case_study src/reconstruction src/qa src/sfm src/segmentation src/procedural tests/unit tests/integration tests/geospatial tests/visual tests/regression tests/acceptance tests/fixtures/photometa scripts
   ```

### 3.2 Executing a Task

1. Write the code/file specified in "Output artifacts"
2. Follow the "Implementation notes" exactly — these are the algorithmic requirements
3. Do not add features not listed in the task
4. Do not modify files not listed in "Repository locations affected"
5. After writing: run the "Validation procedure" and verify it passes

### 3.3 After Completing a Task

Record completion by creating a completion marker:
```bash
echo '{"status": "COMPLETE", "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"}' \
  > data/case_study/.task_status/P0N-T0NN.json
```

(Replace `P0N-T0NN` with the actual task ID)

---

## PART 4 — DECISION TREES FOR COMMON FAILURES

### 4.1 JSON File Fails to Load

```
json.JSONDecodeError when loading a cache file
    │
    ├─ Is the file empty (0 bytes)?
    │   └─ YES: File was partially written during shutdown. Restore from git:
    │           git checkout -- data/blocks_cache.json
    │
    ├─ Does the file contain a Python repr instead of JSON? (e.g., True instead of true)
    │   └─ YES: The file was written with Python's str() not json.dump().
    │           Fix: PYTHONPATH=. python3 -c "
    │                import ast, json
    │                d = ast.literal_eval(open('data/bad_file.json').read())
    │                json.dump(d, open('data/bad_file.json','w'))"
    │
    └─ Otherwise: Use the most recent git commit to restore:
                  git stash && git checkout -- data/
```

### 4.2 `gps_to_local` Returns Unexpected Values

```
Coordinate conversion gives wrong result
    │
    ├─ Is x approximately -37 and y approximately 186 (axes swapped)?
    │   └─ YES: You called gps_to_local(lon, lat) instead of gps_to_local(lat, lon).
    │           Fix: swap arguments.
    │
    ├─ Is the result in the thousands of meters but the wrong sign?
    │   └─ YES: You may have subtracted center from point in the wrong order.
    │           The formula is: dx = R * radians(lon - LON_C) * cos(radians(LAT_C))
    │
    └─ Is the result in degrees (tiny number like 0.00017)?
        └─ YES: You forgot to multiply by EARTH_RADIUS or radians conversion.
```

### 4.3 Playwright Screenshot Is All Black or Blank

```
Screenshot returns bytes but image is all black
    │
    ├─ Are you running in headless mode without a display?
    │   └─ YES: Add --use-gl=swiftshader to browser args (already in browser_scraper.py).
    │           Verify: headless=True is set.
    │
    ├─ Did the page fail to load (network timeout)?
    │   └─ YES: The Street View URL may have changed or the panorama may no longer exist.
    │           Try a different pano_id from panoramas_cache.json.
    │
    └─ Is the image 1280x720 but all one color (#f0f0f0)?
        └─ YES: Google Maps loaded but Street View didn't render.
                Wait longer: increase sleep time from 1.0s to 3.0s in capture_facade_screenshot.
```

### 4.4 COLMAP Produces 0 Points

```
COLMAP sparse reconstruction output is empty
    │
    ├─ Do you have at least 2 images?
    │   └─ NO: COLMAP requires ≥2 images. Add more images or switch to monocular depth.
    │
    ├─ Are the images nearly identical (same camera position)?
    │   └─ YES: Triangulation baseline is too short. This is RISK-02.
    │           Switch to monocular depth estimation (MiDaS) as documented in RISK_REGISTER.md.
    │
    ├─ Did feature extraction produce 0 keypoints?
    │   └─ YES: Images may be too dark or blurry.
    │           Try: colmap feature_extractor ... --ImageReader.camera_model SIMPLE_PINHOLE
    │
    └─ Did matching produce 0 pairs?
        └─ YES: Images don't share visible content.
                Verify images are of the same facade from different angles.
```

### 4.5 Blender Subprocess Fails

```
subprocess.run([blender_path, ...]) returns non-zero exit code
    │
    ├─ Is the exit code 127 (command not found)?
    │   └─ YES: Blender path is wrong. Check ENVIRONMENT.md for the correct path.
    │           Try: shutil.which("blender") to auto-detect.
    │
    ├─ Is there a Python error in the Blender log?
    │   └─ YES: Read the full Blender stderr output. Common issues:
    │           - Missing import: add to blender_script.py's top-level imports
    │           - JSON parse error: verify the scene document is valid JSON
    │
    └─ Does Blender open but not close?
        └─ YES: The script has an infinite loop or unhandled exception.
                Run with: blender --background --debug-python --python blender_script.py ...
```

### 4.6 Texture Coverage Below Threshold

```
texture_extraction_report.json.coverage_pct < 50%
    │
    ├─ Is the source image all black or all gray?
    │   └─ YES: Screenshot capture failed. Re-run P01-T010 for this pano.
    │
    ├─ Is coverage_pct exactly 0.0%?
    │   └─ YES: The facade is behind the camera (camera heading and facade normal are aligned,
    │           not opposing). Check: alignment_dot_product in pose_validation_report.json.
    │           If positive: camera is behind facade. Flip heading by 180°.
    │
    ├─ Is coverage_pct between 10–50%?
    │   └─ YES: Sky masking removed too many pixels.
    │           Check: mask_sky_in_panorama threshold. Try reducing sky color threshold
    │           from 35.0 to 25.0.
    │
    └─ Is coverage_pct > 50% but texture looks wrong?
        └─ YES: Homography projection is off. Verify facade vertex coordinates
                (A, B) are in local Cartesian meters, not GPS degrees.
```

---

## PART 5 — DATA FORMAT CONTRACTS

Every file written by any task must conform to these contracts. Do not deviate.

### 5.1 JSON Files

- Encoding: UTF-8
- No trailing commas
- All float values: maximum 8 decimal places
- All paths: relative to repository root (no absolute paths starting with `/Users/` or `C:\`)
- Null values: JSON `null` (not Python `None` as a string)
- Timestamps: ISO 8601 format `"YYYY-MM-DDTHH:MM:SSZ"` (UTC)

### 5.2 PNG Image Files

- RGBA for textures (4 channels) — transparent pixels must have alpha = 0, not alpha = 128
- RGB for diagnostic/overlay images (3 channels)
- Uint8 data type (0–255 per channel)
- No embedded ICC profiles unless explicitly required
- Dimensions: match the specification in the task (e.g., 512×512 for facade textures)

### 5.3 GLB/glTF Files

- Format: GLB (binary glTF) for standalone files
- All texture references: relative paths from the directory containing the glTF
- Z-up coordinate convention (Blender default after Z-up export setting)
- Must pass `gltf-validator` with 0 errors before acceptance

### 5.4 Python Module Files

- All new modules must have a docstring at the top explaining their purpose
- All new classes must have `__init__` docstrings
- All new public methods must have docstrings specifying input/output types
- No `print()` statements in library code — use `logging.getLogger(__name__)`
- Import order: stdlib → third-party → local (separated by blank lines)

### 5.5 Test Files

- Each test function must have a name starting with `test_`
- Each test function must have a one-line docstring
- Assertions must include a descriptive message: `assert x == y, f"Expected {y}, got {x}"`
- No `time.sleep()` in tests
- No network calls in unit tests

---

## PART 6 — PHASE-BY-PHASE QUICK-START CHECKLISTS

### Phase 0 Checklist

```
[ ] Read docs/CODEBASE_ANALYSIS.md Section 3 (Known Code Issues)
[ ] Locate line 766 in src/reconstruction/prism_generator.py
[ ] Verify the line reads: t = ((mx - ux) * dx + (my - my) * dy) / seg_len_sq
[ ] Fix: change (my - my) to (my - uy)
[ ] Run: grep -n "my - my" src/reconstruction/prism_generator.py  → should return 0 results
[ ] Create tests/ directory structure
[ ] Write tests/unit/test_coords.py (5 test cases, see TASK_BACKLOG.md P00-T003)
[ ] Run: PYTHONPATH=. pytest tests/unit/test_coords.py -v
[ ] Write tests/unit/test_road_distance.py (5 test cases, see P00-T002)
[ ] Run: PYTHONPATH=. pytest tests/unit/test_road_distance.py -v
[ ] All tests pass → QG-01 satisfied
[ ] Write ENVIRONMENT.md
[ ] Phase 0 COMPLETE
```

### Phase 1 Checklist

```
[ ] QG-01 status: PASS (run tests/unit/test_coords.py)
[ ] Create data/case_study/ directory
[ ] Create scripts/ directory
[ ] Run P01-T007: scripts/identify_target_facade.py
[ ] Verify data/case_study/target_facade.json exists and alignment_dot_product > 0.5
[ ] Run P01-T008: scripts/recompute_midpoints.py
[ ] Verify all 193 midpoints are non-null in facades_cache.json
[ ] Run P01-T009: scripts/collect_case_study_images.py
[ ] Check count: ls data/case_study/target_images/ | wc -l  → should be ≥ 1
[ ] If 0 images: Run P01-T010: scripts/capture_missing_screenshots.py
[ ] Run P01-T011: scripts/evaluate_qg02.py
[ ] Verify data/case_study/QG02_report.json status == "PASS"
[ ] Phase 1 COMPLETE
```

### Phase 2 Checklist

```
[ ] QG-02 status: PASS
[ ] Create src/reconstruction/pose_validator.py (P02-T012)
[ ] Run pose validation, verify ≥1 VALID panorama
[ ] Create export/case_study/ directory
[ ] Run texture extraction: scripts/extract_case_study_texture.py (P02-T013)
[ ] Verify coverage_pct ≥ 50% in texture_extraction_report.json
[ ] Run Blender assembly: scripts/build_case_study_block.py (P02-T014)
[ ] Verify export/case_study/target_block.glb exists and is > 10KB
[ ] Create src/qa/ directory
[ ] Implement src/qa/reprojection_validator.py (P02-T015)
[ ] Run reprojection validation
[ ] Verify rms_reprojection_error_px < 5.0  → QG-03 satisfied
[ ] Run: scripts/generate_phase2_report.py (P02-T016)
[ ] Verify overall_status == "PASS"
[ ] Phase 2 COMPLETE
```

### Phase 3 Checklist

```
[ ] QG-03 status: PASS
[ ] Fix absolute paths in prism_generator.py (P03-T017)
[ ] Verify: grep -r "^/Users" export/reconstruction_export.json → 0 results
[ ] Create configs/ directory
[ ] Write src/reconstruction/config_schema.json (P03-T018)
[ ] Write configs/default.json and configs/case_study.json
[ ] Run generalized pipeline on 5 blocks
[ ] Run: PYTHONPATH=. pytest tests/integration/test_pipeline_generalized.py -v
[ ] All tests pass → QG-04 satisfied
[ ] Phase 3 COMPLETE
```

### Phase 4 Checklist (Parallel with Phase 5)

```
[ ] QG-04 status: PASS
[ ] Read docs/SEGMENTATION_MODEL_SELECTION.md (must exist from P04-T019)
[ ] Install selected model: follow SEGMENTATION_MODEL_SELECTION.md instructions
[ ] Create src/segmentation/ directory
[ ] Implement src/segmentation/segmentation_agent.py (P04-T020)
[ ] Run: PYTHONPATH=. pytest tests/unit/test_segmentation_agent.py -v
[ ] Run segmentation on 10 test images
[ ] Compute IoU against manual labels
[ ] Verify mean IoU > 0.70  → QG-05 satisfied
[ ] Phase 4 COMPLETE
```

### Phase 5 Checklist (Parallel with Phase 4)

```
[ ] QG-04 status: PASS
[ ] Verify COLMAP is installed: colmap --version
[ ] Run feasibility test: COLMAP on case study images (P05-T021)
[ ] Read SFM_FEASIBILITY_REPORT.md → note FEASIBLE or FALLBACK path
[ ] Create src/sfm/ directory
[ ] Implement src/sfm/camera_model.py (P05-T022)
[ ] Run: PYTHONPATH=. pytest tests/unit/test_camera_model.py -v
[ ] If FEASIBLE: run full COLMAP pipeline on case study images
[ ] Verify point count ≥ 500  → QG-06 satisfied
[ ] If NOT FEASIBLE: implement MiDaS fallback and document in SFM_FEASIBILITY_REPORT.md
[ ] Phase 5 COMPLETE
```

---

## PART 7 — WHAT NEVER TO DO

These are hard constraints. Violating them will break the pipeline for all subsequent tasks.

| ❌ NEVER DO THIS | ✅ DO THIS INSTEAD |
|-----------------|------------------|
| Modify `src/core_io/coords.py` without running `tests/unit/test_coords.py` | Run the full coordinate test suite before and after any change |
| Write absolute paths into any JSON output file | Use `os.path.relpath(path, start=repo_root)` |
| Call `json.dump` directly on a cache file without atomic write | Write to a `.tmp` file first, then `os.replace(tmp, final)` |
| Import `UrbanBlockReconstructor` in tests without mocking data files | Extract pure functions into standalone helpers for testing |
| Run Playwright without headless mode on a CI/server environment | Always pass `headless=True` to `GoogleStreetViewScraper` |
| Commit `data/screenshots/` to git | Screenshots are in `.gitignore` by convention |
| Use `print()` in library modules | Use `logging.getLogger(__name__).info(...)` |
| Skip a quality gate and proceed anyway | Fix the gate failure before the next phase |
| Modify `data/blocks_cache.json` or `data/facades_cache.json` without atomic write | Atomic write: write to `.tmp` then `os.replace` |

---

## PART 8 — USEFUL DEBUGGING COMMANDS

```bash
# Check how many facades have null midpoints
PYTHONPATH=. python3 -c "
import json
d = json.load(open('data/facades_cache.json'))
null_count = sum(1 for v in d.values() if v.get('facade_midpoint_local') is None)
print(f'Facades with null midpoint: {null_count} / {len(d)}')
"

# Find all facades for a specific block
PYTHONPATH=. python3 -c "
import json
d = json.load(open('data/facades_cache.json'))
block_id = 'block_lat_32.57293_lon_-116.62389'
block_facades = {k: v for k, v in d.items() if k.startswith(block_id)}
print(f'Facades for target block: {len(block_facades)}')
# Print unique pano_ids
panos = set(v.get('pano_id') for v in block_facades.values())
print(f'Unique pano_ids: {len(panos)}')
"

# Check which screenshots exist for a given pano_id
ls data/screenshots/pano/ | grep "V3kxZDRqXe2BHU8FpAg17A"

# Verify a JSON file is valid
python3 -m json.tool data/case_study/target_facade.json > /dev/null && echo "VALID"

# Check a GLB file's magic bytes
python3 -c "
with open('export/case_study/target_block.glb', 'rb') as f:
    magic = f.read(4)
    print('Magic:', magic)
    print('Is glTF:', magic == b'glTF')
"

# Count points in COLMAP sparse reconstruction
wc -l < <(grep -v "^#" data/case_study/sfm/sparse/0/points3D.txt 2>/dev/null || echo "0")

# Run full test suite
PYTHONPATH=. pytest tests/ -v --tb=short 2>&1 | tail -30

# Run only fast unit tests
PYTHONPATH=. pytest tests/unit/ -v

# Run with coverage
PYTHONPATH=. pytest tests/unit/ --cov=src --cov-report=term-missing
```

---

## PART 9 — AUTOMATION CLASSIFICATION REFERENCE

Every task in `TASK_BACKLOG.md` is classified by automation level. Here is the decision rule used:

| Classification | Meaning | Examples |
|---------------|---------|---------|
| **FULLY AUTOMATABLE** | An agent can complete this from start to finish with no human input, given the task spec. All decisions are explicit in the spec. | P00-T001, P00-T002, P00-T003, P01-T008, P02-T012, P02-T013, P02-T015, P07-T023 |
| **SEMI-AUTOMATED** | An agent does most work but one step requires either: live network access (not mockable), Playwright browser, or OS-level tool installation. Human must approve execution. | P00-T004, P00-T006, P01-T010, P02-T014, P05-T021 |
| **MANUAL** | A human decision is required and cannot be programmatically delegated. Model selection with license review, annotation labeling, visual quality inspection. | P04-T019 |

---

## PART 10 — DOCUMENT CROSS-REFERENCE

| Question | Document |
|----------|---------|
| What is the overall architecture? | `IMPLEMENTATION_MASTER_PLAN.md` |
| What does each phase do? | `PHASE_BREAKDOWN.md` |
| What are the specific tasks? | `TASK_BACKLOG.md` |
| What must pass before phase N? | `QUALITY_GATES.md` |
| What tests exist and what do they verify? | `TESTING_STRATEGY.md` |
| Which tasks depend on which? | `DEPENDENCY_GRAPH.md` |
| What are the known risks? | `RISK_REGISTER.md` |
| How do I reconstruct the case study target? | `CASE_STUDY_EXECUTION_PLAN.md` |
| What is the target architecture from research? | `docs/research.md` |
| What does the current codebase do? | `docs/PIPELINE_RECONSTRUCTION.md` |
| What are the data schemas? | `docs/DATA_MODEL.md` |
| What coordinate system is used? | `docs/GEOSPATIAL_MODEL.md` |
| What are all the known gaps? | `docs/UNKNOWNS_AND_GAPS.md` |
| What assets exist? | `docs/ASSET_INVENTORY.md` |
