extends SceneTree

## Suite de Verificación Automatizada del Sistema Modular de Minijuegos y Economía
## Ejecución: /Applications/Godot_mono.app/Contents/MacOS/Godot --headless --path godot_project -s tests/test_minigame_system.gd

const PASS_COLOR = "\u001b[32m"
const FAIL_COLOR = "\u001b[31m"
const INFO_COLOR = "\u001b[36m"
const RESET_COLOR = "\u001b[0m"

const MinigameBaseClass = preload("res://systems/minigames/core/minigame_base.gd")
const MinigameManagerClass = preload("res://systems/minigames/core/minigame_manager.gd")
const ProfileEconomyClass = preload("res://systems/minigames/economy/profile_economy.gd")
const MinigameMiKioskoClass = preload("res://systems/minigames/games/mi_kiosko/minigame_mi_kiosko.gd")
const MinigameLasTraesClass = preload("res://systems/minigames/games/las_traes/minigame_las_traes.gd")
const MinigameQuemadosClass = preload("res://systems/minigames/games/quemados/minigame_quemados.gd")

var tests_passed: int = 0
var tests_failed: int = 0

func _init() -> void:
	print(INFO_COLOR + "\n========================================================" + RESET_COLOR)
	print(INFO_COLOR + " INICIANDO PRUEBAS DEL SISTEMA DE MINIJUEGOS Y ECONOMÍA" + RESET_COLOR)
	print(INFO_COLOR + "========================================================\n" + RESET_COLOR)

	_run_tests()

func _run_tests() -> void:
	test_profile_economy()
	test_minigame_manager_registration()
	test_minigame_lifecycle_and_restoration()
	test_minigame_mi_kiosko_mechanics()
	test_minigame_las_traes_mechanics()
	test_minigame_quemados_mechanics()

	_print_summary()
	quit(0 if tests_failed == 0 else 1)

func assert_true(condition: bool, test_name: String) -> void:
	if condition:
		tests_passed += 1
		print("%s[PASS]%s %s" % [PASS_COLOR, RESET_COLOR, test_name])
	else:
		tests_failed += 1
		print("%s[FAIL]%s %s" % [FAIL_COLOR, RESET_COLOR, test_name])

func _print_summary() -> void:
	print(INFO_COLOR + "\n========================================================" + RESET_COLOR)
	print(INFO_COLOR + " RESUMEN DE PRUEBAS DEL SISTEMA DE MINIJUEGOS" + RESET_COLOR)
	print(INFO_COLOR + "========================================================" + RESET_COLOR)
	print("  Pruebas superadas:  %d" % tests_passed)
	print("  Pruebas fallidas:   %d" % tests_failed)
	print(INFO_COLOR + "========================================================\n" + RESET_COLOR)

func test_profile_economy() -> void:
	print(INFO_COLOR + "--- Prueba 1: Economía Persistente y Guardado de Pesos ---" + RESET_COLOR)
	var eco = ProfileEconomyClass.new()
	var initial_balance = eco.balance_pesos
	assert_true(initial_balance >= 0, "El balance de Pesos Tecatenses es un valor válido.")

	eco.add_pesos(50)
	assert_true(eco.balance_pesos == initial_balance + 50, "Añadir Pesos Tecatenses incrementa el saldo correctamente.")

	var can_spend = eco.spend_pesos(30)
	assert_true(can_spend and eco.balance_pesos == initial_balance + 20, "Gastar Pesos descuenta adecuadamente si hay saldo suficiente.")

	var overspend = eco.spend_pesos(999999)
	assert_true(not overspend, "Gastar más del saldo disponible es rechazado.")

	assert_true(eco.has_cosmetic("elote_con_chile"), "Elote con chile está desbloqueado por defecto.")

	var unlocked = eco.unlock_cosmetic("sombrero_norteno", 10)
	assert_true(unlocked and eco.has_cosmetic("sombrero_norteno"), "Desbloquear cosmético nuevo deduce costo y lo añade a la colección.")

func test_minigame_manager_registration() -> void:
	print(INFO_COLOR + "--- Prueba 2: Catálogo de Minijuegos en MinigameManager ---" + RESET_COLOR)
	var mgr = MinigameManagerClass.new()
	mgr._ready()

	assert_true(mgr.registered_minigames.has("mi_kiosko"), "Minijuego 'Mi Kiosko' registrado en el catálogo.")
	assert_true(mgr.registered_minigames.has("las_traes"), "Minijuego 'Las Traes' registrado en el catálogo.")
	assert_true(mgr.registered_minigames.has("quemados"), "Minijuego 'Quemados' registrado en el catálogo.")
	assert_true(not mgr.is_minigame_active(), "El gestor inicia sin minijuegos activos en curso.")

	mgr.queue_free()

