class_name PlayerHUD
extends CanvasLayer

## Interfaz de Usuario (HUD) Diegética e Inmersiva para Tecate Simulator
## Muestra brújula graduada superior con la calle más cercana hacia la que
## apunta la cámara, telemetría de velocidad en km/h, altimetría sobre el
## nivel del mar, gradiente topográfico de Tecate y modo de cámara (F5).
## La calle se obtiene del Autoload StreetNameLookup que consulta el índice
## espacial generado desde el caché OSM del municipio.

@onready var compass_label: Label = $TopCompass/CompassLabel
@onready var telemetry_label: Label = $BottomLeft/TelemetryLabel
@onready var mode_badge: Label = $BottomRight/ModeBadge
@onready var reticle: Control = $CenterReticle
@onready var axes_gizmo: CompassAxesGizmo = $AxesGizmo
@onready var network_label: Label = get_node_or_null("TopLeft/NetworkLabel") as Label

const CharacterCatalogClass = preload("res://systems/characters/character_catalog.gd")

var _cached_camera_mode: String = AppStrings.CAMERA_MODE_1P
var _current_interaction_prompt: String = ""
var _badge_fade_timer: float = 3.0
var _current_theme_color: Color = Color(0.85, 0.16, 0.16, 1.0) # Rojo Tecate por defecto

var wallet_label: Label = null

func _ready():
	visible = false
	_setup_civic_hud_ui()
	_refresh_mode_badge()

func _setup_civic_hud_ui() -> void:
	var top_left = get_node_or_null(^"TopLeft")
	if top_left:
		var vbox = VBoxContainer.new()
		vbox.name = &"TopLeftVBox"

		if network_label and network_label.get_parent() == top_left:
			top_left.remove_child(network_label)
			vbox.add_child(network_label)

		var wallet_container = HBoxContainer.new()
		wallet_container.name = &"WalletContainer"

		wallet_label = Label.new()
		wallet_label.name = &"WalletLabel"
		wallet_label.text = AppStrings.format_currency_pesos(50)
		wallet_label.add_theme_font_size_override(AppTechnicalStrings.THEME_FONT_SIZE, 13)
		wallet_label.modulate = Color(1.0, 0.95, 0.70, 1.0)
		wallet_container.add_child(wallet_label)

		vbox.add_child(wallet_container)
		top_left.add_child(vbox)

func update_player_balance(balance_pesos: int) -> void:
	if wallet_label:
		wallet_label.text = AppStrings.format_currency_pesos(balance_pesos)

## Aplica dinámicamente el esquema de color firma del personaje elegido al HUD completo
func apply_character_theme(character_id: String) -> void:
	var color = CharacterCatalogClass.get_character_theme_color(character_id)
	apply_theme_color(color)

func apply_theme_color(theme_color: Color) -> void:
	_current_theme_color = theme_color
	_update_hud_theme_styles(_current_theme_color)

func _update_hud_theme_styles(theme_color: Color) -> void:
	var style_flat = StyleBoxFlat.new()
	style_flat.bg_color = Color(0.08, 0.10, 0.13, 0.85)
	style_flat.border_width_left = 2
	style_flat.border_width_top = 2
	style_flat.border_width_right = 2
	style_flat.border_width_bottom = 2
	style_flat.border_color = Color(theme_color.r, theme_color.g, theme_color.b, 0.85)
	style_flat.corner_radius_top_left = 6
	style_flat.corner_radius_top_right = 6
	style_flat.corner_radius_bottom_right = 6
	style_flat.corner_radius_bottom_left = 6
	style_flat.content_margin_left = 14.0
	style_flat.content_margin_top = 8.0
	style_flat.content_margin_right = 14.0
	style_flat.content_margin_bottom = 8.0

	for panel_name in [^"TopLeft", ^"TopCompass", ^"BottomLeft", ^"BottomRight"]:
		var panel = get_node_or_null(panel_name) as PanelContainer
		if panel:
			panel.add_theme_stylebox_override(AppTechnicalStrings.THEME_STYLE_PANEL, style_flat)

	if mode_badge:
		mode_badge.add_theme_color_override(AppTechnicalStrings.THEME_FONT_COLOR, theme_color)

func set_interaction_prompt(prompt_text: String) -> void:
	_current_interaction_prompt = prompt_text
	_refresh_mode_badge()

