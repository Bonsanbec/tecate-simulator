class_name MinigameManager
extends Node

## Gestor de Minijuegos y Competiciones Urbanas en el Cliente (TKT/1).
## Coordina estados de juego, recepción de eventos fiables, sesiones de práctica
## en solitario, retroalimentación háptica/visual y sincronización con el servidor.

const MinigameCatalogClass = preload("res://systems/minigames/minigame_catalog.gd")

signal summon_received(game_id: int, host_id: int, mode: int, max_players: int)
signal minigame_started(game_id: int, countdown_seconds: int, participants: Array)
signal minigame_action_received(action_type: int, target_entity_id: int, param_float: float, dir: Vector3)
signal participant_eliminated(game_id: int, eliminated_entity_id: int, reason: int)
signal minigame_ended(game_id: int, winner_entity_id: int, rankings: Array)
signal minigame_cancelled(game_id: int, reason: int)
signal upcoming_minigame_notified(game_id: int, title: String, phase: int, location_name: String)

enum ClientMinigameState {
	NONE,
	INVITATION_PENDING,
	STAGING,
	ACTIVE,
	SUMMARY
}

var current_state: ClientMinigameState = ClientMinigameState.NONE
var current_game_id: int = 0
var is_participating: bool = false
var is_local_match: bool = false
var is_local_practice: bool:
	get:
		return is_local_match
	set(val):
		is_local_match = val
var local_entity_id: int = 0

var _staging_timer: float = 0.0
var _local_match_timer: float = 0.0
var _saved_local_position: Vector3 = Vector3.ZERO
var _saved_local_yaw: float = 0.0

func is_in_minigame() -> bool:
	return current_state in [ClientMinigameState.STAGING, ClientMinigameState.ACTIVE]

func _set_minigame_zones_visible(is_vis: bool) -> void:
	var tree = get_tree()
	if not tree:
		return
	for mz in tree.get_nodes_in_group("minigame_zones"):
		if mz is Node3D:
			mz.visible = is_vis

func _clear_player_interaction_prompts() -> void:
	if player and is_instance_valid(player):
		if "_nearby_minigame_zone" in player:
			player._nearby_minigame_zone = null
		if "_nearby_minigame_location_id" in player:
			player._nearby_minigame_location_id = ""
		if "hud" in player and player.hud and player.hud.has_method("set_interaction_prompt"):
			player.hud.set_interaction_prompt("")

@export var network_client_path: NodePath = ^"../NetworkClient"
@export var player_path: NodePath = ^"../Player"

var network_client: Node = null
var player: Node = null

func _ready() -> void:
	add_to_group("minigame_manager")
	_resolve_dependencies()
	_connect_network()

func _resolve_dependencies() -> void:
	if has_node(network_client_path):
		network_client = get_node(network_client_path)
	elif get_parent() and get_parent().has_node("NetworkClient"):
		network_client = get_parent().get_node("NetworkClient")

	if has_node(player_path):
		player = get_node(player_path)
	elif get_parent() and get_parent().has_node("Player"):
		player = get_parent().get_node("Player")

func _connect_network() -> void:
	if not network_client:
		return

	if not network_client.event_received.is_connected(_on_network_event_received):
		network_client.event_received.connect(_on_network_event_received)
	if not network_client.connected_to_server.is_connected(_on_connected_to_server):
		network_client.connected_to_server.connect(_on_connected_to_server)

func _on_connected_to_server(_sess: int, ent_id: int) -> void:
	local_entity_id = ent_id

func _process(delta: float) -> void:
	if current_state == ClientMinigameState.STAGING:
		_staging_timer -= delta
		if _staging_timer <= 0.0:
			current_state = ClientMinigameState.ACTIVE
			print("[MinigameManager] Minijuego %d pasó de STAGING a ACTIVE" % current_game_id)

	elif current_state == ClientMinigameState.ACTIVE and is_local_match:
		_process_local_game(delta)