func test_minigame_lifecycle_and_restoration() -> void:
	print(INFO_COLOR + "--- Prueba 3: Ciclo de Vida y Restauración Espacial Exacta ---" + RESET_COLOR)
	var p1 = Node3D.new()
	p1.name = "Jugador1"
	p1.position = Vector3(10.0, 400.0, -15.0)

	var p2 = Node3D.new()
	p2.name = "Jugador2"
	p2.position = Vector3(-20.0, 402.0, 30.0)

	var game = MinigameBaseClass.new()
	var ok = game.setup([p1, p2])
	assert_true(ok, "MinigameBase::setup configuró a los 2 participantes.")
	assert_true(game.participants.size() == 2, "Registro de participantes contiene 2 entradas.")

	# Modificar posiciones durante la partida simulada
	p1.position = Vector3(0.0, 405.0, 0.0)
	p2.position = Vector3(5.0, 405.0, 5.0)

	game.cleanup_and_restore()

	assert_true(p1.position.distance_to(Vector3(10.0, 400.0, -15.0)) < 0.001, "Jugador 1 restaurado a su posición previa exacta.")
	assert_true(p2.position.distance_to(Vector3(-20.0, 402.0, 30.0)) < 0.001, "Jugador 2 restaurado a su posición previa exacta.")
	assert_true(game.participants.is_empty(), "Limpieza de participantes concluida.")

	p1.free()
	p2.free()
	game.free()

func test_minigame_mi_kiosko_mechanics() -> void:
	print(INFO_COLOR + "--- Prueba 4: Mecánicas de 'Mi Kiosko' (Empujones y Caídas) ---" + RESET_COLOR)
	var p1 = CharacterBody3D.new()
	p1.name = "Axel"
	var p2 = CharacterBody3D.new()
	p2.name = "Eli"

	var kiosko_game = MinigameMiKioskoClass.new()
	kiosko_game.setup([p1, p2])
	kiosko_game.start_game()

	assert_true(kiosko_game.get_alive_count() == 2, "Ambos jugadores inician vivos en el Kiosko.")

	# Test push
	var push_ok = kiosko_game.execute_push("Axel", "Eli", Vector3(1, 0, 0))
	assert_true(push_ok, "Empujón ejecutado exitosamente.")
	assert_true(p2.velocity.length() > 0.0, "El jugador receptor adquirió impulso físico.")

	# Test parry / bloqueo
	kiosko_game.set_player_blocking("Eli", true)
	var blocked = kiosko_game.execute_push("Axel", "Eli", Vector3(1, 0, 0))
	assert_true(not blocked, "El empujón fue repelido por el bloqueo defensivo.")

	# Test eliminación por caída al pasto (altura inferior al kiosko)
	p2.position.y = 400.0 # Por debajo de fall_altitude_threshold (401.1)
	kiosko_game._on_tick(0.016)
	assert_true(not kiosko_game.participants["Eli"]["is_alive"], "Eli eliminada por caer de la plataforma del Kiosko.")
	assert_true(kiosko_game.get_alive_count() == 1, "Queda exactamente 1 jugador con vida.")
	assert_true(kiosko_game._check_win_condition(), "Condición de victoria cumplida (Axel campeón del Kiosko).")

	p1.free()
	p2.free()
	kiosko_game.cleanup_and_restore()
	kiosko_game.free()

func test_minigame_las_traes_mechanics() -> void:
	print(INFO_COLOR + "--- Prueba 5: Mecánicas de 'Las Traes' (Tag e Inmunidad) ---" + RESET_COLOR)
	var p1 = CharacterBody3D.new()
	p1.name = "Axel"
	p1.position = Vector3(0, 400.3, 0)

	var p2 = CharacterBody3D.new()
	p2.name = "Eli"
	p2.position = Vector3(10, 400.3, 0)

	var traes_game = MinigameLasTraesClass.new()
	traes_game.setup([p1, p2])
	traes_game.start_game()

	assert_true(not traes_game.current_tagger_id.is_empty(), "Se designó un portador inicial del tag.")
	var first_tagger = traes_game.current_tagger_id
	var other_player = "Eli" if first_tagger == "Axel" else "Axel"

	# Transferencia directa
	traes_game.transfer_tag(other_player)
	assert_true(traes_game.current_tagger_id == other_player, "El tag se transfirió correctamente al otro jugador.")
	assert_true(traes_game._immunity_timer > 0.0, "Se activó el temporizador de inmunidad para evitar retornos instantáneos.")

	p1.free()
	p2.free()
	traes_game.cleanup_and_restore()
	traes_game.free()

func test_minigame_quemados_mechanics() -> void:
	print(INFO_COLOR + "--- Prueba 6: Mecánicas de 'Quemados' (Balística y Eliminación) ---" + RESET_COLOR)
	var p1 = CharacterBody3D.new()
	p1.name = "Axel"
	p1.position = Vector3(0, 400.3, 0)

	var p2 = CharacterBody3D.new()
	p2.name = "Eli"
	p2.position = Vector3(5, 400.3, 0)

	var quemados = MinigameQuemadosClass.new()
	quemados.setup([p1, p2])
	quemados.start_game()

	var thrown = quemados.throw_ball("Axel", Vector3(0, 401.2, 0), Vector3(1, 0, 0))
	assert_true(thrown, "Pelota lanzada exitosamente por Axel.")
	assert_true(quemados.active_balls.size() == 1, "Hay 1 pelota activa simulándose en la arena.")

	# Simular impacto directo en Eli
	quemados.active_balls[0]["pos"] = Vector3(5.0, 401.2, 0.0) # Posición de Eli (torso)
	quemados._on_tick(0.016)

	assert_true(not quemados.participants["Eli"]["is_alive"], "Eli eliminada por impacto de pelota (¡Quemada!).")
	assert_true(quemados.get_alive_count() == 1, "Queda 1 jugador con vida en Quemados.")
	assert_true(quemados._check_win_condition(), "Condición de victoria alcanzada en Quemados.")

	p1.free()
	p2.free()
	quemados.cleanup_and_restore()
	quemados.free()
