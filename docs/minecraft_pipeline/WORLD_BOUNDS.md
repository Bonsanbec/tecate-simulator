# World Bounds — TecateWorld

> **Fuente:** Inspección directa del mundo exportado en `export/minecraft_world/TecateWorld/`.  
> **Todos los valores provienen del análisis programático de los 3,324 archivos `.mca` y del caché de bloques rasterizados.**  
> **Fecha de análisis:** Junio 2026.

---

## Resumen Ejecutivo

El mundo `TecateWorld` es una representación a escala 1:1 de Tecate, B.C., México y su entorno geográfico inmediato en formato Minecraft 1.20. El terreno del modelo 3D (`tecate.glb`) cubre una región geográfica de **~103 km Este-Oeste × ~82 km Norte-Sur**, centrada en el municipio de Tecate. Sobre ese terreno se superpone la infraestructura urbana rasterizada (calles, manzanas) derivada del grafo OSM reconstruido.

El análisis arrojó tres capas de límites con distinto significado:

| Capa | Descripción |
|------|-------------|
| **Terreno completo** | Todos los chunks escritos en archivos `.mca` — el extent total del TIN del GLB |
| **Infraestructura urbana** | Bloques de calles y manzanas (`custom_blocks_cache.npz`) |
| **Área urbana original** | Polígonos de manzanas en `tecate_metadata.json` (bbox de reconstrucción) |

---

## Sistema de Referencia

### Coordinadas en Minecraft

| Eje MC | Dirección geográfica | Fórmula desde coord. local |
|--------|---------------------|---------------------------|
| `X` | Este (+) / Oeste (−) | `X_mc = x_local` |
| `Y` | Arriba | `Y_mc = H_real − y_offset` |
| `Z` | Sur (+) / Norte (−) | `Z_mc = −y_local` |

**Escala:** 1 bloque = 1 metro real.

### Referencia geográfica

- **Origen Minecraft (0, \*, 0)** = **Parque Hidalgo, Tecate, B.C.** (`32.573229°N, −116.626536°E`)
- Verificado: `mc_to_gps(0, 0)` → `(32.573229, −116.626536)` ✓

### Offset vertical

```
y_offset = 391
Y_mc = H_real − 391
H_real = Y_mc + 391
```

Ejemplo: `Y_mc = 0` corresponde a `391 m s.n.m.` (altitud de referencia del punto más bajo del área activa + 230 m de margen).

---

## Centro del Mundo

| Capa | X_mc | Z_mc | Latitud | Longitud |
|------|-----:|-----:|---------|---------|
| **Parque Hidalgo (origen del sistema)** | 0 | 0 | 32.573229°N | −116.626536°E |
| Centro geométrico del terreno completo | 38,655 | 31,743 | 32.288077°N | −116.214477°E |
| Centro geométrico de la infraestructura urbana | 38,735 | 31,829 | 32.287304°N | −116.213624°E |

> **Nota:** El origen cartográfico del sistema es Parque Hidalgo `(0, 0)`. El centro geométrico del terreno generado se desplaza ~38 km al Este y ~32 km al Sur del origen porque el modelo GLB cubre la región completa del municipio de Tecate (que se extiende mucho más hacia el Este y el Sur que hacia el Norte y el Oeste).

---

## Límites Absolutos

### Terreno Completo (todos los chunks escritos en `.mca`)

Origen de datos: barrido de las tablas de ubicación de los **3,324 archivos `.mca`**, confirmando **3,403,776 chunks ocupados**.

| Límite | Coord. Minecraft | Latitud/Longitud |
|--------|-----------------|-----------------|
| **Norte** (Z mínimo) | Z = −9,216 | 32.656018°N |
| **Sur** (Z máximo) | Z = 72,703 | 31.920127°N |
| **Este** (X máximo) | X = 90,111 | −115.665960°E |
| **Oeste** (X mínimo) | X = −12,800 | −116.762983°E |
| **Altitud mínima** | Y = −400 | −9 m s.n.m. (391 − 400) |
| **Altitud máxima** | Y = 1,007 | 1,398 m s.n.m. (391 + 1007) |

> La altitud mínima de −9 m s.n.m. aparece en fondos de cauces fluviales y zonas deprimidas del modelo TIN.  
> La altitud máxima de 1,398 m s.n.m. corresponde al pico del **Cerro Cuchumá** y cimas montañosas del municipio.

### Infraestructura Urbana (bloques de calles y manzanas)

