class_name PlayerNetworkSync
extends Node

## Módulo de Sincronización y Red Multijugador para Tecate Simulator
## Implementa paquetes de estado cuantizados (24 bytes), predicción en cliente
## con búfer circular de 120 ticks, reconciliación con el servidor e interpolación
## Hermite Spline para entidades remotas (otros jugadores en la ciudad).

class PlayerInputPacket:
	var sequence_number: int = 0
	var timestamp: float = 0.0
	var move_vector: Vector2 = Vector2.ZERO
	var look_yaw: float = 0.0
	var look_pitch: float = 0.0
	var is_sprinting: bool = false
	var is_jumping: bool = false

class PlayerStateSnapshot:
	var tick: int = 0
	var timestamp: float = 0.0
	var position: Vector3 = Vector3.ZERO
	var velocity: Vector3 = Vector3.ZERO
	var yaw: float = 0.0
	var pitch: float = 0.0
	var flags: int = 0 # 1=Grounded, 2=Sprinting, 4=InAir, 8=Sliding

const BUFFER_CAPACITY: int = 120
const ERROR_RECONCILIATION_THRESHOLD: float = 0.04 # 4 centímetros

var is_local_authority: bool = true
var current_tick: int = 0

# Búfer circular de predicción de estados locales
var history_snapshots: Array = []
var history_inputs: Array = []

# Búfer de interpolación para jugadores remotos
var remote_snapshots: Array = []
var interpolation_delay: float = 0.10 # 100 ms de interpolación suave

func _init():
	history_snapshots.resize(BUFFER_CAPACITY)
	history_inputs.resize(BUFFER_CAPACITY)

# =============================================================================
# SERIALIZACIÓN / DESERIALIZACIÓN CUANTIZADA (24 BYTES)
# =============================================================================

static func serialize_snapshot(s: PlayerStateSnapshot) -> PackedByteArray:
	var buf = PackedByteArray()
	buf.resize(24)
	var sp = StreamPeerBuffer.new()
	sp.data_array = buf
	
	sp.put_u32(s.tick)
	sp.put_float(s.position.x)
	sp.put_float(s.position.y)
	sp.put_float(s.position.z)
	
	# Cuantización de ángulos a 16 bits
	var quant_yaw = int((fposmod(s.yaw, 360.0) / 360.0) * 65535.0) & 0xFFFF
	var quant_pitch = int(clampf((s.pitch + 90.0) / 180.0, 0.0, 1.0) * 65535.0) & 0xFFFF
	sp.put_u16(quant_yaw)
	sp.put_u16(quant_pitch)
	
	# Cuantización de velocidades horizontal y vertical
	var h_spd = Vector2(s.velocity.x, s.velocity.z).length()
	var quant_h_spd = int(clampf(h_spd / 30.0, 0.0, 1.0) * 255.0) & 0xFF
	var quant_v_spd = int(clampf((s.velocity.y + 20.0) / 40.0, 0.0, 1.0) * 255.0) & 0xFF
	sp.put_u8(quant_h_spd)
	sp.put_u8(quant_v_spd)
	
	sp.put_u8(s.flags & 0xFF)
	sp.put_u8(0) # Padding
	
	return sp.data_array

static func deserialize_snapshot(bytes: PackedByteArray) -> PlayerStateSnapshot:
	if bytes.size() < 24:
		return null
	var sp = StreamPeerBuffer.new()
	sp.data_array = bytes
	
	var s = PlayerStateSnapshot.new()
	s.tick = sp.get_u32()
	s.position.x = sp.get_float()
	s.position.y = sp.get_float()
	s.position.z = sp.get_float()
	
	var quant_yaw = sp.get_u16()
	var quant_pitch = sp.get_u16()
	s.yaw = (float(quant_yaw) / 65535.0) * 360.0
	s.pitch = ((float(quant_pitch) / 65535.0) * 180.0) - 90.0
	
	var quant_h_spd = sp.get_u8()
	var quant_v_spd = sp.get_u8()
	var h_spd = (float(quant_h_spd) / 255.0) * 30.0
	var v_spd = ((float(quant_v_spd) / 255.0) * 40.0) - 20.0
	
	# Reconstrucción de vector de velocidad
	var rad_yaw = deg_to_rad(s.yaw)
	s.velocity = Vector3(-sin(rad_yaw) * h_spd, v_spd, -cos(rad_yaw) * h_spd)
	
	s.flags = sp.get_u8()
	return s

