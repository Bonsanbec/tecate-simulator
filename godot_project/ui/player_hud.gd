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

var prompt_label: Label = null
var _badge_fade_timer: float = 3.0

func _ready():
	visible = false
	_create_interaction_prompt_ui()

func _create_interaction_prompt_ui() -> void:
	var prompt_panel = PanelContainer.new()
	prompt_panel.name = "InteractionPromptPanel"
	prompt_panel.anchors_preset = Control.PRESET_CENTER_BOTTOM
	prompt_panel.anchor_left = 0.5
	prompt_panel.anchor_top = 1.0
	prompt_panel.anchor_right = 0.5
	prompt_panel.anchor_bottom = 1.0
	prompt_panel.offset_left = -160.0
	prompt_panel.offset_top = -120.0
	prompt_panel.offset_right = 160.0
	prompt_panel.offset_bottom = -80.0
	prompt_panel.grow_horizontal = Control.GROW_DIRECTION_BOTH
	prompt_panel.grow_vertical = Control.GROW_DIRECTION_BEGIN

	var style = StyleBoxFlat.new()
	style.bg_color = Color(0.08, 0.10, 0.14, 0.85)
	style.set_corner_radius_all(6)
	style.content_margin_left = 12
	style.content_margin_right = 12
	style.content_margin_top = 6
	style.content_margin_bottom = 6
	prompt_panel.add_theme_stylebox_override("panel", style)

	prompt_label = Label.new()
	prompt_label.name = "PromptLabel"
	prompt_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	prompt_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	prompt_label.add_theme_color_override("font_color", Color(1.0, 0.90, 0.35, 1.0))
	prompt_label.add_theme_font_size_override("font_size", 14)
	prompt_panel.add_child(prompt_label)

	add_child(prompt_panel)
	prompt_panel.visible = false

func set_interaction_prompt(prompt_text: String) -> void:
	if not prompt_label:
		return
	var panel = prompt_label.get_parent() as Control
	if prompt_text.is_empty():
		if panel: panel.visible = false
	else:
		prompt_label.text = prompt_text
		if panel: panel.visible = true

func update_network_status(status_text: String, is_connected: bool = false) -> void:
	if network_label:
		network_label.text = status_text
		if is_connected:
			network_label.modulate = Color(0.55, 0.95, 0.65, 1.0)
		else:
			network_label.modulate = Color(0.85, 0.88, 0.92, 0.75)

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
		compass_label.text = "%03d° %s  |  %s" % [int(deg_norm), cardinal, street_hint]

	# 2. Actualizar Telemetría Urbana
	if telemetry_label:
		var slope_sign = "+" if slope_degrees > 0.5 else ("-" if slope_degrees < -0.5 else "")
		telemetry_label.text = "VELOCIDAD: %4.1f km/h\nALTITUD:   %5.1f m snm\nPENDIENTE: %s%3.1f°" % [
			speed_kmh,
			altitude_meters,
			slope_sign,
			abs(slope_degrees)
		]

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
		compass_label.text = "%03d° %s  |  %s" % [int(deg_norm), cardinal, street_hint]

	if telemetry_label:
		var fuel_str = "∞ (Ruta)" if is_infinite_fuel else ("%3.0f%%" % fuel_pct)
		var role_str = "CONDUCTOR" if is_driver else "PASAJERO"
		var slope_sign = "+" if slope_deg > 0.5 else ("-" if slope_deg < -0.5 else "")
		telemetry_label.text = "[%s - %s]\nVELOCIDAD: %4.1f km/h\nCOMBUSTIBLE: %s\nSUPERFICIE: %s\nPENDIENTE: %s%3.1f°" % [
			vehicle_name,
			role_str,
			speed_kmh,
			fuel_str,
			surface_name,
			slope_sign,
			abs(slope_deg)
		]

	if reticle:
		reticle.visible = false

func update_axes(camera_basis: Basis) -> void:
	if axes_gizmo:
		axes_gizmo.set_camera_basis(camera_basis)

func set_perspective_badge(mode_name: String) -> void:
	if mode_badge:
		mode_badge.text = "[F5] %s" % mode_name
		mode_badge.modulate.a = 1.0
		_badge_fade_timer = 2.5

func _process(delta: float) -> void:
	if mode_badge and _badge_fade_timer > 0.0:
		_badge_fade_timer -= delta
		if _badge_fade_timer <= 1.0:
			mode_badge.modulate.a = clampf(_badge_fade_timer, 0.25, 1.0)

func _get_cardinal_direction(deg: float) -> String:
	if deg >= 337.5 or deg < 22.5: return "N"
	elif deg < 67.5: return "NE"
	elif deg < 112.5: return "E"
	elif deg < 157.5: return "SE"
	elif deg < 202.5: return "S"
	elif deg < 247.5: return "SW"
	elif deg < 292.5: return "W"
	else: return "NW"

func _format_street_hint(street_name: String) -> String:
	if street_name.is_empty():
		return "Zona Urbana Tecate"
	return street_name

func _get_landmark_hint(deg: float) -> String:
	var norm = fposmod(deg, 360.0)
	if norm >= 45.0 and norm < 135.0:
		return "Hacia La Rumorosa / Mexicali"
	elif norm >= 225.0 and norm < 315.0:
		return "Hacia el Cerro Cuchumá / Tijuana"
	elif norm >= 135.0 and norm < 225.0:
		return "Hacia Ensenada / Valle de Guadalupe"
	else:
		return "Hacia la Frontera / USA"
