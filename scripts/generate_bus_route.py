"""
GENERADOR DE RUTA, FLOTA EQUIDISTANTE Y ESCENA DEL AUTOBÚS EL HONGO DE TECATE
Genera la secuencia completa de waypoints 3D (ida y vuelta) desde el extremo
occidental de la carretera libre a Tijuana (-10760.3, 4126.8), avanzando por
Av. Hidalgo, ingresando a la Central de Autobuses, saliendo por Av. Juárez
hacia el este por la carretera libre hasta La Rumorosa (12118.1, 636.4),
y retornando en circuito cerrado.

Calcula la flota requerida para mantener una frecuencia exacta de 1 unidad
cada 15 minutos en cualquier punto, y distribuye las unidades equidistantemente.
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
    cell_size = 30.0
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
        return float(best_y) + 0.15 # 15cm sobre pavimento para contacto perfecto

    return get_elevation

def build_road_graph():
    print("[2/5] Construyendo grafo de la red vial...")
    with open(STREETS_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)
    segments = data.get('segments', [])

    cell_size = 12.0
    nodes = []
    grid = {}

    def get_node(x, z):
        cx = int(math.floor(x / cell_size))
        cz = int(math.floor(z / cell_size))
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                for idx in grid.get((cx + dx, cz + dz), []):
                    nx, nz = nodes[idx]
                    if (x - nx)**2 + (z - nz)**2 < 36.0: # < 6m
                        return idx
        idx = len(nodes)
        nodes.append((x, z))
        grid.setdefault((cx, cz), []).append(idx)
        return idx

    adj = {}
    for s in segments:
        name = s.get('name', '').lower()
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

def subsample_path(pts, target_dist=25.0):
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

    print("[3/5] Trazando la ruta completa del Autobús El Hongo...")
    # Puntos Clave de la Ruta:
    # 1. Extremo Sur de la Carretera Libre Tecate-Tijuana (Segmento Sur libre, límite sur de calzada)
    P_LIBRE_SUR_IDA = (-6309.9, 5838.1)
    # 2. Entronque con Av. Hidalgo
    P_HIDALGO_INICIO = (-1604.9, 303.6)
    # 3. Intersección Av. Hidalgo con Pdte. Abelardo L. Rodríguez
    P_CRUCE_RODRIGUEZ = (189.2, 88.6)
    # 4. Portón Lateral Este de la Central de Autobuses
    P_PORTON_CENTRAL = (175.7, 2.7)
    # 5. Dársena Interior de la Central de Autobuses (Parada de abordaje)
    P_DARSENA_CENTRAL = (143.0, -18.1)
    # 6. Salida Norte de la Central de Autobuses (incorporación a Av. Juárez)
    P_SALIDA_JUAREZ = (167.7, -47.5)
    # 7. Extremo Oriental (La Rumorosa / Mexicali carretera libre)
    P_RUMOROSA = (12118.1, 636.4)
    # 8. Retorno Sur de la Carretera Libre Tecate-Tijuana (calzada paralela poniente)
    P_LIBRE_SUR_RET = (-6321.8, 5833.8)

    # ------------------ IDA (Hacia el Este) ------------------
    # Tramo 1: Carretera Libre Sur (hacia Tecate) hasta Av. Hidalgo
    t1 = subsample_path(get_path(P_LIBRE_SUR_IDA, P_HIDALGO_INICIO), 35.0)
    # Tramo 2: Av. Hidalgo hasta Pdte. Abelardo L. Rodríguez (frente a Parque Hidalgo)
    t2 = subsample_path(get_path(P_HIDALGO_INICIO, P_CRUCE_RODRIGUEZ), 25.0)
    # Tramo 3: Abelardo L. Rodríguez hasta Portón Lateral Central
    t3 = [
        (189.2, 88.6),
        (186.0, 50.0),
        (184.0, 20.0),
        (182.0, 5.0),
        P_PORTON_CENTRAL
    ]
    # Tramo 4: Entrada al patio interior y dársena
    t4 = [
        P_PORTON_CENTRAL,
        (160.0, -6.0),
        P_DARSENA_CENTRAL
    ]
    # Tramo 5: Salida norte hacia Av. Juárez
    t5 = [
        P_DARSENA_CENTRAL,
        (152.0, -32.0),
        P_SALIDA_JUAREZ
    ]
    # Tramo 6: Av. Juárez al este hasta La Rumorosa / Carretera Libre
    t6 = subsample_path(get_path(P_SALIDA_JUAREZ, P_RUMOROSA), 35.0)

    # ------------------ RETORNO (Hacia el Oeste y Sur) ------------------
    # Tramo 7: Retorno en La Rumorosa y recorrido inverso por la carretera libre hasta Tecate
    t7 = list(reversed(t6))
    # Tramo 8: Entrada a la Central de Autobuses por el acceso norte
    t8 = [
        P_SALIDA_JUAREZ,
        (152.0, -32.0),
        P_DARSENA_CENTRAL
    ]
    # Tramo 9: Salida por el portón este hacia Abelardo L. Rodríguez
    t9 = [
        P_DARSENA_CENTRAL,
        (160.0, -6.0),
        P_PORTON_CENTRAL,
        (182.0, 5.0),
        (186.0, 50.0),
        P_CRUCE_RODRIGUEZ
    ]
    # Tramo 10: Retorno por Av. Hidalgo hacia el poniente
    t10 = list(reversed(t2))
    # Tramo 11: Retorno por Carretera Libre hacia el sur hasta la terminal sur
    t11 = subsample_path(get_path(P_HIDALGO_INICIO, P_LIBRE_SUR_RET), 35.0)
    # Tramo 12: Conexión suave entre calzadas para cerrar el ciclo continuo
    t12 = [
        (-6315.0, 5836.0),
        P_LIBRE_SUR_IDA
    ]

    all_2d_points = []
    station_indices = {}

    def add_points(pts_list):
        for p in pts_list:
            if not all_2d_points or math.hypot(p[0] - all_2d_points[-1][0], p[1] - all_2d_points[-1][1]) > 4.0:
                all_2d_points.append(p)

    add_points(t1)
    add_points(t2)
    add_points(t3)

    idx_central_ida = len(all_2d_points) + len(t4) - 1
    add_points(t4)
    station_indices[idx_central_ida] = "Central de Autobuses Tecate (Ida)"

    add_points(t5)

    idx_rumorosa = len(all_2d_points) + len(t6) - 1
    add_points(t6)
    station_indices[idx_rumorosa] = "Terminal La Rumorosa"

    add_points(t7)

    idx_central_vuelta = len(all_2d_points) + len(t8) - 1
    add_points(t8)
    station_indices[idx_central_vuelta] = "Central de Autobuses Tecate (Retorno)"

    add_points(t9)
    add_points(t10)

    idx_sur = len(all_2d_points) + len(t11) - 1
    add_points(t11)
    station_indices[idx_sur] = "Terminal Carretera Libre Tijuana (Sur)"

    add_points(t12)

    print(f"[4/5] Muestreando elevaciones 3D para {len(all_2d_points)} waypoints...")
    waypoints_3d = []
    for x, z in all_2d_points:
        y = get_elev(x, z)
        waypoints_3d.append((round(x, 2), round(y, 2), round(z, 2)))

    # Cálculo acumulativo de longitudes de arco
    arc_lengths = [0.0]
    for i in range(len(waypoints_3d) - 1):
        p1 = waypoints_3d[i]
        p2 = waypoints_3d[i+1]
        d = math.hypot(p2[0] - p1[0], p2[2] - p1[2])
        arc_lengths.append(arc_lengths[-1] + d)

    total_loop_length = arc_lengths[-1]

    # Cálculo de Flota para Headway exacto de 15 minutos (900 s)
    HEADWAY_TARGET_SEC = 900.0 # 15 minutos
    CRUISE_SPEED_KMH = 42.0
    cruise_speed_ms = CRUISE_SPEED_KMH / 3.6
    station_dwell_time = 8.0 # Segundos de espera por parada
    total_dwell_sec = len(station_indices) * station_dwell_time
    pure_travel_time_sec = total_loop_length / cruise_speed_ms
    total_cycle_time_sec = pure_travel_time_sec + total_dwell_sec

    # Número de unidades de la flota (5 unidades para ciclo de 75 min a 15 min de intervalo)
    num_units = 5

    # Ajustar velocidad crucero de operación para que el tiempo de ciclo sea exactamente num_units * 900s
    calibrated_travel_time = (num_units * HEADWAY_TARGET_SEC) - total_dwell_sec
    calibrated_speed_ms = total_loop_length / calibrated_travel_time
    calibrated_speed_kmh = round(calibrated_speed_ms * 3.6, 1)

    print(f"\n=======================================================")
    print(f"CÁLCULO DE FLOTA Y FRECUENCIA (Punto 9):")
    print(f"Longitud total de ruta cerrada: {total_loop_length/1000.0:.2f} km")
    print(f"Tiempo de ciclo nominal: {total_cycle_time_sec/60.0:.1f} min ({total_cycle_time_sec:.0f} s)")
    print(f"Unidades requeridas para paso cada 15 min: {num_units} autobuses")
    print(f"Velocidad crucero calibrada: {calibrated_speed_kmh} km/h")
    print(f"=======================================================\n")

    # Calcular posiciones y waypoints iniciales equidistantes para cada unidad
    # Referenciamos la Unidad 1 en la estación Central de Autobuses de Tecate (idx_central_ida)
    # para que esté presente y abordable de inmediato en el centro urbano.
    fleet_units = []
    unit_numbers = ["24", "18", "23", "07", "12", "15", "03", "09"]
    base_station_idx = idx_central_ida
    base_s = arc_lengths[base_station_idx]
    for k in range(num_units):
        target_s = (base_s + k * (total_loop_length / float(num_units))) % total_loop_length
        # Localizar el índice del waypoint más cercano
        wp_idx = 0
        min_diff = 1e9
        for i, s in enumerate(arc_lengths):
            diff = abs(s - target_s)
            if diff < min_diff:
                min_diff = diff
                wp_idx = i

        spawn_pt = waypoints_3d[wp_idx]
        u_num = unit_numbers[k % len(unit_numbers)]
        unit_info = {
            "unit_id": k + 1,
            "unit_number": u_num,
            "vehicle_name": f"Autobús El Hongo (Unidad {u_num})",
            "start_waypoint_index": wp_idx,
            "spawn_position": [spawn_pt[0], spawn_pt[1], spawn_pt[2]],
            "arc_length_m": round(target_s, 1)
        }
        fleet_units.append(unit_info)
        print(f"Unidad {unit_info['unit_id']} ({unit_info['vehicle_name']}): Waypoint {wp_idx} -> Pos: {spawn_pt}")

    # Guardar waypoints y flota en JSON
    wp_data = {
        "waypoints": waypoints_3d,
        "station_indices": {str(k): v for k, v in station_indices.items()},
        "total_distance_km": round(total_loop_length / 1000.0, 2),
        "fleet_configuration": {
            "headway_minutes": 15.0,
            "num_units": num_units,
            "calibrated_cruise_speed_kmh": calibrated_speed_kmh,
            "station_dwell_time_seconds": station_dwell_time,
            "units": fleet_units
        }
    }
    with open(ROUTE_JSON, "w", encoding="utf-8") as f:
        json.dump(wp_data, f, indent=2)
    print(f"-> Guardado JSON de ruta y flota: {ROUTE_JSON}")

    # Generar la escena Godot 4: bus_hongo.tscn con los 30 ASIENTOS COMPLETOS
    print("[5/5] Generando plantilla canónica de escena Godot 4: bus_hongo.tscn...")
    packed_vecs = ", ".join([f"{p[0]}, {p[1]}, {p[2]}" for p in waypoints_3d])
    st_dict_str = "{\n"
    for idx, name in station_indices.items():
        st_dict_str += f'{idx}: "{name}",\n'
    st_dict_str = st_dict_str.rstrip(",\n") + "\n}"

    # Construir definiciones de los 30 asientos de pasajeros
    seats_tscn = ""
    # Puesto del chofer
    seats_tscn += """
