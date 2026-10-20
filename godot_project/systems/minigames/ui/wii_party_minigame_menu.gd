class_name WiiPartyMinigameMenu
extends CanvasLayer

## Menú de Minijuegos y Retas Urbanas para Tecate Simulator.
## Presenta la selección de minijuegos con la estética cívica e institucional
## del simulador, coherente con la pantalla de inicio y el HUD de exploración.

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

# Nodos de Interfaz
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

# Panel derecho de vista previa y detalle del minijuego
var preview_header_panel: PanelContainer = null
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
	_din_font = load(AppTechnicalStrings.FONT_DIN_CONDENSED_BOLD)
	_resolve_dependencies()
	_build_menu_ui()
	select_category(MinigameCatalogClass.Category.ALL)
	select_minigame(1)

func _resolve_dependencies() -> void:
	if has_node(minigame_manager_path):
		minigame_manager = get_node(minigame_manager_path)
	elif get_parent() and get_parent().has_node(AppTechnicalStrings.NODE_MINIGAME_MANAGER):
		minigame_manager = get_parent().get_node(AppTechnicalStrings.NODE_MINIGAME_MANAGER)

	if has_node(player_path):
		player = get_node(player_path)
	elif get_parent() and get_parent().has_node(AppTechnicalStrings.NODE_PLAYER):
		player = get_parent().get_node(AppTechnicalStrings.NODE_PLAYER)

