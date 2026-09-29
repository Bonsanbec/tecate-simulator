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
const VehicleCameraDirectorClass = preload("res://systems/vehicles/camera/vehicle_camera_director.gd")

# Estados de Vehículo e Interacción
var current_vehicle: VehicleBase = null
var current_vehicle_seat: VehicleSeat = null
var vehicle_camera_director: VehicleCameraDirector = null
var _nearby_vehicle: VehicleBase = null
var _nearby_seat_type: int = 0
var _nearby_pump_zone: Node = null
var _vehicle_scan_timer: float = 0.0

# Parámetros Biomecánicos de Marcha y Carrera
@export var mass_kg: float = 75.0
@export var walk_speed: float = 2.40       # ~8.6 km/h (caminata urbana fluida)
@export var jog_speed: float = 3.80        # ~13.7 km/h
@export var sprint_speed: float = 6.20     # ~22.3 km/h
@export var acceleration: float = 14.0     # m/s^2 aceleración ágil y reactiva
@export var braking_deceleration: float = 16.0
@export var jump_velocity: float = 5.4
@export var max_step_height: float = 0.24  # Altura de banquetas de Tecate
@export var mouse_sensitivity: float = 0.15

# Vuelo libre (Modo utilitario / Minecraft)
@export var fly_speed: float = 25.0
@export var fly_sprint_speed: float = 65.0
@export var fly_vertical_speed: float = 22.0

var gravity: float = ProjectSettings.get_setting("physics/3d/default_gravity", 9.8)

# Estados de control y locomoción
var input_enabled: bool = true
var is_f1_photo_mode: bool = false
var is_flying: bool = false
var space_press_timer: float = 0.0
const DOUBLE_TAP_WINDOW: float = 0.35
const DEFAULT_SNAP_LENGTH: float = 0.30

# Variables de telemetría y topografía de Tecate
var current_slope_angle: float = 0.0
var current_heading_deg: float = 0.0
var current_speed_kmh: float = 0.0
var current_altitude_msnm: float = 540.0
var _street_update_timer: float = 0.0
var _cached_street_name: String = ""

# Posición y rotación de reaparición
var spawn_position: Vector3 = Vector3.ZERO
var spawn_rotation_y: float = 0.0

# Submódulos del jugador
var camera_director: CameraDirectorClass
var foot_ik: FootIKClass
var hud: PlayerHUDClass
var network_sync: PlayerNetworkSyncClass

# Conexión de Red Multijugador TKT/1
var network_client: NetworkClient
var multiplayer_manager: MultiplayerManager
var _net_tick: int = 0
var _net_tick_timer: float = 0.0
const NET_TICK_RATE: float = 30.0

# Nodos del avatar 3D rigged
var humanoid_scene: Node3D
var skeleton: Skeleton3D
var mesh_body: MeshInstance3D
var mesh_head: MeshInstance3D

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

# Banderas de estado de teclas continuas para alta fidelidad en vuelo
var _is_space_held: bool = false
var _is_shift_held: bool = false

# Ciclo de locomoción biomecánico de extremidades
var locomotion_phase: float = 0.0

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

	# Si existe StartScreen en la escena, pausar inputs y ocultar HUD al inicio
	var start_screen = get_parent().get_node_or_null("StartScreen") if get_parent() else null
	if start_screen:
		input_enabled = false
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
		# El HUD ya nace oculto (visible = false en _ready); no se necesita llamada extra
	else:
		input_enabled = true
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
		if hud:
			hud.show_hud()

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

	# 5. Director de Cámaras para Vehículos (1P / 3P)
	vehicle_camera_director = VehicleCameraDirectorClass.new()
	vehicle_camera_director.name = "VehicleCameraDirector"
	vehicle_camera_director.mouse_sensitivity = mouse_sensitivity
	add_child(vehicle_camera_director)

	# 6. Localizar y vincular NetworkClient y MultiplayerManager
	if get_parent():
		network_client = get_parent().find_child("NetworkClient", true, false) as NetworkClient
		multiplayer_manager = get_parent().find_child("MultiplayerManager", true, false) as MultiplayerManager

	if network_client:
		network_client.connected_to_server.connect(_on_net_connected)
		network_client.disconnected_from_server.connect(_on_net_disconnected)
		network_client.latency_updated.connect(_on_net_latency_updated)
		if hud:
			hud.update_network_status("TKT/1: CONECTANDO...", false)
		network_client.start_connection()

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

