class_name PlayerController
extends "res://systems/characters/citizen_entity.gd"

## Controlador Integral del Jugador Humanoide para Tecate Simulator
## Hereda de CitizenEntity (compartiendo el cuerpo rígido CharacterBody3D con
## cápsula antropométrica, rig 3D y locomoción procedural) e integra los
## subsistemas de control del jugador: biomecánica de marcha/carrera en pendientes,
## Foot IK, director de cámaras tripartito (1P/2P/3P con alternancia F5), HUD inmersivo
## y sincronización de red con el servidor TKT/1.

const CameraDirectorClass = preload("res://systems/player/camera_director.gd")
const FootIKClass = preload("res://systems/player/foot_ik_controller.gd")
const PlayerNetworkSyncClass = preload("res://systems/network/player_network_sync.gd")
const PlayerHUDClass = preload("res://ui/player_hud.gd")
const VehicleCameraDirectorClass = preload("res://systems/vehicles/camera/vehicle_camera_director.gd")

# Estados de Vehículo, Asientos e Interacción
enum PlayerState {
	NORMAL = 0,
	FLYING = 1,
	SITTING = 2
}
var player_state: PlayerState = PlayerState.NORMAL
var is_sitting: bool:
	get:
		return player_state == PlayerState.SITTING

var current_vehicle: VehicleBase = null
var current_vehicle_seat: VehicleSeat = null
var current_seat: Node = null # VehicleSeat o UrbanSeat
var vehicle_camera_director: VehicleCameraDirector = null
var _nearby_vehicle: VehicleBase = null
var _nearby_seat: Node = null
var _nearby_seat_type: int = 0
var _nearby_pump_zone: Node = null
var _near_exit_door: bool = false
var _vehicle_scan_timer: float = 0.0

# Parámetros Biomecánicos de Marcha y Carrera
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
var _prev_avatar_visible: bool = true
var is_flying: bool = false
var space_press_timer: float = 0.0
const DOUBLE_TAP_WINDOW: float = 0.35

# Variables de telemetría y topografía de Tecate
var current_slope_angle: float = 0.0
var current_heading_deg: float = 0.0
var current_speed_kmh: float = 0.0
var current_altitude_msnm: float = 0.0
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

# Banderas de estado de teclas continuas para alta fidelidad en vuelo
var _is_space_held: bool = false
var _is_shift_held: bool = false

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
	is_locally_controlled = true
	super._ready()

	spawn_position = global_position
	spawn_rotation_y = rotation_degrees.y

	_initialize_submodules()
	if skeleton and foot_ik:
		foot_ik.setup(self, skeleton)
	if camera_director and mesh_body and mesh_head:
		camera_director.setup(self, mesh_body, mesh_head)

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
		if hud.has_method("apply_character_theme"):
			hud.apply_character_theme(identity_id)
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

func apply_identity(p_id: String) -> void:
	super.apply_identity(p_id)
	if hud and hud.has_method("apply_character_theme"):
		hud.apply_character_theme(p_id)

func _initialize_humanoid_rig() -> void:
	super._initialize_humanoid_rig()
	if skeleton and foot_ik:
		foot_ik.setup(self, skeleton)
	if camera_director and mesh_body and mesh_head:
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
		_prev_avatar_visible = humanoid_scene.visible if humanoid_scene else true
		if humanoid_scene:
			humanoid_scene.visible = false
		print("[PlayerController] Modo Screenshot [F1] ACTIVADO: HUD y avatar ocultos, inputs suspendidos.")
	else:
		if humanoid_scene:
			humanoid_scene.visible = _prev_avatar_visible
		if hud:
			hud.show_hud()
		print("[PlayerController] Modo Screenshot [F1] DESACTIVADO: HUD y avatar restaurados, inputs reactivados.")

