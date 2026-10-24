class_name TestHardcodedStrings
extends SceneTree

## Suite de Pruebas: Verificación de Cadenas de Texto y Política Zero Hardcoded Strings
##
## Valida la integridad estructural, valores canónicos, funciones tipadas de formateo
## y delegación de constantes en AppStrings, AppTechnicalStrings y AppConstants.
##
## Referencia normativa: docs/strings.md

var _tests_passed: int = 0
var _tests_total: int = 0
var _frame: int = 0

func _init() -> void:
	print("\n========================================================")
	print(" INICIANDO PRUEBAS: POLÍTICA Y PIPELINE DE STRINGS")
	print("========================================================")

func _process(_delta: float) -> bool:
	_frame += 1
	if _frame == 2:
		_run_all_tests()
	return false

func _run_all_tests() -> void:
	test_app_strings_integrity()
	test_app_strings_formatters()
	test_app_technical_strings_integrity()
	test_app_constants_facade()
	test_ui_modules_integration()
	test_strict_normative_prohibitions()

	print("\n========================================================")
	print(" RESUMEN DE PRUEBAS DE CADENAS DE TEXTO")
	print("========================================================")
	print("  Pruebas superadas:  %d / %d" % [_tests_passed, _tests_total])
	print("========================================================\n")

	if _tests_passed == _tests_total:
		print("[PASS] TODAS LAS PRUEBAS DE LA POLÍTICA DE STRINGS PASARON CON ÉXITO.")
		quit(0)
	else:
		printerr("[FAIL] ALGUNAS PRUEBAS DE STRINGS FALLARON.")
		quit(1)

func assert_true(cond: bool, msg: String) -> void:
	_tests_total += 1
	if cond:
		_tests_passed += 1
		print("[PASS] %s" % msg)
	else:
		printerr("[FAIL] %s" % msg)

# -----------------------------------------------------------------------------
# 1. Validación de Integridad de AppStrings
# -----------------------------------------------------------------------------
func test_app_strings_integrity() -> void:
	print("\n--- 1. Validación de Integridad de AppStrings ---")

	# Marca y Sistema
	assert_true(not AppStrings.APP_NAME.is_empty(), "AppStrings.APP_NAME está definido")
	assert_true(AppStrings.APP_NAME == "Tecate: Pueblo Mágico y Social", "AppStrings.APP_NAME tiene el valor oficial")
	assert_true(AppStrings.APP_TITLE_TECATE == "Tecate", "AppStrings.APP_TITLE_TECATE es 'Tecate'")
	assert_true(AppStrings.APP_SUBTITLE == "Pueblo Mágico y Social", "AppStrings.APP_SUBTITLE es 'Pueblo Mágico y Social'")

	# Navegación y Botones (Sin punto final según Sec 2.1)
	assert_true(AppStrings.BTN_CONTINUE == "Continuar", "AppStrings.BTN_CONTINUE es 'Continuar'")
	assert_true(AppStrings.BTN_MINIGAMES == "Minijuegos", "AppStrings.BTN_MINIGAMES es 'Minijuegos'")
	assert_true(AppStrings.BTN_RESPAWN == "Reaparecer", "AppStrings.BTN_RESPAWN es 'Reaparecer'")
	assert_true(AppStrings.BTN_QUIT == "Salir", "AppStrings.BTN_QUIT es 'Salir'")
	assert_true(AppStrings.BTN_CONFIRM_SELECTION == "Confirmar selección", "AppStrings.BTN_CONFIRM_SELECTION usa capitalización de oración")
	assert_true(!AppStrings.BTN_CONTINUE.ends_with("."), "Botón no termina con punto")
	assert_true(!AppStrings.BTN_QUIT.ends_with("."), "Botón salir no termina con punto")

	# Identidades de Personajes
	assert_true(AppStrings.CHAR_AXEL_DISPLAY_NAME == "Camarada", "Axel display name es 'Camarada'")
	assert_true(AppStrings.CHAR_ELI_DISPLAY_NAME == "Diseñador", "Eli display name es 'Diseñador'")
	assert_true(AppStrings.CHAR_ASTORGA_DISPLAY_NAME == "Músico", "Astorga display name es 'Músico'")

	# Rumbos Cardinales en Español Estándar (SO, O, NO en lugar de SW, W, NW)
	assert_true(AppStrings.CARDINAL_N == "N", "Rumbo Norte es 'N'")
	assert_true(AppStrings.CARDINAL_E == "E", "Rumbo Este es 'E'")
	assert_true(AppStrings.CARDINAL_S == "S", "Rumbo Sur es 'S'")
	assert_true(AppStrings.CARDINAL_SO == "SO", "Rumbo Suroeste es 'SO' (sin anglicismo SW)")
	assert_true(AppStrings.CARDINAL_O == "O", "Rumbo Oeste es 'O' (sin anglicismo W)")
	assert_true(AppStrings.CARDINAL_NO == "NO", "Rumbo Noroeste es 'NO' (sin anglicismo NW)")

