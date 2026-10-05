class_name HealthComponent
extends Node

## Componente Centralizado de Salud y Daño para Tecate Simulator
## Gestiona la vida máxima, salud actual, invulnerabilidad, recepción de daño,
## curación y eventos de eliminación (muerte o destrucción) para cualquier entidad.

const EntityHealthDefaultsClass = preload("res://systems/combat/entity_health_defaults.gd")

signal health_changed(current_health: float, max_health: float)
signal damaged(amount: float, attacker: Node)
signal healed(amount: float)
signal died(attacker: Node)

@export var max_health: float = 100.0:
	set(val):
		max_health = maxf(1.0, val)
		current_health = clampf(current_health, 0.0, max_health)
		health_changed.emit(current_health, max_health)

@export var current_health: float = 100.0:
	set(val):
		var prev = current_health
		current_health = clampf(val, 0.0, max_health)
		if prev != current_health:
			health_changed.emit(current_health, max_health)

@export var entity_type: String = "":
	set(val):
		entity_type = val

@export var auto_initialize: bool = true
@export var is_invulnerable: bool = false

var is_dead_flag: bool = false

func _ready() -> void:
	if auto_initialize and get_parent():
		if not entity_type.is_empty():
			max_health = EntityHealthDefaultsClass.get_default_health_for_type(entity_type)
		else:
			max_health = EntityHealthDefaultsClass.get_default_health_for_entity(get_parent())
		current_health = max_health

	is_dead_flag = (current_health <= 0.0)

## Inicializa explícitamente los valores de vida máxima y actual
func initialize(p_max: float, p_current: float = -1.0) -> void:
	max_health = maxf(1.0, p_max)
	current_health = p_max if p_current < 0.0 else clampf(p_current, 0.0, max_health)
	is_dead_flag = (current_health <= 0.0)
	health_changed.emit(current_health, max_health)

## Aplica una cantidad de daño a la entidad y retorna el daño real infligido
func take_damage(amount: float, attacker: Node = null) -> float:
	if amount <= 0.0 or is_invulnerable or is_dead_flag:
		return 0.0

	var damage_dealt = minf(current_health, amount)
	current_health -= damage_dealt
	damaged.emit(damage_dealt, attacker)

	if current_health <= 0.0 and not is_dead_flag:
		is_dead_flag = true
		died.emit(attacker)

	return damage_dealt

## Restaura vida a la entidad
func heal(amount: float) -> float:
	if amount <= 0.0 or is_dead_flag or current_health >= max_health:
		return 0.0

	var heal_amount = minf(max_health - current_health, amount)
	current_health += heal_amount
	healed.emit(heal_amount)
	return heal_amount

## Retorna el porcentaje de vida entre 0.0 y 1.0
func get_health_percentage() -> float:
	if max_health <= 0.0:
		return 0.0
	return clampf(current_health / max_health, 0.0, 1.0)

## Retorna si la entidad está muerta o destruida
func is_dead() -> bool:
	return is_dead_flag or current_health <= 0.0

## Revive o restablece la salud completa de la entidad
func reset_health() -> void:
	is_dead_flag = false
	current_health = max_health
