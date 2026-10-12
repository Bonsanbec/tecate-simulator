extends SceneTree

const TKTCodecClass = preload("res://systems/network/tkt_codec.gd")
const MinigameCatalogClass = preload("res://systems/minigames/minigame_catalog.gd")
const MinigameLocationZoneClass = preload("res://systems/minigames/minigame_location_zone.gd")
const MinigameManagerClass = preload("res://systems/minigames/minigame_manager.gd")
const MinigameHUDClass = preload("res://systems/minigames/ui/minigame_hud.gd")
const WiiPartyMinigameMenuClass = preload("res://systems/minigames/ui/wii_party_minigame_menu.gd")
const UrbanSeatClass = preload("res://systems/environment/urban_seat.gd")

var total_tests: int = 0
var passed_tests: int = 0
var _frame: int = 0

func _init() -> void:
	print("================================================================================")
	print(" INICIANDO PRUEBAS UNITARIAS DEL MOTOR MODULAR DE MINIJUEGOS (CLIENTE GODOT 4)")
	print("================================================================================")

func _process(_delta: float) -> bool:
	_frame += 1
	if _frame == 2:
		_run_all_tests()
	return false

func _run_all_tests() -> void:
	test_codec_minigame_summon()
	test_codec_minigame_start()
	test_codec_minigame_action()
	test_codec_minigame_eliminate()
	test_codec_minigame_end()
	test_minigame_manager_lifecycle()
	test_minigame_hud_elements()
	test_minigame_catalog()
	test_minigame_location_zone()
	test_wii_party_minigame_menu()
	test_player_location_tooltips()

	print("================================================================================")
	print(" RESULTADOS: %d/%d pruebas superadas con éxito." % [passed_tests, total_tests])
	print("================================================================================")

	if passed_tests == total_tests:
		quit(0)
	else:
		quit(1)

func test_assert(desc: String, condition: bool) -> void:
	total_tests += 1
	if condition:
		passed_tests += 1
		print("  [PASS] %s" % desc)
	else:
		printerr("  [FAIL] %s" % desc)

func test_codec_minigame_summon() -> void:
	var bytes = TKTCodecClass.encode_minigame_summon_data(1, 0, 8, 1)
	test_assert("MINIGAME_SUMMON tiene longitud mínima de 10 bytes", bytes.size() >= 10)
	var decoded = TKTCodecClass.decode_minigame_summon_data(bytes)
	test_assert("Decodificado game_id == 1 (Mi Kiosko)", decoded.get("game_id") == 1)
	test_assert("Decodificado max_players == 8", decoded.get("max_players") == 8)
	test_assert("Decodificado arena_id == 1", decoded.get("arena_id") == 1)

func test_codec_minigame_start() -> void:
	var participants = [
		{"entity_id": 10, "spawn_x": -6.68, "spawn_y": 401.8, "spawn_z": 2.68, "spawn_yaw": 90.0},
		{"entity_id": 20, "spawn_x": -4.68, "spawn_y": 401.8, "spawn_z": 2.68, "spawn_yaw": 270.0}
	]
	var bytes = TKTCodecClass.encode_minigame_start_data(1, 3, participants)
	test_assert("MINIGAME_START bytes > 4", bytes.size() > 4)
	var dec = TKTCodecClass.decode_minigame_start_data(bytes)
	test_assert("Decodificado countdown == 3", dec.get("countdown_seconds") == 3)
	var dec_part = dec.get("participants", [])
	test_assert("Decodificado count == 2 participantes", dec_part.size() == 2)
	test_assert("Participante 1 entity_id == 10", dec_part[0].get("entity_id") == 10)
	test_assert("Participante 2 entity_id == 20", dec_part[1].get("entity_id") == 20)

func test_codec_minigame_action() -> void:
	var dir = Vector3(1.0, 4.2, 0.0)
	var bytes = TKTCodecClass.encode_minigame_action_data(1, 102, 7.5, dir)
	test_assert("MINIGAME_ACTION bytes == 21", bytes.size() == 21)
	var dec = TKTCodecClass.decode_minigame_action_data(bytes)
	test_assert("ActionType == 1 (Empujón Slapstick)", dec.get("action_type") == 1)
	test_assert("TargetEntityID == 102", dec.get("target_entity_id") == 102)
	test_assert("ParamFloat == 7.5", is_equal_approx(dec.get("param_float"), 7.5))
	test_assert("Dirección Y (Pop Vertical) == 4.2", is_equal_approx(dec.get("dir").y, 4.2))

