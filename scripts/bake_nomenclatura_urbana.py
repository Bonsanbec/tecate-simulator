"""
=============================================================================
Compilador Pre-Bake de Nomenclatura Urbana - Tecate Simulator
=============================================================================
Este script automatiza la generación ultraeficiente e idempotente de la red
de postes de nomenclatura urbana para todo el simulador (Godot Engine 4):
1. Ingesta el grafo vial de OpenStreetMap (road_osm.json).
2. Detecta esquinas de manzana en todas las intersecciones viales con debounce >= 5.0m.
3. Calcula la orientación óptima de yaw para alinear ambas placas en paralelo
   a las vías de la intersección.
4. Muestrea la elevación exacta del terreno en tecate2.glb (BVHTree).
5. Estandariza los nombres de calles en mayúsculas rigurosas con prefijos en la
   esquina superior izquierda del recuadro verde.
6. Reserva el recuadro blanco para iconos PNG deterministas (ciclados desde assets/nomenclatura_icons/).
7. Genera de forma desacoplada:
   - nomenclatura_textos_baked.glb (Malla consolidada de textos 3D en blanco, Bfont).
   - nomenclatura_iconos_baked.glb (Quads de calcomanías UV mapeadas para iconos PNG).
8. Soporta banderas de compilación incremental:
   --icons-only (-i): Regenera únicamente las imágenes/iconos en < 1.5s conservando los textos ya procesados.
   --text-only (-t): Regenera únicamente los textos 3D conservando los iconos.
   --full (-f): Ejecuta el flujo completo (análisis topográfico, textos, iconos y escenas).
9. Escribe los datos de posicionamiento en nomenclatura_data.json y nomenclatura_corners.json,
   generando la escena nomenclatura_urbana.tscn con MultiMeshInstance3D referenciando
   poste_nomenclatura_tecate.glb (CERO copiado, actualización 100% idempotente).
=============================================================================
"""

import os
import sys
import json
import math
import struct
import glob
import re
import time
from collections import defaultdict

try:
    import bpy
    import bmesh
    import mathutils
    from mathutils import Vector, Matrix
    from mathutils.bvhtree import BVHTree
except ImportError:
    bpy = None
    bmesh = None
    mathutils = None
    Vector = None
    Matrix = None
    BVHTree = None

# ─────────────────────────────────────────────────────────────────────────────
# 1. Constantes Geodésicas y Rutas
# ─────────────────────────────────────────────────────────────────────────────
TECATE_LAT_CENTER = 32.573229
TECATE_LON_CENTER = -116.626536
EARTH_RADIUS = 6378137.0
LAT_C_RAD = math.radians(TECATE_LAT_CENTER)
LON_C_RAD = math.radians(TECATE_LON_CENTER)
COS_LAT_C = math.cos(LAT_C_RAD)

ROAD_OSM_PATH = "godot_project/assets/osm_cache/road_osm.json"
TERRAIN_GLB_PATH = "godot_project/assets/tecate2.glb"
ICONS_DIR = "godot_project/assets/nomenclatura_icons"
POSTE_BASE_GLB = "godot_project/assets/poste_nomenclatura_tecate.glb"
OUT_TEXTOS_GLB = "godot_project/assets/nomenclatura_textos_baked.glb"
OUT_ICONOS_GLB = "godot_project/assets/nomenclatura_iconos_baked.glb"
OUT_DATA_JSON = "godot_project/assets/nomenclatura_data.json"
OUT_CORNERS_JSON = "godot_project/assets/nomenclatura_corners.json"
OUT_SCENE_TSCN = "godot_project/assets/nomenclatura_urbana.tscn"
OUT_SCRIPT_GD = "godot_project/assets/nomenclatura_urbana.gd"

def gps_to_local(lat: float, lon: float) -> tuple[float, float]:
    """Convierte WGS84 GPS a coordenadas locales Cartesianas (metros) centradas en Parque Hidalgo."""
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    x = EARTH_RADIUS * (lon_rad - LON_C_RAD) * COS_LAT_C
    y = EARTH_RADIUS * (lat_rad - LAT_C_RAD)
    return x, y

