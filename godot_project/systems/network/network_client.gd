class_name NetworkClient
extends Node

## Cliente de Red UDP para Tecate Simulator (Protocolo TKT/1).
## Conecta de forma no bloqueante con el servidor.

signal connected_to_server(session_id: int, player_entity_id: int)
signal disconnected_from_server(reason: String)
signal latency_updated(ping_ms: float)
signal snapshot_received(server_tick: int, entities: Array[TKTCodec.EntityRecord])
signal chat_received(sender_id: int, channel: int, message: String)
signal event_received(event_data: Dictionary)


enum ConnectionState {
	DISCONNECTED,
	CONNECTING,
	CONNECTED,
	RECONNECTING
}

var state: ConnectionState = ConnectionState.DISCONNECTED
var peer: PacketPeerUDP = PacketPeerUDP.new()

# Configuración de Red
var server_host: String = ""
var server_port: int = 52665
var tick_rate: int = 30
var is_local_dev: bool = false
var debug_logging: bool = false

# Estado de Sesión
var session_id: int = 0
var player_entity_id: int = 0
var sequence_out: int = 0
var current_ping_ms: float = 0.0

# Temporizadores y contadores
var _tick_timer: float = 0.0
var _ping_timer: float = 0.0
var _connect_retry_timer: float = 0.0
var _last_received_time: float = 0.0
var _pending_pings: Dictionary = {} # ping_id -> send_timestamp_ms

const PING_INTERVAL: float = 2.0
const CONNECTION_TIMEOUT: float = 8.0
const HELLO_RETRY_INTERVAL: float = 1.0

func _init():
	peer = PacketPeerUDP.new()

func _ready():
	_load_configuration()

func _load_configuration() -> void:
	## Lee desde el Autoload NetworkConfig (nodo en /root/NetworkConfig).
	## En Godot 4, los Autoloads son nodos del árbol de escena, NO Engine singletons.
	## NetworkConfig lee de ProjectSettings + override opcional de .env local.
	## Esto funciona en TODOS los targets de exportación sin configuración adicional.
	var cfg: Node = get_node_or_null("/root/NetworkConfig")
	if cfg != null:
		server_host = cfg.server_host
		server_port = cfg.server_port
		tick_rate = cfg.tick_rate
		is_local_dev = cfg.is_local_dev
		debug_logging = cfg.debug_net
	else:
		## Fallback de emergencia: valores de producción hardcodeados.
		## Solo se ejecuta si el Autoload no está en el árbol (p. ej. pruebas unitarias aisladas).
		push_warning("[NetworkClient] Autoload 'NetworkConfig' no encontrado en /root/. Usando defaults de emergencia.")
		server_host = "api.tecate.bonsanbec.dev"
		server_port = 52665
		tick_rate = 30
	print("[NetworkClient] Configuración cargada: %s:%d | TickRate=%d | LocalDev=%s" % [
		server_host, server_port, tick_rate, is_local_dev
	])

func start_connection() -> void:
	if state == ConnectionState.CONNECTED or state == ConnectionState.CONNECTING:
		return

	if peer == null:
		peer = PacketPeerUDP.new()

	print("[NetworkClient] Iniciando conexión con %s:%d..." % [server_host, server_port])

	# Resolver DNS (reutilizar el resultado del Autoload si ya está disponible)
	var target_ip: String = server_host
	var cfg: Node = get_node_or_null("/root/NetworkConfig")
	if cfg != null:
		target_ip = cfg.resolve_host()
		if target_ip.is_empty():
			print("[NetworkClient] Sin conexión al servidor. El juego continuará en modo fuera de línea.")
			state = ConnectionState.DISCONNECTED
			disconnected_from_server.emit("Host no alcanzable (DNS offline)")
			return
	elif not server_host.is_valid_ip_address():
		var resolved = IP.resolve_hostname(server_host, IP.TYPE_IPV4)
		if resolved.is_valid_ip_address():
			target_ip = resolved
		else:
			print("[NetworkClient] No se pudo resolver DNS para '%s'. Modo fuera de línea activo." % server_host)
			state = ConnectionState.DISCONNECTED
			disconnected_from_server.emit("Host no resoluble (DNS offline)")
			return

	var err = peer.connect_to_host(target_ip, server_port)
	if err != OK or not peer.is_socket_connected():
		print("[NetworkClient] Error al asociar socket UDP con %s:%d (código: %s)" % [target_ip, server_port, err])
		state = ConnectionState.DISCONNECTED
		disconnected_from_server.emit("Fallo de socket UDP")
		return

	state = ConnectionState.CONNECTING
	_connect_retry_timer = 0.0
	_last_received_time = Time.get_ticks_msec() / 1000.0

	_send_hello()

func disconnect_client(reason: String = "Desconexión manual") -> void:
	if state == ConnectionState.DISCONNECTED:
		return

	print("[NetworkClient] Desconectando: ", reason)
	_send_goodbye()
	state = ConnectionState.DISCONNECTED
	session_id = 0
	player_entity_id = 0
	if peer and peer.is_socket_connected():
		peer.close()
	disconnected_from_server.emit(reason)

