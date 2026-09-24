class_name RainParticles
extends Node3D

## Sistema de Partículas 3D de Precipitación Atmosférica para Tecate Simulator
##
## Centra un volumen de partículas ligeras sobre la cámara activa y ajusta
## la tasa de emisión y la inclinación de las gotas según la intensidad de lluvia y viento.

var particles: GPUParticles3D
var _process_material: ParticleProcessMaterial

func _ready() -> void:
	_setup_particles()

func _setup_particles() -> void:
	particles = GPUParticles3D.new()
	particles.name = "RainGPU"
	particles.amount = 2500
	particles.lifetime = 1.2
	particles.preprocess = 0.5
	particles.visibility_aabb = AABB(Vector3(-30, -15, -30), Vector3(60, 35, 60))
	
	_process_material = ParticleProcessMaterial.new()
	_process_material.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	_process_material.emission_box_extents = Vector3(25.0, 10.0, 25.0)
	_process_material.direction = Vector3(0.0, -1.0, 0.0)
	_process_material.spread = 5.0
	_process_material.initial_velocity_min = 18.0
	_process_material.initial_velocity_max = 24.0
	_process_material.gravity = Vector3(0.0, -9.8, 0.0)
	_process_material.color = Color(0.75, 0.85, 0.95, 0.45)
	
	# Malla alargada para gota de lluvia
	var quad = QuadMesh.new()
	quad.size = Vector2(0.03, 0.45)
	
	var mat = StandardMaterial3D.new()
	mat.shading_mode = StandardMaterial3D.SHADING_MODE_UNSHADED
	mat.transparency = StandardMaterial3D.TRANSPARENCY_ALPHA
	mat.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	quad.material = mat
	
	particles.draw_pass_1 = quad
	particles.process_material = _process_material
	particles.emitting = false
	
	add_child(particles)

func update_weather(weather: WeatherData) -> void:
	if not particles or not weather:
		return
		
	var prec = weather.precipitation
	if prec > 0.05:
		particles.emitting = true
		particles.amount_ratio = clamp(prec, 0.1, 1.0)
		
		# Inclinar lluvia en dirección del viento
		var wind_spd = weather.wind_speed_mps
		var wind_rad = deg_to_rad(weather.wind_direction_deg)
		var wind_drift = Vector3(sin(wind_rad), 0.0, -cos(wind_rad)) * (wind_spd * 0.4)
		_process_material.direction = (Vector3(0.0, -1.0, 0.0) + wind_drift * 0.05).normalized()
	else:
		particles.emitting = false

func _process(_delta: float) -> void:
	# Centrar el volumen de lluvia sobre la cámara del jugador
	var viewport = get_viewport()
	if viewport:
		var cam = viewport.get_camera_3d()
		if cam:
			global_position = cam.global_position + Vector3(0.0, 6.0, 0.0)
