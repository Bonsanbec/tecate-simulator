import re

with open("scripts/generate_bbva_tecate.py", "r", encoding="utf-8") as f:
    code = f.read()

# 1. Update build_45deg_guajardo_corner
old_guajardo = '''def build_45deg_guajardo_corner(mats, col):
    """Construye el chaflán a 45º con el Torreón Guajardo 1956 (trapecio rocoso desgastado) y espectacular 2009."""
    bm_tower = bmesh.new()
    bm_glass = bmesh.new()
    H_tower = 9.05
    
    # Retorno Norte (Y = 4.20, X de -0.40 a 0.40)
    add_box(bm_tower, -0.40, 0.40, 4.15, 4.25, 0.0, H_tower)
    # Retorno Este (X = 4.20, Y de -0.40 a 0.40)
    add_box(bm_tower, 4.15, 4.25, -0.40, 0.40, 0.0, H_tower)
    
    # Muros interiores para sellar el prisma hacia adentro
    add_box(bm_tower, 0.40, 4.20, 4.15, 4.25, 0.0, H_tower)
    add_box(bm_tower, 4.15, 4.25, 0.40, 4.20, 0.0, H_tower)
    
    # Losa de azotea del torreón (5 lados)
    v_top = [
        bm_tower.verts.new((-0.40, 4.20, H_tower)),
        bm_tower.verts.new((4.20, -0.40, H_tower)),
        bm_tower.verts.new((4.20, 0.40, H_tower)),
        bm_tower.verts.new((4.20, 4.20, H_tower)),
        bm_tower.verts.new((0.40, 4.20, H_tower))
    ]
    bm_tower.faces.new(v_top)
    
    # 1. Remate superior rocoso desgastado (coping pétreo natural, sin marco blanco plástico)
    add_wall_segment(bm_tower, -0.43, 4.23, 4.23, -0.43, H_tower - 0.05, H_tower + 0.10, thickness=0.55)
    
    # 2. Muro de mosaico veneciano / trapecio rocoso desgastado (Z = 3.20 a H_tower)
    add_wall_segment(bm_tower, -0.40, 4.20, 4.20, -0.40, 3.20, H_tower, thickness=0.45)
    
    # 3. Viga dintel de concreto sobre acceso (Z = 2.90 a 3.20)
    add_wall_segment(bm_tower, -0.42, 4.22, 4.22, -0.42, 2.90, 3.20, thickness=0.50)
    
    # 4. Planta baja del chaflán: Acceso principal con puertas dobles
    # Muros laterales de planta baja con zócalo (estucados en blanco, Ground Truth media_1789777326353)
    add_wall_segment(bm_tower, -0.40, 4.20, 1.05, 2.75, 0.0, 2.90, thickness=0.45)
    add_wall_segment(bm_tower, 2.75, 1.05, 4.20, -0.40, 0.0, 2.90, thickness=0.45)
    
    # Cancelería de aluminio anodizado brillante
    add_wall_segment(bm_tower, 1.05, 2.75, 2.75, 1.05, 0.0, 0.08, thickness=0.12) # Umbral
    add_wall_segment(bm_tower, 1.05, 2.75, 2.75, 1.05, 2.82, 2.90, thickness=0.12) # Dintel cancelería
    add_wall_segment(bm_tower, 1.05, 2.75, 2.75, 1.05, 2.12, 2.18, thickness=0.12) # Travesaño montante
    add_wall_segment(bm_tower, 1.05, 2.75, 1.12, 2.68, 0.0, 2.90, thickness=0.12) # Jamba izquierda
    add_wall_segment(bm_tower, 2.68, 1.12, 2.75, 1.05, 0.0, 2.90, thickness=0.12) # Jamba derecha
    add_wall_segment(bm_tower, 1.86, 1.94, 1.94, 1.86, 0.0, 2.15, thickness=0.12) # Parteluz central
    
    # Jaladeras tubulares de aluminio (push/pull handles)
    add_wall_segment(bm_tower, 1.80, 1.92, 1.84, 1.88, 0.90, 1.25, thickness=0.04)
    add_wall_segment(bm_tower, 1.96, 1.76, 2.00, 1.72, 0.90, 1.25, thickness=0.04)
    
    # Puertas dobles de vidrio templado y montante superior
    add_wall_segment(bm_glass, 1.12, 2.68, 2.68, 1.12, 0.08, 2.12, thickness=0.02) # Hojas inferiores
    add_wall_segment(bm_glass, 1.12, 2.68, 2.68, 1.12, 2.18, 2.82, thickness=0.02) # Montante superior
    
    # Asignar materiales
    bmesh.ops.recalc_face_normals(bm_tower, faces=bm_tower.faces)
    m_tower = bpy.data.meshes.new("Mesh_Guajardo_Torreon")
    bm_tower.to_mesh(m_tower)
    bm_tower.free()
    obj_tower = bpy.data.objects.new("Guajardo_Torreon_45", m_tower)
    col.objects.link(obj_tower)
    obj_tower.data.materials.append(mats["mosaico_guajardo"]) # 0
    obj_tower.data.materials.append(mats["coping_rocoso"])    # 1 (remate rocoso)
    obj_tower.data.materials.append(mats["muro"])             # 2 (muro/dintel blanco)
    obj_tower.data.materials.append(mats["zocalo"])           # 3 (zócalo basal)
    obj_tower.data.materials.append(mats["aluminio"])         # 4 (cancelería)
    
    for p in m_tower.polygons:
        c_z = sum(m_tower.vertices[v].co.z for v in p.vertices) / len(p.vertices)
        c_x = sum(m_tower.vertices[v].co.x for v in p.vertices) / len(p.vertices)
        c_y = sum(m_tower.vertices[v].co.y for v in p.vertices) / len(p.vertices)
        if c_z < 0.42:
            p.material_index = 3 # Zócalo
        elif c_z >= H_tower - 0.02:
            p.material_index = 1 # Remate rocoso desgastado
        elif c_z >= 2.88 and c_z <= 3.22:
            p.material_index = 2 # Dintel estucado blanco
        elif c_z < 2.90:
            # Los muros laterales a los costados del vano son estucados blancos
            if abs(c_x - c_y) > 0.90:
                p.material_index = 2 # Muro lateral blanco
            else:
                p.material_index = 4 # Cancelería de aluminio
        elif c_x > 4.10 or c_y > 4.10:
            p.material_index = 2 # Retornos laterales estucados
        else:
            p.material_index = 0 # Mosaico vítreo pizarra meteorizada'''