# ─────────────────────────────────────────────────────────────────────────────
# 2. BVHTree de Terreno para Rasante Vertical
# ─────────────────────────────────────────────────────────────────────────────
def build_terrain_bvh(glb_path: str):
    """Carga tinMesh de tecate2.glb y construye un BVHTree para proyectar la cota de suelo."""
    print(f"[Terreno] Cargando malla topográfica desde: {glb_path}")
    if not os.path.exists(glb_path):
        print(f"[Aviso] No se encontró {glb_path}. Se usará cota rasante por defecto (400.0 m).")
        return None

    with open(glb_path, "rb") as f:
        f.read(12)
        chunk_len, _ = struct.unpack("<II", f.read(8))
        gltf = json.loads(f.read(chunk_len).decode("utf-8"))
        f.seek(12 + 8 + chunk_len)
        f.read(8)
        binary_data = f.read()

    tin_mesh_idx = 0
    for node in gltf.get("nodes", []):
        if node.get("name") == "tinMesh":
            tin_mesh_idx = node.get("mesh", 0)
            break

    tin_prim = gltf["meshes"][tin_mesh_idx]["primitives"][0]
    pos_acc = gltf["accessors"][tin_prim["attributes"]["POSITION"]]
    pos_bv = gltf["bufferViews"][pos_acc["bufferView"]]
    pos_offset = pos_bv.get("byteOffset", 0) + pos_acc.get("byteOffset", 0)
    pos_count = pos_acc["count"]

    import numpy as np
    raw_verts = np.frombuffer(
        binary_data[pos_offset : pos_offset + pos_count * 12],
        dtype=np.float32
    ).reshape(pos_count, 3)

    idx_acc = gltf["accessors"][tin_prim["indices"]]
    idx_bv = gltf["bufferViews"][idx_acc["bufferView"]]
    idx_offset = idx_bv.get("byteOffset", 0) + idx_acc.get("byteOffset", 0)
    idx_count = idx_acc["count"]
    indices = np.frombuffer(
        binary_data[idx_offset : idx_offset + idx_count * 4],
        dtype=np.uint32
    ).reshape(-1, 3)

    # Escala y traslación de tecate2 en Godot
    s = 0.8427785648661434
    tx = 28057.9043
    tz = 16614.8854

    world_x = s * raw_verts[:, 0] + tx
    world_y = s * raw_verts[:, 1]
    world_z = s * raw_verts[:, 2] + tz

    # Convención Blender: X=East, Y=North (-world_z), Z=Height (world_y)
    bvh_verts = [mathutils.Vector((world_x[i], -world_z[i], world_y[i])) for i in range(pos_count)]
    bvh_polys = [tuple(indices[i]) for i in range(len(indices))]

    bvh = BVHTree.FromPolygons(bvh_verts, bvh_polys, all_triangles=True)
    print(f"[Terreno] BVHTree generado exitosamente ({len(bvh_verts):,} vértices).")
    return bvh

def get_terrain_height(bvh, x: float, y: float, default_h: float = 400.0) -> float:
    """Obtiene la altura Z (cota de banqueta) proyectando un rayo vertical en (x, y)."""
    if bvh is None:
        return default_h
    origin = mathutils.Vector((x, y, 2000.0))
    direction = mathutils.Vector((0.0, 0.0, -1.0))
    hit, _, _, _ = bvh.ray_cast(origin, direction, 3500.0)
    return hit.z if hit is not None else default_h

# ─────────────────────────────────────────────────────────────────────────────
# 3. Normalizador y Formateador Tipográfico de Calles
# ─────────────────────────────────────────────────────────────────────────────
PREFIX_PATTERNS = [
    (r"^(?:CALLE\s+)?(?:PRESIDENTE|PDTE\.?)\s+", "PDTE."),
    (r"^(?:AVENIDA|AV\.?)\s+", "AV."),
    (r"^(?:BOULEVARD|BULEVAR|BLVD\.?)\s+", "BLVD."),
    (r"^(?:CALLEJ[OÓ]N|CJ[OÓ]N\.?)\s+", "CJÓN."),
    (r"^(?:CALZADA|CALZ\.?)\s+", "CALZ."),
    (r"^PASEO\s+", "PASEO"),
    (r"^(?:CARRETERA|CARR\.?)\s+", "CARR."),
    (r"^(?:PROLONGACI[OÓ]N|PROL\.?)\s+", "PROL."),
    (r"^CALLE\s+", "C."),
    (r"^C\.\s+", "C."),
]

SUB_ABBREVIATIONS = [
    (r"\bGENERAL\b", "GRAL."),
    (r"\bLICENCIADO\b", "LIC."),
    (r"\bDOCTOR\b", "DR."),
    (r"\bPROFESOR\b", "PROFR."),
    (r"\bINGENIERO\b", "ING."),
    (r"\bPRESIDENTE\b", "PDTE."),
]

def standardize_street_name(raw_name: str) -> tuple[str, str]:
    """
    Estandariza un nombre vial para rotulación en placas:
    Retorna (prefijo, nombre_principal) en MAYÚSCULAS con acentuación rigurosa.
    """
    name = raw_name.strip().upper()
    prefix = ""
    main_name = name

    for pat, pref in PREFIX_PATTERNS:
        m = re.match(pat, main_name)
        if m:
            prefix = pref
            main_name = main_name[m.end():].strip()
            break

    for pat, repl in SUB_ABBREVIATIONS:
        main_name = re.sub(pat, repl, main_name)

    main_name = re.sub(r"\s+", " ", main_name).strip()

    # Si el nombre es muy largo (> 18 caracteres), compactar palabras comunes
    if len(main_name) > 18:
        main_name = main_name.replace("BAJA CALIFORNIA", "B.C.")
        main_name = main_name.replace("DE LA ", "")
        main_name = main_name.replace("DE LOS ", "")
        main_name = main_name.replace("DEL ", "")

    return prefix, main_name

