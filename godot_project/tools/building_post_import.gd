@tool
extends EditorScenePostImport

## building_post_import.gd
## Genera colisiones estáticas analíticas y Trimesh precisas en tiempo de importación
## para modelos de edificios, mobiliario y monumentos de Tecate Simulator.
## Excluye de colisión de forma generalizada rótulos tipográficos, adornos y cuerpos de agua/fluidos.

const EXCLUDE_PREFIXES: Array[String] = [
	"Txt_", "Texto_", "Rotulo_", "Panel_Rotulo_", "Silueta_", 
	"Letras_", "Revistas_", "Minisplit_", "Cortinas_", "Toldo_", 
	"Farol_", "Teja_", "Luminaria_", "Ducto_", "Cable_", "Antena_"
]

const EXCLUDE_CONTAINS: Array[String] = [
	"_Txt_", "_Texto_", "_rotulo_", "_letrero_", "revistas", "exhibidor"
]

## Palabras clave generalizadas para identificar cuerpos y superficies de agua / fluidos
const WATER_KEYWORDS: Array[String] = [
	"agua", "water", "waterway", "chorro", "fluid", "liquid", 
	"stream", "river", "rio", "lake", "lago", "ocean", "oceano", 
	"mar", "splash", "estanque_agua", "fuente_agua"
]

func _post_import(scene: Node) -> Object:
	_process_node_recursive(scene, scene)
	return scene

func _process_node_recursive(node: Node, root_scene: Node) -> void:
	if node is MeshInstance3D:
		_process_mesh_instance(node, root_scene)
		
	for child in node.get_children():
		_process_node_recursive(child, root_scene)

func _process_mesh_instance(mesh_node: MeshInstance3D, root_scene: Node) -> void:
	var node_name: String = mesh_node.name
	
	# 1. Verificar exclusiones por nombre de objeto (rótulos, adornos o cuerpos de agua completos)
	if _should_exclude_node(node_name):
		return
		
	var mesh = mesh_node.mesh
	if not mesh:
		return

	# Si ya tiene un StaticBody3D como hijo, evitar duplicar
	for child in mesh_node.get_children():
		if child is StaticBody3D:
			return

	# 2. Construir colisionador cóncavo (Trimesh) filtrando superficies de agua
	var shape: Shape3D = _build_filtered_trimesh_shape(mesh_node)
	if not shape:
		return

	# 3. Crear el StaticBody3D y CollisionShape3D directamente en la escena importada
	var body: StaticBody3D = StaticBody3D.new()
	body.name = node_name + "_StaticBody"
	body.collision_layer = 1
	body.collision_mask = 0
	
	var col_shape: CollisionShape3D = CollisionShape3D.new()
	col_shape.name = "Collision"
	col_shape.shape = shape
	
	body.add_child(col_shape)
	mesh_node.add_child(body)
	
	# Asignar owner para persistencia en el recurso empaquetado de importación
	if root_scene:
		body.owner = root_scene
		col_shape.owner = root_scene

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
	var lower: String = text.to_lower()
	for kw in WATER_KEYWORDS:
		if lower.contains(kw):
			return true
	return false

## Construye la forma Trimesh omitiendo cualquier superficie cuyo material indique agua o fluidos
func _build_filtered_trimesh_shape(mesh_node: MeshInstance3D) -> Shape3D:
	var mesh = mesh_node.mesh
	if not mesh:
		return null
		
	var surface_count: int = mesh.get_surface_count()
	if surface_count == 0:
		return null
		
	# Verificar si alguna superficie tiene material de agua
	var has_water_surfaces: bool = false
	for s in range(surface_count):
		var mat = mesh.surface_get_material(s)
		if not mat:
			mat = mesh_node.get_active_material(s)
		if mat:
			var mat_name: String = mat.resource_name if mat.resource_name != "" else mat.name
			if _is_water_keyword(mat_name):
				has_water_surfaces = true
				break
				
	# Si no contiene superficies de agua, podemos usar la forma trimesh directa de la malla
	if not has_water_surfaces:
		return mesh.create_trimesh_shape()
		
	# Si contiene superficies de agua, extraer manualmente sólo las caras de superficies sólidas
	var faces: PackedVector3Array = PackedVector3Array()
	var any_solid_surface: bool = false
	
	for s in range(surface_count):
		var mat = mesh.surface_get_material(s)
		if not mat:
			mat = mesh_node.get_active_material(s)
		if mat:
			var mat_name: String = mat.resource_name if mat.resource_name != "" else mat.name
			if _is_water_keyword(mat_name):
				continue # Excluir superficie de agua
				
		var arrays: Array = mesh.surface_get_arrays(s)
		if arrays.is_empty():
			continue
			
		var verts: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
		var indices: PackedInt32Array = arrays[Mesh.ARRAY_INDEX]
		
		if verts.is_empty():
			continue
			
		any_solid_surface = true
		
		if not indices.is_empty():
			for idx in indices:
				faces.append(verts[idx])
		else:
			faces.append_array(verts)
			
	if not any_solid_surface or faces.is_empty():
		return null
		
	var shape: ConcavePolygonShape3D = ConcavePolygonShape3D.new()
	shape.set_faces(faces)
	return shape
