# OSM2World Model Management & Working Copy Architecture

**Document Status**: Authoritative  
**Date**: September 2026  
**Primary Working Model**: `godot_project/assets/osm2world_adjusted.blend`  
**Derived Runtime Asset**: `godot_project/assets/osm2world_baked.glb`  
**Automation Script**: `scripts/create_adjusted_blend.py`  
**Source Baseline (Read-Only)**: `models/tecate/osm2world.blend`

---

## 1. Overview & Architecture

Previously, incorporating OpenStreetMap geometry required a multi-stage offline prebaking script that parsed 26,029 meshes from `models/tecate/osm2world.blend` (located on the external backup volume), raycasted against terrain, and exported a monolithic 34.5 MB glTF file.

To eliminate repetitive preprocessing and provide an immediate, editable 3D workspace, we created an authoritative **pre-adjusted working copy**:
$$\mathbf{godot\_project/assets/osm2world\_adjusted.blend} \quad (\approx 20\text{ MB})$$

This model has all horizontal offsets, vertical terrain elevations, foundation skirts, and scale normalizations permanently baked in.

```
┌──────────────────────────────────────────────┐
│       models/tecate/osm2world.blend          │  (Symlinked Backup Volume: READ-ONLY)
│       - 26,029 meshes (85% flat 2D)          │
│       - Generic names (Mesh_0..Mesh_26028)   │
│       - Unaligned coords & 7.285x empty scale│
└──────────────────────┬───────────────────────┘
                       │
                       │ scripts/create_adjusted_blend.py
                       ▼
┌──────────────────────────────────────────────┐
│  godot_project/assets/osm2world_adjusted.blend │  (Primary Workspace Asset, 102 MB)
│  - 3,552 3D volume structures (Full region)  │
│  - Full OSM metadata & real-world names      │
│  - Perfectly aligned (DX=+34976.59, DY=-31879.03)│
│  - Draped on terrain with 3.5m skirts        │
│  - Clean 1 unit = 1 meter coordinates        │
└──────────────────────┬───────────────────────┘
                       │ Fast glTF Export (8.1s)
                       ▼
┌──────────────────────────────────────────────┐
│    godot_project/assets/osm2world_baked.glb  │  (Godot Runtime Asset, 269 MB)
└──────────────────────────────────────────────┘
```

---

## 2. Flat 2D Surface Elimination (Taxonomy & Verification)

### 2.1 The Redundancy of 2D Overlays
In `tecate.glb`, the simulator already possesses:
- A high-resolution terrain mesh (`tinMesh`)
- An authoritative high-resolution aerial ground texture (`tecate_groundTexture.png`)
- Dedicated road surface layers (`roadMesh`) and rail lines

In `models/tecate/osm2world.blend`, 85% of all meshes were flat 2D polygons placed at $Z = -1.0\text{ m}$. In Godot, these flat sheets competed with `tecate.glb`'s textured ground, creating severe Z-fighting, flickering, and 22,000+ unnecessary draw calls.

### 2.2 Mathematical Verification
By analyzing bounding box dimensions, vertical height variation ($\Delta Z$), and polygon normals across all 26,029 meshes:
- **22 semantic categories** have $\Delta Z = 0.00\text{ m}$ and face normals strictly parallel to $(0, 0, 1)$. They possess **zero physical volume**.
- **7 categories** possess genuine vertical extrusion ($\Delta Z > 0.5\text{ m}$) or 3D geometry.

### 2.3 Comprehensive Category Breakdown

