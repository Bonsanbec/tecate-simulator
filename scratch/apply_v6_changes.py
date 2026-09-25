import re

target_path = "scripts/generate_cardenas_25.py"
with open(target_path, "r", encoding="utf-8") as f:
    code = f.read()

# 1. Update add_arch_spandrel and add_arch_spandrel_x to include end caps
old_arch_spandrel = """    for i in range(segments):
        y0, z0 = arc_pts[i]
        y1, z1 = arc_pts[i+1]
        v_bl_in = bm.verts.new((x_max, y0, z0))
        v_br_in = bm.verts.new((x_max, y1, z1))
        v_tr_in = bm.verts.new((x_max, y1, z_top))
        v_tl_in = bm.verts.new((x_max, y0, z_top))

        v_bl_out = bm.verts.new((x_min, y0, z0))
        v_br_out = bm.verts.new((x_min, y1, z1))
        v_tr_out = bm.verts.new((x_min, y1, z_top))
        v_tl_out = bm.verts.new((x_min, y0, z_top))

        bm.faces.new((v_bl_out, v_tl_out, v_tr_out, v_br_out))
        bm.faces.new((v_bl_in, v_br_in, v_tr_in, v_tl_in))
        bm.faces.new((v_bl_out, v_br_out, v_br_in, v_bl_in))
        bm.faces.new((v_tl_out, v_tl_in, v_tr_in, v_tr_out))"""

new_arch_spandrel = """    for i in range(segments):
        y0, z0 = arc_pts[i]
        y1, z1 = arc_pts[i+1]
        v_bl_in = bm.verts.new((x_max, y0, z0))
        v_br_in = bm.verts.new((x_max, y1, z1))
        v_tr_in = bm.verts.new((x_max, y1, z_top))
        v_tl_in = bm.verts.new((x_max, y0, z_top))

        v_bl_out = bm.verts.new((x_min, y0, z0))
        v_br_out = bm.verts.new((x_min, y1, z1))
        v_tr_out = bm.verts.new((x_min, y1, z_top))
        v_tl_out = bm.verts.new((x_min, y0, z_top))

        bm.faces.new((v_bl_out, v_tl_out, v_tr_out, v_br_out))
        bm.faces.new((v_bl_in, v_br_in, v_tr_in, v_tl_in))
        bm.faces.new((v_bl_out, v_br_out, v_br_in, v_bl_in))
        bm.faces.new((v_tl_out, v_tl_in, v_tr_in, v_tr_out))

    # Tapas laterales en y_start y y_end para evitar huecos en los extremos
    v_s_bl = bm.verts.new((x_min, y_start, z_spring))
    v_s_tl = bm.verts.new((x_min, y_start, z_top))
    v_s_tr = bm.verts.new((x_max, y_start, z_top))
    v_s_br = bm.verts.new((x_max, y_start, z_spring))
    bm.faces.new((v_s_bl, v_s_tl, v_s_tr, v_s_br))

    v_e_bl = bm.verts.new((x_min, y_end, z_spring))
    v_e_tl = bm.verts.new((x_min, y_end, z_top))
    v_e_tr = bm.verts.new((x_max, y_end, z_top))
    v_e_br = bm.verts.new((x_max, y_end, z_spring))
    bm.faces.new((v_e_bl, v_e_br, v_e_tr, v_e_tl))"""

assert old_arch_spandrel in code, "old_arch_spandrel not found"
code = code.replace(old_arch_spandrel, new_arch_spandrel, 1)

old_arch_spandrel_x = """    for i in range(segments):
        x0, z0 = arc_pts[i]
        x1, z1 = arc_pts[i+1]
        v_bl_in = bm.verts.new((x0, y_max, z0))
        v_br_in = bm.verts.new((x1, y_max, z1))
        v_tr_in = bm.verts.new((x1, y_max, z_top))
        v_tl_in = bm.verts.new((x0, y_max, z_top))

        v_bl_out = bm.verts.new((x0, y_min, z0))
        v_br_out = bm.verts.new((x1, y_min, z1))
        v_tr_out = bm.verts.new((x1, y_min, z_top))
        v_tl_out = bm.verts.new((x0, y_min, z_top))

        bm.faces.new((v_bl_out, v_tl_out, v_tr_out, v_br_out))
        bm.faces.new((v_bl_in, v_br_in, v_tr_in, v_tl_in))
        bm.faces.new((v_bl_out, v_br_out, v_br_in, v_bl_in))
        bm.faces.new((v_tl_out, v_tl_in, v_tr_in, v_tr_out))"""

