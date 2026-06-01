# PIPELINE_RECONSTRUCTION.md — Tecate Simulator: Complete Pipeline Reconstruction

> All claims in this document are derived from direct code reading of the repository.  
> File citations are provided for each claim.

---

## Overview

The full pipeline consists of **6 major stages** operating sequentially with parallel sub-steps in Stage 4. It is crash-resilient: each stage persists its output to disk, and re-runs resume from the last saved checkpoint.

```
Stage 1: OSM Graph Construction
Stage 2: Block Polygon Extraction
Stage 3: Facade Segment Preparation
Stage 4: Metadata Scraping + Screenshot Capture
Stage 5: Texture Processing + Scene Document Compilation
Stage 6: Blender Assembly + glTF Export
```

---

## Stage 1: OSM Graph Construction

**Class**: `TecateGraphBuilder` in `src/gis_graph/graph_builder.py`  
**Output**: `NetworkX.MultiGraph G`, `data/tecate_osm_cache.json`  
**Invoked by**: `src/main.py` → `graph_builder.build_graph()`

### Steps

1. **Check cache**: If `data/tecate_osm_cache.json` exists and `--force-refresh` not set, load and return.

2. **Construct Overpass query**: Queries for `highway` types (`motorway`, `trunk`, `primary`, `secondary`, `tertiary`, `residential`, `unclassified`, `service`, `living_street`) using the INEGI municipal polygon as spatial filter, or falls back to bounding box.

3. **Call Overpass API**: `https://overpass-api.de/api/interpreter`

4. **Parse response**: Extract nodes (lat/lon) and ways (ordered node sequences with name/highway attributes).

5. **Build NetworkX graph**:
   - Add nodes with `x`/`y` local Cartesian coordinates (via `gps_to_local`)
   - Add edges with `name`, `length`, `id` attributes
   - Edge IDs are sequential: `e_0`, `e_1`, ...

6. **Sample waypoints** along edges (for Layer 1 adjacency): `sample_road_waypoints()` — produces a list of `(lat, lon)` points at regular intervals along each road for panorama metadata discovery.

7. **Save cache**: Write to `data/tecate_osm_cache.json`

8. **Save structural graph**: Write flat node/edge lists to `data/structural_graph/road_graph.json` and `intersections.json`

**Graph statistics** (from `reconstruction_export.json`):
- 82,872 nodes
- 87,177 edges

---

## Stage 2: Block Polygon Extraction

**Method**: `UrbanBlockReconstructor.extract_block_polygons()` in `src/reconstruction/prism_generator.py`  
**Output**: List of block dicts + `data/blocks_cache.json`

### Cache Resume (If Available)

If `blocks_cache.json` exists, blocks are loaded and filtered by:
- Active safety radius (if `--radius N` set)
- Municipal polygon boundary (ray-casting point-in-polygon)

### Fresh Extraction (If No Cache)

1. **Graph preprocessing**:
   - Copy `G` to undirected graph `temp_G`
   - Remove isolated nodes (degree 0)
   - Remove small isolated components (≤ 2 nodes)

2. **Compute angular-sorted neighbor lists**: For each node, sort its neighbors by angle to enable planar graph traversal.

3. **Half-edge traversal** (DCEL-like planar cycle extraction):
   - For each directed half-edge `(u → v)`:
     - Follow the "leftmost turn" at each node using the sorted neighbor list
     - Record the cycle traversed
   - This is equivalent to face traversal in a planar subdivision

4. **Filter valid blocks**:
   - Minimum 4 vertices
   - Signed area between 50 m² and 2,500,000 m²
   - Inside municipal polygon boundary
   - Inside safety radius (if set)
   - CCW orientation (negative signed area)

5. **Subdivide long edges**: `segment_long_polygon_edges(max_length=5.0m)` — inserts collinear intermediate vertices.

6. **Compute block_id**: `block_lat_{centroid_lat:.5f}_lon_{centroid_lon:.5f}`

7. **Save to blocks_cache.json**

**Result**: 4,239 blocks total, 159 processed blocks in current export

---

## Stage 3: Facade Segment Preparation

**Method**: Part of `reconstruct_single_block()` and `reconstruct_blocks_and_texture()`  
**Output**: `block_segments_info` list per block

### Per-Block Processing

1. **Shrink polygon**: `shrink_polygon(raw_poly, d=6.0m)` — inward offset (Minkowski erosion with per-vertex bisector method). Represents building footprint after street setback.

