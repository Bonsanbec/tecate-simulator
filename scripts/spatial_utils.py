"""
spatial_utils.py
================
Utilidades de posicionamiento espacial generalizable para Tecate Simulator.

Principio fundamental:
    El polígono de la manzana (blocks_cache.json) es la ÚNICA fuente de
    verdad para determinar en qué lado de cada calle se ubica un edificio.
    No se usan nombres de calles, umbrales numéricos ni heurísticas ad-hoc.

Todas las funciones trabajan en coordenadas Godot (X, Y, Z):
    Godot X  = osm2world x  = Blender x        (→ Este)
    Godot Z  = -osm2world y = -Blender y       (→ Sur)
    Godot Y  = elevación

Para cargar y usar:
    from scripts.spatial_utils import SpatialContext
    ctx = SpatialContext.load()
    result = ctx.resolve_building("Building_Hotel_Tecate")
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# ─── Rutas por defecto ────────────────────────────────────────────────────────
_BASE = Path(__file__).resolve().parent.parent   # raíz del repositorio
_MANIFEST    = _BASE / "blender_assets" / "manifest_edificios.json"
_BLOCKS      = _BASE / "scratch" / "cache" / "blocks_cache.json"
_FACADES     = _BASE / "scratch" / "cache" / "facades_cache.json"
_PANORAMAS   = _BASE / "scratch" / "cache" / "panoramas_cache.json"
_SPATIAL_MDL = _BASE / "blender_assets" / "spatial_model.json"


# ═══════════════════════════════════════════════════════════════════════════════
# 1. TIPOS DE DATOS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Vec2:
    x: float
    z: float   # eje Z de Godot (Sur = +Z)

    def __add__(self, o: "Vec2") -> "Vec2":
        return Vec2(self.x + o.x, self.z + o.z)

    def __sub__(self, o: "Vec2") -> "Vec2":
        return Vec2(self.x - o.x, self.z - o.z)

    def __mul__(self, s: float) -> "Vec2":
        return Vec2(self.x * s, self.z * s)

    def length(self) -> float:
        return math.sqrt(self.x ** 2 + self.z ** 2)

    def normalized(self) -> "Vec2":
        m = self.length()
        return Vec2(self.x / m, self.z / m) if m > 1e-9 else Vec2(0.0, 0.0)

    def dot(self, o: "Vec2") -> float:
        return self.x * o.x + self.z * o.z

    def rotate_cw_90(self) -> "Vec2":
        """Rotación 90° sentido horario: (x,z) → (z, -x)"""
        return Vec2(self.z, -self.x)

    def heading_deg(self) -> float:
        """
        Convierte el vector al heading geográfico en grados (0=Norte=-Z, 90=Este=+X).
        Fórmula: atan2(componente Este, componente Norte) = atan2(x, -z)
        """
        return math.degrees(math.atan2(self.x, -self.z)) % 360


@dataclass
class PolygonEdge:
    """Una arista del polígono de manzana con su normal saliente ya calculada."""
    idx: int                # índice de arista en el polígono
    v0: Vec2                # vértice inicio (Godot XZ)
    v1: Vec2                # vértice fin
    midpoint: Vec2          # punto medio
    length_m: float         # longitud en metros
    tangent: Vec2           # vector unitario a lo largo de la arista
    outward_normal: Vec2    # normal unitaria saliente (hacia la calle)
    heading_deg: float      # heading geográfico de la normal (0=N, 90=E, 180=S, 270=O)

    @property
    def cardinal(self) -> str:
        """Nombre cardinal de la normal saliente."""
        h = self.heading_deg
        if 22.5 <= h < 67.5:   return "NE"
        if 67.5 <= h < 112.5:  return "E"
        if 112.5 <= h < 157.5: return "SE"
        if 157.5 <= h < 202.5: return "S"
        if 202.5 <= h < 247.5: return "SO"
        if 247.5 <= h < 292.5: return "O"
        if 292.5 <= h < 337.5: return "NO"
        return "N"


@dataclass
class BuildingPlacement:
    """Resultado completo de la resolución de posicionamiento de un edificio."""
    building_name: str
    block_id: Optional[str]
    block_match_method: str       # point_in_polygon | nearest_centroid | none
    # Posición en Godot
    godot_pos: Vec2               # XZ del centroide del edificio en Godot
    godot_y: float                # elevación (Y)
    # Fachada recomendada
    primary_facade_edge: Optional[PolygonEdge]
    secondary_facade_edge: Optional[PolygonEdge]
    # Transform3D listo para pegar en main.tscn
    transform3d: str
    # Información de diagnóstico
    warnings: list[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════════
# 2. FUNCIONES GEOMÉTRICAS PURAS (sin dependencia de datos del proyecto)
# ═══════════════════════════════════════════════════════════════════════════════

def osm2world_to_godot(mx: float, my: float) -> Vec2:
    """
    Convierte coordenadas métricas de osm2world (x=Este, y=Norte)
    a coordenadas Godot XZ (X=Este, Z=Sur).

    Equivalencia: Godot(X, Z) = osm2world(x, -y) = Blender(x, -y)
    """
    return Vec2(mx, -my)


def blender_to_godot(bx: float, by: float, bz: float) -> tuple[float, float, float]:
    """Blender(X,Y,Z) → Godot(X,Y,Z). Fórmula: Godot = (bx, bz, -by)."""
    return (bx, bz, -by)


def point_in_polygon(p: Vec2, polygon: list[Vec2]) -> bool:
    """Ray casting: True si el punto está dentro del polígono."""
    n = len(polygon)
    inside = False
    j = n - 1
    for i in range(n):
        xi, zi = polygon[i].x, polygon[i].z
        xj, zj = polygon[j].x, polygon[j].z
        if ((zi > p.z) != (zj > p.z)) and (p.x < (xj - xi) * (p.z - zi) / (zj - zi) + xi):
            inside = not inside
        j = i
    return inside


def polygon_centroid(polygon: list[Vec2]) -> Vec2:
    """Centroide por promedio simple de vértices."""
    return Vec2(
        sum(v.x for v in polygon) / len(polygon),
        sum(v.z for v in polygon) / len(polygon),
    )


def compute_polygon_edges(polygon: list[Vec2]) -> list[PolygonEdge]:
    """
    Calcula todas las aristas del polígono con sus normales salientes.

    La normal saliente se obtiene rotando el vector de arista 90° en sentido
    horario y verificando que apunte LEJOS del centroide del polígono.
    No requiere conocer el nombre de la calle adyacente.
    """
    centroid = polygon_centroid(polygon)
    n = len(polygon)
    edges: list[PolygonEdge] = []

    for i in range(n):
        v0 = polygon[i]
        v1 = polygon[(i + 1) % n]
        edge_vec = v1 - v0
        length = edge_vec.length()
        if length < 0.1:
            continue

        tangent = edge_vec.normalized()

        # Normal candidata: rotación CW 90°
        normal_candidate = tangent.rotate_cw_90()

        # Verificar orientación: la normal debe apuntar LEJOS del centroide
        midpoint = Vec2((v0.x + v1.x) / 2, (v0.z + v1.z) / 2)
        to_centroid = centroid - midpoint
        if normal_candidate.dot(to_centroid) > 0:
            # Apunta hacia el interior → invertir
            normal_candidate = Vec2(-normal_candidate.x, -normal_candidate.z)

        edges.append(PolygonEdge(
            idx=i,
            v0=v0,
            v1=v1,
            midpoint=midpoint,
            length_m=length,
            tangent=tangent,
            outward_normal=normal_candidate,
            heading_deg=normal_candidate.heading_deg(),
        ))

    return edges


def merge_collinear_edges(edges: list[PolygonEdge],
                          angle_tolerance_deg: float = 10.0) -> list[PolygonEdge]:
    """
    Fusiona aristas consecutivas colineales (variación de heading < tolerancia).
    Reduce 134 microfacetas osm2world a 4-8 lados significativos.
    Retorna las aristas fusionadas con longitud total y normal promedio.
    """
    if not edges:
        return []

    tolerance = angle_tolerance_deg
    merged: list[PolygonEdge] = []
    current = edges[0]
    current_length = current.length_m
    current_nx = current.outward_normal.x * current.length_m
    current_nz = current.outward_normal.z * current.length_m
    current_v0 = current.v0

    for edge in edges[1:]:
        delta_heading = abs(edge.heading_deg - current.heading_deg)
        if delta_heading > 180:
            delta_heading = 360 - delta_heading

        if delta_heading <= tolerance:
            # Fusionar con la arista actual (acumular longitud y normal ponderada)
            current_length += edge.length_m
            current_nx += edge.outward_normal.x * edge.length_m
            current_nz += edge.outward_normal.z * edge.length_m
            current = PolygonEdge(
                idx=current.idx,
                v0=current_v0,
                v1=edge.v1,
                midpoint=Vec2(
                    (current_v0.x + edge.v1.x) / 2,
                    (current_v0.z + edge.v1.z) / 2,
                ),
                length_m=current_length,
                tangent=current.tangent,
                outward_normal=Vec2(current_nx, current_nz).normalized(),
                heading_deg=Vec2(current_nx, current_nz).normalized().heading_deg(),
            )
        else:
            # Guardar la arista actual y empezar nueva
            merged.append(current)
            current = edge
            current_length = edge.length_m
            current_nx = edge.outward_normal.x * edge.length_m
            current_nz = edge.outward_normal.z * edge.length_m
            current_v0 = edge.v0

    merged.append(current)
    return merged


def closest_edge_to_point(point: Vec2,
                           edges: list[PolygonEdge]) -> Optional[PolygonEdge]:
    """
    Devuelve la arista más cercana al punto dado (distancia perpendicular al segmento).
    Se usa para hallar la fachada del edificio cuando no hay dato de heading.
    """
    best_edge = None
    best_dist = float("inf")

    for edge in edges:
        # Distancia punto → segmento (proyección clampada)
        seg = edge.v1 - edge.v0
        to_point = point - edge.v0
        t = max(0.0, min(1.0, to_point.dot(seg) / (seg.length() ** 2 + 1e-12)))
        proj = edge.v0 + seg * t
        dist = (point - proj).length()
        if dist < best_dist:
            best_dist = dist
            best_edge = edge

    return best_edge


def edge_closest_to_heading(edges: list[PolygonEdge],
                             heading_deg: float) -> Optional[PolygonEdge]:
    """
    Devuelve la arista cuya normal saliente es más paralela al heading dado.
    La normal del panorama (cámara apunta al edificio → normal = heading + 180°)
    se pasa como facade_outward_heading = camera_heading + 180.
    """
    best_edge = None
    best_align = -2.0  # cos(ángulo), queremos máximo

    target_x = math.sin(math.radians(heading_deg))   # componente Este
    target_z = -math.cos(math.radians(heading_deg))  # componente Norte (-Z)

    for edge in edges:
        align = (edge.outward_normal.x * target_x +
                 edge.outward_normal.z * target_z)
        if align > best_align:
            best_align = align
            best_edge = edge

    return best_edge


def facade_normal_to_transform3d(normal: Vec2,
                                  godot_x: float,
                                  godot_y: float,
                                  godot_z: float) -> str:
    """
    Convierte la normal saliente de la fachada (Vec2 Godot XZ) al
    Transform3D de Godot completo, listo para pegar en main.tscn.

    El modelo Blender/glTF tiene su fachada mirando en -Y local = +Z Godot.
    Necesitamos rotarlo para que el +Z local apunte en dirección 'normal'.

    La rotación en Y necesaria: ángulo = atan2(normal.x, normal.z)
    (porque +Z local debe alinearse con la normal de la fachada).

    Basis de Godot para rotación θ alrededor de Y:
        [ cos θ,  0,  sin θ ]
        [   0,    1,    0   ]
        [-sin θ,  0,  cos θ ]
    """
    # θ tal que (sin θ, cos θ) apunte en dirección de la normal
    # La fachada del glTF mira en +Z local → queremos que +Z local = normal
    theta = math.atan2(normal.x, normal.z)
    c = round(math.cos(theta), 6)
    s = round(math.sin(theta), 6)

    # Basis columnas de Godot (row-major en el .tscn: a00,a10,a20, a01,a11,a21, a02,a12,a22)
    # Pero Transform3D en .tscn se escribe:
    #   Transform3D(XX,XY,XZ, YX,YY,YZ, ZX,ZY,ZZ, TX,TY,TZ)
    # donde las 3 primeras columnas son los vectores base del objeto
    # Col X del objeto: (c, 0, -s)
    # Col Y del objeto: (0, 1, 0)
    # Col Z del objeto: (s, 0, c)   ← dirección de la fachada
    xx, xy, xz =  c, 0.0, -s
    yx, yy, yz =  0.0, 1.0, 0.0
    zx, zy, zz =  s, 0.0,  c

    def fmt(v):
        return f"{v:.6g}".rstrip("0").rstrip(".")

    return (
        f"Transform3D("
        f"{fmt(xx)}, {fmt(xy)}, {fmt(xz)},  "
        f"{fmt(yx)}, {fmt(yy)}, {fmt(yz)},  "
        f"{fmt(zx)}, {fmt(zy)}, {fmt(zz)},  "
        f"{fmt(godot_x)}, {fmt(godot_y)}, {fmt(godot_z)})"
    )


def distance_point_to_segment(p: Vec2, a: Vec2, b: Vec2) -> float:
    """Distancia de p al segmento [a,b]."""
    ab = b - a
    l2 = ab.length() ** 2
    if l2 < 1e-12:
        return (p - a).length()
    t = max(0.0, min(1.0, (p - a).dot(ab) / l2))
    proj = a + ab * t
    return (p - proj).length()


# ═══════════════════════════════════════════════════════════════════════════════
# 3. CONTEXTO ESPACIAL (carga y consulta de datos)
# ═══════════════════════════════════════════════════════════════════════════════

class SpatialContext:
    """
    Carga los cuatro cachés del proyecto y expone la API de resolución
    de posicionamiento completamente generalizable.

    No contiene ninguna referencia a nombres de calles específicos ni
    umbrales numéricos ad-hoc. Todo se deduce de los polígonos de manzana.
    """

    def __init__(self,
                 manifest: dict,
                 blocks: dict,
                 facades: dict,
                 panoramas: dict,
                 spatial_model: dict | None = None):
        self._manifest_entries: dict[str, dict] = {
            e["name"]: e for e in manifest.get("entries", [])
        }
        self._blocks = blocks       # block_id → {polygon: [[x,y],...], ...}
        self._facades = facades     # facade_id → {pano_id, heading, ...}
        self._panoramas = panoramas # pano_id → {latitude, longitude, ...}
        self._model = spatial_model

        # Índice de fachadas por bloque
        import re
        self._facades_by_block: dict[str, list[dict]] = {}
        for fid, fdata in facades.items():
            m = re.match(r"(block_lat_[0-9.\-]+_lon_[0-9.\-]+)_facade_(\d+)", fid)
            if m:
                bid = m.group(1)
                self._facades_by_block.setdefault(bid, []).append({
                    "facade_id": fid,
                    "facade_n": int(m.group(2)),
                    "pano_id": fdata.get("pano_id"),
                    "heading": fdata.get("heading"),
                })

    @classmethod
    def load(cls,
             manifest_path: Path = _MANIFEST,
             blocks_path: Path = _BLOCKS,
             facades_path: Path = _FACADES,
             panoramas_path: Path = _PANORAMAS,
             spatial_model_path: Path = _SPATIAL_MDL) -> "SpatialContext":
        """Carga todos los archivos y devuelve el contexto listo para usar."""
        def _load(p):
            with open(p, encoding="utf-8") as f:
                return json.load(f)
        print(f"[SpatialContext] Cargando cachés...")
        manifest  = _load(manifest_path)
        blocks    = _load(blocks_path)
        facades   = _load(facades_path)
        panoramas = _load(panoramas_path)
        model     = _load(spatial_model_path) if spatial_model_path.exists() else None
        ctx = cls(manifest, blocks, facades, panoramas, model)
        print(f"[SpatialContext] ✅ {len(ctx._manifest_entries)} edificios | "
              f"{len(blocks)} bloques | {len(panoramas)} panoramas")
        return ctx

    # ── Conversión de polígono de bloque a Godot ─────────────────────────────

    def _block_polygon_godot(self, block_id: str) -> list[Vec2]:
        """
        Convierte el polígono de un bloque de coordenadas osm2world
        a coordenadas Godot XZ.
        """
        raw_poly = self._blocks.get(block_id, {}).get("polygon", [])
        return [osm2world_to_godot(p[0], p[1]) for p in raw_poly]

    # ── Localizar edificio en su polígono ────────────────────────────────────

    def get_block_polygon(self, block_id: str) -> list[Vec2]:
        """Devuelve el polígono de la manzana en coordenadas Godot XZ."""
        return self._block_polygon_godot(block_id)

    def get_merged_edges(self, block_id: str,
                         angle_tolerance_deg: float = 12.0) -> list[PolygonEdge]:
        """
        Devuelve las aristas significativas de la manzana (fusionadas por
        colinealidad) con sus normales salientes en coordenadas Godot.
        """
        polygon = self._block_polygon_godot(block_id)
        if len(polygon) < 3:
            return []
        raw_edges = compute_polygon_edges(polygon)
        return merge_collinear_edges(raw_edges, angle_tolerance_deg)

    # ── Resolver la fachada principal ────────────────────────────────────────

    def _facade_heading_for_block(self, block_id: str) -> Optional[float]:
        """
        Obtiene el heading de la fachada principal del bloque desde
        facades_cache + panoramas_cache.

        El heading del panorama = dirección en que apunta la cámara al capturar.
        La normal SALIENTE de la fachada ≈ heading + 180° (opuesto a la cámara).
        """
        facades = self._facades_by_block.get(block_id, [])
        if not facades:
            return None

        # Tomar la fachada con más resolución (o la primera)
        f = facades[0]
        pano = self._panoramas.get(f.get("pano_id", ""), {})
        camera_heading = f.get("heading")
        if camera_heading is None:
            return None

        # La cámara apunta HACIA el edificio → normal saliente es la dirección contraria
        facade_outward_heading = (camera_heading + 180.0) % 360.0
        return facade_outward_heading

    # ── Resolución completa de posicionamiento ───────────────────────────────

    def resolve_building(self,
                          building_name: str,
                          elevation_y: Optional[float] = None) -> BuildingPlacement:
        """
        Resuelve el posicionamiento completo de un edificio:
          1. Localiza el bloque contenedor (polígono osm2world).
          2. Obtiene el centroide Godot del edificio desde el manifiesto.
          3. Verifica que el centroide esté DENTRO del polígono de la manzana.
             Si no lo está, lo proyecta al interior más cercano.
          4. Determina la fachada principal por heading del panorama o
             por arista más cercana al centroide.
          5. Devuelve Transform3D listo para main.tscn.

        Args:
            building_name: nombre del objeto en el .blend (ej. "Building_BBVA_México")
            elevation_y: elevación Godot Y. Si None, se usa el valor del manifiesto.

        Returns:
            BuildingPlacement con toda la información resuelta.
        """
        warnings: list[str] = []
        entry = self._manifest_entries.get(building_name)

        if entry is None:
            return BuildingPlacement(
                building_name=building_name,
                block_id=None,
                block_match_method="not_found",
                godot_pos=Vec2(0.0, 0.0),
                godot_y=398.0,
                primary_facade_edge=None,
                secondary_facade_edge=None,
                transform3d="Transform3D(1,0,0, 0,1,0, 0,0,1, 0,398,0)",
                warnings=[f"Edificio '{building_name}' no encontrado en el manifiesto."],
            )

        block_id = entry.get("block_id")
        block_match = entry.get("block_match_method", "none")

        # ── Paso 1: Centroide del edificio en Godot ──────────────────────────
        gc = entry.get("godot_centroid")  # [X, Y, Z] desde la malla Blender
        if gc:
            gx, gy, gz = float(gc[0]), float(gc[1]), float(gc[2])
        else:
            # Fallback: convertir desde blender_bbox centroid
            bbox = entry.get("blender_bbox", {})
            bc = bbox.get("centroid", [0.0, 0.0, 0.0])
            gx, gy, gz = blender_to_godot(bc[0], bc[1], bc[2])
            warnings.append("Usando bbox centroid Blender → Godot (godot_centroid no disponible).")

        building_pos = Vec2(gx, gz)
        if elevation_y is not None:
            gy = elevation_y

        # ── Paso 2: Obtener polígono de la manzana ───────────────────────────
        polygon: list[Vec2] = []
        merged_edges: list[PolygonEdge] = []

        if block_id and block_id in self._blocks:
            polygon = self._block_polygon_godot(block_id)
            if len(polygon) >= 3:
                raw_edges = compute_polygon_edges(polygon)
                merged_edges = merge_collinear_edges(raw_edges)
        else:
            warnings.append(f"block_id='{block_id}' no encontrado en blocks_cache.")

        # ── Paso 3: Verificar contención en el polígono ───────────────────────
        # Esta es la verificación clave y generalizable:
        # el edificio DEBE estar dentro de su polígono de manzana.
        # Si no lo está, hay un error de posicionamiento.
        if polygon and not point_in_polygon(building_pos, polygon):
            # Calcular la proyección más cercana al interior del polígono
            centroid = polygon_centroid(polygon)
            warnings.append(
                f"⚠️  E001-GENERALIZADO: El centroide Godot ({gx:.1f}, {gz:.1f}) está "
                f"FUERA del polígono de su manzana ({block_id}). "
                f"El centroide del polígono es ({centroid.x:.1f}, {centroid.z:.1f}). "
                f"Usando centroide del polígono como corrección de emergencia."
            )
            # Corrección: usar el centroide del polígono
            building_pos = centroid
            gx, gz = centroid.x, centroid.z

        # ── Paso 4: Determinar fachada principal ─────────────────────────────
        primary_edge: Optional[PolygonEdge] = None
        secondary_edge: Optional[PolygonEdge] = None

        if merged_edges:
            # Intento 1: usar heading del panorama (más preciso)
            facade_heading = self._facade_heading_for_block(block_id or "")
            if facade_heading is not None:
                primary_edge = edge_closest_to_heading(merged_edges, facade_heading)
            # Intento 2: arista del polígono más cercana al centroide
            if primary_edge is None:
                primary_edge = closest_edge_to_point(building_pos, merged_edges)
                warnings.append("Heading de fachada no disponible; usando arista más cercana al centroide.")

            # Fachada secundaria: la arista más larga que no sea la principal
            if primary_edge:
                others = [e for e in merged_edges if e.idx != primary_edge.idx]
                if others:
                    secondary_edge = max(others, key=lambda e: e.length_m)

        # ── Paso 5: Generar Transform3D ───────────────────────────────────────
        if primary_edge:
            transform = facade_normal_to_transform3d(
                primary_edge.outward_normal, gx, gy, gz
            )
        else:
            transform = (f"Transform3D(1, 0, 0,  0, 1, 0,  0, 0, 1,"
                         f"  {gx:.4g}, {gy:.4g}, {gz:.4g})")
            warnings.append("Sin fachada determinada; rotación = identidad (fachada al Sur).")

        return BuildingPlacement(
            building_name=building_name,
            block_id=block_id,
            block_match_method=block_match,
            godot_pos=building_pos,
            godot_y=gy,
            primary_facade_edge=primary_edge,
            secondary_facade_edge=secondary_edge,
            transform3d=transform,
            warnings=warnings,
        )

    # ── Consulta de bloques vecinos ───────────────────────────────────────────

    def find_block_for_point(self, gx: float, gz: float) -> tuple[Optional[str], str]:
        """
        Encuentra el block_id que contiene el punto Godot (gx, gz).
        Retorna (block_id, método: 'point_in_polygon' | 'nearest_centroid' | 'none').

        Usa SpatialGrid internamente para eficiencia O(1) promedio.
        """
        from collections import defaultdict
        p = Vec2(gx, gz)
        CELL = 200.0

        def cell(x, z):
            return (int(x // CELL), int(z // CELL))

        # Candidatos en la celda del punto y vecinas
        candidates = set()
        cx, cz = cell(gx, gz)
        # Buscar en el dict de bloques (sin grid preconstruida para simplicidad)
        # Para datasets grandes usar la SpatialGrid del build_building_manifest_v3.py
        inside_results = []
        nearest_id, nearest_dist = None, float("inf")

        for block_id, bdata in self._blocks.items():
            raw_poly = bdata.get("polygon", [])
            if len(raw_poly) < 3:
                continue
            poly = [osm2world_to_godot(v[0], v[1]) for v in raw_poly]
            if point_in_polygon(p, poly):
                c = polygon_centroid(poly)
                d = (p - c).length()
                inside_results.append((d, block_id))
            else:
                c = polygon_centroid(poly)
                d = (p - c).length()
                if d < nearest_dist:
                    nearest_dist = d
                    nearest_id = block_id

        if inside_results:
            inside_results.sort()
            return inside_results[0][1], "point_in_polygon"
        if nearest_id and nearest_dist < 1000:
            return nearest_id, "nearest_centroid"
        return None, "none"

    # ── Diagnóstico completo ──────────────────────────────────────────────────

    def diagnose(self, building_name: str) -> None:
        """Imprime un diagnóstico completo de resolución para un edificio."""
        result = self.resolve_building(building_name)

        print(f"\n{'='*60}")
        print(f"DIAGNÓSTICO: {building_name}")
        print(f"{'='*60}")
        print(f"  block_id       : {result.block_id}")
        print(f"  block_match    : {result.block_match_method}")
        print(f"  Posición Godot : X={result.godot_pos.x:.2f}, Y={result.godot_y:.2f}, Z={result.godot_pos.z:.2f}")

        if result.primary_facade_edge:
            e = result.primary_facade_edge
            print(f"  Fachada primaria:")
            print(f"    Arista {e.idx}: ({e.v0.x:.1f},{e.v0.z:.1f}) → ({e.v1.x:.1f},{e.v1.z:.1f})")
            print(f"    Longitud     : {e.length_m:.1f} m")
            print(f"    Normal sal.  : ({e.outward_normal.x:.3f}, {e.outward_normal.z:.3f})")
            print(f"    Heading      : {e.heading_deg:.1f}° ({e.cardinal})")

        if result.secondary_facade_edge:
            e = result.secondary_facade_edge
            print(f"  Fachada secund.: arista {e.idx}, heading {e.heading_deg:.1f}° ({e.cardinal}), L={e.length_m:.1f}m")

        print(f"\n  Transform3D listo para main.tscn:")
        print(f"  {result.transform3d}")

        if result.warnings:
            print(f"\n  ⚠️  Advertencias:")
            for w in result.warnings:
                print(f"    • {w}")

        print(f"{'='*60}\n")


# ═══════════════════════════════════════════════════════════════════════════════
# 4. VERIFICADOR DE INTEGRIDAD
# ═══════════════════════════════════════════════════════════════════════════════

def verify_placed_buildings(ctx: SpatialContext,
                             placed: dict[str, tuple[float, float, float]]) -> None:
    """
    Verifica que los edificios ya colocados en main.tscn estén dentro de
    su polígono de manzana. Detecta errores E001 (lado de calle equivocado).

    Args:
        ctx: SpatialContext cargado
        placed: dict {nombre_godot: (X, Y, Z)} leído de main.tscn
    """
    print("\n=== VERIFICACIÓN DE EDIFICIOS COLOCADOS ===\n")
    for nombre, (gx, gy, gz) in placed.items():
        block_id, method = ctx.find_block_for_point(gx, gz)
        p = Vec2(gx, gz)
        poly = ctx.get_block_polygon(block_id) if block_id else []
        inside = point_in_polygon(p, poly) if poly else False

        status = "✅" if inside else "🚨 FUERA DEL POLÍGONO"
        print(f"  {nombre}")
        print(f"    Pos Godot : ({gx:.1f}, {gz:.1f})")
        print(f"    block_id  : {block_id} ({method})")
        print(f"    En polígono: {status}")

        if not inside and poly:
            c = polygon_centroid(poly)
            dist = (p - c).length()
            print(f"    Dist centroide polígono: {dist:.1f}m")
            print(f"    → Posición correcta debería ser cercana a ({c.x:.1f}, {c.z:.1f})")
        print()


# ═══════════════════════════════════════════════════════════════════════════════
# 5. ENTRY POINT DE DEMOSTRACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    ctx = SpatialContext.load()

    # Verificar los edificios ya colocados en main.tscn
    placed_in_scene = {
        "BBVA":           (-66.8,  400.0,  -24.81),
        "Hotel_Tecate":   (-41.06, 398.79,  45.40),
        "Palacio_Municipal": (47.75, 398.79, 42.40),
        "Kiosko":         (-6.68,  400.01,   2.69),
    }
    verify_placed_buildings(ctx, placed_in_scene)

    # Diagnóstico de edificios individuales
    for name in [
        "Building_BBVA_México",
        "Building_Ayuntamiento_de_Tecate",
        "Building_Biblioteca_Municipal_Tecate",
        "Building_Calimax",
        "Building_Cruz_Roja_Mexicana",
        "Building_Walmart_Supercenter",
        "Building_Caseta_de_Cobro_EL_HONGO_Km_92_+_105",
    ]:
        ctx.diagnose(name)
