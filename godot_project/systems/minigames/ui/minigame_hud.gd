class_name MinigameHUD
extends CanvasLayer

## Interfaz Gráfica Diegética para Minijuegos en Tecate Simulator.
## Despliega invitaciones, cuenta regresiva cinemática, banners de eliminación,
## notificaciones de ubicación y el podio con recompensas en Pesos Tecatenses.

const MinigameCatalogClass = preload("res://systems/minigames/minigame_catalog.gd")

@export var minigame_manager_path: NodePath = ^"../MinigameManager"
var minigame_manager: Node = null

var root_control: Control = null
var invite_panel: PanelContainer = null
var invite_label: Label = null
var countdown_label: Label = null
var header_panel: PanelContainer = null
var header_title: Label = null
var feed_label: Label = null
var podium_panel: PanelContainer = null
var podium_vbox: VBoxContainer = null

var _countdown_timer: float = 0.0
var _is_counting_down: bool = false

func _ready() -> void:
	_resolve_manager()
	if not root_control:
		_build_ui()
	_connect_signals()

func _resolve_manager() -> void:
	if has_node(minigame_manager_path):
		minigame_manager = get_node(minigame_manager_path)
	elif get_parent() and get_parent().has_node(AppTechnicalStrings.NODE_MINIGAME_MANAGER):
		minigame_manager = get_parent().get_node(AppTechnicalStrings.NODE_MINIGAME_MANAGER)

