# UNKNOWNS_AND_GAPS.md — Tecate Simulator: Unknowns, Gaps & Open Questions

> This document catalogues **verified unknowns** — things the code does not answer, data that is missing, and design decisions that are ambiguous.  
> Every item is labeled by severity: 🔴 Critical / 🟡 Important / 🟢 Minor.

---

## Category A: Coordinate System Gaps

### A-1 🔴 Terrain-Reconstruction Coordinate Alignment Is Undefined

**What**: The terrain GLBs in `models/tecate/glb/` were generated from INEGI data and exported via an external toolchain. The reconstruction pipeline uses a local Cartesian system centered at Parque Hidalgo. There is **no documented or implemented coordinate transform** that aligns the terrain mesh with the procedural building geometry.

**Evidence**: 
- `tecate.md` states "Coordinate system preserved from original GeoJSON source" but does not specify what that implies in 3D
- `blender_script.py` uses local coordinates directly as Blender world coordinates — terrain import procedure is not in this script
- No alignment matrix, offset, or scale factor is stored anywhere in the codebase

**Impact**: Without alignment, a Babylon.js or Three.js viewer cannot place the reconstructed buildings on the terrain surface. Buildings would float at Z=0 in an incorrect world position.

**Unknown**: What 3D space does the terrain GLB use? Meters? What origin? Is Z up or Y up?

---

### A-2 🟡 Z=0 Ground Plane vs Actual Terrain Elevation

**What**: All building geometry is placed at `Z = 0` (ground plane). Real Tecate has terrain relief — the city center is at ~540m ASL, and the surrounding hills (Cerro Cuchumá) reach ~1,600m.

**Evidence**: `blender_script.py` line 146: `z_base = 0.0` for all blocks.

**Impact**: On flat terrain, this is fine. But if the terrain mesh reflects actual elevation, buildings would need to be snapped to the terrain surface at the correct elevation.

**Unknown**: Is the terrain GLB normalized to Z=0 at city center, or does it use absolute elevation?

---

## Category B: Pipeline Gaps

### B-1 🔴 `TemporalVisualClassifier` Is Not Wired Into Pipeline

**What**: `src/temporal_filter/classifier.py` implements CV-based temporal classification of panorama images. It is never called in `prism_generator.py` or `main.py`.

**Evidence**: No `import` of `TemporalVisualClassifier` in `prism_generator.py`. Temporal selection is done via raw date comparison on `timeline`.

**Impact**: The system may accept low-quality or modern panoramas when better historical options exist at the same location. The MRF solver (`TemporalMRFSolver`) for graph-propagated label smoothing is also unused.

**Unknown**: Was this intentionally deprecated, or is it planned for future integration?

---

### B-2 🟡 `score_observation_candidate` Is Not Used

**What**: `UrbanBlockReconstructor.score_observation_candidate()` implements a multi-factor observation scoring function (alignment × distance × same-road bonus × visibility quality). It is never called.

**Evidence**: No call sites found in `prism_generator.py`. Current architecture uses direct API query at the facade midpoint + fallback neighbor resolution.

**Impact**: Facades may be assigned suboptimal panoramas when multiple candidates are available within range.

**Unknown**: This method references `obs["quality_score"]` which suggests a prior quality-scoring step that no longer exists.

---

### B-3 🟡 `stitch_facades_with_similarity` Is Not Used

**What**: `find_horizontal_overlap_offset` and `stitch_facades_with_similarity` implement NCC-based sequential image stitching. Neither is called in the current pipeline.

**Evidence**: Current pipeline uses `extract_rectified_facade_observation_texture` with the unified virtual group warping approach.

**Impact**: The stitching approach (which uses overlap detection) may produce better results for adjacent facades from the same panorama. The virtual group approach warps from a single image across all N segments simultaneously.

**Unknown**: Was the stitching approach superseded by the virtual group approach, or is it an alternative mode?

---

### B-4 🟡 `accepted_panos` Parameter Is Unused

**What**: `UrbanBlockReconstructor.__init__` accepts `accepted_panos: list[dict] = None` but references to it are not found in any method.

**Evidence**: Parameter defined at line 21 of `prism_generator.py`. No usage in the class body.

**Impact**: This parameter appears to be a placeholder for pre-filtering panoramas before reconstruction (potentially using the `TemporalMRFSolver` output). Currently, all panoramas returned by the API are accepted.

---

### B-5 🟡 `intercepted_panos` Network Interception Is Inactive

**What**: `GoogleStreetViewScraper.intercepted_panos = {}` is initialized but no `page.on("response", ...)` listener is registered. Network response interception is not active.

**Unknown**: Was network interception planned for capturing tile metadata or additional pano data from the Chromium session? Is it safe to rely on the HTTP metadata API alone?

---