# ─────────────────────────────────────────────────────────────────────────────
# 4. Extracción Geométrica de Intersecciones y Esquinas de Manzana
# ─────────────────────────────────────────────────────────────────────────────
def extract_corners_with_debounce(road_osm_path: str, min_debounce_m: float = 5.0):
    """
    Construye el grafo vial de OSM y extrae las esquinas de manzana de cada cruce.
    Aplica filtro de debounce espacial >= 5.0m para evitar duplicidades.
    """
    print(f"[OSM] Cargando datos viales desde: {road_osm_path}")
    with open(road_osm_path, "r", encoding="utf-8") as f:
        roads_data = json.load(f)

    adj = defaultdict(list)
    node_coords = {}
    ways = [e for e in roads_data.get("elements", []) if e.get("type") == "way"]
    named_ways = [w for w in ways if "name" in w.get("tags", {})]

    for w in named_ways:
        name = w["tags"]["name"]
        nodes = w.get("nodes", [])
        geom = w.get("geometry", [])
        for i in range(len(nodes)):
            nid = nodes[i]
            if nid not in node_coords and i < len(geom):
                node_coords[nid] = gps_to_local(geom[i]["lat"], geom[i]["lon"])
        for i in range(len(nodes) - 1):
            u, v = nodes[i], nodes[i+1]
            ux, uy = node_coords[u]
            vx, vy = node_coords[v]
            d = math.hypot(vx - ux, vy - uy)
            if d > 0.1:
                adj[u].append((v, name, (vx - ux)/d, (vy - uy)/d, math.atan2(vy - uy, vx - ux)))
                adj[v].append((u, name, (ux - vx)/d, (uy - vy)/d, math.atan2(uy - vy, ux - vx)))

    raw_corners = []
    for nid, branches in adj.items():
        distinct_names = set(b[1] for b in branches)
        if len(distinct_names) < 2:
            continue

        cx, cy = node_coords[nid]
        branches_sorted = sorted(branches, key=lambda b: (b[4] + 2*math.pi) % (2*math.pi))
        m = len(branches_sorted)
        if m < 2:
            continue

        for i in range(m):
            b1 = branches_sorted[i]
            b2 = branches_sorted[(i + 1) % m]

            # Si ambas ramas son la misma calle continuando en línea recta, no es esquina
            if b1[1] == b2[1]:
                continue

            a1 = (b1[4] + 2*math.pi) % (2*math.pi)
            a2 = (b2[4] + 2*math.pi) % (2*math.pi)
            delta_a = (a2 - a1) % (2*math.pi)

            # Detectar esquina entre 25° y 160°
            if math.radians(25) <= delta_a <= math.radians(160):
                bisector = a1 + delta_a / 2.0
                sin_half = math.sin(delta_a / 2.0)
                offset_dist = min(max(3.6 / sin_half, 3.8), 7.0)

                px = cx + offset_dist * math.cos(bisector)
                py = cy + offset_dist * math.sin(bisector)

                raw_corners.append({
                    "pos": (px, py),
                    "streets": (b1[1], b2[1]),
                    "v1": (b1[2], b1[3]),
                    "v2": (b2[2], b2[3]),
                    "node_id": nid
                })

    print(f"[Geometría] Esquinas candidatas detectadas: {len(raw_corners)}")

    # Filtro de Debounce espacial estricto (>= 5.0m)
    debounced = []
    for cand in raw_corners:
        px, py = cand["pos"]
        too_close = False
        for ex in debounced:
            if math.hypot(px - ex["pos"][0], py - ex["pos"][1]) < min_debounce_m:
                too_close = True
                break
        if not too_close:
            debounced.append(cand)

    print(f"[Geometría] Esquinas finales debounced (>= {min_debounce_m}m): {len(debounced)}")
    return debounced

# ─────────────────────────────────────────────────────────────────────────────
# 5. Cálculo de Paralelismo Óptimo de Placas
# ─────────────────────────────────────────────────────────────────────────────
def calculate_optimal_post_orientation(v1: tuple[float, float], v2: tuple[float, float]) -> float:
    """
    Calcula el ángulo de yaw óptimo (radianes) para que:
    - Placa Inferior (eje X local) quede lo más paralela posible a Street 1.
    - Placa Superior (eje Y local, a 90°) quede lo más paralela posible a Street 2.
    Devuelve: yaw_rad.
    """
    best_err = 1e9
    best_yaw = 0.0

    for s1 in [1.0, -1.0]:
        t1 = math.atan2(s1 * v1[1], s1 * v1[0])
        for s2 in [1.0, -1.0]:
            t2 = math.atan2(s2 * v2[1], s2 * v2[0])

            diff_t = (t2 - math.pi / 2.0) - t1
            diff_t = (diff_t + math.pi) % (2 * math.pi) - math.pi
            psi = t1 + 0.5 * diff_t

            e1 = abs((psi - t1 + math.pi) % (2 * math.pi) - math.pi)
            e2 = abs(((psi + math.pi / 2.0) - t2 + math.pi) % (2 * math.pi) - math.pi)
            total_err = e1 + e2

            if total_err < best_err:
                best_err = total_err
                best_yaw = psi

    return best_yaw

