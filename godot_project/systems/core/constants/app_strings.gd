class_name AppStrings
extends RefCounted

## Cadenas de Texto Centralizadas para Tecate Simulator (Single Source of Truth)
##
## Centraliza todo texto visible para el usuario, mensajes de interfaz,
## telemetría urbana del HUD, prompts de interacción, identidades cívicas
## y métodos estáticos de formateo tipado.
##
## Cumple estrictamente con la normativa docs/strings.md v2.0.0:
## - Cero mayúsculas sostenidas (ALL CAPS prohibido en etiquetas, roles y badges).
## - Cero corchetes ([...]) o teclas físicas embebidas en cadenas.
## - Cero barras inclinadas (/) en textos y referencias geográficas.
## - Cero símbolos no tipográficos (sin infinito ∞, sin emojis, sin viñetas •).
## - Cero paréntesis (...) explicativos o redundantes.
## - Capitalización estricta de oración en español estándar.

# =============================================================================
# MARCA, SISTEMA Y METADATOS
# =============================================================================
const APP_NAME: String = "Tecate: Pueblo Mágico y Social"
const APP_SHORT_NAME: String = "Tecate Simulator"
const APP_TITLE_TECATE: String = "Tecate"
const APP_SUBTITLE: String = "Pueblo Mágico y Social"
const APP_VERSION_LABEL: String = "Versión"
const BRAND_PUEBLO_MAGICO: String = "Pueblo Mágico"

# =============================================================================
# ACCIONES GENÉRICAS Y NAVEGACIÓN DE BOTONES
# =============================================================================
const BTN_CONTINUE: String = "Continuar"
const BTN_MINIGAMES: String = "Minijuegos"
const BTN_RESPAWN: String = "Reaparecer"
const BTN_QUIT: String = "Salir"
const BTN_BACK: String = "Volver"
const BTN_BACK_TO_MAIN: String = "Volver al menú principal"
const BTN_CONFIRM: String = "Confirmar"
const BTN_CONFIRM_SELECTION: String = "Confirmar selección"
const BTN_CANCEL: String = "Cancelar"
const BTN_CLOSE: String = "Cerrar"
const BTN_ACCEPT: String = "Aceptar"
const BTN_SELECT: String = "Seleccionar"
const BTN_SAVE: String = "Guardar"
const BTN_RETRY: String = "Reintentar"

# =============================================================================
# PANTALLA DE INICIO Y SELECCIÓN DE PERSONAJE
# =============================================================================
const MENU_TITLE: String = "Tecate Simulator"
const MENU_SUBTITLE: String = "Simulación urbana, social y multijugador"
const CHAR_SELECT_TITLE: String = "Selección de personaje"
const CHAR_SELECT_SUBTITLE: String = "Elige tu identidad cívica para recorrer Tecate"

# Identidades de Personajes (Catálogo Cívico)
const CHAR_AXEL_DISPLAY_NAME: String = "Camarada"
const CHAR_AXEL_CODENAME: String = "Axel"
const CHAR_AXEL_TITLE: String = "Camarada"
const CHAR_AXEL_DESCRIPTION: String = "Rechazo la debilidad."
const CHAR_AXEL_GREETING: String = "¿Cómo andamios? ¿Eh? Mal ahí."

const CHAR_ELI_DISPLAY_NAME: String = "Diseñador"
const CHAR_ELI_CODENAME: String = "Eli"
const CHAR_ELI_TITLE: String = "Diseñador"
const CHAR_ELI_DESCRIPTION: String = "La IA crea una imagen, yo diseño una marca."
const CHAR_ELI_GREETING: String = "Sí, pensé que te encontraría."

const CHAR_ASTORGA_DISPLAY_NAME: String = "Músico"
const CHAR_ASTORGA_CODENAME: String = "Astorga"
const CHAR_ASTORGA_TITLE: String = "Músico"
const CHAR_ASTORGA_DESCRIPTION: String = "Me hace feliz formar parte de su grupo."
const CHAR_ASTORGA_GREETING: String = "¿Y mi camarada?"

