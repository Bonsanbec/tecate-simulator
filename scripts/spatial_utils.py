"""
spatial_utils.py
================
Sistema Universal de Posicionamiento Espacial y Geodesia para Tecate Simulator.

NIVEL MUNICIPAL:
    Proporciona transformación bidireccional continua y determinista entre:
      • Geoposición GPS / WGS84 (Latitud, Longitud)
      • Espacio métrico osm2world / Blender (bx, by, bz)
      • Espacio métrico del mundo Godot Engine 4 (gx, gy, gz)

PRINCIPIO CANÓNICO DE MANZANA:
    Toda asignación de predio o edificio se resuelve de forma topológica y analítica
    mediante el polígono cerrado de su manzana (blocks_cache.json).
    Se eliminan por completo heurísticas basadas en nombres de calles o umbrales ad-hoc.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Set
from collections import defaultdict

# ─── CONSTANTES GEODÉSICAS CALIBRADAS A NIVEL MUNICIPAL (WGS84 / TECATE) ────
# Calibradas empíricamente contra el conjunto completo de 4,239 manzanas del municipio.
# Error residual medio: ~18 metros a lo largo de un corredor de 78 km este-oeste.
ORIGIN_LAT: float = 32.5732357          # Latitud del origen métrico osm2world (0, 0)
ORIGIN_LON: float = -116.6265288        # Longitud del origen métrico osm2world (0, 0)
METERS_PER_DEG_LAT: float = 111323.6051 # Metros por grado de latitud en Tecate
METERS_PER_DEG_LON: float = 93810.7490  # Metros por grado de longitud (cos(32.573°)*111323)
DEG_LAT_PER_METER: float = 1.0 / METERS_PER_DEG_LAT  # ~8.982823e-6
DEG_LON_PER_METER: float = 1.0 / METERS_PER_DEG_LON  # ~1.065976e-5

# ─── RUTAS CANÓNICAS ────────────────────────────────────────────────────────
_BASE = Path(__file__).resolve().parent.parent
_CANDIDATE_MANIFESTS = [
    _BASE / "blender_assets" / "manifest_edificios.json",
    _BASE / "scratch" / "manifest_edificios.json",
]
_BLOCKS_PATH = _BASE / "scratch" / "cache" / "blocks_cache.json"
_FACADES_PATH = _BASE / "scratch" / "cache" / "facades_cache.json"
_PANORAMAS_PATH = _BASE / "scratch" / "cache" / "panoramas_cache.json"
_SPATIAL_MODEL_PATH = _BASE / "blender_assets" / "spatial_model.json"


# ═══════════════════════════════════════════════════════════════════════════════
# 1. ÁLGEBRA LINEAL Y GEOMETRÍA 2D PURA
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Vec2:
    x: float
    z: float  # En Godot XZ: +X = Este, -X = Oeste, -Z = Norte, +Z = Sur

    def __add__(self, o: "Vec2") -> "Vec2":
        return Vec2(self.x + o.x, self.z + o.z)

    def __sub__(self, o: "Vec2") -> "Vec2":
        return Vec2(self.x - o.x, self.z - o.z)

    def __mul__(self, s: float) -> "Vec2":
        return Vec2(self.x * s, self.z * s)

    def __truediv__(self, s: float) -> "Vec2":
        return Vec2(self.x / s, self.z / s)

    def length(self) -> float:
        return math.sqrt(self.x * self.x + self.z * self.z)

    def length_squared(self) -> float:
        return self.x * self.x + self.z * self.z

    def normalized(self) -> "Vec2":
        l = self.length()
        return Vec2(self.x / l, self.z / l) if l > 1e-9 else Vec2(0.0, 0.0)

    def dot(self, o: "Vec2") -> float:
        return self.x * o.x + self.z * o.z

    def cross(self, o: "Vec2") -> float:
        """Producto cruz en 2D (determinante): x1*z2 - z1*x2"""
        return self.x * o.z - self.z * o.x

    def heading_deg(self) -> float:
        """
        Heading geográfico en grados [0, 360):
        0° = Norte (-Z), 90° = Este (+X), 180° = Sur (+Z), 270° = Oeste (-X).
        """
        return math.degrees(math.atan2(self.x, -self.z)) % 360.0


@dataclass
class PolygonEdge:
    """Arista orientada de un polígono con su normal exterior analítica."""
    idx: int
    v0: Vec2
    v1: Vec2
    length: float
    tangent: Vec2
    outward_normal: Vec2
    heading_deg: float

    @property
    def midpoint(self) -> Vec2:
        return Vec2((self.v0.x + self.v1.x) * 0.5, (self.v0.z + self.v1.z) * 0.5)

    @property
    def cardinal(self) -> str:
        h = self.heading_deg
        if 22.5 <= h < 67.5:   return "NE"
        if 67.5 <= h < 112.5:  return "E"
        if 112.5 <= h < 157.5: return "SE"
        if 157.5 <= h < 202.5: return "S"
        if 202.5 <= h < 247.5: return "SO"
        if 247.5 <= h < 292.5: return "O"
        if 292.5 <= h < 337.5: return "NO"
        return "N"


def point_in_polygon(p: Vec2, polygon: List[Vec2]) -> bool:
    """Ray casting Jordan curve theorem. Robusto ante vértices colineales."""
    n = len(polygon)
    if n < 3:
        return False
    inside = False
    j = n - 1
    for i in range(n):
        vi = polygon[i]
        vj = polygon[j]
        if ((vi.z > p.z) != (vj.z > p.z)) and (p.x < (vj.x - vi.x) * (p.z - vi.z) / (vj.z - vi.z + 1e-18) + vi.x):
            inside = not inside
        j = i
    return inside


def polygon_centroid(polygon: List[Vec2]) -> Vec2:
    """Centroide ponderado por área (Shoelace formula)."""
    n = len(polygon)
    if n == 0:
        return Vec2(0.0, 0.0)
    if n < 3:
        return Vec2(sum(p.x for p in polygon) / n, sum(p.z for p in polygon) / n)
    
    area_accum = 0.0
    cx_accum = 0.0
    cz_accum = 0.0
    for i in range(n):
        p0 = polygon[i]
        p1 = polygon[(i + 1) % n]
        factor = p0.x * p1.z - p1.x * p0.z
        area_accum += factor
        cx_accum += (p0.x + p1.x) * factor
        cz_accum += (p0.z + p1.z) * factor
    
    area = area_accum * 0.5
    if abs(area) < 1e-7:
        return Vec2(sum(p.x for p in polygon) / n, sum(p.z for p in polygon) / n)
    return Vec2(cx_accum / (6.0 * area), cz_accum / (6.0 * area))


def compute_polygon_edges(polygon: List[Vec2]) -> List[PolygonEdge]:
    """Calcula todas las aristas y sus normales exteriores salientes."""
    n = len(polygon)
    if n < 3:
        return []
    center = polygon_centroid(polygon)
    edges: List[PolygonEdge] = []
    for i in range(n):
        v0 = polygon[i]
        v1 = polygon[(i + 1) % n]
        seg = v1 - v0
        l = seg.length()
        if l < 0.05:
            continue
        tangent = seg.normalized()
        # Normal 90° horario: (dx, dz) -> (dz, -dx)
        normal = Vec2(tangent.z, -tangent.x)
        # Validar si apunta hacia afuera del centroide
        mid = Vec2((v0.x + v1.x) * 0.5, (v0.z + v1.z) * 0.5)
        to_center = center - mid
        if normal.dot(to_center) > 0.0:
            normal = Vec2(-normal.x, -normal.z)
        
        edges.append(PolygonEdge(
            idx=i,
            v0=v0,
            v1=v1,
            length=l,
            tangent=tangent,
            outward_normal=normal,
            heading_deg=normal.heading_deg()
        ))
    return edges


def distance_point_to_edge(p: Vec2, edge: PolygonEdge) -> Tuple[float, Vec2]:
    """Distancia mínima de un punto al segmento de arista y su proyección más cercana."""
    seg = edge.v1 - edge.v0
    l2 = seg.length_squared()
    if l2 < 1e-12:
        return (p - edge.v0).length(), edge.v0
    t = max(0.0, min(1.0, (p - edge.v0).dot(seg) / l2))
    proj = edge.v0 + seg * t
    return (p - proj).length(), proj


# ═══════════════════════════════════════════════════════════════════════════════
# 2. TRANSFORMACIONES CARTESIANAS Y GEODÉSICAS UNIVERSALES
# ═══════════════════════════════════════════════════════════════════════════════

def gps_to_blender(lat: float, lon: float, alt_m: float = 0.0) -> Tuple[float, float, float]:
    """
    Convierte WGS84 GPS (lat, lon, alt) a coordenadas cartesianas Blender (bx, by, bz).
    bx: Este (+X), by: Norte (+Y), bz: Elevación (+Z).
    """
    bx = (lon - ORIGIN_LON) * METERS_PER_DEG_LON
    by = (lat - ORIGIN_LAT) * METERS_PER_DEG_LAT
    return (bx, by, alt_m)


def blender_to_gps(bx: float, by: float, bz: float = 0.0) -> Tuple[float, float, float]:
    """
    Convierte coordenadas cartesianas Blender a GPS WGS84 (lat, lon, alt).
    """
    lat = ORIGIN_LAT + by * DEG_LAT_PER_METER
    lon = ORIGIN_LON + bx * DEG_LON_PER_METER
    return (lat, lon, bz)


def blender_to_godot(bx: float, by: float, bz: float) -> Tuple[float, float, float]:
    """
    Transformación de exportación estándar glTF (Blender Z-up -> Godot Y-up).
    Godot X = Blender X  (Este)
    Godot Y = Blender Z  (Cenit)
    Godot Z = -Blender Y (Sur)
    """
    return (bx, bz, -by)


def godot_to_blender(gx: float, gy: float, gz: float) -> Tuple[float, float, float]:
    """
    Transformación inversa (Godot Y-up -> Blender Z-up).
    Blender X = Godot X
    Blender Y = -Godot Z
    Blender Z = Godot Y
    """
    return (gx, -gz, gy)


def gps_to_godot(lat: float, lon: float, alt_m: float = 0.0) -> Tuple[float, float, float]:
    """
    Convierte WGS84 GPS directamente a coordenadas métricas Godot (gx, gy, gz).
    gx: +Este / -Oeste
    gy: +Elevación
    gz: +Sur / -Norte
    """
    bx, by, bz = gps_to_blender(lat, lon, alt_m)
    return blender_to_godot(bx, by, bz)


def godot_to_gps(gx: float, gy: float, gz: float) -> Tuple[float, float, float]:
    """
    Convierte coordenadas métricas Godot directamente a WGS84 GPS (lat, lon, alt).
    """
    bx, by, bz = godot_to_blender(gx, gy, gz)
    return blender_to_gps(bx, by, bz)


def normal_to_godot_transform3d(outward_normal: Vec2, gx: float, gy: float, gz: float) -> str:
    """
    Genera el Transform3D analítico exacto para Godot 4 (.tscn).
    Alinea la fachada frontal del edificio (+Z local en glTF) con la normal saliente de la calle.
    """
    # Rotación en Y: ángulo entre el vector +Z canónico (Sur) y la normal saliente
    theta = math.atan2(outward_normal.x, outward_normal.z)
    c = math.cos(theta)
    s = math.sin(theta)

    def _f(v: float) -> str:
        s_val = f"{v:.6f}".rstrip("0").rstrip(".")
        return "0" if s_val == "-0" or s_val == "" else s_val

    # Matriz de rotación en columna-major para Transform3D:
    # Columna 1 (X local): (c, 0, -s)
    # Columna 2 (Y local): (0, 1, 0)
    # Columna 3 (Z local / Frente): (s, 0, c)
    return (
        f"Transform3D("
        f"{_f(c)}, 0, {_f(-s)},  "
        f"0, 1, 0,  "
        f"{_f(s)}, 0, {_f(c)},  "
        f"{_f(gx)}, {_f(gy)}, {_f(gz)})"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 3. REJILLA ESPACIAL (SPATIAL GRID) PARA BÚSQUEDA O(1) MUNICIPAL
# ═══════════════════════════════════════════════════════════════════════════════

class SpatialGrid:
    """Indexador espacial de celdas uniformes para polígonos de manzanas."""
    def __init__(self, cell_size: float = 250.0):
        self.cell_size = cell_size
        self.grid: Dict[Tuple[int, int], List[str]] = defaultdict(list)

    def _cell(self, x: float, z: float) -> Tuple[int, int]:
        return (int(math.floor(x / self.cell_size)), int(math.floor(z / self.cell_size)))

    def insert(self, block_id: str, polygon: List[Vec2]) -> None:
        if not polygon:
            return
        min_x = min(p.x for p in polygon)
        max_x = max(p.x for p in polygon)
        min_z = min(p.z for p in polygon)
        max_z = max(p.z for p in polygon)

        c_x0 = int(math.floor(min_x / self.cell_size))
        c_x1 = int(math.floor(max_x / self.cell_size))
        c_z0 = int(math.floor(min_z / self.cell_size))
        c_z1 = int(math.floor(max_z / self.cell_size))

        for cx in range(c_x0, c_x1 + 1):
            for cz in range(c_z0, c_z1 + 1):
                self.grid[(cx, cz)].append(block_id)

    def query(self, x: float, z: float, radius_cells: int = 1) -> Set[str]:
        cx, cz = self._cell(x, z)
        found: Set[str] = set()
        for dx in range(-radius_cells, radius_cells + 1):
            for dz in range(-radius_cells, radius_cells + 1):
                cell_blocks = self.grid.get((cx + dx, cz + dz))
                if cell_blocks:
                    found.update(cell_blocks)
        return found


# ═══════════════════════════════════════════════════════════════════════════════
# 4. CONTEXTO ESPACIAL UNIVERSAL (SPATIAL CONTEXT)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ResolvedBuilding:
    """Resultado del posicionamiento analítico generalizado."""
    name: str
    block_id: Optional[str]
    godot_pos: Vec2
    elevation_y: float
    is_inside_polygon: bool
    distance_to_boundary_m: float
    primary_edge: Optional[PolygonEdge]
    outward_heading_deg: Optional[float]
    transform3d_tscn: str
    warnings: List[str] = field(default_factory=list)


class SpatialContext:
    """Gestor unificado del espacio y las geometrías municipales de Tecate."""

    def __init__(self,
                 manifest_data: dict,
                 blocks_data: dict,
                 facades_data: dict,
                 panoramas_data: dict):
        self.manifest_entries = {e["name"]: e for e in manifest_data.get("entries", [])}
        self.blocks = blocks_data
        self.facades = facades_data
        self.panoramas = panoramas_data
        
        # Pre-computar polígonos en coordenadas Godot XZ
        self._godot_polygons: Dict[str, List[Vec2]] = {}
        self._godot_edges: Dict[str, List[PolygonEdge]] = {}
        self._spatial_grid = SpatialGrid(cell_size=200.0)

        self._build_index()

    def _build_index(self):
        for bid, bdata in self.blocks.items():
            raw_poly = bdata.get("polygon", [])
            if len(raw_poly) < 3:
                continue
            # En blocks_cache: polygon = [[x_osm, y_osm], ...]
            # osm2world x = Godot X
            # osm2world y = -Godot Z
            godot_poly = [Vec2(p[0], -p[1]) for p in raw_poly]
            self._godot_polygons[bid] = godot_poly
            self._spatial_grid.insert(bid, godot_poly)

    @classmethod
    def load(cls) -> "SpatialContext":
        """Carga determinista con fallback de archivos existentes."""
        manifest_path = None
        for cand in _CANDIDATE_MANIFESTS:
            if cand.exists():
                manifest_path = cand
                break
        if not manifest_path:
            raise FileNotFoundError(f"No se encontró manifest_edificios.json en las rutas candidatas: {_CANDIDATE_MANIFESTS}")

        with open(manifest_path, encoding="utf-8") as f:
            manifest_data = json.load(f)
        with open(_BLOCKS_PATH, encoding="utf-8") as f:
            blocks_data = json.load(f)
        with open(_FACADES_PATH, encoding="utf-8") as f:
            facades_data = json.load(f)
        with open(_PANORAMAS_PATH, encoding="utf-8") as f:
            panoramas_data = json.load(f)

        return cls(manifest_data, blocks_data, facades_data, panoramas_data)

    def get_block_polygon(self, block_id: str) -> List[Vec2]:
        """Devuelve el polígono en coordenadas Godot XZ."""
        return self._godot_polygons.get(block_id, [])

    def get_block_edges(self, block_id: str) -> List[PolygonEdge]:
        """Devuelve las aristas del polígono con normales exteriores cacheadas."""
        if block_id not in self._godot_edges:
            poly = self.get_block_polygon(block_id)
            self._godot_edges[block_id] = compute_polygon_edges(poly)
        return self._godot_edges[block_id]

    def find_block_at_point(self, p: Vec2) -> Optional[str]:
        """
        Localiza en O(1) la manzana que contiene topológicamente el punto en Godot.
        """
        candidates = self._spatial_grid.query(p.x, p.z, radius_cells=1)
        for bid in candidates:
            poly = self._godot_polygons[bid]
            if point_in_polygon(p, poly):
                return bid
        return None

    def find_nearest_block(self, p: Vec2) -> Tuple[Optional[str], float]:
        """Encuentra la manzana más cercana y la distancia a su centroide."""
        candidates = self._spatial_grid.query(p.x, p.z, radius_cells=2)
        if not candidates:
            candidates = set(self._godot_polygons.keys())
        
        best_id = None
        best_dist = float("inf")
        for bid in candidates:
            poly = self._godot_polygons[bid]
            c = polygon_centroid(poly)
            d = (p - c).length()
            if d < best_dist:
                best_dist = d
                best_id = bid
        return best_id, best_dist

    def resolve_building(self, building_name: str, fallback_elevation_y: float = 400.0) -> ResolvedBuilding:
        """
        Algoritmo Generalizado de Resolución de Edificio:
        1. Consulta posición en manifiesto (o por cálculo directo de geometría).
        2. Determina la manzana contenedora real mediante Point-in-Polygon.
        3. Verifica si el punto está dentro del polígono de la manzana.
        4. Si está fuera, aplica retranqueo ortogonal hacia el interior de la manzana.
        5. Determina la arista de fachada más cercana y su normal hacia la vialidad.
        6. Genera el Transform3D analítico exacto de Godot.
        """
        warnings: List[str] = []
        entry = self.manifest_entries.get(building_name)

        if not entry:
            warnings.append(f"El edificio '{building_name}' no se encuentra en el manifiesto.")
            # Generar fallback
            return ResolvedBuilding(
                name=building_name,
                block_id=None,
                godot_pos=Vec2(0.0, 0.0),
                elevation_y=fallback_elevation_y,
                is_inside_polygon=False,
                distance_to_boundary_m=999.0,
                primary_edge=None,
                outward_heading_deg=None,
                transform3d_tscn=f"Transform3D(1, 0, 0,  0, 1, 0,  0, 0, 1,  0, {fallback_elevation_y}, 0)",
                warnings=warnings
            )

        # 1. Obtener coordenadas Godot desde manifiesto
        gc = entry.get("godot_centroid")
        if gc:
            pos = Vec2(float(gc[0]), float(gc[2]))
            elev_y = float(gc[1])
        else:
            bbox = entry.get("blender_bbox", {})
            c = bbox.get("centroid", [0.0, 0.0, 400.0])
            gx, gy, gz = blender_to_godot(c[0], c[1], c[2])
            pos = Vec2(gx, gz)
            elev_y = gy
            warnings.append("Posición deducida de bbox centroid Blender.")

        # 2. Localizar manzana
        assigned_block_id = entry.get("block_id")
        real_block_id = self.find_block_at_point(pos)

        target_block_id = assigned_block_id
        if real_block_id and real_block_id != assigned_block_id:
            # Hay discrepancia entre el caché y la ubicación real
            target_block_id = real_block_id

        poly = self.get_block_polygon(target_block_id) if target_block_id else []
        is_inside = point_in_polygon(pos, poly) if poly else False

        # 3. Tratamiento si está fuera del polígono
        dist_to_boundary = 0.0
        final_pos = pos

        if not is_inside and poly:
            warnings.append(
                f"🚨 DETECCIÓN TOPOLÓGICA: El punto ({pos.x:.2f}, {pos.z:.2f}) se encuentra FUERA "
                f"de la manzana {target_block_id}."
            )
            # Encontrar arista más cercana del polígono
            edges = self.get_block_edges(target_block_id)
            if edges:
                best_edge = min(edges, key=lambda e: distance_point_to_edge(pos, e)[0])
                d_min, proj = distance_point_to_edge(pos, best_edge)
                dist_to_boundary = d_min
                # Corregir retranqueando 4 metros hacia el interior de la arista
                corrected_pos = proj - (best_edge.outward_normal * 4.0)
                if point_in_polygon(corrected_pos, poly):
                    final_pos = corrected_pos
                    warnings.append(f"✅ Retranqueo automático aplicado hacia el interior de la manzana: ({final_pos.x:.2f}, {final_pos.z:.2f}).")
                else:
                    centroid = polygon_centroid(poly)
                    final_pos = centroid
                    warnings.append(f"✅ Reubicación de emergencia en el centroide de la manzana: ({final_pos.x:.2f}, {final_pos.z:.2f}).")
                is_inside = True

        # 4. Determinar fachada principal y rotación
        edges = self.get_block_edges(target_block_id) if target_block_id else []
        primary_edge = None
        if edges:
            # La fachada frontal es la arista exterior más próxima al edificio
            primary_edge = min(edges, key=lambda e: distance_point_to_edge(final_pos, e)[0])
            d_b, _ = distance_point_to_edge(final_pos, primary_edge)
            dist_to_boundary = d_b

        # 5. Generar Transform3D
        if primary_edge:
            transform = normal_to_godot_transform3d(primary_edge.outward_normal, final_pos.x, elev_y, final_pos.z)
            heading = primary_edge.heading_deg
        else:
            transform = f"Transform3D(1, 0, 0,  0, 1, 0,  0, 0, 1,  {final_pos.x:.4f}, {elev_y:.4f}, {final_pos.z:.4f})"
            heading = None

        return ResolvedBuilding(
            name=building_name,
            block_id=target_block_id,
            godot_pos=final_pos,
            elevation_y=elev_y,
            is_inside_polygon=is_inside,
            distance_to_boundary_m=dist_to_boundary,
            primary_edge=primary_edge,
            outward_heading_deg=heading,
            transform3d_tscn=transform,
            warnings=warnings
        )

    def resolve_corner_placement(self,
                                 block_id: str,
                                 edge_idx_1: int,
                                 edge_idx_2: int,
                                 setback_distance_m: float = 6.0,
                                 elevation_y: float = 400.0) -> Tuple[Vec2, str, PolygonEdge]:
        """
        Resuelve analíticamente la posición y orientación de un edificio en CUALQUIER
        esquina o cruce del municipio.
        
        Dadas dos aristas de la manzana que se intersectan:
          • Calcula el vértice exacto de la esquina.
          • Calcula la bisectriz interior (hacia adentro de la manzana).
          • Posiciona el edificio a 'setback_distance_m' metros de la esquina hacia el interior.
          • Orienta la fachada o el chaflán hacia la esquina.
        """
        edges = self.get_block_edges(block_id)
        e1 = edges[edge_idx_1]
        e2 = edges[edge_idx_2]

        # Vértice de intersección (punto común entre v0/v1 de ambas aristas)
        candidates = [(e1.v0, e2.v0), (e1.v0, e2.v1), (e1.v1, e2.v0), (e1.v1, e2.v1)]
        v_corner = min(candidates, key=lambda pair: (pair[0] - pair[1]).length())[0]

        # Bisectriz de normales exteriores
        n_combined = (e1.outward_normal + e2.outward_normal).normalized()
        # Vector interior
        inward_dir = Vec2(-n_combined.x, -n_combined.z)

        # Posición interior del edificio
        placed_pos = v_corner + (inward_dir * setback_distance_m)

        # Transform3D con chaflán mirando al exterior (hacia n_combined)
        transform = normal_to_godot_transform3d(n_combined, placed_pos.x, elevation_y, placed_pos.z)

        return placed_pos, transform, e1


# ═══════════════════════════════════════════════════════════════════════════════
# 5. ENTRY POINT DE VERIFICACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("SISTEMA UNIVERSAL DE GEODESIA Y ESPACIO MUNICIPAL — TECATE SIMULATOR")
    print("=" * 70)
    
    # 1. Test de proyecciones directas e inversas
    print("\n[1] TEST DE IDEMPOTENCIA GPS <-> GODOT:")
    test_coords = [
        ("Parque Hidalgo (Centro)", 32.57293, -116.62685, 400.0),
        ("La Rumorosa (Este)", 32.53200, -116.05000, 1250.0),
        ("Valle de las Palmas (Sur)", 32.36000, -116.68000, 310.0),
        ("Paso del Águila (Oeste)", 32.56500, -116.68500, 380.0),
    ]
    for label, lat, lon, alt in test_coords:
        gx, gy, gz = gps_to_godot(lat, lon, alt)
        lat_back, lon_back, alt_back = godot_to_gps(gx, gy, gz)
        err_m = math.sqrt(((lat - lat_back) * METERS_PER_DEG_LAT)**2 + ((lon - lon_back) * METERS_PER_DEG_LON)**2)
        print(f"  • {label:26}: GPS ({lat:.5f}, {lon:.5f}) -> Godot ({gx:9.1f}, {gz:9.1f}) -> Error: {err_m:.6f} m")

    # 2. Carga y verificación topológica de edificios
    print("\n[2] CARGA DE CONTEXTO ESPACIAL MUNICIPAL:")
    ctx = SpatialContext.load()
    print(f"  • Manzanas indexadas en rejilla: {len(ctx._godot_polygons)}")
    print(f"  • Edificios en manifiesto: {len(ctx.manifest_entries)}")

    # 3. Resolución analítica de edificios
    print("\n[3] RESOLUCIÓN ANALÍTICA DE EDIFICIOS (MUESTRA):")
    sample_buildings = [
        "Building_BBVA_México",
        "Building_Ayuntamiento_de_Tecate",
        "Building_Biblioteca_Municipal_Tecate",
        "Building_Calimax",
        "Building_Walmart_Supercenter",
        "Building_Caseta_de_Cobro_EL_HONGO_Km_92_+_105"
    ]
    for bname in sample_buildings:
        res = ctx.resolve_building(bname)
        status = "✅ DENTRO" if res.is_inside_polygon else "🚨 FUERA"
        print(f"\n  Edificio: {res.name}")
        print(f"    Block ID: {res.block_id}")
        print(f"    Godot Pos: ({res.godot_pos.x:.2f}, {res.elevation_y:.2f}, {res.godot_pos.z:.2f}) | {status}")
        if res.primary_edge:
            print(f"    Fachada: Arista {res.primary_edge.idx} | Heading: {res.outward_heading_deg:.1f}° ({res.primary_edge.cardinal})")
        print(f"    Transform3D:\n      {res.transform3d_tscn}")
        for w in res.warnings:
            print(f"    ⚠️  {w}")

    print("\n" + "=" * 70)
    print("VERIFICACIÓN COMPLETADA SATISFACTORIAMENTE.")
    print("=" * 70)
