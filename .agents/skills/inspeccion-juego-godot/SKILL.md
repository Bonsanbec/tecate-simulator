---
name: inspeccion-juego-godot
description: >-
  Guía operativa y runbook para que el agente de IA interactúe de forma autónoma con Tecate Simulator
  en Godot 4 mediante el Cliente Deshidratado (scripts/game_cli.py). Permite inyectar inputs, teletransportar
  al avatar, validar mecánicas, físicas y UI, y obtener telemetría ultraligera y capturas bajo demanda.
---

# Inspección y Control Autónomo de Tecate Simulator (Godot 4)

Esta habilidad guía al agente en el uso del **Cliente Deshidratado**, una interfaz desacoplada de cero rastro en el código de producción que permite abrir el videojuego integralmente, controlarlo mediante comandos CLI y evaluar su comportamiento mecánico y visual.

---

## 1. Cuándo Activar esta Habilidad

Activa esta habilidad cuando modifiques o agregues:
- **Locomoción y Cinemática**: Saltos, aceleración, fricción, Foot IK o cámaras en `player_controller.gd` y `camera_director.gd`.
- **Colisiones Arquitectónicas y Terreno**: Integración de nuevos edificios procedurales o cambios en mallas de colisión para certificar caminabilidad peatonal a escasos centímetros de las fachadas sin muros invisibles.
- **Minijuegos**: Mecánicas de interacción, detección de zonas de actividad, aros de activación y puntuación.
- **Interfaz y HUD**: Menús de inicio, selección de personajes, barras de energía y tipografías.
- **Vehículos Urbanos**: Rutas de autobuses y paradas del transporte público.

---

## 2. Modalidades de Ejecución

### Modalidad A: Ejecución Atómica por Receta (One-Shot Batch)
Recomendada para comprobaciones rápidas de una sola acción.

```bash
# Probar locomoción y salto básico
python3 scripts/game_cli.py run --scenario scripts/scenarios/locomotion_walk_jump.json

# Probar aproximación frente a una fachada específica a mediodía
python3 scripts/game_cli.py run --teleport "-64.2,399.3,5.4" --inputs "move_forward:15:20" --hour 12.0 --capture-path "scratch/prueba_fachada.png"

# Inspeccionar menú de inicio sin cerrar StartScreen
python3 scripts/game_cli.py run --scenario scripts/scenarios/ui_hud_visual.json
```

### Modalidad B: Sesión Interactiva Continua (Daemon IPC)
Recomendada para depuración exploratoria en múltiples pasos sin pagar el tiempo de arranque en cada comando.

```bash
# 1. Iniciar el cliente deshidratado en segundo plano
python3 scripts/game_cli.py start --hour 12.0

# 2. Consultar estado y coordenadas actuales
python3 scripts/game_cli.py status

# 3. Teletransportar al jugador frente a un objetivo
python3 scripts/game_cli.py teleport -6.6844 400.3 11.0

# 4. Inyectar movimiento hacia adelante durante 1 segundo
python3 scripts/game_cli.py input move_forward --duration 1.0

# 5. Capturar imagen del viewport
python3 scripts/game_cli.py capture scratch/interactive_test.png

# 6. Detener limpiamente la sesión
python3 scripts/game_cli.py stop
```

---

## 3. Estrategia de Economía de Tokens

1. **Lectura Numérica Primero**:
   - Inspecciona únicamente la salida JSON en la terminal.
   - Si `status == "PASS"`, `is_on_floor == true`, y la posición alcanzada coincide con la cinemática calculada, la verificación mecánica está certificada.
2. **Puerta Visual Condicional**:
   - Invoca `read_file` sobre la captura PNG redimensionada (1024x576) **exclusivamente** si la tarea es de diseño visual (UI, HUD, materiales, shaders) o si la telemetría numérica muestra un comportamiento anómalo.
   - Prohibido cargar capturas completas en tareas donde los números ya otorgan certidumbre matemática.

---

## 4. Reglas Críticas Inviolables

1. **Cero Rastro en `godot_project/`**:
   - No crees ni edites archivos dentro de `godot_project/` para fines de inspección o asistencia por IA. Todo debe residir en `scripts/`, `scratch/` o `.agents/`.
2. **Cero Emojis y Cero AI Slop**:
   - Mantén los reportes con rigor técnico, concisos y con acentuación ortográfica completa.
