class_name PhoneMenu
extends CanvasLayer

## Interfaz Diegética del Teléfono Celular Motorola MOTOKRZR K1 (Años 2000).
##
## Representa el teléfono personal del protagonista en Tecate Simulator.
## Brinda acceso a las Retas y Actividades Urbanas (reemplazo diegético del
## menú de minijuegos), agenda comunitaria, telemetría y llamadas en red,
## emulando la interfaz Motorola Synergy OS de 2006-2009 en una pantalla TFT de 176x220
## con teclado plano retroiluminado electroluminiscente azul.

signal menu_opened
signal menu_closed
signal minigame_launched(game_id: int)
signal location_teleported(location_id: String, target_pos: Vector3)

const MinigameCatalogClass = preload("res://systems/minigames/minigame_catalog.gd")

enum PhoneScreenState {
	IDLE,
	MAIN_MENU,
	ACTIVITIES_LIST,
	ACTIVITY_DETAIL
}

@export var minigame_manager_path: NodePath = ^"../MinigameManager"
@export var player_path: NodePath = ^"../Player"

var minigame_manager: Node = null
var player: Node = null

var is_open: bool = false
var current_screen: PhoneScreenState = PhoneScreenState.ACTIVITIES_LIST
var current_category: int = MinigameCatalogClass.Category.ALL
var current_location_filter: String = ""
var selected_game_id: int = 1
var selected_menu_index: int = 2 # Inicia resaltando el icono de Retas en la matriz 3x3

# Contenedores raíz y marco físico del teléfono K1
var root_control: Control = null
var backdrop: ColorRect = null
var phone_chassis: PanelContainer = null
var screen_viewport_container: PanelContainer = null
var screen_content_stack: Control = null

# Elementos de la barra de estado superior
var status_bar: HBoxContainer = null
var signal_label: Label = null
var operator_label: Label = null
var clock_label: Label = null
var battery_label: Label = null

# Pantallas del celular
var screen_idle_node: Control = null
var screen_main_menu_node: Control = null
var screen_activities_node: Control = null
var screen_detail_node: Control = null

# Softkeys inferiores de la pantalla
var softkeys_hbox: HBoxContainer = null
var softkey_left_label: Label = null
var softkey_center_label: Label = null
var softkey_right_label: Label = null

# Componentes de la lista de actividades
var category_tabs_hbox: HBoxContainer = null
var category_tab_buttons: Dictionary = {}
var activities_vbox: VBoxContainer = null
var location_filter_chip: Label = null
var activity_item_buttons: Dictionary = {}

# Componentes de la ficha de detalle
var detail_title_label: Label = null
var detail_category_label: Label = null
var detail_location_label: Label = null
var detail_description_label: Label = null
var detail_controls_label: Label = null
var btn_summon_action: Button = null
var btn_teleport_action: Button = null

# Compatibilidad con suites de pruebas y sistemas anteriores
var game_tile_buttons: Dictionary:
	get:
		return activity_item_buttons

var location_filter_banner: Control:
	get:
		return location_filter_chip

var preview_title_label: Label:
	get:
		return detail_title_label

func _on_play_pressed() -> void:
	_on_summon_pressed()

# Matriz 3x3 del menú principal
var menu_grid_buttons: Array[Button] = []

var _din_font: Font = null
var _previous_mouse_mode: Input.MouseMode = Input.MOUSE_MODE_CAPTURED
var _phone_tween: Tween = null

func _ready() -> void:
	layer = 45
	visible = false
	_din_font = load("res://assets/fonts/DIN_Condensed_Bold.ttf")
	_resolve_dependencies()
	_build_motorola_k1_ui()
	select_category(MinigameCatalogClass.Category.ALL)
	select_minigame(1)
	set_process_unhandled_input(true)

func _resolve_dependencies() -> void:
	if has_node(minigame_manager_path):
		minigame_manager = get_node(minigame_manager_path)
	elif get_parent() and get_parent().has_node(AppTechnicalStrings.NODE_MINIGAME_MANAGER):
		minigame_manager = get_parent().get_node(AppTechnicalStrings.NODE_MINIGAME_MANAGER)

	if minigame_manager and not minigame_manager.minigame_started.is_connected(_on_minigame_started_close_menu):
		minigame_manager.minigame_started.connect(_on_minigame_started_close_menu)

	if has_node(player_path):
		player = get_node(player_path)
	elif get_parent() and get_parent().has_node(AppTechnicalStrings.NODE_PLAYER):
		player = get_parent().get_node(AppTechnicalStrings.NODE_PLAYER)

func _on_minigame_started_close_menu(_game_id: int, _countdown: int, _participants: Array) -> void:
	if is_open:
		close_menu()

## Abre el teléfono celular, opcionalmente filtrando por ubicación
func open_menu(location_id: String = "") -> void:
	if is_open:
		if not location_id.is_empty() and location_id != current_location_filter:
			set_location_filter(location_id)
		return

	is_open = true
	visible = true
	_previous_mouse_mode = Input.mouse_mode
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE

	if not location_id.is_empty():
		current_location_filter = location_id
		current_screen = PhoneScreenState.ACTIVITIES_LIST
	else:
		current_screen = PhoneScreenState.ACTIVITIES_LIST

	_update_location_filter_banner()
	_refresh_activities_list()
	_switch_screen(current_screen)
	_animate_open()
	menu_opened.emit()

## Cierra el teléfono celular y reanuda el control
func close_menu() -> void:
	if not is_open:
		return

	is_open = false
	Input.mouse_mode = _previous_mouse_mode
	_animate_close()
	menu_closed.emit()

## Alterna el estado de apertura del teléfono
func toggle_menu(location_id: String = "") -> void:
	if is_open:
		close_menu()
	else:
		open_menu(location_id)

## Selecciona una actividad por su ID
func select_minigame(game_id: int) -> void:
	selected_game_id = game_id
	var g = MinigameCatalogClass.get_minigame(game_id)
	if g.is_empty():
		return
	_populate_activity_detail(g)

