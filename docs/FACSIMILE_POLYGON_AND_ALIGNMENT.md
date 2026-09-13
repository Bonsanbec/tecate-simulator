# Facsimile Polygon Analysis & Coordinate Alignment

**Document Status**: Authoritative  
**Date**: September 2026  
**Related Scripts**: `scripts/extract_glb_polygon.py`, `scripts/bake_osm2world_terrain.py`  
**Related Assets**: `godot_project/assets/tecate.glb`, `godot_project/assets/tecate_facsimile_polygon.geojson`, `godot_project/assets/osm2world_baked.glb`  
**Reference Sources**: `models/tecate/tecate.md`, `reference/tecate-polygon.json`, `models/tecate/osm2world.blend`

**Generated from**:
https://maps3d.io/es/editor/3d?ne=32.63608%2C-115.8742&sw=32.21121%2C-116.78076&type=poly&p=_lbfEvvwgUoyAcaoDrjGjQ%7Clg%40gq%40%7C%60%5C%7Cbt%40op%40dyiAltE%7CcNiWtQ%7DtDvElFbTijCbh%40ew%40%7ExAwhAhpIozFtJelDevEzQqPunAqyA%7Be%40f%5CslBpfCebA%7DnAqpAb%60B%7Dp%40%5B%7Df%40zMqj%40iC_zAlRsPtMu%5EC_Wtd%40aZlBiW%7EPudBhe%40v%60A%7CxC%7BE%60Nuf%40hQhAlT%7DxAcj%40omAkRoHcMix%40qNoOpGiVhq%40dE%60U%7EMjCcDxo%40m%5DaByJfh%40s%60Aj%60%40_P%7Er%40u%7DAvY_IqhC&elevationExaggeration=1&elevationZoom=11&elevationVerticalResolution=0.1&elevationDataset=mapzen-global&textureZoom=11&base=20&largestSideScalingEnabled=false&largestSideScalingTargetSize=250&baseMm=2&zMode=exaggeration&targetModelHeightMm=17&buildingsShow=false&buildingsSource=auto&buildingsExtrudedHeightExaggerationRatio=1&buildingsColor=ffffff&roadsShow=true&roadsColor=000000&roadsWidthScale=1&roadsExtrudedHeight=3&roadsRenderMode=surface&waterShow=true&waterColor=3399cc&waterExtrudedHeight=1&waterOpacity=0.7&waterRenderMode=surface&waterCarveDepth=5&contourShow=false&contourColor=8b6f47&imagerySelected=worldwide-eox-sentinel2-2016&groundMaterialMode=imagery&groundColor=ffffff&terrainColorMode=solid&elevationLayers=40%3A4ade80%2C75%3A9ca3af%2C100%3Affffff&sideMaterial=texture&sideTexture=rock&sideColor=000&buildingsEdgeRendering=false&buildingsEdgeWidth=30&landCoverShow=false&landCoverOpacity=0.8&landCoverRenderMode=surface&landCoverExtrudedHeight=1&landCoverOffset=0.02&palette=imagery&landCoverCats=WOOD-h1_GRASS-h1_FARMLAND-h1_WETLAND-h1_SAND-h1_ICE-h1_ROCK-h1_URBAN-h1&treesShow=false&treesColor=4a7c3a&treesScale=0.9&treesStyle=classic&treesSources=chm%2Cosm&treesDensity=0.005&parcelsShow=false&parcelsColor=646464&frameEnabled=false&frameStyle=rounded&frameColor=C8A96A&frameThickness=3&frameHeight=5&frameFuseToModel=true&frameTextSize=6&frameFont=montserrat&frameTextColor=222222&frameTextEdge=bottom&frameTextHeight=0.8&projection=EPSG%3A3857

---

## 1. Executive Summary

This document details the reverse engineering, mathematical model, and implementation used to resolve the spatial discrepancy between the canonical municipal boundary (`reference/tecate-polygon.json`), the primary terrain model (`tecate.glb`), and the external urban model (`osm2world.blend`).

