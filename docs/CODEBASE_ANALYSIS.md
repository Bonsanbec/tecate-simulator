# CODEBASE_ANALYSIS.md — Tecate Simulator: Codebase Analysis

---

## 1. Module-by-Module Analysis

### 1.1 `src/core_io/coords.py`

**Functions**:
| Signature | Description |
|-----------|-------------|
| `gps_to_local(lat, lon) → (x, y)` | GPS degrees → local Cartesian meters (equirectangular) |
| `local_to_gps(x, y) → (lat, lon)` | Local Cartesian → GPS degrees |

**Constants**:
- `TECATE_LAT_CENTER = 32.573229`
- `TECATE_LON_CENTER = -116.626536`
- `EARTH_RADIUS = 6378137.0` (WGS84 equatorial, not WGS84 mean radius 6371km)

**Design Notes**:
- Uses flat-Earth approximation (equirectangular projection). Valid within ~5km radius with <0.1% error.
- All pipeline geometry passes through these two functions — they are the foundational coordinate contract.
- `gps_to_local` is called from `prism_generator.py`, `browser_scraper.py`, and `migration.py`.

---

### 1.2 `src/core_io/io_manager.py`

**Functions**:
| Signature | Description |
|-----------|-------------|
| `ensure_dir(path: str)` | `os.makedirs(path, exist_ok=True)` |
| `load_json(path: str) → dict` | `json.load` with UTF-8 encoding |
| `save_json(data, path, indent=None)` | `json.dump` with UTF-8 + optional indentation |

**Design Notes**:
- Extremely thin utility wrappers. No error handling — callers use try/except.
- `indent=None` defaults to compact format (no whitespace), saving disk space.

---

### 1.3 `src/core_io/migration.py` — `ArchivalDataMigrator`

**Purpose**: One-time migration of legacy scraped data to the clean structural_graph format.

**Key Methods**:
| Method | Description |
|--------|-------------|
| `migrate()` | Orchestrates migration from old format to structural_graph |
| `save_road_graph()` | Writes `data/structural_graph/road_graph.json` |
| `save_intersections()` | Writes `data/structural_graph/intersections.json` |

**Design Notes**:
- Appears to be a maintenance utility, not part of the live pipeline.
- Indicates the repo has undergone at least one schema evolution.

---

### 1.4 `src/gis_graph/graph_builder.py` — `TecateGraphBuilder`

**Constructor**: `TecateGraphBuilder(data_dir, radius=None, force_refresh=False)`

**Key Methods**:
| Method | Return | Description |
|--------|--------|-------------|
| `build_graph()` | `nx.MultiGraph` | Main entry point: load or build OSM graph |
| `_load_osm_from_overpass()` | `dict` | Raw Overpass API call |
| `_parse_osm_data(data)` | `nx.MultiGraph` | Convert raw OSM to NetworkX |
| `sample_road_waypoints()` | `list[dict]` | Generate evenly-spaced waypoints along edges |
| `save_structural_graph(G)` | `None` | Write road_graph.json + intersections.json |

**Graph Node Attributes** (in NetworkX):
- `x`: local East meters
- `y`: local North meters
- `lat`: WGS84 latitude
- `lon`: WGS84 longitude

**Graph Edge Attributes** (in NetworkX):
- `id`: `e_N` string
- `name`: street name
- `length`: Euclidean distance in meters

**Design Notes**:
- Uses `nx.MultiGraph` (allows multiple parallel edges between same nodes).
- Edge IDs are assigned sequentially during parsing, not from OSM way IDs.
- The graph is used both for block cycle extraction (undirected) and for road distance queries (indexed by spatial grid).

---

### 1.5 `src/data_acquisition/browser_scraper.py`

#### Free Functions

| Function | Description |
|----------|-------------|
| `to_protobuf_url(fields)` | Encodes a nested dict to Google's proto-URL format (`!NtV...`) |
| `build_find_panorama_request_url(lat, lon, radius, ...)` | Builds lat/lon-based metadata search URL |
| `build_find_panorama_by_id_request_url(panoid, ...)` | Builds pano_id-based metadata lookup URL |
| `repair_find_panorama_response(text)` | Strips JSONP wrapper from response |
| `parse_photometa_response(data)` | Extracts fields from nested JSON proto response |

