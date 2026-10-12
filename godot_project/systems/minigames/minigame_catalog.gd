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
		"name": "Todos los Juegos",
		"short_name": "Todos",
		"badge": "MODO FIESTA",
		"icon": "🌟",
		"color": Color(1.0, 0.72, 0.0, 1.0) # Dorado Fiesta Wii Party
	},
	Category.ALL_VS_ALL: {
		"name": "Todos contra Todos",
		"short_name": "Todos vs. Todos",
		"badge": "TODOS CONTRA TODOS",
		"icon": "🔥",
		"color": Color(0.92, 0.22, 0.22, 1.0) # Rojo Fiesta Wii Party
	},
	Category.ONE_VS_ALL: {
		"name": "1 contra Todos",
		"short_name": "1 vs. Todos",
		"badge": "1 CONTRA TODOS",
		"icon": "🎯",
		"color": Color(0.0, 0.58, 0.88, 1.0) # Azul Wii Party
	},
	Category.DUEL_1V1: {
		"name": "Duelo y Mesa (1 vs. 1)",
		"short_name": "Duelo 1 vs. 1",
		"badge": "DUELO 1 VS. 1",
		"icon": "⚔️",
		"color": Color(0.18, 0.72, 0.32, 1.0) # Verde Wii Party
	}
}