func _build_menu_ui() -> void:
	root_control = Control.new()
	root_control.name = &"MinigameMenuRoot"
	root_control.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(root_control)

	# 1. Fondo atmosférico oscuro semi-translúcido institucional
	backdrop = ColorRect.new()
	backdrop.name = &"Backdrop"
	backdrop.set_anchors_preset(Control.PRESET_FULL_RECT)
	backdrop.color = Color(0.04, 0.05, 0.08, 0.88)
	root_control.add_child(backdrop)

	var center_margin = MarginContainer.new()
	center_margin.set_anchors_preset(Control.PRESET_FULL_RECT)
	center_margin.add_theme_constant_override(AppTechnicalStrings.THEME_MARGIN_LEFT, 48)
	center_margin.add_theme_constant_override(AppTechnicalStrings.THEME_MARGIN_RIGHT, 48)
	center_margin.add_theme_constant_override(AppTechnicalStrings.THEME_MARGIN_TOP, 32)
	center_margin.add_theme_constant_override(AppTechnicalStrings.THEME_MARGIN_BOTTOM, 32)
	root_control.add_child(center_margin)

	# 2. Tablero Principal de Tecate Simulator (Panel oscuro con borde Rojo Tecate)
	main_board = PanelContainer.new()
	main_board.name = &"MainBoard"
	main_board.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	main_board.size_flags_vertical = Control.SIZE_EXPAND_FILL

	var style_board = StyleBoxFlat.new()
	style_board.bg_color = Color(0.08, 0.10, 0.14, 0.94)
	style_board.border_width_left = 2
	style_board.border_width_top = 2
	style_board.border_width_right = 2
	style_board.border_width_bottom = 2
	style_board.border_color = Color(0.85, 0.16, 0.16, 0.85) # Rojo Tecate institucional
	style_board.corner_radius_top_left = 8
	style_board.corner_radius_top_right = 8
	style_board.corner_radius_bottom_left = 8
	style_board.corner_radius_bottom_right = 8
	style_board.shadow_color = Color(0.0, 0.0, 0.0, 0.60)
	style_board.shadow_size = 16
	style_board.content_margin_left = 24
	style_board.content_margin_right = 24
	style_board.content_margin_top = 20
	style_board.content_margin_bottom = 20
	main_board.add_theme_stylebox_override(AppTechnicalStrings.THEME_STYLE_PANEL, style_board)
	center_margin.add_child(main_board)

	var board_vbox = VBoxContainer.new()
	board_vbox.add_theme_constant_override(AppTechnicalStrings.THEME_SEPARATION, 14)
	main_board.add_child(board_vbox)

	# 3. Cabecera Superior Institucional
	var top_bar = HBoxContainer.new()
	top_bar.add_theme_constant_override(AppTechnicalStrings.THEME_SEPARATION, 16)
	board_vbox.add_child(top_bar)

	var title_vbox = VBoxContainer.new()
	title_vbox.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	title_vbox.add_theme_constant_override(AppTechnicalStrings.THEME_SEPARATION, 2)
	top_bar.add_child(title_vbox)

	header_title_label = Label.new()
	header_title_label.text = AppStrings.MINIGAMES_HEADER_TITLE
	if _din_font:
		header_title_label.add_theme_font_override(AppTechnicalStrings.THEME_FONT, _din_font)
	header_title_label.add_theme_font_size_override(AppTechnicalStrings.THEME_FONT_SIZE, 32)
	header_title_label.add_theme_color_override(AppTechnicalStrings.THEME_FONT_COLOR, Color(0.96, 0.95, 0.92, 1.0))
	title_vbox.add_child(header_title_label)

	header_subtitle_label = Label.new()
	header_subtitle_label.text = AppStrings.MINIGAMES_HEADER_SUBTITLE
	if _din_font:
		header_subtitle_label.add_theme_font_override(AppTechnicalStrings.THEME_FONT, _din_font)
	header_subtitle_label.add_theme_font_size_override(AppTechnicalStrings.THEME_FONT_SIZE, 18)
	header_subtitle_label.add_theme_color_override(AppTechnicalStrings.THEME_FONT_COLOR, Color(1.0, 0.72, 0.0, 0.95)) # Dorado Sol
	title_vbox.add_child(header_subtitle_label)

	btn_close_menu = Button.new()
	btn_close_menu.name = &"BtnCloseMenu"
	btn_close_menu.text = AppStrings.MINIGAMES_BTN_CLOSE
	btn_close_menu.custom_minimum_size = Vector2(160, 40)
	btn_close_menu.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	if _din_font:
		btn_close_menu.add_theme_font_override(AppTechnicalStrings.THEME_FONT, _din_font)
	btn_close_menu.add_theme_font_size_override(AppTechnicalStrings.THEME_FONT_SIZE, 20)
	_apply_action_button_style(btn_close_menu, Color(0.85, 0.16, 0.16, 0.85))
	btn_close_menu.pressed.connect(close_menu)
	top_bar.add_child(btn_close_menu)

	# Línea divisoria de acento (AccentLine)
	var accent_line = ColorRect.new()
	accent_line.custom_minimum_size = Vector2(0, 2)
	accent_line.color = Color(0.85, 0.16, 0.16, 0.90)
	board_vbox.add_child(accent_line)

	# 4. Pestañas de Categoría y Filtro de Ubicación
	var nav_row = HBoxContainer.new()
	nav_row.add_theme_constant_override(AppTechnicalStrings.THEME_SEPARATION, 12)
	board_vbox.add_child(nav_row)

	category_tabs_hbox = HBoxContainer.new()
	category_tabs_hbox.add_theme_constant_override(AppTechnicalStrings.THEME_SEPARATION, 10)
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
		tab_btn.name = &"Tab_" + str(cat_id)
		tab_btn.text = AppStrings.format_minigame_tab_count(c_info[&"short_name"], count)
		tab_btn.custom_minimum_size = Vector2(170, 38)
		tab_btn.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
		if _din_font:
			tab_btn.add_theme_font_override(AppTechnicalStrings.THEME_FONT, _din_font)
		tab_btn.add_theme_font_size_override(AppTechnicalStrings.THEME_FONT_SIZE, 20)
		tab_btn.pressed.connect(func():
			current_location_filter = ""
			select_category(cat_id)
		)
		category_tabs_hbox.add_child(tab_btn)
		category_buttons[cat_id] = tab_btn

	# Banner de filtro por ubicación
	location_filter_banner = PanelContainer.new()
	location_filter_banner.name = &"LocationFilterBanner"
	location_filter_banner.visible = false
	location_filter_banner.size_flags_horizontal = Control.SIZE_EXPAND_FILL

	var style_loc_banner = StyleBoxFlat.new()
	style_loc_banner.bg_color = Color(0.10, 0.13, 0.18, 0.90)
	style_loc_banner.border_width_left = 2
	style_loc_banner.border_width_top = 2
	style_loc_banner.border_width_right = 2
	style_loc_banner.border_width_bottom = 2
	style_loc_banner.border_color = Color(1.0, 0.72, 0.0, 0.85) # Dorado Sol
	style_loc_banner.corner_radius_top_left = 6
	style_loc_banner.corner_radius_top_right = 6
	style_loc_banner.corner_radius_bottom_left = 6
	style_loc_banner.corner_radius_bottom_right = 6
	style_loc_banner.content_margin_left = 12
	style_loc_banner.content_margin_right = 12
	style_loc_banner.content_margin_top = 4
	style_loc_banner.content_margin_bottom = 4
	location_filter_banner.add_theme_stylebox_override(AppTechnicalStrings.THEME_STYLE_PANEL, style_loc_banner)

	var loc_hbox = HBoxContainer.new()
	loc_hbox.add_theme_constant_override(AppTechnicalStrings.THEME_SEPARATION, 10)
	location_filter_banner.add_child(loc_hbox)

	location_filter_label = Label.new()
	location_filter_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	if _din_font:
		location_filter_label.add_theme_font_override(AppTechnicalStrings.THEME_FONT, _din_font)
	location_filter_label.add_theme_font_size_override(AppTechnicalStrings.THEME_FONT_SIZE, 18)
	location_filter_label.add_theme_color_override(AppTechnicalStrings.THEME_FONT_COLOR, Color(1.0, 0.85, 0.35, 1.0))
	loc_hbox.add_child(location_filter_label)

	btn_clear_location_filter = Button.new()
	btn_clear_location_filter.text = AppStrings.MINIGAMES_CLEAR_FILTER
	btn_clear_location_filter.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	if _din_font:
		btn_clear_location_filter.add_theme_font_override(AppTechnicalStrings.THEME_FONT, _din_font)
	btn_clear_location_filter.add_theme_font_size_override(AppTechnicalStrings.THEME_FONT_SIZE, 17)
	_apply_action_button_style(btn_clear_location_filter, Color(1.0, 0.72, 0.0, 0.85))
	btn_clear_location_filter.pressed.connect(func():
		current_location_filter = ""
		select_category(MinigameCatalogClass.Category.ALL)
	)
	loc_hbox.add_child(btn_clear_location_filter)
	nav_row.add_child(location_filter_banner)

	# 5. Cuerpo Dividido: Columna Izquierda (Cuadrícula) y Columna Derecha (Ficha)
	var content_split = HBoxContainer.new()
	content_split.size_flags_vertical = Control.SIZE_EXPAND_FILL
	content_split.add_theme_constant_override(AppTechnicalStrings.THEME_SEPARATION, 20)
	board_vbox.add_child(content_split)

	# 5A. Columna Izquierda: ScrollContainer y Cuadrícula
	var left_panel = PanelContainer.new()
	left_panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	left_panel.size_flags_vertical = Control.SIZE_EXPAND_FILL
	left_panel.size_flags_stretch_ratio = 1.15

	var style_left = StyleBoxFlat.new()
	style_left.bg_color = Color(0.05, 0.06, 0.08, 0.75)
	style_left.border_width_left = 1
	style_left.border_width_top = 1
	style_left.border_width_right = 1
	style_left.border_width_bottom = 1
	style_left.border_color = Color(0.85, 0.16, 0.16, 0.35)
	style_left.corner_radius_top_left = 8
	style_left.corner_radius_top_right = 8
	style_left.corner_radius_bottom_left = 8
	style_left.corner_radius_bottom_right = 8
	style_left.content_margin_left = 12
	style_left.content_margin_right = 12
	style_left.content_margin_top = 12
	style_left.content_margin_bottom = 12
	left_panel.add_theme_stylebox_override(AppTechnicalStrings.THEME_STYLE_PANEL, style_left)
	content_split.add_child(left_panel)

	var scroll = ScrollContainer.new()
	scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	left_panel.add_child(scroll)

	games_grid = GridContainer.new()
	games_grid.name = &"GamesGrid"
	games_grid.columns = 2
	games_grid.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	games_grid.add_theme_constant_override(AppTechnicalStrings.THEME_H_SEPARATION, 12)
	games_grid.add_theme_constant_override(AppTechnicalStrings.THEME_V_SEPARATION, 12)
	scroll.add_child(games_grid)

	# 5B. Columna Derecha: Ficha Detallada del Minijuego
	var right_card = PanelContainer.new()
	right_card.name = &"PreviewCard"
	right_card.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	right_card.size_flags_vertical = Control.SIZE_EXPAND_FILL
	right_card.size_flags_stretch_ratio = 1.0

	var style_right = StyleBoxFlat.new()
	style_right.bg_color = Color(0.06, 0.08, 0.11, 0.88)
	style_right.border_width_left = 2
	style_right.border_width_top = 2
	style_right.border_width_right = 2
	style_right.border_width_bottom = 2
	style_right.border_color = Color(0.85, 0.16, 0.16, 0.80)
	style_right.corner_radius_top_left = 8
	style_right.corner_radius_top_right = 8
	style_right.corner_radius_bottom_left = 8
	style_right.corner_radius_bottom_right = 8
	style_right.content_margin_left = 18
	style_right.content_margin_right = 18
	style_right.content_margin_top = 16
	style_right.content_margin_bottom = 16
	right_card.add_theme_stylebox_override(AppTechnicalStrings.THEME_STYLE_PANEL, style_right)
	content_split.add_child(right_card)

	var preview_vbox = VBoxContainer.new()
	preview_vbox.add_theme_constant_override(AppTechnicalStrings.THEME_SEPARATION, 12)
	right_card.add_child(preview_vbox)

	# Encabezado de la Ficha
	var prev_title_vbox = VBoxContainer.new()
	prev_title_vbox.add_theme_constant_override(AppTechnicalStrings.THEME_SEPARATION, 3)
	preview_vbox.add_child(prev_title_vbox)

	preview_title_label = Label.new()
	preview_title_label.text = AppStrings.MINIGAME_1_TITLE
	if _din_font:
		preview_title_label.add_theme_font_override(AppTechnicalStrings.THEME_FONT, _din_font)
	preview_title_label.add_theme_font_size_override(AppTechnicalStrings.THEME_FONT_SIZE, 30)
	preview_title_label.add_theme_color_override(AppTechnicalStrings.THEME_FONT_COLOR, Color(0.96, 0.95, 0.92, 1.0))
	prev_title_vbox.add_child(preview_title_label)

	preview_subtitle_label = Label.new()
	preview_subtitle_label.text = AppStrings.MINIGAME_1_SUBTITLE
	if _din_font:
		preview_subtitle_label.add_theme_font_override(AppTechnicalStrings.THEME_FONT, _din_font)
	preview_subtitle_label.add_theme_font_size_override(AppTechnicalStrings.THEME_FONT_SIZE, 17)
	preview_subtitle_label.add_theme_color_override(AppTechnicalStrings.THEME_FONT_COLOR, Color(1.0, 0.72, 0.0, 0.95))
	preview_subtitle_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	prev_title_vbox.add_child(preview_subtitle_label)

	var prev_accent = ColorRect.new()
	prev_accent.custom_minimum_size = Vector2(0, 2)
	prev_accent.color = Color(0.85, 0.16, 0.16, 0.80)
	prev_title_vbox.add_child(prev_accent)

	# Fila de Insignias (Categoría, Jugadores, Duración y Fase)
	var badges_hbox = HBoxContainer.new()
	badges_hbox.add_theme_constant_override(AppTechnicalStrings.THEME_SEPARATION, 8)
	preview_vbox.add_child(badges_hbox)

	preview_category_badge = _create_badge_label(AppStrings.MINIGAMES_BADGE_ALL_VS_ALL, Color(0.85, 0.16, 0.16, 1.0))
	badges_hbox.add_child(preview_category_badge)

	preview_players_badge = _create_badge_label(AppStrings.MINIGAME_1_TITLE, Color(0.12, 0.16, 0.22, 1.0))
	badges_hbox.add_child(preview_players_badge)

	preview_duration_badge = _create_badge_label(AppStrings.format_minigame_duration_reward(90, 50), Color(0.20, 0.24, 0.32, 1.0))
	badges_hbox.add_child(preview_duration_badge)

	preview_phase_badge = _create_badge_label(AppStrings.MINIGAMES_STATUS_PLAYABLE, Color(0.16, 0.65, 0.28, 1.0))
	badges_hbox.add_child(preview_phase_badge)

	# Banda de Ubicación en Tecate
	var loc_strip = PanelContainer.new()
	var style_loc = StyleBoxFlat.new()
	style_loc.bg_color = Color(0.08, 0.10, 0.14, 0.70)
	style_loc.border_width_left = 3
	style_loc.border_color = Color(0.85, 0.16, 0.16, 0.90)
	style_loc.corner_radius_top_right = 6
	style_loc.corner_radius_bottom_right = 6
	style_loc.content_margin_left = 12
	style_loc.content_margin_right = 12
	style_loc.content_margin_top = 6
	style_loc.content_margin_bottom = 6
	loc_strip.add_theme_stylebox_override(AppTechnicalStrings.THEME_STYLE_PANEL, style_loc)
	preview_vbox.add_child(loc_strip)

	preview_location_label = Label.new()
	preview_location_label.text = AppStrings.format_minigame_location_label(AppStrings.MINIGAME_1_TITLE)
	if _din_font:
		preview_location_label.add_theme_font_override(AppTechnicalStrings.THEME_FONT, _din_font)
	preview_location_label.add_theme_font_size_override(AppTechnicalStrings.THEME_FONT_SIZE, 17)
	preview_location_label.add_theme_color_override(AppTechnicalStrings.THEME_FONT_COLOR, Color(0.85, 0.88, 0.94, 1.0))
	loc_strip.add_child(preview_location_label)

	# Recuadro de Reglas del Juego
	var rules_panel = PanelContainer.new()
	rules_panel.size_flags_vertical = Control.SIZE_EXPAND_FILL
	var style_rules = StyleBoxFlat.new()
	style_rules.bg_color = Color(0.05, 0.06, 0.08, 0.65)
	style_rules.border_width_left = 1
	style_rules.border_width_top = 1
	style_rules.border_width_right = 1
	style_rules.border_width_bottom = 1
	style_rules.border_color = Color(0.85, 0.16, 0.16, 0.25)
	style_rules.corner_radius_top_left = 6
	style_rules.corner_radius_top_right = 6
	style_rules.corner_radius_bottom_left = 6
	style_rules.corner_radius_bottom_right = 6
	style_rules.content_margin_left = 12
	style_rules.content_margin_right = 12
	style_rules.content_margin_top = 8
	style_rules.content_margin_bottom = 8
	rules_panel.add_theme_stylebox_override(AppTechnicalStrings.THEME_STYLE_PANEL, style_rules)
	preview_vbox.add_child(rules_panel)

	var rules_vbox = VBoxContainer.new()
	rules_vbox.add_theme_constant_override(AppTechnicalStrings.THEME_SEPARATION, 6)
	rules_panel.add_child(rules_vbox)

	var rules_header = Label.new()
	rules_header.text = AppStrings.MINIGAMES_SECTION_RULES
	if _din_font:
		rules_header.add_theme_font_override(AppTechnicalStrings.THEME_FONT, _din_font)
	rules_header.add_theme_font_size_override(AppTechnicalStrings.THEME_FONT_SIZE, 19)
	rules_header.add_theme_color_override(AppTechnicalStrings.THEME_FONT_COLOR, Color(1.0, 0.72, 0.0, 1.0))
	rules_vbox.add_child(rules_header)

	preview_description_label = Label.new()
	preview_description_label.size_flags_vertical = Control.SIZE_EXPAND_FILL
	preview_description_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	preview_description_label.add_theme_font_size_override(AppTechnicalStrings.THEME_FONT_SIZE, 15)
	preview_description_label.add_theme_color_override(AppTechnicalStrings.THEME_FONT_COLOR, Color(0.92, 0.92, 0.90, 1.0))
	rules_vbox.add_child(preview_description_label)

	# Recuadro de Controles
	var controls_panel = PanelContainer.new()
	var style_ctrls = style_rules.duplicate() as StyleBoxFlat
	controls_panel.add_theme_stylebox_override(AppTechnicalStrings.THEME_STYLE_PANEL, style_ctrls)
	preview_vbox.add_child(controls_panel)

	var ctrls_outer_vbox = VBoxContainer.new()
	ctrls_outer_vbox.add_theme_constant_override(AppTechnicalStrings.THEME_SEPARATION, 6)
	controls_panel.add_child(ctrls_outer_vbox)

	var ctrls_title = Label.new()
	ctrls_title.text = AppStrings.MINIGAMES_SECTION_CONTROLS
	if _din_font:
		ctrls_title.add_theme_font_override(AppTechnicalStrings.THEME_FONT, _din_font)
	ctrls_title.add_theme_font_size_override(AppTechnicalStrings.THEME_FONT_SIZE, 19)
	ctrls_title.add_theme_color_override(AppTechnicalStrings.THEME_FONT_COLOR, Color(1.0, 0.72, 0.0, 1.0))
	ctrls_outer_vbox.add_child(ctrls_title)

	preview_controls_vbox = VBoxContainer.new()
	preview_controls_vbox.add_theme_constant_override(AppTechnicalStrings.THEME_SEPARATION, 5)
	ctrls_outer_vbox.add_child(preview_controls_vbox)

	preview_status_feedback = Label.new()
	preview_status_feedback.visible = false
	preview_status_feedback.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	if _din_font:
		preview_status_feedback.add_theme_font_override(AppTechnicalStrings.THEME_FONT, _din_font)
	preview_status_feedback.add_theme_font_size_override(AppTechnicalStrings.THEME_FONT_SIZE, 17)
	preview_status_feedback.add_theme_color_override(AppTechnicalStrings.THEME_FONT_COLOR, Color(0.20, 0.75, 0.35, 1.0))
	preview_vbox.add_child(preview_status_feedback)

	# Botones de Acción Inferiores
	var actions_hbox = HBoxContainer.new()
	actions_hbox.add_theme_constant_override(AppTechnicalStrings.THEME_SEPARATION, 12)
	preview_vbox.add_child(actions_hbox)

	btn_play_game = Button.new()
	btn_play_game.name = &"BtnPlayGame"
	btn_play_game.text = AppStrings.MINIGAMES_BTN_PLAY
	btn_play_game.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	btn_play_game.custom_minimum_size = Vector2(200, 46)
	btn_play_game.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	if _din_font:
		btn_play_game.add_theme_font_override(AppTechnicalStrings.THEME_FONT, _din_font)
	btn_play_game.add_theme_font_size_override(AppTechnicalStrings.THEME_FONT_SIZE, 24)
	_apply_action_button_style(btn_play_game, Color(0.18, 0.65, 0.32, 0.90))
	btn_play_game.pressed.connect(_on_play_pressed)
	actions_hbox.add_child(btn_play_game)

	btn_teleport_location = Button.new()
	btn_teleport_location.name = &"BtnTeleportLocation"
	btn_teleport_location.text = AppStrings.MINIGAMES_BTN_TELEPORT
	btn_teleport_location.custom_minimum_size = Vector2(175, 46)
	btn_teleport_location.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	if _din_font:
		btn_teleport_location.add_theme_font_override(AppTechnicalStrings.THEME_FONT, _din_font)
	btn_teleport_location.add_theme_font_size_override(AppTechnicalStrings.THEME_FONT_SIZE, 22)
	_apply_action_button_style(btn_teleport_location, Color(0.85, 0.16, 0.16, 0.85))
	btn_teleport_location.pressed.connect(_on_teleport_location_pressed)
	actions_hbox.add_child(btn_teleport_location)