func _exit_tree():
	if state == ConnectionState.CONNECTED:
		_send_goodbye()
	if peer and peer.is_socket_connected():
		peer.close()

func _physics_process(delta: float) -> void:
	if state == ConnectionState.DISCONNECTED or peer == null or not peer.is_socket_connected():
		return

	_poll_incoming_packets()

	var now = Time.get_ticks_msec() / 1000.0

	# Reintento de HELLO si estamos conectando
	if state == ConnectionState.CONNECTING:
		_connect_retry_timer += delta
		if _connect_retry_timer >= HELLO_RETRY_INTERVAL:
			_connect_retry_timer = 0.0
			_send_hello()

		if (now - _last_received_time) > CONNECTION_TIMEOUT:
			print("[NetworkClient] Tiempo de espera agotado al conectar.")
			state = ConnectionState.DISCONNECTED
			disconnected_from_server.emit("Tiempo de espera agotado al conectar")
			return

	# Control de latencia (Ping / Pong) si estamos conectados
	if state == ConnectionState.CONNECTED:
		_ping_timer += delta
		if _ping_timer >= PING_INTERVAL:
			_ping_timer = 0.0
			_send_ping()

		if (now - _last_received_time) > CONNECTION_TIMEOUT:
			print("[NetworkClient] Conexión perdida con el servidor (timeout de paquetes).")
			state = ConnectionState.DISCONNECTED
			disconnected_from_server.emit("Servidor inactivo (timeout)")

func _poll_incoming_packets() -> void:
	if peer == null or not peer.is_socket_connected():
		return

	while peer.get_available_packet_count() > 0:
		var pkt = peer.get_packet()
		if pkt.is_empty():
			continue

		_last_received_time = Time.get_ticks_msec() / 1000.0
		_handle_incoming_packet(pkt)

func _handle_incoming_packet(data: PackedByteArray) -> void:
	var hdr = TKTCodec.decode_header(data)
	if hdr == null:
		return

	var payload = data.slice(TKTCodec.HEADER_SIZE, TKTCodec.HEADER_SIZE + hdr.payload_length)
	if payload.size() != hdr.payload_length:
		return

	match hdr.message_type:
		TKTCodec.MessageType.WELCOME:
			_process_welcome(payload)
		TKTCodec.MessageType.SNAPSHOT:
			_process_snapshot(payload)
		TKTCodec.MessageType.EVENT:
			_process_event(payload)
		TKTCodec.MessageType.PONG:
			_process_pong(payload)
		TKTCodec.MessageType.CHAT:
			_process_chat(payload)

func _process_event(payload: PackedByteArray) -> void:
	var ev = TKTCodec.decode_event(payload)
	if ev.is_empty():
		return
	if debug_logging:
		print("[NetworkClient] EVENT recibido: code=%d, entity_id=%d" % [ev["event_code"], ev["entity_id"]])
	event_received.emit(ev)


func _process_welcome(payload: PackedByteArray) -> void:
	var welcome = TKTCodec.decode_welcome(payload)
	if welcome.is_empty():
		return

	session_id = welcome["session_id"]
	player_entity_id = welcome["player_entity_id"]
	state = ConnectionState.CONNECTED
	print("[NetworkClient] ¡Conectado al servidor! SessionID=%d, PlayerEntityID=%d" % [session_id, player_entity_id])
	connected_to_server.emit(session_id, player_entity_id)

func _process_snapshot(payload: PackedByteArray) -> void:
	var snap = TKTCodec.decode_snapshot(payload)
	if snap.is_empty():
		return

	var entities: Array[TKTCodec.EntityRecord] = snap["entities"]
	snapshot_received.emit(snap["server_tick"], entities)

func _process_pong(payload: PackedByteArray) -> void:
	var pong = TKTCodec.decode_pong(payload)
	if pong.is_empty():
		return

	var pid = pong["ping_id"]
	if _pending_pings.has(pid):
		var sent_time = _pending_pings[pid]
		var now_ms = Time.get_ticks_msec()
		current_ping_ms = float(now_ms - sent_time)
		_pending_pings.erase(pid)
		latency_updated.emit(current_ping_ms)

func _process_chat(payload: PackedByteArray) -> void:
	var chat = TKTCodec.decode_chat(payload)
	if chat.is_empty():
		return

	chat_received.emit(chat["sender_id"], chat["channel"], chat["message"])

# =============================================================================
# EMISIÓN DE PAQUETES SALIENTES
# =============================================================================

func _next_seq() -> int:
	sequence_out = (sequence_out + 1) & 0xFFFFFFFF
	return sequence_out

func _send_hello() -> void:
	if peer == null or not peer.is_socket_connected():
		return

	var hello_payload = TKTCodec.encode_hello("1.0", "")
	var hdr = TKTCodec.Header.new()
	hdr.message_type = TKTCodec.MessageType.HELLO
	hdr.flags = TKTCodec.PacketFlags.RELIABLE
	hdr.sequence = _next_seq()
	hdr.timestamp = Time.get_ticks_msec()

	var packet = TKTCodec.encode_packet(hdr, hello_payload)
	peer.put_packet(packet)

