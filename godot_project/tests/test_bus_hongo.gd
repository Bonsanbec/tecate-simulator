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
	test_parametric_identity()
	test_right_lane_offset()
	test_transmission_and_gears()
	test_crossing_stops_and_debounce()

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

	# Colisiones estructurales generadas en tiempo de importación (Regla 8: Cero cajas manuales en .tscn)
	var floor_col = bus.find_child("Bus_Interior_Piso_ColBody", true, false)
	var body_col = bus.find_child("Bus_Carroceria_Roja_ColBody", true, false)
	assert_true(floor_col != null, "Colisión de piso interior (Bus_Interior_Piso_ColBody) generada vía post-import")
	assert_true(body_col != null, "Colisión de carrocería (Bus_Carroceria_Roja_ColBody) generada vía post-import")
	assert_true(floor_col is AnimatableBody3D, "Cuerpo de colisión es AnimatableBody3D para soporte inercial de plataforma")
	assert_true(bus.get_node_or_null("CollisionRoot") == null, "Regla 8: Cero cajas manuales BoxShape3D en .tscn")

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

	assert_true(max_z >= 12000.0, "Extremo sur alcanza el viraje en Carretera Libre Tijuana (Z = %.1f m >= 12000.0 m)" % max_z)
	assert_true(min_x <= -17000.0, "Extremo suroeste alcanza viraje seguro hacia Tijuana (min X = %.1f m <= -17000 m)" % min_x)
	assert_true(found_hidalgo, "Ruta recorre la conexión con Avenida Hidalgo")
	assert_true(found_rodriguez, "Ruta dobla hacia el norte en Calle Presidente Abelardo L. Rodríguez")
	assert_true(found_central, "Ruta ingresa al patio y dársena de la Central de Autobuses de Tecate")
	assert_true(max_x >= 54000.0, "Extremo este alcanza el poblado de La Rumorosa por la carretera libre (X = %.1f m >= 54000 m)" % max_x)

	# 2. Verificación de paradas obligatorias
	var stations: Dictionary = bus.station_indices
	assert_true(stations.size() >= 2, "Cuenta con paradas programadas obligatorias")
	var has_central_stop = false
	var has_rumorosa_stop = false
	for idx in stations.keys():
		var val = stations[idx]
		var st_name: String = str(val.get("name", val)) if val is Dictionary else str(val)
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

# ---------------------------------------------------------------------------
# Prueba 7: Identidad Paramétrica por Instancia (Unidad, Placas, Concesión)
# ---------------------------------------------------------------------------
func test_parametric_identity() -> void:
	print(INFO_COLOR + "--- Prueba 7: Identidad Paramétrica por Instancia (Unidad, Placas, Concesión) ---" + RESET_COLOR)
	var scene_res = load("res://assets/vehicles/bus_hongo.tscn")
	var bus = scene_res.instantiate()
	get_root().add_child(bus)

	# 1. Verificar valores canónicos iniciales
	assert_true(bus.get("unit_number") == "24", "Número de unidad canónico inicial: '24'")
	assert_true(bus.get("license_plate") == "A-30530-A", "Placa oficial de Baja California: 'A-30530-A'")
	assert_true(bus.get("concession_id") == "TKT-A-19-00006", "Concesión de transporte suburbano: 'TKT-A-19-00006'")

	# 2. Verificar nodos Label3D vinculados
	var label_unit_l = bus.get_node_or_null("ParametricLabels/Label_Unit_Left") as Label3D
	var label_unit_r = bus.get_node_or_null("ParametricLabels/Label_Unit_Right") as Label3D
	var label_unit_rear = bus.get_node_or_null("ParametricLabels/Label_Unit_Rear") as Label3D
	var label_plate_front = bus.get_node_or_null("ParametricLabels/Label_Plate_Front") as Label3D
	var label_plate_rear = bus.get_node_or_null("ParametricLabels/Label_Plate_Rear") as Label3D
	var label_concession = bus.get_node_or_null("ParametricLabels/Label_Concession_Rear") as Label3D

	assert_true(label_unit_l != null and label_unit_l.text == "24", "Label3D unidad lateral izquierdo inicializado en '24'")
	assert_true(label_unit_r != null and label_unit_r.text == "24", "Label3D unidad lateral derecho inicializado en '24'")
	assert_true(label_unit_rear != null and label_unit_rear.text == "24", "Label3D unidad posterior inicializado en '24'")
	assert_true(label_plate_front != null and label_plate_front.text == "A-30530-A", "Label3D placa delantera inicializado")
	assert_true(label_plate_rear != null and label_plate_rear.text == "A-30530-A", "Label3D placa trasera inicializado")
	assert_true(label_concession != null and label_concession.text == "TKT-A-19-00006", "Label3D concesión trasera inicializado")

	# 3. Probar reasignación paramétrica reactiva en tiempo de ejecución (ej. Unidad 18)
	bus.set("unit_number", "18")
	bus.set("license_plate", "A-30531-A")
	bus.set("concession_id", "TKT-A-19-00018")

	assert_true(label_unit_l.text == "18", "Actualización dinámica paramétrica: unidad reasignada a '18'")
	assert_true(label_plate_rear.text == "A-30531-A", "Actualización dinámica paramétrica: placa reasignada a 'A-30531-A'")
	assert_true(label_concession.text == "TKT-A-19-00018", "Actualización dinámica paramétrica: concesión reasignada a 'TKT-A-19-00018'")

	bus.free()