func _create_badge_label(text_val: String, border_col: Color) -> Label:
	var lbl = Label.new()
	lbl.text = text_val
	if _din_font:
		lbl.add_theme_font_override(AppTechnicalStrings.THEME_FONT, _din_font)
	lbl.add_theme_font_size_override(AppTechnicalStrings.THEME_FONT_SIZE, 15)
	lbl.add_theme_color_override(AppTechnicalStrings.THEME_FONT_COLOR, Color(0.96, 0.95, 0.92, 1.0))
	var st = StyleBoxFlat.new()
	st.bg_color = Color(0.10, 0.12, 0.16, 0.90)
	st.border_width_left = 1
	st.border_width_top = 1
	st.border_width_right = 1
	st.border_width_bottom = 1
	st.border_color = border_col
	st.corner_radius_top_left = 4
	st.corner_radius_top_right = 4
	st.corner_radius_bottom_left = 4
	st.corner_radius_bottom_right = 4
	st.content_margin_left = 8
	st.content_margin_right = 8
	st.content_margin_top = 4
	st.content_margin_bottom = 4
	lbl.add_theme_stylebox_override(AppTechnicalStrings.THEME_STYLE_NORMAL, st)
	return lbl

func _apply_action_button_style(btn: Button, accent_color: Color) -> void:
	btn.add_theme_color_override(AppTechnicalStrings.THEME_FONT_COLOR, Color(0.96, 0.95, 0.92, 1.0))
	btn.add_theme_color_override(AppTechnicalStrings.THEME_FONT_HOVER_COLOR, Color(1.0, 0.85, 0.35, 1.0))
	btn.add_theme_color_override(AppTechnicalStrings.THEME_FONT_FOCUS_COLOR, Color(1.0, 0.85, 0.35, 1.0))
	btn.add_theme_color_override(AppTechnicalStrings.THEME_FONT_PRESSED_COLOR, Color(0.85, 0.16, 0.16, 1.0))

	var style_normal = StyleBoxFlat.new()
	style_normal.bg_color = Color(0.08, 0.10, 0.14, 0.85)
	style_normal.border_width_left = 2
	style_normal.border_width_top = 2
	style_normal.border_width_right = 2
	style_normal.border_width_bottom = 2
	style_normal.border_color = accent_color
	style_normal.corner_radius_top_left = 6
	style_normal.corner_radius_bottom_left = 6
	style_normal.corner_radius_top_right = 6
	style_normal.corner_radius_bottom_right = 6
	style_normal.content_margin_left = 16
	style_normal.content_margin_right = 16
	style_normal.content_margin_top = 6
	style_normal.content_margin_bottom = 6
	btn.add_theme_stylebox_override(AppTechnicalStrings.THEME_STYLE_NORMAL, style_normal)

	var style_hover = style_normal.duplicate() as StyleBoxFlat
	style_hover.bg_color = Color(0.12, 0.15, 0.20, 0.92)
	style_hover.border_color = Color(1.0, 0.72, 0.0, 1.0) # Dorado Sol
	btn.add_theme_stylebox_override(AppTechnicalStrings.THEME_STYLE_HOVER, style_hover)
	btn.add_theme_stylebox_override(AppTechnicalStrings.THEME_STYLE_FOCUS, style_hover)

	var style_pressed = style_hover.duplicate() as StyleBoxFlat
	style_pressed.bg_color = Color(0.05, 0.07, 0.10, 0.95)
	btn.add_theme_stylebox_override(AppTechnicalStrings.THEME_STYLE_PRESSED, style_pressed)

