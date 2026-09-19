@tool
extends Node3D

@export var post_model: PackedScene = preload("res://assets/poste_nomenclatura_tecate.glb")
const DATA_PATH = "res://assets/nomenclatura_data.json"

func _ready() -> void:
	var mm_node = get_node_or_null("MultiMeshInstance3D") as MultiMeshInstance3D
	if not mm_node:
		return

	if not FileAccess.file_exists(DATA_PATH):
		push_warning("[Nomenclatura] No se encontró el archivo: " + DATA_PATH)
		return

	var file = FileAccess.open(DATA_PATH, FileAccess.READ)
	var content = file.get_as_text()
	var json_data = JSON.parse_string(content)
	if not json_data or not (json_data is Array):
		return

	var count = json_data.size()
	var mm = MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.instance_count = count

	# Extraer la malla canónica de poste_nomenclatura_tecate.glb
	if post_model:
		var tmp_inst = post_model.instantiate()
		var mesh_inst = _find_mesh(tmp_inst)
		if mesh_inst and mesh_inst.mesh:
			mm.mesh = mesh_inst.mesh
		tmp_inst.queue_free()

	for i in range(count):
		var item = json_data[i]
		var pos = Vector3(item[0], item[1], item[2])
		var rot_y = item[3]
		var basis = Basis(Vector3.UP, rot_y)
		var t = Transform3D(basis, pos)
		mm.set_instance_transform(i, t)

	mm_node.multimesh = mm
	print("[Nomenclatura] Instanciados con éxito ", count, " postes urbanos vía MultiMesh.")

func _find_mesh(node: Node) -> MeshInstance3D:
	if node is MeshInstance3D:
		return node
	for child in node.get_children():
		var found = _find_mesh(child)
		if found:
			return found
	return null
