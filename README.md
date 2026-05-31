# Tecate 2009 Historical Urban Reconstruction System

A production-grade, end-to-end modular Python pipeline designed to reconstruct a spatially coherent and temporally consistent 3D environment of downtown Tecate, Baja California, Mexico, utilizing historical Street View imagery from circa 2009.

This system leverages advanced **planar graph cycle traversal**, **unauthenticated metadata reverse-engineering**, **Playwright Chromium automation**, **homography-based perspective rectification**, and **feature-aligned template-matching similarity blending** to compile highly detailed urban blocks. 

Downstream stages output procedurally generated textured 3D assets compiled via **headless Blender automation** into a unified, high-fidelity `export/geometry.glb` asset.

---

## 1. Modular Architecture & Data Flow

The pipeline decouples network metadata acquisition and Playwright browser crawling from Downstream processing through a **dual-layer caching architecture**. If both caches are warm, the system executes E2E block reconstruction and Blender compilation in under 12 seconds entirely offline.

```mermaid
graph TD
    A[data/tecate_osm_cache.json] --> B[Cycle Traversal Engine]
    B --> C[Planar CCW Extraction & Natural Block Segmentation]
    C --> D[Safety Radius Filter: controllable via --radius]
    D --> E[Outward Normal Offsetting by 8.0 meters]
    E --> F[Offline Cache Fast-Path Optimization]
    F -- Cache Key in Stitching Cache & Pano exists --> G[Instant Bypass: maps UV directly to Stitched Panorama]
    F -- Cache Key missing / --reprocess set --> H[Load Facade png from disk/Metadata Cache]
    H --> I[Standard 512x256 Crop & Perspective Homography]
    I --> J[Face-Group Cardinal Sorting: North/South/East/West]
    J --> K[Coarse-to-Fine Template Matching: NCC TM_CCOEFF_NORMED]
    K --> L[Linear Opacity Weighted Blending]
    L --> M[Dynamic UV Mapping: u = x_i / W_final]
    M --> N[Stitched cardinal panoramas in export/textures/]
    O[Procedural Stucco Caching] --> P[Fallback Materials]
    G --> Q[Multi-Material Blender glTF Compiler]
    N --> Q
    P --> Q
    Q --> R[blender_script.py: procedural assembly]
    R --> S[tecate_reconstruction.blend]
    N --> S
    S --> T[export/geometry.glb compiled successfully]
```

---

## 2. Mathematical Design & Key Systems

### A. Natural Cycle Traversal & Dynamic Park Scaling
Instead of using hardcoded coordinate splits that damage the urban topology, blocks are extracted organically using **planar counter-clockwise (CCW) cycle traversal** of the pruned road network.
* **Low Park Elevation (Parque Hidalgo)**: To preserve the spatial prominence of the central park square, the system computes the distance from the centroid of each extracted block $B$ to the coordinate origin $(0, 0)$:
  $$\text{Dist}_{\text{center}} = \sqrt{\text{centroid}_x^2 + \text{centroid}_y^2}$$
* If $\text{Dist}_{\text{center}} \le 50.0\text{ meters}$, the block is dynamically identified as **Parque Hidalgo** and assigned a low-extrusion height of **1.0 meter**.
* All other surrounding blocks receive standard, multi-story vertical heights between 7.0 and 11.0 meters.

### B. Outward-Facing Normal Coordinate Offset
To position the camera in the street looking directly at a building's facade, the system computes the segment's outward normal vector $N = (N_x, N_y)$ and offsets the search point $S$ by exactly 8.0 meters:
$$S_x = mx + 8.0 \times N_x, \quad S_y = my + 8.0 \times N_y$$
This coordinates pair is translated into GPS `(lat, lon)` to query the Street View API at the exact point where a vehicle would have passed.

### C. Coarse-to-Fine Normalized Cross-Correlation (NCC)
Adjacent 5-meter facade screenshots overlap due to the camera's movement along the street. To merge them seamlessly into a single panorama, the system dynamically solves the horizontal translation shift $s$ between adjacent slices using **coarse-to-fine Normalized Cross-Correlation (NCC)** on grayscale conversions:
1. **Coarse Search**: Slide `img2` horizontally over `img1` checking shifts $s \in [100, 450]$ in steps of 5 pixels. Overlapping grayscale strips are correlated:
   $$\text{Score}(s) = \frac{\sum (T - \bar{T})(S_s - \bar{S}_s)}{\sqrt{\sum(T - \bar{T})^2 \sum(S_s - \bar{S}_s)^2}}$$
   where $T$ represents the template strip of `img1` ($s$ to $512$) and $S_s$ is the overlapping search strip of `img2` ($0$ to $512-s$).
2. **Fine Search**: Refine the search at 1-pixel intervals within a $\pm 4$ pixel window around the coarse peak. If the correlation score falls below $0.35$, the system falls back to a nominal shift of $350$ pixels.

### D. Seamless Linear Opacity Blending
To erase harsh vertical boundaries and storefront duplication artifacts, a weighted blending mask $M(x)$ is evaluated column-wise for each image $i$ in a face's sequential chain:
* **Left Overlap Region** (width $W_{\text{left}} = 512 - s_{i-1}$):
  $$M(x) = \frac{x}{W_{\text{left}}}, \quad x \in [0, W_{\text{left}}]$$
