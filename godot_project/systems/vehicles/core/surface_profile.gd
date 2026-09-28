class_name SurfaceProfile
extends RefCounted

## Perfil Físico y de Rodadura de Superficies para Tecate Simulator
## Define las propiedades de fricción, resistencia al avance, consumo y acústica
## según el material sobre el que transita el vehículo o el avatar.

enum SurfaceType {
	ASPHALT = 0,     ## Asfalto urbano (Roadways / vialidades principales de Tecate)
	CONCRETE = 1,    ## Concreto hidráulico, puentes elevados (Bridges) y guarniciones
	GRAVEL = 2,      ## Grava, terracería y caminos rurales
	DIRT_OFFROAD = 3,## Terreno virgen natural (tinMesh / cerros y periferia)
	WATER = 4,       ## Cuerpos de agua (Río Tecate / Presa Las Auras / arroyos)
	RAILWAY = 5,     ## Vía férrea (Ferrocarril Tijuana-Tecate / balasto)
	UNKNOWN = 6      ## Superficie genérica por defecto
}

var type: SurfaceType = SurfaceType.ASPHALT
var surface_name: String = "Asfalto Urbano"

## Coeficiente de fricción estática / dinámica para tracción y agarre
var friction: float = 1.0

## Coeficiente de resistencia a la rodadura (desaceleración pasiva)
var rolling_resistance: float = 0.015

## Multiplicador de velocidad máxima permitida por la superficie (0.1 a 1.0)
var max_speed_factor: float = 1.0

## Multiplicador de consumo de combustible por sobreesfuerzo de tracción
var fuel_penalty_factor: float = 1.0

## Etiqueta acústica para el sistema de sonido ambiental de rodadura
var sound_tag: String = "asphalt"

## Indica si la superficie es transitable o representa peligro de hundimiento
var is_drivable: bool = true

static func create_default(p_type: SurfaceType):
	var script_res = load("res://systems/vehicles/core/surface_profile.gd")
	var prof = script_res.new()
	prof.type = p_type
	match p_type:
		SurfaceType.ASPHALT:
			prof.surface_name = "Asfalto Urbano"
			prof.friction = 1.0
			prof.rolling_resistance = 0.015
			prof.max_speed_factor = 1.0
			prof.fuel_penalty_factor = 1.0
			prof.sound_tag = "asphalt"
			prof.is_drivable = true
		SurfaceType.CONCRETE:
			prof.surface_name = "Concreto / Puente"
			prof.friction = 0.95
			prof.rolling_resistance = 0.018
			prof.max_speed_factor = 1.0
			prof.fuel_penalty_factor = 1.05
			prof.sound_tag = "concrete"
			prof.is_drivable = true
		SurfaceType.GRAVEL:
			prof.surface_name = "Terracería / Grava"
			prof.friction = 0.72
			prof.rolling_resistance = 0.045
			prof.max_speed_factor = 0.80
			prof.fuel_penalty_factor = 1.30
			prof.sound_tag = "gravel"
			prof.is_drivable = true
		SurfaceType.DIRT_OFFROAD:
			prof.surface_name = "Terreno Virgen"
			prof.friction = 0.55
			prof.rolling_resistance = 0.090
			prof.max_speed_factor = 0.60
			prof.fuel_penalty_factor = 1.65
			prof.sound_tag = "dirt"
			prof.is_drivable = true
		SurfaceType.WATER:
			prof.surface_name = "Agua / Río Tecate"
			prof.friction = 0.25
			prof.rolling_resistance = 0.350
			prof.max_speed_factor = 0.30
			prof.fuel_penalty_factor = 2.50
			prof.sound_tag = "water"
			prof.is_drivable = false # Requiere precaución o anega motor
		SurfaceType.RAILWAY:
			prof.surface_name = "Vía Férrea"
			prof.friction = 0.90
			prof.rolling_resistance = 0.005 # Muy bajo para trenes
			prof.max_speed_factor = 1.0
			prof.fuel_penalty_factor = 0.70
			prof.sound_tag = "rail"
			prof.is_drivable = true
		_:
			prof.surface_name = "Terreno Desconocido"
			prof.friction = 0.8
			prof.rolling_resistance = 0.03
			prof.max_speed_factor = 0.9
			prof.fuel_penalty_factor = 1.1
			prof.sound_tag = "default"
			prof.is_drivable = true
	return prof
