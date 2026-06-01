# PHASE BREAKDOWN
## Tecate 2009 — AI-Assisted Facade Reconstruction

---

## PHASE 0 — Foundation Repair & Environment Verification

**Purpose**: Establish a verified, reproducible development environment and fix known bugs before any new feature work begins. No new features are added in this phase.

**Duration estimate**: 5–8 working days

**Inputs**:
- Existing repository at current commit
- Discovery documents A–H in `docs/`
- `docs/CODEBASE_ANALYSIS.md` bug list (specifically the `my - my` typo)

**Outputs**:
- `tests/unit/test_coords.py` — coordinate round-trip unit tests
- `tests/unit/test_road_distance.py` — road distance calculation tests (including bug regression)
- `tests/fixtures/` — recorded API response fixtures for offline testing
- Bug fix in `src/reconstruction/prism_generator.py` line 766 (`my - my` → `my - uy`)
- `ENVIRONMENT.md` — verified dependency versions and setup instructions
- `tests/conftest.py` — shared pytest fixtures

**Dependencies**: None (this is the root phase)

**Risks**:
- Bug fix at line 766 may subtly alter which facades are classified as street-facing — must quantify the delta
- Fixture recording requires live API access

**Validation criteria**:
- All unit tests pass
- `coords.py` round-trip error verified < 0.5m for target location (32.5728966, -116.6245526)
- Road distance test confirms correct perpendicular distance for diagonal edge
- Bug fix delta report: count of facades that change street-facing status

**Estimated complexity**: Low (2–3 engineers × 1 day each)

**Quality gates produced**: QG-01 (coordinate accuracy)

---

## PHASE 1 — Case Study Dataset Preparation

**Purpose**: Assemble and verify a complete, documented dataset package for the Caseta Telefónica facade reconstruction case study. No reconstruction algorithms are run in this phase — only data collection, verification, and documentation.

**Duration estimate**: 3–5 working days

**Inputs**:
- `data/blocks_cache.json` — block polygon for `block_lat_32.57293_lon_-116.62389`
- `data/facades_cache.json` — 193 facade entries for the target block
- `data/panoramas_cache.json` — associated panorama metadata
- `data/screenshots/pano/` — existing screenshots for target block
- `export/reconstruction_export.json` — current 3D export (target block is present)
- Google Maps reference: `@32.5728966,-116.6245526, heading 263.88°`
- Street: Pdte. Abelardo L. Rodríguez (OSM edge IDs: `e_1367`–`e_1385`)

**Outputs**:
- `data/case_study/` directory with:
  - `case_study_manifest.json` — complete dataset description
  - `target_facade.json` — selected facade(s) facing Pdte. Abelardo L. Rodríguez
  - `target_panoramas.json` — all panoramas covering the target
  - `target_images/` — copies of or symlinks to relevant screenshots
  - `target_block.json` — block polygon + geometry for the target block
  - `validation_reference.json` — ground truth from Google Maps reference URL
- `docs/CASE_STUDY_BASELINE.md` — human-readable description of dataset

**Dependencies**: Phase 0 complete (QG-01 passed)

**Risks**:
- The `facade_midpoint_local` field is null for this block's facades (confirmed in inspection) — requires recomputation from polygon vertices
- Target facade may not be a single polygon segment but multiple collinear sub-segments — requires identification of the correct contiguous group
- Street View heading 263.88° (nearly due West) must be matched to the correct facade normal

**Validation criteria**:
- `case_study_manifest.json` passes schema validation
- Target facade midpoint local coordinate distance from reference GPS < 10m
- At least 1 panorama with date ≤ 2009 covers the target facade with alignment dot product < −0.5
- All referenced image files exist on disk

**Estimated complexity**: Low-Medium (primarily data forensics + scripting)

**Quality gates produced**: QG-02 (dataset completeness)

---

## PHASE 2 — Single Facade Reconstruction (Case Study)

**Purpose**: Execute a complete end-to-end reconstruction of the Caseta Telefónica facade using the current pipeline augmented with explicit pose validation, image quality checking, and output verification. This phase validates the existing pipeline against the case study before replacing it with the research.md architecture.

**Duration estimate**: 8–12 working days

**Inputs**:
- `data/case_study/` from Phase 1
- Existing `src/reconstruction/prism_generator.py`
- Existing `blender_script.py`
- Phase 0 bug fix applied

**Outputs**:
- `export/case_study/target_facade_texture.png` — perspective-warped facade texture
- `export/case_study/target_block.glb` — 3D block mesh (GLB format)
- `export/case_study/reprojection_validation.png` — overlay of mesh projection on source image
- `export/case_study/pose_validation_report.json` — camera pose verification
- `export/case_study/quality_report.json` — PSNR, coverage %, facade completeness
- `tests/integration/test_case_study_reconstruction.py` — reproducibility test