## Aplica filtro por zona o ubicación geográfica
func set_location_filter(location_id: String) -> void:
	current_location_filter = location_id
	_update_location_filter_banner()
	_refresh_activities_list()

## Selecciona una categoría de actividades
func select_category(cat_id: int) -> void:
	current_category = cat_id
	for c_key in category_tab_buttons.keys():
		var btn = category_tab_buttons[c_key] as Button
		if c_key == cat_id:
			_style_phone_tab(btn, true)
		else:
			_style_phone_tab(btn, false)
	_refresh_activities_list()

# =============================================================================
# CONSTRUCCIÓN VISUAL DEL MOTOROLA MOTOKRZR K1
# =============================================================================
func _build_motorola_k1_ui() -> void:
	root_control = Control.new()
	root_control.name = "MotorolaK1Root"
	root_control.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(root_control)

	# Fondo translúcido sutil que enfoca la vista hacia el dispositivo
	backdrop = ColorRect.new()
	backdrop.name = "Backdrop"
	backdrop.set_anchors_preset(Control.PRESET_FULL_RECT)
	backdrop.color = Color(0.02, 0.04, 0.08, 0.55)
	root_control.add_child(backdrop)

	# Chasis del teléfono celular (formato concha vertical esbelto)
	# Dimensiones auténticas del K1: angosto, alargado, con esquinas redondeadas
	phone_chassis = PanelContainer.new()
	phone_chassis.name = "MotorolaK1Chassis"
	phone_chassis.custom_minimum_size = Vector2(360, 680)
	phone_chassis.set_anchors_preset(Control.PRESET_CENTER_RIGHT)
	phone_chassis.anchor_right = 0.96
	phone_chassis.anchor_bottom = 0.95
	phone_chassis.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	phone_chassis.grow_vertical = Control.GROW_DIRECTION_BEGIN

	var style_chassis = StyleBoxFlat.new()
	style_chassis.bg_color = Color(0.06, 0.12, 0.22, 1.0) # Cosmic Blue metalizado
	style_chassis.border_width_left = 6
	style_chassis.border_width_top = 8
	style_chassis.border_width_right = 6
	style_chassis.border_width_bottom = 12
	style_chassis.border_color = Color(0.32, 0.52, 0.78, 1.0) # Bisel magnesio reflectante
	style_chassis.corner_radius_top_left = 32
	style_chassis.corner_radius_top_right = 32
	style_chassis.corner_radius_bottom_left = 34
	style_chassis.corner_radius_bottom_right = 34
	style_chassis.shadow_color = Color(0.0, 0.0, 0.0, 0.65)
	style_chassis.shadow_size = 24
	style_chassis.content_margin_left = 16
	style_chassis.content_margin_right = 16
	style_chassis.content_margin_top = 14
	style_chassis.content_margin_bottom = 16
	phone_chassis.add_theme_stylebox_override("panel", style_chassis)
	root_control.add_child(phone_chassis)

	var body_vbox = VBoxContainer.new()
	body_vbox.add_theme_constant_override("separation", 10)
	phone_chassis.add_child(body_vbox)

	# 1. Auricular superior y logotipo grabado
	var earpiece_box = HBoxContainer.new()
	earpiece_box.alignment = BoxContainer.ALIGNMENT_CENTER
	body_vbox.add_child(earpiece_box)

	var earpiece = PanelContainer.new()
	earpiece.custom_minimum_size = Vector2(50, 6)
	var style_earpiece = StyleBoxFlat.new()
	style_earpiece.bg_color = Color(0.18, 0.25, 0.35, 1.0)
	style_earpiece.border_width_bottom = 1
	style_earpiece.border_color = Color(0.55, 0.72, 0.95, 1.0)
	style_earpiece.corner_radius_top_left = 3
	style_earpiece.corner_radius_top_right = 3
	style_earpiece.corner_radius_bottom_left = 3
	style_earpiece.corner_radius_bottom_right = 3
	earpiece.add_theme_stylebox_override("panel", style_earpiece)
	earpiece_box.add_child(earpiece)

	# 2. Marco de Pantalla TFT (Aspect ratio emulado 176x220)
	screen_viewport_container = PanelContainer.new()
	screen_viewport_container.name = "ScreenViewportContainer"
	screen_viewport_container.custom_minimum_size = Vector2(320, 360)
	screen_viewport_container.size_flags_vertical = Control.SIZE_EXPAND_FILL

	var style_screen_frame = StyleBoxFlat.new()
	style_screen_frame.bg_color = Color(0.03, 0.07, 0.14, 1.0) # Fondo LCD TFT
	style_screen_frame.border_width_left = 4
	style_screen_frame.border_width_top = 4
	style_screen_frame.border_width_right = 4
	style_screen_frame.border_width_bottom = 4
	style_screen_frame.border_color = Color(0.10, 0.16, 0.25, 1.0)
	style_screen_frame.corner_radius_top_left = 10
	style_screen_frame.corner_radius_top_right = 10
	style_screen_frame.corner_radius_bottom_left = 10
	style_screen_frame.corner_radius_bottom_right = 10
	style_screen_frame.content_margin_left = 10
	style_screen_frame.content_margin_right = 10
	style_screen_frame.content_margin_top = 8
	style_screen_frame.content_margin_bottom = 8
	screen_viewport_container.add_theme_stylebox_override("panel", style_screen_frame)
	body_vbox.add_child(screen_viewport_container)

	var screen_vbox = VBoxContainer.new()
	screen_vbox.add_theme_constant_override("separation", 6)
	screen_viewport_container.add_child(screen_vbox)

	# 2A. Barra de Estado Superior (Status Bar Motorola Synergy)
	status_bar = HBoxContainer.new()
	status_bar.name = "StatusBar"
	screen_vbox.add_child(status_bar)

	signal_label = Label.new()
	signal_label.text = "📶"
	signal_label.add_theme_font_size_override("font_size", 14)
	status_bar.add_child(signal_label)

	operator_label = Label.new()
	operator_label.text = AppStrings.PHONE_OPERATOR_NAME
	operator_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	if _din_font:
		operator_label.add_theme_font_override("font", _din_font)
	operator_label.add_theme_font_size_override("font_size", 16)
	operator_label.add_theme_color_override("font_color", Color(0.70, 0.85, 1.0, 1.0))
	status_bar.add_child(operator_label)

	clock_label = Label.new()
	clock_label.text = AppStrings.PHONE_DEFAULT_TIME
	if _din_font:
		clock_label.add_theme_font_override("font", _din_font)
	clock_label.add_theme_font_size_override("font_size", 16)
	clock_label.add_theme_color_override("font_color", Color(1.0, 1.0, 1.0, 1.0))
	status_bar.add_child(clock_label)

	battery_label = Label.new()
	battery_label.text = " 🔋"
	battery_label.add_theme_font_size_override("font_size", 14)
	status_bar.add_child(battery_label)

	# Divisor fino de pantalla
	var screen_div = ColorRect.new()
	screen_div.custom_minimum_size = Vector2(0, 1)
	screen_div.color = Color(0.15, 0.30, 0.50, 0.8)
	screen_vbox.add_child(screen_div)

	# 2B. Stack de contenido de pantalla
	screen_content_stack = Control.new()
	screen_content_stack.name = "ScreenContentStack"
	screen_content_stack.size_flags_vertical = Control.SIZE_EXPAND_FILL
	screen_vbox.add_child(screen_content_stack)

	_build_activities_screen()
	_build_detail_screen()
	_build_main_menu_screen()

	# 2C. Barra inferior de Softkeys de pantalla
	var softkeys_panel = PanelContainer.new()
	var style_softkeys = StyleBoxFlat.new()
	style_softkeys.bg_color = Color(0.05, 0.12, 0.22, 0.95)
	style_softkeys.content_margin_left = 6
	style_softkeys.content_margin_right = 6
	style_softkeys.content_margin_top = 4
	style_softkeys.content_margin_bottom = 4
	softkeys_panel.add_theme_stylebox_override("panel", style_softkeys)
	screen_vbox.add_child(softkeys_panel)

	softkeys_hbox = HBoxContainer.new()
	softkeys_panel.add_child(softkeys_hbox)

	softkey_left_label = Label.new()
	softkey_left_label.text = AppStrings.PHONE_SOFTKEY_MENU
	softkey_left_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	if _din_font:
		softkey_left_label.add_theme_font_override("font", _din_font)
	softkey_left_label.add_theme_font_size_override("font_size", 16)
	softkey_left_label.add_theme_color_override("font_color", Color(0.0, 0.90, 1.0, 1.0))
	softkeys_hbox.add_child(softkey_left_label)

	softkey_center_label = Label.new()
	softkey_center_label.text = AppStrings.PHONE_SOFTKEY_SELECT
	softkey_center_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	softkey_center_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	if _din_font:
		softkey_center_label.add_theme_font_override("font", _din_font)
	softkey_center_label.add_theme_font_size_override("font_size", 16)
	softkey_center_label.add_theme_color_override("font_color", Color(1.0, 1.0, 1.0, 0.9))
	softkeys_hbox.add_child(softkey_center_label)

	softkey_right_label = Label.new()
	softkey_right_label.text = AppStrings.PHONE_SOFTKEY_EXIT
	softkey_right_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	softkey_right_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	if _din_font:
		softkey_right_label.add_theme_font_override("font", _din_font)
	softkey_right_label.add_theme_font_size_override("font_size", 16)
	softkey_right_label.add_theme_color_override("font_color", Color(0.0, 0.90, 1.0, 1.0))
	softkeys_hbox.add_child(softkey_right_label)

	# 3. Bisagra central estilizada
	var hinge = PanelContainer.new()
	hinge.custom_minimum_size = Vector2(0, 14)
	var style_hinge = StyleBoxFlat.new()
	style_hinge.bg_color = Color(0.12, 0.20, 0.32, 1.0)
	style_hinge.border_width_top = 2
	style_hinge.border_width_bottom = 2
	style_hinge.border_color = Color(0.40, 0.60, 0.85, 1.0)
	hinge.add_theme_stylebox_override("panel", style_hinge)
	body_vbox.add_child(hinge)

	# 4. Teclado Metálico Grabado al Láser (Lámina azul electroluminiscente)
	_build_laser_keypad(body_vbox)