**Proto-URL format** (reverse-engineered):
```
!1m5!1sapiv3!5sUS... → top-level proto fields
!1m2!1d32.573!2d-116.626 → location message
!2d50.0 → radius
...
```

#### `GoogleStreetViewScraper` Class

**Constructor**: `GoogleStreetViewScraper(headless=True, log=False, G=None)`

**State**:
- `playwright`, `playwright_context_manager`, `browser`, `context`, `page` — Playwright session (lazy init)
- `intercepted_panos` — dict for network-intercepted panorama data (populated but usage not confirmed in current code)

**Key Methods**:
| Method | Return | Description |
|--------|--------|-------------|
| `init_browser()` | `None` | Lazy Playwright init with SwiftShader GL |
| `close()` | `None` | Safely closes browser session |
| `capture_facade_screenshot(lat, lon, heading, pano_id, slice_id)` | `bytes\|None` | Navigate + screenshot |
| `fetch_public_metadata(lat, lon, pano_id, locale)` | `dict\|None` | Query photometa API |

**Dual API support**: `fetch_public_metadata` handles both:
1. Modern photometa API (`/maps/photometa/v1?...&pb=...`)
2. Legacy GeoPhotoService API (JSONP format, stripped via `repair_find_panorama_response`)
3. Old CBK-format responses (for test mocks)

---

### 1.6 `src/data_acquisition/sv_downloader.py` — `StreetViewDownloader`

**Status**: Legacy/secondary. Not called by `prism_generator.py`. Requires API key (`GOOGLE_STREETVIEW_API_KEY`).

**Methods**:
| Method | Description |
|--------|-------------|
| `has_api_key()` | Check if API key is set |
| `get_metadata(lat, lon)` | Fetch metadata via official SV Metadata API |
| `download_viewpoint(lat, lon, heading, pitch, fov)` | Download 640×640 SV static image |
| `fetch_full_panorama(lat, lon)` | Download 4-heading stitched panorama |

**Temporal probability heuristic** (in `fetch_full_panorama`):
```python
if year == 2009:  prob = 0.95
elif year < 2010: prob = 0.85
else:             prob = 0.05
```

---

### 1.7 `src/temporal_filter/classifier.py`

**Purpose**: Predict whether a given panorama image was captured circa 2009, using classical CV features (without ML models).

#### `TemporalVisualClassifier`

**Key Methods**:
| Method | Return | Description |
|--------|--------|-------------|
| `extract_features(image)` | `dict` | Extract `laplacian_variance`, `orb_keypoints`, `color_histogram` from PIL image |
| `classify(image)` | `float` | Returns probability [0,1] that image is ~2009 vintage |
| `batch_classify(images)` | `list[float]` | Classify a batch |

**Feature extraction logic**:
- `laplacian_variance`: `cv2.Laplacian(gray, cv2.CV_64F).var()` — high variance → sharper image → possibly newer
- `orb_keypoints`: `cv2.ORB_create().detect(gray)` — count of detected keypoints
- `color_histogram`: RGB histogram (normalized)

**Classification**: Rule-based thresholds on feature values. Not ML-trained — heuristic only.

#### `TemporalMRFSolver`

**Purpose**: Propagate temporal labels across the panorama observation graph using a Markov Random Field.

**Key Methods**:
| Method | Description |
|--------|-------------|
| `build_observation_graph(observations)` | Build graph from observation list |
| `solve(observations)` | Run label propagation |
| `get_labels(observations)` | Return final temporal label assignments |

**Connectivity**: Two panoramas are connected if their GPS positions are within a threshold distance. Labels propagate from high-confidence to low-confidence observations.

> [!NOTE]
> **Integration status**: `TemporalVisualClassifier` and `TemporalMRFSolver` are **not invoked** in the current `reconstruct_blocks_and_texture()` pipeline. The temporal selection is handled instead by a simpler **date-comparison on the `timeline` list** in `reconstruct_single_block()`. These classes appear to be a more sophisticated alternative that was not wired into the live pipeline.

---

### 1.8 `src/visualization/coverage.py` — `SpatialCoverageVisualizer`

