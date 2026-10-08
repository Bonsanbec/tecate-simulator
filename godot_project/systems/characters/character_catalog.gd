class_name CharacterCatalog
extends RefCounted

## Catálogo Paramétrico Centralizado de Personajes para Tecate Simulator
##
## Desacopla la definición de identidades, avatares, modelos 3D y recursos
## gráficos, eliminando cualquier referencia hardcoded en el simulador.

const PUEBLO_MAGICO_LETTER_COLORS: Array[Color] = [
	Color(0.85, 0.16, 0.16, 1.0), # T1: Rojo Tecate (#D82A2A)
	Color(0.0, 0.33, 0.72, 1.0),  # E1: Azul Cobalto (#0055B8)
	Color(0.94, 0.31, 0.14, 1.0), # C: Naranja Terracota (#EE4023)
	Color(0.0, 0.53, 0.24, 1.0),  # A: Verde Rumorosa (#00873D)
	Color(1.0, 0.72, 0.0, 1.0),   # T2: Dorado Sol (#FFB800)
	Color(0.38, 0.15, 0.62, 1.0)  # E2: Morado Púrpura (#62259D)
]

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
		"sss_color": Color(0.92, 0.45, 0.35, 1.0),
		"theme_color": Color(0.85, 0.16, 0.16, 1.0) # Rojo Tecate Firma
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
		"sss_color": Color(0.90, 0.44, 0.33, 1.0),
		"theme_color": Color(0.0, 0.33, 0.72, 1.0) # Azul Cobalto Firma
	},
	"astorga": {
		"id": "astorga",
		"display_name": "Músico",
		"codename": "Astorga",
		"title": "Músico",
		"archetype": "classical_musician",
		"description": "Me hace feliz formar parte de su grupo.",
		"greeting": "¿Y mi camarada?",
		"card_path": "res://assets/characters/icons/astorga_card.png",
		"icon_path": "res://assets/characters/icons/astorga_icon.png",
		"model_path": "res://assets/characters/citizens/astorga.glb",
		"profile_path": "res://assets/characters/citizens/astorga_profile.tres",
		"voice_pitch": 0.92,
		"walk_speed_modifier": 0.96,
		"sss_strength": 0.28,
		"sss_color": Color(0.91, 0.46, 0.34, 1.0),
		"theme_color": Color(0.94, 0.31, 0.14, 1.0) # Naranja Terracota Firma
	}
}

const ORDERED_IDS: Array[String] = ["axel", "eli", "astorga"]

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

## Retorna el color firma distintivo centralizado de un personaje
static func get_character_theme_color(p_id: String) -> Color:
	var data = get_character_data(p_id)
	return data.get("theme_color", Color(0.85, 0.16, 0.16, 1.0))

## Genera el código BBCode del título principal con cada letra en su color oficial de Pueblo Mágico
static func get_colored_title_bbcode(title_text: String = "TECATE") -> String:
	var bbcode = ""
	for i in range(title_text.length()):
		var char_str = title_text[i]
		var col = PUEBLO_MAGICO_LETTER_COLORS[i % PUEBLO_MAGICO_LETTER_COLORS.size()]
		bbcode += "[color=#%s]%s[/color]" % [col.to_html(false), char_str]
	return bbcode

## Retorna una identidad paramétrica determinista basada en el entity_id de la entidad.
static func get_character_id_for_entity(entity_id: int) -> String:
	if ORDERED_IDS.is_empty():
		return "axel"
	var idx = abs(entity_id) % ORDERED_IDS.size()
	return ORDERED_IDS[idx]