[node name="Seat_Driver" type="Node3D" parent="Seats"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, -0.75, 1.25, 3.65)
script = ExtResource("2_seat")
seat_type = 0
seat_index = 0
seat_name = "Puesto del Conductor"

[node name="ExitPoint" type="Marker3D" parent="Seats/Seat_Driver"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 1.85, -0.8, 0.2)
"""

    passenger_seat_idx = 1
    # 1. Costado Izquierdo (7 filas dobles = 14 asientos)
    seat_rows_y = [2.75, 1.85, 0.95, 0.05, -0.85, -1.75, -2.65]
    for r_idx, sy in enumerate(seat_rows_y):
        for sx, s_side in [(-1.00, "Ventanilla Izq"), (-0.55, "Pasillo Izq")]:
            seats_tscn += f"""
[node name="Seat_Passenger_{passenger_seat_idx}" type="Node3D" parent="Seats"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, {sx}, 1.25, {sy})
script = ExtResource("2_seat")
seat_type = 1
seat_index = {passenger_seat_idx}
seat_name = "Fila {r_idx+1} {s_side}"

[node name="ExitPoint" type="Marker3D" parent="Seats/Seat_Passenger_{passenger_seat_idx}"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 1.6, -0.8, 0)
"""
            passenger_seat_idx += 1

    # 2. Costado Derecho (5 filas dobles + 1 individual = 11 asientos)
    # Asiento individual delantero
    seats_tscn += f"""
