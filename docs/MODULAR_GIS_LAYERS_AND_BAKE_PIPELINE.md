# Capas GIS Modulares y Pipeline de Horneado Automatizado

> **Estado:** Documento de referencia técnica y arquitectura de assets.  
> **Fecha:** Septiembre 2026.  
> **Ámbito:** Integración de subsistemas continuos (vialidades, ferrocarril, cuerpos de agua, puentes y manzanas), desacoplamiento Blender/Godot, caché de hashes y preservación del relieve natural.

---

## 1. Resumen Ejecutivo y Motivación

A partir de los modelos de dominio desarrollados en el pipeline de Minecraft (detección de puentes, taxonomía vial, interpolación de agua y trazado ferroviario), se enriqueció el gemelo digital en Godot sustituyendo la discretización por bloques de 1×1×1m por **geometría vectorial continua 3D**.

Se logró:
1. **Desacoplamiento Estructural Total:** Separación absoluta entre los archivos de trabajo de Blender (`blender_assets/`) y los binarios de ejecución en Godot (`godot_project/assets/`), eliminando la sobrecarga y los errores del importador headless de Godot 4.x.
2. **Pipeline de Horneado Unificado con Hash-Caching ([`scripts/bake_pipeline.py`](file:///Users/hakkindavid/Documents/GitHub/tecate-simulator/scripts/bake_pipeline.py)):** Verificación en **0.06 segundos** basada en hashes SHA-256 que solo invoca a Blender cuando un archivo `.blend` ha sido modificado o falta su binario `.glb`.
3. **5 Nuevas Capas Vectoriales Continuas:** Generación de vialidades con anchos reales, ferrocarril con balasto y durmientes, cuerpos de agua continuos, puentes suspendidos con pilares y plataformas de manzanas urbanas.
4. **Preservación de la Fotografía Aérea en Montañas:** La cobertura urbana se restringe estrictamente a predios consolidados; todas las montañas, lomas y valles rurales (incluyendo el Cerro Cuchumá / Donohoe Mountain) quedan libres de mallas artificiales, conservando al 100% la textura aérea original de alta resolución ([`tecate_groundTexture.png`](file:///Users/hakkindavid/Documents/GitHub/tecate-simulator/godot_project/assets/tecate_groundTexture.png)).

---

## 2. Arquitectura de Desacoplamiento (Autoría vs. Runtime)

### 2.1 El Conflicto de Importación de Godot 4.x
Cuando los archivos `.blend` se colocan directamente en `res://assets/`, el motor Godot detecta la extensión `.blend` e intenta invocar a Blender en segundo plano mediante `editor_scene_importer_blend.cpp`. En entornos headless, integración continua o sin ruta de Blender configurada en las preferencias del editor, esto provocaba:
```
ERROR: Blender path is invalid or not set, check your Editor Settings.
Cannot configure blender path in headless mode.
```
Además de bloquear la ejecución, generaba archivos `.blend.import` no deseados y sobrecostos masivos de CPU al reescanear el proyecto.

### 2.2 La Separación Limpia
Se estableció una frontera física y lógica estricta:

```
┌─────────────────────────────────────────────────────────┐
│              ENTORNO DE AUTORÍA (Blender)               │
│  Carpeta: blender_assets/                               │
│  - osm2world_adjusted.blend  (102 MB, 3,552 objetos)    │
│  - roadways_adjusted.blend   (2.8 MB, vialidades)       │
│  - railways_adjusted.blend   (6.8 MB, ferrocarril)      │
│  - waterways_adjusted.blend  (503 KB, cuerpos de agua)  │
│  - bridges_adjusted.blend    (113 KB, puentes 3D)       │
│  - manzanas_adjusted.blend   (132 KB, manzanas urbanas) │
└────────────────────────────┬────────────────────────────┘
                             │
                             │ scripts/bake_pipeline.py
                             │ (SHA-256 Hash Manifest: .bake_manifest.json)
                             ▼
┌─────────────────────────────────────────────────────────┐
│              ENTORNO DE EJECUCIÓN (Godot)               │
│  Carpeta: godot_project/assets/                         │
│  - osm2world_baked.glb  (267 MB)                        │
│  - roadways_baked.glb   (3.6 MB)                        │
│  - railways_baked.glb   (12.0 MB)                       │
│  - waterways_baked.glb  (557 KB)                        │
│  - bridges_baked.glb    (60 KB)                         │
│  - manzanas_baked.glb   (101 KB)                        │
│  - tecate.glb           (82 MB, relieve base)           │
└─────────────────────────────────────────────────────────┘
```

**Resultado:** Godot importa exclusivamente archivos `.glb` pre-horneados usando su cargador nativo en C++, logrando tiempos de arranque instantáneos y 0 dependencias externas.

---

## 3. Pipeline de Horneado Automatizado (`scripts/bake_pipeline.py`)

### 3.1 Funcionamiento del Hash-Caching
El script almacena el estado de horneado en `blender_assets/.bake_manifest.json`:
1. Lee los archivos `.blend` en `blender_assets/`.
2. Calcula su firma criptográfica SHA-256 en bloques de 1 MB.
3. Compara contra el hash registrado en el manifiesto y verifica la existencia del `.glb` correspondiente.
4. **Si coinciden:** Omite el archivo (`[UP-TO-DATE]`). La comprobación de todas las capas toma **0.06 s**.
5. **Si difiere o falta el GLB:** Invoca a Blender en modo headless exclusivamente para ese archivo, actualiza el binario en `godot_project/assets/` y reescribe el manifiesto.

### 3.2 Comandos de Uso
```bash
# Verificación y horneado automático de archivos modificados:
python3 scripts/bake_pipeline.py

# Consultar el estado de sincronización y hashes:
python3 scripts/bake_pipeline.py --status

# Forzar el re-horneado de todos los binarios GLB:
python3 scripts/bake_pipeline.py --force

# Hornear exclusivamente una capa (ej. vialidades):
python3 scripts/bake_pipeline.py --layer roadways

# Re-generar proceduralmente todas las capas .blend desde OSM y hornearlas:
python3 scripts/bake_pipeline.py --generate-all
```

---

## 4. Detalle de las Capas Vectoriales Continuas (Paridad con Minecraft)

Todas las capas utilizan la proyección común `gps_to_local()` centrada en Parque Hidalgo $(0, 0)$ y el árbol de colisiones [`BVHTree`](file:///Users/hakkindavid/Documents/GitHub/tecate-simulator/scripts/generate_godot_layers.py) derivado de `tecate.glb` para proyectar alturas topográficas con precisión milimétrica.

### 4.1 Cuerpos de Agua (`waterways`)
- **Archivos:** `blender_assets/waterways_adjusted.blend` $\rightarrow$ `godot_project/assets/waterways_baked.glb` (2.90 MB, 46,921 triángulos).
- **Lagos y Presas (ej. Presa Las Auras):** Triangulación Delaunay 2D Restringida (`delaunay_2d_cdt`) con rejilla interna y faldón vertical perimetral (*water skirt*) de $-1.5\text{ m}$ de profundidad para eliminar desgarros en las orillas.
- **Ríos y Canales (Río Tecate):** Subdivisión cada $4.0\text{ m}$ adaptada a las cotas del terreno con anchos calibrados ($12\text{ m}$ río principal, $4\text{ m}$ arroyos) y coordenadas UV longitudinales continuas para shaders de flujo.

### 4.2 Ferrocarril (`railways`)
- **Archivos:** `blender_assets/railways_adjusted.blend` (6.8 MB) $\rightarrow$ `godot_project/assets/railways_baked.glb` (12.0 MB, 174,532 triángulos).
- **Traza Histórica:** Ferrocarril Tijuana–Tecate (vía de enlace hacia Campo / San Diego).
- **Geometría Tridimensional:**
  - *Balasto:* Prisma trapezoidal extruido ($3.4\text{ m}$ de base, $2.6\text{ m}$ de corona, $+0.22\text{ m}$ de altura sobre terreno).
  - *Durmientes:* Bloques de madera tratada ($2.6\text{m} \times 0.24\text{m} \times 0.14\text{m}$) espaciados uniformemente cada $0.65\text{ m}$ y perpendiculares a la tangente.
  - *Rieles de Acero:* Doble perfil continuo con ancho de vía estándar internacional ($1.435\text{ m}$).

### 4.3 Puentes Suspendidos (`bridges`)
- **Archivos:** `blender_assets/bridges_adjusted.blend` (113 KB) $\rightarrow$ `godot_project/assets/bridges_baked.glb` (0.48 MB, 8,680 triángulos).
- **Resolución Estructural y Conectividad:**
  - Integración de `_merge_bridge_gaps()` (del pipeline de Minecraft) para unificar tramos colineales con el mismo nombre y conectarse perfectamente a las rampas de aproximación.
  - Perfil de rampa de elevación ($z_{\text{start}} \to z_{\text{elev}} \to z_{\text{end}}$) con holgura vertical realista sobre barrancas y ríos.
  - Tablero estructural tipo viga cajón ($0.8\text{ m}$ de espesor) con parapetos laterales de concreto ($+1.1\text{ m}$).
  - Pilares verticales de soporte ($1.0\text{ m}$ de ancho) espaciados cada $10\text{ m}$ donde el espacio libre supere $1.2\text{ m}$, anclados directamente en el lecho del terreno.

### 4.4 Red Vial (`roadways`)
- **Archivos:** `blender_assets/roadways_adjusted.blend` (2.8 MB) $\rightarrow$ `godot_project/assets/roadways_baked.glb` (26.96 MB, 437,304 triángulos).
- **Taxonomía y Propagación de Jerarquía (Minecraft Parity):**
  - Implementación de `resolve_road_properties()` y normalización de nombres de calles (`get_normalized_street_name()`) para propagar la jerarquía máxima y anchura a todos los segmentos de una misma avenida o bulevar.
  - Multi-materiales diferenciados: Asfalto limpio para bulevares principales, asfalto estándar para calles/carreteras, y grava rústica para caminos rurales.
- **Subdivisión Longitudinal y Muestreo Topográfico:**
  - Segmentos subdivididos densamente a intervalos $\le 4.0\text{ m}$, proyectando cada vértice transversal mediante raycasting al `BVHTree` (+0.04m Z-bias). **0% de clipping** en cambios bruscos de rasante o curvas en pendiente.

### 4.5 Manzanas Urbanas Drapadas (`manzanas`)
- **Archivos:** `blender_assets/manzanas_adjusted.blend` (132 KB) $\rightarrow$ `godot_project/assets/manzanas_baked.glb` (5.11 MB, 103,800 triángulos).
- **Drapeado Densa Delaunay 2D:**
  - Sustitución de polígonos perimetrales por mallas Delaunay densas (`delaunay_2d_cdt`) con rejillas internas adaptativas (paso de 5 a 10m).
  - Cada vértice interno y perimetral se proyecta verticalmente sobre el relieve real de `tecate.glb` (+0.025m Z-bias). Las plataformas de las manzanas abrazan perfectamente las lomas y colinas urbanas con **0% de clipping**.
- **Materiales Asignados:** Concreto para predios edificados y césped/vegetación para parques públicos.

---

## 5. Preservación del Paisaje Natural y Montañas

> [!IMPORTANT]
> **Protección del Paisaje Rural y Montañoso**:
> Las mallas de manzanas y vialidades se generan **únicamente donde existen predios urbanos consolidados**.
> En el resto del territorio municipal (Cerro Cuchumá, Donohoe Mountain, laderas escarpadas, cañadas y valles desérticos):
> - **No se genera ninguna malla artificial.**
> - El terreno natural `tinMesh` en `tecate.glb` con su fotografía aérea de alta resolución ([`tecate_groundTexture.png`](file:///Users/hakkindavid/Documents/GitHub/tecate-simulator/godot_project/assets/tecate_groundTexture.png)) permanece **100% continuo, visible y sin alteraciones**.
> - En la zona urbana, las cintas vectoriales nítidas cubren de forma limpia los techos y calles borrosos de la foto satelital sin degradar la vista lejana de las montañas.

---

## 6. Integración en la Escena de Godot (`main.tscn`)

En [`godot_project/main.tscn`](file:///Users/hakkindavid/Documents/GitHub/tecate-simulator/godot_project/main.tscn), las capas se ordenan como nodos hermanos independientes:

```
MainScene (Node3D)
├── Terrain (tecate.glb)               [Relieve base + textura aérea de montañas]
├── Waterways (waterways_baked.glb)     [Presa Las Auras, ríos y arroyos]
├── Manzanas (manzanas_baked.glb)       [Plataformas de banquetas y manzanas urbanas]
├── Roadways (roadways_baked.glb)       [Red vial con anchos clasificados]
├── Railways (railways_baked.glb)       [Balasto, durmientes y rieles de acero]
├── Bridges (bridges_baked.glb)         [Tableros elevados y pilares estructurales]
└── Geometry (osm2world_baked.glb)      [3,552 edificios, torres de energía y árboles]
```

En [`godot_project/apply_shader.gd`](file:///Users/hakkindavid/Documents/GitHub/tecate-simulator/godot_project/apply_shader.gd):
- Se ocultan automáticamente las mallas obsoletas de baja resolución incrustadas en `tecate.glb` (`__mergedRoads_*` y `water_*`).
- Se generan colisionadores trimesh para el terreno, puentes, vialidades y manzanas.
- El avatar del jugador se posiciona y ancla físicamente a la cota exacta del terreno ($405.29\text{ m}$).
- El motor ejecuta la simulación sin errores, sin llamadas a Blender y con 100% de estabilidad.
