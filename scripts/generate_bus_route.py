"""
GENERADOR DE RUTA EXTENDIDA, FLOTA EQUIDISTANTE Y ESCENA DEL AUTOBÚS EL HONGO DE TECATE
Genera la secuencia completa de waypoints 3D (ida y vuelta) cubriendo:
1. Extremo Suroeste de la Carretera Libre hacia Tijuana (-17300.0, 12146.0).
2. Corredor Carretera Libre Tijuana a 82 km/h hasta la entrada poniente de Tecate.
3. Avenida Hidalgo a 30 km/h (zona de ascenso/descenso denso de pasajeros en el centro).
4. Acceso e ingreso a la Central de Autobuses de Tecate (12-15 km/h) con detención de 2 minutos (120 s).
5. Salida norte a Av. Juárez y Paseo Morelos (40-55 km/h).
6. Carretera Federal 2 Libre a 85 km/h pasando por El Hongo hasta La Rumorosa.
7. Retorno en La Rumorosa (55014.5, 2233.9) [aprox. 32.553169, -116.040088].
8. Recorrido inverso cerrado con parada de 2 minutos en la Central Camionera de retorno.

Calcula la flota requerida para mantener una frecuencia exacta de 1 unidad cada 5 minutos
en cualquier punto de cada semiruta en el mismo sentido, distribuyendo las unidades
equidistantemente en el tiempo de ciclo.
"""

import struct
import json
import numpy as np
import math
import heapq
import os

ROADWAYS_GLB = "godot_project/assets/roadways_baked.glb"
STREETS_JSON = "godot_project/assets/street_segments.json"
ROUTE_JSON = "godot_project/assets/vehicles/bus_hongo_route.json"
SERVER_ROUTE_JSON = "server/routes/bus_hongo_route.json"
BUS_TSCN_PATH = "godot_project/assets/vehicles/bus_hongo.tscn"

def load_road_elevations():
    print("[1/5] Cargando elevaciones de roadways_baked.glb...")
    with open(ROADWAYS_GLB, 'rb') as f:
        header = f.read(12)
        magic, version, length = struct.unpack('<III', header)
        chunk_header = f.read(8)
        chunk_length, chunk_type = struct.unpack('<II', chunk_header)
        json_bytes = f.read(chunk_length)
        gltf = json.loads(json_bytes.decode('utf-8'))
        bin_header = f.read(8)
        bin_length, bin_type = struct.unpack('<II', bin_header)
        bin_data = f.read(bin_length)

    all_pts = []
    for mesh in gltf.get('meshes', []):
        for prim in mesh.get('primitives', []):
            if 'POSITION' in prim.get('attributes', {}):
                pos_idx = prim['attributes']['POSITION']
                acc = gltf['accessors'][pos_idx]
                bv = gltf['bufferViews'][acc['bufferView']]
                offset = bv.get('byteOffset', 0) + acc.get('byteOffset', 0)
                count = acc['count']
                pts = np.frombuffer(bin_data[offset:offset+count*12], dtype=np.float32).reshape(-1, 3)
                all_pts.append(pts)

    all_pts = np.vstack(all_pts)
    cell_size = 35.0
    xs = all_pts[:, 0]
    ys = all_pts[:, 1]
    zs = all_pts[:, 2]

    cxs = np.floor(xs / cell_size).astype(np.int32)
    czs = np.floor(zs / cell_size).astype(np.int32)

    grid = {}
    for i in range(len(all_pts)):
        k = (cxs[i], czs[i])
        grid.setdefault(k, []).append(i)

    def get_elevation(x, z):
        cx = int(math.floor(x / cell_size))
        cz = int(math.floor(z / cell_size))
        best_d = 1e9
        best_y = 400.0
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                k = (cx + dx, cz + dz)
                for idx in grid.get(k, []):
                    d = (xs[idx] - x)**2 + (zs[idx] - z)**2
                    if d < best_d:
                        best_d = d
                        best_y = ys[idx]
        return float(best_y) + 0.15 # 15cm sobre pavimento para contacto visual perfecto

    return get_elevation

