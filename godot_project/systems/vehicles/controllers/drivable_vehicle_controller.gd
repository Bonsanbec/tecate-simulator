class_name DrivableVehicle
extends "res://systems/vehicles/core/vehicle_base.gd"

## Controlador para Vehículos Conducibles en Tecate Simulator
## Gestiona la entrada interactiva de teclado del conductor, tracción, reversa,
## frenado, amortiguación de viraje y consumo activo sobre la topografía urbana.

@export var handbrake_deceleration: float = 24.0 # m/s^2
@export var min_turn_speed_kmh: float = 1.0     # Umbral mínimo para poder virar

var _steer_input: float = 0.0
var _throttle_input: float = 0.0
var _handbrake_active: bool = false

# Nodos de ruedas visuales para animación procedural
var wheel_fl_mesh: Node3D = null
var wheel_fr_mesh: Node3D = null
var wheel_rl_mesh: Node3D = null
var wheel_rr_mesh: Node3D = null
var _wheel_roll_angle: float = 0.0

func _ready() -> void:
	super._ready()
	_discover_wheel_meshes()

func _discover_wheel_meshes() -> void:
	wheel_fl_mesh = get_node_or_null("VisualRoot/WheelsVisual/Wheel_FL") as Node3D
	wheel_fr_mesh = get_node_or_null("VisualRoot/WheelsVisual/Wheel_FR") as Node3D
	wheel_rl_mesh = get_node_or_null("VisualRoot/WheelsVisual/Wheel_RL") as Node3D
	wheel_rr_mesh = get_node_or_null("VisualRoot/WheelsVisual/Wheel_RR") as Node3D

func _unhandled_input(event: InputEvent) -> void:
	if not has_driver():
		return

	if event is InputEventKey and event.pressed and not event.is_echo():
		if event.keycode == KEY_L:
			toggle_headlights()
		elif event.keycode == KEY_H:
			_play_horn()

func _play_horn() -> void:
	var horn = get_node_or_null("Audio/HornAudio") as AudioStreamPlayer3D
	if horn and not horn.playing:
		horn.play()

func _physics_process(delta: float) -> void:
	# 1. Alineación a la topografía e inclinación de pendientes
	var avg_normal = process_terrain_alignment(delta)

	# 2. Perfil de superficie actual
	var surf_profile = update_surface_profile()

	# 3. Lectura de comandos si hay conductor activo
	if has_driver():
		_read_driver_input()
	else:
		_steer_input = 0.0
		_throttle_input = 0.0
		_handbrake_active = false

	# 4. Proceso de viraje y ángulo de ruedas
	var target_steer = _steer_input * max_steer_angle_deg
	current_steer_angle_deg = move_toward(current_steer_angle_deg, target_steer, steer_speed * max_steer_angle_deg * delta)

	# 5. Dinámica longitudinal: Aceleración, frenado e inercia
	_process_longitudinal_motion(delta, surf_profile)

	# 6. Gravedad
	if not is_on_floor():
		velocity.y -= default_gravity * delta
	else:
		if velocity.y < 0.0:
			velocity.y = 0.0

	move_and_slide()

	# 7. Telemetría de velocidad real
	current_speed_kmh = Vector2(velocity.x, velocity.z).length() * 3.6

	# 8. Animación visual de ruedas
	_update_wheel_visuals(delta)

func _read_driver_input() -> void:
	_steer_input = 0.0
	if Input.is_key_pressed(KEY_A) or Input.is_key_pressed(KEY_LEFT):
		_steer_input += 1.0 # Giro a la izquierda (+yaw en convención Godot)
	if Input.is_key_pressed(KEY_D) or Input.is_key_pressed(KEY_RIGHT):
		_steer_input -= 1.0

	_throttle_input = 0.0
	if Input.is_key_pressed(KEY_W) or Input.is_key_pressed(KEY_UP):
		_throttle_input += 1.0
	if Input.is_key_pressed(KEY_S) or Input.is_key_pressed(KEY_DOWN):
		_throttle_input -= 1.0

	_handbrake_active = Input.is_key_pressed(KEY_SPACE)

