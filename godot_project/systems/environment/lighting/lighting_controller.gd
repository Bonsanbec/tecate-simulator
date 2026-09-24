class_name LightingController
extends Node3D

## Controlador de Iluminación Dinámica y Entorno Fotorrealista para Tecate Simulator
##
## Administra la luz direccional del Sol, la Luna y el recurso WorldEnvironment,
## ajustando energía, temperatura de color, sombras y niebla según las efemérides
## de Tecate y las variables del subsistema de clima.

@export var sun_light_path: NodePath
@export var moon_light_path: NodePath
@export var world_env_path: NodePath

var sun_light: DirectionalLight3D
var moon_light: DirectionalLight3D
var world_environment: WorldEnvironment
var sky_material: ShaderMaterial

# Curvas de iluminación base
const MAX_SUN_ENERGY: float = 1.35
const MIN_SUN_ENERGY: float = 0.35
const MAX_MOON_ENERGY: float = 0.12

func _ready() -> void:
	_resolve_or_create_nodes()
	_setup_environment()

func _resolve_or_create_nodes() -> void:
	# Sol
	if has_node(sun_light_path):
		sun_light = get_node(sun_light_path)
	else:
		sun_light = DirectionalLight3D.new()
		sun_light.name = "SunLight"
		sun_light.shadow_enabled = true
		add_child(sun_light)
		
	# Luna
	if has_node(moon_light_path):
		moon_light = get_node(moon_light_path)
	else:
		moon_light = DirectionalLight3D.new()
		moon_light.name = "MoonLight"
		moon_light.shadow_enabled = true
		add_child(moon_light)
		
	# Entorno
	if has_node(world_env_path):
		world_environment = get_node(world_env_path)
	else:
		world_environment = WorldEnvironment.new()
		world_environment.name = "WorldEnvironment"
		add_child(world_environment)

func _setup_environment() -> void:
	var env = world_environment.environment
	if not env:
		env = Environment.new()
		world_environment.environment = env
		
	# 1. Configurar cielo fotorrealista con shader
	env.background_mode = Environment.BG_SKY
	var sky = Sky.new()
	var shader = load("res://systems/environment/shaders/realistic_sky.gdshader")
	sky_material = ShaderMaterial.new()
	sky_material.shader = shader
	sky.sky_material = sky_material
	sky.process_mode = Sky.PROCESS_MODE_QUALITY
	env.sky = sky
	
	# 2. Configurar iluminación ambiental PBR
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_sky_contribution = 1.0
	env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	
	# 3. Tonemapping y post-procesado
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.tonemap_exposure = 1.05
	env.glow_enabled = true
	env.glow_intensity = 0.35
	env.glow_bloom = 0.15
	
	# 4. Niebla atmosférica conectada al clima
	env.fog_enabled = true
	env.fog_mode = Environment.FOG_MODE_EXPONENTIAL
	env.fog_density = 0.0001
	env.fog_sky_affect = 0.3