**Key Methods**:
| Method | Description |
|--------|-------------|
| `generate_diagnostic_map(scene_doc, diag_facades, coverage_pct)` | Main entry point |
| `_draw_road_graph(G)` | Plot road edges as gray lines |
| `_draw_facade_dots(facades, status)` | Color-coded facade midpoints |
| `_add_legend(coverage_pct)` | Coverage percentage + legend |

**Output**: PNG image (`export/debug/global_observation_map.png`)

**Color scheme**:
- Green: textured facades
- Red: fallback (untextured) facades
- Blue: cached/resumed facades

---

### 1.9 `src/reconstruction/prism_generator.py` — `UrbanBlockReconstructor`

**This is the largest and most complex module (2,673 lines).** Key methods are catalogued below.

#### Constructor Dependencies (Injected)

| Parameter | Type | Description |
|-----------|------|-------------|
| `G` | `nx.MultiGraph` | Road graph |
| `accepted_panos` | `list[dict]\|None` | Pre-filtered pano list (not actively used) |
| `export_dir` | `str` | Output directory |
| `data_dir` | `str` | Cache directory |
| `headless` | `bool` | Browser headless mode |
| `radius` | `float\|None` | Safety radius filter |
| `reprocess` | `bool` | Force re-processing |
| `skip_scraper` | `bool` | Offline mode |
| `harvest_only` | `bool` | Metadata only mode |
| `parallel` | `int` | Worker thread count |

#### Method Catalogue

| Method | Lines | Category | Description |
|--------|-------|----------|-------------|
| `__init__` | 21–222 | Setup | Cache loading, lock init, Playwright init, SIGINT handler |
| `is_point_in_polygon` | 239–258 | Geometry | Ray-casting PIP test |
| `save_*_cache` | 261–287 | IO | Individual cache savers |
| `_decompose_metadata_cache` | 289–347 | IO | Virtual metadata_cache → relational caches |
| `save_metadata_cache` | 349–353 | IO | Orchestrates all cache saves |
| `graceful_shutdown` | 355–412 | System | Ctrl+C handler with checkpoint export |
| `build_all_facade_segments` | 414–473 | Geometry | Global facade segment registry |
| `migrate_metadata_cache` | 475–479 | Migration | No-op (migration complete) |
| `extract_block_polygons` | 481–623 | Geometry | DCEL-like cycle extraction |
| `segment_long_polygon_edges` | 625–650 | Geometry | 5m edge subdivision |
| `shrink_polygon` | 652–697 | Geometry | Inward polygon offset |
| `get_road_distance` | 699–776 | Geometry | Grid-indexed point-to-segment distance |
| `score_observation_candidate` | 778–821 | Matching | Candidate scoring (alignment × distance × road × quality) |
| `extract_rectified_facade_observation_texture` | 823–904 | CV | Pinhole projection + homography warp |
| `generate_transparent_fallback` | 906–913 | IO | Cached transparent RGBA image |
| `find_horizontal_overlap_offset` | 914–953 | CV | NCC-based coarse+fine shift search |
| `stitch_facades_with_similarity` | 955–1027 | CV | NCC stitching + linear blend |
| `crop_facade` | 1029–1107 | CV | Sky/pavement crop + perspective projection crop |
| `estimate_facade_segment_height` | 1109–1217 | CV | Ray-plane height solving from roofline |
| `mask_sky_in_panorama` | 1219–1345 | CV | Column-wise roofline tracing + alpha mask |
| `resolve_almost_adjacent_fallback_segments` | 1347–1409 | Reconstruction | 2-pass neighbor-based fallback fill |
| `cardinal_from_normal` | 1411–1416 | Utility | Normal → "north"/"south"/"east"/"west" |
| `save_checkpoint_helper` | 1418–1447 | IO | Mid-run checkpoint with all outputs |
| `reconstruct_single_block` | 1449–2108 | Core | Per-block full reconstruction |
| `reconstruct_blocks_and_texture` | 2110–2400+ | Core | Full pipeline orchestrator |
| `generate_diagnostic_visualization` | ~2400+ | Viz | Delegates to `SpatialCoverageVisualizer` |
| `calculate_predominant_roof_color` | ~2400+ | CV | Roof color from facade texture average |

