# Ficha Técnica Arquitectónica: Hotel Tecate (Ground-Truth Histórico 2009)

Documento técnico de especificación morfológica, paramétrica, PBR y consenso multi-perspectiva para la reconstrucción fidedigna del complejo hotelero y comercial **Hotel Tecate** (esquina Calle Presidente Lázaro Cárdenas y Callejón Libertad, Tecate, B.C.) en Blender 5.1 y Godot Engine 4.

---

## 1. Contexto Urbano y Emplazamiento Cartesiano

- **Nombre Oficial**: Hotel Tecate (Época histórica 2009).
- **Emplazamiento Histórico**: Esquina de manzana en la intersección vial de Calle Presidente Lázaro Cárdenas (eje norte-sur) y Callejón Libertad (eje poniente-oriente), frente al Parque Miguel Hidalgo.
- **Vértice de Esquina (Ochava Colonial)**: Emplazado en la intersección proyectada de ambas calles apuntando en chaflán a $45^\circ$ hacia el Parque Miguel Hidalgo (Monumento a Lázaro Cárdenas).
- **Contrato Cartesiano Canónico (Primer Cuadrante Ortogonal)**:
  - $\text{Origen }(0,0,0)$: Intersección de las alineaciones de fachada de Cárdenas y Libertad a nivel de rasante.
  - $\text{Eje }+X$: Vector paralelo a Calle Presidente Lázaro Cárdenas en dirección sur ($X \in [0.00, 28.60\text{ m}]$).
  - $\text{Eje }+Y$: Vector paralelo a Callejón Libertad en dirección oriente ($Y \in [0.00, 20.40\text{ m}]$).
  - $\text{Eje }+Z$: Cota de elevación vertical.
- **Calibración de Rasante y Zócalo Subterráneo**:
  - Todo el perímetro cuenta con zócalo basal continuo en concreto grafito oscuro (`M_Zocalo_Basal`) que desciende en profundidad hasta $Z = -1.20\text{ m}$ bajo rasante, absorbiendo los desniveles y pendientes de la vialidad sin producir flotación del edificio.
  - Prohibición estricta cumplida: el asset 3D (`hotel_tecate.glb`) no embebe banquetas, cordones ni asfalto.
- **Integración en Escena Principal Godot (`godot_project/main.tscn`)**:
  - Instancia: `[node name="Hotel_Tecate" parent="." instance=ExtResource("13_hotel_tecate")]`
  - `transform = Transform3D(0, 0, 1, 0, 1, 0, -1, 0, 0, -46.5, 398.88, 41.5)`
  - **Rotación Cardinal Pura**: Rotación ortogonal estricta de $-90^\circ$ ($270^\circ$) alrededor del eje vertical $Y$, alineando el eje local $+X$ con el sur ($+Z_{\text{mundo}}$) a lo largo de Calle Pdte. Lázaro Cárdenas, y el eje local $-Z$ con el oriente ($+X_{\text{mundo}}$) a lo largo de Callejón Libertad.
  - **Cota Rasante**: $Y = 398.88\text{ m}$, posando la planta baja a ras de la plataforma de la manzana (`manzanas_baked.glb`) y dejando el zócalo basal enterrado herméticamente hasta $Y = 397.68\text{ m}$.
  - **Colisiones Analíticas**: Escena `hotel_tecate.tscn` con 9 cuerpos `BoxShape3D` coordinados con los ejes locales de glTF, preservando el zaguán de acceso de $4.80\text{ m} \times 3.20\text{ m}$ totalmente transitable.

---

## 2. Anatomía y Nomenclatura Vial Rectificada

El inmueble se compone de los siguientes cuerpos arquitectónicos fidedignamente reconstruidos según la evidencia fotográfica histórica:

1. **Ochava a 45º (Chaflán Parque Miguel Hidalgo)**:
   - Longitud de cuerda: $3.96\text{ m}$ ($X \in [0.00, 2.80\text{ m}], Y \in [0.00, 2.80\text{ m}]$).
   - **Planta Baja**: cancel comercial retranqueado con puertas dobles acristaladas de marco oscuro y marquesina volada metálica ("MOCHO RESTAURANT").
   - **Planta Alta**: balcón exterior en voladizo ($1.15\text{ m}$ de saliente) con peana de moldura beige y barandal ornamental de hierro forjado negro ($H = 1.05\text{ m}$), con puerta francesa acristalada de acceso.
   - **Pretil y Corona**: remate colonial curvo acampanado continuo que se eleva hasta $Z = 8.70\text{ m}$, con alvéolo/rejilla cuadrada central de ventilación.
   - **Rótulo Publicitario en Voladizo**: letrero ortogonal de doble cara sobre mástil en $X = 2.60\text{ m}$:
     - Anverso y Reverso: **"HOTEL TECATE"** en letras rojas 3D y **"Tel. 654-11-16"** en azul.

