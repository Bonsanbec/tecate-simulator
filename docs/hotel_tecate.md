# Ficha Técnica Arquitectónica: Hotel Tecate (Ground-Truth Histórico 2009 — Versión V4.0 Refinada)

Documento técnico de especificación morfológica, paramétrica, fenestración, toldería, PBR y consenso multi-perspectiva para la reconstrucción fidedigna del complejo hotelero y comercial **Hotel Tecate** (esquina Calle Presidente Lázaro Cárdenas y Callejón Libertad, Tecate, B.C.) en Blender 5.1 y Godot Engine 4.

---

## 1. Contexto Urbano y Emplazamiento Cartesiano

- **Nombre Oficial**: Hotel Tecate (Época histórica 2009).
- **Emplazamiento Histórico**: Esquina de manzana en la intersección vial de Calle Presidente Lázaro Cárdenas (eje norte-sur) y Callejón Libertad (eje poniente-oriente), frente al Parque Miguel Hidalgo y el monumento a Lázaro Cárdenas.
- **Vértice de Esquina (Ochava Colonial)**: Emplazado en la intersección proyectada de ambas calles apuntando en chaflán a $45^\circ$ hacia el Parque Miguel Hidalgo.
- **Contrato Cartesiano Canónico (Primer Cuadrante Ortogonal)**:
  - $\text{Origen }(0,0,0)$: Intersección de las alineaciones de fachada de Cárdenas y Libertad a nivel de rasante.
  - $\text{Eje }+X$: Vector paralelo a Calle Presidente Lázaro Cárdenas en dirección sur ($X \in [0.00, 26.20\text{ m}]$).
  - $\text{Eje }+Y$: Vector paralelo a Callejón Libertad en dirección oriente ($Y \in [0.00, 18.00\text{ m}]$).
  - $\text{Eje }+Z$: Cota de elevación vertical.
- **Calibración de Rasante y Zócalo Subterráneo**:
  - Todo el perímetro cuenta con zócalo basal continuo en concreto grafito oscuro (`M_Zocalo_Basal`) que desciende en profundidad hasta $Z = -1.25\text{ m}$ bajo rasante, absorbiendo los desniveles y pendientes de la vialidad sin producir flotación del edificio.
  - **Prohibición estricta cumplida**: El asset 3D (`hotel_tecate.glb`) no embebe banquetas, cordones ni asfalto.
- **Integración en Escena Principal Godot (`godot_project/main.tscn`)**:
  - Instancia: `[node name="Hotel_Tecate" parent="." instance=ExtResource("13_hotel_tecate")]`
  - `transform = Transform3D(0, 0, -1, 0, 1, 0, 1, 0, 0, -44.06, 398.79, 45.40)`
  - **Rotación Cardinal Pura hacia el Noroeste (NW)**:
    - La ochava apunta estrictamente al **Noroeste (NW)** hacia el Parque Miguel Hidalgo.
    - La fachada oeste asienta a lo largo de Calle Pdte. Lázaro Cárdenas ($X = -44.06\text{ m}$, extendida hacia el sur $Z \in [48.20, 74.00\text{ m}]$) con normal exterior hacia el **Oeste**.
    - La fachada norte asienta a lo largo de Callejón Libertad ($Z = 45.40\text{ m}$, extendida hacia el oriente $X \in [-41.26, -23.66\text{ m}]$) con normal exterior hacia el **Norte**.
  - **Cota Rasante**: $Y = 398.79\text{ m}$, posando la planta baja a ras de la plataforma de la manzana catastral (`UrbanManzanas`) y dejando el zócalo basal enterrado herméticamente hasta $Y = 397.59\text{ m}$ ($Z = -1.20\text{ m}$).
  - **Colisiones Analíticas**: Escena `hotel_tecate.tscn` con 9 cuerpos `BoxShape3D` coordinados con los ejes locales de glTF, preservando el zaguán de acceso de $4.80\text{ m} \times 3.20\text{ m}$ totalmente transitable sin paredes invisibles.

---

## 2. Anatomía, Fenestración y Nomenclatura Vial Refinada (V4.0)

El inmueble se compone de los siguientes cuerpos arquitectónicos fidedignamente reconstruidos según la evidencia fotográfica histórica:

