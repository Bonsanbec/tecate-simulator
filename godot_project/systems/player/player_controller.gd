class_name PlayerController
extends CharacterBody3D

## Controlador Integral del Jugador Humanoide para Tecate Simulator
## Integra biomecánica realista de Tecate (inercia, pendientes, escalado de guarniciones),
## esqueleto rigged (Skeleton3D), cinemática inversa de pies (Foot IK), director de cámaras
## tripartito (1P/2P/3P con alternancia F5), HUD inmersivo y arquitectura multijugador.

const CameraDirectorClass = preload("res://systems/player/camera_director.gd")
const FootIKClass = preload("res://systems/player/foot_ik_controller.gd")
const PlayerNetworkSyncClass = preload("res://systems/network/player_network_sync.gd")
const PlayerHUDClass = preload("res://ui/player_hud.gd")

# Parámetros Biomecánicos de Marcha y Carrera
@export var mass_kg: float = 75.0
@export var walk_speed: float = 1.45       # ~5.2 km/h
@export var jog_speed: float = 3.20        # ~11.5 km/h
@export var sprint_speed: float = 5.20     # ~18.7 km/h
@export var acceleration: float = 8.5      # m/s^2 con masa realista
@export var braking_deceleration: float = 12.0
@export var jump_velocity: float = 5.2
@export var max_step_height: float = 0.24  # Altura de banquetas de Tecate
@export var mouse_sensitivity: float = 0.15

# Vuelo libre (Modo utilitario / Minecraft)
@export var fly_speed: float = 25.0
@export var fly_sprint_speed: float = 60.0
@export var fly_vertical_speed: float = 18.0

var gravity: float = ProjectSettings.get_setting("physics/3d/default_gravity", 9.8)

# Estados de control y locomoción
var input_enabled: bool = true
var is_flying: bool = false
var space_press_timer: float = 0.0
const DOUBLE_TAP_WINDOW: float = 0.35
const DEFAULT_SNAP_LENGTH: float = 0.30

# Variables de telemetría y topografía de Tecate
var current_slope_angle: float = 0.0
var current_heading_deg: float = 0.0
var current_speed_kmh: float = 0.0
var current_altitude_msnm: float = 540.0

# Posición y rotación de reaparición
var spawn_position: Vector3 = Vector3.ZERO
var spawn_rotation_y: float = 0.0

# Submódulos del jugador
var camera_director: CameraDirectorClass
var foot_ik: FootIKClass
var hud: PlayerHUDClass
var network_sync: PlayerNetworkSyncClass

# Nodos del avatar 3D rigged
var humanoid_scene: Node3D
var skeleton: Skeleton3D
var mesh_body: MeshInstance3D
var mesh_head: MeshInstance3D

# Huesos para animación procedural (brazos, manos, columna)
var bone_upperarm_l: int = -1
var bone_upperarm_r: int = -1
var bone_forearm_l: int = -1
var bone_forearm_r: int = -1
var bone_chest: int = -1

# Ciclo de balanceo biomecánico de brazos
var arm_swing_phase: float = 0.0

# Compatibilidad con scripts existentes que buscan player.camera, player.rot_x y player.rot_y
var camera: Camera3D:
	get:
		if camera_director and camera_director.active_camera:
			return camera_director.active_camera
		return get_node_or_null("Camera3D") as Camera3D

var rot_x: float:
	get:
		return camera_director.rot_pitch if camera_director else 0.0
	set(val):
		if camera_director:
			camera_director.rot_pitch = val
			camera_director._update_camera_rotations()

var rot_y: float:
	get:
		return rotation_degrees.y
	set(val):
		rotation_degrees.y = val
		if camera_director:
			camera_director.rot_yaw = val

func _ready():
	spawn_position = global_position
	spawn_rotation_y = rotation_degrees.y

	# Configuración de CharacterBody3D para colisión óptima en el terreno de Tecate
	safe_margin = 0.02
	floor_max_angle = deg_to_rad(65.0)
	floor_constant_speed = true
	floor_stop_on_slope = true
	floor_block_on_wall = true
	floor_snap_length = DEFAULT_SNAP_LENGTH

	_initialize_submodules()
	_initialize_humanoid_rig()

	# Si existe StartScreen en la escena, pausar inputs al inicio
	var start_screen = get_parent().get_node_or_null("StartScreen") if get_parent() else null
	if start_screen:
		input_enabled = false
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	else:
		input_enabled = true
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED

