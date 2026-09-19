@tool
extends Node3D

@export var post_model: PackedScene = preload("res://assets/poste_nomenclatura_tecate.glb")
const DATA_PATH = "res://assets/nomenclatura_data.json"

# Parámetros de Culling y Rendimiento Espacial
# Chunks espaciales de 300m requieren un rango de visibilidad >= 300m para no descartar esquinas cercanas
const TEXT_VISIBILITY_END = 300.0       # Descarte de textos e iconos a más de 300m
const TEXT_VISIBILITY_MARGIN = 35.0     # Fade out suave de 265m a 300m
const POST_VISIBILITY_END = 300.0       # Descarte de postes a más de 300m
const POST_VISIBILITY_MARGIN = 35.0     # Fade out suave de 265m a 300m
const POST_CHUNK_SIZE = 350.0           # Tamaño de cuadrante espacial para postes

func _ready() -> void:
	# 1. Configurar culling por distancia en los cuadrantes de Textos e Íconos
	_apply_visibility_culling(get_node_or_null("TextosBaked"), TEXT_VISIBILITY_END, TEXT_VISIBILITY_MARGIN)
	_apply_visibility_culling(get_node_or_null("IconosBaked"), TEXT_VISIBILITY_END, TEXT_VISIBILITY_MARGIN)

	# 2. Cargar e instanciar los postes con partición espacial MultiMesh
	_setup_partitioned_postes()

func _apply_visibility_culling(parent_node: Node, max_dist: float, margin: float) -> void:
	if not parent_node:
		return
	if parent_node is GeometryInstance3D:
		parent_node.visibility_range_end = max_dist
		parent_node.visibility_range_end_margin = margin
		parent_node.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_SELF
	for child in parent_node.get_children():
		_apply_visibility_culling(child, max_dist, margin)

func _setup_partitioned_postes() -> void:
	# Limpiar o deshabilitar nodo legacy si existe
	var legacy_mm = get_node_or_null("MultiMeshInstance3D")
	if legacy_mm:
		legacy_mm.visible = false
		legacy_mm.multimesh = null

	var container = get_node_or_null("PostesChunks")
	if not container:
		container = Node3D.new()
		container.name = "PostesChunks"
		add_child(container)
	else:
		for ch in container.get_children():
			ch.queue_free()

	if not FileAccess.file_exists(DATA_PATH):
		push_warning("[Nomenclatura] No se encontró el archivo: " + DATA_PATH)
		return

	var file = FileAccess.open(DATA_PATH, FileAccess.READ)
	var content = file.get_as_text()
	var json_data = JSON.parse_string(content)
	if not json_data or not (json_data is Array):
		return

	# Extraer la malla canónica de poste_nomenclatura_tecate.glb
	var canonical_mesh: Mesh = null
	if post_model:
		var tmp_inst = post_model.instantiate()
		var mesh_inst = _find_mesh(tmp_inst)
		if mesh_inst and mesh_inst.mesh:
			canonical_mesh = mesh_inst.mesh
		tmp_inst.queue_free()

	if not canonical_mesh:
		push_warning("[Nomenclatura] No se pudo obtener la malla canónica del poste.")
		return

	# Agrupar postes en cuadrantes espaciales de POST_CHUNK_SIZE
	var chunks: Dictionary = {}
	for item in json_data:
		var pos = Vector3(item[0], item[1], item[2])
		var rot_y = item[3]
		var cx = int(floor(pos.x / POST_CHUNK_SIZE))
		var cz = int(floor(pos.z / POST_CHUNK_SIZE))
		var key = Vector2i(cx, cz)
		if not chunks.has(key):
			chunks[key] = []
		chunks[key].append([pos, rot_y])

	var total_instanced = 0
	for key in chunks.keys():
		var items_chunk = chunks[key]
		var count = items_chunk.size()
		if count == 0:
			continue

		# Calcular AABB del cuadrante para posicionar el nodo en el centro real
		var first_pos: Vector3 = items_chunk[0][0]
		var chunk_aabb := AABB(first_pos, Vector3.ZERO)
		for it in items_chunk:
			chunk_aabb = chunk_aabb.expand(it[0])

		var chunk_center: Vector3 = chunk_aabb.get_center()
		var local_aabb := AABB(first_pos - chunk_center, Vector3.ZERO)

		var mm = MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.instance_count = count
		mm.mesh = canonical_mesh

		for i in range(count):
			var it = items_chunk[i]
			var pos: Vector3 = it[0]
			var rot_y: float = it[1]
			var local_pos = pos - chunk_center
			local_aabb = local_aabb.expand(local_pos)
			var basis = Basis(Vector3.UP, rot_y)
			var t = Transform3D(basis, local_pos)
			mm.set_instance_transform(i, t)

		mm.custom_aabb = local_aabb.grow(5.0)

		var mm_node = MultiMeshInstance3D.new()
		mm_node.name = "Chunk_%d_%d" % [key.x, key.y]
		mm_node.position = chunk_center
		mm_node.multimesh = mm
		mm_node.visibility_range_end = POST_VISIBILITY_END
		mm_node.visibility_range_end_margin = POST_VISIBILITY_MARGIN
		mm_node.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_SELF

		container.add_child(mm_node)
		total_instanced += count

	print("[Nomenclatura] Instanciados %d postes en %d cuadrantes espaciales con culling activo." % [total_instanced, chunks.size()])

func _find_mesh(node: Node) -> MeshInstance3D:
	if node is MeshInstance3D:
		return node
	for child in node.get_children():
		var found = _find_mesh(child)
		if found:
			return found
	return null
