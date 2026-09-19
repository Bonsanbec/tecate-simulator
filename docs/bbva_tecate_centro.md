# Ficha Técnica Arquitectónica: Banco BBVA Tecate Centro (V9.0 Ground-Truth Histórico 2009)

Documento técnico de especificación morfológica, paramétrica, PBR y consenso multi-perspectiva para la reconstrucción fidedigna del edificio comercial/financiero del **Banco BBVA** (esquina Av. Benito Juárez y Calle Presidente Lázaro Cárdenas, Tecate, B.C.) en Blender 5.1 y Godot Engine 4.

---

## 1. Contexto Urbano y Emplazamiento Cartesiano

- **Nombre Oficial**: Edificio Lic. José F. Guajardo / Sucursal BBVA Bancomer Tecate Centro (2009).
- **Emplazamiento Histórico**: Esquina de manzana en la intersección vial de Avenida Benito Juárez (eje poniente-oriente) y Calle Presidente Lázaro Cárdenas (eje norte-sur).
- **Vértice de Esquina (Ochava Guajardo)**: Emplazado exactamente en la intersección de las dos vialidades apuntando hacia el noreste.
- **Coordenadas en Escena Godot (`main.tscn`)**:
  - `Position = Vector3(-66.8, 400.38, -24.81)`
  - `Basis = Transform3D(-1, 0, 0, 0, 1, 0, 0, 0, -1)` (rotación pura de $180.0^\circ$ garantizando paralelismo geométrico estricto con la banqueta de Av. Benito Juárez, sin reducción de sección hacia el poniente).
  - **Calibración de Rasante y Zócalo Subterráneo**: La Calle Lázaro Cárdenas presenta un descenso topográfico de $-0.67\text{ m}$ hacia el norte. El zócalo basal de concreto grafito se extiende en profundidad hasta $Z = -1.20\text{ m}$ bajo cota de apoyo, quedando herméticamente anclado en la rasante vial de Godot sin desniveles flotantes ni inclinaciones aparentes.
  - Nodo raíz: `BBVA_Tecate (StaticBody3D)` con colisionadores analíticos rectificados para V9.0. La banqueta perimetral se excluye deliberadamente del simulador para integrarse de forma limpia con la infraestructura urbana base existente.

---

## 2. Anatomía y Nomenclatura Vial Rectificada

El edificio se compone de los siguientes cuerpos arquitectónicos fidedignamente reconstruidos según la evidencia fotográfica histórica:

1. **Ochava a 45º (Torreón Lic. José F. Guajardo 1956)**:
   - Apunta en diagonal hacia el cruce de Av. Juárez y Calle Cárdenas.
   - **Morfología**: **Trapecio invertido de mosaico veneciano pizarra meteorizada** (`#252B3E`), con base inferior estrecha ($4.60\text{ m}$ a $Z = 3.20\text{ m}$) y base superior ensanchada ($5.80\text{ m}$ a $Z = 9.05\text{ m}$), coronado por albardilla/coping de piedra natural continua a $Z = 9.05\text{ m} - 9.17\text{ m}$.
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

2. **Fachada Sur sobre Avenida Benito Juárez (Eje Poniente-Oriente, sin Cajero)**:
   - Longitud total de $22.80\text{ m}$, 4 crujías modulares.
   - **Ventanales Superiores en Planta Alta**: Formados estrictamente por sus **tres rectángulos inferiores** ($Z \in [5.10, 6.25\text{ m}]$). Se suprimieron las impostas superiores; el paño comprendido entre $Z = 6.25\text{ m}$ y el pretil ($Z = 7.10\text{ m}$) es pared maciza continua de estuco blanco.
   - **Rótulos en Vidrios**: Rótulos comerciales en pintura blanca `CASAS TERRENOS RANCHOS` (Crujía 3) y `JUAN VARGAS R` (Crujía 4) centrados verticalmente a $Z = 5.85\text{ m}$.
   - **Fascia 2009 de Alucobond azul cobalto**: cubre las Crujías 1 a 3 (hasta el machón $X = 17.40\text{ m}$).
   - **Crujía 4 (`JUAN VARGAS R`)**: dintel superior en estuco blanco continuo.
   - **Filetes blancos horizontales**: espaciado calibrado con holgura limpia ($0.27\text{ m}$) respecto al texto `Bancomer`, extendiéndose hasta $X = 17.20\text{ m}$.
   - Mansarda superior continua de tejas coloniales terracota sobre cornisa corrida.

3. **Fachada Oeste sobre Calle Presidente Lázaro Cárdenas (Eje Norte-Sur, con Cajero)**:
   - Longitud continua de $30.00\text{ m}$ con 6 crujías modulares y zaguán de acceso a consultorios ($25.20\text{ m}$ de sección bancaria + $4.80\text{ m}$ de consultorio DENTISTA).
   - Mansarda de tejas continuas con ménsulas/canecillos de concreto en voladizo (corbels).
   - **Crujías 1 a 3**: Sección bancaria con fascia azul cobalto 2009, logotipo `BBVA Bancomer`.
   - **Crujía 3**: Portal de **Cajero Automático** en el lado izquierdo del vano, con caja de luz azul y rojo `RED` + `CAJERO AUTOMATICO`, cancel de vidrio sellado y muro posterior hermético.
   - **Crujías 4 y 5**: Despachos con fascia plateada de Alucobond metálico.
   - **Crujía 6 (DENTISTA - Ground Truth `media_1789778345732`)**:
     - Paño de fachada azul marino sobre el muro con letras 3D de latón dorado `DENTISTA`.
     - Alero/marquesina horizontal en voladizo ($1.15\text{ m}$ de saliente sobre banqueta).
     - Rótulo colgante blanco perpendicular a 90º centrado bajo el alero, con textos legibles en ambas caras.
     - Recibidor/zaguán transitable con escalera interior de 4 peldaños y colisionadores escalonados en Godot.
     - **Esquina Norponiente**: Se suprimió el machón/polígono redundante de mosaico gris para eliminar cualquier tipo de empalme o *Z-fighting* con la barda colindante existente en el simulador.