func _initialize_submodules() -> void:
	# 1. Director de Cámaras (1P / 2P / 3P con F5)
	camera_director = CameraDirectorClass.new()
	camera_director.name = "CameraDirector3D"
	camera_director.mouse_sensitivity = mouse_sensitivity
	add_child(camera_director)

	# 2. Controlador de Cinemática Inversa (Foot IK)
	foot_ik = FootIKClass.new()
	foot_ik.name = "FootIKController"
	add_child(foot_ik)

	# 3. Módulo de Red Multijugador
	network_sync = PlayerNetworkSyncClass.new()
	network_sync.name = "PlayerNetworkSync"
	add_child(network_sync)

	# 4. Instanciar HUD
	var hud_res = load("res://ui/player_hud.tscn")
	if hud_res:
		hud = hud_res.instantiate() as PlayerHUDClass
		add_child(hud)
		camera_director.perspective_changed.connect(_on_perspective_changed)

func _initialize_humanoid_rig() -> void:
	# Cargar e instanciar el modelo humanoide rigged
	var model_res = load("res://assets/characters/humanoid_player.glb")
	if not model_res:
		push_error("[PlayerController] No se encontró res://assets/characters/humanoid_player.glb")
		return

	humanoid_scene = model_res.instantiate() as Node3D
	humanoid_scene.name = "HumanoidAvatar"
	add_child(humanoid_scene)

	# Localizar Skeleton3D y mallas
	skeleton = humanoid_scene.find_child("Skeleton3D", true, false) as Skeleton3D
	mesh_body = humanoid_scene.find_child("Player_Body_Mesh", true, false) as MeshInstance3D
	mesh_head = humanoid_scene.find_child("Player_Head_Mesh", true, false) as MeshInstance3D

	if skeleton:
		bone_upperarm_l = skeleton.find_bone("UpperArm.L")
		bone_upperarm_r = skeleton.find_bone("UpperArm.R")
		bone_forearm_l = skeleton.find_bone("Forearm.L")
		bone_forearm_r = skeleton.find_bone("Forearm.R")
		bone_chest = skeleton.find_bone("Chest")
		foot_ik.setup(self, skeleton)

	if camera_director:
		camera_director.setup(self, mesh_body, mesh_head)

func _on_perspective_changed(mode: int) -> void:
	var mode_name = "1P - Vista Subjetiva"
	match mode:
		CameraDirectorClass.PerspectiveMode.THIRD_PERSON:
			mode_name = "3P - Vista al Hombro"
		CameraDirectorClass.PerspectiveMode.SECOND_PERSON:
			mode_name = "2P - Observador Frontal"
	if hud:
		hud.set_perspective_badge(mode_name)

func set_input_enabled(enabled: bool) -> void:
	input_enabled = enabled
	if not enabled:
		velocity = Vector3.ZERO

func respawn() -> void:
	global_position = spawn_position
	velocity = Vector3.ZERO
	is_flying = false
	rotation_degrees.y = spawn_rotation_y
	if camera_director:
		camera_director.rot_yaw = spawn_rotation_y
		camera_director.rot_pitch = 0.0
		camera_director._update_camera_rotations()
	var main_node = get_parent()
	if main_node and main_node.has_method("_snap_player"):
		main_node._snap_player(self)
	print("[PlayerController] Reaparecido en Parque Hidalgo: ", global_position)

func _input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.is_echo():
		if event.keycode == KEY_ESCAPE:
			var start_screen = get_tree().root.find_child("StartScreen", true, false)
			if start_screen and start_screen.has_method("toggle_menu"):
				start_screen.toggle_menu()
				get_viewport().set_input_as_handled()
				return
			else:
				if Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
					Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
				else:
					Input.mouse_mode = Input.MOUSE_MODE_CAPTURED

		if not input_enabled:
			return

		# Doble pulsación de barra espaciadora para alternar vuelo
		if event.keycode == KEY_SPACE or event.is_action_pressed("ui_accept"):
			var current_time = Time.get_ticks_msec() / 1000.0
			if (current_time - space_press_timer) < DOUBLE_TAP_WINDOW:
				is_flying = !is_flying
				velocity = Vector3.ZERO
				space_press_timer = 0.0
			else:
				space_press_timer = current_time

	if not input_enabled:
		return

	if camera_director:
		camera_director.handle_input(event)

func _physics_process(delta: float) -> void:
	if not input_enabled:
		return

	if is_flying:
		_process_flying(delta)
	else:
		_process_walking(delta)

	# Actualizar cinemática inversa de pies y adaptación al suelo
	if foot_ik:
		foot_ik.update_ik(delta, is_on_floor())

	# Actualizar animación procedural de brazos y torso
	_update_procedural_animations(delta)

	# Actualizar telemetría y HUD
	_update_telemetry(delta)

