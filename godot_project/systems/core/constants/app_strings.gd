class_name AppStrings
extends RefCounted

## Cadenas de Texto Centralizadas para Tecate Simulator (Single Source of Truth)
##
## Centraliza todo texto visible para el usuario, mensajes de interfaz,
## telemetría urbana del HUD, prompts de interacción, identidades cívicas
## y métodos estáticos de formateo tipado.
##
## Referencia normativa: docs/strings.md

# =============================================================================
# MARCA, SISTEMA Y METADATOS
# =============================================================================
const APP_NAME: String = "Tecate: Pueblo Mágico y Social"
const APP_SHORT_NAME: String = "Tecate Simulator"
const APP_TITLE_TECATE: String = "TECATE"
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
const MENU_SUBTITLE: String = "Simulación Urbana, Social y Multijugador"
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
const HUD_SPEED: String = "VELOCIDAD"
const HUD_ALTITUDE: String = "ALTITUD"
const HUD_SLOPE: String = "PENDIENTE"
const HUD_FUEL: String = "COMBUSTIBLE"
const HUD_SURFACE: String = "SUPERFICIE"
const HUD_UNIT_KMH: String = "km/h"
const HUD_UNIT_METERS_MSNM: String = "m snm"
const HUD_UNIT_PERCENT: String = "%"
const HUD_UNIT_DEGREES: String = "°"
const HINT_CENTRO_DEFAULT: String = "Zona Centro - Tecate, Pueblo Mágico"

# Puntos Cardinales
const CARDINAL_N: String = "N"
const CARDINAL_NE: String = "NE"
const CARDINAL_E: String = "E"
const CARDINAL_SE: String = "SE"
const CARDINAL_S: String = "S"
const CARDINAL_SO: String = "SO"
const CARDINAL_O: String = "O"
const CARDINAL_NO: String = "NO"

# Modos de Perspectiva y Cámara
const CAMERA_MODE_1P: String = "1P - Vista subjetiva"
const CAMERA_MODE_3P_CLOSE: String = "3P - Vista cercana"
const CAMERA_MODE_3P_FAR: String = "3P - Vista lejana"
const CAMERA_TOGGLE_HINT: String = "[V / F5]"

# Iconos e Identificadores Visuales Diegéticos
const CURRENCY_COIN_ICON: String = "🪙 "

# Referencias Geográficas y Paisajísticas
const LANDMARK_RUMOROSA: String = "Hacia La Rumorosa / Mexicali"
const LANDMARK_CUCHUMA: String = "Hacia el Cerro Cuchumá / Tijuana"
const LANDMARK_ENSENADA: String = "Hacia Ensenada / Valle de Guadalupe"
const LANDMARK_FRONTERA: String = "Hacia la Frontera / USA"

# Ejes del Gizmo de Orientación
const AXIS_X: String = "X"
const AXIS_Y: String = "Y"
const AXIS_Z: String = "Z"

# Roles Vehiculares
const VEHICLE_ROLE_DRIVER: String = "CONDUCTOR"
const VEHICLE_ROLE_PASSENGER: String = "PASAJERO"
const VEHICLE_FUEL_INFINITE_ROUTE: String = "∞ (Ruta)"

# =============================================================================
# PROMPTS DE INTERACCIÓN URBANA Y VEHICULAR
# =============================================================================
const PROMPT_SIT: String = "[E] Sentarse"
const PROMPT_STAND: String = "[E] Levantarse"
const PROMPT_ENTER_BUS: String = "[E] Subir al autobús"
const PROMPT_EXIT_BUS: String = "[E] Bajar del autobús"
const PROMPT_DRIVE_VEHICLE: String = "[E] Conducir vehículo"
const PROMPT_ENTER_PASSENGER: String = "[E] Subir como pasajero"
const PROMPT_REFUEL_PUMP: String = "[E] Cargar combustible"
const PROMPT_REFUEL: String = "[R] Repostar"
const PROMPT_DESCEND_STREET: String = "[E] Descender a la calle"
const PROMPT_REQUEST_STOP: String = "[B / T] Solicitar parada"
const PROMPT_SPEED_TOO_HIGH: String = "Velocidad muy alta para descender"
const PROMPT_OPEN_DOOR: String = "[E] Abrir puerta"
const PROMPT_TALK_CITIZEN: String = "[E] Conversar"

const PROMPT_STAND_SPACE: String = "[E] o [Espacio] Levantarse"
const PROMPT_CHANGE_SEAT: String = "[Ctrl] Cambiar asiento"
const DEFAULT_SEAT_NAME: String = "Asiento"

## Prompts de interacción parametrizados
static func prompt_sit_in(seat_name: String) -> String:
	return "[E] Sentarse en %s" % seat_name

