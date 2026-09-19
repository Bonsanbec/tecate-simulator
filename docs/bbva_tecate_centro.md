# Ficha Técnica Arquitectónica: Banco BBVA Tecate Centro (V5.1 Ground-Truth Histórico 2009)

Documento técnico de especificación morfológica, paramétrica, PBR y consensus multi-perspectiva para la reconstrucción fidedigna del edificio comercial/financiero del **Banco BBVA** (esquina Av. Benito Juárez y Calle Presidente Lázaro Cárdenas, Tecate, B.C.) en Blender 5.1 y Godot Engine 4.

---

## 1. Contexto Urbano y Emplazamiento Cartesiano

- **Nombre Oficial**: Edificio Lic. José F. Guajardo / Sucursal BBVA Bancomer Tecate Centro (2009).
- **Emplazamiento Histórico**: Esquina de manzana en la intersección vial de Avenida Benito Juárez (eje poniente-oriente) y Calle Presidente Lázaro Cárdenas (eje norte-sur).
- **Vértice de Esquina (Ochava Guajardo)**: Emplazado exactamente en la intersección de las dos vialidades:
  - En la proyección urbana de Godot, la esquina apunta hacia el cruce vial.
- **Coordenadas en Escena Godot (`main.tscn`)**:
  - `Position = Vector3(-66.8, 400.18, -24.81)`
  - `Basis = Transform3D(-1, 0, 0, 0, 1, 0, 0, 0, -1)` (rotación pura de $180.0^\circ$ garantizando paralelismo geométrico estricto con la banqueta de Av. Benito Juárez, sin reducción de sección hacia el poniente).
  - Nodo raíz: `BBVA_Tecate (StaticBody3D)` con colisionadores analíticos para edificio y banqueta perimetral.

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
     - Ambas caras (orientada a poniente hacia Cárdenas y orientada a oriente hacia el estacionamiento) reproducen fielmente la rotulación corporativa completa.

2. **Fachada Sur sobre Avenida Benito Juárez (Eje Poniente-Oriente, sin Cajero)**:
   - Longitud total de $22.80\text{ m}$, 4 crujías modulares.
   - **Fascia 2009 de Alucobond azul cobalto**: cubre las Crujías 1 a 3 (hasta el machón $X = 17.40\text{ m}$).
   - **Crujía 4 (`JUAN VARGAS R`)**: dintel superior en estuco blanco continuo, tal como documenta la fotografía histórica `media_1789774756138.png`.
   - **Filetes blancos horizontales**: espaciado calibrado con holgura limpia ($0.27\text{ m}$) respecto al texto `Bancomer`, extendiéndose hasta $X = 17.20\text{ m}$ sin solapamiento ni recorte.
   - Vidrios de planta alta con despachos: `CASAS TERRENOS RANCHOS` (Crujía 3) y `JUAN VARGAS R` (Crujía 4).
   - Mansarda superior continua de tejas coloniales terracota sobre cornisa corrida.

3. **Fachada Oeste sobre Calle Presidente Lázaro Cárdenas (Eje Norte-Sur, con Cajero)**:
   - Longitud continua de $30.00\text{ m}$ con 6 crujías modulares y zaguán de acceso a consultorios.
   - Mansarda de tejas continuas con ménsulas/canecillos de concreto en voladizo (corbels).
   - **Crujías 1 a 3**: Sección bancaria con fascia azul cobalto 2009, logotipo `BBVA Bancomer` con separación no-invasiva de filetes horizontales blancos.
   - **Crujía 3**: Portal de **Cajero Automático** en el lado izquierdo del vano, con caja de luz azul y rojo `RED` + `CAJERO AUTOMATICO`, puerta acristalada y ventanal adyacente con persianas.
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
     - Acceso mediante escalera interior de 4 peldaños de concreto hacia el zaguán.
     - Machón esquinero norte revestido en mosaico vítreo a juego con Guajardo.

4. **Fachada Este (Estacionamiento y Rampa de Servicio - Ground Truth `media_1789781403754.jpg`)**:
   - 5 crujías modulares en planta alta con cancelería de 3 hojas verticales y travesaño horizontal en el tercio superior.
   - Rótulo en pintura blanca sobre cristal `LICENCIADO EN DERECHO` situado en la hoja superior de la Crujía 1 (primera ventana del sur).
   - Planta baja modulada en 5 crujías alineadas exactamente con las de planta alta: ventanales comerciales con persianas y puerta central de acceso en Crujía 3 con montante superior vidriado.
   - Luminarias exteriores tipo aplique cilíndrico metálico (sconces) montadas en las pilastras de planta baja.
   - Rampa vehicular descendente con barandal tubular blanco, murete de contención y letrero vial ortogonal `ENTRADA BBVA ➔`.
   - Núcleo semicilíndrico trasero de escalera de emergencia y casetas técnicas HVAC en azotea.

5. **Desacoplamiento Estructural de Banqueta**:
   - El edificio reposa limpio a cota $Z = 0.0\text{ m}$ (`bbva_tecate_centro.glb`).
   - La banqueta modular perimetral con cordón rojo se encuentra en `banqueta_bbva_tecate.glb`.

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
+7.45 m   ┼  Cornisa Moldurada Corrida Blanca (Vuelo 0.40 m)
          │  [Canecillos/ménsulas de concreto bajo alero continuo a lo largo de Cárdenas]
+7.10 m   ┼  Dintel de Ventanales Planta Alta (Vanos de H = 1.65 m, 3 hojas con travesaño)
+4.30 m   ┼  Remate de Fascia Alucobond Azul Corporativo 2009 (H = 1.10 m)
+3.20 m   ┼  Viga Dintel / Base menor del trapecio Guajardo (4.60 m)
+2.85 m   ┼  Dintel de cancelería PB (Vanos de H = 2.45 m a 2.80 m)
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
4. **Escenas Instanciables Godot 4**:
   - `godot_project/assets/buildings/bbva_tecate_centro.tscn`: escena unificada que ensambla el edificio (`bbva_tecate_centro.glb`), la banqueta modular (`banqueta_bbva_tecate.glb`) y todos los colisionadores de suelo y fachada.
   - `godot_project/assets/buildings/banqueta_bbva_tecate.tscn`: escena modular independiente de la banqueta con cordón perimetral.
5. **Integración en Escena Principal (`main.tscn`)**:
   - Emplazado en la intersección Juárez $\cap$ Cárdenas (`Position = Vector3(-66.8, 400.18, -24.81)`, Yaw = $180.0^\circ$).