func _process_longitudinal_motion(delta: float, surf_profile: SurfaceProfileClass) -> void:
	var forward_dir = -global_transform.basis.z
	var current_forward_speed = velocity.dot(forward_dir)

	var target_accel = 0.0
	var is_accelerating = false

	# Modificadores de superficie
	var eff_friction = surf_profile.friction if surf_profile else 1.0
	var eff_max_speed = (max_speed_kmh / 3.6) * (surf_profile.max_speed_factor if surf_profile else 1.0)
	var eff_rev_speed = (reverse_max_speed_kmh / 3.6) * (surf_profile.max_speed_factor if surf_profile else 1.0)

	# Modificador de pendiente: gravedad a favor o en contra
	# Si el frente apunta hacia arriba en el eje Y, el vehículo experimenta resistencia
	var slope_forward_sin = forward_dir.y
	var slope_gravity_accel = -default_gravity * slope_forward_sin

	if _handbrake_active:
		# Freno de mano: Deceleración agresiva
		current_forward_speed = move_toward(current_forward_speed, 0.0, handbrake_deceleration * eff_friction * delta)
	elif _throttle_input > 0.1: # Acelerando hacia adelante
		if engine_running and not fuel_system.is_empty:
			var slope_penalty = maxf(1.0, 1.0 + (slope_forward_sin * 1.5))
			var fuel_penalty = surf_profile.fuel_penalty_factor if surf_profile else 1.0
			fuel_system.consume(_throttle_input, slope_penalty, fuel_penalty, delta)

			var net_accel = (engine_acceleration * eff_friction) + slope_gravity_accel
			current_forward_speed = move_toward(current_forward_speed, eff_max_speed, maxf(0.5, net_accel) * delta)
			is_accelerating = true
	elif _throttle_input < -0.1: # Frenando o Marcha atrás
		if current_forward_speed > 0.5:
			# Frenando avance frontal
			current_forward_speed = move_toward(current_forward_speed, 0.0, brake_deceleration * eff_friction * delta)
		else:
			# Reversa
			if engine_running and not fuel_system.is_empty:
				var fuel_penalty = surf_profile.fuel_penalty_factor if surf_profile else 1.0
				fuel_system.consume(abs(_throttle_input), 1.0, fuel_penalty, delta)
				current_forward_speed = move_toward(current_forward_speed, -eff_rev_speed, (engine_acceleration * 0.6 * eff_friction) * delta)
				is_accelerating = true
	else:
		# Decaimiento por fricción pasiva y resistencia a la rodadura
		var roll_decay = (coasting_friction + (surf_profile.rolling_resistance * 40.0 if surf_profile else 1.0))
		current_forward_speed = move_toward(current_forward_speed, 0.0, roll_decay * delta)
		# En pendientes libres sin acelerar, deslizar suavemente por gravedad
		if abs(slope_forward_sin) > 0.08:
			current_forward_speed += slope_gravity_accel * 0.4 * delta

	# Viraje cinemático: Solo gira si tiene suficiente velocidad longitudinal
	var speed_ratio = clampf(abs(current_forward_speed) / (eff_max_speed * 0.35), 0.0, 1.0)
	if abs(current_forward_speed) > (min_turn_speed_kmh / 3.6):
		var steer_sign = sign(current_forward_speed)
		var yaw_rate = deg_to_rad(current_steer_angle_deg) * speed_ratio * steer_sign * 1.8
		rotate_y(yaw_rate * delta)

	# Actualizar componentes X y Z de la velocidad preservando la orientación actual
	var new_forward = -global_transform.basis.z
	velocity.x = new_forward.x * current_forward_speed
	velocity.z = new_forward.z * current_forward_speed

func _update_wheel_visuals(delta: float) -> void:
	var fwd_speed = velocity.dot(-global_transform.basis.z)
	var wheel_radius = 0.35 # Radio estimado de la rueda en metros
	var roll_delta = (fwd_speed / wheel_radius) * delta
	_wheel_roll_angle = fmod(_wheel_roll_angle + roll_delta, TAU)

	# Ruedas delanteras: Viraje (Yaw) + Rotación (Pitch)
	var steer_rad = deg_to_rad(current_steer_angle_deg)
	if wheel_fl_mesh:
		wheel_fl_mesh.rotation.y = steer_rad
		wheel_fl_mesh.rotation.x = _wheel_roll_angle
	if wheel_fr_mesh:
		wheel_fr_mesh.rotation.y = steer_rad
		wheel_fr_mesh.rotation.x = _wheel_roll_angle

	# Ruedas traseras: Rotación únicamente
	if wheel_rl_mesh:
		wheel_rl_mesh.rotation.x = _wheel_roll_angle
	if wheel_rr_mesh:
		wheel_rr_mesh.rotation.x = _wheel_roll_angle