# =============================================================================
# HUD DIEGÉTICO, BRÚJULA Y TELEMETRÍA URBANA
# =============================================================================
const HUD_SPEED: String = "Velocidad"
const HUD_ALTITUDE: String = "Altitud"
const HUD_SLOPE: String = "Pendiente"
const HUD_FUEL: String = "Combustible"
const HUD_SURFACE: String = "Superficie"
const HUD_UNIT_KMH: String = "km/h"
const HUD_UNIT_METERS_MSNM: String = "m snm"
const HUD_UNIT_PERCENT: String = "%"
const HUD_UNIT_DEGREES: String = "°"
const HINT_CENTRO_DEFAULT: String = "Zona Centro, Tecate"

# Puntos Cardinales
const CARDINAL_N: String = "N"
const CARDINAL_NE: String = "NE"
const CARDINAL_E: String = "E"
const CARDINAL_SE: String = "SE"
const CARDINAL_S: String = "S"
const CARDINAL_SO: String = "SO"
const CARDINAL_O: String = "O"
const CARDINAL_NO: String = "NO"

# Modos de Perspectiva y Cámara (Sin siglas numéricas 1P/3P ni paréntesis)
const CAMERA_MODE_1P: String = "Vista subjetiva"
const CAMERA_MODE_3P_SHOULDER: String = "Vista al hombro"
const CAMERA_MODE_2P_FRONTAL: String = "Observador frontal"
const CAMERA_MODE_3P_CLOSE: String = "Vista en tercera persona"
const CAMERA_MODE_3P_FAR: String = "Vista panorámica"
const CAMERA_TOGGLE_ACTION: String = "Cambiar cámara"

# Referencias Geográficas y Paisajísticas (Sin barras inclinadas '/')
const LANDMARK_RUMOROSA: String = "Hacia La Rumorosa y Mexicali"
const LANDMARK_CUCHUMA: String = "Hacia el Cerro Cuchumá y Tijuana"
const LANDMARK_ENSENADA: String = "Hacia Ensenada y el Valle de Guadalupe"
const LANDMARK_FRONTERA: String = "Hacia la frontera norte"

# Ejes del Gizmo de Orientación
const AXIS_X: String = "X"
const AXIS_Y: String = "Y"
const AXIS_Z: String = "Z"

# Roles Vehiculares (Sin mayúsculas sostenidas)
const VEHICLE_ROLE_DRIVER: String = "Conductor"
const VEHICLE_ROLE_PASSENGER: String = "Pasajero"
const VEHICLE_FUEL_INFINITE_ROUTE: String = "Ilimitado"

# =============================================================================
# PROMPTS DE INTERACCIÓN URBANA Y VEHICULAR (Sin corchetes [E], [R], [Ctrl])
# =============================================================================
const PROMPT_SIT: String = "Sentarse"
const PROMPT_STAND: String = "Levantarse"
const PROMPT_ENTER_BUS: String = "Subir al autobús"
const PROMPT_EXIT_BUS: String = "Bajar del autobús"
const PROMPT_DRIVE_VEHICLE: String = "Conducir vehículo"
const PROMPT_ENTER_PASSENGER: String = "Subir como pasajero"
const PROMPT_REFUEL_PUMP: String = "Cargar combustible"
const PROMPT_REFUEL: String = "Cargar combustible"
const PROMPT_DESCEND_STREET: String = "Descender a la calle"
const PROMPT_REQUEST_STOP: String = "Solicitar parada"
const PROMPT_SPEED_TOO_HIGH: String = "Velocidad muy alta para descender"
const PROMPT_OPEN_DOOR: String = "Abrir puerta"
const PROMPT_TALK_CITIZEN: String = "Conversar"

const PROMPT_STAND_SPACE: String = "Levantarse"
const PROMPT_CHANGE_SEAT: String = "Cambiar de asiento"
const DEFAULT_SEAT_NAME: String = "Asiento"

## Prompts de interacción parametrizados (Acción semántica pura)
static func prompt_sit_in(seat_name: String) -> String:
	return "Sentarse en %s" % seat_name

static func prompt_board_vehicle_door(vehicle_name: String) -> String:
	return "Abordar %s por la puerta" % vehicle_name

static func prompt_drive_vehicle(vehicle_name: String) -> String:
	return "Conducir %s" % vehicle_name

static func prompt_enter_passenger_vehicle(vehicle_name: String) -> String:
	return "Subir como pasajero a %s" % vehicle_name

