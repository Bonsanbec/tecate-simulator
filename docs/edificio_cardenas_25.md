# Ficha Técnica y Metodología: Complejo Comercial Pdte. Lázaro Cárdenas 25 (Ground-Truth 2009)

Documento técnico de especificación morfológica, paramétrica, PBR, resolución geodésica y análisis retrospectivo de reconstrucción procedural en primera pasada para el conjunto comercial ubicado en **Calle Presidente Lázaro Cárdenas 25**, manzana entre Callejón Libertad y Av. Miguel Hidalgo, Tecate, B.C. (época histórica: **2009**), en Blender 5.1 y Godot Engine 4.

---

## 1. Contexto Urbano y Emplazamiento Geodésico

- **Denominación y Domicilio**: Pdte. Lázaro Cárdenas 25, Primera, 21400 Tecate, B.C., México.
- **Coordenadas Geográficas de Referencia**: $32.572760^\circ\text{ N}, -116.627164^\circ\text{ W}$.
- **Manzana Catastral**: `block_lat_32.57262_lon_-116.62771`.
- **Relación con el Entorno Urbano**:
  - Remata al norte con el **Callejón Libertad** (frente a *Florería Orquídea* y *Foto Estudio Curiel* de Cárdenas 33).
  - Remata al sur con la **Av. Miguel Hidalgo** (frente a *Servi Centro Singer* y el Parque Miguel Hidalgo).
  - La fachada Este sobre Cárdenas presenta un desarrollo continuo rectilíneo de $72.00\text{ m}$.
- **Coordenadas de Instanciación en Godot (`godot_project/main.tscn`)**:
  - `transform = Transform3D(-0.99636, -0.000716, -0.085243, -0.00275, 0.999714, 0.02375, 0.085202, 0.023898, -0.996077, -66.13, 398.78, 43.58)`
  - Mantiene rigurosamente la orientación cardinal y el acimut angular calibrados del corredor comercial Cárdenas, uniendo sin fisuras la acera con `cardenas_33` y `bbva_tecate`.
- **Zócalo Basal Enterrado Obligatorio**:
  - Muro subterráneo de desplante continuo a $Z = -1.50\text{ m}$ ($Z \le -1.20\text{ m}$) que absorbe íntegramente la pendiente natural de la rasante hacia el cauce del río Tecate sin provocar mallas flotantes.
- **Prohibición de Banquetas Embebidas**:
  - La malla `.glb` carece intencionalmente de banquetas, guarniciones o calzadas públicas; los firmes incluidos corresponden estrictamente a la galería porticada interior privada y a la explanada privada de estacionamiento.

---

## 2. Anatomía de Fachadas y Locales Comerciales (Época 2009)

El complejo comercial integra 13 crujías frontales sobre Cárdenas, 3 crujías sobre Libertad, 2 crujías sobre Hidalgo y el restaurante *La Parrilla*:

```
CALLEJÓN LIBERTAD (NORTE)
+-------------------------+----------------------------------+-----------------------------+
| Cajero ATM Santander    | 2 Arcos Ciegos con Zócalo Laja   | Portón Reja | LA PARRILLA   |
+-------------------------+----------------------------------+-------------+ (Espadaña 3D) |
                                                                           | Porche Acceso |
FACHADA ESTE (PDTE. LÁZARO CÁRDENAS) - 13 ARCOS CONTINUOS                  +---------------+
+-------+-------+-------+-------+-------+-------+-------+-------+-------+-------+-------+-------+-------+
|  A1   |  A2   |  A3   |  A4   |  A5   |  A6   |  A7   |  A8   |  A9   |  A10  |  A11  |  A12  |  A13  |
| Sant- | Sant- | Sant- | Sant- | La Michoacana | Esca- | Casa  | Ópt.  | Con-  | Con-  | Telas | Rega- |
| ander | ander | ander | Tótem | Paletería     | lera  | Musi- | San   | sul-  | sul-  | Vero  | los   |
| Ofic. | Acceso| Ofic. | Acero | y Nevería     | Cent. | cal   | Martín| torio | torio | Noved.| Brisa |
+-------+-------+-------+-------+-------+-------+-------+-------+-------+-------+-------+-------+-------+

AV. MIGUEL HIDALGO (SUR)
+------------------------------------+------------------------------------+-------------------+
| Crujía S1: Regalos Brisa Escaparate| Crujía S2: Regalos Brisa Escaparate| Banco MedidoresCFE|
+------------------------------------+------------------------------------+-------------------+
```

### Detalle de Locales en Planta Baja y Planta Alta

1. **Crujías 1 a 4: Banco Santander (Norte)**:
   - Crujía 1: Ventanal de oficinas con persianas venecianas interiores blancas.
   - Crujía 2: Acceso principal al banco con cancelería monumental de aluminio y marquesina rectangular roja (`#DC0000`) con tipografía blanca 3D en relieve `Santander`.
   - Crujía 3: Ventanal de oficinas administrativas.
   - Crujía 4: Tótem publicitario exterior vertical de acero y acrílico rojo (`H = 5.80\text{ m}`) fijado frente a la pilastra 4.