### 1. Ochava en Chaflán a 45º (Frente Parque Miguel Hidalgo)
- **Cuerda de Esquina**: $X \in [0.00, 2.80\text{ m}], Y \in [0.00, 2.80\text{ m}]$ en ángulo de $45^\circ$.
- **Planta Baja**: Cancel comercial retranqueado con puertas dobles acristaladas de marco oscuro, marquesina volada metálica de acero espejo y escalón de acceso.
- **Planta Alta**: Balcón exterior voladizo soportado por 3 ménsulas escalonadas de concreto blanco, barandal ornamental de hierro forjado negro ($H = 1.05\text{ m}$), puerta de balcón coronada por arco decorativo de bloques de vidrio translúcido (*pavés*).
- **Torreón Semicircular Peraltado (Corona)**:
  - Estructura cilíndrica sobresaliente de radio $1.60\text{ m}$ que se eleva hasta $Z = 9.15\text{ m}$ ($+1.70\text{ m}$ sobre el pretil general).
  - Flanqueado por golas/aletas decorativas curvadas de transición hacia los pretiles adyacentes.
  - Alvéolo / ventila cuadrada central con rejilla metálica oscura en $Z = 8.35\text{ m}$.
- **Cartel Publicitario en Mástil Volado**:
  - Emplazado en $X = 2.60\text{ m}$ con mástil de soporte en celosía metálica.
  - Letrero rectangular ortogonal de doble cara:
    - **"HOTEL TECATE"** en relieve tridimensional bermellón.
    - **"Tel. 654-11-16"** en azul rey institucional.

### 2. Fachada Oeste sobre Calle Presidente Lázaro Cárdenas (5 Módulos, 26.20 m)
- **Módulo 1 ($X \in [2.80, 7.50\text{ m}]$)**:
  - Planta Baja: Escaparate acristalado y persiana metálica enrollable. Condensador de minisplit A/C en fachada con aspas y rejillas.
  - Planta Alta: 2 ventanas gemelas pareadas `[][]` de dos hojas con perfilería blanca, antepecho y moldura de dintel.
- **Módulo 2 ($X \in [7.50, 12.00\text{ m}]$)**:
  - Planta Baja: Gran escaparate con cortina metálica y aplique decorativo en muro.
  - Planta Alta: 2 ventanas gemelas pareadas con molduras.
- **Módulo 3 ($X \in [12.00, 16.50\text{ m}]$)**:
  - Planta Baja: Local comercial con toldo de lona festoneada color beige arena, cancelería comercial y puerta peatonal.
  - Planta Alta: 2 ventanas gemelas pareadas.
- **Módulo 4 — Taquería Los Gallos y Zaguán Túnel ($X \in [16.50, 21.80\text{ m}]$)**:
  - Planta Baja: Zaguán túnel central pasante ($4.80\text{ m} \times 3.20\text{ m}$) hacia el patio interior, totalmente transitable sin colisiones.
  - Puesto de comida "Taquería Los Gallos" con mostrador interior, toldo rojo festoneado con rótulo tipográfico **"TAQUERIA LOS GALLOS"**.
  - Franja corrida de bloques de vidrio translúcido (*pavés*) sobre el vano del zaguán ($Z \in [3.20, 3.80\text{ m}]$).
  - Planta Alta: 2 ventanas simétricas y frontón central escalonado en el pretil.
- **Módulo 5 — "Internet World" ($X \in [21.80, 26.20\text{ m}]$)**:
  - Planta Baja: Local comercial con toldo semicilíndrico verde bosque con rótulo tipográfico blanco tridimensional:
    `INTERNET WORLD`
    `VENTA Y REPARACION DE COMPUTADORAS`
  - Planta Alta: Ventana corrida triple de 3 hojas.
  - Medianera sur ciega enrasada en $X = 26.20\text{ m}$ colindando con "Dulcería El Molino".

### 3. Fachada Norte sobre Callejón Libertad (5 Crujías, 18.00 m)
- **Crujía N1 ($Y \in [2.80, 6.20\text{ m}]$)**:
  - Planta Baja: Ventanal comercial con persiana enrollable, minisplit A/C en fachada, placa publicitaria decorativa.
  - Planta Alta: Ventana modular con carpintería blanca.
- **Crujía N2 — Franquicia SUBWAY ($Y \in [6.20, 11.20\text{ m}]$)**:
  - Planta Baja: Rótulo tipográfico volumétrico **SUBWAY** en amarillo institucional sobre relieve directo en fachada de estuco, marquesina volada y cancelería de vidrio de piso a techo.
  - Planta Alta: Ventana modular grande y ventana auxiliar de ventilación.
- **Crujía N3 — Portón y Terraza ($Y \in [11.20, 13.80\text{ m}]$)**:
  - Portón de servicio de rejas metálicas verticales hacia el hotel.
