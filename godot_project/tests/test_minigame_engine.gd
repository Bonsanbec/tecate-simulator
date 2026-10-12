extends SceneTree

const TKTCodecClass = preload("res://systems/network/tkt_codec.gd")
const MinigameManagerClass = preload("res://systems/minigames/minigame_manager.gd")
const MinigameHUDClass = preload("res://systems/minigames/ui/minigame_hud.gd")

var total_tests: int = 0
var passed_tests: int = 0

func _init() -> void:
	print("================================================================================")
	print(" INICIANDO PRUEBAS UNITARIAS DEL MOTOR MODULAR DE MINIJUEGOS (CLIENTE GODOT 4)")
	print("================================================================================")

	test_codec_minigame_summon()
	test_codec_minigame_start()
	test_codec_minigame_action()
	test_codec_minigame_eliminate()
	test_codec_minigame_end()
	test_minigame_manager_lifecycle()
	test_minigame_hud_elements()

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