# ---------------------------------------------------------------------------
# Prueba 8: Separación y Carril Derecho (Normativa Mexicana)
# ---------------------------------------------------------------------------
func test_right_lane_offset() -> void:
	print(INFO_COLOR + "--- Prueba 8: Circulación en Carril Derecho en Ambos Sentidos ---" + RESET_COLOR)
	var scene_res = load("res://assets/vehicles/bus_hongo.tscn")
	var bus = scene_res.instantiate()

	var wps: PackedVector3Array = bus.waypoints
	assert_true(wps.size() > 500, "Waypoints disponibles para análisis de carriles")

	# Encontrar un punto en Av. Hidalgo de ida y de retorno (alrededor de X = -453)
	var ida_pt: Vector3 = Vector3.ZERO
	var ret_pt: Vector3 = Vector3.ZERO
	var half_size = wps.size() / 2

	for i in range(half_size):
		if absf(wps[i].x - (-453.0)) < 30.0:
			ida_pt = wps[i]
			break

	for i in range(half_size, wps.size()):
		if absf(wps[i].x - (-453.0)) < 30.0:
			ret_pt = wps[i]
			break

	assert_true(ida_pt != Vector3.ZERO, "Punto de ida en Av. Hidalgo localizado")
	assert_true(ret_pt != Vector3.ZERO, "Punto de retorno en Av. Hidalgo localizado")

	# En Godot (+X Este, +Z Sur):
	# De ida (hacia el Este), el carril derecho se desplaza hacia el Sur (+Z).
	# De retorno (hacia el Poniente), el carril derecho se desplaza hacia el Norte (-Z).
	# Por ende: ida_pt.z debe ser mayor que ret_pt.z
	var delta_z = ida_pt.z - ret_pt.z
	assert_true(delta_z > 2.0, "Separación entre carriles en Av. Hidalgo >= 2.0 m (Obtenido: %.2f m)" % delta_z)
	assert_true(delta_z < 4.5, "Separación cabe dentro del ancho de calzada (< 4.5 m, Obtenido: %.2f m)" % delta_z)

	# En Carretera Federal 2 (alrededor de X = 25000)
	var hw_ida: Vector3 = Vector3.ZERO
	var hw_ret: Vector3 = Vector3.ZERO
	for i in range(half_size):
		if absf(wps[i].x - 25000.0) < 150.0:
			hw_ida = wps[i]
			break
	for i in range(half_size, wps.size()):
		if absf(wps[i].x - 25000.0) < 150.0:
			hw_ret = wps[i]
			break

	assert_true(hw_ida != Vector3.ZERO, "Punto carretero de ida localizado")
	assert_true(hw_ret != Vector3.ZERO, "Punto carretero de retorno localizado")
	var hw_delta_z = hw_ida.z - hw_ret.z
	assert_true(hw_delta_z > 3.0, "Separación carretera federal >= 3.0 m (Obtenido: %.2f m)" % hw_delta_z)

	bus.free()

