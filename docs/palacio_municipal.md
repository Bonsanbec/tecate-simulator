# Ficha Técnica Arquitectónica: Palacio Municipal de Tecate (Ground-Truth Histórico 2009 — V2.0 Refinada)

Documento técnico de especificación morfológica, paramétrica, fenestración, PBR y consenso de verdad de terreno para la reconstrucción fidedigna del **Palacio Municipal de Tecate** (esquina Av. Presidente Pascual Ortiz Rubio y Callejón Libertad / Explanada Cívica, Tecate, B.C.) en Blender 5.1 y Godot Engine 4.

---

## 1. Contexto Urbano y Emplazamiento Cartesiano

- **Nombre Oficial**: Palacio Municipal de Tecate (Época histórica 2009).
- **Dirección Catastral**: Pdte. Pascual Ortiz Rubio 1310, Zona Centro, 21400 Tecate, B.C., México.
- **Coordenadas Geográficas (WGS84)**: $32.572932^\circ\text{N}, -116.626027^\circ\text{W}$.
- **Identificador de Manzana Catastral**: `block_lat_32.57293_lon_-116.62685` (costado este del Parque Miguel Hidalgo).
- **Contrato Cartesiano Canónico (Primer Cuadrante Ortogonal)**:
  - $\text{Origen }(0,0,0)$: Vértice exterior proyectado de la ochava a nivel de banqueta ($Z = 0.00\text{ m}$).
  - $\text{Eje }+X$: Vector paralelo al Ala Oriente / Callejón Libertad ($X \in [5.20, 25.00\text{ m}]$).
  - $\text{Eje }+Y$: Vector paralelo al Ala Norte / Av. Ortiz Rubio ($Y \in [5.20, 21.40\text{ m}]$).
  - $\text{Eje }+Z$: Cota de elevación vertical.
- **Calibración de Rasante y Zócalo Subterráneo**:
  - Zócalo basal continuo en estuco ocre mostaza (`M_Estuco_Ocre`) que desciende subterráneamente hasta $Z = -1.50\text{ m}$ bajo rasante, absorbiendo pendientes topográficas sin producir flotación del edificio.
  - **Prohibición estricta cumplida**: El asset 3D (`palacio_municipal_2009.glb`) no contiene banquetas, cordones ni asfalto embebido.
- **Integración en Escena Principal Godot (`godot_project/main.tscn`)**:
  - Instancia: `[node name="Palacio_Municipal" parent="." instance=ExtResource("14_palacio_municipal")]`
  - `transform = Transform3D(-1, 0, 0, 0, 1, 0, 0, 0, -1, 47.75, 400.0, 33.06)`
  - Orientación canónica: Rotación de $180^\circ$ calibrada que posiciona el chaflán y ambas alas exactamente sobre el perímetro catastral de la manzana urbana, con el pórtico mirando hacia el Parque Miguel Hidalgo.
