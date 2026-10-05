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

var _cached_camera_mode: String = "1P - Vista Subjetiva"
var _current_interaction_prompt: String = ""
var _badge_fade_timer: float = 3.0
var _current_theme_color: Color = Color(0.85, 0.16, 0.16, 1.0) # Rojo Tecate por defecto

var health_label: Label = null
var death_overlay: Control = null
var death_title: Label = null

func _ready():
	visible = false
	_setup_health_and_death_ui()
	_refresh_mode_badge()

func _setup_health_and_death_ui() -> void:
	var top_left = get_node_or_null("TopLeft")
	if top_left:
		var vbox = VBoxContainer.new()
		vbox.name = "TopLeftVBox"

		if network_label and network_label.get_parent() == top_left:
			top_left.remove_child(network_label)
			vbox.add_child(network_label)

		var health_container = HBoxContainer.new()
		health_container.name = "HealthContainer"

		var icon_lbl = Label.new()
		icon_lbl.text = "♥ "
		icon_lbl.modulate = Color(1.0, 0.25, 0.25, 1.0)
		health_container.add_child(icon_lbl)

		health_label = Label.new()
		health_label.name = "HealthLabel"
		health_label.text = "SALUD: 100 / 100 HP"
		health_label.add_theme_font_size_override("font_size", 13)
		health_container.add_child(health_label)

		vbox.add_child(health_container)
		top_left.add_child(vbox)

	death_overlay = get_node_or_null("DeathOverlay") as Control
	if death_overlay == null:
		death_overlay = ColorRect.new()
		death_overlay.name = "DeathOverlay"
		death_overlay.color = Color(0.12, 0.02, 0.02, 0.88)
		death_overlay.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		death_overlay.visible = false

		var center_box = VBoxContainer.new()
		center_box.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
		center_box.alignment = BoxContainer.ALIGNMENT_CENTER

		death_title = Label.new()
		death_title.text = "ELIMINADO"
		death_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		death_title.add_theme_font_size_override("font_size", 34)
		death_title.add_theme_color_override("font_color", Color(1.0, 0.2, 0.2, 1.0))
		center_box.add_child(death_title)

		var death_sub = Label.new()
		death_sub.text = "Reapareciendo en Parque Miguel Hidalgo..."
		death_sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		death_sub.add_theme_font_size_override("font_size", 16)
		death_sub.add_theme_color_override("font_color", Color(0.9, 0.9, 0.9, 0.9))
		center_box.add_child(death_sub)

		death_overlay.add_child(center_box)
		add_child(death_overlay)

func update_player_health(current: float, max_h: float) -> void:
	if health_label:
		health_label.text = "SALUD: %d / %d HP" % [int(ceil(current)), int(ceil(max_h))]
		var pct = current / max_h if max_h > 0.0 else 0.0
		if pct <= 0.25:
			health_label.modulate = Color(1.0, 0.3, 0.3, 1.0)
		elif pct <= 0.50:
			health_label.modulate = Color(1.0, 0.85, 0.2, 1.0)
		else:
			health_label.modulate = Color(0.4, 1.0, 0.6, 1.0)

func show_death_overlay(msg: String = "ELIMINADO") -> void:
	if death_title:
		death_title.text = msg
	if death_overlay:
		death_overlay.visible = true

func hide_death_overlay() -> void:
	if death_overlay:
		death_overlay.visible = false

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

	for panel_name in ["TopLeft", "TopCompass", "BottomLeft", "BottomRight"]:
		var panel = get_node_or_null(panel_name) as PanelContainer
		if panel:
			panel.add_theme_stylebox_override("panel", style_flat)

	if mode_badge:
		mode_badge.add_theme_color_override("font_color", theme_color)

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
	_cached_camera_mode = mode_name
	_badge_fade_timer = 2.5
	_refresh_mode_badge()

func _refresh_mode_badge() -> void:
	if not mode_badge:
		return
	if not _current_interaction_prompt.is_empty():
		mode_badge.text = "[F5] %s   |   %s" % [_cached_camera_mode, _current_interaction_prompt]
		mode_badge.modulate.a = 1.0
	else:
		mode_badge.text = "[F5] %s" % _cached_camera_mode
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
		return "Zona Centro • Tecate, Pueblo Mágico"
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
