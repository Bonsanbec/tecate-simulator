# Normativa Institucional de UI, UX y Redacción: Erradicación Absoluta del "AI Slop"

> **Código:** NORM-UI-UX-003  
> **Estado:** Vigente y Obligatorio para Todo Desarrollador y Asistente de IA  
> **Ámbito de Aplicación:** Toda la interfaz de usuario (`godot_project/ui/`), menús, telemetría del HUD, dispositivos diegéticos (celular), prompts de interacción, cadenas de texto (`AppStrings`), documentación técnica y consolas de registro.  
> **Fundamentación Teórica:** Investigación referenciada en HCI y análisis de diseño de interfaces contemporáneas (Nielsen Norman Group, Jim Nielsen, UX Collective, Smashing Magazine).

---

## 1. Manifiesto: Identidad Cívica y Rechazo Frontal al "AI Slop"

Tecate Simulator es una recreación arquitectónica, histórica, social y cívica de Tecate, Baja California, anclada en la realidad física, topográfica y cotidiana de un municipio fronterizo mexicano (años 2000–2009). 

El fenómeno conocido en la industria como **"AI Slop"** (diseño genérico generado algorítmicamente sin criterio de producto ni anclaje contextual) degrada el software mediante soluciones prefabricadas que imitan dashboards SaaS de Silicon Valley. Este tipo de estéticas rompen la inmersión, despersonalizan el proyecto y crean una barrera artificial entre el jugador y el entorno urbano.

En Tecate Simulator, la interfaz no es una vitrina abstracta de internet: es una extensión táctil, diegética y documental de la ciudad.

---

## 2. Investigación Referenciada: Diagnóstico del "AI Slop" en Interfaces

Las siguientes patologías visuales y textuales han sido tipificadas a partir de la literatura de diseño actual:

### 2.1. El Cliché de las Chispas (*Sparkles*) y Emojis Descontextualizados
* **Referencia:** Jim Nielsen (2026), *"The AI Aesthetic"*; Nielsen Norman Group (NN/g, 2024–2026), *"Intent-Based Interactions and Icon Ambiguity"*.
* **El Problema:** La inclusión del glifo de cuatro puntas (chispas) o emojis Unicode (cohetes, bombillas, chinchetas, trofeos, mandos de videojuegos, pines de mapa) como sustituto de iconografía real o tipografía estructurada destruye la especificidad de las *affordances*. En videojuegos, un emoji renderizado por el sistema operativo huésped (Apple Color Emoji vs. Microsoft Fluent vs. Linux tofu glyphs) produce fragmentación visual, rompe la línea base (*baseline*) de fuentes técnicas como DIN Condensed y destruye la suspensión de incredulidad (*diegetic pact*).

### 2.2. La Paleta "VibeCode Purple" y Gradientes Radiales Etéreos
* **Referencia:** *Dev.to / SmoothUI Design Review* (2025–2026), *"The Purple Dark Mode Plague"*.
* **El Problema:** El uso indiscriminado de fondos oscuros con halos violetas, índigos o magentas (`bg-indigo-500`, `#0f0f2d`) como recurso fácil para hacer que una pantalla luzca "futurista". En Tecate Simulator, este patrón disfraza la falta de jerarquía y no guarda relación alguna con la geografía semiárida del Cuchumá, el asfalto municipal o la identidad cívica bajacaliforniana.

### 2.3. Cuadrículas "Bento" Forzadas y *Glassmorphism* sin Contraste
* **Referencia:** *UX Collective / DevelopersDigest* (2025–2026), *"Bento Grids: Form Without Intent"*.
* **El Problema:** Dividir pantallas mecánicamente en tarjetas rectangulares redondeadas (`rounded-2xl`) con dos líneas de texto y un icono decorativo, ignorando la densidad de datos requerida para telemetría vehicular o navegación urbana. Acompañado de efectos de desenfoque de fondo (`backdrop-filter: blur`), genera caídas de rendimiento en el renderizador 3D y viola los estándares de contraste accesible (WCAG).

### 2.4. Redacción Complaciente y Porrismo Corporativo (*RLHF Cheerleading*)
* **Referencia:** *Whyy / Oxford University / Fast Company*, *"The Telltale Signs of AI Copywriting"*.
* **El Problema:** Los modelos entrenados con retroalimentación humana tienden por defecto a una hiper-cortesía artificial y un optimismo corporativo empalagoso (*"¡Descubre la magia de Tecate!", "¡Potencia tu viaje!", "¡Excelente trabajo!"*), repleto de listas encabezadas por emojis y simetrías gramaticales artificiales ("Regla de tres", "No solo... sino también...").

---

## 3. Las Ocho Reglas de Oro Anti-AI Slop para Tecate Simulator

Cualquier código, interfaz, recurso o texto incorporado por asistentes de IA o desarrolladores DEBE cumplir taxativamente las siguientes directivas:

### Regla 1: Cero Emojis en Cualquier Capa del Sistema
* **Prohibición:** Queda terminantemente prohibido el uso de caracteres Unicode de emojis (`\U00010000-\U0010ffff`, `\u2600-\u27bf`, etc.) en etiquetas de UI, botones, menús, marcadores 3D, cadenas de texto, mensajes de depuración, consolas o documentación.
* **Alternativa Aprobada:** 
  - Para telemetría y estado: Métrica limpia o dibujo procedural 2D con `draw_rect()` / `draw_line()` (ej. barras de señal GSM y contorno de batería en el celular).
  - Para acciones de hardware: Rotulado textual en mayúsculas sobrias grabado en DIN (ej. `"SEND"`, `"END"`, `"OK"`).
  - Para listas y categorías: Rótulos tipográficos directos (`"Retas"`, `"Mensajes"`, `"Ubicación: %s"`).