static func prompt_vehicle_in_motion(speed: float) -> String:
	return "Vehículo en marcha a %.0f km/h" % speed

static func prompt_vehicle_full(vehicle_name: String) -> String:
	return "%s lleno" % vehicle_name

# =============================================================================
# =============================================================================
# MENÚ DE MINIJUEGOS Y RETOS (Sin mayúsculas sostenidas ni barras)
# =============================================================================
const MINIGAMES_HEADER_TITLE: String = "Minijuegos de Tecate"
const MINIGAMES_HEADER_SUBTITLE: String = "Parque Miguel Hidalgo y zonas emblemáticas"
const MINIGAMES_TAB_ALL: String = "Todos"
const MINIGAMES_TAB_ALL_VS_ALL: String = "Todos contra todos"
const MINIGAMES_TAB_ONE_VS_ALL: String = "Uno contra todos"
const MINIGAMES_TAB_DUEL: String = "Duelo individual"

const MINIGAMES_BADGE_PARTY_MODE: String = "Modo fiesta"
const MINIGAMES_BADGE_ALL_VS_ALL: String = "Todos contra todos"
const MINIGAMES_BADGE_ONE_VS_ALL: String = "Uno contra todos"
const MINIGAMES_BADGE_DUEL: String = "Duelo individual"

const MINIGAMES_BTN_PLAY: String = "Jugar"
const MINIGAMES_BTN_TEST_LOCATION: String = "Probar ubicación"
const MINIGAMES_BTN_TELEPORT: String = "Ir a la ubicación"
const MINIGAMES_BTN_CLOSE: String = "Cerrar menú"
const MINIGAMES_CLEAR_FILTER: String = "Mostrar todos los juegos"
const MINIGAMES_STATUS_READY: String = "Listo para iniciar."
const MINIGAMES_STATUS_PLAYABLE: String = "Disponible"
const MINIGAMES_STATUS_PLAYING: String = "En curso..."
const MINIGAMES_STATUS_FINISHED: String = "Juego concluido."
const MINIGAMES_SECTION_RULES: String = "Reglas del juego:"
const MINIGAMES_SECTION_CONTROLS: String = "Controles:"
const MINIGAMES_ELIM_DEFAULT: String = "ha sido eliminado"
const MINIGAMES_ELIM_FALL: String = "ha caído fuera de la tarima"
const MINIGAMES_ELIM_BALL: String = "ha recibido el impacto de una pelota"
const MINIGAMES_ELIM_TAG: String = "portaba la marca al finalizar el tiempo"

# Descripciones Literales del Documento Maestro (docs/minigames/master.md)
const MINIGAME_1_TITLE: String = "Mi Kiosko"
const MINIGAME_1_SUBTITLE: String = "Batalla campal de empujones y bloqueos en la tarima"
const MINIGAME_1_DESC: String = "Juego todos contra todos donde a base de empujones y bloqueos los jugadores intentan tirar a los demás por el acceso o la barandilla y ser el último en pie."

const MINIGAME_2_TITLE: String = "Las traes"
const MINIGAME_2_SUBTITLE: String = "Persecución por el Parque Miguel Hidalgo"
const MINIGAME_2_DESC: String = "Juego todos contra todos donde, en toda el área construida, los jugadores se persiguen para pasarse la marca. Hay un tiempo límite contrarreloj y pierde quien la porte al finalizar. Quedarse quieto es motivo de descalificación."

const MINIGAME_3_TITLE: String = "Quemados"
const MINIGAME_3_SUBTITLE: String = "Pelotas de básquetbol con rebote físico"
const MINIGAME_3_DESC: String = "Juego todos contra todos donde, en toda el área construida, los jugadores lanzan pelotas de básquetbol que rebotan según fuerza e impacto, con tiempo de recarga, y quedan eliminados si alguna pelota los toca, incluso la suya propia. No es posible quedarse quieto."