func _on_net_connected(sess_id: int, p_id: int) -> void:
	print("[PlayerController] Red TKT/1 conectada: Sesión=%d, Jugador=%d" % [sess_id, p_id])
	if hud:
		var p_count = multiplayer_manager.get_player_count() if multiplayer_manager else 1
		hud.update_network_status("● EN LÍNEA  |  %s  |  %d Jug." % [network_client.server_host, p_count], true)

func _on_net_disconnected(reason: String) -> void:
	print("[PlayerController] Red TKT/1 desconectada: ", reason)
	if hud:
		hud.update_network_status("○ FUERA DE LÍNEA", false)

func _on_net_latency_updated(ping_ms: float) -> void:
	if hud and network_client and network_client.state == NetworkClient.ConnectionState.CONNECTED:
		var p_count = multiplayer_manager.get_player_count() if multiplayer_manager else 1
		hud.update_network_status("● EN LÍNEA  |  %d ms  |  %d Jug." % [int(ping_ms), p_count], true)

func set_input_enabled(enabled: bool) -> void:
	input_enabled = enabled
	if not enabled:
		velocity = Vector3.ZERO
	# Sincronizar visibilidad del HUD con el estado de juego activo
	if hud:
		if enabled:
			hud.show_hud()
		else:
			hud.hide_hud()

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

func toggle_f1_photo_mode() -> void:
	is_f1_photo_mode = !is_f1_photo_mode
	if is_f1_photo_mode:
		velocity = Vector3.ZERO
		if hud:
			hud.hide_hud()
		if humanoid_scene:
			humanoid_scene.visible = false
		print("[PlayerController] Modo Screenshot [F1] ACTIVADO: HUD y avatar ocultos, inputs suspendidos.")
	else:
		if humanoid_scene:
			humanoid_scene.visible = true
		if hud:
			hud.show_hud()
		print("[PlayerController] Modo Screenshot [F1] DESACTIVADO: HUD y avatar restaurados, inputs reactivados.")

func _input(event: InputEvent) -> void:
	if event is InputEventKey:
		if event.keycode == KEY_SPACE or event.physical_keycode == KEY_SPACE:
			_is_space_held = event.pressed
		elif event.keycode == KEY_SHIFT or event.physical_keycode == KEY_SHIFT:
			_is_shift_held = event.pressed

	if event is InputEventKey and event.pressed and not event.is_echo():
		# Modo Screenshot (F1): Oculta HUD y avatar, suspende inputs
		if event.keycode == KEY_F1:
			toggle_f1_photo_mode()
			get_viewport().set_input_as_handled()
			return

		if is_f1_photo_mode:
			return

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

		# Tecla de Interacción [E]: Abordar o Descender de Vehículo
		if event.keycode == KEY_E:
			if current_vehicle:
				dismount_vehicle()
				get_viewport().set_input_as_handled()
				return
			elif _nearby_vehicle:
				board_vehicle(_nearby_vehicle, _nearby_seat_type)
				get_viewport().set_input_as_handled()
				return

		# Tecla de Repostaje [R]: Cargar combustible si está en una estación de servicio
		if event.keycode == KEY_R and _nearby_pump_zone and current_vehicle:
			if _nearby_pump_zone.has_method("start_refueling"):
				_nearby_pump_zone.start_refueling()
				get_viewport().set_input_as_handled()
				return

		# Barra espaciadora: doble tap en el suelo/aire inicia vuelo; en vuelo, impulsa ascenso vertical inmediato
		if (event.keycode == KEY_SPACE or event.physical_keycode == KEY_SPACE or event.is_action_pressed("ui_accept")) and not current_vehicle:
			var current_time = Time.get_ticks_msec() / 1000.0
			if not is_flying:
				if (current_time - space_press_timer) < DOUBLE_TAP_WINDOW:
					is_flying = true
					velocity.y = fly_vertical_speed * 0.6 # Impulso inicial de despegue
					floor_snap_length = 0.0
					space_press_timer = 0.0
				else:
					space_press_timer = current_time
			else:
				# Estando en vuelo, presionar barra espaciadora siempre añade elevación inmediata
				velocity.y = maxf(velocity.y + 8.0, fly_vertical_speed)

	if is_f1_photo_mode or not input_enabled:
		return

	if current_vehicle and vehicle_camera_director:
		vehicle_camera_director.handle_input(event)
	elif camera_director:
		camera_director.handle_input(event)

