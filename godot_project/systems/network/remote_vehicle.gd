class_name RemoteVehicle
extends "res://systems/vehicles/core/vehicle_base.gd"

## Representación visual, cinemática y de interacción de vehículos remotos y autónomos en Tecate Simulator.
## Hereda de VehicleBase para integrarse de forma nativa con el sistema de interacción peatonal ([E]),
## HUD diegético, director de cámaras de cabina/persecución y sincronización autoritativa TKT/1.

@export var interpolation_delay: float = 0.10 # 100 ms de búfer de interpolación

var entity_id: int = 0
var is_route_vehicle: bool = false
var snapshot_history: Array[Dictionary] = []
var current_velocity: Vector3 = Vector3.ZERO
var wheel_rotation_angle: float = 0.0

# Nodos visuales y estructurales
var vehicle_mesh_root: Node3D
var nameplate_label: Label3D
var seat_mounts: Array[Marker3D] = []
var seated_passengers: Dictionary = {} # player_id -> Node3D (RemotePlayer)
var wheel_nodes: Array[Node3D] = []

func _ready() -> void:
	super._ready()
	add_to_group("vehicles")
	# Combustible infinito en vehículos de ruta
	if is_route_vehicle and fuel_system:
		fuel_system.is_infinite_fuel = true

func setup(id: int, is_route: bool = false) -> void:
	entity_id = id
	vehicle_id = id
	is_route_vehicle = is_route
	vehicle_type = VehicleType.BUS_HEAVY if is_route else VehicleType.CAR
	vehicle_name = ("Autobús El Hongo (Unidad %d)" if is_route else "Automóvil Urbano #%d") % id
	name = "RemoteVehicle_%d" % id

	add_to_group("vehicles")

	_adjust_chassis_collision()
	_create_nameplate()
	_create_visuals()
	_create_seats_and_mounts()

func _adjust_chassis_collision() -> void:
	var col = get_node_or_null("BodyCollision") as CollisionShape3D
	if not col:
		col = CollisionShape3D.new()
		col.name = "BodyCollision"
		add_child(col)

	var box = BoxShape3D.new()
	if is_route_vehicle:
		box.size = Vector3(2.5, 2.7, 9.6)
		col.position = Vector3(0, 1.5, 0)
	else:
		box.size = Vector3(1.8, 1.4, 4.2)
		col.position = Vector3(0, 0.9, 0)
	col.shape = box

func _create_nameplate() -> void:
	nameplate_label = Label3D.new()
	nameplate_label.name = "Nameplate"
	nameplate_label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	nameplate_label.position = Vector3(0, 3.2 if is_route_vehicle else 2.1, 0)
	nameplate_label.pixel_size = 0.005
	nameplate_label.text = vehicle_name
	nameplate_label.modulate = Color(0.4, 0.9, 1.0, 1.0)
	nameplate_label.outline_render_priority = 1
	nameplate_label.outline_size = 4
	nameplate_label.outline_modulate = Color(0, 0, 0, 0.85)

	var din_font = load("res://assets/fonts/DIN_Condensed_Bold.ttf")
	if din_font:
		nameplate_label.font = din_font
	add_child(nameplate_label)

func _create_visuals() -> void:
	vehicle_mesh_root = Node3D.new()
	vehicle_mesh_root.name = "Visuals"
	add_child(vehicle_mesh_root)

	if is_route_vehicle:
		_build_route_bus_mesh()
	else:
		_build_car_mesh()

