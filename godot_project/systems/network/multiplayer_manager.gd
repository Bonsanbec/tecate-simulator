class_name MultiplayerManager
extends Node

## Gestor de Entidades Remotas y Coordinador Multijugador para Tecate Simulator.
## Conecta la recepción de snapshots con la instanciación y ciclo de vida de avatares remotos.

signal player_count_changed(count: int)

@export var citizen_entity_scene: PackedScene = preload("res://systems/network/citizen_entity.tscn")
@export var remote_player_scene: PackedScene = preload("res://systems/network/citizen_entity.tscn")
@export var remote_vehicle_scene: PackedScene = preload("res://systems/network/remote_vehicle.tscn")
@export var remote_npc_scene: PackedScene = preload("res://systems/network/citizen_entity.tscn")

const CitizenEntityClass = preload("res://systems/characters/citizen_entity.gd")
const RemoteNPCClass = preload("res://systems/network/remote_npc.gd")
const CharacterCatalogClass = preload("res://systems/characters/character_catalog.gd")

var network_client: NetworkClient
var remote_entities_container: Node3D
var active_remote_players: Dictionary = {}  # entity_id -> CitizenEntity
var active_remote_vehicles: Dictionary = {} # entity_id -> RemoteVehicle
var active_remote_npcs: Dictionary = {}     # entity_id -> CitizenEntity
var active_player_characters: Dictionary = {} # entity_id -> character_id
var _entity_last_seen: Dictionary = {}      # entity_id -> float (timestamp)

const ENTITY_TIMEOUT: float = 3.0

var offline_fallback_container: Node3D = null

func _ensure_remote_entities_container() -> void:
	if not remote_entities_container:
		remote_entities_container = Node3D.new()
		remote_entities_container.name = "RemoteEntities"
		add_child(remote_entities_container)

func _ready():
	_ensure_remote_entities_container()

	# Localizar o instanciar NetworkClient
	network_client = get_node_or_null("../NetworkClient") as NetworkClient
	if not network_client and get_parent():
		network_client = get_parent().find_child("NetworkClient", true, false) as NetworkClient

	# Localizar contenedor de transporte local fuera de línea
	offline_fallback_container = get_node_or_null("../OfflineTransitFallback") as Node3D
	if not offline_fallback_container and get_parent():
		offline_fallback_container = get_parent().find_child("OfflineTransitFallback", true, false) as Node3D

	if network_client:
		_bind_network_signals()

func _bind_network_signals() -> void:
	network_client.snapshot_received.connect(_on_snapshot_received)
	network_client.event_received.connect(_on_event_received)
	network_client.disconnected_from_server.connect(_on_disconnected)
	network_client.connected_to_server.connect(_on_connected)

func _set_offline_fallback_active(active: bool) -> void:
	if offline_fallback_container:
		offline_fallback_container.visible = active
		offline_fallback_container.process_mode = Node.PROCESS_MODE_INHERIT if active else Node.PROCESS_MODE_DISABLED

func _on_connected(_session_id: int, _player_id: int) -> void:
	_set_offline_fallback_active(false)
	player_count_changed.emit(get_player_count())

func _on_disconnected(_reason: String) -> void:
	_clear_all_remote_entities()
	_set_offline_fallback_active(true)
	player_count_changed.emit(1)

