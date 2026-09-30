class_name RemoteNPC
extends Node3D

## Representación visual e interpolada de un NPC o agente peatonal coordinado por el servidor TKT/1.

@export var interpolation_delay: float = 0.10

var entity_id: int = 0
var snapshot_history: Array[Dictionary] = []
var locomotion_phase: float = 0.0

var avatar_scene: Node3D
var skeleton: Skeleton3D
var nameplate_label: Label3D

# Huesos para animación procedural sencilla
var bone_upperleg_l: int = -1
var bone_upperleg_r: int = -1
var bone_upperarm_l: int = -1
var bone_upperarm_r: int = -1

var _base_rot_upperleg_l: Quaternion = Quaternion.IDENTITY
var _base_rot_upperleg_r: Quaternion = Quaternion.IDENTITY
var _base_rot_upperarm_l: Quaternion = Quaternion.IDENTITY
var _base_rot_upperarm_r: Quaternion = Quaternion.IDENTITY

func setup(id: int, npc_name: String = "") -> void:
	entity_id = id
	name = "RemoteNPC_%d" % id
	_create_nameplate(npc_name)
	_initialize_avatar()

func _create_nameplate(npc_name: String) -> void:
	nameplate_label = Label3D.new()
	nameplate_label.name = "Nameplate"
	nameplate_label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	nameplate_label.position = Vector3(0, 2.15, 0)
	nameplate_label.pixel_size = 0.005
	nameplate_label.text = npc_name if not npc_name.is_empty() else ("Ciudadano #%d" % entity_id)
	nameplate_label.modulate = Color(0.45, 1.0, 0.65, 1.0) # Verde cívico Tecate
	nameplate_label.outline_render_priority = 1
	nameplate_label.outline_size = 4
	nameplate_label.outline_modulate = Color(0, 0, 0, 0.85)

	var din_font = load("res://assets/fonts/DIN_Condensed_Bold.ttf")
	if din_font:
		nameplate_label.font = din_font
	add_child(nameplate_label)

func _initialize_avatar() -> void:
	var glb = load("res://assets/humanoid_player.glb")
	if glb:
		avatar_scene = glb.instantiate() as Node3D
		add_child(avatar_scene)
		skeleton = avatar_scene.find_child("GeneralSkeleton", true, false) as Skeleton3D
		if skeleton:
			bone_upperleg_l = skeleton.find_bone("DEF-thigh.L")
			bone_upperleg_r = skeleton.find_bone("DEF-thigh.R")
			bone_upperarm_l = skeleton.find_bone("DEF-upper_arm.L")
			bone_upperarm_r = skeleton.find_bone("DEF-upper_arm.R")
			if bone_upperleg_l != -1: _base_rot_upperleg_l = skeleton.get_bone_pose_rotation(bone_upperleg_l)
			if bone_upperleg_r != -1: _base_rot_upperleg_r = skeleton.get_bone_pose_rotation(bone_upperleg_r)
			if bone_upperarm_l != -1: _base_rot_upperarm_l = skeleton.get_bone_pose_rotation(bone_upperarm_l)
			if bone_upperarm_r != -1: _base_rot_upperarm_r = skeleton.get_bone_pose_rotation(bone_upperarm_r)
	else:
		# Malla básica de respaldo
		var mesh_inst = MeshInstance3D.new()
		var capsule = CapsuleMesh.new()
		capsule.radius = 0.35
		capsule.height = 1.75
		mesh_inst.mesh = capsule
		mesh_inst.position = Vector3(0, 0.88, 0)
		add_child(mesh_inst)

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

func _physics_process(delta: float) -> void:
	if snapshot_history.size() < 2:
		if snapshot_history.size() == 1:
			_set_pos(snapshot_history[0]["position"])
			rotation.y = deg_to_rad(snapshot_history[0]["yaw"])
		return

	var render_time = (Time.get_ticks_msec() / 1000.0) - interpolation_delay
	var prev_idx = -1
	var next_idx = -1

	for i in range(snapshot_history.size() - 1):
		if snapshot_history[i]["time"] <= render_time and snapshot_history[i + 1]["time"] >= render_time:
			prev_idx = i
			next_idx = i + 1
			break

	var cur_vel = Vector3.ZERO
	if prev_idx != -1 and next_idx != -1:
		var s0 = snapshot_history[prev_idx]
		var s1 = snapshot_history[next_idx]
		var span = max(0.0001, s1["time"] - s0["time"])
		var t = clampf((render_time - s0["time"]) / span, 0.0, 1.0)
		_set_pos(s0["position"].lerp(s1["position"], t))
		rotation.y = lerp_angle(deg_to_rad(s0["yaw"]), deg_to_rad(s1["yaw"]), t)
		cur_vel = s0["velocity"].lerp(s1["velocity"], t)
	else:
		var latest = snapshot_history.back()
		var current_p = global_position if is_inside_tree() else position
		_set_pos(current_p.lerp(latest["position"], delta * 15.0))
		rotation.y = lerp_angle(rotation.y, deg_to_rad(latest["yaw"]), delta * 15.0)
		cur_vel = latest["velocity"]

	# Animación biomecánica simple de caminado
	var speed = cur_vel.length()
	if speed > 0.1 and skeleton:
		locomotion_phase += speed * delta * 4.5
		var leg_angle = sin(locomotion_phase) * deg_to_rad(28.0)
		var arm_angle = -sin(locomotion_phase) * deg_to_rad(20.0)
		if bone_upperleg_l != -1:
			skeleton.set_bone_pose_rotation(bone_upperleg_l, _base_rot_upperleg_l * Quaternion(Vector3.RIGHT, leg_angle))
		if bone_upperleg_r != -1:
			skeleton.set_bone_pose_rotation(bone_upperleg_r, _base_rot_upperleg_r * Quaternion(Vector3.RIGHT, -leg_angle))
		if bone_upperarm_l != -1:
			skeleton.set_bone_pose_rotation(bone_upperarm_l, _base_rot_upperarm_l * Quaternion(Vector3.RIGHT, arm_angle))
		if bone_upperarm_r != -1:
			skeleton.set_bone_pose_rotation(bone_upperarm_r, _base_rot_upperarm_r * Quaternion(Vector3.RIGHT, -arm_angle))

func _set_pos(pos: Vector3) -> void:
	if is_inside_tree():
		global_position = pos
	else:
		position = pos