new_guajardo = '''def build_45deg_guajardo_corner(mats, col):
    """Construye el chaflán a 45º con el Torreón Guajardo 1956 en TRAPECIO rocoso desgastado, ventanales laterales y espectacular 2009."""
    bm_tower = bmesh.new()
    bm_glass = bmesh.new()
    bm_blind = bmesh.new()
    H_tower = 9.05
    
    # Retorno Norte (Y = 4.20, X de -0.40 a 0.40)
    add_box(bm_tower, -0.40, 0.40, 4.15, 4.25, 0.0, H_tower)
    # Retorno Este (X = 4.20, Y de -0.40 a 0.40)
    add_box(bm_tower, 4.15, 4.25, -0.40, 0.40, 0.0, H_tower)
    
    # Muros interiores para sellar el prisma hacia adentro
    add_box(bm_tower, 0.40, 4.20, 4.15, 4.25, 0.0, H_tower)
    add_box(bm_tower, 4.15, 4.25, 0.40, 4.20, 0.0, H_tower)
    
    # Losa de azotea del torreón (5 lados)
    v_top = [
        bm_tower.verts.new((-0.40, 4.20, H_tower)),
        bm_tower.verts.new((4.20, -0.40, H_tower)),
        bm_tower.verts.new((4.20, 0.40, H_tower)),
        bm_tower.verts.new((4.20, 4.20, H_tower)),
        bm_tower.verts.new((0.40, 4.20, H_tower))
    ]
    bm_tower.faces.new(v_top)
    
    # 1. Trapecio rocoso desgastado de mosaico veneciano (Z = 3.20 a H_tower = 9.05)
    # En la base Z = 3.20: ancho de 5.80 m (desde (-0.15, 3.95) hasta (3.95, -0.15))
    # En la cima Z = 9.05: estrechamiento simétrico en trapecio a 4.60 m (desde (0.27, 3.53) hasta (3.53, 0.27))
    th = 0.45
    nx = 0.70710678 * th
    ny = 0.70710678 * th
    
    v1 = bm_tower.verts.new((-0.15, 3.95, 3.20))
    v2 = bm_tower.verts.new((3.95, -0.15, 3.20))
    v3 = bm_tower.verts.new((3.53, 0.27, H_tower))
    v4 = bm_tower.verts.new((0.27, 3.53, H_tower))
    v5 = bm_tower.verts.new((-0.15 + nx, 3.95 + ny, 3.20))
    v6 = bm_tower.verts.new((3.95 + nx, -0.15 + ny, 3.20))
    v7 = bm_tower.verts.new((3.53 + nx, 0.27 + ny, H_tower))
    v8 = bm_tower.verts.new((0.27 + nx, 3.53 + ny, H_tower))
    
    bm_tower.faces.new((v1, v2, v3, v4)) # Frente del trapecio
    bm_tower.faces.new((v6, v5, v8, v7)) # Dorso
    bm_tower.faces.new((v4, v8, v5, v1)) # Arista inclinada izquierda
    bm_tower.faces.new((v2, v6, v7, v3)) # Arista inclinada derecha
    bm_tower.faces.new((v4, v3, v7, v8)) # Tapa superior
    bm_tower.faces.new((v1, v5, v6, v2)) # Fondo inferior
    
    # Albardilla / Coping pétreo superior coronando el trapecio (Z = H_tower a H_tower + 0.12)
    th_c = 0.55
    cx_c = 0.70710678 * th_c
    cy_c = 0.70710678 * th_c
    cv1 = bm_tower.verts.new((0.22, 3.58, H_tower - 0.05))
    cv2 = bm_tower.verts.new((3.58, 0.22, H_tower - 0.05))
    cv3 = bm_tower.verts.new((3.58, 0.22, H_tower + 0.12))
    cv4 = bm_tower.verts.new((0.22, 3.58, H_tower + 0.12))
    cv5 = bm_tower.verts.new((0.22 + cx_c, 3.58 + cy_c, H_tower - 0.05))
    cv6 = bm_tower.verts.new((3.58 + cx_c, 0.22 + cy_c, H_tower - 0.05))
    cv7 = bm_tower.verts.new((3.58 + cx_c, 0.22 + cy_c, H_tower + 0.12))
    cv8 = bm_tower.verts.new((0.22 + cx_c, 3.58 + cy_c, H_tower + 0.12))
    bm_tower.faces.new((cv1, cv2, cv3, cv4))
    bm_tower.faces.new((cv6, cv5, cv8, cv7))
    bm_tower.faces.new((cv4, cv8, cv5, cv1))
    bm_tower.faces.new((cv2, cv6, cv7, cv3))
    bm_tower.faces.new((cv4, cv3, cv7, cv8))
    bm_tower.faces.new((cv1, cv5, cv6, cv2))
    
    # Muros de conexión lateral estucados en blanco hacia las fachadas de Juárez y Cárdenas
    add_wall_segment(bm_tower, -0.40, 4.20, -0.15, 3.95, 3.20, 7.10, thickness=0.45)
    add_wall_segment(bm_tower, 3.95, -0.15, 4.20, -0.40, 3.20, 7.10, thickness=0.45)
    
    # 2. Viga dintel de concreto sobre todo el chaflán en PB (Z = 2.85 a 3.20)
    add_wall_segment(bm_tower, -0.42, 4.22, 4.22, -0.42, 2.85, 3.20, thickness=0.50)
    
    # 3. Planta baja del chaflán: Puertas dobles en el centro Y VENTANALES a ambos lados (Comentario 9)
    # Plinto basal (zócalo oscuro Z = 0.0 a 0.40)
    add_wall_segment(bm_tower, -0.40, 4.20, 4.20, -0.40, 0.0, 0.40, thickness=0.45)
    
    # --- Vano Izquierdo: Ventanal vidriado (desde (-0.20, 4.00) hasta (1.10, 2.70)) ---
    # Cancelería de aluminio
    add_wall_segment(bm_tower, -0.20, 4.00, 1.10, 2.70, 0.40, 0.46, thickness=0.12) # Umbral
    add_wall_segment(bm_tower, -0.20, 4.00, 1.10, 2.70, 2.79, 2.85, thickness=0.12) # Dintel
    add_wall_segment(bm_tower, -0.20, 4.00, -0.14, 3.94, 0.40, 2.85, thickness=0.12) # Jamba izq
    add_wall_segment(bm_tower, 1.04, 2.76, 1.10, 2.70, 0.40, 2.85, thickness=0.12) # Jamba der
    add_wall_segment(bm_tower, 0.42, 3.38, 0.48, 3.32, 0.40, 2.85, thickness=0.12) # Montante central
    # Vidrio Tintex y persianas
    add_wall_segment(bm_glass, -0.14, 3.94, 1.04, 2.76, 0.46, 2.79, thickness=0.02)
    add_wall_segment(bm_blind, -0.12, 3.92, 1.02, 2.78, 0.48, 2.77, thickness=0.02)
    
    # --- Vano Central: Puertas dobles de acceso vidriadas (desde (1.10, 2.70) hasta (2.70, 1.10)) ---
    add_wall_segment(bm_tower, 1.10, 2.70, 2.70, 1.10, 0.0, 0.08, thickness=0.12) # Umbral
    add_wall_segment(bm_tower, 1.10, 2.70, 2.70, 1.10, 2.77, 2.85, thickness=0.12) # Dintel
    add_wall_segment(bm_tower, 1.10, 2.70, 2.70, 1.10, 2.12, 2.18, thickness=0.12) # Travesaño
    add_wall_segment(bm_tower, 1.10, 2.70, 1.16, 2.64, 0.0, 2.85, thickness=0.12) # Jamba izq
    add_wall_segment(bm_tower, 2.64, 1.16, 2.70, 1.10, 0.0, 2.85, thickness=0.12) # Jamba der
    add_wall_segment(bm_tower, 1.87, 1.93, 1.93, 1.87, 0.0, 2.15, thickness=0.12) # Parteluz central
    # Jaladeras tubulares
    add_wall_segment(bm_tower, 1.80, 1.92, 1.84, 1.88, 0.90, 1.25, thickness=0.04)
    add_wall_segment(bm_tower, 1.96, 1.76, 2.00, 1.72, 0.90, 1.25, thickness=0.04)
    # Vidrios de las puertas y montante
    add_wall_segment(bm_glass, 1.16, 2.64, 2.64, 1.16, 0.08, 2.12, thickness=0.02)
    add_wall_segment(bm_glass, 1.16, 2.64, 2.64, 1.16, 2.18, 2.77, thickness=0.02)
    
    # --- Vano Derecho: Ventanal vidriado (desde (2.70, 1.10) hasta (4.00, -0.20)) ---
    add_wall_segment(bm_tower, 2.70, 1.10, 4.00, -0.20, 0.40, 0.46, thickness=0.12) # Umbral
    add_wall_segment(bm_tower, 2.70, 1.10, 4.00, -0.20, 2.79, 2.85, thickness=0.12) # Dintel
    add_wall_segment(bm_tower, 2.70, 1.10, 2.76, 1.04, 0.40, 2.85, thickness=0.12) # Jamba izq
    add_wall_segment(bm_tower, 3.94, -0.14, 4.00, -0.20, 0.40, 2.85, thickness=0.12) # Jamba der
    add_wall_segment(bm_tower, 3.32, 0.48, 3.38, 0.42, 0.40, 2.85, thickness=0.12) # Montante central
    # Vidrio Tintex y persianas
    add_wall_segment(bm_glass, 2.76, 1.04, 3.94, -0.14, 0.46, 2.79, thickness=0.02)
    add_wall_segment(bm_blind, 2.78, 1.02, 3.92, -0.12, 0.48, 2.77, thickness=0.02)
    
    # Asignar materiales
    bmesh.ops.recalc_face_normals(bm_tower, faces=bm_tower.faces)
    m_tower = bpy.data.meshes.new("Mesh_Guajardo_Torreon")
    bm_tower.to_mesh(m_tower)
    bm_tower.free()
    obj_tower = bpy.data.objects.new("Guajardo_Torreon_45", m_tower)
    col.objects.link(obj_tower)
    obj_tower.data.materials.append(mats["mosaico_guajardo"]) # 0
    obj_tower.data.materials.append(mats["coping_rocoso"])    # 1 (remate rocoso)
    obj_tower.data.materials.append(mats["muro"])             # 2 (muro/dintel blanco)
    obj_tower.data.materials.append(mats["zocalo"])           # 3 (zócalo basal)
    obj_tower.data.materials.append(mats["aluminio"])         # 4 (cancelería)
    
    for p in m_tower.polygons:
        c_z = sum(m_tower.vertices[v].co.z for v in p.vertices) / len(p.vertices)
        c_x = sum(m_tower.vertices[v].co.x for v in p.vertices) / len(p.vertices)
        c_y = sum(m_tower.vertices[v].co.y for v in p.vertices) / len(p.vertices)
        if c_z < 0.42:
            p.material_index = 3 # Zócalo basal
        elif c_z >= H_tower - 0.02:
            p.material_index = 1 # Remate rocoso desgastado
        elif c_z >= 2.84 and c_z <= 3.22:
            p.material_index = 2 # Dintel estucado blanco
        elif c_z < 2.85:
            p.material_index = 4 # Cancelería de aluminio
        elif c_x > 4.10 or c_y > 4.10:
            p.material_index = 2 # Retornos laterales estucados
        else:
            p.material_index = 0 # Trapecio de mosaico vítreo pizarra meteorizada'''

if old_guajardo in code:
    code = code.replace(old_guajardo, new_guajardo)
    print("Guajardo corner successfully updated!")
else:
    print("Could not find old_guajardo exactly!")

