# Arquitectura de Cadenas de Texto y Reglas Normativas: Tecate Simulator

> **Versión del Documento:** 1.0.0  
> **Estado:** Normativa Institucional Activa  
> **Ámbito:** Todo el código fuente de Godot (`godot_project/`), scripts de soporte y generadores  
> **Alineación:** Estándar Institucional de Cadenas y Calidad de Producción

---

## 1. Arquitectura de Centralización

### Única Fuente de Verdad (`Single Source of Truth`)
Todas las cadenas de texto del sistema (legibles por el usuario, técnicas, operativas y de registro) deben encontrarse estricta y obligatoriamente centralizadas en las siguientes clases canónicas dentro de `godot_project/systems/core/constants/`:

```
godot_project/systems/core/constants/app_strings.gd
godot_project/systems/core/constants/app_technical_strings.gd
godot_project/systems/core/constants/app_constants.gd
```

1. **`AppStrings` (`res://systems/core/constants/app_strings.gd`)**:
   - Centraliza todas las cadenas legibles por el usuario final y mensajes del simulador.
   - Declarado como `class_name AppStrings extends RefCounted`.
   - Incluye: títulos de pantalla, subtítulos, etiquetas de botones, menús de navegación, telemetría urbana del HUD (velocidad, altitud sobre el nivel del mar, pendiente, brújula y rumbos cardinales), textos de tarjetas de personajes, descripciones e identidades cívicas, nombres y reglas de minijuegos, diálogos e interacciones urbanas (asientos, bombas de gasolina, puertas), roles de vehículos (conductor, pasajero), distintivos de perspectiva (1P / 3P), mensajes de estado de red multijugador y avisos de contingencia legibles.

2. **`AppTechnicalStrings` (`res://systems/core/constants/app_technical_strings.gd`)**:
   - Centraliza todas las cadenas operativas, sintácticas y técnicas del motor.
   - Declarado como `class_name AppTechnicalStrings extends RefCounted`.
   - Incluye: rutas de recursos y escenas (`res://main.tscn`, `res://ui/...`), nombres de acciones de entrada del mapa de controles (`InputMap`: `move_forward`, `jump`, `interact`, `camera_toggle`, etc.), identificadores de capas físicas y máscaras de colisión, nombres de grupos de Godot (`players`, `vehicles`, `props`, `seats`), identificadores de nodos canónicos, nombres de animaciones de avatar, endpoints de red, extensiones de archivo (`.glb`, `.tscn`, `.tres`, `.png`, `.json`) y cabeceras de protocolo.

3. **`AppConstants` (`res://systems/core/constants/app_constants.gd`)**:
   - Expone la fachada canónica de constantes de alto nivel consumidas transversalmente por la aplicación, delegando directamente sus valores en `AppStrings` y `AppTechnicalStrings`.

---

### Regla Absoluta de Cero Cadenas Literales (`Zero Hardcoded Strings`)
Está **estrictamente prohibido** incrustar cualquier cadena de texto literal (*hardcoded string*) fuera de `app_strings.gd` y `app_technical_strings.gd` dentro de la base de código runtime de `godot_project/`.

Esta norma aplica **sin excepción alguna**, incluyendo:
1. **Cadenas Visibles para el Usuario**:
   - Títulos, subtítulos, etiquetas de botones (`Button.text`, `Label.text`, `RichTextLabel.bbcode_text`).
   - Textos de navegación, opciones del menú de inicio y menú de minijuegos.
   - Telemetría en pantalla (indicadores de velocidad, altitud, inclinación, orientación).
   - Prompts de interacción contextual (`"[E] Sentarse"`, `"[E] Subir al autobús"`).
   - Textos de estado de red (`"Conectando..."`, `"En línea"`).
   - Mensajes de confirmación, diálogos y notificaciones en pantalla.
2. **Cadenas Técnicas e Internas**:
   - Nombres de acciones de entrada pasados a `Input.is_action_pressed(...)` o `Input.is_action_just_pressed(...)`.
   - Nombres de grupos evaluados con `is_in_group(...)` o `add_to_group(...)`.
   - Nombres de animaciones pasados a `AnimationPlayer.play(...)`.
   - Rutas de escenas pasadas a `load(...)` o `change_scene_to_file(...)`.
   - Claves de diccionarios de configuración y persistencia local (`user://save.json`).

---

## 2. Reglas Normativas para las Cadenas de Texto

### 2.1. Puntuación y Capitalización de Oración en Español Estándar