* **Right Overlap Region** (width $W_{\text{right}} = 512 - s_i$):
  $$M(x) = 1.0 - \frac{x - (512 - W_{\text{right}})}{W_{\text{right}}}, \quad x \in [512 - W_{\text{right}}, 512]$$
* **Central Region**: $M(x) = 1.0$

Overlapping pixels are accumulated in a float32 canvas and normalized by the cumulative sum of weights:
$$\text{Pixel}_{\text{blended}} = \frac{\sum_i \text{Pixel}_{i} \times M_i(x)}{\sum_i M_i(x)}$$
This guarantees a smooth transition where the sum of weights is $1.0$ at every column, blending storefront details seamlessly.

### E. Dynamic UV Mapping Coordinates
Because the total width of the stitched panorama $W_{\text{final}}$ varies dynamically based on the shift variables $s_j$:
$$W_{\text{final}} = \sum_{j=1}^{K-1} s_j + 512$$
The UV coordinates for each segment $i$ are dynamically scaled to align perfectly with its column region $[x_i, x_i + 512]$:
* **Bottom-Left**: $\left[\frac{x_i}{W_{\text{final}}}, 0.0\right]$
* **Bottom-Right**: $\left[\frac{x_i + 512}{W_{\text{final}}}, 0.0\right]$
* **Top-Right**: $\left[\frac{x_i + 512}{W_{\text{final}}}, 1.0\right]$
* **Top-Left**: $\left[\frac{x_i}{W_{\text{final}}}, 1.0\right]$

---

## 3. Directory Structure & Workspace Layout

The repository is organized as follows:

```
tecate-simulator/
├── data/                             # GIS graphs and cache footprints
│   ├── tecate_osm_cache.json         # Static OSM road graph data for Tecate
│   ├── facade_metadata_cache.json    # Resolved facade metadata (coordinates, pano_id, date)
│   ├── stitching_cache.json          # Horizontal stitching offsets and widths
│   └── screenshots/
│       └── facades/                  # Raw downloaded screenshots (block_X_facade_Y.png)
├── export/                           # Procedural compiler exports
│   ├── geometry.glb                  # Fully compiled and textured 3D environment
│   ├── reconstruction_export.json    # Compiled block vertices, materials, and UV data
│   ├── metadata.json                 # Coverage rates and asset provenance data
│   ├── textures/
│   │   ├── stucco_facade.png         # Fallback stucco texture for unexposed quads
│   │   └── {block_id}_{cardinal}_facade.png  # Similarity-blended storefront maps
│   └── debug/
│       ├── global_observation_map.png # Real-time light diagnostic dashboard map
│       └── reconstruction_diagnostics.json # Face-level texturing status logs
├── src/                              # Main pipeline source package
│   ├── main.py                       # Pipeline master orchestrator CLI entrypoint
│   ├── core_io/                      # UTM projection conversion and file systems
│   │   ├── coords.py
│   │   └── io_manager.py
│   ├── data_acquisition/             # API clients and Playwright screenshot scraper
│   │   ├── browser_scraper.py
│   │   └── sv_downloader.py
│   ├── gis_graph/                    # OSM road graph builders
│   │   └── graph_builder.py
│   ├── reconstruction/               # Main block compiler & template-matching blending
│   │   └── prism_generator.py
│   ├── temporal_filter/              # Historical time selectors
│   │   └── classifier.py
│   └── visualization/                # Observation maps
│       └── coverage.py
├── blender_script.py                 # Headless / GUI Blender geometry compiler (bpy)
├── requirements.txt                  # Python dependencies
└── README.md                         # This file (documentation hub)
```

---

## 4. Installation & Setup

The system requires **Python 3.10+** and a local installation of **Blender** (registered in your system path).

```bash
# 1. Clone the repository and navigate
cd tecate-simulator

# 2. Initialize virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Upgrade pip and install core requirements
pip install -upgraded pip
pip install -r requirements.txt

# 4. Install Playwright Chromium browser binaries
./venv/bin/playwright install chromium
```

---

## 5. Pipeline CLI Execution Runbook

The master script `src/main.py` orchestrates the entire GIS build, Playwright crawling, cropping, stitching, and Blender compilation:

| CLI Option | Default Value | Description |
| :--- | :--- | :--- |
| `--headless` | `False` | Run Playwright in headless mode (headless is highly recommended for server runs). |
| `--reprocess` | `False` | Forces recalculation of cropping, homography warping, and similarity stitching on cached disk screenshots without querying the network. |
| `--radius` | `-1` | Safety radius from central origin (Parque Hidalgo) in meters. Set to `-1` to process the entire city of Tecate. |

### Running the Recovery and Reconstruction (Headless)
Runs the entire pipeline using the headless crawler, performing offline homography and automatic metadata recovery for pre-downloaded images:
```bash
PYTHONPATH=. ./venv/bin/python src/main.py --headless
```

