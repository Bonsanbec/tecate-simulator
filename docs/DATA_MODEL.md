# DATA_MODEL.md — Tecate Simulator: Dataset Documentation & Entity-Relationship Model

---

## 1. Overview of Datasets

| File | Size | Records | Role |
|------|------|---------|------|
| `data/tecate_osm_cache.json` | 26.1 MB | ~82,872 nodes, ~87,177 edges | Raw OSM road graph |
| `data/blocks_cache.json` | 26.2 MB | 4,239 blocks | Block polygon geometry + heights |
| `data/facades_cache.json` | 22.1 MB | 22,289 facades | Facade observation records |
| `data/panoramas_cache.json` | 1.6 MB | 3,906 panoramas | Panorama metadata |
| `data/stitching_cache.json` | 2 bytes | empty `{}` | Shift offsets (unused) |
| `data/structural_graph/road_graph.json` | 672 KB | 1,655 nodes, 1,814 edges | Processed structural graph |
| `data/structural_graph/intersections.json` | 373 KB | varies | Intersection node registry |
| `export/reconstruction_export.json` | 37 MB | 159 blocks + road graph | Full scene document for Blender |
| `export/metadata.json` | 9 MB | 15,507 provenance entries | Coverage statistics + provenance |
| `export/debug/reconstruction_diagnostics.json` | 6.7 MB | per-facade | Texturing status diagnostics |

---

## 2. tecate_osm_cache.json

**Purpose**: Raw OpenStreetMap road network data for Tecate, downloaded from the Overpass API and cached to avoid repeated network requests.

**Top-Level Structure**:
```json
{
  "nodes": { "<node_id>": { ... } },
  "edges": [ { ... }, ... ]
}
```

