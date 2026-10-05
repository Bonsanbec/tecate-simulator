class_name StartScreen
extends Node3D

## Pantalla de Inicio y Selección de Personaje de Tecate Simulator
##
## Presenta una vista cinematográfica orientada hacia el Cerro Cuchumá en el horizonte,
## con opciones principales ("Continuar", "Reaparecer", "Salir") y una transición fluida
## hacia la pantalla cenital de selección de personajes ("Camarada / Axel" y "Diseñador / Eli"),
## posada contemplando la topografía urbana de Tecate desde las alturas.

signal character_selected(character_id: String)
signal game_continued
signal game_respawned
signal game_exited

const CharacterCatalogClass = preload("res://systems/characters/character_catalog.gd")

enum MenuScreenState {
	MAIN_MENU,
	CHARACTER_SELECT
}

enum PendingAction {
	NONE,
	CONTINUE,
	RESPAWN
}

@export_group("Cámaras Cinematográficas")
@export var initial_cam_position: Vector3 = Vector3(-6.6844, 405.5, 11.0)
@export var target_cuchuma: Vector3 = Vector3(-5850.0, 920.0, -700.0)
@export var topdown_cam_position: Vector3 = Vector3(-6.6844, 495.0, 55.0)
@export var topdown_cam_target: Vector3 = Vector3(-6.6844, 400.0, 2.6878)
@export var camera_fov: float = 58.0
@export var ambient_drift_speed: float = 0.12

@export_group("Referencias")
@export var player_path: NodePath = ^"../Player"
@export var network_client_path: NodePath = ^"../NetworkClient"

@onready var menu_camera: Camera3D = $MenuCamera
@onready var canvas_layer: CanvasLayer = $CanvasLayer

# Contenedor del Menú Principal
@onready var main_menu_container: MarginContainer = $CanvasLayer/RootControl/MarginContainer
@onready var title_label: Label = $CanvasLayer/RootControl/MarginContainer/VBox/TitleContainer/TitleLabel
@onready var subtitle_label: Label = $CanvasLayer/RootControl/MarginContainer/VBox/TitleContainer/SubtitleLabel
@onready var btn_continue: Button = $CanvasLayer/RootControl/MarginContainer/VBox/ButtonsContainer/BtnContinue
@onready var btn_respawn: Button = $CanvasLayer/RootControl/MarginContainer/VBox/ButtonsContainer/BtnRespawn
@onready var btn_quit: Button = $CanvasLayer/RootControl/MarginContainer/VBox/ButtonsContainer/BtnQuit

# Contenedor de Selección de Personajes
@onready var char_select_container: Control = $CanvasLayer/RootControl/CharacterSelectContainer
@onready var char_select_title: Label = $CanvasLayer/RootControl/CharacterSelectContainer/CenterContainer/SelectionVBox/TitleVBox/CharSelectTitle
@onready var char_select_subtitle: Label = $CanvasLayer/RootControl/CharacterSelectContainer/CenterContainer/SelectionVBox/TitleVBox/CharSelectSubtitle
@onready var card_axel_panel: PanelContainer = $CanvasLayer/RootControl/CharacterSelectContainer/CenterContainer/SelectionVBox/CardsHBox/CardAxel
@onready var card_eli_panel: PanelContainer = $CanvasLayer/RootControl/CharacterSelectContainer/CenterContainer/SelectionVBox/CardsHBox/CardEli
@onready var name_axel_label: Label = $CanvasLayer/RootControl/CharacterSelectContainer/CenterContainer/SelectionVBox/CardsHBox/CardAxel/Margin/VBox/NameAxel
@onready var codename_axel_label: Label = get_node_or_null("CanvasLayer/RootControl/CharacterSelectContainer/CenterContainer/SelectionVBox/CardsHBox/CardAxel/Margin/VBox/CodenameAxel") as Label
@onready var desc_axel_label: Label = $CanvasLayer/RootControl/CharacterSelectContainer/CenterContainer/SelectionVBox/CardsHBox/CardAxel/Margin/VBox/DescAxel
@onready var btn_select_axel: Button = $CanvasLayer/RootControl/CharacterSelectContainer/CenterContainer/SelectionVBox/CardsHBox/CardAxel/Margin/VBox/BtnSelectAxel
@onready var name_eli_label: Label = $CanvasLayer/RootControl/CharacterSelectContainer/CenterContainer/SelectionVBox/CardsHBox/CardEli/Margin/VBox/NameEli
@onready var codename_eli_label: Label = get_node_or_null("CanvasLayer/RootControl/CharacterSelectContainer/CenterContainer/SelectionVBox/CardsHBox/CardEli/Margin/VBox/CodenameEli") as Label
@onready var desc_eli_label: Label = $CanvasLayer/RootControl/CharacterSelectContainer/CenterContainer/SelectionVBox/CardsHBox/CardEli/Margin/VBox/DescEli
@onready var btn_select_eli: Button = $CanvasLayer/RootControl/CharacterSelectContainer/CenterContainer/SelectionVBox/CardsHBox/CardEli/Margin/VBox/BtnSelectEli
@onready var btn_confirm_selection: Button = $CanvasLayer/RootControl/CharacterSelectContainer/CenterContainer/SelectionVBox/ActionsHBox/BtnConfirmSelection
@onready var btn_back_to_main: Button = $CanvasLayer/RootControl/CharacterSelectContainer/CenterContainer/SelectionVBox/ActionsHBox/BtnBackToMain

