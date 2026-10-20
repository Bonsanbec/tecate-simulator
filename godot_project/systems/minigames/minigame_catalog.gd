class_name MinigameCatalog
extends RefCounted

## Catálogo Maestro de Minijuegos y Ubicaciones para Tecate Simulator.
## Centraliza la información de los 12 minijuegos documentados en:
## - docs/minigames/master.md
## - docs/minigames/arquitectura_y_plan_maestro.md

enum Category {
	ALL = 0,
	ALL_VS_ALL = 1,
	ONE_VS_ALL = 2,
	DUEL_1V1 = 3
}

const CATEGORY_INFO: Dictionary = {
	Category.ALL: {
		"name": AppStrings.MINIGAMES_TAB_ALL,
		"short_name": AppStrings.MINIGAMES_TAB_ALL,
		"badge": AppStrings.MINIGAMES_BADGE_PARTY_MODE,
		"icon": "",
		"color": Color(1.0, 0.72, 0.0, 1.0)
	},
	Category.ALL_VS_ALL: {
		"name": AppStrings.MINIGAMES_TAB_ALL_VS_ALL,
		"short_name": AppStrings.MINIGAMES_TAB_ALL_VS_ALL,
		"badge": AppStrings.MINIGAMES_BADGE_ALL_VS_ALL,
		"icon": "",
		"color": Color(0.85, 0.16, 0.16, 1.0)
	},
	Category.ONE_VS_ALL: {
		"name": AppStrings.MINIGAMES_TAB_ONE_VS_ALL,
		"short_name": AppStrings.MINIGAMES_TAB_ONE_VS_ALL,
		"badge": AppStrings.MINIGAMES_BADGE_ONE_VS_ALL,
		"icon": "",
		"color": Color(0.0, 0.45, 0.75, 1.0)
	},
	Category.DUEL_1V1: {
		"name": AppStrings.MINIGAMES_TAB_DUEL,
		"short_name": AppStrings.MINIGAMES_TAB_DUEL,
		"badge": AppStrings.MINIGAMES_BADGE_DUEL,
		"icon": "",
		"color": Color(0.18, 0.65, 0.32, 1.0)
	}
}

const LOCATIONS: Dictionary = {
	"kiosko": {
		"id": "kiosko",
		"name": "Kiosko del Parque Miguel Hidalgo",
		"short_name": "Kiosko Central",
		"icon": "",
		"position": Vector3(-6.6844, 400.35, 2.6878),
		"radius": 6.5,
		"arena_id": 1,
		"primary_game_id": 1,
		"game_ids": [1, 7, 8],
		"color": Color(0.85, 0.16, 0.16, 1.0)
	},
	"parque_explanada": {
		"id": "parque_explanada",
		"name": "Explanada del Parque Miguel Hidalgo",
		"short_name": "Explanada del Parque",
		"icon": "",
		"position": Vector3(-6.6844, 400.15, 14.5),
		"radius": 7.0,
		"arena_id": 2,
		"primary_game_id": 2,
		"game_ids": [2, 3, 4],
		"color": Color(1.0, 0.65, 0.12, 1.0)
	},
	"parque_mesas": {
		"id": "parque_mesas",
		"name": "Mesas del Parque Miguel Hidalgo",
		"short_name": "Mesas del Parque",
		"icon": "",
		"position": Vector3(-28.0, 400.85, -6.0),
		"radius": 5.5,
		"arena_id": 2,
		"primary_game_id": 9,
		"game_ids": [9],
		"color": Color(0.18, 0.65, 0.32, 1.0)
	},
	"foto_curiel": {
		"id": "foto_curiel",
		"name": "Foto Estudio Curiel",
		"short_name": "Foto Estudio Curiel",
		"icon": "",
		"position": Vector3(-53.5, 399.35, -18.5),
		"radius": 5.5,
		"arena_id": 5,
		"primary_game_id": 6,
		"game_ids": [6],
		"color": Color(0.0, 0.45, 0.75, 1.0)
	},
	"bus_hongo": {
		"id": "bus_hongo",
		"name": "Autobús urbano El Hongo",
		"short_name": "Autobús El Hongo",
		"icon": "",
		"position": Vector3(143.0, 402.17, -18.1),
		"radius": 6.5,
		"arena_id": 4,
		"primary_game_id": 5,
		"game_ids": [5],
		"color": Color(0.95, 0.52, 0.12, 1.0)
	},
	"bbva_azotea": {
		"id": "bbva_azotea",
		"name": "Edificio BBVA Bancomer Centro",
		"short_name": "Arena BBVA y Parque",
		"icon": "",
		"position": Vector3(-62.0, 399.8, -18.0),
		"radius": 6.5,
		"arena_id": 3,
		"primary_game_id": 10,
		"game_ids": [10],
		"color": Color(0.55, 0.25, 0.88, 1.0)
	},
	"av_hidalgo": {
		"id": "av_hidalgo",
		"name": "Avenida Miguel Hidalgo",
		"short_name": "Avenida Miguel Hidalgo",
		"icon": "",
		"position": Vector3(-48.0, 399.0, 25.0),
		"radius": 6.5,
		"arena_id": 6,
		"primary_game_id": 11,
		"game_ids": [11],
		"color": Color(0.18, 0.65, 0.32, 1.0)
	},
	"obras_municipales": {
		"id": "obras_municipales",
		"name": "Palacio Municipal y obras de Tecate",
		"short_name": "Palacio Municipal",
		"icon": "",
		"position": Vector3(47.75, 398.8, 38.4),
		"radius": 7.0,
		"arena_id": 7,
		"primary_game_id": 12,
		"game_ids": [12],
		"color": Color(0.88, 0.68, 0.08, 1.0)
	}
}