**Dependencies**: Phase 1 complete (QG-02 passed)

**Sub-phases**:
1. **P2-A: Pose validation** — verify camera pose and facade normal alignment
2. **P2-B: Image selection** — select best ≤3 images per facade
3. **P2-C: Texture extraction** — run existing homography pipeline
4. **P2-D: Mesh creation** — run Blender assembly for single block
5. **P2-E: Reprojection test** — project mesh back into source images, measure error
6. **P2-F: Quality report** — compute coverage %, PSNR (vs. source image), reprojection error

**Risks**:
- Blender subprocess invocation may require path configuration
- PSNR computation requires a synthetic "ground truth" view — use source image directly
- Reprojection code does not exist yet (must be written in this phase)

**Validation criteria (QG-03)**:
- Reprojection error of reconstructed mesh into source image < 5px RMS
- Facade coverage ≥ 90% (non-transparent pixels / total facade area)
- Texture resolution ≥ 256×256 px per facade segment
- GLB file loads successfully in a glTF viewer

**Estimated complexity**: Medium (requires new reprojection test tool)

**Quality gates produced**: QG-03

---

## PHASE 3 — Pipeline Generalization

**Purpose**: Abstract the case-study-specific reconstruction logic into a fully configurable pipeline that can process any block in `blocks_cache.json`. This phase introduces a configuration schema and removes hardcoded assumptions.

**Duration estimate**: 6–8 working days

**Inputs**:
- Phase 2 outputs (validated case study pipeline)
- Full `data/blocks_cache.json` (4,239 blocks)
- Current `src/reconstruction/prism_generator.py`

**Outputs**:
- Refactored `src/reconstruction/pipeline.py` — configurable pipeline class
- `src/reconstruction/config_schema.json` — JSON schema for pipeline configuration
- `configs/default.json` — default configuration
- `configs/case_study.json` — case study configuration
- `tests/integration/test_pipeline_generalized.py` — tests for 5 random blocks
- Updated `docs/DATA_MODEL.md` with any new output fields

**Dependencies**: Phase 2 complete (QG-03 passed)

**Risks**:
- Hardcoded absolute paths in `reconstruction_export.json` (gap D-2) must be resolved to relative paths in this phase
- `pano_to_edge` adjacency may use different edge IDs than OSM graph (gap D-3) — must be diagnosed and fixed

**Validation criteria**:
- Pipeline runs successfully on 5 non-case-study blocks without code changes
- All output paths are relative to `export/` directory (no hardcoded absolute paths)
- `src/reconstruction/pipeline.py` passes `pylint` with score ≥ 8.0

**Estimated complexity**: Medium-High (significant refactoring)

**Quality gates produced**: QG-04 (format compatibility)

---

## PHASE 4 — Semantic Segmentation Integration

**Purpose**: Add a semantic segmentation agent that labels facade images by architectural element type (wall, window, door, balcony, sign, sky, vegetation). This enables procedural completion and quality-aware texture selection.

**Duration estimate**: 10–14 working days

**Inputs**:
- `export/case_study/target_facade_texture.png` and related images
- `data/screenshots/pano/` — existing screenshot corpus
- Pre-trained segmentation model (DeepFacade or equivalent — see Implementation Notes in TASK_BACKLOG)

**Outputs**:
- `src/segmentation/` Python module with:
  - `segmentation_agent.py` — main class
  - `model_loader.py` — model download and loading
  - `label_map.py` — label ID → element name mapping
- `data/segmentation_cache/` — per-image segmentation mask PNGs (label IDs per pixel)
- `export/case_study/segmentation_overlay.png` — visualization
- Model weights cached at `models/segmentation/`
- `tests/unit/test_segmentation_agent.py`

**Dependencies**: Phase 3 complete (QG-04 passed)

**Risks**:
- Pre-2010 Street View imagery may differ in quality/style from model training data → IoU may be lower than expected
- Model download may require network access during test — must be mocked in CI
- `research.md` mentions DeepFacade but does not specify a particular model checkpoint — selection must be documented

**Validation criteria (QG-05)**:
- Segmentation IoU > 0.7 on held-out test set of ≥10 Tecate facade images (manually labeled reference masks required)
- Segmentation runs in < 10 seconds per image on CPU
- Output mask PNGs are uint8, single-channel, matching input image dimensions exactly

**Estimated complexity**: High (ML model integration, annotation work needed)

**Quality gates produced**: QG-05

---

## PHASE 5 — SfM/MVS Depth Estimation Integration

**Purpose**: Integrate Structure-from-Motion and Multi-View Stereo to generate 3D point clouds from Street View image collections, per the research.md pipeline specification.

**Duration estimate**: 12–16 working days

