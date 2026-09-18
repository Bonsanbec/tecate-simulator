# Ficha Técnica Arquitectónica: Banco BBVA Tecate Centro (V4.2 Ground-Truth Perfeccionado)

Documento técnico de especificación morfológica, paramétrica, PBR y consensus multi-perspectiva para la reconstrucción fidedigna del edificio comercial/financiero del **Banco BBVA** (esquina Av. Benito Juárez y Calle Presidente Lázaro Cárdenas, Tecate, B.C.) en Blender 5.1 y Godot Engine 4.

---

## 1. Contexto Urbano y Emplazamiento Cartesiano

- **Nombre Oficial**: Sucursal BBVA Tecate Centro (antiguo BBVA Bancomer).
- **Emplazamiento Histórico**: Esquina noreste de la intersección entre Avenida Benito Juárez (arteria principal este-oeste) y Calle Presidente Lázaro Cárdenas (eje norte-sur hacia el monumento y parque).
- **Dirección Catastral**: Calle Presidente Lázaro Cárdenas esq. Av. Benito Juárez, Col. Centro / Primera, C.P. 21400, Tecate, B.C.
- **Coordenadas GPS**: `32.5734618°N, -116.6274318°W`.
- **Coordenadas Locales (Tecate Simulator)**: `X = -84.03 m, Y = 25.92 m` (a **87.94 m** radiales del origen en el Kiosko del Parque Miguel Hidalgo).
- **Transformada en Escena Godot (`main.tscn`)**:
  - `Position = Vector3(-84.03, 400.0, -25.92)`
  - Nodo raíz: `BBVA_Tecate (StaticBody3D)` con colisionadores analíticos `BoxShape3D`.

---

## 2. Anatomía de Consenso Multi-Perspectiva (Eliminación de Alucinaciones)

El edificio presentaba alucinaciones visuales al ser analizado desde una sola fotografía de Street View. Gracias al cotejo riguroso de todo el dataset de la manzana y fotografías del usuario:

1. **La Esquina Ochavada a 45º (Ground Truth: `media_1789772450504.jpg` y `media_1789772893709.png`)**:
   - El edificio **no** tiene una esquina recta a 90º. Presenta un monumental **chaflán / ochava a 45º** típico de la arquitectura bancaria y cívica de mediados del siglo XX en México.
   - En este chaflán se levanta el **Torreón Guajardo**, revestido en **mosaico vítreo veneciano añil/purpúreo** (`#2A2F48`), con rótulo histórico en letras de bronce dorado:
     ```
     EDIFICIO
     LIC. JOSE F. GUAJARDO
     1954
     ```
   - En la base del chaflán se ubica el **acceso principal al banco** con cancelería de aluminio anodizado y puertas dobles de cristal templado.
   - Sobre el pretil del torreón ($Z = 9.00\text{ m}$), anclado mediante dos columnas tubulares de acero estructural, se erige el **anuncio espectacular de azotea**: caja de luz a doble cara orientada a 45º con panel superior azul (`BBVA Bancomer`) y panel inferior blanco (`CAJERO AUTOMATICO` en verde).

2. **Fachada Sur (Avenida Benito Juárez - Ground Truth: `xB3bx-WBbz5e4GxAuGHGWw_yaw_174.72.png`)**:
   - Longitud: $18.60\text{ m}$ (de $X = 4.20$ a $22.80\text{ m}$).
   - 4 crujías modulares con pilastras de concreto blanco en resalte.
   - Gran fascia continua de Alucobond azul marino (`#16215B`) con filete blanco y rótulo corporativo `BBVA Bancomer`.
   - Mansarda de tejas coloniales de barro terracota sobre cornisa moldurada blanca.

3. **Fachada Oeste (Calle Presidente Lázaro Cárdenas - Ground Truth: `media_1789772450504.jpg`)**:
   - Longitud: $16.00\text{ m}$ (de $Y = 4.20$ a $20.20\text{ m}$).
   - 4 crujías comerciales con **ménsulas / canecillos de concreto en voladizo (corbels)** bajo el alero de tejas.
   - Fascia azul continuo con rótulo `BBVA Bancomer`.
   - Vano con cancelería comercial y puerta de acceso al cajero automático exterior (`CAJERO AUTOMATICO`).
   - Remata al norte contra la pared medianera del consultorio dental contiguo (`DENTISTA`).

4. **Fachada Este y Rampa de Estacionamiento (Ground Truth: `z61ozuaV4OPf4Hp2thHEfw_yaw_82.46.png`)**:
   - Muro lateral este con murete de confinamiento de concreto blanco para la rampa descendente hacia el estacionamiento subterráneo/trasero.
   - Barandilla de seguridad tubular en acero esmaltado blanco.
   - Caseta de control/vigilancia.
   - Letrero oficial azul de señalización vial: `ENTRADA BBVA ➔`.

---

## 3. Despiece y Dimensiones Técnicas por Niveles

