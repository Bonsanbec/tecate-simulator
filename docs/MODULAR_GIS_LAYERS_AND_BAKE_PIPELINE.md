# Capas GIS Modulares y Pipeline de Horneado Automatizado

> **Estado:** Documento de referencia técnica y arquitectura de assets.  
> **Fecha:** Septiembre 2026 (Actualizado).  
> **Ámbito:** Integración de subsistemas continuos (vialidades, ferrocarril, cuerpos de agua, puentes y manzanas), desacoplamiento Blender/Godot, caché de hashes, jerarquía vertical estricta, morfología de puentes y preservación del relieve natural.

---

## 1. Resumen Ejecutivo y Motivación

A partir de los modelos de dominio desarrollados en el pipeline de Minecraft (detección de puentes, taxonomía vial, interpolación de agua y trazado ferroviario), se enriqueció el gemelo digital en Godot sustituyendo la discretización por bloques de 1×1×1m por **geometría vectorial continua 3D**.

Se consolidó:
1. **Desacoplamiento Estructural Total:** Separación absoluta entre los archivos de trabajo de Blender (`blender_assets/`) y los binarios de ejecución en Godot (`godot_project/assets/`), eliminando la sobrecarga y los errores del importador headless de Godot 4.x.
2. **Pipeline de Horneado Unificado con Hash-Caching ([`scripts/bake_pipeline.py`](file:///Users/hakkindavid/Documents/GitHub/tecate-simulator/scripts/bake_pipeline.py)):** Verificación instantánea basada en hashes SHA-256 que solo invoca a Blender cuando un archivo `.blend` ha sido modificado o falta su binario `.glb`.
3. **Jerarquía Vertical Estricta (Anti-Clipping y Cero Z-Fighting):**
   - **Terreno Natural (`tecate2.glb`):** $Z = 0.00\text{ m}$ (relieve base).
   - **Plataformas de Manzana / Lotes Urbanos:** $Z = Z_{\text{terreno}} + 0.12\text{ m}$ (faldones perimetrales sólidos hasta $-0.25\text{ m}$).
   - **Superficie de Rodamiento Asfáltica:** $Z = Z_{\text{terreno}} + 0.18\text{ m}$ (6 cm sobre la plataforma de manzana interior).
   - **Señalamiento Horizontal Vial:** $Z = Z_{\text{terreno}} + 0.185\text{ m}$ (5 mm de offset sobre el asfalto).
   - **Guarniciones de Concreto y Aceras Peatonales:** $Z = Z_{\text{terreno}} + 0.28\text{ m}$ (escalón visible de 10 cm sobre el asfalto y 16 cm sobre el lote interior).
4. **Retracción Perimetral e Integración como *Fillers*:** Retracción bisectriz ($d = 3.8\text{ m}$) en manzanas urbanas para no invadir arroyos viales ni guarniciones, respetando la soberanía de los polígonos oficiales de `landuse` (parques, escuelas y jardines).
5. **Poda Topológica Iterativa (2-Core) de Calles Sin Salida:** Eliminación iterativa de espolones de grado $\le 1$ para la extracción de ciclos planares, permitiendo cerrar y generar manzanas que albergan privadas o callejones ciegos (recuperando 174 manzanas adicionales en Tecate, como las situadas al este del Parque Hidalgo).
6. **Morfología Real en Puentes de Bulevar Universidad:** Dos estructuras físicas independientes con vacío central de 4.8m a 8.6m sobre el Río Tecate, acera exterior adosada y parapeto interior de protección hacia el río.
7. **Preservación del Relieve y Cielo Limpio:** Eliminación de las 409 mallas billboard de árboles/bosques sin canal alfa que generaban artefactos en el cielo, y preservación total de la ortofoto aérea satelital ([`tecate_groundTexture.png`](file:///Users/hakkindavid/Documents/GitHub/tecate-simulator/godot_project/assets/tecate_groundTexture.png)) en montañas y áreas no urbanizadas.

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
│  - osm2world_adjusted.blend  (102 MB, 3,143 objetos)    │
│  - roadways_adjusted.blend   (2.8 MB, vialidades)       │
│  - railways_adjusted.blend   (6.8 MB, ferrocarril)      │
│  - waterways_adjusted.blend  (0.5 MB, cuerpos de agua)  │
│  - bridges_adjusted.blend    (0.1 MB, puentes 3D)       │
│  - manzanas_adjusted.blend   (0.1 MB, manzanas urbanas) │
└────────────────────────────┬────────────────────────────┘
                             │
                             │ scripts/bake_pipeline.py
                             │ (SHA-256 Hash Manifest: .bake_manifest.json)
                             ▼
┌─────────────────────────────────────────────────────────┐
│              ENTORNO DE EJECUCIÓN (Godot)               │
│  Carpeta: godot_project/assets/                         │
│  - osm2world_baked.glb  (47.2 MB, 2,602 edificios)      │
│  - roadways_baked.glb   (282.4 MB, 3.8M tris)           │
│  - railways_baked.glb   (12.0 MB, 174K tris)            │
│  - waterways_baked.glb  (3.4 MB, Río Tecate)            │
│  - bridges_baked.glb    (0.7 MB, 12K tris)              │
│  - manzanas_baked.glb   (36.5 MB, 1,864 plataformas)    │
│  - tecate2.glb          (99 MB, relieve base)           │
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
5. **Si difiere o falta el GLB:** Invoca a Blender en modo headless exclusivamente para ese archivo (purgando mallas billboard si aplica), actualiza el binario en `godot_project/assets/` y reescribe el manifiesto.

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

## 4. Detalle de las Capas Vectoriales Continuas

### 4.1 Cuerpos de Agua (`waterways`)
- **Archivos:** `blender_assets/waterways_adjusted.blend` $\rightarrow$ `godot_project/assets/waterways_baked.glb` (3.4 MB).
- **Lagos y Presas (ej. Presa Las Auras):** Triangulación Delaunay 2D Restringida (`delaunay_2d_cdt`) con rejilla interna y faldón vertical perimetral (*water skirt*) de $-1.5\text{ m}$ de profundidad para eliminar desgarros en las orillas.
- **Ríos y Canales (Río Tecate):** Subdivisión cada $4.0\text{ m}$ adaptada a las cotas del terreno con anchos calibrados ($12\text{ m}$ río principal, $4\text{ m}$ arroyos) y coordenadas UV longitudinales continuas para shaders de flujo.

### 4.2 Ferrocarril (`railways`)
- **Archivos:** `blender_assets/railways_adjusted.blend` $\rightarrow$ `godot_project/assets/railways_baked.glb` (12.0 MB, 174,532 triángulos).
- **Traza Histórica:** Ferrocarril Tijuana–Tecate (vía de enlace hacia Campo / San Diego).
- **Geometría Tridimensional:**
  - *Balasto:* Prisma trapezoidal extruido ($3.4\text{ m}$ de base, $2.6\text{ m}$ de corona, $+0.22\text{ m}$ de altura sobre terreno).
  - *Durmientes:* Bloques de madera tratada ($2.6\text{m} \times 0.24\text{m} \times 0.14\text{m}$) espaciados uniformemente cada $0.65\text{ m}$ y perpendiculares a la tangente.
  - *Rieles de Acero:* Doble perfil continuo con ancho de vía estándar internacional ($1.435\text{ m}$).

### 4.3 Puentes Suspendidos y Pasarelas (`bridges`)
- **Archivos:** `blender_assets/bridges_adjusted.blend` $\rightarrow$ `godot_project/assets/bridges_baked.glb` (0.7 MB, 11,932 triángulos).
- **Bulevar Universidad (`51794560` y `51794561`):**
  - Dos puentes separados (Poniente sentido sur, Oriente sentido norte) con un vacío central de 4.8m a 8.6m sobre el río Tecate.
  - Cada puente cuenta con 2 carriles vehiculares (7.6m de ancho en asfalto con línea blanca discontinua central).
  - Flanco interior medianero (`+nx`): Parapeto vertical de concreto (+1.1m) protegiendo el vacío hacia el río, sin banqueta.
  - Flanco exterior derecho (`-nx`): Banqueta peatonal elevada de concreto (+0.15m de escalón, 1.8m de ancho) con barandal exterior de seguridad (+1.1m).
  - Se eliminaron las vías peatonales duplicadas superpuestas (`1229759737` y `1229759758`).
- **Puente Xochimilco y Río Tecate (`363433372`):** Herencia de ancho máximo (6.0m) y estribos con aletas de hormigón abocinadas (+1.2m).
- **Puente Peatonal Paseo de las Águilas (`968895089`):** Conexión topológica automática mediante rampas de aproximación peatonal (1.8m de ancho en concreto) que enlazan con la calle más cercana ($\le 25\text{ m}$).

### 4.4 Red Vial (`roadways`)
- **Archivos:** `blender_assets/roadways_adjusted.blend` $\rightarrow$ `godot_project/assets/roadways_baked.glb` (282.4 MB, 3,796,032 triángulos).
- **Cotas y Perfiles:**
  - Asfalto en rasante a $+0.18\text{ m}$ con faldones laterales sólidos a $-0.20\text{ m}$ (38 cm de espesor continuo).
  - Guarniciones de concreto extruidas a $+0.28\text{ m}$ (labio de 10 cm sobre el asfalto).
  - Marcas viales longitudinales a $+0.185\text{ m}$.
  - Aceras peatonales independientes a $+0.28\text{ m}$ en concreto.
- **Taxonomía Vial:** Asfalto limpio para bulevares, asfalto estándar para calles/carreteras, grava rústica para caminos rurales.

### 4.5 Manzanas Urbanas Drapadas (`manzanas`)
- **Archivos:** `blender_assets/manzanas_adjusted.blend` $\rightarrow$ `godot_project/assets/manzanas_baked.glb` (36.5 MB, 743,275 triángulos, 1,864 plataformas).
- **Retracción Bisectriz ($d = 3.8\text{ m}$):** Las manzanas se contraen hacia el interior del lote, garantizando que nunca invadan la calle ni las guarniciones.
- **Comportamiento como *Fillers*:** Respetan la soberanía de los polígonos de `landuse` de OSM (parques, jardines, escuelas), rellenando exclusivamente el espacio desocupado.
- **Poda Topológica 2-Core para Calles Ciegas:** Se podan iterativamente los nodos de grado $\le 1$ del grafo para que callejones sin salida, privadas y accesos interiores no aborten la extracción del perímetro de la manzana. Esto recuperó 174 manzanas en Tecate (incluyendo la ubicada al este del Parque Hidalgo).
- **Cota:** Plataforma de concreto a $+0.12\text{ m}$ con faldón perimetral vertical a $-0.25\text{ m}$ (37 cm de espesor).

### 4.6 Edificaciones y Mobiliario Urbano (`osm2world`)
- **Archivos:** `blender_assets/osm2world_adjusted.blend` $\rightarrow$ `godot_project/assets/osm2world_baked.glb` (47.2 MB, 3,143 objetos).
- **Alineación a Terreno:** Los 2,602 edificios se mantienen en su cota real de terreno ($390\text{ m} - 540\text{ m}$), asentados firmemente sobre el suelo y sobre las plataformas de manzana.
- **Purga de Billboard Trees:** Se eliminaron las 409 mallas de árboles y bosques en cuadriláteros que carecían de canal alfa, erradicando los romboides negros en el cielo.

---

## 5. Preservación del Paisaje Natural y Montañas

> [!IMPORTANT]
> **Protección del Paisaje Rural y Montañoso**:
> Las mallas de manzanas y vialidades se generan **únicamente donde existen predios urbanos consolidados** (área $< 60,000\text{ m}^2$ y envolvente $< 400\text{ m}$).
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
├── Manzanas (manzanas_baked.glb)       [1,864 plataformas urbanas a +0.12m]
├── Roadways (roadways_baked.glb)       [Red vial a +0.18m, guarniciones a +0.28m]
├── Railways (railways_baked.glb)       [Balasto, durmientes y rieles de acero]
├── Bridges (bridges_baked.glb)         [Puentes Bulevar Univ. y pasarelas continuas]
└── Geometry (osm2world_baked.glb)      [2,602 edificios en tierra, 0 artefactos en cielo]
```

En [`godot_project/apply_shader.gd`](file:///Users/hakkindavid/Documents/GitHub/tecate-simulator/godot_project/apply_shader.gd):
- Se ocultan automáticamente las mallas obsoletas de baja resolución incrustadas en `tecate.glb` (`__mergedRoads_*` y `water_*`).
- Se filtran y ocultan en runtime cualquier malla billboard residual (`Tree_*` o `Forest_*`).
- Se generan colisionadores trimesh para el terreno, puentes, vialidades y manzanas.
- El avatar del jugador se posiciona y ancla físicamente a la cota exacta del terreno ($405.29\text{ m}$).
- El motor ejecuta la simulación sin errores, sin llamadas a Blender y con 100% de estabilidad y rendimiento.