**Inputs**:
- `data/case_study/target_images/` — ≥3 images of the case study facade
- `data/case_study/target_panoramas.json` — camera intrinsics and extrinsics
- COLMAP (external tool, must be installed)

**Outputs**:
- `src/sfm/` Python module:
  - `colmap_runner.py` — subprocess wrapper for COLMAP CLI
  - `camera_model.py` — pinhole camera model from existing `coords.py` parameters
  - `point_cloud_exporter.py` — COLMAP → Open3D point cloud converter
- `data/case_study/sfm/` — COLMAP workspace files
- `data/case_study/point_cloud.ply` — sparse point cloud
- `data/case_study/dense_cloud.ply` — dense point cloud (if ≥3 images available)
- `tests/unit/test_camera_model.py`
- `tests/integration/test_sfm_pipeline.py`

**Dependencies**: Phase 3 complete (QG-04 passed); Phase 0 environment verification

**Critical sub-task**: Image count audit — if fewer than 3 overlapping images exist per facade, the SfM approach fails and monocular depth estimation (e.g., MiDaS or DPT) must be used as fallback.

**Risks (RISK-03)**:
- Street View cameras are near-coplanar (camera moves along street, all facing the same facade) — SfM baseline may be too short for reliable triangulation
- COLMAP may fail silently — robust error detection required
- Dense MVS requires large disk space for intermediate files

**Validation criteria (QG-06)**:
- COLMAP produces a sparse reconstruction with ≥ 500 points for the target facade
- Point cloud bounding box aligns with block polygon footprint in local coordinates within 1.5m
- Dense cloud if available has ≥ 5,000 points covering target facade area

**Estimated complexity**: Very High (external tool integration, potential geometric feasibility issue)

**Quality gates produced**: QG-06

---

## PHASE 6 — Procedural Detail & Mesh Completion

**Purpose**: Implement the procedural detail agent that infers and inserts missing architectural elements (windows, doors, cornices) using patterns detected by the segmentation agent.

**Duration estimate**: 8–12 working days

**Inputs**:
- `data/segmentation_cache/` — segmentation masks from Phase 4
- `data/case_study/point_cloud.ply` — from Phase 5
- Block polygon geometry from `blocks_cache.json`
- Research.md Section 2 (Agente de Detallado Procedimental)

**Outputs**:
- `src/procedural/` Python module:
  - `element_detector.py` — detects periodic elements (windows, doors) from segmentation
  - `pattern_filler.py` — infers missing elements from detected patterns
  - `mesh_assembler.py` — creates element geometry and merges with base mesh
- `export/case_study/detailed_facade.glb` — mesh with procedural elements
- `export/case_study/element_detection_report.json` — detected elements + positions
- `tests/unit/test_element_detector.py`

**Dependencies**: Phase 4 complete (QG-05 passed), Phase 5 complete (QG-06 passed)

**Risks**:
- Single-story commercial facades (typical for Tecate downtown) may have low window periodicity — pattern detection may yield no elements
- Mesh merging (base prism + procedural elements) must preserve UV coordinate integrity

**Validation criteria (QG-07)**:
- Detected window grid positions project correctly into source images (< 10px error)
- Procedural completion fills ≥ 90% of detected element positions
- Final GLB file passes glTF validation (`gltf-validator` tool)

**Estimated complexity**: High

**Quality gates produced**: QG-07

---

## PHASE 7 — Validation, QA Agent & Metrics

**Purpose**: Implement the QA agent that computes objective quality metrics for any reconstructed facade and generates automated validation reports. Also implements regression tests to prevent future regressions.

**Duration estimate**: 8–10 working days

**Inputs**:
- All Phase 2–6 outputs
- Source images from `data/screenshots/pano/`
- `export/case_study/*.glb` — reconstructed meshes
- Research.md Section 7 (Métricas de calidad y pruebas automáticas)

**Outputs**:
- `src/qa/` Python module:
  - `reprojection_validator.py` — projects mesh into camera images, measures pixel error
  - `coverage_analyzer.py` — computes % of facade area with valid texture
  - `psnr_evaluator.py` — PSNR between rendered view and source image
  - `qa_report_generator.py` — produces JSON + PNG summary
- `export/case_study/qa_report.json` — complete quality report
- `export/case_study/qa_overlays/` — reprojection error visualization images
- `tests/regression/` — full regression suite
- `tests/acceptance/test_case_study_acceptance.py` — final acceptance test

**Dependencies**: All previous phases complete

**Validation criteria (QG-08)**:
- Full pipeline PSNR ≥ 25 dB on held-out view synthesis test
- Reprojection RMS < 5px
- Coverage ≥ 90%
- QA report JSON schema validates successfully
- All regression tests pass
- Acceptance test passes on Caseta Telefónica case study

**Estimated complexity**: Medium (primarily evaluation tooling)

**Quality gates produced**: QG-08 (program complete)
