extends SceneTree

## Suite de Verificación Automatizada del Sistema Centralizado de Salud, Barras de Vida y Combate
## Ejecución: /Applications/Godot_mono.app/Contents/MacOS/Godot --headless --path godot_project -s tests/test_health_and_combat_system.gd

const PASS_COLOR = "\u001b[32m"
const FAIL_COLOR = "\u001b[31m"
const INFO_COLOR = "\u001b[36m"
const RESET_COLOR = "\u001b[0m"

const EntityHealthDefaultsClass = preload("res://systems/combat/entity_health_defaults.gd")
const HealthComponentClass = preload("res://systems/combat/health_component.gd")
const HealthBar3DClass = preload("res://ui/health_bar_3d.gd")
const CitizenEntityClass = preload("res://systems/characters/citizen_entity.gd")
const PlayerControllerClass = preload("res://systems/player/player_controller.gd")
const VehicleBaseClass = preload("res://systems/vehicles/core/vehicle_base.gd")
const DrivableVehicleClass = preload("res://systems/vehicles/controllers/drivable_vehicle_controller.gd")
const DestructibleProp3DClass = preload("res://systems/environment/destructible_prop_3d.gd")

var tests_passed = 0
var tests_failed = 0

func _init() -> void:
	print(INFO_COLOR + "\n========================================================" + RESET_COLOR)
	print(INFO_COLOR + " INICIANDO PRUEBAS DEL SISTEMA DE SALUD Y COMBATE" + RESET_COLOR)
	print(INFO_COLOR + "========================================================\n" + RESET_COLOR)

	_run_tests()

func _run_tests() -> void:
	test_entity_health_defaults()
	test_health_component_mechanics()
	test_citizen_health_integration()
	test_vehicle_health_defaults_and_destruction()
	test_destructible_prop_mechanics()
	test_player_combat_and_elimination()
	test_attack_arm_animation_and_kinematics()

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
	print(INFO_COLOR + " RESUMEN DE PRUEBAS DE SALUD Y COMBATE" + RESET_COLOR)
	print(INFO_COLOR + "========================================================" + RESET_COLOR)
	print("  Pruebas superadas:  %d" % tests_passed)
	print("  Pruebas fallidas:   %d" % tests_failed)
	print(INFO_COLOR + "========================================================\n" + RESET_COLOR)

func test_entity_health_defaults() -> void:
	print(INFO_COLOR + "--- Prueba 1: Estándares Centralizados de Salud (EntityHealthDefaults) ---" + RESET_COLOR)
	
	var player_hp = EntityHealthDefaultsClass.get_default_health_for_type("PLAYER")
	assert_true(player_hp == 100.0, "Jugadores y Peatones: 100 HP predeterminados")
	
	var bus_hp = EntityHealthDefaultsClass.get_default_health_for_type("BUS")
	assert_true(bus_hp == 5000.0, "Autobuses urbanos: 5000 HP predeterminados")

	var car_hp = EntityHealthDefaultsClass.get_default_health_for_type("CAR")
	assert_true(car_hp == 500.0, "Automóviles pequeños: 500 HP predeterminados")

	var truck_hp = EntityHealthDefaultsClass.get_default_health_for_type("TRUCK")
	assert_true(truck_hp == 3000.0, "Camiones de carga: 3000 HP predeterminados")

	var moto_hp = EntityHealthDefaultsClass.get_default_health_for_type("MOTORCYCLE")
	assert_true(moto_hp == 250.0, "Motocicletas: 250 HP predeterminados")

	var prop_hp = EntityHealthDefaultsClass.get_default_health_for_type("PROP_MEDIUM")
	assert_true(prop_hp == 150.0, "Mobiliario urbano / Nomenclatura: 150 HP predeterminados")