# 2. Update build_totem_rooftop_bbva (rotate 45 degrees to be parallel to Cárdenas)
old_totem = '''    # Caja de luz: panel superior azul cobalto 2009 (BBVA Bancomer)
    add_box(bm_blue, -1.80, 1.80, -0.16, 0.16, 10.65, 12.30)
    bmesh.ops.recalc_face_normals(bm_blue, faces=bm_blue.faces)
    m_b = bpy.data.meshes.new("Mesh_Totem_Azul")
    bm_blue.to_mesh(m_b)
    bm_blue.free()
    obj_blue = bpy.data.objects.new("BBVA_Totem_Panel_Azul", m_b)
    col.objects.link(obj_blue)
    obj_blue.location = (1.90, 1.90, 0.0)
    obj_blue.rotation_euler = (0.0, 0.0, math.radians(-45.0))
    obj_blue.data.materials.append(mats["fascia"])

    # Recuadro blanco BBVA 2009 centrado en la parte superior
    add_box(bm_white_sq, -0.70, 0.70, -0.17, 0.17, 11.50, 12.20)
    bmesh.ops.recalc_face_normals(bm_white_sq, faces=bm_white_sq.faces)
    m_wsq = bpy.data.meshes.new("Mesh_Totem_Recuadro_Blanco")
    bm_white_sq.to_mesh(m_wsq)
    bm_white_sq.free()
    obj_wsq = bpy.data.objects.new("BBVA_Totem_Recuadro_BBVA", m_wsq)
    col.objects.link(obj_wsq)
    obj_wsq.location = (1.90, 1.90, 0.0)
    obj_wsq.rotation_euler = (0.0, 0.0, math.radians(-45.0))
    obj_wsq.data.materials.append(mats["rotulo_blanco"])

    # Panel inferior blanco (Cajero Automático / RED)
    add_box(bm_white_panel, -1.80, 1.80, -0.16, 0.16, 9.50, 10.65)
    bmesh.ops.recalc_face_normals(bm_white_panel, faces=bm_white_panel.faces)
    m_w = bpy.data.meshes.new("Mesh_Totem_Blanco")
    bm_white_panel.to_mesh(m_w)
    bm_white_panel.free()
    obj_white = bpy.data.objects.new("BBVA_Totem_Panel_Blanco", m_w)
    col.objects.link(obj_white)
    obj_white.location = (1.90, 1.90, 0.0)
    obj_white.rotation_euler = (0.0, 0.0, math.radians(-45.0))
    obj_white.data.materials.append(mats["rotulo_blanco"])

    # Textos del espectacular 2009
    x_t = 1.90 - 0.185 * 0.7071
    y_t = 1.90 - 0.185 * 0.7071
    
    # 1. Letras azules 'BBVA' dentro del recuadro blanco
    f_b1 = bpy.data.curves.new(type="FONT", name="Font_T_BBVA")
    f_b1.body = "BBVA"
    f_b1.size = 0.40
    f_b1.extrude = 0.02
    f_b1.align_x = 'CENTER'
    o_b1 = bpy.data.objects.new("Totem_Txt_BBVA_Azul", f_b1)
    col.objects.link(o_b1)
    o_b1.location = (x_t - 0.015*0.7071, y_t - 0.015*0.7071, 11.65)
    o_b1.rotation_euler = (math.radians(90.0), 0.0, math.radians(-45.0))
    o_b1.data.materials.append(mats["bbva_azul"])

    # 2. Texto blanco 'Bancomer' debajo del recuadro
    f_b2 = bpy.data.curves.new(type="FONT", name="Font_T_Bancomer")
    f_b2.body = "Bancomer"
    f_b2.size = 0.36
    f_b2.extrude = 0.02
    f_b2.align_x = 'CENTER'
    o_b2 = bpy.data.objects.new("Totem_Txt_Bancomer_Blanco", f_b2)
    col.objects.link(o_b2)
    o_b2.location = (x_t, y_t, 10.90)
    o_b2.rotation_euler = (math.radians(90.0), 0.0, math.radians(-45.0))
    o_b2.data.materials.append(mats["rotulo_blanco"])

    # 3. Logotipo 'RED' a la izquierda del panel inferior
    # Desplazado a t = -1.0 m a lo largo de la tangente (0.7071, -0.7071)
    f_red = bpy.data.curves.new(type="FONT", name="Font_T_RED")
    f_red.body = "RED"
    f_red.size = 0.24
    f_red.extrude = 0.015
    f_red.align_x = 'CENTER'
    o_red = bpy.data.objects.new("Totem_Txt_RED", f_red)
    col.objects.link(o_red)
    o_red.location = (x_t - 0.85*0.7071, y_t + 0.85*0.7071, 10.00)
    o_red.rotation_euler = (math.radians(90.0), 0.0, math.radians(-45.0))
    o_red.data.materials.append(mats["red_logo"])

    # 4. Texto verde 'CAJERO AUTOMATICO' a la derecha
    f_b3 = bpy.data.curves.new(type="FONT", name="Font_T_ATM")
    f_b3.body = "CAJERO\\nAUTOMATICO"
    f_b3.size = 0.18
    f_b3.extrude = 0.015
    f_b3.align_x = 'CENTER'
    o_b3 = bpy.data.objects.new("Totem_Txt_ATM_Verde", f_b3)
    col.objects.link(o_b3)
    o_b3.location = (x_t + 0.50*0.7071, y_t - 0.50*0.7071, 10.20)
    o_b3.rotation_euler = (math.radians(90.0), 0.0, math.radians(-45.0))
    o_b3.data.materials.append(mats["cajero_verde"])'''

new_totem = '''    # Caja de luz: panel superior azul cobalto 2009 (rotado 45º para quedar paralelo a Cárdenas, Comentario 7)
    add_box(bm_blue, -1.80, 1.80, -0.16, 0.16, 10.65, 12.30)
    bmesh.ops.recalc_face_normals(bm_blue, faces=bm_blue.faces)
    m_b = bpy.data.meshes.new("Mesh_Totem_Azul")
    bm_blue.to_mesh(m_b)
    bm_blue.free()
    obj_blue = bpy.data.objects.new("BBVA_Totem_Panel_Azul", m_b)
    col.objects.link(obj_blue)
    obj_blue.location = (1.90, 1.90, 0.0)
    obj_blue.rotation_euler = (0.0, 0.0, math.radians(-90.0))
    obj_blue.data.materials.append(mats["fascia"])

    # Recuadro blanco BBVA 2009 centrado en la parte superior
    add_box(bm_white_sq, -0.70, 0.70, -0.17, 0.17, 11.50, 12.20)
    bmesh.ops.recalc_face_normals(bm_white_sq, faces=bm_white_sq.faces)
    m_wsq = bpy.data.meshes.new("Mesh_Totem_Recuadro_Blanco")
    bm_white_sq.to_mesh(m_wsq)
    bm_white_sq.free()
    obj_wsq = bpy.data.objects.new("BBVA_Totem_Recuadro_BBVA", m_wsq)
    col.objects.link(obj_wsq)
    obj_wsq.location = (1.90, 1.90, 0.0)
    obj_wsq.rotation_euler = (0.0, 0.0, math.radians(-90.0))
    obj_wsq.data.materials.append(mats["rotulo_blanco"])

    # Panel inferior blanco (Cajero Automático / RED)
    add_box(bm_white_panel, -1.80, 1.80, -0.16, 0.16, 9.50, 10.65)
    bmesh.ops.recalc_face_normals(bm_white_panel, faces=bm_white_panel.faces)
    m_w = bpy.data.meshes.new("Mesh_Totem_Blanco")
    bm_white_panel.to_mesh(m_w)
    bm_white_panel.free()
    obj_white = bpy.data.objects.new("BBVA_Totem_Panel_Blanco", m_w)
    col.objects.link(obj_white)
    obj_white.location = (1.90, 1.90, 0.0)
    obj_white.rotation_euler = (0.0, 0.0, math.radians(-90.0))
    obj_white.data.materials.append(mats["rotulo_blanco"])

    # Textos del espectacular 2009 (mirando hacia el poniente/Cárdenas, normal hacia -X)
    x_t = 1.90 - 0.18
    y_t = 1.90
    rot_totem_txt = (math.radians(90.0), 0.0, math.radians(-90.0))
    
    # 1. Letras azules 'BBVA' dentro del recuadro blanco
    f_b1 = bpy.data.curves.new(type="FONT", name="Font_T_BBVA")
    f_b1.body = "BBVA"
    f_b1.size = 0.40
    f_b1.extrude = 0.02
    f_b1.align_x = 'CENTER'
    o_b1 = bpy.data.objects.new("Totem_Txt_BBVA_Azul", f_b1)
    col.objects.link(o_b1)
    o_b1.location = (x_t - 0.015, y_t, 11.65)
    o_b1.rotation_euler = rot_totem_txt
    o_b1.data.materials.append(mats["bbva_azul"])

    # 2. Texto blanco 'Bancomer' debajo del recuadro
    f_b2 = bpy.data.curves.new(type="FONT", name="Font_T_Bancomer")
    f_b2.body = "Bancomer"
    f_b2.size = 0.36
    f_b2.extrude = 0.02
    f_b2.align_x = 'CENTER'
    o_b2 = bpy.data.objects.new("Totem_Txt_Bancomer_Blanco", f_b2)
    col.objects.link(o_b2)
    o_b2.location = (x_t, y_t, 10.90)
    o_b2.rotation_euler = rot_totem_txt
    o_b2.data.materials.append(mats["rotulo_blanco"])

    # 3. Logotipo 'RED' a la izquierda del panel inferior (mirando desde el poniente, izquierda es +Y)
    f_red = bpy.data.curves.new(type="FONT", name="Font_T_RED")
    f_red.body = "RED"
    f_red.size = 0.24
    f_red.extrude = 0.015
    f_red.align_x = 'CENTER'
    o_red = bpy.data.objects.new("Totem_Txt_RED", f_red)
    col.objects.link(o_red)
    o_red.location = (x_t, y_t + 0.85, 10.00)
    o_red.rotation_euler = rot_totem_txt
    o_red.data.materials.append(mats["red_logo"])

    # 4. Texto verde 'CAJERO AUTOMATICO' a la derecha (derecha es -Y)
    f_b3 = bpy.data.curves.new(type="FONT", name="Font_T_ATM")
    f_b3.body = "CAJERO\\nAUTOMATICO"
    f_b3.size = 0.18
    f_b3.extrude = 0.015
    f_b3.align_x = 'CENTER'
    o_b3 = bpy.data.objects.new("Totem_Txt_ATM_Verde", f_b3)
    col.objects.link(o_b3)
    o_b3.location = (x_t, y_t - 0.55, 10.20)
    o_b3.rotation_euler = rot_totem_txt
    o_b3.data.materials.append(mats["cajero_verde"])'''

