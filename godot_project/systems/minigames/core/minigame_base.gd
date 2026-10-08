class_name MinigameBase
extends Node

## Clase Base Modular para Minijuegos en Tecate Simulator
## Define el ciclo de vida estandarizado, preservación de estado previo de avatares,
## recolección de estadísticas, gestión de límites y entrega de recompensas.

signal state_changed(new_state: int, old_state: int)
signal countdown_tick(seconds_left: int)
signal player_eliminated(participant_id: String, reason: String)
signal player_scored(participant_id: String, new_score: int)
signal minigame_completed(results: Dictionary)

enum GameState {
	IDLE = 0,
	SETUP = 1,
	COUNTDOWN = 2,
	PLAYING = 3,
	FINISHING = 4,
	CLEANUP = 5
}

@export var minigame_id: String = "base_minigame"
@export var display_name: String = "Minijuego Base"
@export var description: String = "Descripción corta de la actividad."
@export var duration_seconds: float = 60.0
@export var countdown_seconds: int = 3
@export var reward_first_place: int = 50
@export var reward_participation: int = 15

var current_state: GameState = GameState.IDLE
var elapsed_time: float = 0.0
var time_remaining: float = 60.0
var _countdown_timer: float = 0.0

## Registro de participantes: id -> Dictionary de estado y preservación
## {
##   "node": CitizenEntity,
##   "initial_transform": Transform3D,
##   "is_alive": bool,
##   "score": int,
##   "time_tagged": float,
##   "custom_data": Dictionary
## }
var participants: Dictionary = {}
var minigame_config: Dictionary = {}

func _ready() -> void:
	set_process(false)

func setup(p_participants: Array, p_config: Dictionary = {}) -> bool:
	if current_state != GameState.IDLE:
		push_warning("MinigameBase [%s]: Intento de setup fuera de estado IDLE." % minigame_id)
		return false

	_set_state(GameState.SETUP)
	minigame_config = p_config
	elapsed_time = 0.0
	time_remaining = duration_seconds
	participants.clear()

	for entity in p_participants:
		if not is_instance_valid(entity):
			continue
		var entity_id = _get_entity_identifier(entity)
		participants[entity_id] = {
			"node": entity,
			"initial_transform": get_entity_transform(entity),
			"is_alive": true,
			"score": 0,
			"time_tagged": 0.0,
			"custom_data": {}
		}

	# Gancho para configuraciones específicas de las clases hijas
	_on_setup()
	return true

func start_countdown() -> void:
	if current_state != GameState.SETUP:
		return
	_set_state(GameState.COUNTDOWN)
	_countdown_timer = float(countdown_seconds)
	countdown_tick.emit(int(ceil(_countdown_timer)))
	set_process(true)
	_on_countdown_start()

func start_game() -> void:
	_set_state(GameState.PLAYING)
	time_remaining = duration_seconds
	elapsed_time = 0.0
	_on_game_start()

func _process(delta: float) -> void:
	match current_state:
		GameState.COUNTDOWN:
			var prev_second = int(ceil(_countdown_timer))
			_countdown_timer -= delta
			var new_second = int(ceil(_countdown_timer))
			if new_second != prev_second and new_second > 0:
				countdown_tick.emit(new_second)
			if _countdown_timer <= 0.0:
				start_game()

		GameState.PLAYING:
			elapsed_time += delta
			if duration_seconds > 0.0:
				time_remaining = maxf(0.0, duration_seconds - elapsed_time)
				if time_remaining <= 0.0:
					_on_time_expired()
					return
			_on_tick(delta)

			if _check_win_condition():
				finish_game()

func finish_game(custom_results: Dictionary = {}) -> void:
	if current_state != GameState.PLAYING and current_state != GameState.COUNTDOWN:
		return
	_set_state(GameState.FINISHING)
	set_process(false)

	var results = _build_results(custom_results)
	_on_game_finished(results)
	minigame_completed.emit(results)