func _physics_process(delta: float) -> void:
	if is_f1_photo_mode or not input_enabled:
		return

	if current_vehicle:
		_process_riding_vehicle(delta)
		return

	_scan_nearby_interactive_objects(delta)

	if is_flying:
		_process_flying(delta)
	else:
		_process_walking(delta)

	# Actualizar cinemática inversa de pies y adaptación al suelo
	if foot_ik:
		foot_ik.update_ik(delta, is_on_floor() and not is_flying)

	# Actualizar animación procedural de brazos, piernas y torso
	_update_procedural_animations(delta)

	# Actualizar telemetría y HUD
	_update_telemetry(delta)

	# Transmitir estado biomecánico o vehicular a la red TKT/1 (~30 Hz)
	if network_client and network_client.state == NetworkClient.ConnectionState.CONNECTED:
		_net_tick_timer += delta
		if _net_tick_timer >= (1.0 / NET_TICK_RATE):
			_net_tick_timer = 0.0
			_net_tick += 1
			var flags = 0
			var send_pos = global_position
			var yaw = rotation_degrees.y
			var pitch = camera_director.rot_pitch if camera_director else 0.0
			var send_vel = velocity

			if current_vehicle:
				flags |= 0x10 # PlayerFlags.IN_VEHICLE
				var is_driver = (current_vehicle_seat and current_vehicle_seat.is_driver())
				if is_driver:
					flags |= 0x20 # PlayerFlags.DRIVING_VEHICLE
				send_pos = current_vehicle.global_position
				yaw = current_vehicle.rotation_degrees.y
				pitch = current_vehicle.rotation_degrees.x
				send_vel = current_vehicle.linear_velocity
			else:
				if is_on_floor(): flags |= 1
				if Input.is_key_pressed(KEY_SHIFT): flags |= 2
				if is_flying: flags |= 4

			network_client.send_player_input(_net_tick, send_pos, yaw, pitch, send_vel, flags)


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
		if uphill_factor > 0.1 and current_slope_angle > 8.0:
			# Reducción suave y equilibrada a la pendiente cuesta arriba
			var penalty = 1.0 - (sin(deg_to_rad(current_slope_angle)) * 0.40)
			active_speed *= clampf(penalty, 0.65, 1.0)

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
	floor_snap_length = 0.0

	# Aterrizaje suave al descender hasta tocar el piso
	if is_on_floor() and (_is_shift_held or Input.is_key_pressed(KEY_SHIFT) or Input.is_physical_key_pressed(KEY_SHIFT)):
		is_flying = false
		floor_snap_length = DEFAULT_SNAP_LENGTH
		return

	var is_sprint = Input.is_key_pressed(KEY_CTRL) or Input.is_physical_key_pressed(KEY_CTRL) or Input.is_action_pressed("ui_focus_next")
	var active_h_speed = fly_sprint_speed if is_sprint else fly_speed
	var active_v_speed = fly_vertical_speed * 1.8 if is_sprint else fly_vertical_speed

	var input_dir = _get_input_direction()
	var forward = -global_transform.basis.z
	var right = global_transform.basis.x
	var move_dir = (forward * -input_dir.y + right * input_dir.x).normalized()

	var vert_input = 0.0
	# Barra espaciadora: Ascenso constante y potente
	var space_pressed = _is_space_held or Input.is_key_pressed(KEY_SPACE) or Input.is_physical_key_pressed(KEY_SPACE) or Input.is_action_pressed("ui_accept")
	if space_pressed:
		vert_input += 1.0

	# Shift o C: Descenso controlado
	var down_pressed = _is_shift_held or Input.is_key_pressed(KEY_SHIFT) or Input.is_physical_key_pressed(KEY_SHIFT) or Input.is_action_pressed("ui_select")
	if down_pressed:
		vert_input -= 1.0

	var target_h_vel = move_dir * active_h_speed
	velocity.x = lerp(velocity.x, target_h_vel.x, 14.0 * delta)
	velocity.z = lerp(velocity.z, target_h_vel.z, 14.0 * delta)

	if vert_input != 0.0:
		var target_v_vel = vert_input * active_v_speed
		velocity.y = move_toward(velocity.y, target_v_vel, active_v_speed * 5.0 * delta)
	else:
		velocity.y = move_toward(velocity.y, 0.0, 24.0 * delta)

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
	var is_moving = h_speed > 0.1 and is_on_floor() and not is_flying

	if is_moving:
		locomotion_phase += h_speed * 3.8 * delta
	else:
		locomotion_phase = lerp_angle(locomotion_phase, 0.0, 8.0 * delta)

	# Amplitud de oscilación modulada por la velocidad
	var speed_ratio = clampf(h_speed / sprint_speed, 0.0, 1.0)
	var arm_amplitude = speed_ratio * 0.45
	var leg_amplitude = speed_ratio * 0.50

	# Balanceo en antifase (Biomecánica cruzada: Brazo L avanza con Pierna R)
	var arm_angle_l = sin(locomotion_phase) * arm_amplitude
	var arm_angle_r = -sin(locomotion_phase) * arm_amplitude
	var leg_angle_l = -sin(locomotion_phase) * leg_amplitude
	var leg_angle_r = sin(locomotion_phase) * leg_amplitude

	# Flexión natural de codos y rodillas durante el ciclo de zancada
	var elbow_flex_l = maxf(0.0, sin(locomotion_phase)) * arm_amplitude * 0.55
	var elbow_flex_r = maxf(0.0, -sin(locomotion_phase)) * arm_amplitude * 0.55
	var knee_flex_l = maxf(0.0, -sin(locomotion_phase)) * leg_amplitude * 0.85
	var knee_flex_r = maxf(0.0, sin(locomotion_phase)) * leg_amplitude * 0.85

	# Al mirar hacia abajo en 1P, elevar ligeramente los brazos para visibilidad natural de manos
	var pitch_rad = deg_to_rad(camera_director.rot_pitch if camera_director else 0.0)
	var hand_raise = 0.0
	if pitch_rad < -0.35:
		hand_raise = clampf((-pitch_rad - 0.35) * 0.40, 0.0, 0.35)

	# 1. Animación de Brazos (cabeceo hacia adelante/atrás en eje X sin desvío lateral)
	if bone_upperarm_l != -1:
		skeleton.set_bone_pose_rotation(bone_upperarm_l, _base_rot_upperarm_l * Quaternion(Vector3(1, 0, 0), arm_angle_l - hand_raise))
	if bone_upperarm_r != -1:
		skeleton.set_bone_pose_rotation(bone_upperarm_r, _base_rot_upperarm_r * Quaternion(Vector3(1, 0, 0), arm_angle_r - hand_raise))
	if bone_forearm_l != -1:
		skeleton.set_bone_pose_rotation(bone_forearm_l, _base_rot_forearm_l * Quaternion(Vector3(1, 0, 0), elbow_flex_l))
	if bone_forearm_r != -1:
		skeleton.set_bone_pose_rotation(bone_forearm_r, _base_rot_forearm_r * Quaternion(Vector3(1, 0, 0), elbow_flex_r))

	# 2. Animación de Piernas (zancada cruzada y flexión anatómica de rodilla hacia atrás)
	if bone_upperleg_l != -1:
		skeleton.set_bone_pose_rotation(bone_upperleg_l, _base_rot_upperleg_l * Quaternion(Vector3(1, 0, 0), leg_angle_l))
	if bone_upperleg_r != -1:
		skeleton.set_bone_pose_rotation(bone_upperleg_r, _base_rot_upperleg_r * Quaternion(Vector3(1, 0, 0), leg_angle_r))
	if bone_lowerleg_l != -1:
		skeleton.set_bone_pose_rotation(bone_lowerleg_l, _base_rot_lowerleg_l * Quaternion(Vector3(1, 0, 0), -knee_flex_l))
	if bone_lowerleg_r != -1:
		skeleton.set_bone_pose_rotation(bone_lowerleg_r, _base_rot_lowerleg_r * Quaternion(Vector3(1, 0, 0), -knee_flex_r))

	# 3. Inclinación del tórax hacia adelante al ascender pendientes
	if bone_chest != -1:
		var lean_angle = 0.0
		if current_slope_angle > 5.0 and is_moving:
			lean_angle = deg_to_rad(clampf(current_slope_angle * 0.5, 0.0, 15.0))
		skeleton.set_bone_pose_rotation(bone_chest, _base_rot_chest * Quaternion(Vector3(1, 0, 0), -lean_angle))

