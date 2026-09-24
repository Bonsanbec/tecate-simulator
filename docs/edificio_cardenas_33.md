# Ficha Técnica Arquitectónica: Complejo Comercial Pdte. Lázaro Cárdenas 33 (Ground-Truth 2009 V5.2)

Documento técnico de especificación morfológica, paramétrica, PBR y consenso multi-perspectiva para la reconstrucción procedural fidedigna del conjunto comercial ubicado en **Calle Presidente Lázaro Cárdenas 33**, esquina con Callejón Libertad, Tecate, B.C., colindante con el edificio BBVA Bancomer Centro (época: **2009**), en Blender 5.1 y Godot Engine 4.

---

## 1. Contexto Urbano y Emplazamiento Cartesiano

- **Ubicación Histórica**: Pdte. Lázaro Cárdenas 33, Primera, 21400 Tecate, B.C., México.
- **Coordenadas Geográficas de Referencia**: Aprox. $32.573057^\circ\text{ N}, -116.627261^\circ\text{ W}$.
- **Relación con el Edificio BBVA**:
  - Comparte la misma manzana y acera comercial sobre Calle Presidente Lázaro Cárdenas.
  - La fachada de Cárdenas 33 está alineada **a la misma distancia de la acera** que la fachada de BBVA Bancomer ($\Delta x_{\text{local}} = 0.00\text{ m}$).
  - Separación de dilatación de $0.30\text{ m}$ respecto del muro norte de los consultorios DENTISTA ($0.10\text{ m}$ libres de su cornisa), eliminando cualquier tipo de penetración o *clipping*.
- **Coordenadas en Escena Godot (`godot_project/main.tscn`)**:
  - `transform = Transform3D(-0.99636, -0.000716, -0.085243, -0.00275, 0.999714, 0.02375, 0.085202, 0.023898, -0.996077, -64.217, 399.280, 5.371)`
  - Mantiene la misma matriz de rotación e inclinación topográfica que BBVA, logrando una unión continua milimétrica sin fisuras ni holguras.
- **Calibración de Rasante y Zócalo Subterráneo**:
  - Todo el perímetro arquitectónico cuenta con un zócalo basal continuo de concreto enterrado a $Z \le -1.20\text{ m}$ que absorbe íntegramente la pendiente de la calle sin mallas flotantes.
- **Prohibición de Banquetas Embebidas**:
  - El asset `.glb` carece intencionalmente de banquetas, guarniciones o aceras, integrándose de forma limpia sobre las capas viales y de banquetas de Tecate Simulator.

---

## 2. Anatomía de Fachadas y Locales Comerciales (Época 2009)

El complejo comercial agrupa cinco comercios principales sobre Calle Presidente Lázaro Cárdenas, una ochava comercial con frontón monumental Art Déco en esquina, la fachada septentrional sobre Callejón Libertad y la fachada posterior hacia el estacionamiento interior del BBVA:

### Fachada Este (Calle Presidente Lázaro Cárdenas)

1. **Crujía 1: Librería España (colindancia BBVA en $Y \in [0.00, 4.80\text{ m}]$)**:
   - Frente comercial prácticamente **100% acristalado**: escaparate continuo con cancelería cuadriculada, estanterías interiores con libros, revistas y póster de la Virgen de Guadalupe.
   - Murete bajo de apoyo ($Z \in [0.15, 0.60\text{ m}]$) en amarillo mostaza brillante (`#E5B239`) con zócalo inferior marrón chocolate (`#502A1F`).
   - Puerta peatonal vidriada con cancelería de aluminio blanco al centro/derecha ($Y \in [0.20, 1.10\text{ m}]$).
   - Fascia horizontal marrón oscura ($Z \in [3.10, 3.45\text{ m}]$) con tipografía dorada: `PRESIDENTE CARDENAS 95-B Z.C. - TECATE, B.C.`.
   - Gran letrero superior blanco enmarcado ($Z \in [3.45, 4.25\text{ m}]$): tipografía con serifa `Librería España` en relieve negro y `• LIBROS • REVISTAS Y PERIODICOS •` en rojo.
   - Azotea limpia y despejada (sin espectaculares de azotea).

