# Regla de Arquitectura de Cadenas y Cero Cadenas Literales: Tecate Simulator

## Ámbito y Obligatoriedad
Esta regla aplica a **todo el directorio `godot_project/`** y a cualquier generación o modificación de código GDScript, shaders, escenas `.tscn` o scripts de soporte dentro de **Tecate Simulator**. Debe cumplirse de manera estricta y sin excepciones.

Referencia normativa completa: `docs/strings.md`.

---

## 1. Regla Absoluta de Cero Cadenas Literales (`Zero Hardcoded Strings`)
Está **terminantemente prohibido** escribir cadenas de texto literales (*hardcoded strings*) dentro del código runtime de `godot_project/`.

Toda cadena debe obtenerse de:
1. **`AppStrings`** (`res://systems/core/constants/app_strings.gd`):
   - Todo texto legible por el usuario: títulos de pantalla, etiquetas de botones, telemetría urbana, brújula y rumbos cardinales, descripciones de personajes, reglas de minijuegos, prompts de interacción, distintivos de modo de cámara y mensajes legibles de red.
2. **`AppTechnicalStrings`** (`res://systems/core/constants/app_technical_strings.gd`):
   - Toda constante técnica: rutas de recursos (`res://...`), nombres de acciones de entrada del `InputMap` (`move_forward`, `jump`, `interact`), capas físicas y máscaras de colisión, nombres de grupos (`players`, `vehicles`, `props`), nombres de nodos canónicos, animaciones y formatos de archivo.
3. **`AppConstants`** (`res://systems/core/constants/app_constants.gd`):
   - Fachada de constantes globales que delega directamente en `AppStrings` y `AppTechnicalStrings`.

---

## 2. Normas de Formato Estricto y Prohibiciones Absolutas

1. **Prohibición Absoluta de Mayúsculas Sostenidas (*ALL CAPS*)**:
   - Prohibido redactar textos en mayúsculas sostenidas (`VELOCIDAD`, `ALTITUD`, `PENDIENTE`, `COMBUSTIBLE`, `50 PESOS`, `CONDUCTOR`, `PASAJERO`, `MODO FIESTA`).
   - Usar estrictamente capitalización de oración: `"Velocidad"`, `"Altitud"`, `"Pendiente"`, `"Combustible"`, `"50 pesos"`, `"Conductor"`, `"Pasajero"`, `"Modo fiesta"`.

2. **Prohibición Absoluta de Corchetes `[...]` y Teclas Embebidas**:
   - Prohibido incrustar corchetes (`[` y `]`) o nombres de teclas en las cadenas de texto (`[E]`, `[R]`, `[Ctrl]`, `[B / T]`, `[Espacio]`).
   - Las constantes de prompt deben contener únicamente la acción semántica: `"Sentarse"`, `"Levantarse"`, `"Cargar combustible"`, `"Solicitar parada"`, `"Cambiar de asiento"`.

3. **Prohibición Absoluta de Barras Inclinadas (*Slashes* `/`)**:
   - Prohibido usar `/` como alternativa o enlace en textos de cara al usuario.
   - Usar conjunciones en español (`"Hacia La Rumorosa y Mexicali"`, no `"La Rumorosa / Mexicali"`).
   - Excepción técnica única: unidades del SI estandarizadas (`km/h`).

4. **Prohibición Absoluta de Paréntesis `(...)` y Explicaciones Embebidas**:
   - Prohibido usar paréntesis explicativos o aclaraciones innecesarias:
   - Prohibido: `"∞ (Ruta)"`, `"%s (Lleno)"`, `"1P - Vista Subjetiva"`, `"Duelo y Mesa (1 vs. 1)"`.
   - Correcto: `"Ilimitado"`, `"%s lleno"`, `"Vista subjetiva"`, `"Duelo individual"`.

5. **Prohibición Absoluta de Símbolos, Emojis y Glifos Decorativos Embebidos**:
   - Prohibido incrustar el símbolo de infinito (`∞`), emojis, viñetas (`•`), flechas o barras decorativas (`|`) en las constantes de texto.
   - El estilo visual, iconos y separadores pertenecen a la jerarquía de nodos de Godot (`TextureRect`, `VSeparator`, `Theme`).