# ---------------------------------------------------------------------------
# Prueba 9: Transmisión Mecánica de 6 Velocidades y Dinámica de Par
# ---------------------------------------------------------------------------
func test_transmission_and_gears() -> void:
	print(INFO_COLOR + "--- Prueba 9: Transmisión Mecánica de 6 Velocidades ---" + RESET_COLOR)
	var scene_res = load("res://assets/vehicles/bus_hongo.tscn")
	var bus = scene_res.instantiate()
	get_root().add_child(bus)

	assert_true(bus.total_gears == 6, "Transmisión configurada con 6 marchas hacia adelante")
	assert_true(bus.get_gear_name() == "1ª", "Marcha inicial en reposo es 1ª")

	# Probar escalonamiento de marchas según velocidad
	bus.update_transmission(25.0, 0.3)
	assert_true(bus.current_gear == 2, "A 25 km/h selecciona 2ª marcha")
	assert_true(bus.get_gear_name() == "2ª", "Nomenclatura correcta: 2ª")

	bus.update_transmission(55.0, 0.3)
	assert_true(bus.current_gear == 4, "A 55 km/h selecciona 4ª marcha")

	bus.update_transmission(95.0, 0.3)
	assert_true(bus.current_gear == 6, "A 95 km/h selecciona 6ª marcha (sobremarcha crucero)")
	assert_true(bus.get_gear_name() == "6ª", "Nomenclatura correcta: 6ª")
	assert_true(bus.is_shifting == true, "Al cambiar de marcha se activa bandera is_shifting")
	bus.update_transmission(95.0, 0.25)
	assert_true(bus.is_shifting == false, "Embrague acoplado tras cambio de marcha")
	assert_true(bus.engine_rpm > 1200.0, "Régimen de RPM diésel activo en marcha alta")

	bus.free()

# ---------------------------------------------------------------------------
# Prueba 10: Paradas en Cruces con Debounce y Timbre
# ---------------------------------------------------------------------------
func test_crossing_stops_and_debounce() -> void:
	print(INFO_COLOR + "--- Prueba 10: Paradas en Cruces (Debounce 5 min y Timbre) ---" + RESET_COLOR)
	var scene_res = load("res://assets/vehicles/bus_hongo.tscn")
	var bus = scene_res.instantiate()
	get_root().add_child(bus)

	assert_true(bus.crossing_debounce_sec == 300.0, "Debounce de cruces establecido en 300 s (5 minutos)")
	assert_true(bus.crossing_dwell_time >= 10.0, "Tiempo de espera en cruce >= 10.0 s")

	# Simular solicitud de parada por timbre con contenedor array para mutabilidad en lambda
	var bell_ack = [false]
	bus.stop_requested_acknowledged.connect(func(): bell_ack[0] = true)
	bus.request_stop()
	assert_true(bus.stop_requested == true, "Timbre de bajada activa bandera stop_requested")
	assert_true(bell_ack[0] == true, "Señal stop_requested_acknowledged emitida para feedback UI")

	# Configurar un cruce simulado en waypoint 1
	bus.intersections[1] = {"name": "Av. Hidalgo y Calle Aldrete"}
	bus.time_since_last_stop = 300.0 # Cumplió debounce
	bus.current_waypoint_index = 1
	bus.waypoints = PackedVector3Array([Vector3.ZERO, Vector3(0, 0, 1), Vector3(0, 0, 10)])

	var crossing_arrived_name = [""]
	bus.crossing_stop_arrived.connect(func(c_name, _t): crossing_arrived_name[0] = c_name)
	bus._on_waypoint_reached()

	assert_true(bus.is_at_crossing == true, "Autobús entra en estado de parada en cruce")
	assert_true(crossing_arrived_name[0] == "Av. Hidalgo y Calle Aldrete", "Nombre del cruce reportado correctamente")
	assert_true(bus.time_since_last_stop == 0.0, "Debounce reiniciado tras iniciar la parada")

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