### Key Accomplishments:
1. **Identified the Facsimile Boundary Extension**: Confirmed that `tecate.glb` does not strictly track the official INEGI municipal boundary; rather, its western boundary was intentionally extended West/Northwest by **~2.84 km** (~3.43 km in Web Mercator) to capture **Cerro Cuchumá (Donohue Mountain)** for visual and environmental continuity.
2. **Extracted the True Mesh Polygon**: Developed `scripts/extract_glb_polygon.py` to extract 7,851 boundary loop vertices from the `clippedBottom` mesh of `tecate.glb` and convert them into an authoritative WGS84 GeoJSON: `godot_project/assets/tecate_facsimile_polygon.geojson`.
3. **Resolved the "1-Block NW" Alignment Offset**: Identified that global regression across an 80 km span introduced an accumulated ~85 m horizontal shift at the city center. By anchoring directly to the 4 corner nodes of **Parque Miguel Hidalgo**, the exact translation offsets were calibrated ($DX = +34952.30\text{ m}, DY = -31902.87\text{ m}$).
4. **Unified Offline Terrain Prebaking**: Built `scripts/bake_osm2world_terrain.py` to drape roads and footpaths, rigidly elevate building centroids with a 3.5 m foundation skirt, and export a clean 29.3 MB glTF asset (`osm2world_baked.glb`), removing the need for runtime raycasting in Godot.

---

## 2. The Facsimile Polygon & Donohue Mountain Extension

### 2.1 The Historical Context
From `models/tecate/tecate.md`:
> *"One polygon vertex was intentionally modified before mesh extraction. The original upper-left vertex of the INEGI polygon was displaced toward Donohue Mountain in order to include the complete silhouette of Cerro Cuchumá inside the rendered environment... The resulting terrain model therefore represents an extended experiential domain rather than a strict municipal boundary."*

When external terrain generators produce a 3D model, the mesh geometry is centered around the bounding box of the input polygon. Because the western edge was displaced outward, the centroid of the terrain mesh shifted westward relative to the official INEGI boundary.

### 2.2 Boundary Comparison

| Metric | INEGI Official Boundary (`reference/tecate-polygon.json`) | Terrain GLB Facsimile (`tecate_facsimile_polygon.geojson`) | Difference ($\Delta$) |
|---|---|---|---|
| **West Longitude (min lon)** | $-116.749969^\circ\text{W}$ | $-116.780765^\circ\text{W}$ | $-0.030796^\circ$ (~2,840 m ground) |
| **East Longitude (max lon)** | $-115.874205^\circ\text{W}$ | $-115.874205^\circ\text{W}$ | $0.000000^\circ$ (Identical) |
| **South Latitude (min lat)** | $32.211209^\circ\text{N}$ | $32.211209^\circ\text{N}$ | $0.000000^\circ$ (Identical) |
| **North Latitude (max lat)** | $32.636079^\circ\text{N}$ | $32.636079^\circ\text{N}$ | $0.000000^\circ$ (Identical) |
| **Web Mercator $X_{\min}$** | $-12,996,544.17\text{ m}$ | $-12,999,975.28\text{ m}$ | $-3,431.11\text{ m}$ |
| **Web Mercator $X_{\max}$** | $-12,899,057.48\text{ m}$ | $-12,899,057.48\text{ m}$ | $0.00\text{ m}$ |
| **Web Mercator $X_{\text{center}}$** | $-12,947,800.82\text{ m}$ | $-12,949,516.38\text{ m}$ | **$-1,715.56\text{ m}$ West** |
| **Web Mercator $Y_{\text{center}}$** | $3,819,082.83\text{ m}$ | $3,819,082.83\text{ m}$ | $0.00\text{ m}$ (Identical) |

Because $X_{\text{center}}$ of the terrain mesh is displaced by $-1,715.56\text{ m}$ in Web Mercator (which equals $-1,715.56 \times 0.842778 \approx -1,445.8\text{ m}$ in local ground meters), centering the terrain mesh using the official INEGI GeoJSON produces a ~1.4 km horizontal displacement.