# ─────────────────────────────────────────────────────────────────────────────
# 6. Generador de Textos 3D en Blender (BMesh Ultra-Rápido, Desacoplado)
# ─────────────────────────────────────────────────────────────────────────────
def _get_or_create_text_mesh(scene, depsgraph, mesh_cache, text_body, font_size, align_x, align_y):
    """Obtiene de caché o crea una malla a partir de una curva tipográfica."""
    key = (text_body, round(font_size, 4), align_x, align_y)
    if key in mesh_cache:
        return mesh_cache[key]

    c = bpy.data.curves.new(type="FONT", name="T_Temp")
    c.body = text_body
    c.size = font_size
    c.resolution_u = 1
    c.extrude = 0.0
    c.align_x = align_x
    c.align_y = align_y

    o = bpy.data.objects.new("O_Temp", c)
    scene.collection.objects.link(o)
    bpy.context.view_layer.update()

    eval_o = o.evaluated_get(depsgraph)
    me = bpy.data.meshes.new_from_object(eval_o)

    scene.collection.objects.unlink(o)
    bpy.data.objects.remove(o)
    bpy.data.curves.remove(c)

    mesh_cache[key] = me
    return me

def _accumulate_plate_text(bm_dest, scene, depsgraph, mesh_cache, mat_world, prefix, main_name, plate_type, plate_z):
    """
    Acumula exclusivamente las letras 3D de una placa (frente y dorso) en bm_dest.
    Material slot: 0 (M_Texto_Rotulo_Blanco).
    """
    is_lower = (plate_type == "LOWER")

    if prefix:
        f_size_main = 0.052
        if len(main_name) > 13:
            f_size_main = max(0.032, 0.54 / (len(main_name) * 0.82))
        f_size_pref = 0.024
    else:
        f_size_main = 0.058
        if len(main_name) > 13:
            f_size_main = max(0.035, 0.56 / (len(main_name) * 0.82))
        f_size_pref = 0.0

    mat_upright = Matrix.Rotation(math.radians(90.0), 4, 'X')

    for side in [1.0, -1.0]:
        if is_lower:
            y_offset = 0.0105 * side
            rot_local = Matrix.Rotation(0.0 if side > 0 else math.pi, 4, 'Y')
            t_loc = Vector((-0.13 * side, plate_z - (0.015 if prefix else 0.0), y_offset))
            p_loc = Vector((-0.41 * side, plate_z + 0.06, y_offset)) if prefix else None
        else:
            x_offset = 0.0105 * side
            rot_local = Matrix.Rotation(math.pi / 2.0 if side > 0 else -math.pi / 2.0, 4, 'Y')
            t_loc = Vector((x_offset, plate_z - (0.015 if prefix else 0.0), -0.13 * (-side)))
            p_loc = Vector((x_offset, plate_z + 0.06, -0.41 * (-side))) if prefix else None

        # 1. Texto principal
        me_main = _get_or_create_text_mesh(scene, depsgraph, mesh_cache, main_name, f_size_main, 'CENTER', 'CENTER')
        mat_text_local = Matrix.Translation(t_loc) @ rot_local @ mat_upright
        mat_text_final = mat_world @ mat_text_local

        v_start = len(bm_dest.verts)
        bm_dest.from_mesh(me_main)
        for v in bm_dest.verts[v_start:]:
            v.co = mat_text_final @ v.co

        # 2. Texto de prefijo (si existe)
        if prefix and p_loc:
            align_pref = 'LEFT' if side > 0 else 'RIGHT'
            me_pref = _get_or_create_text_mesh(scene, depsgraph, mesh_cache, prefix, f_size_pref, align_pref, 'TOP')
            mat_pref_local = Matrix.Translation(p_loc) @ rot_local @ mat_upright
            mat_pref_final = mat_world @ mat_pref_local

            v_start_p = len(bm_dest.verts)
            bm_dest.from_mesh(me_pref)
            for v in bm_dest.verts[v_start_p:]:
                v.co = mat_pref_final @ v.co