const MINIGAME_4_TITLE: String = "Escondidas"
const MINIGAME_4_SUBTITLE: String = "Sigilo urbano y carrera a la base"
const MINIGAME_4_DESC: String = "Juego uno contra todos donde, en toda el área construida, los jugadores se esconden mientras un jugador cuenta hasta diez mirando hacia una pared u objeto. Al finalizar el conteo, el buscador debe encontrar a los demás y tener línea de visión directa para apuntar sobre ellos, marcarlos y correr a su base de conteo para eliminarlos. Cada jugador escondido puede correr a la base de conteo para salvarse. Ganan quienes no sean descubiertos o el buscador si logra encontrar y eliminar a todos."

const MINIGAME_5_TITLE: String = "Cóbrese"
const MINIGAME_5_SUBTITLE: String = "Conductor contra pasajeros en autobús urbano"
const MINIGAME_5_DESC: String = "Juego uno contra todos donde un jugador es elegido como conductor para cobrar el pasaje en un autobús en movimiento. Con combinaciones variadas de monedas y billetes, cada pasajero debe intentar confundir al conductor pagando de menos respecto a la tarifa solicitada. El conductor debe validar la cantidad solo si es igual o mayor a la debida. Pierde el conductor si la recaudación total es inferior a la esperada, y pierde cada pasajero a quien le cobren la tarifa exacta o superior. Existe un contrarreloj para ambas partes donde agotar el tiempo conlleva penalización."

const MINIGAME_6_TITLE: String = "Curiel y los Fotógrafos"
const MINIGAME_6_SUBTITLE: String = "Cacería fotográfica urbana a contrarreloj"
const MINIGAME_6_DESC: String = "Juego uno contra todos donde un jugador se coloca frente a Foto Estudio Curiel como jefe y exige mediante el chat a contrarreloj una fotografía que muestre determinado escenario, situación u objeto en el mapa. El jefe califica las fotografías y gana la mejor, o gana el jefe si existe al menos una foto entregada y ninguna resulta satisfactoria. Si nadie entrega fotografías, se declara empate entre los fotógrafos y pierde el jefe."

const MINIGAME_7_TITLE: String = "Zumba"
const MINIGAME_7_SUBTITLE: String = "Imitación rítmica de gestos frente al Kiosko"
const MINIGAME_7_DESC: String = "Juego uno contra todos donde un jugador sube al Kiosko y presiona cualquier letra de la A a la Z, provocando cada una un gesto distinto, y los demás deben, de solo ver el gesto, imitarlo. Tras noventa segundos, ganan quienes sigan en ritmo o el instructor en cuanto ya no quede nadie."

const MINIGAME_8_TITLE: String = "Espejito, espejito, ¿quién es el candidato más bonito?"
const MINIGAME_8_SUBTITLE: String = "Discursos en el Kiosko, coaliciones y votaciones"
const MINIGAME_8_DESC: String = "Juego todos contra todos donde uno a uno suben al Kiosko a dar un discurso contrarreloj mediante globos de texto y, al finalizar las participaciones, todos deben votar por alguien excepto por uno mismo. Existe la opción de conformar coaliciones durante el tiempo del discurso, lo cual requiere que los integrantes en cada turno seleccionen a sus aliados y coincidan con exactitud al final. También es posible abstenerse de votar. El empate anula la elección y da paso a una segunda vuelta entre los empatados, dejando al resto únicamente como votantes. Es posible elegir no postularse como candidato desde el inicio, siempre que haya al menos dos candidatos y un votante."

const MINIGAME_9_TITLE: String = "Ajedrez en el Parque"
const MINIGAME_9_SUBTITLE: String = "Partidas clásicas en mesas de concreto"
const MINIGAME_9_DESC: String = "Duelo individual de ajedrez clásico en las tradicionales mesas de concreto bajo los árboles del Parque Miguel Hidalgo, con piezas tridimensionales sobre el tablero y modo de espectador para los transeúntes."

const MINIGAME_10_TITLE: String = "Kuchumá K.O."
const MINIGAME_10_SUBTITLE: String = "Combate en plataformas con cámara fija y violencia cómica"
const MINIGAME_10_DESC: String = "Juego estilo combate en plataforma con múltiples modalidades, ya sea todos contra todos, por equipos, uno contra uno y dos contra dos, en cámara única fija, con repertorio de movimientos rico y diverso según cada personaje, violencia cómica total, contador de daño, diversas ubicaciones como la azotea de BBVA, el Parque Miguel Hidalgo con las calles como límite fuera de juego y vagones del tren, y eliminación por caer fuera del plano visible o por elementos lógicos del entorno como vehículos y trenes a toda velocidad en la vía pública."

