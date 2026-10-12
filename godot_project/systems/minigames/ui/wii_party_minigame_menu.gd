class_name WiiPartyMinigameMenu
extends CanvasLayer

## Menú Interactivo de Minijuegos inspirado en Wii Party para Tecate Simulator.
## Presenta pestañas por categoría (Todos, Todos contra Todos, 1 contra Todos,
## Duelo 1 vs. 1), filtro contextual por ubicación, cuadrícula de tarjetas
## tipo burbuja redondeada y ficha detallada con reglas, controles y convocatoria.

signal menu_opened
signal menu_closed
signal minigame_launched(game_id: int)
signal location_teleported(location_id: String, target_pos: Vector3)

const MinigameCatalogClass = preload("res://systems/minigames/minigame_catalog.gd")

@export var minigame_manager_path: NodePath = ^"../MinigameManager"
@export var player_path: NodePath = ^"../Player"

var minigame_manager: Node = null
var player: Node = null

var is_open: bool = false
var current_category: int = MinigameCatalogClass.Category.ALL
var current_location_filter: String = ""
var selected_game_id: int = 1

# Nodos de UI
var root_control: Control = null
var backdrop: ColorRect = null
var main_board: PanelContainer = null
var header_title_label: Label = null
var header_subtitle_label: Label = null
var location_filter_banner: PanelContainer = null
var location_filter_label: Label = null
var btn_clear_location_filter: Button = null

var category_tabs_hbox: HBoxContainer = null
var category_buttons: Dictionary = {}

var games_grid: GridContainer = null
var game_tile_buttons: Dictionary = {}

# Panel derecho de vista previa (Ficha Wii Party)
var preview_header_panel: PanelContainer = null
var preview_icon_label: Label = null
var preview_title_label: Label = null
var preview_subtitle_label: Label = null
var preview_category_badge: Label = null
var preview_players_badge: Label = null
var preview_duration_badge: Label = null
var preview_phase_badge: Label = null
var preview_location_label: Label = null
var preview_description_label: Label = null
var preview_controls_vbox: VBoxContainer = null
var preview_status_feedback: Label = null

var btn_play_game: Button = null
var btn_teleport_location: Button = null
var btn_close_menu: Button = null

var _previous_mouse_mode: Input.MouseMode = Input.MOUSE_MODE_CAPTURED
var _din_font: Font = null

func _ready() -> void:
	layer = 45
	visible = false
	_din_font = load("res://assets/fonts/DIN_Condensed_Bold.ttf")
	_resolve_dependencies()
	_build_wii_party_ui()
	select_category(MinigameCatalogClass.Category.ALL)
	select_minigame(1)

func _resolve_dependencies() -> void:
	if has_node(minigame_manager_path):
		minigame_manager = get_node(minigame_manager_path)
	elif get_parent() and get_parent().has_node("MinigameManager"):
		minigame_manager = get_parent().get_node("MinigameManager")

	if has_node(player_path):
		player = get_node(player_path)
	elif get_parent() and get_parent().has_node("Player"):
		player = get_parent().get_node("Player")

