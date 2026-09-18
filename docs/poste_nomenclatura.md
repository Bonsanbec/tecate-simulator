# Especificación y Documentación Técnica: Poste de Nomenclatura Urbana Clásica de Tecate, B.C.

Este documento detalla el diseño, modelado paramétrico 3D, materiales PBR y guía de integración en motor (Godot Engine 4) del **Poste de Nomenclatura Urbana Clásica de Tecate**, un elemento de mobiliario urbano tradicional diseñado para ubicarse en las intersecciones y esquinas de manzanas en el simulador.

---

## 1. Contexto Urbano y Morfología Tecatense

En el centro histórico y primer cuadro de la ciudad de Tecate, Baja California (Pueblo Mágico), la señalización vial vertical de las esquinas se caracteriza por postes esbeltos de fundición de hierro rematados por dos placas en cruz perpendicular (90° entre sí). 

### Rasgos Distintivos de Tecate
1. **Doble placa en cruz superpuesta sin intersección**: La placa inferior se orienta a lo largo del eje transversal ($Z = 2.41 \to 2.63\text{ m}$), mientras que la placa superior se apoya directamente sobre su lomo superior a 90° ($Z = 2.63 \to 2.85\text{ m}$), garantizando cero clipping o solapamiento geométrico.
2. **Crestería semicircular centrada**: La placa superior cuenta con un semicírculo en arco de medio punto ($r = 0.10\text{ m}$) estrictamente centrado en la longitud total de 0.90 m ($x = 0.0\text{ m}$), cuya cúspide alcanza con exactitud los **2.95 m de altura total** requeridos.
3. **Escudo y distrito histórico**: El crestón incorpora en altorrelieve de latón la leyenda curva concéntrica **"AYUNTAMIENTO"** y el número **"17"** (distrito municipal de Tecate) con tipografía clásica de fundición en ambas caras (frente y dorso).
4. **Composición asimétrica 2/3 y 1/3 con recuadro blanco de patrocinador**: Un filete vertical en relieve divide la placa en dos áreas funcionales:
   - **2/3 izquierdos (0.63 m)**: Cama de bronce verde cardenillo para el nombre de la calle/avenida.
   - **1/3 derecho (0.27 m)**: Recuadro en esmalte blanco tradicional (`M_Placa_Recuadro_Blanco`) reservado para logotipos o inscripciones de patrocinadores locales y código postal.
5. **Pátina y materiales tradicionales**: Fuste de fundición gris plomo oscuro envejecido, fondo de bronce patinado a la intemperie (verde cardenillo), relieves en latón erosionado y recuadro de esmalte blanco horneado.

---

## 2. Renders Técnicos Oficiales de Inspección

| Vista General (2.95 m) | Acercamiento a Placas (90°) | Crestón Heráldico Centrado | Pedestal / Base Clásica |
| :---: | :---: | :---: | :---: |
| ![Vista General](images/poste_nomenclatura_preview.png) | ![Detalle Placas](images/poste_nomenclatura_closeup.png) | ![Crestón Ayto 17](images/poste_nomenclatura_creston.png) | ![Detalle Pedestal](images/poste_nomenclatura_base.png) |

---

## 3. Jerarquía Espacial y Desglose Geométrico

El modelo está construido a escala métrica real 1:1, con origen y pivote en el suelo $(0, 0, 0)$, listo para colocar directamente sobre las banquetas en Godot sin requerir offsets en $Z$.

```
Poste_Nomenclatura_Tecate (Colección Raíz)
 ├── Poste_Estructura (Hierro Fundido, Malla de Revolución y Herrajes)
 │    ├── Placa_Inferior (Eje X, Z = 2.41 a 2.63 m, centro Z = 2.52 m)
 │    └── Placa_Superior (Eje Y, 90°, Z = 2.63 a 2.85/2.95 m, centro Z = 2.74 m)
 └── [Opcional] Texto_Demostracion_Ejemplo (Colección aislada con textos 3D)
```

### Tabla de Cotas y Dimensiones