```
+12.65 m  ▲  Cúspide de Caja de Luz Espectacular en Azotea
          │  [Panel Azul BBVA Bancomer: 3.60 x 1.65 m]
+11.00 m  ┼  División de Panel
          │  [Panel Blanco Cajero Automático: 3.60 x 1.15 m]
+9.85 m   ┼  Base de Caja de Luz
          │  [Postes de tubo estructural de acero: H = 0.85 m]
+9.00 m   ┼  Pretil Superior del Torreón Guajardo (Ochava 45º)
          │  [Remate perimetral con cornisa blanca volada 0.18 m]
+8.15 m   ┼  Cumbrera de Faldones de Tejas (Alas Juárez y Cárdenas)
          │  [Teja curva colonial de barro: pendiente 25°, H = 0.70 m]
+7.45 m   ┼  Cornisa Moldurada Corrida Blanca (Vuelo 0.40 m)
          │  [Canecillos/ménsulas de concreto en voladizo en Calle Cárdenas]
+7.10 m   ┼  Dintel de Ventanales Planta Alta (Vanos de H = 1.65 m)
+4.30 m   ┼  Remate de Fascia Alucobond Azul Corporativo (H = 1.10 m)
+3.20 m   ┼  Viga Dintel / Cancelería Planta Baja (Vanos de H = 2.80 m)
+0.40 m   ┼  Plinto Basal / Zócalo de Concreto Gris Grafito
 0.00 m   ▼  Nivel de Banqueta con Cordón Rojo Oficial
```

---

## 4. Paleta de Materiales PBR y Calibración Cromática

| Material ID | Nombre Shader | Base Color (sRGB / Hex) | Roughness | Metallic | Normal / Bump Map |
|---|---|---|---|---|---|
| `mosaico_guajardo` | `M_Guajardo_Mosaico` | `#1D2644` (Añil oscuro) | 0.32 | 0.05 | Textura procedural Voronoi a escala 160 (teselas venecianas) |
| `bronce` | `M_Guajardo_Bronce` | `#D4AF37` (Bronce dorado) | 0.25 | 0.90 | Liso reflectivo pulido |
| `fascia` | `M_BBVA_Fascia_Azul` | `#16215B` (Azul corporativo BBVA) | 0.25 | 0.15 | Chapa de Alucobond satinado |
| `muro` | `M_BBVA_Muro_Blanco` | `#F2EFEA` (Blanco cálido enlucido) | 0.80 | 0.00 | Rugosidad estuco fino |
| `vidrio` | `M_BBVA_Vidrio` | `#0B1520` (Tintex reflectivo oscuro) | 0.05 | 0.35 | Transmisión 0.25 con alto índice especular |
| `aluminio` | `M_BBVA_Canceleria` | `#A4A8AD` (Aluminio natural) | 0.35 | 0.85 | Metal pulido mate |
| `zocalo` | `M_BBVA_Zocalo` | `#36383B` (Gris grafito martillado) | 0.88 | 0.00 | Rugosidad pétrea |
| `teja` | `M_BBVA_Teja` | `#8C341E` (Barro cocido terracota) | 0.78 | 0.00 | Normal map PBR de tejas de barro |
| `rotulo_blanco` | `M_BBVA_Rotulo_Blanco` | `#FFFFFF` (Blanco puro gráfico) | 0.20 | 0.05 | Acrílico difusor de luz |
| `persianas` | `M_BBVA_Persianas` | `#DCD9D0` (Beige grisáceo interior) | 0.90 | 0.00 | Mate difuso textil |
| `cordon_rojo` | `M_BBVA_Cordon_Rojo` | `#B22222` (Rojo vial normativo) | 0.85 | 0.00 | Pintura de tránsito |
| `acero` | `M_BBVA_Acero_Estructural` | `#2B2C2E` (Acero grafito industrial) | 0.45 | 0.70 | Acero tubular pintado |

---

## 5. Salidas Generadas y Assets del Proyecto

1. **Archivo Maestro Blender**:
   - `blender_assets/buildings/bbva_tecate_centro.blend`
2. **Asset 3D Optimizado Godot 4**:
   - `godot_project/assets/buildings/bbva_tecate_centro.glb`
3. **Escena Instanciable Godot 4**:
   - `godot_project/assets/buildings/bbva_tecate_centro.tscn` (con 3 cuerpos colisionadores analíticos `StaticBody3D` para cuerpo, torreón y rampa).
4. **Vistas de Validación Fotográfica**:
   - `docs/images/bbva/bbva_guajardo_45.png`: Chaflán a 45º, rótulo en bronce, acceso y espectacular.
   - `docs/images/bbva/bbva_juarez_frontal.png`: Fachada Sur completa a lo largo de Av. Juárez.
   - `docs/images/bbva/bbva_cardenas_west.png`: Fachada Oeste con canecillos y cajero en Calle Cárdenas.
   - `docs/images/bbva/bbva_east_parking.png`: Fachada Este con rampa vehicular, caseta y letrero oficial.
   - `docs/images/bbva/bbva_aerial_top.png`: Vista aérea cenital que reproduce la fotografía satelital.