# =============================================================================
# PANTALLA DE ACTIVIDADES Y RETAS DE TECATE
# =============================================================================
func _build_activities_screen() -> void:
	screen_activities_node = VBoxContainer.new()
	screen_activities_node.name = "ActivitiesScreen"
	screen_activities_node.set_anchors_preset(Control.PRESET_FULL_RECT)
	screen_activities_node.add_theme_constant_override("separation", 6)
	screen_content_stack.add_child(screen_activities_node)

	# Encabezado de la aplicación
	var title_banner = PanelContainer.new()
	var style_tb = StyleBoxFlat.new()
	style_tb.bg_color = Color(0.0, 0.38, 0.72, 1.0)
	style_tb.corner_radius_top_left = 6
	style_tb.corner_radius_top_right = 6
	style_tb.corner_radius_bottom_left = 6
	style_tb.corner_radius_bottom_right = 6
	style_tb.content_margin_left = 8
	style_tb.content_margin_right = 8
	style_tb.content_margin_top = 3
	style_tb.content_margin_bottom = 3
	title_banner.add_theme_stylebox_override("panel", style_tb)
	screen_activities_node.add_child(title_banner)

	var title_lbl = Label.new()
	title_lbl.text = "🏆 %s" % AppStrings.MINIGAMES_HEADER_TITLE
	if _din_font:
		title_lbl.add_theme_font_override("font", _din_font)
	title_lbl.add_theme_font_size_override("font_size", 18)
	title_lbl.add_theme_color_override("font_color", Color(1.0, 1.0, 1.0, 1.0))
	title_banner.add_child(title_lbl)

	# Pestañas de categoría (desplazables con izquierda/derecha)
	category_tabs_hbox = HBoxContainer.new()
	category_tabs_hbox.add_theme_constant_override("separation", 4)
	screen_activities_node.add_child(category_tabs_hbox)

	var cats = [
		MinigameCatalogClass.Category.ALL,
		MinigameCatalogClass.Category.ALL_VS_ALL,
		MinigameCatalogClass.Category.ONE_VS_ALL,
		MinigameCatalogClass.Category.DUEL_1V1
	]
	for cat_id in cats:
		var c_info = MinigameCatalogClass.CATEGORY_INFO[cat_id]
		var tab_b = Button.new()
		tab_b.name = "Tab_%d" % cat_id
		tab_b.text = c_info.get("short_name", "")
		tab_b.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
		if _din_font:
			tab_b.add_theme_font_override("font", _din_font)
		tab_b.add_theme_font_size_override("font_size", 14)
		_style_phone_tab(tab_b, cat_id == current_category)
		tab_b.pressed.connect(func():
			select_category(cat_id)
		)
		category_tabs_hbox.add_child(tab_b)
		category_tab_buttons[cat_id] = tab_b

	# Chip de filtro por ubicación si está activo
	location_filter_chip = Label.new()
	location_filter_chip.visible = false
	if _din_font:
		location_filter_chip.add_theme_font_override("font", _din_font)
	location_filter_chip.add_theme_font_size_override("font_size", 14)
	location_filter_chip.add_theme_color_override("font_color", Color(1.0, 0.85, 0.20, 1.0))
	screen_activities_node.add_child(location_filter_chip)

	# Lista vertical desplazable con las actividades
	var scroll = ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	screen_activities_node.add_child(scroll)

	activities_vbox = VBoxContainer.new()
	activities_vbox.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	activities_vbox.add_theme_constant_override("separation", 4)
	scroll.add_child(activities_vbox)

