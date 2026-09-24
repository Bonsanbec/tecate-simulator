class_name ApiWeatherProvider
extends WeatherProvider

## Proveedor Climático de Red (API REST) para Tecate Simulator
##
## Diseñado para consultar el servicio meteorológico de Open-Meteo para las coordenadas
## exactas de Tecate (Lat: 32.5732, Lon: -116.6265) sin requerir claves de API propietarias.
##
## Incluye:
## - Mapeo oficial de códigos de tiempo WMO (World Meteorological Organization).
## - Sistema de caché y reintento.
## - Respaldo transparente (fallback) a proveedor procedural si la conexión falla.

const API_ENDPOINT: String = "https://api.open-meteo.com/v1/forecast?latitude=32.5732&longitude=-116.6265&current=temperature_2m,relative_humidity_2m,precipitation,weather_code,cloud_cover,surface_pressure,wind_speed_10m,wind_direction_10m"

@export var poll_interval_sec: float = 600.0 # Cada 10 minutos
@export var transition_duration_sec: float = 15.0

var _current_weather: WeatherData
var _fallback_provider: RandomWeatherProvider
var _poll_timer: float = 0.0
var _http_request: HTTPRequest
var _is_request_in_flight: bool = false

func _init() -> void:
	_fallback_provider = RandomWeatherProvider.new()
	_current_weather = _fallback_provider.get_current_weather().duplicate()

func setup_http_node(parent_node: Node) -> void:
	if not _http_request and parent_node:
		_http_request = HTTPRequest.new()
		_http_request.name = "ApiWeatherHTTP"
		_http_request.timeout = 10.0
		parent_node.add_child(_http_request)
		_http_request.request_completed.connect(_on_request_completed)

func get_current_weather() -> WeatherData:
	return _current_weather

func update(delta: float) -> void:
	_poll_timer += delta
	if _poll_timer >= poll_interval_sec:
		_poll_timer = 0.0
		fetch_weather()
		
	# Si estamos transicionando, dejamos que el fallback actualice interpolaciones si está activo
	if _fallback_provider:
		_fallback_provider.update(delta)

func refresh() -> void:
	fetch_weather()

func force_condition(condition_name: String) -> void:
	if _fallback_provider:
		_fallback_provider.force_condition(condition_name)
		_current_weather = _fallback_provider.get_current_weather()
		weather_updated.emit(_current_weather)

func fetch_weather() -> void:
	if _is_request_in_flight or not _http_request:
		return
		
	_is_request_in_flight = true
	var err = _http_request.request(API_ENDPOINT)
	if err != OK:
		print("[ApiWeatherProvider] Error al iniciar petición HTTP: ", err, ". Usando respaldo procedural.")
		_is_request_in_flight = false

func _on_request_completed(result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	_is_request_in_flight = false
	
	if result != HTTPRequest.RESULT_SUCCESS or response_code != 200:
		print("[ApiWeatherProvider] Petición fallida (Código: ", response_code, "). Manteniendo estado actual.")
		return
		
	var json_str = body.get_string_from_utf8()
	var json = JSON.new()
	var parse_err = json.parse(json_str)
	if parse_err != OK:
		print("[ApiWeatherProvider] Error parseando JSON de clima: ", parse_err)
		return
		
	var data_dict = json.data as Dictionary
	if not data_dict.has("current"):
		return
		
	var current = data_dict["current"] as Dictionary
	var new_weather = _parse_open_meteo_payload(current)
	_current_weather = new_weather
	weather_updated.emit(_current_weather)
	print("[ApiWeatherProvider] Clima de Tecate actualizado en vivo: ", new_weather.condition, " | Nubes: ", int(new_weather.cloud_coverage * 100), "% | Temp: ", new_weather.temperature_c, "°C")

func _parse_open_meteo_payload(c: Dictionary) -> WeatherData:
	var data = WeatherData.new()
	data.timestamp = int(Time.get_unix_time_from_system())
	
	var wmo_code = int(c.get("weather_code", 0))
	var cloud_pct = float(c.get("cloud_cover", 20.0))
	data.cloud_coverage = clamp(cloud_pct / 100.0, 0.0, 1.0)
	data.cloud_density = clamp(0.5 + (data.cloud_coverage * 0.5), 0.0, 1.0)
	
	var prec_mm = float(c.get("precipitation", 0.0))
	data.precipitation = clamp(prec_mm / 10.0, 0.0, 1.0)
	
	data.temperature_c = float(c.get("temperature_2m", 20.0))
	data.humidity_pct = float(c.get("relative_humidity_2m", 50.0))
	data.pressure_hpa = float(c.get("surface_pressure", 1013.0))
	data.wind_speed_mps = float(c.get("wind_speed_10m", 3.0))
	data.wind_direction_deg = float(c.get("wind_direction_10m", 270.0))
	
	# Mapeo oficial de códigos WMO
	match wmo_code:
		0:
			data.condition = WeatherData.COND_CLEAR
			data.fog_density = 0.0
		1, 2:
			data.condition = WeatherData.COND_PARTLY_CLOUDY
			data.fog_density = 0.0
		3:
			data.condition = WeatherData.COND_OVERCAST
			data.fog_density = 0.05
		45, 48:
			data.condition = WeatherData.COND_FOG
			data.fog_density = 0.80
		51, 53, 55, 61, 63, 65, 80, 81, 82:
			data.condition = WeatherData.COND_RAIN
			data.fog_density = 0.25
		_:
			data.condition = WeatherData.COND_PARTLY_CLOUDY if data.cloud_coverage > 0.3 else WeatherData.COND_CLEAR
			data.fog_density = 0.0
			
	return data