func _set_input_handled() -> void:
	var vp = get_viewport()
	if vp:
		vp.set_input_as_handled()

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
			_set_input_handled()
			return

		if is_f1_photo_mode:
			return

		if event.keycode == KEY_ESCAPE:
			var tree = get_tree()
			var start_screen = tree.root.find_child("StartScreen", true, false) if (tree and tree.root) else null
			if start_screen and start_screen.has_method("toggle_menu"):
				start_screen.toggle_menu()
				_set_input_handled()
				return
			else:
				if Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
					Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
				else:
					Input.mouse_mode = Input.MOUSE_MODE_CAPTURED

		# Alternar modo Vuelo Libre [F]
		if event.keycode == KEY_F and not current_vehicle and not is_sitting:
			is_flying = !is_flying
			if is_flying:
				player_state = PlayerState.FLYING
				velocity.y = fly_vertical_speed * 0.6
				floor_snap_length = 0.0
			else:
				player_state = PlayerState.NORMAL
				floor_snap_length = DEFAULT_SNAP_LENGTH
			_set_input_handled()
			return

		# Tecla de Interacción [E]: Sentarse, Levantarse, Abordar o Descender
		if event.keycode == KEY_E:
			if is_sitting:
				stand_up()
				_set_input_handled()
				return
			elif _nearby_seat:
				sit_in_seat(_nearby_seat)
				_set_input_handled()
				return
			elif current_vehicle:
				if _near_exit_door:
					dismount_vehicle()
					_set_input_handled()
					return
			elif _nearby_vehicle:
				board_vehicle(_nearby_vehicle, _nearby_seat_type)
				_set_input_handled()
				return

		# Tecla de Timbre / Parada [T]: Solicitar descenso en autobús
		if event.keycode == KEY_T:
			if _try_request_bus_stop():
				_set_input_handled()
				return

		# Tecla de Repostaje [R]: Cargar combustible si está en una estación de servicio
		if event.keycode == KEY_R and _nearby_pump_zone and current_vehicle:
			if _nearby_pump_zone.has_method("start_refueling"):
				_nearby_pump_zone.start_refueling()
				_set_input_handled()
				return

		# Barra espaciadora:
		# Si está sentado, levantarse inmediatamente
		if (event.keycode == KEY_SPACE or event.physical_keycode == KEY_SPACE or event.is_action_pressed("ui_accept")) and is_sitting:
			stand_up()
			_set_input_handled()
			return

		# Barra espaciadora: doble tap en el suelo/aire inicia vuelo; en vuelo, impulsa ascenso vertical inmediato
		if (event.keycode == KEY_SPACE or event.physical_keycode == KEY_SPACE or event.is_action_pressed("ui_accept")) and not current_vehicle and not is_sitting:
			var current_time = Time.get_ticks_msec() / 1000.0
			if not is_flying:
				if (current_time - space_press_timer) < DOUBLE_TAP_WINDOW:
					is_flying = true
					player_state = PlayerState.FLYING
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

	if current_vehicle and vehicle_camera_director and vehicle_camera_director.is_active:
		vehicle_camera_director.handle_input(event)
	elif camera_director:
		camera_director.handle_input(event)

func _physics_process(delta: float) -> void:
	if is_f1_photo_mode or not input_enabled:
		return

	if is_sitting:
		_process_sitting(delta)
	elif current_vehicle:
		_process_riding_vehicle(delta)
	elif is_flying:
		_process_flying(delta)
	else:
		_process_walking(delta)

	_scan_nearby_interactive_objects(delta)

	# Actualizar cinemática inversa de pies y adaptación al suelo
	if foot_ik:
		foot_ik.update_ik(delta, is_on_floor() and not is_flying and not is_sitting)

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
				send_vel = current_vehicle.velocity
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

	if is_sitting:
		# Pose biomecánica anatómica SITTING:
		# Muslos a ~85° hacia adelante en X (horizontales sobre el cojín)
		var sit_thigh_angle = deg_to_rad(85.0)
		# Rodillas flexionadas 90° hacia atrás en X (pantorrillas verticales hacia el suelo)
		var sit_knee_angle = deg_to_rad(90.0)
		# Brazos descansando sobre los muslos
		var sit_arm_pitch = deg_to_rad(20.0)
		var sit_elbow_pitch = deg_to_rad(35.0)

		if bone_upperleg_l != -1:
			skeleton.set_bone_pose_rotation(bone_upperleg_l, _base_rot_upperleg_l * Quaternion(Vector3(1, 0, 0), sit_thigh_angle))
		if bone_upperleg_r != -1:
			skeleton.set_bone_pose_rotation(bone_upperleg_r, _base_rot_upperleg_r * Quaternion(Vector3(1, 0, 0), sit_thigh_angle))
		if bone_lowerleg_l != -1:
			skeleton.set_bone_pose_rotation(bone_lowerleg_l, _base_rot_lowerleg_l * Quaternion(Vector3(1, 0, 0), -sit_knee_angle))
		if bone_lowerleg_r != -1:
			skeleton.set_bone_pose_rotation(bone_lowerleg_r, _base_rot_lowerleg_r * Quaternion(Vector3(1, 0, 0), -sit_knee_angle))

		if bone_upperarm_l != -1:
			skeleton.set_bone_pose_rotation(bone_upperarm_l, _base_rot_upperarm_l * Quaternion(Vector3(1, 0, 0), sit_arm_pitch))
		if bone_upperarm_r != -1:
			skeleton.set_bone_pose_rotation(bone_upperarm_r, _base_rot_upperarm_r * Quaternion(Vector3(1, 0, 0), sit_arm_pitch))
		if bone_forearm_l != -1:
			skeleton.set_bone_pose_rotation(bone_forearm_l, _base_rot_forearm_l * Quaternion(Vector3(1, 0, 0), sit_elbow_pitch))
		if bone_forearm_r != -1:
			skeleton.set_bone_pose_rotation(bone_forearm_r, _base_rot_forearm_r * Quaternion(Vector3(1, 0, 0), sit_elbow_pitch))

		if bone_chest != -1:
			skeleton.set_bone_pose_rotation(bone_chest, _base_rot_chest)
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

