class_name FootIKController
extends Node

## Controlador de Cinemática Inversa (Foot IK) y Adaptación al Terreno de Tecate
## Garantiza que los pies se apoyen sobre banquetas, rampas y calles con desniveles
## y alinea la suela del zapato con la normal de la superficie.

@export var enabled: bool = true
@export var ray_length: float = 1.3
@export var foot_height_offset: float = 0.08
@export var max_step_reach: float = 0.35
@export var ik_blend_speed: float = 16.0
@export var align_foot_to_normal: bool = true

var skeleton: Skeleton3D = null
var character_body: CharacterBody3D = null

# Identificadores de huesos en el Skeleton3D
var bone_hips: int = -1
var bone_foot_l: int = -1
var bone_foot_r: int = -1
var bone_toe_l: int = -1
var bone_toe_r: int = -1

# Estados de compensación calculados
var left_foot_ik_offset: float = 0.0
var right_foot_ik_offset: float = 0.0
var left_foot_normal: Vector3 = Vector3.UP
var right_foot_normal: Vector3 = Vector3.UP
var current_pelvic_drop: float = 0.0

# Raycasts para sondeo de suelo
var ray_left: RayCast3D
var ray_right: RayCast3D

func setup(p_character: CharacterBody3D, p_skeleton: Skeleton3D) -> void:
	character_body = p_character
	skeleton = p_skeleton
	if not skeleton:
		push_warning("[FootIKController] Skeleton3D no proporcionado.")
		return

	bone_hips = skeleton.find_bone("Hips")
	bone_foot_l = skeleton.find_bone("Foot.L")
	bone_foot_r = skeleton.find_bone("Foot.R")
	bone_toe_l = skeleton.find_bone("Toes.L")
	bone_toe_r = skeleton.find_bone("Toes.R")

	_create_raycasts()

func _create_raycasts() -> void:
	if not character_body:
		return

	ray_left = RayCast3D.new()
	ray_left.name = "RayCast_Foot_L"
	ray_left.target_position = Vector3(0, -ray_length, 0)
	ray_left.position = Vector3(-0.11, 0.6, 0.0)
	ray_left.enabled = true
	ray_left.collision_mask = 1 # Capa del mundo/terreno
	character_body.add_child(ray_left)

	ray_right = RayCast3D.new()
	ray_right.name = "RayCast_Foot_R"
	ray_right.target_position = Vector3(0, -ray_length, 0)
	ray_right.position = Vector3(0.11, 0.6, 0.0)
	ray_right.enabled = true
	ray_right.collision_mask = 1
	character_body.add_child(ray_right)

func update_ik(delta: float, is_grounded: bool) -> void:
	if not enabled or not skeleton or not character_body:
		return

	if not is_grounded:
		# En el aire o volando: atenuar suavemente compensaciones a cero
		left_foot_ik_offset = lerpf(left_foot_ik_offset, 0.0, ik_blend_speed * delta)
		right_foot_ik_offset = lerpf(right_foot_ik_offset, 0.0, ik_blend_speed * delta)
		current_pelvic_drop = lerpf(current_pelvic_drop, 0.0, ik_blend_speed * delta)
		left_foot_normal = left_foot_normal.lerp(Vector3.UP, ik_blend_speed * delta)
		right_foot_normal = right_foot_normal.lerp(Vector3.UP, ik_blend_speed * delta)
		_apply_bone_poses()
		return

	# Sondeo de impacto pie izquierdo
	var target_offset_l = 0.0
	var target_norm_l = Vector3.UP
	if ray_left and ray_left.is_colliding():
		var hit_point_l = ray_left.get_collision_point()
		var char_base_y = character_body.global_position.y
		var diff_y = hit_point_l.y - char_base_y
		target_offset_l = clampf(diff_y, -max_step_reach, max_step_reach)
		target_norm_l = ray_left.get_collision_normal()

	# Sondeo de impacto pie derecho
	var target_offset_r = 0.0
	var target_norm_r = Vector3.UP
	if ray_right and ray_right.is_colliding():
		var hit_point_r = ray_right.get_collision_point()
		var char_base_y = character_body.global_position.y
		var diff_y = hit_point_r.y - char_base_y
		target_offset_r = clampf(diff_y, -max_step_reach, max_step_reach)
		target_norm_r = ray_right.get_collision_normal()

	# Interpolación de alta suavidad
	left_foot_ik_offset = lerpf(left_foot_ik_offset, target_offset_l, ik_blend_speed * delta)
	right_foot_ik_offset = lerpf(right_foot_ik_offset, target_offset_r, ik_blend_speed * delta)
	left_foot_normal = left_foot_normal.lerp(target_norm_l, ik_blend_speed * delta)
	right_foot_normal = right_foot_normal.lerp(target_norm_r, ik_blend_speed * delta)

	# Descenso Pélvico Dinámico (Pelvic Drop):
	# Si un pie desciende (ej. al bajar la banqueta hacia el arroyo vehicular),
	# la pelvis desciende la mitad de la diferencia para flexionar naturalmente la rodilla superior.
	var lowest_foot = minf(left_foot_ik_offset, right_foot_ik_offset)
	var target_pelvic_drop = 0.0
	if lowest_foot < 0.0:
		target_pelvic_drop = lowest_foot * 0.5
	current_pelvic_drop = lerpf(current_pelvic_drop, target_pelvic_drop, ik_blend_speed * delta)

	_apply_bone_poses()

func _apply_bone_poses() -> void:
	if not skeleton:
		return

	# 1. Aplicar descenso pélvico al hueso Hips
	if bone_hips != -1:
		var hips_pose = skeleton.get_bone_pose_position(bone_hips)
		hips_pose.y = 0.95 + current_pelvic_drop
		skeleton.set_bone_pose_position(bone_hips, hips_pose)

	# 2. Ajuste vertical y rotación del pie izquierdo
	if bone_foot_l != -1:
		var foot_l_pos = skeleton.get_bone_pose_position(bone_foot_l)
		foot_l_pos.y = 0.08 + (left_foot_ik_offset - current_pelvic_drop)
		skeleton.set_bone_pose_position(bone_foot_l, foot_l_pos)

		if align_foot_to_normal and left_foot_normal.is_normalized():
			var char_basis = character_body.global_transform.basis
			var local_norm = char_basis.inverse() * left_foot_normal
			var pitch = -atan2(local_norm.z, local_norm.y)
			var roll = atan2(local_norm.x, local_norm.y)
			var q_align = Quaternion.from_euler(Vector3(clampf(pitch, -0.6, 0.6), 0.0, clampf(roll, -0.4, 0.4)))
			skeleton.set_bone_pose_rotation(bone_foot_l, q_align)

	# 3. Ajuste vertical y rotación del pie derecho
	if bone_foot_r != -1:
		var foot_r_pos = skeleton.get_bone_pose_position(bone_foot_r)
		foot_r_pos.y = 0.08 + (right_foot_ik_offset - current_pelvic_drop)
		skeleton.set_bone_pose_position(bone_foot_r, foot_r_pos)

		if align_foot_to_normal and right_foot_normal.is_normalized():
			var char_basis = character_body.global_transform.basis
			var local_norm = char_basis.inverse() * right_foot_normal
			var pitch = -atan2(local_norm.z, local_norm.y)
			var roll = atan2(local_norm.x, local_norm.y)
			var q_align = Quaternion.from_euler(Vector3(clampf(pitch, -0.6, 0.6), 0.0, clampf(roll, -0.4, 0.4)))
			skeleton.set_bone_pose_rotation(bone_foot_r, q_align)
