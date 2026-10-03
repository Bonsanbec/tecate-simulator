class_name RouteVehicle
extends "res://systems/vehicles/core/vehicle_base.gd"

## Controlador Avanzado para Vehículos de Ruta Predefinida (Autobuses / Transporte Suburbano)
## Integra física de suspensión por raycast continuo sin rebotes, transmisión de 6 marchas,
## aceleración progresiva de carretera calculada por curvatura física continua,
## y paradas en cruces con debounce de 5 minutos y timbre de descenso.

signal route_station_arrived(station_name: String, dwell_time: float)
signal route_station_departed(station_name: String)
signal crossing_stop_arrived(crossing_name: String, dwell_time: float)
signal crossing_stop_departed(crossing_name: String)
signal stop_requested_acknowledged()

const ROUTE_DATA_PATH := "res://assets/vehicles/bus_hongo_route.json"
const WHEEL_RADIUS: float = 0.50

@export_group("Navegación y Velocidad")
@export var cruise_speed_kmh: float = 38.0
@export var station_dwell_time: float = 6.0
@export var waypoint_reach_threshold: float = 4.0
@export var loop_route: bool = true

## Lista de waypoints en coordenadas globales
@export var waypoints: PackedVector3Array = PackedVector3Array()

## Velocidades crucero asignadas por waypoint en km/h
@export var waypoint_speeds: PackedFloat32Array = PackedFloat32Array()

## Estaciones y paradas fijas programadas: int (índice wp) -> String o Dict
@export var station_indices: Dictionary = {}

## Cruces e intersecciones viales: int o str (índice wp) -> Dict con {name, streets}
@export var intersections: Dictionary = {}

@export_group("Paradas en Cruces (Debounce)")
@export var crossing_debounce_sec: float = 300.0 ## 5 minutos entre paradas de cruce
@export var crossing_dwell_time: float = 15.0    ## Tiempo de espera para ascenso/descenso
var time_since_last_stop: float = 300.0
var is_at_crossing: bool = false
var _crossing_timer: float = 0.0
var stop_requested: bool = false
var _active_crossing_name: String = ""

@export_group("Estado Operativo")
@export var current_waypoint_index: int = 0
var is_at_station: bool = false
var _station_timer: float = 0.0
var _target_speed: float = 0.0

# Dinámica de crucero y aceleración progresiva por tiempo
var steady_speed_timer: float = 0.0
var _wheel_rot_angle: float = 0.0

func _ready() -> void:
	super._ready()
	floor_snap_length = 0.4
	floor_constant_speed = true
	floor_stop_on_slope = true

	# Contrato: Vehículos de ruta predefinida tienen combustible infinito garantizado
	if fuel_system:
		fuel_system.is_infinite_fuel = true
		fuel_system.current_liters = fuel_system.capacity_liters

	engine_running = true
	headlights_on = true
	_update_lights_visual()

	_load_intersections_if_empty()
	_target_speed = cruise_speed_kmh / 3.6

	# Alinear orientación inicial hacia el siguiente waypoint de la ruta
	if not waypoints.is_empty() and current_waypoint_index < waypoints.size():
		var next_idx = (current_waypoint_index + 1) % waypoints.size()
		var target_pt = waypoints[next_idx]
		var forward_dir = (target_pt - global_position)
		forward_dir.y = 0.0
		if forward_dir.length_squared() > 0.01:
			look_at(global_position + forward_dir.normalized(), Vector3.UP)

func _load_intersections_if_empty() -> void:
	if not intersections.is_empty():
		return
	if not FileAccess.file_exists(ROUTE_DATA_PATH):
		return
	var file := FileAccess.open(ROUTE_DATA_PATH, FileAccess.READ)
	if not file:
		return
	var parsed = JSON.parse_string(file.get_as_text())
	file.close()
	if parsed is Dictionary and parsed.has("intersections"):
		intersections = parsed["intersections"]

## Solicita detención en el próximo cruce vial (timbre de parada)
func request_stop() -> void:
	stop_requested = true
	stop_requested_acknowledged.emit()
	print("[RouteVehicle] '%s': Timbre de bajada activado. Parada solicitada en próximo cruce." % vehicle_name)