# -----------------------------------------------------------------------------
# 2. Validación de Métodos de Formateo de AppStrings
# -----------------------------------------------------------------------------
func test_app_strings_formatters() -> void:
	print("\n--- 2. Validación de Métodos de Formateo de AppStrings ---")

	# Formateo monetario en minúsculas normativas
	assert_true(AppStrings.format_currency_pesos(50) == "50 pesos", "format_currency_pesos formatea '50 pesos' en minúsculas")
	assert_true(AppStrings.format_currency_pesos(1000) == "1000 pesos", "format_currency_pesos formatea cantidades mayores en minúsculas")

	# Formateo de velocidad y altitud
	assert_true(AppStrings.format_speed(25.5).ends_with("km/h"), "format_speed incluye unidad km/h")
	assert_true(AppStrings.format_altitude(400.3).ends_with("m snm"), "format_altitude incluye unidad m snm")

	# Formateo de pendiente topográfica
	var pos_slope = AppStrings.format_slope(4.5)
	assert_true(pos_slope.begins_with("+"), "format_slope positivo antepone '+'")
	var neg_slope = AppStrings.format_slope(-2.3)
	assert_true(neg_slope.begins_with("-"), "format_slope negativo antepone '-'")

	# Conversión de ángulos a rumbos cardinales
	assert_true(AppStrings.get_cardinal_direction(0.0) == "N", "0° corresponde a 'N'")
	assert_true(AppStrings.get_cardinal_direction(90.0) == "E", "90° corresponde a 'E'")
	assert_true(AppStrings.get_cardinal_direction(180.0) == "S", "180° corresponde a 'S'")
	assert_true(AppStrings.get_cardinal_direction(225.0) == "SO", "225° corresponde a 'SO'")
	assert_true(AppStrings.get_cardinal_direction(270.0) == "O", "270° corresponde a 'O'")
	assert_true(AppStrings.get_cardinal_direction(315.0) == "NO", "315° corresponde a 'NO'")

	# Prompts de interacción parametrizados (sin corchetes ni paréntesis)
	assert_true(AppStrings.prompt_sit_in("Banca Hidalgo") == "Sentarse en Banca Hidalgo", "prompt_sit_in formatea sin corchetes")
	assert_true(AppStrings.prompt_drive_vehicle("Autobús") == "Conducir Autobús", "prompt_drive_vehicle formatea sin corchetes")
	assert_true(AppStrings.prompt_vehicle_full("Coche") == "Coche lleno", "prompt_vehicle_full formatea sin paréntesis")

