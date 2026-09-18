# Especificación y Documentación Técnica: Poste de Nomenclatura Urbana Clásica de Tecate, B.C.

Este documento detalla el diseño, modelado paramétrico 3D, materiales PBR y guía de integración en motor (Godot Engine 4) del **Poste de Nomenclatura Urbana Clásica de Tecate**, un elemento de mobiliario urbano tradicional diseñado para ubicarse en las intersecciones y esquinas de manzanas en el simulador.

---

## 1. Contexto Urbano e Histórico

En el centro histórico y primer cuadro de la ciudad de Tecate, Baja California (Pueblo Mágico), la señalización vial vertical de las esquinas se caracteriza por postes esbeltos de fundición de hierro rematados por dos placas en cruz perpendicular (90° entre sí). 

### Rasgos Distintivos de Tecate
1. **Doble placa escalonada en escuadra**: Las dos placas comparten el mismo molde de fundición pero se encuentran desfasadas verticalmente por 10 cm para permitir el cruce visual sin obstrucciones desde cualquier ángulo vial.
2. **Crestería heráldica semicircular asimétrica**: En la parte superior izquierda de cada placa sobresale un semicírculo en arco de medio punto destinado históricamente al escudo municipal y distrito ("17").
3. **Composición asimétrica 2/3 y 1/3**: Las placas se subdividen mediante un filete vertical en relieve que separa el nombre principal de la vialidad (2/3 izquierdos) del recuadro complementario para Código Postal y Colonia (1/3 derecho).
4. **Pátina y materiales tradicionales**: Fuste de hierro fundido gris grafito/plomo oscuro envejecido, con placas de bronce/cobre patinado a la intemperie (verde cardenillo) y relieves desgastados en tono latón/bronce erosionado.

---

## 2. Renders Técnicos de Inspección

| Vista General (2.95 m) | Acercamiento a Placas | Base / Pedestal |
| :---: | :---: | :---: |
| ![Vista General](images/poste_nomenclatura_preview.png) | ![Detalle Placas](images/poste_nomenclatura_closeup.png) | ![Detalle Pedestal](images/poste_nomenclatura_base.png) |

---

## 3. Jerarquía Espacial y Desglose Geométrico

El modelo ha sido construido a escala métrica real 1:1, con su punto de pivote en el origen absoluto $(0, 0, 0)$ coincidente con la base de apoyo en el suelo, permitiendo colocarlo directamente sobre banquetas o esquinas de manzanas sin ajustes manuales de compensación en $Z$.

```
Poste_Nomenclatura_Tecate (Colección Raíz)
 ├── Poste_Estructura (Hierro Fundido, Malla de Revolución y Herrajes)
 │    ├── Placa_Inferior (Eje X / Transversal, Z_centro = 2.64 m)
 │    └── Placa_Superior (Eje Y / Frontal, 90°, Z_centro = 2.74 m)
 └── [Opcional] Texto_Demostracion_Ejemplo (Colección aislada con textos 3D)
```

### Tabla de Cotas y Dimensiones