# =============================================================================
# PANTALLA DE FICHA DETALLADA DE LA ACTIVIDAD
# =============================================================================
func _build_detail_screen() -> void:
	screen_detail_node = VBoxContainer.new()
	screen_detail_node.name = "DetailScreen"
	screen_detail_node.visible = false
	screen_detail_node.set_anchors_preset(Control.PRESET_FULL_RECT)
	screen_detail_node.add_theme_constant_override("separation", 6)
	screen_content_stack.add_child(screen_detail_node)

	detail_title_label = Label.new()
	detail_title_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	if _din_font:
		detail_title_label.add_theme_font_override("font", _din_font)
	detail_title_label.add_theme_font_size_override("font_size", 20)
	detail_title_label.add_theme_color_override("font_color", Color(1.0, 0.90, 0.30, 1.0))
	screen_detail_node.add_child(detail_title_label)

	detail_category_label = Label.new()
	if _din_font:
		detail_category_label.add_theme_font_override("font", _din_font)
	detail_category_label.add_theme_font_size_override("font_size", 14)
	detail_category_label.add_theme_color_override("font_color", Color(0.30, 0.80, 1.0, 1.0))
	screen_detail_node.add_child(detail_category_label)

	detail_location_label = Label.new()
	detail_location_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	if _din_font:
		detail_location_label.add_theme_font_override("font", _din_font)
	detail_location_label.add_theme_font_size_override("font_size", 14)
	detail_location_label.add_theme_color_override("font_color", Color(0.80, 0.90, 0.80, 1.0))
	screen_detail_node.add_child(detail_location_label)

	var scroll_desc = ScrollContainer.new()
	scroll_desc.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll_desc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	screen_detail_node.add_child(scroll_desc)

	var desc_vbox = VBoxContainer.new()
	desc_vbox.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	desc_vbox.add_theme_constant_override("separation", 4)
	scroll_desc.add_child(desc_vbox)

	detail_description_label = Label.new()
	detail_description_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	detail_description_label.add_theme_font_size_override("font_size", 13)
	detail_description_label.add_theme_color_override("font_color", Color(0.85, 0.88, 0.92, 1.0))
	desc_vbox.add_child(detail_description_label)

	detail_controls_label = Label.new()
	detail_controls_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	detail_controls_label.add_theme_font_size_override("font_size", 12)
	detail_controls_label.add_theme_color_override("font_color", Color(0.65, 0.82, 0.95, 1.0))
	desc_vbox.add_child(detail_controls_label)

	# Botones de acción del teléfono
	var actions_row = HBoxContainer.new()
	actions_row.add_theme_constant_override("separation", 6)
	screen_detail_node.add_child(actions_row)

	btn_summon_action = Button.new()
	btn_summon_action.text = "📞 %s" % AppStrings.MINIGAMES_BTN_PLAY
	btn_summon_action.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	btn_summon_action.custom_minimum_size = Vector2(0, 34)
	btn_summon_action.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	if _din_font:
		btn_summon_action.add_theme_font_override("font", _din_font)
	btn_summon_action.add_theme_font_size_override("font_size", 17)
	_style_action_button(btn_summon_action, Color(0.12, 0.65, 0.28, 1.0))
	btn_summon_action.pressed.connect(_on_summon_pressed)
	actions_row.add_child(btn_summon_action)

	btn_teleport_action = Button.new()
	btn_teleport_action.text = "📍 %s" % AppStrings.MINIGAMES_BTN_TELEPORT
	btn_teleport_action.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	btn_teleport_action.custom_minimum_size = Vector2(0, 34)
	btn_teleport_action.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	if _din_font:
		btn_teleport_action.add_theme_font_override("font", _din_font)
	btn_teleport_action.add_theme_font_size_override("font_size", 17)
	_style_action_button(btn_teleport_action, Color(0.15, 0.45, 0.85, 1.0))
	btn_teleport_action.pressed.connect(_on_teleport_pressed)
	actions_row.add_child(btn_teleport_action)

