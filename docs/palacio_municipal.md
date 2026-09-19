# Ficha Técnica Arquitectónica: Palacio Municipal de Tecate (Ground-Truth Histórico 2009)

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
  - `transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 47.75, 400.0, 33.06)`
  - Orientación canónica: El pórtico del chaflán apunta en ángulo de $45^\circ$ hacia el suroeste (directamente hacia el Parque Miguel Hidalgo).
- **Colisiones Analíticas**: Escena `palacio_municipal_2009.tscn` con 8 cuerpos convexos (`BoxShape3D` y `CylinderShape3D`) coordinados con los ejes locales, preservando el vano de acceso peatonal diáfano sin paredes invisibles.

---

## 2. Anatomía, Fenestración y Crujías Canónicas

El inmueble se compone de los siguientes cuerpos arquitectónicos fidedignamente reconstruidos según la evidencia fotográfica histórica de 2009:

### 1. Ochava Central en Chaflán a 45º (Pórtico Monumental)
- **Cuerda de Esquina**: Entre $(0.00, 5.20\text{ m})$ y $(5.20, 0.00\text{ m})$ con normal exterior $(-0.707, -0.707)$.
- **Pórtico Monumental Neoclásico**:
  - Cuatro columnas toscanas circulares exentas ($R = 0.22\text{ m}$) con plintos prismáticos ocres ($0.58\text{ m} \times 0.58\text{ m} \times 1.00\text{ m}$) y capiteles toscanos en moldura curva.
  - Altura libre bajo el balcón: $3.40\text{ m}$.
- **Balcón Oficial y Marquesina**:
  - Losa de balcón volada sobre las columnas ($Z = 3.40\text{ a }3.60\text{ m}$).
  - Antepecho macizo blanco con albardilla en ocre ($H = 1.00\text{ m}$).
  - Rótulo tridimensional extruido en letras capitales doradas: **PALACIO MUNICIPAL** (con lectura ortogonal directa y sin efecto espejo).
  - Medallón en relieve con el **Escudo Nacional Mexicano** montado sobre el antepecho.
- **Vano de Acceso Principal**:
  - Portal doble de ingreso en planta baja, enmarcado por jamba y dintel de ladrillo cocido rojo.
  - Vano peatonal libre de colisión estática para permitir acceso peatonal fluido al jugador.
- **Remate Superior / Pretil Escalonado**:
  - Copete ornamental central sobre el chaflán ($Z = 7.55\text{ a }8.95\text{ m}$) con hornacina semicircular moldurada en concha/sol radiante en relieve ocre.

### 2. Ala Oriente (Lado Derecho visto desde el frente): 4 Crujías
- **Fachada Exterior**: Paralela al eje $X$, superficie exterior en $Y = -0.40\text{ m}$ con longitud de $19.80\text{ m}$ ($X \in [5.20, 25.00\text{ m}]$).
- **Crujías Modulares (4 unidades)**: Centradas en $X = [8.00, 12.40, 16.80, 21.20\text{ m}]$.
  - **Planta Alta**: Arcos de medio punto con rosca de ladrillo rojo cocido ($R_{\text{int}} = 0.80\text{ m}, R_{\text{ext}} = 1.08\text{ m}$), jambas de ladrillo y vidrios comerciales tintados oscuros con parteluz de aluminio negro.
  - **Entreplanta**: Paneles ciegos de estuco ocre (*spandrels*) que unen verticalmente los dos niveles.
  - **Planta Baja**: Ventanas rectangulares comerciales ($1.60\text{ m} \times 1.62\text{ m}$) con marcos de cancelería oscura y vidrios reflectantes.
- **Cornisa**: Albardilla corrida en estuco ocre mostaza a lo largo del pretil superior ($Z = 7.40\text{ a }7.55\text{ m}$).

