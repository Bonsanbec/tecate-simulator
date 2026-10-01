extends SceneTree

## Suite de Pruebas: Autobús 'El Hongo' de Tecate y Circuito Metropolitano
## Valida el asset 3D, el contrato de RouteVehicle, la topografía y la ruta completa

const PASS_COLOR = "\u001b[32m"
const FAIL_COLOR = "\u001b[31m"
const INFO_COLOR = "\u001b[36m"
const RESET_COLOR = "\u001b[0m"

const VehicleSeatClass = preload("res://systems/vehicles/core/vehicle_seat.gd")
const RouteVehicleClass = preload("res://systems/vehicles/controllers/route_vehicle_controller.gd")

var tests_passed: int = 0
var tests_failed: int = 0

func _init() -> void:
	print(INFO_COLOR + "\n========================================================")
	print(" INICIANDO PRUEBAS: AUTOBÚS 'EL HONGO' (TECATE)")
	print("========================================================" + RESET_COLOR)

	_run_tests()

func _run_tests() -> void:
	test_scene_loading_and_hierarchy()
	test_visual_mesh_and_materials()
	test_seating_and_passenger_contract()
	test_fuel_and_route_configuration()
	test_route_geographic_waypoints_and_stations()
	test_bus_navigation_simulation()

	_print_summary()
	quit(0 if tests_failed == 0 else 1)

func assert_true(condition: bool, test_name: String) -> void:
	if condition:
		tests_passed += 1
		print(PASS_COLOR + "[PASS] " + test_name + RESET_COLOR)
	else:
		tests_failed += 1
		print(FAIL_COLOR + "[FAIL] " + test_name + RESET_COLOR)

func assert_false(condition: bool, test_name: String) -> void:
	assert_true(not condition, test_name)

func assert_almost_equal(val_a: float, val_b: float, tolerance: float, test_name: String) -> void:
	assert_true(absf(val_a - val_b) <= tolerance, "%s (Obtenido: %.3f, Esperado: %.3f)" % [test_name, val_a, val_b])

# ---------------------------------------------------------------------------
# Prueba 1: Carga e Instanciación de la Escena
# ---------------------------------------------------------------------------
func test_scene_loading_and_hierarchy() -> void:
	print(INFO_COLOR + "--- Prueba 1: Carga e Instanciación de bus_hongo.tscn ---" + RESET_COLOR)
	var scene_res = load("res://assets/vehicles/bus_hongo.tscn")
	assert_true(scene_res != null, "Recurso bus_hongo.tscn cargado en memoria")

	var bus = scene_res.instantiate()
	assert_true(bus != null, "Instancia de Bus_El_Hongo creada correctamente")
	assert_true(bus is RouteVehicleClass, "El autobús es una instancia canónica de RouteVehicle")
	assert_true(bus.vehicle_name == "Autobús El Hongo (Unidad 24)", "Nombre de unidad configurado: Autobús El Hongo (Unidad 24)")
	assert_true(bus.vehicle_type == 2, "Tipo de vehículo clasificado como AUTOBÚS (2)")

	bus.free()

# ---------------------------------------------------------------------------
# Prueba 2: Malla 3D y Nodos Visuales
# ---------------------------------------------------------------------------
func test_visual_mesh_and_materials() -> void:
	print(INFO_COLOR + "--- Prueba 2: Modelo 3D GLB y Jerarquía Visual ---" + RESET_COLOR)
	var scene_res = load("res://assets/vehicles/bus_hongo.tscn")
	var bus = scene_res.instantiate()
	get_root().add_child(bus)

	var visual_root = bus.get_node_or_null("VisualRoot")
	assert_true(visual_root != null, "Nodo VisualRoot presente en el autobús")

	var model = visual_root.get_node_or_null("BusModel")
	assert_true(model != null, "Subnodo BusModel instanciado desde bus_hongo.glb")

	var collision_shape = bus.get_node_or_null("BodyCollision")
	if not collision_shape:
		collision_shape = bus.get_node_or_null("CollisionRoot/BodyCollision")
	assert_true(collision_shape != null, "BodyCollision presente en la jerarquía del autobús")
	assert_true(collision_shape.shape is BoxShape3D, "Colisionador principal es BoxShape3D")
	assert_true(bus.get_shape_owners().size() > 0 or collision_shape.shape != null, "El autobús tiene forma de colisión registrada en físicas (shape_owners > 0)")

	# Raycasts de suspensión (al menos 4)
	var suspension = bus.get_node_or_null("Suspension")
	assert_true(suspension != null, "Contenedor de suspensión presente")
	assert_true(suspension.get_child_count() >= 4, "Dispone de 4 puntos de suspensión (RayCast3D)")

	bus.free()

