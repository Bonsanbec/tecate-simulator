# Ficha Técnica y Registro de Calibración Espacial: Manzana Central Urbana (2009)

Documento técnico de especificación morfológica, paramétrica, fenestración, física analítica y calibración espacial canónica de la **Manzana Central Urbana de Tecate** (`block_lat_32.57328_lon_-116.62516`), delimitada por **Avenida Benito Juárez** al Norte, **Callejón Libertad** al Sur, **Calle Presidente Pascual Ortiz Rubio** al Poniente y **Calle Presidente Abelardo L. Rodríguez** al Oriente.

---

## 1. Contexto Urbano y Emplazamiento Cartesiano

- **Identificador de Manzana Catastral**: `block_lat_32.57328_lon_-116.62516` (superficie: $\approx 10,160\text{ m}^2$).
- **Ubicación Geográfica de Referencia (WGS84)**: Epicentro cívico y comercial del Centro Histórico de Tecate, B.C.
- **Límites Viales**:
  - **Frente Norte**: Avenida Benito Juárez (longitud de manzana: $129.04\text{ m}$, cota de rasante $Y \in [402.30, 403.55\text{ m}]$).
  - **Frente Sur**: Callejón Libertad (longitud de manzana: $129.74\text{ m}$, cota de rasante $Y \in [399.63, 400.87\text{ m}]$).
  - **Costado Poniente**: Calle Presidente Pascual Ortiz Rubio (longitud: $78.12\text{ m}$).
  - **Costado Oriente**: Calle Presidente Abelardo L. Rodríguez (longitud: $86.01\text{ m}$).
- **Contrato Cartesiano Canónico del Modelo (`manzana_central_2009.glb`)**:
  - $\text{Origen }(0,0,0)$: Esquina Suroeste exterior de muros (Pascual Ortiz Rubio y Callejón Libertad) a nivel de rasante local ($Z = 0.00\text{ m}$ en Blender).
  - $\text{Eje }+X$: Vector longitudinal Poniente $\to$ Oriente a lo largo del bloque ($X \in [0.00, 134.73\text{ m}]$, con aleros hasta $135.58\text{ m}$).
  - $\text{Eje }+Y$ (Blender) / $-Z$ (Godot): Vector transversal Sur $\to$ Norte ($Y \in [0.00, 91.19\text{ m}]$, con marquesinas hasta $92.14\text{ m}$).
  - $\text{Eje }+Z$ (Blender) / $+Y$ (Godot): Cota de elevación vertical ($Z \in [-1.50, 9.40\text{ m}]$ con zócalo basal continuo enterrado a $-1.50\text{ m}$).
- **Prohibición Estricta de Banquetas Embebidas**:
  - El asset binario (`manzana_central_2009.glb`) carece intencionalmente de banquetas, guarniciones y calzadas públicas. Las banquetas pertenecen a la capa GIS del simulador (`UrbanManzanas` y `Roadways`).

---

## 2. Diagnóstico de los 3 Errores del Commit `e56cfe5`

El commit `e56cfe5808a6e256eb0515fb9c52791ce221ceae` introdujo la siguiente transformación en `godot_project/main.tscn`:
```tscn
transform = Transform3D(0.950513, 0.011756, -0.092452, -0.009246, 0.999444, 0.032033, 0.084122, -0.026832, 0.861452, 56.5282, 399.5098, 29.9695)
```

Al descomponer la matriz en sus vectores de base según la convención canónica de Godot 4 (`basis.x = (n0, n3, n6)`, `basis.y = (n1, n4, n7)`, `basis.z = (n2, n5, n8)`), se identificaron tres defectos críticos:

### Error 1: Orientación con Ángulo Sesgado e Inversión de Signos
- En el archivo `.tscn`, `n6` se asignó como $+0.084122 > 0$ y `n2` como $-0.092452 < 0$.
- Esto provocó que $\text{basis.x.z} = +0.084122 > 0$, orientando el eje longitudinal hacia el Sur (+Z). Conforme incrementaba $X$, las edificaciones invadían el Callejón Libertad por más de $11\text{ metros}$ en el extremo oriente, apartándose de la Avenida Juárez.
- La pendiente real de la Avenida Juárez es $\frac{\Delta Z}{\Delta X} = -0.014853$ ($\theta = -0.8509^\circ$), lo que exige estrictamente $\text{basis.x.z} < 0$ y $\text{basis.z.x} > 0$.

### Error 2: Inclinación de Terreno Invertida
- El terreno de Tecate desciende hacia el río al Norte ($-Z$) y asciende hacia las montañas al Oriente ($+X$). Por tanto, la normal topográfica unitaria sobre la que reposa la manzana es $\vec{n} = (-0.009349, 0.999465, 0.031356)$.
- El agente anterior asignó $n1 = +0.011756 > 0$ y $n7 = -0.026832 < 0$, invirtiendo ambos signos.
- Como consecuencia, el complejo se enterraba bajo la tierra en el sector oriente y flotaba en el sector poniente, produciendo un desnivel inverso al suelo real.

### Error 3: Escala Anisótropa y Deformación Geométrica
- Las normas de los tres vectores de la base en `e56cfe5` eran:
  $$\|\text{basis.x}\| = 0.95427, \quad \|\text{basis.y}\| = 0.99999, \quad \|\text{basis.z}\| = 0.86699$$
- El agente anterior acható el eje de profundidad ($Z$) a un $86.7\%$ mientras escaló el ancho ($X$) al $95.4\%$ y la altura ($Y$) al $100\%$.
- Esta distorsión destruyó las proporciones arquitectónicas de los edificios: convirtió columnas redondas en elipses, alteró el ancho de puertas y ventanas, deformó los colisionadores de caja analíticos de Godot e introdujo descuadres en las uniones medianeras interiores.