# ── Interacción con Vehículos, Asientos y Paradas de Autobús ──────────────

## Permite al jugador sentarse en cualquier asiento (de vehículo o urbano)
func sit_in_seat(seat: Node) -> bool:
	if not seat or is_sitting:
		return false
	if seat.has_method("is_occupied") and seat.is_occupied():
		print("[PlayerController] El asiento '%s' ya está ocupado" % (seat.seat_name if "seat_name" in seat else "Asiento"))
		return false

	if seat.has_method("occupy"):
		seat.occupy(self)

	current_seat = seat
	player_state = PlayerState.SITTING
	is_flying = false
	velocity = Vector3.ZERO

	# Si el asiento pertenece a un vehículo, vincular vehículo
	var veh: VehicleBase = null
	var parent_node = seat.get_parent()
	while parent_node:
		if parent_node is VehicleBase:
			veh = parent_node as VehicleBase
			break
		parent_node = parent_node.get_parent()

	if veh:
		current_vehicle = veh
		if seat is VehicleSeat:
			current_vehicle_seat = seat as VehicleSeat
			if current_vehicle_seat.is_driver():
				current_vehicle.engine_running = not current_vehicle.fuel_system.is_empty
				current_vehicle.engine_state_changed.emit(current_vehicle.engine_running)
		current_vehicle.vehicle_entered.emit(self, seat)

	# Posicionar y orientar al avatar biomecánicamente sobre el cojín
	var h_offset: float = 0.45
	if "sit_height_offset" in seat:
		h_offset = seat.sit_height_offset
	global_position = seat.global_position - Vector3(0.0, h_offset, 0.0)
	rotation_degrees.y = seat.global_rotation_degrees.y

	if camera_director:
		camera_director.rot_yaw = seat.global_rotation_degrees.y

	# Mantener el avatar visible con su postura de sentado
	if humanoid_scene:
		humanoid_scene.visible = true

	# Configurar cámaras de vehículo si es conductor de vehículo manual
	if current_vehicle_seat and current_vehicle_seat.is_driver() and vehicle_camera_director:
		if camera_director and camera_director.active_camera:
			camera_director.active_camera.current = false
		vehicle_camera_director.setup(current_vehicle, current_vehicle_seat)
		vehicle_camera_director.activate()

	# Notificar abordaje a la red TKT/1 si aplica
	if network_client and network_client.state == NetworkClient.ConnectionState.CONNECTED:
		var v_id = current_vehicle.vehicle_id if (current_vehicle and "vehicle_id" in current_vehicle) else 0
		var seat_idx = current_vehicle_seat.seat_index if current_vehicle_seat else 0
		var is_drv = current_vehicle_seat.is_driver() if current_vehicle_seat else false
		network_client.send_vehicle_enter(v_id, seat_idx, is_drv)

	var s_name = seat.seat_name if "seat_name" in seat else "Asiento"
	if hud:
		var prompt = "[E] o [Espacio] Levantarse"
		if _get_riding_bus():
			prompt += "  |  [T] Solicitar Parada"
		hud.set_interaction_prompt(prompt)
	print("[PlayerController] Sentado con éxito en: %s" % s_name)
	return true