static func prompt_board_vehicle_door(vehicle_name: String) -> String:
	return "[E] Abordar %s por la puerta" % vehicle_name

static func prompt_drive_vehicle(vehicle_name: String) -> String:
	return "[E] Conducir %s" % vehicle_name

static func prompt_enter_passenger_vehicle(vehicle_name: String) -> String:
	return "[E] Subir como pasajero a %s" % vehicle_name

static func prompt_vehicle_in_motion(speed: float) -> String:
	return "Vehículo en marcha (%.0f km/h)" % speed

static func prompt_vehicle_full(vehicle_name: String) -> String:
	return "%s (Lleno)" % vehicle_name

# =============================================================================
# MENÚ DE MINIJUEGOS (WII PARTY) Y RETOS
# =============================================================================
const MINIGAMES_HEADER_TITLE: String = "MINIJUEGOS DE TECATE"
const MINIGAMES_HEADER_SUBTITLE: String = "Parque Miguel Hidalgo y Zonas Emblemáticas"
const MINIGAMES_TAB_ALL: String = "Todos"
const MINIGAMES_TAB_ALL_VS_ALL: String = "Todos vs. Todos"
const MINIGAMES_TAB_ONE_VS_ALL: String = "1 vs. Todos"
const MINIGAMES_TAB_DUEL: String = "Duelo 1 vs. 1"

const MINIGAMES_BADGE_PARTY_MODE: String = "MODO FIESTA"
const MINIGAMES_BADGE_ALL_VS_ALL: String = "TODOS CONTRA TODOS"
const MINIGAMES_BADGE_ONE_VS_ALL: String = "1 CONTRA TODOS"
const MINIGAMES_BADGE_DUEL: String = "DUELO 1 VS. 1"

const MINIGAMES_BTN_PLAY: String = "Jugar"
const MINIGAMES_BTN_TELEPORT: String = "Ir a la ubicación"
const MINIGAMES_CLEAR_FILTER: String = "Mostrar todos los juegos"
const MINIGAMES_STATUS_READY: String = "Listo para iniciar."
const MINIGAMES_STATUS_PLAYING: String = "En curso..."
const MINIGAMES_STATUS_FINISHED: String = "¡Juego concluido!"
const MINIGAMES_SECTION_RULES: String = "Reglas del juego:"
const MINIGAMES_SECTION_CONTROLS: String = "Controles:"

# =============================================================================
# RED MULTIJUGADOR Y CONECTIVIDAD CÍVICA
# =============================================================================
const NET_STATUS_ONLINE: String = "En línea"
const NET_STATUS_CONNECTING: String = "Conectando al servidor..."
const NET_STATUS_DISCONNECTED: String = "Desconectado"
const NET_STATUS_RECONNECTING: String = "Reconectando..."
const NET_STATUS_SYNCING: String = "Sincronizando..."
const NET_ERROR_GENERIC: String = "Error de conexión con el servidor."
const NET_ERROR_TIMEOUT: String = "Tiempo de espera agotado al conectar."

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

## Formatea el saldo del jugador en moneda local
static func format_currency_pesos(pesos: int) -> String:
	return "%d PESOS" % pesos

## Formatea la velocidad con precisión estándar
static func format_speed(speed_kmh: float) -> String:
	return "%4.1f %s" % [speed_kmh, HUD_UNIT_KMH]

## Formatea la altitud sobre el nivel del mar
static func format_altitude(meters: float) -> String:
	return "%5.1f %s" % [meters, HUD_UNIT_METERS_MSNM]

## Formatea la pendiente topográfica con signo explícito
static func format_slope(degrees: float) -> String:
	var sign_str: String = "+" if degrees > 0.5 else ("-" if degrees < -0.5 else "")
	return "%s%3.1f%s" % [sign_str, abs(degrees), HUD_UNIT_DEGREES]

## Formatea el rumbo y calle de la brújula urbana
static func format_compass_street(heading_deg: int, cardinal: String, street_hint: String) -> String:
	return "%03d° %s  |  %s" % [heading_deg, cardinal, street_hint]

## Formatea el indicador de perspectiva y prompt de interacción del HUD
static func format_hud_mode_badge(camera_mode: String, prompt: String = "") -> String:
	if prompt.is_empty():
		return "%s %s   |   [M] %s" % [CAMERA_TOGGLE_HINT, camera_mode, BTN_MINIGAMES]
	return "%s %s   |   %s" % [CAMERA_TOGGLE_HINT, camera_mode, prompt]

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
	return "[%s - %s]\n%s: %s\n%s: %s\n%s: %s\n%s: %s" % [
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
