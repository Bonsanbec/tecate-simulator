extends CharacterBody3D

# Minecraft 1:1 Exact Movement Speeds (m/s)
@export var walk_speed: float = 4.317
@export var sprint_speed: float = 5.612
@export var sneak_speed: float = 1.295
@export var jump_velocity: float = 5.5
@export var sensitivity: float = 0.15

# Minecraft Creative/Spectator Flying Speeds (m/s)
@export var fly_speed: float = 10.92
@export var fly_sprint_speed: float = 21.84

var gravity: float = ProjectSettings.get_setting("physics/3d/default_gravity", 9.8)

@onready var camera = $Camera3D

var rot_x: float = 0.0
var rot_y: float = 0.0

var space_press_timer: float = 0.0
var is_flying: bool = false

func _ready():
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	rot_y = rotation_degrees.y
	if camera:
		rot_x = camera.rotation_degrees.x

func _input(event):
	if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		rot_y -= event.relative.x * sensitivity
		rotation_degrees.y = rot_y
		
		rot_x -= event.relative.y * sensitivity
		rot_x = clamp(rot_x, -89.0, 89.0)
		if camera:
			camera.rotation_degrees.x = rot_x
			
	if event is InputEventKey and event.pressed:
		if event.keycode == KEY_ESCAPE:
			if Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
				Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
			else:
				Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
				
		if event.keycode == KEY_SPACE:
			var current_time = Time.get_ticks_msec() / 1000.0
			# Double-press Space within 0.3s toggles Minecraft flight mode
			if not is_on_floor() and (current_time - space_press_timer) < 0.3:
				is_flying = !is_flying
				if is_flying:
					velocity = Vector3.ZERO
					print("[Player] Minecraft Flying Mode ENABLED")
				else:
					print("[Player] Minecraft Flying Mode DISABLED")
			space_press_timer = current_time

func _physics_process(delta):
	var is_sprinting = Input.is_key_pressed(KEY_CTRL)
	var is_sneaking = Input.is_key_pressed(KEY_SHIFT)

	if is_flying:
		# Minecraft Flying Movement Physics
		var active_fly_speed = fly_sprint_speed if is_sprinting else fly_speed
		
		var input_dir = Vector2.ZERO
		if Input.is_key_pressed(KEY_W) or Input.is_key_pressed(KEY_UP):
			input_dir.y -= 1
		if Input.is_key_pressed(KEY_S) or Input.is_key_pressed(KEY_DOWN):
			input_dir.y += 1
		if Input.is_key_pressed(KEY_A) or Input.is_key_pressed(KEY_LEFT):
			input_dir.x -= 1
		if Input.is_key_pressed(KEY_D) or Input.is_key_pressed(KEY_RIGHT):
			input_dir.x += 1
			
		var cam_basis = camera.global_transform.basis
		var direction = (cam_basis.z * input_dir.y + cam_basis.x * input_dir.x).normalized()
		
		var vertical_fly = 0.0
		if Input.is_key_pressed(KEY_SPACE):
			vertical_fly += 1.0
		if Input.is_key_pressed(KEY_SHIFT):
			vertical_fly -= 1.0
			
		var target_vel = direction * active_fly_speed
		target_vel.y += vertical_fly * active_fly_speed
		
		velocity = target_vel
		move_and_slide()
		
		if is_on_floor():
			is_flying = false
			print("[Player] Landed, flying disabled")
	else:
		# Minecraft Walking / Ground Physics
		var active_speed = walk_speed
		if is_sprinting:
			active_speed = sprint_speed
		elif is_sneaking:
			active_speed = sneak_speed

		if not is_on_floor():
			velocity.y -= gravity * delta

		if Input.is_key_pressed(KEY_SPACE) and is_on_floor():
			velocity.y = jump_velocity

		var input_dir = Vector2.ZERO
		if Input.is_key_pressed(KEY_W) or Input.is_key_pressed(KEY_UP):
			input_dir.y -= 1
		if Input.is_key_pressed(KEY_S) or Input.is_key_pressed(KEY_DOWN):
			input_dir.y += 1
		if Input.is_key_pressed(KEY_A) or Input.is_key_pressed(KEY_LEFT):
			input_dir.x -= 1
		if Input.is_key_pressed(KEY_D) or Input.is_key_pressed(KEY_RIGHT):
			input_dir.x += 1

		var direction = (transform.basis * Vector3(input_dir.x, 0, input_dir.y)).normalized()
		if direction:
			velocity.x = direction.x * active_speed
			velocity.z = direction.z * active_speed
		else:
			velocity.x = move_toward(velocity.x, 0, active_speed)
			velocity.z = move_toward(velocity.z, 0, active_speed)

		move_and_slide()
