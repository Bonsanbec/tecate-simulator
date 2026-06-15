# Semántica de Bloques: Significado Geográfico de Cada Bloque en Minecraft

## Principio fundamental

> **Cada bloque en el mundo Minecraft generado corresponde a exactamente 1 m² de superficie geográfica real de Tecate, B.C., México, y su tipo de bloque codifica la clase de elemento geográfico que representa.**

La posición de cualquier bloque `(X_mc, Y_mc, Z_mc)` se puede invertir a coordenadas geográficas GPS con error submétrico usando:
```
x_local = X_mc                    → metros al Este de Parque Hidalgo
y_local = -Z_mc                   → metros al Norte de Parque Hidalgo
H_real  = Y_mc + y_offset         → metros de altitud real
lat, lon = local_to_gps(x_local, y_local)
```

---

## 1. Capas de generación y orden de prioridad

El mundo se genera en tres capas que se sobreescriben en cascada:

```
[CAPA 1: Geología] → [CAPA 2: Superficie] → [CAPA 3: Infraestructura urbana]
    (fill_chunk_jit)    (fill_chunk_jit)      (custom_blocks: calles + manzanas)
```

Los bloques de la capa 3 sobreescriben a los de la capa 2, que sobreescriben a los de la capa 1.

---

## 2. Significado por bloque — Referencia completa

### 2.1 Bloques de geología subsuperficial

| Bloque Minecraft | ID JIT | Significado geográfico | Condición |
|-----------------|--------|----------------------|-----------|
| `minecraft:stone` | 1 | Roca madre / subsuelo profundo | `Y < Y_terreno - 3` (más de 3m bajo superficie) |
| `minecraft:dirt` | 2 | Capa de suelo/tierra superior | `Y_terreno - 3 ≤ Y < Y_terreno` (los 3 últimos metros antes de superficie) |

Estos bloques **nunca son visibles** en condiciones normales. Representan la estructura interna del terreno. Su profundidad relativa a la superficie es geológicamente significativa.

---

### 2.2 Bloques de superficie — Terreno no urbanizado

La superficie (bloque en `Y == Y_terreno`) varía según la **clasificación OSM del uso de suelo**:

#### Clase: `grass` (default)

| Bloque | Significado | Condición |
|--------|-------------|-----------|
| `minecraft:grass_block` | Suelo natural / área verde | superficie en zona de vegetación (parques, jardines, bosque, pastizal, etc.) |

Fuentes OSM que generan superficie de grass: `landuse=grass/meadow/forest/orchard/cemetery`, `leisure=park/garden/pitch/playground`, `natural=wood/grassland/scrub/heath`, `surface=grass`.

#### Clase: `paved` (pavimentado)

La superficie en zonas pavimentadas usa mezcla determinística:

| Bloque | Significado | Peso | Probabilidad |
|--------|-------------|------|-------------|
| `minecraft:andesite` | Pavimento concreto (claro) | 0.6 | 60% |
| `minecraft:polished_andesite` | Pavimento concreto (pulido) | 0.3 | 30% |
| `minecraft:stone_bricks` | Pavimento de piedra | 0.1 | 10% |

Fuentes OSM que generan superficie paved: `landuse=industrial/commercial/retail/construction/military`, `surface=paved/asphalt/concrete/cobblestone`, `amenity=parking/marketplace`.

#### Clase: `dirt` (tierra/sin pavimentar)

| Bloque | Significado | Peso | Probabilidad |
|--------|-------------|------|-------------|
| `minecraft:coarse_dirt` | Tierra compactada (dura) | 0.6 | 60% |
| `minecraft:dirt` | Tierra suelta | 0.3 | 30% |
| `minecraft:gravel` | Grava superficial | 0.1 | 10% |

Fuentes OSM: `natural=sand/mud/shingle/scree`, `surface=dirt/unpaved/gravel/earth/ground/sand/clay`.

---

### 2.3 Bloques de agua

| Bloque | Significado | Condición |
|--------|-------------|-----------|
| `minecraft:water` | Columna de agua (cuerpo de agua) | `Y_terreno < Y ≤ Y_agua` donde hay agua OSM |
| `minecraft:sand` | Fondo de cuerpo de agua | `Y == Y_terreno` cuando la columna tiene agua encima |
| `minecraft:dirt` | Subsuelo bajo agua (capa superior) | `Y_terreno - 3 ≤ Y < Y_terreno` con agua encima |
| `minecraft:stone` | Roca madre bajo agua | `Y < Y_terreno - 3` con agua encima |

Los cuerpos de agua se modelan a partir de `natural=water` y `waterway=*` de OSM, triangulados con Delaunay. La altura del agua sigue la topografía real del terreno.

---

### 2.4 Bloques de calles — Superficie vial

#### Calles rurales / sin pavimentar

Mezcla determinística por coordenada:

| Bloque | Significado | Peso |
|--------|-------------|------|
| `minecraft:gravel` | Calle de grava / camino rural | 0.50 |
| `minecraft:cobblestone` | Calle empedrada histórica | 0.25 |
| `minecraft:coarse_dirt` | Camino de tierra compactada | 0.15 |
| `minecraft:andesite` | Calle de piedra | 0.05 |
| `minecraft:mossy_cobblestone` | Empedrado con vegetación | 0.05 |

Aplica a `highway = unclassified/service/living_street/track/path/bridleway` sin nombre.

#### Calles urbanas — Asfalto normal (`asphalt`)

| Bloque | Significado | Peso |
|--------|-------------|------|
| `minecraft:gray_concrete_powder` | Asfalto gris oscuro | 0.60 |
| `minecraft:black_concrete_powder` | Asfalto negro | 0.25 |
| `minecraft:smooth_basalt` | Asfalto muy oscuro | 0.05 |
| `minecraft:cobbled_deepslate` | Asfalto granulado | 0.05 |
| `minecraft:coal_block` | Asfalto negro intenso | 0.05 |

#### Calles urbanas — Asfalto limpio (`asphalt_clean` — Boulevards)

| Bloque | Significado | Peso |
|--------|-------------|------|
| `minecraft:gray_concrete` | Pavimento de boulevard (limpio) | 0.80 |
| `minecraft:black_concrete` | Pavimento de boulevard (oscuro) | 0.20 |

#### Calles urbanas — Asfalto ligero (`asphalt_light` — Calles locales)

| Bloque | Significado | Peso |
|--------|-------------|------|
| `minecraft:gray_concrete_powder` | Asfalto local (claro) | 0.70 |
| `minecraft:andesite` | Calle con material mixto | 0.20 |
| `minecraft:gravel` | Calle con grava | 0.10 |

---

### 2.5 Bloques de marcas viales

Las marcas viales se colocan **encima del asfalto** en la misma Y que el carril. Codifican la clasificación jerárquica de la vía:

| Bloque | Significado geográfico | Tipo de marca | Jerarquía |
|--------|----------------------|---------------|-----------|
| `minecraft:yellow_concrete` | Línea amarilla sólida doble | Centro de highway/autopista | Máxima |
| `minecraft:yellow_concrete` (punteado) | Línea amarilla discontinua | Centro de boulevard/avenida | Alta |
| `minecraft:white_concrete` | Línea blanca lateral | Borde de carril / carretera | Media |
| `minecraft:white_concrete` (punteado) | Línea blanca discontinua de carril | Divisor de carriles / calle | Normal |

**Regla de codificación de jerarquía vial por marcas:**

```
Sin marcas (superficie sin demarcación) → Rural / camino sin jerarquía
white_concrete punteado en centro       → Calle local (calle, privada, callejón)
yellow_concrete punteado en centro      → Avenida / boulevard
yellow_concrete sólido en centro        → Autopista / carretera federal
```

Las marcas están **ausentes a ≤4 bloques de distancia de una intersección** para representar las zonas de cruce.

---

### 2.6 Bloques de manzanas urbanas (lots/blocks)

| Bloque | Significado | Ubicación |
|--------|-------------|-----------|
| `minecraft:smooth_stone` | Plataforma de manzana urbana | `Y_terreno + 1` en interior de polígono de manzana |

Las manzanas representan los **bloques urbanísticos de Tecate** tal como los delimita la red vial. Cada manzana es un polígono del `reconstruction_export.json` cuya geometría fue derivada del grafo OSM. El bloque `smooth_stone` en Y+1 sobre el terreno crea una plataforma urbana ligeramente elevada sobre el nivel del suelo natural, simulando el pavimento urbano a nivel de banqueta.

**Nota importante:** Las manzanas se rasterizaron **después** de las calles, y sus bloques sobreescriben cualquier bloque de calle que quede debajo del polígono de manzana. Esto crea una separación visual clara entre calles y predios.

---

### 2.7 Bloques de infraestructura de puentes

| Bloque | Significado | Ubicación |
|--------|-------------|-----------|
| `minecraft:cobblestone` | Pilares de puente | Columnas verticales desde terreno hasta Y_puente, en bordes |
| `minecraft:air` | Espacio libre bajo puente | 4 bloques sobre el nivel del piso del puente |

Los pilar de puente aparecen **cada 8 pasos** (≈8 metros) a lo largo del puente, en los bloques del borde exterior del carril.

---

## 3. Cómo leer el mundo como mapa urbano

### 3.1 Identificar un punto geográfico desde MC

Dado un bloque en `(X_mc, Y_mc, Z_mc)`:

```python
# Reconstruir posición geográfica
x_local = X_mc           # Este (m)
y_local = -Z_mc          # Norte (m)
H_real  = Y_mc + y_offset  # Altitud (m)

lat, lon = local_to_gps(x_local, y_local)
print(f"GPS: {lat:.6f}, {lon:.6f}")
print(f"Altura: {H_real:.1f} m")
```

