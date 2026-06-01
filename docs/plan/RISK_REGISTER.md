# RISK_REGISTER.md
## Tecate 2009 — Implementation Risk Register

**Assessment date**: 2026-06-01  
**Probability scale**: LOW (<20%), MEDIUM (20–50%), HIGH (>50%)  
**Impact scale**: LOW (rework ≤1 day), MEDIUM (rework 1–5 days), HIGH (rework >5 days or blocks milestone)

---

## RISK-01 — Google Photometa API Format Change

**Category**: External Dependency  
**Probability**: MEDIUM  
**Impact**: HIGH  

**Description**: The metadata acquisition pipeline depends on an unauthenticated, reverse-engineered Google API endpoint (`GeoPhotoService.SingleImageSearch` + `photometa/v1`). Google may change the proto-URL format, response schema, or add bot detection at any time. All current cache data was acquired using this API; future scraping depends on it remaining stable.

**Detection criteria**: API returns HTTP 4xx or response body fails `parse_photometa_response` parsing.

**Mitigation**:
1. Record API response fixtures now (P00-T004) so tests work offline
2. Treat `browser_scraper.py` as an isolated adapter layer — new API formats only require changes here
3. Do not rely on live scraping for Phase 1–2 case study work (use existing cached data)

**Contingency if triggered**: 
- Switch to official Street View Static API (`sv_downloader.py`) with API key — requires `GOOGLE_STREETVIEW_API_KEY` environment variable
- Alternative: Use Mapillary API (open, authenticated) as a secondary source

**Tasks affected**: P01-T010, Phase 4–5 city-scale expansion

---

## RISK-02 — SfM Baseline Too Short for Street View Images (Near-Coplanar)

**Category**: Geometric Feasibility  
**Probability**: HIGH  
**Impact**: HIGH  

**Description**: Google Street View cameras drive along a street and capture images nearly parallel to the facade. The triangulation baseline (distance between consecutive camera positions) is typically 2–5m, while the camera-to-facade distance is 8–12m. This produces a small baseline-to-depth ratio (~0.2–0.5), which leads to high uncertainty in depth estimation using classical SfM triangulation.

**Detection criteria**: COLMAP produces < 100 3D points OR point cloud RMS depth error > 1.5m when evaluated against block height estimate.

**Mitigation**:
1. P05-T021 is a mandatory feasibility test before SfM integration is built
2. If baseline-to-depth ratio < 0.3: switch to monocular depth estimation (MiDaS or DPT) as primary depth source
3. Use block polygon height estimate (8.37m from existing pipeline) as absolute scale reference for monocular depth

**Contingency if triggered**:
- Implement `src/sfm/monocular_depth.py` using MiDaS PyTorch model as fallback
- MiDaS produces relative depth map → scale using known building height → absolute depth map
- Document in `SFM_FEASIBILITY_REPORT.md` and adjust Phase 5 scope

**Tasks affected**: P05-T021, P05-T022

---

## RISK-03 — Semantic Segmentation Model Fails on 2009 Tecate Imagery

**Category**: ML Model Generalization  
**Probability**: MEDIUM  
**Impact**: MEDIUM  

**Description**: Pre-2010 Google Street View imagery has lower resolution, different color rendition, and may include JPEG compression artifacts. Models trained on modern facade datasets may not generalize well. Additionally, Tecate has a distinct North Mexican architectural vernacular (single-story commercial facades with rolled security gates, hand-painted signage) that may differ from European or North American facade datasets.

**Detection criteria**: Segmentation IoU on Tecate test images < 0.60.

**Mitigation**:
1. P04-T019 explicitly evaluates models on held-out Tecate imagery before selection
2. Prepare ≥10 manually labeled test images of Tecate facades during model selection
3. Prefer models that label "background" broadly rather than penalizing non-European styles

**Contingency if triggered**:
- Proceed with IoU = 0.60 (reduced threshold) and document limitation
- Mark procedural detail as "inferred from geometry" rather than "inferred from segmentation"
- Consider fine-tuning on 50–100 manually labeled Tecate facade images

**Tasks affected**: P04-T019, P04-T020, QG-05

---

## RISK-04 — Terrain Coordinate Frame Is Incompatible with Local Cartesian

**Category**: Data Integration  
**Probability**: HIGH  
**Impact**: HIGH  

**Description**: The terrain GLB files in `models/tecate/glb/` were generated from INEGI data through an external pipeline not documented in this repository. The 3D coordinate system, scale, and origin of these models are unknown. The reconstruction pipeline uses a local Cartesian system centered at Parque Hidalgo. If the terrain model uses a different coordinate convention (e.g., geographic lon/lat as XY, Z=elevation in a different datum), buildings cannot be placed on terrain without a transform.