const LOCATIONS: Dictionary = {
	"kiosko": {
		"id": "kiosko",
		"name": "Kiosko del Parque Miguel Hidalgo",
		"short_name": "Kiosko Central",
		"icon": "🏛️",
		"position": Vector3(-6.6844, 400.35, 2.6878),
		"radius": 6.5,
		"arena_id": 1,
		"primary_game_id": 1,
		"game_ids": [1, 7, 8],
		"color": Color(0.92, 0.22, 0.22, 1.0)
	},
	"parque_explanada": {
		"id": "parque_explanada",
		"name": "Explanada del Parque Miguel Hidalgo",
		"short_name": "Explanada del Parque",
		"icon": "🌳",
		"position": Vector3(-6.6844, 400.15, 14.5),
		"radius": 7.0,
		"arena_id": 2,
		"primary_game_id": 2,
		"game_ids": [2, 3, 4],
		"color": Color(1.0, 0.65, 0.12, 1.0)
	},
	"parque_mesas": {
		"id": "parque_mesas",
		"name": "Mesas y Fuente del Parque Hidalgo",
		"short_name": "Mesas del Parque",
		"icon": "♟️",
		"position": Vector3(-28.0, 400.85, -6.0),
		"radius": 5.5,
		"arena_id": 2,
		"primary_game_id": 9,
		"game_ids": [9],
		"color": Color(0.18, 0.72, 0.32, 1.0)
	},
	"foto_curiel": {
		"id": "foto_curiel",
		"name": "Foto Estudio Curiel (Cárdenas 33 / Libertad)",
		"short_name": "Foto Estudio Curiel",
		"icon": "📸",
		"position": Vector3(-53.5, 399.35, -18.5),
		"radius": 5.5,
		"arena_id": 5,
		"primary_game_id": 6,
		"game_ids": [6],
		"color": Color(0.0, 0.58, 0.88, 1.0)
	},
	"bus_hongo": {
		"id": "bus_hongo",
		"name": "Autobús Urbano 'El Hongo'",
		"short_name": "Autobús El Hongo",
		"icon": "🚌",
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
		"short_name": "Arena BBVA / Parque",
		"icon": "🥊",
		"position": Vector3(-62.0, 399.8, -18.0),
		"radius": 6.5,
		"arena_id": 3,
		"primary_game_id": 10,
		"game_ids": [10],
		"color": Color(0.55, 0.25, 0.88, 1.0)
	},
	"av_hidalgo": {
		"id": "av_hidalgo",
		"name": "Avenida Miguel Hidalgo y Cárdenas",
		"short_name": "Av. Miguel Hidalgo",
		"icon": "🐎",
		"position": Vector3(-48.0, 399.0, 25.0),
		"radius": 6.5,
		"arena_id": 6,
		"primary_game_id": 11,
		"game_ids": [11],
		"color": Color(0.18, 0.72, 0.32, 1.0)
	},
	"obras_municipales": {
		"id": "obras_municipales",
		"name": "Palacio Municipal y Obras de Tecate",
		"short_name": "Palacio Municipal",
		"icon": "🚜",
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
		"title": "Mi Kiosko",
		"full_title": "Mi Kiosko",
		"subtitle": "Batalla campal de empujones y bloqueos en la tarima",
		"category": Category.ALL_VS_ALL,
		"phase": 1,
		"is_playable": true,
		"icon": "🏛️",
		"location_id": "kiosko",
		"location_name": "Kiosko del Parque Miguel Hidalgo",
		"arena_id": 1,
		"min_players": 2,
		"max_players": 8,
		"players_badge": "2-8 Jugadores • Todos vs. Todos",
		"duration_seconds": 90,
		"reward_first": 50,
		"color": Color(0.92, 0.22, 0.22, 1.0),
		"description": "¡Sube a la plataforma octagonal del Kiosko! A base de empujones cómicos (slapstick) y bloqueos oportunos (parry), intenta lanzar a los demás por las escaleras o sobre la barandilla hacia el pasto. ¡Gana el último habitante en pie!",
		"controls": [
			{"input": "WASD + Espacio", "action": "Moverse y saltar en la tarima"},
			{"input": "Clic Izq / [G]", "action": "Empujar oponente (Knockback)"},
			{"input": "Clic Der / [F]", "action": "Bloqueo oportuno (Parry reflejante)"}
		],
		"spawn_position": Vector3(-6.6844, 401.80, 2.6878)
	},
	{
		"id": 2,
		"title": "Las Traes",
		"full_title": "Las Traes (La Roña Urbana)",
		"subtitle": "Persecución a toda velocidad por el Parque Hidalgo",
		"category": Category.ALL_VS_ALL,
		"phase": 1,
		"is_playable": true,
		"icon": "🏃",
		"location_id": "parque_explanada",
		"location_name": "Parque Miguel Hidalgo",
		"arena_id": 2,
		"min_players": 2,
		"max_players": 8,
		"players_badge": "2-8 Jugadores • Todos vs. Todos",
		"duration_seconds": 75,
		"reward_first": 50,
		"color": Color(1.0, 0.58, 0.10, 1.0),
		"description": "En todo el perímetro del Parque Hidalgo, los jugadores se corretean para pasarse la marca ('la traes'). Quedarse quieto es penalizado por el detector anti-campeo. ¡Pierde quien se quede con la marca al terminar el reloj y gana quien la haya portado menos tiempo!",
		"controls": [
			{"input": "WASD + Shift", "action": "Correr y esquivar por jardineras y bancas"},
			{"input": "Espacio", "action": "Saltar obstáculos urbanos"},
			{"input": "Proximidad (≤ 1.85 m)", "action": "Tocar a otro jugador para pasarle la roña"}
		],
		"spawn_position": Vector3(-6.6844, 400.35, 12.6878)
	},
	{
		"id": 3,
		"title": "Quemados",
		"full_title": "Quemados (Balón Prisionero Callejero)",
		"subtitle": "Pelotas de básquetbol balísticas que rebotan",
		"category": Category.ALL_VS_ALL,
		"phase": 1,
		"is_playable": true,
		"icon": "🏀",
		"location_id": "parque_explanada",
		"location_name": "Explanada del Parque Hidalgo",
		"arena_id": 2,
		"min_players": 2,
		"max_players": 8,
		"players_badge": "2-8 Jugadores • Todos vs. Todos",
		"duration_seconds": 90,
		"reward_first": 50,
		"color": Color(0.95, 0.36, 0.15, 1.0),
		"description": "¡Lanza pelotas de básquetbol que rebotan físicamente contra el piso, muros y bancas! Cualquier impacto directo o de rebote te elimina (¡incluso tu propia pelota!). No puedes quedarte quieto; gana el último sobreviviente en la explanada.",
		"controls": [
			{"input": "WASD + Shift", "action": "Esquivar proyectiles en movimiento"},
			{"input": "Clic Izq / [G]", "action": "Lanzar pelota balística (recarga 1.25 s)"},
			{"input": "Ratón", "action": "Apuntar trayectoria y ángulo de rebote"}
		],
		"spawn_position": Vector3(-6.6844, 400.35, 14.5)
	},
	{
		"id": 4,
		"title": "Escondidas",
		"full_title": "Las Escondidas",
		"subtitle": "Sigilo urbano, línea de visión y carrera a la base",
		"category": Category.ONE_VS_ALL,
		"phase": 2,
		"is_playable": false,
		"icon": "🙈",
		"location_id": "parque_explanada",
		"location_name": "Centro Histórico y Parque Hidalgo",
		"arena_id": 2,
		"min_players": 2,
		"max_players": 8,
		"players_badge": "1 vs. Todos • Sigilo Urbano",
		"duration_seconds": 120,
		"reward_first": 50,
		"color": Color(0.0, 0.62, 0.85, 1.0),
		"description": "Un buscador cuenta hasta 10 frente a la base mientras los demás se esconden tras fachadas y esquinas. Al terminar el conteo, el buscador debe lograr línea de visión directa para marcar a un escondido y correr a la base para eliminarlo. ¡Los escondidos pueden correr a la base para salvarse!",
		"controls": [
			{"input": "WASD + Shift", "action": "Esconderse o correr hacia la base de salvación"},
			{"input": "Clic Izq (Buscador)", "action": "Apuntar y marcar jugador en línea de visión"},
			{"input": "Tocar Base", "action": "'¡1, 2, 3 por mí y por todos mis amigos!'"}
		],
		"spawn_position": Vector3(-6.6844, 400.35, 14.5)
	},
	{
		"id": 5,
		"title": "Cóbrese",
		"full_title": "Cóbrese (Autobús El Hongo)",
		"subtitle": "Chofer contra pasajeros con morralla confusa",
		"category": Category.ONE_VS_ALL,
		"phase": 2,
		"is_playable": false,
		"icon": "🚌",
		"location_id": "bus_hongo",
		"location_name": "Autobús Urbano 'El Hongo'",
		"arena_id": 4,
		"min_players": 2,
		"max_players": 8,
		"players_badge": "1 vs. Todos • Rol y Agilidad Mental",
		"duration_seconds": 90,
		"reward_first": 50,
		"color": Color(0.95, 0.52, 0.12, 1.0),
		"description": "A bordo del autobús 'El Hongo' en movimiento, un jugador es el conductor y los demás son pasajeros que intentan pagar de menos con las combinaciones más absurdas de monedas y billetes a contrarreloj. El chofer debe validar si el monto cubre la tarifa antes de que se agote el tiempo.",
		"controls": [
			{"input": "Ratón / Teclas 1-5", "action": "Seleccionar monedas y billetes para el pasaje"},
			{"input": "[Y] Aceptar / [N] Rechazar", "action": "Visto bueno del conductor al cobro"},
			{"input": "Contrarreloj", "action": "Cálculo rápido antes de la siguiente parada"}
		],
		"spawn_position": Vector3(143.0, 402.17, -18.1)
	},
	{
		"id": 6,
		"title": "Curiel y los Fotógrafos",
		"full_title": "Curiel y los Fotógrafos",
		"subtitle": "Cacería fotográfica a contrarreloj por Tecate",
		"category": Category.ONE_VS_ALL,
		"phase": 2,
		"is_playable": false,
		"icon": "📸",
		"location_id": "foto_curiel",
		"location_name": "Foto Estudio Curiel (Cárdenas 33)",
		"arena_id": 5,
		"min_players": 2,
		"max_players": 8,
		"players_badge": "1 vs. Todos • Fotografía Urbana",
		"duration_seconds": 120,
		"reward_first": 50,
		"color": Color(0.12, 0.52, 0.90, 1.0),
		"description": "Un jugador se planta frente a Foto Estudio Curiel como jefe de redacción y exige por chat una fotografía que muestre cierto escenario, situación u objeto en el mapa. Los fotógrafos corren por Tecate para capturar la mejor toma y el jefe califica las entregas.",
		"controls": [
			{"input": "Chat (Jefe)", "action": "Publicar el encargo fotográfico de la ronda"},
			{"input": "[F1] + Clic Izq", "action": "Encuadrar y capturar fotografía para enviar"},
			{"input": "Calificación", "action": "El jefe evalúa y premia la mejor captura"}
		],
		"spawn_position": Vector3(-53.5, 399.35, -18.5)
	},
	{
		"id": 7,
		"title": "Zumba",
		"full_title": "Zumba en el Kiosko",
		"subtitle": "Imitación rítmica de gestos A-Z frente al Kiosko",
		"category": Category.ONE_VS_ALL,
		"phase": 3,
		"is_playable": false,
		"icon": "💃",
		"location_id": "kiosko",
		"location_name": "Kiosko del Parque Miguel Hidalgo",
		"arena_id": 1,
		"min_players": 2,
		"max_players": 8,
		"players_badge": "1 vs. Todos • Ritmo y Reflejos",
		"duration_seconds": 90,
		"reward_first": 50,
		"color": Color(0.88, 0.20, 0.62, 1.0),
		"description": "Un jugador sube al Kiosko como instructor y presiona cualquier letra A-Z (cada una provoca un paso o gesto cómico distinto). Los demás deben observar el gesto e imitarlo en tiempo real. Tras 90 segundos, ganan los alumnos que sigan en ritmo o el instructor si descalifica a todos.",
		"controls": [
			{"input": "Teclas [A] - [Z]", "action": "Ejecutar o imitar el paso de baile correspondiente"},
			{"input": "Observación Visual", "action": "Identificar el gesto del instructor sin pistas de texto"}
		],
		"spawn_position": Vector3(-6.6844, 401.80, 2.6878)
	},
	{
		"id": 8,
		"title": "Espejito, Espejito",
		"full_title": "Espejito, espejito, ¿quién es el candidato más bonito?",
		"subtitle": "Discursos en el Kiosko, coaliciones y votación secreta",
		"category": Category.ALL_VS_ALL,
		"phase": 3,
		"is_playable": false,
		"icon": "🗳️",
		"location_id": "kiosko",
		"location_name": "Kiosko del Parque Miguel Hidalgo",
		"arena_id": 1,
		"min_players": 3,
		"max_players": 8,
		"players_badge": "3-8 Jugadores • Todos vs. Todos",
		"duration_seconds": 180,
		"reward_first": 50,
		"color": Color(0.65, 0.30, 0.88, 1.0),
		"description": "Uno a uno suben al Kiosko a dar un discurso contrarreloj mientras en secreto se pactan coaliciones exactas entre aliados. Al terminar los discursos, todos votan por alguien (excepto por sí mismos). ¡El empate fuerza una segunda vuelta electoral entre los finalistas!",
		"controls": [
			{"input": "Chat / Globos de Texto", "action": "Pronunciar discurso de campaña en el Kiosko"},
			{"input": "Panel de Coalición", "action": "Seleccionar aliados exactos durante el discurso"},
			{"input": "Boleta Electoral", "action": "Emitir voto secreto o abstenerse"}
		],
		"spawn_position": Vector3(-6.6844, 401.80, 2.6878)
	},
	{
		"id": 9,
		"title": "Ajedrez en el Parque",
		"full_title": "Ajedrez en el Parque Hidalgo",
		"subtitle": "Partidas clásicas en las mesas de concreto bajo los árboles",
		"category": Category.DUEL_1V1,
		"phase": 3,
		"is_playable": false,
		"icon": "♟️",
		"location_id": "parque_mesas",
		"location_name": "Mesas del Parque Miguel Hidalgo",
		"arena_id": 2,
		"min_players": 2,
		"max_players": 2,
		"players_badge": "1 vs. 1 / 1 vs. NPC • Juego de Mesa",
		"duration_seconds": 300,
		"reward_first": 50,
		"color": Color(0.18, 0.72, 0.32, 1.0),
		"description": "Siéntate frente a frente en las tradicionales mesas de concreto con tablero cuadriculado bajo los árboles del Parque Hidalgo. Las piezas se mueven en 3D sobre la mesa mientras el resto de los jugadores pueden reunirse alrededor como espectadores.",
		"controls": [
			{"input": "[E] Sentarse en Mesa", "action": "Ocupar asiento de Blancas o Negras"},
			{"input": "Clic Izq", "action": "Seleccionar y mover pieza 3D en el tablero"}
		],
		"spawn_position": Vector3(-28.0, 400.85, -6.0)
	},
	{
		"id": 10,
		"title": "Kuchumá K.O.",
		"full_title": "Kuchumá K.O.",
		"subtitle": "Combate estilo Smash Bros en cámara fija y arenas urbanas",
		"category": Category.ALL_VS_ALL,
		"phase": 4,
		"is_playable": false,
		"icon": "🥊",
		"location_id": "bbva_azotea",
		"location_name": "Azotea BBVA / Parque Hidalgo / Tren",
		"arena_id": 3,
		"min_players": 2,
		"max_players": 8,
		"players_badge": "2-8 Jugadores • Combate / Equipos / 1v1",
		"duration_seconds": 150,
		"reward_first": 50,
		"color": Color(0.85, 0.16, 0.25, 1.0),
		"description": "Combate de violencia cómica total en cámara única fija con repertorio de ataques rico según cada personaje (Axel, Eli, Astorga). A mayor porcentaje de daño acumulado (%), mayor el impulso al ser golpeado. ¡Cuidado con caer a la calle o ser arrollado en los bordes!",
		"controls": [
			{"input": "WASD + Espacio (x2)", "action": "Movimiento lateral y doble salto aéreo"},
			{"input": "Clic Izq / [G]", "action": "Ataque normal y combos direccionales"},
			{"input": "Clic Der / [F]", "action": "Ataque especial y escudo/esquiva"}
		],
		"spawn_position": Vector3(-62.0, 399.8, -18.0)
	},
	{
		"id": 11,
		"title": "Justas",
		"full_title": "Justas a Caballo en Av. Hidalgo",
		"subtitle": "Duelo ecuestre a toda velocidad sobre Avenida Hidalgo",
		"category": Category.DUEL_1V1,
		"phase": 4,
		"is_playable": false,
		"icon": "🐎",
		"location_id": "av_hidalgo",
		"location_name": "Avenida Miguel Hidalgo",
		"arena_id": 6,
		"min_players": 2,
		"max_players": 2,
		"players_badge": "1 vs. 1 • Duelo de Precisión",
		"duration_seconds": 60,
		"reward_first": 50,
		"color": Color(0.20, 0.68, 0.38, 1.0),
		"description": "Dos jugadores montan a caballo en extremos opuestos de la Avenida Hidalgo y galopan a toda velocidad para ensartar al oponente. Gana quien combine mayor velocidad de galope y puntería precisa hacia el corazón en el instante del cruce.",
		"controls": [
			{"input": "[W] / [Espacio]", "action": "Espolear caballo y mantener ritmo de galope"},
			{"input": "Ratón", "action": "Estabilizar el pulso y apuntar la lanza al corazón"}
		],
		"spawn_position": Vector3(-48.0, 399.0, 25.0)
	},
	{
		"id": 12,
		"title": "Ranch Royale",
		"full_title": "Ranch Royale (Battle Royale Municipal)",
		"subtitle": "Supervivencia en todo Tecate con cierres de obra pública",
		"category": Category.ALL_VS_ALL,
		"phase": 4,
		"is_playable": false,
		"icon": "🚜",
		"location_id": "obras_municipales",
		"location_name": "Todo el Mapa de Tecate (Salto en Avión)",
		"arena_id": 7,
		"min_players": 2,
		"max_players": 16,
		"players_badge": "2-16 Jugadores • Todos vs. Todos",
		"duration_seconds": 240,
		"reward_first": 50,
		"color": Color(0.88, 0.65, 0.05, 1.0),
		"description": "Salta desde un avión en ruta regional (Tijuana, Mexicali, Ensenada, San Diego o Yuma) y busca armas cómicas por la ciudad. La zona segura se reduce manzana por manzana a medida que motoconformadoras y cintas del Gobierno de Tecate clausuran calles por obras.",
		"controls": [
			{"input": "[Espacio]", "action": "Saltar del avión y desplegar paracaídas"},
			{"input": "[E]", "action": "Recoger armas cómicas (resorteras, elotes, globos)"},
			{"input": "Clic Izq", "action": "Disparar / Usar equipamiento"}
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
	return m.get("title", "Minijuego")

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
	var p_title = primary.get("title", "Minijuego")
	var icon_str = loc.get("icon", "🎮")

	if games.size() == 1:
		var status_tag = "" if primary.get("is_playable", false) else " (Vista Previa)"
		return "%s [Q] Minijuego: %s%s  |  [M] Menú Wii Party" % [icon_str, p_title, status_tag]
	else:
		var names: PackedStringArray = []
		for g in games:
			names.append(g["title"])
		return "%s [Q] Jugar \"%s\"  |  [M] %s (%d minijuegos: %s)" % [
			icon_str,
			p_title,
			loc.get("short_name", "Ubicación"),
			games.size(),
			", ".join(names)
		]