- **Supresión de Placeholder Amarillo**: En [`godot_project/apply_shader.gd`](file:///Users/hakkindavid/Documents/GitHub/tecate-simulator/godot_project/apply_shader.gd), la función `_hide_replaced_buildings()` oculta automáticamente las mallas legacy `Building_Ayuntamiento_de_Tecate` y `Building_Ayuntamiento_de_Tecate_part1`.
- **Colisiones Analíticas 1:1**: Escena `palacio_municipal_2009.tscn` con 15 colisionadores analíticos coordinados ($Z_{\text{gltf}} = -Y_{\text{blender}}$): muros perimetrales, 4 columnas con plintos independientes, balcón volado y portal de acceso peatonal diáfano ($H = 2.70\text{ m}$) sin paredes invisibles.

---

## 2. Anatomía, Fenestración y Crujías Canónicas (Ground-Truth 2009)

El inmueble se compone de los siguientes cuerpos arquitectónicos fidedignamente reconstruidos según la evidencia fotográfica histórica de 2009 (`s8jMOjFHZUBdw...`, `WqGF0A9xXd...`, `zb8YAlf6JT...`):

### 1. Ochava Central en Chaflán a 45º (Pórtico Monumental)
- **Cuerda de Esquina**: Entre $(0.00, 5.20\text{ m})$ y $(5.20, 0.00\text{ m})$ con normal exterior $(-0.707, -0.707)$.
- **Pórtico Monumental Neoclásico**:
  - Cuatro columnas toscanas exentas: plintos prismáticos ocres ($0.54\text{ m} \times 0.54\text{ m} \times 0.85\text{ m}$), moldura de toro ocre, fustes circulares lisos ($R = 0.21\text{ m}$) y capiteles toscanos moldurados con equino y ábaco.
  - Altura libre bajo el balcón: $3.40\text{ m}$.
- **Balcón Oficial y Marquesina**:
  - Losa volada sobre columnas ($Z = 3.40\text{ a }3.65\text{ m}$) soportada por modillones/aletas laterales anguladas.
  - Antepecho macizo blanco con moldura de cornisa ocre superior ($Z = 4.52\text{ a }4.65\text{ m}$).
  - Rótulo tridimensional extruido en letras capitales de bronce oscuro patinado: **PALACIO MUNICIPAL** (lectura directa y textura PBR fidedigna).
  - Medallón del **Escudo Nacional Mexicano** en altorrelieve de bronce envejecido centrado sobre el antepecho.
- **Portal de Acceso Principal**:
  - Portal doble de ingreso en planta baja, enmarcado por jambas y dintel de ladrillo cocido rojo.
  - Puerta cancel doble de madera oscura con vitrales superiores.
  - Vano peatonal libre de colisión estática para permitir acceso peatonal fluido al jugador.
- **Ático / Copete Central**:
  - Ático central sobre el chaflán ($Z = 7.40\text{ a }8.75\text{ m}$) con hornacina semicircular moldurada en relieve ocre y remate de cornisa escalonada.

### 2. Ala Oriente (Lado Derecho visto desde el frente): 4 Crujías
- **Fachada Exterior**: Paralela al eje $X$, superficie exterior en $Y = -0.40\text{ m}$ con longitud de $19.80\text{ m}$ ($X \in [5.20, 25.00\text{ m}]$).
- **Crujías Modulares (4 unidades)**: Centradas en $X = [8.00, 12.40, 16.80, 21.20\text{ m}]$.
  - **Rosca y Pilastras de Ladrillo Continuas**: Rosca de arco semicircular de ladrillo rojo ($R_{\text{int}} = 0.80\text{ m}, R_{\text{ext}} = 1.08\text{ m}$) con pilastras laterales de ladrillo que continúan verticalmente sin interrupción hasta el zócalo ocre.
  - **Tímpano Retranqueado**: Superficie de estuco blanco retranqueada bajo el arco.
  - **Planta Alta**: Ventana rectangular con cancelería de aluminio negro y vidrio oscuro tintado.
  - **Delantal Volado de Cantera Beige**: Módulo de cantera/baldosas beige que sobresale $0.14\text{ m}$ hacia el frente, con gotero superior e inferior.
  - **Planta Baja**: Ventanas rectangulares comerciales ($1.60\text{ m} \times 1.62\text{ m}$) con vidrios oscuros.
- **Cornisa**: Albardilla corrida en estuco ocre mostaza a lo largo del pretil superior ($Z = 7.40\text{ a }7.55\text{ m}$).

### 3. Ala Norte (Lado Izquierdo visto desde el frente): 3 Crujías
- **Fachada Exterior**: Paralela al eje $Y$, superficie exterior en $X = -0.40\text{ m}$ con longitud de $16.20\text{ m}$ ($Y \in [5.20, 21.40\text{ m}]$).
- **Crujías Modulares (3 unidades)**: Centradas en $Y = [8.20, 12.80, 17.40\text{ m}]$.
  - Idéntica fenestración con pilastras continuas de ladrillo, tímpano, delantales volados de cantera beige y ventanería comercial.
- **Cornisa**: Albardilla continua en estuco ocre en coronación de pretil ($Z = 7.40\text{ a }7.55\text{ m}$).

### 4. Azotea y Cubierta Sellada
- Prisma poligonal hermético de 7 vértices que sella el inmueble en $Z = 7.00\text{ m}$ sin desbordamientos sobre el chaflán.
- Asfalto impermeabilizante oscuro (`M_Azotea_Asfalto`).

---

## 3. Paleta de Materiales PBR Calibrados

| Material | Tipo PBR | Albedo (sRGB) | Roughness | Metallic | Uso |
|:---|:---|:---|:---:|:---:|:---|
| `M_Estuco_Blanco` | Principled BSDF | `(0.88, 0.88, 0.86)` | 0.85 | 0.00 | Muros generales y pretiles |
| `M_Estuco_Ocre` | Principled BSDF | `(0.75, 0.58, 0.20)` | 0.78 | 0.00 | Zócalo basal, plintos, capiteles, cornisas y hornacina |
| `M_Ladrillo_Arco` | Principled BSDF | `(0.50, 0.16, 0.10)` | 0.82 | 0.00 | Arcos y pilastras continuas de ladrillo rojo |
| `M_Cantera_Beige` | Principled BSDF | `(0.72, 0.65, 0.52)` | 0.88 | 0.00 | Delantales volados entre ventanas (*Spandrels*) |
| `M_Vidrio_Oscuro` | Principled BSDF | `(0.04, 0.06, 0.08)` | 0.08 | 0.00 | Vidrios comerciales (Transmission 0.85, IOR 1.52) |
| `M_Canceleria` | Principled BSDF | `(0.02, 0.02, 0.02)` | 0.30 | 0.85 | Marcos y parteluces de aluminio negro |
| `M_Letras_Oscuras`| Principled BSDF | `(0.12, 0.11, 0.10)` | 0.45 | 0.70 | Tipografía 3D "PALACIO MUNICIPAL" en bronce patinado |
| `M_Escudo_Bronce` | Principled BSDF | `(0.65, 0.52, 0.25)` | 0.35 | 0.80 | Escudo Nacional Mexicano en relieve escultórico |
| `M_Puerta_Madera` | Principled BSDF | `(0.18, 0.10, 0.06)` | 0.65 | 0.00 | Puertas dobles de acceso en portal bajo el pórtico |
| `M_Azotea_Asfalto`| Principled BSDF | `(0.05, 0.05, 0.05)` | 0.95 | 0.00 | Impermeabilización de cubierta |

---

## 4. Archivos Producidos y Versionados

1. **Generador Procedural**: [`scripts/generate_palacio_municipal.py`](file:///Users/hakkindavid/Documents/GitHub/tecate-simulator/scripts/generate_palacio_municipal.py) (878 líneas).
2. **Archivo Maestro Blender**: `blender_assets/palacio_municipal_2009.blend` (119 KB).
3. **Asset de Producción GLB**: `godot_project/assets/palacio_municipal_2009.glb` (215 KB).
4. **Escena Godot con Física Analítica**: [`godot_project/assets/palacio_municipal_2009.tscn`](file:///Users/hakkindavid/Documents/GitHub/tecate-simulator/godot_project/assets/palacio_municipal_2009.tscn) (5.7 KB).
5. **Integración en Escena Principal**: [`godot_project/main.tscn`](file:///Users/hakkindavid/Documents/GitHub/tecate-simulator/godot_project/main.tscn).
6. **Lógica de Ocultamiento de Placeholders**: [`godot_project/apply_shader.gd`](file:///Users/hakkindavid/Documents/GitHub/tecate-simulator/godot_project/apply_shader.gd).
