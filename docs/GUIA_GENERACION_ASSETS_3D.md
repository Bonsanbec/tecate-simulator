# Guía Metodológica: Generación de Assets 3D Paramétricos para Tecate Simulator

Esta guía documenta los factores clave, la estructura de información, la sinergia entre prompt y referencia visual, y el pipeline técnico en Blender/Python que hicieron posible recrear con fidelidad milimétrica el **Poste de Nomenclatura Urbana Clásica de Tecate**. 

El objetivo es establecer un **framework estandarizado y reproducible** para modelar cualquier otro elemento del mobiliario o arquitectura urbana cotidiana de Tecate (bancos de plaza, farolas, quioscos, casetas, paradas de autobús, botes de basura de herrería, monumentos, etc.).

---

## 1. La Clave del Éxito: La Anatomía de la Información Proporcionada

El factor determinante para lograr un resultado de nivel profesional no fue el azar, sino la **calidad y estructura de la información provista en el prompt inicial y en el diálogo**.

### A. Estructura Jerárquica "De Abajo Hacia Arriba" (Bottom-Up)
En lugar de describir el objeto como un todo difuso, la especificación técnica lo descompuso en piezas geométricas independientes con cotas claras:
1. **Dimensiones Globales y Contexto Funcional**:
   - Altura total: $2.95\text{ m}$.
   - Huella en suelo: Diámetro $\varnothing\ 0.32\text{ m}$.
   - Propósito: Nomenclatura repetida en cientos de esquinas (implicó que debía ser modular y ligero).
2. **Desglose Morfológico por Malla**:
   - **Base/Pedestal**: Altura $0.45\text{ m}$, campana hiperbólica con 16 facetas suaves, anillo de piso y molduras (toro y escocia).
   - **Fuste**: Diámetro constante $\varnothing\ 0.085\text{ m}$ hasta $2.25\text{ m}$.
   - **Capitel**: Balustre clásico torneado de transición a las placas.
   - **Herraje y Mecanismo**: Vástago de acero y collarines de asiento sin colisiones.
   - **Placas de Nomenclatura**: Dimensiones $0.90\text{ m} \times 0.22\text{ m}$, cruce en 90°, composición asimétrica (2/3 calle y 1/3 patrocinador).
   - **Crestería Ornamental**: Semicírculo de $0.10\text{ m}$ de radio, pestaña perimetral de $9\text{ mm}$, altorrelieve "AYUNTAMIENTO" y número "17".

### B. Especificación de Acabados y Materiales del Mundo Real
Describir los materiales no por simples colores, sino por su **comportamiento físico y desgaste natural**:
- Hierro fundido gris oscuro grafito con textura rugosa mate de arena (`Metallic 0.70`, `Roughness 0.78`).
- Bronce expuesto a la intemperie con pátina verde cardenillo (`Metallic 0.45`, `Roughness 0.75`).
- Relieves en latón erosionado y pulido en bordes salientes (`Metallic 0.55`, `Roughness 0.65`).
- Recuadro esmaltado blanco porcelanizado tradicional de patrocinador (`Roughness 0.35`).

### C. El Rol Esencial de la Fotografía de Referencia (Verdad de Terreno)
La imagen fotográfica real de la esquina de Tecate (`media_1789700600256.png`) permitió contrastar la teoría con la realidad construida:
- **Descubrimiento del Crestón Centrado**: La especificación preliminar situaba el semicírculo a la izquierda, pero la foto reveló que en Tecate está estrictamente al centro de la placa superior.
- **Identificación del Recuadro de Patrocinador**: La foto mostró que el tercio derecho no es del mismo color cardenillo, sino un recuadro blanco esmaltado para patrocinadores ("CLINICA HOSPITAL SANTA CATARINA").
- **Identificación del Escudo Municipal**: La foto permitió leer la tipografía arqueada "AYUNTAMIENTO" y el número tradicional "17" de la demarcación tecatense.
- **Solución al Clipping**: La foto mostró cómo una placa descansa físicamente sobre la otra a 90° mediante collarines de hierro, en lugar de atravesarse entre sí.

---

## 2. Metodología Técnica: Modelado Paramétrico por Código vs Modelado Manual

En lugar de modelar vértices interactivamente a mano (lo cual es lento, propenso a desviaciones milimétricas y difícil de versionar), se utilizó **programación paramétrica en Python (`bpy` + `bmesh`) dentro de Blender**:

### Ventajas de este Enfoque
1. **Precisión Matemática Absoluta**:
   - Cada perfil de torno del poste se genera mediante funciones matemáticas puras (círculos trigonométricos con modulación de $16$ facetas: $r + A \cos(16\theta)$).
   - El arco de medio punto de la crestería y el kerning tangencial de las letras siguen fórmulas geométricas exactas:
     $$\vec{P}(i) = \left( R_{\text{arc}} \cos(\theta_i),\, Y_{\text{face}},\, H_2 + R_{\text{arc}} \sin(\theta_i) \right)$$
     $$\theta_z = \pm (\theta_i - 90^\circ)$$
