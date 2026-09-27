class_name RemotePlayer
extends Node3D

## Representación visual y cinemática interpolada de un jugador remoto en Tecate Simulator.
## Utiliza el modelo rigged humanoid_player.glb y animación procedural biomecánica.

@export var interpolation_delay: float = 0.10 # 100 ms de búfer de interpolación

var entity_id: int = 0
var snapshot_history: Array[Dictionary] = []
var locomotion_phase: float = 0.0

# Nodos del avatar 3D
var avatar_scene: Node3D
var skeleton: Skeleton3D
var nameplate_label: Label3D

# Huesos biomecánicos
var bone_upperarm_l: int = -1
var bone_upperarm_r: int = -1
var bone_forearm_l: int = -1
var bone_forearm_r: int = -1
var bone_upperleg_l: int = -1
var bone_upperleg_r: int = -1
var bone_lowerleg_l: int = -1
var bone_lowerleg_r: int = -1

var _base_rot_upperarm_l: Quaternion = Quaternion.IDENTITY
var _base_rot_upperarm_r: Quaternion = Quaternion.IDENTITY
var _base_rot_forearm_l: Quaternion = Quaternion.IDENTITY
var _base_rot_forearm_r: Quaternion = Quaternion.IDENTITY
var _base_rot_upperleg_l: Quaternion = Quaternion.IDENTITY
var _base_rot_upperleg_r: Quaternion = Quaternion.IDENTITY
var _base_rot_lowerleg_l: Quaternion = Quaternion.IDENTITY
var _base_rot_lowerleg_r: Quaternion = Quaternion.IDENTITY

func setup(id: int) -> void:
	entity_id = id
	name = "RemotePlayer_%d" % id
	_create_nameplate()
	_initialize_avatar()

func _create_nameplate() -> void:
	nameplate_label = Label3D.new()
	nameplate_label.name = "Nameplate"
	nameplate_label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	nameplate_label.position = Vector3(0, 2.15, 0)
	nameplate_label.pixel_size = 0.005
	nameplate_label.text = "Jugador #%d" % entity_id
	nameplate_label.modulate = Color(1.0, 0.9, 0.4, 1.0)
	nameplate_label.outline_render_priority = 1
	nameplate_label.outline_size = 4
	nameplate_label.outline_modulate = Color(0, 0, 0, 0.85)

	var din_font = load("res://assets/fonts/DIN_Condensed_Bold.ttf")
	if din_font:
		nameplate_label.font = din_font
	add_child(nameplate_label)

func _initialize_avatar() -> void:
	var avatar_res = load("res://assets/characters/humanoid_player.glb")
	if not avatar_res:
		push_error("[RemotePlayer] No se pudo cargar res://assets/characters/humanoid_player.glb")
		return

	avatar_scene = avatar_res.instantiate() as Node3D
	avatar_scene.name = "Avatar"
	add_child(avatar_scene)

	skeleton = avatar_scene.find_child("Skeleton3D", true, false) as Skeleton3D
	if skeleton:
		bone_upperarm_l = skeleton.find_bone("UpperArm.L")
		bone_upperarm_r = skeleton.find_bone("UpperArm.R")
		bone_forearm_l = skeleton.find_bone("Forearm.L")
		bone_forearm_r = skeleton.find_bone("Forearm.R")
		bone_upperleg_l = skeleton.find_bone("UpperLeg.L")
		bone_upperleg_r = skeleton.find_bone("UpperLeg.R")
		bone_lowerleg_l = skeleton.find_bone("LowerLeg.L")
		bone_lowerleg_r = skeleton.find_bone("LowerLeg.R")

		if bone_upperarm_l != -1: _base_rot_upperarm_l = skeleton.get_bone_pose_rotation(bone_upperarm_l)
		if bone_upperarm_r != -1: _base_rot_upperarm_r = skeleton.get_bone_pose_rotation(bone_upperarm_r)
		if bone_forearm_l != -1: _base_rot_forearm_l = skeleton.get_bone_pose_rotation(bone_forearm_l)
		if bone_forearm_r != -1: _base_rot_forearm_r = skeleton.get_bone_pose_rotation(bone_forearm_r)
		if bone_upperleg_l != -1: _base_rot_upperleg_l = skeleton.get_bone_pose_rotation(bone_upperleg_l)
		if bone_upperleg_r != -1: _base_rot_upperleg_r = skeleton.get_bone_pose_rotation(bone_upperleg_r)
		if bone_lowerleg_l != -1: _base_rot_lowerleg_l = skeleton.get_bone_pose_rotation(bone_lowerleg_l)
		if bone_lowerleg_r != -1: _base_rot_lowerleg_r = skeleton.get_bone_pose_rotation(bone_lowerleg_r)

func push_snapshot_record(rec: TKTCodec.EntityRecord, server_time_ms: int) -> void:
	var snap = {
		"time": float(server_time_ms) / 1000.0,
		"position": rec.position,
		"yaw": rec.yaw,
		"pitch": rec.pitch,
		"velocity": rec.velocity,
		"flags": rec.flags
	}
	snapshot_history.append(snap)
	if snapshot_history.size() > 30:
		snapshot_history.pop_front()