# -----------------------------------------------------------------------------
# 3. Validación de Integridad de AppTechnicalStrings
# -----------------------------------------------------------------------------
func test_app_technical_strings_integrity() -> void:
	print("\n--- 3. Validación de Integridad de AppTechnicalStrings ---")

	# Verificación de existencia real de escenas en disco
	assert_true(FileAccess.file_exists(AppTechnicalStrings.SCENE_MAIN), "SCENE_MAIN existe físicamente en el proyecto")
	assert_true(FileAccess.file_exists(AppTechnicalStrings.SCENE_START_SCREEN), "SCENE_START_SCREEN existe físicamente en el proyecto")
	assert_true(FileAccess.file_exists(AppTechnicalStrings.SCENE_PLAYER_HUD), "SCENE_PLAYER_HUD existe físicamente en el proyecto")
	assert_true(FileAccess.file_exists(AppTechnicalStrings.FONT_DIN_CONDENSED_BOLD), "FONT_DIN_CONDENSED_BOLD existe físicamente en el proyecto")

	# Constantes de Entrada
	assert_true(AppTechnicalStrings.ACTION_INTERACT == "interact", "ACTION_INTERACT es 'interact'")
	assert_true(AppTechnicalStrings.ACTION_CAMERA_TOGGLE == "camera_toggle", "ACTION_CAMERA_TOGGLE es 'camera_toggle'")

	# Grupos de Godot
	assert_true(AppTechnicalStrings.GROUP_PLAYERS == "players", "GROUP_PLAYERS es 'players'")
	assert_true(AppTechnicalStrings.GROUP_SEATS == "seats", "GROUP_SEATS es 'seats'")
	assert_true(AppTechnicalStrings.GROUP_VEHICLES == "vehicles", "GROUP_VEHICLES es 'vehicles'")
	assert_true(AppTechnicalStrings.GROUP_PUMP_ZONES == "pump_zones", "GROUP_PUMP_ZONES es 'pump_zones'")

	# Identificadores de Personajes
	assert_true(AppTechnicalStrings.CHAR_ID_AXEL == "axel", "CHAR_ID_AXEL es 'axel'")
	assert_true(AppTechnicalStrings.CHAR_ID_ELI == "eli", "CHAR_ID_ELI es 'eli'")
	assert_true(AppTechnicalStrings.CHAR_ID_ASTORGA == "astorga", "CHAR_ID_ASTORGA es 'astorga'")

# -----------------------------------------------------------------------------
# 4. Validación de Fachada Canónica AppConstants
# -----------------------------------------------------------------------------
func test_app_constants_facade() -> void:
	print("\n--- 4. Validación de Fachada Canónica AppConstants ---")

	assert_true(AppConstants.APP_NAME == AppStrings.APP_NAME, "AppConstants delega APP_NAME correctamente")
	assert_true(AppConstants.APP_TITLE_TECATE == AppStrings.APP_TITLE_TECATE, "AppConstants delega APP_TITLE_TECATE")
	assert_true(AppConstants.ACTION_INTERACT == AppTechnicalStrings.ACTION_INTERACT, "AppConstants delega ACTION_INTERACT")
	assert_true(AppConstants.GROUP_SEATS == AppTechnicalStrings.GROUP_SEATS, "AppConstants delega GROUP_SEATS")
	assert_true(AppConstants.SCENE_MAIN == AppTechnicalStrings.SCENE_MAIN, "AppConstants delega SCENE_MAIN")

# -----------------------------------------------------------------------------
# 5. Validación de Consumo en Módulos de UI y Entorno
# -----------------------------------------------------------------------------
func test_ui_modules_integration() -> void:
	print("\n--- 5. Validación de Integración en Módulos de UI y Entorno ---")

	# Instanciar UrbanSeat y comprobar registro mediante constante técnica
	var seat = UrbanSeat.new()
	root.add_child(seat)
	assert_true(seat.is_in_group(AppTechnicalStrings.GROUP_SEATS), "UrbanSeat se registra en el grupo GROUP_SEATS")
	seat.queue_free()

	# Instanciar GasStationPumpZone y comprobar registro de grupo
	var pump = GasStationPumpZone.new()
	root.add_child(pump)
	assert_true(pump.is_in_group(AppTechnicalStrings.GROUP_PUMP_ZONES), "GasStationPumpZone se registra en GROUP_PUMP_ZONES")
	pump.queue_free()

	# Instanciar PlayerHUD y verificar inicialización con AppStrings
	var hud_scene = load(AppTechnicalStrings.SCENE_PLAYER_HUD)
	assert_true(hud_scene != null, "Escena de PlayerHUD cargada correctamente")
	var hud = hud_scene.instantiate() as PlayerHUD
	root.add_child(hud)
	assert_true(hud.wallet_label != null, "Wallet label de PlayerHUD instanciada")
	assert_true(hud.wallet_label.text == AppStrings.format_currency_pesos(50), "Wallet label inicializada con AppStrings.format_currency_pesos")
	hud.queue_free()