### 3. Ala Norte (Lado Izquierdo visto desde el frente): 3 Crujías
- **Fachada Exterior**: Paralela al eje $Y$, superficie exterior en $X = -0.40\text{ m}$ con longitud de $16.20\text{ m}$ ($Y \in [5.20, 21.40\text{ m}]$).
- **Crujías Modulares (3 unidades)**: Centradas en $Y = [8.20, 12.80, 17.40\text{ m}]$.
  - Mismo diseño canónico de vanos: arcos de ladrillo rojo en planta alta, paneles *spandrel* ocres y ventanas rectangulares en planta baja.
- **Cornisa**: Albardilla continua en estuco ocre en coronación de pretil ($Z = 7.40\text{ a }7.55\text{ m}$).

### 4. Azotea y Cubierta Sellada
- Prisma poligonal hermético de 7 vértices que sella el inmueble en $Z = 7.00\text{ m}$ sin desbordamientos triangulares sobre el chaflán.
- Gravilla asfáltica impermeable oscura (`M_Azotea_Grava`).

---

## 3. Paleta de Materiales PBR

| Material | Tipo PBR | Albedo (sRGB) | Roughness | Metallic | Uso |
|:---|:---|:---|:---:|:---:|:---|
| `M_Estuco_Blanco` | Principled BSDF | `(0.86, 0.86, 0.84)` | 0.85 | 0.00 | Muros generales y pretiles |
| `M_Estuco_Ocre` | Principled BSDF | `(0.74, 0.58, 0.22)` | 0.78 | 0.00 | Zócalo basal, plintos, capiteles, cornisas y paneles *spandrel* |
| `M_Ladrillo_Arco` | Principled BSDF | `(0.52, 0.18, 0.12)` | 0.82 | 0.00 | Rosca de arcos, jambas y marco de acceso |
| `M_Vidrio_Oscuro` | Principled BSDF | `(0.04, 0.06, 0.08)` | 0.08 | 0.00 | Vidrios comerciales de planta baja y alta (IOR 1.52) |
| `M_Canceleria` | Principled BSDF | `(0.12, 0.12, 0.14)` | 0.40 | 0.80 | Marcos y parteluces de aluminio negro |
| `M_Letras_Oro` | Principled BSDF | `(0.85, 0.72, 0.32)` | 0.30 | 0.90 | Tipografía 3D "PALACIO MUNICIPAL" y Escudo Nacional |
| `M_Azotea_Grava` | Principled BSDF | `(0.20, 0.20, 0.22)` | 0.92 | 0.00 | Impermeabilizante de cubierta |

---

## 4. Archivos Producidos y Versionados

1. **Generador Procedural**: [`scripts/generate_palacio_municipal.py`](file:///Users/hakkindavid/Documents/GitHub/tecate-simulator/scripts/generate_palacio_municipal.py) (732 líneas).
2. **Archivo Maestro Blender**: `blender_assets/palacio_municipal_2009.blend` (119 KB).
3. **Asset de Producción GLB**: `godot_project/assets/palacio_municipal_2009.glb` (215 KB).
4. **Escena Godot con Física Analítica**: [`godot_project/assets/palacio_municipal_2009.tscn`](file:///Users/hakkindavid/Documents/GitHub/tecate-simulator/godot_project/assets/palacio_municipal_2009.tscn) (2.2 KB).
5. **Integración en Escena Principal**: [`godot_project/main.tscn`](file:///Users/hakkindavid/Documents/GitHub/tecate-simulator/godot_project/main.tscn).
6. **Galería de Validación Closed-Loop**:
   - `docs/images/palacio_municipal/Cam_Chaflan_45.png`
   - `docs/images/palacio_municipal/Cam_Ala_Oriente.png`
   - `docs/images/palacio_municipal/Cam_Ala_Norte.png`
   - `docs/images/palacio_municipal/Cam_Cenital_Azotea.png`
   - `docs/images/palacio_municipal/Cam_Closeup_Portico.png`
