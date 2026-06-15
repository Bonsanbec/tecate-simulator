# Guía de Extensión: Importadores, Exportadores y Análisis Espacial

## 1. Cómo interpretar el mundo Minecraft como SIG

El mundo Minecraft generado es un **Sistema de Información Geográfica voxelizado**. Cada bloque es un píxel 3D geolocalizable.

### 1.1 Leer coordenadas GPS de cualquier bloque

```python
from src.core_io.coords import local_to_gps

def mc_to_gps(x_mc: int, y_mc: int, z_mc: int, y_offset: int):
    """Convierte posición Minecraft a coordenadas GPS y altura real."""
    x_local = float(x_mc)
    y_local = float(-z_mc)
    h_real  = float(y_mc + y_offset)
    lat, lon = local_to_gps(x_local, y_local)
    return lat, lon, h_real

# Ejemplo:
lat, lon, h = mc_to_gps(150, 65, -220, y_offset=437)
# → (32.573229 + Δlat, -116.626536 + Δlon, 502.0 m)
```

### 1.2 Leer el mundo desde Python (sin Minecraft)

```python
from src.minecraft_pipeline.mca import MCARegion, unpack_block_states
import math

def read_column(world_dir, x_mc, z_mc):
    """Lee todos los bloques de una columna vertical."""
    rx = int(math.floor(x_mc / 512.0))
    rz = int(math.floor(z_mc / 512.0))
    cx_global = int(math.floor(x_mc / 16.0))
    cz_global = int(math.floor(z_mc / 16.0))
    
    mca_path = f"{world_dir}/region/r.{rx}.{rz}.mca"
    region = MCARegion.load(mca_path, rx, rz)
    
    cx_local = cx_global - rx * 32
    cz_local = cz_global - rz * 32
    chunk_nbt = region.get_chunk_nbt(cx_local, cz_local)
    
    # Extraer bloques de la columna
    blocks = {}
    for tag in chunk_nbt.value:
        if tag.name == "sections":
            for sec_tag in tag.value[1]:
                # Leer Y, block_states...
                pass  # Ver extract_chunk_all_blocks() en importer.py
    return blocks
```

Usar la función `extract_chunk_all_blocks()` de `importer.py` directamente para leer bloques.

---

## 2. Cómo reconstruir el mapa geográfico desde el mundo Minecraft

### 2.1 Extraer el perfil de terreno

```python
import json
import numpy as np
from src.minecraft_pipeline.importer import extract_chunk_all_blocks
from src.minecraft_pipeline.mca import MCARegion

def extract_terrain_profile(world_dir, y_offset, min_x, max_x, min_z, max_z):
    """
    Extrae el perfil de terreno leyendo el bloque de superficie de cada columna.
    Retorna dict {(x_mc, z_mc): h_real} donde h_real está en metros.
    """
    surface = {}
    
    for x_mc in range(min_x, max_x + 1):
        for z_mc in range(min_z, max_z + 1):
            # Leer todos los bloques de la columna
            rx = int(x_mc // 512)
            rz = int(z_mc // 512)
            cx_global = int(x_mc // 16)
            cz_global = int(z_mc // 16)
            
            region = MCARegion.load(f"{world_dir}/region/r.{rx}.{rz}.mca", rx, rz)
            cx_local = cx_global - rx * 32
            cz_local = cz_global - rz * 32
            nbt = region.get_chunk_nbt(cx_local, cz_local)
            if nbt is None:
                continue
            
            blocks = extract_chunk_all_blocks(nbt, cx_global, cz_global, -16, 80)
            
            # Encontrar el bloque más alto no-aire en esta columna
            col_blocks = {y: name for (x, y, z), name in blocks.items()
                         if x == x_mc and z == z_mc and name != "minecraft:air"}
            if col_blocks:
                y_surface = max(col_blocks.keys())
                h_real = y_surface + y_offset
                surface[(x_mc, z_mc)] = h_real
    
    return surface
```

### 2.2 Extraer el grafo vial desde el mundo

