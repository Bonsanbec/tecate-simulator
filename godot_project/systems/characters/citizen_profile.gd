class_name CitizenProfile
extends Resource

## Perfil de Identidad de Ciudadano / Avatar para Tecate Simulator
## Define las características visuales, modelo 3D GLB, props y metadatos
## antropométricos de los personajes de Tecate basados en personas reales.

const CharacterCatalogClass = preload("res://systems/characters/character_catalog.gd")

@export var identity_id: String = ""
@export var display_name: String = ""
@export var model_path: String = ""
@export var archetype: String = ""
@export var preferred_greeting: String = ""
@export var voice_pitch: float = 1.0
@export var walk_speed_modifier: float = 1.0
@export var icon_path: String = ""
@export var card_path: String = ""
@export var enable_skin_sss: bool = true
@export var sss_strength: float = 0.32
@export var sss_color: Color = Color(0.92, 0.45, 0.35, 1.0) # Tono subdérmico cálido

static func from_character_id(p_id: String) -> CitizenProfile:
	var data = CharacterCatalogClass.get_character_data(p_id)
	var p = CitizenProfile.new()
	p.identity_id = data.get("id", p_id)
	p.display_name = data.get("display_name", "")
	p.model_path = data.get("model_path", "")
	p.icon_path = data.get("icon_path", "")
	p.card_path = data.get("card_path", "")
	p.archetype = data.get("archetype", "")
	p.preferred_greeting = data.get("greeting", "")
	p.voice_pitch = data.get("voice_pitch", 1.0)
	p.walk_speed_modifier = data.get("walk_speed_modifier", 1.0)
	p.enable_skin_sss = true
	p.sss_strength = data.get("sss_strength", 0.32)
	p.sss_color = data.get("sss_color", Color(0.92, 0.45, 0.35, 1.0))
	return p

static func create_axel_profile() -> CitizenProfile:
	return from_character_id("axel")

static func create_eli_profile() -> CitizenProfile:
	return from_character_id("eli")

static func get_profile_by_identity(id: String) -> CitizenProfile:
	var target_id = id.to_lower()
	if not CharacterCatalogClass.has_character(target_id):
		target_id = CharacterCatalogClass.get_default_character_id()
	return from_character_id(target_id)