- **Crujía N4 — Local "Casa Paris" y Sombrillas ($Y \in [13.80, 18.00\text{ m}]$)**:
  - Planta Baja: Local comercial con toldo negro de borde blanco festoneado con letrero **"CASA PARIS"**.
  - Sombrillas de terraza rojas exteriores frente a la fachada.
  - Planta Alta: Ventana de habitación y medianera oriente en $Y = 18.00\text{ m}$.

### 4. Patio Interior y Azotea Hermética
- Patio central de $10.50\text{ m} \times 7.20\text{ m}$ comunicado por el zaguán túnel de la fachada oeste.
- Corredor perimetral techado en planta alta con barandal de forja negra para acceso a habitaciones.
- Azotea sellada hermética con losa asfáltica multicapa (`M_Azotea_Asfalto`), caseta de servicio y antenas satelitales tipo *Dish*.

---

## 3. Shaders y Materiales PBR Fotorrealistas

| Material | Base Color / Textura | Roughness | Metallic | Características PBR |
| :--- | :--- | :--- | :--- | :--- |
| `M_Estuco_Terracota` | `#CC5828` `(0.58, 0.28, 0.14)` | 0.86 | 0.00 | Estuco naranja terracota histórico 2009 con proyección triplanar PBR seamless continuo |
| `M_Moldura_Crema` | `#F0E6D2` `(0.92, 0.88, 0.80)` | 0.75 | 0.00 | Molduras perimetrales, cornisas, ménsulas y antepechos |
| `M_Zocalo_Basal` | `#2D2B2A` `(0.18, 0.17, 0.16)` | 0.90 | 0.00 | Concreto rugoso zócalo subterráneo hasta $Z = -1.25\text{ m}$ |
| `M_Paves_Vidrio` | `#D8ECE8` `(0.85, 0.92, 0.91)` | 0.15 | 0.00 | Bloques de vidrio con cuadrícula y rugosidad refractante |
| `M_Vidrio_Ventana` | `#0E171E` `(0.06, 0.09, 0.12)` | 0.08 | 0.10 | Vidrio semirreflectante tintado exterior |
| `M_Cortina_Metalica`| `#8E9599` `(0.55, 0.58, 0.60)` | 0.40 | 0.80 | Lámina acanalada horizontal con relieve bump de estrías |
| `M_Toldo_Arena` | `#C8B282` `(0.78, 0.70, 0.51)` | 0.85 | 0.00 | Lona gruesa texturizada con festón |
| `M_Toldo_Rojo` | `#B82822` `(0.72, 0.16, 0.13)` | 0.82 | 0.00 | Toldo Taquería Los Gallos y sombrillas de terraza |
| `M_Toldo_Verde` | `#1D5A38` `(0.11, 0.35, 0.22)` | 0.82 | 0.00 | Toldo semicilíndrico Internet World |
| `M_Toldo_Negro` | `#1A1A1A` `(0.10, 0.10, 0.10)` | 0.80 | 0.00 | Toldo Casa Paris con borde festoneado blanco |
| `M_Rotulo_Subway` | `#FFCE00` `(1.00, 0.81, 0.00)` | 0.30 | 0.00 | Amarillo institucional en relieve directo |
| `M_Hierro_Forjado` | `#1C1C1C` `(0.11, 0.11, 0.11)` | 0.35 | 0.85 | Barandales de balcón y pasillos del patio |

---

## 4. Batería de Renders de Validación Cycles CPU

1. **`hotel_tecate_ochava_45.png`**: Vista en ángulo de $45^\circ$ hacia la ochava, mostrando el torreón semicircular peraltado, la ventila de alvéolo, ménsulas, barandal de forja, balcón con arco de pavés, marquesina de cancel y letrero volado en mástil.
2. **`hotel_tecate_subway_north.png`**: Fachada norte completa sobre Callejón Libertad con rótulo 3D SUBWAY, cancelería comercial, Casa Paris con toldo negro y sombrillas rojas.
3. **`hotel_tecate_cardenas_west.png`**: Fachada oeste completa sobre Calle Pdte. Lázaro Cárdenas con las 5 crujías, ventanas gemelas pareadas `[][]`, minisplit, toldos arena, zaguán túnel de Los Gallos e Internet World.
4. **`hotel_tecate_zaguan_closeup.png`**: Acercamiento en perspectiva peatonal al zaguán túnel, mostrador de taquería, franja de pavés y toldo rojo.
5. **`hotel_tecate_dulceria_border.png`**: Vista de la esquina suroeste en colindancia con Dulcería El Molino.
6. **`hotel_tecate_aerial_top.png`**: Vista cenital de azotea sellada y patio interior central.