def build_baked_texts(corners: list, bvh_terrain=None, out_path: str = OUT_TEXTOS_GLB):
    """
    Construye la malla combinada de textos 3D en mayúsculas (blancos, Bfont extruido)
    para toda la ciudad. Exclusivamente textos, sin caras de iconos.
    """
    print(f"\n[Textos] Compilando textos 3D para {len(corners)} esquinas en toda la ciudad...")
    t_start = time.time()

    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    depsgraph = bpy.context.evaluated_depsgraph_get()

    mat_white = bpy.data.materials.new(name="M_Texto_Rotulo_Blanco")
    mat_white.use_nodes = True
    bsdf_t = mat_white.node_tree.nodes.get("Principled BSDF")
    if bsdf_t:
        bsdf_t.inputs["Base Color"].default_value = (0.95, 0.95, 0.95, 1.0)
        bsdf_t.inputs["Roughness"].default_value = 0.35
        bsdf_t.inputs["Metallic"].default_value = 0.0

    bm_consolidated = bmesh.new()
    mesh_cache = {}

    for corner_idx, c_info in enumerate(corners):
        if (corner_idx + 1) % 500 == 0 or corner_idx == 0:
            elapsed = time.time() - t_start
            print(f"  --> Procesando textos esquina {corner_idx + 1}/{len(corners)} ({elapsed:.1f}s transcurridos)...")

        lx, ly = c_info["pos"]
        st1, st2 = c_info["streets"]
        v1, v2 = c_info["v1"], c_info["v2"]

        if "lz" in c_info:
            lz = c_info["lz"]
        elif bvh_terrain is not None:
            lz = get_terrain_height(bvh_terrain, lx, ly, default_h=400.0)
        else:
            lz = 400.0

        if "yaw_rad" in c_info:
            yaw_rad = c_info["yaw_rad"]
        else:
            yaw_rad = calculate_optimal_post_orientation(v1, v2)

        gx, gy, gz = lx, lz, -ly
        g_rot_y = -yaw_rad

        cos_g = math.cos(g_rot_y)
        sin_g = math.sin(g_rot_y)
        mat_post_godot = Matrix((
            (cos_g,  0.0, sin_g, gx),
            (0.0,    1.0, 0.0,   gy),
            (-sin_g, 0.0, cos_g, gz),
            (0.0,    0.0, 0.0,   1.0)
        ))

        # Placa Inferior
        p1, m1 = standardize_street_name(st1)
        _accumulate_plate_text(
            bm_dest=bm_consolidated,
            scene=scene,
            depsgraph=depsgraph,
            mesh_cache=mesh_cache,
            mat_world=mat_post_godot,
            prefix=p1,
            main_name=m1,
            plate_type="LOWER",
            plate_z=2.52
        )

        # Placa Superior
        p2, m2 = standardize_street_name(st2)
        _accumulate_plate_text(
            bm_dest=bm_consolidated,
            scene=scene,
            depsgraph=depsgraph,
            mesh_cache=mesh_cache,
            mat_world=mat_post_godot,
            prefix=p2,
            main_name=m2,
            plate_type="UPPER",
            plate_z=2.74
        )

    print("\n[Textos] Convirtiendo BMesh consolidado a objeto de Blender...")
    final_mesh = bpy.data.meshes.new("Nomenclatura_Textos_Malla")
    bm_consolidated.to_mesh(final_mesh)
    bm_consolidated.free()

    obj_consolidated = bpy.data.objects.new("Nomenclatura_Textos_Consolidados", final_mesh)
    scene.collection.objects.link(obj_consolidated)
    obj_consolidated.data.materials.append(mat_white)

    print(f"[Textos] Exportando archivo consolidado: {out_path}...")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    bpy.ops.object.select_all(action='DESELECT')
    obj_consolidated.select_set(True)
    bpy.context.view_layer.objects.active = obj_consolidated

    bpy.ops.export_scene.gltf(
        filepath=out_path,
        export_format='GLB',
        use_selection=True,
        export_apply=True,
        export_materials='EXPORT',
        export_yup=True
    )
    t_end = time.time()
    print(f"[Textos] Exportación de textos finalizada con éxito en {t_end - t_start:.2f} segundos.")

