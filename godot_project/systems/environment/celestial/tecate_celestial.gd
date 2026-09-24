class_name TecateCelestial
extends RefCounted

## Motor de Cálculo Astronómico y Posicionamiento Celeste para Tecate, B.C.
##
## Implementa las efemérides analíticas del Sol y la Luna calibradas para el
## origen geodésico de Tecate, Baja California y sincronizadas con el huso horario
## oficial de la franja fronteriza (America/Tijuana: UTC-8 y UTC-7 con Horario Estacional).

# Coordenadas geodésicas del origen municipal de Tecate (SISTEMA_COORDENADAS_Y_POSICIONAMIENTO_ESPACIAL.md)
const ORIGIN_LAT_DEG: float = 32.5732357
const ORIGIN_LON_DEG: float = -116.6265288

const DEG_TO_RAD: float = PI / 180.0
const RAD_TO_DEG: float = 180.0 / PI

class CelestialState:
	var local_datetime: Dictionary = {}
	var is_dst: bool = false
	var utc_time_unix: int = 0
	
	# Ángulos solares (radianes)
	var sun_altitude_rad: float = 0.0
	var sun_azimuth_rad: float = 0.0
	var sun_direction: Vector3 = Vector3.UP
	var sun_visible: bool = true
	
	# Ángulos lunares (radianes)
	var moon_altitude_rad: float = 0.0
	var moon_azimuth_rad: float = 0.0
	var moon_direction: Vector3 = Vector3.DOWN
	var moon_visible: bool = false
	
	# Fase lunar: 0.0 = Nueva, 0.25 = Cuarto creciente, 0.5 = Llena, 0.75 = Cuarto menguante, 1.0 = Nueva
	var moon_phase: float = 0.5
	var moon_illuminated_fraction: float = 1.0
	var moon_phase_name: String = "Llena"
	var sun_ecliptic_lon_rad: float = 0.0
	var moon_ecliptic_lon_rad: float = 0.0


## Determina si en una fecha y hora UTC dada rige el Horario Estacional (DST)
## en la franja fronteriza norte de México (Tecate y Tijuana).
##
## De acuerdo a la Ley de los Husos Horarios en los Estados Unidos Mexicanos (2022),
## los municipios de la frontera norte mantienen el horario de verano sincronizado con California:
## - Inicia: Segundo domingo de marzo a las 02:00 horas locales (UTC-8 -> UTC-7).
## - Termina: Primer domingo de noviembre a las 02:00 horas locales (UTC-7 -> UTC-8).
static func is_tecate_dst(year: int, month: int, day: int, hour_utc: int) -> bool:
	if month < 3 or month > 11:
		return false
	if month > 3 and month < 11:
		return true
		
	# Mes de marzo: cálculo del segundo domingo
	if month == 3:
		var second_sunday = _get_nth_sunday_of_month(year, 3, 2)
		if day < second_sunday:
			return false
		elif day > second_sunday:
			return true
		else:
			# El segundo domingo a las 02:00 locales (10:00 UTC)
			return hour_utc >= 10
			
	# Mes de noviembre: cálculo del primer domingo
	if month == 11:
		var first_sunday = _get_nth_sunday_of_month(year, 11, 1)
		if day < first_sunday:
			return true
		elif day > first_sunday:
			return false
		else:
			# El primer domingo a las 02:00 locales (09:00 UTC)
			return hour_utc < 9
			
	return false

## Encuentra el día del mes correspondiente al n-ésimo domingo
static func _get_nth_sunday_of_month(year: int, month: int, n: int) -> int:
	var count = 0
	for d in range(1, 32):
		var time_dict = {"year": year, "month": month, "day": d, "hour": 12, "minute": 0, "second": 0}
		var unix = Time.get_unix_time_from_datetime_dict(time_dict)
		var check = Time.get_datetime_dict_from_unix_time(unix)
		# En Godot Time.get_datetime_dict_from_unix_time: weekday 0 es domingo (o según convención de Godot, Time.WEEKDAY_SUNDAY = 0)
		if check.weekday == Time.WEEKDAY_SUNDAY:
			count += 1
			if count == n:
				return d
	return 1

## Convierte un timestamp UNIX o diccionario UTC al tiempo local civil de Tecate
static func get_tecate_local_datetime(unix_utc: int) -> Dictionary:
	var utc_dt = Time.get_datetime_dict_from_unix_time(unix_utc)
	var dst = is_tecate_dst(utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour)
	var offset_hours = -7 if dst else -8
	var local_unix = unix_utc + (offset_hours * 3600)
	var local_dt = Time.get_datetime_dict_from_unix_time(local_unix)
	local_dt["is_dst"] = dst
	local_dt["tz_offset"] = offset_hours
	local_dt["tz_name"] = "PDT" if dst else "PST"
	return local_dt

