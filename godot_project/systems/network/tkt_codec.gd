class_name TKTCodec
extends RefCounted

## Codec binario del Protocolo TKT/1 para Godot 4.
## Serializa y deserializa encabezados y payloads de forma idéntica al servidor en server/.

const MAGIC_BYTES: PackedByteArray = [0x54, 0x4B, 0x54, 0x31] # "TKT1"
const PROTOCOL_VERSION: int = 1
const HEADER_SIZE: int = 28

enum MessageType {
	HELLO = 1,
	WELCOME = 2,
	INPUT = 3,
	SNAPSHOT = 4,
	EVENT = 5,
	CHAT = 6,
	TELEMETRY = 7,
	PING = 8,
	PONG = 9,
	GOODBYE = 10
}

enum PacketFlags {
	NONE = 0x00,
	RELIABLE = 0x01,
	ACK = 0x02,
	RESEND = 0x04
}

class Header:
	var magic: PackedByteArray = [0x54, 0x4B, 0x54, 0x31]
	var protocol_version: int = 1
	var message_type: int = MessageType.HELLO
	var flags: int = PacketFlags.NONE
	var reserved: int = 0
	var session_id: int = 0
	var sequence: int = 0
	var ack: int = 0
	var timestamp: int = 0
	var payload_length: int = 0
	var payload_checksum: int = 0

class EntityRecord:
	var entity_id: int = 0
	var entity_type: int = 1
	var flags: int = 0
	var position: Vector3 = Vector3.ZERO
	var yaw: float = 0.0
	var pitch: float = 0.0
	var velocity: Vector3 = Vector3.ZERO

static func calculate_checksum(bytes: PackedByteArray) -> int:
	var sum: int = 0
	for b in bytes:
		sum = (sum + b) & 0xFFFF
	return sum

static func encode_header(hdr: Header) -> PackedByteArray:
	var sp = StreamPeerBuffer.new()
	sp.big_endian = false
	sp.data_array = PackedByteArray()
	sp.data_array.resize(HEADER_SIZE)

	sp.put_data(MAGIC_BYTES)
	sp.put_u8(hdr.protocol_version)
	sp.put_u8(hdr.message_type)
	sp.put_u8(hdr.flags)
	sp.put_u8(hdr.reserved)
	sp.put_u32(hdr.session_id)
	sp.put_u32(hdr.sequence)
	sp.put_u32(hdr.ack)
	sp.put_u32(hdr.timestamp)
	sp.put_u16(hdr.payload_length)
	sp.put_u16(hdr.payload_checksum)

	return sp.data_array

static func decode_header(bytes: PackedByteArray) -> Header:
	if bytes.size() < HEADER_SIZE:
		return null

	var sp = StreamPeerBuffer.new()
	sp.big_endian = false
	sp.data_array = bytes

	var magic = sp.get_data(4)[1]
	if magic != MAGIC_BYTES:
		return null

	var hdr = Header.new()
	hdr.magic = magic
	hdr.protocol_version = sp.get_u8()
	hdr.message_type = sp.get_u8()
	hdr.flags = sp.get_u8()
	hdr.reserved = sp.get_u8()
	hdr.session_id = sp.get_u32()
	hdr.sequence = sp.get_u32()
	hdr.ack = sp.get_u32()
	hdr.timestamp = sp.get_u32()
	hdr.payload_length = sp.get_u16()
	hdr.payload_checksum = sp.get_u16()

	return hdr

static func encode_packet(hdr: Header, payload: PackedByteArray) -> PackedByteArray:
	hdr.payload_length = payload.size()
	hdr.payload_checksum = calculate_checksum(payload)
	var header_bytes = encode_header(hdr)
	var full = PackedByteArray()
	full.append_array(header_bytes)
	full.append_array(payload)
	return full

# =============================================================================
# PAYLOAD SERIALIZERS
# =============================================================================

static func encode_hello(client_version: String = "1.0", auth_token: String = "") -> PackedByteArray:
	var sp = StreamPeerBuffer.new()
	sp.big_endian = false
	var v_bytes = client_version.to_utf8_buffer()
	var t_bytes = auth_token.to_utf8_buffer()

	sp.put_u8(v_bytes.size())
	sp.put_data(v_bytes)
	sp.put_u16(t_bytes.size())
	sp.put_data(t_bytes)
	return sp.data_array

