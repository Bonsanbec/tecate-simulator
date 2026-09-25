import re

target_path = "scripts/generate_cardenas_25.py"
with open(target_path, "r", encoding="utf-8") as f:
    code = f.read()

# 1. Update build_south_hidalgo_facade: seal PA pier [2.20, 2.60] and extend roof eave
old_south_pier = """    # 2. PLANTA ALTA: 2 GRANDES VENTANALES EN ARCO (SEGURIDAD COMERCIAL TECATE)
    add_box(bm_muro_s, 2.20, 11.20, total_y - 0.15, total_y + 0.15, 3.65, 4.30)
    add_box(bm_muro_s, 2.20, 11.20, total_y - 0.15, total_y + 0.15, 6.10, 6.45)
    add_box(bm_muro_s, 5.80, 6.40, total_y - 0.15, total_y + 0.15, 4.30, 6.10)
    add_box(bm_muro_s, 9.60, 11.20, total_y - 0.15, total_y + 0.15, 4.30, 6.10)"""

new_south_pier = """    # 2. PLANTA ALTA: 2 GRANDES VENTANALES EN ARCO (SEGURIDAD COMERCIAL TECATE)
    add_box(bm_muro_s, 2.20, 11.20, total_y - 0.15, total_y + 0.15, 3.65, 4.30)
    add_box(bm_muro_s, 2.20, 11.20, total_y - 0.15, total_y + 0.15, 6.10, 6.45)
    # Machones macizos que sellan por completo los laterales de las ventanas en PA
    add_box(bm_muro_s, 2.20, 2.60, total_y - 0.15, total_y + 0.15, 4.30, 6.10) # Machón oriente sellado
    add_box(bm_muro_s, 5.80, 6.40, total_y - 0.15, total_y + 0.15, 4.30, 6.10) # Machón central
    add_box(bm_muro_s, 9.60, 11.20, total_y - 0.15, total_y + 0.15, 4.30, 6.10) # Machón poniente"""

assert old_south_pier in code, "old_south_pier not found"
code = code.replace(old_south_pier, new_south_pier, 1)

# 2. Update build_la_parrilla_complete: fully enclose volume
pattern_parrilla = re.compile(r'def build_la_parrilla_complete\(mats, col\):.*?def build_parking_and_grounds', re.DOTALL)

