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

1. **Giro Sesgado al Sur (Matriz Identidad)**:
   - El nodo fue introducido originalmente con la base identidad $\text{Transform3D}(1, 0, 0, 0, 1, 0, 0, 0, 1, \dots)$.
   - En Tecate, la trama urbana tiene un rumbo canónico de $\theta = -4.842^\circ$. Al mantenerse en los ejes cartesianos puros ($Z = \text{cte}$), el parque no acompañaba el ascenso hacia el norte de la Avenida Benito Juárez, abriéndose hacia el sur conforme avanzaba hacia el este e invadiendo vialidades.
2. **Inclinación Nula Frente a la Pendiente Topográfica**:
   - Con $\text{basis.y} = (0, 1, 0)$, el parque se encontraba completamente horizontal a cota fija, mientras que el terreno natural desciende hacia el norte a razón de $-0.0314\text{ m/m}$ y asciende al este a $+0.00935\text{ m/m}$.
   - Esto causaba que el parque flotara hasta $+1.60\text{ m}$ sobre el suelo en el sector sur y se enterrara hasta $-1.50\text{ m}$ bajo tierra en el sector norte.

---

## 3. Calibración Matemática Canónica

### A. Base Ortonormal en el Plano del Terreno

- Ángulo azimutal de la cuadrícula urbana: $\theta = -4.842^\circ$.
- Vector longitudinal Este sobre el terreno: $\vec{u}_x = (0.996391, 0.011957, -0.084039)$.
- Vector normal topográfico: $\vec{u}_y = (-0.009349, 0.999465, 0.031356)$.
- Vector transversal Sur sobre el terreno: $\vec{u}_z = \vec{u}_x \times \vec{u}_y = (0.084369, -0.030457, 0.995969)$.
- Determinante estricto: $+1.000000$.

### B. Enrase de Rasante y Origen

- Centro de emplazamiento: coincidente con el centro del Kiosko en $(X_0, Z_0) = (-6.6844, 2.6878)$.
- Cota de rasante $Y_0$ milimétrica sobre el plano topográfico:
  $$Y_0 = 0.009354 \cdot (-6.6844) - 0.031373 \cdot (2.6878) + 400.041627 = \mathbf{399.8948\text{ m}}$$

---

## 4. Transformación Canónica en `main.tscn`

```tscn
[node name="Parque_Miguel_Hidalgo" parent="." instance=ExtResource("23_parque_hidalgo")]
transform = Transform3D(0.996391, -0.009349, 0.084369, 0.011957, 0.999465, -0.030457, -0.084039, 0.031356, 0.995969, -6.6844, 399.8948, 2.6878)
```