def build_road_graph():
    print("[2/5] Construyendo grafo de la red vial...")
    with open(STREETS_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)
    segments = data.get('segments', [])

    cell_size = 15.0
    nodes = []
    grid = {}

    def get_node(x, z):
        cx = int(math.floor(x / cell_size))
        cz = int(math.floor(z / cell_size))
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                for idx in grid.get((cx + dx, cz + dz), []):
                    nx, nz = nodes[idx]
                    if (x - nx)**2 + (z - nz)**2 < 64.0: # < 8m
                        return idx
        idx = len(nodes)
        nodes.append((x, z))
        grid.setdefault((cx, cz), []).append(idx)
        return idx

    adj = {}
    for s in segments:
        name = (s.get('name') or '').lower()
        # Excluir autopistas de cuota, libramientos de peaje y accesos fronterizos restringidos
        if 'cuota' in name or 'toll' in name or 'border' in name or 'carretera tecate–tijuana' in name:
            continue
        u = get_node(s['x0'], s['z0'])
        v = get_node(s['x1'], s['z1'])
        if u != v:
            d = math.hypot(nodes[u][0] - nodes[v][0], nodes[u][1] - nodes[v][1])
            adj.setdefault(u, []).append((v, d))
            adj.setdefault(v, []).append((u, d))

    def find_nearest(x, z):
        best_i = None
        best_d = 1e9
        for i, (nx, nz) in enumerate(nodes):
            d = (x - nx)**2 + (z - nz)**2
            if d < best_d:
                best_d = d
                best_i = i
        return best_i

    def get_path(start_pt, end_pt):
        s_idx = find_nearest(start_pt[0], start_pt[1])
        e_idx = find_nearest(end_pt[0], end_pt[1])
        pq = [(0.0, s_idx, [s_idx])]
        dists = {s_idx: 0.0}

        while pq:
            d, curr, path = heapq.heappop(pq)
            if curr == e_idx:
                return [nodes[i] for i in path]
            if d > dists.get(curr, 1e9):
                continue
            for nxt, weight in adj.get(curr, []):
                new_d = d + weight
                if new_d < dists.get(nxt, 1e9):
                    dists[nxt] = new_d
                    heapq.heappush(pq, (new_d, nxt, path + [nxt]))
        print(f"[ALERTA] No se encontró ruta vial entre {start_pt} y {end_pt}")
        return [start_pt, end_pt]

    return get_path

def compute_right_lane_offset(pts, offset_m, taper_start=False, taper_end=False):
    """
    Desplaza los puntos de una polilínea lateralmente hacia la derecha respecto
    al sentido de avance en el plano XZ.
    En el sistema de coordenadas de Godot (+X Este, +Z Sur):
    Para una dirección tangente unitaria (tx, tz), el vector perpendicular
    a la derecha es (-tz, tx).
    """
    if len(pts) < 2:
        return list(pts)

    n = len(pts)
    tangents = []
    for i in range(n - 1):
        dx = pts[i+1][0] - pts[i][0]
        dz = pts[i+1][1] - pts[i][1]
        length = math.hypot(dx, dz)
        if length > 1e-4:
            tangents.append((dx / length, dz / length))
        else:
            tangents.append((1.0, 0.0) if not tangents else tangents[-1])

    offset_pts = []
    for i in range(n):
        if i == 0:
            tx, tz = tangents[0]
            nx, nz = -tz, tx
        elif i == n - 1:
            tx, tz = tangents[-1]
            nx, nz = -tz, tx
        else:
            t1x, t1z = tangents[i-1]
            t2x, t2z = tangents[i]
            n1x, n1z = -t1z, t1x
            n2x, n2z = -t2z, t2x
            nx = n1x + n2x
            nz = n1z + n2z
            n_len = math.hypot(nx, nz)
            if n_len > 1e-4:
                nx /= n_len
                nz /= n_len
            else:
                nx, nz = n1x, n1z

        cur_offset = offset_m
        if taper_start and taper_end:
            cur_offset = offset_m * math.sin(math.pi * i / float(n - 1))
        elif taper_start:
            cur_offset = offset_m * (float(i) / float(n - 1))
        elif taper_end:
            cur_offset = offset_m * (1.0 - float(i) / float(n - 1))

        offset_pts.append((round(pts[i][0] + nx * cur_offset, 2), round(pts[i][1] + nz * cur_offset, 2)))

    return offset_pts

def compute_radius_and_curvature(p_prev, p_curr, p_next):
    """
    Calcula analíticamente el radio de curvatura circunscrito R y la curvatura kappa
    para cualquier terna consecutiva de puntos en el plano XZ.
    """
    v1 = (p_curr[0] - p_prev[0], p_curr[1] - p_prev[1])
    v2 = (p_next[0] - p_curr[0], p_next[1] - p_curr[1])
    d1 = math.hypot(v1[0], v1[1])
    d2 = math.hypot(v2[0], v2[1])
    chord = math.hypot(p_next[0] - p_prev[0], p_next[1] - p_prev[1])
    if d1 < 1e-3 or d2 < 1e-3 or chord < 1e-3:
        return 99999.0, 0.0
    dot = (v1[0] * v2[0] + v1[1] * v2[1]) / (d1 * d2)
    dot = max(-1.0, min(1.0, dot))
    angle = math.acos(dot)
    sin_angle = math.sin(angle)
    if sin_angle < 1e-4:
        return 99999.0, 0.0
    R = chord / (2.0 * sin_angle)
    kappa = 1.0 / R
    return R, kappa

