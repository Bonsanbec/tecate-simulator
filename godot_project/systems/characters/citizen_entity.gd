class_name CitizenEntity
extends CharacterBody3D

## Entidad Universal Humanoide / Ciudadana para Tecate Simulator
## Define el cuerpo físico rígido (CharacterBody3D con cápsula antropométrica),
## el rig 3D antropométrico (Skeleton3D y mallas de cuerpo/cabeza), el ciclo
## biomecánico de locomoción procedural, la etiqueta diegética Nameplate y el
## subsistema de replicación e interpolación Hermite para entidades coordinadas
## por el servidor TKT/1.
##
## Tanto el jugador local (a través de PlayerController) como los ciudadanos
## autónomos y los jugadores remotos son instancias de esta misma entidad.

const CitizenProfileClass = preload("res://systems/characters/citizen_profile.gd")

# Identidad y estado de control
@export var entity_id: int = 0
@export var citizen_name: String = ""
@export var is_locally_controlled: bool = false
@export var identity_id: String = "axel"
@export var profile: Resource = null

# Parámetros antropométricos y físicos de Tecate
@export var mass_kg: float = 75.0
@export var capsule_radius: float = 0.25
@export var capsule_height: float = 1.75
const DEFAULT_SNAP_LENGTH: float = 0.30

# Replicación e interpolación de red (para entidades gobernadas por el servidor)
@export var interpolation_delay: float = 0.10 # 100 ms de búfer
var snapshot_history: Array[Dictionary] = []

# Nodos del avatar 3D rigged
var humanoid_scene: Node3D
var skeleton: Skeleton3D
var mesh_body: MeshInstance3D
var mesh_head: MeshInstance3D
var mesh_props: MeshInstance3D
var collision_shape: CollisionShape3D
var nameplate_label: Label3D

# Huesos para animación procedural (brazos, manos, piernas, columna)
var bone_upperarm_l: int = -1
var bone_upperarm_r: int = -1
var bone_forearm_l: int = -1
var bone_forearm_r: int = -1
var bone_upperleg_l: int = -1
var bone_upperleg_r: int = -1
var bone_lowerleg_l: int = -1
var bone_lowerleg_r: int = -1
var bone_chest: int = -1

# Rotaciones base de reposo de cada hueso para composición canónica
var _base_rot_upperarm_l: Quaternion = Quaternion.IDENTITY
var _base_rot_upperarm_r: Quaternion = Quaternion.IDENTITY
var _base_rot_forearm_l: Quaternion = Quaternion.IDENTITY
var _base_rot_forearm_r: Quaternion = Quaternion.IDENTITY
var _base_rot_upperleg_l: Quaternion = Quaternion.IDENTITY
var _base_rot_upperleg_r: Quaternion = Quaternion.IDENTITY
var _base_rot_lowerleg_l: Quaternion = Quaternion.IDENTITY
var _base_rot_lowerleg_r: Quaternion = Quaternion.IDENTITY
var _base_rot_chest: Quaternion = Quaternion.IDENTITY

# Ciclo de locomoción biomecánico de extremidades
var locomotion_phase: float = 0.0

# Asientos
var current_seat_node: Node = null

func _ready() -> void:
	_setup_physics_properties()
	_ensure_collision_shape()
	_initialize_humanoid_rig()
	_create_nameplate()

func setup(id: int, is_npc: bool = true, display_name: String = "") -> void:
	entity_id = id
	citizen_name = display_name if not display_name.is_empty() else (("Ciudadano #%d" if is_npc else "Jugador #%d") % id)
	name = ("Citizen_%d" if is_npc else "RemotePlayer_%d") % id

	_setup_physics_properties()
	_ensure_collision_shape()
	_initialize_humanoid_rig()
	_create_nameplate()

	if nameplate_label:
		nameplate_label.text = citizen_name
		if is_npc:
			nameplate_label.modulate = Color(0.45, 1.0, 0.65, 1.0) # Verde cívico Tecate
		else:
			nameplate_label.modulate = Color(1.0, 0.9, 0.4, 1.0) # Amarillo cálido jugador

func _setup_physics_properties() -> void:
	collision_layer = 1
	collision_mask = 1
	set_collision_layer_value(1, true)
	set_collision_mask_value(1, true)
	safe_margin = 0.02
	floor_max_angle = deg_to_rad(65.0)
	floor_constant_speed = true
	floor_stop_on_slope = true
	floor_block_on_wall = true
	floor_snap_length = DEFAULT_SNAP_LENGTH

func _ensure_collision_shape() -> void:
	# Localizar colisionador existente o crear la cápsula canónica
	collision_shape = get_node_or_null("CollisionShape3D") as CollisionShape3D
	if not collision_shape:
		collision_shape = CollisionShape3D.new()
		collision_shape.name = "CollisionShape3D"
		var capsule = CapsuleShape3D.new()
		capsule.radius = capsule_radius
		capsule.height = capsule_height
		collision_shape.shape = capsule
		collision_shape.position = Vector3(0, capsule_height * 0.5, 0)
		add_child(collision_shape)

