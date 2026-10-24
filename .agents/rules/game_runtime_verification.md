# Protocolo Obligatorio de Verificación Autónoma en Runtime para Tecate Simulator

## Propósito y Alcance
Esta regla establece el estándar universal para que todo agente de inteligencia artificial en **Antigravity** evalúe y valide de forma autónoma, fidedigna y con estricta economía de tokens los cambios efectuados sobre el videojuego Tecate Simulator mediante el **Cliente Deshidratado** (`scripts/game_cli.py`).

Queda terminantemente prohibido dar por concluida una tarea de desarrollo de complejidad media o alta sin haber ejecutado la verificación en tiempo de ejecución (*runtime*) y haber obtenido telemetría estructurada confirmando el éxito.

---

## 1. Matriz de Criticidad y Criterio de Discernimiento Autónomo

Antes de concluir una tarea, el agente debe clasificar el impacto del cambio según la siguiente matriz:

| Nivel de Criticidad | Áreas y Componentes Afectados | Obligación de Verificación en Runtime | Tipo de Verificación Requerida |
| :--- | :--- | :--- | :--- |
| **Alta Complejidad** | Locomoción de jugador (`player_controller.gd`), cámaras (`camera_director.gd`), colisiones de edificios/terreno, cinemática de vehículos, minijuegos, shaders y menús HUD. | **Obligatoria e Ineludible** | Telemetría en JSON (`status: PASS`, coordenadas y físicas) **y** captura visual (`read_file`) para inspección de proporciones, oclusión y artefactos. |
| **Media Complejidad** | Rutas viales, waypoints de autobuses, ajustes de velocidad/fricción de avatares, lógica de red multijugador offline. | **Obligatoria** | Telemetría en JSON primero. Si la telemetría confirma convergencia física (`is_on_floor: true`, posición esperada sin errores), la captura visual es opcional. |
| **Baja Complejidad** | Corrección de erratas en `app_strings.gd`, constantes técnicas aisladas en `app_technical_strings.gd`, documentación en `docs/`, scripts analíticos puros en `scripts/` (ej. parsers OSM). | **Exenta** | No requiere abrir el motor de juego. Basta con ejecutar la suite de auditoría estática (`audit_hardcoded_strings.py`). |

---

## 2. Protocolo de Ahorro Extremo de Tokens (Telemetría Primero)

Para preservar la ventana de contexto y evitar el desperdicio de tokens de ida y vuelta:

1. **Paso 1: Validación Numérica Compacta**:
   - Ejecutar la prueba mediante `scripts/game_cli.py run --scenario [receta.json]`.
   - Analizar la salida `TELEMETRY_JSON`. El reporte contiene únicamente las métricas esenciales:
     ```json
     {"status": "PASS", "player_pos": [-6.68, 400.2, 11.0], "is_on_floor": true, "fps": 55.0}
     ```
   - Este paso consume menos de 60 tokens en el contexto.

2. **Paso 2: Puerta Visual Condicional (*Visual Gate*)**:
   - Solo se debe invocar la lectura de imagen (`read_file` sobre el archivo `.png` generado) cuando:
     a) La tarea involucre aspectos visuales o estéticos (UI, HUD, materiales, shaders, iluminación diurna/nocturna).
     b) La telemetría numérica revele anomalías (ej. jugador cayendo al vacío $Y < 350$, velocidad desmedida o colisión no detectada).
   - En tareas puramente mecánicas donde la telemetría confirme el resultado esperado, **no** se debe cargar la imagen en contexto.

---

## 3. Principio de Cero Rastro en el Código de Producción

1. **Aislamiento Absoluto de `godot_project/`**:
   - Queda estrictamente prohibido introducir scripts de prueba, conectores de IA o puertas traseras de depuración dentro del árbol de `godot_project/`.
   - Toda interacción se realiza mediante el runner externo `scripts/desiccated_client_runner.gd` ejecutado a través de `scripts/game_cli.py`.
2. **Preservación de la Pureza para los Usuarios Finales**:
   - Las exportaciones del juego no deben incluir ningún rastro de automatización ni de asistencia por IA.

---

## 4. Ciclo Closed-Loop de Diagnóstico y Corrección

Si la telemetría reporta `status: ERROR` o si la captura visual revela clipping, desconexión de geometrías o inversión de rótulos:
1. El agente debe diagnosticar la discrepancia matemática o cinemática en el código fuente correspondiente.
2. Aplicar la corrección precisa.
3. Volver a ejecutar `scripts/game_cli.py` para contrastar empíricamente que el defecto fue resuelto.
4. Adjuntar la telemetría final en el reporte de entrega.
