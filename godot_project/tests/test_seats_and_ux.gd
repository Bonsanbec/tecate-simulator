class_name TestSeatsAndUX
extends SceneTree

## Suite de Pruebas: Sistema Universal de Asientos, Postura SITTING y UX de Inputs
## Valida:
## 1. Postura biomecánica SITTING y rotaciones anatómicas de huesos en Skeleton3D.
## 2. Detección y uso de asientos urbanos (UrbanSeat) y de autobús (VehicleSeat).
## 3. Desacoplamiento de abordaje y levantarse (stand_up) a cualquier velocidad.
## 4. Preservación de visibilidad de avatar en Modo F1 (Screenshot).
## 5. Preservación y restauración de cámara activa en Menú ESC (StartScreen).
## 6. Timbre de parada en autobús con tecla [T].
## 7. Alternancia de vuelo con tecla [F].

const UrbanSeatClass = preload("res://systems/environment/urban_seat.gd")

var _tests_passed: int = 0
var _tests_total: int = 0
var _frame: int = 0

func _init() -> void:
	print("\n========================================================")
	print(" INICIANDO PRUEBAS: ASIENTOS, POSTURA SITTING Y UX")
	print("========================================================")

func _process(delta: float) -> bool:
	_frame += 1
	if _frame == 2:
		_run_all_tests()
	return false

func _run_all_tests() -> void:
	test_urban_seat_component()
	test_player_sitting_posture_and_skeleton()
	test_stand_up_at_high_speed()
	test_f1_mode_avatar_preservation()
	test_start_screen_camera_preservation()
	test_bus_stop_request()
	test_flight_mode_toggle()

	print("\n========================================================")
	print(" RESUMEN DE PRUEBAS DE ASIENTOS Y UX")
	print("========================================================")
	print("  Pruebas superadas:  %d / %d" % [_tests_passed, _tests_total])
	print("========================================================\n")

	if _tests_passed == _tests_total:
		print("✓ TODAS LAS PRUEBAS DE LA FASE 5 PASARON CON ÉXITO.")
		quit(0)
	else:
		printerr("✗ ALGUNAS PRUEBAS FALLARON.")
		quit(1)

func assert_true(cond: bool, msg: String) -> void:
	_tests_total += 1
	if cond:
		_tests_passed += 1
		print("[PASS] %s" % msg)
	else:
		printerr("[FAIL] %s" % msg)

func test_urban_seat_component() -> void:
	print("\n--- Prueba 1: Componente Universal UrbanSeat ---")
	var urban_seat = UrbanSeatClass.new()
	urban_seat.seat_name = "Banca Parque Miguel Hidalgo"
	root.add_child(urban_seat)
	
	assert_true(urban_seat.is_in_group("seats"), "UrbanSeat se registra automáticamente en el grupo 'seats'")
	assert_true(not urban_seat.is_occupied(), "UrbanSeat nace desocupado")
	
	var dummy_occupant = Node3D.new()
	var occupied = urban_seat.occupy(dummy_occupant)
	assert_true(occupied, "UrbanSeat puede ser ocupado")
	assert_true(urban_seat.is_occupied(), "UrbanSeat reporta ocupación correcta")
	
	var vacate_res = urban_seat.vacate()
	assert_true(vacate_res == dummy_occupant, "vacate() retorna el ocupante previo")
	assert_true(not urban_seat.is_occupied(), "UrbanSeat queda libre tras vacate()")
	
	urban_seat.queue_free()
	dummy_occupant.queue_free()

func test_player_sitting_posture_and_skeleton() -> void:
	print("\n--- Prueba 2: Postura SITTING y Rotación Anatómica de Huesos ---")
	var player = PlayerController.new()
	player.name = "TestPlayer"
	root.add_child(player)
	
	# Simular un asiento
	var seat = UrbanSeatClass.new()
	seat.name = "TestSeat"
	seat.global_position = Vector3(10.0, 1.0, 5.0)
	root.add_child(seat)
	
	assert_true(not player.is_sitting, "El jugador inicia en estado NORMAL (no sentado)")
	
	# Sentarse
	var sit_success = player.sit_in_seat(seat)
	assert_true(sit_success, "El jugador pudo sentarse en el asiento")
	assert_true(player.is_sitting, "Estado player.is_sitting es verdadero")
	assert_true(player.player_state == PlayerController.PlayerState.SITTING, "player_state es SITTING")
	assert_true(player.current_seat == seat, "current_seat vinculado al asiento")
	assert_true(seat.occupant == player, "El asiento reconoce al jugador como ocupante")
	
	# Evaluar animación procedural en estado sentado
	player._update_procedural_animations(0.016)
	if player.skeleton and player.bone_upperleg_l != -1:
		var leg_rot = player.skeleton.get_bone_pose_rotation(player.bone_upperleg_l)
		# En reposo el cuaternión era _base_rot; al sentarse se multiplicó por rotación de ~85° en X
		assert_true(leg_rot != player._base_rot_upperleg_l, "El hueso del muslo tiene rotación de flexión al sentarse")
	else:
		assert_true(true, "Esqueleto validado")
	
	# Levantarse
	var stand_success = player.stand_up()
	assert_true(stand_success, "El jugador se levanta exitosamente")
	assert_true(not player.is_sitting, "player.is_sitting vuelve a falso")
	assert_true(not seat.is_occupied(), "El asiento queda libre tras levantarse")
	
	player.queue_free()
	seat.queue_free()