func update_network_status(status_text: String, is_connected: bool = false) -> void:
	if network_label:
		network_label.text = status_text
		if is_connected:
			network_label.modulate = Color(0.0, 0.75, 0.35, 1.0) # Verde Pueblo Mágico
		else:
			network_label.modulate = Color(0.85, 0.82, 0.78, 0.85)

func show_hud() -> void:
	visible = true

func hide_hud() -> void:
	visible = false
	# Resetear el apuntador explícitamente para evitar que su estado interno
	# quede activo mientras el CanvasLayer está oculto
	if reticle:
		reticle.visible = false

func update_hud(
	heading_degrees: float,
	speed_kmh: float,
	altitude_meters: float,
	slope_degrees: float,
	camera_mode_name: String,
	is_1p: bool,
	nearest_street: String = ""
) -> void:
	# 1. Actualizar Brújula Superior con calle más cercana
	if compass_label:
		var deg_norm = fposmod(heading_degrees, 360.0)
		var cardinal = _get_cardinal_direction(deg_norm)
		var street_hint = _format_street_hint(nearest_street)
		compass_label.text = AppStrings.format_compass_street(int(deg_norm), cardinal, street_hint)

	# 2. Actualizar Telemetría Urbana
	if telemetry_label:
		telemetry_label.text = AppStrings.format_pedestrian_telemetry(speed_kmh, altitude_meters, slope_degrees)

	# 3. Retícula dinámica: Visible en 1P, discreta
	if reticle:
		reticle.visible = is_1p

## Actualiza la telemetría específica al estar a bordo de un vehículo
func update_vehicle_hud(
	vehicle_name: String,
	speed_kmh: float,
	fuel_pct: float,
	is_infinite_fuel: bool,
	surface_name: String,
	slope_deg: float,
	is_driver: bool,
	heading_degrees: float,
	nearest_street: String = ""
) -> void:
	if compass_label:
		var deg_norm = fposmod(heading_degrees, 360.0)
		var cardinal = _get_cardinal_direction(deg_norm)
		var street_hint = _format_street_hint(nearest_street)
		compass_label.text = AppStrings.format_compass_street(int(deg_norm), cardinal, street_hint)

	if telemetry_label:
		var role_str = AppStrings.VEHICLE_ROLE_DRIVER if is_driver else AppStrings.VEHICLE_ROLE_PASSENGER
		telemetry_label.text = AppStrings.format_vehicle_telemetry(
			vehicle_name,
			role_str,
			speed_kmh,
			fuel_pct,
			is_infinite_fuel,
			surface_name,
			slope_deg
		)

	if reticle:
		reticle.visible = false

func update_axes(camera_basis: Basis) -> void:
	if axes_gizmo:
		axes_gizmo.set_camera_basis(camera_basis)

func set_perspective_badge(mode_name: String) -> void:
	_cached_camera_mode = mode_name
	_badge_fade_timer = 2.5
	_refresh_mode_badge()

func _refresh_mode_badge() -> void:
	if not mode_badge:
		return
	mode_badge.text = AppStrings.format_hud_mode_badge(_cached_camera_mode, _current_interaction_prompt)
	if not _current_interaction_prompt.is_empty():
		mode_badge.modulate.a = 1.0
	else:
		if _badge_fade_timer <= 0.0:
			mode_badge.modulate.a = 0.35
		else:
			mode_badge.modulate.a = 1.0

func _process(delta: float) -> void:
	if not mode_badge:
		return
	if not _current_interaction_prompt.is_empty():
		mode_badge.modulate.a = 1.0
	elif _badge_fade_timer > 0.0:
		_badge_fade_timer -= delta
		if _badge_fade_timer <= 1.0:
			mode_badge.modulate.a = clampf(_badge_fade_timer * 0.65 + 0.35, 0.35, 1.0)

func _get_cardinal_direction(deg: float) -> String:
	return AppStrings.get_cardinal_direction(deg)

func _format_street_hint(street_name: String) -> String:
	if street_name.is_empty():
		return AppStrings.HINT_CENTRO_DEFAULT
	return street_name

func _get_landmark_hint(deg: float) -> String:
	var norm = fposmod(deg, 360.0)
	if norm >= 45.0 and norm < 135.0:
		return AppStrings.LANDMARK_RUMOROSA
	elif norm >= 225.0 and norm < 315.0:
		return AppStrings.LANDMARK_CUCHUMA
	elif norm >= 135.0 and norm < 225.0:
		return AppStrings.LANDMARK_ENSENADA
	else:
		return AppStrings.LANDMARK_FRONTERA
