extends Node3D

var lat_regex: RegEx
var lon_regex: RegEx

func _ready():
	lat_regex = RegEx.new()
	lat_regex.compile("lat_(\\d+)_(\\d+)")
	lon_regex = RegEx.new()
	lon_regex.compile("lon_(-?\\d+)_(\\d+)")
	
	var terrain_node = get_node_or_null("Terrain")
	var geometry_node = get_node_or_null("Geometry")
	var player_node = get_node_or_null("Player")
	var camera_node = get_node_or_null("Camera3D")
	
	if not terrain_node:
		print("[ApplyShader] Terrain node not found!")
		return
		
	# 1. Hide legacy embedded low-poly road/water meshes inside terrain node
	_hide_legacy_terrain_overlays(terrain_node)

	# 2. Create trimesh colliders ONLY for the actual walkable terrain surface (tinMesh)
	print("[ApplyShader] Creating collision shapes for terrain surface...")
	var tin_mesh = terrain_node.get_node_or_null("tinMesh")
	if tin_mesh and tin_mesh is MeshInstance3D:
		tin_mesh.create_trimesh_collision()

	# 3. Create colliders for elevated structures (Bridges)
	# Note: Roadways and Manzanas are visual decal overlays draped directly over tinMesh.
	# Generating trimesh colliders for them creates overlapping inverted faces that trap the player.
	var bridges_node = get_node_or_null("Bridges")
	if bridges_node:
		print("[ApplyShader] Creating collision shapes for Bridges...")
		_create_visible_colliders_recursive(bridges_node)
	
	# 4. Await physics frames so colliders register in the physics world
	print("[ApplyShader] Waiting for physics server to synchronize...")
	await get_tree().physics_frame
	await get_tree().physics_frame
	
	# 5. Snap player or camera to terrain
	if player_node:
		print("[ApplyShader] Snapping Player to terrain...")
		_snap_player(player_node)
	elif camera_node:
		print("[ApplyShader] Snapping Camera3D to terrain...")
		_snap_camera(camera_node)
		
	# 6. Create colliders for baked building meshes only (skipping sky powerlines, etc.)
	if geometry_node:
		_hide_replaced_buildings(geometry_node)
		print("[ApplyShader] Creating collision shapes for building meshes...")
		_create_building_colliders_recursive(geometry_node)

func _hide_replaced_buildings(node: Node):
	if node is MeshInstance3D:
		var n = node.name
		if n.begins_with("Building_BBVA_") or n.begins_with("Building_HotelTecate_") or n.begins_with("Building_Hotel_Tecate_") or n.begins_with("Building_Ayuntamiento_de_Tecate"):
			node.visible = false
	for child in node.get_children():
		_hide_replaced_buildings(child)

func _hide_legacy_terrain_overlays(node: Node):
	if node is MeshInstance3D:
		var n = node.name
		if n.begins_with("__mergedRoads_") or n.begins_with("water_"):
			node.visible = false
	for child in node.get_children():
		_hide_legacy_terrain_overlays(child)


func _is_transparent_or_textureless(node: Node) -> bool:
	if not (node is MeshInstance3D):
		return false
		
	var name = node.name
	# Billboard trees and forests without alpha channel (rhomboids in the sky)
	if name.begins_with("Tree_") or name.begins_with("Forest_"):
		return true

	# Roofs are textureless and should not be rendered
	if name.begins_with("roof_") or name.begins_with("roofs_"):
		return true

	# Explicitly untextured meshes
	if name.contains("untextured"):
		return true
		
	# Facades block meshes
	if name.begins_with("facades_block_") or name.begins_with("facade_block_"):
		var base_name = name
		if base_name.begins_with("facades_"):
			base_name = base_name.right(base_name.length() - "facades_".length())
		elif base_name.begins_with("facade_"):
			base_name = base_name.right(base_name.length() - "facade_".length())
			
		if base_name.ends_with("_mesh"):
			base_name = base_name.left(base_name.length() - "_mesh".length())
			
		# Dynamically restore coordinate decimal points (e.g. lat_32_57328 -> lat_32.57328)
		base_name = lat_regex.sub(base_name, "lat_$1.$2", true)
		base_name = lon_regex.sub(base_name, "lon_$1.$2", true)
		
		var tex_name = base_name
		if tex_name.ends_with("_png"):
			tex_name = tex_name.left(tex_name.length() - "_png".length()) + ".png"
			
		var albedo_path = "res://assets/blocks/" + tex_name
		var normal_path = "res://assets/blocks/" + tex_name.replace(".png", "_normal_height.png")
		
		if not (ResourceLoader.exists(albedo_path) and ResourceLoader.exists(normal_path)):
			return true
			
	return false

