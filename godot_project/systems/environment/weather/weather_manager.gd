class_name WeatherManager
extends Node

## Administrador y Coordinador del Subsistema de Clima en Tecate Simulator
##
## Conecta el proveedor seleccionado (procedural o API) con el resto del simulador,
## emitiendo señales fuertemente tipadas hacia las capas de nubes 3D, el controlador
## de iluminación y las partículas de precipitación.

signal weather_changed(data: WeatherData)

@export var use_live_api: bool = false:
	set(val):
		use_live_api = val
		_setup_provider()

var _active_provider: WeatherProvider
var _current_weather: WeatherData

func _ready() -> void:
	_setup_provider()

func _setup_provider() -> void:
	if _active_provider:
		if _active_provider.weather_updated.is_connected(_on_weather_updated):
			_active_provider.weather_updated.disconnect(_on_weather_updated)
			
	if use_live_api:
		var api = ApiWeatherProvider.new()
		api.setup_http_node(self)
		_active_provider = api
		print("[WeatherManager] Proveedor activado: API Meteorológica en Vivo")
	else:
		_active_provider = RandomWeatherProvider.new()
		print("[WeatherManager] Proveedor activado: Generador Procedural Aleatorio")
		
	_active_provider.weather_updated.connect(_on_weather_updated)
	_current_weather = _active_provider.get_current_weather()
	if _current_weather:
		weather_changed.emit(_current_weather)

func _process(delta: float) -> void:
	if _active_provider:
		_active_provider.update(delta)

func get_current_weather() -> WeatherData:
	if _current_weather:
		return _current_weather
	if _active_provider:
		return _active_provider.get_current_weather()
	return WeatherData.new()

func force_weather_condition(condition_name: String) -> void:
	if _active_provider:
		_active_provider.force_condition(condition_name)

func refresh() -> void:
	if _active_provider:
		_active_provider.refresh()

func _on_weather_updated(data: WeatherData) -> void:
	_current_weather = data
	weather_changed.emit(_current_weather)