func _build_wii_party_ui() -> void:
	root_control = Control.new()
	root_control.name = "WiiPartyRoot"
	root_control.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(root_control)

	# 1. Fondo translúcido cálido festivo
	backdrop = ColorRect.new()
	backdrop.name = "Backdrop"
	backdrop.set_anchors_preset(Control.PRESET_FULL_RECT)
	backdrop.color = Color(0.04, 0.08, 0.16, 0.78)
	root_control.add_child(backdrop)

	var center_margin = MarginContainer.new()
	center_margin.set_anchors_preset(Control.PRESET_FULL_RECT)
	center_margin.add_theme_constant_override("margin_left", 42)
	center_margin.add_theme_constant_override("margin_right", 42)
	center_margin.add_theme_constant_override("margin_top", 28)
	center_margin.add_theme_constant_override("margin_bottom", 28)
	root_control.add_child(center_margin)

	# 2. Tablero Principal Estilo Wii Party (Bordes redondeados crema/blanco brillante)
	main_board = PanelContainer.new()
	main_board.name = "MainBoard"
	main_board.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	main_board.size_flags_vertical = Control.SIZE_EXPAND_FILL

	var style_board = StyleBoxFlat.new()
	style_board.bg_color = Color(0.97, 0.96, 0.92, 0.98) # Crema luminoso Wii Party
	style_board.border_width_left = 5
	style_board.border_width_top = 5
	style_board.border_width_right = 5
	style_board.border_width_bottom = 5
	style_board.border_color = Color(1.0, 0.75, 0.10, 1.0) # Borde Dorado Fiesta
	style_board.corner_radius_top_left = 24
	style_board.corner_radius_top_right = 24
	style_board.corner_radius_bottom_left = 24
	style_board.corner_radius_bottom_right = 24
	style_board.shadow_color = Color(0.0, 0.0, 0.0, 0.45)
	style_board.shadow_size = 20
	style_board.content_margin_left = 26
	style_board.content_margin_right = 26
	style_board.content_margin_top = 20
	style_board.content_margin_bottom = 20
	main_board.add_theme_stylebox_override("panel", style_board)
	center_margin.add_child(main_board)

	var board_vbox = VBoxContainer.new()
	board_vbox.add_theme_constant_override("separation", 14)
	main_board.add_child(board_vbox)

	# 3. Cabecera Superior (Cinta Festiva Wii Party)
	var top_bar = HBoxContainer.new()
	top_bar.add_theme_constant_override("separation", 16)
	board_vbox.add_child(top_bar)

	var title_pill = PanelContainer.new()
	var style_title_pill = StyleBoxFlat.new()
	style_title_pill.bg_color = Color(0.0, 0.56, 0.86, 1.0) # Azul Wii Party
	style_title_pill.border_width_bottom = 4
	style_title_pill.border_color = Color(0.0, 0.38, 0.65, 1.0)
	style_title_pill.corner_radius_top_left = 16
	style_title_pill.corner_radius_top_right = 16
	style_title_pill.corner_radius_bottom_left = 16
	style_title_pill.corner_radius_bottom_right = 16
	style_title_pill.content_margin_left = 22
	style_title_pill.content_margin_right = 22
	style_title_pill.content_margin_top = 8
	style_title_pill.content_margin_bottom = 8
	title_pill.add_theme_stylebox_override("panel", style_title_pill)

	var title_hbox = HBoxContainer.new()
	title_hbox.add_theme_constant_override("separation", 12)
	title_pill.add_child(title_hbox)

	header_title_label = Label.new()
	header_title_label.text = "🎉 TECATE PARTY  •  MENÚ DE MINIJUEGOS"
	if _din_font:
		header_title_label.add_theme_font_override("font", _din_font)
	header_title_label.add_theme_font_size_override("font_size", 30)
	header_title_label.add_theme_color_override("font_color", Color(1.0, 1.0, 1.0, 1.0))
	title_hbox.add_child(header_title_label)
	top_bar.add_child(title_pill)

	header_subtitle_label = Label.new()
	header_subtitle_label.text = "¡Elige un minijuego para armar la reta con tus amigos o acude a su ubicación en Tecate!"
	header_subtitle_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	if _din_font:
		header_subtitle_label.add_theme_font_override("font", _din_font)
	header_subtitle_label.add_theme_font_size_override("font_size", 20)
	header_subtitle_label.add_theme_color_override("font_color", Color(0.20, 0.24, 0.30, 1.0))
	top_bar.add_child(header_subtitle_label)

	btn_close_menu = Button.new()
	btn_close_menu.name = "BtnCloseMenu"
	btn_close_menu.text = "✖ Cerrar [M / Esc]"
	btn_close_menu.custom_minimum_size = Vector2(150, 42)
	btn_close_menu.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	if _din_font:
		btn_close_menu.add_theme_font_override("font", _din_font)
	btn_close_menu.add_theme_font_size_override("font_size", 20)
	_style_pill_button(btn_close_menu, Color(0.86, 0.20, 0.20, 1.0), Color(1.0, 1.0, 1.0, 1.0))
	btn_close_menu.pressed.connect(close_menu)
	top_bar.add_child(btn_close_menu)

	# 4. Pestañas de Categoría Estilo Wii Party + Filtro de Ubicación
	var nav_row = HBoxContainer.new()
	nav_row.add_theme_constant_override("separation", 12)
	board_vbox.add_child(nav_row)

	category_tabs_hbox = HBoxContainer.new()
	category_tabs_hbox.add_theme_constant_override("separation", 10)
	nav_row.add_child(category_tabs_hbox)

	var cats = [
		MinigameCatalogClass.Category.ALL,
		MinigameCatalogClass.Category.ALL_VS_ALL,
		MinigameCatalogClass.Category.ONE_VS_ALL,
		MinigameCatalogClass.Category.DUEL_1V1
	]
	for cat_id in cats:
		var c_info = MinigameCatalogClass.CATEGORY_INFO[cat_id]
		var count = MinigameCatalogClass.get_minigames_by_category(cat_id).size()
		var tab_btn = Button.new()
		tab_btn.name = "Tab_%d" % cat_id
		tab_btn.text = "%s %s (%d)" % [c_info["icon"], c_info["short_name"], count]
		tab_btn.custom_minimum_size = Vector2(175, 42)
		tab_btn.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
		if _din_font:
			tab_btn.add_theme_font_override("font", _din_font)
		tab_btn.add_theme_font_size_override("font_size", 21)
		tab_btn.pressed.connect(func():
			current_location_filter = ""
			select_category(cat_id)
		)
		category_tabs_hbox.add_child(tab_btn)
		category_buttons[cat_id] = tab_btn

	# Banner de filtro activo por ubicación (visible al abrir desde una ubicación)
	location_filter_banner = PanelContainer.new()
	location_filter_banner.name = "LocationFilterBanner"
	location_filter_banner.visible = false
	location_filter_banner.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var style_loc_banner = StyleBoxFlat.new()
	style_loc_banner.bg_color = Color(1.0, 0.92, 0.70, 1.0)
	style_loc_banner.border_width_left = 2
	style_loc_banner.border_width_top = 2
	style_loc_banner.border_width_right = 2
	style_loc_banner.border_width_bottom = 2
	style_loc_banner.border_color = Color(0.95, 0.55, 0.10, 1.0)
	style_loc_banner.corner_radius_top_left = 12
	style_loc_banner.corner_radius_top_right = 12
	style_loc_banner.corner_radius_bottom_left = 12
	style_loc_banner.corner_radius_bottom_right = 12
	style_loc_banner.content_margin_left = 14
	style_loc_banner.content_margin_right = 14
	style_loc_banner.content_margin_top = 4
	style_loc_banner.content_margin_bottom = 4
	location_filter_banner.add_theme_stylebox_override("panel", style_loc_banner)

	var loc_hbox = HBoxContainer.new()
	loc_hbox.add_theme_constant_override("separation", 10)
	location_filter_banner.add_child(loc_hbox)

	location_filter_label = Label.new()
	location_filter_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	if _din_font:
		location_filter_label.add_theme_font_override("font", _din_font)
	location_filter_label.add_theme_font_size_override("font_size", 19)
	location_filter_label.add_theme_color_override("font_color", Color(0.45, 0.22, 0.02, 1.0))
	loc_hbox.add_child(location_filter_label)

	btn_clear_location_filter = Button.new()
	btn_clear_location_filter.text = "Ver Todos (12)"
	btn_clear_location_filter.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	if _din_font:
		btn_clear_location_filter.add_theme_font_override("font", _din_font)
	btn_clear_location_filter.add_theme_font_size_override("font_size", 17)
	_style_pill_button(btn_clear_location_filter, Color(0.95, 0.55, 0.10, 1.0), Color(1.0, 1.0, 1.0, 1.0))
	btn_clear_location_filter.pressed.connect(func():
		current_location_filter = ""
		select_category(MinigameCatalogClass.Category.ALL)
	)
	loc_hbox.add_child(btn_clear_location_filter)
	nav_row.add_child(location_filter_banner)

	# 5. Cuerpo Dividido: Izquierda (Cuadrícula de Burbujas) | Derecha (Ficha Wii Party)
	var content_split = HBoxContainer.new()
	content_split.size_flags_vertical = Control.SIZE_EXPAND_FILL
	content_split.add_theme_constant_override("separation", 20)
	board_vbox.add_child(content_split)

	# 5A. Columna Izquierda: ScrollContainer + GridContainer de Minijuegos
	var left_panel = PanelContainer.new()
	left_panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	left_panel.size_flags_vertical = Control.SIZE_EXPAND_FILL
	left_panel.size_flags_stretch_ratio = 1.15
	var style_left = StyleBoxFlat.new()
	style_left.bg_color = Color(0.91, 0.90, 0.85, 0.95)
	style_left.border_width_left = 2
	style_left.border_width_top = 2
	style_left.border_width_right = 2
	style_left.border_width_bottom = 2
	style_left.border_color = Color(0.80, 0.78, 0.72, 1.0)
	style_left.corner_radius_top_left = 18
	style_left.corner_radius_top_right = 18
	style_left.corner_radius_bottom_left = 18
	style_left.corner_radius_bottom_right = 18
	style_left.content_margin_left = 14
	style_left.content_margin_right = 14
	style_left.content_margin_top = 14
	style_left.content_margin_bottom = 14
	left_panel.add_theme_stylebox_override("panel", style_left)
	content_split.add_child(left_panel)

	var scroll = ScrollContainer.new()
	scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	left_panel.add_child(scroll)

	games_grid = GridContainer.new()
	games_grid.name = "GamesGrid"
	games_grid.columns = 2
	games_grid.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	games_grid.add_theme_constant_override("h_separation", 12)
	games_grid.add_theme_constant_override("v_separation", 12)
	scroll.add_child(games_grid)

	# 5B. Columna Derecha: Ficha Detallada del Minijuego Seleccionado
	var right_card = PanelContainer.new()
	right_card.name = "PreviewCard"
	right_card.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	right_card.size_flags_vertical = Control.SIZE_EXPAND_FILL
	right_card.size_flags_stretch_ratio = 1.0
	var style_right = StyleBoxFlat.new()
	style_right.bg_color = Color(1.0, 1.0, 0.99, 1.0)
	style_right.border_width_left = 4
	style_right.border_width_top = 4
	style_right.border_width_right = 4
	style_right.border_width_bottom = 4
	style_right.border_color = Color(0.0, 0.56, 0.86, 1.0)
	style_right.corner_radius_top_left = 20
	style_right.corner_radius_top_right = 20
	style_right.corner_radius_bottom_left = 20
	style_right.corner_radius_bottom_right = 20
	style_right.shadow_color = Color(0.0, 0.0, 0.0, 0.18)
	style_right.shadow_size = 10
	style_right.content_margin_left = 20
	style_right.content_margin_right = 20
	style_right.content_margin_top = 18
	style_right.content_margin_bottom = 18
	right_card.add_theme_stylebox_override("panel", style_right)
	content_split.add_child(right_card)

	var preview_vbox = VBoxContainer.new()
	preview_vbox.add_theme_constant_override("separation", 12)
	right_card.add_child(preview_vbox)

	# Encabezado de color del juego seleccionado
	preview_header_panel = PanelContainer.new()
	var style_prev_hdr = StyleBoxFlat.new()
	style_prev_hdr.bg_color = Color(0.92, 0.22, 0.22, 1.0)
	style_prev_hdr.corner_radius_top_left = 14
	style_prev_hdr.corner_radius_top_right = 14
	style_prev_hdr.corner_radius_bottom_left = 14
	style_prev_hdr.corner_radius_bottom_right = 14
	style_prev_hdr.content_margin_left = 16
	style_prev_hdr.content_margin_right = 16
	style_prev_hdr.content_margin_top = 12
	style_prev_hdr.content_margin_bottom = 12
	preview_header_panel.add_theme_stylebox_override("panel", style_prev_hdr)
	preview_vbox.add_child(preview_header_panel)

	var prev_hdr_hbox = HBoxContainer.new()
	prev_hdr_hbox.add_theme_constant_override("separation", 14)
	preview_header_panel.add_child(prev_hdr_hbox)

	preview_icon_label = Label.new()
	preview_icon_label.text = "🏛️"
	preview_icon_label.add_theme_font_size_override("font_size", 46)
	prev_hdr_hbox.add_child(preview_icon_label)

	var prev_title_vbox = VBoxContainer.new()
	prev_title_vbox.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	prev_hdr_hbox.add_child(prev_title_vbox)

	preview_title_label = Label.new()
	preview_title_label.text = "MI KIOSKO"
	if _din_font:
		preview_title_label.add_theme_font_override("font", _din_font)
	preview_title_label.add_theme_font_size_override("font_size", 32)
	preview_title_label.add_theme_color_override("font_color", Color(1.0, 1.0, 1.0, 1.0))
	prev_title_vbox.add_child(preview_title_label)

	preview_subtitle_label = Label.new()
	preview_subtitle_label.text = "Batalla campal de empujones y bloqueos en la tarima"
	if _din_font:
		preview_subtitle_label.add_theme_font_override("font", _din_font)
	preview_subtitle_label.add_theme_font_size_override("font_size", 18)
	preview_subtitle_label.add_theme_color_override("font_color", Color(1.0, 0.96, 0.85, 0.95))
	preview_subtitle_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	prev_title_vbox.add_child(preview_subtitle_label)

	# Fila de insignias (Categoría, Jugadores, Duración, Estado)
	var badges_hbox = HBoxContainer.new()
	badges_hbox.add_theme_constant_override("separation", 10)
	preview_vbox.add_child(badges_hbox)

	preview_category_badge = _create_badge_label("TODOS CONTRA TODOS", Color(0.92, 0.22, 0.22, 1.0))
	badges_hbox.add_child(preview_category_badge)

	preview_players_badge = _create_badge_label("👥 2-8 Jug.", Color(0.18, 0.24, 0.34, 1.0))
	badges_hbox.add_child(preview_players_badge)

	preview_duration_badge = _create_badge_label("⏱️ 90s  •  🪙 +50 Pesos", Color(0.85, 0.55, 0.05, 1.0))
	badges_hbox.add_child(preview_duration_badge)

	preview_phase_badge = _create_badge_label("✓ ¡DISPONIBLE!", Color(0.15, 0.68, 0.28, 1.0))
	badges_hbox.add_child(preview_phase_badge)

	# Banda de Ubicación en Tecate
	var loc_strip = PanelContainer.new()
	var style_loc = StyleBoxFlat.new()
	style_loc.bg_color = Color(0.93, 0.95, 0.98, 1.0)
	style_loc.border_width_left = 4
	style_loc.border_color = Color(0.0, 0.56, 0.86, 1.0)
	style_loc.corner_radius_top_right = 10
	style_loc.corner_radius_bottom_right = 10
	style_loc.content_margin_left = 12
	style_loc.content_margin_right = 12
	style_loc.content_margin_top = 8
	style_loc.content_margin_bottom = 8
	loc_strip.add_theme_stylebox_override("panel", style_loc)
	preview_vbox.add_child(loc_strip)

	preview_location_label = Label.new()
	preview_location_label.text = "📍 Ubicación en el Mapa: Kiosko del Parque Miguel Hidalgo"
	if _din_font:
		preview_location_label.add_theme_font_override("font", _din_font)
	preview_location_label.add_theme_font_size_override("font_size", 20)
	preview_location_label.add_theme_color_override("font_color", Color(0.10, 0.22, 0.38, 1.0))
	loc_strip.add_child(preview_location_label)

	# Recuadro "¿Cómo se juega?"
	var rules_panel = PanelContainer.new()
	rules_panel.size_flags_vertical = Control.SIZE_EXPAND_FILL
	var style_rules = StyleBoxFlat.new()
	style_rules.bg_color = Color(0.98, 0.97, 0.93, 1.0)
	style_rules.border_width_left = 2
	style_rules.border_width_top = 2
	style_rules.border_width_right = 2
	style_rules.border_width_bottom = 2
	style_rules.border_color = Color(0.86, 0.83, 0.74, 1.0)
	style_rules.corner_radius_top_left = 12
	style_rules.corner_radius_top_right = 12
	style_rules.corner_radius_bottom_left = 12
	style_rules.corner_radius_bottom_right = 12
	style_rules.content_margin_left = 14
	style_rules.content_margin_right = 14
	style_rules.content_margin_top = 10
	style_rules.content_margin_bottom = 10
	rules_panel.add_theme_stylebox_override("panel", style_rules)
	preview_vbox.add_child(rules_panel)

	var rules_vbox = VBoxContainer.new()
	rules_vbox.add_theme_constant_override("separation", 6)
	rules_panel.add_child(rules_vbox)

	var rules_header = Label.new()
	rules_header.text = "📖 ¿CÓMO SE JUEGA?"
	if _din_font:
		rules_header.add_theme_font_override("font", _din_font)
	rules_header.add_theme_font_size_override("font_size", 20)
	rules_header.add_theme_color_override("font_color", Color(0.75, 0.18, 0.18, 1.0))
	rules_vbox.add_child(rules_header)

	preview_description_label = Label.new()
	preview_description_label.size_flags_vertical = Control.SIZE_EXPAND_FILL
	preview_description_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	preview_description_label.add_theme_font_size_override("font_size", 16)
	preview_description_label.add_theme_color_override("font_color", Color(0.16, 0.18, 0.22, 1.0))
	rules_vbox.add_child(preview_description_label)

	# Recuadro de Controles Estilo Wii Party
	var controls_panel = PanelContainer.new()
	var style_ctrls = StyleBoxFlat.new()
	style_ctrls.bg_color = Color(0.94, 0.96, 0.99, 1.0)
	style_ctrls.border_width_left = 2
	style_ctrls.border_width_top = 2
	style_ctrls.border_width_right = 2
	style_ctrls.border_width_bottom = 2
	style_ctrls.border_color = Color(0.72, 0.80, 0.90, 1.0)
	style_ctrls.corner_radius_top_left = 12
	style_ctrls.corner_radius_top_right = 12
	style_ctrls.corner_radius_bottom_left = 12
	style_ctrls.corner_radius_bottom_right = 12
	style_ctrls.content_margin_left = 14
	style_ctrls.content_margin_right = 14
	style_ctrls.content_margin_top = 10
	style_ctrls.content_margin_bottom = 10
	controls_panel.add_theme_stylebox_override("panel", style_ctrls)
	preview_vbox.add_child(controls_panel)

	var ctrls_outer_vbox = VBoxContainer.new()
	ctrls_outer_vbox.add_theme_constant_override("separation", 6)
	controls_panel.add_child(ctrls_outer_vbox)

	var ctrls_title = Label.new()
	ctrls_title.text = "🎮 CONTROLES DEL MINIJUEGO"
	if _din_font:
		ctrls_title.add_theme_font_override("font", _din_font)
	ctrls_title.add_theme_font_size_override("font_size", 19)
	ctrls_title.add_theme_color_override("font_color", Color(0.0, 0.45, 0.75, 1.0))
	ctrls_outer_vbox.add_child(ctrls_title)

	preview_controls_vbox = VBoxContainer.new()
	preview_controls_vbox.add_theme_constant_override("separation", 5)
	ctrls_outer_vbox.add_child(preview_controls_vbox)

	preview_status_feedback = Label.new()
	preview_status_feedback.visible = false
	preview_status_feedback.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	if _din_font:
		preview_status_feedback.add_theme_font_override("font", _din_font)
	preview_status_feedback.add_theme_font_size_override("font_size", 18)
	preview_status_feedback.add_theme_color_override("font_color", Color(0.10, 0.55, 0.22, 1.0))
	preview_vbox.add_child(preview_status_feedback)

	# Botones de Acción Inferiores
	var actions_hbox = HBoxContainer.new()
	actions_hbox.add_theme_constant_override("separation", 12)
	preview_vbox.add_child(actions_hbox)

	btn_play_game = Button.new()
	btn_play_game.name = "BtnPlayGame"
	btn_play_game.text = "🎉 ¡JUGAR / CONVOCAR RETA!"
	btn_play_game.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	btn_play_game.custom_minimum_size = Vector2(220, 50)
	btn_play_game.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	if _din_font:
		btn_play_game.add_theme_font_override("font", _din_font)
	btn_play_game.add_theme_font_size_override("font_size", 25)
	_style_pill_button(btn_play_game, Color(0.16, 0.72, 0.28, 1.0), Color(1.0, 1.0, 1.0, 1.0))
	btn_play_game.pressed.connect(_on_play_pressed)
	actions_hbox.add_child(btn_play_game)

	btn_teleport_location = Button.new()
	btn_teleport_location.name = "BtnTeleportLocation"
	btn_teleport_location.text = "📍 Ir a la Ubicación"
	btn_teleport_location.custom_minimum_size = Vector2(175, 50)
	btn_teleport_location.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	if _din_font:
		btn_teleport_location.add_theme_font_override("font", _din_font)
	btn_teleport_location.add_theme_font_size_override("font_size", 22)
	_style_pill_button(btn_teleport_location, Color(0.0, 0.56, 0.86, 1.0), Color(1.0, 1.0, 1.0, 1.0))
	btn_teleport_location.pressed.connect(_on_teleport_location_pressed)
	actions_hbox.add_child(btn_teleport_location)