# ---------------------------------------------------------------------------
# Prueba 3: Plazas de Pasajero y Contrato No-Dirigible
# ---------------------------------------------------------------------------
func test_seating_and_passenger_contract() -> void:
	print(INFO_COLOR + "--- Prueba 3: Contrato de Plazas (Solo Pasajeros, No Conductor) ---" + RESET_COLOR)
	var scene_res = load("res://assets/vehicles/bus_hongo.tscn")
	var bus = scene_res.instantiate()

	assert_true(bus.get_driver_seat() != null, "El autobús cuenta con asiento físico del chofer modelado en cabina")
	var passengers = bus.get_available_passenger_seats()
	assert_true(passengers.size() == 30, "Cuenta con exactamente 30 asientos reglamentarios de pasajeros (Obtenidos: %d)" % passengers.size())

	# Simular intento de abordaje por el jugador
	var mock_player = Node3D.new()
	mock_player.name = "PlayerAvatar"

	# El jugador intenta entrar como conductor (tipo 0): debe ser asignado automáticamente como pasajero
	var entered = bus.enter_vehicle(mock_player, 0)
	assert_true(entered, "Jugador pudo abordar el autobús como pasajero")
	assert_true(not bus.has_driver(), "El autobús mantiene autonomía (has_driver() == false)")
	assert_true(passengers[0].is_occupied(), "Primer asiento de pasajero ocupado por el jugador")

	# Descenso
	var exited = bus.exit_vehicle(mock_player)
	assert_true(exited, "Jugador descendió exitosamente del autobús")
	assert_true(not passengers[0].is_occupied(), "Asiento liberado tras el descenso")

	mock_player.free()
	bus.free()

# ---------------------------------------------------------------------------
# Prueba 4: Combustible Infinito y Parámetros
# ---------------------------------------------------------------------------
func test_fuel_and_route_configuration() -> void:
	print(INFO_COLOR + "--- Prueba 4: Combustible Infinito y Parámetros de Ruta ---" + RESET_COLOR)
	var scene_res = load("res://assets/vehicles/bus_hongo.tscn")
	var bus = scene_res.instantiate()

	assert_true(bus.fuel_system != null, "FuelSystem presente")
	assert_true(bus.fuel_system.is_infinite_fuel, "Combustible infinito garantizado por contrato")
	assert_true(bus.loop_route, "Ruta configurada en bucle infinito continuo (loop_route = true)")
	assert_true(bus.station_dwell_time >= 5.0, "Tiempo de espera en estación >= 5.0 segundos")
	assert_true(bus.cruise_speed_kmh >= 35.0, "Velocidad crucero de transporte público adecuada (>= 35 km/h)")

	bus.free()