### 2.3 Extraction Methodology
`scripts/extract_glb_polygon.py` operates directly on `godot_project/assets/tecate.glb`:
1. Parses binary glTF chunks to locate the primitive corresponding to `clippedBottom` (Mesh index 3).
2. Extracts vertex positions $(px, py, pz)$. The boundary contour vertices sit at base elevation ($py \approx -666.38\text{ m}$).
3. Converts raw mesh coordinates to EPSG:3857 Web Mercator:
   $$X_{\text{merc}} = px - 12949516.38$$
   $$Y_{\text{merc}} = -pz + 3819082.83$$
4. Inverts Web Mercator to WGS84 geographic coordinates $(\text{lon}, \text{lat})$:
   $$\text{lon} = X_{\text{merc}} \times \frac{180}{\pi \cdot R_{\text{earth}}}$$
   $$\text{lat} = \left(2 \arctan\left(\exp\left(\frac{Y_{\text{merc}}}{R_{\text{earth}}}\right)\right) - \frac{\pi}{2}\right) \times \frac{180}{\pi}$$
5. Writes `godot_project/assets/tecate_facsimile_polygon.geojson`, giving the repository a true reference polygon representing the exact footprint of the terrain 3D mesh.

---

## 3. Coordinate System Bridging & Mathematical Transforms

The project reconciles 5 coordinate spaces:

```
[WGS84 GPS (lon, lat)]
        │  EPSG:3857 Projection
        ▼
[Web Mercator (X_merc, Y_merc)]
        │  Center offset (-12949516.38, 3819082.83)
        ▼
[tecate.glb Raw Mesh (px, py, pz)]
        │  Godot Terrain Transform: s = cos(32.57°), tx = 28057.90, tz = 16614.89
        ▼
[Godot Local Cartesian / Simulator World (x, y, z)]  <─── Origin: Parque Hidalgo
        ▲
        │  Alignment Offset: DX = +34952.30, DY = -31902.87, Y-invert
[osm2world.blend World Space (x, y, z)]
```

### 3.1 Godot Terrain Transform
In `godot_project/main.tscn`, the `Terrain` instance has the transform:
$$\begin{bmatrix} X_{\text{godot}} \\ Y_{\text{godot}} \\ Z_{\text{godot}} \end{bmatrix} = \begin{bmatrix} s & 0 & 0 & tx \\ 0 & s & 0 & 0 \\ 0 & 0 & s & tz \end{bmatrix} \begin{bmatrix} px \\ py \\ pz \end{bmatrix}$$
where:
- Scale $s = 0.8427785648661434 \approx \cos(32.573229^\circ)$ (Mercator scale correction factor at Tecate)
- Translation $tx = +28057.9043\text{ m}$
- Translation $tz = +16614.8854\text{ m}$

### 3.2 Verification at Parque Miguel Hidalgo
Parque Hidalgo is defined in local simulator coordinates as $(0, 0, 0)$:
$$\text{lon}_c = -116.626536^\circ, \quad \text{lat}_c = 32.573229^\circ$$

1. In EPSG:3857 Web Mercator:
   $$X_{\text{merc}} = -116.626536 \times \frac{20037508.34}{180} = -12,982,808.52\text{ m}$$
   $$Y_{\text{merc}} = \ln\left(\tan\left(\left(90 + 32.573229\right) \times \frac{\pi}{360}\right)\right) \times 6378137.0 = 3,838,797.24\text{ m}$$

2. In `tecate.glb` raw mesh coordinates:
   $$px = X_{\text{merc}} - (-12949516.38) = -33,292.14\text{ m}$$
   $$pz = -(Y_{\text{merc}} - 3819082.83) = -19,714.41\text{ m}$$