func _create_badge_label(text_val: String, bg_col: Color) -> Label:
	var lbl = Label.new()
	lbl.text = text_val
	if _din_font:
		lbl.add_theme_font_override("font", _din_font)
	lbl.add_theme_font_size_override("font_size", 16)
	lbl.add_theme_color_override("font_color", Color(1.0, 1.0, 1.0, 1.0))
	var st = StyleBoxFlat.new()
	st.bg_color = bg_col
	st.corner_radius_top_left = 8
	st.corner_radius_top_right = 8
	st.corner_radius_bottom_left = 8
	st.corner_radius_bottom_right = 8
	st.content_margin_left = 10
	st.content_margin_right = 10
	st.content_margin_top = 4
	st.content_margin_bottom = 4
	lbl.add_theme_stylebox_override("normal", st)
	return lbl

func _style_pill_button(btn: Button, bg_color: Color, font_col: Color) -> void:
	btn.add_theme_color_override("font_color", font_col)
	btn.add_theme_color_override("font_hover_color", font_col)
	btn.add_theme_color_override("font_focus_color", font_col)
	btn.add_theme_color_override("font_pressed_color", font_col)

	var st_norm = StyleBoxFlat.new()
	st_norm.bg_color = bg_color
	st_norm.border_width_bottom = 4
	st_norm.border_color = bg_color.darkened(0.28)
	st_norm.corner_radius_top_left = 14
	st_norm.corner_radius_top_right = 14
	st_norm.corner_radius_bottom_left = 14
	st_norm.corner_radius_bottom_right = 14
	st_norm.content_margin_left = 16
	st_norm.content_margin_right = 16
	st_norm.content_margin_top = 6
	st_norm.content_margin_bottom = 6
	btn.add_theme_stylebox_override("normal", st_norm)

	var st_hover = st_norm.duplicate() as StyleBoxFlat
	st_hover.bg_color = bg_color.lightened(0.14)
	btn.add_theme_stylebox_override("hover", st_hover)
	btn.add_theme_stylebox_override("focus", st_hover)

	var st_press = st_norm.duplicate() as StyleBoxFlat
	st_press.bg_color = bg_color.darkened(0.15)
	btn.add_theme_stylebox_override("pressed", st_press)