func select_category(cat_id: int) -> void:
	current_category = cat_id
	_update_category_tab_styles()
	_rebuild_games_grid()

func filter_by_location(location_id: String) -> void:
	current_location_filter = location_id
	var loc_info = MinigameCatalogClass.get_location_info(location_id)
	if not loc_info.is_empty() and location_filter_banner and location_filter_label:
		location_filter_banner.visible = true
		location_filter_label.text = AppStrings.format_minigame_location_filter(loc_info.get(&"name", location_id))
	_update_category_tab_styles()
	_rebuild_games_grid()

	var loc_games = MinigameCatalogClass.get_minigames_by_location(location_id)
	if not loc_games.is_empty():
		var primary_id = int(loc_info.get(&"primary_game_id", loc_games[0][&"id"]))
		select_minigame(primary_id)

func _update_category_tab_styles() -> void:
	for cat_id in category_buttons.keys():
		var btn: Button = category_buttons[cat_id]
		var active = (cat_id == current_category and current_location_filter.is_empty())
		if active:
			_apply_action_button_style(btn, Color(1.0, 0.72, 0.0, 1.0))
			btn.add_theme_color_override(AppTechnicalStrings.THEME_FONT_COLOR, Color(1.0, 0.85, 0.35, 1.0))
		else:
			_apply_action_button_style(btn, Color(0.85, 0.16, 0.16, 0.35))
			btn.add_theme_color_override(AppTechnicalStrings.THEME_FONT_COLOR, Color(0.80, 0.82, 0.86, 0.85))

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
		game_tile_buttons[g[&"id"]] = tile

	_highlight_selected_tile()