4. **Fachada Este hacia Estacionamiento (Ground Truth `media_1789781403754`)**:
   - **Longitud modulada en 6 subdivisiones**: $20.80\text{ m}$ continuos (concluye al término de la crujía 6, suprimida la crujía 7).
   - **Crujías 1 a 5**:
     - Planta alta: ventanales de cancelería conformados exclusivamente por los **tres rectángulos inferiores** ($Z \in [5.10, 6.25\text{ m}]$) con dintel continuo de mampostería superior. Rótulo `LICENCIADO EN DERECHO` en Crujía 1.
     - Planta baja: canceles comerciales vidriados con persianas y puerta de servicio peatonal en Crujía 3.
   - **Crujía 6**:
     - Planta alta y planta baja resueltas como **pared lisa** de mampostería blanca continua (sin ventanales).
     - En planta baja cuenta con una **puerta simple de hierro blanco** ($0.95\text{ m} \times 2.10\text{ m}$) con marco metálico, refuerzos tubulares y manija de acero.
   - 5 apliques lumínicos exteriores montados en las pilastras de planta baja.
   - Rampa vehicular descendente con barandal tubular blanco, murete exterior en $X = 27.35\text{ m}$ y letrero ortogonal `ENTRADA BBVA ➔`.

5. **Posterior: Cara Sur en Rasante Cárdenas y Arco Cóncavo Directo (Ground Truth `media_1789784140324`)**:
   - **Cara Sur Lisa a Cota $Y = 30.00\text{ m}$**: Parte directamente desde donde concluye la fachada de Cárdenas ($X = -0.05\text{ m}, Y = 30.00\text{ m}$), extendiéndose de manera continua y lisa a lo largo de $17.40\text{ m}$ (hasta $X = 17.40\text{ m}, Y = 30.00\text{ m}$). Suprime el patio o retranqueo residual previo, sellando íntegramente la parte posterior del ala de consultorios DENTISTA. Cuenta con moldura horizontal intermedia a $Z = 3.20\text{ m}$, albardilla continua a $Z = 7.10 - 7.25\text{ m}$ y pilastra esquinera de remate en $X = 17.40\text{ m}$.
   - **Arco Cóncavo Ampliado (Cierre Único y Directo)**: Suprime por completo la protuberancia de pared plana a $45^\circ$. El muro en arco cóncavo hacia adentro es el **único elemento volumétrico** que cierra la transición entre la Cara Sur ($X = 17.40\text{ m}, Y = 30.00\text{ m}$) y la Cara Estacionamiento ($X = 22.80\text{ m}, Y = 20.80\text{ m}$). Presenta una cuerda de $10.67\text{ m}$ y una sagita cóncava de $1.20\text{ m}$ hacia el interior del inmueble.
   - **Pilar Central Saliente Coronado**: Machón vertical de $0.45\text{ m}$ de anchura en $u = 0.5$, proyectándose $0.42\text{ m}$ hacia afuera del paramento curvo y coronando con capitel a $Z = 7.45 - 7.50\text{ m}$ por encima del pretil.
   - **Dos Ventanas Rectangulares en Planta Alta con Repisas**: Dispuestas simétricamente a ambos lados del machón central ($u = 0.25$ y $u = 0.75$), con repisas salientes de piedra en $Z \in [5.24, 5.38\text{ m}]$, cancelería de aluminio oscuro ($Z \in [5.38, 6.35\text{ m}]$), parteluz central y vidrio reflectante sobre nicho interior oscuro.
   - **Sellado Hermético Total de Azotea**: Losa continua triangulada en abanico que cubre la totalidad de la huella posterior sin ningún hueco interior.

---

## 3. Salidas Generadas y Assets del Proyecto

1. **Archivo Maestro Blender**:
   - `blender_assets/buildings/bbva_tecate_centro.blend`
2. **Asset 3D Optimizado Godot 4**:
   - `godot_project/assets/buildings/bbva_tecate_centro.glb`
3. **Escena Instanciable Godot 4**:
   - `godot_project/assets/buildings/bbva_tecate_centro.tscn` (colisionadores analíticos rectificados para V9.0 con cara Sur en $Y = 30.00\text{ m}$, arco continuo y rampa libre).
4. **Integración en Escena Principal (`main.tscn`)**:
   - `Position = Vector3(-66.8, 400.38, -24.81)`, `Basis = Transform3D(-1, 0, 0, 0, 1, 0, 0, 0, -1)`.
5. **Renders Técnicos de Validación (`docs/images/bbva/`)**:
   - `bbva_guajardo_45.png`
   - `bbva_juarez_frontal.png`
   - `bbva_cardenas_west.png`
   - `bbva_dentista_closeup.png`
   - `bbva_east_parking.png`
   - `bbva_east_ground_truth.png`
   - `bbva_south_inward_arc.png`
   - `bbva_aerial_top.png`