func _process_walking(delta: float) -> void:
	# 1. Detección de pendiente del terreno de Tecate
	var floor_norm = get_floor_normal() if is_on_floor() else Vector3.UP
	var slope_cos = floor_norm.dot(Vector3.UP)
	current_slope_angle = rad_to_deg(acos(clampf(slope_cos, -1.0, 1.0)))

	# 2. Gravedad y adherencia al suelo
	if not is_on_floor():
		velocity.y -= gravity * delta
	else:
		if velocity.y < 0.0:
			velocity.y = 0.0
		floor_snap_length = DEFAULT_SNAP_LENGTH

	# 3. Salto
	if (Input.is_key_pressed(KEY_SPACE) or Input.is_action_just_pressed("ui_accept")) and is_on_floor():
		velocity.y = jump_velocity
		floor_snap_length = 0.0

	# 4. Modificadores de velocidad (Caminar / Trotar / Sprint)
	var is_sprint = Input.is_key_pressed(KEY_SHIFT) or Input.is_key_pressed(KEY_CTRL)
	var active_speed = sprint_speed if is_sprint else walk_speed

	# 5. Penalización biomecánica al subir pendientes empinadas
	var input_dir = _get_input_direction()
	var forward = -global_transform.basis.z
	var right = global_transform.basis.x
	var move_dir = (forward * -input_dir.y + right * input_dir.x).normalized()

	if is_on_floor() and move_dir != Vector3.ZERO:
		var slope_dir = Vector3(floor_norm.x, 0.0, floor_norm.z)
		var uphill_factor = move_dir.dot(-slope_dir)
		if uphill_factor > 0.1 and current_slope_angle > 5.0:
			# Reducción proporcional a la pendiente cuesta arriba
			var penalty = 1.0 - (sin(deg_to_rad(current_slope_angle)) * 0.70)
			active_speed *= clampf(penalty, 0.35, 1.0)

	# 6. Aceleración con inercia de masa realista (75 kg)
	var target_h_vel = move_dir * active_speed
	var current_h_vel = Vector2(velocity.x, velocity.z)
	var target_h_vec2 = Vector2(target_h_vel.x, target_h_vel.z)

	var rate = acceleration if move_dir != Vector3.ZERO else braking_deceleration
	var next_h_vec2 = current_h_vel.move_toward(target_h_vec2, rate * delta)
	velocity.x = next_h_vec2.x
	velocity.z = next_h_vec2.y

	# 7. Escalado dinámico de guarniciones y banquetas de Tecate
	if is_on_floor() and move_dir != Vector3.ZERO:
		_check_step_up(delta)

	move_and_slide()

	# 8. Estabilización de cabeceo biomecánico en cámara
	if camera_director:
		var spd_ratio = Vector2(velocity.x, velocity.z).length() / sprint_speed
		camera_director.update_head_bob(delta, spd_ratio, is_on_floor())

func _process_flying(delta: float) -> void:
	if is_on_floor() and Input.is_key_pressed(KEY_SHIFT):
		is_flying = false
		return

	var active_speed = fly_sprint_speed if (Input.is_key_pressed(KEY_CTRL) or Input.is_action_pressed("ui_focus_next")) else fly_speed
	var input_dir = _get_input_direction()
	var forward = -global_transform.basis.z
	var right = global_transform.basis.x
	var move_dir = (forward * -input_dir.y + right * input_dir.x).normalized()

	var vert_input = 0.0
	if Input.is_key_pressed(KEY_SPACE) or Input.is_action_pressed("ui_accept"): vert_input += 1.0
	if Input.is_key_pressed(KEY_SHIFT) or Input.is_action_pressed("ui_select"): vert_input -= 1.0

	var target_velocity = move_dir * active_speed
	target_velocity.y = vert_input * fly_vertical_speed
	velocity = velocity.lerp(target_velocity, 10.0 * delta)
	move_and_slide()

func _get_input_direction() -> Vector2:
	var dir = Vector2.ZERO
	if Input.is_key_pressed(KEY_W) or Input.is_key_pressed(KEY_UP) or Input.is_action_pressed("ui_up"):
		dir.y -= 1.0
	if Input.is_key_pressed(KEY_S) or Input.is_key_pressed(KEY_DOWN) or Input.is_action_pressed("ui_down"):
		dir.y += 1.0
	if Input.is_key_pressed(KEY_A) or Input.is_key_pressed(KEY_LEFT) or Input.is_action_pressed("ui_left"):
		dir.x -= 1.0
	if Input.is_key_pressed(KEY_D) or Input.is_key_pressed(KEY_RIGHT) or Input.is_action_pressed("ui_right"):
		dir.x += 1.0
	return dir