new_parrilla_code = """def build_la_parrilla_complete(mats, col):
    \"\"\"
    Construye La Parrilla como estructura edificada continua y hermética que envuelve el estacionamiento:
      - CERO ENTRADAS HUECAS: Cerramiento perimetral macizo completo en Este (hasta Y=32), Sur (Y=32),
        Oeste (X=68) y Fachada Norte hacia el patio (Y=18).
      - Frente Norte sobre Callejón Libertad con espadaña misional, porche ochavado y zaguán.
      - Ala Este con 3 ventanas rústicas, rejas coloniales, tejadillos y cubierta hermética.
      - Gran Cuerpo Sur de 2 niveles completamente cerrado con ventanas, rejas, puertas y losas de azotea continuas.
      - Chimenea anclada sólidamente en azotea.
    \"\"\"
    objects = []
    rot_north = (math.radians(90.0), 0.0, 0.0)
    rot_west_wall = (math.radians(90.0), 0.0, math.radians(90.0))

    bm_muro = bmesh.new()
    bm_espadaña = bmesh.new()
    bm_vigas = bmesh.new()
    bm_ventanas = bmesh.new()
    bm_rejas = bmesh.new()
    bm_salones = bmesh.new()
    bm_tejas_p = bmesh.new()

    # Zócalo basal enterrado de La Parrilla (-1.50 a 0.00 m)
    add_box(bm_muro, 17.50, 68.15, -0.20, 32.20, -1.50, 0.00)

    # -----------------------------------------------------------------------
    # 1. CUERPO NORTE (FRENTE A CALLEJÓN LIBERTAD, Y = 0.00 m)
    # -----------------------------------------------------------------------
    # Marquesina rústica izquierda (X in [17.50, 24.00 m])
    add_box(bm_muro, 17.50, 18.20, -0.15, 0.20, 0.00, 3.80)
    add_box(bm_muro, 23.00, 24.00, -0.15, 0.20, 0.00, 3.80)
    add_box(bm_muro, 18.20, 23.00, -0.15, 0.20, 0.00, 0.90)
    add_box(bm_muro, 18.20, 23.00, -0.15, 0.20, 2.60, 3.80)

    add_box(bm_ventanas, 18.20, 23.00, -0.12, 0.12, 0.90, 2.60)
    for i in range(int((23.00 - 18.20) / 0.18)):
        xb = 18.30 + i * 0.18
        add_box(bm_rejas, xb - 0.015, xb + 0.015, -0.22, -0.14, 0.85, 2.65)

    for i in range(9):
        xb = 17.60 + i * 0.75
        add_box(bm_vigas, xb - 0.08, xb + 0.08, -0.75, 0.40, 3.45, 3.60)

    add_box(bm_rejas, 17.80, 23.40, -0.10, 0.00, 4.00, 5.20)

    # Cuerpo con Espadaña Misional Ondulada (X in [24.00, 32.50 m])
    add_box(bm_muro, 24.00, 30.50, -0.15, 0.20, 0.00, 3.80)
    add_box(bm_espadaña, 24.00, 31.00, -0.15, 0.15, 3.80, 4.25)
    add_box(bm_espadaña, 25.20, 29.80, -0.15, 0.15, 4.25, 4.85)
    add_box(bm_espadaña, 26.20, 28.80, -0.15, 0.15, 4.85, 5.20)

    add_box(bm_ventanas, 24.80, 27.50, -0.14, 0.14, 1.10, 2.40)
    add_box(bm_rejas, 24.75, 27.55, -0.26, -0.12, 1.05, 2.45)

    # Porche en esquina ochavada con zaguán diáfano de doble arco (X in [30.50, 32.50 m], Y in [0.00, 2.20 m])
    add_box(bm_muro, 30.50, 32.30, -0.15, 0.15, 2.60, 3.80)
    add_box(bm_muro, 30.30, 30.60, -0.15, 0.15, 0.00, 2.60)
    add_box(bm_muro, 32.20, 32.50, -0.15, 0.15, 0.00, 2.60)
    add_box(bm_muro, 32.35, 32.55, 0.00, 2.20, 2.60, 3.80)
    add_box(bm_muro, 32.35, 32.55, 2.00, 2.30, 0.00, 2.60)

    add_box(bm_muro, 30.50, 32.40, 0.00, 2.20, 0.00, 0.06)
    for ib in range(3):
        yb = 0.55 + ib * 0.60
        add_box(bm_vigas, 30.55, 32.35, yb - 0.06, yb + 0.06, 2.65, 2.78)

    add_box(bm_muro, 30.50, 32.30, 2.15, 2.35, 2.40, 3.80)
    add_box(bm_ventanas, 30.75, 32.05, 2.18, 2.28, 0.00, 2.35)

    # -----------------------------------------------------------------------
    # 2. ALA ESTE DEL ESTACIONAMIENTO (X = 32.50 m, CONTINUA DE Y = 0 A 32 m)
    # -----------------------------------------------------------------------
    # Muro perimetral oriental continuo de piso a techo (SELLADO COMPLETO HASTA Y = 32.00 m)
    add_box(bm_muro, 32.35, 32.65, 2.20, 32.00, 0.00, 4.20)
    add_box(bm_muro, 32.35, 32.65, 18.00, 32.00, 4.20, 6.90)

    # Losa maciza de azotea del ala este
    add_box(bm_muro, 28.00, 32.65, 0.00, 18.00, 3.70, 3.85)
    add_box(bm_muro, 32.35, 32.65, 0.00, 18.00, 3.85, 4.30) # Pretil

    # 3 Ventanas coloniales rústicas hacia el patio
    for i in range(3):
        yw1 = 4.00 + i * 4.60
        yw2 = yw1 + 2.10
        ymid = (yw1 + yw2) * 0.5
        add_box(bm_ventanas, 32.36, 32.56, yw1, yw2, 1.10, 2.30)
        add_box(bm_rejas, 32.54, 32.68, yw1, yw2, 1.05, 2.35)
        add_box(bm_tejas_p, 32.52, 33.20, yw1 - 0.15, yw2 + 0.15, 2.40, 2.65)
        add_box(bm_vigas, 32.25, 33.15, ymid - 0.08, ymid + 0.08, 2.30, 2.42)

    add_box(bm_espadaña, 32.35, 32.65, 16.00, 18.00, 3.80, 4.45)

    # -----------------------------------------------------------------------
    # 3. GRAN CUERPO SUR ENVOLVENTE (X in [32.50, 68.00 m], Y in [18.00, 32.00 m])
    # -----------------------------------------------------------------------
    # A. Muro Frontal Norte hacia el Patio (Y = 18.00 m): Fachada de 2 niveles sólida y cerrada
    add_box(bm_muro, 32.35, 68.15, 17.85, 18.15, 0.00, 3.90) # Planta baja sólida
    add_box(bm_ventanas, 36.00, 38.50, 17.82, 18.18, 0.00, 2.40) # Puerta de acceso rústica
    add_box(bm_ventanas, 44.00, 47.00, 17.82, 18.18, 1.10, 2.30) # Ventana 1
    add_box(bm_rejas, 43.90, 47.10, 17.75, 17.85, 1.05, 2.35)
    add_box(bm_ventanas, 54.00, 57.00, 17.82, 18.18, 1.10, 2.30) # Ventana 2
    add_box(bm_rejas, 53.90, 57.10, 17.75, 17.85, 1.05, 2.35)

    # Planta Alta sólida de fachada norte (Y = 18.00 m, Z in [3.90, 6.90 m])
    add_box(bm_muro, 32.35, 68.15, 17.85, 18.15, 3.90, 6.90)
    for iwin in range(4):
        xw1 = 35.00 + iwin * 7.50
        xw2 = xw1 + 4.50
        # Carpintería y vidrios rústicos cerrados (cero huecos abiertos hacia el interior)
        add_box(bm_ventanas, xw1, xw2, 17.80, 18.20, 4.40, 6.20)
        add_box(bm_rejas, xw1 + 0.10, xw2 - 0.10, 17.74, 17.84, 4.35, 6.25)

    # B. Muro Sur Testero Continuo de Cerramiento (Y = 32.00 m, X in [32.35, 68.15 m])
    # SELLA POR COMPLETO EL REVERSO DE LA PARRILLA
    add_box(bm_muro, 32.35, 68.15, 31.85, 32.15, 0.00, 6.90)

    # C. Muro Poniente de Confinamiento (X = 68.00 m, Y in [18.00, 32.00 m])
    add_box(bm_muro, 67.85, 68.15, 18.00, 32.00, 0.00, 6.90)

    # D. Cubierta Hermética Continua de Azotea y Pretiles
    add_box(bm_muro, 32.35, 68.15, 18.00, 32.00, 6.70, 6.90) # Losa maciza
    add_box(bm_muro, 32.35, 68.15, 17.85, 18.15, 6.90, 7.40) # Pretil norte
    add_box(bm_muro, 32.35, 68.15, 31.85, 32.15, 6.90, 7.40) # Pretil sur
    add_box(bm_muro, 67.85, 68.15, 18.00, 32.00, 6.90, 7.40) # Pretil oeste
    add_box(bm_muro, 32.35, 32.65, 18.00, 32.00, 6.90, 7.40) # Pretil este

    # E. Chimenea anclada sólidamente en azotea
    add_box(bm_muro, 41.00, 43.20, 24.50, 26.70, 6.70, 8.50)
    add_box(bm_rejas, 40.80, 43.40, 24.30, 26.90, 8.50, 8.90)

    # Creación de objetos visuales
    obj_parr_m = create_mesh_object("LaParrilla_Muros_Terracota", bm_muro, mats["parrilla_terracota"], col)
    obj_parr_e = create_mesh_object("LaParrilla_Espadaña_Misional", bm_espadaña, mats["parrilla_terracota"], col)
    obj_parr_v = create_mesh_object("LaParrilla_Vigas_Canes", bm_vigas, mats["parrilla_madera_vigas"], col)
    obj_parr_win = create_mesh_object("LaParrilla_Ventanas_Madera", bm_ventanas, mats["parrilla_madera_vigas"], col)
    obj_parr_rej = create_mesh_object("LaParrilla_Rejas_Hierro", bm_rejas, mats["parrilla_reja_negra"], col)
    obj_parr_tej = create_mesh_object("LaParrilla_Tejadillos_Teja", bm_tejas_p, mats["teja_colonial"], col, uv_scale=1.5)
    objects.extend([obj_parr_m, obj_parr_e, obj_parr_v, obj_parr_win, obj_parr_rej, obj_parr_tej])

    # 4. RÓTULOS EN RELIEVE 3D DE LA PARRILLA
    t_parr1 = add_3d_text("LaParrilla_Txt_Nombre", "La Parrilla", 0.58, 0.04, (28.20, -0.15, 4.45), rot_north, mats["parrilla_rojo_letras"], col)
    t_parr2 = add_3d_text("LaParrilla_Txt_Sub", "Restaurant  Bar  &  Grill", 0.22, 0.02, (28.20, -0.15, 4.05), rot_north, mats["herreria_negra"], col)

    bm_adt = bmesh.new()
    add_box(bm_adt, 30.60, 31.00, -0.16, -0.14, 2.90, 3.30)
    obj_adt = create_mesh_object("LaParrilla_Placa_ADT", bm_adt, mats["adt_azul"], col)
    objects.extend([t_parr1, t_parr2, obj_adt])

    t_parr_lat = add_3d_text("LaParrilla_Txt_Lateral", "La Parrilla\\nBar & Grill", 0.28, 0.03, (32.68, 18.00, 4.15), rot_west_wall, mats["parrilla_rojo_letras"], col)
    objects.append(t_parr_lat)

    return objects\n\ndef build_parking_and_grounds"""

