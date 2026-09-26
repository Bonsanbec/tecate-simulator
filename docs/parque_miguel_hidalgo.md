# Ficha Técnica y Registro de Calibración Espacial: Parque Miguel Hidalgo (2009)

Documento técnico de especificación morfológica, física analítica y calibración espacial canónica del **Parque Central Miguel Hidalgo** en el Centro Histórico de Tecate, B.C., delimitado por **Avenida Benito Juárez** al Norte, **Callejón Libertad** al Sur, **Calle Presidente Pascual Ortiz Rubio** al Oriente y **Avenida Presidente Lázaro Cárdenas** al Poniente.

---

## 1. Contexto Urbano y Emplazamiento Cartesiano

- **Epicentro Cívico**: Epicentro urbano que acoge el Kiosko Central, la Fuente de la Paz, el Monumento a Benito Juárez (NE), el Busto a Miguel Hidalgo (Sur), el Monumento a Lázaro Cárdenas (SO) y el Obelisco Conmemorativo (Este).
- **Límites Viales**:
  - Frente Norte: Avenida Benito Juárez (cota de rasante $Y \approx 401.05\text{ m}$).
  - Frente Sur: Callejón Libertad (cota de rasante $Y \approx 398.71\text{ m}$).
  - Costado Oriente: Calle Presidente Pascual Ortiz Rubio (cota de rasante $Y \approx 400.30\text{ m}$).
  - Costado Poniente: Avenida Presidente Lázaro Cárdenas (cota de rasante $Y \approx 399.51\text{ m}$).
- **Contrato Cartesiano Canónico del Modelo (`parque_miguel_hidalgo.glb`)**:
  - $\text{Origen }(0,0,0)$: Centro concéntrico del Kiosko a nivel de rasante local.
  - $\text{Eje }+X$: Vector longitudinal hacia Pascual Ortiz Rubio (Oriente).
  - $\text{Eje }-X$: Vector hacia Lázaro Cárdenas (Poniente).
  - $\text{Eje }-Z$ (Godot) / $+Y$ (Blender): Vector hacia Avenida Benito Juárez (Norte).
  - $\text{Eje }+Z$ (Godot) / $-Y$ (Blender): Vector hacia Callejón Libertad (Sur).
  - $\text{Eje }+Y$ (Godot) / $+Z$ (Blender): Cota de elevación vertical con zócalo basal enterrado continuo ($Z \le -1.50\text{ m}$).

---

## 2. Diagnóstico de los Defectos Identificados

1. **Forma del Polígono y Extensión Desfasada**:
   - El script original modeló un perímetro aproximado de $107.65\text{ m} \times 82.19\text{ m}$ que no correspondía fielmente con la forma del encierro de las cuatro calles reales en la capa de banquetas (`manzanas_baked.glb`).
   - Los andadores axiales quedaban cortos (entre $2.8\text{ m}$ y $3.5\text{ m}$) sin conectar con las banquetas de Juárez, Libertad, Ortiz Rubio ni Cárdenas.
   - La forma real del encierro de las cuatro calles es un polígono convexo de 10 vértices de **$114.02\text{ m}$ de ancho por $88.06\text{ m}$ de fondo** con sus cuatro ochavas viales exactas.

2. **Inclinación Excesiva (*Too Steep*) y Falta de Cota Basal**:
   - Inicialmente se aplicó un plano topográfico heredado de la Manzana Central con una pendiente transversal de $\frac{\partial Y}{\partial Z} = -0.031373$ ($-3.14\%$).
   - La medición topográfica directa por mínimos cuadrados sobre la malla de banquetas (`manzanas_baked.glb`) en la manzana del Parque Hidalgo demostró que la pendiente real es de **$-0.025126$ ($-2.51\%$)**, es decir, un $20\%$ menos pronunciada.
   - Asimismo, la cota en el centro del Kiosko requería **$+14.25\text{ cm}$ adicionales** de elevación, pasando de $399.8948\text{ m}$ a **$400.0373\text{ m}$**, enrasando perfectamente con la base del Kiosko ($400.0132\text{ m}$).

---

## 3. Calibración Matemática Canónica

### A. Polígono del Encierro Real de Calles (Coordenadas Locales de Blender)

```python
PARK_PERIMETER_POLYGON = [
    (-49.56, -30.58), # Ochava SO (Callejón Libertad y Av. Pdte. Lázaro Cárdenas)
    (-47.94, -33.08), # Ochava SO vértice intermedio
    (-44.13, -35.21), # Ochava SO (Callejón Libertad)
    ( 55.32, -41.53), # Frente Sur (Callejón Libertad) y Ochava SE
    ( 56.93, -31.70), # Ochava SE (Calle Pdte. Pascual Ortiz Rubio)
    ( 64.45,  37.80), # Costado Oriente (Calle Pdte. Pascual Ortiz Rubio)
    ( 64.45,  41.92), # Ochava NE (Avenida Benito Juárez)
    (-35.30,  46.53), # Frente Norte (Avenida Benito Juárez)
    (-39.92,  46.39), # Ochava NO (Av. Benito Juárez)
    (-43.71,  38.67), # Ochava NO (Av. Pdte. Lázaro Cárdenas)
]
```

### B. Base Ortonormal en el Plano del Terreno

- Ángulo azimutal de la cuadrícula urbana: $\theta = -4.842^\circ$.
- Vector longitudinal Este sobre el terreno: $\vec{u}_x = (0.996407, 0.009330, -0.084178)$.
- Vector normal topográfico calibrado: $\vec{u}_y = (-0.007239, 0.999658, 0.025117)$.
- Vector transversal Sur sobre el terreno: $\vec{u}_z = (0.084383, -0.024418, 0.996134)$.
- Determinante estricto: $+1.000000$.

### C. Enrase de Rasante y Origen

- Centro de emplazamiento: coincidente con el centro del Kiosko en $(X_0, Z_0) = (-6.6844, 2.6878)$.
- Cota de rasante $Y_0$ milimétrica sobre el plano de banquetas:
  $$Y_0 = 0.007241 \cdot (-6.6844) - 0.025126 \cdot (2.6878) + 400.153273 = \mathbf{400.0373\text{ m}}$$

---

## 4. Transformación Canónica en `main.tscn`

```tscn
[node name="Parque_Miguel_Hidalgo" parent="." instance=ExtResource("23_parque_hidalgo")]
transform = Transform3D(0.996407, -0.007239, 0.084383, 0.009330, 0.999658, -0.024418, -0.084178, 0.025117, 0.996134, -6.6844, 400.0373, 2.6878)
```