## Permite levantarse de cualquier asiento a la posición de pie en el pasillo sin salir del vehículo
func stand_up() -> bool:
	if not is_sitting:
		return false

	var seat = current_seat
	var exit_pos = global_position

	if seat and seat.has_method("get_exit_global_position"):
		exit_pos = seat.get_exit_global_position()
	elif seat:
		var aisle_dir = 1.0 if seat.position.x < 0.0 else -1.0
		exit_pos = seat.global_position + (seat.global_transform.basis.x * aisle_dir * 0.65)

	if seat and seat.has_method("vacate"):
		seat.vacate()

	var veh: VehicleBase = current_vehicle
	if not veh and seat:
		var p = seat.get_parent()
		while p:
			if p is VehicleBase:
				veh = p as VehicleBase
				break
			p = p.get_parent()

	# Notificar descenso de asiento a la red TKT/1 si aplica
	if network_client and network_client.state == NetworkClient.ConnectionState.CONNECTED and veh:
		var v_id = veh.vehicle_id if "vehicle_id" in veh else 0
		var s_idx = current_vehicle_seat.seat_index if current_vehicle_seat else 0
		network_client.send_vehicle_exit(v_id, s_idx)

	# Desactivar cámaras vehiculares de conductor si estaban activas y restaurar cámaras de pie
	if vehicle_camera_director and vehicle_camera_director.is_active:
		vehicle_camera_director.deactivate()

	if camera_director and camera_director.active_camera:
		camera_director.active_camera.current = true

	current_seat = null
	current_vehicle_seat = null
	player_state = PlayerState.NORMAL
	global_position = exit_pos

	if veh:
		# Se levanta en el pasillo y PERMANECE A BORDO viajando a la velocidad del vehículo
		current_vehicle = veh
		velocity = veh.velocity
	else:
		current_vehicle = null
		velocity = Vector3.ZERO

	set_collision_layer_value(1, true)
	set_collision_mask_value(1, true)

	if humanoid_scene:
		humanoid_scene.visible = true

	if hud:
		hud.set_interaction_prompt("")

	print("[PlayerController] Levantado a posición de pie en el pasillo.")
	return true

## Aborda un vehículo por la puerta de acceso o en un asiento preferente
func board_vehicle(vehicle: VehicleBase, preferred_type: int = 0) -> bool:
	if not vehicle or is_sitting:
		return false

	# Si el vehículo tiene soporte de puertas o es autobús de pasajeros, ingresar a pie al pasillo interior
	if vehicle.doors.size() > 0 or vehicle.vehicle_type == 2:
		var entry_pos = vehicle.get_interior_entry_position()
		global_position = entry_pos
		current_vehicle = vehicle
		current_seat = null
		current_vehicle_seat = null
		player_state = PlayerState.NORMAL
		is_flying = false
		velocity = vehicle.velocity
		vehicle.vehicle_entered.emit(self, null)
		print("[PlayerController] Abordado %s por la puerta al pasillo interior." % vehicle.vehicle_name)
		if hud:
			hud.set_interaction_prompt("")
		return true

	# Para vehículos convencionales sin pasillo interior, asignar asiento
	var target_seat: VehicleSeat = null
	if preferred_type == VehicleSeat.SeatType.DRIVER:
		var d = vehicle.get_driver_seat()
		if d and not d.is_occupied():
			target_seat = d
		else:
			var pass_seats = vehicle.get_available_passenger_seats()
			if not pass_seats.is_empty():
				target_seat = pass_seats[0]
	else:
		var pass_seats = vehicle.get_available_passenger_seats()
		if not pass_seats.is_empty():
			target_seat = pass_seats[0]
		else:
			var d = vehicle.get_driver_seat()
			if d and not d.is_occupied():
				target_seat = d

	if not target_seat:
		print("[PlayerController] No hay asientos disponibles en '%s'" % vehicle.vehicle_name)
		return false

	return sit_in_seat(target_seat)

## Desciende del vehículo actual hacia la banqueta exterior
func dismount_vehicle() -> bool:
	if is_sitting:
		return stand_up()

	if not current_vehicle:
		return false

	# Si está en movimiento a alta velocidad por carretera, sugerir parada previa
	if current_vehicle.current_speed_kmh > 15.0:
		print("[PlayerController] Vehículo a alta velocidad (%.1f km/h). Use [T] para solicitar parada antes de descender." % current_vehicle.current_speed_kmh)
		if hud:
			hud.set_interaction_prompt("Vehículo en marcha. [T] Solicitar Parada")
		return false

	var exit_pos = current_vehicle.get_exterior_exit_position()
	var veh = current_vehicle

	if network_client and network_client.state == NetworkClient.ConnectionState.CONNECTED:
		var v_id = veh.vehicle_id if "vehicle_id" in veh else 0
		network_client.send_vehicle_exit(v_id, 0)

	veh.exit_vehicle(self)
	current_vehicle = null
	current_vehicle_seat = null
	global_position = exit_pos
	velocity = Vector3.ZERO
	set_collision_layer_value(1, true)
	set_collision_mask_value(1, true)

	if humanoid_scene:
		humanoid_scene.visible = true

	if hud:
		hud.set_interaction_prompt("")

	print("[PlayerController] Descendido del vehículo hacia la banqueta exterior.")
	return true