func _build_car_mesh() -> void:
	var body = MeshInstance3D.new()
	var box = BoxMesh.new()
	box.size = Vector3(1.8, 1.3, 4.2)
	var mat = StandardMaterial3D.new()
	mat.albedo_color = Color(0.18, 0.38, 0.65, 1.0) # Azul Tecate
	mat.roughness = 0.4
	mat.metallic = 0.3
	body.mesh = box
	body.material_override = mat
	body.position = Vector3(0, 0.85, 0)
	vehicle_mesh_root.add_child(body)

	var cabin = MeshInstance3D.new()
	var c_box = BoxMesh.new()
	c_box.size = Vector3(1.6, 0.8, 2.2)
	var c_mat = StandardMaterial3D.new()
	c_mat.albedo_color = Color(0.1, 0.15, 0.2, 0.9)
	c_mat.roughness = 0.1
	cabin.mesh = c_box
	cabin.material_override = c_mat
	cabin.position = Vector3(0, 1.5, -0.2)
	vehicle_mesh_root.add_child(cabin)

	_add_wheel(Vector3(-0.95, 0.35, 1.3))
	_add_wheel(Vector3(0.95, 0.35, 1.3))
	_add_wheel(Vector3(-0.95, 0.35, -1.3))
	_add_wheel(Vector3(0.95, 0.35, -1.3))

func _build_route_bus_mesh() -> void:
	var bus_glb = load("res://assets/vehicles/bus_hongo.glb")
	if bus_glb:
		var bus_model = bus_glb.instantiate()
		bus_model.name = "BusModel"
		vehicle_mesh_root.add_child(bus_model)
	else:
		var body = MeshInstance3D.new()
		var box = BoxMesh.new()
		box.size = Vector3(2.6, 2.8, 8.5)
		var mat = StandardMaterial3D.new()
		mat.albedo_color = Color(0.85, 0.2, 0.15, 1.0)
		mat.roughness = 0.5
		body.mesh = box
		body.material_override = mat
		body.position = Vector3(0, 1.6, 0)
		vehicle_mesh_root.add_child(body)

		_add_wheel(Vector3(-1.35, 0.45, 2.6), 0.45)
		_add_wheel(Vector3(1.35, 0.45, 2.6), 0.45)
		_add_wheel(Vector3(-1.35, 0.45, -1.8), 0.45)
		_add_wheel(Vector3(1.35, 0.45, -1.8), 0.45)
		_add_wheel(Vector3(-1.35, 0.45, -2.9), 0.45)
		_add_wheel(Vector3(1.35, 0.45, -2.9), 0.45)

func _add_wheel(pos: Vector3, radius: float = 0.35) -> void:
	var w = MeshInstance3D.new()
	var cyl = CylinderMesh.new()
	cyl.top_radius = radius
	cyl.bottom_radius = radius
	cyl.height = 0.28
	var mat = StandardMaterial3D.new()
	mat.albedo_color = Color(0.12, 0.12, 0.12, 1.0)
	mat.roughness = 0.9
	w.mesh = cyl
	w.material_override = mat
	w.rotation_degrees = Vector3(0, 0, 90)
	w.position = pos
	vehicle_mesh_root.add_child(w)
	wheel_nodes.append(w)