**Detection criteria**: Importing both terrain GLB and procedurally generated buildings into a single Blender scene results in buildings appearing at wrong position or scale relative to terrain.

**Mitigation**:
1. Create a dedicated alignment investigation task (not in current backlog — add if Phase 7 requires terrain integration)
2. Identify 3 geographically known points in the terrain model (e.g., road intersection visible in model) and compute the transform from terrain model space to local Cartesian space
3. Document result in `docs/TERRAIN_ALIGNMENT.md`

**Contingency if triggered**: 
- Phase 2–7 reconstruction targets only the building geometry (no terrain integration)
- Terrain integration is deferred to a post-MVP phase
- Deliver `target_block.glb` as standalone geometry (at Z=0) without terrain attachment

**Tasks affected**: P02-T014 (GLB assembly), QG-08 (if terrain is in acceptance criteria)

---

## RISK-05 — `facade_midpoint_local` Is Null for More Than Target Block

**Category**: Data Quality  
**Probability**: MEDIUM  
**Impact**: MEDIUM  

**Description**: Inspection confirmed that `facade_midpoint_local` is null for all 193 facades of the case study block. This may affect a wider set of blocks if the null values result from an older pipeline version that didn't populate this field.

**Detection criteria**: `python3 -c "import json; d=json.load(open('data/facades_cache.json')); null_count=sum(1 for v in d.values() if v.get('facade_midpoint_local') is None); print(null_count)"` — if > 193, more blocks are affected.

**Mitigation**:
1. P01-T008 recomputes midpoints for the target block
2. A global recomputation script should be created if the count exceeds 500

**Contingency if triggered**: Run global midpoint recomputation before Phase 3 (pipeline generalization)

**Tasks affected**: P01-T008, P03 (generalized pipeline)

---

## RISK-06 — Blender Path Configuration Failure

**Category**: Infrastructure  
**Probability**: MEDIUM  
**Impact**: LOW  

**Description**: `src/main.py` uses platform-specific Blender paths. On a new machine or if Blender is installed in a non-standard location, the subprocess invocation fails silently or with a non-descriptive error.

**Detection criteria**: `subprocess.run([blender_path, ...])` returns non-zero exit code or `FileNotFoundError`.

**Mitigation**:
1. P00-T006 documents the verified Blender path
2. P02-T014 script validates Blender path before invoking

**Contingency if triggered**: Use `shutil.which("blender")` to auto-detect; if not found, provide clear error message with install instructions.

**Tasks affected**: P02-T014

---

## RISK-07 — Playwright DOM Structure Changes

**Category**: External Dependency  
**Probability**: LOW  
**Impact**: MEDIUM  

**Description**: The CSS selectors used to hide Google Maps UI overlays in screenshots are tied to Google's current DOM structure. If Google updates their Maps frontend, overlays (watermarks, minimap, street labels) may appear in captured screenshots, contaminating facade textures.

**Detection criteria**: Screenshots contain visible Google Maps watermark or blue compass overlay in bottom-right corner.

**Mitigation**:
1. Screenshots for the case study target are already captured
2. Visual test (VV-01) checks for UI element contamination

**Contingency if triggered**: Update CSS hide rules in `browser_scraper.py`; re-capture affected images.

**Tasks affected**: P01-T010 (future capture sessions)

---

## RISK-08 — `shrink_polygon` Produces Degenerate Result for Small Blocks

**Category**: Algorithmic  
**Probability**: LOW  
**Impact**: LOW  

**Description**: The polygon inward offset (shrink by 6m) may produce degenerate results (< 4 vertices or self-intersecting polygon) for small blocks with dimension < 12m in any direction.

**Detection criteria**: `len(shrunk_poly) < 4` OR Shoelace area of shrunk polygon is negative OR polygon self-intersects.

**Mitigation**: P01-T008 validates the shrunk polygon before computing midpoints.

**Contingency**: If degenerate: use raw polygon with d=0 (no shrink) and log warning.

**Tasks affected**: P01-T008

---

## RISK-09 — PSNR Threshold (25 dB) May Be Unachievable Without Neural Rendering

**Category**: Quality Metrics  
**Probability**: MEDIUM  
**Impact**: MEDIUM  

**Description**: The research.md specifies PSNR > 30 dB as a high-fidelity threshold (citing Aryal et al. for Gaussian Splatting). QG-08 uses 25 dB. However, the current pipeline uses perspective-warped Street View screenshots — not neural rendering. PSNR of a warped texture compared to the source image may be lower than 25 dB due to geometric warping artifacts, sky masking holes, and perspective distortion.