# =============================================================================
# PANTALLA DEL MENÚ PRINCIPAL (MATRIZ 3x3 SYNERGY OS)
# =============================================================================
func _build_main_menu_screen() -> void:
	screen_main_menu_node = VBoxContainer.new()
	screen_main_menu_node.name = "MainMenuScreen"
	screen_main_menu_node.visible = false
	screen_main_menu_node.set_anchors_preset(Control.PRESET_FULL_RECT)
	screen_main_menu_node.add_theme_constant_override("separation", 8)
	screen_content_stack.add_child(screen_main_menu_node)

	var mm_title = Label.new()
	mm_title.text = "MOTOROLA SYNERGY"
	mm_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	if _din_font:
		mm_title.add_theme_font_override("font", _din_font)
	mm_title.add_theme_font_size_override("font_size", 16)
	mm_title.add_theme_color_override("font_color", Color(0.35, 0.65, 0.95, 1.0))
	screen_main_menu_node.add_child(mm_title)

	var grid = GridContainer.new()
	grid.columns = 3
	grid.size_flags_vertical = Control.SIZE_EXPAND_FILL
	grid.add_theme_constant_override("h_separation", 6)
	grid.add_theme_constant_override("v_separation", 6)
	screen_main_menu_node.add_child(grid)

	var apps = [
		{"icon": "✉", "name": AppStrings.PHONE_APP_MESSAGES, "id": 0},
		{"icon": "👥", "name": AppStrings.PHONE_APP_CONTACTS, "id": 1},
		{"icon": "🏆", "name": AppStrings.PHONE_APP_ACTIVITIES, "id": 2},
		{"icon": "📷", "name": AppStrings.PHONE_APP_CAMERA, "id": 3},
		{"icon": "🎵", "name": AppStrings.PHONE_APP_MULTIMEDIA, "id": 4},
		{"icon": "🗺", "name": AppStrings.PHONE_APP_CITY_GUIDE, "id": 5},
		{"icon": "⚙", "name": AppStrings.PHONE_APP_SETTINGS, "id": 6},
		{"icon": "⏰", "name": AppStrings.PHONE_APP_ALARM_CLOCK, "id": 7},
		{"icon": "🏛", "name": AppStrings.PHONE_APP_MUNICIPAL_GAZETTE, "id": 8}
	]

	menu_grid_buttons.clear()
	for app in apps:
		var app_btn = Button.new()
		app_btn.text = "%s\n%s" % [app["icon"], app["name"]]
		app_btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		app_btn.size_flags_vertical = Control.SIZE_EXPAND_FILL
		app_btn.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
		if _din_font:
			app_btn.add_theme_font_override("font", _din_font)
		app_btn.add_theme_font_size_override("font_size", 13)
		_style_matrix_button(app_btn, app["id"] == selected_menu_index)

		var app_id: int = app["id"]
		app_btn.pressed.connect(func():
			_on_matrix_app_selected(app_id)
		)
		grid.add_child(app_btn)
		menu_grid_buttons.append(app_btn)

# =============================================================================
# CONSTRUCCIÓN DEL TECLADO GRABADO AL LÁSER
# =============================================================================
func _build_laser_keypad(parent: VBoxContainer) -> void:
	var keypad_panel = PanelContainer.new()
	keypad_panel.name = "LaserKeypad"
	var style_pad = StyleBoxFlat.new()
	style_pad.bg_color = Color(0.04, 0.08, 0.16, 0.98) # Azul metálico oscuro
	style_pad.border_width_top = 2
	style_pad.border_color = Color(0.0, 0.90, 1.0, 0.6) # Retroiluminación cian
	style_pad.corner_radius_bottom_left = 22
	style_pad.corner_radius_bottom_right = 22
	style_pad.content_margin_left = 10
	style_pad.content_margin_right = 10
	style_pad.content_margin_top = 8
	style_pad.content_margin_bottom = 10
	keypad_panel.add_theme_stylebox_override("panel", style_pad)
	parent.add_child(keypad_panel)

	var keypad_vbox = VBoxContainer.new()
	keypad_vbox.add_theme_constant_override("separation", 6)
	keypad_panel.add_child(keypad_vbox)

	# Fila 1: Tecla Llamar (Verde), D-Pad central (OK), Tecla Colgar/Salir (Roja)
	var nav_row = HBoxContainer.new()
	nav_row.add_theme_constant_override("separation", 8)
	keypad_vbox.add_child(nav_row)

	var btn_call = Button.new()
	btn_call.text = "📞"
	btn_call.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	btn_call.custom_minimum_size = Vector2(0, 36)
	_style_keypad_button(btn_call, Color(0.10, 0.55, 0.25, 0.9), Color(0.3, 1.0, 0.5, 1.0))
	btn_call.pressed.connect(_on_call_key_pressed)
	nav_row.add_child(btn_call)

	var btn_ok = Button.new()
	btn_ok.text = "• OK •"
	btn_ok.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	btn_ok.custom_minimum_size = Vector2(0, 36)
	if _din_font:
		btn_ok.add_theme_font_override("font", _din_font)
	btn_ok.add_theme_font_size_override("font_size", 16)
	_style_keypad_button(btn_ok, Color(0.12, 0.24, 0.40, 1.0), Color(0.0, 0.90, 1.0, 1.0))
	btn_ok.pressed.connect(_on_ok_key_pressed)
	nav_row.add_child(btn_ok)

	var btn_end = Button.new()
	btn_end.text = "🔴"
	btn_end.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	btn_end.custom_minimum_size = Vector2(0, 36)
	_style_keypad_button(btn_end, Color(0.65, 0.15, 0.15, 0.9), Color(1.0, 0.4, 0.4, 1.0))
	btn_end.pressed.connect(close_menu)
	nav_row.add_child(btn_end)

	# Teclado numérico grabado al láser 3x4
	var num_grid = GridContainer.new()
	num_grid.columns = 3
	num_grid.add_theme_constant_override("h_separation", 6)
	num_grid.add_theme_constant_override("v_separation", 4)
	keypad_vbox.add_child(num_grid)

	var keys = [
		"1", "2 ABC", "3 DEF",
		"4 GHI", "5 JKL", "6 MNO",
		"7 PQRS", "8 TUV", "9 WXYZ",
		"*", "0 +", "#"
	]
	for k in keys:
		var k_btn = Button.new()
		k_btn.text = k
		k_btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		k_btn.custom_minimum_size = Vector2(0, 24)
		if _din_font:
			k_btn.add_theme_font_override("font", _din_font)
		k_btn.add_theme_font_size_override("font_size", 13)
		_style_laser_num_key(k_btn)
		num_grid.add_child(k_btn)