func _update_telemetry(delta: float) -> void:
	current_speed_kmh = Vector2(velocity.x, velocity.z).length() * 3.6
	current_altitude_msnm = global_position.y # Cota base aproximada de Tecate

	# Cálculo analítico del rumbo cartográfico (Heading Azimuth):
	var forward := -global_transform.basis.z
	current_heading_deg = fposmod(rad_to_deg(atan2(forward.x, -forward.z)), 360.0)

	# Optimización de rendimiento: Consultar nombre de calle a 5 Hz (cada 0.2 s)
	# en lugar de 60 Hz para evitar congelamientos/stuttering.
	_street_update_timer += delta
	if _street_update_timer >= 0.2 or _cached_street_name.is_empty():
		_street_update_timer = 0.0
		if has_node("/root/StreetNameLookup"):
			_cached_street_name = get_node("/root/StreetNameLookup").get_street_ahead(
				global_position, forward
			)

	var nearest_street: String = _cached_street_name

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
			is_1p,
			nearest_street
		)
		# Actualizar gizmo de ejes con la orientación de la cámara activa
		if camera_director and camera_director.active_camera:
			hud.update_axes(camera_director.active_camera.global_transform.basis)

# ── Interacción con Vehículos y Estaciones de Servicio ────────────────────────

## Permite al jugador abordar un vehículo en un asiento específico
func board_vehicle(vehicle: VehicleBase, preferred_type: int = 0) -> bool:
	if not vehicle or current_vehicle:
		return false

	var success = vehicle.enter_vehicle(self, preferred_type as VehicleSeat.SeatType)
	if not success:
		print("[PlayerController] No hay asientos disponibles en '%s'" % vehicle.vehicle_name)
		return false

	current_vehicle = vehicle
	# Localizar el asiento que ocupamos
	for s in vehicle.seats:
		if s.occupant == self:
			current_vehicle_seat = s
			break

	# Desactivar colisiones peatonales y ocultar avatar
	set_collision_layer_value(1, false)
	set_collision_mask_value(1, false)
	velocity = Vector3.ZERO
	is_flying = false

	if humanoid_scene:
		humanoid_scene.visible = false

	# Desactivar cámaras a pie y activar cámaras de vehículo
	if camera_director and camera_director.active_camera:
		camera_director.active_camera.current = false

	if vehicle_camera_director:
		vehicle_camera_director.setup(current_vehicle, current_vehicle_seat)
		vehicle_camera_director.activate()

	if hud:
		hud.set_interaction_prompt("[E] Descender")

	# Notificar abordaje a la red TKT/1
	if network_client and network_client.state == NetworkClient.ConnectionState.CONNECTED:
		var v_id = vehicle.vehicle_id if "vehicle_id" in vehicle else 1001
		var seat_idx = current_vehicle_seat.seat_index if current_vehicle_seat else 0
		var is_drv = current_vehicle_seat.is_driver() if current_vehicle_seat else false
		network_client.send_vehicle_enter(v_id, seat_idx, is_drv)

	print("[PlayerController] Abordado con éxito en '%s' como %s" % [
		vehicle.vehicle_name,
		"CONDUCTOR" if (current_vehicle_seat and current_vehicle_seat.is_driver()) else "PASAJERO"
	])
	return true

