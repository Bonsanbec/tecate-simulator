class_name StartScreen
extends Node3D

## Pantalla de Inicio de Tecate Simulator
##
## Presenta una vista cinematográfica orientada hacia el Cerro Cuchumá en el horizonte,
## con el título "Tecate" y las opciones "Continuar", "Reaparecer" y "Salir" ubicadas
## en la esquina superior izquierda sobre el cielo abierto.

signal game_continued
signal game_respawned
signal game_exited

@export_group("Cámara Cinematográfica Cuchumá")
@export var initial_cam_position: Vector3 = Vector3(-6.6844, 405.5, 11.0)
@export var target_cuchuma: Vector3 = Vector3(-5850.0, 920.0, -700.0)
@export var camera_fov: float = 58.0
@export var ambient_drift_speed: float = 0.12

@export_group("Referencias")
@export var player_path: NodePath = ^"../Player"

@onready var menu_camera: Camera3D = $MenuCamera
@onready var canvas_layer: CanvasLayer = $CanvasLayer
@onready var title_label: Label = $CanvasLayer/RootControl/MarginContainer/VBox/TitleContainer/TitleLabel
@onready var subtitle_label: Label = $CanvasLayer/RootControl/MarginContainer/VBox/TitleContainer/SubtitleLabel
@onready var btn_continue: Button = $CanvasLayer/RootControl/MarginContainer/VBox/ButtonsContainer/BtnContinue
@onready var btn_respawn: Button = $CanvasLayer/RootControl/MarginContainer/VBox/ButtonsContainer/BtnRespawn
@onready var btn_quit: Button = $CanvasLayer/RootControl/MarginContainer/VBox/ButtonsContainer/BtnQuit

var player: CharacterBody3D
var is_menu_active: bool = true
var _time: float = 0.0

func _ready() -> void:
	# Localizar al jugador
	if has_node(player_path):
		player = get_node(player_path) as CharacterBody3D
	elif get_parent() and get_parent().has_node("Player"):
		player = get_parent().get_node("Player") as CharacterBody3D

	# Configuración inicial de cámara orientada al Cuchumá
	if menu_camera:
		menu_camera.fov = camera_fov
		menu_camera.far = 16000.0
		menu_camera.global_position = initial_cam_position
		menu_camera.look_at(target_cuchuma, Vector3.UP)

	_setup_ui_styles()
	_connect_signals()

	# Iniciar mostrando la pantalla de inicio
	open_menu(true)

func _connect_signals() -> void:
	if btn_continue:
		btn_continue.pressed.connect(_on_continue_pressed)
		btn_continue.mouse_entered.connect(_on_button_hover.bind(btn_continue, true))
		btn_continue.mouse_exited.connect(_on_button_hover.bind(btn_continue, false))
		btn_continue.focus_entered.connect(_on_button_hover.bind(btn_continue, true))
		btn_continue.focus_exited.connect(_on_button_hover.bind(btn_continue, false))

	if btn_respawn:
		btn_respawn.pressed.connect(_on_respawn_pressed)
		btn_respawn.mouse_entered.connect(_on_button_hover.bind(btn_respawn, true))
		btn_respawn.mouse_exited.connect(_on_button_hover.bind(btn_respawn, false))
		btn_respawn.focus_entered.connect(_on_button_hover.bind(btn_respawn, true))
		btn_respawn.focus_exited.connect(_on_button_hover.bind(btn_respawn, false))

	if btn_quit:
		btn_quit.pressed.connect(_on_quit_pressed)
		btn_quit.mouse_entered.connect(_on_button_hover.bind(btn_quit, true))
		btn_quit.mouse_exited.connect(_on_button_hover.bind(btn_quit, false))
		btn_quit.focus_entered.connect(_on_button_hover.bind(btn_quit, true))
		btn_quit.focus_exited.connect(_on_button_hover.bind(btn_quit, false))