if old_totem in code:
    code = code.replace(old_totem, new_totem)
    print("Totem successfully updated!")
else:
    print("Could not find old_totem exactly!")

# 3. Update build_south_facade_juarez: remove 21.80 duplicate
old_cols = "col_x = [4.20, 8.60, 13.00, 17.40, 21.80]"
new_cols = "col_x = [4.20, 8.60, 13.00, 17.40]"
if old_cols in code:
    code = code.replace(old_cols, new_cols)
    print("Juarez columns successfully updated (no duplicate 21.80)!")
else:
    print("Could not find old_cols!")

# 4. Update build_west_facade_cardenas: bays, cajero in Crujía 3, remove poster in Crujía 2, 2 bays between ATM and Dentista
old_west_loop = '''    for idx, (y1, y2) in enumerate(bays_y):
        w_f = 0.05
        # Planta Baja
        if idx == 3:
            # Crujía 4: PORTAL DE ACCESO A CAJERO AUTOMÁTICO (Ground Truth media_1789778253725)
            # Puerta acristalada en y = [17.60, 19.10]
            add_box(bm_alum, 0.04, 0.14, 17.60, 19.10, 0.40, 0.46)
            add_box(bm_alum, 0.04, 0.14, 17.60, 19.10, 2.70, 2.76)
            add_box(bm_alum, 0.04, 0.14, 17.60, 17.66, 0.40, 2.76)
            add_box(bm_alum, 0.04, 0.14, 19.04, 19.10, 0.40, 2.76)
            add_box(bm_glass, 0.08, 0.09, 17.66, 19.04, 0.46, 2.70)
            # Jaladera tubular de la puerta
            add_box(bm_alum, -0.02, 0.06, 18.90, 18.94, 1.00, 1.40)
            
            # Ventana lateral izquierda con persianas en y = [19.20, 21.00]
            add_box(bm_alum, 0.04, 0.12, 19.20, 21.00, 0.40, 0.45)
            add_box(bm_alum, 0.04, 0.12, 19.20, 21.00, 3.15, 3.20)
            add_box(bm_alum, 0.04, 0.12, 19.20, 19.25, 0.40, 3.20)
            add_box(bm_alum, 0.04, 0.12, 20.95, 21.00, 0.40, 3.20)
            step_4 = (21.00 - 19.20) / 2.0
            add_box(bm_alum, 0.04, 0.12, 19.20 + step_4 - 0.02, 19.20 + step_4 + 0.02, 0.40, 3.20)
            add_box(bm_glass, 0.075, 0.085, 19.25, 20.95, 0.45, 3.15)
            add_box(bm_blind, 0.135, 0.145, 19.25, 20.95, 0.45, 3.15)
            
        elif idx == 5:
            # Crujía 6: ACCESO DENTISTA (Ground Truth media_1789778345732)
            # Zaguán rehundido hacia el interior (X = 0.0 a 3.20, Y = [25.80, 28.20])
            # Escalera de 4 peldaños de concreto
            stair_w = (25.85, 28.15)
            # Escalón 1
            add_box(bm_dent_stair, 0.20, 3.20, stair_w[0], stair_w[1], 0.0, 0.18)
            # Escalón 2
            add_box(bm_dent_stair, 0.60, 3.20, stair_w[0], stair_w[1], 0.18, 0.36)
            # Escalón 3
            add_box(bm_dent_stair, 1.00, 3.20, stair_w[0], stair_w[1], 0.36, 0.54)
            # Escalón 4 / Rellano
            add_box(bm_dent_stair, 1.40, 3.20, stair_w[0], stair_w[1], 0.54, 0.72)
            
            # Muros interiores del zaguán
            add_box(bm_dent_stair, 0.0, 3.20, 25.75, 25.85, 0.0, 3.20) # Muro sur zaguán
            add_box(bm_dent_stair, 0.0, 3.20, 28.15, 28.25, 0.0, 3.20) # Muro norte zaguán
            add_box(bm_dent_stair, 0.0, 3.20, 25.75, 28.25, 3.20, 3.30) # Techo falso zaguán
            
            # Puerta acristalada interior al fondo del zaguán (X = 3.15, Y = [26.40, 27.80])
            add_box(bm_alum, 3.12, 3.18, 26.40, 27.80, 0.72, 2.72)
            add_box(bm_glass, 3.14, 3.16, 26.46, 27.74, 0.78, 2.66)
            
            # Ventanal lateral exterior a la derecha del acceso: Y in [28.25, 29.35]
            add_box(bm_alum, 0.04, 0.12, 28.25, 29.35, 0.40, 0.45)
            add_box(bm_alum, 0.04, 0.12, 28.25, 29.35, 3.15, 3.20)
            add_box(bm_alum, 0.04, 0.12, 28.25, 28.30, 0.40, 3.20)
            add_box(bm_alum, 0.04, 0.12, 29.30, 29.35, 0.40, 3.20)
            add_box(bm_glass, 0.075, 0.085, 28.30, 29.30, 0.45, 3.15)
            add_box(bm_blind, 0.135, 0.145, 28.30, 29.30, 0.45, 3.15)
            
        elif idx == 1:
            # Crujía 2: Banco con póster institucional Bancomer
            add_box(bm_alum, 0.04, 0.12, y1, y1 + w_f, 0.40, 3.20)
            add_box(bm_alum, 0.04, 0.12, y2 - w_f, y2, 0.40, 3.20)
            add_box(bm_alum, 0.04, 0.12, y1, y2, 0.40, 0.40 + w_f)
            add_box(bm_alum, 0.04, 0.12, y1, y2, 3.20 - w_f, 3.20)
            step = (y2 - y1) / 3.0
            add_box(bm_alum, 0.04, 0.12, y1 + step - 0.025, y1 + step + 0.025, 0.40, 3.20)
            add_box(bm_alum, 0.04, 0.12, y1 + 2*step - 0.025, y1 + 2*step + 0.025, 0.40, 3.20)
            add_box(bm_glass, 0.075, 0.085, y1 + w_f, y2 - w_f, 0.40 + w_f, 3.20 - w_f)
            add_box(bm_blind, 0.135, 0.145, y1 + w_f, y2 - w_f, 0.42, 3.18)
            # Marco de póster publicitario Bancomer en vidrio
            add_box(bm_dent_canopy, -0.06, 0.02, 10.20, 11.40, 1.20, 2.20)
        else:
            # Crujías 1, 3 y 5: Cristaleras estándar
            n_divs_pb = 2 if idx == 4 else 3
            add_box(bm_alum, 0.04, 0.12, y1, y1 + w_f, 0.40, 3.20)
            add_box(bm_alum, 0.04, 0.12, y2 - w_f, y2, 0.40, 3.20)
            add_box(bm_alum, 0.04, 0.12, y1, y2, 0.40, 0.40 + w_f)
            add_box(bm_alum, 0.04, 0.12, y1, y2, 3.20 - w_f, 3.20)
            step = (y2 - y1) / float(n_divs_pb)
            for d in range(1, n_divs_pb):
                mx_pb = y1 + d * step
                add_box(bm_alum, 0.04, 0.12, mx_pb - 0.025, mx_pb + 0.025, 0.40, 3.20)
            add_box(bm_glass, 0.075, 0.085, y1 + w_f, y2 - w_f, 0.40 + w_f, 3.20 - w_f)
            add_box(bm_blind, 0.135, 0.145, y1 + w_f, y2 - w_f, 0.42, 3.18)'''

