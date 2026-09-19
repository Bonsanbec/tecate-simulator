# FICHA TÉCNICA ARQUITECTÓNICA: Fuente de la Paz del Parque Miguel Hidalgo (Época 2009)

## 1. Contexto, Ubicación y Origen Cartesiano

- **Nombre Oficial**: Fuente de la Paz (Fuente Central / Noroeste del Parque Miguel Hidalgo).
- **Ubicación en Tecate**: Cuadrante Noroeste del Parque Miguel Hidalgo, en las inmediaciones de Av. Benito Juárez y Calle Pdte. Lázaro Cárdenas, Tecate, Baja California, México.
- **Coordenadas Geográficas**: Aproximadamente $32.573366^\circ\text{N}, -116.626902^\circ\text{W}$.
- **Origen Local e Integración en el Simulador**:
  - Posición cartesiana en `godot_project/main.tscn`: $\vec{P} = (-41.00\text{ m}, 399.80\text{ m}, -12.50\text{ m})$.
  - Orientación: Rotación de $45^\circ$ en el eje vertical $Y$, orientando la muesca de corte cóncava directamente hacia la intersección vial de Juárez y Cárdenas (esquina noroeste del parque).
  - Relación con el Kiosco central: Situada a $34.3\text{ m}$ al Oeste y $15.2\text{ m}$ al Norte del Kiosco octagonal.
- **Función en el Simulador**: Hito cívico, paisajístico e histórico central de la vida urbana de Tecate en el año 2009, sirviendo como punto de descanso, bancas perimetrales continuas y elemento de identidad comunitaria.

---

## 2. Dimensiones Globales y Jerarquía de Volúmenes

- **Pivote de Origen**: Base basal en el nivel rasante del suelo ($Z = 0.000\text{ m}$).
- **Cota de Descenso Subterránea (Zócalo Basal)**: $Z = -1.300\text{ m}$ (cumpliendo con la regla obligatoria de zócalo enterrado $Z \le -1.20\text{ m}$ para absorber la topografía inclinada de Tecate sin flotación).
- **Altura Total Sobre Nivel de Banqueta**: $2.55\text{ m}$ hasta la cúspide del penacho de agua ($2.22\text{ m}$ hasta el borde superior de la copa de cantera).
- **Huella en Suelo / Envergadura del Estanque**:
  - Ancho total transversal (Eje $X$): $11.80\text{ m}$.
  - Longitud longitudinal (Eje $Y$): $10.60\text{ m}$.
  - Geometría: Contorno lobulado orgánico cuadrifolio simétrico con alabeo cóncavo frontal de corte hacia el Noroeste.
- **Simetría y Geometría Primaria**:
  - Perímetro exterior: Curva cerrada B-spline de 16 nodos de control interpolados a 96 vértices poligonales.
  - Núcleo central: Prisma octagonal regular de 8 caras orientado radialmente a $45^\circ$.

---

## 3. Despiece Anatómico por Niveles (Bottom-Up)

```
                                      ( ) Chorro / Penacho de agua (Z = 2.55 m)
                                     /   \
                                   [=======] Copa / Tazón de Cantera (Z = 2.05 a 2.22 m)
                                      | |    Cuello moldurado
                                 /─────────────\
                                /  /\       /\  \  Cascada piramidal octagonal con 8
                               /  /  \     /  \  \ nervaduras continuas de cantera
                              /  /    \   /    \  \ (Pendiente 34°, Z = 0.85 a 1.70 m)
                             /  /      \ /      \  \
                      ======[===o=======o=======o===]====== Cornisa con esferas azules
                     |                                     |
                     |  [Azul] [Oro] [Azul] [Oro] [Azul]   | Friso octagonal de azulejos
                     |  [Oro] [Azul] [Oro] [Azul] [Oro]    | Talavera en damero y toberas
                     |_____________________________________| (Z = 0.00 a 0.85 m)
                                        |
  ~~~~~~~~~~~~ [ Espejo de Agua Cristalina Z = 0.35 m ] ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 [===================================================================================] Albardilla toro
 |  Paramento de Estuco Ocre Municipal con buña intermedia tallada (Z = 0.00 a 0.50 m)|
 |-----------------------------------------------------------------------------------|
 |  Zócalo Basal Subterráneo Enterrado Continuo (Z = 0.00 m hasta Z = -1.30 m)       |
```

### Nivel 1: Cimentación y Zócalo Basal Enterrado ($Z = -1.30\text{ m}$ a $0.00\text{ m}$)
- **Propósito**: Absorción de las irregularidades y pendientes topográficas del terreno del Parque Hidalgo sin permitir que el murete flote sobre la rasante.
- **Construcción**: Extrusión vertical descendente continua de los 96 vértices de la spline perimetral hasta $Z = -1.30\text{ m}$, con material de mampostería y zócalo de confinamiento (`M_Zocalo_Basal`).

