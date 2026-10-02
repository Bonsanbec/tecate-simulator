class_name VehicleSeat
extends Node3D

## Representación de Asiento para Vehículos en Tecate Simulator
## Define las capacidades de la plaza (Conductor vs. Pasajero), puntos de anclaje
## de cámara y descenso, y gestiona la asociación con el avatar ocupante.

enum SeatType {
	DRIVER = 0,    ## Asiento de conducción con acceso al control del vehículo
	PASSENGER = 1  ## Asiento de pasajero pasivo con vista panorámica / cabina
}

@export var seat_type: SeatType = SeatType.PASSENGER
@export var seat_index: int = 0
@export var seat_name: String = "Asiento"

## Ocupante actual del asiento (PlayerController o NPC)
var occupant: Node3D = null

## Puntos de anclaje de posición y descenso
@onready var exit_point: Marker3D = get_node_or_null("ExitPoint") as Marker3D

func _ready() -> void:
	add_to_group("seats")

func is_occupied() -> bool:
	return occupant != null

func is_driver() -> bool:
	return seat_type == SeatType.DRIVER

func occupy(p_occupant: Node3D) -> bool:
	if is_occupied():
		return false
	occupant = p_occupant
	return true

func vacate() -> Node3D:
	var prev_occupant = occupant
	occupant = null
	return prev_occupant

## Retorna la posición global de descenso seguro
func get_exit_global_position() -> Vector3:
	if exit_point:
		return exit_point.global_position
	# Fallback inteligente: Salir hacia el pasillo central
	var aisle_dir = 1.0 if position.x < 0.0 else -1.0
	return global_position + (global_transform.basis.x * aisle_dir * 0.65)
