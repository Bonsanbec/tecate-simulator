# Ficha Técnica Arquitectónica: Complejo Comercial Pdte. Lázaro Cárdenas 33 (Ground-Truth 2009 V4.1)

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

El complejo comercial agrupa cinco comercios principales sobre Calle Presidente Lázaro Cárdenas, una ochava comercial con frontón monumental Art Déco en esquina, la fachada septentrional sobre Callejón Libertad y la fachada posterior hacia el estacionamiento interior del BBVA:

### Fachada Este (Calle Presidente Lázaro Cárdenas)

1. **Crujía 1: Librería España (colindancia BBVA en $Y \in [0.00, 4.80\text{ m}]$)**:
   - Frente comercial prácticamente **100% acristalado**: escaparate continuo repleto de estanterías interiores con libros, revistas, periódicos y póster de la Virgen de Guadalupe.
   - Murete bajo de apoyo ($Z \in [0.15, 0.60\text{ m}]$) en amarillo mostaza brillante (`#E5B239`) con zócalo inferior marrón chocolate (`#502A1F`).
   - Puerta peatonal vidriada con cancelería de aluminio blanco al centro/derecha ($Y \in [0.20, 1.10\text{ m}]$).
   - Fascia horizontal marrón oscura ($Z \in [3.10, 3.45\text{ m}]$) con tipografía dorada: `PRESIDENTE CARDENAS 95-B Z.C. - TECATE, B.C.`.
   - Gran letrero superior blanco enmarcado ($Z \in [3.45, 4.25\text{ m}]$): tipografía con serifa `Librería España` en relieve negro y `• LIBROS • REVISTAS Y PERIODICOS •` en rojo.
   - En la azotea (sobre la medianera con Bar Diana): estructura metálica con el espectacular publicitario triangular de Cerveza `TECATE / Bar Diana 1957 / Cocktails`.

2. **Crujía 2: Bar Turístico Diana ($Y \in [4.80, 9.10\text{ m}]$)**:
   - Zócalo de **fachaleta de piedra laja blanca apilada horizontal** de $Z = 0.00$ a $0.85\text{ m}$.
   - Paramento superior en estuco liso color **verde menta pastel suave (`#D2DDD5`)**.
   - Clereestorio horizontal alargado con vidrios oscuros ahumados ($Z \in [2.35, 2.70\text{ m}]$).
   - Puerta doble de acceso al extremo derecho ($Y \in [4.90, 5.90\text{ m}]$) en reja de herrería vertical verde olivo/mostaza.
   - Marquesina corrida continua de concreto en voladizo ($0.70\text{ m}$ sobre la calle) a $Z = 2.80\text{ m}$.
   - Panel rectangular blanco superior adosado sobre marquesina: silueta dorada de la Diana Cazadora a la izquierda, tipografía caligráfica central `Bar TURISTICO Diana / DESDE / SINCE 1957` e ilustración de cóctel/copa y botellas a la derecha.

3. **Crujía 3: Annita's Boutique ($Y \in [9.10, 14.20\text{ m}]$)**:
   - Muro en estuco **ocre claro / mostaza suave continuo (`#D5BA86`)** con zócalo marrón chocolate.
   - Puerta de acceso comercial a la derecha ($Y \in [9.30, 10.35\text{ m}]$) con cancelería y herrería de protección.
   - Gran vitrina de escaparate a la izquierda ($Y \in [10.55, 14.10\text{ m}]$) con **persianas venecianas horizontales de lamas de madera cerradas**.
   - Letrero adosado sobre la marquesina: **caja rectangular grafito oscuro mate (`#22252A`)** con marco plateado y óvalo central con `Annita's Boutique` en cursiva blanca.
   - En azotea: gran espectacular vertical monumental `RENTA` en rojo sobre blanco, `MESAS SILLAS` en blanco sobre azul marino y teléfonos.

