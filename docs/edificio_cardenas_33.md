# Ficha Técnica Arquitectónica: Complejo Comercial Pdte. Lázaro Cárdenas 33 (Histórico 2009)

Documento técnico de especificación morfológica, paramétrica, PBR y consenso multi-perspectiva para la reconstrucción procedural fidedigna del conjunto comercial ubicado en **Calle Presidente Lázaro Cárdenas 33**, esquina con Callejón Libertad, Tecate, B.C., colindante con el edificio BBVA Bancomer Centro (época: **2009**), en Blender 5.1 y Godot Engine 4.

---

## 1. Contexto Urbano y Emplazamiento Cartesiano

- **Ubicación Histórica**: Pdte. Lázaro Cárdenas 33, Primera, 21400 Tecate, B.C., México.
- **Coordenadas Geográficas de Referencia**: Aprox. $32.573057^\circ\text{ N}, -116.627261^\circ\text{ W}$.
- **Relación con el Edificio BBVA**:
  - Comparte la misma manzana y acera comercial.
  - La medianera sur de Librería España ($Y = 0.00\text{ m}$ local en Blender) empalma de manera continua y hermética con la cara norte de los consultorios DENTISTA del Banco BBVA ($Y = 30.00\text{ m}$ en BBVA).
- **Coordenadas en Escena Godot (`godot_project/main.tscn`)**:
  - `transform = Transform3D(-0.99636, -0.000716, -0.085243, -0.00275, 0.999714, 0.02375, 0.085202, 0.023898, -0.996077, -69.356, 399.283, 5.072)`
  - Mantiene la misma matriz de rotación e inclinación topográfica que BBVA, logrando una unión continua milimétrica sin fisuras, holguras ni *Z-fighting*.
- **Calibración de Rasante y Zócalo Subterráneo**:
  - Todo el perímetro arquitectónico cuenta con un zócalo basal continuo de concreto enterrado a $Z \le -1.20\text{ m}$ que absorbe íntegramente la pendiente de la calle sin mallas flotantes.
- **Prohibición de Banquetas Embebidas**:
  - El asset `.glb` carece intencionalmente de banquetas, guarniciones o aceras, integrándose de forma limpia sobre las capas viales y de banquetas de Tecate Simulator.

---

## 2. Anatomía de Fachadas y Locales Comerciales (Época 2009)

El complejo comercial agrupa cinco comercios principales sobre Calle Presidente Lázaro Cárdenas, una ochava comercial Art Déco en esquina, la fachada septentrional sobre Callejón Libertad y la fachada posterior hacia el estacionamiento interior del BBVA:

### Fachada Este (Calle Presidente Lázaro Cárdenas)

1. **Crujía 1: Librería España (colindancia BBVA en $Y \in [0.00, 4.80\text{ m}]$)**:
   - Muro medianero sur hermético y ciego con BBVA.
   - Paramento exterior en estuco azul cobalto con zócalo de protección.
   - Puerta comercial acristalada y vitrina de exhibición con marco de aluminio.
   - Rótulo comercial superior en relieve 3D sobre marquesina: `LIBRERIA ESPAÑA`.
   - Cartel publicitario de azotea: soporte estructural metálico con cartelera blanca y letrero en dos líneas: `BAR TURISTICO / Diana`.

2. **Crujía 2: Bar Turístico Diana ($Y \in [4.80, 9.10\text{ m}]$)**:
   - Marquesina prominente en voladizo con barandal perimetral de acero dorado.
   - Rótulo tridimensional principal en color blanco y rojo: `BAR TURISTICO Diana`.
   - Silueta ornamental recortada de la **Diana Cazadora** en latón dorado sobre el paramento.
   - Puerta principal acolchada en piel sintética dorada capitonada con herrajes clásicos de bar tradicional.
   - Zócalo de loseta cerámica marrón y vitrina lateral de vidrio biselado.

3. **Crujía 3: Annita's Boutique ($Y \in [9.10, 14.20\text{ m}]$)**:
   - Paramento comercial en panel compuesto negro pulido de alto impacto.
   - Óvalo superior turquesa con tipografía caligráfica en relieve blanco: `Annita's / BOUTIQUE`.
   - Gran aparador central de cristal de doble hoja con manijas tubulares de aluminio.
   - Cartelera rectangular superior en azotea: rótulo amarillo con texto negro en dos líneas: `RENTA DE MESAS / Y SILLAS`.

