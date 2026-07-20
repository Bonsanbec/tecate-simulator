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
		
	# 1. Create trimesh colliders for terrain meshes
	print("[ApplyShader] Creating collision shapes for terrain meshes...")
	_create_colliders_recursive(terrain_node)
	
	# 2. Await physics frames so terrain colliders register in physics engine
	print("[ApplyShader] Waiting for physics server to synchronize...")
	await get_tree().physics_frame
	await get_tree().physics_frame
	
	# 3. Load manzana GLTFs if available and not already in tree
	if geometry_node:
		_load_manzana_gltfs(geometry_node)
	
	# 4. Snap player or camera to terrain height
	if player_node:
		print("[ApplyShader] Snapping Player to terrain...")
		_snap_player(player_node)
	elif camera_node:
		print("[ApplyShader] Snapping Camera3D to terrain...")
		_snap_camera(camera_node)
		
	# 5. Snap building meshes to terrain height
	if geometry_node:
		print("[ApplyShader] Snapping building meshes to terrain height...")
		_snap_building_meshes_recursive(geometry_node)
		
	# 6. Create colliders for building meshes after snapping
	if geometry_node:
		print("[ApplyShader] Creating collision shapes for building meshes...")
		_create_colliders_recursive(geometry_node)
		
	# 7. Apply facade shaders / fallback materials to building meshes
	var shader = load("res://shaders/facade_pom.gdshader")
	if geometry_node:
		print("[ApplyShader] Applying materials & shaders to building meshes...")
		_apply_materials_recursive(geometry_node, shader)
		
	# 8. Instantiate 3D building name tags from manifest
	_instantiate_building_tags()

func _load_manzana_gltfs(parent_node: Node):
	var manifest_path = "res://assets/blocks/manzana_manifest.json"
	if not FileAccess.file_exists(manifest_path):
		print("[ApplyShader] No manzana manifest found at ", manifest_path)
		return
		
	var f = FileAccess.open(manifest_path, FileAccess.READ)
	var json_str = f.get_as_text()
	f.close()
	
	var json = JSON.new()
	if json.parse(json_str) == OK:
		var manifest = json.data
		print("[ApplyShader] Loading manzana GLTFs from manifest (", manifest.size(), " manzanas)...")
		var loaded_count = 0
		for manzana_id in manifest.keys():
			var minfo = manifest[manzana_id]
			var gltf_path = minfo.get("gltf_path", "")
			if ResourceLoader.exists(gltf_path):
				# Sanitize node name (replace dots with underscores to avoid NodePath issues)
				var clean_name = manzana_id.replace(".", "_")
				if not parent_node.has_node(clean_name):
					var scene = load(gltf_path)
					if scene:
						var inst = scene.instantiate()
						inst.name = clean_name
						parent_node.add_child(inst)
						loaded_count += 1
		print("[ApplyShader] Loaded ", loaded_count, " manzana GLTF scenes into Geometry node.")

func _snap_building_meshes_recursive(node: Node):
	if node is MeshInstance3D:
		var mesh = node.mesh
		if mesh:
			var aabb = mesh.get_aabb()
			var local_center = aabb.position + aabb.size / 2.0
			var global_center = node.global_transform * local_center
			
			var ground_h = _get_terrain_height(global_center.x, global_center.z)
			if ground_h != null:
				# Align bottom of mesh (min Y) to terrain ground height
				var min_y_offset = (aabb.position.y) * node.global_transform.basis.get_scale().y
				node.global_position.y = ground_h - min_y_offset
				
	for child in node.get_children():
		_snap_building_meshes_recursive(child)