func _initialize_humanoid_rig() -> void:
	# Si ya existe el avatar, no reinstanciar
	if humanoid_scene:
		return

	# Resolver ruta del modelo según perfil o identidad
	var model_path: String = "res://assets/characters/citizens/axel.glb"
	if profile and not profile.model_path.is_empty():
		model_path = profile.model_path
	elif not identity_id.is_empty():
		var candidate = "res://assets/characters/citizens/%s.glb" % identity_id.to_lower()
		if ResourceLoader.exists(candidate):
			model_path = candidate
		elif ResourceLoader.exists("res://assets/characters/citizens/axel.glb"):
			model_path = "res://assets/characters/citizens/axel.glb"
		else:
			model_path = "res://assets/characters/humanoid_player.glb"

	var model_res = load(model_path)
	if not model_res:
		model_res = load("res://assets/characters/humanoid_player.glb")
	if not model_res:
		push_error("[CitizenEntity] No se encontró el modelo humanoide en %s" % model_path)
		return

	humanoid_scene = model_res.instantiate() as Node3D
	humanoid_scene.name = "HumanoidAvatar"
	add_child(humanoid_scene)

	skeleton = humanoid_scene.find_child("Skeleton3D", true, false) as Skeleton3D
	mesh_body = humanoid_scene.find_child("Player_Body_Mesh", true, false) as MeshInstance3D
	mesh_head = humanoid_scene.find_child("Player_Head_Mesh", true, false) as MeshInstance3D
	mesh_props = humanoid_scene.find_child("Player_Props_Mesh", true, false) as MeshInstance3D

	# Configurar capas visuales:
	# Capa 1: Renderizado general (cuerpo, accesorios y cabezas de ciudadanos/NPCs)
	# Capa 2: Exclusiva para la cabeza del avatar local (culling en 1P para evitar clipping facial)
	if mesh_body:
		mesh_body.layers = 1
	if mesh_head:
		mesh_head.layers = 2 if is_locally_controlled else 1
		_apply_skin_subsurface_scattering(mesh_head)
	if mesh_props:
		mesh_props.layers = 1

	if skeleton:
		bone_upperarm_l = skeleton.find_bone("UpperArm.L")
		bone_upperarm_r = skeleton.find_bone("UpperArm.R")
		bone_forearm_l = skeleton.find_bone("Forearm.L")
		bone_forearm_r = skeleton.find_bone("Forearm.R")
		bone_upperleg_l = skeleton.find_bone("UpperLeg.L")
		bone_upperleg_r = skeleton.find_bone("UpperLeg.R")
		bone_lowerleg_l = skeleton.find_bone("LowerLeg.L")
		bone_lowerleg_r = skeleton.find_bone("LowerLeg.R")
		bone_chest = skeleton.find_bone("Chest")

		if bone_upperarm_l != -1: _base_rot_upperarm_l = skeleton.get_bone_pose_rotation(bone_upperarm_l)
		if bone_upperarm_r != -1: _base_rot_upperarm_r = skeleton.get_bone_pose_rotation(bone_upperarm_r)
		if bone_forearm_l != -1: _base_rot_forearm_l = skeleton.get_bone_pose_rotation(bone_forearm_l)
		if bone_forearm_r != -1: _base_rot_forearm_r = skeleton.get_bone_pose_rotation(bone_forearm_r)
		if bone_upperleg_l != -1: _base_rot_upperleg_l = skeleton.get_bone_pose_rotation(bone_upperleg_l)
		if bone_upperleg_r != -1: _base_rot_upperleg_r = skeleton.get_bone_pose_rotation(bone_upperleg_r)
		if bone_lowerleg_l != -1: _base_rot_lowerleg_l = skeleton.get_bone_pose_rotation(bone_lowerleg_l)
		if bone_lowerleg_r != -1: _base_rot_lowerleg_r = skeleton.get_bone_pose_rotation(bone_lowerleg_r)
		if bone_chest != -1: _base_rot_chest = skeleton.get_bone_pose_rotation(bone_chest)

func apply_identity(p_id: String) -> void:
	identity_id = p_id
	if humanoid_scene:
		humanoid_scene.queue_free()
		humanoid_scene = null
		skeleton = null
		mesh_body = null
		mesh_head = null
		mesh_props = null
	_initialize_humanoid_rig()

func _apply_skin_subsurface_scattering(head_node: MeshInstance3D) -> void:
	if not head_node:
		return
	var mat_count = head_node.get_surface_override_material_count()
	for s_idx in range(max(1, mat_count)):
		var mat = head_node.get_active_material(s_idx)
		if mat is StandardMaterial3D and ("Skin" in mat.resource_name or s_idx == 0):
			var sss_mat = mat.duplicate() as StandardMaterial3D
			sss_mat.subsurf_scatter_strength = 0.32
			sss_mat.subsurf_scatter_skin_mode = true
			sss_mat.subsurf_scatter_transmittance_color = Color(0.92, 0.45, 0.35, 1.0)
			head_node.set_surface_override_material(s_idx, sss_mat)