new_west_loop = '''    for idx, (y1, y2) in enumerate(bays_y):
        w_f = 0.05
        # Planta Baja
        if idx == 2:
            # Crujía 3: PORTAL DE ACCESO A CAJERO AUTOMÁTICO (Ground Truth media_1789778253725)
            # "Estos elementos van 1 ventanal a la derecha. Entre el cajero y el dentista hay 2 ventanales. El cajero va en el lado izquierdo de su ventanal."
            # Puerta acristalada en el lado izquierdo (norte) del vano: y in [15.20, 16.60]
            add_box(bm_alum, 0.04, 0.14, 15.20, 16.60, 0.40, 0.46)
            add_box(bm_alum, 0.04, 0.14, 15.20, 16.60, 2.70, 2.76)
            add_box(bm_alum, 0.04, 0.14, 15.20, 15.26, 0.40, 2.76)
            add_box(bm_alum, 0.04, 0.14, 16.54, 16.60, 0.40, 2.76)
            add_box(bm_glass, 0.08, 0.09, 15.26, 16.54, 0.46, 2.70)
            # Jaladera tubular de la puerta
            add_box(bm_alum, -0.02, 0.06, 15.32, 15.36, 1.00, 1.40)
            
            # Ventana lateral con persianas en el resto del vano: y in [13.20, 15.10]
            add_box(bm_alum, 0.04, 0.12, 13.20, 15.10, 0.40, 0.45)
            add_box(bm_alum, 0.04, 0.12, 13.20, 15.10, 3.15, 3.20)
            add_box(bm_alum, 0.04, 0.12, 13.20, 13.25, 0.40, 3.20)
            add_box(bm_alum, 0.04, 0.12, 15.05, 15.10, 0.40, 3.20)
            add_box(bm_glass, 0.075, 0.085, 13.25, 15.05, 0.45, 3.15)
            add_box(bm_blind, 0.135, 0.145, 13.25, 15.05, 0.45, 3.15)
            
        elif idx == 5:
            # Crujía 6: ACCESO DENTISTA (Ground Truth media_1789778345732)
            # Zaguán rehundido hacia el interior (X = 0.0 a 3.20, Y = [25.80, 28.20])
            # Escalera de 4 peldaños de concreto
            stair_w = (25.85, 28.15)
            add_box(bm_dent_stair, 0.20, 3.20, stair_w[0], stair_w[1], 0.0, 0.18)
            add_box(bm_dent_stair, 0.60, 3.20, stair_w[0], stair_w[1], 0.18, 0.36)
            add_box(bm_dent_stair, 1.00, 3.20, stair_w[0], stair_w[1], 0.36, 0.54)
            add_box(bm_dent_stair, 1.40, 3.20, stair_w[0], stair_w[1], 0.54, 0.72)
            
            # Muros interiores del zaguán
            add_box(bm_dent_stair, 0.0, 3.20, 25.75, 25.85, 0.0, 3.20) # Muro sur zaguán
            add_box(bm_dent_stair, 0.0, 3.20, 28.15, 28.25, 0.0, 3.20) # Muro norte zaguán
            add_box(bm_dent_stair, 0.0, 3.20, 25.75, 28.25, 3.20, 3.30) # Techo falso zaguán
            
            # Puerta acristalada interior al fondo del zaguán (X = 3.15, Y = [26.40, 27.80])
            add_box(bm_alum, 3.12, 3.18, 26.40, 27.80, 0.72, 2.72)
            add_box(bm_glass, 3.14, 3.16, 26.46, 27.74, 0.78, 2.66)
            
            # Ventanal lateral exterior a la derecha del acceso: Y in [28.25, 29.35]
            add_box(bm_alum, 0.04, 0.12, 28.25, 29.35, 0.40, 0.45)
            add_box(bm_alum, 0.04, 0.12, 28.25, 29.35, 3.15, 3.20)
            add_box(bm_alum, 0.04, 0.12, 28.25, 28.30, 0.40, 3.20)
            add_box(bm_alum, 0.04, 0.12, 29.30, 29.35, 0.40, 3.20)
            add_box(bm_glass, 0.075, 0.085, 28.30, 29.30, 0.45, 3.15)
            add_box(bm_blind, 0.135, 0.145, 28.30, 29.30, 0.45, 3.15)
            
        else:
            # Crujías 1, 2, 4 y 5: Cristaleras estándar (se eliminó el recuadro blanco de Crujía 2 según Comentario 2)
            n_divs_pb = 2 if (idx == 3 or idx == 4) else 3
            add_box(bm_alum, 0.04, 0.12, y1, y1 + w_f, 0.40, 3.20)
            add_box(bm_alum, 0.04, 0.12, y2 - w_f, y2, 0.40, 3.20)
            add_box(bm_alum, 0.04, 0.12, y1, y2, 0.40, 0.40 + w_f)
            add_box(bm_alum, 0.04, 0.12, y1, y2, 3.20 - w_f, 3.20)
            step = (y2 - y1) / float(n_divs_pb)
            for d in range(1, n_divs_pb):
                mx_pb = y1 + d * step
                add_box(bm_alum, 0.04, 0.12, mx_pb - 0.025, mx_pb + 0.025, 0.40, 3.20)
            add_box(bm_glass, 0.075, 0.085, y1 + w_f, y2 - w_f, 0.40 + w_f, 3.20 - w_f)
            add_box(bm_blind, 0.135, 0.145, y1 + w_f, y2 - w_f, 0.42, 3.18)'''

if old_west_loop in code:
    code = code.replace(old_west_loop, new_west_loop)
    print("West facade loop successfully updated!")
else:
    print("Could not find old_west_loop!")