## Calcula el estado astronómico completo (Sol, Luna y Fase) para Tecate
## Si unix_utc <= 0, toma el tiempo actual del sistema.
static func calculate_celestial_state(unix_utc: int = -1) -> CelestialState:
	if unix_utc <= 0:
		unix_utc = int(Time.get_unix_time_from_system())
		
	var state = CelestialState.new()
	state.utc_time_unix = unix_utc
	state.local_datetime = get_tecate_local_datetime(unix_utc)
	state.is_dst = state.local_datetime.get("is_dst", false)
	
	var utc_dt = Time.get_datetime_dict_from_unix_time(unix_utc)
	var year = utc_dt.year
	var month = utc_dt.month
	var day = utc_dt.day
	var hour = utc_dt.hour
	var minute = utc_dt.minute
	var second = utc_dt.second
	
	# Día juliano (Julian Day)
	var jd = _calculate_julian_day(year, month, day, hour, minute, second)
	var d = jd - 2451545.0 # Días desde J2000.0
	
	# 1. Posición del Sol (Algoritmo solar NOAA/PSA de alta precisión)
	_calculate_sun_position(d, hour, minute, second, state)
	
	# 2. Posición de la Luna (Efemérides orbitales simplificadas de Brown)
	_calculate_moon_position(d, hour, minute, second, state)
	
	# 3. Cálculo de la fase lunar analítica
	_calculate_moon_phase(state)
	
	# 4. Proyección a coordenadas tridimensionales de Godot
	# Canónico de Tecate: Norte = -Z, Sur = +Z, Este = +X, Oeste = -X, Cenit = +Y
	state.sun_direction = _horizontal_to_godot(state.sun_altitude_rad, state.sun_azimuth_rad)
	state.moon_direction = _horizontal_to_godot(state.moon_altitude_rad, state.moon_azimuth_rad)
	
	# Visibilidad
	state.sun_visible = state.sun_altitude_rad > -0.10 # Visible durante el día y crepúsculo civil
	state.moon_visible = state.moon_altitude_rad > -0.05
	
	return state

## Día Juliano estándar
static func _calculate_julian_day(y: int, m: int, d: int, h: int, min: int, s: int) -> float:
	if m <= 2:
		y -= 1
		m += 12
	var a = int(floor(float(y) / 100.0))
	var b = 2 - a + int(floor(float(a) / 4.0))
	var day_frac = float(d) + (float(h) + float(min) / 60.0 + float(s) / 3600.0) / 24.0
	return int(floor(365.25 * float(y + 4716))) + int(floor(30.6001 * float(m + 1))) + day_frac + float(b) - 1524.5

## Posición solar analítica
static func _calculate_sun_position(d: float, h: int, min: int, s: int, state: CelestialState) -> void:
	# Longitud media y anomalía media del Sol (grados)
	var L = fmod(280.460 + 0.9856474 * d, 360.0)
	var g = fmod(357.528 + 0.9856003 * d, 360.0) * DEG_TO_RAD
	
	# Longitud eclíptica
	var lambda = (L + 1.915 * sin(g) + 0.020 * sin(2.0 * g)) * DEG_TO_RAD
	# Oblicuidad de la eclíptica
	var epsilon = (23.439 - 0.0000004 * d) * DEG_TO_RAD
	
	# Ascensión recta y declinación
	var alpha = atan2(cos(epsilon) * sin(lambda), cos(lambda))
	var delta = asin(sin(epsilon) * sin(lambda))
	
	# Tiempo sidéreo medio en Greenwich (GMST) en radianes
	var decimal_hours = float(h) + float(min) / 60.0 + float(s) / 3600.0
	var gmst_deg = fmod(280.46061837 + 360.98564736629 * d, 360.0)
	var lmst_rad = fmod(gmst_deg + ORIGIN_LON_DEG, 360.0) * DEG_TO_RAD
	if lmst_rad < 0.0:
		lmst_rad += TAU
		
	# Ángulo horario (Hour Angle)
	var H = lmst_rad - alpha
	var lat_rad = ORIGIN_LAT_DEG * DEG_TO_RAD
	
	# Elevación (altitud) del Sol
	var sin_alt = sin(lat_rad) * sin(delta) + cos(lat_rad) * cos(delta) * cos(H)
	var altitude = asin(clamp(sin_alt, -1.0, 1.0))
	
	# Azimut del Sol (medido desde el Norte = 0, Este = 90, Sur = 180, Oeste = 270)
	var cos_az = (sin(delta) - sin(lat_rad) * sin(altitude)) / (cos(lat_rad) * cos(altitude) + 1e-7)
	cos_az = clamp(cos_az, -1.0, 1.0)
	var azimuth = acos(cos_az)
	if sin(H) > 0.0:
		azimuth = TAU - azimuth
		
	state.sun_altitude_rad = altitude
	state.sun_azimuth_rad = azimuth
	state.sun_ecliptic_lon_rad = lambda