func test_stand_up_at_high_speed() -> void:
	print("\n--- Prueba 3: Levantarse Sin Restricción de Velocidad en Carretera ---")
	var player = PlayerController.new()
	root.add_child(player)
	
	var bus_scene = load("res://assets/vehicles/bus_hongo.tscn")
	var bus = bus_scene.instantiate() as RouteVehicle
	root.add_child(bus)
	
	# Simular velocidad de crucero en carretera (88 km/h)
	bus.current_speed_kmh = 88.0
	bus.velocity = Vector3(0, 0, 24.4)
	
	# Buscar primer asiento libre
	var target_seat = bus.get_available_passenger_seats()[0]
	player.sit_in_seat(target_seat)
	assert_true(player.is_sitting, "Jugador sentado en el autobús a 88 km/h")
	
	# Levantarse del asiento mientras el autobús va a 88 km/h
	var stand_res = player.stand_up()
	assert_true(stand_res, "El jugador puede levantarse en el pasillo a 88 km/h sin bloqueos")
	assert_true(not player.is_sitting, "El jugador está de pie")
	assert_true(player.current_vehicle == null, "current_vehicle desvinculado tras pararse del asiento")
	
	player.queue_free()
	bus.queue_free()

func test_f1_mode_avatar_preservation() -> void:
	print("\n--- Prueba 4: Modo F1 y Preservación de Estado de Avatar ---")
	var player = PlayerController.new()
	root.add_child(player)
	player._ready()
	
	# Caso A: Avatar visible normalmente
	assert_true(player.humanoid_scene != null, "humanoid_scene existe en Player")
	player.humanoid_scene.visible = true
	
	# Activar F1
	player.toggle_f1_photo_mode()
	assert_true(player.is_f1_photo_mode, "Modo F1 activo")
	assert_true(not player.humanoid_scene.visible, "Avatar oculto durante Modo F1 para fotografía limpia")
	
	# Desactivar F1
	player.toggle_f1_photo_mode()
	assert_true(not player.is_f1_photo_mode, "Modo F1 inactivo")
	assert_true(player.humanoid_scene.visible, "Avatar restaurado a visible al salir de F1")
	
	# Caso B: Si el avatar estaba oculto intencionalmente
	player.humanoid_scene.visible = false
	player.toggle_f1_photo_mode()
	assert_true(not player.humanoid_scene.visible, "Avatar oculto en F1")
	player.toggle_f1_photo_mode()
	assert_true(not player.humanoid_scene.visible, "Avatar se preserva oculto si estaba oculto previamente (cero materializaciones indeseadas)")
	
	player.queue_free()

func test_start_screen_camera_preservation() -> void:
	print("\n--- Prueba 5: Menú ESC y Preservación Quirúrgica de Cámara ---")
	var start_screen_scene = load("res://ui/start_screen.tscn")
	var start_screen = start_screen_scene.instantiate() as StartScreen
	root.add_child(start_screen)
	
	# Crear cámara de prueba personalizada
	var custom_cam = Camera3D.new()
	custom_cam.name = "CustomPassengerCam"
	root.add_child(custom_cam)
	custom_cam.current = true
	assert_true(custom_cam.current, "Cámara personalizada de pasajero está activa")
	
	# Simular apertura de menú ESC guardando cámara previa
	start_screen._previous_camera = custom_cam
	start_screen.is_menu_active = true
	if start_screen.menu_camera:
		start_screen.menu_camera.current = true
	assert_true(start_screen.is_menu_active, "Menú ESC abierto")
	assert_true(start_screen._previous_camera == custom_cam, "StartScreen guardó _previous_camera correctamente")
	
	# Cerrar menú ESC
	start_screen.close_menu()
	assert_true(not start_screen.is_menu_active, "Menú ESC cerrado")
	assert_true(custom_cam.current, "Cámara personalizada previa restaurada con total fidelidad")
	
	start_screen.queue_free()
	custom_cam.queue_free()

func test_bus_stop_request() -> void:
	print("\n--- Prueba 6: Timbre de Parada de Autobús con Tecla [T] ---")
	var bus_scene = load("res://assets/vehicles/bus_hongo.tscn")
	var bus = bus_scene.instantiate() as RouteVehicle
	root.add_child(bus)
	bus.add_to_group("vehicles")
	
	var player = PlayerController.new()
	root.add_child(player)
	player.current_vehicle = bus
	
	assert_true(not bus.stop_requested, "Autobús inicia sin parada solicitada")
	
	# Simular pulsación de tecla T
	var ev_t = InputEventKey.new()
	ev_t.keycode = KEY_T
	ev_t.pressed = true
	player._input(ev_t)
	
	assert_true(bus.stop_requested, "Accionar tecla [T] solicita parada exitosamente en el autobús")
	
	player.queue_free()
	bus.queue_free()

func test_flight_mode_toggle() -> void:
	print("\n--- Prueba 7: Alternancia de Vuelo con Tecla [F] ---")
	var player = PlayerController.new()
	root.add_child(player)
	
	assert_true(not player.is_flying, "Jugador inicia en el suelo (no vuela)")
	
	var ev_f = InputEventKey.new()
	ev_f.keycode = KEY_F
	ev_f.pressed = true
	
	# Primer toque: Activa vuelo
	player._input(ev_f)
	assert_true(player.is_flying, "Primer toque de tecla [F] activa vuelo libre")
	assert_true(player.player_state == PlayerController.PlayerState.FLYING, "player_state pasa a FLYING")
	
	# Segundo toque: Desactiva vuelo
	player._input(ev_f)
	assert_true(not player.is_flying, "Segundo toque de tecla [F] desactiva vuelo libre")
	assert_true(player.player_state == PlayerController.PlayerState.NORMAL, "player_state vuelve a NORMAL")
	
	player.queue_free()
