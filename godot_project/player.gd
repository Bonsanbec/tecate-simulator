extends CharacterBody3D

# Walking speeds
@export var walk_speed: float = 10.0
@export var sprint_speed: float = 18.0
@export var jump_velocity: float = 7.5
@export var sensitivity: float = 0.15

# Flight speeds (Minecraft-style)
@export var fly_speed: float = 25.0
@export var fly_sprint_speed: float = 60.0
@export var fly_vertical_speed: float = 18.0

# Smoothness & step climbing
@export var acceleration: float = 14.0
@export var friction: float = 12.0
@export var max_step_height: float = 0.35

# Gravity
var gravity: float = ProjectSettings.get_setting("physics/3d/default_gravity", 9.8)

@onready var camera: Camera3D = $Camera3D

var rot_x: float = 0.0
var rot_y: float = 0.0

var space_press_timer: float = 0.0
var is_flying: bool = false
const DOUBLE_TAP_WINDOW: float = 0.35
const DEFAULT_SNAP_LENGTH: float = 0.3

func _ready():
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	rot_y = rotation_degrees.y
	if camera:
		rot_x = camera.rotation_degrees.x
		
	# Optimal CharacterBody3D settings for large-scale terrain & city meshes
	safe_margin = 0.02
	floor_max_angle = deg_to_rad(65.0)
	floor_constant_speed = true
	floor_stop_on_slope = false
	floor_block_on_wall = true
	floor_snap_length = DEFAULT_SNAP_LENGTH

func _input(event):
	if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		rot_y -= event.relative.x * sensitivity
		rotation_degrees.y = rot_y
		
		rot_x -= event.relative.y * sensitivity
		rot_x = clamp(rot_x, -89.0, 89.0)
		if camera:
			camera.rotation_degrees.x = rot_x
			
	if event is InputEventKey and event.pressed and not event.is_echo():
		if event.keycode == KEY_ESCAPE:
			if Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
				Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
			else:
				Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
				
		if event.keycode == KEY_SPACE or event.is_action_pressed("ui_accept"):
			var current_time = Time.get_ticks_msec() / 1000.0
			# Double-tap Space anywhere (on floor or in air) toggles Minecraft-style flying
			if (current_time - space_press_timer) < DOUBLE_TAP_WINDOW:
				is_flying = !is_flying
				if is_flying:
					velocity = Vector3.ZERO
					print("[Player] Flying enabled")
				else:
					print("[Player] Flying disabled")
				space_press_timer = 0.0
			else:
				space_press_timer = current_time

func _physics_process(delta):
	if is_flying:
		_process_flying(delta)
	else:
		_process_walking(delta)

func _process_flying(delta: float):
	# Shift + on floor lands cleanly
	if is_on_floor() and Input.is_key_pressed(KEY_SHIFT):
		is_flying = false
		print("[Player] Landed, flying disabled")
		return

	# Speed modifier (Ctrl for super fast flight sprint)
	var active_speed = fly_speed
	if Input.is_key_pressed(KEY_CTRL) or Input.is_action_pressed("ui_focus_next"):
		active_speed = fly_sprint_speed

	var input_dir = _get_input_direction()
	
	# Horizontal flight aligned with horizontal view direction
	var forward = -global_transform.basis.z
	var right = global_transform.basis.x
	var move_dir = (forward * -input_dir.y + right * input_dir.x).normalized()
	
	# Vertical flight: Space = UP, Shift = DOWN (Minecraft controls)
	var vert_input = 0.0
	if Input.is_key_pressed(KEY_SPACE) or Input.is_action_pressed("ui_accept"):
		vert_input += 1.0
	if Input.is_key_pressed(KEY_SHIFT) or Input.is_action_pressed("ui_select"):
		vert_input -= 1.0
		
	var target_velocity = move_dir * active_speed
	target_velocity.y = vert_input * (fly_vertical_speed if not (Input.is_key_pressed(KEY_CTRL) or Input.is_action_pressed("ui_focus_next")) else fly_vertical_speed * 1.8)
	
	# Responsive lerp for smooth flying feel
	velocity = velocity.lerp(target_velocity, 10.0 * delta)
	move_and_slide()

func _process_walking(delta: float):
	# Gravity & floor settling
	if not is_on_floor():
		velocity.y -= gravity * delta
	else:
		if velocity.y < 0.0:
			velocity.y = 0.0
		floor_snap_length = DEFAULT_SNAP_LENGTH

	# Jump: Space while on floor
	if (Input.is_key_pressed(KEY_SPACE) or Input.is_action_just_pressed("ui_accept")) and is_on_floor():
		velocity.y = jump_velocity
		floor_snap_length = 0.0  # Temporarily disable snap to jump cleanly

	# Speed modifier: Shift or Ctrl to sprint
	var is_sprinting = Input.is_key_pressed(KEY_SHIFT) or Input.is_key_pressed(KEY_CTRL)
	var active_speed = sprint_speed if is_sprinting else walk_speed

	var input_dir = _get_input_direction()
	var forward = -global_transform.basis.z
	var right = global_transform.basis.x
	var move_dir = (forward * -input_dir.y + right * input_dir.x).normalized()

	# Smooth horizontal acceleration / deceleration
	var target_h_vel = move_dir * active_speed
	var rate = acceleration if move_dir != Vector3.ZERO else friction
	velocity.x = move_toward(velocity.x, target_h_vel.x, rate * active_speed * delta)
	velocity.z = move_toward(velocity.z, target_h_vel.z, rate * active_speed * delta)

	# Step-up (curb / sidewalk climbing)
	if is_on_floor() and move_dir != Vector3.ZERO:
		_check_step_up(delta)

	move_and_slide()

func _get_input_direction() -> Vector2:
	var input_dir = Vector2.ZERO
	if Input.is_key_pressed(KEY_W) or Input.is_key_pressed(KEY_UP) or Input.is_action_pressed("ui_up"):
		input_dir.y -= 1.0
	if Input.is_key_pressed(KEY_S) or Input.is_key_pressed(KEY_DOWN) or Input.is_action_pressed("ui_down"):
		input_dir.y += 1.0
	if Input.is_key_pressed(KEY_A) or Input.is_key_pressed(KEY_LEFT) or Input.is_action_pressed("ui_left"):
		input_dir.x -= 1.0
	if Input.is_key_pressed(KEY_D) or Input.is_key_pressed(KEY_RIGHT) or Input.is_action_pressed("ui_right"):
		input_dir.x += 1.0
	return input_dir

func _check_step_up(delta: float):
	var h_vel = Vector3(velocity.x, 0.0, velocity.z)
	if h_vel.length_squared() < 0.001:
		return

	var h_motion = h_vel * delta
	# Test if horizontal movement would collide with a step/curb (a vertical obstacle)
	var col = KinematicCollision3D.new()
	if test_move(global_transform, h_motion, col):
		# Only step up if the obstacle is actually a steep wall/curb, not the floor itself
		if col.get_normal().y < 0.7:
			var step_xform = global_transform
			step_xform.origin.y += max_step_height
			if not test_move(step_xform, Vector3.ZERO):
				if not test_move(step_xform, h_motion):
					# Find the exact step height by testing downwards
					var down_col = KinematicCollision3D.new()
					if test_move(step_xform, Vector3(0, -max_step_height, 0), down_col):
						var actual_step = max_step_height - down_col.get_travel().length()
						if actual_step > 0.01:
							global_position.y += actual_step + 0.02
					else:
						global_position.y += max_step_height
