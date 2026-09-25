extends Node

## StreetNameLookup — Autoload de Tecate Simulator
## ─────────────────────────────────────────────────────────────────────────────
## Carga street_segments.json al inicio y expone:
##
##   get_street_ahead(pos: Vector3, forward: Vector3) → String
##     Determina qué calle física se encuentra enfrente del jugador en la
##     dirección de su mirada (vector forward), evaluando la intersección
##     del rayo de visión contra los segmentos reales de calle (acotados [A, B]).
##     Incluye caché interno de posición y dirección para cero costo de CPU
##     cuando el jugador se mueve despacio o está detenido.
##
##   get_nearest_street(pos: Vector3) → String
##     Calle más cercana en posición, sin considerar dirección.
##
## Registro en project.godot:
##   [autoload]
##   StreetNameLookup="*res://systems/urban/street_name_lookup.gd"

const DATA_PATH: String = "res://assets/street_segments.json"

## Radio de búsqueda alrededor del jugador (metros).
## 160 m cubre 25 celdas de grilla en lugar de 49, reduciendo a la mitad el área.
const SEARCH_RADIUS: float = 160.0

var _cell_size: float = 200.0
var _segments: Array[Dictionary] = []
var _grid: Dictionary = {}

## Cache de última consulta para evitar recalculado innecesario
var _last_query_pos: Vector3 = Vector3(INF, INF, INF)
var _last_query_forward: Vector3 = Vector3.ZERO
var _last_street_name: String = ""

const HW_PRIORITY := {
	"motorway": 0, "trunk": 1, "primary": 2, "secondary": 3,
	"tertiary": 4, "residential": 5, "unclassified": 5,
	"living_street": 6, "service": 7,
	"motorway_link": 3, "trunk_link": 3, "primary_link": 3,
	"secondary_link": 4, "tertiary_link": 5,
}

# ── Inicialización ────────────────────────────────────────────────────────────

func _ready() -> void:
	_load_data()

func _load_data() -> void:
	if not FileAccess.file_exists(DATA_PATH):
		push_warning("[StreetNameLookup] No se encontró: %s" % DATA_PATH)
		return
	var file := FileAccess.open(DATA_PATH, FileAccess.READ)
	if not file:
		push_error("[StreetNameLookup] Error al abrir: %s" % DATA_PATH)
		return
	var parsed_variant = JSON.parse_string(file.get_as_text())
	file.close()
	if not parsed_variant or not (parsed_variant is Dictionary):
		push_error("[StreetNameLookup] JSON inválido en: %s" % DATA_PATH)
		return

	var parsed_dict: Dictionary = parsed_variant as Dictionary
	_cell_size = float(parsed_dict.get("cell_size", 200.0))

	_segments.clear()
	var raw_segments: Array = parsed_dict.get("segments", []) as Array
	for item in raw_segments:
		if item is Dictionary:
			_segments.append(item as Dictionary)

	_grid = parsed_dict.get("grid", {}) as Dictionary

	print("[StreetNameLookup] Cargados %d segmentos, %d celdas" % [
		_segments.size(), _grid.size()
	])

# ── API pública ───────────────────────────────────────────────────────────────

## Calle hacia la que apunta el jugador (intersección real de rayo contra segmento).
func get_street_ahead(pos: Vector3, forward: Vector3) -> String:
	# Caché de micro-movimientos: Si el jugador se movió menos de 0.5m y giró menos de ~3.6°,
	# devolver el resultado en caché instantáneamente.
	if pos.distance_squared_to(_last_query_pos) < 0.25 and forward.dot(_last_query_forward) > 0.998:
		return _last_street_name

	var dx: float = forward.x
	var dz: float = forward.z
	var len_xz: float = sqrt(dx * dx + dz * dz)
	if len_xz < 0.001:
		return get_nearest_street(pos)
	dx /= len_xz
	dz /= len_xz

	_last_query_pos = pos
	_last_query_forward = forward
	_last_street_name = _query_ray(pos.x, pos.z, dx, dz)
	return _last_street_name

## Calle más cercana al punto (sin importar dirección).
func get_nearest_street(pos: Vector3) -> String:
	return _query_point(pos.x, pos.z)

func get_nearest_street_2d(x: float, z: float) -> String:
	return _query_point(x, z)

# ── Internos ─────────────────────────────────────────────────────────────────