```python
def extract_road_blocks(world_dir, y_offset, bbox_mc):
    """Identifica qué columnas son bloques de calle."""
    road_blocks = {}
    road_types = {
        "minecraft:gray_concrete_powder", "minecraft:black_concrete_powder",
        "minecraft:smooth_basalt", "minecraft:cobbled_deepslate", "minecraft:coal_block",
        "minecraft:gray_concrete", "minecraft:black_concrete",
        "minecraft:gray_concrete_powder", "minecraft:andesite", "minecraft:gravel",
        "minecraft:yellow_concrete", "minecraft:white_concrete",
        "minecraft:cobblestone", "minecraft:mossy_cobblestone", "minecraft:coarse_dirt"
    }
    
    min_x, max_x, min_z, max_z = bbox_mc
    for x in range(min_x, max_x):
        for z in range(min_z, max_z):
            # Leer superficie de columna...
            block_at_surface = get_surface_block(world_dir, x, z)
            if block_at_surface in road_types:
                road_blocks[(x, z)] = block_at_surface
    
    return road_blocks

def infer_road_hierarchy(block_name, surrounding_blocks):
    """Infiere la jerarquía vial a partir del tipo de bloque."""
    if block_name == "minecraft:yellow_concrete":
        # Ver si hay blocks de asfalto alrededor → es marca central
        if any(b in ["minecraft:gray_concrete", "minecraft:black_concrete"] 
               for b in surrounding_blocks.values()):
            return "boulevard"
        return "autopista"
    if block_name == "minecraft:white_concrete":
        return "marca de carril"
    if block_name in ["minecraft:gravel", "minecraft:cobblestone", "minecraft:coarse_dirt"]:
        return "rural"
    if block_name in ["minecraft:gray_concrete", "minecraft:black_concrete"]:
        return "boulevard"
    if block_name in ["minecraft:gray_concrete_powder", "minecraft:black_concrete_powder"]:
        return "calle urbana"
    return "calle local"
```

---

## 3. Cómo extender el exportador

### 3.1 Agregar un nuevo tipo de elemento geográfico

Para agregar, por ejemplo, edificios con altura:

```python
# En export_world(), después de rasterizar manzanas:
def rasterize_buildings(buildings_json, get_mc_terrain_y, custom_blocks, y_offset):
    for building in buildings_json:
        poly = building["polygon"]
        floors = building.get("floors", 1)
        height = floors * 3  # 3 bloques por piso
        
        poly_mc = [[pt[0], -pt[1]] for pt in poly]
        xs_in, zs_in, _ = find_inside_points(
            min_x_p, max_x_p, min_z_p, max_z_p, poly_mc
        )
        
        for x_mc, z_mc in zip(xs_in, zs_in):
            y_terrain = get_mc_terrain_y(x_mc, z_mc)
            for dy in range(height):
                y_mc = y_terrain + 1 + dy
                if dy < height - 1:
                    custom_blocks[(x_mc, y_mc, z_mc)] = "minecraft:white_concrete"
                else:
                    custom_blocks[(x_mc, y_mc, z_mc)] = "minecraft:gray_concrete"
```

### 3.2 Agregar un nuevo tipo de bloque para calles

Modificar `rasterize_roads_worker()` en `exporter.py`:

```python
# Ejemplo: agregar ciclovías (surface="cycleway")
if surface == "cycleway":
    choices = ["minecraft:lime_concrete", "minecraft:green_concrete"]
    weights = [0.8, 0.2]
    block_name = get_deterministic_choice(x_mc, y_road, z_mc, choices, weights)
```

### 3.3 Agregar block entities (e.g., señales de tráfico)

```python
# Crear un sign NBT como block entity
def create_sign_entity(x, y, z, text):
    return NBT(TAG_COMPOUND, value=[
        NBT(TAG_STRING, "id", "minecraft:sign"),
        NBT(TAG_INT, "x", x),
        NBT(TAG_INT, "y", y),
        NBT(TAG_INT, "z", z),
        NBT(TAG_STRING, "front_text", json.dumps({"messages": [text]}))
    ])

# Añadir al VoxelMap
custom_blocks[(x, y, z)] = "minecraft:oak_sign"
custom_blocks.block_entities[(x, y, z)] = create_sign_entity(x, y, z, "Av. Juárez")
```

---

## 4. Cómo implementar un importador personalizado

Para crear un importador que extraiga datos del mundo sin usar Blender:

```python
import json
import math
from src.minecraft_pipeline.mca import MCARegion, unpack_block_states
from src.minecraft_pipeline.importer import extract_chunk_all_blocks
from src.core_io.coords import local_to_gps

def world_to_geojson(world_dir, y_offset, output_path):
    """
    Extrae bloques modificados y los convierte a GeoJSON.
    Requiere fresh_world para comparación, o analiza solo el mundo modificado.
    """
    import glob
    features = []
    
    region_files = glob.glob(f"{world_dir}/region/r.*.*.mca")
    
    for mca_path in region_files:
        parts = mca_path.replace("\\", "/").split("/")[-1].split(".")
        rx, rz = int(parts[1]), int(parts[2])
        
        region = MCARegion.load(mca_path, rx, rz)
        
        for (cx_local, cz_local) in region.chunks:
            cx_global = rx * 32 + cx_local
            cz_global = rz * 32 + cz_local
            
            chunk_nbt = region.get_chunk_nbt(cx_local, cz_local)
            if not chunk_nbt:
                continue
            
            blocks = extract_chunk_all_blocks(chunk_nbt, cx_global, cz_global, -16, 80)
            
            for (x_mc, y_mc, z_mc), block_name in blocks.items():
                # Solo exportar bloques de interés
                if block_name in ["minecraft:yellow_concrete", "minecraft:gray_concrete"]:
                    x_local = float(x_mc)
                    y_local = float(-z_mc)
                    h_real  = float(y_mc + y_offset)
                    lat, lon = local_to_gps(x_local, y_local)
                    
                    feature = {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [lon, lat, h_real]
                        },
                        "properties": {
                            "block": block_name,
                            "x_mc": x_mc,
                            "y_mc": y_mc,
                            "z_mc": z_mc,
                            "x_local": x_local,
                            "y_local": y_local
                        }
                    }
                    features.append(feature)
    
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, indent=2)
    
    print(f"Exported {len(features)} blocks to {output_path}")
```

---

## 5. Usar Minecraft como interfaz de edición territorial

### 5.1 Flujo de trabajo de diseño urbano participativo

```
[Exportar mundo] → [Jugador edita en Minecraft] → [Importar cambios] → [Analizar GeoJSON]
```

1. Generar el mundo con `export_world()`.
2. El jugador coloca bloques representando propuestas: calles nuevas, edificios, áreas verdes.
3. Ejecutar `import_world()` para extraer el diferencial.
4. Analizar `boxes.json` o el `.glb` generado.
5. Opcionalmente: convertir a GeoJSON con `world_to_geojson()`.

### 5.2 Convención de colores para diseño participativo

Dado que el mundo base ya usa bloques con significado, se recomienda usar bloques **específicamente no utilizados por el generador** para intervenciones del jugador:

| Bloque | Propuesta de uso |
|--------|-----------------|
| `minecraft:red_concrete` | Zona a demoler / restricción |
| `minecraft:blue_concrete` | Infraestructura hidráulica |
| `minecraft:cyan_concrete` | Equipamiento comunitario |
| `minecraft:green_concrete` | Área verde propuesta |
| `minecraft:orange_concrete` | Zona de construcción |
| `minecraft:purple_concrete` | Equipamiento especial |
| `minecraft:pink_concrete` | Zona residencial propuesta |
| `minecraft:brown_concrete` | Zona patrimonial |
| `minecraft:magenta_concrete` | Corredor cultural |

### 5.3 Reconstruir calle propuesta desde modificaciones

Si el jugador colocó bloques de calle en una nueva ruta:

```python
def extract_proposed_road(modified_blocks, block_types=None):
    """
    Identifica bloques consecutivos en el plano XZ que forman una calle propuesta.
    Retorna lista de coordenadas GPS de la calle.
    """
    if block_types is None:
        block_types = {"minecraft:yellow_concrete", "minecraft:white_concrete",
                       "minecraft:gray_concrete"}
    
    road_coords = []
    for (x_mc, y_mc, z_mc), block in modified_blocks.items():
        if block in block_types:
            road_coords.append((x_mc, z_mc, y_mc))
    
    # Ordenar por cercanía y convertir a GPS
    gps_coords = []
    for (x_mc, z_mc, y_mc) in sorted(road_coords, key=lambda p: (p[0], p[1])):
        lat, lon = local_to_gps(float(x_mc), float(-z_mc))
        gps_coords.append((lat, lon))
    
    return gps_coords
```