new_arch_spandrel_x = """    for i in range(segments):
        x0, z0 = arc_pts[i]
        x1, z1 = arc_pts[i+1]
        v_bl_in = bm.verts.new((x0, y_max, z0))
        v_br_in = bm.verts.new((x1, y_max, z1))
        v_tr_in = bm.verts.new((x1, y_max, z_top))
        v_tl_in = bm.verts.new((x0, y_max, z_top))

        v_bl_out = bm.verts.new((x0, y_min, z0))
        v_br_out = bm.verts.new((x1, y_min, z1))
        v_tr_out = bm.verts.new((x1, y_min, z_top))
        v_tl_out = bm.verts.new((x0, y_min, z_top))

        bm.faces.new((v_bl_out, v_tl_out, v_tr_out, v_br_out))
        bm.faces.new((v_bl_in, v_br_in, v_tr_in, v_tl_in))
        bm.faces.new((v_bl_out, v_br_out, v_br_in, v_bl_in))
        bm.faces.new((v_tl_out, v_tl_in, v_tr_in, v_tr_out))

    # Tapas laterales en x_start y x_end
    v_sx_bl = bm.verts.new((x_start, y_min, z_spring))
    v_sx_tl = bm.verts.new((x_start, y_min, z_top))
    v_sx_tr = bm.verts.new((x_start, y_max, z_top))
    v_sx_br = bm.verts.new((x_start, y_max, z_spring))
    bm.faces.new((v_sx_bl, v_sx_br, v_sx_tr, v_sx_tl))

    v_ex_bl = bm.verts.new((x_end, y_min, z_spring))
    v_ex_tl = bm.verts.new((x_end, y_min, z_top))
    v_ex_tr = bm.verts.new((x_end, y_max, z_top))
    v_ex_br = bm.verts.new((x_end, y_max, z_spring))
    bm.faces.new((v_ex_bl, v_ex_tl, v_ex_tr, v_ex_br))"""

assert old_arch_spandrel_x in code, "old_arch_spandrel_x not found"
code = code.replace(old_arch_spandrel_x, new_arch_spandrel_x, 1)

# 2. Add roof helpers add_sloped_roof_hip_x and add_teja_ribs_x after add_teja_ribs
new_roof_x_helpers = """
def add_sloped_roof_hip_x(bm, x_start, x_end, y_eave, y_ridge, z_eave, z_ridge, hip_x_start=None, hip_x_end=None):
    \"\"\"Construye un plano inclinado de cubierta a lo largo del eje X con remates de limaoya (hip).\"\"\"
    delta_y = abs(y_ridge - y_eave)
    x0_eave = x_start
    x1_eave = x_end
    x0_ridge = x_start + delta_y if hip_x_start is not None else x_start
    x1_ridge = x_end - delta_y if hip_x_end is not None else x_end

    v_eave_l = bm.verts.new((x0_eave, y_eave, z_eave))
    v_eave_r = bm.verts.new((x1_eave, y_eave, z_eave))
    v_ridge_r = bm.verts.new((x1_ridge, y_ridge, z_ridge))
    v_ridge_l = bm.verts.new((x0_ridge, y_ridge, z_ridge))

    bm.faces.new((v_eave_l, v_eave_r, v_ridge_r, v_ridge_l))

    # Cierre inferior de plafón machihembrado
    v_soff_l = bm.verts.new((x0_eave, y_eave, z_eave - 0.14))
    v_soff_r = bm.verts.new((x1_eave, y_eave, z_eave - 0.14))
    v_soff_rr = bm.verts.new((x1_ridge, y_ridge, z_ridge - 0.14))
    v_soff_rl = bm.verts.new((x0_ridge, y_ridge, z_ridge - 0.14))

    bm.faces.new((v_soff_l, v_soff_rl, v_soff_rr, v_soff_r))
    bm.faces.new((v_eave_l, v_soff_l, v_soff_r, v_eave_r))

    # Hip end en el extremo poniente si aplica
    if hip_x_end is not None:
        v_corner_back = bm.verts.new((x1_eave, y_ridge, z_eave))
        bm.faces.new((v_eave_r, v_ridge_r, v_corner_back))
        v_soff_cb = bm.verts.new((x1_eave, y_ridge, z_eave - 0.14))
        bm.faces.new((v_soff_r, v_soff_cb, v_soff_rr))
        bm.faces.new((v_eave_r, v_corner_back, v_soff_cb, v_soff_r))

def add_teja_ribs_x(bm, x_start, x_end, y_eave, y_ridge, z_eave, z_ridge, spacing=0.45, hip_x_start=None, hip_x_end=None):
    \"\"\"Genera hiladas de teja colonial a lo largo del eje X recortadas en las limaoyas.\"\"\"
    num_ribs = int((x_end - x_start) / spacing)
    delta_y = abs(y_ridge - y_eave)
    for i in range(num_ribs):
        xc = x_start + i * spacing
        yr = y_ridge
        if hip_x_start is not None and xc < x_start + delta_y:
            yr = y_eave + max(0.15, xc - x_start) if y_eave < y_ridge else y_eave - max(0.15, xc - x_start)
        elif hip_x_end is not None and xc > x_end - delta_y:
            yr = y_ridge - max(0.15, x_end - xc) if y_eave < y_ridge else y_ridge + max(0.15, x_end - xc)

        if abs(yr - y_eave) <= 0.20:
            continue

        zr = z_eave + (z_ridge - z_eave) * (abs(yr - y_eave) / delta_y)
        v0 = bm.verts.new((xc - 0.10, y_eave, z_eave + 0.05))
        v1 = bm.verts.new((xc + 0.10, y_eave, z_eave + 0.05))
        v2 = bm.verts.new((xc + 0.10, yr, zr + 0.05))
        v3 = bm.verts.new((xc - 0.10, yr, zr + 0.05))
        v_top0 = bm.verts.new((xc, y_eave, z_eave + 0.11))
        v_top1 = bm.verts.new((xc, yr, zr + 0.11))

        bm.faces.new((v0, v1, v_top0))
        bm.faces.new((v1, v2, v_top1, v_top0))
        bm.faces.new((v2, v3, v_top1))
        bm.faces.new((v3, v0, v_top0, v_top1))
"""

