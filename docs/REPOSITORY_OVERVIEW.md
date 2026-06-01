# REPOSITORY_OVERVIEW.md — Tecate Simulator: Complete Architectural Overview

> **Project**: Tecate 2009 Historical Urban Reconstruction System  
> **Purpose**: End-to-end pipeline to reconstruct a spatially coherent 3D environment of downtown Tecate, Baja California, Mexico using historical (~2009) Google Street View imagery.  
> **Repository**: `Bonsanbec/tecate-simulator`

---

## 1. High-Level Purpose

The system ingests an OpenStreetMap road graph, traverses it to extract city block polygons, queries the Google Street View backend (unauthenticated) for historical panorama metadata, captures screenshots via a headless Chromium browser (Playwright), processes them with perspective homography warping and NCC-based stitching, and compiles the result into a textured 3D glTF/GLB asset via headless Blender.

The pipeline is designed to be **crash-resilient**, **incrementally resumable**, and **offline-capable** once caches are warm.

---

## 2. Directory Tree

```
tecate-simulator/
│
├── src/                              # Main Python package
│   ├── __init__.py
│   ├── main.py                       # CLI master orchestrator (entry point)
│   ├── core_io/                      # Coordinate conversion + IO utilities
│   │   ├── coords.py                 # GPS ↔ local Cartesian (ETP projection)
│   │   ├── io_manager.py             # ensure_dir / save_json / load_json
│   │   └── migration.py              # Legacy archive migrator (ArchivalDataMigrator)
│   ├── data_acquisition/             # Network scrapers
│   │   ├── browser_scraper.py        # Playwright Chromium scraper + unauthenticated photometa API
│   │   └── sv_downloader.py          # (Legacy) Official Street View Static API downloader
│   ├── gis_graph/
│   │   └── graph_builder.py          # OSM Overpass query + NetworkX graph builder
│   ├── reconstruction/
│   │   └── prism_generator.py        # Core: block cycle extraction, facade texturing, scene export (2673 lines)
│   ├── temporal_filter/
│   │   └── classifier.py             # CV-based 2009 temporal classifier + MRF solver
│   └── visualization/
│       └── coverage.py               # Spatial coverage diagnostic map generator
│
├── data/                             # Relational cache tables (primary datasets)
│   ├── tecate_osm_cache.json         # OSM road graph (26 MB)
│   ├── blocks_cache.json             # Block polygons + heights + roof colors (26 MB)
│   ├── facades_cache.json            # Facade observations (22 MB)
│   ├── panoramas_cache.json          # Panorama metadata (1.6 MB)
│   ├── stitching_cache.json          # (currently empty — shift offsets)
│   ├── screenshots/                  # Raw downloaded Playwright screenshots (PNG)
│   └── structural_graph/             # Layer 1 graph output from ArchivalDataMigrator
│       ├── intersections.json        # OSM intersection nodes (373 KB)
│       └── road_graph.json           # Flat node/edge list (672 KB)
│
├── export/                           # Compiler outputs
│   ├── geometry.gltf                 # Final textured 3D scene (glTF, separate)
│   ├── geometry.bin                  # Binary geometry buffer (2.4 MB)
│   ├── reconstruction_export.json    # Scene document: road graph + block list (37 MB)
│   ├── reconstruction_export_win.json # Windows-path translated version (38 MB)
│   ├── metadata.json                 # Coverage statistics + provenance (9 MB)
│   ├── textures/                     # Per-block facade PNG textures (virtual renders)
│   └── debug/
│       ├── global_observation_map.png  # Spatial coverage visualization
│       └── reconstruction_diagnostics.json  # Per-facade texturing status (6.7 MB)
│
├── models/                           # Pre-existing terrain models (external source)
│   └── tecate/
│       ├── tecate.md                 # Terrain provenance notes
│       ├── babylon/                  # Three Babylon.js .babylon terrain variants
│       └── glb/                      # Three GLB terrain variants (~86–325 MB each)
│
├── reference/                        # Reference geospatial data
│   └── tecate-polygon.json           # INEGI municipal boundary GeoJSON
│
├── blender_script.py                 # Blender headless assembler (796 lines)
├── requirements.txt                  # Python dependencies
├── run.sh                            # Bash crawler loop (scrape → commit → push)
├── research.md                       # Extended project research notes (27 KB)
├── tecate_reconstruction.blend1      # Blender autosave (~12.8 MB)
└── README.md                         # Documentation hub
```