const MINIGAMES: Array[Dictionary] = [
	{
		"id": 1,
		"title": AppStrings.MINIGAME_1_TITLE,
		"full_title": AppStrings.MINIGAME_1_TITLE,
		"subtitle": AppStrings.MINIGAME_1_SUBTITLE,
		"category": Category.ALL_VS_ALL,
		"phase": 1,
		"is_playable": true,
		"icon": "",
		"location_id": "kiosko",
		"location_name": "Kiosko del Parque Miguel Hidalgo",
		"arena_id": 1,
		"min_players": 2,
		"max_players": 8,
		"players_badge": "2 a 8 jugadores",
		"duration_seconds": 90,
		"reward_first": 50,
		"color": Color(0.85, 0.16, 0.16, 1.0),
		"description": AppStrings.MINIGAME_1_DESC,
		"controls": [
			{"input": "WASD y Espacio", "action": "Moverse y saltar en la tarima"},
			{"input": "Clic izquierdo o G", "action": "Empujar oponente con retroceso físico"},
			{"input": "Clic derecho o F", "action": "Bloqueo oportuno reflejante"}
		],
		"spawn_position": Vector3(-6.6844, 401.80, 2.6878)
	},
	{
		"id": 2,
		"title": AppStrings.MINIGAME_2_TITLE,
		"full_title": AppStrings.MINIGAME_2_TITLE,
		"subtitle": AppStrings.MINIGAME_2_SUBTITLE,
		"category": Category.ALL_VS_ALL,
		"phase": 1,
		"is_playable": true,
		"icon": "",
		"location_id": "parque_explanada",
		"location_name": "Parque Miguel Hidalgo",
		"arena_id": 2,
		"min_players": 2,
		"max_players": 8,
		"players_badge": "2 a 8 jugadores",
		"duration_seconds": 75,
		"reward_first": 50,
		"color": Color(1.0, 0.58, 0.10, 1.0),
		"description": AppStrings.MINIGAME_2_DESC,
		"controls": [
			{"input": "WASD y Shift", "action": "Correr y esquivar obstáculos"},
			{"input": "Espacio", "action": "Saltar jardineras y bancas"},
			{"input": "Proximidad", "action": "Tocar a otro jugador para transferir la marca"}
		],
		"spawn_position": Vector3(-6.6844, 400.35, 12.6878)
	},
	{
		"id": 3,
		"title": AppStrings.MINIGAME_3_TITLE,
		"full_title": AppStrings.MINIGAME_3_TITLE,
		"subtitle": AppStrings.MINIGAME_3_SUBTITLE,
		"category": Category.ALL_VS_ALL,
		"phase": 1,
		"is_playable": true,
		"icon": "",
		"location_id": "parque_explanada",
		"location_name": "Explanada del Parque Miguel Hidalgo",
		"arena_id": 2,
		"min_players": 2,
		"max_players": 8,
		"players_badge": "2 a 8 jugadores",
		"duration_seconds": 90,
		"reward_first": 50,
		"color": Color(0.95, 0.36, 0.15, 1.0),
		"description": AppStrings.MINIGAME_3_DESC,
		"controls": [
			{"input": "WASD y Shift", "action": "Esquivar proyectiles en movimiento"},
			{"input": "Clic izquierdo o G", "action": "Lanzar pelota con rebote físico"},
			{"input": "Ratón", "action": "Apuntar trayectoria de rebote"}
		],
		"spawn_position": Vector3(-6.6844, 400.35, 14.5)
	},
	{
		"id": 4,
		"title": AppStrings.MINIGAME_4_TITLE,
		"full_title": AppStrings.MINIGAME_4_TITLE,
		"subtitle": AppStrings.MINIGAME_4_SUBTITLE,
		"category": Category.ONE_VS_ALL,
		"phase": 2,
		"is_playable": false,
		"icon": "",
		"location_id": "parque_explanada",
		"location_name": "Parque Miguel Hidalgo",
		"arena_id": 2,
		"min_players": 2,
		"max_players": 8,
		"players_badge": "1 contra todos",
		"duration_seconds": 120,
		"reward_first": 50,
		"color": Color(0.0, 0.45, 0.75, 1.0),
		"description": AppStrings.MINIGAME_4_DESC,
		"controls": [
			{"input": "WASD y Shift", "action": "Esconderse o correr hacia la base"},
			{"input": "Clic izquierdo", "action": "Apuntar y marcar jugador en línea de visión"},
			{"input": "Tocar base", "action": "Llegar a la base para salvarse"}
		],
		"spawn_position": Vector3(-6.6844, 400.35, 14.5)
	},
	{
		"id": 5,
		"title": AppStrings.MINIGAME_5_TITLE,
		"full_title": AppStrings.MINIGAME_5_TITLE,
		"subtitle": AppStrings.MINIGAME_5_SUBTITLE,
		"category": Category.ONE_VS_ALL,
		"phase": 2,
		"is_playable": false,
		"icon": "",
		"location_id": "bus_hongo",
		"location_name": "Autobús urbano El Hongo",
		"arena_id": 4,
		"min_players": 2,
		"max_players": 8,
		"players_badge": "1 contra todos",
		"duration_seconds": 90,
		"reward_first": 50,
		"color": Color(0.95, 0.52, 0.12, 1.0),
		"description": AppStrings.MINIGAME_5_DESC,
		"controls": [
			{"input": "Teclas 1 a 5", "action": "Seleccionar monedas y billetes"},
			{"input": "Y o N", "action": "Visto bueno del conductor al monto"},
			{"input": "Contrarreloj", "action": "Cálculo rápido antes de la siguiente parada"}
		],
		"spawn_position": Vector3(143.0, 402.17, -18.1)
	},
	{
		"id": 6,
		"title": AppStrings.MINIGAME_6_TITLE,
		"full_title": AppStrings.MINIGAME_6_TITLE,
		"subtitle": AppStrings.MINIGAME_6_SUBTITLE,
		"category": Category.ONE_VS_ALL,
		"phase": 2,
		"is_playable": false,
		"icon": "",
		"location_id": "foto_curiel",
		"location_name": "Foto Estudio Curiel",
		"arena_id": 5,
		"min_players": 2,
		"max_players": 8,
		"players_badge": "1 contra todos",
		"duration_seconds": 120,
		"reward_first": 50,
		"color": Color(0.0, 0.45, 0.75, 1.0),
		"description": AppStrings.MINIGAME_6_DESC,
		"controls": [
			{"input": "Chat", "action": "Publicar encargo fotográfico de la ronda"},
			{"input": "F1 y Clic izquierdo", "action": "Encuadrar y capturar fotografía"},
			{"input": "Calificación", "action": "El jefe evalúa la mejor captura"}
		],
		"spawn_position": Vector3(-53.5, 399.35, -18.5)
	},
	{
		"id": 7,
		"title": AppStrings.MINIGAME_7_TITLE,
		"full_title": AppStrings.MINIGAME_7_TITLE,
		"subtitle": AppStrings.MINIGAME_7_SUBTITLE,
		"category": Category.ONE_VS_ALL,
		"phase": 3,
		"is_playable": false,
		"icon": "",
		"location_id": "kiosko",
		"location_name": "Kiosko del Parque Miguel Hidalgo",
		"arena_id": 1,
		"min_players": 2,
		"max_players": 8,
		"players_badge": "1 contra todos",
		"duration_seconds": 90,
		"reward_first": 50,
		"color": Color(0.88, 0.20, 0.62, 1.0),
		"description": AppStrings.MINIGAME_7_DESC,
		"controls": [
			{"input": "Teclas A a Z", "action": "Ejecutar o imitar el gesto de baile"},
			{"input": "Observación visual", "action": "Identificar el gesto del instructor"}
		],
		"spawn_position": Vector3(-6.6844, 401.80, 2.6878)
	},
	{
		"id": 8,
		"title": AppStrings.MINIGAME_8_TITLE,
		"full_title": AppStrings.MINIGAME_8_TITLE,
		"subtitle": AppStrings.MINIGAME_8_SUBTITLE,
		"category": Category.ALL_VS_ALL,
		"phase": 3,
		"is_playable": false,
		"icon": "",
		"location_id": "kiosko",
		"location_name": "Kiosko del Parque Miguel Hidalgo",
		"arena_id": 1,
		"min_players": 3,
		"max_players": 8,
		"players_badge": "3 a 8 jugadores",
		"duration_seconds": 180,
		"reward_first": 50,
		"color": Color(0.65, 0.30, 0.88, 1.0),
		"description": AppStrings.MINIGAME_8_DESC,
		"controls": [
			{"input": "Chat de texto", "action": "Pronunciar discurso en el Kiosko"},
			{"input": "Selección de aliados", "action": "Pactar coalición durante el discurso"},
			{"input": "Votación", "action": "Emitir voto secreto o abstenerse"}
		],
		"spawn_position": Vector3(-6.6844, 401.80, 2.6878)
	},
	{
		"id": 9,
		"title": AppStrings.MINIGAME_9_TITLE,
		"full_title": AppStrings.MINIGAME_9_TITLE,
		"subtitle": AppStrings.MINIGAME_9_SUBTITLE,
		"category": Category.DUEL_1V1,
		"phase": 3,
		"is_playable": false,
		"icon": "",
		"location_id": "parque_mesas",
		"location_name": "Mesas del Parque Miguel Hidalgo",
		"arena_id": 2,
		"min_players": 2,
		"max_players": 2,
		"players_badge": "Duelo individual",
		"duration_seconds": 300,
		"reward_first": 50,
		"color": Color(0.18, 0.65, 0.32, 1.0),
		"description": AppStrings.MINIGAME_9_DESC,
		"controls": [
			{"input": "E", "action": "Ocupar asiento en la mesa"},
			{"input": "Clic izquierdo", "action": "Seleccionar y mover pieza en el tablero"}
		],
		"spawn_position": Vector3(-28.0, 400.85, -6.0)
	},
	{
		"id": 10,
		"title": AppStrings.MINIGAME_10_TITLE,
		"full_title": AppStrings.MINIGAME_10_TITLE,
		"subtitle": AppStrings.MINIGAME_10_SUBTITLE,
		"category": Category.ALL_VS_ALL,
		"phase": 4,
		"is_playable": false,
		"icon": "",
		"location_id": "bbva_azotea",
		"location_name": "Azotea de BBVA y Parque Miguel Hidalgo",
		"arena_id": 3,
		"min_players": 2,
		"max_players": 8,
		"players_badge": "2 a 8 jugadores",
		"duration_seconds": 150,
		"reward_first": 50,
		"color": Color(0.85, 0.16, 0.25, 1.0),
		"description": AppStrings.MINIGAME_10_DESC,
		"controls": [
			{"input": "WASD y Espacio", "action": "Movimiento lateral y salto doble"},
			{"input": "Clic izquierdo o G", "action": "Ataques normales y combinaciones"},
			{"input": "Clic derecho o F", "action": "Ataques especiales y esquiva"}
		],
		"spawn_position": Vector3(-62.0, 399.8, -18.0)
	},
	{
		"id": 11,
		"title": AppStrings.MINIGAME_11_TITLE,
		"full_title": AppStrings.MINIGAME_11_TITLE,
		"subtitle": AppStrings.MINIGAME_11_SUBTITLE,
		"category": Category.DUEL_1V1,
		"phase": 4,
		"is_playable": false,
		"icon": "",
		"location_id": "av_hidalgo",
		"location_name": "Avenida Miguel Hidalgo",
		"arena_id": 6,
		"min_players": 2,
		"max_players": 2,
		"players_badge": "Duelo individual",
		"duration_seconds": 60,
		"reward_first": 50,
		"color": Color(0.18, 0.65, 0.32, 1.0),
		"description": AppStrings.MINIGAME_11_DESC,
		"controls": [
			{"input": "W o Espacio", "action": "Mantener ritmo de galope"},
			{"input": "Ratón", "action": "Apuntar la lanza al corazón del rival"}
		],
		"spawn_position": Vector3(-48.0, 399.0, 25.0)
	},
	{
		"id": 12,
		"title": AppStrings.MINIGAME_12_TITLE,
		"full_title": AppStrings.MINIGAME_12_TITLE,
		"subtitle": AppStrings.MINIGAME_12_SUBTITLE,
		"category": Category.ALL_VS_ALL,
		"phase": 4,
		"is_playable": false,
		"icon": "",
		"location_id": "obras_municipales",
		"location_name": "Todo el mapa de Tecate",
		"arena_id": 7,
		"min_players": 2,
		"max_players": 16,
		"players_badge": "2 a 16 jugadores",
		"duration_seconds": 240,
		"reward_first": 50,
		"color": Color(0.88, 0.65, 0.05, 1.0),
		"description": AppStrings.MINIGAME_12_DESC,
		"controls": [
			{"input": "Espacio", "action": "Descender del avión y desplegar paracaídas"},
			{"input": "E", "action": "Recoger armas cómicas y suministros"},
			{"input": "Clic izquierdo", "action": "Usar equipamiento recolectado"}
		],
		"spawn_position": Vector3(47.75, 398.8, 38.4)
	}
]