var player: CharacterBody3D = null
var network_client: Node = null
var is_menu_active: bool = true
var current_screen_state: MenuScreenState = MenuScreenState.MAIN_MENU
var _pending_action: PendingAction = PendingAction.NONE

var selected_character_id: String = ""
var has_chosen_character: bool = false
var _time: float = 0.0
var _previous_camera: Camera3D = null
var _camera_tween: Tween = null
var _is_transitioning: bool = false

func _ready() -> void:
	# Localizar al jugador
	if has_node(player_path):
		player = get_node(player_path) as CharacterBody3D
	elif get_parent() and get_parent().has_node("Player"):
		player = get_parent().get_node("Player") as CharacterBody3D

	# Localizar cliente de red
	if has_node(network_client_path):
		network_client = get_node(network_client_path)
	elif get_parent() and get_parent().has_node("NetworkClient"):
		network_client = get_parent().get_node("NetworkClient")

	# Configuración inicial de cámara orientada al Cuchumá
	if menu_camera:
		menu_camera.fov = camera_fov
		menu_camera.far = 16000.0
		menu_camera.global_position = initial_cam_position
		menu_camera.look_at(target_cuchuma, Vector3.UP)

	_setup_ui_styles()
	_connect_signals()

	# Iniciar mostrando la pantalla de inicio principal
	current_screen_state = MenuScreenState.MAIN_MENU
	if main_menu_container:
		main_menu_container.visible = true
		main_menu_container.modulate = Color(1.0, 1.0, 1.0, 1.0)
	if char_select_container:
		char_select_container.visible = false
		char_select_container.modulate = Color(1.0, 1.0, 1.0, 0.0)

	open_menu(true)

func _connect_signals() -> void:
	# Botones del menú principal
	if btn_continue:
		btn_continue.pressed.connect(_on_continue_pressed)
		_setup_button_hover_events(btn_continue)

	if btn_respawn:
		btn_respawn.pressed.connect(_on_respawn_pressed)
		_setup_button_hover_events(btn_respawn)

	if btn_quit:
		btn_quit.pressed.connect(_on_quit_pressed)
		_setup_button_hover_events(btn_quit)

	# Botones de selección de personaje
	if btn_select_axel:
		btn_select_axel.pressed.connect(func(): _select_character("axel"))
		_setup_button_hover_events(btn_select_axel)

	if btn_select_eli:
		btn_select_eli.pressed.connect(func(): _select_character("eli"))
		_setup_button_hover_events(btn_select_eli)

	if btn_confirm_selection:
		btn_confirm_selection.pressed.connect(_on_confirm_selection_pressed)
		_setup_button_hover_events(btn_confirm_selection)

	if btn_back_to_main:
		btn_back_to_main.pressed.connect(_on_back_to_main_pressed)
		_setup_button_hover_events(btn_back_to_main)

func _setup_button_hover_events(btn: Button) -> void:
	if not btn:
		return
	btn.mouse_entered.connect(_on_button_hover.bind(btn, true))
	btn.mouse_exited.connect(_on_button_hover.bind(btn, false))
	btn.focus_entered.connect(_on_button_hover.bind(btn, true))
	btn.focus_exited.connect(_on_button_hover.bind(btn, false))

