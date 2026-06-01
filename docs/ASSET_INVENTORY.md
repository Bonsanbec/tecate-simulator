# ASSET_INVENTORY.md — Tecate Simulator: Complete Asset Inventory

---

## 1. Terrain Models (Pre-Existing, External Source)

Located at `models/tecate/`

These are **externally authored assets** generated from INEGI data and Sketchup/terrain tooling. They are **not produced by the Python pipeline** and are treated as a stable foundation.

### GLB Format (`models/tecate/glb/`)

| File | Size | Description |
|------|------|-------------|
| `tecate (detallado con edificios).glb` | 95.5 MB | Detailed terrain with buildings |
| `tecate (detallado sin edificios).glb` | 88.7 MB | Detailed terrain without buildings, with vegetation |
| `tecate (detallado sin edificios ni vegetación).glb` | 86.2 MB | Bare terrain only (buildings AND vegetation removed) |

### Babylon.js Format (`models/tecate/babylon/`)

| File | Size | Description |
|------|------|-------------|
| `tecate (detallado con edificios).babylon` | 325.2 MB | Detailed with buildings (Babylon.js scene format) |
| `tecate (detallado sin edificios).babylon` | 281.7 MB | Without buildings (Babylon.js) |
| `tecate (detallado sin edificios ni vegetación).babylon` | 272.7 MB | Bare terrain (Babylon.js) |

**Notes**:
- Three variants allow selective layering: terrain base, vegetation, and procedural reconstruction on top.
- The "detallado sin edificios ni vegetación" variant is the cleanest base for overlaying the pipeline's reconstructed building geometry.
- Babylon format files are ~3.4× larger than GLB due to JSON encoding overhead.
- From `tecate.md`: one polygon vertex was extended to include Cerro Cuchumá (Donohue Mountain) in the terrain.

---

## 2. Reference Geospatial Data

Located at `reference/`

| File | Size | Description |
|------|------|-------------|
| `tecate-polygon.json` | ~varies | INEGI municipal boundary polygon (GeoJSON format) |

**Schema**: GeoJSON `FeatureCollection` with `Polygon` or `MultiPolygon` geometry type.  
**Usage**: Municipal boundary filter — blocks outside this polygon are excluded from reconstruction.  
**Provenance**: INEGI (National Institute of Statistics and Geography, Mexico).  
**Note**: The corresponding copy in `models/tecate/` has one vertex modified to include Cerro Cuchumá.

---

## 3. Cache Data Files

Located at `data/`

| File | Size | Records | Description |
|------|------|---------|-------------|
| `tecate_osm_cache.json` | 26.1 MB | ~82k nodes, ~87k edges | OSM road network |
| `blocks_cache.json` | 26.2 MB | 4,239 blocks | Block polygons + geometry |
| `facades_cache.json` | 22.1 MB | 22,289 facades | Facade observations |
| `panoramas_cache.json` | 1.6 MB | 3,906 panoramas | Pano metadata |
| `stitching_cache.json` | 2 bytes | 0 entries | NCC shift cache (empty) |

---

## 4. Structural Graph Data

Located at `data/structural_graph/`

| File | Size | Description |
|------|------|-------------|
| `road_graph.json` | 672 KB | Processed flat road graph (1,655 nodes, 1,814 edges) |
| `intersections.json` | 373 KB | Intersection registry |
| `adjacency.json` | varies | Edge-to-panorama adjacency index (if present) |

---

## 5. Pipeline Output Exports

Located at `export/`

### Core Scene Documents

| File | Size | Description |
|------|------|-------------|
| `reconstruction_export.json` | 37.0 MB | Full scene document (road graph + 159 blocks) — primary Blender input |
| `reconstruction_export_win.json` | 38.0 MB | Windows path-translated version (for WSL→Windows Blender) |
| `metadata.json` | 9.0 MB | Coverage statistics + 15,507 provenance entries |

### 3D Geometry

| File | Size | Description |
|------|------|-------------|
| `geometry.gltf` | varies | glTF scene file (GLTF_SEPARATE format, references external textures) |
| `geometry.bin` | 2.4 MB | Binary geometry buffer (vertices, faces, UVs) |

### Fallback Texture

| File | Size | Description |
|------|------|-------------|
| `textures/transparent_facade.png` | tiny | 512×512 fully transparent RGBA (used for untextured facades) |