func _create_game_tile(g: Dictionary) -> Button:
	var gid: int = g[&"id"]
	var btn = Button.new()
	btn.name = &"GameTile_" + str(gid)
	btn.custom_minimum_size = Vector2(235, 102)
	btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	btn.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND

	var margin = MarginContainer.new()
	margin.set_anchors_preset(Control.PRESET_FULL_RECT)
	margin.mouse_filter = Control.MOUSE_FILTER_IGNORE
	margin.add_theme_constant_override(AppTechnicalStrings.THEME_MARGIN_LEFT, 14)
	margin.add_theme_constant_override(AppTechnicalStrings.THEME_MARGIN_RIGHT, 14)
	margin.add_theme_constant_override(AppTechnicalStrings.THEME_MARGIN_TOP, 10)
	margin.add_theme_constant_override(AppTechnicalStrings.THEME_MARGIN_BOTTOM, 10)
	btn.add_child(margin)

	var vbox = VBoxContainer.new()
	vbox.mouse_filter = Control.MOUSE_FILTER_IGNORE
	vbox.add_theme_constant_override(AppTechnicalStrings.THEME_SEPARATION, 4)
	margin.add_child(vbox)

	# Fila 1: Número e Indicador de Estado
	var top_row = HBoxContainer.new()
	top_row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	vbox.add_child(top_row)

	var num_lbl = Label.new()
	num_lbl.text = AppStrings.format_minigame_tile_number(gid)
	if _din_font:
		num_lbl.add_theme_font_override(AppTechnicalStrings.THEME_FONT, _din_font)
	num_lbl.add_theme_font_size_override(AppTechnicalStrings.THEME_FONT_SIZE, 20)
	num_lbl.add_theme_color_override(AppTechnicalStrings.THEME_FONT_COLOR, Color(1.0, 0.72, 0.0, 0.95))
	num_lbl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top_row.add_child(num_lbl)

	var status_lbl = Label.new()
	if g.get(&"is_playable", false):
		status_lbl.text = AppStrings.MINIGAMES_STATUS_PLAYABLE
		status_lbl.add_theme_color_override(AppTechnicalStrings.THEME_FONT_COLOR, Color(0.20, 0.75, 0.35, 1.0))
	else:
		status_lbl.text = AppStrings.format_minigame_phase(g.get(&"phase", 2))
		status_lbl.add_theme_color_override(AppTechnicalStrings.THEME_FONT_COLOR, Color(1.0, 0.75, 0.25, 0.90))
	if _din_font:
		status_lbl.add_theme_font_override(AppTechnicalStrings.THEME_FONT, _din_font)
	status_lbl.add_theme_font_size_override(AppTechnicalStrings.THEME_FONT_SIZE, 15)
	top_row.add_child(status_lbl)

	# Fila 2: Título del minijuego (capitalización normal de Tecate Simulator)
	var title_lbl = Label.new()
	title_lbl.text = g[&"title"]
	if _din_font:
		title_lbl.add_theme_font_override(AppTechnicalStrings.THEME_FONT, _din_font)
	title_lbl.add_theme_font_size_override(AppTechnicalStrings.THEME_FONT_SIZE, 22)
	title_lbl.add_theme_color_override(AppTechnicalStrings.THEME_FONT_COLOR, Color(0.96, 0.95, 0.92, 1.0))
	vbox.add_child(title_lbl)

	# Fila 3: Ubicación
	var loc_info = MinigameCatalogClass.get_location_info(g[&"location_id"])
	var loc_lbl = Label.new()
	loc_lbl.text = loc_info.get(&"short_name", g[&"location_name"])
	if _din_font:
		loc_lbl.add_theme_font_override(AppTechnicalStrings.THEME_FONT, _din_font)
	loc_lbl.add_theme_font_size_override(AppTechnicalStrings.THEME_FONT_SIZE, 14)
	loc_lbl.add_theme_color_override(AppTechnicalStrings.THEME_FONT_COLOR, Color(0.70, 0.74, 0.80, 0.90))
	vbox.add_child(loc_lbl)

	btn.pressed.connect(func(): select_minigame(gid))
	return btn

