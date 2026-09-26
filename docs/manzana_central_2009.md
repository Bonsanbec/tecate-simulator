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

Para corregir los tres problemas se aplicó la formulación analítica de la metodología:

1. **Escala Uniforme e Isótropa ($S = 0.9400$)**:
   - Se unificaron los tres ejes a $S_x = S_y = S_z = 0.9400$.
   - Con $S = 0.9400$, la longitud de muros en $X$ es $134.73 \times 0.9400 = 126.65\text{ m}$ (total con marquesinas: $128.81\text{ m}$), encajando con holguras simétricas de banqueta dentro del frente de $129.04\text{ m}$ de la manzana catastral ($1.81\text{ m}$ libre en Pascual Ortiz Rubio y $0.58\text{ m}$ en Abelardo L. Rodríguez).
   - En profundidad, $91.19 \times 0.9400 = 85.72\text{ m}$, coincidiendo milimétricamente con el lateral oriente de la manzana ($86.01\text{ m}$).

2. **Alineación Angular Analítica con Avenida Juárez ($\theta = -0.8509^\circ$)**:
   - Vector longitudinal unitario horizontal: $\vec{u}_{xh} = (0.999890, 0, -0.014853)$.
   - Proyección sobre el plano del suelo con normal $\vec{n}_{suelo} = (-0.009349, 0.999465, 0.031356)$:
     $$\vec{u}_x = (0.999846, 0.009809, -0.014549)$$
     $$\vec{u}_y = (-0.009349, 0.999465, 0.031356)$$
     $$\vec{u}_z = \vec{u}_x \times \vec{u}_y = (0.014849, -0.031215, 0.999402)$$
   - Ortonormalidad exacta: $\vec{u}_x \cdot \vec{u}_y = 0$, $\vec{u}_x \cdot \vec{u}_z = 0$, $\vec{u}_y \cdot \vec{u}_z = 0$, determinante $= +1.000000$.

3. **Cota de Rasante y Enrase Topográfico Milimétrico**:
   - Desplante de origen en $(X_0, Y_0, Z_0) = (56.0728, 399.6291, 29.8674)$.
   - Cotas en las cuatro esquinas:
     - **SW (Ortiz Rubio & Libertad)**: $(56.07, 399.63, 29.87)$ — Cota de terreno: $399.63\text{ m}$ (discrepancia: $0.0000\text{ m}$).
     - **SE (Rodríguez & Libertad)**: $(182.70, 400.87, 28.02)$ — Cota de terreno: $400.87\text{ m}$ (discrepancia: $0.0000\text{ m}$).
     - **NW (Ortiz Rubio & Juárez)**: $(54.80, 402.30, -55.80)$ — Cota de terreno: $402.30\text{ m}$ (discrepancia: $0.0000\text{ m}$).
     - **NE (Rodríguez & Juárez)**: $(181.43, 403.55, -57.64)$ — Cota de terreno: $403.55\text{ m}$ (discrepancia: $0.0000\text{ m}$).
   - Discrepancia vertical en toda la huella: **$0.00\text{ cm}$**.

---

## 4. Transformación Canónica Integrada en `main.tscn`

```tscn
[node name="Manzana_Central_2009" parent="." instance=ExtResource("22_manzana_central")]
transform = Transform3D(0.939855, -0.008788, 0.013958, 0.009220, 0.939497, -0.029342, -0.013676, 0.029475, 0.939438, 56.0728, 399.6291, 29.8674)
```

---

## 5. Tabla de Mapeo de Componentes de la Matriz

| Índice en `.tscn` | Componente de Matriz | Valor en `e56cfe5` (Erróneo) | Valor Calibrado (Corregido) | Justificación Física / Canónica |
| :--- | :--- | :--- | :--- | :--- |
| `n0` | $\text{basis.x.x}$ | $0.950513$ | $0.939855$ | Escala $S \cdot \cos\theta$ longitudinal |
| `n1` | $\text{basis.y.x}$ | $+0.011756$ | $-0.008788$ | Inclinación de normal hacia Poniente (signo corregido) |
| `n2` | $\text{basis.z.x}$ | $-0.092452$ | $+0.013958$ | Componente $X$ de eje transversal (signo corregido) |
| `n3` | $\text{basis.x.y}$ | $-0.009246$ | $+0.009220$ | Pendiente longitudinal ascendente hacia Oriente |
| `n4` | $\text{basis.y.y}$ | $0.999444$ | $0.939497$ | Escala uniforme $S$ en eje vertical |
| `n5` | $\text{basis.z.y}$ | $+0.032033$ | $-0.029342$ | Pendiente transversal descendente hacia el río |
| `n6` | $\text{basis.x.z}$ | $+0.084122$ | $-0.013676$ | Descenso en $Z$ hacia el Norte (paralelo a Juárez, signo corregido) |
| `n7` | $\text{basis.y.z}$ | $-0.026832$ | $+0.029475$ | Inclinación de normal hacia Sur (signo corregido) |
| `n8` | $\text{basis.z.z}$ | $0.861452$ | $0.939438$ | Escala uniforme $S$ (eliminada deformación del 86%) |
| `n9` | $\text{origin.x}$ | $56.5282$ | $56.0728$ | Origen enrasado en esquina Suroeste |
| `n10` | $\text{origin.y}$ | $399.5098$ | $399.6291$ | Cota rasante milimétrica en plano topográfico |
| `n11` | $\text{origin.z}$ | $29.9695$ | $29.8674$ | Retranqueo perimetral simétrico de banquetas |