# 5. Update Cárdenas texts, fascias, ATM signbox, Dentista letters and hanging sign
old_cardenas_details = '''    # 5. Rótulos en vidrios de despachos (Ground Truth media_1789778253725)
    # Crujía 3: Despacho Contable Fiscal Lic. Ramón Quezada (Y in [13.20, 16.80])
    f_q2 = bpy.data.curves.new(type="FONT", name="Font_C_Quezada2")
    f_q2.body = "DESPACHO CONTABLE FISCAL\\nLOCAL Nº 4\\nLIC. RAMON QUEZADA LOPEZ\\nABOGADO"
    f_q2.size = 0.13
    f_q2.extrude = 0.008
    f_q2.align_x = 'CENTER'
    o_q2 = bpy.data.objects.new("Cardenas_Txt_Despacho_Contable", f_q2)
    col.objects.link(o_q2)
    o_q2.location = (0.055, 15.00, 6.35)
    o_q2.rotation_euler = (math.radians(90.0), 0.0, math.radians(-90.0))
    o_q2.data.materials.append(mats["rotulo_blanco"])
    text_objs.append(o_q2)

    # Crujía 4: Despacho Jurídico Quezada (Y in [17.40, 21.00])
    f_q1 = bpy.data.curves.new(type="FONT", name="Font_C_Quezada1")
    f_q1.body = "DESPACHO JURIDICO\\nQUEZADA Y ASOCIADOS\\nTel. 52-22"
    f_q1.size = 0.15
    f_q1.extrude = 0.008
    f_q1.align_x = 'CENTER'
    o_q1 = bpy.data.objects.new("Cardenas_Txt_Despacho_Juridico", f_q1)
    col.objects.link(o_q1)
    o_q1.location = (0.055, 19.20, 6.35)
    o_q1.rotation_euler = (math.radians(90.0), 0.0, math.radians(-90.0))
    o_q1.data.materials.append(mats["rotulo_blanco"])
    text_objs.append(o_q1)

    # Crujía 6: Rótulo ABIERTO en ventana PA Dentista
    f_ab = bpy.data.curves.new(type="FONT", name="Font_C_Abierto")
    f_ab.body = "ABIERTO"
    f_ab.size = 0.12
    f_ab.extrude = 0.005
    f_ab.align_x = 'CENTER'
    o_ab = bpy.data.objects.new("Cardenas_Txt_Abierto", f_ab)
    col.objects.link(o_ab)
    o_ab.location = (0.055, 27.60, 6.20)
    o_ab.rotation_euler = (math.radians(90.0), 0.0, math.radians(-90.0))
    o_ab.data.materials.append(mats["rojo_letras"])
    text_objs.append(o_ab)

    # 6. Fascias: Azul Cobalto para Banco BBVA (4 Crujías) + Plateada para Dentista/Despachos
    # Fascia Banco BBVA (Y = 4.20 a 21.00)
    bm_fascia_b = bmesh.new()
    add_box(bm_fascia_b, -0.14, 0.02, Y_start, 21.00, 3.20, 4.30)
    bmesh.ops.recalc_face_normals(bm_fascia_b, faces=bm_fascia_b.faces)
    m_fa_b = bpy.data.meshes.new("Mesh_Cardenas_Fascia_Banco")
    bm_fascia_b.to_mesh(m_fa_b)
    bm_fascia_b.free()
    obj_fascia_b = bpy.data.objects.new("Cardenas_Fascia_Azul_2009", m_fa_b)
    col.objects.link(obj_fascia_b)
    obj_fascia_b.data.materials.append(mats["fascia"])

    # Filetes blancos horizontales en fascia del banco
    bm_stripe_c = bmesh.new()
    add_box(bm_stripe_c, -0.148, -0.138, 4.60, 10.00, 3.72, 3.76)
    add_box(bm_stripe_c, -0.148, -0.138, 15.80, 20.80, 3.72, 3.76)
    bmesh.ops.recalc_face_normals(bm_stripe_c, faces=bm_stripe_c.faces)
    m_str_c = bpy.data.meshes.new("Mesh_Cardenas_Stripe")
    bm_stripe_c.to_mesh(m_str_c)
    bm_stripe_c.free()
    obj_stripe_c = bpy.data.objects.new("Cardenas_Fascia_Stripe", m_str_c)
    col.objects.link(obj_stripe_c)
    obj_stripe_c.data.materials.append(mats["rotulo_blanco"])

    # Recuadro blanco BBVA 2009 en Crujía 3 (Y = 14.40 a 15.70)
    bm_rec_c = bmesh.new()
    add_box(bm_rec_c, -0.148, -0.138, 14.40, 15.70, 3.35, 4.15)
    bmesh.ops.recalc_face_normals(bm_rec_c, faces=bm_rec_c.faces)
    m_rc_c = bpy.data.meshes.new("Mesh_Cardenas_Recuadro_BBVA")
    bm_rec_c.to_mesh(m_rc_c)
    bm_rec_c.free()
    obj_rec_c = bpy.data.objects.new("Cardenas_Recuadro_BBVA", m_rc_c)
    col.objects.link(obj_rec_c)
    obj_rec_c.data.materials.append(mats["rotulo_blanco"])

    # Letras BBVA azules (centradas en el recuadro blanco Y = 15.05)
    f_bbva_c = bpy.data.curves.new(type="FONT", name="Font_C_BBVA")
    f_bbva_c.body = "BBVA"
    f_bbva_c.size = 0.44
    f_bbva_c.extrude = 0.015
    f_bbva_c.align_x = 'CENTER'
    o_bbva_c = bpy.data.objects.new("Cardenas_Txt_BBVA", f_bbva_c)
    col.objects.link(o_bbva_c)
    o_bbva_c.location = (-0.155, 15.05, 3.55)
    o_bbva_c.rotation_euler = (math.radians(90.0), 0.0, math.radians(-90.0))
    o_bbva_c.data.materials.append(mats["bbva_azul"])
    text_objs.append(o_bbva_c)

    # Texto blanco 'Bancomer' en Crujía 2 (Y = 10.40 a 14.00)
    f_bancomer_c = bpy.data.curves.new(type="FONT", name="Font_C_Bancomer")
    f_bancomer_c.body = "Bancomer"
    f_bancomer_c.size = 0.48
    f_bancomer_c.extrude = 0.02
    o_bancomer_c = bpy.data.objects.new("Cardenas_Txt_Bancomer", f_bancomer_c)
    col.objects.link(o_bancomer_c)
    o_bancomer_c.location = (-0.155, 14.20, 3.52)
    o_bancomer_c.rotation_euler = (math.radians(90.0), 0.0, math.radians(-90.0))
    o_bancomer_c.data.materials.append(mats["rotulo_blanco"])
    text_objs.append(o_bancomer_c)

    # Fascia Metálica Plateada para Crujía 5 de Despachos (Y = 21.00 a 25.80)
    bm_fascia_s = bmesh.new()
    add_box(bm_fascia_s, -0.13, 0.02, 21.00, 25.80, 3.20, 4.30)
    bmesh.ops.recalc_face_normals(bm_fascia_s, faces=bm_fascia_s.faces)
    m_fa_s = bpy.data.meshes.new("Mesh_Cardenas_Fascia_Silver")
    bm_fascia_s.to_mesh(m_fa_s)
    bm_fascia_s.free()
    obj_fascia_s = bpy.data.objects.new("Cardenas_Fascia_Silver", m_fa_s)
    col.objects.link(obj_fascia_s)
    obj_fascia_s.data.materials.append(mats["fascia_silver"])

    # 7. Rótulo Luminoso de Acceso a Cajero Automático en Crujía 4 (Ground Truth media_1789778253725)
    # Caja azul sobre la puerta de cajero en Y = [17.65, 19.15]
    bm_atm = bmesh.new()
    add_box(bm_atm, -0.18, -0.02, 17.65, 19.15, 2.76, 3.16)
    # Cuadro rojo RED a la izquierda
    add_box(bm_atm, -0.19, -0.18, 17.70, 18.15, 2.80, 3.12)
    bmesh.ops.recalc_face_normals(bm_atm, faces=bm_atm.faces)
    m_ab = bpy.data.meshes.new("Mesh_ATM_Portal_Box")
    bm_atm.to_mesh(m_ab)
    bm_atm.free()
    obj_atm_box = bpy.data.objects.new("Cardenas_ATM_Portal_Box", m_ab)
    col.objects.link(obj_atm_box)
    obj_atm_box.data.materials.append(mats["atm_caja"])
    obj_atm_box.data.materials.append(mats["red_logo"])
    for p in m_ab.polygons:
        c_y = sum(m_ab.vertices[v].co.y for v in p.vertices) / len(p.vertices)
        if c_y < 18.20:
            p.material_index = 1
        else:
            p.material_index = 0

    f_atm_p = bpy.data.curves.new(type="FONT", name="Font_C_ATM_Portal")
    f_atm_p.body = "CAJERO\\nAUTOMATICO"
    f_atm_p.size = 0.11
    f_atm_p.extrude = 0.01
    f_atm_p.align_x = 'CENTER'
    o_atm_p = bpy.data.objects.new("Cardenas_ATM_Portal_Txt", f_atm_p)
    col.objects.link(o_atm_p)
    o_atm_p.location = (-0.20, 18.65, 2.85)
    o_atm_p.rotation_euler = (math.radians(90.0), 0.0, math.radians(-90.0))
    o_atm_p.data.materials.append(mats["rotulo_blanco"])
    text_objs.append(o_atm_p)

    f_red_p = bpy.data.curves.new(type="FONT", name="Font_C_RED")
    f_red_p.body = "RED"
    f_red_p.size = 0.12
    f_red_p.extrude = 0.01
    f_red_p.align_x = 'CENTER'
    o_red_p = bpy.data.objects.new("Cardenas_RED_Txt", f_red_p)
    col.objects.link(o_red_p)
    o_red_p.location = (-0.20, 17.92, 2.92)
    o_red_p.rotation_euler = (math.radians(90.0), 0.0, math.radians(-90.0))
    o_red_p.data.materials.append(mats["rotulo_blanco"])
    text_objs.append(o_red_p)

    # 8. MARQUESINA Y ELEMENTOS DENTISTA EN CRUJÍA 6 (Ground Truth media_1789778345732)
    # Marquesina volada azul oscuro
    # Sobresale 1.15 m hacia la banqueta (X de -1.15 a 0.05, Y de 25.75 a 28.25, Z de 3.05 a 3.45)
    add_box(bm_dent_canopy, -1.15, 0.05, 25.75, 28.25, 3.05, 3.45)
    
    # Rótulo colgante bajo la marquesina (panel blanco en X = -0.55, Y in [25.85, 28.15], Z in [2.40, 2.95])
    add_box(bm_dent_canopy, -0.57, -0.53, 25.85, 28.15, 2.40, 2.95)
    
    # Foco / Cámara de seguridad sobre esquina de marquesina
    add_box(bm_dent_canopy, -0.15, 0.05, 28.15, 28.35, 3.45, 3.75) # Caja
    add_box(bm_dent_canopy, -0.25, -0.10, 28.20, 28.30, 3.55, 3.65) # Lente

    bmesh.ops.recalc_face_normals(bm_dent_canopy, faces=bm_dent_canopy.faces)
    m_dcan = bpy.data.meshes.new("Mesh_Dentista_Canopy")
    bm_dent_canopy.to_mesh(m_dcan)
    bm_dent_canopy.free()
    obj_canopy = bpy.data.objects.new("Dentista_Marquesina_Volada", m_dcan)
    col.objects.link(obj_canopy)
    obj_canopy.data.materials.append(mats["letrero_dentista"])
    obj_canopy.data.materials.append(mats["rotulo_blanco"])
    obj_canopy.data.materials.append(mats["aluminio"])
    for p in m_dcan.polygons:
        c_x = sum(m_dcan.vertices[v].co.x for v in p.vertices) / len(p.vertices)
        c_z = sum(m_dcan.vertices[v].co.z for v in p.vertices) / len(p.vertices)
        if c_z < 3.00:
            p.material_index = 1 # Panel colgante blanco
        elif c_x > -0.20 and c_z > 3.45:
            p.material_index = 2 # Foco seguridad
        else:
            p.material_index = 0 # Marquesina azul marino

    # Letras 3D DENTISTA en el frente de la marquesina (Ground Truth media_1789778345732)
    f_d3d = bpy.data.curves.new(type="FONT", name="Font_C_Dentista_3D")
    f_d3d.body = "DENTISTA"
    f_d3d.size = 0.32
    f_d3d.extrude = 0.03
    f_d3d.align_x = 'CENTER'
    o_d3d = bpy.data.objects.new("Dentista_Txt_3D_Oro", f_d3d)
    col.objects.link(o_d3d)
    o_d3d.location = (-1.16, 27.00, 3.12)
    o_d3d.rotation_euler = (math.radians(90.0), 0.0, math.radians(-90.0))
    o_d3d.data.materials.append(mats["oro_letras"])
    text_objs.append(o_d3d)

    # Textos del rótulo colgante Dr. Álvarez
    h_labels = [
        ("Dr. Eduardo R. Álvarez Olague", 0.07, 2.82, mats["rojo_letras"]),
        ("DENTISTA", 0.10, 2.70, mats["letrero_dentista"]),
        ("LOCAL - 1    RX   Tel: 654-11-87", 0.06, 2.58, mats["zocalo"]),
        ("SE ACEPTAN ASEGURANZAS U.S.A.", 0.055, 2.48, mats["zocalo"])
    ]
    for text_line, sz, z_pos, mat_t in h_labels:
        f_lbl = bpy.data.curves.new(type="FONT", name=f"Font_C_H_{text_line[:6]}")
        f_lbl.body = text_line
        f_lbl.size = sz
        f_lbl.extrude = 0.005
        f_lbl.align_x = 'CENTER'
        o_lbl = bpy.data.objects.new(f"Dentista_Txt_{text_line[:6]}", f_lbl)
        col.objects.link(o_lbl)
        o_lbl.location = (-0.58, 27.00, z_pos)
        o_lbl.rotation_euler = (math.radians(90.0), 0.0, math.radians(-90.0))
        o_lbl.data.materials.append(mat_t)
        text_objs.append(o_lbl)'''

