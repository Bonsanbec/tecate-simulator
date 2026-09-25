extends Node

## StreetNameLookup — Autoload de Tecate Simulator
## ─────────────────────────────────────────────────────────────────────────────
## Carga street_segments.json al inicio y expone:
##
##   get_street_ahead(pos: Vector3, forward: Vector3) → String
##     De las calles que rodean al jugador (dentro de NEARBY_RADIUS),
##     devuelve aquella cuya línea infinita el rayo {pos + t·forward}
##     cruzaría primero (menor t > 0).
##     Esta es la semántica correcta para el header de brújula:
##     "la primera barrera de calle que el jugador tiene enfrente."
##
##   get_nearest_street(pos: Vector3) → String
##     Calle más cercana en posición, sin considerar dirección.
##
## El índice espacial de grilla garantiza O(k) por consulta.
##
## Registro en project.godot:
##   [autoload]
##   StreetNameLookup="*res://systems/urban/street_name_lookup.gd"

const DATA_PATH: String = "res://assets/street_segments.json"

## Radio de búsqueda alrededor del jugador (metros).
## Sólo se consideran calles dentro de este radio; las más lejanas se ignoran.
## ~120 m cubre 1-2 manzanas típicas de Tecate (~80-100 m de lado).
const NEARBY_RADIUS: float = 120.0
const NEARBY_RADIUS_SQ: float = 120.0 * 120.0

var _cell_size: float = 200.0
var _segments: Array[Dictionary] = []
var _grid: Dictionary = {}

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

	print("[StreetNameLookup] Cargados %d segmentos, %d celdas, radio=%.0f m" % [
		_segments.size(), _grid.size(), NEARBY_RADIUS
	])

# ── API pública ───────────────────────────────────────────────────────────────

## Calle hacia la que apunta el jugador, entre las que lo rodean de cerca.
func get_street_ahead(pos: Vector3, forward: Vector3) -> String:
	var dx: float = forward.x
	var dz: float = forward.z
	var len_xz: float = sqrt(dx * dx + dz * dz)
	if len_xz < 0.001:
		return get_nearest_street(pos)
	dx /= len_xz
	dz /= len_xz
	return _query_ray_nearby(pos.x, pos.z, dx, dz)

## Calle más cercana al punto (sin importar dirección).
func get_nearest_street(pos: Vector3) -> String:
	return _query_point(pos.x, pos.z)

func get_nearest_street_2d(x: float, z: float) -> String:
	return _query_point(x, z)

# ── Internos ─────────────────────────────────────────────────────────────────

func _query_ray_nearby(ox: float, oz: float, dx: float, dz: float) -> String:
	var cr: int = int(ceil(NEARBY_RADIUS / _cell_size)) + 1
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

				if _point_to_segment_sq(ox, oz, x0, z0, x1, z1) > NEARBY_RADIUS_SQ:
					continue

				var t: float = _ray_line_t(ox, oz, dx, dz, x0, z0, x1, z1)
				if t < 0.0:
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

func _ray_line_t(
	ox: float, oz: float,
	dx: float, dz: float,
	ax: float, az: float,
	bx: float, bz: float
) -> float:
	var ex: float = bx - ax
	var ez: float = bz - az
	var det: float = dz * ex - dx * ez
	if absf(det) < 0.0001:
		return INF
	return ((az - oz) * ex - (ax - ox) * ez) / det

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
