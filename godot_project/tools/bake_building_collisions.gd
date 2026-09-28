@tool
extends SceneTree

## bake_building_collisions.gd
## Genera escenas .tscn estáticas con colisionadores Trimesh exactos (1:1)
## derivados directamente de las submallas estructurales del archivo .glb.
## Excluye de forma generalizada rótulos tipográficos, adornos y agua.

const EXCLUDE_PREFIXES: Array[String] = [
	"Txt_", "Texto_", "Rotulo_", "Panel_Rotulo_", "Silueta_", 
	"Letras_", "Revistas_", "Minisplit_", "Cortinas_", "Toldo_", 
	"Farol_", "Teja_", "Luminaria_", "Ducto_", "Cable_", "Antena_"
]

const EXCLUDE_CONTAINS: Array[String] = [
	"_Txt_", "_Texto_", "_rotulo_", "_letrero_", "revistas", "exhibidor"
]

const WATER_KEYWORDS: Array[String] = [
	"agua", "water", "waterway", "chorro", "fluid", "liquid", 
	"stream", "river", "rio", "lake", "lago", "ocean", "oceano", 
	"mar", "splash", "estanque_agua", "fuente_agua"
]

func _init():
	print("==================================================================")
	print("INICIANDO HORNEADO ESTÁTICO DE COLISIONES EN ARCHIVOS .TSCN")
	print("==================================================================")
	
	var targets = [
		{"glb": "res://assets/kiosko_parque_hidalgo.glb", "tscn": "res://assets/kiosko_parque_hidalgo.tscn", "root_name": "Kiosko_Parque_Hidalgo", "model_node": "Kiosko_Model"},
		{"glb": "res://assets/fuente_parque_hidalgo.glb", "tscn": "res://assets/fuente_parque_hidalgo.tscn", "root_name": "Fuente_Parque_Hidalgo", "model_node": "VisualMesh"},
		{"glb": "res://assets/parque_miguel_hidalgo.glb", "tscn": "res://assets/parque_miguel_hidalgo.tscn", "root_name": "ParqueMiguelHidalgo", "model_node": "VisualMesh"},
		{"glb": "res://assets/palacio_municipal_2009.glb", "tscn": "res://assets/palacio_municipal_2009.tscn", "root_name": "PalacioMunicipal2009", "model_node": "ModelInstance"},
		{"glb": "res://assets/buildings/bbva_tecate_centro.glb", "tscn": "res://assets/buildings/bbva_tecate_centro.tscn", "root_name": "BBVA_Tecate", "model_node": "ModelInstance"},
		{"glb": "res://assets/buildings/edificio_cardenas_33.glb", "tscn": "res://assets/buildings/edificio_cardenas_33.tscn", "root_name": "Edificio_Cardenas_33", "model_node": "ModelInstance"},
		{"glb": "res://assets/buildings/edificio_cardenas_25.glb", "tscn": "res://assets/buildings/edificio_cardenas_25.tscn", "root_name": "Edificio_Cardenas_25", "model_node": "ModelInstance"},
		{"glb": "res://assets/buildings/hotel_tecate.glb", "tscn": "res://assets/buildings/hotel_tecate.tscn", "root_name": "Hotel_Tecate", "model_node": "ModelInstance"},
		{"glb": "res://assets/buildings/edificio_juarez_235.glb", "tscn": "res://assets/buildings/edificio_juarez_235.tscn", "root_name": "Edificio_Juarez_235", "model_node": "ModelInstance"},
		{"glb": "res://assets/buildings/edificio_continuo_la_panza.glb", "tscn": "res://assets/buildings/edificio_continuo_la_panza.tscn", "root_name": "Continuo_La_Panza", "model_node": "ModelInstance"},
		{"glb": "res://assets/buildings/manzana_central_2009.glb", "tscn": "res://assets/buildings/manzana_central_2009.tscn", "root_name": "Manzana_Central_2009", "model_node": "MeshInstance"}
	]
	
	for item in targets:
		_bake_target(item)
		
	print("\n✓ HORNEADO ESTÁTICO COMPLETADO EXITOSAMENTE.")
	print("==================================================================")
	quit(0)