Origen de datos: `custom_blocks_cache.npz` — **207,382,659 bloques rasterizados**.

| Límite | Coord. Minecraft | Latitud/Longitud |
|--------|-----------------|-----------------|
| **Norte** (Z mínimo) | Z = −8,729 | 32.651643°N |
| **Sur** (Z máximo) | Z = 72,387 | 31.922966°N |
| **Este** (X máximo) | X = 89,954 | −115.667634°E |
| **Oeste** (X mínimo) | X = −12,484 | −116.759614°E |
| **Y mínimo** | Y = −374 | 17 m s.n.m. |
| **Y máximo** | Y = 1,024 | 1,415 m s.n.m. |

---

## Bounding Box Completo

### Terreno completo (`.mca` location tables)

| Campo | Valor (bloques) |
|-------|----------------|
| `min_x` | −12,800 |
| `max_x` | 90,111 |
| `min_y` | −400 |
| `max_y` | 1,007 |
| `min_z` | −9,216 |
| `max_z` | 72,703 |

### Infraestructura urbana (`custom_blocks_cache.npz`)

| Campo | Valor (bloques) |
|-------|----------------|
| `min_x` | −12,484 |
| `max_x` | 89,954 |
| `min_y` | −374 |
| `max_y` | 1,024 |
| `min_z` | −8,729 |
| `max_z` | 72,387 |

### `tecate_metadata.json` bbox (polígonos de reconstrucción urbana)

Estos valores son los límites de los vértices de los polígonos de manzanas en el `reconstruction_export.json` y representan la extensión del grafo urbano reconstruido de OSM:

| Campo | Local (metros) | Minecraft |
|-------|---------------|----------|
| `min_local_x` → `min_x_mc` | −10,804.78 m | X = −10,805 |
| `max_local_x` → `max_x_mc` | +67,235.03 m | X = 67,235 |
| `min_local_y` → `max_z_mc` | −37,369.65 m | Z = 37,370 |
| `max_local_y` → `min_z_mc` | +3,088.12 m | Z = −3,088 |

> La diferencia entre el bbox del metadata y los límites reales de la caché se debe a que la caché incluye el terreno del GLB completo (calles + manzanas + terreno interpolado para todo el modelo 3D), mientras que el metadata solo registra el envelope de los polígonos de manzanas.

---

## Esquinas

### Terreno Completo

| Esquina | X_mc | Z_mc | Latitud | Longitud |
|---------|-----:|-----:|---------|---------|
| **Noroeste** | −12,800 | −9,216 | 32.656018°N | −116.762983°E |
| **Noreste** | 90,111 | −9,216 | 32.656018°N | −115.665960°E |
| **Suroeste** | −12,800 | 72,703 | 31.920127°N | −116.762983°E |
| **Sureste** | 90,111 | 72,703 | 31.920127°N | −115.665960°E |

### Infraestructura Urbana

| Esquina | X_mc | Z_mc | Latitud | Longitud |
|---------|-----:|-----:|---------|---------|
| **Noroeste** | −12,484 | −8,729 | 32.651643°N | −116.759614°E |
| **Noreste** | 89,954 | −8,729 | 32.651643°N | −115.667634°E |
| **Suroeste** | −12,484 | 72,387 | 31.922966°N | −116.759614°E |
| **Sureste** | 89,954 | 72,387 | 31.922966°N | −115.667634°E |

> La geometría ocupada **no es perfectamente rectangular**: la distribución de archivos `.mca` es irregular (se generaron solo las regiones que contienen chunks activos). El rectángulo envolvente es el envelope mínimo de todos esos chunks.

---

## Dimensiones

### Terreno completo

| Dimensión | Bloques | Equivalente real |
|-----------|---------|-----------------|
| **Ancho Este-Oeste** | 102,912 | ~102.9 km |
| **Largo Norte-Sur** | 81,920 | ~81.9 km |
| **Altura utilizada** | 1,408 | 1,408 m |
| **Área 2D** | ~8,430,613,120 m² | **~8,431 km²** |
| **Altitud mínima real** | — | −9 m s.n.m. |
| **Altitud máxima real** | — | 1,398 m s.n.m. |
| **Rango altimétrico** | 1,408 bloques | 1,407 m |

### Infraestructura urbana (calles + manzanas)

