extends SceneTree

## Suite de Pruebas Automatizadas: Cinemática de Retroceso Slapstick (Estilo Minecraft)
## y Verificación de No-Regresión tras la Purga del Sistema de Salud
##
## Ejecución: /Applications/Godot_mono.app/Contents/MacOS/Godot --headless --path godot_project -s tests/test_slapstick_knockback.gd

const CitizenEntityClass = preload("res://systems/characters/citizen_entity.gd")
const PlayerControllerClass = preload("res://systems/player/player_controller.gd")
const VehicleBaseClass = preload("res://systems/vehicles/core/vehicle_base.gd")

var total_tests: int = 0
var passed_tests: int = 0

func _init() -> void:
	print("\n========================================================")
	print(" INICIANDO TEST: RETROCESO SLAPSTICK (ESTILO MINECRAFT)")
	print("========================================================")

	_test_purge_verification()
	_test_citizen_knockback_kinematics()
	_test_knockback_signal_and_flash()
	_test_player_slapstick_punch()
	_test_vehicle_health_free()

	print("\n========================================================")
	print(" RESUMEN: %d / %d pruebas superadas." % [passed_tests, total_tests])
	print("========================================================")

	if passed_tests == total_tests:
		print("✓ TODAS LAS PRUEBAS DE FÍSICAS SLAPSTICK PASARON CON ÉXITO.\n")
		quit(0)
	else:
		printerr("✗ ALGUNAS PRUEBAS FALLARON.")
		quit(1)

func assert_test(cond: bool, msg: String) -> void:
	total_tests += 1
	if cond:
		passed_tests += 1
		print("[PASS] %s" % msg)
	else:
		printerr("[FAIL] %s" % msg)

func _test_purge_verification() -> void:
	print("\n--- 1. Verificación de Purga de Componentes de Salud ---")
	var citizen = CitizenEntityClass.new()
	citizen.setup(101, true, "Peatón de Prueba")
	root.add_child(citizen)

	assert_test(not citizen.has_node("HealthComponent"), "CitizenEntity no posee nodo HealthComponent")
	assert_test(not citizen.has_node("HealthBar3D"), "CitizenEntity no posee nodo HealthBar3D")
	assert_test(not ("health_component" in citizen and citizen.health_component != null), "health_component es nulo o inexistente")

	citizen.queue_free()

func _test_citizen_knockback_kinematics() -> void:
	print("\n--- 2. Cinemática de Retroceso Horizontal y Salto Pop Vertical ---")
	var victim = CitizenEntityClass.new()
	victim.setup(102, true, "Víctima Kiosko")
	root.add_child(victim)
	victim.position = Vector3(0.0, 401.8, 0.0)

	var attacker_pos = Vector3(0.0, 401.8, 2.0) # Atacante ubicado en +Z
	victim.apply_impact_knockback(attacker_pos, 7.0, 4.2)

	# El vector de retroceso debe empujar hacia -Z (alejándose del atacante)
	assert_test(victim.velocity.z < -6.5, "Impulso horizontal aleja a la víctima en -Z (Velocidad: %.2f m/s)" % victim.velocity.z)
	assert_test(is_equal_approx(victim.velocity.y, 4.2), "Salto pop vertical (+Y) impulsa a la víctima hacia arriba (%.2f m/s)" % victim.velocity.y)

	victim.queue_free()

func _test_knockback_signal_and_flash() -> void:
	print("\n--- 3. Señal de Impacto y Temporizador de Destello Rojo ---")
	var citizen = CitizenEntityClass.new()
	citizen.setup(103, true, "Peatón Señales")
	root.add_child(citizen)

	var signal_received = [false]
	var received_force_h = [0.0]
	var received_force_v = [0.0]

	citizen.knockback_received.connect(func(_pos, fh, fv):
		signal_received[0] = true
		received_force_h[0] = fh
		received_force_v[0] = fv
	)

	citizen.apply_impact_knockback(Vector3(1.0, 0.0, 0.0), 6.5, 4.0)
	assert_test(signal_received[0], "Señal knockback_received emitida correctamente")
	assert_test(is_equal_approx(received_force_h[0], 6.5), "Fuerza horizontal reportada fielmente (6.5 m/s)")
	assert_test(is_equal_approx(received_force_v[0], 4.0), "Fuerza vertical de salto pop reportada fielmente (4.0 m/s)")
	assert_test(citizen._knockback_flash_timer > 0.0, "Temporizador de destello rojo activo (~0.15s)")

	citizen._process_attack_timers(0.20)
	assert_test(citizen._knockback_flash_timer == 0.0, "Temporizador de destello decae a cero tras expirar")

	citizen.queue_free()

func _test_player_slapstick_punch() -> void:
	print("\n--- 4. Interacción de Golpe Slapstick del Jugador ---")
	var player = PlayerControllerClass.new()
	player.setup(1, false, "Jugador Local")
	root.add_child(player)

	assert_test(not ("health_component" in player and player.health_component != null), "PlayerController no enlaza HealthComponent")
	assert_test(player.has_method("perform_melee_attack"), "PlayerController dispone de perform_melee_attack")

	# Simular ejecución de golpe
	var punch_ok = player.trigger_melee_attack()
	assert_test(punch_ok, "trigger_melee_attack() ejecuta sin requerir validación de is_dead")

	player.queue_free()

func _test_vehicle_health_free() -> void:
	print("\n--- 5. Vehículo Desacoplado de Barras de Salud ---")
	var car = VehicleBaseClass.new()
	car.vehicle_name = "Auto Sin HP"
	car.vehicle_type = VehicleBaseClass.VehicleType.CAR
	root.add_child(car)

	assert_test(not car.has_node("HealthComponent"), "VehicleBase no instancia HealthComponent")
	assert_test(not car.has_node("HealthBar3D"), "VehicleBase no instancia HealthBar3D overhead")

	car.queue_free()