## Permite descender del vehículo actual si la velocidad es segura
func dismount_vehicle() -> bool:
	if not current_vehicle:
		return false

	if current_vehicle.current_speed_kmh > 8.0:
		print("[PlayerController] Demasiado rápido para descender: %.1f km/h" % current_vehicle.current_speed_kmh)
		return false

	# Notificar descenso a la red TKT/1
	if network_client and network_client.state == NetworkClient.ConnectionState.CONNECTED:
		var v_id = current_vehicle.vehicle_id if "vehicle_id" in current_vehicle else 1001
		var seat_idx = current_vehicle_seat.seat_index if current_vehicle_seat else 0
		network_client.send_vehicle_exit(v_id, seat_idx)

	var exit_pos = global_position
	if current_vehicle_seat:
		exit_pos = current_vehicle_seat.get_exit_global_position()

	current_vehicle.exit_vehicle(self)
	var prev_veh_name = current_vehicle.vehicle_name
	current_vehicle = null
	current_vehicle_seat = null


	# Desactivar cámaras de vehículo y reactivar cámaras a pie
	if vehicle_camera_director:
		vehicle_camera_director.deactivate()

	if camera_director and camera_director.active_camera:
		camera_director.active_camera.current = true

	# Restaurar avatar y físicas a pie
	global_position = exit_pos
	velocity = Vector3.ZERO
	set_collision_layer_value(1, true)
	set_collision_mask_value(1, true)

	if humanoid_scene:
		humanoid_scene.visible = true

	if hud:
		hud.set_interaction_prompt("")

	print("[PlayerController] Descendido de '%s'" % prev_veh_name)
	return true