func _create_visible_colliders_recursive(node: Node):
	if node is MeshInstance3D and node.visible:
		if not _is_transparent_or_textureless(node):
			node.create_trimesh_collision()
	for child in node.get_children():
		_create_visible_colliders_recursive(child)

func _create_building_colliders_recursive(node: Node):
	if node is MeshInstance3D and node.visible:
		if node.name.begins_with("Building_") and not _is_transparent_or_textureless(node):
			node.create_trimesh_collision()
	for child in node.get_children():
		_create_building_colliders_recursive(child)

func _snap_meshes_recursive(node: Node):
	if node is MeshInstance3D:
		var name = node.name
		# Only snap roofs and facades
		if name.begins_with("roof_") or name.begins_with("facades_"):
			if _is_transparent_or_textureless(node):
				node.visible = false
			else:
				var mesh = node.mesh
				if mesh:
					var aabb = mesh.get_aabb()
					var local_center = aabb.position + aabb.size / 2.0
					var global_center = node.global_transform * local_center
					
					# Raycast downwards from high above
					var height = _get_terrain_height(global_center.x, global_center.z)
					if height != null:
						# Adjust the Y position of the node
						node.global_position.y = height
					else:
						print("[ApplyShader] Warning: Could not find terrain height for ", name, " at position ", global_center)
					
	for child in node.get_children():
		_snap_meshes_recursive(child)

func _snap_camera(camera: Camera3D):
	var pos = camera.global_position
	var height = _get_terrain_height(pos.x, pos.z)
	if height != null:
		camera.global_position.y = height + 15.0
		print("[ApplyShader] Snapped Camera3D to height: ", camera.global_position.y)

func _snap_player(player: CharacterBody3D):
	var pos = player.global_position
	var height = _get_terrain_height(pos.x, pos.z, [player.get_rid()])
	if height != null:
		player.global_position.y = height + 0.1
		print("[ApplyShader] Snapped Player to height: ", player.global_position.y)

func _get_terrain_height(x: float, z: float, exclude_rids: Array = []):
	var space_state = get_world_3d().direct_space_state
	# Raycast from Y = 2000 down to Y = -2000
	var query = PhysicsRayQueryParameters3D.create(
		Vector3(x, 2000.0, z),
		Vector3(x, -2000.0, z)
	)
	if not exclude_rids.is_empty():
		query.exclude = exclude_rids
	var result = space_state.intersect_ray(query)
	if not result.is_empty():
		return result.position.y
	return null

func _apply_shader_recursive(node: Node, shader: Shader):
	if node is MeshInstance3D:
		var name = node.name
		if _is_transparent_or_textureless(node):
			node.visible = false
		elif (name.begins_with("facades_block_") or name.begins_with("facade_block_")):
			var base_name = name
			if base_name.begins_with("facades_"):
				base_name = base_name.right(base_name.length() - "facades_".length())
			elif base_name.begins_with("facade_"):
				base_name = base_name.right(base_name.length() - "facade_".length())
				
			if base_name.ends_with("_mesh"):
				base_name = base_name.left(base_name.length() - "_mesh".length())
				
			# Dynamically restore coordinate decimal points (e.g. lat_32_57328 -> lat_32.57328)
			base_name = lat_regex.sub(base_name, "lat_$1.$2", true)
			base_name = lon_regex.sub(base_name, "lon_$1.$2", true)
			
			var tex_name = base_name
			# If the name ends with "_png", replace with ".png"
			if tex_name.ends_with("_png"):
				tex_name = tex_name.left(tex_name.length() - "_png".length()) + ".png"
				
			var albedo_path = "res://assets/blocks/" + tex_name
			var normal_path = "res://assets/blocks/" + tex_name.replace(".png", "_normal_height.png")
			
			var albedo_tex = load(albedo_path)
			var normal_tex = load(normal_path)
			
			var mat = ShaderMaterial.new()
			mat.shader = shader
			mat.set_shader_parameter("texture_albedo_roughness", albedo_tex)
			mat.set_shader_parameter("texture_normal_height", normal_tex)
			mat.set_shader_parameter("depth_scale", 0.08)
			
			node.material_override = mat
				
	for child in node.get_children():
		_apply_shader_recursive(child, shader)