# -----------------------------------------------------------------------------
# 6. Validación Normativa Estricta (Zero Slashes, Zero Brackets, Zero Parens, Zero All-Caps)
# -----------------------------------------------------------------------------
func test_strict_normative_prohibitions() -> void:
	print("\n--- 6. Validación Normativa Estricta (Zero Slashes, Zero Brackets, Zero Parens, Zero All-Caps) ---")

	# Verificar constantes de HUD y Roles sin ALL CAPS
	assert_true(AppStrings.HUD_SPEED == "Velocidad", "HUD_SPEED es 'Velocidad' (no 'VELOCIDAD')")
	assert_true(AppStrings.HUD_ALTITUDE == "Altitud", "HUD_ALTITUDE es 'Altitud' (no 'ALTITUD')")
	assert_true(AppStrings.HUD_SLOPE == "Pendiente", "HUD_SLOPE es 'Pendiente' (no 'PENDIENTE')")
	assert_true(AppStrings.HUD_FUEL == "Combustible", "HUD_FUEL es 'Combustible' (no 'COMBUSTIBLE')")
	assert_true(AppStrings.VEHICLE_ROLE_DRIVER == "Conductor", "VEHICLE_ROLE_DRIVER es 'Conductor' (no 'CONDUCTOR')")
	assert_true(AppStrings.VEHICLE_ROLE_PASSENGER == "Pasajero", "VEHICLE_ROLE_PASSENGER es 'Pasajero' (no 'PASAJERO')")
	assert_true(AppStrings.MINIGAMES_BADGE_PARTY_MODE == "Modo fiesta", "MINIGAMES_BADGE_PARTY_MODE es 'Modo fiesta' (no 'MODO FIESTA')")

	# Prohibición de barras '/' en referencias geográficas (debe usar conjunción 'y')
	assert_true(!AppStrings.LANDMARK_RUMOROSA.contains("/"), "LANDMARK_RUMOROSA no contiene '/'")
	assert_true(!AppStrings.LANDMARK_CUCHUMA.contains("/"), "LANDMARK_CUCHUMA no contiene '/'")
	assert_true(!AppStrings.LANDMARK_ENSENADA.contains("/"), "LANDMARK_ENSENADA no contiene '/'")
	assert_true(AppStrings.LANDMARK_RUMOROSA == "Hacia La Rumorosa y Mexicali", "LANDMARK_RUMOROSA usa conjunción 'y'")
	assert_true(AppStrings.LANDMARK_CUCHUMA == "Hacia el Cerro Cuchumá y Tijuana", "LANDMARK_CUCHUMA usa conjunción 'y'")

	# Prohibición de corchetes en prompts
	assert_true(!AppStrings.PROMPT_SIT.contains("[") and !AppStrings.PROMPT_SIT.contains("]"), "PROMPT_SIT sin corchetes")
	assert_true(!AppStrings.PROMPT_STAND.contains("[") and !AppStrings.PROMPT_STAND.contains("]"), "PROMPT_STAND sin corchetes")
	assert_true(!AppStrings.PROMPT_DRIVE_VEHICLE.contains("[") and !AppStrings.PROMPT_DRIVE_VEHICLE.contains("]"), "PROMPT_DRIVE_VEHICLE sin corchetes")

	# Prohibición de símbolos de infinito y emojis
	assert_true(!AppStrings.VEHICLE_FUEL_INFINITE_ROUTE.contains("∞"), "VEHICLE_FUEL_INFINITE_ROUTE no contiene símbolo infinito '∞'")
	assert_true(AppStrings.VEHICLE_FUEL_INFINITE_ROUTE == "Ilimitado", "VEHICLE_FUEL_INFINITE_ROUTE es 'Ilimitado'")

	# Prohibición de paréntesis en telemetría vehicular
	var veh_telemetry = AppStrings.format_vehicle_telemetry("Autobús", "Conductor", 40.0, 80.0, false, "Asfalto", 2.0)
	assert_true(!veh_telemetry.contains("(") and !veh_telemetry.contains(")"), "format_vehicle_telemetry no contiene paréntesis")

	# Verificación de formateo de red
	assert_true(AppStrings.format_network_status_host("127.0.0.1", 4) == "En línea, servidor 127.0.0.1, 4 jugadores", "format_network_status_host formatea limpiamente")
	assert_true(AppStrings.format_network_status_ping(35, 2) == "En línea, 35 ms, 2 jugadores", "format_network_status_ping formatea limpiamente")