4. **Crujía 4: Party Rentals - Kuroky ($Y \in [14.20, 19.30\text{ m}]$)**:
   - Fachada con bandas horizontales en color morado y verde manzana.
   - Rótulo principal en letras tridimensionales: `PARTY RENTALS / KUROKY`.
   - Cartelera publicitaria de azotea con texto en tres líneas: `RENTA DE ROCKOLAS / LONAS Y CARPAS / INFLABLES`.
   - Puerta acristalada y cancelería comercial con motivos festivos (notas musicales impresas en cristal).
   - Batería de buzones metálicos postales en murete exterior.

5. **Crujía 5: Florería Orquídea ($Y \in [19.30, 24.50\text{ m}]$)**:
   - Frontón Art Déco escalonado revestido en mosaico veneciano verde esmeralda reflectivo.
   - Rótulo tridimensional en magenta/fucsia: `FLORERIA ORQUIDEA`.
   - Amplios ventanales en ochava a 45º hacia el crucero peatonal.
   - Murete bajo de laja rústica de piedra tecatense en el ala hacia Callejón Libertad.

---

### Fachada Norte (Callejón Libertad)

1. **Florería Orquídea (Ala Norte)**:
   - Murete de piedra rústica y ventanales alargados sobre la acera peatonal.
2. **Foto Estudio Curiel**:
   - Marquesina aerodinámica estilo *Streamline Moderne* con tres estrías horizontales metálicas continuas.
   - Letrero tridimensional sobre marquesina: `FOTO ESTUDIO CURIEL`.
   - Letrero pintado sobre paramento superior: `ESTUDIO CURIEL`.
   - Tótem publicitario vertical en aluminio rojo brillante con letras blancas `FOTO` visibles desde la calle.
   - Puerta y cancelería de madera lacada con vitrina de retratos fotográficos.

---

### Fachada Poniente (Reverso hacia Estacionamiento BBVA)

1. **Posterior de Foto Estudio Curiel**:
   - Muro funcional en estuco gris claro con bajantes pluviales y acometidas de servicio.
2. **Posterior y Marquesina de Bar Diana**:
   - Marquesina angulada de protección pluvial sobre acceso posterior.
   - Rótulo de servicio en azotea: `BAR TURISTICO Diana`.
   - Puerta metálica de emergencia con letrero de señalética `Salida`.
   - Terraza técnica cercada con reja metálica negra de perfilería tubular analíticamente colisionable.

---

## 3. Especificación de Materiales PBR

Todos los materiales fueron configurados con sombreadores Principled BSDF compatibles con glTF 2.0 y Godot StandardMaterial3D:

| Nombre del Material | Color Base / Hex | Roughness | Metallic | Uso en Modelo |
|---|---|---|---|---|
| `M_Estuco_Libreria` | Azul cobalto `#1B3B6F` | 0.85 | 0.00 | Muros Librería España |
| `M_Panel_Diana` | Ocre colonial `#B87333` | 0.40 | 0.10 | Marquesina Bar Diana |
| `M_Dorado_Diana` | Latón brillante `#D4AF37` | 0.25 | 0.90 | Diana Cazadora y herrajes |
| `M_Puerta_Diana` | Dorado envejecido `#997A15` | 0.50 | 0.40 | Puerta capitonada Bar Diana |
| `M_Panel_Negro_Anita` | Negro asfalto `#1C1C1C` | 0.20 | 0.05 | Panel comercial Annita's |
| `M_Turquesa_Anita` | Turquesa cálido `#17B890` | 0.40 | 0.00 | Óvalo de rótulo Annita's |
| `M_Verde_Party` | Verde manzana `#60A917` | 0.45 | 0.00 | Franjas Party Rentals |
| `M_Morado_Party` | Morado festivo `#7B1FA2` | 0.45 | 0.00 | Franjas Party Rentals |
| `M_Mosaico_Orquidea` | Verde esmeralda `#008B74` | 0.15 | 0.10 | Frontón Art Déco |
| `M_Letras_Orquidea` | Magenta fucsia `#D81B60` | 0.30 | 0.00 | Rótulo Florería Orquídea |
| `M_Laja_Rustica` | Piedra tecatense `#8D7B68` | 0.90 | 0.00 | Murete Callejón Libertad |
| `M_Marquesina_Curiel` | Gris plata `#D0D0D0` | 0.30 | 0.70 | Marquesina Streamline Curiel |
| `M_Totem_Curiel` | Rojo bermellón `#C62828` | 0.35 | 0.10 | Tótem vertical Foto Curiel |
| `M_Zocalo_Basal` | Concreto grafito `#2A2A2A` | 0.95 | 0.00 | Zócalo basal enterrado |
| `M_Vidrio_Comercial` | Azul humo `#A0C4D8` (Alfa 0.35) | 0.10 | 0.00 | Vitrinas y canceles |
| `M_Aluminio_Negro` | Grafito mate `#262626` | 0.40 | 0.85 | Cancelería y reja de terraza |