**Detection criteria**: `psnr_db < 25.0` in `qa_report.json`.

**Mitigation**:
1. Measure baseline PSNR of existing pipeline (Phase 2) before setting the 25 dB target as a hard requirement
2. If baseline is 20–25 dB: consider whether the comparison method (cropped region vs full image) needs adjustment
3. PSNR is measured against the facade region only (masked ROI) — not the full 1280×720 image

**Contingency if triggered**:
- Lower QG-08 threshold to 20 dB for the prism-extrusion baseline
- Implement NeRF or Gaussian Splatting rendering for improved PSNR in a post-MVP phase
- Document limitation in `qa_report.json.notes`

**Tasks affected**: P07-T023, QG-08

---

## RISK-10 — Target Facade Is a Single Long Wall (No Segmentable Elements)

**Category**: Domain  
**Probability**: MEDIUM  
**Impact**: LOW  

**Description**: The Caseta Telefónica is a telephone exchange building, which may be a simple concrete wall with no windows, balconies, or ornamental features. The segmentation and procedural detail phases assume detectable architectural elements exist.

**Detection criteria**: Segmentation mask contains < 5% pixels labeled as window, door, or balcony.

**Mitigation**:
1. Segmentation still provides useful wall/sky/vegetation labeling even without window elements
2. Procedural detail agent falls back to "plain wall" completion if no elements detected
3. The validation case study may need to be supplemented with a secondary target (e.g., a residential building on Av. Juárez) if La Panza has no elements

**Contingency if triggered**: Add a secondary case study target for the procedural detail validation; keep La Panza as the primary geometric reconstruction target.

**Tasks affected**: P04-T020, Phase 6

---

## RISK-11 — Insufficient Image Count for Dense MVS

**Category**: Data Availability  
**Probability**: HIGH  
**Impact**: MEDIUM  

**Description**: Google Street View typically provides 1–3 images per facade location. Dense MVS (OpenMVS, PMVS) requires ≥3 images with significant overlap. For a single facade face, Street View may only provide 1 or 2 frontal views.

**Detection criteria**: `len(target_panoramas.json.panoramas)` < 3.

**Mitigation**:
1. P01-T009 counts available images before Phase 5 begins
2. Phase 5 explicitly documents the monocular fallback path (MiDaS)
3. Risk-02 already covers the geometric aspect of this problem

**Contingency**: Monocular depth estimation as primary approach if < 3 images.

**Tasks affected**: P05-T021, P05-T022

---

## RISK-12 — Cache File Corruption During Concurrent Writes

**Category**: Concurrency  
**Probability**: LOW  
**Impact**: HIGH  

**Description**: The existing pipeline uses `threading.Lock` to protect shared caches. If `graceful_shutdown` is triggered during a parallel processing run, caches may be partially written (Python's `json.dump` is not atomic).

**Detection criteria**: `json.load` raises `JSONDecodeError` on any cache file.

**Mitigation**:
1. All new code that modifies `data/facades_cache.json` (P01-T008) must use atomic write (write to temp file, then `os.replace`)
2. Add `try/except JSONDecodeError` with backup-and-reinitialize logic

**Tasks affected**: P01-T008, P03 refactoring

---

## Risk Summary Matrix

| Risk ID | Probability | Impact | Priority | Phase |
|---------|------------|--------|----------|-------|
| RISK-02 | HIGH | HIGH | 🔴 CRITICAL | P05 |
| RISK-04 | HIGH | HIGH | 🔴 CRITICAL | P02, P07 |
| RISK-11 | HIGH | MEDIUM | 🟡 HIGH | P05 |
| RISK-01 | MEDIUM | HIGH | 🟡 HIGH | P01 |
| RISK-03 | MEDIUM | MEDIUM | 🟡 HIGH | P04 |
| RISK-05 | MEDIUM | MEDIUM | 🟡 HIGH | P01 |
| RISK-06 | MEDIUM | LOW | 🟢 MEDIUM | P02 |
| RISK-09 | MEDIUM | MEDIUM | 🟡 HIGH | P07 |
| RISK-10 | MEDIUM | LOW | 🟢 MEDIUM | P04, P06 |
| RISK-12 | LOW | HIGH | 🟡 HIGH | P01, P03 |
| RISK-07 | LOW | MEDIUM | 🟢 MEDIUM | P01 |
| RISK-08 | LOW | LOW | ⚪ LOW | P01 |
