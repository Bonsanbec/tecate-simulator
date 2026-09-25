class_name CompassAxesGizmo
extends Control

## Gizmo de Ejes de Orientación al Estilo Blender para Tecate Simulator
## Dibuja los tres ejes del espacio de mundo (X, Y, Z) proyectados en 2D,
## con los colores canónicos de Blender/Godot:
##   X = Rojo   (#F04040)
##   Y = Verde  (#4CAF50)
##   Z = Azul   (#4080F0)
## Los ejes negativos se dibujan semi-transparentes y punteados.
## Se actualiza llamando a set_camera_basis(basis: Basis).

# ── Parámetros exportables ──────────────────────────────────────────────────
@export var radius: float = 44.0          ## Radio del círculo de fondo
@export var axis_length: float = 36.0     ## Longitud de cada eje en píxeles
@export var line_width: float = 2.8       ## Grosor de línea de eje positivo
@export var label_font_size: int = 11     ## Tamaño de letra de etiquetas

# ── Colores canónicos Blender ───────────────────────────────────────────────
const COLOR_X     := Color(0.941, 0.251, 0.251, 1.00)   # Rojo X
const COLOR_Y     := Color(0.298, 0.686, 0.314, 1.00)   # Verde Y
const COLOR_Z     := Color(0.251, 0.502, 0.941, 1.00)   # Azul Z
const COLOR_X_NEG := Color(0.941, 0.251, 0.251, 0.38)
const COLOR_Y_NEG := Color(0.298, 0.686, 0.314, 0.38)
const COLOR_Z_NEG := Color(0.251, 0.502, 0.941, 0.38)
const COLOR_BG    := Color(0.06,  0.08,  0.10,  0.60)   # Fondo oscuro translúcido

# ── Estado interno ──────────────────────────────────────────────────────────
var _basis: Basis = Basis.IDENTITY

## Actualiza la base de la cámara activa para re-proyectar los ejes.
func set_camera_basis(b: Basis) -> void:
	_basis = b
	queue_redraw()

func _draw() -> void:
	var center := Vector2(size.x * 0.5, size.y * 0.5)

	# ── Fondo circular ──────────────────────────────────────────────────────
	draw_circle(center, radius, COLOR_BG)

	# ── Proyección de los ejes del mundo al plano 2D de pantalla ───────────
	# La cámara mira hacia -Z en su espacio local.
	# Convertimos cada eje del mundo al espacio de vista de la cámara:
	#   right_view  = basis.x  (columna X de la base)
	#   up_view     = basis.y  (columna Y de la base)
	# El eje del mundo en espacio de cámara es:  axis_cam = basis.inverse() * world_axis
	# Para proyectar: pantalla_x = dot(world_axis, right)  → dato real del mundo en X de cámara
	#                 pantalla_y = -dot(world_axis, up)     → invertir Y para pantalla

	var cam_right := _basis.x           # Vector del mundo que apunta a la derecha de la cámara
	var cam_up    := _basis.y           # Vector del mundo que apunta arriba de la cámara

	# Ejes del mundo que queremos visualizar (Godot: X=Este, Y=Arriba, Z=Sur)
	var axes := [
		{ "dir": Vector3(1,0,0), "col": COLOR_X, "col_neg": COLOR_X_NEG, "lbl": "X" },
		{ "dir": Vector3(0,1,0), "col": COLOR_Y, "col_neg": COLOR_Y_NEG, "lbl": "Y" },
		{ "dir": Vector3(0,0,1), "col": COLOR_Z, "col_neg": COLOR_Z_NEG, "lbl": "Z" },
	]

	# ── Ordenar por profundidad (Z de cámara) para pintar primero los más lejanos ──
	# Eje más alejado de la cámara: dot(axis, -cam_fwd) más negativo
	var cam_fwd := -_basis.z            # Dirección hacia la que apunta la cámara
	axes.sort_custom(func(a, b):
		return a["dir"].dot(cam_fwd) < b["dir"].dot(cam_fwd)
	)

	# ── Dibujar cada eje ────────────────────────────────────────────────────
	for ax in axes:
		var world_dir: Vector3 = ax["dir"]
		var neg_dir: Vector3   = -world_dir

		# Proyección 2D: mapear el eje del mundo al plano de pantalla
		var tip_2d    := _project_world_to_gizmo(world_dir,  center)
		var neg_2d    := _project_world_to_gizmo(neg_dir,    center)

		# Profundidad del extremo positivo (cuánto apunta hacia la cámara)
		var depth_pos := world_dir.dot(cam_fwd)

		var col_pos: Color = ax["col"]
		var col_neg: Color = ax["col_neg"]

		# ── Eje negativo (semi-transparente) ───────────────────────────────
		draw_line(center, neg_2d, col_neg, line_width * 0.8)

		# ── Eje positivo ───────────────────────────────────────────────────
		draw_line(center, tip_2d, col_pos, line_width)

		# Punto en extremo positivo
		draw_circle(tip_2d, line_width * 1.6, col_pos)

		# ── Etiqueta del eje (solo positivo) ───────────────────────────────
		# Si el eje apunta hacia la cámara (depth > 0) el label va cerca del tip,
		# si apunta lejos, el gizmo lo muestra más pequeño / opaco.
		var label_alpha := clampf(0.55 + depth_pos * 0.45, 0.40, 1.0)
		var label_col   := Color(col_pos.r, col_pos.g, col_pos.b, label_alpha)
		var label_pos   := tip_2d + (tip_2d - center).normalized() * 9.0
		draw_string(
			ThemeDB.fallback_font,
			label_pos - Vector2(4, -4),
			ax["lbl"],
			HORIZONTAL_ALIGNMENT_LEFT,
			-1,
			label_font_size,
			label_col
		)

## Proyecta un vector del mundo 3D al plano 2D del gizmo.
func _project_world_to_gizmo(world_dir: Vector3, center: Vector2) -> Vector2:
	var cam_right := _basis.x
	var cam_up    := _basis.y
	var px := world_dir.dot(cam_right)
	var py := -world_dir.dot(cam_up)    # Invertir Y: en pantalla Y crece hacia abajo
	return center + Vector2(px, py) * axis_length