func select_category(cat_id: int) -> void:
	current_category = cat_id
	_update_category_tab_styles()
	_rebuild_games_grid()

func filter_by_location(location_id: String) -> void:
	current_location_filter = location_id
	var loc_info = MinigameCatalogClass.get_location_info(location_id)
	if not loc_info.is_empty() and location_filter_banner and location_filter_label:
		location_filter_banner.visible = true
		location_filter_label.text = "📍 Juegos en %s" % loc_info.get("name", location_id)
	_update_category_tab_styles()
	_rebuild_games_grid()

	var loc_games = MinigameCatalogClass.get_minigames_by_location(location_id)
	if not loc_games.is_empty():
		var primary_id = int(loc_info.get("primary_game_id", loc_games[0]["id"]))
		select_minigame(primary_id)

func _update_category_tab_styles() -> void:
	for cat_id in category_buttons.keys():
		var btn: Button = category_buttons[cat_id]
		var c_info = MinigameCatalogClass.CATEGORY_INFO[cat_id]
		var active = (cat_id == current_category and current_location_filter.is_empty())
		if active:
			_style_pill_button(btn, c_info["color"], Color(1.0, 1.0, 1.0, 1.0))
		else:
			_style_pill_button(btn, Color(0.84, 0.83, 0.78, 1.0), Color(0.22, 0.25, 0.30, 1.0))

	if location_filter_banner:
		location_filter_banner.visible = not current_location_filter.is_empty()