## Posición lunar analítica
static func _calculate_moon_position(d: float, _h: int, _min: int, _s: int, state: CelestialState) -> void:
	# Elementos orbitales principales de la Luna
	var L = fmod(218.316 + 13.176396 * d, 360.0) * DEG_TO_RAD # Longitud media
	var M = fmod(134.963 + 13.064993 * d, 360.0) * DEG_TO_RAD # Anomalía media Luna
	var F = fmod(93.272 + 13.229350 * d, 360.0) * DEG_TO_RAD  # Argumento de latitud
	
	# Longitud eclíptica de la Luna (aproximación con perturbaciones)
	var lambda_m = L + (6.289 * sin(M)) * DEG_TO_RAD
	state.moon_ecliptic_lon_rad = lambda_m

	# Latitud eclíptica de la Luna
	var beta_m = (5.128 * sin(F)) * DEG_TO_RAD
	var epsilon = 23.439 * DEG_TO_RAD
	
	# Coordenadas ecuatoriales de la Luna
	var sin_delta_m = sin(beta_m) * cos(epsilon) + cos(beta_m) * sin(epsilon) * sin(lambda_m)
	var delta_m = asin(clamp(sin_delta_m, -1.0, 1.0))
	
	var y = sin(lambda_m) * cos(epsilon) - tan(beta_m) * sin(epsilon)
	var x = cos(lambda_m)
	var alpha_m = atan2(y, x)
	
	# Tiempo sidéreo local
	var gmst_deg = fmod(280.46061837 + 360.98564736629 * d, 360.0)
	var lmst_rad = fmod(gmst_deg + ORIGIN_LON_DEG, 360.0) * DEG_TO_RAD
	if lmst_rad < 0.0:
		lmst_rad += TAU
		
	var H_m = lmst_rad - alpha_m
	var lat_rad = ORIGIN_LAT_DEG * DEG_TO_RAD
	
	# Elevación de la Luna
	var sin_alt_m = sin(lat_rad) * sin(delta_m) + cos(lat_rad) * cos(delta_m) * cos(H_m)
	var altitude_m = asin(clamp(sin_alt_m, -1.0, 1.0))
	
	# Azimut de la Luna
	var cos_az_m = (sin(delta_m) - sin(lat_rad) * sin(altitude_m)) / (cos(lat_rad) * cos(altitude_m) + 1e-7)
	cos_az_m = clamp(cos_az_m, -1.0, 1.0)
	var azimuth_m = acos(cos_az_m)
	if sin(H_m) > 0.0:
		azimuth_m = TAU - azimuth_m
		
	state.moon_altitude_rad = altitude_m
	state.moon_azimuth_rad = azimuth_m

## Cálculo analítico de la fase lunar basado en la diferencia de longitud eclíptica Luna - Sol
static func _calculate_moon_phase(state: CelestialState) -> void:
	# El ciclo de fases lunares (sinódico) depende de la diferencia de longitud eclíptica
	var diff_lon = fposmod(state.moon_ecliptic_lon_rad - state.sun_ecliptic_lon_rad, TAU)
	
	# Fracción del ciclo lunar [0.0 - 1.0]: 0.0 = Nueva, 0.25 = Cuarto Creciente, 0.5 = Llena, 0.75 = Cuarto Menguante
	state.moon_phase = diff_lon / TAU
	
	# Fracción iluminada geométrica visible: (1 - cos(diff_lon)) / 2
	state.moon_illuminated_fraction = (1.0 - cos(diff_lon)) * 0.5
	
	# Es creciente (waxing) durante la primera mitad del ciclo (0 a PI)
	var is_waxing = diff_lon < PI
	var deg = rad_to_deg(diff_lon)
	
	if deg < 12.0 or deg > 348.0:
		state.moon_phase_name = "Luna Nueva"
	elif is_waxing:
		if deg < 75.0:
			state.moon_phase_name = "Creciente Cóncava"
		elif deg <= 105.0:
			state.moon_phase_name = "Cuarto Creciente"
		elif deg < 168.0:
			state.moon_phase_name = "Creciente Gibosa"
		else:
			state.moon_phase_name = "Luna Llena"
	else:
		if deg < 192.0:
			state.moon_phase_name = "Luna Llena"
		elif deg < 255.0:
			state.moon_phase_name = "Menguante Gibosa"
		elif deg <= 285.0:
			state.moon_phase_name = "Cuarto Menguante"
		else:
			state.moon_phase_name = "Menguante Cóncava"


## Proyección de coordenadas horizontales (altitud, azimut) al espacio canónico de Godot 4
## Norte = -Z, Sur = +Z, Este = +X, Oeste = -X, Cenit = +Y
static func _horizontal_to_godot(alt_rad: float, az_rad: float) -> Vector3:
	var cos_alt = cos(alt_rad)
	var x = cos_alt * sin(az_rad)
	var y = sin(alt_rad)
	var z = -cos_alt * cos(az_rad)
	return Vector3(x, y, z).normalized()