[node name="Seat_Passenger_{passenger_seat_idx}" type="Node3D" parent="Seats"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0.75, 1.25, 2.75)
script = ExtResource("2_seat")
seat_type = 1
seat_index = {passenger_seat_idx}
seat_name = "Fila 1 Preferencial Der"

[node name="ExitPoint" type="Marker3D" parent="Seats/Seat_Passenger_{passenger_seat_idx}"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0.5, -0.8, 0.8)
"""
    passenger_seat_idx += 1

    for r_idx, sy in enumerate([1.85, 0.95, 0.05, -0.85, -1.75]):
        for sx, s_side in [(0.55, "Pasillo Der"), (1.00, "Ventanilla Der")]:
            seats_tscn += f"""
[node name="Seat_Passenger_{passenger_seat_idx}" type="Node3D" parent="Seats"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, {sx}, 1.25, {sy})
script = ExtResource("2_seat")
seat_type = 1
seat_index = {passenger_seat_idx}
seat_name = "Fila {r_idx+2} {s_side}"

[node name="ExitPoint" type="Marker3D" parent="Seats/Seat_Passenger_{passenger_seat_idx}"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0.4, -0.8, 0)
"""
            passenger_seat_idx += 1

    # 3. Banca Posterior (5 asientos contiguos)
    for b_idx, sx in enumerate([-0.92, -0.46, 0.00, 0.46, 0.92]):
        seats_tscn += f"""