---

## 6. Comportamientos implementados pero sin documentar previamente

### 6.1 Selección determinística de bloques por hash

`get_deterministic_choice(x, y, z, choices, weights)` usa:
```python
h = (int(x) * 73856093) ^ (int(y) * 19349663) ^ (int(z) * 83492791)
normalized = (abs(h) & 0xFFFF) / 65536.0
```

Esto produce pseudoaleatoriedad **no-cryptographic** basada en coordenadas. El mismo `(x, y, z)` siempre produce el mismo bloque. Esto garantiza que regenerar el mundo produce el mismo resultado visual, y que los bloques no cambian al regenerar regiones incrementalmente.

**Implicación:** Si se necesita reidentificar qué bloque específico de asfalto cayó en una posición, se puede recalcular el hash directamente sin leer el archivo MCA.

### 6.2 Ajuste de altura bajo zonas de agua

Cuando una columna tiene agua encima, la altura del terreno se ajusta automáticamente:
```python
# En export_single_region():
if has_chunk_water and local_water_found[idx]:
    y_water_mc = int(round(local_water_y[idx])) - y_offset
    if cached_h >= y_water_mc - 2:
        cached_h = y_water_mc - 3
        height_cache.set(x_val, z_val, cached_h)
```

Si el terreno está a menos de 2 metros bajo el nivel del agua, se baja artificialmente 3 metros para asegurar que la columna de agua tenga al menos 3 bloques de profundidad.

### 6.3 Propagación de estilo vial por nombre normalizado

El `get_normalized_street_name()` elimina prefijos comunes (`calle`, `av`, `blvd`, etc.) y acentos, y convierte a minúsculas. Esto permite que todos los segmentos con el mismo nombre base hereden el estilo más alto encontrado en esa calle, incluso si algunos segmentos tienen clasificaciones OSM incorrectas.

**Ejemplo:** Si "Av. Benito Juárez" tiene un segmento clasificado como `residential` en OSM pero el resto como `secondary`, todos los segmentos se tratarán como `secondary` (estilo `avenida`).

### 6.4 Altura de spawn

El jugador aparece en `(0, spawn_y, 0)` que corresponde a Parque Hidalgo. La altura se calcula:
```python
spawn_y = get_mc_terrain_y(0, 0) + 2
```
Es decir, 2 bloques sobre el nivel del terreno en el centro exacto de la ciudad.

### 6.5 Datapack "Higher Heights"

Si existe un archivo `*HigherHeights*.zip` en el directorio de salida, se copia automáticamente al directorio `datapacks/` del mundo y se activa en `level.dat`. Esto permite que el mundo Minecraft soporte alturas Y superiores a 320, necesario para representar picos de más de ~80m sobre el punto más bajo del área.

El rango vertical activo se determina dinámicamente:
```python
min_s_y = floor((glb_min_y - y_offset) / 16)
max_s_y = ceil((glb_max_y - y_offset) / 16)
```

---

## 7. Consideraciones de rendimiento para desarrolladores

| Operación | Tiempo estimado | Optimización usada |
|-----------|-----------------|-------------------|
| Carga de vértices GLB | 1-5s | NumPy frombuffer |
| Construcción índice terreno | 5-30s | Grilla espacial lazy |
| Consulta de altura (batch) | O(N/cell) | LinearNDInterpolator celda por celda |
| Rasterización de calles | 30-300s | ThreadPoolExecutor + Numba JIT |
| Rasterización de manzanas | 60-600s | ThreadPoolExecutor + Numba JIT |
| Generación de regiones MCA | 60-600s | ProcessPoolExecutor |
| Escaneo de diferencial (import) | 10-120s | ProcessPoolExecutor + 3-tier compare |

**Cuello de botella principal:** La interpolación del TIN para resolución de alturas. El caché de alturas (`terrain_height_cache.json`) elimina este costo en ejecuciones incrementales.

**Numba:** Cuando está disponible, las funciones marcadas con `@njit` se compilan JIT en el primer llamado (≈2-15s de overhead de compilación) pero luego ejecutan a velocidad nativa de C. Esto afecta principalmente a `fill_chunk_jit`, `find_inside_points`, y `query_water_chunk_jit`.
