# Formatos de Datos del Minecraft Pipeline

## 1. Entradas del exportador

### 1.1 `reconstruction_export.json`

Archivo JSON principal con la geometría urbana de Tecate. Contiene:

```json
{
  "blocks": [
    {
      "polygon": [
        [x1_local, y1_local],
        [x2_local, y2_local],
        ...
      ]
    },
    ...
  ],
  "road_graph": {
    "nodes": [
      { "id": "12345678", "x": 150.3, "y": -220.7 },
      ...
    ],
    "edges": [
      { "u": "12345678", "v": "98765432", "name": "Av. Benito Juárez" },
      ...
    ]
  }
}
```

**Coordenadas:** Locales en metros. Origen = Parque Hidalgo. `x` = Este, `y` = Norte.  
**Filtro aplicado:** Solo se usan bloques con área ≤ 60,000 m² (6 ha).

---

### 1.2 `tecate.glb` — Modelo de terreno TIN

Archivo binario GLB (glTF Binary). Contiene múltiples meshes. El exportador accede únicamente a **Mesh 1** (índice 1), que es la malla TIN de superficie del terreno.

**Estructura GLB relevante:**
```
GLB Header (12 bytes)
  magic:   0x46546c67 ('glTF')
  version: 2
  length:  total_bytes

Chunk 0 (JSON)
  gltf["meshes"][1]         ← tinMesh (superficie TIN)
    primitives[0]
      attributes.POSITION   ← accessor index

Chunk 1 (Binary Buffer)
  Datos de vértices float32 (x, y, z) por vértice
```

**Formato de vértices:** `float32[N][3]` — N vértices × 3 componentes (x, y, z en espacio GLB/Godot).

---

## 2. Caché interna del exportador

### 2.1 `custom_blocks_cache.npz`

Archivo NumPy comprimido. Guarda el estado de rasterización intermedio.

| Array | dtype | Descripción |
|-------|-------|-------------|
| `x` | `int32[N]` | Coordenadas X_mc de bloques rasterizados |
| `y` | `int32[N]` | Coordenadas Y_mc |
| `z` | `int32[N]` | Coordenadas Z_mc |
| `block_ids` | `uint8[N]` | Índice en la paleta |
| `palette` | `str[P]` | Array de strings: nombres de bloques Minecraft |
| `last_edge_idx` | `int` scalar | Índice de última arista completada |
| `last_block_idx` | `int` scalar | Índice de última manzana completada |
| `completed_block_indices` | `int32[M]` | Índices de manzanas finalizadas |

**Acompañante:** `custom_blocks_cache_entities.pkl` — `dict {(x,y,z): NBT_tag}` con block entities.

---

### 2.2 `terrain_height_cache.json`

```json
{
  "150,-220": 42,
  "151,-220": 43,
  ...
}
```

Mapa de `"X_mc,Z_mc"` → `Y_mc` para todos los puntos del terreno ya interpolados.

---

### 2.3 `road_metadata.json`

```json
{
  "edges": {
    "12345678,98765432": {
      "highway": "secondary",
      "lanes": 2,
      "width": 8.0,
      "surface": "asphalt",
      "service": "",
      "name": "Av. Benito Juárez",
      "bridge": "",
      "layer": ""
    },
    ...
  }
}
```

La clave de cada arista es `get_edge_key(u, v) = "{min},{max}"` de los IDs de nodo.

---

### 2.4 `terrain_classification.json`

```json
[
  {
    "vertices": [[x1, z1], [x2, z2], ...],
    "class": "grass"
  },
  {
    "vertices": [[x1, z1], ...],
    "class": "paved"
  },
  ...
]
```

Los vértices están en coordenadas MC `(X_mc, Z_mc)` (i.e., `(x_local, -y_local)`).  
Clases posibles: `"grass"`, `"paved"`, `"dirt"`.

---

### 2.5 `water_osm_cache.json`

JSON raw de la respuesta de Overpass API para features de agua. Formato estándar de la API Overpass:
```json
{
  "version": 0.6,
  "elements": [
    {
      "type": "way",
      "id": 12345678,
      "tags": {"natural": "water"},
      "geometry": [{"lat": 32.57, "lon": -116.62}, ...]
    },
    ...
  ]
}
```

---

## 3. Archivos de salida del exportador

### 3.1 `TecateWorld/region/r.RX.RZ.mca`

Archivo de región Minecraft. Contiene 32×32 = 1,024 chunks.

**Estructura de chunk NBT:**
```
TAG_Compound ""
  TAG_Int "DataVersion" = 3463          (Minecraft 1.20.x)
  TAG_Int "xPos" = cx_global
  TAG_Int "zPos" = cz_global
  TAG_Int "yPos" = min_section_y        (sección Y mínima)
  TAG_String "Status" = "full"
  TAG_List "sections" [TAG_Compound]
    TAG_Compound
      TAG_Byte "Y" = section_y
      TAG_Compound "block_states"
        TAG_List "palette" [TAG_Compound]
          TAG_Compound
            TAG_String "Name" = "minecraft:block_name"
        TAG_Long_Array "data"             (solo si palette > 1 entrada)
          [empaquetado non-overlapping, bits_per_block = max(4, ceil(log2(palette_size)))]
      TAG_Compound "biomes"
        TAG_List "palette" [TAG_String]
          "minecraft:plains"
  TAG_List "block_entities" [TAG_Compound]
    ... (si hay block entities)
```