func _setup_ui_styles() -> void:
	var din_font = load("res://assets/fonts/DIN_Condensed_Bold.ttf")

	# Tipografía de títulos
	if din_font:
		if title_label: title_label.add_theme_font_override("font", din_font)
		if subtitle_label: subtitle_label.add_theme_font_override("font", din_font)
		if char_select_title: char_select_title.add_theme_font_override("font", din_font)
		if char_select_subtitle: char_select_subtitle.add_theme_font_override("font", din_font)
		if name_axel_label: name_axel_label.add_theme_font_override("font", din_font)
		if codename_axel_label: codename_axel_label.add_theme_font_override("font", din_font)
		if name_eli_label: name_eli_label.add_theme_font_override("font", din_font)
		if codename_eli_label: codename_eli_label.add_theme_font_override("font", din_font)

	# Estilos de botones principales
	for btn in [btn_continue, btn_respawn, btn_quit]:
		if not btn: continue
		if din_font: btn.add_theme_font_override("font", din_font)
		btn.add_theme_font_size_override("font_size", 34)
		btn.alignment = HORIZONTAL_ALIGNMENT_LEFT
		btn.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
		_apply_menu_button_style(btn)

	# Estilos de botones de selección
	for btn in [btn_select_axel, btn_select_eli, btn_confirm_selection, btn_back_to_main]:
		if not btn: continue
		if din_font: btn.add_theme_font_override("font", din_font)
		btn.add_theme_font_size_override("font_size", 24)
		btn.alignment = HORIZONTAL_ALIGNMENT_CENTER
		btn.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
		_apply_action_button_style(btn)

	# Estilos de tarjetas de personajes
	_update_card_styles()

func _apply_menu_button_style(btn: Button) -> void:
	btn.add_theme_color_override("font_color", Color(0.96, 0.95, 0.92, 1.0))
	btn.add_theme_color_override("font_hover_color", Color(1.0, 0.78, 0.25, 1.0))
	btn.add_theme_color_override("font_focus_color", Color(1.0, 0.78, 0.25, 1.0))
	btn.add_theme_color_override("font_pressed_color", Color(0.85, 0.16, 0.16, 1.0))
	btn.add_theme_color_override("font_shadow_color", Color(0.04, 0.05, 0.08, 0.85))
	btn.add_theme_constant_override("shadow_offset_x", 1)
	btn.add_theme_constant_override("shadow_offset_y", 2)
	btn.add_theme_constant_override("shadow_outline_size", 3)

	var style_normal = StyleBoxEmpty.new()
	style_normal.content_margin_left = 6
	style_normal.content_margin_top = 4
	style_normal.content_margin_bottom = 4
	style_normal.content_margin_right = 16
	btn.add_theme_stylebox_override("normal", style_normal)

	var style_hover = StyleBoxFlat.new()
	style_hover.bg_color = Color(0.08, 0.10, 0.13, 0.65)
	style_hover.border_width_left = 4
	style_hover.border_color = Color(0.85, 0.16, 0.16, 1.0) # Rojo Tecate
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
	style_pressed.bg_color = Color(0.05, 0.07, 0.10, 0.85)
	style_pressed.border_color = Color(1.0, 0.72, 0.0, 1.0) # Dorado Sol
	btn.add_theme_stylebox_override("pressed", style_pressed)

func _apply_action_button_style(btn: Button) -> void:
	btn.add_theme_color_override("font_color", Color(0.96, 0.95, 0.92, 1.0))
	btn.add_theme_color_override("font_hover_color", Color(1.0, 0.85, 0.35, 1.0))
	btn.add_theme_color_override("font_focus_color", Color(1.0, 0.85, 0.35, 1.0))
	btn.add_theme_color_override("font_pressed_color", Color(0.85, 0.16, 0.16, 1.0))

	var style_normal = StyleBoxFlat.new()
	style_normal.bg_color = Color(0.08, 0.10, 0.14, 0.82)
	style_normal.border_width_left = 2
	style_normal.border_width_top = 2
	style_normal.border_width_right = 2
	style_normal.border_width_bottom = 2
	style_normal.border_color = Color(0.85, 0.16, 0.16, 0.70) # Rojo Tecate
	style_normal.corner_radius_top_left = 6
	style_normal.corner_radius_bottom_left = 6
	style_normal.corner_radius_top_right = 6
	style_normal.corner_radius_bottom_right = 6
	style_normal.content_margin_left = 16
	style_normal.content_margin_right = 16
	style_normal.content_margin_top = 8
	style_normal.content_margin_bottom = 8
	btn.add_theme_stylebox_override("normal", style_normal)

	var style_hover = style_normal.duplicate()
	style_hover.bg_color = Color(0.12, 0.15, 0.20, 0.92)
	style_hover.border_color = Color(1.0, 0.72, 0.0, 1.0) # Dorado Sol
	btn.add_theme_stylebox_override("hover", style_hover)
	btn.add_theme_stylebox_override("focus", style_hover)

	var style_pressed = style_hover.duplicate()
	style_pressed.bg_color = Color(0.05, 0.07, 0.10, 0.95)
	btn.add_theme_stylebox_override("pressed", style_pressed)