### Regla 2: Prohibición de Gradientes Púrpura/Índigo Genéricos
* **Prohibición:** Ningún componente o panel debe utilizar gradientes abstractos morados, fucsias, violetas o púrpuras.
* **Paleta Oficial de Tecate:**
  - **Rojo Tecate (Oficial):** `Color(0.85, 0.16, 0.16)` (`#D92626`).
  - **Arena / Hueso Cívico:** `Color(0.96, 0.94, 0.88)` (`#F5F0E1`).
  - **Terracota Cuchumá:** `Color(0.80, 0.45, 0.25)` (`#CC7340`).
  - **Gris Asfalto / Chasis:** `Color(0.08, 0.10, 0.13)` (`#141A21`).
  - **Azul Metálico Motorola (Hardware 2000s):** `Color(0.04, 0.08, 0.16)` (`#0A1429`) con acento cian fósforo `Color(0.0, 0.85, 1.0)`.
  - **Verde Pueblo Mágico:** `Color(0.12, 0.65, 0.28)` (`#1FA647`).

### Regla 3: Cero Chispas (*Sparkles*) e Iconografía Mágica Ambigua
* **Prohibición:** No existen botones "mágicos", filtros con chispas ni asistentes flotantes de oficina.
* **Alternativa Aprobada:** Cada acción de interacción describe con exactitud su verbo funcional (`"Participar"`, `"Sentarse"`, `"Abordar autobús"`, `"Ir al lugar"`).

### Regla 4: Densidad de Datos y Jerarquía sobre Grillas "Bento" Estériles
* **Prohibición:** No fragmentar menús ni telemetría en cajas vacías que requieran scroll o dispersen la atención.
* **Alternativa Aprobada:** Interfaces operativas, compactas y estructuradas según estándares de señalética vial y tableros vehiculares reales.

### Regla 5: Rechazo al Glassmorphism Extremo sin Alto Contraste
* **Prohibición:** No apilar paneles translúcidos con fondos borrosos sobre la vista 3D si reducen la legibilidad o comprometen el framerate.
* **Alternativa Aprobada:** Cajas sólidas o con opacidad mínima del 85% (`Color(0.08, 0.10, 0.13, 0.85)`), con bordes contrastantes de 1 o 2 píxeles en el color de acento.

### Regla 6: Voz Cívica, Pragmática y Cero Porrismo RLHF
* **Prohibición:** Cero signos de exclamación artificiales (`¡!`), cero adulación barata (*"¡Fantástico!"*), cero verbos huecos (*"empoderar", "elevar", "sumergirse en la magia"*).
* **Tono Oficial:** Sobrio, directo, institucional y documental. En diálogos y personajes, reflejar el habla real y desenfadada de Tecate (ej. Camarada Axel: *"¿Cómo andamios? ¿Eh? Mal ahí."*), sin imposturas de chatbot de atención al cliente.

### Regla 7: Única Fuente de Verdad para Textos (`Zero Hardcoded Strings`)
* **Prohibición:** Queda terminantemente prohibido escribir cadenas de texto literales crudas fuera de `app_strings.gd` y `app_technical_strings.gd`.
* **Alternativa Aprobada:** Toda etiqueta, rol, telemetría o prompt debe provenir de `AppStrings` o formularse mediante métodos estáticos tipados (ej. `AppStrings.format_currency_pesos()`).

### Regla 8: Ortografía Rigurosa y Cero Anglicismos en UI
* **Prohibición:** No usar términos como *singleplayer*, *multiplayer*, *score*, *driver*, *spawn*, ni *Title Case* anglosajón.
* **Alternativa Aprobada:** Mayúscula únicamente en la primera palabra de oraciones y títulos; acentuación ortográfica completa y obligatoria (`Selección de personaje`, `Brújula`, `Configuración`).

---

## 4. Pipeline de Verificación Automatizada

Todo pull request, commit o intervención de IA se somete a tres filtros de validación continua:

1. **Auditoría de Cero Emojis (Python AST/Regex):**
   ```bash
   python3 -c "
   import os, re, sys
   pattern = re.compile(r'[\U00010000-\U0010ffff]|[\u2600-\u27bf]|[\u2300-\u23ff]|[\u2b50-\u2b55]')
   for root, _, files in os.walk('godot_project'):
       for f in files:
           if f.endswith(('.gd', '.tscn', '.tres', '.json')):
               with open(os.path.join(root, f), 'r', encoding='utf-8') as h:
                   for idx, line in enumerate(h, 1):
                       if pattern.findall(line):
                           print(f'[VIOLACIÓN] {f}:{idx} -> Emoji detectado')
                           sys.exit(1)
   print('[OK] Cero emojis en godot_project.')
   "
   ```

2. **Auditoría de Cadenas de Texto Literales:**
   ```bash
   python3 scripts/audit_hardcoded_strings.py --scope ui
   ```

3. **Suite de Pruebas en Godot Headless:**
   ```bash
   /Applications/Godot_mono.app/Contents/MacOS/Godot --headless --log-file /tmp/godot.log --path godot_project -s tests/test_hardcoded_strings.gd
   ```