static func get_all_minigames() -> Array[Dictionary]:
	return MINIGAMES

static func get_all_games() -> Array[Dictionary]:
	return MINIGAMES

static func get_minigame(game_id: int) -> Dictionary:
	for m in MINIGAMES:
		if m["id"] == game_id:
			return m
	return {}

static func get_game_title(game_id: int) -> String:
	var m = get_minigame(game_id)
	return m.get("title", AppStrings.MINIGAMES_HEADER_TITLE)

static func get_minigames_by_category(cat: int) -> Array[Dictionary]:
	if cat == Category.ALL:
		return MINIGAMES
	var filtered: Array[Dictionary] = []
	for m in MINIGAMES:
		if m["category"] == cat:
			filtered.append(m)
	return filtered

static func get_games_by_category(cat: int) -> Array[Dictionary]:
	return get_minigames_by_category(cat)

static func get_minigames_by_location(location_id: String) -> Array[Dictionary]:
	var filtered: Array[Dictionary] = []
	for m in MINIGAMES:
		if m["location_id"] == location_id:
			filtered.append(m)
	return filtered

static func get_games_for_location(location_id: String) -> Array[Dictionary]:
	return get_minigames_by_location(location_id)

static func get_location_info(location_id: String) -> Dictionary:
	return LOCATIONS.get(location_id, {})

static func get_all_locations() -> Array[Dictionary]:
	var list: Array[Dictionary] = []
	for k in LOCATIONS.keys():
		list.append(LOCATIONS[k])
	return list

static func format_location_tooltip(location_id: String) -> String:
	var loc = get_location_info(location_id)
	if loc.is_empty():
		return ""
	var games = get_minigames_by_location(location_id)
	if games.is_empty():
		return ""

	var primary = get_minigame(loc.get("primary_game_id", games[0]["id"]))
	var p_title = primary.get("title", AppStrings.MINIGAMES_HEADER_TITLE)

	if games.size() == 1:
		var status_tag = "" if primary.get("is_playable", false) else ", vista previa"
		return "Minijuego: %s%s" % [p_title, status_tag]
	else:
		var names: PackedStringArray = []
		for g in games:
			names.append(g["title"])
		return "%s: %s" % [loc.get("short_name", "Ubicación"), ", ".join(names)]