4. **Crujía 4: Party Rentals - Kuroky ($Y \in [14.20, 19.30\text{ m}]$)**:
   - Muro en estuco ocre mostaza continuo con zócalo marrón chocolate.
   - Puerta de acceso comercial a la derecha ($Y \in [14.40, 15.45\text{ m}]$).
   - Gran vitrina con **3 franjas de notas musicales blancas (`♫ ♬ ♪`)** impresas en el cristal ($Y \in [15.60, 18.80\text{ m}]$).
   - Buzones metálicos postales amarillos sobre la acera.
   - Panel rectangular blanco adosado sobre la marquesina: `PARTY RENTALS` en verde bold, logotipo `kuroky` con óvalo magenta, columnas de servicios en azul y lona colorida con fotos de fiestas e inflables a la izquierda.
   - Remate de esquina izquierda: **pilastra / aleta vertical saliente blanca** de concreto con remate oblicuo ascendente hacia Florería Orquídea.

5. **Crujía 5: Florería Orquídea ($Y \in [19.30, 24.50\text{ m}]$)**:
   - Zócalo de basamento continuo en **piedra laja café rojiza (`#8C5542`) con juntas pronunciadas**.
   - Escaparates de cristal en esquina con arreglos florales, coronas y follaje visible en el interior.
   - Puerta de aluminio blanco.

---

### Fachada Norte (Callejón Libertad)

1. **Frontón Monumental de Florería Orquídea**:
   - Orientado hacia Callejón Libertad / Parque Hidalgo ($H = 6.20\text{ m}$).
   - Marco perimetral grueso de concreto blanco con bisel ensanchado hacia afuera.
   - Paño central empotrado revestido de **mosaico veneciano / terrazo de piedritas verde salvia y blanco moteado (`#8EA78C`)**.
   - Gran letrero rectangular blanco con **greca perimetral de cuadritos rojos**: `FLORERIA ORQUIDEA` en púrpura oscuro y leyenda `Teléfono 654-10-51`.
   - Puerta doble acristalada de cancelería de aluminio blanco y zócalo de laja café rojiza.
2. **Foto Estudio Curiel**:
   - Estilo *Streamline Moderne* en estuco blanco puro con zócalo marrón.
   - Marquesina horizontal en voladizo con **3 estrías / molduras metálicas continuas**.
   - Rótulo superior en relieve 3D sobre pretil: `FOTO STUDIO` en azul cobalto y `CURIEL` en dorado/marrón.
   - Rótulo pintado en muro inferior: `FOTO STUDIO CURIEL` en rojo.
   - Puerta oscura con reja de protección a la izquierda y vitrina de exhibición fotográfica.
   - **Tótem publicitario vertical en esquina**: caja prismática roja bermellón con letras blancas `FOTO` visibles desde la calle.

---

### Fachada Poniente (Reverso hacia Estacionamiento BBVA)

1. Posterior de Foto Estudio Curiel en estuco blanco de servicio.
2. Marquesina angulada de Bar Diana, puerta metálica con señalética `Salida` y rótulo de azotea `BAR TURISTICO Diana`.
3. Terraza técnica de servicio cercada con reja metálica negra de barrotes tubulares analíticos.

---

## 3. Especificación de Materiales PBR