---

## 3. Module Map

| Module | File | Role |
|--------|------|------|
| **CLI Orchestrator** | `src/main.py` | Argument parsing, pipeline execution, Blender invocation, WSL path translation |
| **Coordinate System** | `src/core_io/coords.py` | GPS ↔ local ETP Cartesian projection centered at Parque Hidalgo |
| **IO Utilities** | `src/core_io/io_manager.py` | `ensure_dir`, `save_json`, `load_json` |
| **Cache Migrator** | `src/core_io/migration.py` | Migrates legacy raw-scraped archive to structural_graph layout |
| **OSM Graph Builder** | `src/gis_graph/graph_builder.py` | Overpass query, NetworkX graph construction, edge sampling |
| **Playwright Scraper** | `src/data_acquisition/browser_scraper.py` | Unauthenticated photometa API + Chromium screenshot capture |
| **Static API Downloader** | `src/data_acquisition/sv_downloader.py` | Official SV Static API (requires key, secondary/legacy) |
| **Block Reconstructor** | `src/reconstruction/prism_generator.py` | Complete reconstruction engine (2673 lines) |
| **Temporal Classifier** | `src/temporal_filter/classifier.py` | `TemporalVisualClassifier` + `TemporalMRFSolver` |
| **Coverage Visualizer** | `src/visualization/coverage.py` | `SpatialCoverageVisualizer` → PNG map |
| **Blender Assembler** | `blender_script.py` | Reads scene JSON, builds Blender meshes, exports glTF/GLB |

---

## 4. Python Dependencies

```
numpy>=1.20.0        # Vectorized math, array operations
opencv-python>=4.5.0 # NCC template matching, Laplacian, ORB keypoints, homography
networkx>=2.6.0      # Road graph representation and cycle traversal
pillow>=8.0.0        # Image I/O, compositing, drawing
requests>=2.25.0     # HTTP: Overpass API + photometa API calls
pytest>=6.0.0        # Test runner
playwright>=1.15.0   # Chromium browser automation
py360convert>=1.0.4  # Equirectangular/panorama conversions (present in requirements, not actively called in current main pipeline)
```

> **Note**: `py360convert` is listed but its active usage was not found in the main pipeline code. It may be legacy or reserved for future panorama conversion work.

---

## 5. Entry Points

### Primary CLI
```bash
PYTHONPATH=. python src/main.py [options]
```

Key flags:
| Flag | Default | Effect |
|------|---------|--------|
| `--skip-scraper` | `False` | Run entirely from cache (offline) |
| `--reprocess` | `False` | Re-run image processing without re-downloading |
| `--harvest-only` | `False` | Scrape metadata/screenshots only, skip 3D |
| `--headless` | Platform-detected | Chromium headless mode |
| `--radius N` | `-1` (whole city) | Restrict crawl to N-meter radius from Parque Hidalgo |
| `--parallel N` | `os.cpu_count()` | Worker thread count |
| `--no-cull` | — | Disable camera FOV culling in Blender |

### Batch Loop
```bash
./run.sh   # Loops: scrape → commit → sleep → repeat
```

### Blender
```bash
blender --background --python blender_script.py -- --import export/reconstruction_export.json
```

---

## 6. Build System

- **No formal build system** (no Makefile, CMake, pyproject.toml, or setup.py).
- Dependencies managed via `pip` + `venv`.
- `run.sh` is the operational automation wrapper.
- Blender is invoked as an external subprocess via `subprocess.run()` in `src/main.py`.