func _highlight_selected_tile() -> void:
	for gid in game_tile_buttons.keys():
		var btn: Button = game_tile_buttons[gid]
		var is_sel = (gid == selected_game_id)

		var st = StyleBoxFlat.new()
		st.corner_radius_top_left = 6
		st.corner_radius_top_right = 6
		st.corner_radius_bottom_left = 6
		st.corner_radius_bottom_right = 6

		if is_sel:
			st.bg_color = Color(0.10, 0.13, 0.18, 0.95)
			st.border_width_left = 2
			st.border_width_top = 2
			st.border_width_right = 2
			st.border_width_bottom = 2
			st.border_color = Color(1.0, 0.72, 0.0, 1.0) # Dorado Sol
			st.shadow_color = Color(1.0, 0.72, 0.0, 0.20)
			st.shadow_size = 8
		else:
			st.bg_color = Color(0.05, 0.07, 0.10, 0.80)
			st.border_width_left = 1
			st.border_width_top = 1
			st.border_width_right = 1
			st.border_width_bottom = 1
			st.border_color = Color(0.85, 0.16, 0.16, 0.35)
			st.shadow_size = 0

		var st_hover = st.duplicate() as StyleBoxFlat
		st_hover.bg_color = Color(0.12, 0.15, 0.20, 0.92)
		st_hover.border_color = Color(1.0, 0.78, 0.25, 1.0)

		btn.add_theme_stylebox_override(AppTechnicalStrings.THEME_STYLE_NORMAL, st)
		btn.add_theme_stylebox_override(AppTechnicalStrings.THEME_STYLE_HOVER, st_hover)
		btn.add_theme_stylebox_override(AppTechnicalStrings.THEME_STYLE_FOCUS, st_hover)
		btn.add_theme_stylebox_override(AppTechnicalStrings.THEME_STYLE_PRESSED, st)

