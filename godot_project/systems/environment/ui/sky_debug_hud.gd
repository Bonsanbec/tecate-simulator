class_name SkyDebugHUD
extends CanvasLayer

## Interfaz de Telemetría y Control Atmosférico para Tecate Simulator
##
## Desplegable mediante la tecla F3. Proporciona telemetría astronómica y meteorológica
## en tiempo real y permite controlar manualmente la hora del día, la velocidad temporal
## y los estados de clima para pruebas inmediatas.

signal realtime_toggled(is_realtime: bool)
signal hour_changed(hour_float: float)
signal timescale_changed(multiplier: float)
signal weather_forced(condition_name: String)

var panel: PanelContainer
var label_telemetry: Label
var check_realtime: CheckBox
var slider_hour: HSlider
var label_hour_val: Label
var speed_buttons: Array[Button] = []

var is_visible: bool = false
var _updating_ui_internally: bool = false

func _ready() -> void:
	layer = 100
	_build_ui()
	visible = is_visible

func _input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.is_echo():
		if event.keycode == KEY_F3:
			is_visible = !is_visible
			visible = is_visible
			if is_visible:
				# Mostrar ratón para interacción
				Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
			else:
				Input.mouse_mode = Input.MOUSE_MODE_CAPTURED

func _build_ui() -> void:
	panel = PanelContainer.new()
	panel.set_anchors_and_offsets_preset(Control.PRESET_TOP_LEFT, Control.PRESET_MODE_MINSIZE, 15)
	panel.custom_minimum_size = Vector2(400, 480)
	
	# Estilo translúcido moderno
	var style = StyleBoxFlat.new()
	style.bg_color = Color(0.08, 0.10, 0.14, 0.88)
	style.corner_radius_top_left = 8
	style.corner_radius_top_right = 8
	style.corner_radius_bottom_left = 8
	style.corner_radius_bottom_right = 8
	style.content_margin_left = 16
	style.content_margin_right = 16
	style.content_margin_top = 14
	style.content_margin_bottom = 14
	panel.add_theme_stylebox_override("panel", style)
	
	var vbox = VBoxContainer.new()
	vbox.add_theme_constant_override("separation", 10)
	panel.add_child(vbox)
	
	# Título
	var title = Label.new()
	title.text = "TECATE SIMULATOR — ATMÓSFERA Y CLIMA [F3]"
	title.add_theme_color_override("font_color", Color(0.95, 0.8, 0.35))
	title.add_theme_font_size_override("font_size", 14)
	vbox.add_child(title)
	
	# Telemetría
	label_telemetry = Label.new()
	label_telemetry.add_theme_font_size_override("font_size", 12)
	label_telemetry.text = "Cargando efemérides..."
	vbox.add_child(label_telemetry)
	
	vbox.add_child(HSeparator.new())
	
	# Control de Tiempo Real
	check_realtime = CheckBox.new()
	check_realtime.text = "Sincronización en Tiempo Real (Tecate, B.C.)"
	check_realtime.button_pressed = true
	check_realtime.toggled.connect(func(pressed):
		slider_hour.editable = !pressed
		realtime_toggled.emit(pressed)
	)
	vbox.add_child(check_realtime)
	
	# Control Deslizante de Hora Manual
	var hbox_hour = HBoxContainer.new()
	var lbl_h = Label.new()
	lbl_h.text = "Hora:"
	lbl_h.custom_minimum_size.x = 50
	hbox_hour.add_child(lbl_h)
	
	slider_hour = HSlider.new()
	slider_hour.min_value = 0.0
	slider_hour.max_value = 23.95
	slider_hour.step = 0.05
	slider_hour.value = 12.0
	slider_hour.editable = false
	slider_hour.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	slider_hour.value_changed.connect(func(val):
		if not _updating_ui_internally:
			label_hour_val.text = _format_hour(val)
			hour_changed.emit(val)
	)
	hbox_hour.add_child(slider_hour)
	
	label_hour_val = Label.new()
	label_hour_val.text = "12:00"
	label_hour_val.custom_minimum_size.x = 60
	label_hour_val.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	hbox_hour.add_child(label_hour_val)
	vbox.add_child(hbox_hour)
	
	# Multiplicador de Velocidad
	var hbox_speed = HBoxContainer.new()
	var lbl_sp = Label.new()
	lbl_sp.text = "Velocidad:"
	lbl_sp.custom_minimum_size.x = 75
	hbox_speed.add_child(lbl_sp)
	
	var speeds = [1.0, 10.0, 60.0, 300.0]
	for sp in speeds:
		var btn = Button.new()
		btn.text = str(int(sp)) + "x"
		btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		btn.pressed.connect(func(): timescale_changed.emit(sp))
		hbox_speed.add_child(btn)
	vbox.add_child(hbox_speed)
	
	vbox.add_child(HSeparator.new())
	
	# Botones de Clima
	var lbl_weather = Label.new()
	lbl_weather.text = "Forzar Estado de Clima:"
	lbl_weather.add_theme_color_override("font_color", Color(0.7, 0.85, 1.0))
	vbox.add_child(lbl_weather)
	
	var grid_weather = GridContainer.new()
	grid_weather.columns = 3
	grid_weather.add_theme_constant_override("h_separation", 6)
	grid_weather.add_theme_constant_override("v_separation", 6)
	
	var presets = [
		{"name": "Despejado", "cond": WeatherData.COND_CLEAR},
		{"name": "Cúmulos", "cond": WeatherData.COND_PARTLY_CLOUDY},
		{"name": "Nublado", "cond": WeatherData.COND_OVERCAST},
		{"name": "Lluvia", "cond": WeatherData.COND_RAIN},
		{"name": "Santa Ana", "cond": WeatherData.COND_WINDY},
		{"name": "Aleatorio", "cond": WeatherData.COND_CLEAR}
	]

	
	for p in presets:
		var btn = Button.new()
		btn.text = p["name"]
		btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		var c = p["cond"]
		btn.pressed.connect(func(): weather_forced.emit(c))
		grid_weather.add_child(btn)
	vbox.add_child(grid_weather)
	
	add_child(panel)