2. **Crujía 2: Bar Turístico Diana ($Y \in [4.80, 9.10\text{ m}]$)**:
   - Zócalo de **fachaleta de piedra laja blanca apilada horizontal** de $Z = 0.00$ a $0.85\text{ m}$.
   - Paramento superior en estuco liso color **verde menta pastel suave (`#D2DDD5`)**.
   - Clereestorio horizontal alargado con vidrios oscuros ahumados ($Z \in [2.35, 2.70\text{ m}]$).
   - Puerta doble de acceso al extremo derecho ($Y \in [4.90, 5.90\text{ m}]$) en reja de herrería vertical verde olivo/mostaza.
   - **Letrero comercial de Cerveza Tecate**: caja luminosa blanca con franja y águila roja montada sobre la entrada frente a Bar Diana a $Z = 3.90\text{ m}$.
   - Marquesina corrida continua de concreto en voladizo ($0.70\text{ m}$ sobre la calle) a $Z = 2.80\text{ m}$.
   - Panel rectangular blanco superior adosado sobre marquesina: silueta dorada de la Diana Cazadora a la izquierda, tipografía caligráfica central `Bar TURISTICO Diana / DESDE / SINCE 1957` e ilustración de cóctel/copa y botellas a la derecha.

3. **Crujía 3: Annita's Boutique ($Y \in [9.10, 14.20\text{ m}]$)**:
   - Muro en estuco **ocre claro / mostaza suave continuo (`#D5BA86`)** con zócalo marrón chocolate.
   - Puerta de acceso comercial a la derecha ($Y \in [9.30, 10.35\text{ m}]$) con cancelería y herrería de protección.
   - Gran vitrina de escaparate a la izquierda ($Y \in [10.55, 14.10\text{ m}]$) con **persianas venecianas horizontales de lamas de madera cerradas**.
   - Letrero adosado sobre la marquesina: **caja rectangular grafito oscuro mate (`#22252A`)** con marco plateado y óvalo central con `Annita's Boutique` en cursiva blanca.
   - Azotea limpia sin estructuras publicitarias sobre el techo.

4. **Crujía 4: Party Rentals - Kuroky ($Y \in [14.20, 19.30\text{ m}]$)**:
   - Muro en estuco ocre mostaza continuo con zócalo marrón chocolate.
   - Puerta de acceso comercial a la derecha ($Y \in [14.40, 15.45\text{ m}]$).
   - Gran vitrina con **3 franjas de notas musicales blancas (`♫ ♬ ♪`)** impresas en el cristal ($Y \in [15.60, 18.80\text{ m}]$).
   - Buzones metálicos postales amarillos sobre la acera.
   - Panel rectangular blanco adosado sobre la marquesina: `PARTY RENTALS` en verde bold, logotipo `kuroky` con óvalo magenta, columnas de servicios en azul y lona colorida con fotos de fiestas e inflables a la izquierda.
   - Remate de esquina izquierda: pilastra vertical saliente blanca de concreto con remate oblicuo ascendente hacia Florería Orquídea.

---

### Esquina Cárdenas / Libertad: Florería Orquídea en Ochava a 45º

1. **Geometría Diagonal Analítica**:
   - Chaflán biselado exacto a $45^\circ$ conectando $P_1 = (0.00, 20.50\text{ m})$ sobre Cárdenas con $P_2 = (4.00, 24.50\text{ m})$ sobre Libertad ($L = 5.657\text{ m}$, normal $\vec{n} = (-\sqrt{2}/2, \sqrt{2}/2, 0)$).
2. **Planta Baja de la Ochava**:
   - Zócalo de basamento continuo en **piedra laja café rojiza (`#8C5542`)**.
   - Puerta doble acristalada de cancelería de aluminio blanco con hojas batientes, postes, cabezal, jaladeras tubulares y escaparates laterales con flores visibles por transparencia.
   - Marquesina corrida biselada en voladizo a $Z = 2.80\text{ m}$.
