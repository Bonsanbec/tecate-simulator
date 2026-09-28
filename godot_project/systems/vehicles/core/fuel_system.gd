class_name FuelSystem
extends Node

## Subsistema Integral de Combustible para Vehículos en Tecate Simulator
## Gestiona la capacidad volumétrica, consumo dinámico según esfuerzo del motor,
## pendiente topográfica y tipo de superficie, y repostaje en estaciones de servicio.

signal fuel_changed(current_liters: float, capacity_liters: float, percentage: float)
signal out_of_fuel()
signal refueled(amount_liters: float)

@export var capacity_liters: float = 50.0
@export var current_liters: float = 50.0
@export var is_infinite_fuel: bool = false

## Tasa de consumo en ralentí con motor encendido (litros por segundo)
@export var idle_consumption_rate: float = 0.0003 # ~1.0 L/hora

## Tasa de consumo a aceleración máxima en plano (litros por segundo)
@export var load_consumption_rate: float = 0.0035 # ~12.6 L/100km a velocidad crucero

var is_empty: bool:
	get:
		return not is_infinite_fuel and current_liters <= 0.0

func _ready() -> void:
	current_liters = clampf(current_liters, 0.0, capacity_liters)
	_notify_fuel_changed()

## Descuenta combustible proporcional a la demanda de potencia
## Retorna true si hay combustible disponible para continuar la marcha
func consume(throttle: float, slope_penalty: float, surface_penalty: float, delta: float) -> bool:
	if is_infinite_fuel:
		return true

	if is_empty:
		return false

	var abs_throttle = clampf(abs(throttle), 0.0, 1.0)
	var active_slope_k = maxf(1.0, slope_penalty)
	var active_surf_k = maxf(1.0, surface_penalty)

	var consumption = (idle_consumption_rate + (load_consumption_rate * abs_throttle * active_slope_k * active_surf_k)) * delta
	current_liters = maxf(0.0, current_liters - consumption)
	_notify_fuel_changed()

	if current_liters <= 0.0:
		out_of_fuel.emit()
		return false

	return true

## Carga combustible en el tanque hasta su capacidad máxima
## Retorna el volumen real repostado en litros
func refuel(amount_liters: float) -> float:
	if amount_liters <= 0.0 or is_infinite_fuel:
		return 0.0

	var prev_fuel = current_liters
	current_liters = minf(capacity_liters, current_liters + amount_liters)
	var added = current_liters - prev_fuel
	if added > 0.0:
		refueled.emit(added)
		_notify_fuel_changed()
	return added

func get_fuel_percentage() -> float:
	if is_infinite_fuel:
		return 100.0
	if capacity_liters <= 0.0:
		return 0.0
	return (current_liters / capacity_liters) * 100.0

func _notify_fuel_changed() -> void:
	fuel_changed.emit(current_liters, capacity_liters, get_fuel_percentage())
