extends CharacterBody3D

@export var speed: float = 8.0
@export var jump_velocity: float = 6.0
@export var sensitivity: float = 0.15
@export var fly_speed: float = 20.0

# Get the gravity from the project settings to be synced with RigidBody nodes.
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
			# If double-pressed Space in the air within 0.3s, toggle flying
			if not is_on_floor() and (current_time - space_press_timer) < 0.3:
				is_flying = !is_flying
				if is_flying:
					velocity = Vector3.ZERO
					print("[Player] Flying enabled")
				else:
					print("[Player] Flying disabled")
			space_press_timer = current_time

func _physics_process(delta):
	# Handle running modifier (Ctrl)
	var active_speed = speed
	if Input.is_key_pressed(KEY_CTRL):
		active_speed *= 2.0  # Run speed multiplier

	if is_flying:
		# Flying movement
		var input_dir = Vector2.ZERO
		if Input.is_key_pressed(KEY_W) or Input.is_key_pressed(KEY_UP):
			input_dir.y -= 1
		if Input.is_key_pressed(KEY_S) or Input.is_key_pressed(KEY_DOWN):
			input_dir.y += 1
		if Input.is_key_pressed(KEY_A) or Input.is_key_pressed(KEY_LEFT):
			input_dir.x -= 1
		if Input.is_key_pressed(KEY_D) or Input.is_key_pressed(KEY_RIGHT):
			input_dir.x += 1
			
		# Compute direction relative to camera basis (including looking up/down)
		var cam_basis = camera.global_transform.basis
		var direction = (cam_basis.z * input_dir.y + cam_basis.x * input_dir.x).normalized()
		
		# Vertical fly controls
		var fly_up_down = 0.0
		if Input.is_key_pressed(KEY_SPACE):
			fly_up_down += 1.0
		if Input.is_key_pressed(KEY_SHIFT):
			fly_up_down -= 1.0
			
		var fly_velocity = direction * active_speed
		fly_velocity.y += fly_up_down * active_speed
		
		velocity = fly_velocity
		move_and_slide()
		
		# If we touch the floor, disable flying
		if is_on_floor():
			is_flying = false
			print("[Player] Landed, flying disabled")
	else:
		# Walking physics
		# Add the gravity.
		if not is_on_floor():
			velocity.y -= gravity * delta

		# Handle Jump.
		if Input.is_key_pressed(KEY_SPACE) and is_on_floor():
			velocity.y = jump_velocity

		# Get the input direction and handle the movement/deceleration.
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