new_cardenas_details = '''    # 5. Rótulos en vidrios de despachos (Ground Truth media_1789778253725)
    # Crujía 2: Despacho Contable Fiscal Lic. Ramón Quezada (Y in [9.00, 12.60])
    f_q2 = bpy.data.curves.new(type="FONT", name="Font_C_Quezada2")
    f_q2.body = "DESPACHO CONTABLE FISCAL\\nLOCAL Nº 4\\nLIC. RAMON QUEZADA LOPEZ\\nABOGADO"
    f_q2.size = 0.13
    f_q2.extrude = 0.008
    f_q2.align_x = 'CENTER'
    o_q2 = bpy.data.objects.new("Cardenas_Txt_Despacho_Contable", f_q2)
    col.objects.link(o_q2)
    o_q2.location = (0.055, 10.80, 6.35)
    o_q2.rotation_euler = (math.radians(90.0), 0.0, math.radians(-90.0))
    o_q2.data.materials.append(mats["rotulo_blanco"])
    text_objs.append(o_q2)

    # Crujía 3: Despacho Jurídico Quezada (Y in [13.20, 16.80], sobre el cajero automático)
    f_q1 = bpy.data.curves.new(type="FONT", name="Font_C_Quezada1")
    f_q1.body = "DESPACHO JURIDICO\\nQUEZADA Y ASOCIADOS\\nTel. 52-22"
    f_q1.size = 0.15
    f_q1.extrude = 0.008
    f_q1.align_x = 'CENTER'
    o_q1 = bpy.data.objects.new("Cardenas_Txt_Despacho_Juridico", f_q1)
    col.objects.link(o_q1)
    o_q1.location = (0.055, 15.00, 6.35)
    o_q1.rotation_euler = (math.radians(90.0), 0.0, math.radians(-90.0))
    o_q1.data.materials.append(mats["rotulo_blanco"])
    text_objs.append(o_q1)

    # Crujía 6: Rótulo ABIERTO en ventana PA Dentista
    f_ab = bpy.data.curves.new(type="FONT", name="Font_C_Abierto")
    f_ab.body = "ABIERTO"
    f_ab.size = 0.12
    f_ab.extrude = 0.005
    f_ab.align_x = 'CENTER'
    o_ab = bpy.data.objects.new("Cardenas_Txt_Abierto", f_ab)
    col.objects.link(o_ab)
    o_ab.location = (0.055, 27.60, 6.20)
    o_ab.rotation_euler = (math.radians(90.0), 0.0, math.radians(-90.0))
    o_ab.data.materials.append(mats["rojo_letras"])
    text_objs.append(o_ab)

    # 6. Fascias: Azul Cobalto para Banco BBVA (Crujías 1 a 3, Y = 4.20 a 17.40) + Plateada para Crujías 4 y 5 (Y = 17.40 a 25.80)
    # Fascia Banco BBVA (Y = 4.20 a 17.40)
    bm_fascia_b = bmesh.new()
    add_box(bm_fascia_b, -0.14, 0.02, Y_start, 17.40, 3.20, 4.30)
    # Área azul sobre la fachada misma en Crujía 6 arriba del alero (Comentario 5: "DENTISTA va sobre la fachada del edificio mismo, arriba de donde empieza este ala. Esa área va del mismo azul.")
    add_box(bm_fascia_b, -0.14, 0.02, 25.75, 28.25, 3.25, 4.30)
    bmesh.ops.recalc_face_normals(bm_fascia_b, faces=bm_fascia_b.faces)
    m_fa_b = bpy.data.meshes.new("Mesh_Cardenas_Fascia_Banco")
    bm_fascia_b.to_mesh(m_fa_b)
    bm_fascia_b.free()
    obj_fascia_b = bpy.data.objects.new("Cardenas_Fascia_Azul_2009", m_fa_b)
    col.objects.link(obj_fascia_b)
    obj_fascia_b.data.materials.append(mats["fascia"])

    # Filetes blancos horizontales en fascia del banco
    bm_stripe_c = bmesh.new()
    add_box(bm_stripe_c, -0.148, -0.138, 4.60, 9.20, 3.72, 3.76)
    add_box(bm_stripe_c, -0.148, -0.138, 13.80, 17.20, 3.72, 3.76)
    bmesh.ops.recalc_face_normals(bm_stripe_c, faces=bm_stripe_c.faces)
    m_str_c = bpy.data.meshes.new("Mesh_Cardenas_Stripe")
    bm_stripe_c.to_mesh(m_str_c)
    bm_stripe_c.free()
    obj_stripe_c = bpy.data.objects.new("Cardenas_Fascia_Stripe", m_str_c)
    col.objects.link(obj_stripe_c)
    obj_stripe_c.data.materials.append(mats["rotulo_blanco"])

    # Recuadro blanco BBVA 2009 entre Crujías 2 y 3 (Y = 12.00 a 13.30)
    bm_rec_c = bmesh.new()
    add_box(bm_rec_c, -0.148, -0.138, 12.00, 13.30, 3.35, 4.15)
    bmesh.ops.recalc_face_normals(bm_rec_c, faces=bm_rec_c.faces)
    m_rc_c = bpy.data.meshes.new("Mesh_Cardenas_Recuadro_BBVA")
    bm_rec_c.to_mesh(m_rc_c)
    bm_rec_c.free()
    obj_rec_c = bpy.data.objects.new("Cardenas_Recuadro_BBVA", m_rc_c)
    col.objects.link(obj_rec_c)
    obj_rec_c.data.materials.append(mats["rotulo_blanco"])

    # Letras BBVA azules (centradas en el recuadro blanco Y = 12.65)
    f_bbva_c = bpy.data.curves.new(type="FONT", name="Font_C_BBVA")
    f_bbva_c.body = "BBVA"
    f_bbva_c.size = 0.44
    f_bbva_c.extrude = 0.015
    f_bbva_c.align_x = 'CENTER'
    o_bbva_c = bpy.data.objects.new("Cardenas_Txt_BBVA", f_bbva_c)
    col.objects.link(o_bbva_c)
    o_bbva_c.location = (-0.155, 12.65, 3.55)
    o_bbva_c.rotation_euler = (math.radians(90.0), 0.0, math.radians(-90.0))
    o_bbva_c.data.materials.append(mats["bbva_azul"])
    text_objs.append(o_bbva_c)

    # Texto blanco 'Bancomer' en Crujía 2 (Y = 10.40)
    f_bancomer_c = bpy.data.curves.new(type="FONT", name="Font_C_Bancomer")
    f_bancomer_c.body = "Bancomer"
    f_bancomer_c.size = 0.48
    f_bancomer_c.extrude = 0.02
    o_bancomer_c = bpy.data.objects.new("Cardenas_Txt_Bancomer", f_bancomer_c)
    col.objects.link(o_bancomer_c)
    o_bancomer_c.location = (-0.155, 10.40, 3.52)
    o_bancomer_c.rotation_euler = (math.radians(90.0), 0.0, math.radians(-90.0))
    o_bancomer_c.data.materials.append(mats["rotulo_blanco"])
    text_objs.append(o_bancomer_c)

    # Fascia Metálica Plateada para Crujías 4 y 5 de Despachos (Y = 17.40 a 25.80, 2 ventanales continuos)
    bm_fascia_s = bmesh.new()
    add_box(bm_fascia_s, -0.13, 0.02, 17.40, 25.80, 3.20, 4.30)
    bmesh.ops.recalc_face_normals(bm_fascia_s, faces=bm_fascia_s.faces)
    m_fa_s = bpy.data.meshes.new("Mesh_Cardenas_Fascia_Silver")
    bm_fascia_s.to_mesh(m_fa_s)
    bm_fascia_s.free()
    obj_fascia_s = bpy.data.objects.new("Cardenas_Fascia_Silver", m_fa_s)
    col.objects.link(obj_fascia_s)
    obj_fascia_s.data.materials.append(mats["fascia_silver"])

    # 7. Rótulo Luminoso de Acceso a Cajero Automático en Crujía 3 (lado izquierdo, Y = [15.20, 16.60])
    bm_atm = bmesh.new()
    add_box(bm_atm, -0.18, -0.02, 15.20, 16.60, 2.76, 3.16)
    # Cuadro rojo RED a la izquierda (en vista frontal desde el poniente, izquierda es +Y)
    add_box(bm_atm, -0.19, -0.18, 16.10, 16.55, 2.80, 3.12)
    bmesh.ops.recalc_face_normals(bm_atm, faces=bm_atm.faces)
    m_ab = bpy.data.meshes.new("Mesh_ATM_Portal_Box")
    bm_atm.to_mesh(m_ab)
    bm_atm.free()
    obj_atm_box = bpy.data.objects.new("Cardenas_ATM_Portal_Box", m_ab)
    col.objects.link(obj_atm_box)
    obj_atm_box.data.materials.append(mats["atm_caja"])
    obj_atm_box.data.materials.append(mats["red_logo"])
    for p in m_ab.polygons:
        c_y = sum(m_ab.vertices[v].co.y for v in p.vertices) / len(p.vertices)
        if c_y > 16.05:
            p.material_index = 1 # Cuadro rojo RED
        else:
            p.material_index = 0 # Caja azul marino

    f_atm_p = bpy.data.curves.new(type="FONT", name="Font_C_ATM_Portal")
    f_atm_p.body = "CAJERO\\nAUTOMATICO"
    f_atm_p.size = 0.11
    f_atm_p.extrude = 0.01
    f_atm_p.align_x = 'CENTER'
    o_atm_p = bpy.data.objects.new("Cardenas_ATM_Portal_Txt", f_atm_p)
    col.objects.link(o_atm_p)
    o_atm_p.location = (-0.20, 15.65, 2.85)
    o_atm_p.rotation_euler = (math.radians(90.0), 0.0, math.radians(-90.0))
    o_atm_p.data.materials.append(mats["rotulo_blanco"])
    text_objs.append(o_atm_p)

    f_red_p = bpy.data.curves.new(type="FONT", name="Font_C_RED")
    f_red_p.body = "RED"
    f_red_p.size = 0.12
    f_red_p.extrude = 0.01
    f_red_p.align_x = 'CENTER'
    o_red_p = bpy.data.objects.new("Cardenas_RED_Txt", f_red_p)
    col.objects.link(o_red_p)
    o_red_p.location = (-0.20, 16.32, 2.92)
    o_red_p.rotation_euler = (math.radians(90.0), 0.0, math.radians(-90.0))
    o_red_p.data.materials.append(mats["rotulo_blanco"])
    text_objs.append(o_red_p)

    # 8. MARQUESINA Y ELEMENTOS DENTISTA EN CRUJÍA 6 (Ground Truth media_1789778345732)
    # Alero volado (tejadillo shelf horizontal saliente 1.15 m sobre la banqueta)
    # X de -1.15 a 0.05, Y de 25.75 a 28.25, Z de 3.05 a 3.25
    add_box(bm_dent_canopy, -1.15, 0.05, 25.75, 28.25, 3.05, 3.25)
    
    # Rótulo colgante a 90º bajo la marquesina (Comentario 6: "El letrero con los datos va en 90º a la fachada, como un colgante. Esto era para que los peatones leyeran.")
    # Se sitúa perpendicular a la fachada en Y = 26.05, extendiéndose desde la fachada (X = -0.05) hacia afuera (X = -0.95), Z in [2.38, 2.98]
    add_box(bm_dent_canopy, -0.95, -0.05, 26.03, 26.07, 2.38, 2.98)
    
    # Foco / Cámara de seguridad sobre esquina de marquesina
    add_box(bm_dent_canopy, -0.15, 0.05, 28.15, 28.35, 3.25, 3.55)
    add_box(bm_dent_canopy, -0.25, -0.10, 28.20, 28.30, 3.35, 3.45)

    bmesh.ops.recalc_face_normals(bm_dent_canopy, faces=bm_dent_canopy.faces)
    m_dcan = bpy.data.meshes.new("Mesh_Dentista_Canopy")
    bm_dent_canopy.to_mesh(m_dcan)
    bm_dent_canopy.free()
    obj_canopy = bpy.data.objects.new("Dentista_Marquesina_Volada", m_dcan)
    col.objects.link(obj_canopy)
    obj_canopy.data.materials.append(mats["letrero_dentista"])
    obj_canopy.data.materials.append(mats["rotulo_blanco"])
    obj_canopy.data.materials.append(mats["aluminio"])
    for p in m_dcan.polygons:
        c_x = sum(m_dcan.vertices[v].co.x for v in p.vertices) / len(p.vertices)
        c_z = sum(m_dcan.vertices[v].co.z for v in p.vertices) / len(p.vertices)
        if c_z < 3.00:
            p.material_index = 1 # Rótulo colgante blanco a 90º
        elif c_x > -0.20 and c_z > 3.25:
            p.material_index = 2 # Foco seguridad
        else:
            p.material_index = 0 # Alero azul marino

    # Comentario 5: "DENTISTA va sobre la fachada del edificio mismo, o sea, arriba de donde empieza este ala. Esa área va del mismo azul."
    # Letras 3D DENTISTA en oro montadas sobre la pared de fachada azul en X = -0.16, centradas en Y = 27.00, Z = 3.75
    f_d3d = bpy.data.curves.new(type="FONT", name="Font_C_Dentista_3D")
    f_d3d.body = "DENTISTA"
    f_d3d.size = 0.38
    f_d3d.extrude = 0.035
    f_d3d.align_x = 'CENTER'
    o_d3d = bpy.data.objects.new("Dentista_Txt_3D_Oro", f_d3d)
    col.objects.link(o_d3d)
    o_d3d.location = (-0.16, 27.00, 3.65)
    o_d3d.rotation_euler = (math.radians(90.0), 0.0, math.radians(-90.0))
    o_d3d.data.materials.append(mats["oro_letras"])
    text_objs.append(o_d3d)

    # Textos del rótulo colgante a 90º (Comentarios 3 y 4: "Ocampo", "Es 654-11-57", orientados hacia el sur en Y = 26.01)
    rot_hang = (math.radians(90.0), 0.0, 0.0) # Cara frontal del colgante mirando hacia -Y (hacia los peatones)
    y_hang = 26.015
    h_labels = [
        ("Dr. Eduardo R. Álvarez Ocampo", 0.045, 2.85, mats["rojo_letras"]),
        ("DENTISTA", 0.075, 2.73, mats["letrero_dentista"]),
        ("LOCAL - 1    RX   Tel: 654-11-57", 0.040, 2.62, mats["zocalo"]),
        ("SE ACEPTAN ASEGURANZAS U.S.A.", 0.038, 2.53, mats["zocalo"]),
        ("ATENCION ESPECIAL A NIÑOS - ORTODONCIA", 0.032, 2.45, mats["zocalo"])
    ]
    for text_line, sz, z_pos, mat_t in h_labels:
        f_lbl = bpy.data.curves.new(type="FONT", name=f"Font_C_H_{text_line[:6]}")
        f_lbl.body = text_line
        f_lbl.size = sz
        f_lbl.extrude = 0.005
        f_lbl.align_x = 'CENTER'
        o_lbl = bpy.data.objects.new(f"Dentista_Txt_{text_line[:6]}", f_lbl)
        col.objects.link(o_lbl)
        o_lbl.location = (-0.50, y_hang, z_pos)
        o_lbl.rotation_euler = rot_hang
        o_lbl.data.materials.append(mat_t)
        text_objs.append(o_lbl)'''