func _rebuild_games_grid() -> void:
	if not games_grid:
		return

	for child in games_grid.get_children():
		child.queue_free()
	game_tile_buttons.clear()

	var games_list: Array[Dictionary] = []
	if not current_location_filter.is_empty():
		games_list = MinigameCatalogClass.get_minigames_by_location(current_location_filter)
	else:
		games_list = MinigameCatalogClass.get_minigames_by_category(current_category)

	for g in games_list:
		var tile = _create_game_tile(g)
		games_grid.add_child(tile)
		game_tile_buttons[g["id"]] = tile

	_highlight_selected_tile()

func _create_game_tile(g: Dictionary) -> Button:
	var gid: int = g["id"]
	var btn = Button.new()
	btn.name = "GameTile_%d" % gid
	btn.custom_minimum_size = Vector2(235, 108)
	btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	btn.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND

	var margin = MarginContainer.new()
	margin.set_anchors_preset(Control.PRESET_FULL_RECT)
	margin.mouse_filter = Control.MOUSE_FILTER_IGNORE
	margin.add_theme_constant_override("margin_left", 14)
	margin.add_theme_constant_override("margin_right", 14)
	margin.add_theme_constant_override("margin_top", 10)
	margin.add_theme_constant_override("margin_bottom", 10)
	btn.add_child(margin)

	var vbox = VBoxContainer.new()
	vbox.mouse_filter = Control.MOUSE_FILTER_IGNORE
	vbox.add_theme_constant_override("separation", 4)
	margin.add_child(vbox)

	# Fila 1: Número + Ícono + Estado
	var top_row = HBoxContainer.new()
	top_row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	vbox.add_child(top_row)

	var num_lbl = Label.new()
	num_lbl.text = "#%02d  %s" % [gid, g["icon"]]
	if _din_font:
		num_lbl.add_theme_font_override("font", _din_font)
	num_lbl.add_theme_font_size_override("font_size", 20)
	num_lbl.add_theme_color_override("font_color", g["color"].darkened(0.15))
	num_lbl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top_row.add_child(num_lbl)

	var status_lbl = Label.new()
	if g.get("is_playable", false):
		status_lbl.text = "● ¡LISTO!"
		status_lbl.add_theme_color_override("font_color", Color(0.12, 0.62, 0.24, 1.0))
	else:
		status_lbl.text = "FASE %d" % g.get("phase", 2)
		status_lbl.add_theme_color_override("font_color", Color(0.75, 0.45, 0.08, 1.0))
	if _din_font:
		status_lbl.add_theme_font_override("font", _din_font)
	status_lbl.add_theme_font_size_override("font_size", 15)
	top_row.add_child(status_lbl)

	# Fila 2: Título del minijuego
	var title_lbl = Label.new()
	title_lbl.text = g["title"].to_upper()
	if _din_font:
		title_lbl.add_theme_font_override("font", _din_font)
	title_lbl.add_theme_font_size_override("font_size", 24)
	title_lbl.add_theme_color_override("font_color", Color(0.12, 0.15, 0.20, 1.0))
	vbox.add_child(title_lbl)

	# Fila 3: Ubicación corta
	var loc_info = MinigameCatalogClass.get_location_info(g["location_id"])
	var loc_lbl = Label.new()
	loc_lbl.text = "📍 %s" % loc_info.get("short_name", g["location_name"])
	if _din_font:
		loc_lbl.add_theme_font_override("font", _din_font)
	loc_lbl.add_theme_font_size_override("font_size", 15)
	loc_lbl.add_theme_color_override("font_color", Color(0.38, 0.42, 0.48, 1.0))
	vbox.add_child(loc_lbl)

	btn.pressed.connect(func(): select_minigame(gid))
	return btn

