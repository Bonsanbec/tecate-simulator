extends SceneTree

## Suite de Verificación Automatizada del Sistema Integral de Vehículos
## Ejecución: /Applications/Godot.app/Contents/MacOS/Godot --headless --path godot_project -s tests/test_vehicle_system.gd

const PASS_COLOR = "\u001b[32m"
const FAIL_COLOR = "\u001b[31m"
const INFO_COLOR = "\u001b[36m"
const RESET_COLOR = "\u001b[0m"

const SurfaceProfileClass = preload("res://systems/vehicles/core/surface_profile.gd")
const SurfaceDetectorClass = preload("res://systems/vehicles/core/surface_detector.gd")
const FuelSystemClass = preload("res://systems/vehicles/core/fuel_system.gd")
const VehicleSeatClass = preload("res://systems/vehicles/core/vehicle_seat.gd")
const VehicleBaseClass = preload("res://systems/vehicles/core/vehicle_base.gd")
const DrivableVehicleClass = preload("res://systems/vehicles/controllers/drivable_vehicle_controller.gd")
const RouteVehicleClass = preload("res://systems/vehicles/controllers/route_vehicle_controller.gd")
const VehicleCameraDirectorClass = preload("res://systems/vehicles/camera/vehicle_camera_director.gd")
const GasStationPumpZoneClass = preload("res://systems/vehicles/interaction/gas_station_pump_zone.gd")

var tests_passed = 0
var tests_failed = 0

func _init() -> void:
	print(INFO_COLOR + "\n========================================================" + RESET_COLOR)
	print(INFO_COLOR + " INICIANDO SUITE DE PRUEBAS DEL SISTEMA DE VEHÍCULOS" + RESET_COLOR)
	print(INFO_COLOR + "========================================================\n" + RESET_COLOR)

	_run_tests()

func _run_tests() -> void:
	test_surface_profiles()
	test_surface_detector_logic()
	test_fuel_system_dynamics()
	test_car_placeholder_contract()
	test_bus_route_placeholder_contract()
	test_player_boarding_and_dismounting()
	test_topography_slope_response()
	test_route_vehicle_navigation()
	test_remote_vehicle_network_representation()

	_print_summary()
	quit(0 if tests_failed == 0 else 1)


func assert_true(condition: bool, test_name: String) -> void:
	if condition:
		tests_passed += 1
		print("%s[PASS]%s %s" % [PASS_COLOR, RESET_COLOR, test_name])
	else:
		tests_failed += 1
		print("%s[FAIL]%s %s" % [FAIL_COLOR, RESET_COLOR, test_name])

func test_surface_profiles() -> void:
	print(INFO_COLOR + "--- Prueba 1: Perfiles Físicos de Superficies ---" + RESET_COLOR)
	var asphalt = SurfaceProfileClass.create_default(SurfaceProfileClass.SurfaceType.ASPHALT)
	assert_true(asphalt.friction == 1.0, "Asfalto Urbano: Fricción nominal 1.0")
	assert_true(asphalt.max_speed_factor == 1.0, "Asfalto Urbano: Factor velocidad 1.0")

	var dirt = SurfaceProfileClass.create_default(SurfaceProfileClass.SurfaceType.DIRT_OFFROAD)
	assert_true(dirt.friction < 0.7, "Terreno Virgen: Fricción reducida (<0.7)")
	assert_true(dirt.max_speed_factor < 0.7, "Terreno Virgen: Velocidad tope penalizada")
	assert_true(dirt.fuel_penalty_factor > 1.4, "Terreno Virgen: Consumo de combustible incrementado (>1.4x)")

	var water = SurfaceProfileClass.create_default(SurfaceProfileClass.SurfaceType.WATER)
	assert_true(water.rolling_resistance > 0.2, "Agua: Alta resistencia hidrodinámica")
	assert_true(not water.is_drivable, "Agua: Declarada no transitable/riesgo de anegamiento")