func send_player_input(tick: int, pos: Vector3, yaw: float, pitch: float, vel: Vector3, flags: int) -> void:
	if state != ConnectionState.CONNECTED or peer == null or not peer.is_socket_connected():
		return

	var input_payload = TKTCodec.encode_input(tick, pos, yaw, pitch, vel, flags)
	var hdr = TKTCodec.Header.new()
	hdr.message_type = TKTCodec.MessageType.INPUT
	hdr.session_id = session_id
	hdr.sequence = _next_seq()
	hdr.timestamp = Time.get_ticks_msec()

	var packet = TKTCodec.encode_packet(hdr, input_payload)
	peer.put_packet(packet)

func _send_ping() -> void:
	if peer == null or not peer.is_socket_connected():
		return

	var ping_id = int(randi()) & 0x7FFFFFFF
	var now_ms = Time.get_ticks_msec()
	_pending_pings[ping_id] = now_ms

	# Limpiar pings viejos si quedaron acumulados
	if _pending_pings.size() > 20:
		_pending_pings.clear()

	var ping_payload = TKTCodec.encode_ping(ping_id, now_ms)
	var hdr = TKTCodec.Header.new()
	hdr.message_type = TKTCodec.MessageType.PING
	hdr.session_id = session_id
	hdr.sequence = _next_seq()
	hdr.timestamp = now_ms

	var packet = TKTCodec.encode_packet(hdr, ping_payload)
	peer.put_packet(packet)

func send_chat_message(channel: int, message: String) -> void:
	if state != ConnectionState.CONNECTED or peer == null or not peer.is_socket_connected():
		return

	var chat_payload = TKTCodec.encode_chat(channel, message)
	var hdr = TKTCodec.Header.new()
	hdr.message_type = TKTCodec.MessageType.CHAT
	hdr.flags = TKTCodec.PacketFlags.RELIABLE
	hdr.session_id = session_id
	hdr.sequence = _next_seq()
	hdr.timestamp = Time.get_ticks_msec()

	var packet = TKTCodec.encode_packet(hdr, chat_payload)
	peer.put_packet(packet)

func _send_goodbye() -> void:
	if peer == null or not peer.is_socket_connected():
		return

	var bye_payload = TKTCodec.encode_goodbye(0)
	var hdr = TKTCodec.Header.new()
	hdr.message_type = TKTCodec.MessageType.GOODBYE
	hdr.session_id = session_id
	hdr.sequence = _next_seq()
	hdr.timestamp = Time.get_ticks_msec()

	var packet = TKTCodec.encode_packet(hdr, bye_payload)
	peer.put_packet(packet)

func send_event(event_code: int, data: PackedByteArray = PackedByteArray()) -> void:
	if state != ConnectionState.CONNECTED or peer == null or not peer.is_socket_connected():
		return

	var event_id = int(randi()) & 0x7FFFFFFF
	var now_ms = Time.get_ticks_msec()
	var ev_payload = TKTCodec.encode_event(event_id, event_code, player_entity_id, now_ms, data)

	var hdr = TKTCodec.Header.new()
	hdr.message_type = TKTCodec.MessageType.EVENT
	hdr.flags = TKTCodec.PacketFlags.RELIABLE
	hdr.session_id = session_id
	hdr.sequence = _next_seq()
	hdr.timestamp = now_ms

	var packet = TKTCodec.encode_packet(hdr, ev_payload)
	peer.put_packet(packet)

func send_vehicle_enter(vehicle_id: int, seat_index: int, is_driver: bool) -> void:
	var data = TKTCodec.encode_vehicle_enter_data(vehicle_id, seat_index, is_driver)
	send_event(TKTCodec.EventCode.VEHICLE_ENTER, data)
	if debug_logging:
		print("[NetworkClient] Enviado VEHICLE_ENTER: vehicle_id=%d, seat=%d, is_driver=%s" % [vehicle_id, seat_index, is_driver])

func send_vehicle_exit(vehicle_id: int, seat_index: int) -> void:
	var data = TKTCodec.encode_vehicle_exit_data(vehicle_id, seat_index)
	send_event(TKTCodec.EventCode.VEHICLE_EXIT, data)
	if debug_logging:
		print("[NetworkClient] Enviado VEHICLE_EXIT: vehicle_id=%d, seat=%d" % [vehicle_id, seat_index])

func send_vehicle_refuel(vehicle_id: int, fuel_amount: float) -> void:
	var data = TKTCodec.encode_vehicle_refuel_data(vehicle_id, fuel_amount)
	send_event(TKTCodec.EventCode.VEHICLE_REFUEL, data)
	if debug_logging:
		print("[NetworkClient] Enviado VEHICLE_REFUEL: vehicle_id=%d, fuel=%.1f" % [vehicle_id, fuel_amount])