const MINIGAME_11_TITLE: String = "Justas"
const MINIGAME_11_SUBTITLE: String = "Duelo ecuestre a toda velocidad en Avenida Miguel Hidalgo"
const MINIGAME_11_DESC: String = "A caballo, dos jugadores sobre la Avenida Miguel Hidalgo corren a toda velocidad para ensartar al oponente. Gana quien, combinando velocidad y puntería al corazón, resulte más letal."

const MINIGAME_12_TITLE: String = "Ranch Royale"
const MINIGAME_12_SUBTITLE: String = "Supervivencia urbana y cierre de calles por obras"
const MINIGAME_12_DESC: String = "Juego todos contra todos donde, en todo el mapa de Tecate, los jugadores encuentran armas cómicas y se enfrentan con ellas. La zona segura se reduce y desplaza mediante un polígono delimitado por manzanas urbanas cada vez menor. La barrera diegética son las motoconformadoras y cintas de precaución del Gobierno de Tecate cerrando calles por obras públicas. Al inicio, los jugadores descienden desde un avión en trayectoria aérea regional y gana el último habitante en pie."

# =============================================================================
# RED MULTIJUGADOR Y CONECTIVIDAD CÍVICA
# =============================================================================
const NET_STATUS_ONLINE: String = "En línea"
const NET_STATUS_OFFLINE: String = "Desconectado"
const NET_STATUS_CONNECTING: String = "Conectando al servidor..."
const NET_STATUS_DISCONNECTED: String = "Desconectado"
const NET_STATUS_RECONNECTING: String = "Reconectando..."
const NET_STATUS_SYNCING: String = "Sincronizando..."
const NET_ERROR_GENERIC: String = "Error de conexión con el servidor."
const NET_ERROR_TIMEOUT: String = "Tiempo de espera agotado al conectar."
const PROMPT_STOP_REQUESTED: String = "Parada solicitada para el próximo cruce"

# =============================================================================
# CONDICIONES CLIMÁTICAS
# =============================================================================
const WEATHER_CLEAR: String = "Despejado"
const WEATHER_PARTLY_CLOUDY: String = "Parcialmente nublado"
const WEATHER_CLOUDY: String = "Nublado"
const WEATHER_LIGHT_RAIN: String = "Lluvia ligera"
const WEATHER_RAIN: String = "Lluvia"
const WEATHER_STORM: String = "Tormenta"

# =============================================================================
# MÉTODOS ESTÁTICOS DE FORMATEO TIPADO
# =============================================================================

## Formatea el estado de red con host y jugadores
static func format_network_status_host(host: String, player_count: int) -> String:
	return "En línea, servidor %s, %d jugadores" % [host, player_count]

## Formatea el estado de red con latencia y jugadores
static func format_network_status_ping(ping_ms: int, player_count: int) -> String:
	return "En línea, %d ms, %d jugadores" % [ping_ms, player_count]

## Formatea el saldo del jugador en moneda local (minúsculas normativas)
static func format_currency_pesos(pesos: int) -> String:
	return "%d pesos" % pesos

## Formatea la velocidad con precisión estándar
static func format_speed(speed_kmh: float) -> String:
	return "%4.1f %s" % [speed_kmh, HUD_UNIT_KMH]

## Formatea la altitud sobre el nivel del mar
static func format_altitude(meters: float) -> String:
	return "%5.1f %s" % [meters, HUD_UNIT_METERS_MSNM]

## Formatea la pendiente topográfica
static func format_slope(degrees: float) -> String:
	var sign_str: String = "+" if degrees > 0.5 else ("-" if degrees < -0.5 else "")
	return "%s%3.1f%s" % [sign_str, abs(degrees), HUD_UNIT_DEGREES]

## Formatea el rumbo y calle de la brújula urbana
static func format_compass_street(heading_deg: int, cardinal: String, street_hint: String) -> String:
	return "%03d° %s, %s" % [heading_deg, cardinal, street_hint]