1. **Prohibición Absoluta de *Title Case* Anglosajón**:
   En español estándar únicamente se escribe con mayúscula inicial la primera palabra de un texto, título, subtítulo, etiqueta o botón, además de los nombres propios y siglas reales (`Tecate`, `Cuchumá`, `Hidalgo`, `Juárez`, `BBVA`, `3D`, `HUD`, `km/h`, `snm`).
   - Está **estrictamente prohibido** capitalizar sustantivos y adjetivos intermedios como si fueran siglas (*Title Case*).
   - Los sustantivos comunes que designan vistas, secciones o elementos (*menú principal*, *minijuegos*, *ajustes*, *velocidad*, *altitud*, *cámara*) deben escribirse **siempre con minúscula inicial** cuando forman parte de una frase u oración.
   - *Correcto*: `"Selección de personaje"`, `"Pueblo Mágico y Social"`, `"Volver al menú principal"`, `"Vista en tercera persona"`, `"Cargar combustible"`
   - *Incorrecto*: `"Selección De Personaje"`, `"Volver Al Menú Principal"`, `"Vista En Tercera Persona"`, `"Cargar Combustible"`

2. **Mensajes, Descripciones, Avisos y Notificaciones**:
   Toda oración completa, descripción de personaje, regla de minijuego, mensaje explicativo o aviso en pantalla debe comenzar con mayúscula inicial, mantener capitalización normal de oración y finalizar obligatoriamente con un punto (`.`).
   - *Correcto*: `"Conexión establecida con el servidor de Tecate."`
   - *Incorrecto*: `"Conexión establecida con el servidor de Tecate"`
   - *Correcto*: `"El depósito de combustible ha sido llenado por completo."`
   - *Incorrecto*: `"el depósito de combustible ha sido llenado por completo"`

3. **Etiquetas, Botones, Títulos y Distintivos**:
   Los títulos de sección, nombres de pantallas, etiquetas de botones, elementos de menú, nombres de campos y distintivos de estado utilizan **exclusivamente capitalización de oración** (mayúscula solo en la primera letra y nombres propios) y **nunca** llevan punto final.
   - *Correcto*: `"Continuar"`, `"Reaparecer"`, `"Minijuegos"`, `"Salir"`, `"Confirmar selección"`, `"Conductor"`, `"Pasajero"`
   - *Incorrecto*: `"Continuar."`, `"reaparecer"`, `"Confirmar Selección"`, `"SALIR"`

---

### 2.2. Español Profesional y Eliminación de Anglicismos
Todas las cadenas visibles del simulador se expresan en un español claro, natural y formal. Se prohíbe el uso de anglicismos crudos o no adaptados en la interfaz de usuario:

| Anglicismo no permitido | Término estandarizado en Tecate Simulator | Justificación y Ámbito |
| :--- | :--- | :--- |
| *Singleplayer* | **Un jugador / Modo individual** | Modo de exploración en solitario. |
| *Multiplayer* | **Multijugador / En línea** | Módulo de red cívica compartida. |
| *Respawn* | **Reaparecer** | Acción de reubicar al avatar en el punto de inicio. |
| *Quit / Exit* | **Salir** | Salida del simulador. |
| *Settings* | **Ajustes / Configuración** | Menú de preferencias gráficas y sonoras. |
| *Score* | **Puntuación** | Puntos acumulados en minijuegos. |
| *Driver / Passenger* | **Conductor / Pasajero** | Roles dentro de autobuses y automóviles. |
| *Seat / Sit down* | **Asiento / Sentarse** | Interacción con mobiliario urbano y bancas. |
| *Fuel / Gas station* | **Combustible / Gasolinera** | Abastecimiento vehicular. |
| *First-person / Third-person* | **Vista subjetiva (1P) / Tercera persona (3P)** | Modos de cámara de exploración. |
| *Screenshot* | **Captura de pantalla** | Guardado de imágenes del entorno. |
| *Speed / Altitude / Slope* | **Velocidad / Altitud / Pendiente** | Telemetría urbana en la brújula y HUD. |

---

### 2.3. Prohibición de Desdoblamientos y Redundancias Léxicas
El lenguaje de la interfaz debe ser directo, económico y libre de pleonasmos:
- *Incorrecto*: `"Presiona la tecla E para sentarse en la banca o asiento urbano"` $\rightarrow$ *Correcto*: `"[E] Sentarse"`
- *Incorrecto*: `"Velocidad actual en kilómetros por hora"` $\rightarrow$ *Correcto*: `"Velocidad"`
- *Incorrecto*: `"Salir y cerrar el simulador por completo"` $\rightarrow$ *Correcto*: `"Salir"`

---