**Node Schema**:
```json
{
  "id": "49276523",
  "lat": 32.578789,
  "lon": -116.629913,
  "name": ""
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | OSM node ID |
| `lat` | float | WGS84 latitude |
| `lon` | float | WGS84 longitude |
| `name` | string | Street name (usually empty for mid-segment nodes) |

**Edge Schema**:
```json
{
  "id": "e_0",
  "u": "49276523",
  "v": "49276525",
  "name": "Industrial Road"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Internal edge ID (`e_N`) |
| `u` | string | Source node ID |
| `v` | string | Target node ID |
| `name` | string | Street name from OSM `highway` tag |

**Record counts**: ~82,872 nodes, ~87,177 edges  
**Generation**: Overpass API query for `highway` types: motorway, trunk, primary, secondary, tertiary, residential, unclassified, service, living_street  
**Bounding query**: `poly:"<INEGI municipal polygon>"` or fallback bbox `(32.521704,-116.681499,32.580233,-116.510525)`

---

## 3. blocks_cache.json

**Purpose**: Cached city block (manzana) polygons with their geometry, area, and height. Primary Key: `block_id`.

**Top-Level Structure**:
```json
{
  "<block_id>": { ... }
}
```

**Block ID Format**: `block_lat_{centroid_lat:.5f}_lon_{centroid_lon:.5f}`  
**Example**: `block_lat_32.57293_lon_-116.62685`

**Block Schema**:
```json
{
  "polygon": [[x0,y0], [x1,y1], ..., [x0,y0]],
  "area_sq_meters": 263.94,
  "is_external": false,
  "height_meters": 8.93,
  "roof_color": [0.431, 0.433, 0.422]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `polygon` | list[list[float,float]] | Closed CCW polygon in **local Cartesian meters** (x=East, y=North). First==Last vertex. |
| `area_sq_meters` | float | Signed area from Shoelace formula (magnitude) |
| `is_external` | bool | `true` if CCW signed area was positive (outer boundary — skipped) |
| `height_meters` | float | Computed building extrusion height (7–11m typical) |
| `roof_color` | list[float,float,float] | RGB [0–1] roof tint derived from facade texture average |

**Notes**:
- Polygons are stored in **local Cartesian coordinates** relative to Parque Hidalgo origin (32.573229°N, -116.626536°W).
- Vertex coordinates are **meters** from origin (x=East, y=North).
- Polygon vertices are subdivided at ≤5m intervals — a block polygon of 19 vertices represents the segmented facade boundaries.
- `is_external = true` blocks are the city-boundary outer cycle — excluded from reconstruction.
- **4,239 total blocks** cached.

**Sample coordinates** (first block):
```
KEY: block_lat_32.56181_lon_-116.57077
polygon: 19 vertices, first 3: 
  [5226.40, -1261.41]  → ~5.2 km East, ~1.26 km South of center
  [5227.88, -1265.06]
  [5228.33, -1269.30]
```

---

## 4. facades_cache.json

**Purpose**: Per-facade observation records linking geometry to panorama metadata. Primary Key: `facade_id`. Foreign Key: `pano_id → panoramas_cache`.

**Facade ID Format**: `{block_id}_facade_{f_idx}`  
**Example**: `block_lat_32.57293_lon_-116.62685_facade_0`

**Facade Schema** (full enriched form):
```json
{
  "pano_id": "vgFm69XT_uSvaGdjGnOIzQ",
  "block_id": "block_lat_32.57293_lon_-116.62685",
  "facade_index": 0,
  "heading": 353.38,
  "captured_heading": 353.38,
  "resolution": {
    "screenshot_width": 1280,
    "screenshot_height": 720,
    "slice_width": 512,
    "slice_height": 256
  },
  "camera_rotation_matrix": [
    [0.9933, 0.1152, 0.0],
    [-0.1152, 0.9933, 0.0],
    [0.0, 0.0, 1.0]
  ],
  "road_relation": {
    "road_name": "Calle Libertad",
    "road_distance_meters": 8.3,
    "road_edge_id": "e_42"
  },
  "facade_midpoint_local": [mx, my],
  "offset_search_point_gps": [lat, lon],
  "search_query_url": "https://maps.googleapis.com/...",
  "captured_url": "https://www.google.com/maps?layer=c&cbll=...",
  "modern_pano_id": "XxXxXx...",
  "camera_alignment_diagnostics": {
    "look_vector": [dx, dy],
    "facade_normal": [nx, ny],
    "dot_product": -0.97,
    "is_correct_side": true
  },
  "facade_segment_vertices_local": [[ax, ay], [bx, by]],
  "roof_color": [r, g, b]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `pano_id` | string | Google Street View panorama ID (22-char base64 or ARI ID) |
| `block_id` | string | FK → blocks_cache |
| `facade_index` | int | Index of this facade within its block polygon |
| `heading` | float | Computed outward normal heading in degrees (0=North, clockwise) |
| `captured_heading` | float | Actual heading used for screenshot capture |
| `resolution` | dict | Screenshot dimensions used (1280×720) and texture slice size (512×256) |
| `camera_rotation_matrix` | list[list[float]] | 3×3 yaw-only rotation matrix (heading → matrix) |
| `road_relation` | dict | Nearest road name, perpendicular distance, edge ID |
| `facade_midpoint_local` | [x,y] | Midpoint of facade segment in local Cartesian meters |
| `offset_search_point_gps` | [lat,lon] | Search point 8m outward along facade normal — used for API query |
| `search_query_url` | string | Full protobuf-encoded Overpass metadata URL |
| `captured_url` | string | Google Maps Street View URL with panorama + heading |
| `modern_pano_id` | string | Current (modern) pano_id at the location — distinct from historical |
| `camera_alignment_diagnostics` | dict | Validation: look vector vs normal dot product |
| `facade_segment_vertices_local` | [[ax,ay],[bx,by]] | Two endpoints in local Cartesian meters |
| `roof_color` | [r,g,b] | Block roof tint propagated from block |

**Record count**: 22,289 facades

---

## 5. panoramas_cache.json

**Purpose**: Panorama-level metadata. One record per unique `pano_id`. Primary Key: `pano_id`.

**Schema**:
```json
{
  "latitude": 32.57212,
  "longitude": -116.62316,
  "altitude": null,
  "date": "2008-12",
  "pitch": null,
  "roll": null,
  "projection_yaw": null,
  "pano_yaw": null,
  "road_name": "",
  "adjacent_links": [],
  "timeline": []
}
```

| Field | Type | Description |
|-------|------|-------------|
| `latitude` | float | WGS84 latitude of panorama camera position |
| `longitude` | float | WGS84 longitude of panorama camera position |
| `altitude` | float\|null | GPS altitude (meters above sea level, often null) |
| `date` | string | Capture date `"YYYY-MM"` (e.g., `"2009-09"`) |
| `pitch` | float\|null | Camera pitch angle (degrees) |
| `roll` | float\|null | Camera roll angle (normalized [-180,180]) |
| `projection_yaw` | float\|null | Panorama north offset yaw |
| `pano_yaw` | float\|null | Same as projection_yaw |
| `road_name` | string | Road name extracted from photometa |
| `adjacent_links` | list[dict] | Neighboring pano_ids and their yaw directions |
| `timeline` | list[dict] | Historical panorama states at same location |

**Record count**: 3,906 panoramas

**Date Distribution** (of 3,906 panoramas with dates):
| Period | Count | Notes |
|--------|-------|-------|
| 2008-12 | 217 | Pre-2009 capture |
| 2009-02 | 327 | Early 2009 |
| 2009-08 | 141 | Summer 2009 |
| **2009-09** | **2,468** | **Largest batch — primary target** |
| 2009-03, 2009-06 | ~21 | Scattered 2009 |
| 2015–2022 | ~658 | Modern panoramas — typically filtered/replaced by older timeline |
| 2025 | ~67 | Very recent |

**Key insight**: 79.8% of panoramas date to 2009 (or 2008-12), confirming successful historical epoch selection.

---

## 6. structural_graph/road_graph.json

**Purpose**: Processed flat road graph output from `ArchivalDataMigrator`. Used as a spatial reference for pano-to-edge assignment.

**Schema**:
```json
{
  "nodes": [
    {"id": "49276523", "x": -316.79, "y": 618.94, "lat": 32.578789, "lon": -116.629913}
  ],
  "edges": [
    {"id": "e_0", "u": "49276523", "v": "49276525", "name": "Industrial Road", "length": 15.51}
  ]
}
```

- **1,655 nodes**, **1,814 edges**
- Coordinates include both GPS and local Cartesian `x`/`y` 
- `length` is computed Euclidean distance in meters

---

## 7. reconstruction_export.json

**Purpose**: Scene document consumed by `blender_script.py` to build the 3D model.

**Top-Level Schema**:
```json
{
  "road_graph": {
    "nodes": [{"id": "...", "x": float, "y": float}],
    "edges": [{"u": "...", "v": "..."}]
  },
  "blocks": [ ... ]
}
```

**Block Entry Schema**:
```json
{
  "block_id": "block_lat_32.57293_lon_-116.62685",
  "polygon": [[x0,y0], ..., [x0,y0]],
  "height_meters": 8.93,
  "centroid": [cx, cy],
  "texture_atlas_path": "/abs/path/to/transparent_facade.png",
  "texture_atlas_filename": "transparent_facade.png",
  "facade_textures": {
    "block_lat_..._facade_0": "/abs/path/to/block_..._virtual_south_0.png",
    ...
  },
  "uv_mappings": {
    "block_lat_..._facade_0": [[u0,v0],[u1,v1],[u2,v2],[u3,v3]],
    ...
  },
  "roof_color": [0.431, 0.433, 0.422],
  "traceability": [
    {"facade_idx": 0, "source": "image"},
    {"facade_idx": 1, "source": "fallback"},
    ...
  ]
}
```

| Field | Description |
|-------|-------------|
| `polygon` | Shrunk polygon in local meters (inward 6m from road graph cycle) |
| `height_meters` | Building extrusion height |
| `centroid` | Block centroid in local meters |
| `texture_atlas_path` | Absolute path to fallback transparent PNG |
| `facade_textures` | Map: facade_id → abs path to per-facade warped PNG |
| `uv_mappings` | Map: facade_id → 4 UV corners [BL, BR, TR, TL] |
| `roof_color` | RGB float tuple for solid roof material |
| `traceability` | Per-facade source label: `"image"` or `"fallback"` |

**Current state**: 159 blocks, 15,532 total facades, 99.84% textured

---

## 8. export/metadata.json

**Purpose**: Coverage statistics and per-facade provenance data.

**Schema**:
```json
{
  "total_blocks": 159,
  "total_facades": 15532,
  "textured_facades": 15507,
  "coverage_percentage": 99.84,
  "provenance": {
    "block_lat_..._facade_0": {
      "source_pano_id": "vgFm69XT_uSvaGdjGnOIzQ",
      "source_date": "2017-07",
      "source_lat_lon": [32.57355, -116.62609],
      "facade_normal": [0.1152, -0.9933],
      "projection_parameters": {
        "cam_z": 2.5,
        "height_meters": 8.93,
        "facade_length": 2.42
      }
    }
  }
}
```

> [!NOTE]
> `source_date` in provenance shows some facades using 2017 panoramas rather than 2009. This occurs when the timeline selection logic resolves to a non-2009 pano that is nonetheless the "oldest" available at that location.

---

## 9. Entity-Relationship Diagram

```
┌─────────────────┐          ┌──────────────────────┐
│  OSM_NODE       │          │  BLOCK               │
│─────────────────│          │──────────────────────│
│ id (PK)         │          │ block_id (PK)         │
│ lat             │          │ polygon (local meters)│
│ lon             │          │ area_sq_meters        │
│ x               │          │ is_external           │
│ y               │          │ height_meters         │
│ name            │          │ roof_color            │
└────────┬────────┘          └──────────┬───────────┘
         │ n:m (via edges)             │ 1:N
┌────────▼────────┐          ┌──────────▼───────────┐
│  OSM_EDGE       │          │  FACADE              │
│─────────────────│          │──────────────────────│
│ id (PK)         │◄─────────│ facade_id (PK)       │
│ u (FK→OSM_NODE) │ road_rel │ block_id (FK→BLOCK)  │
│ v (FK→OSM_NODE) │          │ facade_index          │
│ name            │          │ heading               │
│ length          │          │ captured_heading      │
└─────────────────┘          │ facade_midpoint_local │
                             │ facade_segment_verts  │
                             │ road_relation         │
                             │ pano_id (FK)          │
                             │ camera_rotation_matrix│
                             │ camera_alignment_diag │
                             │ roof_color            │
                             └──────────┬────────────┘
                                       │ N:1
                             ┌──────────▼────────────┐
                             │  PANORAMA             │
                             │──────────────────────-│
                             │ pano_id (PK)          │
                             │ latitude              │
                             │ longitude             │
                             │ altitude              │
                             │ date                  │
                             │ pitch                 │
                             │ roll                  │
                             │ projection_yaw        │
                             │ road_name             │
                             │ adjacent_links        │
                             │ timeline              │
                             └───────────────────────┘
```

---

## 10. Export Texture Files

Located at `export/textures/`:

**Naming convention**: `{block_id}_virtual_{cardinal}_{group_idx}.png`  
**Example**: `block_lat_32.56577_lon_-116.62657_virtual_east_32.png`

- **Cardinal directions**: `north`, `south`, `east`, `west` — computed from facade outward normal
- **Group index**: Sequential index of contiguous facade groups sharing the same panorama
- **Format**: PNG, RGBA, typically 512–4096 px wide × 512 px tall (proportional to group size)
- **Content**: Perspective-warped, sky-masked facade texture from Street View screenshot

**Fallback**: `export/textures/transparent_facade.png` (512×512 fully transparent RGBA)

---

## 11. Stitching Cache

`data/stitching_cache.json` — currently `{}` (empty).

Designed to cache NCC-computed horizontal shift offsets between adjacent facade screenshots to avoid recomputation on `--reprocess` runs. Currently not populated, suggesting either all current processing already uses the virtual group approach or this is a legacy structure.