func _highlight_selected_tile() -> void:
	for gid in game_tile_buttons.keys():
		var btn: Button = game_tile_buttons[gid]
		var g = MinigameCatalogClass.get_minigame(gid)
		var g_col: Color = g.get("color", Color(0.0, 0.56, 0.86, 1.0))
		var is_sel = (gid == selected_game_id)

		var st = StyleBoxFlat.new()
		st.corner_radius_top_left = 16
		st.corner_radius_top_right = 16
		st.corner_radius_bottom_left = 16
		st.corner_radius_bottom_right = 16

		if is_sel:
			st.bg_color = Color(1.0, 0.99, 0.92, 1.0)
			st.border_width_left = 4
			st.border_width_top = 4
			st.border_width_right = 4
			st.border_width_bottom = 5
			st.border_color = g_col
			st.shadow_color = Color(g_col.r, g_col.g, g_col.b, 0.35)
			st.shadow_size = 10
		else:
			st.bg_color = Color(0.99, 0.99, 0.98, 0.94)
			st.border_width_left = 2
			st.border_width_top = 2
			st.border_width_right = 2
			st.border_width_bottom = 3
			st.border_color = Color(g_col.r, g_col.g, g_col.b, 0.42)
			st.shadow_color = Color(0.0, 0.0, 0.0, 0.10)
			st.shadow_size = 4

		var st_hover = st.duplicate() as StyleBoxFlat
		st_hover.bg_color = Color(1.0, 1.0, 0.95, 1.0)
		st_hover.border_color = g_col

		btn.add_theme_stylebox_override("normal", st)
		btn.add_theme_stylebox_override("hover", st_hover)
		btn.add_theme_stylebox_override("focus", st_hover)
		btn.add_theme_stylebox_override("pressed", st)