### Nivel 2: Murete Perimetral y Albardilla de Banca ($Z = 0.00\text{ m}$ a $0.52\text{ m}$)
- **Paramento Vertical**: Muro perimetral continuo de $0.50\text{ m}$ de altura sobre el suelo, revestido de estuco ocre amarillo municipal (`M_Estuco_Ocre`). Presenta una buña/moldura horizontal rehundida de $0.05\text{ m}$ de espesor a $Z = 0.35\text{ m}$, replicando el detalle constructivo observado en los panoramas de Street View de febrero de 2009.
- **Albardilla Superior (Banca de Descanso)**: Moldura en sección transversal de toro/cordón semicilíndrico ($R = 0.22\text{ m}$) en terracota esmaltada cálida (`M_Terracota_Banca`), con coronamiento a $Z = 0.52\text{ m}$, concebida dimensionalmente para el asiento ergonómico de los ciudadanos.

### Nivel 3: Estanque y Espejo de Agua ($Z = 0.00\text{ m}$ a $0.35\text{ m}$)
- **Vaso Interior**: Revestimiento en mosaico vítreo turquesa sumergido (`M_Fondo_Estanque`), con profundidad de vaso de $0.50\text{ m}$.
- **Espejo de Agua**: Superficie líquida situada a $Z = 0.35\text{ m}$, dotada de material dieléctrico de alta reflectividad, refracción cristalina y color base aguamarina tenue (`M_Agua_Espejo`), que refleja el cielo de Tecate y los colores Talavera del núcleo central.

### Nivel 4: Pedestal Octagonal y Friso de Talavera ($Z = 0.00\text{ m}$ a $0.85\text{ m}$)
- **Cuerpo Octagonal**: Prisma de 8 caras regulares circunscrito en un radio de $2.35\text{ m}$.
- **Friso de Azulejos Talavera**: Paramento vertical recubierto por un damero cerámico vidriado en azul cobalto y oro brillante (`M_Talavera_Checker`), representativo de la artesanía colonial mexicana de la época 2009.
- **Cornisa Volada**: Saliente perimetral de cantera de $0.15\text{ m}$ a $Z = 0.85\text{ m}$.
- **Toberas y Esferas Cerámicas**: 8 toberas de descarga en azul ultramar situadas en el centro de cada cara, y 8 esferas ornamentales cerámicas vidriadas (`M_Azul_Tobera`) coronando el arranque de cada nervadura.

### Nivel 5: Cascada Piramidal Facetada y Nervaduras ($Z = 0.85\text{ m}$ a $1.70\text{ m}$)
- **Plataforma Escalonada Inclinada**: Cascada de 8 planos facetados que ascienden con una pendiente aproximada de $34^\circ$ desde el radio basal ($R = 2.10\text{ m}$) hasta la plataforma superior ($R = 0.95\text{ m}$).
- **Nervaduras / Mochetas Radiales de Cantera**: 8 nervaduras macizas continuas de cantera gris claro (`M_Cantera_Cascada`) de $0.14\text{ m}$ de ancho y $0.08\text{ m}$ de resalto que recorren las 8 aristas de unión de los planos, canalizando el flujo de agua en caídas independientes hacia el estanque inferior.
- **Sombreado Tectónico**: Sombreado plano (*Flat Shading*) estricto en las caras de cantera para garantizar aristas biseladas nítidas y sombras contrastadas bajo iluminación solar.

### Nivel 6: Copa Superior y Penacho Hidráulico ($Z = 1.70\text{ m}$ a $2.55\text{ m}$)
- **Pedestal del Tazón**: Cuello moldurado octagonal que asciende de $Z = 1.70\text{ m}$ a $1.90\text{ m}$.
- **Tazón / Copa de Cantera**: Recipiente cóncavo superior con vuelo exterior hasta $R = 0.72\text{ m}$ y remate a $Z = 2.22\text{ m}$ (`M_Copa_Cantera`).
- **Penacho de Agua**: Surtidor central vertical de agua translúcida burbujeante (`M_Chorro_Agua`) con una altura de $0.33\text{ m}$ sobre el borde de la copa.

---

## 4. Especificación de Materiales PBR

