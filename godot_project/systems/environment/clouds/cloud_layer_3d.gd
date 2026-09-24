class_name CloudLayer3D
extends MeshInstance3D

## Nodo de Malla 3D para una Capa Física de Nubes en Tecate Simulator
##
## Mantiene rígidamente su altitud mundial en el eje Y (ej: Y=900m para la mitad del Cuchumá),
## y desplaza sus coordenadas horizontales (X, Z) junto a la cámara para brindar
## cobertura completa del horizonte sin cortes de visión.

@export var layer_name: String = "Estratos_Cuchuma"
@export var altitude_y: float = 900.0
@export var layer_radius: float = 35000.0
@export var cloud_coverage: float = 0.45
@export var cloud_density: float = 0.85
@export var uv_scale: float = 0.00015
@export var depth_fade_distance: float = 60.0

var _material: ShaderMaterial
var _shader: Shader

func _ready() -> void:
	# Cargar shader de nube física
	_shader = load("res://systems/environment/shaders/cloud_layer.gdshader")
	_setup_mesh()
	_setup_material()
	
	# Fijar altitud inicial en el mundo
	global_position.y = altitude_y

func _setup_mesh() -> void:
	var plane_mesh = PlaneMesh.new()
	plane_mesh.size = Vector2(layer_radius * 2.0, layer_radius * 2.0)
	plane_mesh.subdivide_width = 16
	plane_mesh.subdivide_depth = 16
	mesh = plane_mesh

func _setup_material() -> void:
	_material = ShaderMaterial.new()
	_material.shader = _shader
	
	_material.set_shader_parameter("cloud_coverage", cloud_coverage)
	_material.set_shader_parameter("cloud_density", cloud_density)
	_material.set_shader_parameter("uv_scale", uv_scale)
	_material.set_shader_parameter("depth_fade_distance", depth_fade_distance)
	_material.set_shader_parameter("horizon_fade_distance", layer_radius)
	
	material_override = _material

func update_weather_params(coverage: float, density: float, wind_dir: Vector2, wind_spd: float) -> void:
	cloud_coverage = coverage
	cloud_density = density
	if _material:
		_material.set_shader_parameter("cloud_coverage", cloud_coverage)
		_material.set_shader_parameter("cloud_density", cloud_density)
		_material.set_shader_parameter("wind_vector", wind_dir)
		_material.set_shader_parameter("wind_speed", wind_spd)

func update_lighting_params(sun_dir: Vector3, sun_col: Color, moon_dir: Vector3, moon_col: Color, ambient_col: Color) -> void:
	if _material:
		_material.set_shader_parameter("sun_direction", sun_dir)
		_material.set_shader_parameter("sun_color", Vector3(sun_col.r, sun_col.g, sun_col.b))
		_material.set_shader_parameter("moon_direction", moon_dir)
		_material.set_shader_parameter("moon_color", Vector3(moon_col.r, moon_col.g, moon_col.b))
		_material.set_shader_parameter("ambient_light_color", Vector3(ambient_col.r, ambient_col.g, ambient_col.b))

func _process(_delta: float) -> void:
	# Centrar horizontalmente en la cámara activa manteniendo la altitud mundial Y
	var viewport = get_viewport()
	if viewport:
		var cam = viewport.get_camera_3d()
		if cam:
			var cam_pos = cam.global_position
			global_position.x = cam_pos.x
			global_position.z = cam_pos.z
			
	# Garantizar que la altitud física permanezca inmutable
	global_position.y = altitude_y