func update_celestial_lighting(celestial: TecateCelestial.CelestialState, weather: WeatherData) -> void:
	if not celestial or not weather:
		return
		
	var cloud_cov = weather.cloud_coverage
	var cloud_att = clamp(1.0 - (cloud_cov * 0.72), 0.15, 1.0) # Atenuación por nubes
	
	# 1. ACTUALIZAR SOL
	var sun_elev = celestial.sun_altitude_rad
	var sun_dir = celestial.sun_direction
	
	if sun_elev > -0.10:
		sun_light.visible = true
		_align_directional_light(sun_light, sun_dir)
		
		# Curva de color según elevación (dorado en amanecer/ocaso a blanco diurno)
		var t_color = clamp(sun_elev / 0.35, 0.0, 1.0)
		var sunset_color = Color(1.0, 0.58, 0.25) # Dorado de Tecate
		var midday_color = Color(1.0, 0.98, 0.92) # Blanco luz de día
		sun_light.light_color = sunset_color.lerp(midday_color, t_color)
		
		# Curva de energía fotométrica
		var t_energy = clamp((sun_elev + 0.08) / 0.40, 0.0, 1.0)
		var base_energy = lerpf(MIN_SUN_ENERGY, MAX_SUN_ENERGY, t_energy)
		sun_light.light_energy = base_energy * cloud_att
		
		# Sombras: más nítidas con cielo claro, más difusas con nubes
		sun_light.shadow_blur = lerpf(1.0, 3.8, cloud_cov)
	else:
		sun_light.visible = false
		sun_light.light_energy = 0.0
		
	# 2. ACTUALIZAR LUNA
	var moon_elev = celestial.moon_altitude_rad
	var moon_dir = celestial.moon_direction
	
	# La luna ilumina la escena cuando el sol está oculto y la luna sobre el horizonte
	if moon_elev > -0.02 and sun_elev < 0.02:
		moon_light.visible = true
		_align_directional_light(moon_light, moon_dir)
		
		# Luz lunar plateada-azulada
		moon_light.light_color = Color(0.72, 0.83, 1.0)
		
		# Energía dependiente de la fase y elevación lunar
		var phase_factor = celestial.moon_illuminated_fraction
		var elev_factor = clamp(moon_elev / 0.5, 0.1, 1.0)
		var night_blend = clamp((-sun_elev) / 0.10, 0.0, 1.0)
		
		moon_light.light_energy = MAX_MOON_ENERGY * phase_factor * elev_factor * night_blend * cloud_att
		moon_light.shadow_blur = 2.0
	else:
		moon_light.visible = false
		moon_light.light_energy = 0.0
		
	# 3. ACTUALIZAR UNIFORMS DEL SHADER DE CIELO
	if sky_material:
		sky_material.set_shader_parameter("sun_direction", sun_dir)
		sky_material.set_shader_parameter("sun_color", Vector3(sun_light.light_color.r, sun_light.light_color.g, sun_light.light_color.b))
		sky_material.set_shader_parameter("moon_direction", moon_dir)
		sky_material.set_shader_parameter("moon_phase", celestial.moon_phase)
		
	# 4. ACTUALIZAR NIEBLA Y AMBIENTE EN EL ENTORNO
	var env = world_environment.environment
	if env:
		# En Tecate el aire es nítido y seco; prácticamente nunca hay niebla
		var target_fog = (weather.fog_density * 0.0002) + (weather.precipitation * 0.00008)
		if target_fog < 0.000005:
			env.fog_enabled = false
			env.fog_density = 0.0
		else:
			env.fog_enabled = true
			env.fog_density = target_fog
			
		# Color de niebla armonizado con el cielo
		var fog_ambient = sun_light.light_color.lerp(Color(0.2, 0.25, 0.35), 1.0 - clamp(sun_elev / 0.3, 0.0, 1.0))
		env.fog_light_color = fog_ambient

func get_sun_direction() -> Vector3:
	return sun_light.global_transform.basis.z if sun_light else Vector3.UP

func get_moon_direction() -> Vector3:
	return moon_light.global_transform.basis.z if moon_light else Vector3.DOWN

func get_sun_color() -> Color:
	return sun_light.light_color if sun_light else Color.WHITE

func get_moon_color() -> Color:
	return moon_light.light_color if moon_light else Color(0.7, 0.8, 1.0)

## Orienta una luz direccional para que sus rayos coincidan con la dirección de la fuente celeste
func _align_directional_light(light: DirectionalLight3D, celestial_dir: Vector3) -> void:
	# En Godot, la luz de DirectionalLight3D viaja en dirección hacia -Z local
	if celestial_dir.length_squared() < 0.001:
		return
		
	var forward = -celestial_dir.normalized()
	var up = Vector3.UP if abs(forward.y) < 0.99 else Vector3(0, 0, 1)
	light.transform.basis = Basis.looking_at(forward, up)