func _on_network_event_received(ev: Dictionary) -> void:
	var code = ev.get("event_code", 0)
	var data: PackedByteArray = ev.get("data", PackedByteArray())

	match code:
		TKTCodec.EventCode.MINIGAME_SUMMON:
			_handle_minigame_summon(data, ev.get("entity_id", 0))
		TKTCodec.EventCode.MINIGAME_START:
			_handle_minigame_start(data)
		TKTCodec.EventCode.MINIGAME_ACTION:
			_handle_minigame_action(data)
		TKTCodec.EventCode.MINIGAME_ELIMINATE:
			_handle_minigame_eliminate(data)
		TKTCodec.EventCode.MINIGAME_END:
			_handle_minigame_end(data)
		TKTCodec.EventCode.MINIGAME_CANCEL:
			_handle_minigame_cancel(data)

func _handle_minigame_summon(data: PackedByteArray, host_id: int) -> void:
	var s = TKTCodec.decode_minigame_summon_data(data)
	if s.is_empty():
		return

	# Si la convocatoria fue iniciada por el propio jugador local, no auto-mostrársela
	if host_id != 0 and host_id == local_entity_id:
		print("[MinigameManager] Convocatoria propia enviada para Minijuego %d (host_id=%d), esperando participantes..." % [s["game_id"], host_id])
		return

	current_game_id = s["game_id"]
	current_state = ClientMinigameState.INVITATION_PENDING
	print("[MinigameManager] Convocatoria recibida para Minijuego %d por jugador %d" % [current_game_id, host_id])
	summon_received.emit(s["game_id"], host_id, s["mode"], s["max_players"])

func _handle_minigame_start(data: PackedByteArray) -> void:
	var s = TKTCodec.decode_minigame_start_data(data)
	if s.is_empty():
		return

	is_local_match = false
	current_game_id = s["game_id"]
	current_state = ClientMinigameState.STAGING
	_staging_timer = float(s.get("countdown_seconds", 3))
	is_participating = false

	_set_minigame_zones_visible(false)
	_clear_player_interaction_prompts()

	# Verificar si el jugador local está en la lista de participantes
	var participants = s.get("participants", [])
	for p in participants:
		if p.get("entity_id", 0) == local_entity_id:
			is_participating = true
			if player and is_instance_valid(player):
				_saved_local_position = player.global_position
				_saved_local_yaw = player.rotation.y
				var target_pos = Vector3(p["spawn_x"], p["spawn_y"], p["spawn_z"])
				player.global_position = target_pos
				player.rotation.y = deg_to_rad(p.get("spawn_yaw", 0.0))
				player.velocity = Vector3.ZERO
			break

	print("[MinigameManager] Minijuego %d INICIADO (Participando=%s, Countdown=%ds)" % [
		current_game_id, is_participating, s["countdown_seconds"]
	])
	minigame_started.emit(current_game_id, s["countdown_seconds"], participants)

func _handle_minigame_action(data: PackedByteArray) -> void:
	var act = TKTCodec.decode_minigame_action_data(data)
	if act.is_empty():
		return

	var action_type = act["action_type"]
	var target_id = act["target_entity_id"]
	var param_float = act["param_float"]
	var dir = act["dir"]

	# Si la acción es empujón slapstick (1) y el objetivo somos nosotros
	if action_type == 1 and target_id == local_entity_id:
		if player and player.has_method("apply_impact_knockback"):
			var source_pos = player.global_position - Vector3(dir.x, 0.0, dir.z)
			player.apply_impact_knockback(source_pos, param_float, dir.y)

	minigame_action_received.emit(action_type, target_id, param_float, dir)

func _handle_minigame_eliminate(data: PackedByteArray) -> void:
	var elim = TKTCodec.decode_minigame_eliminate_data(data)
	if elim.is_empty():
		return

	var e_id = elim["eliminated_entity_id"]
	var reason = elim["reason"]
	print("[MinigameManager] Participante %d ELIMINADO (motivo=%d)" % [e_id, reason])
	participant_eliminated.emit(elim["game_id"], e_id, reason)