func _build_ui() -> void:
	layer = 10
	root_control = Control.new()
	root_control.name = &"RootControl"
	root_control.set_anchors_preset(Control.PRESET_FULL_RECT)
	root_control.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(root_control)

	var din_font = load(AppTechnicalStrings.FONT_DIN_CONDENSED_BOLD)

	# 1. Banner de Invitación y Convocatoria (Arriba al Centro)
	invite_panel = PanelContainer.new()
	invite_panel.name = &"InvitePanel"
	invite_panel.visible = false
	invite_panel.set_anchors_preset(Control.PRESET_CENTER_TOP)
	invite_panel.offset_top = 40.0
	invite_panel.offset_left = -220.0
	invite_panel.offset_right = 220.0

	var style_invite = StyleBoxFlat.new()
	style_invite.bg_color = Color(0.08, 0.10, 0.14, 0.92)
	style_invite.border_color = Color(1.0, 0.72, 0.0, 1.0) # Dorado Sol
	style_invite.border_width_left = 2
	style_invite.border_width_top = 2
	style_invite.border_width_right = 2
	style_invite.border_width_bottom = 2
	style_invite.corner_radius_top_left = 6
	style_invite.corner_radius_top_right = 6
	style_invite.corner_radius_bottom_left = 6
	style_invite.corner_radius_bottom_right = 6
	style_invite.content_margin_left = 20
	style_invite.content_margin_right = 20
	style_invite.content_margin_top = 10
	style_invite.content_margin_bottom = 10
	invite_panel.add_theme_stylebox_override(AppTechnicalStrings.THEME_STYLE_PANEL, style_invite)

	invite_label = Label.new()
	invite_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	if din_font:
		invite_label.add_theme_font_override(AppTechnicalStrings.THEME_FONT, din_font)
	invite_label.add_theme_font_size_override(AppTechnicalStrings.THEME_FONT_SIZE, 22)
	invite_label.modulate = Color(1.0, 0.95, 0.85, 1.0)
	invite_panel.add_child(invite_label)
	root_control.add_child(invite_panel)

	# 2. Contador de Cuenta Regresiva (Centro de Pantalla)
	countdown_label = Label.new()
	countdown_label.name = &"CountdownLabel"
	countdown_label.visible = false
	countdown_label.set_anchors_preset(Control.PRESET_CENTER)
	countdown_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	countdown_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	if din_font:
		countdown_label.add_theme_font_override(AppTechnicalStrings.THEME_FONT, din_font)
	countdown_label.add_theme_font_size_override(AppTechnicalStrings.THEME_FONT_SIZE, 96)
	countdown_label.modulate = Color(1.0, 0.82, 0.15, 1.0)
	root_control.add_child(countdown_label)

	# 3. Encabezado de Juego Activo (Barra Superior)
	header_panel = PanelContainer.new()
	header_panel.name = &"HeaderPanel"
	header_panel.visible = false
	header_panel.set_anchors_preset(Control.PRESET_CENTER_TOP)
	header_panel.offset_top = 58.0
	header_panel.offset_left = -200.0
	header_panel.offset_right = 200.0

	var style_header = StyleBoxFlat.new()
	style_header.bg_color = Color(0.06, 0.08, 0.12, 0.88)
	style_header.border_color = Color(0.85, 0.16, 0.16, 1.0) # Rojo Tecate
	style_header.border_width_bottom = 2
	style_header.corner_radius_bottom_left = 6
	style_header.corner_radius_bottom_right = 6
	style_header.corner_radius_top_left = 6
	style_header.corner_radius_top_right = 6
	style_header.content_margin_left = 18
	style_header.content_margin_right = 18
	style_header.content_margin_top = 6
	style_header.content_margin_bottom = 6
	header_panel.add_theme_stylebox_override(AppTechnicalStrings.THEME_STYLE_PANEL, style_header)

	var header_vbox = VBoxContainer.new()
	header_vbox.alignment = BoxContainer.ALIGNMENT_CENTER
	header_panel.add_child(header_vbox)

	header_title = Label.new()
	header_title.text = AppStrings.MINIGAME_1_TITLE
	header_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	if din_font:
		header_title.add_theme_font_override(AppTechnicalStrings.THEME_FONT, din_font)
	header_title.add_theme_font_size_override(AppTechnicalStrings.THEME_FONT_SIZE, 28)
	header_title.modulate = Color(1.0, 1.0, 1.0, 1.0)
	header_vbox.add_child(header_title)
	root_control.add_child(header_panel)

	# 4. Feed de Notificaciones y Eliminaciones (Lado Derecho)
	feed_label = Label.new()
	feed_label.name = &"FeedLabel"
	feed_label.visible = false
	feed_label.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	feed_label.offset_top = 110.0
	feed_label.offset_left = -380.0
	feed_label.offset_right = -24.0
	feed_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	if din_font:
		feed_label.add_theme_font_override(AppTechnicalStrings.THEME_FONT, din_font)
	feed_label.add_theme_font_size_override(AppTechnicalStrings.THEME_FONT_SIZE, 20)
	feed_label.modulate = Color(1.0, 0.40, 0.40, 1.0)
	root_control.add_child(feed_label)

	# 5. Podio de Resultados (Ventana Modal Centrada)
	podium_panel = PanelContainer.new()
	podium_panel.name = &"PodiumPanel"
	podium_panel.visible = false
	podium_panel.set_anchors_preset(Control.PRESET_CENTER)
	podium_panel.offset_left = -200.0
	podium_panel.offset_right = 200.0
	podium_panel.offset_top = -140.0
	podium_panel.offset_bottom = 140.0

	var style_podium = StyleBoxFlat.new()
	style_podium.bg_color = Color(0.05, 0.07, 0.10, 0.95)
	style_podium.border_color = Color(1.0, 0.72, 0.0, 1.0)
	style_podium.border_width_left = 2
	style_podium.border_width_top = 2
	style_podium.border_width_right = 2
	style_podium.border_width_bottom = 2
	style_podium.corner_radius_top_left = 8
	style_podium.corner_radius_top_right = 8
	style_podium.corner_radius_bottom_left = 8
	style_podium.corner_radius_bottom_right = 8
	style_podium.content_margin_left = 24
	style_podium.content_margin_right = 24
	style_podium.content_margin_top = 16
	style_podium.content_margin_bottom = 16
	podium_panel.add_theme_stylebox_override(AppTechnicalStrings.THEME_STYLE_PANEL, style_podium)

	podium_vbox = VBoxContainer.new()
	podium_vbox.alignment = BoxContainer.ALIGNMENT_CENTER
	podium_panel.add_child(podium_vbox)
	root_control.add_child(podium_panel)

func _connect_signals() -> void:
	if not minigame_manager:
		return

	if not minigame_manager.summon_received.is_connected(_on_summon_received):
		minigame_manager.summon_received.connect(_on_summon_received)
	if not minigame_manager.minigame_started.is_connected(_on_minigame_started):
		minigame_manager.minigame_started.connect(_on_minigame_started)
	if not minigame_manager.participant_eliminated.is_connected(_on_participant_eliminated):
		minigame_manager.participant_eliminated.connect(_on_participant_eliminated)
	if not minigame_manager.minigame_ended.is_connected(_on_minigame_ended):
		minigame_manager.minigame_ended.connect(_on_minigame_ended)
	if not minigame_manager.minigame_cancelled.is_connected(_on_minigame_cancelled):
		minigame_manager.minigame_cancelled.connect(_on_minigame_cancelled)
	if &"upcoming_minigame_notified" in minigame_manager and not minigame_manager.upcoming_minigame_notified.is_connected(_on_upcoming_minigame_notified):
		minigame_manager.upcoming_minigame_notified.connect(_on_upcoming_minigame_notified)