func _on_snapshot_received(_server_tick: int, entities: Array[TKTCodec.EntityRecord]) -> void:
	_ensure_remote_entities_container()
	var now = Time.get_ticks_msec() / 1000.0
	var local_id = network_client.player_entity_id if network_client else 0

	for rec in entities:
		# Ignorar nuestra propia entidad local si es jugador
		if rec.entity_id == local_id:
			continue

		if rec.entity_type == TKTCodec.EntityType.VEHICLE:
			var remote_v: RemoteVehicle = active_remote_vehicles.get(rec.entity_id)
			if not remote_v:
				remote_v = remote_vehicle_scene.instantiate() as RemoteVehicle
				remote_entities_container.add_child(remote_v)
				var is_route = (rec.flags & TKTCodec.VehicleFlags.ROUTE_VEHICLE) != 0
				remote_v.setup(rec.entity_id, is_route)
				active_remote_vehicles[rec.entity_id] = remote_v
				print("[MultiplayerManager] Nuevo vehículo remoto avistado: ID=%d" % rec.entity_id)

			remote_v.push_snapshot_record(rec, Time.get_ticks_msec())
			_entity_last_seen[rec.entity_id] = now

		elif rec.entity_type == TKTCodec.EntityType.PLAYER:
			var remote_p = active_remote_players.get(rec.entity_id) as CitizenEntityClass
			if not remote_p:
				remote_p = (citizen_entity_scene if citizen_entity_scene else remote_player_scene).instantiate() as CitizenEntityClass
				remote_entities_container.add_child(remote_p)
				var char_id = active_player_characters.get(rec.entity_id, "")
				if not char_id.is_empty():
					remote_p.identity_id = char_id
				remote_p.setup(rec.entity_id, false, "Jugador #%d" % rec.entity_id)
				active_remote_players[rec.entity_id] = remote_p
				print("[MultiplayerManager] Nuevo jugador remoto avistado: ID=%d (Personaje=%s)" % [rec.entity_id, remote_p.identity_id])
				player_count_changed.emit(get_player_count())

			remote_p.push_snapshot_record(rec, Time.get_ticks_msec())
			_entity_last_seen[rec.entity_id] = now

		elif rec.entity_type == TKTCodec.EntityType.NPC:
			var remote_npc = active_remote_npcs.get(rec.entity_id) as CitizenEntityClass
			if not remote_npc:
				remote_npc = (citizen_entity_scene if citizen_entity_scene else remote_npc_scene).instantiate() as CitizenEntityClass
				remote_entities_container.add_child(remote_npc)
				var c_name = _get_citizen_name_by_id(rec.entity_id)
				remote_npc.identity_id = CharacterCatalogClass.get_character_id_for_entity(rec.entity_id)
				remote_npc.setup(rec.entity_id, true, c_name)
				active_remote_npcs[rec.entity_id] = remote_npc
				print("[MultiplayerManager] Nuevo ciudadano remoto avistado: %s (ID=%d, Personaje=%s)" % [c_name, rec.entity_id, remote_npc.identity_id])

			remote_npc.push_snapshot_record(rec, Time.get_ticks_msec())
			_entity_last_seen[rec.entity_id] = now

	# Purgar entidades que dejaron de reportarse
	var to_remove_players: Array[int] = []
	for eid in active_remote_players.keys():
		var last_seen = _entity_last_seen.get(eid, 0.0)
		if (now - last_seen) > ENTITY_TIMEOUT:
			to_remove_players.append(eid)

	for eid in to_remove_players:
		_remove_remote_player(eid)

	var to_remove_vehicles: Array[int] = []
	for vid in active_remote_vehicles.keys():
		var last_seen = _entity_last_seen.get(vid, 0.0)
		if (now - last_seen) > ENTITY_TIMEOUT:
			to_remove_vehicles.append(vid)

	for vid in to_remove_vehicles:
		_remove_remote_vehicle(vid)

	var to_remove_npcs: Array[int] = []
	for nid in active_remote_npcs.keys():
		var last_seen = _entity_last_seen.get(nid, 0.0)
		if (now - last_seen) > ENTITY_TIMEOUT:
			to_remove_npcs.append(nid)

	for nid in to_remove_npcs:
		_remove_remote_npc(nid)

