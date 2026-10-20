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
	_test_damage_flash_visual_material()
	_test_citizen_physics_movement_on_knockback()
	_test_player_knockback_recovery_and_pop()
	_test_volumetric_melee_hit()
	_test_kiosko_local_practice_rivals()
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
	assert_test(victim._knockback_active_timer > 0.0, "Temporizador de retroceso activo (_knockback_active_timer > 0)")
	assert_test(victim.floor_snap_length == 0.0, "floor_snap_length se libera a 0.0 para permitir despegue")

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

func _test_damage_flash_visual_material() -> void:
	print("\n--- 5. Material de Destello Rojo Visible (Mesh Override) ---")
	var citizen = CitizenEntityClass.new()
	citizen.setup(104, true, "Peatón Destello")
	root.add_child(citizen)

	citizen.apply_impact_knockback(Vector3(0, 0, 1), 5.0, 3.0)
	var flash_ok = (citizen.mesh_body != null and citizen.mesh_body.material_override != null)
	assert_test(flash_ok, "mesh_body recibe material_override rojo durante destello de daño")

	citizen._restore_mesh_colors()
	var restored_ok = (citizen.mesh_body != null and citizen.mesh_body.material_override == null)
	assert_test(restored_ok, "material_override es restaurado fielmente tras expirar destello")

	citizen.queue_free()

func _test_citizen_physics_movement_on_knockback() -> void:
	print("\n--- 6. Traslación Física Real de Víctima por move_and_slide ---")
	var victim = CitizenEntityClass.new()
	victim.setup(105, true, "Víctima Física")
	root.add_child(victim)
	victim.position = Vector3(0.0, 10.0, 0.0) # En el aire

	var initial_z = victim.position.z
	victim.apply_impact_knockback(Vector3(0.0, 10.0, 1.0), 8.0, 4.0)

	# Simular un paso de física
	victim._physics_process(0.05)
	assert_test(victim.position.z < initial_z, "La posición Z de la víctima se desplazó físicamente (Z: %.3f -> %.3f)" % [initial_z, victim.position.z])

	victim.queue_free()

func _test_player_knockback_recovery_and_pop() -> void:
	print("\n--- 7. Retroceso y Preservación de Impulso en PlayerController ---")
	var player = PlayerControllerClass.new()
	player.setup(1, false, "Jugador Impactado")
	root.add_child(player)
	player.position = Vector3(0.0, 5.0, 0.0)

	player.apply_impact_knockback(Vector3(0.0, 5.0, 2.0), 7.0, 4.2)
	assert_test(player.floor_snap_length == 0.0, "PlayerController floor_snap_length es 0.0 tras impacto")
	assert_test(player._knockback_recovery_timer > 0.0, "PlayerController _knockback_recovery_timer activo (~0.40s)")
	assert_test(player.velocity.y > 4.0, "Velocidad vertical pop (+Y) preservada en PlayerController")

	# Procesar un paso de marcha durante knockback
	player._process_walking(0.02)
	assert_test(player.velocity.z < -5.0, "Inercia horizontal de retroceso no es borrada instantáneamente por WASD")

	player.queue_free()

func _test_volumetric_melee_hit() -> void:
	print("\n--- 8. Impacto Volumétrico (SphereCast Frontal sin Rayo Cero) ---")
	var player = PlayerControllerClass.new()
	player.setup(1, false, "Atacante")
	root.add_child(player)
	player.position = Vector3(0.0, 0.0, 0.0)

	# Ubicar víctima ligeramente desplazada del centro (donde un rayo delgado de grosor 0 fallaría)
	var dummy = CitizenEntityClass.new()
	dummy.setup(106, true, "Dummy Desplazado")
	root.add_child(dummy)
	dummy.position = Vector3(0.35, 0.0, -1.8) # 1.8m adelante, 0.35m a la derecha

	var hit_detected = [false]
	dummy.knockback_received.connect(func(_pos, _fh, _fv):
		hit_detected[0] = true
	)

	player.perform_melee_attack()
	assert_test(hit_detected[0], "SphereCast volumétrico conecta exitosamente con objetivo desplazado lateralmente")

	dummy.queue_free()
	player.queue_free()

func _test_kiosko_local_practice_rivals() -> void:
	print("\n--- 9. Rivales de Práctica y Ring-Out en Mi Kiosko ---")
	var minigame_mgr_script = load("res://systems/minigames/minigame_manager.gd")
	var mgr = minigame_mgr_script.new()
	root.add_child(mgr)

	var player = PlayerControllerClass.new()
	player.setup(1, false, "Jugador Kiosko")
	root.add_child(player)
	mgr.player = player

	# Iniciar juego local de Kiosko (ID=1)
	mgr.start_local_game(1)
	player.position = Vector3(-6.6844, 401.80, 2.6878)
	assert_test(mgr._local_practice_rivals.size() == 2, "Mi Kiosko genera 2 contrincantes de práctica en tarima")

	var rival1 = mgr._local_practice_rivals[0]
	assert_test(is_instance_valid(rival1), "Rival 1 instanciado e insertado en la escena")

	# Simular caída de rival 1 (Ring-Out)
	rival1.position.y = 400.0
	mgr._process_local_game(0.05)
	assert_test(mgr._local_practice_rivals.size() == 1, "Rival expulsado de tarima es eliminado y removido de la partida")

	mgr.finish_local_game(true)
	assert_test(mgr._local_practice_rivals.is_empty(), "Contrincantes de práctica limpiados tras concluir partida")

	player.queue_free()
	mgr.queue_free()

func _test_vehicle_health_free() -> void:
	print("\n--- 10. Vehículo Desacoplado de Barras de Salud ---")
	var car = VehicleBaseClass.new()
	car.vehicle_name = "Auto Sin HP"
	car.vehicle_type = VehicleBaseClass.VehicleType.CAR
	root.add_child(car)

	assert_test(not car.has_node("HealthComponent"), "VehicleBase no instancia HealthComponent")
	assert_test(not car.has_node("HealthBar3D"), "VehicleBase no instancia HealthBar3D overhead")

	car.queue_free()