# ─────────────────────────────────────────────────────────────────────────────
# 7. Generador de Iconos/Calcomanías en Blender (Ultra-Rápido, Desacoplado)
# ─────────────────────────────────────────────────────────────────────────────
def build_baked_icons(items: list, icons_paths: list, out_path: str = OUT_ICONOS_GLB):
    """
    Construye la malla combinada de calcomanías/cuadros de iconos para todas las esquinas.
    Ultra-rápido: genera 16,528 quads y exporta a GLB en < 1 segundo.
    """
    print(f"\n[Iconos] Compilando quads de calcomanías para {len(items)} esquinas...")
    t_start = time.time()

    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene

    icon_materials = []
    for i, p_icon in enumerate(icons_paths):
        icon_name = os.path.splitext(os.path.basename(p_icon))[0]
        m_ico = bpy.data.materials.new(name=f"M_Icon_{icon_name}")
        m_ico.use_nodes = True
        nodes = m_ico.node_tree.nodes
        links = m_ico.node_tree.links
        bsdf_i = nodes.get("Principled BSDF")

        tex_node = nodes.new("ShaderNodeTexImage")
        img = bpy.data.images.load(os.path.abspath(p_icon))
        tex_node.image = img

        links.new(tex_node.outputs["Color"], bsdf_i.inputs["Base Color"])
        if "Alpha" in tex_node.outputs and "Alpha" in bsdf_i.inputs:
            links.new(tex_node.outputs["Alpha"], bsdf_i.inputs["Alpha"])
        bsdf_i.inputs["Roughness"].default_value = 0.4
        m_ico.blend_method = 'BLEND'
        icon_materials.append(m_ico)

    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    mat_upright = Matrix.Rotation(math.radians(90.0), 4, 'X')
    w_half, h_half = 0.11, 0.08
    base_pts = [
        Vector((-w_half, -h_half, 0.0)),
        Vector((w_half, -h_half, 0.0)),
        Vector((w_half, h_half, 0.0)),
        Vector((-w_half, h_half, 0.0))
    ]

    # Configuraciones de las 4 caras de placas:
    # (loc_relativa, rot_relativa)
    plates_config = [
        (Vector((0.31, 2.52, 0.0105)), Matrix.Identity(4)),
        (Vector((-0.31, 2.52, -0.0105)), Matrix.Rotation(math.pi, 4, 'Y')),
        (Vector((0.0105, 2.74, -0.31)), Matrix.Rotation(math.pi / 2.0, 4, 'Y')),
        (Vector((-0.0105, 2.74, 0.31)), Matrix.Rotation(-math.pi / 2.0, 4, 'Y')),
    ]

    for item in items:
        if isinstance(item, dict):
            gx = item.get("gx", item["pos"][0])
            gy = item.get("gy", item.get("lz", 400.0))
            gz = item.get("gz", -item["pos"][1])
            rot_y = item.get("g_rot_y", -item.get("yaw_rad", 0.0))
        else:
            gx, gy, gz, rot_y = item

        cos_g = math.cos(rot_y)
        sin_g = math.sin(rot_y)
        mat_world = Matrix((
            (cos_g,  0.0, sin_g, gx),
            (0.0,    1.0, 0.0,   gy),
            (-sin_g, 0.0, cos_g, gz),
            (0.0,    0.0, 0.0,   1.0)
        ))

        ico_idx = (hash((round(gx, 1), round(-gz, 1))) & 0x7FFFFFFF) % len(icon_materials)

        for loc, rot in plates_config:
            m_final = mat_world @ Matrix.Translation(loc) @ rot @ mat_upright
            v = [bm.verts.new(m_final @ p) for p in base_pts]
            f = bm.faces.new(v)
            f.material_index = ico_idx
            f.loops[0][uv_layer].uv = (0.0, 0.0)
            f.loops[1][uv_layer].uv = (1.0, 0.0)
            f.loops[2][uv_layer].uv = (1.0, 1.0)
            f.loops[3][uv_layer].uv = (0.0, 1.0)

    mesh = bpy.data.meshes.new("Nomenclatura_Iconos_Malla")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("Nomenclatura_Iconos_Consolidados", mesh)
    scene.collection.objects.link(obj)
    for m in icon_materials:
        obj.data.materials.append(m)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(
        filepath=out_path,
        export_format='GLB',
        use_selection=True,
        export_apply=True,
        export_materials='EXPORT',
        export_yup=True
    )
    print(f"[Iconos] Malla exportada en {out_path} ({os.path.getsize(out_path):,} bytes) en {time.time() - t_start:.2f}s.")

