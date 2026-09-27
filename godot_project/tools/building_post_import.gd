@tool
extends EditorScenePostImport

## building_post_import.gd
## Genera colisiones estáticas analíticas y Trimesh precisas en tiempo de importación
## para modelos de edificios y monumentos de Tecate Simulator.

const EXCLUDE_PREFIXES: Array[String] = [
	"Txt_", "Texto_", "Rotulo_", "Panel_Rotulo_", "Silueta_", 
	"Letras_", "Revistas_", "Minisplit_", "Cortinas_", "Toldo_", 
	"Farol_", "Teja_", "Luminaria_", "Ducto_", "Cable_", "Antena_"
]

const EXCLUDE_CONTAINS: Array[String] = [
	"_Txt_", "_Texto_", "_rotulo_", "_letrero_", "revistas", "exhibidor"
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
	
	# Verificar si debe excluirse de colisión física (letreros, rótulos, adornos)
	if _should_exclude(node_name):
		return
		
	var mesh = mesh_node.mesh
	if not mesh:
		return

	# Si ya tiene un StaticBody3D como hijo, evitar duplicar
	for child in mesh_node.get_children():
		if child is StaticBody3D:
			return

	# Crear el StaticBody3D y CollisionShape3D directamente en la escena importada
	var body: StaticBody3D = StaticBody3D.new()
	body.name = node_name + "_StaticBody"
	body.collision_layer = 1
	body.collision_mask = 0
	
	var shape = mesh.create_trimesh_shape()
	if not shape:
		return
		
	var col_shape: CollisionShape3D = CollisionShape3D.new()
	col_shape.name = "Collision"
	col_shape.shape = shape
	
	body.add_child(col_shape)
	mesh_node.add_child(body)
	
	# Asignar owner para persistencia en el recurso empaquetado de importación
	if root_scene:
		body.owner = root_scene
		col_shape.owner = root_scene

func _should_exclude(node_name: String) -> bool:
	for prefix in EXCLUDE_PREFIXES:
		if node_name.begins_with(prefix):
			return true
	for part in EXCLUDE_CONTAINS:
		if node_name.containsn(part):
			return true
	return false