func _update_card_styles() -> void:
	_style_card_panel(card_axel_panel, selected_character_id == "axel", Color(0.85, 0.16, 0.16, 1.0)) # Rojo Tecate
	_style_card_panel(card_eli_panel, selected_character_id == "eli", Color(0.0, 0.33, 0.72, 1.0)) # Azul Cobalto

func _style_card_panel(panel: PanelContainer, is_selected: bool, accent_color: Color = Color(1.0, 0.72, 0.0, 1.0)) -> void:
	if not panel:
		return
	var style = StyleBoxFlat.new()
	style.corner_radius_top_left = 12
	style.corner_radius_top_right = 12
	style.corner_radius_bottom_left = 12
	style.corner_radius_bottom_right = 12

	if is_selected:
		style.bg_color = Color(0.08, 0.10, 0.14, 0.90)
		style.border_width_left = 3
		style.border_width_top = 3
		style.border_width_right = 3
		style.border_width_bottom = 3
		style.border_color = accent_color
		style.shadow_color = Color(accent_color.r, accent_color.g, accent_color.b, 0.35)
		style.shadow_size = 14
	else:
		style.bg_color = Color(0.05, 0.06, 0.08, 0.70)
		style.border_width_left = 1
		style.border_width_top = 1
		style.border_width_right = 1
		style.border_width_bottom = 1
		style.border_color = Color(0.35, 0.38, 0.44, 0.4)
		style.shadow_color = Color(0.0, 0.0, 0.0, 0.5)
		style.shadow_size = 6

	panel.add_theme_stylebox_override("panel", style)

func _on_button_hover(btn: Button, hovered: bool) -> void:
	if not btn:
		return
	var tween = create_tween().set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	var target_mod = Color(1.15, 1.15, 1.15) if hovered else Color(1.0, 1.0, 1.0)
	tween.tween_property(btn, "modulate", target_mod, 0.12)

func _process(delta: float) -> void:
	if is_menu_active and menu_camera and not _is_transitioning:
		_time += delta
		var drift_x = sin(_time * ambient_drift_speed) * 0.8
		var drift_y = cos(_time * (ambient_drift_speed * 0.75)) * 0.25

		if current_screen_state == MenuScreenState.MAIN_MENU:
			menu_camera.global_position = initial_cam_position + Vector3(drift_x, drift_y, 0.0)
			menu_camera.look_at(target_cuchuma, Vector3.UP)
		elif current_screen_state == MenuScreenState.CHARACTER_SELECT:
			menu_camera.global_position = topdown_cam_position + Vector3(drift_x * 0.5, drift_y * 0.3, 0.0)
			menu_camera.look_at(topdown_cam_target, Vector3.UP)

func open_menu(_instant: bool = false) -> void:
	if _camera_tween and _camera_tween.is_valid():
		_camera_tween.kill()
	_is_transitioning = false

	is_menu_active = true
	var vp = get_viewport()
	var current_cam = vp.get_camera_3d() if vp else null
	if current_cam and current_cam != menu_camera:
		_previous_camera = current_cam

	if canvas_layer:
		canvas_layer.visible = true
	if menu_camera:
		menu_camera.make_current()
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE

	if player and player.has_method("set_input_enabled"):
		player.set_input_enabled(false)

	# Mostrar el menú principal
	current_screen_state = MenuScreenState.MAIN_MENU
	if main_menu_container:
		main_menu_container.visible = true
		main_menu_container.modulate = Color(1.0, 1.0, 1.0, 1.0)
	if char_select_container:
		char_select_container.visible = false
		char_select_container.modulate = Color(1.0, 1.0, 1.0, 0.0)

	if menu_camera:
		menu_camera.global_position = initial_cam_position
		menu_camera.look_at(target_cuchuma, Vector3.UP)

	if btn_continue:
		btn_continue.grab_focus()

func close_menu() -> void:
	if _camera_tween and _camera_tween.is_valid():
		_camera_tween.kill()
	_is_transitioning = false

	is_menu_active = false
	if canvas_layer:
		canvas_layer.visible = false

	if is_instance_valid(_previous_camera):
		_previous_camera.make_current()
	elif player:
		var player_cam = player.camera if ("camera" in player and player.camera) else player.get_node_or_null("Camera3D")
		if player_cam and player_cam is Camera3D:
			player_cam.make_current()

	if player and player.has_method("set_input_enabled"):
		player.set_input_enabled(true)

	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	_previous_camera = null

