@tool
extends EditorScenePostImport

## vehicle_post_import.gd
## Genera colisiones estáticas y de plataforma analíticas y Trimesh en tiempo de importación
## para modelos vehiculares de Tecate Simulator (ej. Autobús El Hongo).
## Crea cuerpos físicos (AnimatableBody3D para soporte nativo de plataforma móvil inercial)
## a partir de las submallas estructurales (piso interior, carrocería, techo, asientos, tableros)
## y excluye submallas decorativas, rótulos, vidrios, calaveras y tornillería.

const EXCLUDE_PREFIXES: Array[String] = [
	"Txt_", "Texto_", "Rotulo_", "Panel_Rotulo_", "Silueta_", 
	"Letras_", "Bus_Rutero_", "Bus_Limpiaparabrisas", "Bus_Parrilla_Cromos_",
	"Bus_Tuercas_", "Bus_Calaveras_", "Bus_Faros_", "Bus_Galibo_", 
	"Bus_Rines_", "Bus_Neumaticos_", "Bus_Interior_Pasamanos", "Bus_Guardafangos_"
]

const EXCLUDE_CONTAINS: Array[String] = [
	"_Txt_", "_Texto_", "_rotulo_", "_letrero_", "Vidrios", "Parabrisas", "Cristal", "Canceleria", "Textura_"
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
	
	# 1. Verificar exclusiones por nombre de objeto
	if _should_exclude_node(node_name):
		return
		
	var mesh = mesh_node.mesh
	if not mesh:
		return

	# Si ya tiene un cuerpo de colisión como hijo, evitar duplicar
	for child in mesh_node.get_children():
		if child is StaticBody3D:
			return

	# 2. Construir colisionador trimesh cóncavo exacto de la submalla
	var shape: Shape3D = mesh.create_trimesh_shape()
	if not shape:
		return

	# 3. Crear AnimatableBody3D para soporte nativo de plataforma móvil
	# Esto permite que el jugador camine sobre el piso del vehículo en movimiento
	# y sincronice inercia automáticamente mediante CharacterBody3D.get_platform_velocity()
	var body: AnimatableBody3D = AnimatableBody3D.new()
	body.name = node_name + "_ColBody"
	body.collision_layer = 1 # Capa 1: Sólido para el jugador a pie y el entorno
	body.collision_mask = 0
	body.sync_to_physics = false

	var col_shape: CollisionShape3D = CollisionShape3D.new()
	col_shape.name = "Collision"
	col_shape.shape = shape
	
	body.add_child(col_shape)
	mesh_node.add_child(body)
	
	# Asignar owner para persistencia en el recurso empaquetado de importación
	if root_scene:
		body.owner = root_scene
		col_shape.owner = root_scene
	
	print("[VehiclePostImport] Generado colisionador para submalla: %s" % node_name)

func _should_exclude_node(node_name: String) -> bool:
	for prefix in EXCLUDE_PREFIXES:
		if node_name.begins_with(prefix):
			return true
	for part in EXCLUDE_CONTAINS:
		if node_name.containsn(part):
			return true
	return false
