extends Camera3D

@export var sensitivity: float = 0.2
@export var speed: float = 30.0

var rot_x: float = 0.0
var rot_y: float = 0.0

func _ready():
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	rot_x = rotation_degrees.x
	rot_y = rotation_degrees.y

func _input(event):
	if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		rot_y -= event.relative.x * sensitivity
		rot_x -= event.relative.y * sensitivity
		rot_x = clamp(rot_x, -89.0, 89.0)
		rotation_degrees = Vector3(rot_x, rot_y, 0)
		
	if event is InputEventKey and event.pressed:
		if event.keycode == KEY_ESCAPE:
			if Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
				Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
			else:
				Input.mouse_mode = Input.MOUSE_MODE_CAPTURED

func _process(delta):
	if Input.mouse_mode != Input.MOUSE_MODE_CAPTURED:
		return
		
	var dir = Vector3.ZERO
	if Input.is_key_pressed(KEY_W) or Input.is_key_pressed(KEY_UP):
		dir -= global_transform.basis.z
	if Input.is_key_pressed(KEY_S) or Input.is_key_pressed(KEY_DOWN):
		dir += global_transform.basis.z
	if Input.is_key_pressed(KEY_A) or Input.is_key_pressed(KEY_LEFT):
		dir -= global_transform.basis.x
	if Input.is_key_pressed(KEY_D) or Input.is_key_pressed(KEY_RIGHT):
		dir += global_transform.basis.x
	if Input.is_key_pressed(KEY_SPACE) or Input.is_key_pressed(KEY_E):
		dir += global_transform.basis.y
	if Input.is_key_pressed(KEY_C) or Input.is_key_pressed(KEY_Q):
		dir -= global_transform.basis.y
		
	# Increase speed if holding Shift
	var active_speed = speed
	if Input.is_key_pressed(KEY_SHIFT):
		active_speed *= 3.0
		
	dir = dir.normalized()
	global_translate(dir * active_speed * delta)