2. **For each facade segment (f_idx)**:
   - Compute endpoints A, B from shrunk polygon vertices
   - Compute midpoint (mx, my)
   - Compute outward normal (perpendicular to edge, pointing outward)
   - Compute `facade_id = {block_id}_facade_{f_idx}`

3. **Check cache**: If `facade_id` in `facades_cache`, restore `pano_id` and `heading`.

4. **Compute road distance**: `get_road_distance(mx, my)` via spatial grid index.  
   Mark as `is_street_facing` if `road_dist <= 20.0m`

5. **Compute search point**: `(search_x, search_y) = midpoint + 8.0 * normal`  
   Convert to GPS for API query.

6. **Compute initial heading**: `degrees(atan2(-normal_x, -normal_y)) % 360.0`

---

## Stage 4: Metadata Scraping + Screenshot Capture

**Pre-pass**: Sequential on main thread  
**Main pass**: Can run in parallel worker threads  
**Class**: `GoogleStreetViewScraper` in `src/data_acquisition/browser_scraper.py`

### 4A: Metadata Resolution (Main Thread, Sequential)

For each uncached street-facing facade:

1. **Build API URL**: `build_find_panorama_request_url(lat, lon)` — encodes a protobuf-format URL to Google's unauthenticated photometa endpoint:
   ```
   https://maps.googleapis.com/maps/api/js/GeoPhotoService.SingleImageSearch?pb=...
   ```

2. **HTTP GET with headers**: Spoofed Mac Chrome User-Agent + Referer.

3. **Parse response**: `parse_photometa_response()` — decodes nested JSON proto structure to extract:
   - `pano_id` (22-char base64 or ARI format)
   - `lat`, `lon` of panorama
   - `date` (YYYY-MM)
   - `road_name`
   - `adjacent_links` (neighboring pano_ids)
   - `timeline` (historical states)

4. **Temporal chronology selection**: Iterate `timeline` list, find the entry with the **oldest date**:
   ```python
   oldest_date = min(tl['date'] for tl in timeline)
   oldest_pano_id = timeline_entry_for_oldest
   ```
   If the oldest pano differs from the returned modern pano, query the oldest pano_id directly via `build_find_panorama_by_id_request_url()`.

5. **Update caches**:
   - `panoramas_cache[pano_id] = {lat, lon, altitude, date, pitch, roll, projection_yaw, road_name, adjacent_links, timeline}`
   - `facades_cache[facade_id] = {pano_id, block_id, facade_index, heading, resolution, camera_rotation_matrix, road_relation, facade_midpoint_local, offset_search_point_gps, search_query_url, captured_url, modern_pano_id, camera_alignment_diagnostics, facade_segment_vertices_local}`

### 4B: Screenshot Capture

For each contiguous group of facades sharing the same `pano_id` + similar heading (within 20°):

1. **Group formation**: Facades are grouped by `(pano_id, heading)` (circular sequence, angular diff ≤ 20°). The combined group represents a single camera view.

2. **Check for existing virtual texture**: If `{block_id}_virtual_{cardinal}_{group_idx}.png` already exists at `export/textures/`, skip capture.

3. **Check for existing screenshot**: `data/screenshots/pano/{pano_id}_yaw_{heading:.2f}.png`

4. **Capture if missing**:
   - `capture_facade_screenshot(lat, lon, heading, pano_id, slice_id)` 
   - Navigates Playwright (persistent Chromium) to:
     ```
     https://www.google.com/maps?layer=c&cbll={lat},{lon}&panoid={pano_id}&cbp=11,{heading:.2f},,0,0
     ```
   - Waits for `<canvas>` selector
   - Injects CSS to hide Google Maps overlays (minimap, compass, watermark, controls)
   - Waits for `networkidle` (max 1.5s) + 1.0s sleep
   - Takes `page.screenshot()` → bytes
   - Saves to `data/screenshots/pano/{pano_id}_yaw_{heading:.2f}.png`

**Browser settings**:
- Viewport: 1280×720
- User-Agent: Mac Chrome 120
- GL: SwiftShader (software renderer for headless compatibility)
- `--ignore-gpu-blocklist`, `--disable-web-security`

---

## Stage 5: Texture Processing + Scene Document Compilation

**Methods**: `mask_sky_in_panorama()`, `extract_rectified_facade_observation_texture()`, `reconstruct_single_block()`

