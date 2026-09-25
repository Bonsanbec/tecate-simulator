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

var _badge_fade_timer: float = 3.0

func _ready():
	visible = false

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
