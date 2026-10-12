class_name MinigameManager
extends Node

## Gestor de Minijuegos y Competiciones Urbanas en el Cliente (TKT/1).
## Coordina estados de juego, recepción de eventos fiables, retroalimentación
## háptica/visual y sincronización con el servidor autoritativo.

signal summon_received(game_id: int, host_id: int, mode: int, max_players: int)
signal minigame_started(game_id: int, countdown_seconds: int, participants: Array)
signal minigame_action_received(action_type: int, target_entity_id: int, param_float: float, dir: Vector3)
signal participant_eliminated(game_id: int, eliminated_entity_id: int, reason: int)
signal minigame_ended(game_id: int, winner_entity_id: int, rankings: Array)
signal minigame_cancelled(game_id: int, reason: int)

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
var local_entity_id: int = 0

@export var network_client_path: NodePath = ^"../NetworkClient"
@export var player_path: NodePath = ^"../Player"

var network_client: Node = null
var player: Node = null

func _ready() -> void:
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

	network_client.event_received.connect(_on_network_event_received)
	network_client.connected_to_server.connect(func(_sess, ent_id): local_entity_id = ent_id)

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

	current_game_id = s["game_id"]
	current_state = ClientMinigameState.INVITATION_PENDING
	print("[MinigameManager] Convocatoria recibida para Minijuego %d por jugador %d" % [current_game_id, host_id])
	summon_received.emit(s["game_id"], host_id, s["mode"], s["max_players"])

func _handle_minigame_start(data: PackedByteArray) -> void:
	var s = TKTCodec.decode_minigame_start_data(data)
	if s.is_empty():
		return

	current_game_id = s["game_id"]
	current_state = ClientMinigameState.STAGING
	is_participating = false

	# Verificar si el jugador local está en la lista de participantes
	var participants = s.get("participants", [])
	for p in participants:
		if p.get("entity_id", 0) == local_entity_id:
			is_participating = true
			if player and is_instance_valid(player):
				# Posicionar en el spawn asignado
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
			# El vector dir contiene (push_x, force_v, push_z)
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

	current_state = ClientMinigameState.NONE
	current_game_id = 0
	is_participating = false
	print("[MinigameManager] Minijuego CANCELADO (motivo=%d)" % c["reason"])
	minigame_cancelled.emit(c["game_id"], c["reason"])

func _notify_player_reward(coins: int) -> void:
	var tree = get_tree()
	if not tree:
		return
	var hud = tree.root.find_child("PlayerHUD", true, false)
	if hud and hud.has_method("update_player_balance") and "wallet_label" in hud and hud.wallet_label:
		# Extraer balance actual
		var text = hud.wallet_label.text
		var parts = text.split(" ")
		var curr = int(parts[0]) if parts.size() > 0 else 50
		hud.update_player_balance(curr + coins)

# =============================================================================
# ENVÍO DE ACCIONES AL SERVIDOR
# =============================================================================

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