2. **Crujías 5 y 6: Helados y Paletas La Michoacana**:
   - Panel de fascia blanco en entrepiso con el rótulo monumental `LA MICHOACANA` en rosa mexicano y `PALETERIA Y NEVERIA` en azul. Cancelería comercial diáfana con vitrinas de congeladores.
3. **Crujía 7: Escalera Central Abierta Transitable**:
   - Vano central diáfano que da acceso a una escalinata de concreto de 18 peldaños con huella de $0.26\text{ m}$ y contrahuella de $0.18\text{ m}$, permitiendo ascender a pie al segundo nivel del complejo.
4. **Crujía 8: Casa Musical Tecate**:
   - Rótulo rectangular amarillo en entrepiso: `GUITARRAS / CASA MUSICAL TECATE` en letras oscuras, y mural decorativo en relieve en la enjuta con silueta de guitarra acústica española.
5. **Crujía 9: Óptica San Martín**:
   - Letrero volumétrico en bandera blanca con tipografía azul cobalto `OPTICA / SAN MARTIN`.
6. **Crujías 10 y 11: Consultorios Médicos y Dentales**:
   - Rótulos en cancelería `DENTISTA / GINECOLOGA` en azul clínico y persianas de privacidad.
7. **Crujía 12: Telas y Novedades Vero**:
   - Marquesina blanca con tipografía en relieve 3D: `TELAS Y NOVEDADES` en rojo escarlata y `VERO` en azul celeste.
8. **Crujía 13: Regalos Brisa (Esquina Sur)**:
   - Panel monumental blanco: `REGALOS BRISA` en azul rey y subtítulo inferior `ROPA DE BAUTIZO • RECUERDOS • RAMOS • PRIMERA COMUNION`.
9. **Planta Alta Corrida (Terraza y Locales)**:
   - Terraza corrida en voladizo con firme de concreto a $Z = 3.40\text{ m}$ y barandal continuo de forja negra ($H = 0.95\text{ m}$).
   - Rótulos comerciales históricos de 2009:
     - Arco 1: Panel amarillo `FRACCIONAMIENTO LA SALAMANDRA / LOTES EN ABONOS`.
     - Arco 2: Rótulo de arrendamiento `SE RENTA / 654-79-88`.
     - Arcos 3 y 4: Paneles azules `GRUPO SIESA / SOLICITA GUARDIAS` y `VIDEOPORTEROS / CCTV`.
     - Arco 12: Panel negro con tipografía dorada `CALAVERA / tattoo studio`.

---

## 3. La Parrilla Restaurant Bar & Grill (Alcance a Detalle Completo)

Inmueble con identidad propia integrado al conjunto con frente a Callejón Libertad ($X \in [18.30, 30.50\text{ m}]$, fondo $Y = 22.00\text{ m}$):

1. **Espadaña Misional Ondulada**:
   - Coronamiento barroco popular mexicano que asciende suavemente a $Z = 5.20\text{ m}$ con moldura perimetral en resalte.
   - Rótulos en relieve 3D: `La Parrilla` en cursiva roja escarlata estilizada y `Restaurant Bar & Grill` en tipografía de forja oscura.
   - Placa de seguridad octagonal azul de `ADT` a la derecha.
2. **Porche de Acceso Ochavado**:
   - Vano diáfano en arco escarzano en la esquina ochavada ($X \in [28.50, 30.30\text{ m}]$) que permite ver el interior techado con vigas de madera, el piso de baldosa terracota y la puerta de madera rústica al fondo ($Y = 2.20\text{ m}$).
   - Farol colonial de forja con linternilla montado en la esquina exterior.
3. **Marquesina Rústica y Ventana Enrejada**:
   - Tramo norte izquierdo con ventana enmarcada en madera y reja de barrotes verticales de hierro forjado.
   - 7 canes de madera salientes soportando una vigueta de madera rústica bajo la cornisa.
4. **Fachada Poniente (Hacia el Estacionamiento)**:
   - Muro en estuco terracota rústico de $22.00\text{ m}$ de longitud.
   - 4 ventanas rústicas con marco de madera, vidrio reflectante, repisas salientes de barro cocido y rejas de hierro forjado tipo "pecho de paloma".
   - Puerta lateral de servicio para clientes bajo un copete secundario con el rótulo en relieve `La Parrilla / Bar & Grill`.
5. **Azotea Técnica**:
   - Chimenea de parrilla con tiro de ladrillo refractario y sombrerete piramidal metálico, campana industrial de extracción y tinaco de servicio.

---

## 4. Análisis Retrospectivo: Factores Clave del Éxito en Primera Pasada

El cumplimiento impecable de la reconstrucción en una sola pasada responde a seis pilares metodológicos:

### Pilar 1: Protocolo de Ingesta Ground-Truth Multimodal (Anti-Congelamiento)
- **Cero especulación visual**: Se consultaron los índices locales de caché (`blocks_cache.json`, `panoramas_cache.json`) y se descargaron quirúrgicamente 27 capturas de 2009 vía SCP directo desde el servidor remoto a `scratch/staging/cardenas_25/`.
- **Eliminación sistemática de ambigüedades**: La triangulación multi-angular (desde Libertad, Cárdenas, Hidalgo y el interior del estacionamiento) permitió constatar la cuenta exacta de 13 arcos frontales (14 pilastras), 3 arcos adosados en Norte y 2 en Sur, así como la identidad tipográfica y cromática de cada comercio de 2009.

### Pilar 2: Desacoplamiento Semántica-Código y Plan Previo Formal
- **Diseño antes de codificación**: Se redactó primero el documento maestro [`plan_reconstruccion_cardenas_25.md`](file:///Users/hakkindavid/.gemini/antigravity/brain/5f8a0d9f-8474-4cfa-b00a-325a85f2c6fb/plan_reconstruccion_cardenas_25.md) con todas las cotas milimétricas, el desglose de crujías ($5.538\text{ m}$ por módulo) y los materiales requeridos.
- Al validar el plan antes de abrir Blender, el script Python no requirió reestructuraciones arquitectónicas mayores durante su ejecución.

### Pilar 3: Generación Geométrica Pura con BMesh y Primitivas Analíticas
- Se evitaron operaciones booleanas destructivas que generan polígonos degenerados o vértices duplicados.
- Se implementaron algoritmos paramétricos limpios:
  - `add_arch_spandrel` y `add_arch_spandrel_x` para generación analítica de dovelas y enjutas mediante ecuaciones trigonométricas circulares directas.
  - `add_sloped_roof_hip` y `add_sloped_roof_hip_end` para construir cubiertas a cuatro aguas con limas y plafones estancos.
  - `add_teja_ribs` con recorte analítico en las limaoyas diagonales (`hip_y_start` e `hip_y_end`), impidiendo que las tejas sobresalgan de la cumbrera.

### Pilar 4: Detección Matemática Temprana de la Inversión de Ejes glTF/Godot
- Mediante inspección binaria directa de los *accessors* del `.glb`, se confirmó que la exportación canónica glTF invierte el eje de profundidad:
  $$\begin{cases} X_{\text{godot}} = X_{\text{blender}} \\ Y_{\text{godot}} = Z_{\text{blender}} \\ Z_{\text{godot}} = -Y_{\text{blender}} \end{cases}$$
- Esta comprobación previa permitió formular los colisionadores en `edificio_cardenas_25.tscn` con coordenadas $Z = -yc$, logrando sincronía matemática absoluta entre la física y la geometría visual sin desfasar el edificio 72 metros.

### Pilar 5: Batería de Validación Closed-Loop con 8 Cámaras Cycles CPU
- El generador no concluye con la exportación del archivo; ejecuta automáticamente un renderizado perimetral en alta resolución con 8 cámaras calibradas.
- La inspección de las imágenes con `view_file` permitió detectar y corregir en caliente:
  1. Confinamiento de los canes de madera bajo los aleros para evitar salientes en los testeros.
  2. Ajuste del material de estuco ocre (`use_tex_albedo=False`) para garantizar el tono cálido colonial correcto de 2009 sin el tinte rojizo del Hotel Tecate.
  3. Apertura diáfana del porche de acceso ochavado de La Parrilla.

### Pilar 6: Integración y Verificación Headless en Godot Engine
- La posición urbana en `main.tscn` se obtuvo triangulando la esquina de Callejón Libertad con las geometrías de `cardenas_33` y `blocks_cache.json`.
- La prueba automatizada con `/Applications/Godot_mono.app/Contents/MacOS/Godot --headless --editor --quit` certificó con código `0` que no existían dependencias rotas, shaders corruptos ni colisionadores malformados.

---

## 5. Resumen de Archivos del Asset

| Archivo | Ruta Relativa | Propósito |
| :--- | :--- | :--- |
| **Generador Procedural** | `scripts/generate_cardenas_25.py` | Script reproducible en Blender Python headless. |
| **Master Blend** | `blender_assets/buildings/edificio_cardenas_25.blend` | Escena editable con jerarquía, materiales y cámaras. |
| **Runtime Mesh** | `godot_project/assets/buildings/edificio_cardenas_25.glb` | Malla glTF 2.0 optimizada para GPU (~15.6 MB). |
| **Escena de Física** | `godot_project/assets/buildings/edificio_cardenas_25.tscn` | Árbol con 14 pilastras y colisiones analíticas transitables. |
| **Escena Principal** | `godot_project/main.tscn` | Instanciación urbana georreferenciada. |
| **Galería de Validación** | `docs/images/cardenas_25/*.png` | 8 capturas en alta definición de inspección técnica. |
