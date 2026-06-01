# RECONSTRUCTION_READINESS.md — Tecate Simulator: Reconstruction Readiness Assessment

> **Assessment methodology**: All claims based on direct code and data file reading. No inferences beyond what was explicitly observed.

---

## 1. Executive Summary

| Dimension | Status | Evidence |
|-----------|--------|---------|
| OSM road graph | ✅ Complete | `tecate_osm_cache.json` — 82,872 nodes, 87,177 edges |
| Block polygon extraction | ✅ Complete | `blocks_cache.json` — 4,239 blocks |
| Panorama metadata | ✅ Substantial (3,906 records) | `panoramas_cache.json` — 80% from 2009 era |
| Facade observations | ✅ Substantial (22,289 records) | `facades_cache.json` |
| Image capture (screenshots) | ✅ In progress (partial) | `data/screenshots/pano/` |
| Texture generation | ✅ Near-complete | 99.84% of 15,532 facades textured |
| 3D Scene document | ✅ Available | `reconstruction_export.json` — 159 blocks |
| Blender 3D model | ✅ Available | `tecate_reconstruction.blend1` (autosave) |
| glTF export | ✅ Available | `geometry.gltf` + `geometry.bin` |
| Terrain base model | ✅ Available | 3 GLB variants in `models/tecate/glb/` |
| Terrain-reconstruction alignment | ❌ Missing | No documented coordinate frame bridge |
| Temporal accuracy | ⚠️ Partial | ~80% 2009 panos, but some 2015–2025 leakage |
| Building height accuracy | ⚠️ Estimated | Vision-estimated from roofline, not ground truth |
| Complete city coverage | ⚠️ Partial | 159/4,239 blocks reconstructed (3.75%) |

---

## 2. What Is Operational

### 2.1 End-to-End Pipeline

The full pipeline from OSM graph → glTF is **functional and has produced output**:
- `reconstruction_export.json` exists with 159 reconstructed blocks
- `metadata.json` shows 99.84% facade coverage within those 159 blocks
- `geometry.gltf` exists as the final 3D export

### 2.2 Incremental Architecture

The pipeline is **crash-resilient and incrementally resumable**. All intermediate state is persisted to JSON caches. Re-running the pipeline will:
- Skip already-cached blocks
- Skip already-downloaded screenshots
- Skip already-generated textures

### 2.3 Temporal Epoch Selection

The pipeline correctly identifies and selects **historical panoramas from the Google Street View timeline**. The date distribution confirms that ~79.8% of acquired panoramas are from 2009 (2,468 from 2009-09 alone) and ~5.6% from 2008-12.

### 2.4 Terrain Models Available

Three GLB variants exist and are ready for use:
- `tecate (detallado sin edificios ni vegetación).glb` (86.2 MB) — clean terrain base for procedural building overlay

### 2.5 Blender Integration

The `.blend` file is populated and the embedded `Viewport_FOV_Cull_Utility.py` script enables interactive real-time culling for performance management.

---

## 3. Current Limitations

### 3.1 City Coverage — 3.75% of Blocks Reconstructed

Of 4,239 cached city blocks, only **159 are present in the current reconstruction export**. The remaining ~4,080 blocks are captured in `blocks_cache.json` but not yet processed through the full texture pipeline.

**Cause**: The `run.sh` loop processes blocks incrementally on each run. The pipeline sorts blocks by proximity to Parque Hidalgo, so the 159 blocks represent the city center.

**Not a data gap** — block polygons exist for all 4,239; the bottleneck is screenshot acquisition (network-bound) and texture processing (compute-bound).

### 3.2 Temporal Leakage (~20% Non-2009 Panos)

Approximately 20% of panoramas in the cache are from 2015–2025. This occurs because:
1. Not every facade position has a 2009 panorama in Google's coverage
2. The `timeline` list returned by the API is not always exhaustive
3. The chronology selection picks the "oldest" pano — but if Google only has 2017+ coverage at a location, the 2017 pano is used

**Evidence from provenance**: First provenance entry shows `source_date: "2017-07"` for a Parque Hidalgo facade.

**No automated fallback** currently exists to flag or exclude modern panos from the reconstruction.

### 3.3 Terrain-Reconstruction Coordinate Gap

**Critical unresolved issue**: There is no documented or implemented alignment between:
- The pipeline's **local Cartesian coordinate system** (origin = Parque Hidalgo GPS)
- The terrain GLB models' **INEGI GeoJSON coordinate system**