if old_cardenas_details in code:
    code = code.replace(old_cardenas_details, new_cardenas_details)
    print("Cárdenas details successfully updated!")
else:
    print("Could not find old_cardenas_details!")

# 6. Update build_east_and_rear_parking_facade: eliminate coplanar overlap at Y in [0.0, 0.40]
old_east_start = '''    # 1. Muro Este principal del cuerpo bancario (Z = 0.0 a 7.10, Y = 0.0 a 16.0)
    add_box(bm_east, X_east - 0.40, X_east, 0.0, 16.0, 0.0, 0.40) # Zócalo
    add_box(bm_east, X_east - 0.40, X_east, 0.0, 16.0, 3.20, 5.10) # Faja intermedia
    add_box(bm_east, X_east - 0.40, X_east, 0.0, 16.0, 6.75, H_wall) # Remate'''

new_east_start = '''    # 1. Muro Este principal del cuerpo bancario (Z = 0.0 a 7.10, Y = 0.40 a 16.0 para no solapar con el machón sur)
    add_box(bm_east, X_east - 0.40, X_east, 0.40, 16.0, 0.0, 0.40) # Zócalo
    add_box(bm_east, X_east - 0.40, X_east, 0.40, 16.0, 3.20, 5.10) # Faja intermedia
    add_box(bm_east, X_east - 0.40, X_east, 0.40, 16.0, 6.75, H_wall) # Remate'''

if old_east_start in code:
    code = code.replace(old_east_start, new_east_start)
    print("East start successfully updated!")
else:
    print("Could not find old_east_start!")

# Also fix the ground and upper floor machones that started at 0.0 in East
code = code.replace("add_box(bm_east, X_east - 0.40, X_east, 0.0, 0.80, 5.10, 6.75)",
                    "add_box(bm_east, X_east - 0.40, X_east, 0.40, 0.80, 5.10, 6.75)")
code = code.replace("add_box(bm_east, X_east - 0.40, X_east, 0.0, 0.80, 0.40, 3.20)",
                    "add_box(bm_east, X_east - 0.40, X_east, 0.40, 0.80, 0.40, 3.20)")

# 7. Update Cam_Dentista_Closeup to view the 90º hanging sign and the facade letters clearly
old_dent_cam = '''    # 6. Cámara 'Dentista_Closeup': Acercamiento a nivel de calle al acceso de DENTISTA
    c6_data = bpy.data.cameras.new("Cam_Dentista_Closeup")
    c6_data.lens = 32
    c6 = bpy.data.objects.new("Cam_Dentista_Closeup", c6_data)
    col.objects.link(c6)
    loc6 = Vector((-6.80, 27.20, 2.20))
    tgt6 = Vector((-0.20, 27.20, 3.10))
    dir6 = tgt6 - loc6
    c6.location = loc6
    c6.rotation_euler = dir6.to_track_quat('-Z', 'Y').to_euler()
    cams["dentista_closeup"] = c6'''

new_dent_cam = '''    # 6. Cámara 'Dentista_Closeup': Acercamiento en perspectiva angular capturando el letrero a 90º y las letras DENTISTA en fachada
    c6_data = bpy.data.cameras.new("Cam_Dentista_Closeup")
    c6_data.lens = 30
    c6 = bpy.data.objects.new("Cam_Dentista_Closeup", c6_data)
    col.objects.link(c6)
    loc6 = Vector((-5.60, 23.40, 2.15)) # Vista desde el sur hacia el norte-noreste como en media_1789778345732
    tgt6 = Vector((-0.35, 26.85, 2.95))
    dir6 = tgt6 - loc6
    c6.location = loc6
    c6.rotation_euler = dir6.to_track_quat('-Z', 'Y').to_euler()
    cams["dentista_closeup"] = c6'''

if old_dent_cam in code:
    code = code.replace(old_dent_cam, new_dent_cam)
    print("Dentista camera successfully updated!")
else:
    print("Could not find old_dent_cam!")

with open("scripts/generate_bbva_tecate.py", "w", encoding="utf-8") as f:
    f.write(code)

print("Saved updated scripts/generate_bbva_tecate.py successfully!")
