class_name DestructibleProp3D
extends StaticBody3D

## Objeto Urbano Interactivo para Tecate Simulator
## Permite a elementos del entorno (mobiliario urbano, señales, bombas de gasolina, bancas)
## responder a impactos físicos slapstick sin requerir barras de vida ni salud numérica.

signal prop_impacted(prop: Node3D, attacker: Node)

@export var prop_name: String = "Objeto Urbano"
@export var entity_type_name: String = "PROP_MEDIUM"

func _ready() -> void:
	add_to_group("urban_props")

## Responde a impactos físicos o empujones
func apply_impact_knockback(_source_pos: Vector3, _force_h: float = 4.0, _force_v: float = 2.0) -> void:
	prop_impacted.emit(self, null)