func _create_seats_and_mounts() -> void:
	seat_mounts.clear()
	_internal_seats.clear()

	var seats_container = get_node_or_null("Seats")
	if not seats_container:
		seats_container = Node3D.new()
		seats_container.name = "Seats"
		add_child(seats_container)
	else:
		for c in seats_container.get_children():
			c.queue_free()

	if is_route_vehicle:
		# Asiento 0: Conductor AI (reservado, frente en -Z)
		_create_seat(seats_container, 0, "Conductor (Ruta)", VehicleSeat.SeatType.DRIVER, Vector3(-0.75, 1.25, -3.65), Vector3(1.5, 0.2, -3.2))

		# Asientos 1..30 de pasajeros (filas desde el frente -Z hacia atrás +Z)
		var seat_idx = 1
		var z_rows_left = [-2.75, -1.85, -0.95, -0.05, 0.85, 1.75, 2.65]
		for z in z_rows_left:
			_create_seat(seats_container, seat_idx, "Pasajero Izq Ventanilla", VehicleSeat.SeatType.PASSENGER, Vector3(-1.0, 1.25, z), Vector3(1.5, 0.2, -3.2))
			seat_idx += 1
			_create_seat(seats_container, seat_idx, "Pasajero Izq Pasillo", VehicleSeat.SeatType.PASSENGER, Vector3(-0.55, 1.25, z), Vector3(1.5, 0.2, -3.2))
			seat_idx += 1

		var z_rows_right = [-1.85, -0.95, -0.05, 0.85, 1.75, 2.65]
		for z in z_rows_right:
			_create_seat(seats_container, seat_idx, "Pasajero Der Pasillo", VehicleSeat.SeatType.PASSENGER, Vector3(0.55, 1.25, z), Vector3(1.5, 0.2, -3.2))
			seat_idx += 1
			_create_seat(seats_container, seat_idx, "Pasajero Der Ventanilla", VehicleSeat.SeatType.PASSENGER, Vector3(1.0, 1.25, z), Vector3(1.5, 0.2, -3.2))
			seat_idx += 1

		for x in [-0.9, -0.3, 0.3, 0.9]:
			_create_seat(seats_container, seat_idx, "Pasajero Fila Trasera", VehicleSeat.SeatType.PASSENGER, Vector3(x, 1.25, 4.35), Vector3(1.5, 0.2, -3.2))
			seat_idx += 1
	else:
		# Automóvil: Conductor + Copiloto + 2 traseros
		_create_seat(seats_container, 0, "Conductor", VehicleSeat.SeatType.DRIVER, Vector3(-0.45, 0.7, 0.1), Vector3(-1.4, 0.2, 0.1))
		_create_seat(seats_container, 1, "Copiloto", VehicleSeat.SeatType.PASSENGER, Vector3(0.45, 0.7, 0.1), Vector3(1.4, 0.2, 0.1))
		_create_seat(seats_container, 2, "Pasajero Trasero Izq", VehicleSeat.SeatType.PASSENGER, Vector3(-0.45, 0.7, -0.9), Vector3(-1.4, 0.2, -0.9))
		_create_seat(seats_container, 3, "Pasajero Trasero Der", VehicleSeat.SeatType.PASSENGER, Vector3(0.45, 0.7, -0.9), Vector3(1.4, 0.2, -0.9))

	_discover_seats()

func _create_seat(parent: Node, index: int, s_name: String, s_type: VehicleSeat.SeatType, pos: Vector3, exit_pos: Vector3) -> VehicleSeat:
	var s = VehicleSeat.new()
	s.name = "Seat_%d" % index
	s.seat_index = index
	s.seat_name = s_name
	s.seat_type = s_type
	s.position = pos

	var exit_marker = Marker3D.new()
	exit_marker.name = "ExitPoint"
	exit_marker.position = exit_pos - pos
	s.add_child(exit_marker)
	s.exit_point = exit_marker

	parent.add_child(s)
	_internal_seats.append(s)

	# Mantener compatibilidad con markers y mocks
	seat_mounts.append(exit_marker)
	return s

func get_driver_seat() -> VehicleSeat:
	if is_route_vehicle:
		# En autobuses de ruta, el jugador NUNCA es conductor (es operado por la simulación)
		return null
	for s in seats:
		if s.is_driver():
			return s
	return null

func enter_vehicle(player: Node3D, preferred_type: int = 1) -> bool:
	var target_seat: VehicleSeat = null

	if is_route_vehicle:
		var passengers = get_available_passenger_seats()
		if not passengers.is_empty():
			target_seat = passengers[0]
	else:
		if preferred_type == VehicleSeat.SeatType.DRIVER:
			var d = get_driver_seat()
			if d and not d.is_occupied():
				target_seat = d
			else:
				var passengers = get_available_passenger_seats()
				if not passengers.is_empty():
					target_seat = passengers[0]
		else:
			var passengers = get_available_passenger_seats()
			if not passengers.is_empty():
				target_seat = passengers[0]

	if not target_seat:
		return false

	if target_seat.occupy(player):
		vehicle_entered.emit(player, target_seat)
		var net_client = _find_network_client()
		if net_client and net_client.state == NetworkClient.ConnectionState.CONNECTED:
			net_client.send_vehicle_enter(vehicle_id, target_seat.seat_index, target_seat.is_driver())
		return true

	return false

func exit_vehicle(player: Node3D) -> bool:
	for s in seats:
		if s.occupant == player:
			var seat_idx = s.seat_index
			s.vacate()
			vehicle_exited.emit(player, s)
			var net_client = _find_network_client()
			if net_client and net_client.state == NetworkClient.ConnectionState.CONNECTED:
				net_client.send_vehicle_exit(vehicle_id, seat_idx)
			return true
	return false