code, n_subs = pattern_parrilla.subn(new_parrilla_code, code)
assert n_subs == 1, f"pattern_parrilla replaced {n_subs} times"

# 3. Update generate_godot_scene: impenetrable perimeter collision boxes for La Parrilla
old_godot_parrilla = """[sub_resource type="BoxShape3D" id="BoxShape3D_parrilla_norte"]
size = Vector3(15.00, 4.20, 0.30)

[sub_resource type="BoxShape3D" id="BoxShape3D_parrilla_ala_este"]
size = Vector3(0.30, 3.80, 20.00)

[sub_resource type="BoxShape3D" id="BoxShape3D_parrilla_cuerpo_sur_norte"]
size = Vector3(35.50, 6.80, 0.30)

[sub_resource type="BoxShape3D" id="BoxShape3D_parrilla_cuerpo_sur_sur"]
size = Vector3(35.50, 6.80, 0.30)"""

new_godot_parrilla = """[sub_resource type="BoxShape3D" id="BoxShape3D_parrilla_norte"]
size = Vector3(15.00, 4.20, 0.30)

[sub_resource type="BoxShape3D" id="BoxShape3D_parrilla_muro_este"]
size = Vector3(0.30, 6.90, 32.00)

[sub_resource type="BoxShape3D" id="BoxShape3D_parrilla_muro_sur"]
size = Vector3(35.80, 6.90, 0.30)

[sub_resource type="BoxShape3D" id="BoxShape3D_parrilla_muro_oeste"]
size = Vector3(0.30, 6.90, 14.00)

[sub_resource type="BoxShape3D" id="BoxShape3D_parrilla_muro_patio"]
size = Vector3(35.80, 6.90, 0.30)"""