### 5A: Sky Masking

`mask_sky_in_panorama(image_path, cx, cy, heading, height_meters, group_segments)`:

1. **Compute roofline Y position** per-column using inverse perspective:
   ```
   y_proj = c_y - f * ((height_meters - cam_z) / z_c_x)
   ```
   Where `z_c_x` is camera depth to the facade at that column (via ray-plane intersection).

2. **Refine with edge detection**: Within ±25px of projected roofline, find first column pixel where:
   - `color_distance_from_sky > 35.0` AND `color_gradient > 15.0`

3. **Mask sky**: Set `alpha = 0` for all pixels above the detected roofline per column.

4. **Returns**: RGBA PIL Image with sky masked out.

### 5B: Perspective Homography Warp

`extract_rectified_facade_observation_texture(obs, A, B, height_meters, width, height)`:

1. **Project 4 wall corners** (BL, BR, TR, TL in world space) into screenshot pixel space using pinhole projection.

2. **Compute homography**: `cv2.getPerspectiveTransform(source_pts, target_pts)` — maps screen quad to texture quad.

3. **Warp image**: `cv2.warpPerspective(RGBA_img, M, (width, height), INTER_LINEAR, BORDER_CONSTANT, border=(0,0,0,0))`.

4. **Edge blur** (seam smoothing): Apply `GaussianBlur(kernel=25, sigma=0)` to leftmost and rightmost 25% of the warped image to smooth group boundaries.

5. **Save**: `export/textures/{block_id}_virtual_{cardinal}_{group_idx}.png`

### 5C: UV Coordinate Assignment

For each facade within a group:
- `u_seg_start = 0.375 + 0.25 * (cum_L / L_total)` — maps to center 25% of texture
- `u_seg_end = 0.375 + 0.25 * ((cum_L + seg_len) / L_total)`

The UV `[0.375, 0.625]` range corresponds to the unblurred central region of the warped group texture.

### 5D: Height Estimation

`estimate_facade_segment_height()` — per-facade:
- Scans columns of saved screenshot
- Detects roofline per column via sky color matching
- Solves 3D height via ray-plane intersection
- Returns `median * 2.0` as building extrusion height
- Clamped to `[3.2, 6.5]` per-column, then doubled for block height

### 5E: Roof Color Extraction

`calculate_predominant_roof_color(facade_textures_map)`:
- Loads a sample of facade textures
- Computes average RGB of non-transparent pixels
- Returns RGB float tuple for solid roof material

### 5F: Block Data Assembly

For each block, assembles:
```python
block_data = {
    "block_id": b_id,
    "polygon": shrunk_poly,
    "height_meters": height_meters,
    "centroid": [centroid_x, centroid_y],
    "texture_atlas_path": fallback_path,
    "facade_textures": {facade_id: tex_path, ...},
    "uv_mappings": {facade_id: [[u,v]×4], ...},
    "roof_color": [r, g, b],
    "traceability": [{"facade_idx": i, "source": "image"|"fallback"}, ...]
}
```

### 5G: Fallback Segment Resolution

`resolve_almost_adjacent_fallback_segments()` — 2-pass loop:
- For facades with no panorama (fallback), find nearest textured neighbor within 2 positions
- Assign that neighbor's `pano_id` and `heading`
- This propagates texture coverage across short gap segments

### 5H: Scene Document Export

After all blocks are processed:
```python
scene_doc = {
    "road_graph": {"nodes": [...], "edges": [...]},
    "blocks": [block_data_0, block_data_1, ...]
}
```
Saved to `export/reconstruction_export.json`.

Metadata saved to `export/metadata.json`:
```python
{
    "total_blocks": N,
    "total_facades": M,
    "textured_facades": T,
    "coverage_percentage": T/M*100,
    "provenance": {facade_id: {source_pano_id, source_date, ...}}
}
```

---

## Stage 6: Blender Assembly + glTF Export

**Script**: `blender_script.py`  
**Invoked by**: `src/main.py::run_blender_export()` via `subprocess.run()`

### 6A: Scene Clearing

`clear_scene()` — removes all objects, meshes, materials, images, cameras, lights.

### 6B: Road Graph

`create_road_graph_mesh(graph_data)`:
- Creates vertices at `(node.x, node.y, 0.05)` for each graph node
- Creates edges between connected nodes
- Assigns flat dark road material
- Creates single `RoadNetwork` mesh object

