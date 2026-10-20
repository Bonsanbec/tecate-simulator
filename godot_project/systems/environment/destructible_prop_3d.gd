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

var _is_wobbling: bool = false
var _initial_pos: Vector3 = Vector3.ZERO

## Responde a impactos físicos o empujones
func apply_impact_knockback(source_pos: Vector3, force_h: float = 4.0, _force_v: float = 2.0) -> void:
	prop_impacted.emit(self, null)
	_play_slapstick_wobble(source_pos, force_h)

func _play_slapstick_wobble(source_pos: Vector3, force_h: float) -> void:
	if _is_wobbling:
		return
	_is_wobbling = true
	if _initial_pos == Vector3.ZERO:
		_initial_pos = position
	var diff = global_position - source_pos
	var dir = Vector3(diff.x, 0.0, diff.z).normalized()
	var push_offset = dir * minf(0.18, force_h * 0.02)
	var tween = create_tween().set_trans(Tween.TRANS_ELASTIC).set_ease(Tween.EASE_OUT)
	tween.tween_property(self, "position", _initial_pos + push_offset, 0.06)
	tween.tween_property(self, "position", _initial_pos, 0.26)
	tween.finished.connect(func(): _is_wobbling = false)