func toggle_menu() -> void:
	if is_menu_active:
		_on_continue_pressed()
	else:
		open_menu()

# =============================================================================
# TRANSICIONES CINEMÁTICAS Y NAVEGACIÓN
# =============================================================================

func _on_continue_pressed() -> void:
	if not has_chosen_character:
		# Primera vez sin personaje: abrir selección de personaje
		_pending_action = PendingAction.CONTINUE
		transition_to_character_select()
	else:
		# Ya se eligió personaje previamente: reanudar inmediatamente
		close_menu()
		game_continued.emit()

func _on_respawn_pressed() -> void:
	# Siempre abre la pantalla de selección tras reaparecer
	_pending_action = PendingAction.RESPAWN
	transition_to_character_select()

func _on_quit_pressed() -> void:
	game_exited.emit()
	get_tree().quit()

func _select_character(char_id: String) -> void:
	selected_character_id = char_id
	_update_card_styles()

func _on_confirm_selection_pressed() -> void:
	if selected_character_id.is_empty():
		selected_character_id = CharacterCatalogClass.get_default_character_id()

	has_chosen_character = true
	_update_card_styles()

	# Aplicar identidad al jugador local
	if player and player.has_method("apply_identity"):
		player.apply_identity(selected_character_id)

	# Sincronizar selección con el servidor TKT/1
	if network_client and network_client.has_method("send_character_select"):
		network_client.send_character_select(selected_character_id)

	character_selected.emit(selected_character_id)

	var action_to_resolve = _pending_action
	_pending_action = PendingAction.NONE

	if action_to_resolve == PendingAction.RESPAWN:
		if player and player.has_method("respawn"):
			player.respawn()
		close_menu()
		game_respawned.emit()
	else:
		close_menu()
		game_continued.emit()

func _on_back_to_main_pressed() -> void:
	_pending_action = PendingAction.NONE
	transition_to_main_menu()

func transition_to_character_select() -> void:
	if _camera_tween and _camera_tween.is_valid():
		_camera_tween.kill()
	_is_transitioning = true
	current_screen_state = MenuScreenState.CHARACTER_SELECT

	if selected_character_id.is_empty():
		selected_character_id = CharacterCatalogClass.get_default_character_id()
	_update_card_styles()

	char_select_container.visible = true
	char_select_container.modulate = Color(1.0, 1.0, 1.0, 0.0)

	# Calcular orientación cenital mirando hacia el mapa desde arriba
	var look_dir = (topdown_cam_target - topdown_cam_position).normalized()
	var target_basis = Transform3D.IDENTITY.looking_at(look_dir, Vector3.UP).basis
	var target_quat = target_basis.get_rotation_quaternion()

	_camera_tween = create_tween().set_parallel(true).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN_OUT)
	_camera_tween.tween_property(menu_camera, "global_position", topdown_cam_position, 1.1)
	_camera_tween.tween_property(menu_camera, "quaternion", target_quat, 1.1)
	_camera_tween.tween_property(main_menu_container, "modulate:a", 0.0, 0.4)
	_camera_tween.tween_property(char_select_container, "modulate:a", 1.0, 0.8)

	_camera_tween.chain().tween_callback(func():
		_is_transitioning = false
		main_menu_container.visible = false
		if btn_confirm_selection:
			btn_confirm_selection.grab_focus()
	)

func transition_to_main_menu() -> void:
	if _camera_tween and _camera_tween.is_valid():
		_camera_tween.kill()
	_is_transitioning = true
	current_screen_state = MenuScreenState.MAIN_MENU

	main_menu_container.visible = true

	# Calcular orientación mirando al Cuchumá
	var look_dir = (target_cuchuma - initial_cam_position).normalized()
	var target_basis = Transform3D.IDENTITY.looking_at(look_dir, Vector3.UP).basis
	var target_quat = target_basis.get_rotation_quaternion()

	_camera_tween = create_tween().set_parallel(true).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN_OUT)
	_camera_tween.tween_property(menu_camera, "global_position", initial_cam_position, 1.1)
	_camera_tween.tween_property(menu_camera, "quaternion", target_quat, 1.1)
	_camera_tween.tween_property(char_select_container, "modulate:a", 0.0, 0.4)
	_camera_tween.tween_property(main_menu_container, "modulate:a", 1.0, 0.8)

	_camera_tween.chain().tween_callback(func():
		_is_transitioning = false
		char_select_container.visible = false
		if btn_continue:
			btn_continue.grab_focus()
	)
