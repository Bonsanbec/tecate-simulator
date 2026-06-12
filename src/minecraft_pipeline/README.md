# Minecraft Java Edition Integration Pipeline

This package implements a complete, deterministic, and highly scalable export and import pipeline between the Tecate historical urban reconstruction simulator and Minecraft Java Edition.

Minecraft serves as the primary visual editor for the city layout, roads, and buildings, coexisting with the existing Blender/Godot rendering pipeline.

---

## 1. Directory Structure

```
src/minecraft_pipeline/
├── __init__.py
├── nbt.py              # Pure-Python NBT serialization & Gzip/Zlib compression
├── mca.py              # Pure-Python Region MCA writer & bit-packer (1.18+)
├── exporter.py         # GIS Geometry + Terrain GLB -> Minecraft Java World
├── importer.py         # Minecraft World -> Optimized Boxes JSON -> Blender trigger
├── import_minecraft.py # Blender background Python compiler script
└── README.md           # Documentation (this file)
```

---

## 2. Coordinate System & Scale Mapping

Minecraft represents blocks at integer coordinates in a 1:1 scale (1 block = 1 real meter) using a right-handed system ($X$ = East, $Y$ = Up, $Z$ = South).

The local Cartesian coordinates (Equirectangular tangent plane centered at Parque Hidalgo) are transformed to Minecraft as follows:
- $X_{MC} = x_{local}$
- $Z_{MC} = -y_{local}$
- $Y_{MC} = z_{local} - Y_{offset}$

### Dynamic Vertical Elevation Offset
The municipality of Tecate has a base elevation of around 400 meters. Placing blocks directly at $Y=400$ would exceed Minecraft's default height limit of $320$. 
To prevent clipping, the exporter dynamically calculates a vertical offset:
$$Y_{offset} = \lfloor \text{min\_elevation} \rfloor - 10$$
This shifts the base terrain down to start around $Y=10$ blocks. The offset is saved in `tecate_metadata.json` in the world directory, allowing the importer to mathematically reverse the shift:
$$z_{local} = Y_{MC} + Y_{offset}$$

---

## 3. High-Scalability Design

To process the full Tecate municipality (covering over 4300 blocks/manzanas) without memory exhaustion:
1. **Local Terrain Height Lookup**: Rather than loading a massive 2D heightmap in memory, the exporter indexes the 700k+ terrain vertices of the GLB model into a 2D spatial grid of $500 \times 500$ meters. Point queries retrieve only vertices from the 3x3 local cell neighborhood and run linear Delaunay interpolation locally, achieving $O(1)$ query times.
2. **Region-Level Chunk Streaming**: Active chunks are grouped by Minecraft Region coordinates (`r.rx.rz.mca`). The exporter generates, bit-packs, and Zlib compresses chunks region-by-region, writing them directly to disk and freeing memory immediately. RAM usage remains constant regardless of the municipality size.

---

## 4. Minecraft Representations

- **Terrain**: Materialized as solid blocks of stone, dirt, and grass based on the local interpolated terrain heights.
- **Road Network**: Drawn as lines of grey concrete (`"minecraft:gray_concrete"`) on the terrain surface.
- **Buildings**: Visualized as a 3D wireframe skeleton:
  - **Base Footprint**: `"minecraft:yellow_concrete"` outline on the terrain.
  - **Pillars**: `"minecraft:red_concrete"` vertical columns at vertices.
  - **Roof outline**: `"minecraft:light_blue_concrete"` perimeter connecting column tops.

---

## 5. Terrain Subtraction Mathematics

When reimporting the world, the importer reads the MCA files and performs a deterministic geometric subtraction:
$$\text{GeometryPreserved} = \text{MinecraftWorldEdited} - \text{BaseTerrainRegenerated}$$

For each block coordinate:
- The importer computes the original terrain height $y_{terrain}$.
- If the block type is in `TERRAIN_BLOCKS` (grass, dirt, stone, bedrock, clay, sand, gravel, water) AND its height satisfies $Y \le y_{terrain} - Y_{offset}$, it is culled.
- All other blocks (user modifications, structures built out of other materials, or blocks placed above $y_{terrain}$) are preserved.

---

## 6. Execution Commands

Ensure you run commands using the virtual environment's Python interpreter and set `PYTHONPATH=.`.

### Export to Minecraft
Exports `reconstruction_export.json` and the terrain GLB to a new world directory:
```bash
PYTHONPATH=. ./venv/bin/python src/minecraft_pipeline/exporter.py \
    --import-json export/reconstruction_export.json \
    --glb-path models/tecate/glb/tecate.glb \
    --output-dir export/minecraft_world
```
This produces a fully functional save folder `export/minecraft_world/TecateWorld` which can be copied into Minecraft's `saves/` folder.

### Import from Minecraft
Reads the edited Minecraft world saves folder, performs subtraction, and compiles a new `.blend` and `.glb` mesh in Blender:
```bash
PYTHONPATH=. ./venv/bin/python src/minecraft_pipeline/importer.py \
    --world-dir export/minecraft_world/TecateWorld \
    --glb-path models/tecate/glb/tecate.glb \
    --output-dir export/minecraft_world
```
This produces:
- `export/minecraft_world/tecate_reimported.blend`
- `export/minecraft_world/geometry_reimported.glb`

---

## 7. Future Microblock Extensibility

To support block subdivision mods (such as *Chisels & Bits* or *LittleTiles*):
- The `importer.py` parses blocks into float-based coordinate ranges: `Box(x_min, y_min, z_min, x_max, y_max, z_max, color)`.
- For standard blocks, the box is $1 \times 1 \times 1$.
- To support microblocks, you only need to update the block parsing loop in `importer.py` to inspect the chunk's tile entities and output sub-meter box coordinates (e.g. size $0.125 \times 0.125 \times 0.125$).
- The meshing, face culling, and Blender compiler script (`import_minecraft.py`) consume the box floats directly and will require **no changes**.