---

## 4. Colisiones Analíticas Transitables (Godot 4)

Se descartó de manera estricta el uso de mallas de colisión globales (*Convex Hull* o mallas cóncavas pesadas) en favor de cuerpos `BoxShape3D` independientes calibrados por crujía comercial en `godot_project/assets/buildings/edificio_cardenas_33.tscn`:

- `Col_Libreria`: $16.50\times 4.50\times 4.80\text{ m}$ en $(8.25, 2.25, -2.40\text{ m})$.
- `Col_Diana`: $16.50\times 4.50\times 4.30\text{ m}$ en $(8.25, 2.25, -6.95\text{ m})$.
- `Col_Anita`: $16.50\times 4.50\times 5.10\text{ m}$ en $(8.25, 2.25, -11.65\text{ m})$.
- `Col_Party`: $16.50\times 4.50\times 5.10\text{ m}$ en $(8.25, 2.25, -16.75\text{ m})$.
- `Col_Orquidea`: $9.20\times 4.50\times 5.20\text{ m}$ en $(4.60, 2.25, -21.90\text{ m})$.
- `Col_Curiel`: $7.30\times 4.50\times 6.50\text{ m}$ en $(12.85, 2.25, -21.25\text{ m})$.
- `Col_Terraza_Reja`: $4.30\times 2.00\times 7.00\text{ m}$ en $(18.65, 1.00, -10.50\text{ m})$.

---

## 5. Renders de Validación Closed-Loop

La batería de 6 vistas canónicas se encuentra disponible en `docs/images/cardenas_33/`:

1. `Cam_Cardenas_Frontal.png`: Perspectiva completa de la fachada sobre Calle Cárdenas, validando contraste de paneles comerciales y rotulación tridimensional.
2. `Cam_Esquina_Ochava.png`: Ochava a 45º y frontón Art Déco de Florería Orquídea con mosaico verde y rótulo sin espejo.
3. `Cam_Libertad_Curiel.png`: Marquesina con estrías y tótem de Foto Estudio Curiel sobre Callejón Libertad.
4. `Cam_Reverso_Estacionamiento.png`: Fachada de servicio, marquesina posterior de Bar Diana, letrero de azotea y reja perimetral.
5. `Cam_Closeup_Rotulos.png`: Acercamiento de detalle en rótulos de Annita's Boutique, silueta de Diana Cazadora y Bar Diana.
6. `Cam_Cenital_Azotea.png`: Inspección hermética de la cubierta y cartelera publicitaria.

---

## 6. Archivos del Pipeline

- **Script Procedural Maestro**: [`scripts/generate_cardenas_33.py`](file:///Users/hakkindavid/Documents/GitHub/tecate-simulator/scripts/generate_cardenas_33.py)
- **Archivo Fuente Blender**: [`blender_assets/buildings/edificio_cardenas_33.blend`](file:///Users/hakkindavid/Documents/GitHub/tecate-simulator/blender_assets/buildings/edificio_cardenas_33.blend)
- **Malla glTF/GLB Optimizada**: [`godot_project/assets/buildings/edificio_cardenas_33.glb`](file:///Users/hakkindavid/Documents/GitHub/tecate-simulator/godot_project/assets/buildings/edificio_cardenas_33.glb)
- **Escena Godot 4**: [`godot_project/assets/buildings/edificio_cardenas_33.tscn`](file:///Users/hakkindavid/Documents/GitHub/tecate-simulator/godot_project/assets/buildings/edificio_cardenas_33.tscn)
- **Integración Mundial**: [`godot_project/main.tscn`](file:///Users/hakkindavid/Documents/GitHub/tecate-simulator/godot_project/main.tscn)