func _handle_minigame_end(data: PackedByteArray) -> void:
	var fin = TKTCodec.decode_minigame_end_data(data)
	if fin.is_empty():
		return

	current_state = ClientMinigameState.SUMMARY
	is_local_match = false
	_set_minigame_zones_visible(true)
	var winner_id = fin["winner_entity_id"]
	var rankings = fin.get("rankings", [])
	print("[MinigameManager] Minijuego FINALIZADO. Ganador: %d. Resultados: %s" % [winner_id, rankings])

	# Si el jugador local recibió recompensas, actualizar monedero en HUD
	for r in rankings:
		if r.get("entity_id", 0) == local_entity_id:
			var coins = r.get("coins_rewarded", 0)
			_notify_player_reward(coins)
			break

	minigame_ended.emit(fin["game_id"], winner_id, rankings)

func _handle_minigame_cancel(data: PackedByteArray) -> void:
	var c = TKTCodec.decode_minigame_cancel_data(data)
	if c.is_empty():
		return

	# Si estábamos en partida local, ignorar cancelación de red por falta de quórum
	if is_local_match and current_state in [ClientMinigameState.STAGING, ClientMinigameState.ACTIVE]:
		return

	current_state = ClientMinigameState.NONE
	current_game_id = 0
	is_participating = false
	_set_minigame_zones_visible(true)
	print("[MinigameManager] Minijuego CANCELADO (motivo=%d)" % c["reason"])
	minigame_cancelled.emit(c["game_id"], c["reason"])

func _notify_player_reward(coins: int) -> void:
	var tree = get_tree()
	if not tree:
		return
	var hud = tree.root.find_child("PlayerHUD", true, false)
	if hud and hud.has_method("update_player_balance") and "wallet_label" in hud and hud.wallet_label:
		var text = hud.wallet_label.text
		var parts = text.split(" ")
		var curr = int(parts[0]) if parts.size() > 0 else 50
		hud.update_player_balance(curr + coins)

# =============================================================================
# ENVÍO DE ACCIONES AL SERVIDOR Y EJECUCIÓN LOCAL
# =============================================================================

func start_or_summon_minigame(game_id: int, mode: int = 0, max_players: int = 8, arena_id: int = 1) -> void:
	_resolve_dependencies()
	var is_net_connected: bool = (network_client != null and "state" in network_client and network_client.state == 2) # ConnectionState.CONNECTED == 2
	var online_players: int = 1
	if get_parent():
		var mp_mgr = get_parent().find_child("MultiplayerManager", true, false)
		if mp_mgr and mp_mgr.has_method("get_player_count"):
			online_players = mp_mgr.get_player_count()

	if is_net_connected:
		send_summon_request(game_id, mode, max_players, arena_id)

	# Si el jugador está desconectado o jugando solo en el servidor, iniciar el minijuego de inmediato
	if not is_net_connected or online_players <= 1:
		start_local_game(game_id)

func start_local_game(game_id: int) -> void:
	_resolve_dependencies()
	var g = MinigameCatalogClass.get_minigame(game_id)
	if g.is_empty():
		return

	is_local_match = true
	is_participating = true
	current_game_id = game_id
	current_state = ClientMinigameState.STAGING
	_staging_timer = 3.0
	_local_match_timer = float(g.get("duration_seconds", 60))

	_set_minigame_zones_visible(false)
	_clear_player_interaction_prompts()

	var spawn_pos: Vector3 = g.get("spawn_position", Vector3(-6.6844, 401.80, 2.6878))
	if player and is_instance_valid(player):
		if "is_sitting" in player and player.is_sitting and player.has_method("stand_up"):
			player.stand_up()
		if "current_vehicle" in player and player.current_vehicle and player.has_method("dismount_vehicle"):
			player.dismount_vehicle()
		_saved_local_position = player.global_position
		_saved_local_yaw = player.rotation.y
		player.global_position = spawn_pos
		player.velocity = Vector3.ZERO

	var pid = local_entity_id if local_entity_id != 0 else 1
	var participants = [{
		"entity_id": pid,
		"spawn_x": spawn_pos.x,
		"spawn_y": spawn_pos.y,
		"spawn_z": spawn_pos.z,
		"spawn_yaw": 0.0
	}]
	print("[MinigameManager] Minijuego iniciado para '%s' (ID=%d)" % [g.get("title", "Minijuego"), game_id])
	minigame_started.emit(game_id, 3, participants)

