extends SceneTree

func _init() -> void:
	print("\n========================================================")
	print(" VALIDACIÓN RIGUROSA DE TOOLTIPS Y ESCANEO EN TIEMPO REAL")
	print("========================================================")
	call_deferred("_run_validation")

func _run_validation() -> void:
	# 1. Crear jugador
	var player = PlayerController.new()
	root.add_child(player)
	player.global_position = Vector3(0, 0, 0)
	player._ready()

	# 2. Crear una banca urbana en (1.0, 0, 0)
	var UrbanSeatClass = load("res://systems/environment/urban_seat.gd")
	var urban_seat = UrbanSeatClass.new()
	urban_seat.seat_name = "Banca Parque Miguel Hidalgo"
	root.add_child(urban_seat)
	urban_seat.global_position = Vector3(1.2, 0.0, 0.0)

	# 3. Crear un autobús en (10.0, 0, 0)
	var bus_scene = load("res://assets/vehicles/bus_hongo.tscn")
	var bus = bus_scene.instantiate() as RouteVehicle
	root.add_child(bus)
	bus.global_position = Vector3(10.0, 0.0, 0.0)

	# Ejecutar varios frames de física con el jugador frente a la banca urbana
	for i in range(15):
		player._physics_process(0.016)

	assert(player._nearby_seat == urban_seat, "Debe detectar la banca urbana cercana en _physics_process")
	assert(player.hud._current_interaction_prompt.contains("Banca Parque Miguel Hidalgo"), "El tooltip debe mostrar la banca urbana")
	print("[PASS] Tooltip de banca urbana funcionando: '%s'" % player.hud._current_interaction_prompt)

	# 4. Mover al jugador cerca de la puerta de abordaje del autobús
	var door_global = bus.get_closest_boarding_door(Vector3(12.0, 0.0, -3.65)).global_position
	player.global_position = door_global + Vector3(0.8, 0.0, 0.0)

	for i in range(15):
		player._physics_process(0.016)

	assert(player._nearby_vehicle == bus, "Debe detectar el autobús por la puerta")
	assert(player.hud._current_interaction_prompt.contains("Abordar") and player.hud._current_interaction_prompt.contains("por la puerta"), "El tooltip debe indicar abordaje por la puerta")
	print("[PASS] Tooltip de abordaje por puerta funcionando: '%s'" % player.hud._current_interaction_prompt)

	# 5. Abordar el autobús con la tecla E
	var ev_e = InputEventKey.new()
	ev_e.keycode = KEY_E
	ev_e.pressed = true
	player._input(ev_e)

	assert(player.current_vehicle == bus, "Jugador abordó el autobús con tecla E")
	assert(not player.is_sitting, "Jugador está de pie en el pasillo")
	print("[PASS] Tecla [E] aborda correctamente al pasillo interior")

	# 6. Una vez dentro en el pasillo, caminar junto a un asiento interior
	var interior_seat = bus.get_available_passenger_seats()[0]
	player.global_position = interior_seat.global_position + Vector3(0.5, -0.4, 0.0)

	for i in range(15):
		player._physics_process(0.016)

	assert(player._nearby_seat == interior_seat, "A bordo debe detectar el asiento del autobús")
	assert(player.hud._current_interaction_prompt.contains("Sentarse en Fila 1"), "El tooltip debe mostrar la butaca del autobús")
	print("[PASS] Tooltip de asiento interior funcionando: '%s'" % player.hud._current_interaction_prompt)

	# 7. Sentarse con tecla E
	player._input(ev_e)
	assert(player.is_sitting, "Jugador sentado en el autobús con tecla E")
	assert(player.hud._current_interaction_prompt.contains("Levantarse"), "Tooltip de levantarse visible")
	print("[PASS] Tooltip de levantarse funcionando: '%s'" % player.hud._current_interaction_prompt)

	# 8. Levantarse con tecla E
	player._input(ev_e)
	assert(not player.is_sitting, "Jugador de pie tras presionar E")
	assert(player.current_vehicle == bus, "Jugador sigue a bordo del autobús tras levantarse")
	print("[PASS] Levantarse con tecla E funcionando")

	print("\n========================================================")
	print("✓ TODAS LAS INTERACCIONES [E] Y TOOLTIPS OPERAN AL 100%")
	print("========================================================\n")

	player.free()
	urban_seat.free()
	bus.free()
	quit(0)
