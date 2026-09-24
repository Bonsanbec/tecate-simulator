class_name CloudManager
extends Node3D

## Administrador y Orquestador de Capas Físicas de Nubes 3D en Tecate Simulator
##
## Instancia y sincroniza tres niveles atmosféricos a altitudes calibradas:
## 1. Estratos Bajos (Y = 900m): A la mitad de altura del Cerro Cuchumá (~1520m).
## 2. Cúmulos Medios (Y = 2200m): Masas de convección sobre las montañas.
## 3. Cirros Altos (Y = 7000m): Filamentos de hielo en la alta troposfera.

var layer_cuchuma: CloudLayer3D
var layer_cumulus: CloudLayer3D
var layer_cirrus: CloudLayer3D

func _ready() -> void:
	_create_layers()

func _create_layers() -> void:
	# 1. Capa de Estratos Bajos / Cuchumá (Y = 900.0m)
	layer_cuchuma = CloudLayer3D.new()
	layer_cuchuma.name = "Layer_Cuchuma_Stratus"
	layer_cuchuma.layer_name = "Estratos Cuchuma"
	layer_cuchuma.altitude_y = 900.0
	layer_cuchuma.layer_radius = 35000.0
	layer_cuchuma.uv_scale = 0.00018
	layer_cuchuma.depth_fade_distance = 70.0
	add_child(layer_cuchuma)
	
	# 2. Capa de Cúmulos Medios (Y = 2200.0m)
	layer_cumulus = CloudLayer3D.new()
	layer_cumulus.name = "Layer_Mid_Cumulus"
	layer_cumulus.layer_name = "Cumulos Medios"
	layer_cumulus.altitude_y = 2200.0
	layer_cumulus.layer_radius = 45000.0
	layer_cumulus.uv_scale = 0.00012
	layer_cumulus.depth_fade_distance = 120.0
	add_child(layer_cumulus)
	
	# 3. Capa de Cirros Altos (Y = 7000.0m)
	layer_cirrus = CloudLayer3D.new()
	layer_cirrus.name = "Layer_High_Cirrus"
	layer_cirrus.layer_name = "Cirros Altos"
	layer_cirrus.altitude_y = 7000.0
	layer_cirrus.layer_radius = 60000.0
	layer_cirrus.uv_scale = 0.00006
	layer_cirrus.depth_fade_distance = 250.0
	add_child(layer_cirrus)

func update_from_weather(weather_data: RefCounted) -> void:
	if not weather_data:
		return
		
	var coverage = weather_data.get("cloud_coverage") if weather_data.get("cloud_coverage") != null else 0.4
	var density = weather_data.get("cloud_density") if weather_data.get("cloud_density") != null else 0.8
	var wind_speed = weather_data.get("wind_speed_mps") if weather_data.get("wind_speed_mps") != null else 8.0
	var wind_deg = weather_data.get("wind_direction_deg") if weather_data.get("wind_direction_deg") != null else 270.0
	
	# Vector 2D de viento (X = Este, Y = Sur en espacio de mapa/plano horizontal)
	var wind_rad = deg_to_rad(wind_deg)
	var wind_vector = Vector2(sin(wind_rad), -cos(wind_rad))
	
	# Distribución de nubosidad por capas según el tipo de clima
	var cuchuma_cov: float
	var cumulus_cov: float
	var cirrus_cov: float
	
	var condition = weather_data.get("condition")
	if condition == "CLEAR" or condition == "DESPEJADO":
		cuchuma_cov = 0.0
		cumulus_cov = 0.0
		cirrus_cov = clamp(coverage * 0.5, 0.0, 0.12)
	elif condition == "PARTLY_CLOUDY":
		# Cúmulos aislados y bien definidos a 2200m; Cuchumá totalmente despejado
		cuchuma_cov = 0.0
		cumulus_cov = clamp(coverage * 1.1, 0.15, 0.45)
		cirrus_cov = 0.20
	elif condition == "RAIN" or condition == "OVERCAST":
		cuchuma_cov = clamp((coverage - 0.45) * 0.7, 0.0, 0.5)
		cumulus_cov = coverage
		cirrus_cov = clamp(coverage * 0.8, 0.3, 0.8)
	else:
		cuchuma_cov = 0.0
		cumulus_cov = coverage * 0.8
		cirrus_cov = coverage * 0.5

		
	if layer_cuchuma:
		layer_cuchuma.update_weather_params(cuchuma_cov, density, wind_vector, wind_speed)
	if layer_cumulus:
		layer_cumulus.update_weather_params(cumulus_cov, density * 0.9, wind_vector, wind_speed * 1.2)
	if layer_cirrus:
		layer_cirrus.update_weather_params(cirrus_cov, density * 0.6, wind_vector, wind_speed * 2.0)

func update_lighting(sun_dir: Vector3, sun_col: Color, moon_dir: Vector3, moon_col: Color, ambient_col: Color) -> void:
	if layer_cuchuma:
		layer_cuchuma.update_lighting_params(sun_dir, sun_col, moon_dir, moon_col, ambient_col)
	if layer_cumulus:
		layer_cumulus.update_lighting_params(sun_dir, sun_col, moon_dir, moon_col, ambient_col)
	if layer_cirrus:
		layer_cirrus.update_lighting_params(sun_dir, sun_col, moon_dir, moon_col, ambient_col)