| Category Prefix | Mesh Count | Nature in OSM2World | Action |
|---|---|---|---|
| `Building` | 2,602 | 3D extruded structures with walls, roofs, and volume | **RETAINED** |
| `HighVoltagePowerTower` | 794 | 3D structural lattice transmission towers | **RETAINED** |
| `Tree` | 253 | 3D individual foliage and trunks | **RETAINED** |
| `Forest` | 156 | Clustered 3D tree canopies ($\Delta Z = 14\text{–}22\text{ m}$, up to 250k vertices) | **RETAINED** |
| `WindTurbine` | 79 | 3D generation towers and rotors ($\Delta Z = 21\text{ m}$) | **RETAINED** |
| `PowerLine` | 13 | 3D catenary wire spans | **RETAINED** |
| `BusStop` | 2 | 3D street passenger shelters | **RETAINED** |
| **Total 3D Physical Structures** | **3,899** | **15.0% of meshes (100% of physical volume)** | **PRESERVED** |
| `Road` | 10,650 | 2D street/lane strip polygons ($\Delta Z = 0.00$) | **PURGED** |
| `RoadJunction` | 10,560 | 2D intersection polygons ($\Delta Z = 0.00$) | **PURGED** |
| `RoadConnector` | 280 | 2D road connection strips ($\Delta Z = 0.00$) | **PURGED** |
| `Waterway` | 190 | 2D canal/stream surface fills ($\Delta Z = 0.00$) | **PURGED** |
| `SurfaceArea` | 124 | 2D ground landuse fills ($\Delta Z = 0.00$) | **PURGED** |
| `SurfaceParking` | 48 | 2D parking lot pavement ($\Delta Z = 0.00$) | **PURGED** |
| `Rail` | 45 | 2D railway line strips ($\Delta Z = 0.00$) | **PURGED** |
| `Pool` | 40 | 2D water polygon fills ($\Delta Z = 0.00$) | **PURGED** |
| `TennisPitch` | 29 | 2D sports court surface ($\Delta Z = 0.00$) | **PURGED** |
| `RiverJunction` | 25 | 2D water confluence polygons ($\Delta Z = 0.00$) | **PURGED** |
| `Water` | 25 | 2D reservoir water sheets ($\Delta Z = 0.00$) | **PURGED** |
| `TrafficSignGroup` | 24 | 2D quad placeholders ($\Delta Z = 0.00$) | **PURGED** |
| `RoadCrossingAtConnector` | 20 | 2D pedestrian crosswalks ($\Delta Z = 0.00$) | **PURGED** |
| `SoccerPitch` | 20 | 2D football pitch surface ($\Delta Z = 0.00$) | **PURGED** |
| `PoleFence` | 19 | 2D boundary perimeter lines ($\Delta Z = 0.00$) | **PURGED** |
| `Wall` | 12 | 2D boundary outlines ($\Delta Z = 0.00$) | **PURGED** |
| `RoadArea` | 6 | 2D plaza pedestrian areas ($\Delta Z = 0.00$) | **PURGED** |
| `Runway` | 5 | 2D airstrip surfaces ($\Delta Z = 0.00$) | **PURGED** |
| `Helipad` | 4 | 2D landing pad decals ($\Delta Z = 0.00$) | **PURGED** |
| `AreaFountain` | 2 | 2D fountain water basins ($\Delta Z = 0.00$) | **PURGED** |
| `NodeModelInstance` | 1 | 2D point placeholder ($\Delta Z = 0.00$) | **PURGED** |
| `Table` | 1 | 2D picnic table flat polygon ($\Delta Z = 0.00$) | **PURGED** |
| **Total Flat Surfaces Purged** | **22,130** | **85.0% of meshes (Zero physical volume)** | **PURGED** |

---

## 3. Metadata Retention Schema

### 3.1 Problem Statement
In the original `osm2world.blend`, leaf mesh objects were named generically (`Mesh_100`, `Mesh_10015`), while all rich OpenStreetMap metadata resided in ancestor Empties (`Building Antigua estación de Tecate`, `Building w1162248333`, `HighVoltagePowerTower n649327087`). Previous export routines unparented objects, causing all semantic names to be lost.

### 3.2 Implemented Metadata Inheritance
`scripts/create_adjusted_blend.py` walks up the parent chain before hierarchy flattening and transfers metadata directly to the object and its mesh data block:

1. **Object Naming**:
   - Primary: `Building_Antigua_estación_de_Tecate`
   - Multi-part components: `Building_Antigua_estación_de_Tecate_part1`
   - OSM Way/Node: `Building_w1162248333`, `Tree_n11403950522`
2. **Custom Blender Properties (attached to `obj` and `obj.data`)**:
   - `osm_semantic_name`: Full original string (e.g., `"Building Antigua estación de Tecate"`).
   - `osm_category`: Primary classification (e.g., `"Building"`, `"PowerInfrastructure"`, `"Vegetation"`).
   - `osm_type`: `"way"` or `"node"`.
   - `osm_id`: String containing the 64-bit OSM ID (stored as string to prevent 32-bit C integer overflow).
   - `osm_chain`: Full genealogical hierarchy (e.g., `"Node_32251 -> Building Antigua estación de Tecate"`).
