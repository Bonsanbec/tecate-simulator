class_name EntityHealthDefaults
extends RefCounted

## Configuración Centralizada de Valores Predeterminados de Vida para Entidades
## Define los estándares numéricos de salud según el tipo de entidad en Tecate Simulator:
## - Jugadores y Peatones: 100 HP
## - Autobuses urbanos y pesados: 5000 HP
## - Automóviles y vehículos pequeños: 500 HP
## - Motocicletas: 250 HP
## - Camiones de carga: 3000 HP
## - Trenes y ferrocarril: 10000 HP
## - Elementos y objetos urbanos (props): 50 - 500 HP según escala

# Constantes de Salud Predeterminada por Tipo de Entidad
const HEALTH_PLAYER: float = 100.0
const HEALTH_CITIZEN: float = 100.0
const HEALTH_BUS: float = 5000.0
const HEALTH_CAR: float = 500.0
const HEALTH_MOTORCYCLE: float = 250.0
const HEALTH_TRUCK: float = 3000.0
const HEALTH_TRAIN: float = 10000.0

const HEALTH_PROP_SMALL: float = 50.0
const HEALTH_PROP_MEDIUM: float = 150.0
const HEALTH_PROP_LARGE: float = 500.0
const HEALTH_DEFAULT: float = 100.0

## Retorna el valor de salud predeterminado según el nombre del tipo de entidad
static func get_default_health_for_type(type_name: String) -> float:
	var key = type_name.to_upper().strip_edges()
	match key:
		"PLAYER", "JUGADOR", "CITIZEN", "CIUDADANO", "NPC", "HUMANOIDE":
			return HEALTH_PLAYER
		"BUS", "AUTOBUS", "AUTOBÚS", "BUS_HEAVY", "BUS_LIGHT", "ROUTE_BUS", "EL_HONGO":
			return HEALTH_BUS
		"CAR", "AUTOMOVIL", "AUTOMÓVIL", "AUTO", "SMALL_VEHICLE", "VEHICULO_PEQUENO":
			return HEALTH_CAR
		"MOTORCYCLE", "MOTOCICLETA", "MOTO":
			return HEALTH_MOTORCYCLE
		"TRUCK", "CAMION", "CAMIÓN":
			return HEALTH_TRUCK
		"TRAIN", "TREN", "FERROCARRIL":
			return HEALTH_TRAIN
		"PROP_SMALL", "OBJETO_PEQUENO":
			return HEALTH_PROP_SMALL
		"PROP_MEDIUM", "PROP", "OBJETO_MEDIANO", "NOMENCLATURA", "BOMBA_GASOLINERA":
			return HEALTH_PROP_MEDIUM
		"PROP_LARGE", "ESTRUCTURA", "OBJETO_GRANDE", "KIOSKO", "FUENTE":
			return HEALTH_PROP_LARGE
		_:
			return HEALTH_DEFAULT

## Retorna la salud predeterminada según el enum VehicleType de VehicleBase
static func get_default_health_for_vehicle_type(v_type: int) -> float:
	match v_type:
		0: # CAR
			return HEALTH_CAR
		1: # BUS_LIGHT
			return HEALTH_BUS
		2: # BUS_HEAVY
			return HEALTH_BUS
		3: # MOTORCYCLE
			return HEALTH_MOTORCYCLE
		4: # TRAIN
			return HEALTH_TRAIN
		5: # TRUCK
			return HEALTH_TRUCK
		_:
			return HEALTH_CAR

## Deduce y retorna la salud predeterminada de un nodo inspeccionando sus propiedades y grupos
static func get_default_health_for_entity(entity_node: Node) -> float:
	if not is_instance_valid(entity_node):
		return HEALTH_DEFAULT

	# 1. Si el nodo declara explícitamente un tipo de entidad o salud inicial
	if "default_health" in entity_node and entity_node.default_health > 0:
		return float(entity_node.default_health)

	if "entity_type_name" in entity_node and not str(entity_node.entity_type_name).is_empty():
		return get_default_health_for_type(str(entity_node.entity_type_name))

	# 2. Si es un vehículo (VehicleBase o derivado)
	if "vehicle_type" in entity_node:
		return get_default_health_for_vehicle_type(int(entity_node.vehicle_type))

	# 3. Si es un ciudadano o jugador (CitizenEntity / PlayerController / RemotePlayer / RemoteNPC)
	if entity_node.is_in_group("players") or entity_node.is_in_group("citizens") or "citizen_name" in entity_node:
		return HEALTH_PLAYER

	# 4. Si es un vehículo genérico en el grupo "vehicles"
	if entity_node.is_in_group("vehicles"):
		if "is_route_vehicle" in entity_node and entity_node.is_route_vehicle:
			return HEALTH_BUS
		return HEALTH_CAR

	# 5. Si es un objeto destructible
	if entity_node.is_in_group("destructible_props"):
		return HEALTH_PROP_MEDIUM

	return HEALTH_DEFAULT