2. **Cero Clipping Garantizado**:
   - Al definir las cotas verticalmente en un sistema algebraico secuencial ($Z_{\text{base\_sup}} = Z_{\text{tope\_inf}}$), es físicamente imposible que las piezas colisionen.
3. **Reproducibilidad y Automatización Total**:
   - El asset completo (modelo maestro `.blend`, exportaciones limpias y demo `.glb`, y renders en alta resolución) se regenera en **menos de 15 segundos** con un solo comando desatendido:
     ```bash
     /Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/generate_poste_nomenclatura.py
     ```
4. **Inspección Visual Autónoma (Closed-Loop Feedback)**:
   - El agente configuró cámaras ortogonales y de detalle, renderizó en Cycles CPU con iluminación de tres puntos, y luego utilizó la herramienta de visión (`view_file`) para inspeccionar la imagen como un humano. Esto permitió detectar y corregir de forma inmediata cualquier texto en espejo o collarín sobresaliente.

---

## 3. Arquitectura del Asset para Motores de Videojuegos (Godot 4)

Un error común al crear assets 3D es sobrecargarlos o hacerlos estáticos. Aquí se aplicó un estándar de producción:

1. **Separación Producción vs Demostración**:
   - `poste_nomenclatura_tecate.glb`: **Asset de producción limpio**. Pesa solo ~168 KB, no tiene textos 3D pesados ni quemados, cuenta con UVs planas limpias y 3 slots de material bien asignados.
   - `poste_nomenclatura_tecate_demo.glb`: **Asset de previsualización**. Incluye texto 3D para evaluar la escala y estética de inmediato en el viewport.
2. **Normales y Sombreado Híbrido**:
   - Las superficies curvas del poste y molduras tienen `poly.use_smooth = True` para reflejos continuos de hierro fundido.
   - Las caras planas frontales y traseras de las placas tienen `poly.use_smooth = False` para garantizar rigidez plana absoluta sin sombras fantasma diagonales.
3. **Pivote en Origen de Apoyo $(0, 0, 0)$**:
   - El punto de pivote está exactamente en el contacto del anillo con la banqueta. Al colocar el nodo en Godot con $Y=0$ sobre la acera, asienta perfectamente.
4. **Integración con `Label3D` / Decals**:
   - Se entregó el script GDScript exacto con las coordenadas locales $X, Y, Z$ de las caras para que el programador solo tenga que cambiar dos cadenas de texto (`calle_inferior`, `calle_superior`) y las 4 etiquetas se instancien alineadas en ambas caras.

---

## 4. Framework Replicable para Futuros Objetos Cotidianos de Tecate

Para reproducir este mismo resultado con cualquier otro objeto del entorno de Tecate, sigue esta plantilla estándar:

### Plantilla de Ficha Técnica (Prompt para el Asistente)

```markdown
**Nombre del Asset**: [Ejemplo: Banco Colonial del Parque Miguel Hidalgo]
**Ubicación y Función**: [Ejemplo: Bancas de descanso a lo largo de los senderos del parque central]

**1. Dimensiones y Cotas Principales**:
- Altura total: [Ej. 0.85 m]
- Longitud / Ancho: [Ej. 1.80 m de largo x 0.65 m de profundidad]
- Huella de apoyo: [Ej. 4 patas de hierro fundido espaciadas 1.60 m x 0.50 m]

**2. Despiece Anatómico (De la base a la cima)**:
- [Elemento 1]: [Forma, espesor, curvaturas o molduras]
- [Elemento 2]: [Listones de madera, tornillería, refuerzos]
- [Elemento 3]: [Respaldar, emblema central del municipio, reposabrazos con volutas]

**3. Materiales y Pátina (Acabados del mundo real)**:
- Estructura metálica: [Ej. Hierro forjado negro satinado o verde colonial con bordes cobrizos]
- Elementos secundarios: [Ej. Madera de encino barnizada a la intemperie con desgaste en el asiento]

**4. Particularidades Locales de Tecate**:
- [Ej. Detalle del escudo "Tecate Pueblo Mágico", placa conmemorativa del Club Rotario, o remaches tradicionales]

**5. Fotografías de Referencia**:
- [Adjuntar 1 a 3 fotos tomadas de frente, en ángulo de 45° y detalle de los ornamentos]
```

### Protocolo de Ejecución del Agente para cada Asset
1. **Fase 1 - Script Paramétrico**: Crear un script en `scripts/generate_<nombre_asset>.py` utilizando primitivas `bmesh` y operaciones de torno/extrusión.
2. **Fase 2 - Guardado Maestro y Exports**: Guardar el `.blend` en `blender_assets/` y exportar el `.glb` modular a `godot_project/assets/`.
3. **Fase 3 - Render de Estudio**: Renderizar 3 a 4 vistas técnicas (general, acercamiento y detalles clave) a `docs/images/`.
4. **Fase 4 - Validación Visual**: Inspeccionar los renders con `view_file` para asegurar que las proporciones coinciden con las fotos reales de Tecate.
5. **Fase 5 - Documentación y Snippet de Motor**: Generar el documento técnico en `docs/<nombre_asset>.md` con tabla de cotas, slots de material y código de integración en Godot.
