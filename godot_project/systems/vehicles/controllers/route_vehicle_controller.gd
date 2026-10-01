class_name RouteVehicle
extends "res://systems/vehicles/core/vehicle_base.gd"

## Controlador para Vehículos de Ruta Predefinida (Autónomos / Transporte Público / Trenes)
## Sigue un circuito programado de waypoints, realiza paradas temporizadas en estaciones,
## garantiza combustible infinito por contrato y solo admite al jugador como Pasajero.

signal route_station_arrived(station_name: String, dwell_time: float)
signal route_station_departed(station_name: String)

@export var cruise_speed_kmh: float = 38.0
@export var station_dwell_time: float = 6.0
@export var waypoint_reach_threshold: float = 3.5 # Distancia para considerar waypoint alcanzado
@export var loop_route: bool = true

## Lista de waypoints en coordenadas globales
@export var waypoints: PackedVector3Array = PackedVector3Array()

## Velocidades crucero asignadas por waypoint en km/h (si está poblado, anula a cruise_speed_kmh)
@export var waypoint_speeds: PackedFloat32Array = PackedFloat32Array()

## Índices de waypoints que corresponden a paradas obligatorias con su nombre o diccionario {name, dwell_time}
@export var station_indices: Dictionary = {} # int -> String | Dictionary

@export var current_waypoint_index: int = 0
var is_at_station: bool = false
var _station_timer: float = 0.0
var _target_speed: float = 0.0

func _ready() -> void:
	super._ready()
	# Contrato: Vehículos de ruta predefinida tienen combustible infinito garantizado
	if fuel_system:
		fuel_system.is_infinite_fuel = true
		fuel_system.current_liters = fuel_system.capacity_liters

	engine_running = true
	headlights_on = true
	_update_lights_visual()

	_target_speed = cruise_speed_kmh / 3.6

	# Alinear orientación inicial hacia el siguiente waypoint de la ruta
	if not waypoints.is_empty() and current_waypoint_index < waypoints.size():
		var next_idx = (current_waypoint_index + 1) % waypoints.size()
		var target_pt = waypoints[next_idx]
		var forward_dir = (target_pt - global_position)
		forward_dir.y = 0.0
		if forward_dir.length_squared() > 0.01:
			look_at(global_position + forward_dir.normalized(), Vector3.UP)

## Sobrescribe la entrada al vehículo para forzar siempre plaza de pasajero
func enter_vehicle(player: Node3D, _preferred_type: int = 1) -> bool:
	# En vehículos de ruta, el jugador NUNCA puede asumir el rol de conductor
	var passengers = get_available_passenger_seats()
	if passengers.is_empty():
		return false

	var target_seat = passengers[0]
	if target_seat.occupy(player):
		vehicle_entered.emit(player, target_seat)
		return true

	return false

func _has_any_passenger() -> bool:
	for s in seats:
		if s and s.has_method("is_occupied") and s.is_occupied():
			return true
	return false