### Per-Block Virtual Facade Textures

Located at `export/textures/`

**Naming**: `{block_id}_virtual_{cardinal}_{group_idx}.png`

| Attribute | Value |
|-----------|-------|
| Format | PNG, RGBA |
| Width | 512 × K × 2 pixels (K = number of collinear segments in group) |
| Height | 512 pixels |
| Count | ~hundreds (one per contiguous facade group per block) |
| Origin | Perspective-warped, sky-masked Street View screenshots |

**Sample file**: `block_lat_32.56577_lon_-116.62657_virtual_east_32.png`

---

## 6. Debug and Diagnostic Assets

Located at `export/debug/`

| File | Size | Description |
|------|------|-------------|
| `global_observation_map.png` | varies | Spatial coverage visualization (color-coded by status) |
| `reconstruction_diagnostics.json` | 6.7 MB | Per-facade: midpoint, normal, status, road_distance |

### Diagnostic Map Color Legend (from `coverage.py`)

| Status | Color | Meaning |
|--------|-------|---------|
| `textured` | green | Facade successfully texturized with SV imagery |
| `fallback` | red | No matching panorama found — transparent fallback used |
| `cached` | blue | Resumed from existing cache — not re-processed |

The diagnostic PNG map is a 2D top-down view of all facade midpoints with colored status dots, overlaid on the road graph.

---

## 7. Screenshots (Raw Captured Images)

Located at `data/screenshots/`

| Subdirectory | Content |
|-------------|---------|
| `data/screenshots/pano/` | Per-panorama screenshots: `{pano_id}_yaw_{heading:.2f}.png` (1280×720 RGB) |
| `data/screenshots/facades/` | Per-facade debug screenshots: `{slice_id}.png` |

These are **intermediate working assets** — the raw Playwright captures before sky-masking and warping.

**Storage note**: This directory may be very large depending on pipeline progress. Each screenshot is ~300KB–800KB.

---

## 8. Blender Files

| File | Size | Description |
|------|------|-------------|
| `tecate_reconstruction.blend` | (not listed) | Primary Blender 3D scene |
| `tecate_reconstruction.blend1` | 12.8 MB | Blender autosave backup |

The `.blend` file contains:
- All road network wireframe mesh (`RoadNetwork` object)
- All block facade mesh objects (grouped by texture material)
- All roof objects (color-only materials)
- Camera (`OrthoCamera` at `[0, -120, 110]`, `[48°, 0, 0]` rotation)
- Sun light + Point (hemi) light
- Embedded `Viewport_FOV_Cull_Utility.py` script (auto-registered, N-panel "Tecate Culler" tab)

---

## 9. Asset Provenance Summary

| Asset Category | Source | Automated? |
|---------------|--------|-----------|
| Terrain GLBs | INEGI + Sketchup/3D tooling | No (manual) |
| Municipal polygon | INEGI | No (manual) |
| OSM road graph | Overpass API | Yes (automated) |
| Block polygons | Computed from OSM graph | Yes |
| Facade observations | Google photometa API (unauthenticated) | Yes |
| Panorama metadata | Google photometa API | Yes |
| Facade screenshots | Google Street View (Playwright) | Yes |
| Warped textures | OpenCV homography + PIL compositing | Yes |
| Blender scene | `blender_script.py` | Yes |
| glTF export | Blender gltf exporter operator | Yes |

---

## 10. Asset Status Summary

| Category | Status | Notes |
|----------|--------|-------|
| Terrain models | ✅ Complete | 3 variants available in GLB + Babylon |
| Road graph cache | ✅ Complete | 82k+ nodes |
| Block cache | ✅ Complete | 4,239 blocks |
| Facade cache | ✅ Complete | 22,289 facades |
| Panorama cache | ✅ Substantial | 3,906 panoramas, ~80% from 2009 era |
| Facade textures | ✅ Near-complete | 99.84% textured |
| 3D Scene | ✅ Exported | 159 blocks in geometry.gltf |
| Terrain-scene alignment | ❌ Not implemented | Coordinate frame bridging is missing |
| Stereo/depth maps | ❌ Not present | No depth data or stereo output |
| Orthophoto/DSM | ❌ Not present | No aerial or satellite imagery |
| Temporal layering | ⚠️ Partial | Temporal filter exists but is not integrated into final output |
