"""
GENERADOR DE RUTA Y ESCENA DEL AUTOBÚS EL HONGO DE TECATE
Genera la secuencia completa de waypoints 3D (ida y vuelta) desde el borde oeste (carretera libre Tijuana),
pasando por Av. Hidalgo, Pdte. Abelardo L. Rodríguez, entrando a la Central de Autobuses (acceso lateral),
saliendo por el norte hacia Av. Juárez, avanzando por la carretera libre hasta La Rumorosa y retornando.
"""

import struct
import json
import numpy as np
import math
import heapq

ROADWAYS_GLB = "godot_project/assets/roadways_baked.glb"
STREETS_JSON = "godot_project/assets/street_segments.json"
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
        return float(best_y) + 0.15 # 15cm sobre el pavimento para contacto perfecto de ruedas

    return get_elevation

def build_road_graph():
    print("[2/5] Construyendo grafo de la red vial...")
    with open(STREETS_JSON) as f:
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
        hw = s.get('hw', '')
        # Filtros estrictos requeridos: Libre Tecate-Mexicali (sin Defensores ni autopista de Cuota)
        if 'cuota' in name or 'defensores' in name or hw == 'motorway' or 'border' in name:
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
        return [start_pt, end_pt]

    return get_path

def subsample_path(pts, target_dist=25.0):
    """Sub-muestrea puntos espaciados uniformemente cada ~25 metros para suavidad."""
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
    # 1. Extremo Oeste (Carretera libre Tecate-Tijuana)
    P_OESTE = (-10760.3, 4126.8)
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
    # 7. Extremo Este (La Rumorosa carretera libre)
    P_RUMOROSA = (12118.1, 636.4)

    # ------------------ IDA (Hacia el Este) ------------------
    # Tramo 1: Carretera Libre Oeste a Av. Hidalgo
    t1 = subsample_path(get_path(P_OESTE, P_HIDALGO_INICIO), 35.0)
    # Tramo 2: Av. Hidalgo hasta Pdte. Abelardo L. Rodríguez
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
    # Tramo 6: Av. Juárez al este hasta La Rumorosa
    t6 = subsample_path(get_path(P_SALIDA_JUAREZ, P_RUMOROSA), 35.0)

    # ------------------ RETORNO (Hacia el Oeste) ------------------
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
    # Tramo 11: Retorno por Carretera Libre Tecate-Tijuana hasta el borde oeste
    t11 = list(reversed(t1))
    # Tramo 12: Conexión suave de retorno al punto inicial
    t12 = [
        (-10755.0, 4122.0),
        (-10760.3, 4126.8)
    ]

    all_2d_points = []
    station_indices = {}

    def add_points(pts_list):
        for p in pts_list:
            if not all_2d_points or math.hypot(p[0] - all_2d_points[-1][0], p[1] - all_2d_points[-1][1]) > 4.0:
                all_2d_points.append(p)

    # Construir la secuencia global
    add_points(t1)
    add_points(t2)
    add_points(t3)

    # Punto de parada en Central de Autobuses (Ida)
    idx_central_ida = len(all_2d_points) + len(t4) - 1
    add_points(t4)
    station_indices[idx_central_ida] = "Central de Autobuses Tecate (Ida)"

    add_points(t5)

    # Punto de parada en La Rumorosa
    idx_rumorosa = len(all_2d_points) + len(t6) - 1
    add_points(t6)
    station_indices[idx_rumorosa] = "Terminal La Rumorosa"

    add_points(t7)

    # Punto de parada en Central de Autobuses (Retorno)
    idx_central_vuelta = len(all_2d_points) + len(t8) - 1
    add_points(t8)
    station_indices[idx_central_vuelta] = "Central de Autobuses Tecate (Retorno)"

    add_points(t9)
    add_points(t10)

    # Punto terminal en el borde oeste
    idx_oeste = len(all_2d_points) + len(t11) - 1
    add_points(t11)
    station_indices[idx_oeste] = "Terminal Carretera Libre Tijuana (Oeste)"

    add_points(t12)

    print(f"[4/5] Muestreando elevaciones 3D para {len(all_2d_points)} waypoints...")
    waypoints_3d = []
    for x, z in all_2d_points:
        y = get_elev(x, z)
        waypoints_3d.append((round(x, 2), round(y, 2), round(z, 2)))

    print(f"Waypoints 3D generados: {len(waypoints_3d)}")
    print(f"Paradas de estación configuradas: {station_indices}")

    # Guardar waypoints en JSON para inspección y tests
    wp_data = {
        "waypoints": waypoints_3d,
        "station_indices": {str(k): v for k, v in station_indices.items()},
        "total_distance_km": round(sum(math.hypot(waypoints_3d[i+1][0] - waypoints_3d[i][0], waypoints_3d[i+1][2] - waypoints_3d[i][2]) for i in range(len(waypoints_3d)-1)) / 1000.0, 2)
    }
    with open("godot_project/assets/vehicles/bus_hongo_route.json", "w") as f:
        json.dump(wp_data, f, indent=2)
    print(f"-> Guardado JSON de ruta: godot_project/assets/vehicles/bus_hongo_route.json (Distancia total: {wp_data['total_distance_km']} km)")

    # [5/5] Generar la escena Godot 4: bus_hongo.tscn
    print("[5/5] Generando escena Godot 4: bus_hongo.tscn...")

    # Formatear el PackedVector3Array
    packed_vecs = ", ".join([f"{p[0]}, {p[1]}, {p[2]}" for p in waypoints_3d])

    # Formatear station_indices para el script
    st_dict_str = "{\n"
    for idx, name in station_indices.items():
        st_dict_str += f'{idx}: "{name}",\n'
    st_dict_str = st_dict_str.rstrip(",\n") + "\n}"

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
cruise_speed_kmh = 42.0
station_dwell_time = 8.0
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