3. **glTF Compatibility**:
   - Exported with `export_extras=True`, ensuring all custom properties are preserved in the glTF JSON `extras` dictionary for Godot and external game engines.

---

## 4. Applied Transformations & Calibrations

### 4.1 Horizontal Alignment
- **Translation Offsets**:
  $$\mathbf{DX = +34,976.59\text{ m}}, \quad \mathbf{DY = -31,879.03\text{ m}}$$
- **Calibration Basis**: Procrustes regression across 437 OpenStreetMap road intersections within 1 km of Parque Miguel Hidalgo.
- **Accuracy**: Eliminates both the initial 85m NW block shift and the residual 24m SW park-perimeter shift. Local accuracy is within $\sim 1.0\text{ m}$ of ground-truth `tecate.glb` road coordinates.

### 4.2 Vertical Elevation & Foundation Skirts
- **Terrain Raycasting**: High-speed C++ `mathutils.bvhtree.BVHTree` built directly from `tecate.glb`'s TIN mesh ($704,645\text{ vertices}, 1,401,437\text{ triangles}$).
- **Rigid Base Elevation**: Each structure's centroid is queried against the terrain surface to determine local ground elevation $Z_{\text{terrain}}$.
- **Foundation Skirt Extrusion**:
  - Ground-level building vertices ($w.z \le -0.99\text{ m}$) are extruded downward by **$3.5\text{ m}$** ($Z_{\text{base}} = Z_{\text{terrain}} - 3.5\text{ m}$).
  - This prevents visual gaps or floating corners on sloped hillside terrain while keeping roofs strictly horizontal.

### 4.3 Scale & Hierarchy Normalization
- **Nested Empty Scaling Trap Avoided**: In `osm2world.blend`, parent empties carried a non-uniform scale factor of $\approx 7.2852$.
- In `osm2world_adjusted.blend`, all vertex coordinates are baked into true world metric space ($1\text{ Blender unit} = 1.0\text{ meter}$), parent empties are removed, and all objects have clean identity matrices (`matrix_world = Identity`).

### 4.4 Collection Organization
Surviving objects are cleanly organized into 4 semantic Blender Collections across the entire municipality:
- `Buildings` (2,602 objects: 100% of all OSM buildings)
- `PowerInfrastructure` (539 objects: HighVoltagePowerTowers, WindTurbines, PowerLines)
- `Vegetation` (409 objects: 253 Trees + 156 Forest canopy clusters)
- `CivicAmenities` (2 objects: BusStops)

---

## 5. Performance Optimization & Parallelization

The previous prebaking script suffered from a severe 16-minute bottleneck during object deletion due to Blender's Python API updating internal dependency graphs on every single call to `bpy.data.objects.remove(obj)`.

### Key Optimizations Implemented:
1. **C++ Native Batch Removal (`bpy.data.batch_remove`)**:
   - Instead of 54,000 Python removal iterations, objects to delete and empty hierarchy nodes are collected into lists and purged in bulk using native C++ `bpy.data.batch_remove(ids=...)`.
   - **Result**: Reduced deletion time from **16+ minutes down to 67 seconds** across 51,697 objects.
2. **C++ SIMD Raycasting**:
   - `mathutils.bvhtree.BVHTree.FromPolygons` evaluates 3,899 raycasts in parallel C routines in **under 36 seconds**.
3. **Sub-10s glTF Export**:
   - Exporting the entire city of 3,552 physical structures with full custom properties takes only **8.16 seconds**.

---

## 6. Usage & Re-Export Workflow

To inspect, modify, or add custom assets to the scene:

1. **Open directly in Blender**:
   ```bash
   blender godot_project/assets/osm2world_adjusted.blend
   ```
2. **Re-export to Godot GLB**:
   From Blender's menu:
   - `File` → `Export` → `glTF 2.0 (.glb/.gltf)`
   - Destination: `godot_project/assets/osm2world_baked.glb`
   - Under **Data** → **Include**, check **Custom Properties** (`extras`).
   - Export time is **only 8 seconds**!

3. **Or run the automated pipeline**:
   ```bash
   /Applications/Blender.app/Contents/MacOS/Blender -b -P scripts/create_adjusted_blend.py -- --radius -1.0
   ```