func select_minigame(game_id: int) -> void:
	var g = MinigameCatalogClass.get_minigame(game_id)
	if g.is_empty():
		return

	selected_game_id = game_id
	_highlight_selected_tile()

	if preview_status_feedback:
		preview_status_feedback.visible = false

	var g_col: Color = g["color"]
	if preview_header_panel:
		var st_hdr = StyleBoxFlat.new()
		st_hdr.bg_color = g_col
		st_hdr.corner_radius_top_left = 14
		st_hdr.corner_radius_top_right = 14
		st_hdr.corner_radius_bottom_left = 14
		st_hdr.corner_radius_bottom_right = 14
		st_hdr.content_margin_left = 16
		st_hdr.content_margin_right = 16
		st_hdr.content_margin_top = 12
		st_hdr.content_margin_bottom = 12
		preview_header_panel.add_theme_stylebox_override("panel", st_hdr)

	if preview_icon_label:
		preview_icon_label.text = g["icon"]
	if preview_title_label:
		preview_title_label.text = g["full_title"].to_upper()
	if preview_subtitle_label:
		preview_subtitle_label.text = g["subtitle"]

	var cat_info = MinigameCatalogClass.CATEGORY_INFO.get(g["category"], {})
	if preview_category_badge:
		preview_category_badge.text = "%s %s" % [cat_info.get("icon", "🔥"), cat_info.get("badge", "FIESTA")]
		var st_cat = preview_category_badge.get_theme_stylebox("normal").duplicate() as StyleBoxFlat
		st_cat.bg_color = cat_info.get("color", g_col)
		preview_category_badge.add_theme_stylebox_override("normal", st_cat)

	if preview_players_badge:
		preview_players_badge.text = "👥 %s" % g["players_badge"]

	if preview_duration_badge:
		preview_duration_badge.text = "⏱️ %ds  •  🪙 +%d Pesos" % [g["duration_seconds"], g["reward_first"]]

	if preview_phase_badge:
		var st_ph = preview_phase_badge.get_theme_stylebox("normal").duplicate() as StyleBoxFlat
		if g.get("is_playable", false):
			preview_phase_badge.text = "✓ ¡DISPONIBLE!"
			st_ph.bg_color = Color(0.15, 0.68, 0.28, 1.0)
		else:
			preview_phase_badge.text = "⏳ FASE %d (VISTA PREVIA)" % g.get("phase", 2)
			st_ph.bg_color = Color(0.85, 0.52, 0.08, 1.0)
		preview_phase_badge.add_theme_stylebox_override("normal", st_ph)

	if preview_location_label:
		preview_location_label.text = "📍 Ubicación en el Mapa: %s" % g["location_name"]

	if preview_description_label:
		preview_description_label.text = g["description"]

	if preview_controls_vbox:
		for c in preview_controls_vbox.get_children():
			c.queue_free()
		for ctrl in g.get("controls", []):
			var row = HBoxContainer.new()
			row.add_theme_constant_override("separation", 10)

			var key_lbl = _create_badge_label(ctrl["input"], Color(0.18, 0.26, 0.38, 1.0))
			key_lbl.custom_minimum_size = Vector2(145, 26)
			key_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
			row.add_child(key_lbl)

			var act_lbl = Label.new()
			act_lbl.text = ctrl["action"]
			act_lbl.add_theme_font_size_override("font_size", 15)
			act_lbl.add_theme_color_override("font_color", Color(0.18, 0.20, 0.25, 1.0))
			act_lbl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			row.add_child(act_lbl)

			preview_controls_vbox.add_child(row)

	if btn_play_game:
		if g.get("is_playable", false):
			btn_play_game.text = "🎉 ¡JUGAR / CONVOCAR RETA!"
			_style_pill_button(btn_play_game, Color(0.16, 0.72, 0.28, 1.0), Color(1.0, 1.0, 1.0, 1.0))
		else:
			btn_play_game.text = "🚀 PROBAR UBICACIÓN (FASE %d)" % g.get("phase", 2)
			_style_pill_button(btn_play_game, Color(0.88, 0.55, 0.10, 1.0), Color(1.0, 1.0, 1.0, 1.0))

