class_name MinigameLasTraes
extends "res://systems/minigames/core/minigame_base.gd"

## Minijuego "Las Traes" (La Roña Urbana en el Parque Miguel Hidalgo)
## Un jugador porta el "tag". Debe corretear a los demás para pasarlo antes
## de que termine el tiempo. Quedarse inmóvil (campear) está sancionado.

signal tag_transferred(new_tagger_id: String, old_tagger_id: String)
signal camping_warning(player_id: String)

@export var park_center: Vector3 = Vector3(-6.6844, 400.3132, 2.6878)
@export var park_play_radius: float = 48.0
@export var tag_contact_distance: float = 1.85
@export var immunity_duration: float = 2.0
@export var camping_speed_threshold: float = 0.50
@export var camping_time_limit: float = 3.50

var current_tagger_id: String = ""
var _immunity_target_id: String = ""
var _immunity_timer: float = 0.0

func _init() -> void:
	minigame_id = "las_traes"
	display_name = "Las Traes"
	description = "¡Corre y pasa la roña antes de que termine el tiempo! Prohibido campear."
	duration_seconds = 75.0
	reward_first_place = 50
	reward_participation = 15

func _on_setup() -> void:
	var p_keys = participants.keys()
	if p_keys.is_empty():
		return

	# Inicializar datos personalizados de rastreo de posición y acampada
	for p_id in p_keys:
		var p_data = participants[p_id]
		var entity = p_data["node"]
		var start_pos = get_entity_position(entity) if is_instance_valid(entity) else park_center
		p_data["custom_data"] = {
			"last_position": start_pos,
			"immobile_time": 0.0,
			"has_tag": false
		}

	# Elegir al azar quién inicia trayéndola
	var random_index = randi() % p_keys.size()
	current_tagger_id = p_keys[random_index]
	participants[current_tagger_id]["custom_data"]["has_tag"] = true
	_immunity_target_id = ""
	_immunity_timer = 0.0

func _on_tick(delta: float) -> void:
	if _immunity_timer > 0.0:
		_immunity_timer = maxf(0.0, _immunity_timer - delta)

	# Acumular tiempo trayéndola
	if not current_tagger_id.is_empty() and participants.has(current_tagger_id):
		participants[current_tagger_id]["time_tagged"] += delta

	var tagger_entity = null
	if participants.has(current_tagger_id):
		tagger_entity = participants[current_tagger_id]["node"]

	# Verificar acampada y proximidad de pase de tag
	for p_id in participants:
		var p_data = participants[p_id]
		if not p_data["is_alive"]:
			continue

		var entity = p_data["node"]
		if not is_instance_valid(entity) or not (entity is Node3D):
			continue

		var current_pos: Vector3 = get_entity_position(entity)

		# 1. Chequeo de límites del parque
		var dist_to_center = Vector2(current_pos.x - park_center.x, current_pos.z - park_center.z).length()
		if dist_to_center > park_play_radius:
			# Fuera del parque: regresar al borde
			var dir = (current_pos - park_center).normalized()
			set_entity_position(entity, park_center + dir * (park_play_radius - 2.0))

		# 2. Chequeo de inmovilidad (anti-campeo)
		var last_pos: Vector3 = p_data["custom_data"]["last_position"]
		var movement_delta = current_pos.distance_to(last_pos)
		p_data["custom_data"]["last_position"] = current_pos

		if movement_delta < camping_speed_threshold * delta:
			p_data["custom_data"]["immobile_time"] += delta
			if p_data["custom_data"]["immobile_time"] >= camping_time_limit:
				camping_warning.emit(p_id)
				p_data["custom_data"]["immobile_time"] = 0.0
		else:
			p_data["custom_data"]["immobile_time"] = maxf(0.0, p_data["custom_data"]["immobile_time"] - delta * 2.0)

		# 3. Transferencia de tag por contacto físico con el portador
		if p_id != current_tagger_id and is_instance_valid(tagger_entity):
			if _immunity_timer <= 0.0 or p_id != _immunity_target_id:
				var contact_dist = current_pos.distance_to(get_entity_position(tagger_entity))
				if contact_dist <= tag_contact_distance:
					transfer_tag(p_id)

func transfer_tag(new_tagger_id: String) -> void:
	if not participants.has(new_tagger_id):
		return
	var old_tagger_id = current_tagger_id

	if participants.has(old_tagger_id):
		participants[old_tagger_id]["custom_data"]["has_tag"] = false

	current_tagger_id = new_tagger_id
	participants[new_tagger_id]["custom_data"]["has_tag"] = true

	_immunity_target_id = old_tagger_id
	_immunity_timer = immunity_duration

	tag_transferred.emit(new_tagger_id, old_tagger_id)

func _check_win_condition() -> bool:
	return false # Termina por expiración de tiempo (time_remaining <= 0)

func _build_results(custom: Dictionary) -> Dictionary:
	var ranking: Array = []
	for p_id in participants:
		var p_data = participants[p_id]
		# En Las Traes, menor tiempo portando el tag = mejor desempeño
		ranking.append({
			"id": p_id,
			"time_tagged": p_data["time_tagged"],
			"has_tag_at_end": (p_id == current_tagger_id),
			"score": int(maxf(0.0, 100.0 - p_data["time_tagged"] * 2.0)),
			"node": p_data["node"]
		})

	# Ordenar por menor tiempo portando el tag
	ranking.sort_custom(func(a, b):
		return a["time_tagged"] < b["time_tagged"]
	)

	var winner_id = ranking[0]["id"] if not ranking.is_empty() else ""
	var results = {
		"minigame_id": minigame_id,
		"winner_id": winner_id,
		"loser_id": current_tagger_id,
		"ranking": ranking,
		"elapsed_time": elapsed_time
	}
	results.merge(custom, true)
	return results