func _instantiate_building_tags():
	var manifest_path = "res://assets/blocks/manzana_manifest.json"
	if not FileAccess.file_exists(manifest_path):
		return
		
	var f = FileAccess.open(manifest_path, FileAccess.READ)
	var json_str = f.get_as_text()
	f.close()
	
	var json = JSON.new()
	if json.parse(json_str) != OK:
		return
		
	var manifest = json.data
	var tags_container = get_node_or_null("BuildingTags")
	if not tags_container:
		tags_container = Node3D.new()
		tags_container.name = "BuildingTags"
		add_child(tags_container)
		
	print("[ApplyShader] Instantiating 3D building name tags...")
	var tag_count = 0
	for manzana_id in manifest.keys():
		var minfo = manifest[manzana_id]
		var buildings = minfo.get("buildings", [])
		for b in buildings:
			var label_text = b.get("label", "")
			var tag_pos_arr = b.get("tag_position", [0, 0, 0])
			if label_text != "":
				# Raycast terrain height at tag X, Z location
				var ground_h = _get_terrain_height(tag_pos_arr[0], tag_pos_arr[2])
				var tag_y = (ground_h if ground_h != null else 405.0) + b.get("height_m", 5.0) + 2.0
				
				var lbl = Label3D.new()
				lbl.text = label_text
				lbl.position = Vector3(tag_pos_arr[0], tag_y, tag_pos_arr[2])
				lbl.billboard = BaseMaterial3D.BILLBOARD_ENABLED
				lbl.font_size = 48
				lbl.outline_size = 12
				lbl.outline_render_priority = 1
				lbl.no_depth_test = true
				lbl.modulate = Color(1.0, 1.0, 1.0, 1.0)
				tags_container.add_child(lbl)
				tag_count += 1
				
	print("[ApplyShader] Instantiated ", tag_count, " 3D building tags.")

func _create_colliders_recursive(node: Node):
	if node is MeshInstance3D:
		node.create_trimesh_collision()
	for child in node.get_children():
		_create_colliders_recursive(child)

func _snap_camera(camera: Camera3D):
	var pos = camera.global_position
	var height = _get_terrain_height(pos.x, pos.z)
	if height != null:
		camera.global_position.y = height + 15.0
		print("[ApplyShader] Snapped Camera3D to height: ", camera.global_position.y)

func _snap_player(player: CharacterBody3D):
	var pos = player.global_position
	var height = _get_terrain_height(pos.x, pos.z)
	if height != null:
		player.global_position.y = height + 2.0
		print("[ApplyShader] Snapped Player to height: ", player.global_position.y)

func _get_terrain_height(x: float, z: float):
	var space_state = get_world_3d().direct_space_state
	var query = PhysicsRayQueryParameters3D.create(
		Vector3(x, 2000.0, z),
		Vector3(x, -2000.0, z)
	)
	var result = space_state.intersect_ray(query)
	if not result.is_empty():
		return result.position.y
	return null

func _apply_materials_recursive(node: Node, shader: Shader):
	if node is MeshInstance3D:
		node.visible = true
		
		var name = node.name
		var applied_shader = false
		
		if (name.begins_with("facades_block_") or name.begins_with("facade_block_")):
			var base_name = name
			if base_name.begins_with("facades_"):
				base_name = base_name.right(base_name.length() - "facades_".length())
			elif base_name.begins_with("facade_"):
				base_name = base_name.right(base_name.length() - "facade_".length())
				
			if base_name.ends_with("_mesh"):
				base_name = base_name.left(base_name.length() - "_mesh".length())
				
			base_name = lat_regex.sub(base_name, "lat_$1.$2", true)
			base_name = lon_regex.sub(base_name, "lon_$1.$2", true)
			
			var tex_name = base_name
			if tex_name.ends_with("_png"):
				tex_name = tex_name.left(tex_name.length() - "_png".length()) + ".png"
				
			var albedo_path = "res://assets/blocks/" + tex_name
			var normal_path = "res://assets/blocks/" + tex_name.replace(".png", "_normal_height.png")
			
			if ResourceLoader.exists(albedo_path) and ResourceLoader.exists(normal_path) and shader:
				var albedo_tex = load(albedo_path)
				var normal_tex = load(normal_path)
				
				var mat = ShaderMaterial.new()
				mat.shader = shader
				mat.set_shader_parameter("texture_albedo_roughness", albedo_tex)
				mat.set_shader_parameter("texture_normal_height", normal_tex)
				mat.set_shader_parameter("depth_scale", 0.08)
				
				node.material_override = mat
				applied_shader = true
				
		# Fallback PBR material for textureless or untextured buildings/roofs so they render cleanly
		if not applied_shader and node.material_override == null:
			var fallback_mat = StandardMaterial3D.new()
			fallback_mat.albedo_color = Color(0.85, 0.85, 0.88)
			fallback_mat.roughness = 0.8
			node.material_override = fallback_mat

	for child in node.get_children():
		_apply_materials_recursive(child, shader)