func _process(delta: float) -> void:
	if snapshot_history.is_empty():
		return

	var current_time = float(Time.get_ticks_msec()) / 1000.0
	var interp_state = _sample_interpolated_state(current_time)
	if interp_state.is_empty():
		return

	global_position = interp_state["position"]
	rotation_degrees.y = interp_state["yaw"]

	_update_procedural_locomotion(delta, interp_state["velocity"])

func _sample_interpolated_state(current_time: float) -> Dictionary:
	if snapshot_history.size() == 1:
		var s0 = snapshot_history[0]
		return {
			"position": s0["position"],
			"yaw": s0["yaw"],
			"pitch": s0["pitch"],
			"velocity": s0["velocity"]
		}

	var target_time = current_time - interpolation_delay
	var s_prev = snapshot_history[0]
	var s_next = snapshot_history[-1]

	for i in range(snapshot_history.size() - 1):
		if snapshot_history[i]["time"] <= target_time and snapshot_history[i + 1]["time"] >= target_time:
			s_prev = snapshot_history[i]
			s_next = snapshot_history[i + 1]
			break

	var dt = s_next["time"] - s_prev["time"]
	var t = 0.0
	if dt > 0.0001:
		t = clampf((target_time - s_prev["time"]) / dt, 0.0, 1.0)

	# Interpolación cúbica Hermite conservando derivadas de velocidad
	var p0 = s_prev["position"]
	var p1 = s_next["position"]
	var v0 = s_prev["velocity"] * dt
	var v1 = s_next["velocity"] * dt

	var t2 = t * t
	var t3 = t2 * t
	var h00 = 2.0 * t3 - 3.0 * t2 + 1.0
	var h10 = t3 - 2.0 * t2 + t
	var h01 = -2.0 * t3 + 3.0 * t2
	var h11 = t3 - t2
	var inter_pos = h00 * p0 + h10 * v0 + h01 * p1 + h11 * v1

	var inter_yaw = lerp_angle(deg_to_rad(s_prev["yaw"]), deg_to_rad(s_next["yaw"]), t)
	var inter_pitch = lerpf(s_prev["pitch"], s_next["pitch"], t)
	var inter_vel = s_prev["velocity"].lerp(s_next["velocity"], t)

	return {
		"position": inter_pos,
		"yaw": rad_to_deg(inter_yaw),
		"pitch": inter_pitch,
		"velocity": inter_vel
	}

func _update_procedural_locomotion(delta: float, vel: Vector3) -> void:
	if not skeleton:
		return

	var h_speed = Vector2(vel.x, vel.z).length()
	var is_moving = h_speed > 0.1

	if is_moving:
		locomotion_phase += h_speed * 3.8 * delta
	else:
		locomotion_phase = lerp_angle(locomotion_phase, 0.0, 8.0 * delta)

	var speed_ratio = clampf(h_speed / 6.2, 0.0, 1.0)
	var arm_amplitude = speed_ratio * 0.45
	var leg_amplitude = speed_ratio * 0.50

	var arm_angle_l = sin(locomotion_phase) * arm_amplitude
	var arm_angle_r = -sin(locomotion_phase) * arm_amplitude
	var leg_angle_l = -sin(locomotion_phase) * leg_amplitude
	var leg_angle_r = sin(locomotion_phase) * leg_amplitude

	var elbow_flex_l = maxf(0.0, sin(locomotion_phase)) * arm_amplitude * 0.55
	var elbow_flex_r = maxf(0.0, -sin(locomotion_phase)) * arm_amplitude * 0.55
	var knee_flex_l = maxf(0.0, -sin(locomotion_phase)) * leg_amplitude * 0.85
	var knee_flex_r = maxf(0.0, sin(locomotion_phase)) * leg_amplitude * 0.85

	if bone_upperarm_l != -1:
		skeleton.set_bone_pose_rotation(bone_upperarm_l, _base_rot_upperarm_l * Quaternion(Vector3(1, 0, 0), arm_angle_l))
	if bone_upperarm_r != -1:
		skeleton.set_bone_pose_rotation(bone_upperarm_r, _base_rot_upperarm_r * Quaternion(Vector3(1, 0, 0), arm_angle_r))
	if bone_forearm_l != -1:
		skeleton.set_bone_pose_rotation(bone_forearm_l, _base_rot_forearm_l * Quaternion(Vector3(1, 0, 0), elbow_flex_l))
	if bone_forearm_r != -1:
		skeleton.set_bone_pose_rotation(bone_forearm_r, _base_rot_forearm_r * Quaternion(Vector3(1, 0, 0), elbow_flex_r))
	if bone_upperleg_l != -1:
		skeleton.set_bone_pose_rotation(bone_upperleg_l, _base_rot_upperleg_l * Quaternion(Vector3(1, 0, 0), leg_angle_l))
	if bone_upperleg_r != -1:
		skeleton.set_bone_pose_rotation(bone_upperleg_r, _base_rot_upperleg_r * Quaternion(Vector3(1, 0, 0), leg_angle_r))
	if bone_lowerleg_l != -1:
		skeleton.set_bone_pose_rotation(bone_lowerleg_l, _base_rot_lowerleg_l * Quaternion(Vector3(1, 0, 0), -knee_flex_l))
	if bone_lowerleg_r != -1:
		skeleton.set_bone_pose_rotation(bone_lowerleg_r, _base_rot_lowerleg_r * Quaternion(Vector3(1, 0, 0), -knee_flex_r))