func update_telemetry(celestial: TecateCelestial.CelestialState, weather: WeatherData, is_realtime: bool, cur_hour: float) -> void:
	if not visible:
		return
		
	_updating_ui_internally = true
	check_realtime.button_pressed = is_realtime
	slider_hour.editable = !is_realtime
	if is_realtime:
		slider_hour.value = cur_hour
		label_hour_val.text = _format_hour(cur_hour)
	_updating_ui_internally = false
	
	var dt = celestial.local_datetime
	var date_str = "%04d-%02d-%02d %02d:%02d:%02d %s" % [
		dt.get("year", 2026), dt.get("month", 9), dt.get("day", 24),
		dt.get("hour", 12), dt.get("minute", 0), dt.get("second", 0),
		dt.get("tz_name", "PDT")
	]
	
	var sun_alt_deg = celestial.sun_altitude_rad * (180.0 / PI)
	var sun_az_deg = celestial.sun_azimuth_rad * (180.0 / PI)
	var moon_alt_deg = celestial.moon_altitude_rad * (180.0 / PI)
	var moon_az_deg = celestial.moon_azimuth_rad * (180.0 / PI)
	
	var lines = [
		"Hora Tecate: " + date_str,
		"Sol: Elev: %+.1f° | Azimut: %.1f° (%s)" % [sun_alt_deg, sun_az_deg, "Día" if sun_alt_deg > 0 else "Noche"],
		"Luna: Elev: %+.1f° | Az: %.1f° | Fase: %s (%d%%)" % [
			moon_alt_deg, moon_az_deg, celestial.moon_phase_name, int(celestial.moon_illuminated_fraction * 100)
		],
		"--------------------------------------------------",
		"Clima: %s" % weather.condition,
		"Nubosidad: %d%% | Densidad: %d%% | Lluvia: %d%%" % [
			int(weather.cloud_coverage * 100), int(weather.cloud_density * 100), int(weather.precipitation * 100)
		],
		"Niebla: %d%% | Viento: %.1f m/s (%.0f°)" % [
			int(weather.fog_density * 100), weather.wind_speed_mps, weather.wind_direction_deg
		],
		"Nubes 3D: Cuchumá (Y=900m) | Cúmulos (Y=2200m) | Cirros (Y=7000m)"
	]
	
	label_telemetry.text = "\n".join(lines)

func _format_hour(h: float) -> String:
	var hours = int(floor(h))
	var minutes = int(floor((h - float(hours)) * 60.0))
	return "%02d:%02d" % [hours, minutes]
