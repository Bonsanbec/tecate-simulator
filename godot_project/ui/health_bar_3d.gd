class_name HealthBar3D
extends Node3D

## Componente de Barra de Vida 3D Diegética (Overhead Billboard)
## Renderiza una barra de vida 3D flotante sobre personajes, vehículos u objetos
## en Tecate Simulator mediante SubViewport y Sprite3D en modo Billboard.
## Se actualiza automáticamente respondiendo a la señal health_changed de HealthComponent.

const HealthComponentClass = preload("res://systems/combat/health_component.gd")

@export var show_text: bool = true
@export var auto_hide_full: bool = false
@export var billboard_offset: Vector3 = Vector3(0, 0.4, 0)

var health_component: HealthComponentClass = null
var sprite_3d: Sprite3D = null
var viewport: SubViewport = null
var progress_bar: ProgressBar = null
var hp_label: Label = null
var style_fill: StyleBoxFlat = null

var _target_percentage: float = 1.0
var _current_percentage: float = 1.0

func _ready() -> void:
	_setup_viewports_and_visuals()

func setup(p_health_component: HealthComponentClass) -> void:
	if health_component:
		if health_component.health_changed.is_connected(_on_health_changed):
			health_component.health_changed.disconnect(_on_health_changed)

	health_component = p_health_component
	if health_component:
		health_component.health_changed.connect(_on_health_changed)
		update_bar(health_component.current_health, health_component.max_health)

func _setup_viewports_and_visuals() -> void:
	if sprite_3d != null:
		return

	position = billboard_offset

	# 1. SubViewport para renderizado 2D en textura 3D
	viewport = SubViewport.new()
	viewport.name = "HealthViewport"
	viewport.size = Vector2i(200, 32)
	viewport.transparent_bg = true
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(viewport)

	# 2. Contenedor principal UI
	var container = PanelContainer.new()
	container.size = Vector2(200, 32)

	var style_bg = StyleBoxFlat.new()
	style_bg.bg_color = Color(0.06, 0.08, 0.10, 0.85)
	style_bg.border_width_left = 1
	style_bg.border_width_top = 1
	style_bg.border_width_right = 1
	style_bg.border_width_bottom = 1
	style_bg.border_color = Color(0.25, 0.30, 0.35, 0.9)
	style_bg.corner_radius_top_left = 4
	style_bg.corner_radius_top_right = 4
	style_bg.corner_radius_bottom_right = 4
	style_bg.corner_radius_bottom_left = 4
	container.add_theme_stylebox_override("panel", style_bg)
	viewport.add_child(container)

	# 3. ProgressBar
	progress_bar = ProgressBar.new()
	progress_bar.custom_minimum_size = Vector2(196, 28)
	progress_bar.show_percentage = false

	var style_empty = StyleBoxFlat.new()
	style_empty.bg_color = Color(0.12, 0.14, 0.16, 0.9)
	style_empty.corner_radius_top_left = 3
	style_empty.corner_radius_top_right = 3
	style_empty.corner_radius_bottom_right = 3
	style_empty.corner_radius_bottom_left = 3
	progress_bar.add_theme_stylebox_override("background", style_empty)

	style_fill = StyleBoxFlat.new()
	style_fill.bg_color = Color(0.15, 0.85, 0.40, 1.0) # Verde inicial
	style_fill.corner_radius_top_left = 3
	style_fill.corner_radius_top_right = 3
	style_fill.corner_radius_bottom_right = 3
	style_fill.corner_radius_bottom_left = 3
	progress_bar.add_theme_stylebox_override("fill", style_fill)
	container.add_child(progress_bar)

	# 4. Texto HP superpuesto
	hp_label = Label.new()
	hp_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	hp_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	hp_label.add_theme_font_size_override("font_size", 12)
	hp_label.add_theme_color_override("font_color", Color(1.0, 1.0, 1.0, 0.95))
	hp_label.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.9))
	hp_label.add_theme_constant_override("outline_size", 3)
	container.add_child(hp_label)

	# 5. Sprite3D Billboard
	sprite_3d = Sprite3D.new()
	sprite_3d.name = "HealthSprite3D"
	sprite_3d.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	sprite_3d.pixel_size = 0.005
	sprite_3d.texture = viewport.get_texture()
	sprite_3d.no_depth_test = false
	add_child(sprite_3d)

	# Si ya existe health_component en el padre, conectar automáticamente
	if health_component == null and get_parent():
		var hc = get_parent().get_node_or_null("HealthComponent") as HealthComponentClass
		if hc:
			setup(hc)

func _process(delta: float) -> void:
	if not is_equal_approx(_current_percentage, _target_percentage):
		_current_percentage = lerpf(_current_percentage, _target_percentage, delta * 10.0)
		if progress_bar:
			progress_bar.value = _current_percentage * 100.0

func _on_health_changed(current: float, max_h: float) -> void:
	update_bar(current, max_h)

func update_bar(current: float, max_h: float) -> void:
	if max_h <= 0.0:
		return
	_target_percentage = clampf(current / max_h, 0.0, 1.0)

	if auto_hide_full:
		visible = (_target_percentage < 0.999 and _target_percentage > 0.0)
	else:
		visible = (_target_percentage > 0.0)

	if hp_label:
		if show_text:
			hp_label.text = "%d / %d HP" % [int(ceil(current)), int(ceil(max_h))]
		else:
			hp_label.text = ""

	# Cambio de color según porcentaje de salud
	if style_fill:
		if _target_percentage > 0.50:
			# Verde -> Amarillo
			style_fill.bg_color = Color(0.15, 0.85, 0.40, 1.0).lerp(Color(0.95, 0.80, 0.15, 1.0), (1.0 - _target_percentage) * 2.0)
		else:
			# Amarillo -> Rojo
			style_fill.bg_color = Color(0.95, 0.80, 0.15, 1.0).lerp(Color(0.90, 0.18, 0.18, 1.0), (0.50 - _target_percentage) * 2.0)