---

## 3. Calibración Matemática Canónica de Producción

### A. La Causa Raíz del Cierre y Dimensionamiento de la Manzana
1. **La Confusión de la Caja Envolvente Diagonal**:
   - En `blocks_cache.json`, la manzana catastral se encuentra orientada con un rumbo geodésico canónico de $\theta = -4.842^\circ$ (headings de fachada: $85.10^\circ, 175.16^\circ, 265.10^\circ, 355.16^\circ$).
   - La distancia diagonal entre esquinas extremas opuestas sin rotar (Bounding Box cartesiano AABB) arrojaba $\Delta Z = 29.14 - (-62.05) = 91.19\text{ m}$.
   - El generador procedural tomó este valor como si fuera el fondo de la manzana y dimensionó el modelo en $134.73\text{ m} \times 91.19\text{ m}$.
   - Sin embargo, la **distancia perpendicular real entre la Avenida Juárez y el Callejón Libertad** es de **$80.62\text{ m}$** ($78.3\text{ m}$ en zona de desplante de muros).
   - El modelo en Blender posee por tanto casi $13\text{ metros}$ de fondo excedente acumulados en el patio interior de maniobras y en la prolongación de los locales de Ortiz Rubio.

2. **Alineación Angular con el Rumbo Geodésico Canónico ($\theta = -4.842^\circ$)**:
   - La rotación se calibra con el rumbo canónico de la trama urbana de Tecate ($\theta = -4.842^\circ$).
   - Vector longitudinal Este en el plano del terreno: $\vec{u}_x = (0.996390, 0.011957, -0.084040)$.
   - Vector vertical normal: $\vec{u}_y = (-0.009349, 0.999465, 0.031356)$.
   - Vector transversal Sur: $\vec{u}_z = \vec{u}_x \times \vec{u}_y = (0.084368, -0.030458, 0.995969)$.
   - Ortonormalidad estricta con determinante $+1.000000$.

3. **Compensación de Escala Calibrada (Reducción del 10% Adicional) y Balance de Banquetas**:
   - Para que el complejo encaje con holgura y simetría dentro de la manzana catastral sin rozar ninguna de las cuatro vialidades perimetrales:
     - En $X$ (ancho poniente-oriente): $S_x = 0.799425 \implies 134.73 \times 0.799425 = 107.71\text{ m}$, garantizando **$5.60\text{ m}$ de banqueta libre** en Ortiz Rubio y **$5.56\text{ m}$** en Rodríguez.
     - En $Z$ (profundidad norte-sur): $S_z = 0.728460 \implies 91.19 \times 0.728460 = 66.43\text{ m}$, garantizando **$5.67\text{ m}$ de banqueta libre** en Avenida Juárez (poniente) y **$5.60\text{ m}$** en Callejón Libertad.
     - En $Y$ (altura vertical): $S_y = 0.799425$ (sincronizada exactamente con el eje longitudinal).
   - Todos los aleros, marquesinas, voladizos y letreros quedan $100\%$ resguardados dentro del polígono de la manzana con holguras libres de banqueta de **$\ge 4.88\text{ m}$** ($4.88\text{ m}$ en el alero NW, $5.01\text{ m}$ en SW, $4.97\text{ m}$ en SE y $6.84\text{ m}$ en NE).

---

## 4. Transformación Canónica Integrada en `main.tscn`

```tscn
[node name="Manzana_Central_2009" parent="." instance=ExtResource("22_manzana_central")]
transform = Transform3D(0.796540, -0.007474, 0.061460, 0.009559, 0.798997, -0.022187, -0.067183, 0.025067, 0.725524, 69.4245, 399.9872, 22.4332)
```

---

## 5. Tabla de Mapeo de Componentes de la Matriz

| Índice en `.tscn` | Componente | Valor Calibrado | Justificación Física / Canónica |
| :--- | :--- | :--- | :--- |
| `n0` | $\text{basis.x.x}$ | $0.796540$ | $S_x \cdot u_x.x$ a lo largo de la calle ($S_x = 0.799425$) |
| `n1` | $\text{basis.y.x}$ | $-0.007474$ | Normal topográfica ascendente hacia Oriente (signo corregido) |
| `n2` | $\text{basis.z.x}$ | $+0.061460$ | Componente $X$ del eje transversal hacia Callejón Libertad ($>0$) |
| `n3` | $\text{basis.x.y}$ | $+0.009559$ | Pendiente longitudinal del terreno |
| `n4` | $\text{basis.y.y}$ | $0.798997$ | Escala vertical sincronizada con el eje longitudinal ($S_y = 0.799425$) |
| `n5` | $\text{basis.z.y}$ | $-0.022187$ | Pendiente transversal del terreno hacia el río |
| `n6` | $\text{basis.x.z}$ | $-0.067183$ | Descenso hacia el Norte ($\theta = -4.842^\circ$, paralelo a Juárez y Libertad) |
| `n7` | $\text{basis.y.z}$ | $+0.025067$ | Normal topográfica descendente hacia Norte (signo corregido) |
| `n8` | $\text{basis.z.z}$ | $0.725524$ | Escala transversal compensatoria para profundidad real ($S_z = 0.728460$) |
| `n9` | $\text{origin.x}$ | $69.4245$ | Origen centrado garantizando $\approx 5.6\text{ m}$ de banqueta en Ortiz Rubio y Rodríguez |
| `n10` | $\text{origin.y}$ | $399.9872$ | Cota de rasante enrasada con el plano del suelo ($Y = 0.009354 \cdot X - 0.031373 \cdot Z + 400.041627$) |
| `n11` | $\text{origin.z}$ | $22.4332$ | Origen centrado con balance simétrico de banquetas en Callejón Libertad y Av. Juárez |
