class_name SkySystem
extends Node3D

## Sistema Integral de Atmósfera, Cielo Fotorrealista y Clima de Tecate Simulator
##
## Orquesta:
## - El motor astronómico analítico de Tecate y huso horario de Tijuana (America/Tijuana).
## - El controlador de iluminación PBR (Sol, Luna y WorldEnvironment).
## - El gestor de nubes tridimensionales desacopladas (Cuchumá a Y=900m, Cúmulos a Y=2200m y Cirros a Y=7000m).
## - El subsistema desacoplado de clima por contrato (WeatherData / WeatherProvider).
## - Las partículas físicas de precipitación pluvial.
## - La interfaz de telemetría y control [F3].

@export_group("Tiempo y Cronología")
@export var realtime_sync: bool = true
@export var time_scale: float = 1.0
@export var manual_hour: float = 12.0 # [0.0 - 24.0]

@export_group("Clima")
@export var use_live_api: bool = false:
	set(val):
		use_live_api = val
		if weather_manager:
			weather_manager.use_live_api = val

var celestial_state: TecateCelestial.CelestialState
var current_weather: WeatherData

var lighting_controller: LightingController
var cloud_manager: CloudManager
var weather_manager: WeatherManager
var rain_particles: RainParticles
var debug_hud: SkyDebugHUD

var _simulated_unix: float = 0.0

func _ready() -> void:
	_init_subsystems()
	_connect_hud_signals()
	
	# Inicializar timestamp de simulación con el tiempo real de Tecate
	_simulated_unix = Time.get_unix_time_from_system()
	if not realtime_sync:
		_apply_manual_hour_to_simulated_time()

func _init_subsystems() -> void:
	# 1. Controlador de Iluminación y WorldEnvironment
	lighting_controller = LightingController.new()
	lighting_controller.name = "LightingController"
	add_child(lighting_controller)
	
	# 2. Orquestador de Nubes Físicas 3D
	cloud_manager = CloudManager.new()
	cloud_manager.name = "CloudManager"
	add_child(cloud_manager)
	
	# 3. Gestor de Clima Desacoplado
	weather_manager = WeatherManager.new()
	weather_manager.name = "WeatherManager"
	weather_manager.use_live_api = use_live_api
	add_child(weather_manager)
	
	# 4. Partículas de Lluvia
	rain_particles = RainParticles.new()
	rain_particles.name = "RainParticles"
	add_child(rain_particles)
	
	# 5. HUD de Telemetría y Pruebas
	debug_hud = SkyDebugHUD.new()
	debug_hud.name = "SkyDebugHUD"
	add_child(debug_hud)

func _connect_hud_signals() -> void:
	debug_hud.realtime_toggled.connect(func(is_rt):
		realtime_sync = is_rt
		if not is_rt:
			_apply_manual_hour_to_simulated_time()
	)
	
	debug_hud.hour_changed.connect(func(h):
		manual_hour = h
		realtime_sync = false
		_apply_manual_hour_to_simulated_time()
	)
	
	debug_hud.timescale_changed.connect(func(scale):
		time_scale = scale
	)
	
	debug_hud.weather_forced.connect(func(cond):
		if weather_manager:
			weather_manager.force_weather_condition(cond)
	)

func _process(delta: float) -> void:
	# 1. Actualizar tiempo
	var unix_to_evaluate: int
	var current_decimal_hour: float
	
	if realtime_sync:
		_simulated_unix = Time.get_unix_time_from_system()
		unix_to_evaluate = int(_simulated_unix)
		var local_dt = TecateCelestial.get_tecate_local_datetime(unix_to_evaluate)
		current_decimal_hour = float(local_dt.hour) + float(local_dt.minute) / 60.0 + float(local_dt.second) / 3600.0
		manual_hour = current_decimal_hour
	else:
		_simulated_unix += delta * time_scale
		unix_to_evaluate = int(_simulated_unix)
		var local_dt = TecateCelestial.get_tecate_local_datetime(unix_to_evaluate)
		current_decimal_hour = float(local_dt.hour) + float(local_dt.minute) / 60.0 + float(local_dt.second) / 3600.0
		manual_hour = current_decimal_hour
		
	# 2. Calcular efemérides astronómicas de Tecate
	celestial_state = TecateCelestial.calculate_celestial_state(unix_to_evaluate)
	
	# 3. Obtener estado de clima actual
	current_weather = weather_manager.get_current_weather()
	
	# 4. Actualizar iluminación del mapa (Sol, Luna, Ambiente, Niebla)
	lighting_controller.update_celestial_lighting(celestial_state, current_weather)
	
	# 5. Actualizar capas físicas de nubes 3D
	cloud_manager.update_from_weather(current_weather)
	var sun_dir = celestial_state.sun_direction
	var sun_col = lighting_controller.get_sun_color()
	var moon_dir = celestial_state.moon_direction
	var moon_col = lighting_controller.get_moon_color()
	var ambient_col = Color(0.2, 0.25, 0.35)
	cloud_manager.update_lighting(sun_dir, sun_col, moon_dir, moon_col, ambient_col)
	
	# 6. Actualizar precipitación
	rain_particles.update_weather(current_weather)
	
	# 7. Actualizar telemetría visual
	debug_hud.update_telemetry(celestial_state, current_weather, realtime_sync, current_decimal_hour)

func _apply_manual_hour_to_simulated_time() -> void:
	var base_unix = int(Time.get_unix_time_from_system())
	var local_dt = TecateCelestial.get_tecate_local_datetime(base_unix)
	var offset_hours = local_dt.get("tz_offset", -7)
	
	# Fijar la hora manual requerida en el día actual (rango válido 0..23)
	var safe_h = clamp(manual_hour, 0.0, 23.999)
	var target_hours = int(floor(safe_h))
	var target_minutes = int(floor((safe_h - float(target_hours)) * 60.0))
	var target_seconds = int(floor(((safe_h - float(target_hours)) * 60.0 - float(target_minutes)) * 60.0))
	
	var synth_local_dt = {
		"year": local_dt.year,
		"month": local_dt.month,
		"day": local_dt.day,
		"hour": target_hours,
		"minute": target_minutes,
		"second": target_seconds
	}
	var local_unix = Time.get_unix_time_from_datetime_dict(synth_local_dt)
	_simulated_unix = float(local_unix - (offset_hours * 3600))

