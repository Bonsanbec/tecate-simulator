# Ficha Técnica Arquitectónica: Banco BBVA Tecate Centro (V7.0 Ground-Truth Histórico 2009)

Documento técnico de especificación morfológica, paramétrica, PBR y consensus multi-perspectiva para la reconstrucción fidedigna del edificio comercial/financiero del **Banco BBVA** (esquina Av. Benito Juárez y Calle Presidente Lázaro Cárdenas, Tecate, B.C.) en Blender 5.1 y Godot Engine 4.

---

## 1. Contexto Urbano y Emplazamiento Cartesiano

- **Nombre Oficial**: Edificio Lic. José F. Guajardo / Sucursal BBVA Bancomer Tecate Centro (2009).
- **Emplazamiento Histórico**: Esquina de manzana en la intersección vial de Avenida Benito Juárez (eje poniente-oriente) y Calle Presidente Lázaro Cárdenas (eje norte-sur).
- **Vértice de Esquina (Ochava Guajardo)**: Emplazado exactamente en la intersección de las dos vialidades apuntando hacia el noreste.
- **Coordenadas en Escena Godot (`main.tscn`)**:
  - `Position = Vector3(-66.8, 400.38, -24.81)`
  - `Basis = Transform3D(-1, 0, 0, 0, 1, 0, 0, 0, -1)` (rotación pura de $180.0^\circ$ garantizando paralelismo geométrico estricto con la banqueta de Av. Benito Juárez, sin reducción de sección hacia el poniente).
  - **Calibración de Rasante y Zócalo Subterráneo**: La Calle Lázaro Cárdenas presenta un descenso topográfico de $-0.67\text{ m}$ hacia el norte. El zócalo basal de concreto grafito se extiende en profundidad hasta $Z = -1.20\text{ m}$ bajo cota de apoyo, quedando herméticamente anclado en la rasante vial de Godot sin desniveles flotantes ni inclinaciones aparentes.
  - Nodo raíz: `BBVA_Tecate (StaticBody3D)` con colisionadores analíticos descompuestos que eliminan cualquier barrera invisible en la rampa y permiten el ingreso físico al recibidor de DENTISTA.

---

## 2. Anatomía y Nomenclatura Vial Rectificada

El edificio se compone de los siguientes cuerpos arquitectónicos fidedignamente reconstruidos según la evidencia fotográfica histórica:

1. **Ochava a 45º (Torreón Lic. José F. Guajardo 1956)**:
   - Apunta en diagonal hacia el cruce de Av. Juárez y Calle Cárdenas.
   - **Morfología**: **Trapecio invertido de mosaico veneciano pizarra meteorizada** (`#252B3E`), con base inferior estrecha ($4.60\text{ m}$ a $Z = 3.20\text{ m}$) y base superior ensanchada ($5.80\text{ m}$ a $Z = 9.05\text{ m}$), coronado por albardilla/coping de piedra natural continua a $Z = 9.05\text{ m} - 9.17\text{ m}$.
   - Sin cuñas ni franjas blancas laterales extrañas; integración directa con el cuerpo del edificio.
   - Inscripción en letras 3D de bronce fundido en 3 líneas:
     ```
     EDIFICIO
     LIC. JOSE F. GUAJARDO
     1956
     ```
   - Acceso bancario en PB: cancelería de aluminio anodizado oscuro con puertas dobles acristaladas al centro y amplios ventanales comerciales a ambos lados con persianas verticales.
   - **Espectacular de Azotea 2009 con branding en ambas caras (Oeste y Este)**:
     - Mástil tubular de acero central.
     - Panel superior azul cobalto (`#00288E`) con recuadro blanco `BBVA` en relieve y rótulo blanco `Bancomer`.
     - Panel inferior blanco con logotipo rojo `RED` y texto verde `CAJERO AUTOMATICO`.
     - Ambas caras reproducen fielmente la rotulación corporativa completa.

2. **Fachada Sur sobre Avenida Benito Juárez (Eje Poniente-Oriente, sin Cajero)**:
   - Longitud total de $22.80\text{ m}$, 4 crujías modulares.
   - **Fascia 2009 de Alucobond azul cobalto**: cubre las Crujías 1 a 3 (hasta el machón $X = 17.40\text{ m}$).
   - **Crujía 4 (`JUAN VARGAS R`)**: dintel superior en estuco blanco continuo, tal como documenta la fotografía histórica `media_1789774756138.png`.
   - **Filetes blancos horizontales**: espaciado calibrado con holgura limpia ($0.27\text{ m}$) respecto al texto `Bancomer`, extendiéndose hasta $X = 17.20\text{ m}$ sin solapamiento ni recorte.
   - Vidrios de planta alta con despachos: `CASAS TERRENOS RANCHOS` (Crujía 3) y `JUAN VARGAS R` (Crujía 4).
   - Mansarda superior continua de tejas coloniales terracota sobre cornisa corrida.

