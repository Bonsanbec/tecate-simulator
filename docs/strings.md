# Arquitectura de Cadenas de Texto y Reglas Normativas: Tecate Simulator

> **Versión del Documento:** 2.0.0  
> **Estado:** Normativa Institucional Activa  
> **Ámbito:** Todo el código fuente de Godot (`godot_project/`), scripts de soporte y generadores  
> **Alineación:** Estándar Institucional Estricto de Cadenas (Zero Hardcoded Strings)

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
   - Incluye: títulos de pantalla, subtítulos, etiquetas de botones, menús de navegación, telemetría urbana del HUD (velocidad, altitud sobre el nivel del mar, pendiente, brújula y rumbos cardinales), textos de tarjetas de personajes, descripciones e identidades cívicas, nombres y reglas de minijuegos, diálogos e interacciones urbanas (asientos, bombas de gasolina, puertas), roles de vehículos (conductor, pasajero), distintivos de perspectiva (vista subjetiva, tercera persona), mensajes de estado de red multijugador y avisos de contingencia legibles.

2. **`AppTechnicalStrings` (`res://systems/core/constants/app_technical_strings.gd`)**:
   - Centraliza todas las cadenas operativas, sintácticas y técnicas del motor.
   - Declarado como `class_name AppTechnicalStrings extends RefCounted`.
   - Incluye: rutas de recursos y escenas (`res://main.tscn`, `res://ui/...`), nombres de acciones de entrada del mapa de controles (`InputMap`: `move_forward`, `jump`, `interact`, `camera_toggle`, etc.), identificadores de capas físicas y máscaras de colisión, nombres de grupos de Godot (`players`, `vehicles`, `props`, `seats`), identificadores de nodos canónicos, nombres de animaciones de avatar, endpoints de red, extensiones de archivo (`.glb`, `.tscn`, `.tres`, `.png`, `.json`) y constantes de tema (`ThemeDB`, `StyleBox`).

3. **`AppConstants` (`res://systems/core/constants/app_constants.gd`)**:
   - Expone la fachada canónica de constantes de alto nivel consumidas transversalmente por la aplicación, delegando directamente sus valores en `AppStrings` y `AppTechnicalStrings`.

---

### Regla Absoluta de Cero Cadenas Literales (`Zero Hardcoded Strings`)
Está **estrictamente prohibido** incrustar cualquier cadena de texto literal (*hardcoded string*) fuera de `app_strings.gd` y `app_technical_strings.gd` dentro de la base de código runtime de `godot_project/`.

---

## 2. Reglas Normativas Rigurosas para las Cadenas de Texto

### 2.1. Puntuación y Prohibición de Mayúsculas Sostenidas (*ALL CAPS*) y *Title Case*

1. **Prohibición Absoluta de Mayúsculas Sostenidas (*ALL CAPS*)**:
   Está **estrictamente prohibido** redactar etiquetas, títulos, distintivos (*badges*), roles o telemetría en mayúsculas sostenidas:
   - *Incorrecto*: `"VELOCIDAD"`, `"ALTITUD"`, `"PENDIENTE"`, `"COMBUSTIBLE"`, `"SUPERFICIE"`, `"50 PESOS"`, `"CONDUCTOR"`, `"PASAJERO"`, `"MODO FIESTA"`, `"TODOS CONTRA TODOS"`, `"1 CONTRA TODOS"`
   - *Correcto*: `"Velocidad"`, `"Altitud"`, `"Pendiente"`, `"Combustible"`, `"Superficie"`, `"50 pesos"`, `"Conductor"`, `"Pasajero"`, `"Modo fiesta"`, `"Todos contra todos"`, `"Uno contra todos"`
   - **Excepción única**: Siglas reconocidas e invariables (`BBVA`, `3D`, `HUD`, `snm`).

2. **Prohibición Absoluta de *Title Case* Anglosajón**:
   En español estándar únicamente se escribe con mayúscula inicial la primera palabra de un texto, título, subtítulo, etiqueta o botón, además de los nombres propios y siglas reales.
   - *Correcto*: `"Selección de personaje"`, `"Pueblo Mágico y Social"`, `"Volver al menú principal"`, `"Vista en tercera persona"`
   - *Incorrecto*: `"Selección De Personaje"`, `"Volver Al Menú Principal"`, `"Vista En Tercera Persona"`