## Sobrescribe la entrada al vehículo para forzar siempre plaza de pasajero
func enter_vehicle(player: Node3D, _preferred_type: int = 1) -> bool:
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
	var cam = get_viewport().get_camera_3d() if get_viewport() else null
	var is_far_away = cam != null and cam.global_position.distance_squared_to(global_position) > (220.0 * 220.0)
	if is_far_away and not _has_any_passenger():
		_process_distant_kinematics(delta)
		return

	time_since_last_stop += delta

	# 1. Adaptación continua a la topografía e inclinación del terreno de Tecate
	var avg_normal = process_terrain_alignment(delta)
	var surf_profile = update_surface_profile()

	# 2. Lógica de paradas en estación principal o terminal
	if is_at_station:
		_process_station_dwell(delta)
		velocity.x = move_toward(velocity.x, 0.0, brake_deceleration * delta)
		velocity.z = move_toward(velocity.z, 0.0, brake_deceleration * delta)
		_process_suspension_height(delta, global_position.y)
		move_and_slide()
		current_speed_kmh = Vector2(velocity.x, velocity.z).length() * 3.6
		update_transmission(current_speed_kmh, delta)
		return

	# 3. Lógica de paradas periódicas en cruces viales (debounce 5 min o timbre)
	if is_at_crossing:
		_process_crossing_dwell(delta)
		velocity.x = move_toward(velocity.x, 0.0, brake_deceleration * delta)
		velocity.z = move_toward(velocity.z, 0.0, brake_deceleration * delta)
		_process_suspension_height(delta, global_position.y)
		move_and_slide()
		current_speed_kmh = Vector2(velocity.x, velocity.z).length() * 3.6
		update_transmission(current_speed_kmh, delta)
		return

	if waypoints.is_empty():
		return

	var target_pt = waypoints[current_waypoint_index]
	var to_target = target_pt - global_position
	to_target.y = 0.0
	var dist_to_target = to_target.length()

	# Comprobar si se alcanzó el waypoint actual
	if dist_to_target <= waypoint_reach_threshold:
		_on_waypoint_reached()
		return

	# Giro suave hacia el waypoint
	var desired_heading = to_target.normalized()
	var current_forward = -global_transform.basis.z
	var angle_diff = current_forward.signed_angle_to(desired_heading, Vector3.UP)
	var max_yaw_delta = deg_to_rad(48.0) * delta
	rotate_y(clampf(angle_diff, -max_yaw_delta, max_yaw_delta))

	# 4. Cálculo de curvatura analítica continua y techo físico admisible (Fase 3 generalizada)
	var local_R = _get_path_curvature_radius()
	var a_lat_max = 3.0 # m/s^2 aceleración centrípeta máxima segura en curvas
	var v_curve_phys_max_kmh = minf(max_speed_kmh, sqrt(a_lat_max * local_R) * 3.6)

	# Velocidad base de tramo
	var base_cruise_kmh = cruise_speed_kmh
	if not waypoint_speeds.is_empty() and current_waypoint_index < waypoint_speeds.size():
		base_cruise_kmh = waypoint_speeds[current_waypoint_index]

	# 5. Aceleración Progresiva por Tiempo en Crucero Estable (Fase 3)
	if current_speed_kmh >= base_cruise_kmh * 0.82 and local_R > 90.0:
		steady_speed_timer += delta
	else:
		steady_speed_timer = maxf(0.0, steady_speed_timer - 3.5 * delta)

	# Factor de estiramiento progresivo en cualquier forma de tramo donde la geometría lo permita
	var speed_boost_factor = 1.0 + 0.25 * (1.0 - exp(-steady_speed_timer / 12.0))
	var boosted_cruise_kmh = minf(max_speed_kmh, base_cruise_kmh * speed_boost_factor)
	var effective_max_kmh = minf(v_curve_phys_max_kmh, boosted_cruise_kmh)

	var speed_curve_factor = clampf(current_forward.dot(desired_heading), 0.70, 1.0)
	var effective_max_ms = (effective_max_kmh / 3.6) * speed_curve_factor * (surf_profile.max_speed_factor if surf_profile else 1.0)

	# 6. Desaceleración suave ante paradas inminentes (estación o cruce programado)
	var is_approaching_stop = false
	if station_indices.has(current_waypoint_index):
		is_approaching_stop = true
	elif _is_wp_eligible_crossing(current_waypoint_index):
		is_approaching_stop = true

	if is_approaching_stop and dist_to_target < 22.0:
		effective_max_ms = minf(effective_max_ms, maxf(1.8, dist_to_target * 0.38))

	# 7. Modelo de Transmisión de 6 Marchas con micro-corte de embrague
	update_transmission(current_speed_kmh, delta)
	var current_h_speed = velocity.dot(current_forward)

	var accel_rate = engine_acceleration
	if is_shifting:
		accel_rate *= 0.50 # Transición suave durante cambio de marcha
	else:
		accel_rate *= lerpf(0.75, 1.10, float(current_gear) / float(total_gears))

	var new_speed: float
	if effective_max_ms < current_h_speed:
		var engine_brake = brake_deceleration * (0.45 + 0.1 * (total_gears - current_gear))
		new_speed = move_toward(current_h_speed, effective_max_ms, engine_brake * delta)
	else:
		new_speed = move_toward(current_h_speed, effective_max_ms, accel_rate * delta)

	velocity.x = current_forward.x * new_speed
	velocity.z = current_forward.z * new_speed

	# 8. Suspensión Firme con Adherencia Continua al Pavimento (Cero Rebotes)
	_process_suspension_height(delta, target_pt.y)

	move_and_slide()
	current_speed_kmh = Vector2(velocity.x, velocity.z).length() * 3.6

	# 9. Rotación Procedural de Ruedas por Distancia Avanzada
	var step_dist = Vector2(velocity.x, velocity.z).length() * delta
	_wheel_rot_angle += step_dist / WHEEL_RADIUS