func cleanup_and_restore() -> void:
	_set_state(GameState.CLEANUP)
	set_process(false)

	# Restaurar cada jugador a su posición y estado previo exacto
	for p_id in participants:
		var data = participants[p_id]
		var entity = data["node"]
		if is_instance_valid(entity) and entity is Node3D:
			var saved_transform: Transform3D = data["initial_transform"]
			set_entity_transform(entity, saved_transform)
			if entity.has_method("reset_physics_interpolation"):
				entity.reset_physics_interpolation()

	_on_cleanup()
	participants.clear()
	_set_state(GameState.IDLE)

func get_entity_position(entity: Node) -> Vector3:
	if entity is Node3D:
		return entity.global_position if entity.is_inside_tree() else entity.position
	return Vector3.ZERO

func set_entity_position(entity: Node, pos: Vector3) -> void:
	if entity is Node3D:
		if entity.is_inside_tree():
			entity.global_position = pos
		else:
			entity.position = pos

func get_entity_transform(entity: Node) -> Transform3D:
	if entity is Node3D:
		return entity.global_transform if entity.is_inside_tree() else entity.transform
	return Transform3D.IDENTITY

func set_entity_transform(entity: Node, xform: Transform3D) -> void:
	if entity is Node3D:
		if entity.is_inside_tree():
			entity.global_transform = xform
		else:
			entity.transform = xform

func eliminate_participant(p_id: String, reason: String = "eliminado") -> void:
	if not participants.has(p_id):
		return
	var data = participants[p_id]
	if not data["is_alive"]:
		return
	data["is_alive"] = false
	player_eliminated.emit(p_id, reason)
	_on_participant_eliminated(p_id, reason)

func add_score(p_id: String, amount: int) -> void:
	if not participants.has(p_id):
		return
	participants[p_id]["score"] += amount
	player_scored.emit(p_id, participants[p_id]["score"])

func get_alive_count() -> int:
	var count = 0
	for p_id in participants:
		if participants[p_id]["is_alive"]:
			count += 1
	return count

func get_alive_participants() -> Array:
	var alive_list = []
	for p_id in participants:
		if participants[p_id]["is_alive"]:
			alive_list.append(participants[p_id]["node"])
	return alive_list

func _get_entity_identifier(entity: Node) -> String:
	if "citizen_id" in entity and not str(entity.citizen_id).is_empty():
		return str(entity.citizen_id)
	return entity.name

func _set_state(new_state: GameState) -> void:
	var old = current_state
	current_state = new_state
	state_changed.emit(int(new_state), int(old))

## Métodos virtuales para ser sobreescritos por cada minijuego concreto
func _on_setup() -> void:
	pass

func _on_countdown_start() -> void:
	pass

func _on_game_start() -> void:
	pass

func _on_tick(_delta: float) -> void:
	pass

func _on_time_expired() -> void:
	finish_game({"reason": "time_expired"})

func _check_win_condition() -> bool:
	return false

func _on_participant_eliminated(_p_id: String, _reason: String) -> void:
	pass

func _on_game_finished(_results: Dictionary) -> void:
	pass

func _on_cleanup() -> void:
	pass

func _build_results(custom: Dictionary) -> Dictionary:
	var ranking: Array = []
	for p_id in participants:
		var p_data = participants[p_id]
		ranking.append({
			"id": p_id,
			"score": p_data["score"],
			"is_alive": p_data["is_alive"],
			"node": p_data["node"]
		})

	ranking.sort_custom(func(a, b):
		if a["is_alive"] != b["is_alive"]:
			return a["is_alive"]
		return a["score"] > b["score"]
	)

	var winner_id = ranking[0]["id"] if not ranking.is_empty() else ""
	var final_dict = {
		"minigame_id": minigame_id,
		"winner_id": winner_id,
		"ranking": ranking,
		"elapsed_time": elapsed_time
	}
	final_dict.merge(custom, true)
	return final_dict
