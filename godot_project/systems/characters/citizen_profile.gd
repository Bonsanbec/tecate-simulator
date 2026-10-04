class_name CitizenProfile
extends Resource

## Perfil de Identidad de Ciudadano / Avatar para Tecate Simulator
## Define las características visuales, modelo 3D GLB, props y metadatos
## antropométricos de los personajes de Tecate basados en personas reales.

@export var identity_id: String = "axel"
@export var display_name: String = "Axel"
@export var model_path: String = "res://assets/characters/citizens/axel.glb"
@export var archetype: String = "urban_youth" # "urban_youth", "formal_beige", "casual_street", "formal_artist"
@export var preferred_greeting: String = "¡Qué onda! Bienvenidos a Tecate."
@export var voice_pitch: float = 1.0
@export var walk_speed_modifier: float = 1.0
@export var enable_skin_sss: bool = true
@export var sss_strength: float = 0.32
@export var sss_color: Color = Color(0.92, 0.45, 0.35, 1.0) # Tono subdérmico cálido

static func create_axel_profile() -> CitizenProfile:
	var p = CitizenProfile.new()
	p.identity_id = "axel"
	p.display_name = "Axel"
	p.model_path = "res://assets/characters/citizens/axel.glb"
	p.archetype = "urban_youth"
	p.preferred_greeting = "¡Qué onda! Bienvenidos a Tecate."
	p.voice_pitch = 1.0
	p.walk_speed_modifier = 1.0
	p.enable_skin_sss = true
	p.sss_strength = 0.32
	p.sss_color = Color(0.92, 0.45, 0.35, 1.0)
	return p

static func create_eli_profile() -> CitizenProfile:
	var p = CitizenProfile.new()
	p.identity_id = "eli"
	p.display_name = "Eli"
	p.model_path = "res://assets/characters/citizens/eli.glb"
	p.archetype = "formal_beige"
	p.preferred_greeting = "Buenas tardes, un placer coincidir en Tecate."
	p.voice_pitch = 0.95
	p.walk_speed_modifier = 0.98
	p.enable_skin_sss = true
	p.sss_strength = 0.30
	p.sss_color = Color(0.90, 0.44, 0.33, 1.0)
	return p

static func get_profile_by_identity(id: String) -> CitizenProfile:
	match id.to_lower():
		"eli":
			return create_eli_profile()
		"axel", _:
			return create_axel_profile()