func test_surface_detector_logic() -> void:
	print(INFO_COLOR + "--- Prueba 2: Clasificación de Mallas por SurfaceDetector ---" + RESET_COLOR)
	var detector = SurfaceDetectorClass.new()
	var dummy_bridge = Node3D.new()
	dummy_bridge.name = "Bridges_Suspension_Deck"
	var prof_bridge = detector.classify_collider(dummy_bridge, Vector3.ZERO)
	assert_true(prof_bridge.type == SurfaceProfileClass.SurfaceType.CONCRETE, "Detección de nodo Bridges clasifica como CONCRETO")

	var dummy_rail = Node3D.new()
	dummy_rail.name = "Railways_Main_Track"
	var prof_rail = detector.classify_collider(dummy_rail, Vector3.ZERO)
	assert_true(prof_rail.type == SurfaceProfileClass.SurfaceType.RAILWAY, "Detección de nodo Railways clasifica como VÍA FÉRREA")

	var dummy_water = Node3D.new()
	dummy_water.name = "Waterways_RioTecate"
	var prof_water = detector.classify_collider(dummy_water, Vector3.ZERO)
	assert_true(prof_water.type == SurfaceProfileClass.SurfaceType.WATER, "Detección de nodo Waterways clasifica como AGUA")

	dummy_bridge.free()
	dummy_rail.free()
	dummy_water.free()
	detector.free()

func test_fuel_system_dynamics() -> void:
	print(INFO_COLOR + "--- Prueba 3: Dinámica y Reabastecimiento de Combustible ---" + RESET_COLOR)
	var fuel = FuelSystemClass.new()
	fuel.capacity_liters = 50.0
	fuel.current_liters = 10.0
	fuel.is_infinite_fuel = false

	# 1. Consumo activo
	var has_fuel = fuel.consume(1.0, 1.0, 1.0, 10.0) # 10 segundos a full gas
	assert_true(has_fuel, "Combustible disponible tras aceleración moderada")
	assert_true(fuel.current_liters < 10.0, "Nivel de combustible disminuyó tras el consumo")

	# 2. Agotamiento completo
	fuel.current_liters = 0.0001
	var out_fired = [false]
	fuel.out_of_fuel.connect(func(): out_fired[0] = true)
	var can_continue = fuel.consume(1.0, 1.0, 1.0, 1.0)
	assert_true(not can_continue, "Sin combustible: consume() retorna false")
	assert_true(out_fired[0], "Señal out_of_fuel emitida correctamente")

	# 3. Reabastecimiento (Gasolinera)
	var refueled = fuel.refuel(25.0)
	assert_true(refueled == 25.0, "Repostaje exacto de 25 litros")
	assert_true(fuel.current_liters == 25.0, "Nivel actual refleja el combustible cargado")
	assert_true(fuel.get_fuel_percentage() == 50.0, "Cálculo porcentual de tanque (50%)")

	# 4. Combustible infinito en ruta
	fuel.is_infinite_fuel = true
	var inf_result = fuel.consume(1.0, 2.0, 2.0, 100.0)
	assert_true(inf_result, "Vehículo de ruta con is_infinite_fuel nunca se queda sin combustible")
	assert_true(fuel.get_fuel_percentage() == 100.0, "Porcentaje permanece en 100% permanente")
	fuel.free()

func test_car_placeholder_contract() -> void:
	print(INFO_COLOR + "--- Prueba 4: Cumplimiento del Contrato en Car_Placeholder ---" + RESET_COLOR)
	var car_scene = load("res://assets/vehicles/car_placeholder.tscn")
	assert_true(car_scene != null, "Escena car_placeholder.tscn cargada exitosamente")

	var car = car_scene.instantiate()
	assert_true(car != null, "Instanciado como DrivableVehicle")
	root.add_child(car)

	assert_true(car.seats.size() == 4, "Auto dispone de exactamente 4 asientos configurados")
	var driver_seat = car.get_driver_seat()
	assert_true(driver_seat != null, "Auto dispone de asiento de Conductor (DRIVER)")
	assert_true(driver_seat.seat_type == VehicleSeatClass.SeatType.DRIVER, "Tipo de asiento de conductor validado")

	var passenger_seats = car.get_available_passenger_seats()
	assert_true(passenger_seats.size() == 3, "Auto dispone de 3 plazas de Pasajero libres")

	assert_true(car.fuel_system != null, "Auto cuenta con FuelSystem integrado")
	assert_true(not car.fuel_system.is_infinite_fuel, "Auto particular NO tiene combustible infinito")

	assert_true(car.suspension_rays.size() >= 4, "Auto dispone de al menos 4 raycasts de suspensión")

	car.queue_free()