func test_codec_minigame_eliminate() -> void:
	var bytes = TKTCodecClass.encode_minigame_eliminate_data(1, 102, 1)
	test_assert("MINIGAME_ELIMINATE bytes == 8", bytes.size() == 8)
	var dec = TKTCodecClass.decode_minigame_eliminate_data(bytes)
	test_assert("Eliminated entity_id == 102", dec.get("eliminated_entity_id") == 102)
	test_assert("Reason == 1 (Ring-Out)", dec.get("reason") == 1)

func test_codec_minigame_end() -> void:
	var rankings = [
		{"entity_id": 101, "score": 25, "coins_rewarded": 50},
		{"entity_id": 102, "score": 10, "coins_rewarded": 30}
	]
	var bytes = TKTCodecClass.encode_minigame_end_data(1, 101, rankings)
	test_assert("MINIGAME_END bytes == 27", bytes.size() == 27)
	var dec = TKTCodecClass.decode_minigame_end_data(bytes)
	test_assert("Winner ID == 101", dec.get("winner_entity_id") == 101)
	var dec_ranks = dec.get("rankings", [])
	test_assert("Rankings size == 2", dec_ranks.size() == 2)
	test_assert("1er lugar recompensado con 50 pesos", dec_ranks[0].get("coins_rewarded") == 50)
	test_assert("2do lugar recompensado con 30 pesos", dec_ranks[1].get("coins_rewarded") == 30)

func test_minigame_manager_lifecycle() -> void:
	var mgr = MinigameManagerClass.new()
	root.add_child(mgr)

	var summon_flag = [false]
	mgr.summon_received.connect(func(_g, _h, _m, _max): summon_flag[0] = true)

	var summon_bytes = TKTCodecClass.encode_minigame_summon_data(1, 0, 8, 1)
	var ev_summon = {
		"event_code": TKTCodecClass.EventCode.MINIGAME_SUMMON,
		"entity_id": 101,
		"data": summon_bytes
	}
	mgr._on_network_event_received(ev_summon)
	test_assert("MinigameManager procesa MINIGAME_SUMMON y emite señal", summon_flag[0])
	test_assert("Estado del cliente pasa a INVITATION_PENDING", mgr.current_state == MinigameManagerClass.ClientMinigameState.INVITATION_PENDING)

	var start_flag = [false]
	mgr.minigame_started.connect(func(_g, _cd, _parts): start_flag[0] = true)
	var start_bytes = TKTCodecClass.encode_minigame_start_data(1, 3, [])
	var ev_start = {
		"event_code": TKTCodecClass.EventCode.MINIGAME_START,
		"entity_id": 0,
		"data": start_bytes
	}
	mgr._on_network_event_received(ev_start)
	test_assert("MinigameManager procesa MINIGAME_START y emite señal", start_flag[0])
	test_assert("Estado del cliente pasa a STAGING", mgr.current_state == MinigameManagerClass.ClientMinigameState.STAGING)

	# Simular avance de 3.1s para verificar transición automática STAGING -> ACTIVE
	mgr._process(3.1)
	test_assert("Estado del cliente pasa a ACTIVE tras cuenta regresiva", mgr.current_state == MinigameManagerClass.ClientMinigameState.ACTIVE)

	mgr.queue_free()