[node name="Seat_Passenger_0" type="Node3D" parent="Seats"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, -0.75, 1.2, -2.0)
script = ExtResource("2_seat")
seat_type = 1
seat_index = 0
seat_name = "Pasajero Delantero Izquierdo"

[node name="ExitPoint" type="Marker3D" parent="Seats/Seat_Passenger_0"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 2.2, -0.8, 0)

[node name="Seat_Passenger_1" type="Node3D" parent="Seats"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0.75, 1.2, -2.0)
script = ExtResource("2_seat")
seat_type = 1
seat_index = 1
seat_name = "Pasajero Delantero Derecho"

[node name="ExitPoint" type="Marker3D" parent="Seats/Seat_Passenger_1"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 1.0, -0.8, 0)

[node name="Seat_Passenger_2" type="Node3D" parent="Seats"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, -0.75, 1.2, 0.0)
script = ExtResource("2_seat")
seat_type = 1
seat_index = 2
seat_name = "Pasajero Central Izquierdo"

[node name="ExitPoint" type="Marker3D" parent="Seats/Seat_Passenger_2"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 2.2, -0.8, 0)

[node name="Seat_Passenger_3" type="Node3D" parent="Seats"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0.75, 1.2, 0.0)
script = ExtResource("2_seat")
seat_type = 1
seat_index = 3
seat_name = "Pasajero Central Derecho"

[node name="ExitPoint" type="Marker3D" parent="Seats/Seat_Passenger_3"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 1.0, -0.8, 0)

[node name="Cameras" type="Node3D" parent="."]

[node name="Mount_1P" type="Marker3D" parent="Cameras"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, -0.75, 1.8, -2.0)

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
"""

    with open(BUS_TSCN_PATH, "w") as f:
        f.write(tscn_content)
    print(f"-> Escena guardada exitosamente: {BUS_TSCN_PATH}")

if __name__ == "__main__":
    main()