func _create_nameplate() -> void:
	if nameplate_label:
		return

	nameplate_label = Label3D.new()
	nameplate_label.name = "Nameplate"
	nameplate_label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	nameplate_label.position = Vector3(0, 2.15, 0)
	nameplate_label.pixel_size = 0.005
	nameplate_label.text = citizen_name if not citizen_name.is_empty() else ("Ciudadano #%d" % entity_id)
	nameplate_label.modulate = Color(0.45, 1.0, 0.65, 1.0)
	nameplate_label.outline_render_priority = 1
	nameplate_label.outline_size = 4
	nameplate_label.outline_modulate = Color(0, 0, 0, 0.85)

	var din_font = load("res://assets/fonts/DIN_Condensed_Bold.ttf")
	if din_font:
		nameplate_label.font = din_font
	add_child(nameplate_label)

	# Si es el jugador local, ocultar nameplate en visión subjetiva
	if is_locally_controlled:
		nameplate_label.visible = false

# =============================================================================
# REPLICACIÓN E INTERPOLACIÓN DE RED (PARA ENTIDADES REMOTAS Y AUTÓNOMAS)
# =============================================================================

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
	# Si la entidad es controlada localmente por el jugador, PlayerController
	# maneja su propio bucle de física con inputs periféricos.
	if is_locally_controlled:
		return

	if snapshot_history.is_empty():
		return

	var current_time = float(Time.get_ticks_msec()) / 1000.0
	var interp_state = _sample_interpolated_state(current_time)
	if interp_state.is_empty():
		return

	var target_pos: Vector3 = interp_state["position"]

	# Corrección topográfica: Raycast vertical hacia el pavimento o terreno de Tecate
	# para garantizar que las suelas descansen exactamente sobre la superficie,
	# absorbiendo pendientes de banquetas sin hundirse hasta la rodilla ni flotar.
	if is_inside_tree() and get_world_3d():
		var space_state = get_world_3d().direct_space_state
		if space_state:
			var ray_from = Vector3(target_pos.x, target_pos.y + 2.5, target_pos.z)
			var ray_to = Vector3(target_pos.x, target_pos.y - 3.5, target_pos.z)
			var ray_query = PhysicsRayQueryParameters3D.create(ray_from, ray_to, 1)
			ray_query.exclude = [get_rid()]
			var hit = space_state.intersect_ray(ray_query)
			if not hit.is_empty() and hit.has("position"):
				target_pos.y = hit["position"].y

	# Aplicar cinemática en el mundo físico de Godot (CharacterBody3D)
	global_position = target_pos
	rotation_degrees.y = interp_state["yaw"]
	velocity = interp_state["velocity"]

	_update_procedural_locomotion(delta, velocity)

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

# =============================================================================
# SOPORTE DE ASIENTOS E INTERACCIÓN
# =============================================================================

func sit_in_seat(seat_node: Node) -> bool:
	current_seat_node = seat_node
	if not seat_node:
		return false

	# Desactivar colisiones temporales mientras está sentado
	if collision_shape:
		collision_shape.disabled = true

	global_position = seat_node.global_position
	global_rotation = seat_node.global_rotation
	velocity = Vector3.ZERO

	# Aplicar pose sedente en el esqueleto
	if skeleton:
		var sit_leg_pitch = deg_to_rad(-85.0)
		var sit_knee_angle = deg_to_rad(85.0)
		if bone_upperleg_l != -1:
			skeleton.set_bone_pose_rotation(bone_upperleg_l, _base_rot_upperleg_l * Quaternion(Vector3(1, 0, 0), sit_leg_pitch))
		if bone_upperleg_r != -1:
			skeleton.set_bone_pose_rotation(bone_upperleg_r, _base_rot_upperleg_r * Quaternion(Vector3(1, 0, 0), sit_leg_pitch))
		if bone_lowerleg_l != -1:
			skeleton.set_bone_pose_rotation(bone_lowerleg_l, _base_rot_lowerleg_l * Quaternion(Vector3(1, 0, 0), -sit_knee_angle))
		if bone_lowerleg_r != -1:
			skeleton.set_bone_pose_rotation(bone_lowerleg_r, _base_rot_lowerleg_r * Quaternion(Vector3(1, 0, 0), -sit_knee_angle))
	return true

func stand_up() -> bool:
	current_seat_node = null
	if collision_shape:
		collision_shape.disabled = false

	# Restaurar pose erguida base
	if skeleton:
		if bone_upperleg_l != -1: skeleton.set_bone_pose_rotation(bone_upperleg_l, _base_rot_upperleg_l)
		if bone_upperleg_r != -1: skeleton.set_bone_pose_rotation(bone_upperleg_r, _base_rot_upperleg_r)
		if bone_lowerleg_l != -1: skeleton.set_bone_pose_rotation(bone_lowerleg_l, _base_rot_lowerleg_l)
		if bone_lowerleg_r != -1: skeleton.set_bone_pose_rotation(bone_lowerleg_r, _base_rot_lowerleg_r)
	return true