func open_menu(location_id: String = "") -> void:
	_resolve_dependencies()
	if not is_open:
		_previous_mouse_mode = Input.mouse_mode

	is_open = true
	visible = true
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE

	if player and player.has_method("set_input_enabled"):
		player.set_input_enabled(false)

	if not location_id.is_empty():
		filter_by_location(location_id)
	else:
		current_location_filter = ""
		select_category(current_category)

	menu_opened.emit()

func close_menu() -> void:
	if not is_open:
		return

	is_open = false
	visible = false

	var start_screen = get_tree().root.find_child("StartScreen", true, false) if get_tree() else null
	if start_screen and "is_menu_active" in start_screen and start_screen.is_menu_active:
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	else:
		if player and player.has_method("set_input_enabled"):
			player.set_input_enabled(true)
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED

	menu_closed.emit()

func toggle_menu(location_id: String = "") -> void:
	if is_open:
		close_menu()
	else:
		open_menu(location_id)

func _on_play_pressed() -> void:
	var g = MinigameCatalogClass.get_minigame(selected_game_id)
	if g.is_empty():
		return

	if g.get("is_playable", false):
		close_menu()
		if minigame_manager and minigame_manager.has_method("start_or_summon_minigame"):
			minigame_manager.start_or_summon_minigame(
				selected_game_id,
				0,
				g.get("max_players", 8),
				g.get("arena_id", 1)
			)
		elif minigame_manager and minigame_manager.has_method("send_summon_request"):
			minigame_manager.send_summon_request(
				selected_game_id,
				0,
				g.get("max_players", 8),
				g.get("arena_id", 1)
			)
		minigame_launched.emit(selected_game_id)
	else:
		# Si es de Fase 2-4, teletransportar a la sede y mostrar banner informativo
		_on_teleport_location_pressed()
		if minigame_manager and minigame_manager.has_method("notify_upcoming_minigame"):
			minigame_manager.notify_upcoming_minigame(selected_game_id)

func _on_teleport_location_pressed() -> void:
	var g = MinigameCatalogClass.get_minigame(selected_game_id)
	if g.is_empty():
		return

	var target_pos: Vector3 = g.get("spawn_position", Vector3(-6.6844, 401.80, 2.6878))
	var loc_id: String = g.get("location_id", "kiosko")

	close_menu()

	if player and is_instance_valid(player):
		if "is_sitting" in player and player.is_sitting and player.has_method("stand_up"):
			player.stand_up()
		if "current_vehicle" in player and player.current_vehicle and player.has_method("dismount_vehicle"):
			player.dismount_vehicle()
		player.global_position = target_pos
		player.velocity = Vector3.ZERO

	location_teleported.emit(loc_id, target_pos)