### B-6 🟢 `stitching_cache.json` Is Empty

**What**: `data/stitching_cache.json` contains `{}`. The stitching cache was designed to store NCC shift offsets between adjacent facade screenshots to avoid recomputation.

**Evidence**: `save_stitching_cache` method exists and is called in `graceful_shutdown`. The file is created but never populated with shift values.

**Impact**: No functional impact in the current pipeline (which doesn't use the stitching approach). But if the stitching approach is ever revived, this cache would need to be populated.

---

## Category C: Data Quality Gaps

### C-1 🔴 ~19% of Panoramas Are Post-2009

**What**: Of 3,906 panoramas, ~740 are dated 2015–2025. These represent locations where Google had no 2009 coverage. These facades receive modern imagery in the "historical" reconstruction.

**Evidence**: Date distribution from `panoramas_cache.json`:
```
2015-12: 2 | 2016-02: 39 | 2017-07: 45 | 2017-08: 7 | 2017-10: 80
2021-09: 53 | 2022-05: 3 | 2022-09: 260 | 2022-10: 167 | 2025-08: 62
```

**Impact**: Facades textured with 2022 panoramas will show modern storefronts, cars, signs, etc. — breaking temporal coherence.

**Unknown**: Is there a per-facade flag in the output that marks these as "modern"? The provenance JSON contains `source_date` — it is present but not surfaced in the 3D export.

---

### C-2 🟡 Building Heights Are Heuristic, Unvalidated

**What**: All building heights are computed by `estimate_facade_segment_height()` using sky/roofline detection. Range: 3.2–11m. No ground-truth validation dataset exists.

**Evidence**: `metadata.json` does not include height estimates per-block. `blocks_cache.json` stores computed `height_meters` but these are derived values.

**Impact**: Incorrect heights affect urban silhouette accuracy.

**Unknown**: What is the expected height distribution for Tecate downtown buildings? Typical one-story commercial buildings in this region are 3–5m; two-story residential 6–8m.

---

### C-3 🟡 Camera Alignment Quality Not Summarized

**What**: Each facade cache entry has `camera_alignment_diagnostics.dot_product` and `is_correct_side`. These are stored but never aggregated into a quality report.

**Evidence**: Fields present in `facades_cache.json` sample.

**Impact**: Facades with `is_correct_side = False` (camera facing away from facade) would produce incorrect textures. Their proportion is unknown.

**Unknown**: How many facades have `is_correct_side = False`? What percentage have `dot_product > -0.3` (near-oblique views)?

---

### C-4 🟢 `altitude` Is Null for Most Panoramas

**What**: The `altitude` field in `panoramas_cache.json` is `null` for all sampled records.

**Evidence**: Panorama sample shows `"altitude": null`.

**Impact**: If altitude were used for terrain snapping, this null value would need handling. Currently altitude is unused in the pipeline.

---

## Category D: Architecture Gaps

### D-1 🟡 No Test Suite

**What**: `pytest` is in `requirements.txt` but no test files (`.py` files beginning with `test_` or in a `tests/` directory) were found.

**Impact**: No automated verification of coordinate transforms, polygon algorithms, or API parsing. Changes to core functions carry high regression risk.

---

### D-2 🟡 Absolute Paths in `reconstruction_export.json`

**What**: `facade_textures` values and `texture_atlas_path` in `reconstruction_export.json` are **absolute filesystem paths**:
```
"/Users/hakkindavid/Documents/GitHub/tecate-simulator/export/textures/..."
```

**Evidence**: From `reconstruction_export.json` sample.

**Impact**: This file is non-portable. Moving the project directory or sharing the file with another machine will cause Blender to fail to load textures. A `reconstruction_export_win.json` variant with Windows paths is generated for the WSL case, but this further fragments the portability issue.

**Root cause**: `os.path.abspath()` is used throughout `prism_generator.py` when building texture paths.

---

### D-3 🟡 OSM Graph Has 82k Nodes vs Structural Graph's 1,655 Nodes

**What**: The OSM cache graph has 82,872 nodes and 87,177 edges (from `reconstruction_export.json`). The structural graph (from `ArchivalDataMigrator`) has only 1,655 nodes and 1,814 edges.

**Evidence**: Both figures confirmed by direct data file inspection.

**Impact**: The reconstruction uses the full 82k-node graph for block cycle extraction and road distance calculations. The 1,655-node structural graph is used only for the `pano_to_edge` adjacency lookup. These two graphs may not be spatially aligned or share the same edge ID namespace — the `e_0`...`e_N` IDs in structural graph may not match OSM graph edge IDs.

**Unknown**: Are the `road_edge_id` values stored in `facades_cache` from the OSM graph or the structural graph? Are they consistent across pipeline runs?

---

### D-4 🟡 `py360convert` Is in requirements.txt but Not Used

**What**: `py360convert>=1.0.4` is listed in `requirements.txt` but no active call to this library was found in the codebase.

**Unknown**: Was this planned for equirectangular-to-perspective conversion of full panorama images (as opposed to the current perspective screenshot approach)? Is it used in a part of the codebase not yet discovered?

---

### D-5 🟢 `pano_yaw` and `projection_yaw` Are Both Stored

**What**: `panoramas_cache.json` stores both `projection_yaw` and `pano_yaw` with identical values:
```python
"pano_yaw": meta.get("projection_yaw"),
"projection_yaw": meta.get("projection_yaw"),
```

**Evidence**: Line 1729 of `prism_generator.py`.

**Impact**: Redundancy only — both are null in many records. `pano_yaw` appears to be a legacy field alias.

---

### D-6 🟢 Blender Camera Uses Non-Standard Coordinate System

**What**: The Blender scene uses world coordinates where local X=East, Y=North, Z=Up. However, Blender's default coordinate system is X=Right, Y=Forward, Z=Up. The pipeline works because it directly sets vertex coordinates — but the camera rotation `(48°, 0, 0)` is specified in Blender's Euler XYZ convention which may not intuitively correspond to a "48° pitch from horizontal" in the geographic sense.

**Unknown**: Has the camera framing been validated to produce the expected bird's-eye city view?

---

## Category E: External Dependencies & Fragility

### E-1 🔴 Pipeline Relies on Unauthenticated Google APIs

**What**: The entire metadata acquisition pipeline depends on:
- `maps.googleapis.com/maps/api/js/GeoPhotoService.SingleImageSearch` (unauthenticated)
- `www.google.com/maps/photometa/v1` (unauthenticated)
- Google Street View rendered via Playwright (UI automation)

**Risk**: Google may change their proto-URL format, add bot detection, require authentication, or restructure their response schemas. Any of these would break metadata acquisition.

**Evidence**: The proto-URL encoding is a reverse-engineered format, not a documented API.

**Mitigation**: Caches mean the pipeline can continue `--skip-scraper` once data is acquired.

---

### E-2 🟡 Playwright Requires Specific Chromium Version

**What**: `playwright install chromium` installs a pinned Chromium version. The CSS selectors and JS injection used to hide UI overlays are tied to Google Maps' current DOM structure.

**Risk**: Google Maps DOM changes may cause UI elements to remain visible in screenshots (watermarks, minimap) — contaminating textures.

---

### E-3 🟢 Blender Version Compatibility

**What**: `blender_script.py` uses Blender Python API (`bpy`). The script references `mat.blend_method` and `mat.shadow_method` as `try/except AttributeError` — acknowledging Blender version differences.

**Evidence**: Lines 268–274 of `blender_script.py`.

**Tested version**: Not documented. References to "Blender 5.1" in Windows path suggest Blender 5.x is the target.

---

## Category F: Research Notes Reference

`research.md` (27KB) exists in the repository root. It was not fully analyzed but appears to contain extended project research, references, and notes. It may contain additional context for some of the unknowns listed above. A dedicated review of this file is recommended.

---

## Summary Table

| ID | Category | Severity | Item |
|----|----------|----------|------|
| A-1 | Coordinates | 🔴 | Terrain-reconstruction alignment undefined |
| A-2 | Coordinates | 🟡 | Building Z=0 vs actual terrain elevation |
| B-1 | Pipeline | 🔴 | TemporalVisualClassifier not wired |
| B-2 | Pipeline | 🟡 | score_observation_candidate unused |
| B-3 | Pipeline | 🟡 | stitch_facades_with_similarity unused |
| B-4 | Pipeline | 🟡 | accepted_panos parameter unused |
| B-5 | Pipeline | 🟡 | Network interception inactive |
| B-6 | Pipeline | 🟢 | Stitching cache empty |
| C-1 | Data | 🔴 | ~19% panoramas are post-2009 |
| C-2 | Data | 🟡 | Heights unvalidated |
| C-3 | Data | 🟡 | Camera alignment not summarized |
| C-4 | Data | 🟢 | Altitude null |
| D-1 | Architecture | 🟡 | No test suite |
| D-2 | Architecture | 🟡 | Absolute paths in export JSON |
| D-3 | Architecture | 🟡 | OSM graph vs structural graph ID mismatch risk |
| D-4 | Architecture | 🟡 | py360convert unused |
| D-5 | Architecture | 🟢 | pano_yaw/projection_yaw redundancy |
| D-6 | Architecture | 🟢 | Blender camera convention unclear |
| E-1 | External | 🔴 | Unauthenticated Google API dependency |
| E-2 | External | 🟡 | Playwright/DOM fragility |
| E-3 | External | 🟢 | Blender version compatibility |