3. **Mensajes, Descripciones, Avisos y Notificaciones**:
   Toda oración completa, descripción de personaje, regla de minijuego, mensaje explicativo o aviso en pantalla debe comenzar con mayúscula inicial, mantener capitalización normal de oración y finalizar obligatoriamente con un punto (`.`).
   - *Correcto*: `"Conexión establecida con el servidor de Tecate."`
   - *Incorrecto*: `"Conexión establecida con el servidor de Tecate"`

4. **Etiquetas, Botones, Títulos y Distintivos**:
   Los títulos de sección, nombres de pantallas, etiquetas de botones, elementos de menú, nombres de campos y distintivos de estado utilizan **exclusivamente capitalización de oración** y **nunca** llevan punto final.
   - *Correcto*: `"Continuar"`, `"Reaparecer"`, `"Minijuegos"`, `"Salir"`, `"Confirmar selección"`
   - *Incorrecto*: `"Continuar."`, `"reaparecer"`, `"Confirmar Selección"`

---

### 2.2. Prohibición Absoluta de Corchetes `[...]` y Teclas Embebidas en las Cadenas
Está **terminantemente prohibido** incrustar corchetes (`[` y `]`) o nombres de teclas físicas directamente en las constantes de texto del sistema:
- **Justificación**: Las asignaciones de teclas son configurables por el usuario y los glifos de tecla pertenecen a los componentes gráficos de la interfaz (botones de control, iconos de gamepad o etiquetas de atajo desacopladas). Incrustar corchetes rompe la localización y acopla la interfaz a una configuración fija.
- Las constantes deben representar exclusivamente la acción semántica:
  - *Incorrecto*: `"[E] Sentarse"`, `"[E] Levantarse"`, `"[E] Subir al autobús"`, `"[R] Repostar"`, `"[Ctrl] Cambiar Asiento"`
  - *Correcto*: `"Sentarse"`, `"Levantarse"`, `"Subir al autobús"`, `"Cargar combustible"`, `"Cambiar de asiento"`
- Los formateadores de prompt combinan dinámicamente la acción con el contexto sin incrustar corchetes crudos en la constante.

---

### 2.3. Prohibición Absoluta de Barras Inclinadas (*Slashes* `/`)
Está **terminantemente prohibido** utilizar barras inclinadas (`/`) como cópulas, disyunciones o atajos léxicos en textos dirigidos al usuario:
- En español estándar se deben utilizar las conjunciones naturales (`y`, `o`):
  - *Incorrecto*: `"Hacia La Rumorosa / Mexicali"` $\rightarrow$ *Correcto*: `"Hacia La Rumorosa y Mexicali"`
  - *Incorrecto*: `"Hacia el Cerro Cuchumá / Tijuana"` $\rightarrow$ *Correcto*: `"Hacia el Cerro Cuchumá y Tijuana"`
  - *Incorrecto*: `"Hacia Ensenada / Valle de Guadalupe"` $\rightarrow$ *Correcto*: `"Hacia Ensenada y el Valle de Guadalupe"`
  - *Incorrecto*: `"Hacia la Frontera / USA"` $\rightarrow$ *Correcto*: `"Hacia la frontera norte"`
  - *Incorrecto*: `"[V / F5]"` $\rightarrow$ *Correcto*: Separación gráfica en la interfaz o mención textual limpia.
- **Excepción técnica estricta**: Unidades de medida científicas estandarizadas del Sistema Internacional (`km/h`).

---

### 2.4. Prohibición Absoluta de Paréntesis `(...)` y Explicaciones Embebidas
Se prohíbe el uso de paréntesis explicativos innecesarios `(...)` y aclaraciones redundantes en las cadenas de texto:
- *Incorrecto*: `"∞ (Ruta)"` $\rightarrow$ *Correcto*: `"Ilimitado"` o `"Ruta continua"`
- *Incorrecto*: `"%s (Lleno)"` $\rightarrow$ *Correcto*: `"%s lleno"`
- *Incorrecto*: `"1P - Vista Subjetiva"` $\rightarrow$ *Correcto*: `"Vista subjetiva"`
- *Incorrecto*: `"3P - Vista Cercana"` $\rightarrow$ *Correcto*: `"Vista en tercera persona"`
- *Incorrecto*: `"Duelo y Mesa (1 vs. 1)"` $\rightarrow$ *Correcto*: `"Duelo individual"`
- *Incorrecto*: `"Vehículo en marcha (%.0f km/h)"` $\rightarrow$ *Correcto*: `"Vehículo en marcha a %.0f km/h"`