2. **Fachada Oeste sobre Calle Presidente Lázaro Cárdenas (6 Crujías, 25.80 m)**:
   - **Crujía 1 ($X \in [2.80, 7.10\text{ m}]$)**: Escaparate con cortina metálica de persiana, condensador de minisplit A/C en fachada y ventanería blanca corredera en planta alta.
   - **Crujía 2 ($X \in [7.10, 11.40\text{ m}]$)**: Gran escaparate con cortina metálica enrollable, aplique decorativo circular en muro y ventana modular en planta alta.
   - **Crujía 3 ($X \in [11.40, 15.70\text{ m}]$)**: Puerta de acceso peatonal y ventanas modulares altas.
   - **Crujía 4 ($X \in [15.70, 20.00\text{ m}]$)**: Local comercial con toldo de lona festoneada color beige arena y ventanas gemelas en planta alta.
   - **Crujía 5 — Zaguán Túnel Central Transitable ($X \in [20.00, 24.80\text{ m}]$)**:
     - Vano pasante abierto de $4.80\text{ m}$ de ancho y $3.20\text{ m}$ de gálibo libre hacia el patio interior.
     - Franja superior continua de bloques de vidrio translúcido (*pavés*) en $Z \in [3.20, 3.80\text{ m}]$.
     - Puesto de comida "Taquería Los Gallos" con mostrador interior y espacio caminable sin colisiones bloqueantes.
     - Planta alta con dos ventanas simétricas y frontón escalonado central en el pretil.
   - **Crujía 6 — "Internet World" ($X \in [24.80, 28.60\text{ m}]$)**:
     - Cancel comercial con toldo vinílico azul y rótulos tridimensionales legibles de izquierda a derecha:
       `INTERNET WORLD`
       `VENTA Y REPARACION DE COMPUTADORAS`
     - Ventana corrida triple en planta alta.
     - Medianera sur ciega enrasada en $X = 28.60\text{ m}$ que colinda con "Dulcería El Molino".

3. **Fachada Norte sobre Callejón Libertad (4 Crujías, 17.60 m)**:
   - **Crujía N1 ($Y \in [2.80, 7.00\text{ m}]$)**: Ventanal con cortina enrollable, minisplit A/C, placa oval Corona y ventana superior corredera.
   - **Crujía N2 — Franquicia SUBWAY ($Y \in [7.00, 12.00\text{ m}]$)**:
     - Logotipo tridimensional institucional **SUBWAY** en relieve amarillo sobre fascia verde esmeralda.
     - Escaparate comercial y cancelería.
     - Planta alta con ventana modular grande y ventana cuadrada auxiliar.
   - **Crujía N3 ($Y \in [12.00, 15.20\text{ m}]$)**: Portón de rejas metálicas verticales de servicio hacia el hotel.
   - **Crujía N4 ($Y \in [15.20, 20.40\text{ m}]$)**: Local comercial con toldo verde semicilíndrico ("Linda..."), ventana superior y medianera oriente en $Y = 20.40\text{ m}$.

4. **Patio Interior y Azotea Hermética**:
   - Patio central abierto de $12.00\text{ m} \times 8.00\text{ m}$ accesible a través del zaguán túnel de la Crujía 5.
   - Pasillo perimetral techado en planta alta con barandal de forja negra para distribución de habitaciones.
   - Azotea continua sellada con losa asfáltica hermética (`M_Azotea_Asfalto`), caseta de escaleras/elevador y antenas parabólicas satelitales (*Dish*).

---

## 3. Salidas Generadas y Assets del Proyecto

1. **Script Generador Procedural**:
   - [`scripts/generate_hotel_tecate.py`](file:///Users/hakkindavid/Documents/GitHub/tecate-simulator/scripts/generate_hotel_tecate.py)
2. **Archivo Maestro Blender**:
   - `blender_assets/buildings/hotel_tecate.blend`
3. **Asset 3D Optimizado Godot 4**:
   - `godot_project/assets/buildings/hotel_tecate.glb` (desacoplado de banquetas)
4. **Escena Instanciable Godot 4**:
   - `godot_project/assets/buildings/hotel_tecate.tscn` (con jerarquía de colisiones analíticas `BoxShape3D` y zaguán transitable)
5. **Batería de Validación (6 Renders Técnicos Cycles)**:
   - `docs/images/hotel_tecate/hotel_tecate_ochava_45.png`
   - `docs/images/hotel_tecate/hotel_tecate_subway_north.png`
   - `docs/images/hotel_tecate/hotel_tecate_cardenas_west.png`
   - `docs/images/hotel_tecate/hotel_tecate_zaguan_closeup.png`
   - `docs/images/hotel_tecate/hotel_tecate_dulceria_border.png`
   - `docs/images/hotel_tecate/hotel_tecate_aerial_top.png`