func test_minigame_hud_elements() -> void:
	var mgr = MinigameManagerClass.new()
	var hud = MinigameHUDClass.new()
	root.add_child(mgr)
	root.add_child(hud)
	hud.minigame_manager = mgr
	hud._build_ui()
	hud._connect_signals()

	test_assert("MinigameHUD inicializado con RootControl", hud.root_control != null)
	test_assert("Panel de invitación existe", hud.invite_panel != null)
	test_assert("Contador de cuenta regresiva existe", hud.countdown_label != null)
	test_assert("Encabezado de juego existe", hud.header_panel != null)
	test_assert("Modal de podio existe", hud.podium_panel != null)

	# Simular inicio de minijuego para verificar activación de HUD
	mgr.minigame_started.emit(1, 3, [])
	test_assert("Encabezado de Mi Kiosko visible al iniciar", hud.header_panel.visible)
	test_assert("Título del encabezado es 'Mi Kiosko'", hud.header_title.text == "Mi Kiosko")
	test_assert("Cuenta regresiva activa", hud._is_counting_down)

	mgr.queue_free()
	hud.queue_free()

func test_minigame_catalog() -> void:
	print("\n--- Prueba 8: Catálogo Maestro de los 12 Minijuegos y 8 Ubicaciones ---")
	var all_games = MinigameCatalogClass.get_all_minigames()
	test_assert("Catálogo contiene exactamente 12 minijuegos", all_games.size() == 12)

	var all_locations = MinigameCatalogClass.get_all_locations()
	test_assert("Catálogo contiene las 8 ubicaciones emblemáticas", all_locations.size() == 8)

	var ffa_games = MinigameCatalogClass.get_minigames_by_category(MinigameCatalogClass.Category.ALL_VS_ALL)
	var one_vs_all_games = MinigameCatalogClass.get_minigames_by_category(MinigameCatalogClass.Category.ONE_VS_ALL)
	var duel_games = MinigameCatalogClass.get_minigames_by_category(MinigameCatalogClass.Category.DUEL_1V1)
	test_assert("Categoría Todos vs. Todos tiene 6 juegos", ffa_games.size() == 6)
	test_assert("Categoría 1 vs. Todos tiene 4 juegos", one_vs_all_games.size() == 4)
	test_assert("Categoría Duelo 1v1 tiene 2 juegos", duel_games.size() == 2)

	var kiosko_games = MinigameCatalogClass.get_minigames_by_location("kiosko")
	test_assert("Ubicación 'kiosko' agrupa 3 minijuegos (Mi Kiosko, Zumba, Espejito, Espejito)", kiosko_games.size() == 3)

	var tooltip_kiosko = MinigameCatalogClass.format_location_tooltip("kiosko")
	test_assert("Tooltip de Kiosko incluye Mi Kiosko, Zumba, [Q] y [M]", tooltip_kiosko.contains("Mi Kiosko") and tooltip_kiosko.contains("Zumba") and tooltip_kiosko.contains("[Q]") and tooltip_kiosko.contains("[M]"))

	var tooltip_curiel = MinigameCatalogClass.format_location_tooltip("foto_curiel")
	test_assert("Tooltip de Foto Curiel incluye Curiel y los Fotógrafos y [Q]", tooltip_curiel.contains("Curiel y los Fotógrafos") and tooltip_curiel.contains("[Q]"))

func test_minigame_location_zone() -> void:
	print("\n--- Prueba 9: Nodo 3D MinigameLocationZone y Detección Espacial ---")
	var zone = MinigameLocationZoneClass.new()
	zone.location_id = "kiosko"
	zone.radius = 7.5
	zone.position = Vector3(-6.6844, 400.2132, 2.6878)
	root.add_child(zone)

	test_assert("MinigameLocationZone pertenece al grupo 'minigame_zones'", zone.is_in_group("minigame_zones"))
	test_assert("MinigameLocationZone construye su marcador 3D (marker_root)", zone.marker_root != null)
	test_assert("Punto dentro del radio (distancia 2 m) es detectado", zone.is_point_inside(Vector3(-5.0, 400.5, 2.6878)))
	test_assert("Punto fuera del radio (distancia 25 m) es descartado", not zone.is_point_inside(Vector3(25.0, 400.5, 2.6878)))
	test_assert("get_tooltip_prompt() retorna texto contextual de Kiosko", zone.get_tooltip_prompt().contains("Mi Kiosko"))

	zone.queue_free()