static func decode_welcome(payload: PackedByteArray) -> Dictionary:
	if payload.size() < 16:
		return {}
	var sp = StreamPeerBuffer.new()
	sp.big_endian = false
	sp.data_array = payload

	return {
		"session_id": sp.get_u32(),
		"player_entity_id": sp.get_u32(),
		"server_tick": sp.get_u32(),
		"server_time": sp.get_u32()
	}

static func encode_input(tick: int, pos: Vector3, yaw: float, pitch: float, vel: Vector3, flags: int) -> PackedByteArray:
	var sp = StreamPeerBuffer.new()
	sp.big_endian = false
	sp.data_array = PackedByteArray()
	sp.data_array.resize(38)

	sp.put_u32(tick)
	sp.put_float(pos.x)
	sp.put_float(pos.y)
	sp.put_float(pos.z)
	sp.put_float(yaw)
	sp.put_float(pitch)
	sp.put_float(vel.x)
	sp.put_float(vel.y)
	sp.put_float(vel.z)
	sp.put_u8(flags)
	sp.put_u8(0) # Padding
	return sp.data_array

static func decode_snapshot(payload: PackedByteArray) -> Dictionary:
	if payload.size() < 10:
		return {}

	var sp = StreamPeerBuffer.new()
	sp.big_endian = false
	sp.data_array = payload

	var server_tick = sp.get_u32()
	var server_time = sp.get_u32()
	var count = sp.get_u16()

	var entities: Array[EntityRecord] = []
	for i in range(count):
		if sp.get_position() + 38 > payload.size():
			break
		var rec = EntityRecord.new()
		rec.entity_id = sp.get_u32()
		rec.entity_type = sp.get_u8()
		rec.flags = sp.get_u8()
		rec.position = Vector3(sp.get_float(), sp.get_float(), sp.get_float())
		rec.yaw = sp.get_float()
		rec.pitch = sp.get_float()
		rec.velocity = Vector3(sp.get_float(), sp.get_float(), sp.get_float())
		entities.append(rec)

	return {
		"server_tick": server_tick,
		"server_time": server_time,
		"entities": entities
	}

static func encode_ping(ping_id: int, timestamp: int) -> PackedByteArray:
	var sp = StreamPeerBuffer.new()
	sp.big_endian = false
	sp.put_u32(ping_id)
	sp.put_u32(timestamp)
	return sp.data_array

static func decode_pong(payload: PackedByteArray) -> Dictionary:
	if payload.size() < 8:
		return {}
	var sp = StreamPeerBuffer.new()
	sp.big_endian = false
	sp.data_array = payload
	return {
		"ping_id": sp.get_u32(),
		"timestamp": sp.get_u32()
	}

static func encode_goodbye(reason: int = 0) -> PackedByteArray:
	var sp = StreamPeerBuffer.new()
	sp.big_endian = false
	sp.put_u16(reason)
	return sp.data_array

static func encode_chat(channel: int, message: String) -> PackedByteArray:
	var sp = StreamPeerBuffer.new()
	sp.big_endian = false
	var m_bytes = message.to_utf8_buffer()
	sp.put_u8(channel)
	sp.put_u32(0) # sender_id (el servidor lo asigna)
	sp.put_u16(m_bytes.size())
	sp.put_data(m_bytes)
	return sp.data_array

static func decode_chat(payload: PackedByteArray) -> Dictionary:
	if payload.size() < 7:
		return {}
	var sp = StreamPeerBuffer.new()
	sp.big_endian = false
	sp.data_array = payload
	var channel = sp.get_u8()
	var sender_id = sp.get_u32()
	var msg_len = sp.get_u16()
	var msg = ""
	if msg_len > 0 and sp.get_position() + msg_len <= payload.size():
		var data_res = sp.get_data(msg_len)
		if data_res[0] == OK:
			msg = data_res[1].get_string_from_utf8()
	return {
		"channel": channel,
		"sender_id": sender_id,
		"message": msg
	}