## Seguimiento de rasante críticamente amortiguado con adherencia continua sobre el pavimento (cero rebotes)
func _process_suspension_height(delta: float, fallback_target_y: float) -> void:
	var ground_hits: Array[float] = []
	for ray in suspension_rays:
		if ray and ray.is_colliding():
			ground_hits.append(ray.get_collision_point().y)

	var target_ground_y: float = fallback_target_y
	if not ground_hits.is_empty():
		var sum_y: float = 0.0
		for gy in ground_hits:
			sum_y += gy
		target_ground_y = sum_y / float(ground_hits.size())

	# Seguimiento de rasante de primer orden críticamente amortiguado (cero overshoot, neumáticos asentados)
	var prev_y = global_position.y
	global_position.y = lerpf(global_position.y, target_ground_y, clampf(14.0 * delta, 0.0, 1.0))
	velocity.y = (global_position.y - prev_y) / maxf(0.0001, delta)
	velocity.y = clampf(velocity.y, -6.0, 6.0)

## Calcula el radio de curvatura local R a partir de los waypoints adelante en el plano XZ
func _get_path_curvature_radius() -> float:
	if waypoints.size() < 3:
		return 99999.0
	var idx1 = current_waypoint_index
	var idx2 = (idx1 + 1) % waypoints.size()
	var idx3 = (idx2 + 1) % waypoints.size()

	var p1 = waypoints[idx1]
	var p2 = waypoints[idx2]
	var p3 = waypoints[idx3]

	var v1 = Vector2(p2.x - p1.x, p2.z - p1.z)
	var v2 = Vector2(p3.x - p2.x, p3.z - p2.z)
	var d1 = v1.length()
	var d2 = v2.length()
	var chord = Vector2(p3.x - p1.x, p3.z - p1.z).length()

	if d1 < 0.1 or d2 < 0.1 or chord < 0.1:
		return 99999.0

	var dot = clampf(v1.dot(v2) / (d1 * d2), -1.0, 1.0)
	var angle = acos(dot)
	var sin_angle = sin(angle)
	if sin_angle < 0.001:
		return 99999.0

	return maxf(8.0, chord / (2.0 * sin_angle))

func _is_wp_eligible_crossing(wp_idx: int) -> bool:
	var key_int = wp_idx
	var key_str = str(wp_idx)
	if not intersections.has(key_int) and not intersections.has(key_str):
		return false
	return (time_since_last_stop >= crossing_debounce_sec) or stop_requested

func _get_crossing_name(wp_idx: int) -> String:
	var data = intersections.get(wp_idx, intersections.get(str(wp_idx), {}))
	if data is Dictionary and data.has("name"):
		return str(data["name"])
	return "Cruce Vial Km %.1f" % (float(wp_idx) * 0.08)

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
		time_since_last_stop = 0.0
		stop_requested = false
		var info = _get_station_info(current_waypoint_index)
		route_station_arrived.emit(info["name"], info["dwell_time"])
		print("[RouteVehicle] '%s' llegó a parada oficial: %s (Espera: %.1f s)" % [vehicle_name, info["name"], info["dwell_time"]])
	elif _is_wp_eligible_crossing(current_waypoint_index):
		is_at_crossing = true
		_crossing_timer = 0.0
		time_since_last_stop = 0.0
		stop_requested = false
		_active_crossing_name = _get_crossing_name(current_waypoint_index)
		crossing_stop_arrived.emit(_active_crossing_name, crossing_dwell_time)
		print("[RouteVehicle] '%s' parada en cruce (debounce 5 min): %s (Espera: %.1f s)" % [vehicle_name, _active_crossing_name, crossing_dwell_time])
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

func _process_crossing_dwell(delta: float) -> void:
	_crossing_timer += delta
	if _crossing_timer >= crossing_dwell_time:
		is_at_crossing = false
		crossing_stop_departed.emit(_active_crossing_name)
		print("[RouteVehicle] '%s' reanuda marcha desde cruce: %s" % [vehicle_name, _active_crossing_name])
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

	if is_at_crossing:
		_process_crossing_dwell(delta)
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