assert old_godot_parrilla in code, "old_godot_parrilla not found"
code = code.replace(old_godot_parrilla, new_godot_parrilla, 1)

old_godot_nodes = """# 6. La Parrilla Restaurant (Estructura Envolvente en Muros Perimetrales Delgados)
[node name="Col_Parrilla_Norte" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 25.00, 2.10, 0.00)
shape = SubResource("BoxShape3D_parrilla_norte")

[node name="Col_Parrilla_Ala_Este" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 32.45, 1.90, -10.00)
shape = SubResource("BoxShape3D_parrilla_ala_este")

[node name="Col_Parrilla_Cuerpo_Sur_Norte" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 50.25, 3.40, -18.00)
shape = SubResource("BoxShape3D_parrilla_cuerpo_sur_norte")

[node name="Col_Parrilla_Cuerpo_Sur_Sur" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 50.25, 3.40, -32.00)
shape = SubResource("BoxShape3D_parrilla_cuerpo_sur_sur")"""

new_godot_nodes = """# 6. La Parrilla Restaurant (Cerramiento Perimetral Completo e Impenetrable)
[node name="Col_Parrilla_Norte" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 25.00, 2.10, 0.00)
shape = SubResource("BoxShape3D_parrilla_norte")

[node name="Col_Parrilla_Muro_Este" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 32.50, 3.45, -16.00)
shape = SubResource("BoxShape3D_parrilla_muro_este")

[node name="Col_Parrilla_Muro_Sur" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 50.25, 3.45, -32.00)
shape = SubResource("BoxShape3D_parrilla_muro_sur")

[node name="Col_Parrilla_Muro_Oeste" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 68.00, 3.45, -25.00)
shape = SubResource("BoxShape3D_parrilla_muro_oeste")

[node name="Col_Parrilla_Muro_Patio" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 50.25, 3.45, -18.00)
shape = SubResource("BoxShape3D_parrilla_muro_patio")"""

assert old_godot_nodes in code, "old_godot_nodes not found"
code = code.replace(old_godot_nodes, new_godot_nodes, 1)

with open(target_path, "w", encoding="utf-8") as f:
    f.write(code)

print("Etapa 3 aplicada con éxito.")