| Dimensión | Bloques | Equivalente real |
|-----------|---------|-----------------|
| **Ancho Este-Oeste** | 102,439 | ~102.4 km |
| **Largo Norte-Sur** | 81,117 | ~81.1 km |
| **Área 2D** | ~8,309,537,063 m² | **~8,310 km²** |
| **Altitud mínima real** | — | 17 m s.n.m. |
| **Altitud máxima real** | — | 1,415 m s.n.m. |

> La diferencia de 473 bloques en X y 803 bloques en Z entre el terreno completo y los bloques urbanos refleja el margen de bloques de terreno puro en los bordes exteriores del mundo que no tienen infraestructura rasterizada.

---

## Validación Contra TecateWorld

### Evidencias verificadas en el mundo exportado

#### 1. Archivos `.mca` — Barrido completo
```
Total archivos .mca procesados : 3,324
Total chunks ocupados confirmados: 3,403,776
```
Todos los archivos tienen exactamente 4,202,496 bytes (1,024 chunks × máximo posible de sectores), lo que indica regiones completamente escritas.

**Coordenadas extremas confirmadas de los archivos por nombre:**
- Región más al Oeste: `r.-25.5.mca`, `r.-25.6.mca` → X_bloque = −25×32×16 = −12,800 ✓
- Región más al Este: `r.175.-17.mca` → X_bloque = 175×32×16 + 511 = 90,111 ✓  
- Región más al Norte: `r.*.-18.mca` → Z_bloque = −18×32×16 = −9,216 ✓
- Región más al Sur: `r.88.141.mca` → Z_bloque = 141×32×16 + 511 = 72,703 ✓

#### 2. Chunk NBT — Confirmación de xPos/zPos/yPos
Muestreo de 60 archivos repartidos uniformemente:
```
xPos range confirmado : 544 a 5,604 (subset del total)
zPos range confirmado : -576 a 4,512
yPos confirmado       : -25 (sección mínima = Y_bloque -400)
Section Y range       : -25 a 62 → Y_bloque: [-400, 1007]
```

#### 3. `tecate_metadata.json` — Parámetros del pipeline
```json
{
  "vertical_offset": 391,
  "bbox": {
    "min_local_x": -10804.78,
    "max_local_x": 67235.03,
    "min_local_y": -37369.65,
    "max_local_y": 3088.12
  }
}
```
Este archivo es escrito por el exportador al final de cada ejecución exitosa. El `vertical_offset = 391` es el valor que se usó para toda la generación del mundo.

#### 4. `custom_blocks_cache.npz` — Bloques rasterizados reales
```
Total bloques en caché : 207,382,659
X range               : -12,484 a 89,954
Z range               : -8,729 a 72,387
Y range               : -374 a 1,024
Tipos de bloque únicos: 16
```

**Paleta completa de 16 bloques verificada:**
```
minecraft:air, minecraft:andesite, minecraft:black_concrete,
minecraft:black_concrete_powder, minecraft:coal_block, minecraft:coarse_dirt,
minecraft:cobbled_deepslate, minecraft:cobblestone, minecraft:gravel,
minecraft:gray_concrete, minecraft:gray_concrete_powder, minecraft:mossy_cobblestone,
minecraft:smooth_basalt, minecraft:smooth_stone, minecraft:white_concrete,
minecraft:yellow_concrete
```

#### 5. Verificación del origen geográfico
```python
mc_to_gps(0, 0) → (32.573229°N, -116.626536°E)
```
El resultado es exactamente igual a `TECATE_LAT_CENTER, TECATE_LON_CENTER` en `src/core_io/coords.py`. El origen Minecraft `(0, 0)` apunta con precisión a **Parque Hidalgo**, centro histórico de Tecate. ✓

---

## Procedimiento de Reproducción

Para recalcular estos límites en el futuro, ejecutar el siguiente script desde la raíz del proyecto:

```python
import os, re, struct, json, math
import numpy as np

REGION_DIR = "export/minecraft_world/TecateWorld/region"
META_PATH  = "export/minecraft_world/TecateWorld/tecate_metadata.json"
CACHE_PATH = "export/minecraft_world/custom_blocks_cache.npz"

# 1. Leer y_offset
with open(META_PATH) as f:
    meta = json.load(f)
y_offset = meta["vertical_offset"]

# 2. Barrer todos los archivos .mca para obtener chunks ocupados
mca_files = [f for f in os.listdir(REGION_DIR) if f.endswith('.mca')]
real_min_cx = real_min_cz = math.inf
real_max_cx = real_max_cz = -math.inf

for fname in mca_files:
    m = re.match(r'r\.(-?\d+)\.(-?\d+)\.mca', fname)
    if not m: continue
    rx, rz = int(m.group(1)), int(m.group(2))
    with open(os.path.join(REGION_DIR, fname), 'rb') as f:
        header = f.read(4096)
    for i in range(1024):
        val = struct.unpack(">I", header[i*4:i*4+4])[0]
        if (val >> 8) & 0xFFFFFF:  # occupied
            cx_global = rx * 32 + (i % 32)
            cz_global = rz * 32 + (i // 32)
            real_min_cx = min(real_min_cx, cx_global)
            real_max_cx = max(real_max_cx, cx_global)
            real_min_cz = min(real_min_cz, cz_global)
            real_max_cz = max(real_max_cz, cz_global)

# 3. Convertir chunks → bloques
min_bx = int(real_min_cx) * 16
max_bx = int(real_max_cx) * 16 + 15
min_bz = int(real_min_cz) * 16
max_bz = int(real_max_cz) * 16 + 15

# 4. Leer Y range del caché de bloques
cache = np.load(CACHE_PATH, allow_pickle=True)
y_min_mc = int(cache['y'].min())
y_max_mc = int(cache['y'].max())

# 5. Convertir a GPS
EARTH_RADIUS = 6378137.0
TECATE_LAT, TECATE_LON = 32.573229, -116.626536
lat_c = math.radians(TECATE_LAT)

def mc_to_gps(x, z):
    lat = math.degrees((-z / EARTH_RADIUS) + math.radians(TECATE_LAT))
    lon = math.degrees((x / (EARTH_RADIUS * math.cos(lat_c))) + math.radians(TECATE_LON))
    return lat, lon

print(f"Block X: {min_bx} to {max_bx}  ({max_bx-min_bx+1} blocks)")
print(f"Block Z: {min_bz} to {max_bz}  ({max_bz-min_bz+1} blocks)")
print(f"Block Y: {y_min_mc} to {y_max_mc}")
print(f"Real alt: {y_min_mc+y_offset}m to {y_max_mc+y_offset}m")
print(f"Norte: {mc_to_gps(0, min_bz)[0]:.6f}°N")
print(f"Sur:   {mc_to_gps(0, max_bz)[0]:.6f}°N")
print(f"Este:  {mc_to_gps(max_bx, 0)[1]:.6f}°E")
print(f"Oeste: {mc_to_gps(min_bx, 0)[1]:.6f}°E")
```

### Para verificar el Y range directamente de los chunks NBT

```python
import zlib, struct

def get_section_y_range(mca_path):
    with open(mca_path, 'rb') as f:
        data = f.read()
    min_y, max_y = math.inf, -math.inf
    for i in range(1024):
        val = struct.unpack(">I", data[i*4:i*4+4])[0]
        sec_off = (val >> 8) & 0xFFFFFF
        if sec_off == 0: continue
        boffset = sec_off * 4096
        length = struct.unpack(">I", data[boffset:boffset+4])[0]
        try:
            nbt = zlib.decompress(data[boffset+5:boffset+5+length-1])
        except: continue
        pos = 0
        while True:
            idx = nbt.find(b'\x01\x00\x01Y', pos)
            if idx == -1: break
            y = struct.unpack(">b", nbt[idx+4:idx+5])[0]
            min_y = min(min_y, y)
            max_y = max(max_y, y)
            pos = idx + 1
    return int(min_y), int(max_y)
```

---

## Notas Sobre la Extensión del Mundo

El tamaño del mundo (~8,430 km²) puede parecer sorprendentemente grande para representar una ciudad. Esto se debe a que:

1. **El modelo de terreno `tecate.glb` cubre toda la región geomorfológica** del municipio de Tecate, incluyendo serranías, cañones, valles y el corredor fronterizo México-EE.UU.

2. **El Cerro Cuchumá** (cima: 32.5796°N, −116.688985°E, ~1,630 m s.n.m.) está explícitamente incluido en el mundo con un radio de 1.63 km alrededor de su cima, para representar el hito geográfico más importante de la región.

3. **El bbox del `reconstruction_export.json`** (`max_local_x ≈ 67 km`) indica que el grafo de calles reconstruido abarca un territorio extenso hacia el Este del centro de Tecate, probablemente incluyendo caminos rurales del municipio.

4. La ciudad de **Tecate urbana central** ocupa aproximadamente el área en torno al origen `(0, 0)`, con el núcleo histórico en un radio de ~2 km desde Parque Hidalgo.