func test_health_component_mechanics() -> void:
	print(INFO_COLOR + "--- Prueba 2: Dinámica Interna del HealthComponent ---" + RESET_COLOR)

	var hc = HealthComponentClass.new()
	hc.initialize(100.0)

	assert_true(hc.current_health == 100.0, "Salud inicial asignada a 100 HP")
	assert_true(hc.max_health == 100.0, "Salud máxima asignada a 100 HP")
	assert_true(not hc.is_dead(), "Entidad recién creada nace viva")

	var damaged_signal_received = [false]
	hc.damaged.connect(func(amt, _att): damaged_signal_received[0] = true)

	var damage_dealt = hc.take_damage(30.0)
	assert_true(damage_dealt == 30.0, "Daño infligido retornado correctamente (30 HP)")
	assert_true(hc.current_health == 70.0, "Salud reducida a 70 HP")
	assert_true(damaged_signal_received[0], "Señal damaged emitida con éxito")

	var healed_amt = hc.heal(20.0)
	assert_true(healed_amt == 20.0, "Curación de 20 HP aplicada correctamente")
	assert_true(hc.current_health == 90.0, "Salud restaurada a 90 HP")

	var died_signal_received = [false]
	hc.died.connect(func(_att): died_signal_received[0] = true)
	hc.take_damage(100.0)
	assert_true(hc.is_dead(), "Salud en 0 marca a la entidad como muerta (is_dead)")
	assert_true(died_signal_received[0], "Señal died emitida al llegar a 0 HP")

	hc.free()

func test_citizen_health_integration() -> void:
	print(INFO_COLOR + "--- Prueba 3: Integración de Salud y Barra 3D en CitizenEntity ---" + RESET_COLOR)

	var citizen = CitizenEntityClass.new()
	citizen.name = "TestCitizen"
	citizen.setup(101, true, "Peatón de Prueba")

	assert_true(citizen.health_component != null, "CitizenEntity dispone de HealthComponent instanciado")
	assert_true(citizen.get_max_health() == 100.0, "CitizenEntity tiene 100 HP por defecto")
	assert_true(citizen.health_bar_3d != null, "CitizenEntity dispone de Barra de Vida 3D (HealthBar3D)")

	citizen.take_damage(40.0)
	assert_true(citizen.get_health() == 60.0, "take_damage(40) reduce la vida del ciudadano a 60 HP")
	assert_true(citizen.get_health_percentage() == 0.60, "Porcentaje de salud es 60%")

	citizen.free()

func test_vehicle_health_defaults_and_destruction() -> void:
	print(INFO_COLOR + "--- Prueba 4: Salud de Vehículos (Auto: 500 HP, Autobús: 5000 HP) ---" + RESET_COLOR)

	var car = VehicleBaseClass.new()
	car.vehicle_name = "Auto Prueba"
	car.vehicle_type = VehicleBaseClass.VehicleType.CAR
	car._ready()

	assert_true(car.get_max_health() == 500.0, "Automóvil: Salud predeterminada de 500 HP")
	assert_true(car.health_bar_3d != null, "Automóvil: Dispone de HealthBar3D overhead")

	var bus = VehicleBaseClass.new()
	bus.vehicle_name = "Autobús El Hongo"
	bus.vehicle_type = VehicleBaseClass.VehicleType.BUS_HEAVY
	bus._ready()

	assert_true(bus.get_max_health() == 5000.0, "Autobús Pesado: Salud predeterminada de 5000 HP")

	var bus_destroyed = [false]
	bus.vehicle_destroyed.connect(func(_att): bus_destroyed[0] = true)

	bus.take_damage(5000.0)
	assert_true(bus.is_dead(), "Autobús destruido tras recibir 5000 de daño")
	assert_true(bus_destroyed[0], "Señal vehicle_destroyed emitida en el autobús")
	assert_true(not bus.engine_running, "El motor del autobús se apaga al ser destruido")

	car.free()
	bus.free()

func test_destructible_prop_mechanics() -> void:
	print(INFO_COLOR + "--- Prueba 5: Muebles y Objetos Destruibles (DestructibleProp3D) ---" + RESET_COLOR)

	var prop = DestructibleProp3DClass.new()
	prop.prop_name = "Poste de Nomenclatura"
	prop.entity_type_name = "PROP_MEDIUM"
	prop._ready()

	assert_true(prop.health_component != null, "DestructibleProp3D integra HealthComponent")
	assert_true(prop.health_component.max_health == 150.0, "Objeto mediano tiene 150 HP predeterminados")

	prop.take_damage(50.0)
	assert_true(prop.health_component.current_health == 100.0, "Daño parcial de 50 HP registrado correctamente")

	prop.free()