# =============================================================================
# MANEJO DE ENTRADAS Y NAVEGACIÓN
# =============================================================================
func _unhandled_input(event: InputEvent) -> void:
	if not is_open:
		return

	if event is InputEventKey and event.pressed and not event.is_echo():
		match event.keycode:
			KEY_ESCAPE:
				_handle_back_key()
				get_viewport().set_input_as_handled()
			KEY_M:
				close_menu()
				get_viewport().set_input_as_handled()
			KEY_ENTER, KEY_SPACE:
				_on_ok_key_pressed()
				get_viewport().set_input_as_handled()
			KEY_UP:
				_navigate_vertical(-1)
				get_viewport().set_input_as_handled()
			KEY_DOWN:
				_navigate_vertical(1)
				get_viewport().set_input_as_handled()
			KEY_LEFT:
				_navigate_horizontal(-1)
				get_viewport().set_input_as_handled()
			KEY_RIGHT:
				_navigate_horizontal(1)
				get_viewport().set_input_as_handled()

func _handle_back_key() -> void:
	if current_screen == PhoneScreenState.ACTIVITY_DETAIL:
		_switch_screen(PhoneScreenState.ACTIVITIES_LIST)
	elif current_screen == PhoneScreenState.ACTIVITIES_LIST:
		_switch_screen(PhoneScreenState.MAIN_MENU)
	else:
		close_menu()

func _on_ok_key_pressed() -> void:
	if current_screen == PhoneScreenState.MAIN_MENU:
		_on_matrix_app_selected(selected_menu_index)
	elif current_screen == PhoneScreenState.ACTIVITIES_LIST:
		_switch_screen(PhoneScreenState.ACTIVITY_DETAIL)
	elif current_screen == PhoneScreenState.ACTIVITY_DETAIL:
		_on_summon_pressed()

func _on_call_key_pressed() -> void:
	if current_screen == PhoneScreenState.ACTIVITY_DETAIL:
		_on_summon_pressed()
	elif current_screen == PhoneScreenState.ACTIVITIES_LIST:
		_switch_screen(PhoneScreenState.ACTIVITY_DETAIL)
	else:
		_switch_screen(PhoneScreenState.ACTIVITIES_LIST)

func _navigate_vertical(direction: int) -> void:
	if current_screen == PhoneScreenState.ACTIVITIES_LIST:
		var games = _get_filtered_games()
		if games.is_empty():
			return
		var idx = 0
		for i in range(games.size()):
			if games[i]["id"] == selected_game_id:
				idx = i
				break
		idx = clampi(idx + direction, 0, games.size() - 1)
		select_minigame(games[idx]["id"])
		_highlight_selected_activity_button()
	elif current_screen == PhoneScreenState.MAIN_MENU:
		selected_menu_index = clampi(selected_menu_index + (direction * 3), 0, 8)
		_update_matrix_highlights()

func _navigate_horizontal(direction: int) -> void:
	if current_screen == PhoneScreenState.ACTIVITIES_LIST:
		# Cambiar entre pestañas de categoría
		var cats = [
			MinigameCatalogClass.Category.ALL,
			MinigameCatalogClass.Category.ALL_VS_ALL,
			MinigameCatalogClass.Category.ONE_VS_ALL,
			MinigameCatalogClass.Category.DUEL_1V1
		]
		var cur_idx = cats.find(current_category)
		var next_idx = (cur_idx + direction + cats.size()) % cats.size()
		select_category(cats[next_idx])
	elif current_screen == PhoneScreenState.MAIN_MENU:
		selected_menu_index = clampi(selected_menu_index + direction, 0, 8)
		_update_matrix_highlights()

func _on_matrix_app_selected(app_id: int) -> void:
	selected_menu_index = app_id
	_update_matrix_highlights()
	if app_id == 2: # Retas y Actividades
		_switch_screen(PhoneScreenState.ACTIVITIES_LIST)
	else:
		# Feedback temporal para apps complementarias
		softkey_center_label.text = "Cargando..."
		var t = get_tree().create_timer(0.4)
		t.timeout.connect(func():
			if is_instance_valid(softkey_center_label):
				softkey_center_label.text = AppStrings.PHONE_SOFTKEY_SELECT
		)

func _switch_screen(new_screen: PhoneScreenState) -> void:
	current_screen = new_screen
	if screen_activities_node:
		screen_activities_node.visible = (new_screen == PhoneScreenState.ACTIVITIES_LIST)
	if screen_detail_node:
		screen_detail_node.visible = (new_screen == PhoneScreenState.ACTIVITY_DETAIL)
	if screen_main_menu_node:
		screen_main_menu_node.visible = (new_screen == PhoneScreenState.MAIN_MENU)

	if new_screen == PhoneScreenState.ACTIVITIES_LIST:
		softkey_left_label.text = AppStrings.PHONE_SOFTKEY_MENU
		softkey_center_label.text = "Detalles"
		softkey_right_label.text = AppStrings.PHONE_SOFTKEY_EXIT
	elif new_screen == PhoneScreenState.ACTIVITY_DETAIL:
		softkey_left_label.text = AppStrings.PHONE_SOFTKEY_BACK
		softkey_center_label.text = AppStrings.PHONE_SOFTKEY_CALL
		softkey_right_label.text = AppStrings.PHONE_SOFTKEY_EXIT
	elif new_screen == PhoneScreenState.MAIN_MENU:
		softkey_left_label.text = ""
		softkey_center_label.text = AppStrings.PHONE_SOFTKEY_SELECT
		softkey_right_label.text = AppStrings.PHONE_SOFTKEY_BACK

