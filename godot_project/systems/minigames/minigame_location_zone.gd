class_name MinigameLocationZone
extends Node3D

## Zona de Activación e Información de Actividades por Ubicación en el Mapa 3D.
## Se registra en el grupo "minigame_zones" para que PlayerController muestre
## los tooltips contextuales al acercarse y despliega un marcador diegético 3D
## en el entorno urbano de Tecate.

const MinigameCatalogClass = preload("res://systems/minigames/minigame_catalog.gd")

@export var location_id: String = "kiosko"
@export var interaction_radius: float = 6.0
@export var show_3d_marker: bool = true
@export var follow_node_path: NodePath = ^""

var radius: float:
	get:
		return interaction_radius
	set(val):
		interaction_radius = val

var location_name: String = ""
var primary_game_id: int = 1
var game_ids: Array = []
var accent_color: Color = Color(1.0, 0.72, 0.0, 1.0)
var icon_text: String = ""

var marker_root: Node3D = null
var ring_mesh: MeshInstance3D = null
var title_label_3d: Label3D = null
var sub_label_3d: Label3D = null

var _follow_target: Node3D = null
var _anim_time: float = 0.0

func _ready() -> void:
	add_to_group("minigame_zones")
	_load_from_catalog()
	if not follow_node_path.is_empty() and has_node(follow_node_path):
		_follow_target = get_node(follow_node_path) as Node3D
	if show_3d_marker:
		_build_3d_marker()

func _load_from_catalog() -> void:
	var info = MinigameCatalogClass.get_location_info(location_id)
	if not info.is_empty():
		location_name = info.get("name", location_id)
		if is_equal_approx(interaction_radius, 6.0):
			interaction_radius = float(info.get("radius", interaction_radius))
		primary_game_id = int(info.get("primary_game_id", 1))
		game_ids = info.get("game_ids", [1])
		accent_color = info.get("color", Color(1.0, 0.72, 0.0, 1.0))
		icon_text = info.get("icon", "")
	else:
		location_name = location_id

func _build_3d_marker() -> void:
	marker_root = Node3D.new()
	marker_root.name = "MarkerRoot"
	add_child(marker_root)

	# 1. Anillo luminoso a ras de suelo
	ring_mesh = MeshInstance3D.new()
	ring_mesh.name = "RingMesh"
	var torus = TorusMesh.new()
	torus.inner_radius = 1.15
	torus.outer_radius = 1.35
	torus.rings = 32
	torus.ring_segments = 12
	ring_mesh.mesh = torus
	ring_mesh.position = Vector3(0.0, 0.08, 0.0)

	var mat = StandardMaterial3D.new()
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.albedo_color = Color(accent_color.r, accent_color.g, accent_color.b, 0.78)
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	ring_mesh.material_override = mat
	marker_root.add_child(ring_mesh)

	# 2. Etiqueta 3D flotante (Billboard) con los juegos de la ubicación
	var din_font = load("res://assets/fonts/DIN_Condensed_Bold.ttf")

	title_label_3d = Label3D.new()
	title_label_3d.name = "TitleLabel3D"
	title_label_3d.position = Vector3(0.0, 2.35, 0.0)
	title_label_3d.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	title_label_3d.no_depth_test = false
	title_label_3d.pixel_size = 0.0045
	title_label_3d.font_size = 68
	title_label_3d.outline_size = 14
	title_label_3d.modulate = Color(1.0, 0.96, 0.82, 0.96)
	title_label_3d.outline_modulate = Color(0.05, 0.07, 0.12, 0.95)
	if din_font:
		title_label_3d.font = din_font

	var games = MinigameCatalogClass.get_minigames_by_location(location_id)
	var game_titles: PackedStringArray = []
	for g in games:
		game_titles.append(g.get("title", "Minijuego"))

	title_label_3d.text = ", ".join(game_titles)
	title_label_3d.visibility_range_end = 42.0
	title_label_3d.visibility_range_end_margin = 6.0
	title_label_3d.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_SELF
	marker_root.add_child(title_label_3d)

	sub_label_3d = Label3D.new()
	sub_label_3d.name = "SubLabel3D"
	sub_label_3d.position = Vector3(0.0, 1.95, 0.0)
	sub_label_3d.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	sub_label_3d.pixel_size = 0.0042
	sub_label_3d.font_size = 46
	sub_label_3d.outline_size = 10
	sub_label_3d.modulate = accent_color.lightened(0.25)
	if din_font:
		sub_label_3d.font = din_font
	sub_label_3d.text = "%s  •  %s" % [AppStrings.PROMPT_START_ACTIVITY, AppStrings.PHONE_PROMPT_SHORT]
	sub_label_3d.visibility_range_end = 26.0
	sub_label_3d.visibility_range_end_margin = 4.0
	sub_label_3d.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_SELF
	marker_root.add_child(sub_label_3d)

func _process(delta: float) -> void:
	if not is_visible_in_tree():
		return
	if _follow_target and is_instance_valid(_follow_target):
		global_position = _follow_target.global_position
	if marker_root and marker_root.visible:
		_anim_time += delta
		var bob = sin(_anim_time * 2.6) * 0.09
		if title_label_3d:
			title_label_3d.position.y = 2.35 + bob
		if sub_label_3d:
			sub_label_3d.position.y = 1.95 + bob
		if ring_mesh:
			var pulse = 1.0 + sin(_anim_time * 3.2) * 0.06
			ring_mesh.scale = Vector3(pulse, 1.0, pulse)

func is_point_inside(world_pos: Vector3) -> bool:
	var dx = world_pos.x - global_position.x
	var dz = world_pos.z - global_position.z
	var dy = absf(world_pos.y - global_position.y)
	if dy > 6.5:
		return false
	return (dx * dx + dz * dz) <= (interaction_radius * interaction_radius)

func get_tooltip_prompt() -> String:
	return MinigameCatalogClass.format_location_tooltip(location_id)