## Formatea el indicador de perspectiva y prompt de interacción del HUD
static func format_hud_mode_badge(camera_mode: String, prompt: String = "") -> String:
	if prompt.is_empty():
		return "%s: %s" % [camera_mode, BTN_MINIGAMES]
	return "%s: %s" % [camera_mode, prompt]

## Formatea el bloque multilínea de telemetría a pie
static func format_pedestrian_telemetry(speed_kmh: float, altitude_m: float, slope_deg: float) -> String:
	return "%s: %s\n%s:   %s\n%s: %s" % [
		HUD_SPEED, format_speed(speed_kmh),
		HUD_ALTITUDE, format_altitude(altitude_m),
		HUD_SLOPE, format_slope(slope_deg)
	]

## Formatea el bloque multilínea de telemetría a bordo de un vehículo
static func format_vehicle_telemetry(
	vehicle_name: String,
	role_name: String,
	speed_kmh: float,
	fuel_pct: float,
	is_infinite_fuel: bool,
	surface_name: String,
	slope_deg: float
) -> String:
	var fuel_str: String = VEHICLE_FUEL_INFINITE_ROUTE if is_infinite_fuel else ("%3.0f%%" % fuel_pct)
	return "%s, %s\n%s: %s\n%s: %s\n%s: %s\n%s: %s" % [
		vehicle_name, role_name,
		HUD_SPEED, format_speed(speed_kmh),
		HUD_FUEL, fuel_str,
		HUD_SURFACE, surface_name,
		HUD_SLOPE, format_slope(slope_deg)
	]

## Convierte un ángulo en grados (0 a 360) a su rumbo cardinal en español
static func get_cardinal_direction(deg: float) -> String:
	var d: float = fposmod(deg, 360.0)
	if d >= 337.5 or d < 22.5:
		return CARDINAL_N
	elif d < 67.5:
		return CARDINAL_NE
	elif d < 112.5:
		return CARDINAL_E
	elif d < 157.5:
		return CARDINAL_SE
	elif d < 202.5:
		return CARDINAL_S
	elif d < 247.5:
		return CARDINAL_SO
	elif d < 292.5:
		return CARDINAL_O
	else:
		return CARDINAL_NO

## Formatea la etiqueta de fase del minijuego
static func format_minigame_phase(phase: int) -> String:
	return "Fase %d" % phase

## Formatea el distintivo de fase previa
static func format_minigame_phase_preview(phase: int) -> String:
	return "Fase %d, vista previa" % phase

## Formatea el número de tarjeta en el catálogo
static func format_minigame_tile_number(game_id: int) -> String:
	return "%02d" % game_id

## Formatea la duración y recompensa en pesos
static func format_minigame_duration_reward(seconds: int, pesos: int) -> String:
	return "%d s, %d pesos" % [seconds, pesos]

## Formatea la cabecera de filtro por ubicación
static func format_minigame_location_filter(location_name: String) -> String:
	return "Juegos en %s" % location_name

## Formatea la mención de ubicación en la ficha
static func format_minigame_location_label(location_name: String) -> String:
	return "Ubicación en Tecate: %s" % location_name

## Formatea la pestaña de categoría con contador
static func format_minigame_tab_count(tab_name: String, count: int) -> String:
	return "%s: %d" % [tab_name, count]

## Formatea el aviso de convocatoria a una reta
static func format_minigame_summon_notice(game_name: String) -> String:
	return "Convocatoria: %s" % game_name

## Formatea la notificación de eliminación de un jugador
static func format_minigame_elimination(player_id: int, reason_text: String) -> String:
	return "Jugador %d %s." % [player_id, reason_text]

## Formatea el aviso de sede futura programada
static func format_minigame_upcoming(title: String, location_name: String, phase: int) -> String:
	return "Sede de %s, %s, fase %d" % [title, location_name, phase]

## Formatea el título del podio de resultados
static func format_minigame_results(game_title: String) -> String:
	return "Resultados: %s" % game_title

## Formatea la mención del jugador ganador
static func format_minigame_winner(winner_id: int) -> String:
	return "Ganador: Jugador %d" % winner_id

## Formatea una posición individual en la tabla de podio
static func format_minigame_ranking_entry(rank: int, player_id: int) -> String:
	return "%d. Jugador %d" % [rank, player_id]