Both systems use WGS84 as the underlying datum, but:
- The terrain GLBs contain absolute 3D geometry in an unknown 3D scale and offset
- The reconstruction uses meters relative to an origin point
- Blender imports each independently with no documented transform to align them

Without this alignment, the procedural building geometry cannot be correctly overlaid on the terrain mesh in a viewer or engine.

### 3.4 Building Heights Are Vision-Estimated

Heights are computed by `estimate_facade_segment_height()` — a heuristic that:
- Detects roofline from sky/building color boundary per pixel column
- Solves inverse perspective depth to estimate height
- Clips to `[3.2m, 6.5m]` per-column, then doubles

This produces values in the 7–11m range. These are **estimates**, not ground truth (no LiDAR or survey data is used).

**Validation needed**: The resulting heights have not been verified against any ground-truth building height dataset (e.g., INEGI building footprints, OpenBuildings, or field survey).

### 3.5 Sky Masking Is Heuristic

The `mask_sky_in_panorama` method uses:
- Local sky color sample from top 15 pixels
- Color distance threshold: `> 35.0` (L2 in RGB space)
- Gradient threshold: `> 15.0`

This works well for clear-sky conditions but may fail for:
- Overcast skies (sky color similar to concrete/stucco)
- Tall buildings occluding the sky at roofline
- Trees or vegetation in foreground
- Night captures (rare but possible in SV)

No semantic segmentation is used.

### 3.6 No Texture Quality Filtering

The current pipeline accepts any successfully warped texture without quality checks:
- Blurry images (low Laplacian variance) are accepted
- Occluded facades (cars, trees) are accepted
- Non-frontal views are partially mitigated by `alignment > 0.05` in scoring, but low-quality textures can still pass

The `TemporalVisualClassifier` (which computes Laplacian variance and ORB keypoints) is not integrated into the acceptance pipeline.

### 3.7 No Depth or Normals

The reconstruction produces:
- Flat vertical facade quads (no surface relief)
- No normal maps
- No depth maps or photogrammetric reconstruction
- Buildings are extruded flat prisms — no window recesses, balconies, or facade detail

### 3.8 No Tests

`pytest` is in `requirements.txt` but no test files were found. The pipeline is untested programmatically — all validation is visual/manual inspection of the diagnostic map and output textures.

---

## 4. Data Quality Assessment

### 4.1 Panorama Date Quality

```
Total panoramas: 3,906
Pre-2010 (target epoch): ~3,166 (81%)
  - 2009-09: 2,468 (63%)
  - 2009-02:   327  (8%)
  - 2008-12:   217  (6%)
  - 2009-08:   141  (4%)
  - Other 2009:  13  (0.3%)
Post-2010 (leakage): ~740 (19%)
```

### 4.2 Facade Coverage Quality

```
Total facades in export: 15,532
Textured: 15,507 (99.84%)
Fallback: 25 (0.16%)
```

Coverage is extremely high within the 159 processed blocks. The near-100% coverage is partly explained by the `resolve_almost_adjacent_fallback_segments` function which propagates adjacent pano IDs to gap segments (within 2 positions).

### 4.3 Camera Alignment Quality

Each facade record stores `camera_alignment_diagnostics.dot_product` and `is_correct_side`. These were computed but their distribution is not summarized in any report. A future analysis should filter facades where `is_correct_side = false` or `dot_product > -0.5` (near-oblique captures).

---

## 5. Readiness for Next Phases

### For Wider City Coverage
- **Ready**: Pipeline is operational — just needs more `run.sh` iterations
- **Bottleneck**: Screenshot acquisition rate (~1–3 per second with Playwright)
- **Scale**: 4,239 blocks × ~6 facades/block ≈ 25,000 screenshots needed total

### For Temporal Accuracy Improvement
- **Ready**: `TemporalVisualClassifier` and `TemporalMRFSolver` classes exist
- **Gap**: Not wired into pipeline — integration needed

### For Terrain Integration
- **Gap**: Coordinate alignment between terrain GLB and local reconstruction space is undefined
- **Need**: Either transform terrain to local Cartesian, or transform local Cartesian to match terrain's 3D space

### For Rendering/Engine Integration
- **Ready**: `geometry.gltf` exists with correct texture references
- **Gap**: Terrain-building alignment (see above)
- **Need**: Runtime terrain streaming solution (terrain GLBs at 86–95 MB are large for real-time streaming)