def subsample_path(pts, target_dist=35.0):
    if not pts:
        return []
    res = [pts[0]]
    for p in pts[1:]:
        last = res[-1]
        dist = math.hypot(p[0] - last[0], p[1] - last[1])
        if dist >= target_dist:
            res.append(p)
    if pts[-1] != res[-1]:
        res.append(pts[-1])
    return res

def main():
    get_elev = load_road_elevations()
    get_path = build_road_graph()

    print("[3/5] Trazando la ruta completa extendida del Autobús El Hongo (Carril Derecho)...")
    # Puntos Clave de la Ruta Extendida:
    # 1. Viraje seguro en el extremo suroeste de la Carretera Libre Tijuana
    P_SW_IDA = (-17300.0, 12146.0)
    P_SW_RET = (-17315.0, 12155.0)

    # 2. Entronque con Av. Hidalgo (inicio zona urbana poniente de Tecate)
    P_HIDALGO_INICIO = (-1604.9, 303.6)

    # 3. Intersección Av. Hidalgo con Pdte. Abelardo L. Rodríguez (frente a Parque Hidalgo)
    P_CRUCE_RODRIGUEZ = (189.2, 88.6)

    # 4. Portón Lateral Este de la Central de Autobuses
    P_PORTON_CENTRAL = (175.7, 2.7)

    # 5. Dársena Interior de la Central de Autobuses (Parada oficial de 2 minutos)
    P_DARSENA_CENTRAL = (143.0, -18.1)

    # 6. Salida Norte de la Central de Autobuses (incorporación a Av. Juárez)
    P_SALIDA_JUAREZ = (167.7, -47.5)

    # 7. La Rumorosa (32.553169, -116.040088 -> X=55014.5, Z=2233.9)
    P_RUMOROSA_IDA = (54998.6, 2213.6)
    P_RUMOROSA_RET = (55014.5, 2233.9)

    # ------------------ IDA (Hacia el Este) ------------------
    # Tramo 1: Carretera Libre Suroeste (desde frontera Tijuana hasta entrada Tecate)
    raw_t1 = get_path(P_SW_IDA, P_HIDALGO_INICIO)
    t1_base = subsample_path(raw_t1, 40.0)
    t1 = compute_right_lane_offset(t1_base, 1.95)

    # Tramo 2: Av. Hidalgo (zona de ascenso/descenso frecuente de pasajeros en el centro)
    raw_t2 = get_path(P_HIDALGO_INICIO, P_CRUCE_RODRIGUEZ)
    t2_base = subsample_path(raw_t2, 25.0)
    t2 = compute_right_lane_offset(t2_base, 1.60)

    # Tramo 3: Abelardo L. Rodríguez hasta Portón Lateral Central (tapering hacia portón)
    t3_base = [
        t2[-1],
        (189.2, 88.6),
        (186.0, 50.0),
        (184.0, 20.0),
        (182.0, 5.0),
        P_PORTON_CENTRAL
    ]
    t3 = compute_right_lane_offset(t3_base, 1.60, taper_end=True)

    # Tramo 4: Entrada al patio interior y dársena (offset 0.0 m exacto en andén)
    t4 = [
        P_PORTON_CENTRAL,
        (160.0, -6.0),
        P_DARSENA_CENTRAL
    ]

    # Tramo 5: Salida norte hacia Av. Juárez y Paseo Morelos (tapering de 0.0 a 1.60 m)
    t5_base = [
        P_DARSENA_CENTRAL,
        (152.0, -32.0),
        P_SALIDA_JUAREZ
    ]
    t5 = compute_right_lane_offset(t5_base, 1.60, taper_start=True)

    # Tramo 6: Av. Juárez y Paseo Morelos hacia Carretera Federal 2 hasta La Rumorosa
    raw_t6 = get_path(P_SALIDA_JUAREZ, P_RUMOROSA_IDA)
    t6_base = subsample_path(raw_t6, 40.0)
    t6 = compute_right_lane_offset(t6_base, 1.95)

    # ------------------ RETORNO (Hacia el Poniente) ------------------
    # Tramo 7: Retorno en La Rumorosa por Carretera Federal 2 hasta Tecate
    # Al viajar hacia el poniente, la normal a la derecha se orienta hacia el norte (+Z -> -Z),
    # separando automáticamente los sentidos por 3.90 m.
    t7_base = list(reversed(t6_base))
    t7 = compute_right_lane_offset(t7_base, 1.95)

    # Conexión y viraje en La Rumorosa entre carril derecho de llegada y carril derecho de retorno
    t_rumorosa_turn = [
        t6[-1],
        P_RUMOROSA_RET,
        t7[0]
    ]

    # Tramo 8: Entrada a la Central de Autobuses por acceso norte (tapering a dársena)
    t8_base = [
        P_SALIDA_JUAREZ,
        (152.0, -32.0),
        P_DARSENA_CENTRAL
    ]
    t8 = compute_right_lane_offset(t8_base, 1.60, taper_end=True)

    # Tramo 9: Salida por portón lateral hacia Abelardo L. Rodríguez (tapering a calle)
    t9_base = [
        P_DARSENA_CENTRAL,
        (160.0, -6.0),
        P_PORTON_CENTRAL,
        (182.0, 5.0),
        (186.0, 50.0),
        P_CRUCE_RODRIGUEZ
    ]
    t9 = compute_right_lane_offset(t9_base, 1.60, taper_start=True)

    # Tramo 10: Retorno por Av. Hidalgo hacia el poniente (carril derecho al norte, sep 3.20m)
    t10_base = list(reversed(t2_base))
    t10 = compute_right_lane_offset(t10_base, 1.60)

    # Tramo 11: Retorno por Carretera Libre hacia el suroeste hasta viraje de Tijuana
    raw_t11 = get_path(P_HIDALGO_INICIO, P_SW_RET)
    t11_base = subsample_path(raw_t11, 40.0)
    t11 = compute_right_lane_offset(t11_base, 1.95)

    # Tramo 12: Viraje suave en SW para cerrar el bucle entre carriles derechos
    t12 = [
        t11[-1],
        P_SW_RET,
        P_SW_IDA,
        t1[0]
    ]

    all_2d_points = []
    waypoint_speeds = []
    station_indices = {}

    def add_segment_points(pts_list, speed_kmh):
        for p in pts_list:
            if not all_2d_points or math.hypot(p[0] - all_2d_points[-1][0], p[1] - all_2d_points[-1][1]) > 3.0:
                all_2d_points.append(p)
                waypoint_speeds.append(speed_kmh)

    # Ensamblaje con perfiles de velocidad por roadway y límite de curvatura
    # 1. SW -> Hidalgo (Carretera libre interurbana a 90 km/h)
    add_segment_points(t1, 90.0)

    # 2. Av. Hidalgo (zona urbana de ascenso y descenso a 32 km/h)
    add_segment_points(t2, 32.0)

    # 3. Acceso hacia Central (18 km/h)
    add_segment_points(t3, 18.0)

    # 4. Patio y dársena Central (12 km/h)
    add_segment_points(t4, 12.0)
    idx_central_ida = len(all_2d_points) - 1
    station_indices[idx_central_ida] = {
        "name": "Central de Autobuses Tecate (Ida)",
        "dwell_time": 120.0 # Parada fija de 2 minutos
    }

    # 5. Salida hacia Av. Juárez (42 km/h)
    add_segment_points(t5, 42.0)

    # 6. Carretera Federal 2 a La Rumorosa (94 km/h en crucero)
    add_segment_points(t6, 94.0)
    add_segment_points(t_rumorosa_turn, 20.0)
    idx_rumorosa = len(all_2d_points) - 1
    station_indices[idx_rumorosa] = {
        "name": "Terminal La Rumorosa",
        "dwell_time": 45.0
    }

    # 7. Retorno Carretera Federal 2 (94 km/h)
    add_segment_points(t7, 94.0)

    # 8. Entrada a Central de retorno (15 km/h)
    add_segment_points(t8, 15.0)
    idx_central_vuelta = len(all_2d_points) - 1
    station_indices[idx_central_vuelta] = {
        "name": "Central de Autobuses Tecate (Retorno)",
        "dwell_time": 120.0 # Parada fija de 2 minutos
    }

    # 9. Salida de Central hacia Abelardo L. Rodríguez (15 km/h)
    add_segment_points(t9, 15.0)

    # 10. Retorno Av. Hidalgo (32 km/h)
    add_segment_points(t10, 32.0)

    # 11. Carretera Libre Retorno a Tijuana (90 km/h)
    add_segment_points(t11, 90.0)
    add_segment_points(t12, 20.0)
    idx_sw_term = len(all_2d_points) - 1
    station_indices[idx_sw_term] = {
        "name": "Terminal Carretera Libre Tijuana (Suroeste)",
        "dwell_time": 45.0
    }

    print(f"[4/5] Muestreando elevaciones 3D y evaluando curvatura física para {len(all_2d_points)} waypoints...")
    waypoints_3d = []
    for x, z in all_2d_points:
        y = get_elev(x, z)
        waypoints_3d.append((round(x, 2), round(y, 2), round(z, 2)))

    # Ajuste analítico de velocidades por radio de curvatura circunscrito
    # v_curva_max = sqrt(a_lat_max * R) con a_lat_max = 3.0 m/s^2
    A_LAT_MAX = 3.0
    for i in range(1, len(all_2d_points) - 1):
        p_prev = all_2d_points[i - 1]
        p_curr = all_2d_points[i]
        p_next = all_2d_points[i + 1]
        R, kappa = compute_radius_and_curvature(p_prev, p_curr, p_next)
        if R < 120.0: # Curvas cerradas o esquinas
            v_phys_max = math.sqrt(A_LAT_MAX * R) * 3.6
            waypoint_speeds[i] = round(min(waypoint_speeds[i], max(14.0, v_phys_max)), 1)

    # Cálculo acumulativo de longitudes y tiempos de recorrido
    arc_lengths = [0.0]
    cumulative_times = [0.0]

    for i in range(len(waypoints_3d) - 1):
        p1 = waypoints_3d[i]
        p2 = waypoints_3d[i+1]
        d = math.hypot(p2[0] - p1[0], p2[2] - p1[2])
        arc_lengths.append(arc_lengths[-1] + d)

        v_ms = max(5.0, waypoint_speeds[i] / 3.6)
        dt = d / v_ms
        if i in station_indices:
            dt += station_indices[i]["dwell_time"]
        cumulative_times.append(cumulative_times[-1] + dt)

    d_close = math.hypot(waypoints_3d[0][0] - waypoints_3d[-1][0], waypoints_3d[0][2] - waypoints_3d[-1][2])
    v_close = max(5.0, waypoint_speeds[-1] / 3.6)
    dt_close = d_close / v_close
    if (len(waypoints_3d) - 1) in station_indices:
        dt_close += station_indices[len(waypoints_3d) - 1]["dwell_time"]

    total_loop_length = arc_lengths[-1] + d_close
    total_cycle_time_sec = cumulative_times[-1] + dt_close

    HEADWAY_TARGET_SEC = 300.0  # Exactamente 5 minutos
    num_units = int(math.ceil(total_cycle_time_sec / HEADWAY_TARGET_SEC))

    # Velocidad promedio ponderada global de la operación
    mean_speed_ms = total_loop_length / (total_cycle_time_sec - sum(st["dwell_time"] for st in station_indices.values()))
    calibrated_speed_kmh = round(mean_speed_ms * 3.6, 1)

    print(f"\n=======================================================")
    print(f"CÁLCULO DE FLOTA Y FRECUENCIA OPTIMIZADA (FASE 2/3):")
    print(f"Longitud total de ruta cerrada: {total_loop_length/1000.0:.2f} km")
    print(f"Tiempo de ciclo nominal: {total_cycle_time_sec/60.0:.1f} min ({total_cycle_time_sec:.0f} s)")
    print(f"Unidades requeridas para paso cada 5 min: {num_units} autobuses")
    print(f"Velocidad crucero ponderada: {calibrated_speed_kmh} km/h")
    print(f"=======================================================\n")

    # Detectar cruces e intersecciones viales con street_segments.json
    print("[4.5/5] Identificando cruces e intersecciones viales en la ruta...")
    with open(STREETS_JSON, 'r', encoding='utf-8') as f:
        streets_data = json.load(f)
    s_cell = float(streets_data.get('cell_size', 200.0))
    s_grid = streets_data.get('grid', {})
    s_segs = streets_data.get('segments', [])

    intersections = {}
    last_crossing_dist = -999.0
    for wp_i, (wx, wy, wz) in enumerate(waypoints_3d):
        cx = int(math.floor(wx / s_cell))
        cz = int(math.floor(wz / s_cell))
        candidate_indices = set()
        for dcx in (-1, 0, 1):
            for dcz in (-1, 0, 1):
                key = f"{cx + dcx},{cz + dcz}"
                if key in s_grid:
                    for s_idx in s_grid[key]:
                        candidate_indices.add(s_idx)

        nearby_names = set()
        for s_idx in candidate_indices:
            seg = s_segs[s_idx]
            s_name = (seg.get('name') or '').strip()
            if not s_name:
                continue
            d0 = math.hypot(wx - seg['x0'], wz - seg['z0'])
            d1 = math.hypot(wx - seg['x1'], wz - seg['z1'])
            if min(d0, d1) < 22.0:
                nearby_names.add(s_name)

        if len(nearby_names) >= 2 and (arc_lengths[wp_i] - last_crossing_dist) > 90.0:
            names_list = sorted(list(nearby_names))
            intersections[str(wp_i)] = {
                "name": f"{names_list[0]} y {names_list[1]}",
                "streets": names_list,
                "arc_length_m": round(arc_lengths[wp_i], 1)
            }
            last_crossing_dist = arc_lengths[wp_i]

    print(f"-> Identificados {len(intersections)} cruces/intersecciones para paradas con debounce.")

    # Calcular posiciones y waypoints iniciales equidistantes TEMPORALMENTE para cada unidad
    fleet_units = []
    unit_numbers = [
        "24", "18", "23", "07", "12", "15", "03", "09", "31", "42",
        "05", "11", "16", "22", "27", "33", "38", "44", "49", "52",
        "01", "08", "14", "19", "25", "30", "36", "41", "47", "50",
    ]
    base_station_idx = idx_central_ida
    base_time = cumulative_times[base_station_idx]
    total_time = total_cycle_time_sec

    for k in range(num_units):
        target_t = (base_time + k * (total_time / float(num_units))) % total_time
        wp_idx = 0
        min_diff = 1e9
        for i, t in enumerate(cumulative_times):
            diff = abs(t - target_t)
            if diff < min_diff:
                min_diff = diff
                wp_idx = i

        spawn_pt = waypoints_3d[wp_idx]
        u_num = unit_numbers[k % len(unit_numbers)]
        unit_info = {
            "unit_id": 2001 + k,
            "unit_number": u_num,
            "vehicle_name": f"Autobús El Hongo (Unidad {u_num})",
            "start_waypoint_index": wp_idx,
            "spawn_position": [spawn_pt[0], spawn_pt[1], spawn_pt[2]],
            "arc_length_m": round(arc_lengths[wp_idx], 1),
            "target_speed_kmh": waypoint_speeds[wp_idx],
        }
        fleet_units.append(unit_info)

    # Guardar waypoints y flota en JSON para Godot y Servidor
    wp_data = {
        "waypoints": waypoints_3d,
        "waypoint_speeds": waypoint_speeds,
        "station_indices": {str(k): v for k, v in station_indices.items()},
        "intersections": intersections,
        "total_distance_km": round(total_loop_length / 1000.0, 2),
        "total_cycle_time_minutes": round(total_cycle_time_sec / 60.0, 2),
        "fleet_configuration": {
            "headway_minutes": 5.0,
            "num_units": num_units,
            "calibrated_cruise_speed_kmh": calibrated_speed_kmh,
            "units": fleet_units
        }
    }

    os.makedirs(os.path.dirname(ROUTE_JSON), exist_ok=True)
    with open(ROUTE_JSON, "w", encoding="utf-8") as f:
        json.dump(wp_data, f, indent=2)
    print(f"-> Guardado JSON de ruta y flota en Godot: {ROUTE_JSON}")

    os.makedirs(os.path.dirname(SERVER_ROUTE_JSON), exist_ok=True)
    with open(SERVER_ROUTE_JSON, "w", encoding="utf-8") as f:
        json.dump(wp_data, f, indent=2)
    print(f"-> Guardado JSON de ruta y flota en Servidor: {SERVER_ROUTE_JSON}")

    # Generar la escena Godot 4: bus_hongo.tscn (Cero cajas manuales, Regla 8)
    print("[5/5] Generando plantilla canónica de escena Godot 4: bus_hongo.tscn...")
    packed_vecs = ", ".join([f"{p[0]}, {p[1]}, {p[2]}" for p in waypoints_3d])
    packed_speeds = ", ".join([f"{s:.1f}" for s in waypoint_speeds])
    st_dict_str = "{\n"
    for idx, info in station_indices.items():
        st_dict_str += f'{idx}: {{"name": "{info["name"]}", "dwell_time": {info["dwell_time"]}}},\n'
    st_dict_str = st_dict_str.rstrip(",\n") + "\n}"

    seats_tscn = """
[node name="Seat_Driver" type="Node3D" parent="Seats"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, -0.75, 1.25, -3.65)
script = ExtResource("2_seat")
seat_type = 0
seat_index = 0
seat_name = "Puesto del Conductor"

[node name="ExitPoint" type="Marker3D" parent="Seats/Seat_Driver"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0.65, -0.40, 0.0)
"""

    passenger_seat_idx = 1
    seat_rows_z = [-2.75, -1.85, -0.95, -0.05, 0.85, 1.75, 2.65]
    for r_idx, sz in enumerate(seat_rows_z):
        for sx, s_side, exit_dx in [(-1.00, "Ventanilla Izq", 0.85), (-0.55, "Pasillo Izq", 0.45)]:
            seats_tscn += f"""
[node name="Seat_Passenger_{passenger_seat_idx}" type="Node3D" parent="Seats"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, {sx}, 1.25, {sz})
script = ExtResource("2_seat")
seat_type = 1
seat_index = {passenger_seat_idx}
seat_name = "Fila {r_idx+1} {s_side}"

[node name="ExitPoint" type="Marker3D" parent="Seats/Seat_Passenger_{passenger_seat_idx}"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, {exit_dx}, -0.40, 0.0)
"""
            passenger_seat_idx += 1

    seats_tscn += f"""
[node name="Seat_Passenger_{passenger_seat_idx}" type="Node3D" parent="Seats"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0.75, 1.25, -2.75)
script = ExtResource("2_seat")
seat_type = 1
seat_index = {passenger_seat_idx}
seat_name = "Fila 1 Preferencial Der"

[node name="ExitPoint" type="Marker3D" parent="Seats/Seat_Passenger_{passenger_seat_idx}"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, -0.65, -0.40, 0.0)
"""
    passenger_seat_idx += 1

    for r_idx, sz in enumerate([-1.85, -0.95, -0.05, 0.85, 1.75]):
        for sx, s_side, exit_dx in [(0.55, "Pasillo Der", -0.45), (1.00, "Ventanilla Der", -0.85)]:
            seats_tscn += f"""
[node name="Seat_Passenger_{passenger_seat_idx}" type="Node3D" parent="Seats"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, {sx}, 1.25, {sz})
script = ExtResource("2_seat")
seat_type = 1
seat_index = {passenger_seat_idx}
seat_name = "Fila {r_idx+2} {s_side}"

[node name="ExitPoint" type="Marker3D" parent="Seats/Seat_Passenger_{passenger_seat_idx}"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, {exit_dx}, -0.40, 0.0)
"""
            passenger_seat_idx += 1

    for b_idx, sx in enumerate([-0.92, -0.46, 0.00, 0.46, 0.92]):
        seats_tscn += f"""
[node name="Seat_Passenger_{passenger_seat_idx}" type="Node3D" parent="Seats"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, {sx}, 1.25, 4.35)
script = ExtResource("2_seat")
seat_type = 1
seat_index = {passenger_seat_idx}
seat_name = "Banca Posterior Asiento {b_idx+1}"

[node name="ExitPoint" type="Marker3D" parent="Seats/Seat_Passenger_{passenger_seat_idx}"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0.0, -0.40, -0.75)
"""
        passenger_seat_idx += 1

    tscn_content = f"""[gd_scene load_steps=8 format=3 uid="uid://bus_hongo_tkt_001"]

[ext_resource type="Script" path="res://systems/vehicles/controllers/bus_hongo_controller.gd" id="1_route"]
[ext_resource type="Script" path="res://systems/vehicles/core/vehicle_seat.gd" id="2_seat"]
[ext_resource type="Script" path="res://systems/vehicles/core/surface_detector.gd" id="3_surface"]
[ext_resource type="Script" path="res://systems/vehicles/core/fuel_system.gd" id="4_fuel"]
[ext_resource type="PackedScene" path="res://assets/vehicles/bus_hongo.glb" id="5_mesh"]

[node name="Bus_El_Hongo" type="CharacterBody3D"]
collision_layer = 2
collision_mask = 3
script = ExtResource("1_route")
unit_number = "24"
license_plate = "A-30530-A"
concession_id = "TKT-A-19-00006"
route_destination = "TECATE   EL HONGO   LA RUMOROSA"
cruise_speed_kmh = {calibrated_speed_kmh}
station_dwell_time = 8.0
waypoint_reach_threshold = 5.0
loop_route = true
waypoints = PackedVector3Array({packed_vecs})
waypoint_speeds = PackedFloat32Array({packed_speeds})
station_indices = {st_dict_str}
vehicle_name = "Autobús El Hongo (Unidad 24)"
vehicle_type = 2
mass_kg = 9200.0
max_speed_kmh = 105.0
engine_acceleration = 4.5
brake_deceleration = 11.0

[node name="VisualRoot" type="Node3D" parent="."]

[node name="BusModel" parent="VisualRoot" instance=ExtResource("5_mesh")]

[node name="Suspension" type="Node3D" parent="."]

[node name="Ray_FL" type="RayCast3D" parent="Suspension"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, -1.2, 0.6, -2.6)
target_position = Vector3(0, -2.0, 0)

[node name="Ray_FR" type="RayCast3D" parent="Suspension"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 1.2, 0.6, -2.6)
target_position = Vector3(0, -2.0, 0)

[node name="Ray_RL" type="RayCast3D" parent="Suspension"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, -1.2, 0.6, 2.6)
target_position = Vector3(0, -2.0, 0)

[node name="Ray_RR" type="RayCast3D" parent="Suspension"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 1.2, 0.6, 2.6)
target_position = Vector3(0, -2.0, 0)

[node name="Seats" type="Node3D" parent="."]
{seats_tscn}

[node name="Cameras" type="Node3D" parent="."]

[node name="Mount_1P" type="Marker3D" parent="Cameras"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, -0.75, 1.8, -3.65)

[node name="Mount_3P" type="Marker3D" parent="Cameras"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 3.2, 8.5)

[node name="Lights" type="Node3D" parent="."]

[node name="Headlights" type="Node3D" parent="Lights"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1.1, -4.8)

[node name="Light_L" type="SpotLight3D" parent="Lights/Headlights"]
transform = Transform3D(1, 0, 0, 0, 0.984808, 0.173648, 0, -0.173648, 0.984808, -0.9, 0, 0)
light_color = Color(1, 0.96, 0.88, 1)
light_energy = 5.0
spot_range = 65.0
spot_angle = 45.0

[node name="Light_R" type="SpotLight3D" parent="Lights/Headlights"]
transform = Transform3D(1, 0, 0, 0, 0.984808, 0.173648, 0, -0.173648, 0.984808, 0.9, 0, 0)
light_color = Color(1, 0.96, 0.88, 1)
light_energy = 5.0
spot_range = 65.0
spot_angle = 45.0

[node name="SurfaceDetector" type="Node3D" parent="."]
script = ExtResource("3_surface")

[node name="FuelSystem" type="Node" parent="."]
script = ExtResource("4_fuel")
capacity_liters = 250.0
current_liters = 250.0
is_infinite_fuel = true

[node name="ParametricLabels" type="Node3D" parent="."]

[node name="Label_Unit_Left" type="Label3D" parent="ParametricLabels"]
transform = Transform3D(0, 0, -1, 0, 1, 0, 1, 0, 0, -1.265, 0.52, -3.45)
pixel_size = 0.003
text = "24"
font_size = 64
modulate = Color(0.004, 0.24, 0.31, 1)
outline_modulate = Color(1, 1, 1, 0)

[node name="Label_Unit_Right" type="Label3D" parent="ParametricLabels"]
transform = Transform3D(0, 0, 1, 0, 1, 0, -1, 0, 0, 1.265, 0.48, -3.7)
pixel_size = 0.003
text = "24"
font_size = 64
modulate = Color(0.004, 0.24, 0.31, 1)
outline_modulate = Color(1, 1, 1, 0)

[node name="Label_Unit_Rear" type="Label3D" parent="ParametricLabels"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0.63, 1.64, 4.86)
pixel_size = 0.0025
text = "24"
font_size = 64
modulate = Color(0.004, 0.24, 0.31, 1)
outline_modulate = Color(1, 1, 1, 0)

[node name="Label_Plate_Front" type="Label3D" parent="ParametricLabels"]
transform = Transform3D(-1, 0, 0, 0, 1, 0, 0, 0, -1, 0, 0.55, -4.91)
pixel_size = 0.0018
text = "A-30530-A"
font_size = 48
modulate = Color(0.08, 0.08, 0.08, 1)
outline_modulate = Color(1, 1, 1, 0)

[node name="Label_Plate_Rear" type="Label3D" parent="ParametricLabels"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0.72, 4.86)
pixel_size = 0.0018
text = "A-30530-A"
font_size = 48
modulate = Color(0.08, 0.08, 0.08, 1)
outline_modulate = Color(1, 1, 1, 0)

[node name="Label_Concession_Rear" type="Label3D" parent="ParametricLabels"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0.48, 4.86)
pixel_size = 0.0018
text = "TKT-A-19-00006"
font_size = 44
modulate = Color(1, 1, 1, 1)
outline_modulate = Color(0, 0, 0, 0)
"""

    with open(BUS_TSCN_PATH, "w", encoding="utf-8") as f:
        f.write(tscn_content)
    print(f"-> Guardada escena canónica: {BUS_TSCN_PATH} ({passenger_seat_idx-1} asientos configurados, Regla 8 cumplida)")

if __name__ == "__main__":
    main()
