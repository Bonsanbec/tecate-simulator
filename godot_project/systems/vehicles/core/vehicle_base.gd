class_name VehicleBase
extends CharacterBody3D

## Clase Base Universal de Vehículos para Tecate Simulator
## Integra física cinemática de inercia y amortiguamiento, adaptación a pendientes
## topográficas de Tecate, sondeo multi-raycast de suspensión, perfilado de superficies,
## tanque de combustible y gestión modular de asientos de conductor y pasajeros.

const FuelSystemClass = preload("res://systems/vehicles/core/fuel_system.gd")
const SurfaceDetectorClass = preload("res://systems/vehicles/core/surface_detector.gd")
const VehicleSeatClass = preload("res://systems/vehicles/core/vehicle_seat.gd")
const SurfaceProfileClass = preload("res://systems/vehicles/core/surface_profile.gd")

signal vehicle_entered(player: Node3D, seat: VehicleSeatClass)
signal vehicle_exited(player: Node3D, seat: VehicleSeatClass)
signal engine_state_changed(is_running: bool)
signal lights_toggled(is_on: bool)
signal gear_changed(old_gear: int, new_gear: int)

enum VehicleType {
	CAR = 0,
	BUS_LIGHT = 1,
	BUS_HEAVY = 2,
	MOTORCYCLE = 3,
	TRAIN = 4,
	TRUCK = 5
}

@export_group("Identidad y Clasificación")
@export var vehicle_id: int = 1001
@export var vehicle_name: String = "Vehículo Genérico"
@export var vehicle_type: VehicleType = VehicleType.CAR

@export_group("Transmisión Mecánica")
@export var total_gears: int = 6
@export var gear_speeds_kmh: Array[float] = [0.0, 18.0, 32.0, 48.0, 68.0, 88.0, 115.0]
var current_gear: int = 1
var is_shifting: bool = false
var shift_timer: float = 0.0
var engine_rpm: float = 800.0


@export_group("Física y Rendimiento")
@export var mass_kg: float = 1400.0
@export var max_speed_kmh: float = 85.0
@export var reverse_max_speed_kmh: float = 24.0
@export var engine_acceleration: float = 7.5 # m/s^2
@export var brake_deceleration: float = 14.0  # m/s^2
@export var coasting_friction: float = 3.0   # Decaimiento pasivo
@export var max_steer_angle_deg: float = 32.0
@export var steer_speed: float = 6.0
@export var suspension_tilt_speed: float = 8.0 # Suavizado angular con el terreno

# Estado operativo interno
var engine_running: bool = false
var headlights_on: bool = false
var current_speed_kmh: float = 0.0
var current_steer_angle_deg: float = 0.0
var current_slope_angle: float = 0.0
var current_surface_profile: SurfaceProfileClass = null

# Componentes modulares
var _internal_fuel_system: FuelSystemClass = null
var fuel_system: FuelSystemClass:
	get:
		if _internal_fuel_system == null:
			_internal_fuel_system = get_node_or_null("FuelSystem") as FuelSystemClass
			if not _internal_fuel_system:
				_internal_fuel_system = FuelSystemClass.new()
				_internal_fuel_system.name = "FuelSystem"
				add_child(_internal_fuel_system)
			if not _internal_fuel_system.out_of_fuel.is_connected(_on_out_of_fuel):
				_internal_fuel_system.out_of_fuel.connect(_on_out_of_fuel)
		return _internal_fuel_system
	set(val):
		_internal_fuel_system = val

var surface_detector: SurfaceDetectorClass

var _internal_seats: Array = []
var seats: Array:
	get:
		if _internal_seats.is_empty():
			_discover_seats()
		return _internal_seats
	set(val):
		_internal_seats = val

# Raycasts de suspensión en las esquinas/ruedas
var _internal_suspension_rays: Array[RayCast3D] = []
var suspension_rays: Array[RayCast3D]:
	get:
		if _internal_suspension_rays.is_empty():
			_discover_suspension_rays()
		return _internal_suspension_rays
	set(val):
		_internal_suspension_rays = val

# Puertas de abordaje y descenso
var _internal_doors: Array[Marker3D] = []
var doors: Array[Marker3D]:
	get:
		if _internal_doors.is_empty():
			_discover_doors()
		return _internal_doors
	set(val):
		_internal_doors = val

# Nodos de iluminación opcionales
var headlights_root: Node3D = null
var taillights_root: Node3D = null

# Gravedad del proyecto
var default_gravity: float = ProjectSettings.get_setting("physics/3d/default_gravity", 9.8)

func _ready() -> void:
	add_to_group("vehicles")
	var _fs = fuel_system # Dispara inicialización
	_discover_doors()
	_discover_seats()
	_discover_suspension_rays()
	_discover_lights()

func _initialize_components() -> void:
	var _fs = fuel_system
	surface_detector = get_node_or_null("SurfaceDetector") as SurfaceDetectorClass
	if not surface_detector:
		surface_detector = SurfaceDetectorClass.new()
		surface_detector.name = "SurfaceDetector"
		add_child(surface_detector)
	current_surface_profile = SurfaceProfileClass.create_default(SurfaceProfileClass.SurfaceType.ASPHALT)