---

### 2.5. Prohibición Absoluta de Símbolos, Emojis y Caracteres Decorativos Embebidos
Está **estrictamente prohibido** incrustar glifos decorativos, viñetas, símbolos matemáticos no funcionales o emojis (`∞`, `🪙`, `•`, `➔`, `+`, `#`, `|`) dentro de las cadenas de texto:
- **Infinito (`∞`)**: Prohibido en cadenas de interfaz. Usar palabras funcionales (`"Ilimitado"`, `"Ruta continua"`).
- **Emojis (`🪙`)**: Prohibidos en cadenas de texto. Las monedas e iconos son nodos `TextureRect` o fuentes de iconos dedicadas.
- **Viñetas (`•`) y Pleonasmos**:
  - *Incorrecto*: `"Zona Centro • Tecate, Pueblo Mágico"`
  - *Correcto*: `"Zona Centro, Tecate"`
- **Separadores decorativos (`|`)**: Las barras verticales pertenecen al layout visual (`VSeparator`, `HBoxContainer`), no a los literales de texto.

---

### 2.6. Español Profesional y Cero Anglicismos en la Interfaz
Todas las cadenas visibles del simulador se expresan en un español claro, natural y formal:

| Anglicismo o término no permitido | Término estandarizado en Tecate Simulator | Ámbito |
| :--- | :--- | :--- |
| *Singleplayer* | **Un jugador / Modo individual** | Modo de exploración en solitario. |
| *Multiplayer* | **Multijugador / En línea** | Módulo de red cívica compartida. |
| *Respawn* | **Reaparecer** | Reubicación del avatar. |
| *Quit / Exit* | **Salir** | Salida del simulador. |
| *Settings* | **Ajustes / Configuración** | Menú de preferencias. |
| *Score* | **Puntuación** | Puntos en minijuegos. |
| *Driver / Passenger* | **Conductor / Pasajero** | Roles vehiculares. |
| *Seat / Sit down* | **Asiento / Sentarse** | Interacción con mobiliario. |
| *Fuel / Gas station* | **Combustible / Gasolinera** | Abastecimiento vehicular. |
| *First-person / Third-person* | **Vista subjetiva / Tercera persona** | Modos de cámara de exploración. |
| *Speed / Altitude / Slope* | **Velocidad / Altitud / Pendiente** | Telemetría urbana en la brújula y HUD. |

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
   const PROMPT_SIT: String = "Sentarse"
   const HUD_SPEED: String = "Velocidad"
   ```

2. **Cadenas Dinámicas con Parámetros (`static func nombre(...) -> String`)**:
   ```gdscript
   static func player_speed(speed_kmh: float) -> String:
       return "%4.1f %s" % [speed_kmh, HUD_UNIT_KMH]

   static func player_balance(pesos: int) -> String:
       return "%d pesos" % pesos

   static func prompt_sit_in(seat_name: String) -> String:
       return "Sentarse en %s" % seat_name
   ```

---

## 4. Pipeline de Verificación y Auditoría Continua

1. **Auditor Estático en Python (`scripts/audit_hardcoded_strings.py`)**:
   - Valida la ausencia de cadenas crudas no centralizadas.
   - Valida la ausencia de corchetes `[...]`, slashes `/`, paréntesis `(...)`, símbolos decorativos (`∞`, `🪙`, `•`) y mayúsculas sostenidas (*ALL CAPS*) en textos legibles por el usuario.

2. **Suite de Pruebas en Godot Headless (`godot_project/tests/test_hardcoded_strings.gd`)**:
   - Comprueba mediante aserciones unitarias que ninguna cadena de `AppStrings` contenga corchetes, slashes no autorizados, mayúsculas sostenidas ni paréntesis.