# =============================================================================
# POBLADO DE DATOS Y REFRESH
# =============================================================================
func _get_filtered_games() -> Array[Dictionary]:
	var list: Array[Dictionary] = []
	if not current_location_filter.is_empty():
		list = MinigameCatalogClass.get_minigames_by_location(current_location_filter)
	elif current_category == MinigameCatalogClass.Category.ALL:
		list = MinigameCatalogClass.get_all_minigames()
	else:
		list = MinigameCatalogClass.get_minigames_by_category(current_category)
	return list

func _refresh_activities_list() -> void:
	if not activities_vbox:
		return

	for child in activities_vbox.get_children():
		child.queue_free()
	activity_item_buttons.clear()

	var games = _get_filtered_games()
	if games.is_empty():
		var empty_lbl = Label.new()
		empty_lbl.text = "Sin actividades registradas."
		empty_lbl.add_theme_font_size_override("font_size", 14)
		activities_vbox.add_child(empty_lbl)
		return

	var found_selected = false
	for g in games:
		if g["id"] == selected_game_id:
			found_selected = true
			break
	if not found_selected and not games.is_empty():
		selected_game_id = games[0]["id"]

	for g in games:
		var btn = Button.new()
		var g_id: int = g["id"]
		var title: String = g.get("title", "Reta")
		var loc: String = g.get("location_name", "Tecate")
		btn.text = "%02d. %s\n   📍 %s" % [g_id, title, loc]
		btn.alignment = HORIZONTAL_ALIGNMENT_LEFT
		btn.custom_minimum_size = Vector2(0, 40)
		btn.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
		if _din_font:
			btn.add_theme_font_override("font", _din_font)
		btn.add_theme_font_size_override("font_size", 14)

		_style_activity_item(btn, g_id == selected_game_id)
		btn.pressed.connect(func():
			select_minigame(g_id)
			_switch_screen(PhoneScreenState.ACTIVITY_DETAIL)
		)
		activities_vbox.add_child(btn)
		activity_item_buttons[g_id] = btn

	var current_game = MinigameCatalogClass.get_minigame(selected_game_id)
	if not current_game.is_empty():
		_populate_activity_detail(current_game)

func _highlight_selected_activity_button() -> void:
	for g_id in activity_item_buttons.keys():
		var btn = activity_item_buttons[g_id] as Button
		if is_instance_valid(btn):
			_style_activity_item(btn, g_id == selected_game_id)

func _populate_activity_detail(g: Dictionary) -> void:
	if not detail_title_label:
		return

	detail_title_label.text = g.get("title", "Reta")
	detail_category_label.text = "#%02d • Modalidad: %s" % [g.get("id", 1), g.get("category_name", "Reta")]
	detail_location_label.text = "📍 %s" % g.get("location_name", "Tecate, B.C.")
	detail_description_label.text = g.get("description", "")
	detail_controls_label.text = "Controles: %s" % g.get("controls_summary", "Teclas estándar")

func _update_location_filter_banner() -> void:
	if not location_filter_chip:
		return
	if current_location_filter.is_empty():
		location_filter_chip.visible = false
	else:
		var loc_info = MinigameCatalogClass.get_location_info(current_location_filter)
		location_filter_chip.visible = true
		location_filter_chip.text = "📍 Zona activa: %s" % loc_info.get("name", current_location_filter)

func _update_matrix_highlights() -> void:
	for i in range(menu_grid_buttons.size()):
		var btn = menu_grid_buttons[i]
		if is_instance_valid(btn):
			_style_matrix_button(btn, i == selected_menu_index)

# =============================================================================
# ACCIONES
# =============================================================================
func _on_summon_pressed() -> void:
	var g = MinigameCatalogClass.get_minigame(selected_game_id)
	if g.is_empty():
		return

	close_menu()
	minigame_launched.emit(selected_game_id)

	if minigame_manager and minigame_manager.has_method("start_or_summon_minigame"):
		minigame_manager.start_or_summon_minigame(
			selected_game_id,
			0,
			g.get("max_players", 8),
			g.get("arena_id", 1)
		)

func _on_teleport_pressed() -> void:
	var g = MinigameCatalogClass.get_minigame(selected_game_id)
	if g.is_empty():
		return

	var loc_id = g.get("location_id", "")
	var target_pos = g.get("target_position", Vector3.ZERO)

	close_menu()
	location_teleported.emit(loc_id, target_pos)

	if player and player.has_method("teleport_to_position") and target_pos != Vector3.ZERO:
		player.teleport_to_position(target_pos)

# =============================================================================
# ESTILOS VISUALES Y ANIMACIONES
# =============================================================================
func _style_phone_tab(btn: Button, is_active: bool) -> void:
	var sb = StyleBoxFlat.new()
	sb.bg_color = Color(0.0, 0.45, 0.85, 1.0) if is_active else Color(0.08, 0.14, 0.22, 0.9)
	sb.border_width_bottom = 2 if is_active else 0
	sb.border_color = Color(0.0, 0.95, 1.0, 1.0)
	sb.corner_radius_top_left = 4
	sb.corner_radius_top_right = 4
	sb.content_margin_left = 6
	sb.content_margin_right = 6
	sb.content_margin_top = 3
	sb.content_margin_bottom = 3
	btn.add_theme_stylebox_override("normal", sb)
	btn.add_theme_stylebox_override("hover", sb)
	btn.add_theme_stylebox_override("pressed", sb)
	btn.add_theme_color_override("font_color", Color(1.0, 1.0, 1.0, 1.0) if is_active else Color(0.6, 0.75, 0.9, 0.8))

