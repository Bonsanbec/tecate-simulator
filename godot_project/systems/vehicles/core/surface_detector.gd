class_name SurfaceDetector
extends Node3D

## Detector Dinámico de Malla y Clasificador de Superficie para Vehículos
## Identifica el tipo de terreno (asfalto, concreto, grava, terreno virgen,
## agua o vía férrea) mediante sondeo por raycast vertical y consulta
## espacial a StreetNameLookup.

const SurfaceProfileClass = preload("res://systems/vehicles/core/surface_profile.gd")

signal surface_changed(new_profile: SurfaceProfileClass)

@export var ray_length: float = 3.0
@export var road_snap_distance: float = 8.0 # Metros de tolerancia para considerar calzada

var current_profile: SurfaceProfileClass = null
var _raycast: RayCast3D = null

func _ready() -> void:
	current_profile = SurfaceProfileClass.create_default(SurfaceProfileClass.SurfaceType.ASPHALT)
	_setup_raycast()

func _setup_raycast() -> void:
	_raycast = RayCast3D.new()
	_raycast.name = "SurfaceRayCast"
	_raycast.target_position = Vector3(0, -ray_length, 0)
	_raycast.position = Vector3(0, 0.5, 0) # Inicia medio metro arriba del centro
	_raycast.enabled = true
	_raycast.collision_mask = 1 # Capa principal de terreno y estructuras
	add_child(_raycast)

## Ejecuta la detección en cada ciclo físico y actualiza el perfil si cambió
func update_surface_detection() -> SurfaceProfileClass:
	if not _raycast or not _raycast.is_colliding():
		# Si no hay colisión directa debajo, verificar cercanía horizontal a vialidades
		var fallback_prof = _classify_by_spatial_position(global_position)
		_set_profile(fallback_prof)
		return current_profile

	var collider = _raycast.get_collider()
	var col_point = _raycast.get_collision_point()
	var detected_profile = classify_collider(collider, col_point)
	_set_profile(detected_profile)
	return current_profile

func _set_profile(new_prof: SurfaceProfileClass) -> void:
	if current_profile == null or current_profile.type != new_prof.type:
		current_profile = new_prof
		surface_changed.emit(current_profile)

func classify_collider(collider: Object, point: Vector3) -> SurfaceProfileClass:
	if not collider:
		return SurfaceProfileClass.create_default(SurfaceProfileClass.SurfaceType.ASPHALT)

	var col_name: String = ""
	var parent_name: String = ""
	if collider is Node:
		col_name = (collider as Node).name.to_lower()
		var p = (collider as Node).get_parent()
		if p:
			parent_name = p.name.to_lower()

	# 1. Comprobar puentes y estructuras suspendidas
	if "bridge" in col_name or "bridge" in parent_name or "puente" in col_name:
		return SurfaceProfileClass.create_default(SurfaceProfileClass.SurfaceType.CONCRETE)

	# 2. Comprobar vías férreas
	if "rail" in col_name or "rail" in parent_name or "ferrocarril" in col_name:
		return SurfaceProfileClass.create_default(SurfaceProfileClass.SurfaceType.RAILWAY)

	# 3. Comprobar cuerpos de agua (Río Tecate)
	if "water" in col_name or "water" in parent_name or "rio" in col_name:
		return SurfaceProfileClass.create_default(SurfaceProfileClass.SurfaceType.WATER)

	# 4. Comprobar malla de calzadas explícitas (Roadways)
	if "road" in col_name or "road" in parent_name or "calzada" in col_name:
		return SurfaceProfileClass.create_default(SurfaceProfileClass.SurfaceType.ASPHALT)

	# 5. Si impactó con el tinMesh del terreno, contrastar con StreetNameLookup
	return _classify_by_spatial_position(point)

func _classify_by_spatial_position(point: Vector3) -> SurfaceProfileClass:
	# Consultar el Autoload StreetNameLookup si está disponible en el árbol
	var street_lookup = Engine.get_main_loop().root.get_node_or_null("StreetNameLookup") if Engine.get_main_loop() else null
	if street_lookup:
		# Si hay un método para consultar el segmento más cercano
		if street_lookup.has_method("get_nearest_street"):
			var st_name: String = street_lookup.get_nearest_street(point)
			# Si la distancia al segmento de calle es menor que el radio de calzada
			var dist = _get_distance_to_nearest_segment(street_lookup, point)
			if dist <= road_snap_distance:
				# Dentro del ancho de la vialidad
				return SurfaceProfileClass.create_default(SurfaceProfileClass.SurfaceType.ASPHALT)
			else:
				# Alejado de calles: Terreno virgen / cerro natural de Tecate
				return SurfaceProfileClass.create_default(SurfaceProfileClass.SurfaceType.DIRT_OFFROAD)

	# Si no hay StreetNameLookup, asumir asfalto por defecto
	return SurfaceProfileClass.create_default(SurfaceProfileClass.SurfaceType.ASPHALT)

func _get_distance_to_nearest_segment(street_lookup: Node, point: Vector3) -> float:
	# Medición directa de distancia contra los segmentos cacheados si están expuestos
	if "_segments" in street_lookup:
		var segments: Array = street_lookup.get("_segments")
		var min_d_sq: float = INF
		# Muestrear los segmentos más cercanos
		var px = point.x
		var pz = point.z
		for seg in segments:
			if seg is Dictionary:
				var x0 = float(seg.get("x0", 0.0))
				var z0 = float(seg.get("z0", 0.0))
				var x1 = float(seg.get("x1", 0.0))
				var z1 = float(seg.get("z1", 0.0))
				var d_sq = _dist_to_segment_squared(px, pz, x0, z0, x1, z1)
				if d_sq < min_d_sq:
					min_d_sq = d_sq
					if min_d_sq < 16.0: # Si ya está a menos de 4m, terminar búsqueda anticipada
						break
		return sqrt(min_d_sq) if min_d_sq != INF else road_snap_distance + 1.0
	return road_snap_distance - 1.0

func _dist_to_segment_squared(px: float, pz: float, x0: float, z0: float, x1: float, z1: float) -> float:
	var dx = x1 - x0
	var dz = z1 - z0
	var l2 = dx * dx + dz * dz
	if l2 < 0.0001:
		var ddx = px - x0
		var ddz = pz - z0
		return ddx * ddx + ddz * ddz
	var t = clampf(((px - x0) * dx + (pz - z0) * dz) / l2, 0.0, 1.0)
	var proj_x = x0 + t * dx
	var proj_z = z0 + t * dz
	var ex = px - proj_x
	var ez = pz - proj_z
	return ex * ex + ez * ez