### 2.4. Opacidad Técnica (Principio de Caja Negra hacia el Usuario)
La interfaz de usuario **jamás debe desnudar la fontanería interna de Godot o del servidor**:
- Está **prohibido** mostrar al jugador identificadores internos de nodos (`@Node3D@142`), nombres de shaders (`res://shaders/water.gdshader`), puertos TCP/UDP crudos, llamadas RPC, estructuras de paquetes JSON ni nombres de variables internas.
- Los mensajes de error de red deben redactarse en lenguaje comprensible:
  - *Incorrecto*: `"Error: WebSocket peer disconnected with code 1006 - connection dropped"`
  - *Correcto*: `"Se interrumpió la conexión con el servidor. Reconectando..."`

---

### 2.5. Prohibición de Símbolos Embebidos en Cadenas
Está **estrictamente prohibido** incrustar glifos decorativos, viñetas o marcadores manuales (`•`, `+`, `➔`, `[X]`, emojis como separadores) dentro de las constantes de texto literales.
- **Justificación**: El estilo visual, márgenes, bordes e iconos pertenecen a la arquitectura de nodos de Godot (`TextureRect`, `StyleBoxFlat`, `Theme`, `HBoxContainer`).
- Los textos que requieran formato de tecla (como `[E]`) se estructuran mediante métodos formateadores en `AppStrings` o constantes de acción claras (`AppStrings.prompt_interact_action("E", AppStrings.PROMPT_SIT)`).

---

### 2.6. Extensión Normativa de Formato para Catálogos de Datos Dinámicos
Los catálogos (`CharacterCatalog`, `MinigameCatalog`, `manifest_edificios.json`):
1. **Nombres Propios y Títulos**: Sin punto final, capitalización de oración o nombres propios de identidad (`"Camarada"`, `"Axel"`, `"Diseñador"`, `"Eli"`).
2. **Descripciones y Reglas de Juego**: Oraciones completas con mayúscula inicial y punto final obligatorio (`.`).
3. **Frases y Saludos**: Deben contar con signos de puntuación de apertura y cierre en español (`¿...?`, `¡...!`).
   - *Correcto*: `"¿Cómo andamios? ¿Eh? Mal ahí."`
   - *Incorrecto*: `"Como andamios? Eh? Mal ahi"`

---

## 3. Patrones de Implementación en GDScript (Godot 4)

### 3.1. Constantes Estáticas vs. Métodos Parametrizados Tipados
1. **Cadenas Fijas (`const NOMBRE: String = "..."`)**:
   ```gdscript
   class_name AppStrings
   extends RefCounted

   const BTN_CONTINUE: String = "Continuar"
   const BTN_RESPAWN: String = "Reaparecer"
   const BTN_QUIT: String = "Salir"
   ```

2. **Cadenas Dinámicas con Parámetros (`static func nombre(...) -> String`)**:
   Cuando una cadena requiere interpolar números, nombres o rumbos, se define obligatoriamente como una función estática con tipado estricto:
   ```gdscript
   static func player_speed(speed_kmh: float) -> String:
       return "%4.1f km/h" % speed_kmh

   static func player_balance(pesos: int) -> String:
       return "%d pesos" % pesos

   static func compass_heading(deg: int, cardinal: String, street: String) -> String:
       return "%03d° %s  |  %s" % [deg, cardinal, street]
   ```

### 3.2. Consumo en Nodos de UI y Sistemas
Cualquier script en `godot_project/` tiene acceso inmediato a `AppStrings` y `AppTechnicalStrings` sin requerir `preload()`:
```gdscript
# En ui/start_screen.gd
btn_continue.text = AppStrings.BTN_CONTINUE
btn_respawn.text = AppStrings.BTN_RESPAWN
btn_quit.text = AppStrings.BTN_QUIT

# En ui/player_hud.gd
telemetry_label.text = "%s: %s\n%s: %s" % [
    AppStrings.HUD_SPEED, AppStrings.player_speed(speed),
    AppStrings.HUD_ALTITUDE, AppStrings.player_altitude(altitude)
]
```

---

## 4. Pipeline de Verificación y Auditoría Continua

1. **Auditor Estático en Python (`scripts/audit_hardcoded_strings.py`)**:
   - Analiza el código fuente GDScript detectando literales de texto no centralizados.
   - Se ejecuta en modo CLI y valida directorios clave con `--scope`.
   - Se integra en `scripts/release_local.sh` impidiendo generar binarios ante infracciones de cadenas.

2. **Suite de Pruebas en Godot Headless (`godot_project/tests/test_hardcoded_strings.gd`)**:
   - Valida la integridad de `AppStrings`, `AppTechnicalStrings` y `AppConstants`.
   - Comprueba que los módulos de UI respeten la política institucional.
   - Ejecutable en local y CI mediante:
     ```bash
     /Applications/Godot_mono.app/Contents/MacOS/Godot --headless --path godot_project -s res://tests/test_hardcoded_strings.gd --quit
     ```