---

## 7. Pipeline Summary (High Level)

```
[OSM Overpass API]
       │
       ▼
[TecateGraphBuilder] → tecate_osm_cache.json → NetworkX MultiGraph (G)
       │
       ▼
[UrbanBlockReconstructor]
  ├── [extract_block_polygons()] → planar CCW cycle traversal → block polygons → blocks_cache.json
  ├── [shrink_polygon(d=6.0m)] → per-block inward offset (street setback)
  ├── [segment_long_polygon_edges(max=5m)] → 5-meter facade subdivisions
  ├── [get_road_distance()] → spatial grid index → street-facing filter (≤20m)
  │
  ├── [Pre-pass: Sequential scraping on main thread]
  │     ├── [fetch_public_metadata(lat,lon)] → protobuf URL → JSON photometa → pano_id, date, timeline
  │     ├── [Temporal chronology selection] → select oldest pano_id from timeline
  │     └── Update panoramas_cache + facades_cache
  │
  ├── [Parallel worker threads (N=cpu_count)]
  │     ├── [capture_facade_screenshot()] → Playwright → 1280×720 PNG
  │     ├── [mask_sky_in_panorama()] → sky/roofline masking (vectorized NumPy)
  │     ├── [extract_rectified_facade_observation_texture()] → pinhole projection + cv2.getPerspectiveTransform
  │     └── Save virtual facade PNG → export/textures/
  │
  └── [reconstruct_single_block()] → block_data dict (polygon, UVs, textures, roof_color)
       │
       ▼
[scene_doc: reconstruction_export.json]
       │
       ▼
[blender_script.py] → bpy mesh assembly → GPU config → .blend + geometry.gltf/geometry.bin
```

---

## 8. Operational Automation

`run.sh` implements a **continuous crawl-commit loop**:
1. Run `src/main.py --headless` with full pipeline
2. Remove Blender autosave `tecate_reconstruction.blend1`
3. `git add data/ export/ tecate_reconstruction.blend *.glb`
4. `git commit -m "Incremental Street View archival $(date)"`
5. `git push origin master`
6. `sleep 1` and repeat

This implies the repository functions as a **living archive** that incrementally captures and commits new Street View data.

---

## 9. Cross-Platform Support

The codebase explicitly handles:
- **macOS**: Blender at `/Applications/Blender.app/Contents/MacOS/Blender`
- **Windows**: Blender at `C:/Program Files/Blender Foundation/Blender 5.1/blender.exe`
- **WSL**: Path translation via `wslpath -w`, Windows Blender called from Linux shell
- **Linux**: `shutil.which("blender")` fallback
- **Headless**: Auto-detected for WSL/Linux without `DISPLAY`

---

## 10. Key Constants

| Constant | Value | Source |
|----------|-------|--------|
| Tecate center lat | `32.573229` | `coords.py` |
| Tecate center lon | `-116.626536` | `coords.py` |
| Earth radius | `6,378,137.0 m` | `coords.py` |
| Street offset distance | `8.0 m` | `prism_generator.py` |
| Polygon inward shrink | `6.0 m` | `prism_generator.py` |
| Facade segment max length | `5.0 m` | `prism_generator.py` |
| Street-facing threshold | `≤ 20.0 m` | `prism_generator.py` |
| Park height (Parque Hidalgo) | `1.0 m` | `prism_generator.py` |
| Standard block height range | `7–11 m` | `prism_generator.py` |
| Camera height (cam_z) | `2.5 m` | `prism_generator.py` |
| Camera FOV (screenshots) | `75.0°` | `prism_generator.py` |
| Screenshot resolution | `1280 × 720 px` | `browser_scraper.py` |
| Facade texture slice | `512 × 256 px` | `prism_generator.py` |
| Bounding box SW | `32.521704, -116.681499` | `browser_scraper.py` |
| Bounding box NE | `32.580233, -116.510525` | `browser_scraper.py` |