3. **Fachada Oeste sobre Calle Presidente Lázaro Cárdenas (Eje Norte-Sur, con Cajero)**:
   - Longitud continua de $30.00\text{ m}$ con 6 crujías modulares y zaguán de acceso a consultorios ($25.20\text{ m}$ de sección bancaria + $4.80\text{ m}$ de consultorio DENTISTA).
   - Mansarda de tejas continuas con ménsulas/canecillos de concreto en voladizo (corbels).
   - **Crujías 1 a 3**: Sección bancaria con fascia azul cobalto 2009, logotipo `BBVA Bancomer` con separación no-invasiva de filetes horizontales blancos.
   - **Crujía 3**: Portal de **Cajero Automático** en el lado izquierdo del vano, con caja de luz azul y rojo `RED` + `CAJERO AUTOMATICO`, cancel de vidrio sellado y muro posterior hermético.
   - **Crujías 4 y 5**: Despachos con fascia plateada de Alucobond metálico.
   - **Crujía 6 (DENTISTA - Ground Truth `media_1789778345732`)**:
     - Paño de fachada azul marino sobre el muro con letras 3D de latón dorado `DENTISTA`.
     - Alero/marquesina horizontal en voladizo ($1.15\text{ m}$ de saliente sobre banqueta).
     - Rótulo colgante blanco perpendicular a 90º centrado bajo el alero, con textos legibles en ambas caras:
       - `Dr. Eduardo R. Álvarez Ocampo` (rojo)
       - `DENTISTA` (azul marino)
       - `LOCAL - 1    RX   Tel: 654-11-57`
       - `SE ACEPTAN ASEGURANZAS U.S.A.`
       - `ATENCION ESPECIAL A NIÑOS - ORTODONCIA`
     - Recibidor/zaguán transitable con escalera interior de 4 peldaños y colisionadores escalonados en Godot.
     - Machón esquinero norte revestido en mosaico vítreo a juego con Guajardo.

4. **Fachada Este hacia Estacionamiento (Ground Truth `media_1789781403754` y `media_1789783721505`)**:
   - **Longitud ampliada proporcionalmente**: $25.20\text{ m}$ continuos (equivalente a la longitud de Cárdenas menos el área de Dentista, $30.00 - 4.80 = 25.20\text{ m}$).
   - **7 crujías modulares**: 7 ventanas en planta alta de 3 hojas verticales con travesaño horizontal en el tercio superior, y 7 módulos en planta baja (6 escaparates comerciales y puerta peatonal de servicio en Crujía 3).
   - Rótulo en pintura blanca sobre cristal `LICENCIADO EN DERECHO` en Crujía 1.
   - 6 apliques lumínicos exteriores montados en las pilastras de planta baja.
   - Rampa vehicular descendente con barandal tubular blanco, murete exterior en $X = 27.35\text{ m}$ (sin colisiones que bloqueen el paso) y letrero ortogonal `ENTRADA BBVA ➔`.
   - **Cero estructuras parásitas**: cilindro posterior falso y vanos abiertos de iteraciones anteriores totalmente erradicados.

5. **Fachada Sur Posterior y Pared en Arco Cóncavo Inward (Ground Truth `media_1789784140324`)**:
   - **Pared Sur Lisa**: Paño continuo en $Y = 25.20\text{ m}$ desde Cárdenas ($X = 0.0\text{ m}$) hasta $X = 17.40\text{ m}$ (longitud equivalente a donde termina el azul de BBVA en Juárez), con moldura horizontal a media altura ($Z = 3.20\text{ m}$).
   - **Pared en Arco Cóncavo hacia Adentro**: Sella la distancia entre el final de la cara Sur ($X = 17.40\text{ m}$) y la cara Estacionamiento ($X = 22.80\text{ m}$), curvándose suavemente hacia el interior del edificio ($Y = 25.20 - 1.35 \cdot \sin(\pi \cdot u)$).
   - **Pilar Central Delgado**: Machón/contrafuerte rectangular vertical de $0.40\text{ m}$ de frente que sobresale marcadamente del arco y remata por encima del pretil ($Z = 7.45\text{ m}$).
   - **Dos Ventanas Rectangulares Pequeñas en Planta Alta**: Ubicadas a ambos lados del pilar central ($Z \in [5.42, 6.35\text{ m}]$), provistas de repisas exteriores de piedra natural (sills) a $Z = 5.30\text{ m}$.
   - **Sellado Hermético de Azotea**: Losa continua con material de impermeabilización asfáltica cerrando toda la unión entre el arco y el bloque principal.