func test_player_combat_and_elimination() -> void:
	print(INFO_COLOR + "--- Prueba 6: Sistema de Combate y Eliminación entre Entidades ---" + RESET_COLOR)

	var player = PlayerControllerClass.new()
	player.name = "MainPlayer"
	player.setup(1, false, "Jugador Tecate")

	var enemy_npc = CitizenEntityClass.new()
	enemy_npc.name = "EnemyNPC"
	enemy_npc.setup(202, true, "Peatón Adversario")

	assert_true(player.get_health() == 100.0, "Jugador inicia con 100 HP")
	assert_true(enemy_npc.get_health() == 100.0, "Adversario inicia con 100 HP")

	# Simular 4 golpes al adversario (25 HP cada golpe)
	for i in range(4):
		enemy_npc.take_damage(25.0, player)

	assert_true(enemy_npc.is_dead(), "Adversario es eliminado tras recibir 100 HP de daño acumulado")

	player.free()
	enemy_npc.free()

func test_attack_arm_animation_and_kinematics() -> void:
	print(INFO_COLOR + "--- Prueba 7: Animación Cinemática de Brazos y Alternancia de Ataques ---" + RESET_COLOR)

	var player = PlayerControllerClass.new()
	player.name = "TestCombatPlayer"
	player.setup(1, false, "Jugador Animación")

	assert_true(not player.is_attacking, "El jugador inicia sin ataque activo")
	assert_true(player.attack_timer == 0.0, "Temporizador de ataque en reposo inicial")

	# 1. Disparar golpe
	var attack_triggered = player.trigger_melee_attack()
	assert_true(attack_triggered, "trigger_melee_attack() exitoso")
	assert_true(player.is_attacking, "is_attacking pasa a true")
	assert_true(player.attack_timer > 0.0, "attack_timer es positivo (~0.32s)")

	var first_hand = player.current_attack_hand
	assert_true(first_hand == 0 or first_hand == 1, "Mano de ataque asignada correctamente")

	# 2. Protección contra spam (Cooldown activo)
	var spam_blocked = not player.trigger_melee_attack()
	assert_true(spam_blocked, "Cooldown bloquea spam de ataques instantáneos")

	# 3. Cinemática procedural y modificación articular de huesos en el punto de impacto
	player._update_procedural_animations(0.15)
	assert_true(player.skeleton != null, "Esqueleto 3D disponible para cinemática")

	if player.skeleton:
		var bone_strike = player.bone_upperarm_r if first_hand == 0 else player.bone_upperarm_l
		if bone_strike != -1:
			var strike_rot = player.skeleton.get_bone_pose_rotation(bone_strike)
			var base_rot = player._base_rot_upperarm_r if first_hand == 0 else player._base_rot_upperarm_l
			assert_true(not strike_rot.is_equal_approx(base_rot), "Hueso del brazo atacante se desplaza cinemáticamente de la pose base")

	# 4. Conclusión de la animación
	player._update_procedural_animations(0.35)
	assert_true(not player.is_attacking, "Ataque concluye al expirar su duración")

	# 5. Alternancia de puños (Combo rítmico: Puño alterno en el siguiente ataque)
	# Esperar cooldown
	player._process_attack_timers(0.30)
	var next_attack = player.trigger_melee_attack()
	assert_true(next_attack, "Segundo ataque ejecutado tras enfriamiento")
	assert_true(player.current_attack_hand != first_hand, "Los puños alternan dinámicamente (Jab / Cross)")

	# 6. Sacudida de cámara (Camera Shake)
	if player.camera_director:
		player.camera_director.apply_camera_shake(0.25, 0.15)
		assert_true(player.camera_director.shake_timer > 0.0, "Sacudida de cámara registra timer activo")
		player.camera_director._process(0.20)
		assert_true(player.camera_director.shake_timer == 0.0, "Sacudida de cámara decae a 0 al finalizar la duración")

	# 7. Entidades ciudadanas autónomas (CitizenEntity)
	var npc = CitizenEntityClass.new()
	npc.name = "CombatCitizen"
	npc.setup(303, true, "Peatón Karateka")

	assert_true(not npc.is_attacking, "Ciudadano inicia sin ataque activo")
	var npc_atk = npc.trigger_melee_attack()
	assert_true(npc_atk, "CitizenEntity ejecuta trigger_melee_attack()")
	assert_true(npc.is_attacking, "CitizenEntity entra en estado is_attacking")

	npc._update_procedural_locomotion(0.15, Vector3.ZERO)
	assert_true(npc.skeleton != null, "Esqueleto del ciudadano actualizado cinemáticamente")

	player.free()
	npc.free()