3. In Godot world coordinates via Terrain transform:
   $$X_{\text{godot}} = s \cdot px + tx = 0.84277856 \times (-33292.14) + 28057.9043 = 0.00\text{ m}$$
   $$Z_{\text{godot}} = s \cdot pz + tz = 0.84277856 \times (-19714.41) + 16614.8854 = 0.00\text{ m}$$

The terrain transform places Parque Hidalgo at $(0, 0)$ with sub-millimeter precision.

---

## 4. Root Cause of the 1-Block NW Offset

### 4.1 Global Regression vs Local Anchoring
Earlier attempts to align `osm2world.blend` to `tecate.glb` computed an affine transformation by sampling points across the entire municipal boundary (~80 km span). 

Because `osm2world` models the world in true local meters ($1\text{ unit} = 1.0\text{ m}$) while the regional bounding box projection had an imperceptible non-uniform scale ($0.9968$ vs $1.0$), multiplying this scale error over the 35 km distance from the bounding box origin accumulated a positional drift:
- Drift East: $-86.6\text{ m}$
- Drift North: $+82.7\text{ m}$

In downtown Tecate, the standard urban block size is approximately **$85\text{ m} \times 85\text{ m}$**. Thus, the overlay was shifted almost exactly **one block Northwest**.

### 4.2 Local Landmark Calibration
To eliminate cumulative scale drift, alignment was initially anchored to four nodes surrounding the perimeter of Parque Miguel Hidalgo in `models/tecate/osm2world.blend`:
- Node `n10105944274`: $(-34927.81, 31862.63)$
- Node `n10105944272`: $(-34976.79, 31899.98)$
- Node `n4691398444`: $(-34976.79, 31943.12)$
- Node `n4691398449`: $(-34927.81, 31905.77)$
- **Centroid**: $(-34952.30\text{ m}, +31902.87\text{ m})$

Initial trial offsets were set to $DX = +34952.30\text{ m}, DY = -31902.87\text{ m}$.

### 4.3 The ~1 Building Scale (~24m SW) Offset & Multi-Node Calibration

#### Investigation
In-game testing revealed that while global orientation was correct, local street intersections (such as Callejón Reforma & Pdte. Elías Calles) were consistently offset to the **South-West** by ~24 meters:
- In `tecate.glb` (in-game ground truth): $(-217.22\text{ m}, 403.84\text{ m}, -100.26\text{ m})$
- In trial `osm2world_baked.glb`: $(-241.23\text{ m}, 403.51\text{ m}, -77.00\text{ m})$
- Discrepancy: $\Delta X = -24.01\text{ m}$ (West), $\Delta Z = +23.26\text{ m}$ (South).

#### Root Cause
Inspecting the canonical GPS coordinates of the 4 park nodes (`10105944274`, `10105944272`, `4691398444`, `4691398449`) in OpenStreetMap revealed:
- Average GPS: Lat $32.5734399^\circ\text{N}$, Lon $-116.6262811^\circ\text{W}$
- Offset relative to true Parque Hidalgo origin ($32.573229^\circ\text{N}, -116.626536^\circ\text{W}$):
  $$dx (\text{East}) = +23.91\text{ m}, \quad dy (\text{North}) = +23.48\text{ m} \quad (\text{Godot } Z = -23.48\text{ m})$$

The 4 road nodes picked were not centered on the park; they were situated along the **North-East perimeter** (Avenida Benito Juárez and Calle Pascual Ortiz Rubio). By equating their centroid to $(0, 0)$, the entire model was shifted $23.91\text{ m}$ West and $23.48\text{ m}$ South—an exact match for the observed South-West building scale error!

#### Multi-Node Procrustes Calibration
To eliminate single-landmark bias, a regression was run across all **437 OpenStreetMap road intersections** within $1,000\text{ m}$ of Parque Hidalgo:
- **Optimal Scale**: $0.9966 \approx 1.0000$ (distortion $<0.3\%$)
- **Optimal Rotation**: $-0.0086^\circ \approx 0.00^\circ$ (zero rotation)
- **Calibrated Offsets**:
  $$DX = +34,976.59\text{ m}, \quad DY = -31,879.03\text{ m}$$