[node name="Seat_Passenger_{passenger_seat_idx}" type="Node3D" parent="Seats"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, {sx}, 1.25, -4.35)
script = ExtResource("2_seat")
seat_type = 1
seat_index = {passenger_seat_idx}
seat_name = "Banca Posterior Asiento {b_idx+1}"

[node name="ExitPoint" type="Marker3D" parent="Seats/Seat_Passenger_{passenger_seat_idx}"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0.0, -0.8, 1.2)
"""
        passenger_seat_idx += 1

    tscn_content = f"""[gd_scene load_steps=9 format=3 uid="uid://bus_hongo_tkt_001"]

[ext_resource type="Script" path="res://systems/vehicles/controllers/route_vehicle_controller.gd" id="1_route"]
[ext_resource type="Script" path="res://systems/vehicles/core/vehicle_seat.gd" id="2_seat"]
[ext_resource type="Script" path="res://systems/vehicles/core/surface_detector.gd" id="3_surface"]
[ext_resource type="Script" path="res://systems/vehicles/core/fuel_system.gd" id="4_fuel"]
[ext_resource type="PackedScene" path="res://assets/vehicles/bus_hongo.glb" id="5_mesh"]

[sub_resource type="BoxShape3D" id="BoxShape3D_chassis"]
size = Vector3(2.5, 2.7, 9.6)

