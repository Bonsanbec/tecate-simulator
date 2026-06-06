# Tecate Simulator: Facade Appearance MVP Design & Implementation Roadmap

## Goal Description
The objective is to transition the Tecate Simulator project away from the failed 3D geometric facade reconstruction approach and design a fully automated, high-fidelity, and performance-optimized **Hybrid Facade System** suitable for a real-time videogame environment built in the **Godot Engine (C++/C#)**.

The previous MVP attempted to extract complex 3D meshes for facade elements (windows, doors, recesses), which proved too fragile to automate at scale. The new strategic direction focuses on **facade appearance** rather than geometry: keeping the main building geometry as flat, planar blocks (reusing the existing low-poly geometry) and using advanced shading techniques (Physically Based Rendering, Parallax Occlusion Mapping) and lightweight procedural mesh instancing in Godot to achieve visual plausibility, scalability, automation, and real-time rendering performance.

---

## User Review Required

> [!IMPORTANT]
> **Key Strategic Shift**: The pipeline will no longer export complex extruded window and door geometry. Instead, it will export flat quads with packed PBR material maps (Albedo, Normal, Roughness, Height) that simulate depth in Godot spatial shaders.

> [!NOTE]
> **Heuristic-Driven Height Maps**: Rather than running slow and noisy AI depth estimation models, we generate height maps procedurally by combining semantic segmentation masks from the SegFormer model (`nvidia/segformer-b0-finetuned-ade-512-512`) with predefined depth rules (e.g., wall = constant base, windows/doors = sharp recess). This is fully parameterized and supports per-facade overrides.

> [!WARNING]
> **Draw Call and Shader Cost**: While Parallax Occlusion Mapping (POM) provides realistic depth, it is pixel-shader intensive. To scale to the entire municipality, we will implement Godot's built-in Level of Detail (LOD) system to switch from POM to cheaper parallax/normal mapping shaders at medium-to-far distances.

---

## Technical Decisions & Integrations

### 1. Game Engine & Shader Target: Godot 4.x (C++/C#)
* **Graphics API**: Vulkan (Mobile or Forward+ Clustered backend).
* **Shader Implementation**: Custom Godot Spatial Shaders writing to the `ALBEDO`, `NORMAL`, `ROUGHNESS`, and `METALLIC` built-ins.
* **Depth Simulation**: Custom HLSL-like ray-march loop inside the fragment shader performing Parallax Occlusion Mapping (POM) using the packed height map.
* **LOD Management**: Utilize Godot 4's native `LOD` system (via import settings or `GeometryInstance3D` visibility ranges) to swap materials and hide/show props dynamically.

### 2. Case Study Workspace Collection
The development environment does not populate local screenshot caches by default nor exports the low-poly geometry. Developers must run:
```bash
python scripts/collect_case_study_images.py
```
This script reads the target facade list from `data/case_study/target_facade.json`, references the caches, detects missing or Git LFS pointer files, and fetches the required screenshots from the remote host configured in `.env` via SSH/WSL. It then creates symlinks in `data/case_study/target_images/` pointing to the retrieved images. And also pull the export/geometry.gltf similarly.

### 3. Terrain-Reconstruction Coordinate Alignment
The terrain GLB has its center at the shape's center and contains an altered NW-most vertex. The reconstruction pipeline places Parque Hidalgo (32.573229, -116.626536) at Cartesian (0,0). 
We align them via the following 2D Procrustes-style mathematical transform:
1. **Load Reference Polygon**: Parse WGS84 coordinates from `reference/tecate-polygon.json`.
2. **Project to Cartesian**: Project WGS84 vertices into local Cartesian meters relative to Parque Hidalgo using `gps_to_local()`.
3. **Filter Outliers**: Discard the NW-most vertex from both the projected polygon and the terrain GLB boundary mesh.
4. **Solve Least Squares**: Compute the optimal scale $S$, rotation $\theta$ (assumed near 0), and 2D translation $(T_x, T_y)$ that minimizes the Euclidean distance between the remaining matching vertices.
5. **Apply Transform**: Apply the resulting transformation matrix to the terrain GLB import node in Godot to bring it into alignment with the local Cartesian building block coordinates.

### 4. Planar Block Height Alignment (Terrain Projection)
The low-poly building geometry exported at remote's `export/geometry.gltf` (centered at Parque Hidalgo 0,0) lacks elevation adjustments; all building blocks have their base at height Z = 0. To resolve this and sit buildings correctly on the terrain:
1. **Centroid Elevation Retrieval**: For each building block, compute the 2D Cartesian centroid $(C_x, C_y)$ of its footprint.
2. **Raycast Snapping**: Perform a vertical raycast from $(C_x, C_y, +\infty)$ downwards onto the aligned terrain GLB mesh to find the terrain intersection height $Z_{terrain}$.
3. **Height Offset & Skirt Extrusion**: Set the block's base elevation to $Z_{terrain}$. To prevent visual gaps or floating corners due to local terrain slope, extend the block geometry downwards (skirt/foundation extrusion) by a safety margin (e.g., 1.5m) into the terrain mesh. This keeps roofs level and avoids complex polygon shearing or UV stretching.
Note: For retrieving the GLTF from remote, follow a similar approach to that of collect_case_study_images.py.

### 5. Parameterized Per-Facade PBR & Height Generation
* **Default Heuristics**: Maps semantic mask IDs from SegFormer to material properties:
  * `wall` (ADE20K 0,1): Height = 1.0 (base), Roughness = 0.8, Metallic = 0.0
  * `window` (ADE20K 8): Height = 0.85 (15cm recess), Roughness = 0.1, Metallic = 0.2
  * `door` (ADE20K 14,58): Height = 0.90 (10cm recess), Roughness = 0.6, Metallic = 0.0
* **Per-Facade Customization**: 
  * The generator checks for the existence of `{facade_id}_material_config.json`.
  * If found, the generator overrides default heights, roughness, or metallic constants for that specific facade, or loads an external custom height mask.

---

## Required Analysis: Candidate Approaches

We evaluate the candidate approaches for a municipal-scale Godot game:

| Approach | Advantages | Disadvantages | Godot Implementation |
|---|---|---|---|
| **Simple Texturing** | Lowest cost; fits any hardware. | Looks completely flat and painted-on. | Standard `StandardMaterial3D` with albedo. |
| **Perspective Warp** | Corrects camera skew. | Stretches occlusion gaps. | Pre-process homography via OpenCV. |
| **Sprite-Based** | Lightweight depth. | Hard to automate from single photos. | Multi-mesh billboard cards. |
| **Billboard Systems** | Extremely cheap. | Breaks connected street blocks. | `StandardMaterial3D` billboard mode. |
| **Impostors** | Low draw calls for distant views. | Looks blurry close-up. | Baked octahedron texture sheets (LOD 3). |
| **Atlas Generation** | Reduces draw calls. | Packing overhead; UV management. | Pack textures per block. |
| **Material Gen** | Realistic light response. | Heuristics required. | Automated PBR map extraction. |
| **PBR Enhancement** | Native engine support. | Slight shader overhead. | Godot `ORMMaterial3D` structure. |
| **AI Normals** | Micro-relief detail. | Mistaken shadow shading. | OpenCV Sobel filter from height map. |
| **AI Heights** | Capture macro structure. | Blurry/wavy edges; slow offline. | Neural network depth estimators. |
| **Parallax Mapping** | Cheap depth effect. | Warps at oblique viewing angles. | Shader offset with minor steps (LOD 1). |
| **Parallax Occlusion (POM)**| Outstanding depth; self-occlusion. | High pixel shader cost. | Ray-march spatial shader (LOD 0). |
| **Procedural Props** | Breaks silhouette lines. | Requires prop library. | Godot `MultiMeshInstance3D` spawner. |
| **Hybrid System** | Best quality-performance balance. | High pipeline complexity. | POM + Instanced props (LOD 0). |
| **LOD rendering** | Scalable to whole city. | Requires asset variations. | Godot native LOD distance swaps. |

---

## Decision Framework

* **Recommended Approach**: **Hybrid Facade System with LOD-Aware Rendering**. Planar geometry with POM/PBR (LOD 0) and standard Parallax (LOD 1) coupled with instanced props spawned based on semantic masks.
* **MVP Scope**: **Caseta Telefónica LA PANZA** (Block ID: `block_lat_32.57255_lon_-116.62529`, Facades `[68-77]`).
* **Recommended Asset Formats**:
  * **Geometry**: glTF 2.0 (containing planar block and instanced nodes).
  * **Textures**: Packed PNGs:
    * `Texture_Albedo_Roughness`: RGB = Albedo, Alpha = Roughness.
    * `Texture_Normal_Height`: RGB = Normal, Alpha = Height.
* **Runtime Strategy**: Custom Godot Spatial Shaders implementing POM. Transition to standard Normal Mapping at >30m, and flat atlases at >100m.
* **Tooling**: PyTorch (SegFormer), OpenCV (warp/filters/packing), Python CLI (orchestrator), Blender `bpy` (export), Godot 4.x (runtime rendering).
* **Validation Metrics**: Window/door recess depth verification, frame-rate profiling (>60 FPS), VRAM budget (<1.5MB for LA PANZA asset).

---

## Phased Implementation Roadmap

### Phase 1: Prototyping (Weeks 1 - 3)
* Run local SegFormer-B0 model on rectified images.
* Implement the PBR height/roughness texture packer.
* Write a Godot Spatial Shader supporting POM.
* Code the Least Squares boundary-matching algorithm to calculate the terrain-reconstruction alignment matrix.

### Phase 2: Success Measurement (Week 4)
* Create validation scripts to measure PSNR/SSIM between rendered POM and rectified source photos.
* Establish automation timers (<10s per block target).
* Set up a Godot runtime profiler to log GPU frame times.

### Phase 3: Study Case Evaluation (Weeks 5 - 6)
* Run `collect_case_study_images.py` to acquire baseline photos over SSH.
* Process "Caseta Telefónica LA PANZA" (Facades `[68-77]`).
* Generate albedo, masks, packed PBR textures, and prop transform points.
* Compile and export the glTF. Verify POM depth and prop alignment in Godot.

### Phase 4: Scaling the Pipeline (Weeks 7 - 9)
* Implement block-level texture atlasing to ensure 1 draw call per building block.
* Automate LOD generation (baking far-field impostors in Blender).
* Implement the terrain raycast snapping script inside Godot/Python to adjust building base altitudes and extrude foundations.

### Phase 5: Municipality-Wide Operation (Weeks 10 - 12)
* Run crawler across all 4,239 blocks.
* Compile final city-wide Godot scene (Terrain GLB + aligned block LODs).
* Perform final performance profiling.

---

## Proposed Changes (Architectural Layout)

#### [NEW] [segmentation_processor.py](file:///Users/hakkindavid/Documents/GitHub/tecate-simulator/src/reconstruction/segmentation_processor.py)
* Runs SegFormer-B0 to extract window, door, and wall coordinates.

#### [NEW] [pbr_generator.py](file:///Users/hakkindavid/Documents/GitHub/tecate-simulator/src/reconstruction/pbr_generator.py)
* Generates height, normal, and roughness maps, and packs them into Godot-compatible PNG channels. 
* Parses `{facade_id}_material_config.json` configuration files for overrides.

#### [MODIFY] [prism_generator.py](file:///Users/hakkindavid/Documents/GitHub/tecate-simulator/src/reconstruction/prism_generator.py)
* Integrates segmentation and PBR generators; outputs block-level coordinate maps.

#### [NEW] [prop_spawner.py](file:///Users/hakkindavid/Documents/GitHub/tecate-simulator/src/reconstruction/prop_spawner.py)
* Places sills, signs, and awnings relative to the facade plane.

#### [NEW] [terrain_aligner.py](file:///Users/hakkindavid/Documents/GitHub/tecate-simulator/src/reconstruction/terrain_aligner.py)
* Solves Procrustes least squares alignment between [tecate-polygon.json](file:///Users/hakkindavid/Documents/GitHub/tecate-simulator/reference/tecate-polygon.json) and terrain GLB.

#### [MODIFY] [blender_script.py](file:///Users/hakkindavid/Documents/GitHub/tecate-simulator/blender_script.py)
* Imports components, sets up LOD properties, raycasts and offsets building mesh vertices onto the terrain surface, and exports clean glTF 2.0 assets.

---

## Task Breakdown (Work Breakdown Structure)

### Task 1: Segmentation and Parameterized PBR Generator
* **Purpose**: Segment facades and generate custom height/normal/roughness maps with parameter overrides.
* **Inputs**: Rectified facade textures, `{facade_id}_material_config.json` (optional).
* **Outputs**: Packed `Albedo_Roughness` and `Normal_Height` textures.
* **Dependencies**: SegFormer workspace setup.
* **Validation**: Output textures match Godot target channels; height overrides are correctly loaded.
* **Effort**: 6 days.

### Task 2: Terrain Aligner and Raycast Snapper
* **Purpose**: Calculate translation and scale to align the terrain GLB, and snap the low-poly building bases to the terrain.
* **Inputs**: `tecate-polygon.json`, terrain GLB boundary vertices, building geometries at Z=0.
* **Outputs**: Transform matrix $(S, \theta, T_x, T_y)$, Z-offset building geometries.
* **Dependencies**: Coordinate projection module (`coords.py`).
* **Validation**: Aligned terrain boundary matches projected polygon (excluding NW vertex) with RMSE < 0.5m; building bases sit on terrain with foundation extrusion.
* **Effort**: 5 days.

### Task 3: Godot POM Shader & Spawner Integration
* **Purpose**: Implement the spatial shader and MultiMesh spawner in Godot.
* **Inputs**: Packed textures, prop coordinate tables.
* **Outputs**: Godot prototype project.
* **Dependencies**: Task 1.
* **Validation**: Windows appear recessed in-game; props align without floating; runs >60 FPS on target hardware.
* **Effort**: 6 days.

### Task 4: Study Case Execution (LA PANZA)
* **Purpose**: Validate target facade `[68-77]` of block `block_lat_32.57255_lon_-116.62529`.
* **Inputs**: Baseline photos fetched via `collect_case_study_images.py`, scraper caches.
* **Outputs**: Aligned glTF + Godot scene + validation report.
* **Dependencies**: Tasks 1, 2, 3.
* **Validation**: Pass visual and performance metrics; visual alignment error < 0.10m.
* **Effort**: 4 days.

---

## Quality Gates

* **QG-01 (Alignment)**: < 0.10m offset from block cycle edges.
* **QG-02 (Resolution)**: 100 - 150 px/meter of facade width.
* **QG-03 (Visual Quality)**: PSNR > 28 dB / SSIM > 0.82 compared to source photo.
* **QG-04 (Generation)**: < 10 seconds execution time per block.
* **QG-05 (Performance)**: > 60 FPS under full scene load in Godot.
* **QG-06 (VRAM)**: < 1.0 GB total VRAM for city center.

---

## Risk Analysis

### 1. High Shader Cost of POM in Godot
* **Likelihood**: High | **Impact**: High.
* **Mitigation**: Switch to standard normal mapping (LOD 2) at >30m.

### 2. Occlusion and Stretched Pixels in Warp
* **Likelihood**: Medium | **Impact**: Medium.
* **Mitigation**: Discard screenshots captured at angles >60° from facade normal and fallback to adjacent observations.

### 3. Noise or Wavy Contours in Height Maps
* **Likelihood**: High | **Impact**: High.
* **Mitigation**: Generate sharp, clean height masks from binary semantic segmentation layers instead of neural depth estimation.
