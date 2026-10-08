class_name MinigameMiKiosko
extends "res://systems/minigames/core/minigame_base.gd"

## Minijuego "Mi Kiosko" (All-vs-All de Empujones y Bloqueo en el Kiosko de Tecate)
## Los participantes luchan en la tarima elevada del Kiosko de Parque Hidalgo.
## Cualquier jugador que caiga al pasto o sea arrojado fuera queda eliminado.

@export var kiosk_center: Vector3 = Vector3(-6.6844, 401.80, 2.6878)
@export var platform_radius: float = 4.80
@export var fall_altitude_threshold: float = 401.10
@export var push_force: float = 12.0
@export var parry_window: float = 0.40

func _init() -> void:
	minigame_id = "mi_kiosko"
	display_name = "Mi Kiosko"
	description = "¡Empuja a tus amigos fuera del Kiosko y sé el último en pie!"
	duration_seconds = 90.0
	reward_first_place = 50
	reward_participation = 15

func _on_setup() -> void:
	# Colocar a los participantes distribuidos radialmente sobre la plataforma
	var p_keys = participants.keys()
	var count = p_keys.size()
	if count == 0:
		return

	var angle_step = TAU / float(maxi(1, count))
	var spawn_radius = minf(2.5, platform_radius * 0.6)

	for i in range(count):
		var p_id = p_keys[i]
		var angle = float(i) * angle_step
		var spawn_pos = kiosk_center + Vector3(cos(angle) * spawn_radius, 0.15, sin(angle) * spawn_radius)
		var entity = participants[p_id]["node"]
		if is_instance_valid(entity) and entity is Node3D:
			set_entity_position(entity, spawn_pos)
			# Mirar hacia el centro del kiosko si está en el árbol de escena
			if entity.is_inside_tree():
				var look_target = kiosk_center
				look_target.y = spawn_pos.y
				if spawn_pos.distance_squared_to(look_target) > 0.01:
					entity.look_at(look_target, Vector3.UP)
					entity.rotate_y(PI) # Mirar hacia el frente/oponentes

func _on_tick(_delta: float) -> void:
	# Verificar si algún participante activo cayó de la plataforma
	for p_id in participants:
		var p_data = participants[p_id]
		if not p_data["is_alive"]:
			continue

		var entity = p_data["node"]
		if not is_instance_valid(entity) or not (entity is Node3D):
			continue

		var pos: Vector3 = get_entity_position(entity)
		var horizontal_dist = Vector2(pos.x - kiosk_center.x, pos.z - kiosk_center.z).length()

		# Criterio de caída: fuera del radio del kiosko o por debajo de la altura de la tarima
		if pos.y < fall_altitude_threshold or horizontal_dist > platform_radius:
			eliminate_participant(p_id, "caída del kiosko")

func _check_win_condition() -> bool:
	# Si solo queda 1 jugador con vida (o ninguno si cayeron simultáneamente)
	var alive_count = get_alive_count()
	var total_initial = participants.size()

	if total_initial > 1 and alive_count <= 1:
		return true
	elif total_initial == 1 and alive_count == 0:
		return true
	return false

## Acción de empujar: aplica un impulso vectorial en el cuerpo del adversario
func execute_push(attacker_id: String, target_id: String, direction: Vector3) -> bool:
	if current_state != GameState.PLAYING:
		return false
	if not participants.has(attacker_id) or not participants.has(target_id):
		return false
	if not participants[attacker_id]["is_alive"] or not participants[target_id]["is_alive"]:
		return false

	var target_entity = participants[target_id]["node"]
	if not is_instance_valid(target_entity):
		return false

	# Verificar bloqueo / parry si el objetivo lo tenía activo
	var target_data = participants[target_id]
	if target_data["custom_data"].get("is_blocking", false):
		# El bloqueo exitoso desvía el empujón y aturde levemente al atacante
		add_score(target_id, 5)
		return false

	# Aplicar knockback al personaje
	var push_dir = direction.normalized()
	push_dir.y = 0.25 # Leve levantamiento para saltar barandales
	push_dir = push_dir.normalized()

	if target_entity is CharacterBody3D:
		target_entity.velocity += push_dir * push_force
	elif "velocity" in target_entity:
		target_entity.velocity += push_dir * push_force

	add_score(attacker_id, 10)
	return true

func set_player_blocking(p_id: String, blocking: bool) -> void:
	if participants.has(p_id):
		participants[p_id]["custom_data"]["is_blocking"] = blocking