| Nombre del Material | Color Base / Hex | Roughness | Metallic | Uso en Modelo |
|---|---|---|---|---|
| `M_Estuco_Ocre_Continuo` | Ocre mostaza `#D5BA86` | 0.85 | 0.00 | Muros continuos centrales |
| `M_Zocalo_Marron_Chocolate` | Marrón vino `#502A1F` | 0.90 | 0.00 | Zócalo inferior continuo |
| `M_Concreto_Marquesina` | Beige claro `#E0DCD4` | 0.70 | 0.00 | Marquesina corrida horizontal |
| `M_Fachaleta_Laja_Blanca` | Piedra blanca `#EBE4D5` | 0.65 | 0.00 | Zócalo Bar Diana |
| `M_Verde_Menta_Diana` | Verde menta `#D2DDD5` | 0.85 | 0.00 | Muro superior Bar Diana |
| `M_Herreria_Verde_Diana` | Verde olivo `#68724D` | 0.45 | 0.60 | Puerta de reja Bar Diana |
| `M_Caja_Grafito_Anita` | Grafito mate `#22252A` | 0.30 | 0.20 | Caja de letrero Annita's |
| `M_Persianas_Madera_Anita` | Madera `#805433` | 0.55 | 0.00 | Lamas de vitrina Annita's |
| `M_Espectacular_Azul_Renta` | Azul marino `#0D2C54` | 0.35 | 0.00 | Espectacular azotea Renta |
| `M_Mosaico_Terrazo_Verde` | Verde salvia `#8EA78C` | 0.30 | 0.00 | Frontón Florería Orquídea |
| `M_Laja_Rustica_Cafe` | Café rojizo `#8C5542` | 0.95 | 0.00 | Zócalo Florería Orquídea |
| `M_Estuco_Blanco_Curiel` | Blanco puro `#F5F5F5` | 0.75 | 0.00 | Fachada Foto Curiel |
| `M_Totem_Rojo_Curiel` | Rojo bermellón `#BA181B` | 0.35 | 0.20 | Tótem vertical Curiel |
| `M_Murete_Mostaza_Libreria` | Mostaza brillante `#E5B239` | 0.75 | 0.00 | Murete Librería España |
| `M_Vidrio_Comercial_Limpio` | Azul humo translúcido | 0.08 | 0.00 | Canceles y vitrinas |

---

## 4. Colisiones Analíticas Transitables (Godot 4)

7 volúmenes `BoxShape3D` independientes calibrados por local comercial en `godot_project/assets/buildings/edificio_cardenas_33.tscn`:
- `Col_Libreria`: $16.50\times 4.50\times 4.80\text{ m}$ en $(8.25, 2.25, -2.40\text{ m})$.
- `Col_Diana`: $16.50\times 4.50\times 4.30\text{ m}$ en $(8.25, 2.25, -6.95\text{ m})$.
- `Col_Anita`: $16.50\times 4.50\times 5.10\text{ m}$ en $(8.25, 2.25, -11.65\text{ m})$.
- `Col_Party`: $16.50\times 4.50\times 5.10\text{ m}$ en $(8.25, 2.25, -16.75\text{ m})$.
- `Col_Orquidea`: $9.20\times 6.50\times 5.20\text{ m}$ en $(4.60, 3.25, -21.90\text{ m})$.
- `Col_Curiel`: $7.30\times 4.50\times 6.50\text{ m}$ en $(12.85, 2.25, -21.25\text{ m})$.
- `Col_Terraza_Reja`: $4.30\times 2.00\times 7.00\text{ m}$ en $(18.65, 1.00, -10.50\text{ m})$.

---

## 5. Renders de Validación Canónicos V4

Galería disponible en `docs/images/cardenas_33/`:
1. `Cam_Cardenas_Frontal_V4.png`: Perspectiva frontal completa idéntica a `media_1790243320877.png`.
2. `Cam_Orquidea_Libertad_V4.png`: Encuadre del frontón monumental idéntico a `media_1790243423150.jpg`.
3. `Cam_Curiel_Libertad_V4.png`: Perspectiva de Foto Estudio Curiel idéntica a `DcOz2fF61YH1bc6cN7zlrA_yaw_354.12.png`.
4. `Cam_Diana_Closeup_V4.png`: Detalle de fachaleta de laja blanca, puerta verde de reja y rótulo de Diana Cazadora.
5. `Cam_Libreria_Espana_V4.png`: Detalle del frente acristalado de revistas/libros y espectacular Tecate de azotea.
6. `Cam_Reverso_Estacionamiento_V4.png`: Vista posterior desde el estacionamiento interior del BBVA.