func _discover_doors() -> void:
	_internal_doors.clear()
	var doors_container = get_node_or_null("Doors")
	if doors_container:
		for child in doors_container.get_children():
			if child is Marker3D:
				_internal_doors.append(child as Marker3D)
	if _internal_doors.is_empty():
		for child in find_children("Door_*", "Marker3D", true, false):
			_internal_doors.append(child as Marker3D)

## Retorna la puerta de abordaje más cercana a una posición global dada
func get_closest_boarding_door(pos: Vector3) -> Marker3D:
	if doors.is_empty():
		_discover_doors()
	if doors.is_empty():
		return null
	var closest: Marker3D = null
	var min_d_sq = INF
	for d in doors:
		var d_sq = pos.distance_squared_to(d.global_position)
		if d_sq < min_d_sq:
			min_d_sq = d_sq
			closest = d
	return closest

## Verifica si una posición (jugador a pie) se encuentra cerca de una puerta de acceso
func is_near_boarding_door(pos: Vector3, max_dist: float = 2.2) -> bool:
	if doors.is_empty():
		_discover_doors()
	if doors.is_empty():
		# Fallback para automóviles genéricos sin puertas marcadas: zona lateral derecha/izquierda
		var local_p = to_local(pos)
		return absf(local_p.x) >= 0.8 and absf(local_p.x) <= 2.2 and absf(local_p.z) <= 2.8
	var d = get_closest_boarding_door(pos)
	return d != null and pos.distance_to(d.global_position) <= max_dist

## Retorna la posición global del pasillo interior tras abordar por la puerta
func get_interior_entry_position() -> Vector3:
	var entry_node = get_node_or_null("Doors/Interior_Entry") as Marker3D
	if entry_node:
		return entry_node.global_position
	# Fallback: frente al acceso delantero sobre el piso (Y=0.82)
	return to_global(Vector3(0.0, 0.82, -3.2))

## Retorna la posición global de descenso seguro en la banqueta exterior
func get_exterior_exit_position() -> Vector3:
	var exit_node = get_node_or_null("Doors/Exterior_Exit") as Marker3D
	if exit_node:
		return exit_node.global_position
	var d = get_closest_boarding_door(global_position)
	if d:
		return d.global_position + (global_transform.basis.x * 0.8)
	return global_position + (global_transform.basis.x * 2.0)

func _discover_seats() -> void:
	_internal_seats.clear()
	var seats_container = get_node_or_null("Seats")
	if seats_container:
		for child in seats_container.get_children():
			_internal_seats.append(child)
	else:
		for child in get_children():
			if "seat_type" in child or child.has_method("is_occupied"):
				_internal_seats.append(child)

func _discover_suspension_rays() -> void:
	_internal_suspension_rays.clear()
	var rays_container = get_node_or_null("Suspension")
	if rays_container:
		for child in rays_container.get_children():
			if child is RayCast3D:
				_internal_suspension_rays.append(child)
	else:
		for child in find_children("Ray_*", "RayCast3D", true, false):
			_internal_suspension_rays.append(child as RayCast3D)

	if _internal_suspension_rays.is_empty():
		_generate_default_suspension_rays()

func _generate_default_suspension_rays() -> void:
	var positions = [
		Vector3(-0.85, 0.5, -1.3),
		Vector3(0.85, 0.5, -1.3),
		Vector3(-0.85, 0.5, 1.3),
		Vector3(0.85, 0.5, 1.3)
	]
	var susp_node = Node3D.new()
	susp_node.name = "AutoSuspension"
	add_child(susp_node)

	for i in range(positions.size()):
		var rc = RayCast3D.new()
		rc.name = "Ray_Auto_%d" % i
		rc.position = positions[i]
		rc.target_position = Vector3(0, -1.8, 0)
		rc.enabled = true
		rc.collision_mask = 1
		susp_node.add_child(rc)
		suspension_rays.append(rc)

## Retorna el asiento de conductor principal si existe
func get_driver_seat() -> VehicleSeatClass:
	if seats.is_empty():
		_discover_seats()
	for s in seats:
		if s.seat_type == VehicleSeatClass.SeatType.DRIVER:
			return s
	return null

## Retorna lista de asientos de pasajero disponibles
func get_available_passenger_seats() -> Array[VehicleSeatClass]:
	if seats.is_empty():
		_discover_seats()
	var result: Array[VehicleSeatClass] = []
	for s in seats:
		if s.seat_type == VehicleSeatClass.SeatType.PASSENGER and not s.is_occupied():
			result.append(s)
	return result

func _discover_lights() -> void:
	headlights_root = get_node_or_null("Lights/Headlights") as Node3D
	taillights_root = get_node_or_null("Lights/Taillights") as Node3D
	_update_lights_visual()

## Alterna el encendido de los faros
func toggle_headlights() -> void:
	headlights_on = not headlights_on
	_update_lights_visual()
	lights_toggled.emit(headlights_on)

func _update_lights_visual() -> void:
	if headlights_root:
		headlights_root.visible = headlights_on

