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

## Índices de waypoints que corresponden a paradas obligatorias con su nombre
@export var station_indices: Dictionary = {} # int -> String (ej: { 2: "Parada Parque Hidalgo", 6: "Parada Presidencia" })

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

func _physics_process(delta: float) -> void:
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

	# Reducir velocidad si la curva es cerrada
	var speed_curve_factor = clampf(current_forward.dot(desired_heading), 0.35, 1.0)
	var effective_max = (cruise_speed_kmh / 3.6) * speed_curve_factor * (surf_profile.max_speed_factor if surf_profile else 1.0)

	# Desaceleración previa si nos aproximamos a una parada
	if station_indices.has(current_waypoint_index) and dist_to_target < 15.0:
		effective_max = minf(effective_max, maxf(1.5, dist_to_target * 0.35))

	var current_h_speed = velocity.dot(current_forward)
	var new_speed = move_toward(current_h_speed, effective_max, engine_acceleration * 0.6 * delta)

	velocity.x = current_forward.x * new_speed
	velocity.z = current_forward.z * new_speed

	# Gravedad
	if not is_on_floor():
		velocity.y -= default_gravity * delta
	else:
		if velocity.y < 0.0:
			velocity.y = 0.0

	move_and_slide()
	current_speed_kmh = Vector2(velocity.x, velocity.z).length() * 3.6

func _on_waypoint_reached() -> void:
	if station_indices.has(current_waypoint_index):
		is_at_station = true
		_station_timer = 0.0
		var st_name = station_indices[current_waypoint_index]
		route_station_arrived.emit(st_name, station_dwell_time)
		print("[RouteVehicle] '%s' llegó a parada: %s (Espera: %.1f s)" % [vehicle_name, st_name, station_dwell_time])
	else:
		_advance_waypoint()

func _process_station_dwell(delta: float) -> void:
	_station_timer += delta
	if _station_timer >= station_dwell_time:
		is_at_station = false
		var st_name = station_indices.get(current_waypoint_index, "Parada")
		route_station_departed.emit(st_name)
		print("[RouteVehicle] '%s' reanuda marcha desde %s" % [vehicle_name, st_name])
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
