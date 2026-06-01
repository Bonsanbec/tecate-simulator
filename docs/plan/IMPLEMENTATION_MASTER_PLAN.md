# IMPLEMENTATION MASTER PLAN
## Tecate 2009 Urban Reconstruction — AI-Assisted Facade Pipeline

**Document version**: 1.0  
**Authored**: 2026-06-01  
**Primary authority**: `docs/research.md` (target architecture) + discovery documents A–H  
**Reconstruction target milestone**: Caseta Telefónica LA PANZA, Pdte. Abelardo L. Rodríguez

---

## 1. Program Summary

This plan transforms the `tecate-simulator` repository from its current state — a functional prism-extrusion pipeline with perspective-warped Street View textures — into a full AI-assisted facade reconstruction system as specified in `docs/research.md`.

The target architecture introduces:
- Semantic facade segmentation (CNN-based, per-element labeling)
- Multi-view depth estimation and/or SfM/MVS point cloud generation
- Mesh reconstruction from point clouds (Poisson/Ball Pivoting)
- Procedural architectural detail completion
- Neural rendering validation (PSNR/LPIPS metrics)
- An orchestrated multi-agent pipeline

The plan is organized around a **validation-first philosophy**: every system change is validated against the Caseta Telefónica facade before being applied at city scale.

---

## 2. Scope Boundaries

### In Scope
- All Python code in `src/`
- `blender_script.py`
- `data/` cache schema evolution
- `export/` output format extensions
- New modules for: segmentation, SfM integration, mesh reconstruction, procedural detail, QA
- Test infrastructure
- The single-facade validation case study

### Out of Scope
- The terrain GLB models in `models/tecate/` (treated as read-only external assets)
- The Google Street View scraping infrastructure (treated as stable; no changes unless a bug is confirmed)
- Runtime visualization engines (Babylon.js, Three.js, Unity) — only GLB/glTF output format is in scope
- Cloud infrastructure deployment

---

## 3. Authoritative References

| Reference | Role |
|-----------|------|
| `docs/research.md` | Target architecture — primary authority |
| `docs/REPOSITORY_OVERVIEW.md` | Current system architecture |
| `docs/DATA_MODEL.md` | Current data schemas |
| `docs/GEOSPATIAL_MODEL.md` | Coordinate system contract |
| `docs/ASSET_INVENTORY.md` | Available assets |
| `docs/PIPELINE_RECONSTRUCTION.md` | Current pipeline steps |
| `docs/CODEBASE_ANALYSIS.md` | Known bugs and unused code |
| `docs/RECONSTRUCTION_READINESS.md` | Current capability gaps |
| `docs/UNKNOWNS_AND_GAPS.md` | All open risks |

---

## 4. Foundational Assumptions

The following assumptions are made explicit. Each must be verified before the corresponding phase begins.

| ID | Assumption | Verification Method |
|----|-----------|---------------------|
| ASM-01 | The block `block_lat_32.57293_lon_-116.62389` contains the Caseta Telefónica facade | Visual verification via Google Maps coordinate comparison |
| ASM-02 | The Google Street View panorama at `@32.5728966,-116.6245526` heading 263.88° is accessible via the photometa API | API call test |
| ASM-03 | COLMAP can be installed and run on the development machine | `colmap --version` |
| ASM-04 | The equirectangular projection in `coords.py` is accurate within 0.5m at 500m radius | Roundtrip test: GPS → local → GPS |
| ASM-05 | Facade polygon vertices in `blocks_cache.json` are in local Cartesian meters | Numeric verification |
| ASM-06 | The `facade_midpoint_local` field is null for older cache entries (confirmed by inspection) | Count null entries in facades_cache |
| ASM-07 | The research.md SfM/MVS approach is feasible with ≥3 Street View images of the same facade | Literature review + test run |
| ASM-08 | `py360convert` (already in requirements.txt) can convert equirectangular panoramas to perspective tiles | Functional test |

---

## 5. Technical Risk Summary

Detailed risks are in `RISK_REGISTER.md`. Critical risks affecting program structure:

| Risk ID | Risk | Mitigation in Plan |
|---------|------|--------------------|
| RISK-01 | Google API format changes break metadata acquisition | Scraping is isolated; plan adds integration tests with recorded fixtures |
| RISK-02 | Terrain-reconstruction coordinate frame undefined (gap A-1) | Phase 1 includes explicit terrain alignment validation task |
| RISK-03 | Only 1–3 Street View images per facade (SfM requires ≥3 with overlap) | Plan includes image count audit before SfM phase; fallback to monocular depth |
| RISK-04 | `get_road_distance` bug (my-my typo) causes incorrect street-facing detection | Phase 1 bug-fix task |
| RISK-05 | Semantic segmentation model may not generalize to 2009 Tecate imagery | Case study validation before city-scale deployment |
| RISK-06 | COLMAP SfM may fail for near-coplanar Street View images | Feasibility test task with recorded images before integration |

---

## 6. Phase Overview

```
PHASE 0  Foundation Repair & Environment Verification        (Weeks 1–2)
PHASE 1  Case Study Dataset Preparation                      (Weeks 2–3)
PHASE 2  Single Facade Reconstruction — Case Study           (Weeks 3–6)
PHASE 3  Pipeline Generalization                             (Weeks 6–9)
PHASE 4  Semantic Segmentation Integration                   (Weeks 7–10)
PHASE 5  SfM/MVS Depth Estimation Integration                (Weeks 8–12)
PHASE 6  Procedural Detail & Mesh Completion                 (Weeks 10–14)
PHASE 7  Validation, QA Agent & Metrics                      (Weeks 12–16)
```

Phases 4–7 can proceed in parallel after Phase 3 is complete.

---

## 7. Non-Negotiable Quality Gates

All quality gates are defined in `QUALITY_GATES.md`. No phase may begin until its prerequisite gates pass.

| Gate | Blocks | Description |
|------|--------|-------------|
| QG-01 | Phase 1 start | Coordinate round-trip error < 0.5m at target location |
| QG-02 | Phase 2 start | Case study facade dataset fully assembled and documented |
| QG-03 | Phase 2 end | Reconstructed mesh reprojects into source images with reprojection error < 5px |
| QG-04 | Phase 3 start | Phase 2 outputs are format-compatible with generalized pipeline schema |
| QG-05 | Phase 4 end | Segmentation model achieves IoU > 0.7 on held-out Tecate facade images |
| QG-06 | Phase 5 end | SfM produces sparse point cloud with > 500 points per facade |
| QG-07 | Phase 6 end | Procedural completion fills > 90% of detected missing elements |
| QG-08 | Phase 7 end | Full pipeline PSNR > 25 dB on held-out view synthesis test |

---

## 8. Deliverable Artifacts per Phase

| Phase | Deliverables |
|-------|-------------|
| 0 | `tests/unit/`, `tests/fixtures/`, environment verification report |
| 1 | `data/case_study/`, case study dataset package, QG-01/02 reports |
| 2 | `export/case_study/`, reconstructed mesh GLB, reprojection validation images |
| 3 | Refactored `src/reconstruction/`, generalized pipeline configuration schema |
| 4 | `src/segmentation/` module, trained/downloaded model weights, segmentation masks |
| 5 | `src/sfm/` module, COLMAP integration, per-facade point clouds |
| 6 | `src/procedural/` module, completed meshes with procedural detail |
| 7 | `src/qa/` module, automated metrics report, regression test suite |

---

## 9. Output Format Contract

All phases must produce outputs compatible with this coordinate contract (from `docs/GEOSPATIAL_MODEL.md`):

- **Spatial units**: meters, local Cartesian
- **Origin**: Parque Hidalgo (32.573229°N, -116.626536°W)
- **Axis convention**: X=East, Y=North, Z=Up
- **Coordinate functions**: `src/core_io/coords.py::gps_to_local` and `local_to_gps` — must not be modified without updating all consumers

All new file outputs must be documented in `docs/DATA_MODEL.md` with their schema before being written by code.

---

## 10. Agent Execution Philosophy

Every task in `TASK_BACKLOG.md` is written for an autonomous coding agent with no prior knowledge. Each task is self-contained: it references exact file paths, field names, expected data types, algorithmic steps, and validation procedures.

An agent receiving any single task from the backlog must be able to:
1. Identify what files to read
2. Identify what computation to perform
3. Identify what files to write
4. Validate the output
5. Report pass/fail

No task requires judgment beyond what is written. If a task requires judgment, it is decomposed into a discovery sub-task and a decision gate before the implementation task.