**Índice de bloque en sección** (layout XYZ flat):
```
flat_idx = dy * 256 + dz * 16 + dx
```
donde `dx, dy, dz ∈ [0, 15]`.

---

### 3.2 `TecateWorld/level.dat`

Archivo NBT comprimido con GZIP. Metadatos del mundo.

```
TAG_Compound ""
  TAG_Compound "Data"
    TAG_String "LevelName" = "Tecate Simulator"
    TAG_String "generatorName" = "flat"
    TAG_Int "SpawnX" = 0
    TAG_Int "SpawnY" = spawn_y
    TAG_Int "SpawnZ" = 0
    TAG_Int "GameType" = 1              (Creative)
    TAG_Byte "Difficulty" = 0          (Peaceful)
    TAG_Long "Time" = 6000             (mediodía)
    TAG_Long "DayTime" = 6000
    TAG_Int "version" = 19133
    TAG_Byte "initialized" = 1
    TAG_Compound "GameRules"
      TAG_String "doMobSpawning" = "false"
      TAG_String "keepInventory" = "true"
      TAG_String "doDaylightCycle" = "false"
    TAG_Compound "DataPacks"
      TAG_List "Enabled" [TAG_String]
        "vanilla"
        "file/HigherHeights-X.Y.zip"   (si existe)
      TAG_List "Disabled" [TAG_String]
```

---

### 3.3 `TecateWorld/tecate_metadata.json`

```json
{
  "vertical_offset": 437,
  "bbox": {
    "min_local_x": -2340.5,
    "max_local_x": 3120.8,
    "min_local_y": -1890.2,
    "max_local_y": 2450.1
  },
  "terrain_alignment": {
    "scale": 0.8427785648661434,
    "translation_x": 28052.404303473268,
    "translation_z": -16620.3853885848
  }
}
```

---

## 4. Archivos de salida del importador

### 4.1 `boxes.json`

```json
{
  "region_data": {
    "r.0.0": [
      {
        "pos": [150.0, 220.0, 479.0],
        "mask": 6,
        "block_type": "minecraft:yellow_concrete",
        "color": [0.95, 0.8, 0.1]
      }
    ],
    "r.-1.0": [...]
  }
}
```

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `pos` | `[float, float, float]` | Posición en Blender space `[X_mc, -Z_mc, Y_mc + y_offset]` |
| `mask` | `int` (0-63) | Bitmask de caras expuestas (ver ARCHITECTURE.md §`import_minecraft.py`) |
| `block_type` | `str` | Nombre completo del bloque Minecraft |
| `color` | `[float, float, float]` | Color RGB para material de fallback |

---

### 4.2 `importer_checkpoint.json`

```json
{
  "mtimes": {
    "r.0.0": [1718340123.5, 45678, 1718340200.1, 56789],
    ...
  },
  "modified_blocks": {
    "r.0.0": {
      "150,65,-220": "minecraft:yellow_concrete",
      "151,65,-220": "minecraft:yellow_concrete"
    }
  }
}
```

Las coordenadas de bloques se almacenan como strings `"x,y,z"` para compatibilidad JSON.

---

## 5. Estructura del `VoxelMap`

`VoxelMap` es la estructura de datos central del exportador. Almacena bloques personalizados rasterizados con organización por chunk:

```python
class VoxelMap:
    x_arr: np.int32[N]      # Coordenadas X_mc de todos los bloques
    y_arr: np.int32[N]      # Coordenadas Y_mc
    z_arr: np.int32[N]      # Coordenadas Z_mc
    block_ids: np.uint8[N]  # Índice en palette
    palette: list[str]      # Nombres de bloques (máx 256 entries por uint8)
    
    chunk_slices: dict[(cx, cz) → (start, end)]  # Slices de los arrays por chunk
    new_blocks_by_chunk: dict[(cx, cz) → dict[(x,y,z) → str]]  # Bloques nuevos
    block_entities: dict[(x, y, z) → NBT_tag]   # Block entities
```

**Acceso:** Los chunks del array principal se indexan con `chunk_slices`. Los bloques añadidos dinámicamente van a `new_blocks_by_chunk`. La función `get_chunk_dict(cx, cz)` fusiona ambos.

**Limitación de paleta:** `block_ids` es `uint8`, lo que implica un máximo de **256 tipos de bloques distintos** en el conjunto rasterizado completo. En la práctica, el pipeline usa ≈15-20 tipos de bloque, muy por debajo del límite.

---

## 6. Paleta estándar de `fill_chunk_jit`

Los IDs numéricos dentro del JIT (solo válidos dentro de `fill_chunk_jit`) son:

| ID | `block_name` |
|----|--------------|
| 0 | `minecraft:air` |
| 1 | `minecraft:stone` |
| 2 | `minecraft:dirt` |
| 3 | `minecraft:sand` |
| 4 | `minecraft:water` |
| 5 | `minecraft:grass_block` |
| 6 | `minecraft:andesite` |
| 7 | `minecraft:polished_andesite` |
| 8 | `minecraft:stone_bricks` |
| 9 | `minecraft:coarse_dirt` |
| 10 | `minecraft:gravel` |

Estos IDs son **internos al JIT** y no se persisten directamente en el MCA (el código los traduce a nombres completos antes de escribir el NBT).