func select_minigame(game_id: int) -> void:
	var g = MinigameCatalogClass.get_minigame(game_id)
	if g.is_empty():
		return

	selected_game_id = game_id
	_highlight_selected_tile()

	if preview_status_feedback:
		preview_status_feedback.visible = false

	if preview_title_label:
		preview_title_label.text = g[&"full_title"]
	if preview_subtitle_label:
		preview_subtitle_label.text = g[&"subtitle"]

	var cat_info = MinigameCatalogClass.CATEGORY_INFO.get(g[&"category"], {})
	if preview_category_badge:
		preview_category_badge.text = cat_info.get(&"name", AppStrings.MINIGAMES_BADGE_PARTY_MODE)
		var st_cat = preview_category_badge.get_theme_stylebox(AppTechnicalStrings.THEME_STYLE_NORMAL).duplicate() as StyleBoxFlat
		st_cat.border_color = cat_info.get(&"color", Color(0.85, 0.16, 0.16, 1.0))
		preview_category_badge.add_theme_stylebox_override(AppTechnicalStrings.THEME_STYLE_NORMAL, st_cat)

	if preview_players_badge:
		preview_players_badge.text = g[&"players_badge"]

	if preview_duration_badge:
		preview_duration_badge.text = AppStrings.format_minigame_duration_reward(g[&"duration_seconds"], g[&"reward_first"])

	if preview_phase_badge:
		var st_ph = preview_phase_badge.get_theme_stylebox(AppTechnicalStrings.THEME_STYLE_NORMAL).duplicate() as StyleBoxFlat
		if g.get(&"is_playable", false):
			preview_phase_badge.text = AppStrings.MINIGAMES_STATUS_PLAYABLE
			st_ph.border_color = Color(0.20, 0.75, 0.35, 1.0)
		else:
			preview_phase_badge.text = AppStrings.format_minigame_phase_preview(g.get(&"phase", 2))
			st_ph.border_color = Color(1.0, 0.75, 0.25, 0.90)
		preview_phase_badge.add_theme_stylebox_override(AppTechnicalStrings.THEME_STYLE_NORMAL, st_ph)

	if preview_location_label:
		preview_location_label.text = AppStrings.format_minigame_location_label(g[&"location_name"])

	if preview_description_label:
		preview_description_label.text = g[&"description"]

	if preview_controls_vbox:
		for c in preview_controls_vbox.get_children():
			c.queue_free()
		for ctrl in g.get(&"controls", []):
			var row = HBoxContainer.new()
			row.add_theme_constant_override(AppTechnicalStrings.THEME_SEPARATION, 10)

			var key_lbl = _create_badge_label(ctrl[&"input"], Color(1.0, 0.72, 0.0, 0.75))
			key_lbl.custom_minimum_size = Vector2(130, 26)
			key_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
			row.add_child(key_lbl)

			var act_lbl = Label.new()
			act_lbl.text = ctrl[&"action"]
			act_lbl.add_theme_font_size_override(AppTechnicalStrings.THEME_FONT_SIZE, 15)
			act_lbl.add_theme_color_override(AppTechnicalStrings.THEME_FONT_COLOR, Color(0.85, 0.88, 0.92, 1.0))
			act_lbl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			row.add_child(act_lbl)

			preview_controls_vbox.add_child(row)

	if btn_play_game:
		if g.get(&"is_playable", false):
			btn_play_game.text = AppStrings.MINIGAMES_BTN_PLAY
			_apply_action_button_style(btn_play_game, Color(0.18, 0.65, 0.32, 0.90))
		else:
			btn_play_game.text = AppStrings.MINIGAMES_BTN_TEST_LOCATION
			_apply_action_button_style(btn_play_game, Color(1.0, 0.72, 0.0, 0.85))