func _on_event_received(ev: Dictionary) -> void:
	var code = ev.get("event_code", 0)
	var data = ev.get("data", PackedByteArray())
	var entity_id = ev.get("entity_id", 0)

	match code:
		TKTCodec.EventCode.VEHICLE_ENTER:
			var enter_data = TKTCodec.decode_vehicle_enter_data(data)
			if not enter_data.is_empty():
				var remote_v = active_remote_vehicles.get(enter_data["vehicle_id"])
				var remote_p = active_remote_players.get(entity_id)
				if not remote_p:
					remote_p = active_remote_npcs.get(entity_id)
				if remote_v and remote_p:
					remote_v.mount_passenger(entity_id, enter_data["seat_index"], remote_p)
					print("[MultiplayerManager] Ciudadano/Jugador %d montado en vehículo %d (asiento %d)" % [
						entity_id, enter_data["vehicle_id"], enter_data["seat_index"]
					])

		TKTCodec.EventCode.VEHICLE_EXIT:
			var exit_data = TKTCodec.decode_vehicle_exit_data(data)
			if not exit_data.is_empty():
				var remote_v = active_remote_vehicles.get(exit_data["vehicle_id"])
				if remote_v:
					var unmounted = remote_v.unmount_passenger(entity_id)
					if unmounted:
						remote_entities_container.add_child(unmounted)
					print("[MultiplayerManager] Ciudadano/Jugador %d desmontado del vehículo %d" % [
						entity_id, exit_data["vehicle_id"]
					])

		TKTCodec.EventCode.CHARACTER_SELECT:
			var character_id = TKTCodec.decode_character_select_data(data)
			if not character_id.is_empty():
				active_player_characters[entity_id] = character_id
				var remote_p = active_remote_players.get(entity_id)
				if remote_p and remote_p.has_method("apply_identity"):
					remote_p.apply_identity(character_id)
				print("[MultiplayerManager] Jugador remoto %d sincronizó personaje '%s'" % [entity_id, character_id])

func _remove_remote_player(entity_id: int) -> void:
	var remote_p = active_remote_players.get(entity_id)
	if remote_p:
		remote_p.queue_free()
		active_remote_players.erase(entity_id)
		active_player_characters.erase(entity_id)
		_entity_last_seen.erase(entity_id)
		print("[MultiplayerManager] Jugador remoto removido: ID=%d" % entity_id)
		player_count_changed.emit(get_player_count())

func _remove_remote_vehicle(entity_id: int) -> void:
	var remote_v = active_remote_vehicles.get(entity_id)
	if remote_v:
		remote_v.queue_free()
		active_remote_vehicles.erase(entity_id)
		_entity_last_seen.erase(entity_id)
		print("[MultiplayerManager] Vehículo remoto removido: ID=%d" % entity_id)

func _remove_remote_npc(entity_id: int) -> void:
	var remote_npc = active_remote_npcs.get(entity_id)
	if remote_npc:
		remote_npc.queue_free()
		active_remote_npcs.erase(entity_id)
		_entity_last_seen.erase(entity_id)
		print("[MultiplayerManager] NPC remoto removido: ID=%d" % entity_id)

func _clear_all_remote_entities() -> void:
	for remote_p in active_remote_players.values():
		if is_instance_valid(remote_p):
			remote_p.queue_free()
	active_remote_players.clear()

	for remote_v in active_remote_vehicles.values():
		if is_instance_valid(remote_v):
			remote_v.queue_free()
	active_remote_vehicles.clear()

	for remote_npc in active_remote_npcs.values():
		if is_instance_valid(remote_npc):
			remote_npc.queue_free()
	active_remote_npcs.clear()

	active_player_characters.clear()
	_entity_last_seen.clear()

func get_player_count() -> int:
	# Retorna 1 (jugador local) + cantidad de jugadores remotos activos
	return 1 + active_remote_players.size()

func _get_citizen_name_by_id(id: int) -> String:
	match id:
		3001: return "Don Miguel"
		3002: return "Doña Rosa"
		3003: return "Juan Carlos"
		3004: return "Carmen"
		_: return "Ciudadano #%d" % id