---

## 3. Despiece y Dimensiones Técnicas por Niveles

```
+12.65 m  ▲  Cúspide de Caja de Luz Espectacular en Azotea (Rotulada ambas caras)
          │  [Panel Azul BBVA Bancomer: 3.60 x 1.65 m]
+11.00 m  ┼  División de Panel
          │  [Panel Blanco RED / CAJERO AUTOMATICO: 3.60 x 1.15 m]
+9.85 m   ┼  Base de Caja de Luz
          │  [Poste central tubular de acero: H = 0.85 m]
+9.05 m   ┼  Pretil Superior del Torreón Guajardo (Base mayor del trapecio: 5.80 m)
          │  [Albardilla/coping pétreo natural: 0.12 m espesor]
+8.15 m   ┼  Cumbrera de Mansarda de Tejas (Alas Juárez y Cárdenas)
          │  [Teja curva colonial de barro: pendiente 25°, H = 0.70 m]
+7.45 m   ┼  Remate del Pilar Central del Arco Posterior / Cornisa Corrida
+7.10 m   ┼  Dintel de Ventanales Planta Alta y Pretil de Fachadas Este/Sur
+4.30 m   ┼  Remate de Fascia Alucobond Azul Corporativo 2009 (H = 1.10 m)
+3.20 m   ┼  Moldura Horizontal Intermedia / Viga Dintel Guajardo (4.60 m)
+2.85 m   ┼  Dintel de cancelería PB (Vanos de H = 2.45 m a 2.80 m)
+0.40 m   ┼  Cota Superior de Banqueta / Plinto Basal Visible
 0.00 m   ┼  Nivel Cero de Referencia Estructural
-1.20 m   ▼  Profundidad de Zócalo Enterrado (Absorbe desniveles viales hasta -0.67 m)
```

---

## 4. Salidas Generadas y Assets del Proyecto

1. **Archivo Maestro Blender**:
   - `blender_assets/buildings/bbva_tecate_centro.blend`
2. **Asset 3D Optimizado Godot 4 (Edificio hermético sin banqueta)**:
   - `godot_project/assets/buildings/bbva_tecate_centro.glb`
3. **Asset 3D Modular de Banqueta Urbana**:
   - `godot_project/assets/buildings/banqueta_bbva_tecate.glb`
4. **Escenas Instanciables Godot 4**:
   - `godot_project/assets/buildings/bbva_tecate_centro.tscn`: escena unificada con colisionadores analíticos de alta precisión (peldaños de escalera en DENTISTA, colisionadores curvos del arco posterior, murete exterior de rampa sin barreras en pasillo peatonal).
   - `godot_project/assets/buildings/banqueta_bbva_tecate.tscn`: escena modular independiente de la banqueta.
5. **Integración en Escena Principal (`main.tscn`)**:
   - Emplazado en `Position = Vector3(-66.8, 400.38, -24.81)`, `Basis = Transform3D(-1, 0, 0, 0, 1, 0, 0, 0, -1)`.
6. **Renders Técnicos de Validación (`docs/images/bbva/`)**:
   - `bbva_guajardo_45.png`: Chaflán Guajardo a 45º y letrero 2009 en azotea.
   - `bbva_juarez_frontal.png`: Fachada Sur (Av. Juárez) con 4 crujías, fascia azul y filetes calibrados.
   - `bbva_cardenas_west.png`: Fachada Oeste (Calle Cárdenas) con 6 crujías, portal ATM y consultorio DENTISTA.
   - `bbva_dentista_closeup.png`: Detalle fotorrealista de DENTISTA, marquesina, rótulo colgante a 90º y escalera.
   - `bbva_east_parking.png`: Fachada Este ampliada a 25.20 m con 7 crujías, rampa y caseta.
   - `bbva_east_ground_truth.png`: Perspectiva matching ángulo exacto de `media_1789781403754`.
   - `bbva_south_inward_arc.png`: Arco cóncavo posterior, pilar central y ventanas con repisa matching `media_1789784140324`.
   - `bbva_aerial_top.png`: Vista cenital mostrando huella volumétrica cerrada y distribución hermética.