func _bake_target(item: Dictionary) -> void:
	var glb_path = item["glb"]
	var tscn_path = item["tscn"]
	var root_name = item["root_name"]
	var model_name = item["model_node"]
	
	print("\n>>> Procesando: ", tscn_path)
	var glb_res = load(glb_path) as PackedScene
	if not glb_res:
		push_error("No se pudo cargar: " + glb_path)
		return
		
	var model_inst = glb_res.instantiate()
	
	# Raíz de la nueva escena .tscn
	var root = Node3D.new()
	root.name = root_name
	
	# Instanciar el modelo visual como hijo preservando el PackedScene de origen
	model_inst.name = model_name
	model_inst.scene_file_path = glb_path
	root.add_child(model_inst)
	model_inst.owner = root
	
	# Crear StaticBody3D contenedor de colisiones
	var body = StaticBody3D.new()
	body.name = "CollisionStructure"
	body.collision_layer = 1
	body.collision_mask = 0
	root.add_child(body)
	body.owner = root
	
	var counter = [0]
	_extract_structural_shapes_recursive(model_inst, body, root, counter)
	
	print("    Colisiones estructurales creadas: ", counter[0])
	
	# Empaquetar y guardar en disco
	var packed = PackedScene.new()
	var err = packed.pack(root)
	if err != OK:
		push_error("Error empaquetando escena: " + str(err))
		root.queue_free()
		return
		
	var save_err = ResourceSaver.save(packed, tscn_path)
	if save_err != OK:
		push_error("Error guardando escena: " + str(save_err))
	else:
		print("    [GUARDADO OK] ", tscn_path)
		
	root.queue_free()

func _extract_structural_shapes_recursive(node: Node, body: StaticBody3D, root: Node, counter: Array) -> void:
	if node is MeshInstance3D:
		var name = node.name
		if not _should_exclude_node(name):
			var shape = _build_filtered_trimesh_shape(node)
			if shape:
				var col_shape = CollisionShape3D.new()
				col_shape.name = "Col_" + name
				col_shape.shape = shape
				
				# La transformación del colisionador respeta la jerarquía local relativa a root
				var xform = _get_relative_transform(node, root)
				col_shape.transform = xform
				
				body.add_child(col_shape)
				col_shape.owner = root
				counter[0] += 1
				
	for child in node.get_children():
		_extract_structural_shapes_recursive(child, body, root, counter)

func _get_relative_transform(child: Node3D, ancestor: Node) -> Transform3D:
	var t: Transform3D = Transform3D.IDENTITY
	var cur: Node = child
	while cur != ancestor and cur != null:
		if cur is Node3D:
			t = cur.transform * t
		cur = cur.get_parent()
	return t

func _should_exclude_node(node_name: String) -> bool:
	for prefix in EXCLUDE_PREFIXES:
		if node_name.begins_with(prefix):
			return true
	for part in EXCLUDE_CONTAINS:
		if node_name.containsn(part):
			return true
	if _is_water_keyword(node_name):
		return true
	return false

func _is_water_keyword(text: String) -> bool:
	var lower = text.to_lower()
	for kw in WATER_KEYWORDS:
		if lower.contains(kw):
			return true
	return false

func _build_filtered_trimesh_shape(mesh_node: MeshInstance3D) -> Shape3D:
	var mesh = mesh_node.mesh
	if not mesh:
		return null
		
	var surface_count = mesh.get_surface_count()
	if surface_count == 0:
		return null
		
	var has_water = false
	for s in range(surface_count):
		var mat = mesh.surface_get_material(s)
		if not mat:
			mat = mesh_node.get_active_material(s)
		if mat:
			var mat_name = mat.resource_name if mat.resource_name != "" else mat.name
			if _is_water_keyword(mat_name):
				has_water = true
				break
				
	if not has_water:
		return mesh.create_trimesh_shape()
		
	var faces = PackedVector3Array()
	var any_solid = false
	
	for s in range(surface_count):
		var mat = mesh.surface_get_material(s)
		if not mat:
			mat = mesh_node.get_active_material(s)
		if mat:
			var mat_name = mat.resource_name if mat.resource_name != "" else mat.name
			if _is_water_keyword(mat_name):
				continue
				
		var arrays = mesh.surface_get_arrays(s)
		if arrays.is_empty():
			continue
			
		var verts = arrays[Mesh.ARRAY_VERTEX]
		var indices = arrays[Mesh.ARRAY_INDEX]
		
		if verts.is_empty():
			continue
			
		any_solid = true
		if not indices.is_empty():
			for idx in indices:
				faces.append(verts[idx])
		else:
			faces.append_array(verts)
			
	if not any_solid or faces.is_empty():
		return null
		
	var shape = ConcavePolygonShape3D.new()
	shape.set_faces(faces)
	return shape