func _on_summon_received(game_id: int, host_id: int, _mode: int, _max_players: int) -> void:
	if minigame_manager and host_id != 0 and host_id == minigame_manager.local_entity_id:
		return
	var name_str = _get_game_name(game_id)
	invite_label.text = AppStrings.format_minigame_summon_notice(name_str)
	invite_panel.visible = true

func _on_minigame_started(game_id: int, countdown: int, _participants: Array) -> void:
	invite_panel.visible = false
	podium_panel.visible = false

	header_title.text = _get_game_name(game_id)
	header_panel.visible = true

	_start_countdown(countdown)

func _start_countdown(seconds: int) -> void:
	_countdown_timer = float(seconds)
	_is_counting_down = true
	countdown_label.visible = true

func _process(delta: float) -> void:
	if _is_counting_down:
		_countdown_timer -= delta
		if _countdown_timer > 0.0:
			countdown_label.text = str(int(ceil(_countdown_timer)))
		else:
			countdown_label.text = AppStrings.MINIGAMES_STATUS_PLAYING
			if _countdown_timer <= -0.75:
				_is_counting_down = false
				countdown_label.visible = false

func _on_participant_eliminated(_game_id: int, eliminated_id: int, reason: int) -> void:
	var reason_str = AppStrings.MINIGAMES_ELIM_DEFAULT
	if reason == 1:
		reason_str = AppStrings.MINIGAMES_ELIM_FALL
	elif reason == 2:
		reason_str = AppStrings.MINIGAMES_ELIM_BALL
	elif reason == 3:
		reason_str = AppStrings.MINIGAMES_ELIM_TAG

	feed_label.modulate = Color(1.0, 0.40, 0.40, 1.0)
	feed_label.text = AppStrings.format_minigame_elimination(eliminated_id, reason_str)
	feed_label.visible = true

	var tween = create_tween()
	feed_label.modulate.a = 1.0
	tween.tween_interval(3.0)
	tween.tween_property(feed_label, ^"modulate:a", 0.0, 0.8)
	tween.tween_callback(func(): feed_label.visible = false)

func _on_upcoming_minigame_notified(_game_id: int, title: String, phase: int, location_name: String) -> void:
	feed_label.modulate = Color(1.0, 0.85, 0.25, 1.0)
	feed_label.text = AppStrings.format_minigame_upcoming(title, location_name, phase)
	feed_label.visible = true

	var tween = create_tween()
	feed_label.modulate.a = 1.0
	tween.tween_interval(4.0)
	tween.tween_property(feed_label, ^"modulate:a", 0.0, 0.8)
	tween.tween_callback(func(): feed_label.visible = false)

func _on_minigame_ended(game_id: int, winner_id: int, rankings: Array) -> void:
	header_panel.visible = false

	for child in podium_vbox.get_children():
		child.queue_free()

	var title = Label.new()
	title.text = AppStrings.format_minigame_results(_get_game_name(game_id))
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.add_theme_font_size_override(AppTechnicalStrings.THEME_FONT_SIZE, 24)
	title.modulate = Color(1.0, 0.85, 0.25, 1.0)
	podium_vbox.add_child(title)

	var winner_label = Label.new()
	if winner_id > 0:
		winner_label.text = AppStrings.format_minigame_winner(winner_id)
	else:
		winner_label.text = AppStrings.MINIGAMES_STATUS_FINISHED
	winner_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	winner_label.add_theme_font_size_override(AppTechnicalStrings.THEME_FONT_SIZE, 20)
	winner_label.modulate = Color(0.96, 0.95, 0.92, 1.0)
	podium_vbox.add_child(winner_label)

	var sep = HSeparator.new()
	podium_vbox.add_child(sep)

	for idx in range(rankings.size()):
		var r = rankings[idx]
		var row = HBoxContainer.new()
		var rank_lbl = Label.new()
		rank_lbl.text = AppStrings.format_minigame_ranking_entry(idx + 1, r.get(&"entity_id", 0))
		rank_lbl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		row.add_child(rank_lbl)

		var reward_lbl = Label.new()
		reward_lbl.text = AppStrings.format_currency_pesos(r.get(&"coins_rewarded", 0))
		reward_lbl.modulate = Color(1.0, 0.85, 0.25, 1.0)
		row.add_child(reward_lbl)

		podium_vbox.add_child(row)

	podium_panel.visible = true

	var t = create_tween()
	t.tween_interval(6.0)
	t.tween_callback(func(): podium_panel.visible = false)

func _on_minigame_cancelled(_game_id: int, _reason: int) -> void:
	invite_panel.visible = false
	countdown_label.visible = false
	header_panel.visible = false
	podium_panel.visible = false

func _get_game_name(game_id: int) -> String:
	return MinigameCatalogClass.get_game_title(game_id)
