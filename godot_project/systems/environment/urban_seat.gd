class_name UrbanSeat
extends Node3D

## Componente de Asiento Urbano para Bancas, Sillas y Espacios Públicos de Tecate
## Permite al jugador sentarse con la postura biomecánica SITTING y levantarse fluidamente.

@export var seat_name: String = "Banca Urbana"
@export var sit_height_offset: float = 0.45

var occupant: Node3D = null
@onready var exit_point: Marker3D = get_node_or_null("ExitPoint") as Marker3D

func _ready() -> void:
	add_to_group("seats")

func is_occupied() -> bool:
	return occupant != null

func occupy(p_occupant: Node3D) -> bool:
	if is_occupied():
		return false
	occupant = p_occupant
	return true

func vacate() -> Node3D:
	var prev = occupant
	occupant = null
	return prev

func get_exit_global_position() -> Vector3:
	if exit_point:
		return exit_point.global_position
	# Salir de pie 0.65 m hacia adelante de la banca
	return global_position + (-global_transform.basis.z * 0.65)