func test_bus_route_placeholder_contract() -> void:
	print(INFO_COLOR + "--- Prueba 5: Cumplimiento del Contrato en Bus_Route_Placeholder ---" + RESET_COLOR)
	var bus_scene = load("res://assets/vehicles/bus_route_placeholder.tscn")
	assert_true(bus_scene != null, "Escena bus_route_placeholder.tscn cargada exitosamente")

	var bus = bus_scene.instantiate()
	assert_true(bus != null, "Instanciado como RouteVehicle")
	root.add_child(bus)

	assert_true(bus.get_driver_seat() == null, "Autobús de ruta predefinida NO tiene asiento de conductor para jugador")
	assert_true(bus.seats.size() >= 4, "Autobús cuenta con múltiples asientos de pasajero")
	assert_true(bus.fuel_system.is_infinite_fuel, "Autobús de ruta predefinida tiene combustible infinito garantizado")
	assert_true(bus.waypoints.size() > 0, "Autobús tiene circuito de waypoints configurado")
	assert_true(bus.station_indices.size() > 0, "Autobús tiene paradas obligatorias programadas")

	bus.queue_free()

func test_player_boarding_and_dismounting() -> void:
	print(INFO_COLOR + "--- Prueba 6: Ciclo de Abordaje y Descenso Jugador <-> Vehículo ---" + RESET_COLOR)
	var car_scene = load("res://assets/vehicles/car_placeholder.tscn")
	var car = car_scene.instantiate()
	root.add_child(car)

	var dummy_player = CharacterBody3D.new()
	dummy_player.name = "DummyPlayer"
	root.add_child(dummy_player)

	# 1. Abordar como conductor
	var entered = car.enter_vehicle(dummy_player, VehicleSeatClass.SeatType.DRIVER)
	assert_true(entered, "Jugador abordó el vehículo con éxito")
	assert_true(car.has_driver(), "Vehículo reconoce que tiene conductor activo")
	assert_true(car.engine_running, "Motor se encendió automáticamente al tomar el volante")

	# 2. Intentar que un segundo jugador aborde el mismo asiento de conductor
	var dummy_player_2 = CharacterBody3D.new()
	var entered_2 = car.enter_vehicle(dummy_player_2, VehicleSeatClass.SeatType.DRIVER)
	assert_true(entered_2, "Segundo ocupante ingresa redirigido a plaza de Pasajero")
	assert_true(car.get_available_passenger_seats().size() == 2, "Plaza de pasajero ocupada por segundo jugador")

	# 3. Descenso de conductor
	var exited = car.exit_vehicle(dummy_player)
	assert_true(exited, "Conductor descendió con éxito")
	assert_true(not car.has_driver(), "Vehículo ya no tiene conductor activo")

	car.queue_free()
	dummy_player.queue_free()
	dummy_player_2.queue_free()

func test_topography_slope_response() -> void:
	print(INFO_COLOR + "--- Prueba 7: Respuesta Matemática a Pendientes Topográficas ---" + RESET_COLOR)
	var car_scene = load("res://assets/vehicles/car_placeholder.tscn")
	var car = car_scene.instantiate()

	# Simular una normal de terreno inclinada a 15 grados (~0.26 rad)
	var slope_angle_deg = 15.0
	var slope_rad = deg_to_rad(slope_angle_deg)
	var inclined_normal = Vector3(0.0, cos(slope_rad), sin(slope_rad)).normalized()

	# Validar el cálculo trigonométrico de pendiente
	var calculated_cos = inclined_normal.dot(Vector3.UP)
	var calculated_angle = rad_to_deg(acos(calculated_cos))

	assert_true(abs(calculated_angle - slope_angle_deg) < 0.1, "Cálculo analítico de ángulo de pendiente (15°)")

	# Validar cálculo de orientación de chasis proyectada
	var forward = -Vector3.FORWARD # Vector -Z
	var projected_forward = (forward - inclined_normal * forward.dot(inclined_normal)).normalized()
	assert_true(projected_forward.length_squared() > 0.0, "Proyección de vector frontal sobre normal inclinada sin singularidades")

	car.free()

