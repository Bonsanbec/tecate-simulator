# Tecate 2009 Historical Urban Reconstruction System

A production-grade, end-to-end modular Python repository designed to reconstruct a spatially coherent and temporally consistent 3D approximation of Tecate, Baja California, Mexico, using historical Street View imagery from circa 2009.

**Mandatory Override Applied**: This system operates *without* official Google developer APIs or credentials. It implements a browser-driven scraping and reverse-engineering pipeline using **Playwright Chromium automation** and public unauthenticated backend crawlers to scrape, stitch, and archive Street View nodes locally. Downstream computer vision modules consume *exclusively* from this local disk cache.

---

## 1. Modular Architecture & Data Flow

The scraping subsystem decouples coordinate sampling from downstream triangulation. Downstream stages consume only from the locally archived cash folder footprint:

```mermaid
graph TD
    A[OSM Graph Nodes] --> B[data_acquisition: GoogleStreetViewScraper]
    B --> C[Playwright Chromium Session]
    C --> D[Request Interceptor: Tiles & JSON Metadata]
    B --> E[Public Backend Requests: cbk?output=json & cbk?output=tile]
    E --> F[Graph Traversal Engine & Timeline Parser]
    F --> G[Stitched Equirectangular Panoramas & timelines]
    G --> H[Local Cache Archive: data/raw_scraped/{pano_id}/]
    I[data_acquisition: Procedural Cache Generator] --> H
    H --> J[image_alignment: VP Correction & Anchoring]
    J --> K[temporal_filter: Visual Classifier & MRF Solver]
    K --> L[Pruned Modern Nodes]
    K --> M[Accepted 2009 Nodes]
    M --> N[sfm: SIFT/ORB corridor Triangulation]
    N --> O[Global Point Cloud & Extruded Block Footprints]
    M --> P[texturing: Facade projections & Atlas PNG stitching]
    O --> Q[blender_export: Structured IR JSON]
    P --> Q
    Q --> R[blender_script.py: procedural assembly]
    R --> S[tecate_reconstruction.blend]
```

---

## 2. Directory Structure & Local Cache Footprint

The repository is organized as follows:

```
tecate-simulator/
├── data/                         # Cached GIS data and fallback models
│   ├── tecate_osm_cache.json     # Pre-cached central Tecate OSM road network
│   └── raw_scraped/              # Local Archival Cache Directory (Scraper Outputs)
│       └── {pano_id}/            # Unique folder per Street View node
│           ├── metadata.json     # Node coordinates, capture date, connectivity links
│           ├── panorama.png      # Seamless stitched horizontal panorama (2560x640)
│           └── tiles/            # Raw intercepted tile files (tile_z3_x_y.png)
├── export/                       # Compiled 3D assets and scene databases
│   ├── textures/                 # Stitched block texture atlases (.png)
│   └── reconstruction_export.json# Self-contained 3D reconstruction JSON
├── src/                          # Modular source code package
│   ├── __init__.py
│   ├── main.py                   # Master orchestration CLI entrypoint
│   ├── core_io/                  # Bidirectional UTM coordinate projection and file managers
│   │   ├── coords.py
│   │   └── io_manager.py
│   ├── data_acquisition/         # Google Street View Scraper & Procedural Cache Generator
│   │   ├── browser_scraper.py
│   │   └── sv_procedural.py
│   ├── gis_graph/                # OSM MultiGraph processor & virtual camera interpolator
│   │   └── graph_builder.py
│   ├── image_alignment/          # Geospatial anchoring and line-based Vanishing Point (VP) tuner
│   │   └── aligner.py
│   ├── temporal_filter/          # Visual degradation analyzer and Graph Diffusion MRF Solver
│   │   └── classifier.py
│   ├── sfm/                      # ORB/SIFT descriptors, Essential RANSAC, & Triangulation
│   │   └── sfm_lite.py
│   ├── block_modeling/           # Planar cycle basis manzana builders
│   │   └── block_builder.py
│   └── texturing/                # Facade projection, perspective crops, & atlas stitchers
│       └── texture_generator.py
├── tests/                        # Consolidation test suite
│   └── test_reconstruction.py
├── blender_script.py             # Headless / GUI Blender import automate script (bpy)
├── scraper_legal_limits.md       # Scraping reverse engineering and legal limits document
├── requirements.txt              # Python requirements
└── README.md                     # Documentation & setup instructions
```

---

## 3. Installation & Setup Instructions

The project requires Python 3.10+ and standard dependencies. It is recommended to install them in an isolated virtual environment:

```bash
# 1. Clone the repository and navigate
cd tecate-simulator

# 2. Set up local virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Upgrade package installer and install requirements
pip install --upgrade pip
pip install -r requirements.txt

# 4. Install Playwright Chromium browser binaries
./venv/bin/playwright install chromium
```

---

## 4. Running the Pipeline

The master CLI orchestrates the scraping and reconstruction steps:

### Option A: Simulated/Procedural Cache Mode (100% Offline, Recommended for instant testing)
Generates high-fidelity simulated Street View panoramas, structures their connections, and writes simulated nodes to cache. Downstream modules load their assets *strictly and exclusively* from this cache:
```bash
PYTHONPATH=. ./venv/bin/python src/main.py --mode simulated
```

### Option B: Real Web Scraping Mode
Launches Playwright Chromium session, intercepts unauthenticated background network traffic to trace tile coordinates, stitches them, crawler connected streets BFS-wise near Tecate plaza, and caches everything locally:
```bash
PYTHONPATH=. ./venv/bin/python src/main.py --mode real
```

### Run Unit Tests:
Validate the entire codebase's mathematical consistency, including unauthenticated metadata parsers, timeline extraction, and procedural cache generators (9 unit tests):
```bash
./venv/bin/pytest tests/
```

---

## 5. Blender 3D Scene Assembly

The exported intermediate format (`export/reconstruction_export.json`) is fully self-contained. To automatically build the 3D model, materials, and textures, run `blender_script.py` inside Blender:

```bash
# 1. Run headlessly (Fastest, saves tecate_reconstruction.blend directly)
blender --background --python blender_script.py -- --import export/reconstruction_export.json

# 2. Run in standard GUI mode (Builds the city inside the interactive window)
blender --python blender_script.py -- --import export/reconstruction_export.json
```

**Inside Blender**:
1. Open the generated `tecate_reconstruction.blend` file.
2. Toggle the viewport shading mode to **Material Preview** or **Rendered** (Eevee/Cycles).
3. The road network wireframe, the SIFT-extracted sparse 3D point cloud with points colored in vertex RGB, and the fully textured extruded 3D block facades mapped to their texture atlases are fully visible and editable!

---

## 7. Data Assumptions, Limitations, & Failure Mitigations

For detailed reverse-engineering principles, legal limits, IP rate throttling, CAPTCHAs, and a detailed step-by-step troubleshooting runbook on how to adjust Playwright selectors if Google modifies frontend web classes, please refer to the dedicated file **[`scraper_legal_limits.md`](file:///Users/hakkindavid/Documents/GitHub/tecate-simulator/scraper_legal_limits.md)**.