3. **Jerarquía de Capas del Frontón Monumental Art Déco ($H = 6.60\text{ m}$)**:
   - **Marco perimetral blanco en resalte**: pilastras laterales ($0.68\text{ m}$ de ancho) y cornisa superior con bisel saliente. La cara frontal se sitúa en $d = 0.00\text{ m}$.
   - **Paño central rehundido**: situado a $d = -0.12\text{ m}$ (12 cm por detrás del marco blanco), revestido de un sombreador procedural PBR de **mosaico de terrazo verde salvia con piedritas/detallitos blancos** (`M_Mosaico_Terrazo_Verde`).
   - **Caja física del letrero**: montada en resalte sobre el mosaico (espesor de 8 cm, cara frontal en $d = -0.04\text{ m}$), de fondo blanco puro.
   - **Greca perimetral roja**: moldura en relieve de 2 cm sobre la cara del letrero ($d = -0.025\text{ m}$).
   - **Letras 3D en relieve**: tipografía `FLORERIA ORQUIDEA` en burdeos profundo y `Teléfono 654-10-51` en rojo ($d \in [-0.035, -0.005\text{ m}]$).
   - **Cero Z-fighting / Clipping**: todas las superficies poseen desfases analíticos independientes.

---

### Fachada Norte (Callejón Libertad): Foto Estudio Curiel

1. **Cuerpo Arquitectónico**:
   - Estilo *Streamline Moderne* en estuco blanco puro con zócalo marrón ($X \in [4.00, 16.50\text{ m}]$, $Y = 24.50\text{ m}$).
   - Marquesina horizontal en voladizo con 3 estrías metálicas plateadas continuas.
   - **Fin de marquesina**: la marquesina concluye en $X = 14.80\text{ m}$, dejando una holgura limpia de $1.00\text{ m}$ antes del tótem de esquina.
   - Rótulo superior en relieve 3D sobre pretil: `FOTO STUDIO` en azul cobalto y `CURIEL` en dorado metálico.
   - Rótulo pintado en muro inferior: `FOTO STUDIO CURIEL` en rojo cerca de la puerta.
   - Puerta oscura con cancelería y vitrina de exhibición fotográfica.
2. **Tótem Vertical Rojo de Esquina**:
   - Emplazado en el extremo de esquina ($X \in [15.80, 16.30\text{ m}]$).
   - Mástil y cuerpo prismático rojo bermellón continuo de $Z = 1.60$ a $4.40\text{ m}$.
   - **Completamente libre y exento**: cero cortes, intersecciones o solapamientos con la marquesina o alero.
   - Letras blancas en relieve 3D `FOTO` en sus caras norte y sur.
3. **Confinamiento de Cubierta de Azotea**:
   - Losa de azotea confinada a $Y \le 24.15\text{ m}$, imposibilitando cualquier intersección con las letras tridimensionales o el pretil norte.

---

### Fachada Poniente (Reverso hacia Estacionamiento BBVA)

1. **Muro de Servicio Diáfano**:
   - Paramento continuo de estuco blanco de servicio a $X = 16.50\text{ m}$, libre de volúmenes invasivos, jaulas o corrales oscuros.
2. **Rótulos 3D en Pretil Poniente**:
   - Extremo norte: `FOTO STUDIO` en azul y `CURIEL` en dorado sobre la fachada posterior de Foto Curiel ($Y \in [20.00, 23.00\text{ m}]$).
   - Extremo sur: `Bar TURISTICO Diana` en dorado sobre la fachada posterior de Bar Diana ($Y \in [5.50, 8.50\text{ m}]$).
   - Puerta metálica de salida de emergencia de Bar Diana con marco oscuro, marquesina ligera en voladizo ($0.60\text{ m}$) y señalética tridimensional roja `Salida`.

---

## 3. Especificación de Materiales PBR

