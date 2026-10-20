# Regla de Arquitectura de Cadenas y Cero Cadenas Literales: Tecate Simulator

## Ámbito y Obligatoriedad
Esta regla aplica a **todo el directorio `godot_project/`** y a cualquier generación o modificación de código GDScript, shaders, escenas `.tscn` o scripts de soporte dentro de **Tecate Simulator**. Debe cumplirse de manera estricta y sin excepciones.

Referencia normativa completa: `docs/strings.md`.

---

## 1. Regla Absoluta de Cero Cadenas Literales (`Zero Hardcoded Strings`)
Está **terminantemente prohibido** escribir cadenas de texto literales (*hardcoded strings*) dentro del código runtime de `godot_project/`.

Toda cadena debe obtenerse de:
1. **`AppStrings`** (`res://systems/core/constants/app_strings.gd`):
   - Todo texto legible por el usuario: títulos de pantalla, etiquetas de botones, telemetría urbana, brújula y rumbos cardinales, descripciones de personajes, reglas de minijuegos, prompts de interacción (`[E] Sentarse`, `[E] Subir`), distintivos de modo de cámara y mensajes legibles de red o excepciones.
2. **`AppTechnicalStrings`** (`res://systems/core/constants/app_technical_strings.gd`):
   - Toda constante técnica: rutas de recursos (`res://...`), nombres de acciones de entrada del `InputMap` (`move_forward`, `jump`, `interact`), capas físicas y máscaras de colisión, nombres de grupos (`players`, `vehicles`, `props`), nombres de nodos canónicos, animaciones y formatos de archivo.
3. **`AppConstants`** (`res://systems/core/constants/app_constants.gd`):
   - Fachada de constantes globales que delega directamente en `AppStrings` y `AppTechnicalStrings`.

Si se necesita un nuevo texto en la interfaz o una nueva constante técnica, **primero debe agregarse a `AppStrings` o `AppTechnicalStrings`** y luego consumirse en el código.

---

## 2. Reglas Normativas de Formato, Puntuación y Experiencia de Usuario

### 2.1 Puntuación y Capitalización de Oración
1. **Capitalización de Oración Obligatoria (Prohibido *Title Case*)**:
   - En español estándar solo se escribe con mayúscula inicial la primera palabra de la cadena y los nombres propios o siglas reales (`Tecate`, `Cuchumá`, `Hidalgo`, `Juárez`, `BBVA`, `3D`, `HUD`, `km/h`, `snm`).
   - Prohibido capitalizar sustantivos o palabras intermedias en títulos, botones o etiquetas.
   - Los sustantivos comunes de vistas o secciones (*menú principal*, *minijuegos*, *ajustes*, *velocidad*, *altitud*, *cámara*) van **siempre en minúscula** cuando forman parte de una frase.
2. **Oraciones, Notificaciones, Descripciones y Mensajes**:
   - Deben comenzar siempre con mayúscula, respetar capitalización de oración y **finalizar obligatoriamente con punto (`.`)**.
3. **Botones, Etiquetas, Títulos y Distintivos**:
   - Deben usar **exclusivamente capitalización de oración** y **nunca llevar punto final**.

### 2.2 Español Profesional y Cero Anglicismos en la Interfaz
Se prohíbe el uso de anglicismos crudos en la interfaz de usuario:
- *Singleplayer* $\rightarrow$ **Un jugador**
- *Multiplayer* $\rightarrow$ **Multijugador / En línea**
- *Respawn* $\rightarrow$ **Reaparecer**
- *Quit* $\rightarrow$ **Salir**
- *Settings* $\rightarrow$ **Ajustes**
- *Driver / Passenger* $\rightarrow$ **Conductor / Pasajero**
- *Seat / Sit* $\rightarrow$ **Asiento / Sentarse**
- *Fuel* $\rightarrow$ **Combustible**
- *First-person / Third-person* $\rightarrow$ **Vista subjetiva (1P) / Tercera persona (3P)**

### 2.3 Prohibición de Símbolos Visuales Embebidos
No incrustar viñetas decorativas, glifos ni caracteres decorativos (`•`, `+`, `➔`, `[X]`) en las cadenas de texto. El estilo visual pertenece a los nodos de Godot (`StyleBox`, `Theme`, `Icon`).

### 2.4 Opacidad Técnica (Caja Negra)
Ninguna cadena visible para el jugador debe desnudar la infraestructura interna del motor (rutas de shaders, nombres de nodos internos, códigos de error de bajo nivel o puertos TCP).