## Solicita parada en el próximo cruce para el autobús en el que viaja el jugador
func _try_request_bus_stop() -> bool:
	var bus = _get_riding_bus()
	if bus and bus.has_method("request_stop"):
		bus.request_stop()
		if hud:
			hud.set_interaction_prompt("🔔 Timbre: Parada solicitada para el próximo cruce")
		print("[PlayerController] Timbre accionado: Parada solicitada en '%s'" % bus.vehicle_name)
		return true
	return false

## Localiza el autobús de ruta en el que viaja o se encuentra el jugador
func _get_riding_bus() -> RouteVehicle:
	if current_vehicle and current_vehicle is RouteVehicle:
		return current_vehicle as RouteVehicle

	var tree = get_tree()
	if not tree:
		return null

	# Comprobar vehículos registrados en el grupo
	var vehicles = tree.get_nodes_in_group("vehicles")
	for v in vehicles:
		if v is RouteVehicle and v.is_inside_tree():
			var dist = global_position.distance_to(v.global_position)
			if dist < 7.5: # Longitud del Marcopolo Boxer
				return v as RouteVehicle
	return null

## Procesa la sincronización física del jugador mientras está sentado
func _process_sitting(_delta: float) -> void:
	if not is_instance_valid(current_seat):
		stand_up()
		return

	var h_offset: float = 0.45
	if "sit_height_offset" in current_seat:
		h_offset = current_seat.sit_height_offset

	global_position = current_seat.global_position - Vector3(0.0, h_offset, 0.0)
	rotation_degrees.y = current_seat.global_rotation_degrees.y

	if current_vehicle:
		velocity = current_vehicle.velocity
		# Brújula según vehículo
		var v_fwd = -current_vehicle.global_transform.basis.z
		var veh_heading = fposmod(rad_to_deg(atan2(v_fwd.x, -v_fwd.z)), 360.0)

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
	else:
		velocity = Vector3.ZERO

func _process_riding_vehicle(delta: float) -> void:
	if not current_vehicle:
		return

	# Pasajero de pie a bordo del vehículo:
	# Permitir locomoción peatonal en el pasillo sumando la velocidad inercial del vehículo
	var input_dir = _get_input_direction()
	var forward = -global_transform.basis.z
	var right = global_transform.basis.x
	var local_move = (forward * -input_dir.y + right * input_dir.x).normalized() * walk_speed

	velocity = current_vehicle.velocity + local_move

	if not is_on_floor():
		velocity.y -= gravity * delta
	else:
		if velocity.y < 0.0:
			velocity.y = 0.0

	move_and_slide()

	# Confinamiento protector en el pasillo del autobús para evitar salir por desincronización
	var local_pos = current_vehicle.to_local(global_position)
	if absf(local_pos.x) > 1.35:
		local_pos.x = clampf(local_pos.x, -1.25, 1.25)
		global_position = current_vehicle.to_global(local_pos)

