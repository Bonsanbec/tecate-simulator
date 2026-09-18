# Ficha Técnica Arquitectónica: Banco BBVA Tecate Centro (V5.0 Ground-Truth Histórico 2009)

Documento técnico de especificación morfológica, paramétrica, PBR y consensus multi-perspectiva para la reconstrucción fidedigna del edificio comercial/financiero del **Banco BBVA** (esquina Av. Benito Juárez y Calle Presidente Lázaro Cárdenas, Tecate, B.C.) en Blender 5.1 y Godot Engine 4.

---

## 1. Contexto Urbano y Emplazamiento Cartesiano

- **Nombre Oficial**: Edificio Lic. José F. Guajardo / Sucursal BBVA Bancomer Tecate Centro (2009).
- **Emplazamiento Histórico**: Esquina noreste de la intersección entre Avenida Benito Juárez (arteria principal este-oeste) y Calle Presidente Lázaro Cárdenas (eje norte-sur hacia el monumento y parque).
- **Dirección Catastral**: Calle Presidente Lázaro Cárdenas esq. Av. Benito Juárez, Col. Centro / Primera, C.P. 21400, Tecate, B.C.
- **Coordenadas GPS**: `32.5734618°N, -116.6274318°W`.
- **Coordenadas Locales (Tecate Simulator)**: `X = -84.03 m, Y = 25.92 m` (a **87.94 m** radiales del origen en el Kiosko del Parque Miguel Hidalgo).
- **Transformada en Escena Godot (`main.tscn`)**:
  - `Position = Vector3(-84.03, 400.0, -25.92)`
  - Nodo raíz: `BBVA_Tecate (StaticBody3D)` con colisionadores analíticos `BoxShape3D`.

---

## 2. Anatomía de Consenso Multi-Perspectiva y Ground Truth Histórico 2009

El modelo 3D fue reconstruido integrando el consenso fotográfico de todas las caras de la manzana y fotografías históricas aportadas por el usuario:

1. **Torreón Guajardo en Ochava a 45º (Ground Truth: `media_1789774890984.png`)**:
   - Geometría: **Trapecio de piedra volcánica / mosaico veneciano desgastado** (`#252B3E`), sin molduras de plástico blanco perimetrales, coronado por un remate/coping de piedra natural.
   - Inscripción en bronce en 3 líneas exactas:
     ```
     EDIFICIO
     LIC. JOSE F. GUAJARDO
     1956
     ```
     *(Año confirmado como **1956**, no 1954)*.
   - En la base del chaflán se ubica el acceso principal al banco con cancelería de aluminio y puertas dobles de cristal templado.
   - Espectacular de Azotea 2009:
     - Poste tubular estructural central de acero.
     - Panel superior (60%): Azul cobalto (`#00288E`) con recuadro blanco corporativo conteniendo `BBVA` en azul, y `Bancomer` en blanco debajo.
     - Panel inferior (40%): Fondo blanco con logotipo rojo `RED` (con estrella de red interbancaria) a la izquierda y texto verde en 2 líneas `CAJERO AUTOMATICO` a la derecha.

2. **Fachada Oeste (Calle Presidente Lázaro Cárdenas - Ground Truth: `media_1789774670397.png`)**:
   - **Edificio continuo de 2 niveles** hasta el consultorio dental (`DENTISTA`) con una longitud total de **$27.20\text{ m}$**.
   - Mansarda corrida de tejas con canecillos/ménsulas de concreto en voladizo (corbels) a lo largo de toda la fachada.
   - Fascia 2009: Azul cobalto Alucobond para el banco que transiciona limpiamente a panel plateado con rótulo `DENTISTA` en la crujía norte.
   - Crujía 3: Portal exterior de **Cajero Automático** con cajetín luminoso azul `CAJERO AUTOMATICO` y puerta de cristal.
   - Vidrios de planta alta con rotulación comercial histórica en vinil blanco:
     - `DESPACHO JURIDICO QUEZADA Y ASOCIADOS Tel. 52-22`
     - `DESPACHO CONTABLE FISCAL LOCAL Nº 4 LIC. RAMON QUEZADA LOPEZ ABOGADO`

