class_name RandomWeatherProvider
extends WeatherProvider

## Proveedor Climático Procedural y Estocástico para Tecate Simulator
##
## Modela el comportamiento meteorológico típico del semidesierto y valles de Tecate:
## - Cielos despejados predominantes y vientos suaves del Pacífico.
## - Episodios periódicos de bancos de niebla matutina del Cuchumá (baja troposfera).
## - Vientos de Santa Ana (cálidos, secos y veloces desde el oriente/Rumorosa).
## - Chubascos y lluvias estacionales con densificación gradual de nubes.
##
## Garantiza transiciones suaves de tiempo continuo (lerp) sin cambios bruscos de iluminación.

@export var auto_cycle_weather: bool = true
@export var change_interval_sec: float = 240.0 # Cada 4 minutos cambia de tendencia climática
@export var transition_duration_sec: float = 30.0 # 30 segundos de transición fluida

var _current_weather: WeatherData
var _source_weather: WeatherData
var _target_weather: WeatherData

var _cycle_timer: float = 0.0
var _transition_timer: float = 0.0
var _is_transitioning: bool = false
var _rng: RandomNumberGenerator

func _init() -> void:
	_rng = RandomNumberGenerator.new()
	_rng.randomize()
	_current_weather = _create_preset(WeatherData.COND_CLEAR)
	_source_weather = _current_weather.duplicate()
	_target_weather = _current_weather.duplicate()

func get_current_weather() -> WeatherData:
	return _current_weather

func update(delta: float) -> void:
	if _is_transitioning:
		_transition_timer += delta
		var weight = clamp(_transition_timer / max(transition_duration_sec, 0.01), 0.0, 1.0)
		_current_weather = _source_weather.lerp_with(_target_weather, weight)
		weather_updated.emit(_current_weather)
		
		if weight >= 1.0:
			_is_transitioning = false
			_transition_timer = 0.0
			_source_weather = _target_weather.duplicate()
	elif auto_cycle_weather:
		_cycle_timer += delta
		if _cycle_timer >= change_interval_sec:
			_cycle_timer = 0.0
			_pick_next_random_weather()

func refresh() -> void:
	_pick_next_random_weather()

func force_condition(condition_name: String) -> void:
	var target = _create_preset(condition_name)
	start_transition(target, 2.5) # Transición rápida de 2.5 segundos para pruebas interactivas

func start_transition(new_target: WeatherData, duration_sec: float = -1.0) -> void:
	_source_weather = _current_weather.duplicate()
	_target_weather = new_target.duplicate()
	transition_duration_sec = duration_sec if duration_sec > 0.0 else transition_duration_sec
	_transition_timer = 0.0
	_is_transitioning = true
	transition_started.emit(_source_weather, _target_weather, transition_duration_sec)

func _pick_next_random_weather() -> void:
	# Distribución estocástica fiel al microclima de Tecate:
	# Clima semidesértico / mediterráneo interior con cielos mayormente despejados y sin niebla
	var roll = _rng.randf()
	var selected_condition: String
	
	if roll < 0.80:
		selected_condition = WeatherData.COND_CLEAR
	elif roll < 0.97:
		selected_condition = WeatherData.COND_PARTLY_CLOUDY
	else:
		selected_condition = WeatherData.COND_RAIN
		
	var next_preset = _create_preset(selected_condition)
	
	# Introducir ligera varianza orgánica a los valores
	next_preset.wind_speed_mps += _rng.randf_range(-1.0, 1.0)
	next_preset.wind_direction_deg = fposmod(next_preset.wind_direction_deg + _rng.randf_range(-20.0, 20.0), 360.0)
	next_preset.temperature_c += _rng.randf_range(-1.0, 1.0)
	
	start_transition(next_preset, transition_duration_sec)

func _create_preset(condition_type: String) -> WeatherData:
	var data = WeatherData.new()
	data.condition = condition_type
	data.timestamp = int(Time.get_unix_time_from_system())
	
	match condition_type:
		WeatherData.COND_CLEAR:
			data.cloud_coverage = 0.03
			data.cloud_density = 0.50
			data.precipitation = 0.0
			data.fog_density = 0.0
			data.wind_speed_mps = 3.5
			data.wind_direction_deg = 270.0 # Brisa habitual del poniente
			data.temperature_c = 24.5
			data.humidity_pct = 28.0
			data.pressure_hpa = 1015.0
			
		WeatherData.COND_PARTLY_CLOUDY:
			# Nubes cúmulos bien definidas y aisladas sobre el valle
			data.cloud_coverage = 0.22
			data.cloud_density = 0.95
			data.precipitation = 0.0
			data.fog_density = 0.0
			data.wind_speed_mps = 4.5
			data.wind_direction_deg = 265.0
			data.temperature_c = 22.0
			data.humidity_pct = 40.0
			data.pressure_hpa = 1013.0
			
		WeatherData.COND_OVERCAST:
			data.cloud_coverage = 0.65
			data.cloud_density = 0.95
			data.precipitation = 0.0
			data.fog_density = 0.01
			data.wind_speed_mps = 7.0
			data.wind_direction_deg = 240.0
			data.temperature_c = 17.5
			data.humidity_pct = 60.0
			data.pressure_hpa = 1010.0
			
		WeatherData.COND_RAIN:
			data.cloud_coverage = 0.85
			data.cloud_density = 1.0
			data.precipitation = 0.60
			data.fog_density = 0.03
			data.wind_speed_mps = 9.5
			data.wind_direction_deg = 225.0
			data.temperature_c = 14.0
			data.humidity_pct = 85.0
			data.pressure_hpa = 1004.0
			
		WeatherData.COND_FOG:
			# Preset residual (en Tecate prácticamente no hay niebla)
			data.cloud_coverage = 0.40
			data.cloud_density = 0.85
			data.precipitation = 0.0
			data.fog_density = 0.05
			data.wind_speed_mps = 2.0
			data.wind_direction_deg = 280.0
			data.temperature_c = 16.0
			data.humidity_pct = 70.0
			data.pressure_hpa = 1014.0

			
		WeatherData.COND_WINDY:
			# Vientos de Santa Ana (oriente / La Rumorosa)
			data.cloud_coverage = 0.12
			data.cloud_density = 0.50
			data.precipitation = 0.0
			data.fog_density = 0.0
			data.wind_speed_mps = 19.0
			data.wind_direction_deg = 65.0 # Noreste
			data.temperature_c = 29.5
			data.humidity_pct = 12.0
			data.pressure_hpa = 1018.0
			
	return data