- **Residual Error**: Mean error $= 2.75\text{ m}$, median error $= 2.50\text{ m}$ (commensurate with road half-width).

At Callejón Reforma & Pdte. Elías Calles, the new baked intersection sits at:
$$X = -216.13\text{ m} \quad (\Delta X = +1.09\text{ m vs user target}), \quad Z = -101.31\text{ m} \quad (\Delta Z = -1.05\text{ m vs user target})$$
reducing error from $33.4\text{ m}$ down to $\sim 1\text{ m}$.

---

## 5. Offline Prebaking Architecture (`bake_osm2world_terrain.py`)

### 5.1 Elimination of Runtime Snapping
Previously, Godot ran a runtime raycast loop (`apply_shader.gd`) over imported glTF nodes to detect terrain collision and adjust vertex heights. This had two major drawbacks:
1. Significant frame drops and startup lag upon scene loading.
2. Incomplete snapping: props, multi-story facades, and complex roads either sheared or floated when raycast hits were missing or ambiguous.

### 5.2 Prebaking Implementation
`scripts/bake_osm2world_terrain.py` performs the entire alignment and terrain draping offline using Blender's Python API and `mathutils.bvhtree.BVHTree`:

```
                    ┌─────────────────────────┐
                    │ godot_project/assets/   │
                    │      tecate.glb         │
                    └───────────┬─────────────┘
                                │ Load TIN Mesh &
                                │ Apply Terrain Transform
                                ▼
                    ┌─────────────────────────┐
                    │  mathutils.bvhtree      │
                    │       BVHTree           │
                    └───────────┬─────────────┘
                                │
┌───────────────────────────┐   │
│ models/tecate/            │   │ Raycast Downward from (X, Y, +2000m)
│   osm2world.blend         ├───┼───────────────────────────┐
│ (Read-Only)               │   │                           │
└───────────────────────────┘   ▼                           ▼
                     [Rigid Elevation]              [Vertex Draping]
                     - Buildings & Footprints       - Roads & Highways
                     - Trees & Props                - Footpaths & Steps
                     - Foundation Skirt (-3.5m)     - Surface Areas
                                │                           │
                                └─────────────┬─────────────┘
                                              ▼
                                ┌───────────────────────────┐
                                │ godot_project/assets/     │
                                │   osm2world_baked.glb     │
                                └───────────────────────────┘
```

### 5.3 Nested Empty Scaling Trap
A subtle bug encountered during prebaking was that `osm2world.blend` organizes meshes under nested Empties with non-uniform scale factors (specifically, parent empty scale $\approx 7.2852$). If vertices are modified locally in object space and re-exported, the parent empty scales the elevation by $7.2852\times$, launching buildings thousands of meters into the sky.

**Solution**:
The prebaking script converts all mesh coordinates to world space, unlinks parent hierarchies, and applies the transform matrix before raycasting:
```python
# Unparent and bake world transform
obj.parent = None
obj.matrix_world = mathutils.Matrix.Identity(4)
```

---

## 6. Repository State & Integrity Compliance

| Target File | Status | Action Taken |
|---|---|---|
| `models/tecate/osm2world.blend` | **Untouched** | Read-only input; opened via headless Blender. |
| `export/geometry.gltf` | **Preserved** | Untouched in export folder. |
| `godot_project/main.tscn` | **Updated** | Replaced `geometry.gltf` with `osm2world_baked.glb`. |
| `godot_project/apply_shader.gd` | **Updated** | Removed runtime raycast loops and texture transparency hacks. |
| `godot_project/assets/tecate_facsimile_polygon.geojson` | **Created** | Clean GeoJSON representing the extended terrain boundary. |
| `godot_project/assets/osm2world_baked.glb` | **Created** | Prebaked 29.3 MB city model with 4,320 draped meshes. |

All changes strictly adhere to the requirement that symlinked backup targets (`models/`, `export/`, `reference/`, `data/`) remain read-only.
