class_name WeatherProvider
extends RefCounted

## Contrato de Interfaz Abstracta para Proveedores de Clima en Tecate Simulator
##
## Todo proveedor de clima (generador aleatorio procedural, simulador histórico,
## o cliente de API REST remota como Open-Meteo) DEBE heredar de esta clase
## e implementar estos métodos para garantizar desacoplamiento total del renderizador.

signal weather_updated(data: WeatherData)
signal transition_started(from_state: WeatherData, to_state: WeatherData, duration_sec: float)

## Retorna el estado meteorológico actual activo
func get_current_weather() -> WeatherData:
	return null

## Actualiza el ciclo de vida del proveedor en cada cuadro de simulación
func update(_delta: float) -> void:
	pass

## Fuerza una actualización inmediata de datos (ej: reintento de consulta HTTP o cambio de fase)
func refresh() -> void:
	pass

## Fuerza un estado climático específico (útil para pruebas o depuración en el HUD)
func force_condition(_condition_name: String) -> void:
	pass
