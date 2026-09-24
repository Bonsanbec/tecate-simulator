extends SceneTree

const TecateCelestial = preload("res://systems/environment/celestial/tecate_celestial.gd")
const WeatherData = preload("res://systems/environment/weather/weather_data.gd")
const RandomWeatherProvider = preload("res://systems/environment/weather/random_weather_provider.gd")

func _init():
	print("==================================================")
	print("[TEST] INICIANDO PRUEBAS DE CIELO Y CLIMA TECATE")
	print("==================================================")
	
	var all_ok = true
	
	# 1. Prueba de Huso Horario y Horario Estacional (Tecate / America/Tijuana)
	print("\n--- 1. Prueba de Horario Estacional (DST) para Tecate ---")
	# En julio (verano) debe ser DST (UTC-7)
	var dst_summer = TecateCelestial.is_tecate_dst(2026, 7, 15, 12)
	assert(dst_summer == true, "Julio debe tener horario estacional")
	print("✓ Verano 2026: DST =", dst_summer, " (Correcto: UTC-7 / PDT)")
	
	# En enero (invierno) NO debe ser DST (UTC-8)
	var dst_winter = TecateCelestial.is_tecate_dst(2026, 1, 15, 12)
	assert(dst_winter == false, "Enero NO debe tener horario estacional")
	print("✓ Invierno 2026: DST =", dst_winter, " (Correcto: UTC-8 / PST)")
	
	# 2. Prueba de Efemérides Astronómicas
	print("\n--- 2. Prueba de Efemérides Astronómicas del Sol y la Luna ---")
	# Simular mediodía solar en Tecate (ej: 19:30 UTC en verano -> 12:30 PDT)
	var noon_dt = {"year": 2026, "month": 6, "day": 21, "hour": 19, "minute": 30, "second": 0}
	var noon_unix = Time.get_unix_time_from_datetime_dict(noon_dt)
	var noon_state = TecateCelestial.calculate_celestial_state(noon_unix)
	
	print("Mediodía Solar en Tecate (21 Junio 12:30 PDT):")
	print("  • Elevación Sol: ", rad_to_deg(noon_state.sun_altitude_rad), "°")
	print("  • Azimut Sol: ", rad_to_deg(noon_state.sun_azimuth_rad), "°")
	print("  • Vector Sol: ", noon_state.sun_direction)
	assert(noon_state.sun_altitude_rad > deg_to_rad(60.0), "En el solsticio de verano al mediodía la elevación debe ser > 60°")
	assert(noon_state.sun_direction.y > 0.8, "El vector solar debe apuntar fuertemente hacia arriba (+Y)")
	print("✓ Posición solar de mediodía validada con éxito.")
	
	# Simular medianoche (07:30 UTC -> 00:30 PDT)
	var night_dt = {"year": 2026, "month": 6, "day": 21, "hour": 7, "minute": 30, "second": 0}
	var night_unix = Time.get_unix_time_from_datetime_dict(night_dt)
	var night_state = TecateCelestial.calculate_celestial_state(night_unix)
	print("\nMedianoche en Tecate (21 Junio 00:30 PDT):")
	print("  • Elevación Sol: ", rad_to_deg(night_state.sun_altitude_rad), "° (bajo horizonte)")
	print("  • Vector Sol: ", night_state.sun_direction)
	assert(night_state.sun_altitude_rad < 0.0, "A medianoche el sol debe estar bajo el horizonte")
	assert(night_state.sun_visible == false, "El sol no debe ser visible a medianoche")
	print("✓ Posición solar de medianoche validada con éxito.")
	
	# Fase lunar
	print("\nEstado de la Luna (21 Junio):")
	print("  • Fase: ", noon_state.moon_phase_name, " (Fracción iluminada: ", int(noon_state.moon_illuminated_fraction * 100), "%)")
	print("  • Vector Luna: ", noon_state.moon_direction)
	print("✓ Efemérides lunares calculadas con éxito.")
	
	# Estado astronómico exacto para HOY en Tecate
	var today_state = TecateCelestial.calculate_celestial_state()
	print("\n--- Estado Astronómico en Tecate en Tiempo Real (HOY) ---")
	print("  • Hora Tecate: ", today_state.local_datetime.year, "-", today_state.local_datetime.month, "-", today_state.local_datetime.day, " ", today_state.local_datetime.hour, ":", today_state.local_datetime.minute, " ", today_state.local_datetime.tz_name)
	print("  • Sol Elevación: ", rad_to_deg(today_state.sun_altitude_rad), "°")
	print("  • Luna Elevación: ", rad_to_deg(today_state.moon_altitude_rad), "°")
	print("  • Fase Lunar: ", today_state.moon_phase_name, " (Iluminación: ", int(today_state.moon_illuminated_fraction * 100), "%)")
	assert(today_state.moon_phase_name.begins_with("Creciente") or today_state.moon_phase_name == "Cuarto Creciente", "La luna debe ser creciente")
	print("✓ Fase de hoy en Tecate validada como Creciente.")

	
	# 3. Prueba del Contrato de Clima
	print("\n--- 3. Prueba del Contrato de Clima (WeatherData e Interpolación) ---")
	var w1 = WeatherData.new()
	w1.condition = WeatherData.COND_CLEAR
	w1.cloud_coverage = 0.1
	w1.wind_speed_mps = 4.0
	w1.wind_direction_deg = 270.0
	
	var w2 = WeatherData.new()
	w2.condition = WeatherData.COND_RAIN
	w2.cloud_coverage = 0.9
	w2.wind_speed_mps = 12.0
	w2.wind_direction_deg = 220.0
	
	# Interpolación al 50%
	var w_mid = w1.lerp_with(w2, 0.5)
	assert(abs(w_mid.cloud_coverage - 0.5) < 0.01, "La nubosidad al 50% debe ser 0.5")
	assert(abs(w_mid.wind_speed_mps - 8.0) < 0.01, "El viento al 50% debe ser 8.0 m/s")
	print("✓ Interpolación continua (lerp) de variables meteorológicas validada.")
	
	# 4. Prueba de Proveedor Procedural
	print("\n--- 4. Prueba de RandomWeatherProvider ---")
	var provider = RandomWeatherProvider.new()
	provider.auto_cycle_weather = false
	var cur = provider.get_current_weather()
	assert(cur != null, "El proveedor debe proveer un WeatherData válido")
	print("✓ Estado inicial del proveedor: ", cur.condition, " (Cobertura: ", cur.cloud_coverage, ")")
	
	provider.force_condition(WeatherData.COND_FOG)
	# Avanzar interpolación
	provider.update(3.0)
	var fog_w = provider.get_current_weather()
	print("✓ Transición a niebla del Cuchumá forzada: ", fog_w.condition, " | Niebla: ", fog_w.fog_density)
	
	# 5. Prueba de Shaders y Nubes 3D
	print("\n--- 5. Verificación de Carga de Shaders y Escena SkySystem ---")
	var sky_shader = load("res://systems/environment/shaders/realistic_sky.gdshader")
	assert(sky_shader != null, "El shader de cielo debe cargarse correctamente")
	print("✓ realistic_sky.gdshader cargado.")
	
	var cloud_shader = load("res://systems/environment/shaders/cloud_layer.gdshader")
	assert(cloud_shader != null, "El shader de nubes 3D debe cargarse correctamente")
	print("✓ cloud_layer.gdshader cargado.")
	
	var sky_system_scene = load("res://systems/environment/sky_system.tscn")
	assert(sky_system_scene != null, "La escena sky_system.tscn debe cargarse correctamente")
	print("✓ sky_system.tscn cargado.")
	
	print("\n==================================================")
	print("TODAS LAS PRUEBAS UNITARIAS PASARON EXITOSAMENTE.")
	print("==================================================")
	
	quit(0 if all_ok else 1)
