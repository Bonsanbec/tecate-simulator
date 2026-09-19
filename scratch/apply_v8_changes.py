#!/usr/bin/env python3
"""
scratch/apply_v8_changes.py
Aplica las rectificaciones V7.1 / V8.0 a scripts/generate_bbva_tecate.py:
1. Ventanales superiores en Fachada Juárez (Z = 5.10 a 6.25, sin impostas superiores, muro corrido a 7.10).
2. Ventanales superiores en Fachada Este (Z = 5.10 a 6.25, solo 3 rectángulos inferiores).
3. Reducción de Fachada Este a 6 subdivisiones (Y = 0.40 a 20.80).
4. Subdivisión 6 como pared lisa con puerta simple de hierro blanco.
5. Cierre angulado en chaflán a 45º (contraesquina de Guajardo) de (21.00, 22.60) a (22.80, 20.80).
6. Arco cóncavo posterior calibrado con su pilar central y dos ventanas con repisa.
7. Actualización de colisionadores analíticos en Godot .tscn.
"""

import os

def main():
    script_path = "scripts/generate_bbva_tecate.py"
    with open(script_path, "r", encoding="utf-8") as f:
        code = f.read()

    # 1. Modificar build_south_facade_juarez
    # Muro superior en Juárez (Z = 6.25 a H_wall en vez de 6.75 a H_wall)
    code = code.replace(
        "add_box(bm_struct, X_start, 21.80, 0.02, 0.30, 6.75, H_wall)",
        "add_box(bm_struct, X_start, 21.80, 0.02, 0.30, 6.25, H_wall)"
    )

    # Ventanales PA Juárez: Z = 5.10 a 6.25, eliminando montante superior y recortando a solo los 3 rectángulos inferiores
    old_juarez_pa = '''    # Planta Alta (Z = 5.10 a 6.75) con montantes superiores
    for idx, (x1, x2) in enumerate(bays):
        w_f2 = 0.04
        add_box(bm_alum, x1, x1 + w_f2, 0.04, 0.10, 5.10, 6.75)
        add_box(bm_alum, x2 - w_f2, x2, 0.04, 0.10, 5.10, 6.75)
        add_box(bm_alum, x1, x2, 0.04, 0.10, 5.10, 5.10 + w_f2)
        add_box(bm_alum, x1, x2, 0.04, 0.10, 6.75 - w_f2, 6.75)
        add_box(bm_alum, x1, x2, 0.04, 0.10, 6.25, 6.25 + 0.03) # Montante horizontal
        
        n_divs = 2 if idx == 0 else (4 if idx == 3 else 3)
        step = (x2 - x1) / float(n_divs)
        for i in range(1, n_divs):
            mx = x1 + i * step
            add_box(bm_alum, mx - 0.02, mx + 0.02, 0.04, 0.10, 5.10, 6.75)
        add_box(bm_glass, x1 + w_f2, x2 - w_f2, 0.065, 0.075, 5.10 + w_f2, 6.75 - w_f2)'''

    new_juarez_pa = '''    # Planta Alta (Z = 5.10 a 6.25) solo los 3 rectángulos inferiores (sin impostas superiores)
    for idx, (x1, x2) in enumerate(bays):
        w_f2 = 0.04
        add_box(bm_alum, x1, x1 + w_f2, 0.04, 0.10, 5.10, 6.25)
        add_box(bm_alum, x2 - w_f2, x2, 0.04, 0.10, 5.10, 6.25)
        add_box(bm_alum, x1, x2, 0.04, 0.10, 5.10, 5.10 + w_f2)
        add_box(bm_alum, x1, x2, 0.04, 0.10, 6.25 - w_f2, 6.25)
        
        n_divs = 2 if idx == 0 else (4 if idx == 3 else 3)
        step = (x2 - x1) / float(n_divs)
        for i in range(1, n_divs):
            mx = x1 + i * step
            add_box(bm_alum, mx - 0.02, mx + 0.02, 0.04, 0.10, 5.10, 6.25)
        add_box(bm_glass, x1 + w_f2, x2 - w_f2, 0.065, 0.075, 5.10 + w_f2, 6.25 - w_f2)'''

    if old_juarez_pa in code:
        code = code.replace(old_juarez_pa, new_juarez_pa)
    else:
        print("ADVERTENCIA: old_juarez_pa no encontrado textualmente.")

    # Rótulos en vidrios de Juárez (centrados a Z = 5.85 m dentro del nuevo vano)
    code = code.replace("o_d1.location = (15.50, 0.055, 6.45)", "o_d1.location = (15.50, 0.055, 5.85)")
    code = code.replace("o_d2.location = (19.80, 0.055, 6.42)", "o_d2.location = (19.80, 0.055, 5.85)")

    # 2. Reemplazo completo de build_east_facade_and_parking
    old_east_func_start = 'def build_east_facade_and_parking(mats, col):'
    old_south_func_start = 'def build_south_and_inward_arc_facade(mats, col):'
    
    idx_east = code.find(old_east_func_start)
    idx_south = code.find(old_south_func_start)
    
    if idx_east == -1 or idx_south == -1:
        print("ERROR: No se encontraron los encabezados de función este/sur.")
        return

    new_east_func = '''def build_east_facade_and_parking(mats, col):
    """Construye la Fachada Este limitada a 6 subdivisiones (Y = 0.40 a 20.80 m).
    Crujías 1 a 5 con ventanales superiores de solo 3 rectángulos inferiores (Z = 5.10 a 6.25 m).
    Crujía 6 con pared lisa en PA y PB, y puerta simple de hierro blanco en PB."""
    bm_east = bmesh.new()
    bm_alum = bmesh.new()
    bm_glass = bmesh.new()
    bm_blind = bmesh.new()
    bm_hvac = bmesh.new()
    bm_white_door = bmesh.new()
    
    X_east = 22.80
    Y_east_max = 20.80  # Concluye al término de la subdivisión 6 (Ground Truth V8.0)
    H_wall = 7.10
    
    # 1. Muro Este principal (Z = -1.20 a 7.10, Y = 0.40 a 20.80)
    add_box(bm_east, X_east - 0.40, X_east, 0.40, Y_east_max, -1.20, 0.40) # Zócalo enterrado continuo
    add_box(bm_east, X_east - 0.40, X_east, 0.40, Y_east_max, 3.20, 5.10)  # Faja intermedia
    add_box(bm_east, X_east - 0.40, X_east, 0.40, Y_east_max, 6.25, H_wall) # Dintel superior corrido
    add_box(bm_east, X_east - 0.45, X_east + 0.05, 0.40, Y_east_max, 7.10, 7.25) # Albardilla coping
    
    # Losa interior de azotea hermética
    add_box(bm_east, 4.20, X_east, 0.40, Y_east_max, 7.00, 7.25)
    add_box(bm_east, 0.40, 4.20, 4.20, 30.00, 7.00, 7.25) # Losa ala Cárdenas
    
    # 2. Las 6 Crujías modulares a lo largo de los 20.80 m
    e_bays = [
        (0.80, 3.60),   # Crujía 1: Despacho Lic. en Derecho
        (4.20, 7.00),   # Crujía 2
        (7.60, 10.40),  # Crujía 3: Puerta peatonal de servicio con montante
        (11.00, 13.80), # Crujía 4
        (14.40, 17.20), # Crujía 5
        (17.80, 20.60)  # Crujía 6: Pared lisa y puerta simple de hierro blanco
    ]
    
    # Machones y pilastras divisorias
    add_box(bm_east, X_east - 0.40, X_east, 0.40, 0.80, 0.40, H_wall)
    for i in range(len(e_bays) - 1):
        add_box(bm_east, X_east - 0.40, X_east, e_bays[i][1], e_bays[i+1][0], 0.40, H_wall)
    add_box(bm_east, X_east - 0.40, X_east, 20.60, Y_east_max, 0.40, H_wall)
    
    # Crujías 1 a 5 en Planta Alta: Ventanales de solo los 3 rectángulos inferiores (Z = 5.10 a 6.25 m)
    for y1, y2 in e_bays[:5]:
        add_box(bm_alum, X_east - 0.10, X_east - 0.02, y1, y2, 5.10, 5.15)
        add_box(bm_alum, X_east - 0.10, X_east - 0.02, y1, y2, 6.20, 6.25)
        add_box(bm_alum, X_east - 0.10, X_east - 0.02, y1, y1 + 0.04, 5.10, 6.25)
        add_box(bm_alum, X_east - 0.10, X_east - 0.02, y2 - 0.04, y2, 5.10, 6.25)
        step_e = (y2 - y1) / 3.0
        m1 = y1 + step_e
        m2 = y1 + 2.0 * step_e
        add_box(bm_alum, X_east - 0.10, X_east - 0.02, m1 - 0.02, m1 + 0.02, 5.10, 6.25)
        add_box(bm_alum, X_east - 0.10, X_east - 0.02, m2 - 0.02, m2 + 0.02, 5.10, 6.25)
        add_box(bm_glass, X_east - 0.07, X_east - 0.05, y1 + 0.04, y2 - 0.04, 5.15, 6.20)
        
    # Crujía 6 en Planta Alta: Pared lisa (sin ventana)
    y6_1, y6_2 = e_bays[5]
    add_box(bm_east, X_east - 0.40, X_east, y6_1, y6_2, 5.10, 6.25)
        
    # Planta Baja Este:
    # Crujías 1 a 5:
    for idx_pb, (y1, y2) in enumerate(e_bays[:5]):
        if idx_pb == 2:
            # Crujía 3: Puerta peatonal con montante de vidrio
            add_box(bm_east, X_east - 0.40, X_east, y1, y2, 3.15, 3.20)
            door_y1 = y1 + 0.35
            door_y2 = y2 - 0.35
            add_box(bm_east, X_east - 0.40, X_east, y1, door_y1, 0.40, 3.20)
            add_box(bm_east, X_east - 0.40, X_east, door_y2, y2, 0.40, 3.20)
            add_box(bm_alum, X_east - 0.10, X_east - 0.02, door_y1, door_y2, 0.40, 0.45)
            add_box(bm_alum, X_east - 0.10, X_east - 0.02, door_y1, door_y2, 2.55, 2.60)
            add_box(bm_alum, X_east - 0.10, X_east - 0.02, door_y1, door_y2, 3.10, 3.15)
            add_box(bm_alum, X_east - 0.10, X_east - 0.02, door_y1, door_y1 + 0.04, 0.40, 3.15)
            add_box(bm_alum, X_east - 0.10, X_east - 0.02, door_y2 - 0.04, door_y2, 0.40, 3.15)
            add_box(bm_glass, X_east - 0.07, X_east - 0.05, door_y1 + 0.04, door_y2 - 0.04, 0.45, 2.55)
            add_box(bm_glass, X_east - 0.07, X_east - 0.05, door_y1 + 0.04, door_y2 - 0.04, 2.60, 3.10)
        else:
            add_box(bm_alum, X_east - 0.10, X_east - 0.02, y1, y2, 0.40, 0.45)
            add_box(bm_alum, X_east - 0.10, X_east - 0.02, y1, y2, 3.15, 3.20)
            add_box(bm_alum, X_east - 0.10, X_east - 0.02, y1, y1 + 0.04, 0.40, 3.20)
            add_box(bm_alum, X_east - 0.10, X_east - 0.02, y2 - 0.04, y2, 0.40, 3.20)
            my_pb = (y1 + y2) * 0.5
            add_box(bm_alum, X_east - 0.10, X_east - 0.02, my_pb - 0.025, my_pb + 0.025, 0.40, 3.20)
            add_box(bm_glass, X_east - 0.07, X_east - 0.05, y1 + 0.04, y2 - 0.04, 0.45, 3.15)
            add_box(bm_blind, X_east - 0.14, X_east - 0.13, y1 + 0.04, y2 - 0.04, 0.45, 3.15)

    # Crujía 6 en Planta Baja: Pared lisa con puerta simple de hierro blanco (Ground Truth Imagen 1)
    door_w = 0.95
    d_start = (y6_1 + y6_2 - door_w) * 0.5 # ~18.725
    d_end = d_start + door_w               # ~19.675
    # Pared lisa rodeando la puerta
    add_box(bm_east, X_east - 0.40, X_east, y6_1, d_start, 0.40, 3.20)
    add_box(bm_east, X_east - 0.40, X_east, d_end, y6_2, 0.40, 3.20)
    add_box(bm_east, X_east - 0.40, X_east, d_start, d_end, 2.50, 3.20)
    
    # Puerta simple de hierro blanco
    add_box(bm_white_door, X_east - 0.06, X_east - 0.01, d_start, d_end, 0.40, 2.50) # Hoja de puerta
    # Marco y molduras de refuerzo de hierro blanco
    add_box(bm_white_door, X_east - 0.08, X_east + 0.01, d_start - 0.03, d_start + 0.03, 0.40, 2.52)
    add_box(bm_white_door, X_east - 0.08, X_east + 0.01, d_end - 0.03, d_end + 0.03, 0.40, 2.52)
    add_box(bm_white_door, X_east - 0.08, X_east + 0.01, d_start - 0.03, d_end + 0.03, 2.48, 2.54)
    # Tableros de la puerta de hierro
    add_box(bm_white_door, X_east - 0.075, X_east - 0.055, d_start + 0.10, d_end - 0.10, 0.55, 1.30)
    add_box(bm_white_door, X_east - 0.075, X_east - 0.055, d_start + 0.10, d_end - 0.10, 1.45, 2.35)
    # Manija de acero
    add_box(bm_alum, X_east - 0.02, X_east + 0.05, d_end - 0.15, d_end - 0.09, 1.35, 1.40)

    # 5 Luminarias tipo aplique / sconce exterior sobre las pilastras de PB
    for y_lamp in [3.90, 7.30, 10.70, 14.10, 17.50]:
        add_box(bm_alum, X_east - 0.02, X_east + 0.10, y_lamp - 0.03, y_lamp + 0.03, 2.68, 2.72)
        add_box(bm_alum, X_east + 0.08, X_east + 0.22, y_lamp - 0.06, y_lamp + 0.06, 2.58, 2.78)

    # Casetas HVAC en azotea
    add_box(bm_hvac, 7.00, 11.50, 15.00, 19.50, 7.15, 8.65)
    add_box(bm_hvac, 8.50, 10.50, 9.00, 11.50, 7.15, 8.10)
    add_box(bm_hvac, 11.00, 13.00, 9.00, 11.50, 7.15, 8.10)

    bmesh.ops.recalc_face_normals(bm_hvac, faces=bm_hvac.faces)
    m_hv = bpy.data.meshes.new("Mesh_Roof_HVAC")
    bm_hvac.to_mesh(m_hv)
    bm_hvac.free()
    obj_hvac = bpy.data.objects.new("Roof_HVAC_Units", m_hv)
    col.objects.link(obj_hvac)
    obj_hvac.data.materials.append(mats["acero"])

    # Convertir muro este a objeto
    bmesh.ops.recalc_face_normals(bm_east, faces=bm_east.faces)
    m_east = bpy.data.meshes.new("Mesh_East_Wall")
    bm_east.to_mesh(m_east)
    bm_east.free()
    obj_east = bpy.data.objects.new("East_Parking_Estructura", m_east)
    col.objects.link(obj_east)
    obj_east.data.materials.append(mats["muro"])
    obj_east.data.materials.append(mats["zocalo"])
    obj_east.data.materials.append(mats["azotea"])
    for p in m_east.polygons:
        c_z = sum(m_east.vertices[v].co.z for v in p.vertices) / len(p.vertices)
        if c_z < 0.42:
            p.material_index = 1
        elif c_z > 6.95:
            p.material_index = 2
        else:
            p.material_index = 0

    # Convertir cancelería y vidrios este
    bmesh.ops.recalc_face_normals(bm_alum, faces=bm_alum.faces)
    m_e_al = bpy.data.meshes.new("Mesh_East_Canceleria")
    bm_alum.to_mesh(m_e_al)
    bm_alum.free()
    obj_e_al = bpy.data.objects.new("East_Canceleria", m_e_al)
    col.objects.link(obj_e_al)
    obj_e_al.data.materials.append(mats["aluminio"])

    bmesh.ops.recalc_face_normals(bm_glass, faces=bm_glass.faces)
    m_e_gl = bpy.data.meshes.new("Mesh_East_Vidrio")
    bm_glass.to_mesh(m_e_gl)
    bm_glass.free()
    obj_e_gl = bpy.data.objects.new("East_Vidrio", m_e_gl)
    col.objects.link(obj_e_gl)
    obj_e_gl.data.materials.append(mats["vidrio"])

    bmesh.ops.recalc_face_normals(bm_blind, faces=bm_blind.faces)
    m_e_bl = bpy.data.meshes.new("Mesh_East_Persianas")
    bm_blind.to_mesh(m_e_bl)
    bm_blind.free()
    obj_e_bl = bpy.data.objects.new("East_Persianas", m_e_bl)
    col.objects.link(obj_e_bl)
    obj_e_bl.data.materials.append(mats["persianas"])

    # Objeto puerta simple de hierro blanco
    bmesh.ops.recalc_face_normals(bm_white_door, faces=bm_white_door.faces)
    m_wd = bpy.data.meshes.new("Mesh_East_Puerta_Hierro")
    bm_white_door.to_mesh(m_wd)
    bm_white_door.free()
    obj_wd = bpy.data.objects.new("East_Puerta_Hierro", m_wd)
    col.objects.link(obj_wd)
    obj_wd.data.materials.append(mats["rotulo_blanco"])

    # Rótulo de despacho en ventana de Crujía 1 PA Este
    f_ed = bpy.data.curves.new(type="FONT", name="Font_E_Despacho")
    f_ed.body = "LICENCIADO EN DERECHO"
    f_ed.size = 0.16
    f_ed.extrude = 0.01
    f_ed.align_x = 'CENTER'
    o_ed = bpy.data.objects.new("East_Txt_Despacho", f_ed)
    col.objects.link(o_ed)
    o_ed.location = (X_east - 0.05, 2.20, 5.85)
    o_ed.rotation_euler = (math.radians(90.0), 0.0, math.radians(-90.0))
    o_ed.data.materials.append(mats["rotulo_blanco"])

    # Rampa de servicio, caseta de vigilancia y letrero ENTRADA BBVA
    bm_rampa = bmesh.new()
    add_box(bm_rampa, 22.80, 27.20, 0.0, 14.00, -1.20, 0.0)
    bmesh.ops.recalc_face_normals(bm_rampa, faces=bm_rampa.faces)
    m_rm = bpy.data.meshes.new("Mesh_Rampa_Suelo")
    bm_rampa.to_mesh(m_rm)
    bm_rampa.free()
    obj_rampa = bpy.data.objects.new("Rampa_Suelo", m_rm)
    col.objects.link(obj_rampa)
    obj_rampa.data.materials.append(mats["asfalto"])

    # Barandal metálico tubular de la rampa
    bm_rail = bmesh.new()
    for y_post in [0.80, 4.00, 7.50, 11.00, 14.00]:
        add_box(bm_rail, 27.25, 27.35, y_post - 0.04, y_post + 0.04, 0.0, 1.10)
    add_box(bm_rail, 27.25, 27.35, 0.80, 14.00, 1.05, 1.12)
    add_box(bm_rail, 27.25, 27.35, 0.80, 14.00, 0.55, 0.60)
    add_box(bm_rail, 27.20, 27.50, 0.0, 14.00, -1.20, 0.20) # Murete lateral
    bmesh.ops.recalc_face_normals(bm_rail, faces=bm_rail.faces)
    m_rl = bpy.data.meshes.new("Mesh_Rampa_Barandal")
    bm_rail.to_mesh(m_rl)
    bm_rail.free()
    obj_rail = bpy.data.objects.new("Rampa_Barandal", m_rl)
    col.objects.link(obj_rail)
    obj_rail.data.materials.append(mats["aluminio"])

    # Caseta blanca de vigilancia de estacionamiento
    bm_caseta = bmesh.new()
    add_box(bm_caseta, 27.50, 30.50, 4.50, 7.50, 0.0, 2.80)
    add_box(bm_caseta, 27.35, 30.65, 4.35, 7.65, 2.75, 2.95) # Cornisa losa
    add_box(bm_caseta, 27.48, 27.52, 5.20, 6.80, 1.10, 2.00) # Ventanilla
    bmesh.ops.recalc_face_normals(bm_caseta, faces=bm_caseta.faces)
    m_cs = bpy.data.meshes.new("Mesh_Caseta_Blanca")
    bm_caseta.to_mesh(m_cs)
    bm_caseta.free()
    obj_caseta = bpy.data.objects.new("Caseta_Estacionamiento", m_cs)
    col.objects.link(obj_caseta)
    obj_caseta.data.materials.append(mats["muro"])

    # Barda perimetral azul del estacionamiento
    bm_park_wall = bmesh.new()
    add_box(bm_park_wall, 30.50, 36.50, 4.50, 4.80, 0.0, 2.20)
    bmesh.ops.recalc_face_normals(bm_park_wall, faces=bm_park_wall.faces)
    m_pw = bpy.data.meshes.new("Mesh_Parking_Wall")
    bm_park_wall.to_mesh(m_pw)
    bm_park_wall.free()
    obj_pw = bpy.data.objects.new("Parking_Perimeter_Wall", m_pw)
    col.objects.link(obj_pw)
    obj_pw.data.materials.append(mats["bbva_azul"])

    # Letrero 'ENTRADA BBVA ->'
    bm_sgn = bmesh.new()
    add_box(bm_sgn, 27.32, 27.38, 2.20, 2.26, 0.0, 1.85)
    add_box(bm_sgn, 27.30, 27.40, 1.60, 3.20, 1.25, 1.85)
    bmesh.ops.recalc_face_normals(bm_sgn, faces=bm_sgn.faces)
    m_sg = bpy.data.meshes.new("Mesh_Senal_Entrada_Ortogonal")
    bm_sgn.to_mesh(m_sg)
    bm_sgn.free()
    obj_sgn = bpy.data.objects.new("Senal_Entrada_BBVA_Ortogonal", m_sg)
    col.objects.link(obj_sgn)
    obj_sgn.data.materials.append(mats["bbva_azul"])

    f_sgn = bpy.data.curves.new(type="FONT", name="Font_Senal_Rampa_Ort")
    f_sgn.body = "ENTRADA\\nBBVA ->"
    f_sgn.size = 0.20
    f_sgn.extrude = 0.015
    f_sgn.align_x = 'CENTER'
    o_sgn = bpy.data.objects.new("Txt_Senal_Rampa_Ort", f_sgn)
    col.objects.link(o_sgn)
    o_sgn.location = (27.42, 2.40, 1.62)
    o_sgn.rotation_euler = (math.radians(90.0), 0.0, math.radians(90.0))
    o_sgn.data.materials.append(mats["rotulo_blanco"])

    return obj_east, [obj_e_al, obj_e_gl, obj_e_bl, o_ed, obj_hvac, obj_pw, obj_wd], obj_rampa, obj_rail, obj_caseta, obj_sgn, o_sgn

'''

    # 3. Reemplazo completo de build_south_and_inward_arc_facade
    old_sidewalk_func_start = 'def build_optional_sidewalk(mats, col):'
    idx_sidewalk = code.find(old_sidewalk_func_start)
    
    if idx_sidewalk == -1:
        print("ERROR: No se encontró build_optional_sidewalk.")
        return

    new_south_func = '''def build_south_and_inward_arc_facade(mats, col):
    """Construye la Fachada Sur posterior lisa, la pared en arco cóncavo hacia adentro
    y el cierre angulado a 45º (contraesquina de Guajardo) que conecta en (22.80, 20.80 m).
    Mantiene el pilar central y las dos ventanas rectangulares pequeñas con repisas."""
    bm_south = bmesh.new()
    bm_roof_arc = bmesh.new()
    bm_alum = bmesh.new()
    bm_glass = bmesh.new()
    
    Y_south = 25.20
    H_wall = 7.10
    
    # 1. PARED SUR LISA (X = 0.00 a 17.40 m, Y = 25.20 m)
    # Plinto basal (Z = -1.20 a 0.40)
    add_box(bm_south, -0.05, 17.40, Y_south - 0.28, Y_south + 0.12, -1.20, 0.40)
    # Muro principal liso (Z = 0.40 a 7.10)
    add_box(bm_south, -0.05, 17.40, Y_south - 0.28, Y_south + 0.12, 0.40, H_wall)
    # Moldura intermedia a media altura
    add_box(bm_south, -0.05, 17.40, Y_south + 0.12, Y_south + 0.22, 3.16, 3.28)
    # Albardilla / pretil coping
    add_box(bm_south, -0.05, 17.40, Y_south - 0.35, Y_south + 0.18, 7.10, 7.25)
    # Columna esquinera de transición en X = 17.40
    add_box(bm_south, 17.20, 17.60, Y_south - 0.32, Y_south + 0.25, -1.20, 7.35)

    # 2. PARED EN ARCO CÓNCAVO HACIA ADENTRO: desde (17.40, 25.20) hasta (21.00, 22.60)
    # El arco se curva hacia el interior del edificio (sagita hacia el centro)
    # y en (21.00, 22.60) su tangente empalma suavemente con el chaflán a 45º.
    p_start = (17.40, 25.20)
    p_end = (21.00, 22.60)
    n_segments = 14
    thick = 0.35
    sagitta = 0.85 # Profundidad de concavidad hacia el interior
    
    # Vector normal perpendicular hacia el interior
    dx_c = p_end[0] - p_start[0]
    dy_c = p_end[1] - p_start[1]
    L_c = math.hypot(dx_c, dy_c)
    # Normal hacia el interior (sentido -X, -Y)
    nx_in = dy_c / L_c
    ny_in = -dx_c / L_c
    if ny_in > 0:
        nx_in, ny_in = -nx_in, -ny_in
    # Normal hacia el exterior
    nx_out, ny_out = -nx_in, -ny_in

    arc_points = []
    for i in range(n_segments + 1):
        u = i / float(n_segments)
        # Punto sobre la cuerda recta
        cx = p_start[0] + u * dx_c
        cy = p_start[1] + u * dy_c
        # Desplazamiento cóncavo parabólico hacia adentro
        disp = sagitta * math.sin(math.pi * u)
        x = cx + disp * nx_in
        y = cy + disp * ny_in
        arc_points.append((x, y))

    # Construir caras del arco
    for i in range(n_segments):
        x1, y1 = arc_points[i]
        x2, y2 = arc_points[i+1]
        
        dx = x2 - x1
        dy = y2 - y1
        L = math.hypot(dx, dy)
        if L > 0:
            nx = -dy / L * thick
            ny = dx / L * thick
        else:
            nx, ny = 0.0, -thick
            
        # Asegurar orientación hacia el exterior
        if ny < 0 and nx > 0:
            nx, ny = -nx, -ny

        # Plinto basal (Z = -1.20 a 0.40)
        v_b1 = bm_south.verts.new((x1, y1, -1.20))
        v_b2 = bm_south.verts.new((x2, y2, -1.20))
        v_b3 = bm_south.verts.new((x2 + nx, y2 + ny, -1.20))
        v_b4 = bm_south.verts.new((x1 + nx, y1 + ny, -1.20))
        
        v_t1 = bm_south.verts.new((x1, y1, 0.40))
        v_t2 = bm_south.verts.new((x2, y2, 0.40))
        v_t3 = bm_south.verts.new((x2 + nx, y2 + ny, 0.40))
        v_t4 = bm_south.verts.new((x1 + nx, y1 + ny, 0.40))
        
        bm_south.faces.new((v_b1, v_b2, v_t2, v_t1))
        bm_south.faces.new((v_b2, v_b3, v_t3, v_t2))
        bm_south.faces.new((v_b3, v_b4, v_t4, v_t3))
        bm_south.faces.new((v_b4, v_b1, v_t1, v_t4))
        
        # Muro principal (Z = 0.40 a 7.10)
        v_w1 = bm_south.verts.new((x1, y1, H_wall))
        v_w2 = bm_south.verts.new((x2, y2, H_wall))
        v_w3 = bm_south.verts.new((x2 + nx, y2 + ny, H_wall))
        v_w4 = bm_south.verts.new((x1 + nx, y1 + ny, H_wall))
        
        bm_south.faces.new((v_t1, v_t2, v_w2, v_w1))
        bm_south.faces.new((v_t2, v_t3, v_w3, v_w2))
        bm_south.faces.new((v_t3, v_t4, v_w4, v_w3))
        bm_south.faces.new((v_t4, v_t1, v_w1, v_w4))
        bm_south.faces.new((v_w1, v_w2, v_w3, v_w4)) # Tapa pretil
        
        # Losa de azotea hermética detrás del arco
        vr1 = bm_roof_arc.verts.new((x1, y1, 7.00))
        vr2 = bm_roof_arc.verts.new((x2, y2, 7.00))
        vr3 = bm_roof_arc.verts.new((x2, Y_south, 7.00))
        vr4 = bm_roof_arc.verts.new((x1, Y_south, 7.00))
        bm_roof_arc.faces.new((vr1, vr2, vr3, vr4))
        vr1t = bm_roof_arc.verts.new((x1, y1, 7.25))
        vr2t = bm_roof_arc.verts.new((x2, y2, 7.25))
        vr3t = bm_roof_arc.verts.new((x2, Y_south, 7.25))
        vr4t = bm_roof_arc.verts.new((x1, Y_south, 7.25))
        bm_roof_arc.faces.new((vr4t, vr3t, vr2t, vr1t))

    # 3. CIERRE ANGULADO A 45º (CONTRAESQUINA DE GUAJARDO)
    # Desde (21.00, 22.60) hasta (22.80, 20.80 m)
    # Delta X = +1.80, Delta Y = -1.80 (ángulo exacto de 45º)
    x_c1, y_c1 = 21.00, 22.60
    x_c2, y_c2 = 22.80, 20.80
    nx_cham = 0.25
    ny_cham = 0.25 # Normal hacia el exterior (sentido +X, +Y)
    
    # Plinto basal chaflán
    v_cb1 = bm_south.verts.new((x_c1, y_c1, -1.20))
    v_cb2 = bm_south.verts.new((x_c2, y_c2, -1.20))
    v_cb3 = bm_south.verts.new((x_c2 + nx_cham, y_c2 + ny_cham, -1.20))
    v_cb4 = bm_south.verts.new((x_c1 + nx_cham, y_c1 + ny_cham, -1.20))
    v_ct1 = bm_south.verts.new((x_c1, y_c1, 0.40))
    v_ct2 = bm_south.verts.new((x_c2, y_c2, 0.40))
    v_ct3 = bm_south.verts.new((x_c2 + nx_cham, y_c2 + ny_cham, 0.40))
    v_ct4 = bm_south.verts.new((x_c1 + nx_cham, y_c1 + ny_cham, 0.40))
    bm_south.faces.new((v_cb1, v_cb2, v_ct2, v_ct1))
    bm_south.faces.new((v_cb2, v_cb3, v_ct3, v_ct2))
    bm_south.faces.new((v_cb3, v_cb4, v_ct4, v_ct3))
    bm_south.faces.new((v_cb4, v_cb1, v_ct1, v_ct4))

    # Muro principal chaflán
    v_cw1 = bm_south.verts.new((x_c1, y_c1, H_wall))
    v_cw2 = bm_south.verts.new((x_c2, y_c2, H_wall))
    v_cw3 = bm_south.verts.new((x_c2 + nx_cham, y_c2 + ny_cham, H_wall))
    v_cw4 = bm_south.verts.new((x_c1 + nx_cham, y_c1 + ny_cham, H_wall))
    bm_south.faces.new((v_ct1, v_ct2, v_cw2, v_cw1))
    bm_south.faces.new((v_ct2, v_ct3, v_cw3, v_cw2))
    bm_south.faces.new((v_ct3, v_ct4, v_cw4, v_cw3))
    bm_south.faces.new((v_ct4, v_ct1, v_cw1, v_cw4))
    bm_south.faces.new((v_cw1, v_cw2, v_cw3, v_cw4)) # Pretil
    
    # Losa de azotea chaflán
    v_cr1 = bm_roof_arc.verts.new((x_c1, y_c1, 7.00))
    v_cr2 = bm_roof_arc.verts.new((x_c2, y_c2, 7.00))
    v_cr3 = bm_roof_arc.verts.new((x_c1, 20.80, 7.00))
    bm_roof_arc.faces.new((v_cr1, v_cr2, v_cr3))
    v_cr1t = bm_roof_arc.verts.new((x_c1, y_c1, 7.25))
    v_cr2t = bm_roof_arc.verts.new((x_c2, y_c2, 7.25))
    v_cr3t = bm_roof_arc.verts.new((x_c1, 20.80, 7.25))
    bm_roof_arc.faces.new((v_cr3t, v_cr2t, v_cr1t))

    # 4. PILAR DELGADO SALIENTE EN EL CENTRO DEL ARCO (Ground Truth media_1789784140324)
    # Centro del arco (u = 0.5)
    mid_idx = n_segments // 2
    px_mid, py_mid = arc_points[mid_idx]
    # El pilar se orienta hacia el exterior con saliente marcada
    add_box(bm_south, px_mid - 0.20, px_mid + 0.20, py_mid - 0.15, py_mid + 0.55, -1.20, 7.45)

    # 5. DOS VENTANAS RECTANGULARES PEQUEÑAS EN PLANTA ALTA CON REPISAS
    # Ventana 1 (hacia el lado de cara Sur, u ~ 0.25)
    w1_idx = int(n_segments * 0.28)
    w1_x, w1_y = arc_points[w1_idx]
    add_box(bm_south, w1_x - 0.55, w1_x + 0.55, w1_y - 0.05, w1_y + 0.35, 5.28, 5.42) # Repisa
    add_box(bm_alum, w1_x - 0.48, w1_x + 0.48, w1_y + 0.05, w1_y + 0.25, 5.42, 5.46)
    add_box(bm_alum, w1_x - 0.48, w1_x + 0.48, w1_y + 0.05, w1_y + 0.25, 6.30, 6.35)
    add_box(bm_alum, w1_x - 0.48, w1_x - 0.44, w1_y + 0.05, w1_y + 0.25, 5.42, 6.35)
    add_box(bm_alum, w1_x + 0.44, w1_x + 0.48, w1_y + 0.05, w1_y + 0.25, 5.42, 6.35)
    add_box(bm_glass, w1_x - 0.44, w1_x + 0.44, w1_y + 0.12, w1_y + 0.18, 5.48, 6.28)

    # Ventana 2 (hacia el lado del chaflán, u ~ 0.72)
    w2_idx = int(n_segments * 0.72)
    w2_x, w2_y = arc_points[w2_idx]
    add_box(bm_south, w2_x - 0.55, w2_x + 0.55, w2_y - 0.05, w2_y + 0.35, 5.28, 5.42) # Repisa
    add_box(bm_alum, w2_x - 0.48, w2_x + 0.48, w2_y + 0.05, w2_y + 0.25, 5.42, 5.46)
    add_box(bm_alum, w2_x - 0.48, w2_x + 0.48, w2_y + 0.05, w2_y + 0.25, 6.30, 6.35)
    add_box(bm_alum, w2_x - 0.48, w2_x - 0.44, w2_y + 0.05, w2_y + 0.25, 5.42, 6.35)
    add_box(bm_alum, w2_x + 0.44, w2_x + 0.48, w2_y + 0.05, w2_y + 0.25, 5.42, 6.35)
    add_box(bm_glass, w2_x - 0.44, w2_x + 0.44, w2_y + 0.12, w2_y + 0.18, 5.48, 6.28)

    bmesh.ops.recalc_face_normals(bm_south, faces=bm_south.faces)
    m_sth = bpy.data.meshes.new("Mesh_South_Inward_Arc")
    bm_south.to_mesh(m_sth)
    bm_south.free()
    obj_south = bpy.data.objects.new("South_Inward_Arc_Wall", m_sth)
    col.objects.link(obj_south)
    obj_south.data.materials.append(mats["muro"])
    obj_south.data.materials.append(mats["zocalo"])
    for p in m_sth.polygons:
        c_z = sum(m_sth.vertices[v].co.z for v in p.vertices) / len(p.vertices)
        if c_z < 0.42:
            p.material_index = 1
        else:
            p.material_index = 0
            
    bmesh.ops.recalc_face_normals(bm_roof_arc, faces=bm_roof_arc.faces)
    m_rf = bpy.data.meshes.new("Mesh_Roof_Arc_Closure")
    bm_roof_arc.to_mesh(m_rf)
    bm_roof_arc.free()
    obj_rf = bpy.data.objects.new("Roof_Arc_Closure", m_rf)
    col.objects.link(obj_rf)
    obj_rf.data.materials.append(mats["azotea"])
    
    bmesh.ops.recalc_face_normals(bm_alum, faces=bm_alum.faces)
    m_al = bpy.data.meshes.new("Mesh_South_Arc_Canceleria")
    bm_alum.to_mesh(m_al)
    bm_alum.free()
    obj_al = bpy.data.objects.new("South_Arc_Canceleria", m_al)
    col.objects.link(obj_al)
    obj_al.data.materials.append(mats["aluminio"])
    
    bmesh.ops.recalc_face_normals(bm_glass, faces=bm_glass.faces)
    m_gl = bpy.data.meshes.new("Mesh_South_Arc_Vidrio")
    bm_glass.to_mesh(m_gl)
    bm_glass.free()
    obj_gl = bpy.data.objects.new("South_Arc_Vidrio", m_gl)
    col.objects.link(obj_gl)
    obj_gl.data.materials.append(mats["vidrio"])
    
    return obj_south, [obj_rf, obj_al, obj_gl]

'''

    # Unir las funciones modificadas este y sur
    code = code[:idx_east] + new_east_func + new_south_func + code[idx_sidewalk:]

    # 4. Actualizar generate_godot_tscn reemplazando estrictamente hasta 'def main():'
    old_tscn_func_start = 'def generate_godot_tscn(tscn_path, glb_rel_path):'
    old_main_func_start = 'def main():'
    
    idx_tscn = code.find(old_tscn_func_start)
    idx_main = code.find(old_main_func_start)
    
    if idx_tscn != -1 and idx_main != -1:
        new_tscn_func = '''def generate_godot_tscn(tscn_path, glb_rel_path):
    """Genera la escena .tscn de Godot 4 con colisionadores analíticos rectificados para V8.0:
    - Col_East_Wall ajustado a 20.40 m (6 subdivisiones).
    - Col_Contraesquina_Chamfer a 45º conectando en (22.80, 20.80 m).
    - Peldaños transitables en DENTISTA y rampa sin obstáculos."""
    tscn_content = f"""[gd_scene load_steps=23 format=3 uid="uid://bbva_tecate_centro_010"]

[ext_resource type="PackedScene" path="{glb_rel_path}" id="1_mesh"]
[ext_resource type="PackedScene" path="res://assets/buildings/banqueta_bbva_tecate.glb" id="2_banqueta"]

[sub_resource type="BoxShape3D" id="BoxShape3D_juarez"]
size = Vector3(18.6, 8.5, 16.0)

[sub_resource type="BoxShape3D" id="BoxShape3D_cardenas_bank"]
size = Vector3(16.0, 8.5, 21.0)

[sub_resource type="BoxShape3D" id="BoxShape3D_dentista_south"]
size = Vector3(3.2, 8.5, 0.6)

[sub_resource type="BoxShape3D" id="BoxShape3D_dentista_north"]
size = Vector3(3.2, 8.5, 1.8)

[sub_resource type="BoxShape3D" id="BoxShape3D_dentista_back"]
size = Vector3(12.8, 8.5, 4.8)

[sub_resource type="BoxShape3D" id="BoxShape3D_dentista_step_1"]
size = Vector3(0.40, 0.18, 2.30)

[sub_resource type="BoxShape3D" id="BoxShape3D_dentista_step_2"]
size = Vector3(0.40, 0.36, 2.30)

[sub_resource type="BoxShape3D" id="BoxShape3D_dentista_step_3"]
size = Vector3(0.40, 0.54, 2.30)

[sub_resource type="BoxShape3D" id="BoxShape3D_dentista_step_4"]
size = Vector3(1.75, 0.72, 2.30)

[sub_resource type="BoxShape3D" id="BoxShape3D_puertas"]
size = Vector3(5.8, 9.1, 0.35)

[sub_resource type="BoxShape3D" id="BoxShape3D_south_wall"]
size = Vector3(17.4, 8.5, 0.4)

[sub_resource type="BoxShape3D" id="BoxShape3D_inward_arc"]
size = Vector3(3.8, 8.5, 0.4)

[sub_resource type="BoxShape3D" id="BoxShape3D_contraesquina_chamfer"]
size = Vector3(0.4, 8.5, 2.6)

[sub_resource type="BoxShape3D" id="BoxShape3D_east_wall"]
size = Vector3(0.4, 8.5, 20.4)

[sub_resource type="BoxShape3D" id="BoxShape3D_rampa_murete"]
size = Vector3(0.3, 1.7, 14.0)

[sub_resource type="BoxShape3D" id="BoxShape3D_rampa_floor"]
size = Vector3(4.4, 0.2, 14.0)

[sub_resource type="BoxShape3D" id="BoxShape3D_banqueta_juarez"]
size = Vector3(34.6, 0.18, 3.8)

[sub_resource type="BoxShape3D" id="BoxShape3D_banqueta_cardenas"]
size = Vector3(3.8, 0.18, 32.0)

[node name="BBVA_Tecate" type="StaticBody3D"]

[node name="ModelInstance" parent="." instance=ExtResource("1_mesh")]

[node name="BanquetaInstance" parent="." instance=ExtResource("2_banqueta")]

[node name="Col_Juarez" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 13.5, 3.05, -8.0)
shape = SubResource("BoxShape3D_juarez")

[node name="Col_Cardenas_Bank" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 8.0, 3.05, -14.7)
shape = SubResource("BoxShape3D_cardenas_bank")

[node name="Col_Dentista_South" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 1.6, 3.05, -25.5)
shape = SubResource("BoxShape3D_dentista_south")

[node name="Col_Dentista_North" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 1.6, 3.05, -29.1)
shape = SubResource("BoxShape3D_dentista_north")

[node name="Col_Dentista_Interior" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 9.6, 3.05, -27.6)
shape = SubResource("BoxShape3D_dentista_back")

[node name="Col_Dentista_Step_1" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0.40, 0.09, -27.0)
shape = SubResource("BoxShape3D_dentista_step_1")

[node name="Col_Dentista_Step_2" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0.80, 0.18, -27.0)
shape = SubResource("BoxShape3D_dentista_step_2")

[node name="Col_Dentista_Step_3" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 1.20, 0.27, -27.0)
shape = SubResource("BoxShape3D_dentista_step_3")

[node name="Col_Dentista_Step_4" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 2.275, 0.36, -27.0)
shape = SubResource("BoxShape3D_dentista_step_4")

[node name="Col_Puertas_Chamfer" type="CollisionShape3D" parent="."]
transform = Transform3D(0.707107, 0, 0.707107, 0, 1, 0, -0.707107, 0, 0.707107, 2.12, 4.55, -2.12)
shape = SubResource("BoxShape3D_puertas")

[node name="Col_South_Wall" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 8.7, 3.05, -25.0)
shape = SubResource("BoxShape3D_south_wall")

[node name="Col_Inward_Arc" type="CollisionShape3D" parent="."]
transform = Transform3D(0.81, 0, 0.585, 0, 1, 0, -0.585, 0, 0.81, 19.2, 3.05, -23.9)
shape = SubResource("BoxShape3D_inward_arc")

[node name="Col_Contraesquina_Chamfer" type="CollisionShape3D" parent="."]
transform = Transform3D(0.707107, 0, -0.707107, 0, 1, 0, 0.707107, 0, 0.707107, 21.90, 3.05, -21.70)
shape = SubResource("BoxShape3D_contraesquina_chamfer")

[node name="Col_East_Wall" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 22.6, 3.05, -10.60)
shape = SubResource("BoxShape3D_east_wall")

[node name="Col_Rampa_Murete" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 27.35, 0.85, -7.0)
shape = SubResource("BoxShape3D_rampa_murete")

[node name="Col_Rampa_Floor" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 25.0, -0.1, -7.0)
shape = SubResource("BoxShape3D_rampa_floor")

[node name="Col_Banqueta_Juarez" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 13.5, 0.09, 1.9)
shape = SubResource("BoxShape3D_banqueta_juarez")

[node name="Col_Banqueta_Cardenas" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, -1.9, 0.09, -16.0)
shape = SubResource("BoxShape3D_banqueta_cardenas")
"""
    with open(tscn_path, "w", encoding="utf-8") as f:
        f.write(tscn_content)
    print(f"--> Escena Godot generada: {tscn_path}")

'''
        code = code[:idx_tscn] + new_tscn_func + code[idx_main:]

    # 5. Cámaras de renderizado
    # Cam_South_Inward_Arc calibrada para ver cara Sur lisa, arco con pilar y ventanas, y el cierre angulado a 45º
    old_c8 = '''    # 8. Cámara 'South_Inward_Arc': Perspectiva hacia el arco cóncavo posterior matching media_1789784140324
    c8_data = bpy.data.cameras.new("Cam_South_Inward_Arc")
    c8_data.lens = 32
    c8 = bpy.data.objects.new("Cam_South_Inward_Arc", c8_data)
    col.objects.link(c8)
    loc8 = Vector((14.80, 34.50, 2.40))
    tgt8 = Vector((19.50, 24.50, 4.00))
    dir8 = tgt8 - loc8
    c8.location = loc8
    c8.rotation_euler = dir8.to_track_quat('-Z', 'Y').to_euler()
    cams["south_inward_arc"] = c8'''

    new_c8 = '''    # 8. Cámara 'South_Inward_Arc': Perspectiva hacia el arco cóncavo posterior y cierre angulado a 45º
    c8_data = bpy.data.cameras.new("Cam_South_Inward_Arc")
    c8_data.lens = 30
    c8 = bpy.data.objects.new("Cam_South_Inward_Arc", c8_data)
    col.objects.link(c8)
    loc8 = Vector((15.20, 32.50, 2.50))
    tgt8 = Vector((19.80, 22.80, 3.80))
    dir8 = tgt8 - loc8
    c8.location = loc8
    c8.rotation_euler = dir8.to_track_quat('-Z', 'Y').to_euler()
    cams["south_inward_arc"] = c8'''

    if old_c8 in code:
        code = code.replace(old_c8, new_c8)

    with open(script_path, "w", encoding="utf-8") as f:
        f.write(code)

    print("Actualización V8.0 aplicada con éxito a scripts/generate_bbva_tecate.py")

if __name__ == "__main__":
    main()