target_after_ribs = "        bm.faces.new((v3, v0, v_top0, v_top1))\n"
assert target_after_ribs in code, "target_after_ribs not found"
code = code.replace(target_after_ribs, target_after_ribs + new_roof_x_helpers, 1)

# 3. Add ATM materials in create_materials
atm_mats = """    # Complementos ATM y servicio
    mats["atm_pantalla"] = make_pbr("M_ATM_Pantalla", (0.05, 0.40, 0.70), roughness=0.15)
    mats["atm_acero"] = make_pbr("M_ATM_Acero_Inox", (0.78, 0.80, 0.82), roughness=0.20, metallic=0.90)
    mats["puerta_crema"] = make_pbr("M_Puerta_Servicio_Crema", (0.88, 0.86, 0.80), roughness=0.50)
"""
target_mat = '    mats["puerta_servicio_gris"] = make_pbr("M_Puerta_Servicio_Gris", (0.45, 0.47, 0.50), roughness=0.40, metallic=0.6)\n'
assert target_mat in code, "target_mat not found"
code = code.replace(target_mat, target_mat + atm_mats, 1)

# 4. In build_front_cardenas: add solid masonry above pilasters to eliminate holes
old_front_arcos = """    for i in range(bay_count):
        y_start = i * bay_w + pilar_w * 0.5
        y_end = (i + 1) * bay_w - pilar_w * 0.5
        add_arch_spandrel(bm_arcos, 0.00, pilar_d, y_start, y_end, 2.50, 3.30, 3.55, segments=16)
        # Rosca de dovelas de ladrillo con resalte volumétrico de 5 cm hacia la calle
        add_arch_spandrel(bm_dovelas, -0.05, 0.00, y_start, y_end, 2.50, 3.30, 3.48, segments=16)"""

new_front_arcos = """    for i in range(bay_count):
        y_start = i * bay_w + pilar_w * 0.5
        y_end = (i + 1) * bay_w - pilar_w * 0.5
        add_arch_spandrel(bm_arcos, 0.00, pilar_d, y_start, y_end, 2.50, 3.30, 3.55, segments=16)
        # Rosca de dovelas de ladrillo con resalte volumétrico de 5 cm hacia la calle
        add_arch_spandrel(bm_dovelas, -0.05, 0.00, y_start, y_end, 2.50, 3.30, 3.48, segments=16)

    # SELLADO MACIZO DE MAMPOSTERÍA SOBRE CADA PILASTRA (ELIMINA EL HUECO ENTRE ARCOS)
    for i in range(bay_count + 1):
        yc = i * bay_w
        y1 = max(0.00, yc - pilar_w * 0.5)
        y2 = min(total_y, yc + pilar_w * 0.5)
        # Muro macizo estucado que une las enjutas a ambos lados sobre la pilastra
        add_box(bm_arcos, 0.00, pilar_d, y1, y2, 2.50, 3.65)
        # Franja de resalte de dovelas de ladrillo en la coronación de la pilastra
        add_box(bm_dovelas, -0.05, 0.00, y1, y2, 2.50, 2.65)"""

assert old_front_arcos in code, "old_front_arcos not found"
code = code.replace(old_front_arcos, new_front_arcos, 1)

with open(target_path, "w", encoding="utf-8") as f:
    f.write(code)

print("Etapa 1 aplicada con éxito.")