# =============================================================================
# PREDICCIÓN Y RECONCILIACIÓN EN CLIENTE LOCAL
# =============================================================================

func record_local_state(tick: int, snap: PlayerStateSnapshot, input: PlayerInputPacket) -> void:
	var idx = tick % BUFFER_CAPACITY
	history_snapshots[idx] = snap
	history_inputs[idx] = input
	current_tick = tick

func check_server_reconciliation(server_snap: PlayerStateSnapshot) -> bool:
	"""Compara el estado autorizado del servidor con la predicción local.
	Devuelve true si hubo divergencia que amerita corrección (rollback)."""
	var idx = server_snap.tick % BUFFER_CAPACITY
	var predicted = history_snapshots[idx]
	if predicted == null or predicted.tick != server_snap.tick:
		return false
	
	var dist = predicted.position.distance_to(server_snap.position)
	return dist > ERROR_RECONCILIATION_THRESHOLD

# =============================================================================
# INTERPOLACIÓN HERMITE PARA ENTIDADES REMOTAS
# =============================================================================

func push_remote_snapshot(snap: PlayerStateSnapshot) -> void:
	remote_snapshots.append(snap)
	if remote_snapshots.size() > 30:
		remote_snapshots.pop_front()

func sample_remote_state(render_time: float) -> Dictionary:
	"""Calcula la posición y rotación interpolada para un jugador remoto
	usando cubic/Hermite spline entre los dos snapshots más cercanos."""
	if remote_snapshots.size() == 0:
		return {}
	if remote_snapshots.size() == 1:
		var s0 = remote_snapshots[0]
		return {"position": s0.position, "yaw": s0.yaw, "pitch": s0.pitch, "velocity": s0.velocity}
	
	var target_time = render_time - interpolation_delay
	var s_prev = remote_snapshots[0]
	var s_next = remote_snapshots[-1]
	
	for i in range(remote_snapshots.size() - 1):
		if remote_snapshots[i].timestamp <= target_time and remote_snapshots[i + 1].timestamp >= target_time:
			s_prev = remote_snapshots[i]
			s_next = remote_snapshots[i + 1]
			break
	
	var dt = s_next.timestamp - s_prev.timestamp
	var t = 0.0
	if dt > 0.0001:
		t = clampf((target_time - s_prev.timestamp) / dt, 0.0, 1.0)
	
	# Interpolación cúbica Hermite con conservación de velocidad
	var p0 = s_prev.position
	var p1 = s_next.position
	var v0 = s_prev.velocity * dt
	var v1 = s_next.velocity * dt
	
	var t2 = t * t
	var t3 = t2 * t
	var h00 = 2.0 * t3 - 3.0 * t2 + 1.0
	var h10 = t3 - 2.0 * t2 + t
	var h01 = -2.0 * t3 + 3.0 * t2
	var h11 = t3 - t2
	var inter_pos = h00 * p0 + h10 * v0 + h01 * p1 + h11 * v1
	
	var inter_yaw = lerp_angle(deg_to_rad(s_prev.yaw), deg_to_rad(s_next.yaw), t)
	var inter_pitch = lerpf(s_prev.pitch, s_next.pitch, t)
	var inter_vel = s_prev.velocity.lerp(s_next.velocity, t)
	
	return {
		"position": inter_pos,
		"yaw": rad_to_deg(inter_yaw),
		"pitch": inter_pitch,
		"velocity": inter_vel
	}