func _find_network_client() -> NetworkClient:
	var root = get_tree().root if is_inside_tree() else null
	if root:
		return root.find_child("NetworkClient", true, false) as NetworkClient
	return null

func push_snapshot_record(rec: TKTCodec.EntityRecord, server_time_ms: int) -> void:
	var snap = {
		"time": float(server_time_ms) / 1000.0,
		"position": rec.position,
		"yaw": rec.yaw,
		"pitch": rec.pitch,
		"velocity": rec.velocity,
		"flags": rec.flags
	}
	snapshot_history.append(snap)
	if snapshot_history.size() > 30:
		snapshot_history.pop_front()

func mount_passenger(player_id: int, seat_index: int, passenger_node: Node3D) -> void:
	if not is_instance_valid(passenger_node):
		return
	if seat_index < 0 or seat_index >= seats.size():
		seat_index = 0

	var seat_node = seats[seat_index]
	if passenger_node.get_parent():
		passenger_node.get_parent().remove_child(passenger_node)
	seat_node.add_child(passenger_node)
	passenger_node.position = Vector3.ZERO
	passenger_node.rotation = Vector3.ZERO
	seated_passengers[player_id] = passenger_node

func unmount_passenger(player_id: int) -> Node3D:
	var p_node: Node3D = seated_passengers.get(player_id)
	if p_node:
		if p_node.get_parent():
			p_node.get_parent().remove_child(p_node)
		seated_passengers.erase(player_id)
	return p_node

func _physics_process(delta: float) -> void:
	if snapshot_history.is_empty():
		return

	if snapshot_history.size() == 1:
		_set_pos(snapshot_history[0]["position"])
		rotation.y = deg_to_rad(-snapshot_history[0]["yaw"])
		rotation.x = deg_to_rad(snapshot_history[0]["pitch"])
		current_velocity = snapshot_history[0]["velocity"]
	else:
		var render_time = (Time.get_ticks_msec() / 1000.0) - interpolation_delay
		var prev_idx = -1
		var next_idx = -1

		for i in range(snapshot_history.size() - 1):
			if snapshot_history[i]["time"] <= render_time and snapshot_history[i + 1]["time"] >= render_time:
				prev_idx = i
				next_idx = i + 1
				break

		if prev_idx != -1 and next_idx != -1:
			var s0 = snapshot_history[prev_idx]
			var s1 = snapshot_history[next_idx]
			var span = max(0.0001, s1["time"] - s0["time"])
			var t = clampf((render_time - s0["time"]) / span, 0.0, 1.0)

			_set_pos(s0["position"].lerp(s1["position"], t))
			rotation.y = lerp_angle(deg_to_rad(-s0["yaw"]), deg_to_rad(-s1["yaw"]), t)
			rotation.x = lerp_angle(deg_to_rad(s0["pitch"]), deg_to_rad(s1["pitch"]), t)
			current_velocity = s0["velocity"].lerp(s1["velocity"], t)
		else:
			var latest = snapshot_history.back()
			var current_p = global_position if is_inside_tree() else position
			_set_pos(current_p.lerp(latest["position"], delta * 15.0))
			rotation.y = lerp_angle(rotation.y, deg_to_rad(-latest["yaw"]), delta * 15.0)
			rotation.x = lerp_angle(rotation.x, deg_to_rad(latest["pitch"]), delta * 15.0)
			current_velocity = latest["velocity"]

	# Telemetría de velocidad real
	current_speed_kmh = Vector2(current_velocity.x, current_velocity.z).length() * 3.6
	velocity = current_velocity

	# Animación procedural de giro de ruedas
	var forward_speed = current_velocity.length()
	wheel_rotation_angle += forward_speed * delta * 4.0
	for w in wheel_nodes:
		w.rotation.x = wheel_rotation_angle

func _set_pos(pos: Vector3) -> void:
	if is_inside_tree():
		global_position = pos
	else:
		position = pos
