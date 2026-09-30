class_name RemoteVehicle
extends Node3D

## Representación visual y cinemática interpolada de un vehículo remoto o ruta autónoma en Tecate Simulator.
## Interpolará posición, orientación topográfica (yaw, pitch, roll) y velocidad desde snapshots TKT/1.
## Soporta anclaje de pasajeros y conductores remotos.

@export var interpolation_delay: float = 0.10 # 100 ms de búfer de interpolación

var entity_id: int = 0
var is_route_vehicle: bool = false
var snapshot_history: Array[Dictionary] = []
var current_velocity: Vector3 = Vector3.ZERO
var wheel_rotation_angle: float = 0.0

# Nodos visuales
var vehicle_mesh_root: Node3D
var nameplate_label: Label3D
var seat_mounts: Array[Marker3D] = []
var seated_passengers: Dictionary = {} # player_id -> Node3D (RemotePlayer)
var wheel_nodes: Array[Node3D] = []

func setup(id: int, is_route: bool = false) -> void:
	entity_id = id
	is_route_vehicle = is_route
	name = "RemoteVehicle_%d" % id

	_create_nameplate()
	_create_visuals()
	_create_seat_mounts()

func _create_nameplate() -> void:
	nameplate_label = Label3D.new()
	nameplate_label.name = "Nameplate"
	nameplate_label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	nameplate_label.position = Vector3(0, 2.6, 0)
	nameplate_label.pixel_size = 0.005
	nameplate_label.text = ("Autobús de Ruta #%d" if is_route_vehicle else "Vehículo #%d") % entity_id
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
	# Carrocería
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

	# Cabina / Parabrisas
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

	# Ruedas procedimentales
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
		# Respaldo si no estuviera disponible el recurso GLB
		var body = MeshInstance3D.new()
		var box = BoxMesh.new()
		box.size = Vector3(2.6, 2.8, 8.5)
		var mat = StandardMaterial3D.new()
		mat.albedo_color = Color(0.85, 0.2, 0.15, 1.0) # Rojo Transporte
		mat.roughness = 0.5
		body.mesh = box
		body.material_override = mat
		body.position = Vector3(0, 1.6, 0)
		vehicle_mesh_root.add_child(body)

	# 6 ruedas de autobús para cinemática procedural de rotación
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

func _create_seat_mounts() -> void:
	if is_route_vehicle:
		# Asiento 0: Puesto del conductor
		_add_seat_marker(Vector3(-0.75, 1.25, 3.65))

		# Asientos 1..30 reglamentarios de pasajeros (8 filas dobles y bancada trasera)
		var z_rows_left = [2.75, 1.85, 0.95, 0.05, -0.85, -1.75, -2.65]
		for z in z_rows_left:
			_add_seat_marker(Vector3(-1.0, 1.25, z))   # Ventanilla Izq
			_add_seat_marker(Vector3(-0.55, 1.25, z))  # Pasillo Izq

		var z_rows_right = [1.85, 0.95, 0.05, -0.85, -1.75, -2.65]
		for z in z_rows_right:
			_add_seat_marker(Vector3(0.55, 1.25, z))   # Pasillo Der
			_add_seat_marker(Vector3(1.0, 1.25, z))    # Ventanilla Der

		# Fila trasera (4 plazas)
		for x in [-0.9, -0.3, 0.3, 0.9]:
			_add_seat_marker(Vector3(x, 1.25, -3.55))
	else:
		# Conductor + Copiloto + 2 traseros
		_add_seat_marker(Vector3(-0.45, 0.7, 0.1))  # Conductor
		_add_seat_marker(Vector3(0.45, 0.7, 0.1))   # Copiloto
		_add_seat_marker(Vector3(-0.45, 0.7, -0.9)) # Pasajero Izq
		_add_seat_marker(Vector3(0.45, 0.7, -0.9))  # Pasajero Der

func _add_seat_marker(pos: Vector3) -> void:
	var m = Marker3D.new()
	m.name = "SeatMount_%d" % seat_mounts.size()
	m.position = pos
	add_child(m)
	seat_mounts.append(m)

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
	if seat_index < 0 or seat_index >= seat_mounts.size():
		seat_index = 0

	var marker = seat_mounts[seat_index]
	if passenger_node.get_parent():
		passenger_node.get_parent().remove_child(passenger_node)
	marker.add_child(passenger_node)
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
	if snapshot_history.size() < 2:
		if snapshot_history.size() == 1:
			_set_pos(snapshot_history[0]["position"])
			rotation.y = deg_to_rad(snapshot_history[0]["yaw"])
			rotation.x = deg_to_rad(snapshot_history[0]["pitch"])
		return

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
		var target_yaw = lerp_angle(deg_to_rad(s0["yaw"]), deg_to_rad(s1["yaw"]), t)
		var target_pitch = lerp_angle(deg_to_rad(s0["pitch"]), deg_to_rad(s1["pitch"]), t)
		rotation.y = target_yaw
		rotation.x = target_pitch

		current_velocity = s0["velocity"].lerp(s1["velocity"], t)
	else:
		var latest = snapshot_history.back()
		var current_p = global_position if is_inside_tree() else position
		_set_pos(current_p.lerp(latest["position"], delta * 15.0))
		rotation.y = lerp_angle(rotation.y, deg_to_rad(latest["yaw"]), delta * 15.0)
		rotation.x = lerp_angle(rotation.x, deg_to_rad(latest["pitch"]), delta * 15.0)
		current_velocity = latest["velocity"]

	# Animación procedural de giro de ruedas según velocidad
	var forward_speed = current_velocity.length()
	wheel_rotation_angle += forward_speed * delta * 4.0
	for w in wheel_nodes:
		w.rotation.x = wheel_rotation_angle

func _set_pos(pos: Vector3) -> void:
	if is_inside_tree():
		global_position = pos
	else:
		position = pos

