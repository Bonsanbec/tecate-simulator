extends SceneTree

func _init() -> void:
	print("\n========================================================")
	print(" PRUEBA DINÁMICA DE INTEGRACIÓN FÍSICA Y EXPERIENCIA DE VIAJE")
	print("========================================================")
	call_deferred("_run_simulation")

func _run_simulation() -> void:
	var bus_scene = load("res://assets/vehicles/bus_hongo.tscn")
	var bus = bus_scene.instantiate() as RouteVehicle
	root.add_child(bus)
	bus.global_position = Vector3(0, 0, 0)

	var player = PlayerController.new()
	root.add_child(player)

	# 1. Jugador en la banqueta exterior junto a la pared lateral pero lejos de la puerta
	player.global_position = Vector3(2.5, 0.0, 0.0) # Fuera del autobús a media carrocería
	player._scan_nearby_interactive_objects(0.2)
	assert(player._nearby_seat == null, "Desde el exterior NO debe detectar asientos de autobús")
	print("[PASS] Escaneo exterior: Cero acceso a asientos desde la banqueta")

	# 2. Jugador se aproxima a la puerta de abordaje delantera
	var door_pos = bus.get_closest_boarding_door(player.global_position).global_position
	player.global_position = door_pos + Vector3(0.5, 0.0, 0.0) # A 0.5 m de la puerta
	player._scan_nearby_interactive_objects(0.2)
	assert(player._nearby_vehicle == bus, "Al aproximarse a la puerta detecta el autobús para abordaje")
	print("[PASS] Proximidad a puerta: Detecta correctamente el autobús para abordaje")

	# 3. Abordaje por la puerta
	var boarded = player.board_vehicle(bus)
	assert(boarded, "Abordaje por la puerta exitoso")
	assert(player.current_vehicle == bus, "Jugador vinculado a bordo")
	assert(not player.is_sitting, "Jugador ingresa de pie en el pasillo")
	var entry_local = bus.to_local(player.global_position)
	assert(absf(entry_local.x) < 0.8, "Posición de ingreso está centrada en el pasillo")
	print("[PASS] Abordaje por puerta: Jugador posicionado en el pasillo interior (X_local = %.2f)" % entry_local.x)

	# 4. Sentarse en un asiento interior
	var seat = bus.get_available_passenger_seats()[0]
	var seated = player.sit_in_seat(seat)
	assert(seated and player.is_sitting, "Jugador sentado en el asiento")
	print("[PASS] Ocupación de asiento: Jugador sentado correctamente")

	# 5. Autobús en marcha rápida (65 km/h)
	bus.current_speed_kmh = 65.0
	bus.velocity = Vector3(0, 0, 18.0)

	# 6. Levantarse a 65 km/h
	var stood = player.stand_up()
	assert(stood, "Levantarse exitoso")
	assert(not player.is_sitting, "Jugador de pie")
	assert(player.current_vehicle == bus, "Jugador PERMANECE a bordo del autobús tras levantarse")
	print("[PASS] Levantarse a 65 km/h: Jugador permanece a bordo sin ser eyectado")

	# 7. Simular 60 cuadros continuos de física (1 segundo completo) a alta velocidad
	for f in range(60):
		# Mover autobús
		bus.global_position += bus.velocity * 0.016
		# Procesar física del jugador
		player._process_riding_vehicle(0.016)
		var rel_pos = bus.to_local(player.global_position)
		if absf(rel_pos.x) > 1.4 or absf(rel_pos.z) > 6.0:
			printerr("[FAIL] Cuadro %d: Jugador despedido fuera del autobús (X=%.2f, Z=%.2f)" % [f, rel_pos.x, rel_pos.z])
			quit(1)
			return

	print("[PASS] Simulación continua de 60 cuadros a 65 km/h: Cero desincronización ni expulsión")

	# 8. Detener autobús y descender por la puerta
	bus.current_speed_kmh = 0.0
	bus.velocity = Vector3.ZERO
	# Desplazarse hacia la puerta
	player.global_position = bus.get_interior_entry_position()
	player._scan_nearby_interactive_objects(0.2)
	assert(player._near_exit_door, "Detecta proximidad a la puerta de salida")

	var dismounted = player.dismount_vehicle()
	assert(dismounted, "Descenso exitoso")
	assert(player.current_vehicle == null, "Jugador desvinculado del autobús")
	var exit_rel = bus.to_local(player.global_position)
	assert(exit_rel.x > 1.2, "Jugador depositado en la banqueta exterior (X_local = %.2f)" % exit_rel.x)
	print("[PASS] Descenso por puerta: Jugador situado en la banqueta exterior segura")

	print("\n========================================================")
	print("✓ TODAS LAS COMPROBACIONES DINÁMICAS PASARON EXITOSAMENTE")
	print("========================================================\n")

	player.free()
	bus.free()
	quit(0)