### 6C: Block Mesh Construction

`build_block_meshes(blocks_data, cull_fov, cam_loc, cam_rot, fov_deg, max_dist)`:

**Performance design**: Facades are **grouped by shared texture file** into single mesh objects. This prevents material slot explosion and EEVEE memory crashes.

For each block:
1. **Evaluate camera visibility** (FOV frustum + distance culling) → sets `hide_viewport/hide_render`
2. **Accumulate facade geometry** into per-texture dict: vertices, faces, UVs
3. **Create roof mesh** — flat polygon at `z = height`, solid color material (shared by similar roof colors)

For each unique texture file:
1. **Create mesh** from accumulated vertices + faces
2. **Load texture image** into Blender (exactly once, cached)
3. **Create Principled BSDF material** with texture → Base Color + Alpha
4. **Set blend_method = 'BLEND'** for transparency support
5. **Create Blender Object**, attach material, store centroid as custom property

### 6D: GPU Configuration

`configure_gpu_acceleration()` — attempts Metal (macOS), OptiX, CUDA, HIP, OpenAPI GPU compute in preference order.

### 6E: Lighting + Camera

`setup_lighting_and_camera()`:
- **Sun light**: Energy 3.5, at (0, 0, 150), 35°/20°/45° euler
- **Point light**: Energy 8000, at (0, 0, 80) — acts as ambient
- **Camera**: FOV-matched, at `cam_loc=[0, -120, 110]`, `cam_rot=[48°, 0, 0]`

### 6F: Embedded Culling Script

`embed_culling_utility_script()`:
- Generates a full Blender `bpy.types.Panel` + `Timer` script as a string
- Writes to `bpy.data.texts["Viewport_FOV_Cull_Utility.py"]`
- Sets `use_module = True` (auto-runs on blend file load)
- Provides N-panel "Tecate Culler" with OFF/AUTO/MANUAL modes + distance/FOV sliders + safety cap

### 6G: Save + Export

1. `bpy.ops.wm.save_as_mainfile(filepath="tecate_reconstruction.blend")` → `.blend` file
2. `bpy.ops.export_scene.gltf(filepath="export/geometry.gltf", export_format='GLTF_SEPARATE', ...)` → `geometry.gltf` + `geometry.bin`

---

## Incremental Resumption Logic

At each major stage, the pipeline checks for existing output and skips if found:

| Stage | Resume Trigger | Skip Condition |
|-------|---------------|----------------|
| OSM graph | `data/tecate_osm_cache.json` | File exists + no `--force-refresh` |
| Block extraction | `data/blocks_cache.json` | File exists |
| Facade metadata | `data/facades_cache.json[facade_id]` | Entry exists |
| Screenshot | `data/screenshots/pano/{pano_id}_{heading}.png` | File exists |
| Virtual texture | `export/textures/{block_id}_virtual_*.png` | File exists |
| Block 3D output | `export/reconstruction_export.json[block_id]` | Entry exists + no `--reprocess` |

---

## Graceful Shutdown (Ctrl+C)

`graceful_shutdown()` in `UrbanBlockReconstructor`:
1. Save `stitching_cache.json`
2. Save `metadata_cache` → `panoramas_cache.json` + `facades_cache.json` + `blocks_cache.json`
3. If partial `current_blocks_data` exists: export `reconstruction_export.json`, `metadata.json`, `reconstruction_diagnostics.json`
4. Generate diagnostic coverage map
5. Trigger background Blender compilation
6. `os._exit(0)`

---

## Parallelism Model

- **Main thread**: Sequential metadata resolution + API queries (rate-limited, serialized for reliability)
- **Worker threads** (`self.parallel` = `os.cpu_count()`): Texture processing (homography warping, sky masking) per block
- **Thread safety**: `cache_lock` (threading.Lock) guards all read/write of shared caches; `scraper_lock` guards the singleton Playwright browser instance

---

## Coverage Statistics (Current State)

| Metric | Value |
|--------|-------|
| Total blocks in cache | 4,239 |
| Blocks in current export | 159 |
| Total facades in export | 15,532 |
| Textured facades | 15,507 |
| **Coverage** | **99.84%** |
| Unique panoramas used | 3,906 |
| Date range of panos | 2008-12 to 2025-09 |
| Primary target year | 2009 (80% of panos) |