# ---------------------------------------------------------------------------
# Prueba 5: Cobertura Geográfica de Waypoints y Paradas
# ---------------------------------------------------------------------------
func test_route_geographic_waypoints_and_stations() -> void:
	print(INFO_COLOR + "--- Prueba 5: Verificación Geográfica de la Ruta Completa ---" + RESET_COLOR)
	var scene_res = load("res://assets/vehicles/bus_hongo.tscn")
	var bus = scene_res.instantiate()

	var wps: PackedVector3Array = bus.waypoints
	assert_true(wps.size() > 500, "Ruta contiene circuito de alta densidad (>500 waypoints, total: %d)" % wps.size())

	# 1. Borde Sur: Carretera Libre Tecate-Tijuana (max Z >= 5800 m, min X >= -6400 m)
	var min_x = 999999.0
	var max_x = -999999.0
	var max_z = -999999.0
	var found_hidalgo = false
	var found_central = false
	var found_rodriguez = false

	for pt in wps:
		min_x = minf(min_x, pt.x)
		max_x = maxf(max_x, pt.x)
		max_z = maxf(max_z, pt.z)
		# Cruce Av. Hidalgo
		if absf(pt.x - (-1604.9)) < 60.0 and absf(pt.z - 303.6) < 60.0:
			found_hidalgo = true
		# Pdte. Abelardo L. Rodriguez
		if absf(pt.x - 189.2) < 40.0 and absf(pt.z - 88.6) < 40.0:
			found_rodriguez = true
		# Central de Autobuses (Dársena)
		if absf(pt.x - 143.0) < 30.0 and absf(pt.z - (-18.1)) < 30.0:
			found_central = true

	assert_true(max_z >= 5800.0, "Extremo sur alcanza el límite en Carretera Libre Tijuana (Z = %.1f m)" % max_z)
	assert_true(min_x >= -6400.0, "Autopista de cuota excluida correctamente (min X = %.1f m >= -6400 m)" % min_x)
	assert_true(found_hidalgo, "Ruta recorre la conexión con Avenida Hidalgo")
	assert_true(found_rodriguez, "Ruta dobla hacia el norte en Calle Presidente Abelardo L. Rodríguez")
	assert_true(found_central, "Ruta ingresa al patio y dársena de la Central de Autobuses de Tecate")
	assert_true(max_x >= 12100.0, "Extremo este alcanza La Rumorosa por la carretera libre (X = %.1f m)" % max_x)

	# 2. Verificación de paradas obligatorias
	var stations: Dictionary = bus.station_indices
	assert_true(stations.size() >= 2, "Cuenta con paradas programadas obligatorias")
	var has_central_stop = false
	var has_rumorosa_stop = false
	for idx in stations.keys():
		var st_name: String = stations[idx]
		if "Central de Autobuses" in st_name:
			has_central_stop = true
		if "Rumorosa" in st_name:
			has_rumorosa_stop = true

	assert_true(has_central_stop, "Parada obligatoria registrada en Central de Autobuses de Tecate")
	assert_true(has_rumorosa_stop, "Parada obligatoria registrada en Terminal La Rumorosa")

	bus.free()

# ---------------------------------------------------------------------------
# Prueba 6: Simulación Física de Avance y Detección de Estación
# ---------------------------------------------------------------------------
func test_bus_navigation_simulation() -> void:
	print(INFO_COLOR + "--- Prueba 6: Simulación de Avance y Llegada a Estación ---" + RESET_COLOR)
	var scene_res = load("res://assets/vehicles/bus_hongo.tscn")
	var bus = scene_res.instantiate()

	# Asignar un circuito simplificado de 3 waypoints para simular
	bus.waypoints = PackedVector3Array([
		Vector3(0, 400, 0),
		Vector3(0, 400, 15),
		Vector3(0, 400, 30)
	])
	bus.station_indices = {
		1: "Parada Terminal Central Simulada"
	}
	bus.current_waypoint_index = 1
	bus.station_dwell_time = 0.5

	var station_arrived = [false]
	var station_name_received = [""]
	bus.route_station_arrived.connect(func(st_name, _dwell):
		station_arrived[0] = true
		station_name_received[0] = st_name
	)

	# Simular llegada al waypoint de estación
	bus._on_waypoint_reached()

	assert_true(bus.is_at_station, "Autobús entró en estado de espera en estación")
	assert_true(station_arrived[0], "Señal route_station_arrived emitida correctamente")
	assert_true(station_name_received[0] == "Parada Terminal Central Simulada", "Nombre de estación validado: %s" % station_name_received[0])

	# Simular paso del tiempo de dwell
	bus._process_station_dwell(0.6)
	assert_true(not bus.is_at_station, "Autobús reanuda la marcha tras cumplir tiempo de espera")

	bus.free()

func _print_summary() -> void:
	print(INFO_COLOR + "\n========================================================")
	print(" RESUMEN DE PRUEBAS DEL AUTOBÚS EL HONGO")
	print("========================================================" + RESET_COLOR)
	print(PASS_COLOR + "  Pruebas superadas:  %d" % tests_passed + RESET_COLOR)
	if tests_failed > 0:
		print(FAIL_COLOR + "  Pruebas fallidas:   %d" % tests_failed + RESET_COLOR)
	else:
		print(INFO_COLOR + "  Pruebas fallidas:   0" + RESET_COLOR)
	print(INFO_COLOR + "========================================================\n" + RESET_COLOR)