func test_wii_party_minigame_menu() -> void:
	print("\n--- Prueba 10: Menú de Minijuegos Estilo Wii Party ---")
	var mgr = MinigameManagerClass.new()
	mgr.name = "MinigameManager"
	root.add_child(mgr)

	var menu = WiiPartyMinigameMenuClass.new()
	menu.name = "WiiPartyMinigameMenu"
	menu.minigame_manager = mgr
	root.add_child(menu)

	test_assert("Menú Wii Party inicia cerrado", not menu.is_open)
	test_assert("Grid de minijuegos crea las 12 tarjetas al iniciar", menu.game_tile_buttons.size() == 12)

	# Abrir menú general
	menu.open_menu()
	test_assert("open_menu() activa visibilidad e is_open", menu.is_open and menu.visible)
	test_assert("Juego seleccionado por defecto es #1 (MI KIOSKO)", menu.selected_game_id == 1 and menu.preview_title_label.text == "MI KIOSKO")

	# Seleccionar juego #6 (Curiel y los Fotógrafos)
	menu.select_minigame(6)
	test_assert("select_minigame(6) actualiza tarjeta de detalle a 'CURIEL Y LOS FOTÓGRAFOS'", menu.selected_game_id == 6 and menu.preview_title_label.text == "CURIEL Y LOS FOTÓGRAFOS")

	# Filtrar por ubicación 'kiosko'
	menu.open_menu("kiosko")
	test_assert("open_menu('kiosko') filtra a los 3 juegos del Kiosko", menu.game_tile_buttons.size() == 3)
	test_assert("Banner de filtro de ubicación es visible", menu.location_filter_banner.visible)

	# Limpiar filtro de ubicación y cambiar a categoría DUEL_1V1
	menu.current_location_filter = ""
	menu.select_category(MinigameCatalogClass.Category.DUEL_1V1)
	test_assert("Filtro DUEL_1V1 muestra 2 minijuegos (Ajedrez en el Parque, Justas)", menu.game_tile_buttons.size() == 2)

	# Probar lanzamiento de práctica local desde el botón Jugar con juego #1 (Mi Kiosko)
	menu.select_minigame(1)
	menu._on_play_pressed()
	test_assert("Presionar Jugar cierra el menú Wii Party e inicia sesión de práctica local", not menu.is_open and mgr.current_state == MinigameManagerClass.ClientMinigameState.STAGING)

	mgr.finish_local_practice(true)
	test_assert("finish_local_practice() finaliza la sesión y pasa a SUMMARY", mgr.current_state == MinigameManagerClass.ClientMinigameState.SUMMARY)

	menu.queue_free()
	mgr.queue_free()

func test_player_location_tooltips() -> void:
	print("\n--- Prueba 11: Tooltips Contextuales de Ubicación en PlayerController y Coexistencia con Asientos ---")
	var zone = MinigameLocationZoneClass.new()
	zone.location_id = "foto_curiel"
	zone.radius = 7.0
	zone.position = Vector3(-48.87, 400.93, -45.17)
	root.add_child(zone)

	var player = PlayerController.new()
	player.position = Vector3(-48.0, 400.93, -45.0)
	root.add_child(player)

	# Ejecutar escaneo de objetos y zonas interactivas
	player._scan_nearby_interactive_objects(0.20)
	test_assert("PlayerController detecta ubicación 'foto_curiel'", player._nearby_minigame_location_id == "foto_curiel")
	test_assert("HUD muestra tooltip de Curiel y los Fotógrafos con [Q] y [M]", player.hud._current_interaction_prompt.contains("Curiel y los Fotógrafos") and player.hud._current_interaction_prompt.contains("[Q]"))

	# Añadir una banca (UrbanSeat) a 1.0 m del jugador dentro de la misma zona
	var bench = UrbanSeatClass.new()
	bench.seat_name = "Banca Jardín"
	bench.position = Vector3(-47.5, 400.93, -45.0)
	root.add_child(bench)

	player._scan_nearby_interactive_objects(0.20)
	test_assert("Coexistencia: HUD conserva '[E] Sentarse en Banca Jardín' y añade el tooltip de minijuego con '[Q]'",
		player.hud._current_interaction_prompt.contains("[E] Sentarse en Banca Jardín") and player.hud._current_interaction_prompt.contains("[Q]"))

	bench.queue_free()
	player.queue_free()
	zone.queue_free()

