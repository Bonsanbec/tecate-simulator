class_name GasStationPumpZone
extends Area3D

## Zona Interactiva de Estación de Servicio (Bomba de Gasolina)
## Detecta vehículos estacionados en su radio y gestiona el reabastecimiento
## de combustible hacia el tanque del vehículo.

const VehicleBaseClass = preload("res://systems/vehicles/core/vehicle_base.gd")

signal refuel_started(vehicle: VehicleBaseClass)
signal refuel_progress(current: float, capacity: float, percent: float)
signal refuel_completed(vehicle: VehicleBaseClass)

@export var station_name: String = "Gasolinera Pemex Tecate"
@export var refuel_rate_lps: float = 3.5 # Litros por segundo

var active_vehicle: VehicleBaseClass = null
var is_refueling: bool = false

func _ready() -> void:
	add_to_group("pump_zones")
	body_entered.connect(_on_body_entered)
	body_exited.connect(_on_body_exited)

func _on_body_entered(body: Node) -> void:
	if body is VehicleBaseClass or body.has_method("process_terrain_alignment"):
		active_vehicle = body as VehicleBaseClass
		print("[GasStation] Vehículo '%s' ingresó a la bomba de: %s" % [active_vehicle.vehicle_name, station_name])

func _on_body_exited(body: Node) -> void:
	if body == active_vehicle:
		if is_refueling:
			stop_refueling()
		active_vehicle = null

func start_refueling() -> bool:
	if not active_vehicle or not active_vehicle.fuel_system:
		return false
	if active_vehicle.current_speed_kmh > 2.0:
		print("[GasStation] No se puede repostar: El vehículo debe estar completamente detenido.")
		return false

	is_refueling = true
	refuel_started.emit(active_vehicle)
	return true

func stop_refueling() -> void:
	is_refueling = false
	if active_vehicle:
		refuel_completed.emit(active_vehicle)

func _process(delta: float) -> void:
	if not is_refueling or not active_vehicle or not active_vehicle.fuel_system:
		return

	if active_vehicle.current_speed_kmh > 2.0:
		stop_refueling()
		return

	var fuel_sys = active_vehicle.fuel_system
	var added = fuel_sys.refuel(refuel_rate_lps * delta)
	refuel_progress.emit(fuel_sys.current_liters, fuel_sys.capacity_liters, fuel_sys.get_fuel_percentage())

	if fuel_sys.current_liters >= fuel_sys.capacity_liters:
		stop_refueling()
		print("[GasStation] Tanque lleno al 100% en '%s'" % active_vehicle.vehicle_name)
