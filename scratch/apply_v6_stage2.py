import re

target_path = "scripts/generate_cardenas_25.py"
with open(target_path, "r", encoding="utf-8") as f:
    code = f.read()

# Replace build_north_libertad_facade completely
pattern_north = re.compile(r'def build_north_libertad_facade\(mats, col\):.*?def build_south_hidalgo_facade', re.DOTALL)

new_north_code = """def build_north_libertad_facade(mats, col):
    \"\"\"
    Construye la fachada norte sobre Callejón Libertad (V6.0 Ground-Truth):
      - CERO HUECOS LATERALES: Muros macizos continuos con enjutas selladas y machones completos.
      - Portal peatonal de esquina 100% abierto y transitable en PB (X in [0.65, 2.20 m]).
      - 2 arcos ciegos rehundidos con zócalo de laja dorada y paños estucados con pátina.
      - 3.er arco con CAJERO AUTOMÁTICO SANTANDER (ATM) 2009 fidedigno: cancelería negra,
        doble puerta de cristal ahumado, tiradores de acero inox, rótulo vertical, vestíbulo
        rehundido con cajero ATM tridimensional y puerta de servicio contigua acanalada.
      - PLANTA ALTA: 3 ventanales en arco sin huecos laterales, balcón corrido con barandales a 90°.
      - CUBIERTA VOLADA CONTINUA: Faldón de tejas coloniales que CUBRE LA TOTALIDAD DEL BALCÓN DE LIBERTAD
        (X in [-0.70, 14.80 m], Y in [-1.50, 0.50 m]) con postes de sustentación, trabe maestra y canes de madera.
      - Cierre testero perpendicular hermético en X = 14.50 m.
    \"\"\"
    objects = []
    rot_north = (math.radians(90.0), 0.0, 0.0)

    bm_muro = bmesh.new()
    bm_ladrillo = bmesh.new()
    bm_atm_vid = bmesh.new()
    bm_atm_alu = bmesh.new()
    bm_atm_acero = bmesh.new()
    bm_sant_rojo = bmesh.new()
    bm_atm_scr = bmesh.new()
    bm_puer_crema = bmesh.new()
    bm_balcon = bmesh.new()
    bm_techo_n = bmesh.new()
    bm_postes_n = bmesh.new()
    bm_trabe_n = bmesh.new()
    bm_canes_n = bmesh.new()

    # 1. PLANTA BAJA (Callejón Libertad, Y = 0.00 m, Z in [0.00, 3.65 m])
    add_box(bm_muro, 2.20, 14.50, -0.15, 0.15, 0.00, 0.40)
    add_box(bm_muro, 0.00, 14.50, -0.15, 0.15, 3.30, 3.65)

    # A. Vano peatonal de esquina: X in [0.65, 2.20 m]
    add_arch_spandrel_x(bm_muro, -0.15, 0.15, 0.65, 2.20, 2.45, 3.25, 3.65, segments=10)

    # Pilar esquinero (X in [0.00, 0.65 m]):
    add_box(bm_muro, 0.00, 0.65, -0.18, 0.18, 0.00, 1.40) # Laja
    add_box(bm_muro, -0.02, 0.67, -0.20, 0.20, 1.40, 1.48) # Moldura
    add_box(bm_muro, 0.00, 0.65, -0.15, 0.15, 1.48, 3.65) # Estuco continuo

    # Machón de retorno vertical (conecta portal de esquina con arco 1):
    add_box(bm_muro, 2.20, 2.45, -0.15, 0.15, 0.00, 3.65)

    # Pilastras intermedias sólidas de piso a techo:
    for xp1, xp2 in [(5.60, 6.25), (9.65, 10.30), (13.85, 14.50)]:
        add_box(bm_muro, xp1, xp2, -0.18, 0.22, 0.00, 1.40) # Laja
        add_box(bm_muro, xp1 - 0.02, xp2 + 0.02, -0.20, 0.24, 1.40, 1.48) # Moldura
        add_box(bm_muro, xp1, xp2, -0.16, 0.20, 1.48, 2.45) # Fuste
        add_box(bm_muro, xp1 - 0.03, xp2 + 0.03, -0.19, 0.23, 2.45, 2.58) # Capitel
        add_box(bm_muro, xp1, xp2, -0.15, 0.15, 2.58, 3.65) # Mampostería hasta dintel

    # Arcos 1 y 2 (Ciegos con nichos rehundidos y tímpanos cerrados):
    for x1, x2 in [(2.45, 5.60), (6.25, 9.65)]:
        add_arch_spandrel_x(bm_ladrillo, -0.20, -0.14, x1, x2, 2.30, 3.05, 3.30, segments=14)
        add_box(bm_muro, x1, x2, -0.15, 0.15, 3.05, 3.65)
        add_box(bm_muro, x1, x2, -0.06, 0.15, 0.00, 3.05)
        add_box(bm_muro, x1, x2, -0.09, 0.15, 0.00, 0.95)

    # Arco 3 (Cajero Automático Santander - ATM, X in [10.30, 13.85 m]):
    add_arch_spandrel_x(bm_ladrillo, -0.20, -0.14, 10.30, 13.85, 2.30, 3.05, 3.30, segments=14)
    add_box(bm_muro, 10.30, 13.85, -0.15, 0.15, 2.45, 3.65)

    # Vestíbulo interior rehundido (X in [10.30, 12.65 m], Y in [-0.15, 0.75 m])
    add_box(bm_muro, 10.30, 12.65, -0.15, 0.75, 0.00, 0.05) # Suelo granito
    add_box(bm_muro, 10.30, 12.65, -0.15, 0.75, 2.40, 2.45) # Plafón
    add_box(bm_muro, 10.30, 12.65, 0.70, 0.75, 0.00, 2.45)  # Muro trasero
    add_box(bm_muro, 10.25, 10.30, -0.15, 0.75, 0.00, 2.45) # Muro lateral izq
    add_box(bm_muro, 12.65, 12.70, -0.15, 0.75, 0.00, 2.45) # Muro divisor der

    # Cancelería de aluminio anodizado negro y doble puerta en Y = -0.10 m
    add_box(bm_atm_alu, 10.30, 12.65, -0.13, -0.07, 0.00, 2.45) # Cerco exterior
    add_box(bm_atm_alu, 10.30, 12.65, -0.14, -0.06, 0.00, 0.12) # Zócalo
    add_box(bm_atm_alu, 10.30, 12.65, -0.14, -0.06, 2.32, 2.45) # Dintel
    add_box(bm_atm_alu, 11.45, 11.50, -0.14, -0.06, 0.12, 2.32) # Montante central

    # Doble puerta acristalada ahumada oscura
    add_box(bm_atm_vid, 10.35, 11.45, -0.11, -0.09, 0.12, 2.32)
    add_box(bm_atm_vid, 11.50, 12.60, -0.11, -0.09, 0.12, 2.32)

    # Tiradores tubulares verticales de acero inoxidable (60 cm)
    add_box(bm_atm_acero, 11.38, 11.42, -0.18, -0.14, 0.85, 1.45)
    add_box(bm_atm_acero, 11.53, 11.57, -0.18, -0.14, 0.85, 1.45)

    # Terminal ATM Santander en el interior del vestíbulo (empotrado en pared trasera en Y = 0.68 m)
    add_box(bm_muro, 10.70, 12.25, 0.45, 0.70, 0.00, 1.95) # Carcasa
    add_box(bm_sant_rojo, 10.75, 12.20, 0.42, 0.46, 0.55, 1.90) # Frontal rojo Santander
    add_box(bm_sant_rojo, 10.85, 12.10, 0.40, 0.44, 1.65, 1.85) # Marquesina luminosa
    add_box(bm_atm_scr, 11.10, 11.85, 0.40, 0.43, 1.25, 1.55)   # Pantalla interactiva
    add_box(bm_atm_acero, 11.15, 11.80, 0.35, 0.44, 1.02, 1.08) # Repisa teclado numérico
    add_box(bm_atm_acero, 11.20, 11.75, 0.40, 0.44, 0.82, 0.90) # Ranura de efectivo

    # Puerta de servicio contigua en X in [12.70, 13.85 m]
    add_box(bm_muro, 12.70, 13.85, -0.14, 0.02, 0.00, 2.35) # Marco de acero
    add_box(bm_puer_crema, 12.75, 13.80, -0.12, -0.04, 0.05, 2.30) # Hoja de puerta
    add_box(bm_atm_acero, 12.80, 12.85, -0.16, -0.11, 0.95, 1.05)  # Picaporte

    # 2. PLANTA ALTA: BALCÓN CORRIDO Y VENTANALES SIN HUECOS (Z in [3.65, 6.45 m])
    add_box(bm_muro, 0.00, 14.50, -0.15, 0.15, 3.65, 4.30)
    add_box(bm_muro, 0.00, 14.50, -0.15, 0.15, 6.10, 6.45)

    # Machones macizos verticales entre ventanas (SELLAN LOS HUECOS LATERALES)
    add_box(bm_muro, 0.00, 0.60, -0.15, 0.15, 4.30, 6.10)
    add_box(bm_muro, 4.00, 5.00, -0.15, 0.15, 4.30, 6.10)
    add_box(bm_muro, 8.40, 9.40, -0.15, 0.15, 4.30, 6.10)
    add_box(bm_muro, 12.80, 14.50, -0.15, 0.15, 4.30, 6.10)

    # 3 grandes ventanales en arco
    for x1, x2 in [(0.60, 4.00), (5.00, 8.40), (9.40, 12.80)]:
        add_arch_spandrel_x(bm_ladrillo, -0.16, -0.12, x1, x2, 5.20, 5.90, 6.10, segments=12)
        add_box(bm_muro, x1, x2, -0.15, 0.15, 5.80, 6.10) # Tímpano cerrado
        add_box(bm_atm_vid, x1 + 0.10, x2 - 0.10, -0.12, -0.08, 4.30, 5.80)
        xmid = (x1 + x2) * 0.5
        add_box(bm_muro, xmid - 0.04, xmid + 0.04, -0.14, -0.06, 4.30, 5.80)

    # Losa de piso en voladizo (X in [0.00, 14.50 m], Y in [-1.20, 0.00 m])
    add_box(bm_balcon, 0.00, 14.50, -1.20, 0.00, 3.55, 3.65)
    add_box(bm_balcon, 0.00, 14.50, -1.25, -1.18, 3.50, 3.68)
    add_box(bm_balcon, -0.08, 0.02, -1.25, 0.00, 3.50, 3.68)

    # Ménsulas estructurales de apoyo bajo el balcón
    for im in range(7):
        xm = 1.00 + im * 2.10
        add_box(bm_muro, xm - 0.12, xm + 0.12, -1.15, 0.10, 3.10, 3.55)

    # Barandal corrido de forja negra a lo largo de Libertad (Y = -1.20 m)
    add_box(bm_balcon, 0.00, 14.50, -1.22, -1.18, 4.55, 4.60)
    add_box(bm_balcon, 0.00, 14.50, -1.21, -1.19, 3.68, 3.72)
    for i in range(int(14.50 / 0.15)):
        xb = i * 0.15
        add_box(bm_balcon, xb - 0.012, xb + 0.012, -1.21, -1.19, 3.70, 4.55)

    # Unión a 90° de barandales en esquina norte
    add_box(bm_balcon, -0.02, 0.02, -1.20, 0.00, 4.55, 4.60)
    add_box(bm_balcon, -0.015, 0.015, -1.20, 0.00, 3.68, 3.72)
    for i in range(int(1.20 / 0.15)):
        yb = -i * 0.15
        add_box(bm_balcon, -0.012, 0.012, yb - 0.012, yb + 0.012, 3.70, 4.55)

    # Cierre perpendicular testero en X = 14.50 m
    add_box(bm_muro, 14.35, 14.65, -0.15, 4.50, 0.00, 6.45)
    add_box(bm_muro, 11.20, 14.50, 4.35, 4.65, 0.00, 6.45)

    # 3. CUBIERTA VOLADA CONTINUA DE TEJAS SOBRE TODO EL BALCÓN DE LIBERTAD
    # Postes de sustentación verticales en Y = -1.15 m
    for xp in [0.00, 4.65, 9.30, 14.50]:
        add_box(bm_postes_n, xp - 0.05, xp + 0.05, -1.18, -1.12, 3.65, 6.46)

    # Trabe maestra corrida en Y = -1.15 m
    add_box(bm_trabe_n, -0.70, 14.80, -1.20, -1.10, 6.35, 6.48)

    # Viguería transversal y canes de madera cada 0.65 m en X
    for i in range(int((14.80 - (-0.70)) / 0.65) + 1):
        xc = -0.70 + i * 0.65
        add_box(bm_canes_n, xc - 0.06, xc + 0.06, -1.50, 0.10, 6.32, 6.46)

    # Faldón inclinado de tejas que vuela 30 cm sobre el barandal (Y in [-1.50, 0.50 m])
    add_sloped_roof_hip_x(bm_techo_n, -0.70, 14.80, -1.50, 0.50, 6.46, 7.45, hip_x_start=-0.70, hip_x_end=14.80)
    add_teja_ribs_x(bm_techo_n, -0.70, 14.80, -1.50, 0.50, 6.46, 7.45, spacing=0.45, hip_x_start=-0.70, hip_x_end=14.80)

    # Creación de objetos visuales y vinculación a colección
    obj_mn = create_mesh_object("Libertad_Muro_Norte", bm_muro, mats["estuco_ocre"], col)
    obj_ln = create_mesh_object("Libertad_Arcos_Ladrillo", bm_ladrillo, mats["ladrillo_dovelas"], col, uv_scale=1.2)
    obj_avid = create_mesh_object("Libertad_ATM_Vidrios", bm_atm_vid, mats["vidrio_oscuro"], col)
    obj_aalu = create_mesh_object("Libertad_ATM_Canceleria", bm_atm_alu, mats["aluminio_negro"], col)
    obj_aace = create_mesh_object("Libertad_ATM_Herrajes", bm_atm_acero, mats["atm_acero"], col)
    obj_snt = create_mesh_object("Libertad_ATM_Santander_Front", bm_sant_rojo, mats["santander_rojo"], col)
    obj_ascr = create_mesh_object("Libertad_ATM_Pantalla", bm_atm_scr, mats["atm_pantalla"], col)
    obj_apue = create_mesh_object("Libertad_Puerta_Servicio", bm_puer_crema, mats["puerta_crema"], col)
    obj_bal = create_mesh_object("Libertad_Balcon_Terraza_Corrida", bm_balcon, mats["herreria_negra"], col)
    obj_tn = create_mesh_object("Libertad_Techo_Tejas_Hip", bm_techo_n, mats["teja_colonial"], col, uv_scale=1.5)
    obj_pst_n = create_mesh_object("Libertad_Postes_Techo", bm_postes_n, mats["herreria_negra"], col)
    obj_trb_n = create_mesh_object("Libertad_Trabe_Madera", bm_trabe_n, mats["madera_canes"], col)
    obj_cns_n = create_mesh_object("Libertad_Canes_Madera", bm_canes_n, mats["madera_canes"], col)
    objects.extend([obj_mn, obj_ln, obj_avid, obj_aalu, obj_aace, obj_snt, obj_ascr, obj_apue, obj_bal, obj_tn, obj_pst_n, obj_trb_n, obj_cns_n])

    # Rótulo vertical tridimensional CAJERO AUTOMATICO
    t_atm = add_3d_text("Libertad_Txt_Cajero", "CAJERO\\nAUTOMATICO", 0.18, 0.02, (10.40, -0.20, 1.65), rot_north, mats["santander_blanco"], col)
    objects.append(t_atm)

    # Letrero de Fraccionamiento La Salamandra colgado en el balcón
    bm_sal_b = bmesh.new()
    add_box(bm_sal_b, 1.20, 4.20, -1.24, -1.21, 3.85, 4.50)
    obj_sal_p = create_mesh_object("Libertad_Panel_Salamandra", bm_sal_b, mats["salamandra_amarillo"], col)
    objects.append(obj_sal_p)
    t_sal_b = add_3d_text("Libertad_Txt_Salamandra", "FRACCIONAMIENTO\\nLA SALAMANDRA\\nLOTES EN ABONOS", 0.16, 0.02, (2.70, -1.26, 4.18), rot_north, mats["salamandra_letras"], col)
    objects.append(t_sal_b)

    # Portón de servicio de reja gris (X in [14.50, 17.50 m])
    bm_reja = bmesh.new()
    add_box(bm_reja, 14.50, 17.50, -0.10, -0.05, 0.00, 2.40)
    for i in range(int(3.0 / 0.15)):
        xr = 14.50 + i * 0.15
        add_box(bm_reja, xr - 0.015, xr + 0.015, -0.11, -0.04, 0.00, 2.45)
    obj_rej = create_mesh_object("Libertad_Reja_Servicio", bm_reja, mats["puerta_servicio_gris"], col)
    objects.append(obj_rej)

    return objects\n\ndef build_south_hidalgo_facade"""

code, n_subs = pattern_north.subn(new_north_code, code)
assert n_subs == 1, f"pattern_north replaced {n_subs} times"

with open(target_path, "w", encoding="utf-8") as f:
    f.write(code)

print("Etapa 2 (Libertad completa) aplicada con éxito.")