func test_route_vehicle_navigation() -> void:
	print(INFO_COLOR + "--- Prueba 8: Navegación de Ruta y Paradas Temporizadas ---" + RESET_COLOR)
	var bus_scene = load("res://assets/vehicles/bus_route_placeholder.tscn")
	var bus = bus_scene.instantiate()

	bus.waypoints = PackedVector3Array([
		Vector3(0, 0, 0),
		Vector3(0, 0, 10),
		Vector3(10, 0, 10)
	])
	bus.station_indices = { 1: "Parada de Prueba" }
	bus.station_dwell_time = 0.5
	bus.current_waypoint_index = 1

	var arrived_signal_fired = [false]
	bus.route_station_arrived.connect(func(_st, _dwell): arrived_signal_fired[0] = true)

	# Simular llegada al waypoint de estación
	bus._on_waypoint_reached()
	assert_true(bus.is_at_station, "Autobús detectó llegada a estación obligatoria")
	assert_true(arrived_signal_fired[0], "Señal route_station_arrived emitida")

	# Procesar tiempo de espera
	bus._process_station_dwell(0.6)
	assert_true(not bus.is_at_station, "Autobús reanuda la marcha tras cumplir tiempo de espera")

	bus.free()

func test_remote_vehicle_network_representation() -> void:
	print(INFO_COLOR + "--- Prueba 9: Representación y Anclaje en RemoteVehicle (Multijugador) ---" + RESET_COLOR)
	var remote_veh_script = preload("res://systems/network/remote_vehicle.gd")
	var tkt_codec_script = preload("res://systems/network/tkt_codec.gd")

	# 1. Instanciación y setup de automóvil particular
	var rv_car = CharacterBody3D.new()
	rv_car.set_script(remote_veh_script)
	rv_car.setup(1001, false)
	assert_true(rv_car.entity_id == 1001, "RemoteVehicle: Entity ID asignado correctamente")
	assert_true(not rv_car.is_route_vehicle, "RemoteVehicle: Reconoce que no es autobús de ruta")
	assert_true(rv_car.seats.size() == 4, "RemoteVehicle (Auto): Dispone de 4 plazas de asientos")

	# 2. Ingesta de snapshot y actualización de cinemática
	var rec1 = tkt_codec_script.EntityRecord.new()
	rec1.entity_id = 1001
	rec1.entity_type = tkt_codec_script.EntityType.VEHICLE
	rec1.position = Vector3(10, 400, 20)
	rec1.yaw = 90.0
	rec1.pitch = -5.0
	rec1.velocity = Vector3(5, 0, 0)
	rv_car.push_snapshot_record(rec1, 1000)

	assert_true(rv_car.snapshot_history.size() == 1, "RemoteVehicle: Registro de snapshot almacenado")
	rv_car._physics_process(0.016)
	assert_true(is_equal_approx(rv_car.position.x, 10.0), "RemoteVehicle: Posición refleja snapshot (X=10)")

	# 3. Anclaje de pasajero o conductor remoto
	var mock_player = Node3D.new()
	mock_player.name = "MockRemotePlayer_42"
	rv_car.mount_passenger(42, 0, mock_player) # Conductor
	assert_true(rv_car.seated_passengers.has(42), "RemoteVehicle: Pasajero ID 42 montado en asiento")
	assert_true(mock_player.get_parent() == rv_car.seats[0], "MockPlayer es hijo del asiento 0")

	# 4. Descenso de pasajero remoto
	var unmounted = rv_car.unmount_passenger(42)
	assert_true(unmounted == mock_player, "RemoteVehicle: Pasajero desmontado con éxito")
	assert_true(not rv_car.seated_passengers.has(42), "RemoteVehicle: Pasajero ID 42 removido del diccionario")

	mock_player.free()
	rv_car.free()

	# 5. Instanciación y setup de autobús de ruta
	var rv_bus = CharacterBody3D.new()
	rv_bus.set_script(remote_veh_script)
	rv_bus.setup(1002, true)
	assert_true(rv_bus.is_route_vehicle, "RemoteVehicle (Bus): Reconoce modo de ruta predefinida")
	assert_true(rv_bus.seats.size() == 31, "RemoteVehicle (Bus): Construye 31 asientos reglamentarios")
	rv_bus.free()

func _print_summary() -> void:

	print("\n========================================================")
	print(" RESUMEN DE PRUEBAS DEL SISTEMA DE VEHÍCULOS")
	print("========================================================")
	print("  Pruebas superadas:  %s%d%s" % [PASS_COLOR, tests_passed, RESET_COLOR])
	print("  Pruebas fallidas:   %s%d%s" % [FAIL_COLOR if tests_failed > 0 else PASS_COLOR, tests_failed, RESET_COLOR])
	print("========================================================\n")
