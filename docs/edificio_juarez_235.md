# Ficha Técnica Arquitectónica: Complejo Comercial Av. Benito Juárez 235 (Ground-Truth Histórico 2009 — V2.0 de Producción)

Documento técnico de especificación morfológica, paramétrica, fenestración, PBR, resolución geodésica y verificación visual en circuito cerrado para la reconstrucción fidedigna del conjunto continuo ubicado en **Av. Benito Juárez 235**, delimitado entre **Calle Presidente Lázaro Cárdenas** al Poniente y **Calle Presidente Pascual Ortiz Rubio** al Oriente, Tecate, B.C. (época histórica: **2009**), modelado proceduralmente en Blender 5.1 y exportado a Godot Engine 4.

---

## 1. Contexto Urbano y Emplazamiento Cartesiano

- **Denominación Catastral**: Complejo Comercial Juárez 235 (El Baratero a La Michoacana).
- **Ubicación Geográfica de Referencia (WGS84)**: $32.573753^\circ\text{ N}, -116.626557^\circ\text{ W}$.
- **Identificador de Manzana Catastral**: `block_lat_32.57381_lon_-116.62658` (frente de $104.43\text{ m}$ sobre Av. Benito Juárez).
- **Límites Urbanos**:
  - **Frente Sur**: Av. Benito Juárez (acera norte, mirando hacia el Parque Miguel Hidalgo).
  - **Costado Poniente**: Calle Presidente Lázaro Cárdenas (alzado lateral de El Baratero y nave de servicios).
  - **Costado Oriente**: Calle Presidente Pascual Ortiz Rubio (alzado este de La Michoacana, San Diego Beauty Salon y Murillo's Cerrajería).
  - **Fondo Norte**: Callejón Libertad / patios interiores y portón de estacionamiento privado.
- **Contrato Cartesiano Canónico (Primer Cuadrante Blender)**:
  - $\text{Origen }(0,0,0)$: Esquina exterior suroeste de El Baratero a nivel de rasante ($Z = 0.00\text{ m}$).
  - $\text{Eje }+X$: Vector longitudinal paralelo a Av. Benito Juárez en dirección Oriente ($X \in [0.00, 112.50\text{ m}]$).
  - $\text{Eje }+Y$: Vector transversal hacia el fondo de la manzana en dirección Norte ($Y \in [0.00, 36.00\text{ m}]$).
  - $\text{Eje }+Z$: Cota de elevación vertical ($Z \in [-1.30, 13.50\text{ m}]$).
- **Zócalo Basal Subterráneo Continuo (Protocolo Topográfico)**:
  - Todos los muros de fachada, bardas perimetrales y medianeras descienden subterráneamente a $Z = -1.30\text{ m}$ ($Z \le -1.20\text{ m}$).
  - Absorbe de forma hermética la pendiente natural de la vialidad hacia el cauce del río Tecate sin provocar mallas flotantes.
- **Prohibición Estricta de Banquetas Embebidas**:
  - El asset binario (`edificio_juarez_235.glb`) carece intencionalmente de banquetas, guarniciones y calzadas públicas. Las banquetas corresponden estrictamente a la capa GIS del simulador (`Roadways` y `Manzanas`).
- **Integración en Escena Principal Godot (`godot_project/main.tscn`)**:
  - Instancia: `[node name="Edificio_Juarez_235" parent="." instance=ExtResource("21_juarez_235")]`
  - Transformación:
    `transform = Transform3D(0.99636, 0, 0.08524, 0, 1, 0, -0.08524, 0, 0.99636, -53.85, 398.79, 35.95)`
  - Orientación y alineación geodésica calibradas milimétricamente con el polígono catastral, enlazando la acera de Av. Juárez con `Edificio_Cardenas_33`, `Edificio_Cardenas_25` y `Palacio_Municipal`.

---

## 2. Anatomía, Fenestración y Crujías de los 10 Inmuebles (Ground-Truth 2009)

```
NORTE (CALLEJÓN LIBERTAD / PATIO INTERIOR)
+---------------------------------------------------------------------------------------------------------------+
| Nave Baratero / PRI  | Patio Central y Bardas Perimetrales | Portón Estacionamiento | Reverso Locales / Azotea|
+----------------------+-------------------------------------+------------------------+-------------------------+
                                                             |   CALLEJÓN ACCESO $15  |
FACHADA SUR (AVENIDA BENITO JUÁREZ) - DESPIECE CONTINUO DE PONIENTE A ORIENTE         |
+---------------------+-------------+-------+-----------+------------+-------+--------+-----+-----+------+------+
|    EL BARATERO /    | RESTAURANT  | LOCAL | DULCERÍA  |  KARAOKE   | PASO  | REST.  | SKY |ARCO | JOY. | LA   |
|      SEDE PRI       |   D'ARCE    |BLANCO | LA FUENTE |   RODEO    | LIBRE |  HING  |     |     |      |MICHO-|
|     (3 NIVELES)     | (TEJAS 3D)  |CORTINA| FRONTÓN   |  CELOSÍAS  | CALLE-|  KANG  |     |LADR.|TOLDO |ACANA |
|   X: [0.0, 26.5]    |X:[26.5,37.0]|37-41.5|X:41.5-49.5|X:49.5-63.0 | 63-69.5|69.5-82.5|82-89|89-97|97-102|102-112|
+---------------------+-------------+-------+-----------+------------+-------+--------+-----+-----+------+------+
```

### Detalle Específico por Inmueble

1. **El Baratero & Sede Municipal del PRI ($X \in [0.00, 26.50\text{ m}]$, $Y \in [0.00, 36.00\text{ m}]$)**:
   - **Planta Baja ($Z \in [0.00, 3.40\text{ m}]$)**: Muro cortina comercial con carpintería metálica azul cielo (`#3A75C4`), escaparates continuos y fascia horizontal púrpura/magenta (`#BD6BB6`) con rótulo 3D: `EL BARATERO - ROPA • CALZADO • ACCESORIOS`.
   - **Planta Alta ($Z \in [3.40, 7.20\text{ m}]$)**: Oficinas del Partido Revolucionario Institucional con cristalera corrida, montantes verticales azules y franja de remate verde institucional (`#43A047`) con rótulo: `Partido Revolucionario Institucional`.
   - **Tercer Nivel / Frontispicio ($Z \in [7.20, 11.50\text{ m}]$)**: Muro macizo blanco con cuatro marcas verticales de alineación numeradas (`1`, `2`, `3`, `4`) registradas en los panoramas históricos.
   - **Alzado Poniente (Calle Presidente Lázaro Cárdenas)**: Nave industrial verde oliva (`#88A399`) de $20.00\text{ m}$ de desarrollo ($Y \in [16.00, 36.00\text{ m}]$), estructurada con retícula de 5 pilastras y 2 trabes exteriores magenta, dos portones dobles de carga rojos (`#B74B4B`) y rótulo volumétrico `PRI` en el testero sur.
   - **Anuncio de Esquina**: Cartel espectacular sobre poste metálico en la intersección de Cárdenas y Juárez con el logotipo de `EL BARATERO`.

2. **Restaurant D'Arce ($X \in [26.50, 37.00\text{ m}]$)**:
   - Fachada en estuco rústico terracota (`#C06B47`).
   - Marquesina voladiza con canes de madera oscura y tejas coloniales curvas 3D en terracota cocida, rematada por un panel de fascia azul rey con tipografía blanca tridimensional: `D'ARCE RESTAURANT`.
   - Tres amplios ventanales enmarcados y cancelería de acceso central.

3. **Local Comercial Blanco ($X \in [37.00, 41.50\text{ m}]$)**:
   - Módulo comercial con estuco blanco, pretil lineal a $Z = 3.80\text{ m}$ y cortina metálica de acero corrugado gris claro para cierre de seguridad.

4. **Dulcería La Fuente ($X \in [41.50, 49.50\text{ m}]$)**:
   - Fachada tradicional con frontón triangular a dos aguas y molduras decorativas en azul cielo (`#6FA8DC`).
   - Marquesina superior en bermellón oscuro con letrero en doble renglón: `DULCERIA` y `"La Fuente"`.
   - Ventana con cancelería colonial de cuarterones y zócalo inferior contrastante.

5. **Karaoke & Dance / Rodeo Bar ($X \in [49.50, 63.00\text{ m}]$)**:
   - Zócalo horizontal en verde menta pálido (`#A8D5BA`) que asciende a $Z = 1.30\text{ m}$.
   - Dos ventanales monumentales protegidos por celosías de herrería metálica oscura con entrecalles cuadradas.
   - Testero oriente orientado hacia el callejón con rótulo de mural publicitario pintado a mano.

6. **Callejón Central de Estacionamiento ($X \in [63.00, 69.50\text{ m}]$)**:
   - Paso diáfano libre de $6.50\text{ m}$ de ancho con firme de concreto oscuro.
   - Portón corredizo de herrería negra al fondo del predio ($Y = 36.00\text{ m}$) coronado por marquesina con el anuncio luminoso en tipografía verde neón: `PARKING $15`.
   - Bardas perimetrales laterales de protección de $2.50\text{ m}$ de elevación.

7. **Restaurante Hing Kang ($X \in [69.50, 82.50\text{ m}]$)**:
   - Zócalo bermellón rojizo (`#D15353`) en planta baja.
   - Dos toldos abombados de cuarto de cilindro en lona roja brillante con faldón y ribete blanco, portando la rotulación publicitaria lateral `Coca-Cola`.
   - Gran fascia horizontal en negro carbón (`#262626`) con tipografía tridimensional en dos renglones: `HING KANG` (blanco) y `RESTAURANTE COMIDA CHINA` (rojo).
   - Tótem publicitario rectangular de azotea sobre doble soporte tubular de acero.

8. **Distribuidor Autorizado SKY ($X \in [82.50, 89.00\text{ m}]$)**:
   - Fachada con marquesina corrida en azul ultramar corporativo (`#70A4D4`) y rótulo 3D: `SKY DISTRIBUIDOR AUTORIZADO`.
   - Cortina metálica de seguridad enrollable y cancelería de cristal.

9. **Local Comercial Tradicional del Arco ($X \in [89.00, 97.00\text{ m}]$)**:
   - Arco rebajado con intradós y rosca de ladrillo cocido con dovelas aparentes.
   - Cinco canes de viguería de madera rústica voladiza sobresaliendo del pretil superior.
   - Amplio vano acristalado bajo la rosca del arco.

10. **Local Joyería y Accesorios ($X \in [97.00, 102.00\text{ m}]$)**:
    - Marquesina con toldo de tela festoneado a rayas y rotulación: `ANILLOS DE GRADUACION`.
    - Cortina de acero enrollable.

11. **Helados y Paletas La Michoacana & Locales Ortiz Rubio ($X \in [102.00, 112.50\text{ m}]$, $Y \in [0.00, 22.00\text{ m}]$)**:
    - Esquina abierta con pilares de concreto amarillo crema (`#F9E79F`), mostrador continuo y zócalo verde claro (`#A2D9CE`).
    - Fascia perimetral envolvente en crema y amarillo con letrero tridimensional: `LA MICHOACANA` (rosa mexicano) y `PALETERIA Y NEVERIA` (azul).
    - **Cartelera Espectacular Monumental de Azotea**:
      - Estructura de celosía metálica tubular y perfiles estructurales de acero que eleva un panel publicitario de $12.00\text{ m} \times 4.80\text{ m}$ hasta $Z = 13.50\text{ m}$.
      - Rótulo tridimensional de época: `CAEM • GRUPO SIESA`.
    - **Alzado Este (Calle Presidente Pascual Ortiz Rubio)**:
      - Crujía intermedia: `San Diego Beauty Salon` en volumen rosa pálido con marco volado y escaparate vidriado.
      - Crujía norte: `MURILLO'S CERRAJERIA` en fachada azul con portón metálico.

---

## 3. Colisiones Analíticas Godot 4 (`BoxShape3D`)

El archivo [`godot_project/assets/buildings/edificio_juarez_235.tscn`](file:///Users/hakkindavid/Documents/GitHub/tecate-simulator/godot_project/assets/buildings/edificio_juarez_235.tscn) implementa una jerarquía analítica rigurosamente sincronizada bajo la regla canónica $Z_{\text{godot}} = -Y_{\text{blender}}$:

| Colisionador ID | Dimensiones BoxShape3D ($L_x, L_y, L_z$) | Centro Godot ($X, Y, Z$) | Función y Cobertura Arquitectónica |
| :--- | :--- | :--- | :--- |
| `Col_Baratero_Frontal` | $26.50 \times 7.50 \times 16.00\text{ m}$ | $(13.25, 3.75, -8.00)$ | Cuerpo comercial frontal de El Baratero y oficinas PRI. |
| `Col_Baratero_Nave` | $26.50 \times 9.40 \times 20.00\text{ m}$ | $(13.25, 4.70, -26.00)$ | Nave posterior de servicios y portones sobre Cárdenas. |
| `Col_Darce` | $10.50 \times 4.30 \times 14.50\text{ m}$ | $(31.75, 2.15, -7.25)$ | Estructura de Restaurant D'Arce con marquesina. |
| `Col_Local_Blanco` | $4.50 \times 3.80 \times 12.00\text{ m}$ | $(39.25, 1.90, -6.00)$ | Módulo comercial blanco adyacente. |
| `Col_La_Fuente` | $8.00 \times 4.30 \times 14.00\text{ m}$ | $(45.50, 2.15, -7.00)$ | Dulcería La Fuente y frontón triangular. |
| `Col_Rodeo_Bar` | $13.50 \times 4.65 \times 16.00\text{ m}$ | $(56.25, 2.32, -8.00)$ | Bar Karaoke y testero oeste del callejón. |
| **Vano $X \in [63.00, 69.50]$** | **CERO COLISIONADORES** | **PASO DIÁFANO** | **Acceso vehicular y peatonal diáfano sin paredes invisibles.** |
| `Col_Hing_Kang` | $13.00 \times 4.65 \times 15.00\text{ m}$ | $(76.00, 2.32, -7.50)$ | Restaurante Hing Kang y testero este del callejón. |
| `Col_SKY` | $6.50 \times 4.10 \times 12.00\text{ m}$ | $(85.75, 2.05, -6.00)$ | Distribuidor SKY y marquesina azul. |
| `Col_Arco_Tradicional` | $8.00 \times 4.20 \times 12.00\text{ m}$ | $(93.00, 2.10, -6.00)$ | Local con arco rebajado de ladrillo. |
| `Col_Joyeria` | $5.00 \times 3.90 \times 11.00\text{ m}$ | $(99.50, 1.95, -5.50)$ | Local de joyería y toldo festoneado. |
| `Col_Michoacana` | $10.50 \times 4.30 \times 7.50\text{ m}$ | $(107.25, 2.15, -3.75)$ | Esquina comercial de La Michoacana en Juárez. |
| `Col_Beauty_Salon` | $8.50 \times 3.90 \times 6.00\text{ m}$ | $(108.25, 1.95, -10.50)$ | Local San Diego Beauty Salon en Ortiz Rubio. |
| `Col_Cerrajeria` | $8.50 \times 3.60 \times 8.50\text{ m}$ | $(108.25, 1.80, -17.75)$ | Local Murillo's Cerrajería en Ortiz Rubio. |
| `Col_Barda_Norte_1` | $37.00 \times 2.50 \times 0.40\text{ m}$ | $(45.00, 1.25, -36.00)$ | Barda perimetral norte sección poniente. |
| `Col_Barda_Norte_2` | $33.00 \times 2.50 \times 0.40\text{ m}$ | $(85.50, 1.25, -36.00)$ | Barda perimetral norte sección oriente. |

---

## 4. Galería de Verificación Visual (Suite de Renders V2.0)

La suite de 8 cámaras técnicas diurnas (Cycles CPU con domo de iluminación suave para evitar penumbras duras) se preserva en [`docs/images/juarez_235/`](file:///Users/hakkindavid/Documents/GitHub/tecate-simulator/docs/images/juarez_235/):

1. **`Cam_01_Frontal_Baratero_45.png`**:
   - Perspectiva a $45^\circ$ del cuerpo mayor de El Baratero y sede del PRI.
   - Certifica los ventanales de planta baja, las fascias tridimensionales, el letrero espectacular de esquina y el frontispicio de $11.50\text{ m}$ con marcas numeradas.
2. **`Cam_02_Frontal_Centro_Oeste.png`**:
   - Alzado frontal de Restaurant D'Arce, Local Blanco y Dulcería La Fuente.
   - Demuestra la volumetría de tejas coloniales curvas 3D con canes de madera, frontón triangular a dos aguas y cortinas enrollables.
3. **`Cam_03_Callejon_Estacionamiento.png`**:
   - Vista directa peatonal hacia el callejón de estacionamiento.
   - Certifica la orientación corregida del rótulo `PARKING $15` en el portón de fondo, el mural del Karaoke a la izquierda, el toldo curvo de Hing Kang a la derecha y la ausencia absoluta de paredes invisibles.
4. **`Cam_04_Frontal_Centro_Este.png`**:
   - Alzado frontal de Restaurante Hing Kang, Distribuidor SKY y Local del Arco.
   - Destacan los dos toldos abombados de cuarto de cilindro en lona roja Coca-Cola, el letrero de azotea en doble mástil y el arco de ladrillo con dovelas.
5. **`Cam_05_Frontal_Michoacana_45.png`**:
   - Perspectiva a $45^\circ$ de la esquina de La Michoacana y el alzado de Ortiz Rubio.
   - Evidencia la erradicación total de sombras negras gracias al domo de cielo suave, la monumental cartelera `CAEM • GRUPO SIESA` sobre celosía metálica y los mostradores amarillos.
6. **`Cam_06_Lateral_Cardenas_Oeste.png`**:
   - Alzado ortogonal completo sobre Calle Presidente Lázaro Cárdenas.
   - Valida la retícula de pilastras y trabes magenta sobresalientes, el muro verde oliva y los dos portones de servicio rojos.
7. **`Cam_07_Lateral_OrtizRubio_Este.png`**:
   - Alzado este completo sobre Calle Presidente Pascual Ortiz Rubio.
   - Muestra con nitidez absoluta los locales San Diego Beauty Salon y Murillo's Cerrajería, así como el reverso de la estructura del espectacular.
8. **`Cam_08_Cenital_Azoteas_Z60.png`**:
   - Planta cenital de azoteas a $Z = 60\text{ m}$.
   - Comprueba la correspondencia milimétrica de las profundidades de lote, el canal diáfano del callejón y el cerramiento de pretiles.

---

## 5. Certificación de Reglas del Proyecto (`GEMINI.md`)

- [x] **Consulta previa de documentación**: Lectura rigurosa de `docs/metodologia_reconstruccion_edificios.md` y `docs/APRENDIZAJES_Y_PLANTILLA_ASSETS_ARQUITECTONICOS.md`.
- [x] **Protocolo SCP anti-congelamiento**: Cero escaneos sobre `/Volumes/tecate-backup/`; descarga directa vía `scp` de 45 panoramas históricos de 2009.
- [x] **Prohibición de banquetas embebidas**: Ningún elemento de banqueta ni asfalto incluido en el archivo `.glb`.
- [x] **Zócalo basal subterráneo obligatorio**: Todos los muros perimetrales descienden herméticamente a $Z = -1.30\text{ m}$ ($Z \le -1.20\text{ m}$).
- [x] **Colisiones analíticas sin paredes invisibles**: Jerarquía descompuesta `BoxShape3D` con paso diáfano en callejón de estacionamiento ($X \in [63.00, 69.50]$) y escalones $\le 0.18\text{ m}$.
- [x] **Desacoplamiento semántica-código y plan previo**: Plan de despiece aprobado y validado en `implementation_plan.md`.
- [x] **Acentuación ortográfica estricta**: Revisión gramatical exhaustiva de acentos en toda la documentación y reportes.
- [x] **Sincronización canónica glTF/Godot**: Aplicación estricta de $Z_{\text{godot}} = -Y_{\text{blender}}$ certificada en colisionadores y bounding box binario.