| Material | Elementos Asignados | Color Base / Textura | Roughness | Metallic | Sombreado |
| :--- | :--- | :--- | :---: | :---: | :---: |
| `M_Estuco_Ocre` | Paramento exterior del murete | Ocre amarillo colonial (`#D4B36A`) | 0.85 | 0.00 | Smooth |
| `M_Zocalo_Basal` | Cimentación subterránea ($Z \le 0.00\text{ m}$) | Concreto basal gris medio (`#7A7870`) | 0.95 | 0.00 | Flat |
| `M_Terracota_Banca`| Albardilla toro perimetral | Terracota tostada cocida (`#C27351`) | 0.40 | 0.00 | Smooth |
| `M_Talavera_Checker`| Friso del pedestal octagonal | Damero cerámico Azul Cobalto / Amarillo Oro | 0.18 | 0.05 | Flat |
| `M_Azul_Tobera` | Esferas y toberas de descarga | Azul ultramar vidriado (`#1B3F8B`) | 0.20 | 0.00 | Smooth |
| `M_Cantera_Cascada`| Planos y nervaduras de cascada | Cantera gris perla claro (`#DCDCD8`) | 0.75 | 0.00 | Flat |
| `M_Copa_Cantera` | Pedestal y tazón superior | Cantera beige claro (`#D8D3C8`) | 0.60 | 0.00 | Smooth |
| `M_Fondo_Estanque` | Vaso interior sumergido | Mosaico vítreo turquesa (`#288A9E`) | 0.50 | 0.00 | Smooth |
| `M_Agua_Espejo` | Superficie del agua del estanque | Turquesa translúcido / reflectivo | 0.05 | 0.00 | Smooth |
| `M_Chorro_Agua` | Penacho del surtidor central | Blanco azulado translúcido | 0.10 | 0.00 | Smooth |

---

## 5. Galería Oficial de Renders de Validación (Cycles)

Ubicación de capturas de alta definición: `docs/images/fuente_parque_hidalgo/`

1. **`Cam_Cenital_Top.png` (Vista Cenital Ortográfica)**:
   - Valida la silueta lobulada del estanque, la muesca de corte diagonal orientada al Noroeste, el ancho ergonómico de la albardilla perimetral y la concentricidad del pedestal octagonal con sus 8 toberas.
2. **`Cam_Corte_Frente.png` (Elevación Frontal)**:
   - Certifica las cotas verticales relativas, la visibilidad de la buña intermedia en el murete ocre, el zócalo enterrado inferior, el contraste del friso Talavera y el perfil piramidal de la cascada.
3. **`Cam_Perspectiva_45.png` (Axonometría General)**:
   - Demuestra la integración tridimensional de todos los volúmenes, la volumetría de las nervaduras de cantera y los reflejos en el espejo de agua.
4. **`Cam_Peatonal_Banca.png` (Perspectiva a Escala Peatonal $Z = 1.65\text{ m}$)**:
   - Simula la experiencia visual inmersiva de un ciudadano en el Parque Hidalgo contemplando la fuente a la altura de los ojos.
5. **`Cam_Closeup_Cascada.png` (Primer Plano de Nervaduras y Copa)**:
   - Inspección macro del detalle tectónico: mochetas radiales continuas de cantera tallada, biseles nítidos libres de aberraciones de sombreado y copa superior.

---

## 6. Colisiones y Arquitectura en Godot Engine 4

- **Archivo Runtime GLB**: `godot_project/assets/fuente_parque_hidalgo.glb` (Primitivas PBR optimizadas, cero banquetas embebidas).
- **Escena Godot**: `godot_project/assets/fuente_parque_hidalgo.tscn`.
- **Nodo Raíz**: `StaticBody3D` optimizado para colisiones dinámicas de alto rendimiento a 60 FPS estables.
- **Estrategia de Colisión Analítica Descompuesta**:
  - **Murete Perimetral (Banca)**: Cadena de 24 colisionadores `BoxShape3D` tangentes a lo largo de la curva alabeada de la spline, orientados con matrices `Transform3D` coordinadas $1:1$ con la geometría física. Permite al jugador interactuar con la banca perimetral sin paredes invisibles ni huecos cóncavos anómalos.
  - **Fondo de Estanque**: 1 `BoxShape3D` horizontal ($11.50 \times 0.20 \times 11.50\text{ m}$) que previene caídas al infinito si el jugador escala la banca.
  - **Núcleo Central**: 1 `CylinderShape3D` ($R = 2.35\text{ m}$, $H = 0.65\text{ m}$) para el pedestal octagonal con friso de Talavera.
  - **Cuerpo de Cascada**: 1 `CylinderShape3D` ($R = 1.65\text{ m}$, $H = 1.05\text{ m}$) escalonado.
  - **Copa Superior**: 1 `CylinderShape3D` ($R = 0.75\text{ m}$, $H = 0.75\text{ m}$).
- **Prohibición de Mallas Convexas Globales**: No se utilizaron mallas `ConcavePolygonShape3D` pesadas ni `ConvexPolygonShape3D` envolventes simplificadas que habrían cerrado el vaso de la fuente impidiendo el contacto cercano.

---

## 7. Instrucciones de Reproducibilidad

Para regenerar de forma totalmente desatendida el archivo `.blend`, el runtime `.glb`, la escena `.tscn` y la suite de renders Cycles:

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/generate_fuente_parque_hidalgo.py
```
