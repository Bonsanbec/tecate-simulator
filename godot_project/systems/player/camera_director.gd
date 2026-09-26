class_name CameraDirector3D
extends Node3D

## Director de Cámaras Tripartito (1P, 2P y 3P) para Tecate Simulator
## Gestiona la alternancia fluida con la tecla F5, control de capas visuales
## (Layer Culling para True First Person sin clipping facial), SpringArm colisionable
## y estabilización armónica de cabeceo (Head Bobbing).

signal perspective_changed(new_mode: PerspectiveMode)

enum PerspectiveMode {
	FIRST_PERSON = 0,
	THIRD_PERSON = 1,
	SECOND_PERSON = 2
}

@export var current_mode: PerspectiveMode = PerspectiveMode.FIRST_PERSON
@export var transition_duration: float = 0.22
@export var mouse_sensitivity: float = 0.15

# Parámetros Primera Persona (1P)
@export var eye_height: float = 1.68
@export var eye_forward_offset: float = 0.16
@export var fov_1p: float = 75.0

# Parámetros Tercera Persona (3P)
@export var spring_arm_length: float = 3.2
@export var shoulder_offset: Vector3 = Vector3(0.38, 0.15, 0.0)

# Parámetros Segunda Persona (2P - Observador Frontal)
@export var observer_distance: float = 3.5
@export var observer_height: float = 1.60

var character_body: CharacterBody3D = null
var active_camera: Camera3D = null

# Nodos de cámaras
var cam_1p: Camera3D

var spring_arm_3p: SpringArm3D
var cam_3p: Camera3D

var pivot_2p: Node3D
var cam_2p: Camera3D

# Referencias a mallas para Layer Culling
var mesh_body: MeshInstance3D = null
var mesh_head: MeshInstance3D = null

# Rotación de mirada acumulada
var rot_yaw: float = 0.0
var rot_pitch: float = 0.0

# Estabilización biomecánica de cabeceo (Head Bob)
var bob_phase: float = 0.0
var current_bob_offset: Vector3 = Vector3.ZERO

func setup(p_character: CharacterBody3D, p_mesh_body: MeshInstance3D, p_mesh_head: MeshInstance3D) -> void:
	character_body = p_character
	mesh_body = p_mesh_body
	mesh_head = p_mesh_head

	# Configurar capas visuales en las mallas:
	# Capa 1: Cuerpo, torso, brazos, manos, piernas y zapatos.
	# Capa 2: Cabeza, rostro y cabello.
	if mesh_body:
		mesh_body.layers = 1
		mesh_body.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	if mesh_head:
		mesh_head.layers = 2
		mesh_head.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON

	_build_camera_rig()

	# Si StartScreen está presente y activo, no forzar cámara de jugador para no robar el menú
	var start_screen = character_body.get_parent().get_node_or_null("StartScreen") if character_body and character_body.get_parent() else null
	var menu_active = start_screen.is_menu_active if (start_screen and "is_menu_active" in start_screen) else false

	if not menu_active:
		_apply_perspective_instant(current_mode)
	else:
		active_camera = cam_1p

