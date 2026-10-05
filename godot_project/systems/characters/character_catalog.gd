class_name CharacterCatalog
extends RefCounted

## Catálogo Paramétrico Centralizado de Personajes para Tecate Simulator
##
## Desacopla la definición de identidades, avatares, modelos 3D y recursos
## gráficos, eliminando cualquier referencia hardcoded en el simulador.

const CHARACTERS: Dictionary = {
	"axel": {
		"id": "axel",
		"display_name": "Camarada",
		"codename": "Axel",
		"title": "Camarada",
		"archetype": "urban_youth",
		"description": "Rechazo la debilidad.",
		"greeting": "¿Cómo andamios? ¿Eh? Mal ahí.",
		"card_path": "res://assets/characters/icons/axel_card.png",
		"icon_path": "res://assets/characters/icons/axel_icon.png",
		"model_path": "res://assets/characters/citizens/axel.glb",
		"profile_path": "res://assets/characters/citizens/axel_profile.tres",
		"voice_pitch": 1.0,
		"walk_speed_modifier": 1.0,
		"sss_strength": 0.32,
		"sss_color": Color(0.92, 0.45, 0.35, 1.0)
	},
	"eli": {
		"id": "eli",
		"display_name": "Diseñador",
		"codename": "Eli",
		"title": "Diseñador",
		"archetype": "formal_beige",
		"description": "La IA crea una imagen, yo diseño una marca.",
		"greeting": "Sí, pensé que te encontraría.",
		"card_path": "res://assets/characters/icons/eli_card.png",
		"icon_path": "res://assets/characters/icons/eli_icon.png",
		"model_path": "res://assets/characters/citizens/eli.glb",
		"profile_path": "res://assets/characters/citizens/eli_profile.tres",
		"voice_pitch": 0.95,
		"walk_speed_modifier": 0.98,
		"sss_strength": 0.30,
		"sss_color": Color(0.90, 0.44, 0.33, 1.0)
	}
}

const ORDERED_IDS: Array[String] = ["axel", "eli"]

static func get_character_ids() -> Array[String]:
	return ORDERED_IDS.duplicate()

static func has_character(p_id: String) -> bool:
	return CHARACTERS.has(p_id.to_lower())

static func get_character_data(p_id: String) -> Dictionary:
	var key = p_id.to_lower()
	if CHARACTERS.has(key):
		return CHARACTERS[key].duplicate(true)
	return CHARACTERS["axel"].duplicate(true)

static func get_all_characters() -> Array[Dictionary]:
	var list: Array[Dictionary] = []
	for id in ORDERED_IDS:
		list.append(get_character_data(id))
	return list

static func get_default_character_id() -> String:
	return ORDERED_IDS[0]

## Retorna una identidad paramétrica determinista basada en el entity_id de la entidad.
## Permite que ciudadanos no jugadores (NPCs) tengan diversidad estética balanceada
## sin forzar a ningún personaje como placeholder monolítico.
static func get_character_id_for_entity(entity_id: int) -> String:
	if ORDERED_IDS.is_empty():
		return "axel"
	var idx = abs(entity_id) % ORDERED_IDS.size()
	return ORDERED_IDS[idx]