func _query_ray(ox: float, oz: float, dx: float, dz: float) -> String:
	var cr: int = int(ceil(SEARCH_RADIUS / _cell_size)) + 1
	var cx0: int = int(floor(ox / _cell_size))
	var cz0: int = int(floor(oz / _cell_size))

	var best_name: String = ""
	var best_t: float = INF
	var best_prio: int = 999
	var seen: Dictionary = {}

	for dcx in range(-cr, cr + 1):
		for dcz in range(-cr, cr + 1):
			var ck: String = "%d,%d" % [cx0 + dcx, cz0 + dcz]
			if not _grid.has(ck):
				continue
			var cell_indices: Array = _grid[ck] as Array
			for idx_variant in cell_indices:
				var idx: int = int(idx_variant)
				if seen.has(idx):
					continue
				seen[idx] = true

				var seg: Dictionary = _segments[idx]
				var x0: float = float(seg.get("x0", 0.0))
				var z0: float = float(seg.get("z0", 0.0))
				var x1: float = float(seg.get("x1", 0.0))
				var z1: float = float(seg.get("z1", 0.0))

				var t: float = _ray_segment_corridor(ox, oz, dx, dz, x0, z0, x1, z1, 20.0)
				if t < 0.0 or t == INF:
					continue

				var hw_name: String = str(seg.get("hw", ""))
				var prio: int = int(HW_PRIORITY.get(hw_name, 8))
				if t < best_t or (t < best_t + 2.0 and prio < best_prio):
					best_t = t
					best_name = str(seg.get("name", ""))
					best_prio = prio

	if best_name.is_empty():
		return _query_point(ox, oz)
	return best_name

## Evalúa la intersección del rayo O + t*D contra el segmento acotado [A, B].
func _ray_segment_corridor(
	ox: float, oz: float,
	dx: float, dz: float,
	ax: float, az: float,
	bx: float, bz: float,
	max_perp: float = 20.0
) -> float:
	# 1. Intersección rayo vs segmento acotado [A, B]
	var ex: float = bx - ax
	var ez: float = bz - az
	var det: float = dz * ex - dx * ez
	if absf(det) > 0.0001:
		var t: float = ((az - oz) * ex - (ax - ox) * ez) / det
		var s: float = ((az - oz) * dx - (ax - ox) * dz) / det
		if t >= 0.0 and s >= 0.0 and s <= 1.0:
			return t

	# 2. Corredor de visión (extremos de segmento dentro de max_perp)
	var px: float = -dz
	var pz: float = dx

	var t_a: float = (ax - ox) * dx + (az - oz) * dz
	var p_a: float = (ax - ox) * px + (az - oz) * pz

	var t_b: float = (bx - ox) * dx + (bz - oz) * dz
	var p_b: float = (bx - ox) * px + (bz - oz) * pz

	var min_t: float = INF
	if t_a >= 0.0 and absf(p_a) <= max_perp:
		min_t = minf(min_t, t_a)
	if t_b >= 0.0 and absf(p_b) <= max_perp:
		min_t = minf(min_t, t_b)

	return min_t

func _query_point(px: float, pz: float) -> String:
	var cx0: int = int(floor(px / _cell_size))
	var cz0: int = int(floor(pz / _cell_size))
	var best_name: String = ""
	var best_dist: float = INF
	var best_prio: int = 999
	for dcx in range(-1, 2):
		for dcz in range(-1, 2):
			var ck: String = "%d,%d" % [cx0 + dcx, cz0 + dcz]
			if not _grid.has(ck):
				continue
			var cell_indices: Array = _grid[ck] as Array
			for idx_variant in cell_indices:
				var idx: int = int(idx_variant)
				var seg: Dictionary = _segments[idx]
				var d: float = _point_to_segment_sq(
					px, pz,
					float(seg.get("x0", 0.0)), float(seg.get("z0", 0.0)),
					float(seg.get("x1", 0.0)), float(seg.get("z1", 0.0))
				)
				var hw_name: String = str(seg.get("hw", ""))
				var prio: int = int(HW_PRIORITY.get(hw_name, 8))
				if d < best_dist or (d == best_dist and prio < best_prio):
					best_dist = d
					best_name = str(seg.get("name", ""))
					best_prio = prio
	return best_name

func _point_to_segment_sq(
	px: float, pz: float,
	ax: float, az: float,
	bx: float, bz: float
) -> float:
	var ex: float = bx - ax
	var ez: float = bz - az
	var len_sq: float = ex * ex + ez * ez
	if len_sq < 0.0001:
		var fx: float = px - ax
		var fz: float = pz - az
		return fx * fx + fz * fz
	var t: float = clampf(((px - ax) * ex + (pz - az) * ez) / len_sq, 0.0, 1.0)
	var cx: float = ax + t * ex
	var cz: float = az + t * ez
	var gx: float = px - cx
	var gz: float = pz - cz
	return gx * gx + gz * gz