func _process_riding_vehicle(delta: float) -> void:
	if not current_vehicle:
		return

	# Sincronizar posición con el asiento del vehículo
	if current_vehicle_seat:
		global_position = current_vehicle_seat.global_position
	else:
		global_position = current_vehicle.global_position

	velocity = current_vehicle.velocity

	# Orientación de brújula según vehículo
	var v_fwd = -current_vehicle.global_transform.basis.z
	var veh_heading = fposmod(rad_to_deg(atan2(v_fwd.x, -v_fwd.z)), 360.0)

	# Actualizar telemetría de vehículo en el HUD
	if hud:
		var fuel_pct = current_vehicle.fuel_system.get_fuel_percentage() if current_vehicle.fuel_system else 100.0
		var is_inf = current_vehicle.fuel_system.is_infinite_fuel if current_vehicle.fuel_system else false
		var surf_name = current_vehicle.current_surface_profile.surface_name if current_vehicle.current_surface_profile else "Asfalto"
		var is_drv = current_vehicle_seat.is_driver() if current_vehicle_seat else false

		hud.update_vehicle_hud(
			current_vehicle.vehicle_name,
			current_vehicle.current_speed_kmh,
			fuel_pct,
			is_inf,
			surf_name,
			current_vehicle.current_slope_angle,
			is_drv,
			veh_heading,
			_cached_street_name
		)

		if current_vehicle.current_speed_kmh < 8.0:
			hud.set_interaction_prompt("[E] Descender")
		else:
			hud.set_interaction_prompt("")

func _scan_nearby_interactive_objects(delta: float) -> void:
	_vehicle_scan_timer += delta
	if _vehicle_scan_timer < 0.15:
		return
	_vehicle_scan_timer = 0.0

	_nearby_vehicle = null
	_nearby_seat_type = 0
	_nearby_pump_zone = null

	var tree_root = get_tree().root
	if not tree_root:
		return

	# Buscar vehículos en un radio de 4.0 metros
	var search_radius_sq = 16.0 # 4m ^ 2
	var min_d_sq = search_radius_sq
	var my_pos = global_position

	for veh in tree_root.find_children("*", "VehicleBase", true, false):
		if veh is VehicleBase:
			var d_sq = my_pos.distance_squared_to(veh.global_position)
			if d_sq < min_d_sq:
				min_d_sq = d_sq
				_nearby_vehicle = veh as VehicleBase

	if _nearby_vehicle:
		var d_seat = _nearby_vehicle.get_driver_seat()
		if d_seat and not d_seat.is_occupied():
			_nearby_seat_type = VehicleSeat.SeatType.DRIVER
			if hud:
				hud.set_interaction_prompt("[E] Conducir %s" % _nearby_vehicle.vehicle_name)
		else:
			var avail_pass = _nearby_vehicle.get_available_passenger_seats()
			if not avail_pass.is_empty():
				_nearby_seat_type = VehicleSeat.SeatType.PASSENGER
				if hud:
					hud.set_interaction_prompt("[E] Abordar como Pasajero en %s" % _nearby_vehicle.vehicle_name)
			else:
				if hud:
					hud.set_interaction_prompt("%s (Lleno)" % _nearby_vehicle.vehicle_name)
	else:
		if hud:
			hud.set_interaction_prompt("")