# ─────────────────────────────────────────────────────────────────────────────
# 8. Generador de la Escena e Integración en Godot 4
# ─────────────────────────────────────────────────────────────────────────────
def generate_godot_integration(transforms: list):
    """
    Exporta el JSON de datos y genera nomenclatura_urbana.gd y nomenclatura_urbana.tscn
    con MultiMeshInstance3D ultra-eficiente referenciando poste_nomenclatura_tecate.glb.
    """
    print(f"\n[Godot] Escribiendo datos de transformación en: {OUT_DATA_JSON} ({len(transforms)} postes)...")
    data_payload = [
        [round(gx, 3), round(gy, 3), round(gz, 3), round(rot_y, 4)]
        for gx, gy, gz, rot_y in transforms
    ]
    with open(OUT_DATA_JSON, "w", encoding="utf-8") as f:
        json.dump(data_payload, f)
    print("--> JSON de transformaciones guardado.")

    gd_script_content = """@tool
extends Node3D

@export var post_model: PackedScene = preload("res://assets/poste_nomenclatura_tecate.glb")
const DATA_PATH = "res://assets/nomenclatura_data.json"

func _ready() -> void:
	var mm_node = get_node_or_null("MultiMeshInstance3D") as MultiMeshInstance3D
	if not mm_node:
		return

	if not FileAccess.file_exists(DATA_PATH):
		push_warning("[Nomenclatura] No se encontró el archivo: " + DATA_PATH)
		return

	var file = FileAccess.open(DATA_PATH, FileAccess.READ)
	var content = file.get_as_text()
	var json_data = JSON.parse_string(content)
	if not json_data or not (json_data is Array):
		return

	var count = json_data.size()
	var mm = MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.instance_count = count

	# Extraer la malla canónica de poste_nomenclatura_tecate.glb
	if post_model:
		var tmp_inst = post_model.instantiate()
		var mesh_inst = _find_mesh(tmp_inst)
		if mesh_inst and mesh_inst.mesh:
			mm.mesh = mesh_inst.mesh
		tmp_inst.queue_free()

	for i in range(count):
		var item = json_data[i]
		var pos = Vector3(item[0], item[1], item[2])
		var rot_y = item[3]
		var basis = Basis(Vector3.UP, rot_y)
		var t = Transform3D(basis, pos)
		mm.set_instance_transform(i, t)

	mm_node.multimesh = mm
	print("[Nomenclatura] Instanciados con éxito ", count, " postes urbanos vía MultiMesh.")

func _find_mesh(node: Node) -> MeshInstance3D:
	if node is MeshInstance3D:
		return node
	for child in node.get_children():
		var found = _find_mesh(child)
		if found:
			return found
	return null
"""
    with open(OUT_SCRIPT_GD, "w", encoding="utf-8") as f:
        f.write(gd_script_content)
    print(f"--> Script GDScript de runtime creado: {OUT_SCRIPT_GD}")

    tscn_content = """[gd_scene load_steps=6 format=3 uid="uid://nomenclatura_urbana_tecate_001"]

[ext_resource type="Script" path="res://assets/nomenclatura_urbana.gd" id="1_script"]
[ext_resource type="PackedScene" path="res://assets/nomenclatura_textos_baked.glb" id="2_text_glb"]
[ext_resource type="PackedScene" path="res://assets/nomenclatura_iconos_baked.glb" id="3_icon_glb"]

[sub_resource type="MultiMesh" id="MultiMesh_postes"]
transform_format = 1

[node name="NomenclaturaUrbana" type="Node3D"]
script = ExtResource("1_script")

[node name="MultiMeshInstance3D" type="MultiMeshInstance3D" parent="."]
multimesh = SubResource("MultiMesh_postes")

[node name="TextosBaked" parent="." instance=ExtResource("2_text_glb")]

[node name="IconosBaked" parent="." instance=ExtResource("3_icon_glb")]

"""
    with open(OUT_SCENE_TSCN, "w", encoding="utf-8") as f:
        f.write(tscn_content)
    print(f"--> Escena de Godot creada: {OUT_SCENE_TSCN}")

# ─────────────────────────────────────────────────────────────────────────────
# 9. Procesamiento de Argumentos CLI y Despacho
# ─────────────────────────────────────────────────────────────────────────────
def parse_cli_args():
    """Extrae las banderas pasadas al script tras el delimitador '--' de Blender."""
    raw_args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    mode = "full"
    for arg in raw_args:
        if arg in ("--icons-only", "-i"):
            mode = "icons"
        elif arg in ("--text-only", "-t"):
            mode = "text"
        elif arg in ("--full", "-f"):
            mode = "full"
        elif arg in ("--help", "-h"):
            print("\nUso del Compilador de Nomenclatura Urbana:")
            print("  blender --background --python scripts/bake_nomenclatura_urbana.py -- [opción]")
            print("\nOpciones disponibles:")
            print("  --icons-only, -i   Regenera ÚNICAMENTE los quads e imágenes/iconos en < 1.5s.")
            print("                     Conserva intactos los textos ya procesados.")
            print("  --text-only, -t    Regenera ÚNICAMENTE la malla 3D de textos de calles.")
            print("                     Conserva intactos los iconos.")
            print("  --full, -f         (Por defecto) Flujo completo: análisis OSM, cota de terreno,")
            print("                     malla de textos, quads de iconos y escenas.")
            print("  --help, -h         Muestra este mensaje de ayuda.\n")
            sys.exit(0)
    return mode

def ensure_corners_metadata():
    """Garantiza la existencia de esquinas y cotas en caché, o las calcula si faltan."""
    if os.path.exists(OUT_CORNERS_JSON):
        print(f"[Caché] Cargando datos de esquinas desde: {OUT_CORNERS_JSON}")
        with open(OUT_CORNERS_JSON, "r", encoding="utf-8") as f:
            return json.load(f)

    print("[Caché] Generando caché de esquinas y cotas topográficas...")
    bvh = build_terrain_bvh(TERRAIN_GLB_PATH)
    raw_corners = extract_corners_with_debounce(ROAD_OSM_PATH, min_debounce_m=5.0)

    corners_data = []
    for c in raw_corners:
        lx, ly = c["pos"]
        st1, st2 = c["streets"]
        v1, v2 = c["v1"], c["v2"]
        lz = get_terrain_height(bvh, lx, ly, default_h=400.0)
        yaw_rad = calculate_optimal_post_orientation(v1, v2)
        gx, gy, gz = lx, lz, -ly
        g_rot_y = -yaw_rad
        corners_data.append({
            "pos": [round(lx, 3), round(ly, 3)],
            "streets": [st1, st2],
            "v1": [round(v1[0], 4), round(v1[1], 4)],
            "v2": [round(v2[0], 4), round(v2[1], 4)],
            "lz": round(lz, 3),
            "yaw_rad": round(yaw_rad, 4),
            "gx": round(gx, 3),
            "gy": round(gy, 3),
            "gz": round(gz, 3),
            "g_rot_y": round(g_rot_y, 4)
        })

    with open(OUT_CORNERS_JSON, "w", encoding="utf-8") as f:
        json.dump(corners_data, f, indent=2)
    print(f"[Caché] Guardadas {len(corners_data)} esquinas en: {OUT_CORNERS_JSON}")
    return corners_data

