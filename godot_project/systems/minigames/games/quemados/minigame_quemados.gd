class_name MinigameQuemados
extends "res://systems/minigames/core/minigame_base.gd"

## Minijuego "Quemados" (Balón Prisionero Callejero en el Parque Miguel Hidalgo)
## Los jugadores arrojan pelotas de básquetbol con rebote elástico.
## El impacto de cualquier pelota elimina al jugador. Prohibido quedarse quieto.

signal ball_thrown(thrower_id: String, position: Vector3, direction: Vector3)
signal player_burned(victim_id: String, thrower_id: String)

@export var park_center: Vector3 = Vector3(-6.6844, 400.3132, 2.6878)
@export var court_radius: float = 38.0
@export var throw_speed: float = 18.0
@export var throw_cooldown: float = 1.25
@export var max_bounces: int = 4

## Estructura de pelotas activas en simulación
## { "pos": Vector3, "vel": Vector3, "bounces": int, "thrower_id": String, "life": float }
var active_balls: Array[Dictionary] = []

func _init() -> void:
	minigame_id = "quemados"
	display_name = "Quemados"
	description = "¡Esquiva los pelotazos y quema a tus rivales! Una sola pelota te elimina."
	duration_seconds = 90.0
	reward_first_place = 50
	reward_participation = 15

func _on_setup() -> void:
	active_balls.clear()
	for p_id in participants:
		var p_data = participants[p_id]
		p_data["custom_data"] = {
			"throw_cooldown": 0.0,
			"balls_thrown": 0,
			"eliminations": 0
		}

func _on_tick(delta: float) -> void:
	# Actualizar cooldowns de disparo de los jugadores
	for p_id in participants:
		var cd = participants[p_id]["custom_data"]["throw_cooldown"]
		if cd > 0.0:
			participants[p_id]["custom_data"]["throw_cooldown"] = maxf(0.0, cd - delta)

	# Simular física de pelotas activas
	var i = active_balls.size() - 1
	while i >= 0:
		var ball = active_balls[i]
		ball["life"] -= delta
		if ball["life"] <= 0.0:
			active_balls.remove_at(i)
			i -= 1
			continue

		# Gravedad e integración de posición
		ball["vel"].y -= 9.8 * delta
		var prev_pos: Vector3 = ball["pos"]
		var next_pos: Vector3 = prev_pos + ball["vel"] * delta

		# Chequeo de colisión de pelota con jugadores vivos
		var hit_player = false
		for p_id in participants:
			var p_data = participants[p_id]
			if not p_data["is_alive"]:
				continue

			# Inmunidad inicial de 0.2s al lanzador para evitar auto-golpe al soltarla
			if ball["life"] > (10.0 - 0.20) and p_id == ball["thrower_id"]:
				continue

			var entity = p_data["node"]
			if not is_instance_valid(entity) or not (entity is Node3D):
				continue

			var player_pos: Vector3 = get_entity_position(entity)
			var hit_dist = next_pos.distance_to(player_pos + Vector3(0, 0.9, 0)) # Torso
			if hit_dist < 0.85:
				hit_player = true
				eliminate_participant(p_id, "quemado por pelota")
				player_burned.emit(p_id, ball["thrower_id"])
				if participants.has(ball["thrower_id"]):
					participants[ball["thrower_id"]]["custom_data"]["eliminations"] += 1
					add_score(ball["thrower_id"], 25)
				break

		if hit_player:
			active_balls.remove_at(i)
			i -= 1
			continue

		# Rebote simple con el suelo a la cota del parque (~400.3m)
		if next_pos.y <= park_center.y + 0.15:
			next_pos.y = park_center.y + 0.15
			ball["vel"].y = -ball["vel"].y * 0.70 # Coeficiente de restitución
			ball["vel"].x *= 0.85 # Fricción
			ball["vel"].z *= 0.85
			ball["bounces"] += 1
			if ball["bounces"] >= max_bounces or ball["vel"].length_squared() < 1.0:
				active_balls.remove_at(i)
				i -= 1
				continue

		ball["pos"] = next_pos
		i -= 1

func throw_ball(thrower_id: String, origin: Vector3, direction: Vector3) -> bool:
	if current_state != GameState.PLAYING:
		return false
	if not participants.has(thrower_id) or not participants[thrower_id]["is_alive"]:
		return false

	var cd = participants[thrower_id]["custom_data"]["throw_cooldown"]
	if cd > 0.0:
		return false

	participants[thrower_id]["custom_data"]["throw_cooldown"] = throw_cooldown
	participants[thrower_id]["custom_data"]["balls_thrown"] += 1

	var launch_dir = direction.normalized()
	var launch_vel = launch_dir * throw_speed + Vector3(0, 1.5, 0) # Ligera parábola

	active_balls.append({
		"pos": origin,
		"vel": launch_vel,
		"bounces": 0,
		"thrower_id": thrower_id,
		"life": 10.0
	})

	ball_thrown.emit(thrower_id, origin, launch_dir)
	return true

func _check_win_condition() -> bool:
	var alive_count = get_alive_count()
	var total_initial = participants.size()
	if total_initial > 1 and alive_count <= 1:
		return true
	return false

func _on_cleanup() -> void:
	active_balls.clear()