| Nombre del Material | Color Base / Hex | Roughness | Metallic | Uso en Modelo |
|---|---|---|---|---|
| `M_Estuco_Ocre_Continuo` | Ocre mostaza `#D5BA86` | 0.85 | 0.00 | Muros continuos centrales (Annita / Party) |
| `M_Zocalo_Marron_Chocolate` | Marrón chocolate `#502A1F` | 0.90 | 0.00 | Zócalo inferior continuo |
| `M_Concreto_Marquesina` | Beige claro `#E0DCD4` | 0.70 | 0.00 | Marquesina corrida horizontal |
| `M_Concreto_Blanco_Remates` | Blanco puro `#F5F5F5` | 0.55 | 0.00 | Remates y marco del frontón Orquídea |
| `M_Zocalo_Basal_Enterrado` | Gris oscuro `#282828` | 0.95 | 0.00 | Zócalo subterráneo a $Z \le -1.20\text{ m}$ |
| `M_Fachaleta_Laja_Blanca` | Piedra laja marfil `#EBE6DC` | 0.65 | 0.00 | Zócalo rústico de Bar Diana |
| `M_Verde_Menta_Diana` | Verde menta suave `#D2DDD5` | 0.85 | 0.00 | Paramento frontal de Bar Diana |
| `M_Herreria_Verde_Diana` | Verde olivo oscuro `#333E2B` | 0.45 | 0.60 | Reja de entrada y puerta trasera de servicio |
| `M_Rotulo_Diana_Dorado` | Oro pulido `#D4AF37` | 0.30 | 0.70 | Diana Cazadora y tipografía Bar Diana |
| `M_Logo_Rojo_Tecate` | Rojo Tecate `#D11515` | 0.30 | 0.00 | Logotipo y franja de Cerveza Tecate |
| `M_Lona_Blanca_Tecate` | Blanco luminoso `#F5F5F5` | 0.35 | 0.00 | Caja luminosa de Cerveza Tecate |
| `M_Caja_Grafito_Anita` | Grafito mate `#22252A` | 0.30 | 0.20 | Caja de letrero de Annita's Boutique |
| `M_Persianas_Madera_Anita` | Nogal cálido `#805433` | 0.55 | 0.00 | Persianas venecianas de vitrina Annita |
| `M_Murete_Mostaza_Libreria` | Mostaza brillante `#E5B239` | 0.75 | 0.00 | Murete bajo de apoyo Librería España |
| `M_Fascia_Marron_Libreria` | Marrón oscuro `#3D2319` | 0.50 | 0.00 | Banda de architrabes con dirección |
| `M_Mosaico_Terrazo_Verde` | Salvia con piedritas blancas (Procedural) | 0.60 | 0.00 | Paño rehundido del frontón monumental |
| `M_Laja_Rustica_Cafe` | Laja café rojiza `#8C5542` | 0.95 | 0.00 | Zócalo de basamento Florería Orquídea |
| `M_Greca_Roja_Orquidea` | Rojo carmesí `#CC1414` | 0.30 | 0.00 | Borde greca y señalética Salida |
| `M_Letras_Purpura_Orquidea` | Burdeos oscuro `#590D26` | 0.75 | 0.00 | Tipografía 3D de Florería Orquídea |
| `M_Estuco_Blanco_Curiel` | Blanco yeso `#F5F5F5` | 0.75 | 0.00 | Fachada y reverso de Foto Estudio Curiel |
| `M_Moldura_Streamline_Plata` | Aluminio pulido `#D9DDDE` | 0.30 | 0.60 | Estrías horizontales Streamline Moderne |
| `M_Letras_Azul_Curiel` | Azul cobalto `#1F40A6` | 0.30 | 0.00 | Tipografía FOTO STUDIO en relieve |
| `M_Totem_Rojo_Curiel` | Rojo bermellón `#BA171C` | 0.35 | 0.20 | Tótem vertical esquinero |

---

## 4. Colisiones Físicas Analíticas en Godot 4 (`edificio_cardenas_33.tscn`)

1. `Col_Libreria`: `Vector3(16.5, 4.5, 4.8)` en `(8.25, 2.25, -2.40)`
2. `Col_Diana`: `Vector3(16.5, 4.5, 4.5)` en `(8.25, 2.25, -7.05)`
3. `Col_Anita`: `Vector3(16.5, 4.5, 5.2)` en `(8.25, 2.25, -11.90)`
4. `Col_Party`: `Vector3(16.5, 4.5, 5.5)` en `(8.25, 2.25, -17.25)`
5. `Col_Orquidea_Ochava`: `Vector3(5.7, 6.8, 1.2)` con rotación $45^\circ$ en `Transform3D(0.707107, 0, 0.707107, 0, 1, 0, -0.707107, 0, 0.707107, 2.00, 3.40, -22.50)`
6. `Col_Curiel`: `Vector3(12.5, 4.5, 4.5)` en `(10.25, 2.25, -22.25)`