---

## 2. Design Patterns

### 2.1 Relational Cache Architecture

The system implements a **virtual in-memory merge + disk decomposition** pattern:

```
disk:  panoramas_cache.json  +  facades_cache.json
                    ↓
memory: metadata_cache (merged view)
                    ↓
disk:  metadata_cache  →  _decompose_metadata_cache()  →  panoramas_cache + facades_cache
```

This allows the reconstruction code to work with a single unified dict while preserving normalized storage. The decomposition step strips ephemeral in-memory fields (like `camera_position_local`, `offset_search_point_local`) before writing to disk.

### 2.2 Incremental Resumption

Three levels of skip-ahead:
1. **Block-level**: If `block_id` in `existing_export_blocks` → return cached result immediately
2. **Facade-level**: If `facade_id` in `facades_cache` → skip metadata API call
3. **File-level**: If PNG exists on disk → skip screenshot capture / texture generation

### 2.3 Thread Safety

- `cache_lock`: `threading.Lock` protects all shared cache dict reads/writes
- `scraper_lock`: `threading.Lock` ensures single-threaded Playwright browser access
- Pre-pass on main thread handles all network I/O (sequential) — parallel threads handle compute only

### 2.4 Lazy Initialization

- Playwright browser: initialized only when first `capture_facade_screenshot` is called
- Spatial grid index: built on first `get_road_distance` call
- Transparent fallback PNG: cached in-memory dict `_cached_transparent_dict`

### 2.5 Graceful Degradation

- Missing pano → transparent fallback texture
- Screenshot capture failure → fallback texture
- API query failure → segment skipped (not retried in current code)
- Homography projection failure (z_c ≤ 0) → full screenshot used unwarped

---

## 3. Known Code Issues

...

---

## 4. Algorithmic Choices

| Algorithm | Location | Choice | Alternative |
|-----------|----------|--------|------------|
| Block cycle extraction | `extract_block_polygons` | DCEL-like planar CCW traversal | `nx.cycle_basis` (less geometrically precise) |
| Polygon inward offset | `shrink_polygon` | Per-vertex bisector method | Shapely `polygon.buffer(-d)` |
| Pano metadata | `fetch_public_metadata` | Unauthenticated proto-URL API | Official SV Metadata API (requires key) |
| Temporal selection | `reconstruct_single_block` | Min-date from timeline list | CV-based `TemporalVisualClassifier` |
| Facade texture | `extract_rectified_facade_observation_texture` | OpenCV pinhole homography | Direct image crop / ML depth estimation |
| Sky masking | `mask_sky_in_panorama` | Color distance + gradient threshold per column | Semantic segmentation |
| Height estimation | `estimate_facade_segment_height` | Inverse perspective from sky-building boundary | LiDAR / depth maps |
| Road distance | `get_road_distance` | Grid-indexed point-to-segment | R-tree spatial index (e.g., via Shapely/scipy) |
| Image stitching | `stitch_facades_with_similarity` | NCC coarse+fine search | SIFT/ORB feature matching |
| Roof color | `calculate_predominant_roof_color` | Mean RGB of texture | Dominant color clustering (KMeans) |
| Blender geometry | `build_block_meshes` | Group faces by shared texture | Per-face individual objects |

---

## 5. File Size Analysis

| Source File | Lines | Bytes | Complexity |
|-------------|-------|-------|-----------|
| `prism_generator.py` | 2,673 | 126,589 | Very High — core engine |
| `blender_script.py` | 796 | 30,517 | High — full Blender API usage |
| `browser_scraper.py` | 701 | 26,446 | Medium-High — proto encoding + Playwright |
| `graph_builder.py` | ~400 | varies | Medium |
| `classifier.py` | ~300 | varies | Medium |
| `coverage.py` | ~200 | varies | Low-Medium |
| `migration.py` | ~150 | varies | Low |
| `sv_downloader.py` | 134 | 5,004 | Low |
| `coords.py` | ~30 | ~1,000 | Very Low |
| `io_manager.py` | ~20 | ~500 | Very Low |

---

## 6. Test Coverage

`pytest` is listed in `requirements.txt`. No test files were observed in the repository during discovery. Test infrastructure exists but no test files appear present.
