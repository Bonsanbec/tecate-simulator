# Regla Mandatoria para Asistentes de IA: Erradicación del "AI Slop" en UI, UX y Textos

## Ámbito y Obligatoriedad
Esta regla aplica a **todos los asistentes de IA, agentes y desarrolladores** que interactúen con el repositorio de **Tecate Simulator**.
Aplica transversalmente a código en `godot_project/`, scripts en `scripts/`, herramientas en `tools/`, documentación en `docs/` y salidas por consola.

Referencia normativa maestra completa: [`docs/normativa_ui_ux_anti_ai_slop.md`](file:///Users/hakkindavid/Documents/GitHub/tecate-simulator/docs/normativa_ui_ux_anti_ai_slop.md).

---

## 1. Las Ocho Directivas Obligatorias Anti-AI Slop

1. **Cero Emojis Unicode en Cualquier Archivo:**
   - Queda estrictamente prohibido emitir caracteres de emoji (cohetes, chispas, bombillas, trofeos, mandos, palomitas, cruces) en código fuente, terminales, interfaces de usuario, marcadores 3D o documentación.
   - En consola/logs usar identificadores técnicos limpios: `[OK]`, `[ERROR]`, `[PASS]`, `[FAIL]`, `[WARN]`, `[INFO]`.
   - En interfaces usar tipografía condensada DIN, vectores SVG o dibujo procedural con `draw_rect()` / `draw_line()`.

2. **Cero Gradientes "VibeCode Purple" o Neón Abstracto:**
   - Prohibido recurrir a fondos oscuros genéricos con halos radiales púrpuras, índigos o magentas (`bg-indigo-500`, `#0f0f2d`).
   - Usar exclusivamente la paleta tangible y cívica de Tecate: Rojo Tecate oficial (`#D92626`), Gris Asfalto (`#141A21`), Hueso Cívico (`#F5F0E1`), Terracota Cuchumá (`#CC7340`) y Azul Metálico Hardware 2000s (`#0A1429`).

3. **Cero Chispas (*Sparkles*) ni Botones "Mágicos" Ambiguos:**
   - Prohibida la iconografía de chispas o metáforas mágicas.
   - Cada botón y acción debe indicar su verbo operativo concreto y determinista (`"Participar"`, `"Sentarse"`, `"Cargar combustible"`).

4. **Densidad de Información sobre Bento Grids Forzados:**
   - No forzar cuadrículas asimétricas de cajas redondeadas con poco contenido.
   - Diseñar interfaces operativas y densas orientadas a la simulación y la señalética urbana real.

5. **Alto Contraste y Rechazo al Glassmorphism Extremo:**
   - Prohibido apilar paneles translúcidos con fondos borrosos que reduzcan la legibilidad sobre el render 3D o impacten la tasa de cuadros por segundo.
   - Paneles sólidos con fondo oscuro (`Color(0.08, 0.10, 0.13, 0.85)`) y bordes de 1 a 2 píxeles con alto contraste.

6. **Voz Documental, Pragmática y Cero Porrismo RLHF:**
   - Prohibido el tono empalagoso, las exclamaciones artificiales (`¡Descubre la magia!`) y la jerga corporativa hueca (`"empoderar", "elevar", "seamless", "tapestry"`).
   - Mantener un tono sobrio, documental, directo y con habla local auténtica para personajes y diálogos.

7. **Centralización Absoluta de Textos (`Zero Hardcoded Strings`):**
   - Todo texto para el usuario debe residir en `AppStrings` (`res://systems/core/constants/app_strings.gd`).
   - Toda constante técnica debe residir en `AppTechnicalStrings` (`res://systems/core/constants/app_technical_strings.gd`).

8. **Español Riguroso, Cero Anglicismos y Acentuación Estricta:**
   - Capitalización de oración estándar (no *Title Case* anglosajón).
   - Acentuación ortográfica obligatoria en español estándar.

---

## 2. Comprobación Previa al Término de Cada Tarea

Antes de considerar concluida cualquier tarea que involucre UI, UX o textos, el asistente DEBE validar que:
1. No se haya introducido ningún emoji (auditoría con regex `[\U00010000-\U0010ffff]|[\u2600-\u27bf]|[\u2300-\u23ff]|[\u2b50-\u2b55]`).
2. La prueba de política de strings de Godot pase al 100%:
   ```bash
   /Applications/Godot_mono.app/Contents/MacOS/Godot --headless --log-file /tmp/godot.log --path godot_project -s tests/test_hardcoded_strings.gd
   ```
3. La auditoría de cadenas de texto no arroje violaciones:
   ```bash
   python3 scripts/audit_hardcoded_strings.py --scope ui
   ```