### 3.2 Identificar el tipo de elemento por bloque

```python
def classify_block(block_name, y_mc, terrain_y_mc):
    if block_name == "minecraft:water":
        return "agua superficial"
    if block_name == "minecraft:sand" and y_mc == terrain_y_mc:
        return "fondo de cuerpo de agua"
    if block_name == "minecraft:smooth_stone":
        return "manzana urbana"
    if block_name in ["minecraft:yellow_concrete", "minecraft:white_concrete"]:
        return "marca vial"
    if block_name in ["minecraft:gray_concrete", "minecraft:black_concrete",
                      "minecraft:gray_concrete_powder", "minecraft:black_concrete_powder",
                      "minecraft:smooth_basalt", "minecraft:cobbled_deepslate",
                      "minecraft:coal_block"]:
        return "calzada asfaltada"
    if block_name in ["minecraft:gravel", "minecraft:cobblestone",
                      "minecraft:coarse_dirt", "minecraft:mossy_cobblestone"]:
        return "vía rural / camino sin pavimentar"
    if block_name == "minecraft:grass_block":
        return "superficie natural / área verde"
    if block_name in ["minecraft:andesite", "minecraft:polished_andesite",
                      "minecraft:stone_bricks"]:
        return "superficie pavimentada (no vial)"
    if block_name in ["minecraft:coarse_dirt", "minecraft:gravel"] and y_mc == terrain_y_mc:
        return "superficie de tierra / sin pavimentar"
    if block_name == "minecraft:dirt":
        return "subsuelo superior"
    if block_name == "minecraft:stone":
        return "roca madre"
    if block_name == "minecraft:cobblestone":
        return "pilar de puente"
    return "desconocido"
```

### 3.3 Identificar el nombre de la calle por posición

Dado un bloque de calle `(X_mc, Z_mc)`, se puede consultar cuál arista del grafo vial lo generó:
1. Convertir `(X_mc, Z_mc)` a `(x_local, y_local) = (X_mc, -Z_mc)`.
2. Para cada arista del grafo vial, calcular la distancia perpendicular del punto al segmento.
3. La arista con mínima distancia perpendicular que sea ≤ `width/2 + 1.5` metros es la generadora.
4. El nombre de esa arista es el nombre de la calle.

### 3.4 Leer la topografía desde el mundo

La altura `Y_mc` de los bloques de superficie codifica la topografía real del terreno. Para reconstruir un perfil de terreno:

```python
# Para cada columna (X_mc, Z_mc), el bloque de superficie está en Y_mc = Y_terreno
# H_real = Y_mc + y_offset (metros sobre referencia)

# Ejemplo: generar mapa de curvas de nivel
terrain_data = {}
for x in range(min_x, max_x):
    for z in range(min_z, max_z):
        y_surface = find_topmost_non_air_block(world, x, z)
        h_real = y_surface + y_offset
        terrain_data[(x, z)] = h_real
```

---

## 4. Invariantes del sistema

Las siguientes propiedades son garantizadas por el pipeline y deben preservarse en cualquier extensión:

1. **Escala 1:1:** 1 bloque = 1 metro real. No hay factor de escala adicional.
2. **Origen geográfico:** `(0, 0, Y_spawn)` en Minecraft = Parque Hidalgo, Tecate, B.C.
3. **Eje Norte:** `-Z_mc` apunta al Norte geográfico. `+Z_mc` apunta al Sur.
4. **Offset persistente:** `y_offset` no cambia entre ejecuciones del mismo mundo.
5. **Determinismo:** El mismo JSON + GLB siempre produce el mismo mundo (bloques determinísticos por hash de coordenadas).
6. **Sin solapamiento calle/manzana:** Las manzanas sobreescriben las calles, nunca al revés.
7. **Calles sobre terreno:** Los bloques de calle se colocan en `Y_terreno` (no en Y arbitrario).

---

## 5. Ejemplo concreto: Av. Benito Juárez

Si la Av. Benito Juárez pasa por las coordenadas locales `x ∈ [-200, -150]`, `y ≈ 50`:

1. En Minecraft: `X_mc ∈ [-200, -150]`, `Z_mc ≈ -50`
2. El segmento se rasterizó como `avenida` (porque el nombre contiene "av")
3. Ancho: 9 bloques centrados en el centerline
4. Superficie: mezcla de `gray_concrete_powder/black_concrete_powder/smooth_basalt` (asfalto normal)
5. Centro de la calle: `yellow_concrete` discontinuo (cada 4 bloques: 2 on / 2 off)
6. Bordes: `white_concrete` lateral
7. Altura de los bloques sigue el perfil topográfico real del cerro bajo la avenida

Al leer el mundo desde Minecraft, ver una calle con línea amarilla discontinua y bordes blancos indica inequívocamente que se trata de una **avenida o vía de tráfico medio-alto**.