func _build_camera_rig() -> void:
	# 1. Rig de Primera Persona (1P)
	# Reutilizar o crear Camera3D directamente en character_body para compatibilidad nativa
	var existing_cam = character_body.get_node_or_null("Camera3D") if character_body else null
	if existing_cam and existing_cam is Camera3D:
		cam_1p = existing_cam
	else:
		cam_1p = Camera3D.new()
		cam_1p.name = "Camera3D"
		character_body.add_child(cam_1p)

	cam_1p.position = Vector3(0.0, eye_height, -eye_forward_offset)
	cam_1p.fov = fov_1p
	cam_1p.near = 0.05 # Near plane ultra corto para ver manos sin recorte facial
	cam_1p.far = 16000.0
	# Capa 1 visible (cuerpo/manos/piernas), Capa 2 OCULTA (cabeza)
	cam_1p.cull_mask = 1
	active_camera = cam_1p

	# 2. Rig de Tercera Persona (3P - SpringArm al hombro derecho)
	spring_arm_3p = SpringArm3D.new()
	spring_arm_3p.name = "SpringArm_3P"
	spring_arm_3p.spring_length = spring_arm_length
	spring_arm_3p.margin = 0.2
	spring_arm_3p.position = Vector3(shoulder_offset.x, eye_height + shoulder_offset.y, 0.0)
	var col_shape = SphereShape3D.new()
	col_shape.radius = 0.18
	spring_arm_3p.shape = col_shape
	character_body.add_child(spring_arm_3p)

	cam_3p = Camera3D.new()
	cam_3p.name = "Camera_3P"
	cam_3p.fov = 72.0
	cam_3p.near = 0.1
	cam_3p.far = 16000.0
	cam_3p.cull_mask = 1 | 2 # Cabeza y cuerpo visibles
	spring_arm_3p.add_child(cam_3p)

	# 3. Rig de Segunda Persona (2P - Observador Frontal mirando al avatar)
	pivot_2p = Node3D.new()
	pivot_2p.name = "Pivot_2P"
	pivot_2p.position = Vector3(0.0, observer_height, -observer_distance)
	pivot_2p.rotation_degrees = Vector3(0, 180.0, 0) # Mirando hacia el jugador
	character_body.add_child(pivot_2p)

	cam_2p = Camera3D.new()
	cam_2p.name = "Camera_2P"
	cam_2p.fov = 68.0
	cam_2p.near = 0.1
	cam_2p.far = 16000.0
	cam_2p.cull_mask = 1 | 2 # Cabeza y cuerpo visibles
	pivot_2p.add_child(cam_2p)

func handle_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.is_echo():
		if event.keycode == KEY_F5:
			cycle_perspective()

	if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		rot_yaw -= event.relative.x * mouse_sensitivity
		rot_pitch -= event.relative.y * mouse_sensitivity
		rot_pitch = clampf(rot_pitch, -89.0, 85.0)

		# Aplicar rotación horizontal al personaje
		if character_body:
			character_body.rotation_degrees.y = rot_yaw

		# Aplicar cabeceo vertical a las cámaras
		_update_camera_rotations()

func _update_camera_rotations() -> void:
	if cam_1p:
		cam_1p.rotation_degrees.x = rot_pitch
	if spring_arm_3p:
		spring_arm_3p.rotation_degrees.x = rot_pitch
	if pivot_2p:
		pivot_2p.rotation_degrees.x = -rot_pitch * 0.4

func cycle_perspective() -> void:
	match current_mode:
		PerspectiveMode.FIRST_PERSON:
			set_perspective(PerspectiveMode.THIRD_PERSON)
		PerspectiveMode.THIRD_PERSON:
			set_perspective(PerspectiveMode.SECOND_PERSON)
		PerspectiveMode.SECOND_PERSON:
			set_perspective(PerspectiveMode.FIRST_PERSON)

func set_perspective(new_mode: PerspectiveMode) -> void:
	current_mode = new_mode
	_apply_perspective_instant(current_mode)
	perspective_changed.emit(current_mode)

func _apply_perspective_instant(mode: PerspectiveMode) -> void:
	if cam_1p: cam_1p.current = false
	if cam_3p: cam_3p.current = false
	if cam_2p: cam_2p.current = false

	match mode:
		PerspectiveMode.FIRST_PERSON:
			if cam_1p:
				cam_1p.current = true
				active_camera = cam_1p
		PerspectiveMode.THIRD_PERSON:
			if cam_3p:
				cam_3p.current = true
				active_camera = cam_3p
		PerspectiveMode.SECOND_PERSON:
			if cam_2p:
				cam_2p.current = true
				active_camera = cam_2p

func update_head_bob(delta: float, speed_ratio: float, is_grounded: bool) -> void:
	if not is_grounded or speed_ratio < 0.05:
		current_bob_offset = current_bob_offset.lerp(Vector3.ZERO, 10.0 * delta)
	else:
		# Frecuencia de zancada modulada por velocidad
		var cadence = 7.0 * speed_ratio
		bob_phase += cadence * delta
		var bob_y = sin(bob_phase * 2.0) * 0.028 * speed_ratio
		var bob_x = cos(bob_phase) * 0.018 * speed_ratio
		var target_bob = Vector3(bob_x, bob_y, 0.0)
		current_bob_offset = current_bob_offset.lerp(target_bob, 14.0 * delta)

	if cam_1p:
		cam_1p.position = Vector3(0.0, eye_height, -eye_forward_offset) + current_bob_offset