### Full Reprocessing of Cached Screenshots
Regenerates all horizontal panoramas and UV layouts directly from existing screenshots without firing any browser queries:
```bash
PYTHONPATH=. ./venv/bin/python src/main.py --headless --reprocess
```

### Process Central Area only (350-meter radius)
```bash
PYTHONPATH=. ./venv/bin/python src/main.py --headless --radius 350
```

---

## 6. Real-Time Auto-Saving & Unified High-Fidelity Caching

The reconstructor implements robust resilience features to prevent any data loss and maintain a unified, enriched geospatial knowledge base:
* **SIGINT/KeyboardInterrupt Handler**: If a run is interrupted via `Ctrl+C`, the system catches the signal, gracefully closes the active Playwright session, immediately serializes both `facade_metadata_cache.json` and `stitching_cache.json` to disk, and exits safely.
* **Offline Metadata Recovery**: If screenshot images are present in `data/screenshots/facades/` but are missing from `facade_metadata_cache.json` (due to a prior crash or interruption), the system triggers a recovery fast-path. It uses the static coordinates of the facade to fetch its metadata using rapid GET queries, maps it to the file, and runs standard homography warping on the existing image **without opening Playwright or downloading any screenshots**.
* **Unified Enriched Schema**: The system aggregates all parameters from Point 1 (Indispensables) and Point 2 (Desirables) into a single unified JSON object under `data/facade_metadata_cache.json` for every facade slice:

```json
{
  "pano_id": "-NXu3HuDlMVBf9Y46OE9fQ",
  "latitude": 32.57212712658536,
  "longitude": -116.6231560210298,
  "altitude": 522.06,
  "date": "2008-12",
  "heading": 84.23546955855736,
  "pitch": 10.33,
  "roll": -0.95,
  "hfov": null,
  "vfov": null,
  "focal_length_px": null,
  "resolution": {
    "screenshot_width": 1280,
    "screenshot_height": 720,
    "slice_width": 512,
    "slice_height": 256
  },
  "optical_center": null,
  "intrinsic_matrix": null,
  "camera_height_m": null,
  "camera_position_local": [317.07, -122.66, null],
  "camera_rotation_matrix": [
    [0.100, -0.995, 0.0],
    [0.995, 0.100, 0.0],
    [0.0, 0.0, 1.0]
  ],
  "road_relation": {
    "road_name": "Boulevard Defensores de Baja California",
    "road_distance_meters": 7.36,
    "road_edge_id": "e_234"
  },
  "distance_to_center_m": 391.0,
  "facade_midpoint_local": [-636.56, -832.87],
  "offset_search_point_local": [-628.65, -834.02],
  "offset_search_point_gps": [32.56573, -116.63323],
  "search_query_url": "https://maps.googleapis.com/maps/api/js/GeoPhotoService.SingleImageSearch?pb=...",
  "captured_url": "https://www.google.com/maps?layer=c&cbll=...",
  "modern_pano_id": "uZbChf3zuqASbI9Y47B3sg",
  "camera_alignment_diagnostics": {
    "look_vector": [-2.95, -1.29],
    "facade_normal": [0.99, -0.14],
    "dot_product": -2.74,
    "is_correct_side": true
  },
  "image_filename": "block_5_facade_1409.png",
  "block_id": "block_5",
  "facade_index": 1409,
  "facade_segment_vertices_local": [
    [-639.11, -832.52],
    [-634.01, -833.22]
  ],
  "facade_normal_vector": [0.99, -0.14],
  "block_polygon_vertices_raw_local": [
    [-645.11, -838.52],
    [-628.01, -839.22],
    [...]
  ],
  "block_polygon_vertices_shrunk_local": [
    [-639.11, -832.52],
    [-634.01, -833.22],
    [...]
  ],
  "normal_offset_distance_m": 8.0,
  "block_shrink_distance_m": 6.0
}
```

* **Automatic Cache Migration**: At instantiation, `migrate_metadata_cache()` scans `data/facade_metadata_cache.json` and automatically migrates any legacy entries to the unified high-fidelity schema deterministically without modifying already collected raw values.

---

## 7. Blender Integration & Unified 3D compilation

The master script automatically triggers **Blender** background processing using `blender_script.py`. 

1. **Procedural Geometry Compiler**: Reads `export/reconstruction_export.json` containing vertices and faces.
2. **Texturing & Material Slotting**: Binds cardinally stitched horizontal panoramas to vertical storefront quads and maps exact UV coordinates.
3. **Stucco Fallback Shader**: Applies a warm, procedurally bump-mapped beige stucco material to non-street-facing walls.
4. **Dynamic Roof Tinting**: Calculates the average RGB value of all storefront textures on a block and applies it as a solid color to the block's roof geometry.
5. **Illumination & Camera Layout**: Creates a sun lamp and top-down ortho camera.
6. **Unified GLB Asset Compilation**: Saves the project as `tecate_reconstruction.blend` and exports the fully textured, self-contained scene to **`export/geometry.glb`** (~260MB).

To open the compiled scene visually in Blender:
```bash
blender tecate_reconstruction.blend
```
*(Toggle viewport shading to **Material Preview** or **Rendered** to see the blended storefront storefronts).*