| Componente | Cota / Rango $Z$ | Diámetro / Dimensiones | Características Principales |
| :--- | :--- | :--- | :--- |
| **Anillo de apoyo en suelo** | $0.00 \to 0.04\text{ m}$ | $\varnothing\ 0.32\text{ m}$ | Huella de apoyo con bisel perimetral hacia $\varnothing\ 0.28\text{ m}$. |
| **Campana clásica (Pedestal)** | $0.04 \to 0.34\text{ m}$ | $\varnothing\ 0.28 \to \varnothing\ 0.11\text{ m}$ | Transición cóncava acampanada con 16 estrías suaves de fundición. |
| **Cuello y molduras** | $0.34 \to 0.45\text{ m}$ | $\varnothing\ 0.11 \to \varnothing\ 0.085\text{ m}$ | Molduras clásicas: toroide (bocel $\varnothing\ 0.13\text{ m}$) y escocia cóncava. |
| **Fuste (Columna principal)** | $0.45 \to 2.25\text{ m}$ | $\varnothing\ 0.085\text{ m}$ constante | Cilindro tubular liso de hierro de 1.80 m de longitud. |
| **Capitel de balustre torneado** | $2.25 \to 2.41\text{ m}$ | $\varnothing_{\max} 0.128\text{ m}$ | Capitel clásico torneado con collarines de transición. |
| **Vástago interior y asientos** | $2.41 \to 2.745\text{ m}$ | $\varnothing\ 0.016\text{ m}$ interior | Eje interno de sujeción que culmina a $Z=2.745\text{ m}$ sin penetrar la crestería. |
| **Placa Inferior (Eje X)** | $2.41 \to 2.63\text{ m}$ | $0.90\text{ m} \times 0.22\text{ m} \times 0.018\text{ m}$ | Lomo recto sobre el que asienta la placa superior. Filete divisor y recuadro blanco. |
| **Placa Superior (Eje Y)** | $2.63 \to 2.95\text{ m}$ | $0.90\text{ m} \times 0.22/0.32\text{ m} \times 0.018\text{ m}$ | Orientada a 90°. Semicírculo centrado con "AYUNTAMIENTO" y "17" en relieve. Cúspide: **2.95 m**. |

---

## 4. Especificación de Materiales PBR

El modelo utiliza 4 materiales PBR optimizados para el pipeline PBR/ORM (`Occlusion-Roughness-Metallic`) de Godot 4:

### 1. `M_Hierro_Fundido_Poste`
- **Uso**: Pedestal, fuste, capitel torneado y asientos de montaje.
- **Albedo / Base Color**: `#2C2A26` (Lineal `[0.042, 0.039, 0.035]`).
- **Metallic**: `0.70`.
- **Roughness**: `0.78` (textura mate de fundición de arena).

### 2. `M_Placa_Bronce_Patinado` (Slot 0 de las Placas)
- **Uso**: Fondo principal de la placa y cama de rotulación de la calle.
- **Albedo / Base Color**: `#3E4E40` (Lineal `[0.065, 0.105, 0.075]`, verde cardenillo oscuro).
- **Metallic**: `0.45`.
- **Roughness**: `0.75`.

### 3. `M_Placa_Relieve_Laton` (Slot 1 de las Placas)
- **Uso**: Marco perimetral, pestaña de 9 mm de crestería, filete divisor, letras "AYUNTAMIENTO" y número "17".
- **Albedo / Base Color**: `#8A856A` (Lineal `[0.32, 0.29, 0.18]`, latón envejecido pulido en aristas).
- **Metallic**: `0.55`.
- **Roughness**: `0.65`.

### 4. `M_Placa_Recuadro_Blanco` (Slot 2 de las Placas)
- **Uso**: Recuadro derecho de 1/3 ($0.27\text{ m} \times 0.19\text{ m}$) destinado a patrocinadores / colonia.
- **Albedo / Base Color**: `#EAEAE6` (Lineal `[0.82, 0.82, 0.79]`, blanco esmaltado clásico).
- **Metallic**: `0.05`.
- **Roughness**: `0.35` (acabado porcelanizado brillante).

---

## 5. Implementación de Textos Dinámicos en Godot 4

Para permitir que cada esquina tenga sus propios nombres de calles sin duplicar modelos 3D en memoria, el asset base (`poste_nomenclatura_tecate.glb`) no incluye texto estático. Se incluye a continuación el script recomendado para instanciar textos nítidos mediante `Label3D`:

```gdscript
extends Node3D

@export var calle_inferior: String = "ESTEBAN CANTU"
@export var info_inferior: String = "HOSPITAL\nSANTA CATARINA\nC.P. 21400"

@export var calle_superior: String = "BENITO JUAREZ"
@export var info_superior: String = "CLINICA\nHOSPITAL\nSANTA CATARINA"

func _ready() -> void:
	crear_etiquetas_placa_inferior()
	crear_etiquetas_placa_superior()

func crear_etiquetas_placa_inferior() -> void:
	# Cota Z = 2.52 m
	# Cara Frontal (+Y)
	_agregar_label(calle_inferior, Vector3(-0.14, 2.52, 0.0105), Vector3(0, 0, 0), 0.060, Color("8a856a"))
	_agregar_label(info_inferior, Vector3(0.295, 2.52, 0.0105), Vector3(0, 0, 0), 0.024, Color("1a1a1a"))
	
	# Cara Trasera (-Y)
	_agregar_label(calle_inferior, Vector3(0.14, 2.52, -0.0105), Vector3(0, 180, 0), 0.060, Color("8a856a"))
	_agregar_label(info_inferior, Vector3(-0.295, 2.52, -0.0105), Vector3(0, 180, 0), 0.024, Color("1a1a1a"))

func crear_etiquetas_placa_superior() -> void:
	# Cota Z = 2.74 m (Rotada 90° en Y)
	# Cara Frontal (-X)
	_agregar_label(calle_superior, Vector3(-0.0105, 2.74, 0.14), Vector3(0, -90, 0), 0.060, Color("8a856a"))
	_agregar_label(info_superior, Vector3(-0.0105, 2.74, -0.295), Vector3(0, -90, 0), 0.024, Color("1a1a1a"))
	
	# Cara Trasera (+X)
	_agregar_label(calle_superior, Vector3(0.0105, 2.74, -0.14), Vector3(0, 90, 0), 0.060, Color("8a856a"))
	_agregar_label(info_superior, Vector3(0.0105, 2.74, 0.295), Vector3(0, 90, 0), 0.024, Color("1a1a1a"))

func _agregar_label(texto: String, pos: Vector3, rot_deg: Vector3, font_size_m: float, color: Color) -> void:
	var label = Label3D.new()
	label.text = texto
	label.pixel_size = font_size_m / 64.0
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	label.modulate = color
	label.position = pos
	label.rotation_degrees = rot_deg
	label.render_priority = 1
	label.double_sided = false
	add_child(label)
```

---

## 6. Inventario de Archivos Entregados

1. **`blender_assets/poste_nomenclatura_tecate.blend`**:
   - Archivo maestro nativo de Blender 5.1.
   - Jerarquía completa, transformaciones congeladas en escala 1.0, materiales PBR asignados por slot, cámaras e iluminación Cycles.
2. **`godot_project/assets/poste_nomenclatura_tecate.glb`**:
   - Modelo para producción en Godot. Ligero (~168 KB), sin textos estáticos, 3 slots de material por placa.
3. **`godot_project/assets/poste_nomenclatura_tecate_demo.glb`**:
   - Modelo de demostración con tipografía 3D de muestra ("ESTEBAN CANTU" / "BENITO JUAREZ" y datos de patrocinador) para inspección directa en el visor 3D de Godot.
4. **`scripts/generate_poste_nomenclatura.py`**:
   - Script 100% determinista y reproducible para regenerar el `.blend` y ambos `.glb` de forma desatendida:
     ```bash
     /Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/generate_poste_nomenclatura.py
     ```
5. **`docs/images/`**:
   - `poste_nomenclatura_preview.png`: Vista ortométrica completa (2.95 m).
   - `poste_nomenclatura_closeup.png`: Acercamiento a las placas a 90° con recuadros blancos.
   - `poste_nomenclatura_creston.png`: Acercamiento detallado al crestón semicircular con "AYUNTAMIENTO" y "17".
   - `poste_nomenclatura_base.png`: Detalle del pedestal acampanado con 16 estrías suaves.