func _style_activity_item(btn: Button, is_selected: bool) -> void:
	var sb = StyleBoxFlat.new()
	sb.bg_color = Color(0.0, 0.32, 0.65, 0.9) if is_selected else Color(0.06, 0.10, 0.18, 0.8)
	sb.border_width_left = 3 if is_selected else 1
	sb.border_color = Color(0.0, 0.90, 1.0, 1.0) if is_selected else Color(0.15, 0.25, 0.38, 0.6)
	sb.corner_radius_top_left = 4
	sb.corner_radius_top_right = 4
	sb.corner_radius_bottom_left = 4
	sb.corner_radius_bottom_right = 4
	sb.content_margin_left = 8
	sb.content_margin_right = 6
	sb.content_margin_top = 4
	sb.content_margin_bottom = 4
	btn.add_theme_stylebox_override("normal", sb)
	btn.add_theme_stylebox_override("hover", sb)
	btn.add_theme_stylebox_override("pressed", sb)
	btn.add_theme_color_override("font_color", Color(1.0, 1.0, 1.0, 1.0) if is_selected else Color(0.8, 0.88, 0.95, 0.9))

func _style_matrix_button(btn: Button, is_selected: bool) -> void:
	var sb = StyleBoxFlat.new()
	sb.bg_color = Color(0.05, 0.25, 0.50, 0.9) if is_selected else Color(0.06, 0.12, 0.20, 0.7)
	sb.border_width_left = 2 if is_selected else 1
	sb.border_width_top = 2 if is_selected else 1
	sb.border_width_right = 2 if is_selected else 1
	sb.border_width_bottom = 2 if is_selected else 1
	sb.border_color = Color(0.0, 0.95, 1.0, 1.0) if is_selected else Color(0.18, 0.30, 0.45, 0.5)
	sb.corner_radius_top_left = 6
	sb.corner_radius_top_right = 6
	sb.corner_radius_bottom_left = 6
	sb.corner_radius_bottom_right = 6
	btn.add_theme_stylebox_override("normal", sb)
	btn.add_theme_stylebox_override("hover", sb)
	btn.add_theme_stylebox_override("pressed", sb)

func _style_action_button(btn: Button, col: Color) -> void:
	var sb = StyleBoxFlat.new()
	sb.bg_color = col
	sb.corner_radius_top_left = 6
	sb.corner_radius_top_right = 6
	sb.corner_radius_bottom_left = 6
	sb.corner_radius_bottom_right = 6
	sb.content_margin_left = 8
	sb.content_margin_right = 8
	sb.content_margin_top = 4
	sb.content_margin_bottom = 4
	btn.add_theme_stylebox_override("normal", sb)
	btn.add_theme_stylebox_override("hover", sb)
	btn.add_theme_stylebox_override("pressed", sb)

func _style_keypad_button(btn: Button, bg_col: Color, border_col: Color) -> void:
	var sb = StyleBoxFlat.new()
	sb.bg_color = bg_col
	sb.border_width_left = 1
	sb.border_width_top = 1
	sb.border_width_right = 1
	sb.border_width_bottom = 2
	sb.border_color = border_col
	sb.corner_radius_top_left = 6
	sb.corner_radius_top_right = 6
	sb.corner_radius_bottom_left = 6
	sb.corner_radius_bottom_right = 6
	btn.add_theme_stylebox_override("normal", sb)
	btn.add_theme_stylebox_override("hover", sb)
	btn.add_theme_stylebox_override("pressed", sb)

func _style_laser_num_key(btn: Button) -> void:
	var sb = StyleBoxFlat.new()
	sb.bg_color = Color(0.06, 0.12, 0.22, 0.8)
	sb.border_width_left = 1
	sb.border_width_top = 1
	sb.border_width_right = 1
	sb.border_width_bottom = 1
	sb.border_color = Color(0.0, 0.85, 1.0, 0.35)
	sb.corner_radius_top_left = 3
	sb.corner_radius_top_right = 3
	sb.corner_radius_bottom_left = 3
	sb.corner_radius_bottom_right = 3
	btn.add_theme_stylebox_override("normal", sb)
	btn.add_theme_stylebox_override("hover", sb)
	btn.add_theme_stylebox_override("pressed", sb)
	btn.add_theme_color_override("font_color", Color(0.0, 0.90, 1.0, 0.9))

func _animate_open() -> void:
	if _phone_tween and _phone_tween.is_valid():
		_phone_tween.kill()
	_phone_tween = create_tween().set_parallel(true).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)

	phone_chassis.modulate.a = 0.0
	phone_chassis.scale = Vector2(0.85, 0.85)
	phone_chassis.position.y += 60.0

	_phone_tween.tween_property(phone_chassis, "modulate:a", 1.0, 0.25)
	_phone_tween.tween_property(phone_chassis, "scale", Vector2.ONE, 0.25)
	_phone_tween.tween_property(phone_chassis, "position:y", phone_chassis.position.y - 60.0, 0.25)
	_phone_tween.tween_property(backdrop, "modulate:a", 1.0, 0.20)

func _animate_close() -> void:
	if _phone_tween and _phone_tween.is_valid():
		_phone_tween.kill()
	_phone_tween = create_tween().set_parallel(true).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN)

	_phone_tween.tween_property(phone_chassis, "modulate:a", 0.0, 0.18)
	_phone_tween.tween_property(phone_chassis, "scale", Vector2(0.85, 0.85), 0.18)
	_phone_tween.tween_property(backdrop, "modulate:a", 0.0, 0.15)
	_phone_tween.chain().tween_callback(func():
		visible = false
	)
