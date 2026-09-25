# Ficha Técnica Arquitectónica: Complejo Comercial Av. Benito Juárez 235 (Ground-Truth Histórico 2009 — V4.1 de Producción)

Documento técnico de especificación morfológica, paramétrica, fenestración, PBR, física analítica transitable y verificación visual en circuito cerrado para la reconstrucción procedural fidedigna del conjunto comercial continuo ubicado en **Av. Benito Juárez 235**, delimitado entre **Calle Presidente Lázaro Cárdenas** al Poniente y **Calle Presidente Pascual Ortiz Rubio** al Oriente, Tecate, B.C. (época histórica: **2009**), modelado 100% en mallas procedimentales puras en Blender 5.1 y exportado a Godot Engine 4.

---

## 1. Contexto Urbano y Emplazamiento Cartesiano

- **Denominación Catastral**: Complejo Comercial Juárez 235 (El Baratero a La Michoacana).
- **Ubicación Geográfica de Referencia (WGS84)**: $32.573753^\circ\text{ N}, -116.626557^\circ\text{ W}$.
- **Identificador de Manzana Catastral**: `block_lat_32.57381_lon_-116.62658` (frente de $104.43\text{ m}$ sobre Av. Benito Juárez).
- **Límites Urbanos**:
  - **Frente Sur**: Av. Benito Juárez (acera norte, mirando hacia el Parque Miguel Hidalgo).
  - **Costado Poniente**: Calle Presidente Lázaro Cárdenas (alzado lateral de El Baratero y nave de servicios).
  - **Costado Oriente**: Calle Presidente Pascual Ortiz Rubio (alzado este de La Michoacana, San Diego Beauty Salon y Murillo's Cerrajería).
  - **Fondo Norte**: Callejón Libertad / patios interiores y portón de estacionamiento privado ($Y = 36.00\text{ m}$).
- **Contrato Cartesiano Canónico (Primer Cuadrante Blender)**:
  - $\text{Origen }(0,0,0)$: Esquina exterior suroeste de El Baratero a nivel de rasante ($Z = 0.00\text{ m}$).
  - $\text{Eje }+X$: Vector longitudinal paralelo a Av. Benito Juárez en dirección Oriente ($X \in [0.00, 112.50\text{ m}]$).
  - $\text{Eje }+Y$: Vector transversal hacia el fondo de la manzana en dirección Norte ($Y \in [0.00, 36.00\text{ m}]$).
  - $\text{Eje }+Z$: Cota de elevación vertical ($Z \in [-1.30, 13.50\text{ m}]$).
- **Zócalo Basal Subterráneo Continuo (Protocolo Topográfico)**:
  - Todos los muros de fachada, bardas perimetrales y medianeras descienden subterráneamente a $Z = -2.00\text{ m}$ ($Z \le -1.20\text{ m}$).
  - Absorbe de forma hermética la pendiente natural de la vialidad hacia el cauce del río Tecate (desnivel de $1.27\text{ m}$ entre Cárdenas y Ortiz Rubio) sin provocar mallas flotantes.
- **Prohibición Estricta de Banquetas Embebidas**:
  - El asset binario (`edificio_juarez_235.glb`) carece intencionalmente de banquetas, guarniciones y calzadas públicas. Las banquetas corresponden estrictamente a la capa GIS del simulador (`Roadways` y `Manzanas`).
- **Integración Canónica en Escena Principal Godot (`godot_project/main.tscn`)**:
  - Instancia: `[node name="Edificio_Juarez_235" parent="." instance=ExtResource("21_juarez_235")]`
  - Transformación Canónica:
    `transform = Transform3D(0.844426, 0, 0.097192, 0, 0.85, 0, -0.097192, 0, 0.844426, -50.3735, 400.81, -40.1705)`
  - *Calibración Geométrica y Desescalado Proporcional*:
    - **Orden Canónico de Índices de `Transform3D` en Godot 4**: En archivos `.tscn`, `Transform3D(n0, n1, n2, n3, n4, n5, n6, n7, n8, n9, n10, n11)` se asigna internamente a `basis.x = (n0, n3, n6)`, `basis.y = (n1, n4, n7)`, `basis.z = (n2, n5, n8)`, `origin = (n9, n10, n11)`. Por tanto, para obtener una rotación analítica donde $\text{basis.x} = (S\cos\theta, 0, -S\sin\theta)$, el valor negativo $-S\sin\theta$ debe ubicarse estrictamente en la posición $n6$, mientras que la posición $n2$ ($\text{basis.z.x}$) recibe $+S\sin\theta$. Invertir estas posiciones provoca que $\text{basis.x.z} > 0$, desplazando la fachada hacia el sur (+Z) en lugar de alinearse hacia el norte (-Z).
    - **Desescalado Proporcional Isótropo ($S = 0.8500$)**: Ajusta la longitud nominal de $112.50\text{ m}$ a $95.63\text{ m}$ ($95.91\text{ m}$ con marquesinas), encajando en la longitud útil del frente de manzana ($96.82\text{ m}$ entre Calle Lázaro Cárdenas y Calle Pascual Ortiz Rubio). Elimina por completo la invasión del cruce vial oriente y de la manzana vecina, dejando márgenes libres en ambas bocacalles.
    - **Paralelismo Analítico con la Arista Sur de la Manzana ($\theta = 6.566^\circ$, $\frac{\Delta Z}{\Delta X} = -0.115098$)**: Calibrado contra los vértices reales de la arista sur de la manzana en `manzanas_baked.glb` (desde la esquina poniente $(-50.3735, -40.1705)$ hasta la esquina oriente $(45.8098, -51.2410)$). Con $\text{basis.x.z} = -0.097192 < 0$, la fachada desciende en $Z$ conforme avanza en $X$ a la misma tasa exacta que la calle ($\Delta Z / \Delta X = -0.115098$), manteniendo paralelismo absoluto y cero invasión de vialidad.
    - **Vértice de Esquina Catastral Canónico ($(X_0, Y_0, Z_0) = (-50.3735, 400.81, -40.1705)$)**: El origen del edificio se enrasa milimétricamente en la esquina suroeste de la manzana (`UrbanManzanas`), corrigiendo el error histórico de tomar el eje vial central (asfalto a $Z = -35.95\text{ m}$).
    - **Cota Rasante de Rasante ($Y = 400.81\text{ m}$)**: Enrasa el acceso de El Baratero a ras de banqueta, permitiendo que el zócalo basal enterrado continuo ($Z \le -1.20\text{ m}$) absorba la topografía natural ascendente de la vialidad hacia Ortiz Rubio ($402.03\text{ m}$) sin provocar escalones intransitables ni mallas flotantes.

---

## 2. Estándar de Producción: Mallas Geométricas Puras (100% Meshes)

En cumplimiento estricto con las directrices de calidad y fotorrealismo:
1. **Cero Texturas de Panoramas Pegadas sobre Planos**: Se eliminaron por completo los quads planos con fotografías de Street View que introducían sombras oblicuas, vehículos incrustados y artefactos visuales.
2. **Geometría Paramétrica Volumétrica**:
   - **Cancelería Real**: Marcos de aluminio extruidos, zócalos de $18\text{ cm}$, montantes dobles, travesaños horizontales y parteluces.
   - **Tiradores Tubulares 3D**: Manijas de acero inoxidable de $1.20\text{ m}$ con herrajes a $90^\circ$ en puertas peatonales.
   - **Tejas Coloniales de Barro 3D**: Canales y cobijas cilíndricas curvas apiladas con solape y reborde físico.
   - **Dovelas de Ladrillo en Relieve**: Rosca radial extruida en resalte de $6\text{ cm}$ con intradós de mampostería.
   - **Celosías de Herrería 3D**: Retícula de barrotes cruzados de sección cuadrada ($2.5\text{ cm}$) con relieve de sombras reales.
   - **Cortinas Metálicas Acanaladas**: Lamas horizontales extruidas con sombras de plegado mecánico.
   - **Cerchas Espaciales Trianguladas (*Space Frame Trusses*)**: Estructura de tubos de acero galvanizado para el espectacular monumental con pasarela de servicio y barandal.
   - **Rótulos Corpóreos 3D**: Letras y logotipos extruidos con curvas FONT de Blender orientadas con precisión anti-espejo en cada fachada cardinal.

---

## 3. Anatomía y Fenestración de los Inmuebles (Ground-Truth 2009)

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

### Despiece Arquitectónico Detallado

1. **El Baratero & Sede Municipal del PRI ($X \in [0.00, 26.50\text{ m}]$, $Y \in [0.00, 36.00\text{ m}]$)**:
   - **Planta Baja ($Z \in [0.00, 3.45\text{ m}]$)**: Escaparates continuos en aluminio azul con zócalo de $18\text{ cm}$, montantes cada $3.31\text{ m}$, puertas dobles con tiradores tubulares de acero inoxidable de $1.20\text{ m}$, fascia magenta en resalte de $45\text{ cm}$ con molduras y rótulo 3D: `EL BARATERO` (blanco) y `ROPA • CALZADO • ACCESORIOS` (dorado). Cartelera de esquina en bandera sobre mástil tubular.
   - **Planta Alta ($Z \in [3.45, 7.20\text{ m}]$)**: Muro cortina de oficinas con montantes verticales y franja horizontal verde institucional del PRI con letras 3D: `PARTIDO REVOLUCIONARIO INSTITUCIONAL` y `COMITE DIRECTIVO MUNICIPAL • TECATE`.
   - **Nivel 3 / Frontispicio ($Z \in [7.20, 11.50\text{ m}]$)**: Muro ciego blanco con cuatro pilastras en resalte y números corpóreos dorados `1`, `2`, `3`, `4`.
   - **Alzado Poniente (Calle Presidente Lázaro Cárdenas)**: Testero blanco del PRI con rótulo corpóreo 3D `PRI` de $0.95\text{ m}$ y `SEDE MUNICIPAL TECATE`. Nave verde oliva de $20.00\text{ m}$ con retícula de pilastras y trabes fucsias salientes, dos portones dobles de carga rojos con marcos angulares de acero y cerrojos.

2. **Restaurant D'Arce ($X \in [26.50, 37.00\text{ m}]$, $Y \in [0.00, 14.50\text{ m}]$)**:
   - Fachada en estuco rústico terracota con zócalo basal.
   - Marquesina volada corrida con 7 canes de vigas de madera oscura escuadrada y tejado inclinado con hiladas de tejas coloniales curvas 3D.
   - Caja de letrero blanca con marco azul y letras 3D: `D'ARCE` (azul) y `RESTAURANT • BAR` (dorado), sostenida con varillas tensoras metálicas.
   - Dos ventanales con marcos negros y parteluces, puerta doble acristalada central y 2 faroles coloniales de forja negra.

3. **Local Blanco ($X \in [37.00, 41.50\text{ m}]$, $Y \in [0.00, 12.00\text{ m}]$)**:
   - Muro en estuco blanco pulido con pretil a $Z = 4.05\text{ m}$.
   - Cortina metálica enrollable de acero galvanizado con lamas acanaladas horizontales en relieve y marco superior para anuncio comercial.

4. **Dulcería La Fuente ($X \in [41.50, 49.50\text{ m}]$, $Y \in [0.00, 14.00\text{ m}]$)**:
   - Casita tradicional con porche a dos aguas sobre viguería de madera oscura, con tejas coloniales de barro escurriendo a ambos lados y caballete de cumbrera semicilíndrico superior.
   - Cancel de acceso bajo el porche con reja de hierro verde limón, ventana colonial derecha con alféizar moldurado y cuarterones de madera blanca.
   - Rótulos corpóreos 3D: `DULCERIA` (azul) y `"La Fuente"` (rojo).

5. **Bar Rodeo / Karaoke ($X \in [49.50, 63.00\text{ m}]$, $Y \in [0.00, 16.00\text{ m}]$)**:
   - Muro blanco con zócalo basal en verde menta pálido de $1.45\text{ m}$ con moldura de pecho de paloma.
   - Dos grandes ventanales con celosías de herrería negra 3D compuestas de barrotes verticales y horizontales de sección cuadrada ($2.5\text{ cm}$) con cruces decorativas.
   - Rótulos corpóreos 3D en frontis: `RODEO BAR` (estilo vaquero) y `KARAOKE & DANCE` (blanco).
   - Rótulos corpóreos 3D en testero hacia el callejón: `ESTACIONAMIENTO PUBLICO` y `KARAOKE • BILLAR • BAR`.

6. **Callejón de Estacionamiento ($X \in [63.00, 69.50\text{ m}]$, $Y \in [0.00, 36.00\text{ m}]$)**:
   - Paso peatonal y vehicular diáfano libre de colisiones ($6.50\text{ m}$ de luz libre) con firme de concreto oscuro y bardas laterales de block con albardillas.
   - Portón corredizo norte de reja negra con rótulo corpóreo 3D: `PARKING $15 PESOS` en verde fluorescente orientado hacia el sur para los usuarios del callejón.

7. **Restaurante Hing Kang ($X \in [69.50, 82.50\text{ m}]$, $Y \in [0.00, 15.00\text{ m}]$)**:
   - Zócalo rojo bermellón de $1.20\text{ m}$, puerta en arco de medio punto enmarcado en moldura roja.
   - Dos toldos abombados de cuarto de cilindro en lona roja Coca-Cola con faldón festoneado blanco y rótulos 3D `Coca-Cola`.
   - Fascia horizontal de caja negra con marco de aluminio y letras corpóreas 3D adelantadas: `RESTAURANTE COMIDA CHINA` (dorado) y `HING KANG` (rojo).
   - Tótems de azotea con cerchas metálicas para `Cerveza TECATE` y `PARKING`.

8. **Distribuidor SKY ($X \in [82.50, 89.00\text{ m}]$, $Y \in [0.00, 12.00\text{ m}]$)**:
   - Marquesina abovedada curva en lona azul cobalto con rótulos 3D: `SKY` (blanco) y `DISTRIBUIDOR AUTORIZADO`.
   - Escaparate inferior de aluminio blanco con vidrio reflectante y zócalo rojo bermellón.

9. **Local del Arco Tradicional ($X \in [89.00, 97.00\text{ m}]$, $Y \in [0.00, 12.00\text{ m}]$)**:
   - Cinco canes de madera oscura escuadrada salientes $0.60\text{ m}$ del pretil.
   - Gran arco rebajado monumental con dovelas de ladrillo decimonónico en resalte de $6\text{ cm}$ con mapeo PBR continuo.
   - Mostrador tradicional interior y cancelería de madera con cuarterones de vidrio.

10. **Local Joyería ($X \in [97.00, 102.00\text{ m}]$, $Y \in [0.00, 11.00\text{ m}]$)**:
    - Toldo festoneado curvo azul con rótulos corpóreos 3D: `JOYERIA` (dorado) y `ANILLOS DE GRADUACION` (blanco), con escaparate de aluminio blanco y cristal.

11. **La Michoacana y Alzado Ortiz Rubio ($X \in [102.00, 112.50\text{ m}]$, $Y \in [0.00, 22.00\text{ m}]$)**:
    - Mostrador en escuadra con azulejo verde esmeralda, encimera de acero inoxidable y tapas cilíndricas para botes de nieve.
    - Columnas cuadradas amarillas con capiteles escalonados.
    - Fascia curva rosa mexicano envolvente con rótulos corpóreos 3D: `LA MICHOACANA` (amarillo) y `PALETERIA Y NEVERIA` (blanco).
    - **Cartelera Espectacular Monumental de Azotea ($13.50\text{ m}$ de altura)**:
      - Estructura portante de cerchas espaciales tridimensionales de tubos de acero galvanizado con pasarela de servicio y barandal.
      - Cara Sur: Anuncio publicitario con letras corpóreas 3D doradas y blancas: `GRUPO SIESA`, `SEGURIDAD PRIVADA • CCTV • GUARDIAS` y `TEL. 654-20-00`.
      - Cara Norte / Este: Anuncio con letras 3D: `CAEM`, `CENTRO DE ARTES Y ESTUDIOS MUSICALES` y `CANTO • GUITARRA • PIANO • BATERIA`.
    - Alzado Ortiz Rubio:
      - **San Diego Beauty Salon ($Y \in [7.50, 13.50\text{ m}]$)**: Fachada de estuco salmón, letrero blanco con letras 3D fucsias `SAN DIEGO` y `BEAUTY SALON • ESTETICA UNISEX`, escaparate acristalado de aluminio blanco.
      - **Murillo's Cerrajería ($Y \in [13.50, 22.00\text{ m}]$)**: Fachada de estuco azul, letrero amarillo y blanco con `CERRAJERIA MURILLO` y `LLAVES CON CHIP • APERTURAS • DUPLICADOS`, portón metálico de taller.

12. **Equipamiento de Azotea e Instalaciones Técnicas**:
    - Condensadores de aire acondicionado tipo paquete y minisplit con carcasas metálicas, rejillas y soportes angulares de perfilería.
    - Baterías de tinacos cilíndricos negros rotomoldeados.
    - Bajantes pluviales verticales galvanizados.

---

## 4. Jerarquía de Colisiones Analíticas (Godot 4)

La escena [`godot_project/assets/buildings/edificio_juarez_235.tscn`](file:///Users/hakkindavid/Documents/GitHub/tecate-simulator/godot_project/assets/buildings/edificio_juarez_235.tscn) implementa física modular descompuesta basada en primitivas convexas simples (`BoxShape3D`), cumpliendo con la sincronización canónica $Z_{\text{godot}} = -Y_{\text{blender}}$:

1. **Prevención Estricta de Paredes Invisibles**:
   - El callejón central ($X \in [63.00, 69.50\text{ m}]$) posee **CERO colisionadores frontales**, permitiendo el tránsito peatonal y vehicular diáfano hacia el patio norte.
2. **Descomposición Modular por Inmueble**:
   - Cada cuerpo comercial cuenta con su propio colisionador `BoxShape3D` ajustado milimétricamente al perímetro edificado.
3. **Bardas Perimetrales Norte**:
   - `Col_Barda_Norte_1` y `Col_Barda_Norte_2` confinan el patio posterior a $Y_{\text{blender}} = 36.00\text{ m}$ ($Z_{\text{godot}} = -36.00\text{ m}$).

---

## 5. Batería de Validación Closed-Loop (Suite de 8 Renders Diurnos)

| ID de Cámara | Perspectiva / Encuadre | Propósito Técnico de Validación |
| :--- | :--- | :--- |
| `Cam_01_Frontal_Baratero_45` | Frontal Poniente Av. Juárez ($X: 0 - 27$) | Validación de PB El Baratero, PA PRI y frontispicio de $11.50\text{ m}$ con números corpóreos $1, 2, 3, 4$. |
| `Cam_02_Frontal_Centro_Oeste` | Frontal Av. Juárez ($X: 26.5 - 50$) | Detalle de marquesina D'Arce con tejas 3D, cortina acanalada del Local Blanco y porche a dos aguas de La Fuente. |
| `Cam_03_Callejon_Estacionamiento` | Perspectiva Callejón Central ($X: 63 - 70$) | Verificación de paso diáfano transitable y legibilidad directa del rótulo `PARKING $15 PESOS` en el fondo norte. |
| `Cam_04_Frontal_Centro_Este` | Frontal Av. Juárez ($X: 70 - 102$) | Validación de fascia Hing Kang, toldos Coca-Cola, marquesina azul SKY y dovelas de ladrillo del Arco Tradicional. |
| `Cam_05_Frontal_Michoacana_45` | Esquina Sureste Juárez y Ortiz Rubio | Validación de La Michoacana, mostrador con copas de nieve y Cartelera Monumental de azotea de `GRUPO SIESA`. |
| `Cam_06_Lateral_Cardenas_Oeste` | Alzado Lateral Poniente ($Y: 0 - 36$) | Validación de la nave verde oliva, retícula de pilastras fucsias, portones rojos y rótulo corpóreo `PRI`. |
| `Cam_07_Lateral_OrtizRubio_Este` | Alzado Lateral Oriente ($Y: 0 - 22$) | Legibilidad tipográfica de San Diego Beauty Salon y Murillo's Cerrajería sobre calle Ortiz Rubio. |
| `Cam_08_Cenital_Azoteas_Z60` | Vista Cenital Completa ($Z = 70\text{ m}$) | Certificación de azoteas herméticas, losas continuas, condensadores HVAC y baterías de tinacos. |

Todas las imágenes se encuentran generadas en alta resolución en el directorio [`docs/images/juarez_235/`](file:///Users/hakkindavid/Documents/GitHub/tecate-simulator/docs/images/juarez_235/).
