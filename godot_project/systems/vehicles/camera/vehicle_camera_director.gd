class_name VehicleCameraDirector
extends Node3D

## Director de Cámaras para Vehículos en Tecate Simulator
## Ofrece perspectiva de cabina (1P / subjetiva) y persecución trasera (3P / SpringArm),
## con alternancia fluida mediante tecla F5 y límite angular de visión en cabina.

const VehicleBaseClass = preload("res://systems/vehicles/core/vehicle_base.gd")
const VehicleSeatClass = preload("res://systems/vehicles/core/vehicle_seat.gd")

signal perspective_changed(is_1p: bool)

enum PerspectiveMode {
	FIRST_PERSON = 0,
	THIRD_PERSON = 1
}

@export var current_mode: PerspectiveMode = PerspectiveMode.THIRD_PERSON
@export var mouse_sensitivity: float = 0.15
@export var spring_arm_length: float = 5.2
@export var spring_arm_height: float = 1.8

var vehicle: VehicleBaseClass = null
var current_seat: VehicleSeatClass = null
var is_active: bool = false

var cam_1p: Camera3D
var spring_arm: SpringArm3D
var cam_3p: Camera3D

var rot_yaw: float = 0.0
var rot_pitch: float = 0.0

func _ready() -> void:
	_build_cameras()

func _build_cameras() -> void:
	# 1. Cámara en Primera Persona (1P)
	cam_1p = Camera3D.new()
	cam_1p.name = "VehicleCam1P"
	cam_1p.current = false
	cam_1p.fov = 75.0
	cam_1p.near = 0.1
	cam_1p.far = 16000.0
	add_child(cam_1p)

	# 2. Brazo elástico y Cámara en Tercera Persona (3P)
	spring_arm = SpringArm3D.new()
	spring_arm.name = "VehicleSpringArm3P"
	spring_arm.spring_length = spring_arm_length
	spring_arm.position = Vector3(0.0, spring_arm_height, 0.0)
	spring_arm.collision_mask = 1 # Colisiona con mallas del mundo
	add_child(spring_arm)

	cam_3p = Camera3D.new()
	cam_3p.name = "VehicleCam3P"
	cam_3p.current = false
	cam_3p.fov = 72.0
	cam_3p.near = 0.1
	cam_3p.far = 16000.0
	spring_arm.add_child(cam_3p)

func setup(p_vehicle: VehicleBaseClass, p_seat: VehicleSeatClass) -> void:
	vehicle = p_vehicle
	current_seat = p_seat

	# Posicionar la cámara 1P en el asiento
	if current_seat:
		cam_1p.global_transform = current_seat.global_transform
		cam_1p.position.y += 0.65 # Nivel de los ojos del pasajero/conductor
	elif vehicle:
		var mount_1p = vehicle.get_node_or_null("Cameras/Mount_1P") as Marker3D
		if mount_1p:
			cam_1p.global_transform = mount_1p.global_transform

	rot_yaw = 0.0
	rot_pitch = 0.0

func activate() -> void:
	is_active = true
	_apply_mode()

func deactivate() -> void:
	is_active = false
	if cam_1p: cam_1p.current = false
	if cam_3p: cam_3p.current = false

func toggle_mode() -> void:
	if current_mode == PerspectiveMode.FIRST_PERSON:
		current_mode = PerspectiveMode.THIRD_PERSON
	else:
		current_mode = PerspectiveMode.FIRST_PERSON
	_apply_mode()
	perspective_changed.emit(current_mode == PerspectiveMode.FIRST_PERSON)

func _apply_mode() -> void:
	if not is_active:
		return

	if current_mode == PerspectiveMode.FIRST_PERSON:
		if cam_3p: cam_3p.current = false
		if cam_1p: cam_1p.current = true
	else:
		if cam_1p: cam_1p.current = false
		if cam_3p: cam_3p.current = true

func handle_input(event: InputEvent) -> void:
	if not is_active:
		return

	if event is InputEventKey and event.pressed and not event.is_echo():
		if event.keycode == KEY_F5:
			toggle_mode()
			get_viewport().set_input_as_handled()
			return

	if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		var dx = -event.relative.x * mouse_sensitivity
		var dy = -event.relative.y * mouse_sensitivity

		rot_yaw += dx
		rot_pitch += dy

		if current_mode == PerspectiveMode.FIRST_PERSON:
			# Límites anatómicos de cuello dentro del habitáculo
			rot_yaw = clampf(rot_yaw, -85.0, 85.0)
			rot_pitch = clampf(rot_pitch, -40.0, 35.0)
		else:
			# Vista 3P orbital libre
			rot_pitch = clampf(rot_pitch, -60.0, 20.0)

		_update_camera_rotations()

func _update_camera_rotations() -> void:
	if current_mode == PerspectiveMode.FIRST_PERSON:
		cam_1p.rotation_degrees = Vector3(rot_pitch, rot_yaw, 0.0)
	else:
		spring_arm.rotation_degrees = Vector3(rot_pitch, rot_yaw, 0.0)

func _physics_process(delta: float) -> void:
	if not is_active or not vehicle:
		return

	if current_mode == PerspectiveMode.FIRST_PERSON:
		if current_seat:
			cam_1p.global_position = current_seat.global_position + Vector3(0.0, 0.65, 0.0)
		else:
			var m1p = vehicle.get_node_or_null("Cameras/Mount_1P") as Marker3D
			if m1p:
				cam_1p.global_position = m1p.global_position
			else:
				cam_1p.global_position = vehicle.global_position + Vector3(0.0, 1.2, 0.0)
	else:
		# Centrar el SpringArm suavemente sobre el vehículo
		spring_arm.global_position = spring_arm.global_position.lerp(vehicle.global_position + Vector3(0.0, spring_arm_height, 0.0), 16.0 * delta)