func _check_step_up(delta: float) -> void:
	var h_vel = Vector3(velocity.x, 0.0, velocity.z)
	if h_vel.length_squared() < 0.001:
		return

	var h_motion = h_vel * delta
	var col = KinematicCollision3D.new()
	if test_move(global_transform, h_motion, col):
		if col.get_normal().y < 0.70:
			var step_xform = global_transform
			step_xform.origin.y += max_step_height
			if not test_move(step_xform, Vector3.ZERO):
				if not test_move(step_xform, h_motion):
					var down_col = KinematicCollision3D.new()
					if test_move(step_xform, Vector3(0, -max_step_height, 0), down_col):
						var actual_step = max_step_height - down_col.get_travel().length()
						if actual_step > 0.01:
							global_position.y += actual_step + 0.02
					else:
						global_position.y += max_step_height

func _update_procedural_animations(delta: float) -> void:
	if not skeleton:
		return

	var h_speed = Vector2(velocity.x, velocity.z).length()
	var is_moving = h_speed > 0.1 and is_on_floor()

	if is_moving:
		arm_swing_phase += h_speed * 4.2 * delta
	else:
		arm_swing_phase = lerp_angle(arm_swing_phase, 0.0, 8.0 * delta)

	# Balanceo armónico de brazos en antifase
	var swing_amplitude = clampf(h_speed / sprint_speed, 0.0, 1.0) * 0.45
	var angle_l = sin(arm_swing_phase) * swing_amplitude
	var angle_r = -sin(arm_swing_phase) * swing_amplitude

	# Al mirar hacia abajo en 1P, elevar ligeramente los brazos para visibilidad natural de manos
	var pitch_rad = deg_to_rad(camera_director.rot_pitch if camera_director else 0.0)
	var hand_raise = 0.0
	if pitch_rad < -0.35:
		hand_raise = clampf((-pitch_rad - 0.35) * 0.40, 0.0, 0.35)

	if bone_upperarm_l != -1:
		var q_arm_l = Quaternion.from_euler(Vector3(angle_l - hand_raise, 0.0, 0.0))
		skeleton.set_bone_pose_rotation(bone_upperarm_l, q_arm_l)

	if bone_upperarm_r != -1:
		var q_arm_r = Quaternion.from_euler(Vector3(angle_r - hand_raise, 0.0, 0.0))
		skeleton.set_bone_pose_rotation(bone_upperarm_r, q_arm_r)

	# Inclinación del tórax hacia adelante al ascender pendientes
	if bone_chest != -1:
		var lean_angle = 0.0
		if current_slope_angle > 5.0 and is_moving:
			lean_angle = deg_to_rad(clampf(current_slope_angle * 0.5, 0.0, 15.0))
		var q_chest = Quaternion.from_euler(Vector3(-lean_angle, 0.0, 0.0))
		skeleton.set_bone_pose_rotation(bone_chest, q_chest)

func _update_telemetry(_delta: float) -> void:
	current_speed_kmh = Vector2(velocity.x, velocity.z).length() * 3.6
	current_altitude_msnm = 540.0 + global_position.y # Cota base aproximada de Tecate
	
	# Cálculo analítico del rumbo cartográfico (Heading Azimuth):
	# En el marco geodésico de Tecate: +X = Este, -Z = Norte, -X = Oeste, +Z = Sur.
	# atan2(forward.x, -forward.z) define el ángulo horario estándar: Norte=0°, Este=90°, Sur=180°, Oeste=270°.
	var forward = -global_transform.basis.z
	current_heading_deg = fposmod(rad_to_deg(atan2(forward.x, -forward.z)), 360.0)

	if hud:
		var is_1p = camera_director.current_mode == CameraDirectorClass.PerspectiveMode.FIRST_PERSON if camera_director else true
		var mode_str = "1P"
		if camera_director:
			match camera_director.current_mode:
				CameraDirectorClass.PerspectiveMode.THIRD_PERSON: mode_str = "3P"
				CameraDirectorClass.PerspectiveMode.SECOND_PERSON: mode_str = "2P"
		hud.update_hud(
			current_heading_deg,
			current_speed_kmh,
			current_altitude_msnm,
			current_slope_angle,
			mode_str,
			is_1p
		)
		# Actualizar gizmo de ejes con la orientación de la cámara activa
		if camera_director and camera_director.active_camera:
			hud.update_axes(camera_director.active_camera.global_transform.basis)