func _physics_process(delta: float) -> void:
	# Optimización LOD / Distance Culling:
	# Si el autobús está a más de 220 metros y no lleva al jugador, usar cinemática ligera
	# evitando 4 raycasts continuos de suspensión y colisiones en cada tick de física.
	var cam = get_viewport().get_camera_3d() if get_viewport() else null
	var is_far_away = cam != null and cam.global_position.distance_squared_to(global_position) > (220.0 * 220.0)
	if is_far_away and not _has_any_passenger():
		_process_distant_kinematics(delta)
		return

	# 1. Adaptación continua a la topografía e inclinación del terreno de Tecate
	var avg_normal = process_terrain_alignment(delta)

	# 2. Perfil de superficie actual
	var surf_profile = update_surface_profile()

	# 3. Lógica de paradas en estación
	if is_at_station:
		_process_station_dwell(delta)
		velocity.x = move_toward(velocity.x, 0.0, brake_deceleration * delta)
		velocity.z = move_toward(velocity.z, 0.0, brake_deceleration * delta)
		move_and_slide()
		current_speed_kmh = Vector2(velocity.x, velocity.z).length() * 3.6
		return

	# 4. Navegación hacia el waypoint actual
	if waypoints.is_empty():
		return

	var target_pt = waypoints[current_waypoint_index]
	var to_target = target_pt - global_position
	to_target.y = 0.0 # Proyección horizontal
	var dist_to_target = to_target.length()

	# Comprobar si se alcanzó el waypoint actual
	if dist_to_target <= waypoint_reach_threshold:
		_on_waypoint_reached()
		return

	# Giro suave hacia el waypoint
	var desired_heading = to_target.normalized()
	var current_forward = -global_transform.basis.z
	var angle_diff = current_forward.signed_angle_to(desired_heading, Vector3.UP)
	var max_yaw_delta = deg_to_rad(45.0) * delta
	rotate_y(clampf(angle_diff, -max_yaw_delta, max_yaw_delta))

	# Reducir velocidad si la curva es cerrada y usar velocidad de tramo si existe
	var current_cruise_kmh = cruise_speed_kmh
	if not waypoint_speeds.is_empty() and current_waypoint_index < waypoint_speeds.size():
		current_cruise_kmh = waypoint_speeds[current_waypoint_index]

	var speed_curve_factor = clampf(current_forward.dot(desired_heading), 0.35, 1.0)
	var effective_max = (current_cruise_kmh / 3.6) * speed_curve_factor * (surf_profile.max_speed_factor if surf_profile else 1.0)

	# Desaceleración previa si nos aproximamos a una parada
	if station_indices.has(current_waypoint_index) and dist_to_target < 15.0:
		effective_max = minf(effective_max, maxf(1.5, dist_to_target * 0.35))

	var current_h_speed = velocity.dot(current_forward)
	var new_speed = move_toward(current_h_speed, effective_max, engine_acceleration * 0.6 * delta)

	velocity.x = current_forward.x * new_speed
	velocity.z = current_forward.z * new_speed

	# Adaptación vertical suave hacia la cota de calzada de la ruta (evita caer a través del asfalto hacia tinMesh)
	var target_y = target_pt.y
	var y_error = target_y - global_position.y
	velocity.y = move_toward(velocity.y, clampf(y_error * 8.0, -15.0, 15.0), 35.0 * delta)

	move_and_slide()
	current_speed_kmh = Vector2(velocity.x, velocity.z).length() * 3.6

func _get_station_info(wp_idx: int) -> Dictionary:
	if not station_indices.has(wp_idx):
		return {"name": "Parada", "dwell_time": station_dwell_time}
	var val = station_indices[wp_idx]
	if val is Dictionary:
		return {
			"name": str(val.get("name", "Parada")),
			"dwell_time": float(val.get("dwell_time", station_dwell_time))
		}
	return {"name": str(val), "dwell_time": station_dwell_time}

func _on_waypoint_reached() -> void:
	if station_indices.has(current_waypoint_index):
		is_at_station = true
		_station_timer = 0.0
		var info = _get_station_info(current_waypoint_index)
		route_station_arrived.emit(info["name"], info["dwell_time"])
		print("[RouteVehicle] '%s' llegó a parada: %s (Espera: %.1f s)" % [vehicle_name, info["name"], info["dwell_time"]])
	else:
		_advance_waypoint()

func _process_station_dwell(delta: float) -> void:
	_station_timer += delta
	var info = _get_station_info(current_waypoint_index)
	if _station_timer >= info["dwell_time"]:
		is_at_station = false
		route_station_departed.emit(info["name"])
		print("[RouteVehicle] '%s' reanuda marcha desde %s" % [vehicle_name, info["name"]])
		_advance_waypoint()

func _advance_waypoint() -> void:
	if waypoints.is_empty():
		return
	current_waypoint_index += 1
	if current_waypoint_index >= waypoints.size():
		if loop_route:
			current_waypoint_index = 0
		else:
			current_waypoint_index = waypoints.size() - 1
			engine_running = false

func _process_distant_kinematics(delta: float) -> void:
	if is_at_station:
		_process_station_dwell(delta)
		velocity = Vector3.ZERO
		current_speed_kmh = 0.0
		return

	if waypoints.is_empty():
		return

	var target_pt = waypoints[current_waypoint_index]
	var to_target = target_pt - global_position
	var dist_h = Vector2(to_target.x, to_target.z).length()

	if dist_h <= waypoint_reach_threshold:
		_on_waypoint_reached()
		return

	var current_cruise = cruise_speed_kmh
	if not waypoint_speeds.is_empty() and current_waypoint_index < waypoint_speeds.size():
		current_cruise = waypoint_speeds[current_waypoint_index]

	var desired_speed = current_cruise / 3.6
	var step_dist = desired_speed * delta

	if dist_h > 0.001:
		var dir_h = Vector3(to_target.x, 0.0, to_target.z).normalized()
		global_position.x += dir_h.x * minf(step_dist, dist_h)
		global_position.z += dir_h.z * minf(step_dist, dist_h)
		global_position.y = move_toward(global_position.y, target_pt.y + 0.1, 5.0 * delta)
		look_at(global_position + dir_h, Vector3.UP)

	current_speed_kmh = current_cruise