func open_menu(location_id: String = "") -> void:
	_resolve_dependencies()
	if minigame_manager and minigame_manager.has_method(&"is_in_minigame") and minigame_manager.is_in_minigame():
		return
	if not is_open:
		_previous_mouse_mode = Input.mouse_mode

	is_open = true
	visible = true
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE

	if player and player.has_method(AppTechnicalStrings.METHOD_SET_INPUT_ENABLED):
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

	var start_screen = get_tree().root.find_child(AppTechnicalStrings.SCENE_START_SCREEN.get_file().get_basename(), true, false) if get_tree() else null
	if start_screen and &"is_menu_active" in start_screen and start_screen.is_menu_active:
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	else:
		if player and player.has_method(AppTechnicalStrings.METHOD_SET_INPUT_ENABLED):
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

	if g.get(&"is_playable", false):
		close_menu()
		if minigame_manager and minigame_manager.has_method(&"start_or_summon_minigame"):
			minigame_manager.start_or_summon_minigame(
				selected_game_id,
				0,
				g.get(&"max_players", 8),
				g.get(&"arena_id", 1)
			)
		elif minigame_manager and minigame_manager.has_method(&"send_summon_request"):
			minigame_manager.send_summon_request(
				selected_game_id,
				0,
				g.get(&"max_players", 8),
				g.get(&"arena_id", 1)
			)
		minigame_launched.emit(selected_game_id)
	else:
		# Si es de Fase 2-4, teletransportar a la sede y mostrar banner informativo
		_on_teleport_location_pressed()
		if minigame_manager and minigame_manager.has_method(&"notify_upcoming_minigame"):
			minigame_manager.notify_upcoming_minigame(selected_game_id)

func _on_teleport_location_pressed() -> void:
	var g = MinigameCatalogClass.get_minigame(selected_game_id)
	if g.is_empty():
		return

	var target_pos: Vector3 = g.get(&"spawn_position", Vector3(-6.6844, 401.80, 2.6878))
	var loc_id: String = str(g.get(&"location_id", &"kiosko"))

	close_menu()

	if player and is_instance_valid(player):
		if &"is_sitting" in player and player.is_sitting and player.has_method(&"stand_up"):
			player.stand_up()
		if &"current_vehicle" in player and player.current_vehicle and player.has_method(&"dismount_vehicle"):
			player.dismount_vehicle()
		player.global_position = target_pos
		player.velocity = Vector3.ZERO

	location_teleported.emit(loc_id, target_pos)