## Verifica si el vehículo tiene conductor activo
func has_driver() -> bool:
	var d_seat = get_driver_seat()
	return d_seat != null and d_seat.is_occupied()

## Permite abordar el vehículo al jugador en un asiento específico o en el primer disponible
func enter_vehicle(player: Node3D, preferred_type: int = 0) -> bool:
	var target_seat: VehicleSeatClass = null

	if preferred_type == VehicleSeatClass.SeatType.DRIVER:
		var d = get_driver_seat()
		if d and not d.is_occupied():
			target_seat = d
		else:
			# Si conductor está ocupado, buscar plaza de pasajero
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
		if target_seat.is_driver():
			engine_running = not fuel_system.is_empty
			engine_state_changed.emit(engine_running)
		vehicle_entered.emit(player, target_seat)
		return true

	return false

## Permite descender del vehículo
func exit_vehicle(player: Node3D) -> bool:
	for s in seats:
		if s.occupant == player:
			s.vacate()
			if s.is_driver():
				# Si el conductor desciende y el vehículo se detiene, apagar motor
				if current_speed_kmh < 2.0:
					engine_running = false
					engine_state_changed.emit(false)
			vehicle_exited.emit(player, s)
			return true
	vehicle_exited.emit(player, null)
	return true

## Física de adaptación topográfica e inclinación con el terreno de Tecate
func process_terrain_alignment(delta: float) -> Vector3:
	var ground_normal_sum = Vector3.ZERO
	var contact_count = 0

	for ray in suspension_rays:
		if ray.is_colliding():
			ground_normal_sum += ray.get_collision_normal()
			contact_count += 1

	var avg_normal = Vector3.UP
	if contact_count > 0:
		avg_normal = (ground_normal_sum / float(contact_count)).normalized()
	elif is_on_floor():
		avg_normal = get_floor_normal()

	# 1. Medición de pendiente
	var slope_cos = clampf(avg_normal.dot(Vector3.UP), -1.0, 1.0)
	current_slope_angle = rad_to_deg(acos(slope_cos))

	# 2. Alineación del chasis con la pendiente (Pitch y Roll)
	var forward = -global_transform.basis.z
	var projected_forward = (forward - avg_normal * forward.dot(avg_normal)).normalized()
	if projected_forward.length_squared() > 0.001:
		var target_right = projected_forward.cross(avg_normal).normalized()
		var target_basis = Basis(target_right, avg_normal, -projected_forward)
		var current_quat = global_transform.basis.get_rotation_quaternion()
		var target_quat = target_basis.get_rotation_quaternion()
		var smoothed_quat = current_quat.slerp(target_quat, clampf(suspension_tilt_speed * delta, 0.0, 1.0))
		global_transform.basis = Basis(smoothed_quat)

	return avg_normal

## Actualiza la superficie y calcula los modificadores de rodadura
func update_surface_profile() -> SurfaceProfileClass:
	if surface_detector:
		current_surface_profile = surface_detector.update_surface_detection()
	else:
		current_surface_profile = SurfaceProfileClass.create_default(SurfaceProfileClass.SurfaceType.ASPHALT)
	return current_surface_profile

func _on_out_of_fuel() -> void:
	engine_running = false
	engine_state_changed.emit(false)
	print("[VehicleBase] '%s' se quedó sin combustible. Motor apagado." % vehicle_name)

## Retorna la nomenclatura de la marcha actual ("1ª", "2ª", ..., "6ª", "R", "N")
func get_gear_name() -> String:
	if current_gear == 0:
		return "R"
	elif current_gear < 0:
		return "N"
	return "%dª" % current_gear

## Actualiza la transmisión escalonada de marchas y el régimen de RPM
func update_transmission(speed_kmh: float, delta: float) -> void:
	if shift_timer > 0.0:
		shift_timer -= delta
		if shift_timer <= 0.0:
			is_shifting = false

	# Determinar marcha óptima según la velocidad con histéresis de reducción
	var target_gear = 1
	for g in range(total_gears, 0, -1):
		var threshold = gear_speeds_kmh[g - 1]
		# Margen de histéresis: si se reduce, exigir caer por debajo del umbral con tolerancia
		if g < current_gear:
			threshold -= 2.0
		if speed_kmh >= threshold:
			target_gear = g
			break

	target_gear = clampi(target_gear, 1, total_gears)
	if target_gear != current_gear and not is_shifting:
		var old_gear = current_gear
		current_gear = target_gear
		is_shifting = true
		shift_timer = 0.18 # 180ms de transición suave
		gear_changed.emit(old_gear, current_gear)

	# Simular RPM de motor pesado diésel (850 a 2350 RPM)
	var min_g_spd = gear_speeds_kmh[current_gear - 1]
	var max_g_spd = gear_speeds_kmh[current_gear]
	var ratio = clampf((speed_kmh - min_g_spd) / maxf(1.0, max_g_spd - min_g_spd), 0.0, 1.0)
	if is_shifting:
		engine_rpm = move_toward(engine_rpm, 950.0, 3200.0 * delta)
	else:
		engine_rpm = lerpf(1050.0, 2350.0, ratio)