# ─────────────────────────────────────────────────────────────────────────────
# 10. Función Principal
# ─────────────────────────────────────────────────────────────────────────────
def main():
    mode = parse_cli_args()

    print("=" * 75)
    print(" COMPILADOR PRE-BAKE DE NOMENCLATURA URBANA - TECATE SIMULATOR")
    print(f" Modo seleccionado: [{mode.upper()}]")
    print("=" * 75)

    icons_list = sorted(glob.glob(os.path.join(ICONS_DIR, "*.png")))
    if not icons_list and mode in ("icons", "full"):
        print(f"[Error] No se encontraron iconos PNG en {ICONS_DIR}.")
        return 1

    # ── MODO 1: SOLO ICONOS (--icons-only / -i) ──
    if mode == "icons":
        print("[Modo Incremental] Reprocesando únicamente imágenes e iconos...")
        if os.path.exists(OUT_DATA_JSON):
            with open(OUT_DATA_JSON, "r", encoding="utf-8") as f:
                items = json.load(f)
        else:
            corners = ensure_corners_metadata()
            items = [[c["gx"], c["gy"], c["gz"], c["g_rot_y"]] for c in corners]

        build_baked_icons(items, icons_list, OUT_ICONOS_GLB)
        print("\n--> Procesamiento de imágenes completado conservando intactos los textos.")
        return 0

    # ── MODO 2: SOLO TEXTOS (--text-only / -t) ──
    if mode == "text":
        print("[Modo Incremental] Reprocesando únicamente la malla 3D de textos...")
        corners = ensure_corners_metadata()
        build_baked_texts(corners, None, OUT_TEXTOS_GLB)
        transforms = [[c["gx"], c["gy"], c["gz"], c["g_rot_y"]] for c in corners]
        generate_godot_integration(transforms)
        print("\n--> Procesamiento de textos completado conservando intactos los iconos.")
        return 0

    # ── MODO 3: FLUJO COMPLETO (--full / -f) ──
    print("[Modo Completo] Ejecutando análisis geométrico, topográfico y pre-bake...")
    bvh_terrain = build_terrain_bvh(TERRAIN_GLB_PATH)
    raw_corners = extract_corners_with_debounce(ROAD_OSM_PATH, min_debounce_m=5.0)
    if not raw_corners:
        print("[Error] No se detectaron esquinas válidas.")
        return 1

    corners_data = []
    transforms = []
    for c in raw_corners:
        lx, ly = c["pos"]
        st1, st2 = c["streets"]
        v1, v2 = c["v1"], c["v2"]
        lz = get_terrain_height(bvh_terrain, lx, ly, default_h=400.0)
        yaw_rad = calculate_optimal_post_orientation(v1, v2)
        gx, gy, gz = lx, lz, -ly
        g_rot_y = -yaw_rad
        corners_data.append({
            "pos": [round(lx, 3), round(ly, 3)],
            "streets": [st1, st2],
            "v1": [round(v1[0], 4), round(v1[1], 4)],
            "v2": [round(v2[0], 4), round(v2[1], 4)],
            "lz": round(lz, 3),
            "yaw_rad": round(yaw_rad, 4),
            "gx": round(gx, 3),
            "gy": round(gy, 3),
            "gz": round(gz, 3),
            "g_rot_y": round(g_rot_y, 4)
        })
        transforms.append([round(gx, 3), round(gy, 3), round(gz, 3), round(g_rot_y, 4)])

    with open(OUT_CORNERS_JSON, "w", encoding="utf-8") as f:
        json.dump(corners_data, f, indent=2)

    build_baked_texts(corners_data, bvh_terrain, OUT_TEXTOS_GLB)
    build_baked_icons(transforms, icons_list, OUT_ICONOS_GLB)
    generate_godot_integration(transforms)

    print("\n" + "=" * 75)
    print(" COMPILACIÓN PRE-BAKE COMPLETADA SATISFACTORIAMENTE")
    print("=" * 75)
    return 0

if __name__ == "__main__":
    sys.exit(main())