| Componente | Altura / Rango $Z$ | Diámetro / Dimensiones | Características Principales |
| :--- | :--- | :--- | :--- |
| **Anillo de suelo** | $0.00 \to 0.04\text{ m}$ | $\varnothing\ 0.32\text{ m}$ | Cilindro achatado con bisel perimetral superior hacia $\varnothing\ 0.28\text{ m}$. |
| **Cuerpo de campana** | $0.04 \to 0.34\text{ m}$ | $\varnothing\ 0.28 \to \varnothing\ 0.11\text{ m}$ | Transición cóncava hiperbólica con 16 facetas radiales suaves de molde. |
| **Cuello de transición** | $0.34 \to 0.45\text{ m}$ | $\varnothing\ 0.11 \to \varnothing\ 0.085\text{ m}$ | Molduras clásicas: toroide (bocel $\varnothing\ 0.13\text{ m}$) y escocia cóncava. |
| **Fuste (Columna)** | $0.45 \to 2.40\text{ m}$ | $\varnothing\ 0.085\text{ m}$ constante | Cilindro tubular liso recto de 1.95 m de longitud. |
| **Capitel ornamental** | $2.40 \to 2.58\text{ m}$ | $\varnothing_{\max} 0.14\text{ m}$ | Balustre ornamental clásico con collares superior e inferior ($\varnothing\ 0.11\text{ m}$). |
| **Vástago y herrajes** | $2.58 \to 2.93\text{ m}$ | $\varnothing\ 0.025\text{ m}$ | Eje cilíndrico de acero con manguitos de abrazadera doble en cruz a 90°. |
| **Placa Inferior** | $2.53 \to 2.85\text{ m}$ | $0.90\text{ m} \times 0.22/0.32\text{ m} \times 0.025\text{ m}$ | Orientada en eje X. Cama plana limpia con reborde y división en relieve. |
| **Placa Superior** | $2.63 \to 2.95\text{ m}$ | $0.90\text{ m} \times 0.22/0.32\text{ m} \times 0.025\text{ m}$ | Orientada a 90° (eje Y/Z). Cúspide de la crestería alcanza los **2.95 m totales**. |

---

## 4. Especificación de Materiales y Shaders (Godot StandardMaterial3D / ORM)

El asset cuenta con 3 materiales PBR físicamente calibrados, compatibles con el pipeline ORM (`Occlusion-Roughness-Metallic`) de Godot 4:

### 1. `M_Hierro_Fundido_Poste`
- **Uso**: Pedestal, fuste, capitel, vástago y abrazaderas de montaje.
- **Albedo / Base Color**: `#2C2A26` (`sRGB [0.17, 0.16, 0.15]` / Lineal `[0.042, 0.039, 0.035]`).
- **Metallic**: `0.70`.
- **Roughness**: `0.78` (acabado mate de fundición de arena con micro-rugosidad).

### 2. `M_Placa_Bronce_Patinado` (Slot 0 de las Placas)
- **Uso**: Cuerpo base de la placa y camas planas interiores de texto.
- **Albedo / Base Color**: `#3E4E40` (`sRGB [0.24, 0.31, 0.25]` / Lineal `[0.065, 0.105, 0.075]`).
- **Metallic**: `0.45`.
- **Roughness**: `0.75`.

### 3. `M_Placa_Relieve_Laton` (Slot 1 de las Placas)
- **Uso**: Rebordes perimetrales exteriores, arco de crestería, medallón heráldico y filete divisor vertical.
- **Albedo / Base Color**: `#8A856A` (`sRGB [0.54, 0.52, 0.42]` / Lineal `[0.32, 0.29, 0.18]`).
- **Metallic**: `0.55`.
- **Roughness**: `0.65`.

---

## 5. Implementación de Textos Dinámicos en Godot 4

Dado que el letrero se colocará en cientos de esquinas a lo largo del mapa urbano de Tecate, **el modelo principal (`poste_nomenclatura_tecate.glb`) omite texto fijo tridimensional**. En su lugar, las camas de texto de cada placa están construidas como superficies planas limpias con coordenadas UV ortogonales directas, listas para recibir nombres de calles de forma programática.

### Método Recomendado: `Label3D` en Godot 4

Este método es el más ligero, nítido y eficiente en memoria GPU. Se añade un script simple a la escena del letrero (`poste_esquina.gd`) que instancia los textos:

```gdscript
extends Node3D

@export var calle_inferior: String = "AV. JUAREZ"
@export var colonia_inferior: String = "ZONA CENTRO\nC.P. 21400\nTECATE, B.C."

@export var calle_superior: String = "CALLE TERCERA"
@export var colonia_superior: String = "ZONA CENTRO\nC.P. 21400\nTECATE, B.C."

func _ready() -> void:
	crear_etiquetas_placa_inferior()
	crear_etiquetas_placa_superior()

func crear_etiquetas_placa_inferior() -> void:
	# Cara Frontal (+Y)
	_agregar_label(calle_inferior, Vector3(-0.14, 2.64, 0.011), Vector3(0, 0, 0), 0.060, true)
	_agregar_label(colonia_inferior, Vector3(0.295, 2.64, 0.011), Vector3(0, 0, 0), 0.024, false)
	
	# Cara Trasera (-Y)
	_agregar_label(calle_inferior, Vector3(0.14, 2.64, -0.011), Vector3(0, 180, 0), 0.060, true)
	_agregar_label(colonia_inferior, Vector3(-0.295, 2.64, -0.011), Vector3(0, 180, 0), 0.024, false)

func crear_etiquetas_placa_superior() -> void:
	# Cara Frontal (-X)
	_agregar_label(calle_superior, Vector3(-0.011, 2.74, -0.14), Vector3(0, 90, 0), 0.060, true)
	_agregar_label(colonia_superior, Vector3(-0.011, 2.74, 0.295), Vector3(0, 90, 0), 0.024, false)
	
	# Cara Trasera (+X)
	_agregar_label(calle_superior, Vector3(0.011, 2.74, 0.14), Vector3(0, -90, 0), 0.060, true)
	_agregar_label(colonia_superior, Vector3(0.011, 2.74, -0.295), Vector3(0, -90, 0), 0.024, false)

func _agregar_label(texto: String, pos: Vector3, rot_deg: Vector3, font_size_m: float, bold: bool) -> void:
	var label = Label3D.new()
	label.text = texto
	label.pixel_size = font_size_m / 64.0
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	label.modulate = Color("8a856a") # Tono latón erosionado idéntico al relieve
	label.position = pos
	label.rotation_degrees = rot_deg
	label.render_priority = 1
	label.double_sided = false
	add_child(label)
```

### Alternativa: Generación de Texturas Dinámicas (SubViewport)
Si se desea proyectar mapas de normales o relieves tipográficos horneados mediante shaders, la cama plana cuenta con su propio material slot (`M_Placa_Bronce_Patinado`), al cual se le puede inyectar en tiempo de ejecución un `ViewportTexture` generado por un `SubViewport` que renderice el texto con estilo de fundición.

---

## 6. Inventario de Archivos del Asset

Los archivos generados se encuentran organizados en el repositorio:

1. **`blender_assets/poste_nomenclatura_tecate.blend`**:
   - Archivo fuente maestro de Blender.
   - Contiene la jerarquía limpia, transformaciones aplicadas a escala 1.0, materiales PBR configurados, colección secundaria con textos 3D y entorno de iluminación Cycles listo.
2. **`godot_project/assets/poste_nomenclatura_tecate.glb`**:
   - Asset principal optimizado para producción en Godot 4.
   - Sin textos estáticos, peso liviano (~172 KB), 2 slots de material por placa para máxima personalización.
3. **`godot_project/assets/poste_nomenclatura_tecate_demo.glb`**:
   - Asset de demostración con los textos 3D de muestra convertidos a mallas ("ESTEBAN CANTU" / "BENITO JUAREZ") para pruebas rápidas de visualización en el editor.
4. **`scripts/generate_poste_nomenclatura.py`**:
   - Script generador reproducible en Python para Blender. Permite modificar cotas, radios o parámetros y regenerar el modelo en cualquier momento mediante:
     ```bash
     /Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/generate_poste_nomenclatura.py
     ```
5. **`docs/images/`**:
   - `poste_nomenclatura_preview.png`: Render completo de 2.95 m.
   - `poste_nomenclatura_closeup.png`: Acercamiento a placas, relieves y herrajes.
   - `poste_nomenclatura_base.png`: Acercamiento a pedestal y molduras de transición.
