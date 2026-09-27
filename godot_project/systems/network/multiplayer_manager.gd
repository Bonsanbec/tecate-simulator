class_name MultiplayerManager
extends Node

## Gestor de Entidades Remotas y Coordinador Multijugador para Tecate Simulator.
## Conecta la recepción de snapshots con la instanciación y ciclo de vida de avatares remotos.

signal player_count_changed(count: int)

@export var remote_player_scene: PackedScene = preload("res://systems/network/remote_player.tscn")

var network_client: NetworkClient
var remote_entities_container: Node3D
var active_remote_players: Dictionary = {} # entity_id -> RemotePlayer
var _entity_last_seen: Dictionary = {}     # entity_id -> float (timestamp)

const ENTITY_TIMEOUT: float = 3.0

func _ready():
	# Crear contenedor para entidades remotas en la escena
	remote_entities_container = Node3D.new()
	remote_entities_container.name = "RemoteEntities"
	add_child(remote_entities_container)

	# Localizar o instanciar NetworkClient
	network_client = get_node_or_null("../NetworkClient") as NetworkClient
	if not network_client and get_parent():
		network_client = get_parent().find_child("NetworkClient", true, false) as NetworkClient

	if network_client:
		_bind_network_signals()

func _bind_network_signals() -> void:
	network_client.snapshot_received.connect(_on_snapshot_received)
	network_client.disconnected_from_server.connect(_on_disconnected)
	network_client.connected_to_server.connect(_on_connected)

func _on_connected(_session_id: int, _player_id: int) -> void:
	player_count_changed.emit(get_player_count())

func _on_disconnected(_reason: String) -> void:
	_clear_all_remote_players()
	player_count_changed.emit(1)

func _on_snapshot_received(_server_tick: int, entities: Array[TKTCodec.EntityRecord]) -> void:
	var now = Time.get_ticks_msec() / 1000.0
	var local_id = network_client.player_entity_id if network_client else 0

	for rec in entities:
		# Ignorar nuestra propia entidad local
		if rec.entity_id == local_id:
			continue

		var remote_p: RemotePlayer = active_remote_players.get(rec.entity_id)
		if not remote_p:
			remote_p = remote_player_scene.instantiate() as RemotePlayer
			remote_entities_container.add_child(remote_p)
			remote_p.setup(rec.entity_id)
			active_remote_players[rec.entity_id] = remote_p
			print("[MultiplayerManager] Nuevo jugador remoto avistado: ID=%d" % rec.entity_id)
			player_count_changed.emit(get_player_count())

		remote_p.push_snapshot_record(rec, Time.get_ticks_msec())
		_entity_last_seen[rec.entity_id] = now

	# Purgar entidades que dejaron de reportarse
	var to_remove: Array[int] = []
	for eid in active_remote_players.keys():
		var last_seen = _entity_last_seen.get(eid, 0.0)
		if (now - last_seen) > ENTITY_TIMEOUT:
			to_remove.append(eid)

	for eid in to_remove:
		_remove_remote_player(eid)

func _remove_remote_player(entity_id: int) -> void:
	var remote_p = active_remote_players.get(entity_id)
	if remote_p:
		remote_p.queue_free()
		active_remote_players.erase(entity_id)
		_entity_last_seen.erase(entity_id)
		print("[MultiplayerManager] Jugador remoto removido: ID=%d" % entity_id)
		player_count_changed.emit(get_player_count())

func _clear_all_remote_players() -> void:
	for remote_p in active_remote_players.values():
		if is_instance_valid(remote_p):
			remote_p.queue_free()
	active_remote_players.clear()
	_entity_last_seen.clear()

func get_player_count() -> int:
	# Retorna 1 (jugador local) + cantidad de jugadores remotos activos
	return 1 + active_remote_players.size()