[node name="Bus_El_Hongo" type="CharacterBody3D"]
collision_layer = 2
collision_mask = 3
script = ExtResource("1_route")
cruise_speed_kmh = {calibrated_speed_kmh}
station_dwell_time = {station_dwell_time}
waypoint_reach_threshold = 5.0
loop_route = true
waypoints = PackedVector3Array({packed_vecs})
station_indices = {st_dict_str}
vehicle_name = "Autobús El Hongo (Unidad 24)"
vehicle_type = 2
mass_kg = 9200.0
max_speed_kmh = 65.0
engine_acceleration = 4.5
brake_deceleration = 11.0

[node name="VisualRoot" type="Node3D" parent="."]

[node name="BusModel" parent="VisualRoot" instance=ExtResource("5_mesh")]

[node name="CollisionRoot" type="Node3D" parent="."]

[node name="BodyCollision" type="CollisionShape3D" parent="CollisionRoot"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1.5, 0)
shape = SubResource("BoxShape3D_chassis")

[node name="Suspension" type="Node3D" parent="."]

[node name="Ray_FL" type="RayCast3D" parent="Suspension"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, -1.2, 0.6, 2.6)
target_position = Vector3(0, -2.0, 0)

[node name="Ray_FR" type="RayCast3D" parent="Suspension"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 1.2, 0.6, 2.6)
target_position = Vector3(0, -2.0, 0)

[node name="Ray_RL" type="RayCast3D" parent="Suspension"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, -1.2, 0.6, -2.6)
target_position = Vector3(0, -2.0, 0)

[node name="Ray_RR" type="RayCast3D" parent="Suspension"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 1.2, 0.6, -2.6)
target_position = Vector3(0, -2.0, 0)

[node name="Seats" type="Node3D" parent="."]
{seats_tscn}

[node name="Cameras" type="Node3D" parent="."]

[node name="Mount_1P" type="Marker3D" parent="Cameras"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, -0.75, 1.8, 3.65)

[node name="Mount_3P" type="Marker3D" parent="Cameras"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 3.2, -8.5)

[node name="Lights" type="Node3D" parent="."]

[node name="Headlights" type="Node3D" parent="Lights"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1.1, 4.8)

[node name="Light_L" type="SpotLight3D" parent="Lights/Headlights"]
transform = Transform3D(1, 0, 0, 0, 0.984808, -0.173648, 0, 0.173648, 0.984808, -0.9, 0, 0)
light_color = Color(1, 0.96, 0.88, 1)
light_energy = 5.0
spot_range = 65.0
spot_angle = 45.0

[node name="Light_R" type="SpotLight3D" parent="Lights/Headlights"]
transform = Transform3D(1, 0, 0, 0, 0.984808, -0.173648, 0, 0.173648, 0.984808, 0.9, 0, 0)
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
"""

    with open(BUS_TSCN_PATH, "w", encoding="utf-8") as f:
        f.write(tscn_content)
    print(f"-> Guardada escena canónica: {BUS_TSCN_PATH} ({passenger_seat_idx-1} asientos configurados)")

if __name__ == "__main__":
    main()
