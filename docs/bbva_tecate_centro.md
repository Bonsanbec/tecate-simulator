# Ficha Técnica Arquitectónica: Banco BBVA Tecate Centro (V5.0 Ground-Truth Histórico 2009)

Documento técnico de especificación morfológica, paramétrica, PBR y consensus multi-perspectiva para la reconstrucción fidedigna del edificio comercial/financiero del **Banco BBVA** (esquina Av. Benito Juárez y Calle Presidente Lázaro Cárdenas, Tecate, B.C.) en Blender 5.1 y Godot Engine 4.

---

## 1. Contexto Urbano y Emplazamiento Cartesiano

- **Nombre Oficial**: Edificio Lic. José F. Guajardo / Sucursal BBVA Bancomer Tecate Centro (2009).
- **Emplazamiento Histórico**: Esquina suroeste de la manzana frente a la intersección vial de Avenida Benito Juárez (eje poniente-oriente) y Calle Presidente Lázaro Cárdenas (eje norte-sur).
- **Vértice de Esquina (Ochava Guajardo)**: Emplazado exactamente en la intersección de las dos vialidades:
  - En la proyección urbana de Godot, la esquina apunta en diagonal hacia el **Noreste** (vector $(+X, -Z)$).
- **Coordenadas en Escena Godot (`main.tscn`)**:
  - `Position = Vector3(-66.79, 400.25, -24.81)`
  - `Basis = Transform3D(-0.996195, 0, 0.087156, 0, 1, 0, -0.087156, 0, -0.996195)` (rotación calibrada de $175^\circ$ coincidente con la traza de Juárez a $174.7^\circ$).
  - Nodo raíz: `BBVA_Tecate (StaticBody3D)` con colisionadores analíticos `BoxShape3D`.

---

## 2. Anatomía y Nomenclatura Vial Rectificada

El edificio se emplaza en la manzana con la siguiente correspondencia geográfica y funcional:

1. **Ochava Noreste a 45º (Torreón Lic. José F. Guajardo 1956)**:
   - Apunta en dirección **Noreste** hacia el cruce de Av. Juárez y Calle Cárdenas.
   - Geometría: **Trapecio de piedra volcánica / mosaico veneciano oscuro desgastado** (`#252B3E`), sin molduras plásticas blancas, rematado con albardilla/coping de piedra natural en el pretil superior ($Z = 9.05\text{ m}$).
   - Inscripción en letras de bronce fundido en 3 líneas:
     ```
     EDIFICIO
     LIC. JOSE F. GUAJARDO
     1956
     ```
   - Acceso bancario principal en planta baja con cancelería de aluminio y puertas dobles acristaladas.
   - Espectacular de Azotea 2009: Mástil tubular de acero central; panel superior azul cobalto (`#00288E`) con recuadro `BBVA` + `Bancomer`; panel inferior blanco con logotipo rojo `RED` a la izquierda y `CAJERO AUTOMATICO` en verde a la derecha.

2. **Fachada Norte sobre Avenida Benito Juárez (Eje Poniente-Oriente, sin Cajero)**:
   - Corre en sentido **poniente-oriente** (longitud $22.80\text{ m}$).
   - 4 crujías modulares con pilastras y machón esquinero.
   - Fascia 2009 de Alucobond azul cobalto con filetes blancos y logotipo corporativo `BBVA Bancomer`.
   - Rotulaciones de despachos en vidrios de planta alta (`CASAS TERRENOS RANCHOS`, `JUAN VARGAS R`).
   - Al extremo poniente se ubica el acceso vehicular hacia el estacionamiento, delimitado por la rampa descendente, barandal blanco, caseta de vigilancia y letrero vial ortogonal `ENTRADA BBVA ➔`.

3. **Fachada Este sobre Calle Presidente Lázaro Cárdenas (Eje Norte-Sur, con Cajero)**:
   - Corre en sentido **norte-sur** (longitud continua $27.20\text{ m}$ hasta el consultorio dental `DENTISTA`).
   - Mansarda continua de tejas de barro con **canecillos/ménsulas de concreto en voladizo (corbels)** bajo el alero a lo largo de toda la fachada.
   - **Crujía 3**: Portal exterior de **Cajero Automático** con cajetín azul iluminado `CAJERO AUTOMATICO` y puerta de cristal.
   - Transición de fascia: azul cobalto para el banco y fascia plateada con rótulo `DENTISTA` en la crujía norte.
   - Vidrios de planta alta con rotulación de despachos: `DESPACHO JURIDICO QUEZADA Y ASOCIADOS` y `LIC. RAMON QUEZADA LOPEZ ABOGADO`.

4. **Fachada Poniente (Rampa y Estacionamiento)**:
   - 5 vanos de cancelería con cristales en planta alta (`LICENCIADO EN DERECHO`).
   - Planta baja con ventanales comerciales y puerta de servicio peatonal metálica con luminaria exterior.

5. **Desacoplamiento Estructural de Banqueta**:
   - El edificio reposa limpio a cota $Z = 0.0\text{ m}$ (`bbva_tecate_centro.glb`).
   - La banqueta modular perimetral con cordón rojo se encuentra en `banqueta_bbva_tecate.glb`.

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
   - `godot_project/assets/buildings/bbva_tecate_centro.tscn` (con colisionadores analíticos `StaticBody3D` orientados a $-Z$).
5. **Integración en Escena Principal (`main.tscn`)**:
   - Emplazado en la intersección Juárez $\cap$ Cárdenas (`Position = Vector3(-66.79, 400.25, -24.81)`).