3. **Fachada Sur (Avenida Benito Juárez - Ground Truth: `media_1789774756138.png`)**:
   - Longitud: $18.60\text{ m}$ (de $X = 4.20$ a $22.80\text{ m}$).
   - 4 crujías modulares + machón macizo en la esquina este.
   - Vidrios en planta alta con rotulaciones: `CASAS TERRENOS RANCHOS` y `JUAN VARGAS R`.
   - Fascia 2009: Azul cobalto con filetes blancos y logotipo corporativo `BBVA Bancomer`, rematando antes del machón este.

4. **Fachada Este y Rampa de Estacionamiento (Ground Truth: `media_1789774721368.jpg`)**:
   - 5 vanos de cancelería de aluminio con cristales en planta alta (`LICENCIADO EN DERECHO`).
   - Planta baja con ventanales comerciales y puerta peatonal con luminaria exterior.
   - Caseta de vigilancia blanca desplazada a $X = 27.60\text{ m}$.
   - Letrero azul `ENTRADA BBVA ➔` orientado ortogonalmente (mirando hacia el sur) para guiar el flujo vehicular de Av. Juárez.

5. **Desacoplamiento de Banqueta Urbana**:
   - La banqueta perimetral con cordón rojo se exporta como asset modular independiente (`banqueta_bbva_tecate.glb`), garantizando que el edificio (`bbva_tecate_centro.glb`) descanse a cota limpia $Z = 0.0\text{ m}$.

---

## 3. Despiece y Dimensiones Técnicas por Niveles

```
+12.65 m  ▲  Cúspide de Caja de Luz Espectacular en Azotea
          │  [Panel Azul BBVA Bancomer: 3.60 x 1.65 m]
+11.00 m  ┼  División de Panel
          │  [Panel Blanco RED / CAJERO AUTOMATICO: 3.60 x 1.15 m]
+9.85 m   ┼  Base de Caja de Luz
          │  [Poste central tubular de acero: H = 0.85 m]
+9.00 m   ┼  Pretil Superior del Torreón Guajardo (Ochava 45º)
          │  [Remate rocoso natural oscuro (coping)]
+8.15 m   ┼  Cumbrera de Faldones de Tejas (Alas Juárez y Cárdenas)
          │  [Teja curva colonial de barro: pendiente 25°, H = 0.70 m]
+7.45 m   ┼  Cornisa Moldurada Corrida Blanca (Vuelo 0.40 m)
          │  [Canecillos/ménsulas de concreto bajo alero continuo a lo largo de Cárdenas]
+7.10 m   ┼  Dintel de Ventanales Planta Alta (Vanos de H = 1.65 m)
+4.30 m   ┼  Remate de Fascia Alucobond Azul Corporativo 2009 (H = 1.10 m)
+3.20 m   ┼  Viga Dintel / Cancelería Planta Baja (Vanos de H = 2.80 m)
+0.40 m   ┼  Plinto Basal / Zócalo de Concreto Gris Grafito
 0.00 m   ▼  Nivel Cero de Apoyo Estructural (Edificio limpio sobre Z = 0.0)
```

---

## 4. Salidas Generadas y Assets del Proyecto

1. **Archivo Maestro Blender**:
   - `blender_assets/buildings/bbva_tecate_centro.blend`
2. **Asset 3D Optimizado Godot 4 (Edificio sin banqueta)**:
   - `godot_project/assets/buildings/bbva_tecate_centro.glb`
3. **Asset 3D Modular de Banqueta Urbana**:
   - `godot_project/assets/buildings/banqueta_bbva_tecate.glb`
4. **Escena Instanciable Godot 4**:
   - `godot_project/assets/buildings/bbva_tecate_centro.tscn` (con colisionadores analíticos `StaticBody3D`).
5. **Vistas de Validación en Bucle Cerrado**:
   - `docs/images/bbva/bbva_guajardo_45.png`: Chaflán a 45º, año 1956, trapecio rocoso y espectacular 2009.
   - `docs/images/bbva/bbva_cardenas_west.png`: Fachada continua a Dentista (27.20m), canecillos, cajero y despachos.
   - `docs/images/bbva/bbva_juarez_frontal.png`: 4 crujías de Av. Juárez, despachos y fascia 2009.
   - `docs/images/bbva/bbva_east_parking.png`: Ventanales este, puerta peatonal, rampa, caseta y letrero ortogonal.
   - `docs/images/bbva/bbva_aerial_top.png`: Planta de azotea sellada y delimitación del bloque.