func _setup_ui_styles() -> void:
	var din_font = load("res://assets/fonts/DIN_Condensed_Bold.ttf")
	if din_font:
		if title_label:
			title_label.add_theme_font_override("font", din_font)
		if subtitle_label:
			subtitle_label.add_theme_font_override("font", din_font)

	for btn in [btn_continue, btn_respawn, btn_quit]:
		if not btn:
			continue
		if din_font:
			btn.add_theme_font_override("font", din_font)
		btn.add_theme_font_size_override("font_size", 34)
		btn.alignment = HORIZONTAL_ALIGNMENT_LEFT
		btn.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND

		# Colores de texto
		btn.add_theme_color_override("font_color", Color(0.94, 0.94, 0.94, 1.0))
		btn.add_theme_color_override("font_hover_color", Color(1.0, 0.88, 0.42, 1.0))
		btn.add_theme_color_override("font_focus_color", Color(1.0, 0.88, 0.42, 1.0))
		btn.add_theme_color_override("font_pressed_color", Color(0.85, 0.72, 0.28, 1.0))

		# Sombra para contraste sobre cualquier cielo o nubes
		btn.add_theme_color_override("font_shadow_color", Color(0.04, 0.05, 0.08, 0.85))
		btn.add_theme_constant_override("shadow_offset_x", 1)
		btn.add_theme_constant_override("shadow_offset_y", 2)
		btn.add_theme_constant_override("shadow_outline_size", 3)

		# Estilo normal: limpio y transparente
		var style_normal = StyleBoxEmpty.new()
		style_normal.content_margin_left = 6
		style_normal.content_margin_top = 4
		style_normal.content_margin_bottom = 4
		style_normal.content_margin_right = 16
		btn.add_theme_stylebox_override("normal", style_normal)

		# Estilo hover / focus: resaltado sutil con borde ámbar a la izquierda
		var style_hover = StyleBoxFlat.new()
		style_hover.bg_color = Color(0.06, 0.08, 0.12, 0.45)
		style_hover.border_width_left = 4
		style_hover.border_color = Color(0.96, 0.82, 0.38, 1.0)
		style_hover.corner_radius_top_left = 2
		style_hover.corner_radius_bottom_left = 2
		style_hover.corner_radius_top_right = 6
		style_hover.corner_radius_bottom_right = 6
		style_hover.content_margin_left = 14
		style_hover.content_margin_top = 4
		style_hover.content_margin_bottom = 4
		style_hover.content_margin_right = 16
		btn.add_theme_stylebox_override("hover", style_hover)
		btn.add_theme_stylebox_override("focus", style_hover)

		var style_pressed = style_hover.duplicate()
		style_pressed.bg_color = Color(0.04, 0.06, 0.09, 0.7)
		btn.add_theme_stylebox_override("pressed", style_pressed)

func _on_button_hover(btn: Button, hovered: bool) -> void:
	if not btn:
		return
	# Sutil modulación de brillo
	var tween = create_tween().set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	var target_mod = Color(1.15, 1.15, 1.15) if hovered else Color(1.0, 1.0, 1.0)
	tween.tween_property(btn, "modulate", target_mod, 0.12)

func _process(delta: float) -> void:
	if is_menu_active and menu_camera:
		_time += delta
		# Suave respiración ambiental cinematográfica
		var drift_x = sin(_time * ambient_drift_speed) * 0.8
		var drift_y = cos(_time * (ambient_drift_speed * 0.75)) * 0.25
		menu_camera.global_position = initial_cam_position + Vector3(drift_x, drift_y, 0.0)
		menu_camera.look_at(target_cuchuma, Vector3.UP)

func open_menu(_instant: bool = false) -> void:
	is_menu_active = true
	if canvas_layer:
		canvas_layer.visible = true
	if menu_camera:
		menu_camera.make_current()
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE

	if player and player.has_method("set_input_enabled"):
		player.set_input_enabled(false)

	if btn_continue:
		btn_continue.grab_focus()

func close_menu() -> void:
	is_menu_active = false
	if canvas_layer:
		canvas_layer.visible = false

	if player:
		if player.has_method("set_input_enabled"):
			player.set_input_enabled(true)
		var player_cam = player.camera if ("camera" in player and player.camera) else player.get_node_or_null("Camera3D")
		if player_cam and player_cam is Camera3D:
			player_cam.make_current()

	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED

func toggle_menu() -> void:
	if is_menu_active:
		_on_continue_pressed()
	else:
		open_menu()

func _on_continue_pressed() -> void:
	close_menu()
	game_continued.emit()

func _on_respawn_pressed() -> void:
	if player and player.has_method("respawn"):
		player.respawn()
	close_menu()
	game_respawned.emit()

func _on_quit_pressed() -> void:
	game_exited.emit()
	get_tree().quit()