func _scan_nearby_interactive_objects(delta: float) -> void:
	_vehicle_scan_timer += delta
	if _vehicle_scan_timer < 0.12:
		return
	_vehicle_scan_timer = 0.0

	_nearby_seat = null
	_nearby_vehicle = null
	_nearby_seat_type = 0
	_nearby_pump_zone = null
	_near_exit_door = false

	var tree = get_tree()
	if not tree:
		return

	var my_pos = global_position

	# 1. Escaneo de asientos cercanos (radio ergonómico ≤ 1.5 m, dist_sq ≤ 2.25)
	if not is_sitting:
		var seats = tree.get_nodes_in_group("seats")
		var min_seat_dist_sq = 2.25 # radio 1.5 m
		for s in seats:
			if s is Node3D and s.is_inside_tree():
				if s.has_method("is_occupied") and s.is_occupied():
					continue

				# Identificar si el asiento pertenece a un vehículo
				var seat_veh: VehicleBase = null
				var parent_node = s.get_parent()
				while parent_node:
					if parent_node is VehicleBase:
						seat_veh = parent_node as VehicleBase
						break
					parent_node = parent_node.get_parent()

				if current_vehicle == null:
					# Desde el exterior: PROHIBIDO interactuar con asientos de vehículos
					if seat_veh != null or s is VehicleSeat:
						continue
				else:
					# A bordo: solo interactuar con asientos de este vehículo
					if seat_veh != current_vehicle:
						continue

				var d_sq = my_pos.distance_squared_to(s.global_position)
				if d_sq < min_seat_dist_sq:
					min_seat_dist_sq = d_sq
					_nearby_seat = s

	# 2. Escaneo de vehículos y puertas
	if current_vehicle == null:
		# Exterior: buscar vehículo accesible exclusivamente por la puerta
		var vehicles = tree.get_nodes_in_group("vehicles")
		for veh in vehicles:
			if veh is VehicleBase and veh.is_inside_tree():
				if veh.doors.size() > 0 or veh.has_method("is_near_boarding_door"):
					if veh.is_near_boarding_door(my_pos, 2.5):
						_nearby_vehicle = veh as VehicleBase
						break
				else:
					# Vehículo particular sin puertas modeladas: proximidad estricta (≤ 2.2 m)
					var d_sq = my_pos.distance_squared_to(veh.global_position)
					if d_sq < 4.84:
						_nearby_vehicle = veh as VehicleBase
						break
	else:
		# A bordo: verificar si está junto a una puerta para descender
		if not is_sitting:
			if current_vehicle.doors.size() > 0 or current_vehicle.has_method("is_near_boarding_door"):
				_near_exit_door = current_vehicle.is_near_boarding_door(my_pos, 2.2)
			else:
				_near_exit_door = true

	# 3. Escaneo de estaciones de servicio (para repostaje [R])
	for pz in get_tree().get_nodes_in_group("pump_zones"):
		if pz is Area3D and pz.is_inside_tree():
			var d_sq = my_pos.distance_squared_to(pz.global_position)
			if d_sq < 25.0:
				_nearby_pump_zone = pz
				break

	# 4. Actualización contextual de indicaciones en el HUD
	if not hud:
		return

	if is_sitting:
		var prompt = "[E] o [Espacio] Levantarse"
		var bus_on_board = _get_riding_bus()
		if bus_on_board:
			prompt += "  |  [T] Solicitar Parada"
		hud.set_interaction_prompt(prompt)
	elif current_vehicle != null:
		if _nearby_seat:
			var s_name = _nearby_seat.seat_name if "seat_name" in _nearby_seat else "Asiento"
			var prompt = "[E] Sentarse en %s" % s_name
			var bus_on_board = _get_riding_bus()
			if bus_on_board:
				prompt += "  |  [T] Solicitar Parada"
			hud.set_interaction_prompt(prompt)
		elif _near_exit_door:
			if current_vehicle.current_speed_kmh > 15.0:
				hud.set_interaction_prompt("Vehículo en marcha (%.0f km/h)  |  [T] Solicitar Parada" % current_vehicle.current_speed_kmh)
			else:
				hud.set_interaction_prompt("[E] Descender a la calle  |  [T] Solicitar Parada")
		else:
			hud.set_interaction_prompt("[T] Solicitar Parada")
	elif _nearby_seat:
		var s_name = _nearby_seat.seat_name if "seat_name" in _nearby_seat else "Asiento"
		hud.set_interaction_prompt("[E] Sentarse en %s" % s_name)
	elif _nearby_vehicle:
		if _nearby_vehicle.doors.size() > 0 or _nearby_vehicle.vehicle_type == 2:
			hud.set_interaction_prompt("[E] Abordar %s por la puerta" % _nearby_vehicle.vehicle_name)
		else:
			var d_seat = _nearby_vehicle.get_driver_seat()
			if d_seat and not d_seat.is_occupied():
				_nearby_seat_type = VehicleSeat.SeatType.DRIVER
				hud.set_interaction_prompt("[E] Conducir %s" % _nearby_vehicle.vehicle_name)
			else:
				var avail_pass = _nearby_vehicle.get_available_passenger_seats()
				if not avail_pass.is_empty():
					_nearby_seat_type = VehicleSeat.SeatType.PASSENGER
					hud.set_interaction_prompt("[E] Abordar como Pasajero en %s" % _nearby_vehicle.vehicle_name)
				else:
					hud.set_interaction_prompt("%s (Lleno)" % _nearby_vehicle.vehicle_name)
	else:
		hud.set_interaction_prompt("")