func start_local_practice(game_id: int) -> void:
	start_local_game(game_id)

func _process_local_game(delta: float) -> void:
	_local_match_timer -= delta

	# En Mi Kiosko (ID=1), comprobar caída fuera de la tarima del Kiosko
	if current_game_id == 1 and player and is_instance_valid(player):
		var center = Vector3(-6.6844, 401.80, 2.6878)
		var dx = player.global_position.x - center.x
		var dz = player.global_position.z - center.z
		var h_dist = sqrt(dx * dx + dz * dz)
		if player.global_position.y < 401.10 or h_dist > 5.20:
			var pid = local_entity_id if local_entity_id != 0 else 1
			participant_eliminated.emit(1, pid, 1)
			finish_local_game(false)
			return

	if _local_match_timer <= 0.0:
		finish_local_game(true)

func _process_local_practice(delta: float) -> void:
	_process_local_game(delta)

func finish_local_game(won: bool = true) -> void:
	if not is_local_match:
		return

	is_local_match = false
	is_participating = false
	current_state = ClientMinigameState.SUMMARY
	_set_minigame_zones_visible(true)

	if player and is_instance_valid(player):
		player.global_position = _saved_local_position
		player.rotation.y = _saved_local_yaw
		player.velocity = Vector3.ZERO

	var pid = local_entity_id if local_entity_id != 0 else 1
	var reward = 50 if won else 15
	_notify_player_reward(reward)
	var rankings = [{
		"entity_id": pid,
		"score": 100 if won else 25,
		"coins_rewarded": reward
	}]
	minigame_ended.emit(current_game_id, pid if won else 0, rankings)

func finish_local_practice(won: bool = true) -> void:
	finish_local_game(won)

func notify_upcoming_minigame(game_id: int) -> void:
	var g = MinigameCatalogClass.get_minigame(game_id)
	if g.is_empty():
		return
	upcoming_minigame_notified.emit(
		game_id,
		g.get("title", "Minijuego"),
		g.get("phase", 2),
		g.get("location_name", "Tecate")
	)

func send_summon_request(game_id: int, mode: int = 0, max_players: int = 8, arena_id: int = 1) -> void:
	if not network_client:
		return
	var data = TKTCodec.encode_minigame_summon_data(game_id, mode, max_players, arena_id)
	network_client.send_event(TKTCodec.EventCode.MINIGAME_SUMMON, data)
	print("[MinigameManager] Enviado MINIGAME_SUMMON para juego %d" % game_id)

func send_join_response(game_id: int, accepted: bool) -> void:
	if not network_client:
		return
	var data = TKTCodec.encode_minigame_join_data(game_id, accepted)
	network_client.send_event(TKTCodec.EventCode.MINIGAME_JOIN, data)
	if not accepted:
		current_state = ClientMinigameState.NONE
	print("[MinigameManager] Enviado MINIGAME_JOIN para juego %d (aceptado=%s)" % [game_id, accepted])

func send_game_action(action_type: int, target_entity_id: int, param_float: float, dir: Vector3) -> void:
	if not network_client:
		return
	var data = TKTCodec.encode_minigame_action_data(action_type, target_entity_id, param_float, dir)
	network_client.send_event(TKTCodec.EventCode.MINIGAME_ACTION, data)
