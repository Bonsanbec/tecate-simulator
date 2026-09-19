"""
GENERADOR PROCEDURAL 3D - FUENTE DE LA PAZ (PARQUE MIGUEL HIDALGO, 2009)
Tecate Simulator - Godot Engine 4 / Blender Python Headless API

Ubicación: Esquina Noroeste del Parque Miguel Hidalgo (Av. Benito Juárez y Calle Pdte. Lázaro Cárdenas)
Coordenadas GPS: 32.573366°N, -116.626902°W
Manzana: block_lat_32.57293_lon_-116.62685
Época Histórica: 2009

Fidelidad Total Ground-Truth 2009 (V4.0 Definitiva):
  - Perímetro lobulado simétrico fidedigno a la vista aérea 'aerial_fuente.png' y fotos a pie de calle.
  - Murete exterior en estuco amarillo municipal (#ECC673) con buña/ranura intermedia y zócalo a Z = -1.30 m.
  - Albardilla de asiento en barro cocido terracota vidriado (#8F3018).
  - Vaso interior con mosaico turquesa (#1C667E) y espejo de agua cristalina a Z = 0.28 m.
  - Núcleo central monumental de 8 sectores:
    * Friso vertical octagonal con azulejos Talavera en damero azul cobalto y oro.
    * Cornisa moldurada de cantera con 16 toberas/esferas cerámicas azules.
    * Cascada piramidal inclinada con 8 nervaduras/mochetas radiales continuas de cantera
      y 3 resaltes/peldaños intermedios de rotura de agua.
    * Pedestal central torneado y copa/tazón labrado superior (#C4BCAC) con surtidor central de agua.
  - Colisiones analíticas en Godot 4 (BoxShape3D segmentadas + CylinderShape3D escalonadas).
"""

import bpy
import bmesh
import math
import os
from mathutils import Vector

# ==============================================================================
# 1. LIMPIEZA DE ESCENA Y SUITE DE MATERIALES PBR
# ==============================================================================

def clean_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    col = bpy.data.collections.new("Fuente_Parque_Hidalgo_Collection")
    scene.collection.children.link(col)
    return col

def create_materials():
    mats = {}

    # 1. Estuco Amarillo/Ocre Municipal (Murete exterior de banca)
    m_ocre = bpy.data.materials.new("M_Murete_Ocre")
    m_ocre.use_nodes = True
    bsdf_o = m_ocre.node_tree.nodes.get("Principled BSDF")
    bsdf_o.inputs["Base Color"].default_value = (0.84, 0.70, 0.40, 1.0) # Amarillo tecatense
    bsdf_o.inputs["Roughness"].default_value = 0.80
    mats["ocre"] = m_ocre

    # 2. Zócalo Basal Enterrado (Concreto/estuco basal continuo Z <= -1.20 m)
    m_zoc = bpy.data.materials.new("M_Zocalo_Basal")
    m_zoc.use_nodes = True
    bsdf_z = m_zoc.node_tree.nodes.get("Principled BSDF")
    bsdf_z.inputs["Base Color"].default_value = (0.42, 0.38, 0.32, 1.0)
    bsdf_z.inputs["Roughness"].default_value = 0.95
    mats["zocalo"] = m_zoc

    # 3. Albardilla Terracota / Barro Cocido (Remate de asiento)
    m_terracota = bpy.data.materials.new("M_Albardilla_Terracota")
    m_terracota.use_nodes = True
    bsdf_t = m_terracota.node_tree.nodes.get("Principled BSDF")
    bsdf_t.inputs["Base Color"].default_value = (0.56, 0.18, 0.08, 1.0) # Rojo terracota cerámico
    bsdf_t.inputs["Roughness"].default_value = 0.35
    mats["terracota"] = m_terracota

    # 4. Friso Talavera Mexicano (Damero decorativo azul cobalto y oro)
    m_talavera = bpy.data.materials.new("M_Talavera_Friso")
    m_talavera.use_nodes = True
    nt = m_talavera.node_tree
    bsdf_tal = nt.nodes.get("Principled BSDF")
    bsdf_tal.inputs["Roughness"].default_value = 0.18
    tex_checker = nt.nodes.new('ShaderNodeTexChecker')
    tex_checker.inputs["Color1"].default_value = (0.08, 0.20, 0.52, 1.0) # Azul cobalto profundo
    tex_checker.inputs["Color2"].default_value = (0.86, 0.60, 0.10, 1.0) # Oro ocre Talavera
    tex_checker.inputs["Scale"].default_value = 14.0
    nt.links.new(tex_checker.outputs["Color"], bsdf_tal.inputs["Base Color"])
    mats["talavera"] = m_talavera

    # 5. Esferas / Toberas Azules de Azulejo
    m_azul = bpy.data.materials.new("M_Azul_Ceramica")
    m_azul.use_nodes = True
    bsdf_at = m_azul.node_tree.nodes.get("Principled BSDF")
    bsdf_at.inputs["Base Color"].default_value = (0.06, 0.18, 0.48, 1.0)
    bsdf_at.inputs["Roughness"].default_value = 0.18
    mats["azul_ceramica"] = m_azul

    # 6. Cantera Cascada (Pirámide escalonada y cornisas)
    m_cantera = bpy.data.materials.new("M_Cantera_Cascada")
    m_cantera.use_nodes = True
    bsdf_c = m_cantera.node_tree.nodes.get("Principled BSDF")
    bsdf_c.inputs["Base Color"].default_value = (0.75, 0.71, 0.63, 1.0) # Cantera beige cálida
    bsdf_c.inputs["Roughness"].default_value = 0.78
    mats["cantera"] = m_cantera

    # 7. Copa Superior / Tazón Labrado
    m_copa = bpy.data.materials.new("M_Copa_Superior")
    m_copa.use_nodes = True
    bsdf_copa = m_copa.node_tree.nodes.get("Principled BSDF")
    bsdf_copa.inputs["Base Color"].default_value = (0.71, 0.67, 0.59, 1.0)
    bsdf_copa.inputs["Roughness"].default_value = 0.65
    mats["copa"] = m_copa

    # 8. Fondo de Estanque Sumergido (Mosaico turquesa)
    m_fondo = bpy.data.materials.new("M_Fondo_Mosaico")
    m_fondo.use_nodes = True
    bsdf_f = m_fondo.node_tree.nodes.get("Principled BSDF")
    bsdf_f.inputs["Base Color"].default_value = (0.12, 0.42, 0.54, 1.0)
    bsdf_f.inputs["Roughness"].default_value = 0.30
    mats["fondo"] = m_fondo

    # 9. Lámina de Agua de Estanque
    m_agua = bpy.data.materials.new("M_Agua_Superficie")
    m_agua.use_nodes = True
    bsdf_w = m_agua.node_tree.nodes.get("Principled BSDF")
    bsdf_w.inputs["Base Color"].default_value = (0.24, 0.62, 0.76, 1.0)
    bsdf_w.inputs["Roughness"].default_value = 0.06
    if "Transmission Weight" in bsdf_w.inputs:
        bsdf_w.inputs["Transmission Weight"].default_value = 0.85
    elif "Transmission" in bsdf_w.inputs:
        bsdf_w.inputs["Transmission"].default_value = 0.85
    if "IOR" in bsdf_w.inputs:
        bsdf_w.inputs["IOR"].default_value = 1.333
    mats["agua"] = m_agua

    # 10. Chorro / Geiser de Agua Vertical
    m_chorro = bpy.data.materials.new("M_Chorro_Agua")
    m_chorro.use_nodes = True
    bsdf_ch = m_chorro.node_tree.nodes.get("Principled BSDF")
    bsdf_ch.inputs["Base Color"].default_value = (0.88, 0.96, 0.98, 1.0)
    bsdf_ch.inputs["Roughness"].default_value = 0.20
    if "Transmission Weight" in bsdf_ch.inputs:
        bsdf_ch.inputs["Transmission Weight"].default_value = 0.70
    elif "Transmission" in bsdf_ch.inputs:
        bsdf_ch.inputs["Transmission"].default_value = 0.70
    mats["chorro"] = m_chorro

    return mats


# ==============================================================================
# 2. CURVATURA Y PERÍMETRO LOBULADO (SIMETRÍA FIDEDIGNA)
# ==============================================================================

def catmull_rom_spline(p0, p1, p2, p3, num_points=6):
    points = []
    for i in range(num_points):
        t = i / float(num_points)
        t2 = t * t
        t3 = t2 * t
        f0 = -0.5 * t3 + t2 - 0.5 * t
        f1 =  1.5 * t3 - 2.5 * t2 + 1.0
        f2 = -1.5 * t3 + 2.0 * t2 + 0.5 * t
        f3 =  0.5 * t3 - 0.5 * t2
        x = p0[0]*f0 + p1[0]*f1 + p2[0]*f2 + p3[0]*f3
        y = p0[1]*f0 + p1[1]*f1 + p2[1]*f2 + p3[1]*f3
        points.append((x, y))
    return points

def generate_perimeter_points(samples_per_seg=6):
    """
    Puntos de control para el perímetro lobulado según 'aerial_fuente.png':
    - Apertura/corte frontal hacia +Y (Noroeste Juárez-Cárdenas).
    - Dos hombreras/lóbulos frontales prominentes a ambos lados del corte.
    - Cintura lateral y lóbulos posteriores.
    - Lóbulo posterior central apuntando al sureste (interior del parque).
    """
    half_cp = [
        (0.00, 4.40),   # 0: Centro de línea de corte frontal
        (1.80, 4.55),   # 1: Extremo de la línea de corte frontal
        (3.60, 5.50),   # 2: LÓBULO FRONTAL (proyección hacia NW)
        (5.60, 4.20),   # 3: Transición fronto-lateral
        (6.40, 2.20),   # 4: LÓBULO LATERAL SALIENTE
        (5.40, 0.40),   # 5: Cintura lateral superior
        (5.40, -1.20),  # 6: Cintura lateral inferior
        (6.10, -3.20),  # 7: LÓBULO SUR-LATERAL POSTERIOR
        (5.00, -5.00),  # 8: Hombro posterior
        (3.00, -6.00),  # 9: Curva hacia el centro posterior
        (0.00, -6.50)   # 10: LÓBULO POSTERIOR CENTRAL (Parque Hidalgo)
    ]
    
    full_cp = list(half_cp)
    for p in reversed(half_cp[1:-1]):
        full_cp.append((-p[0], p[1]))
        
    n = len(full_cp)
    spline_points = []
    for i in range(n):
        p0 = full_cp[(i - 1) % n]
        p1 = full_cp[i]
        p2 = full_cp[(i + 1) % n]
        p3 = full_cp[(i + 2) % n]
        seg = catmull_rom_spline(p0, p1, p2, p3, samples_per_seg)
        spline_points.extend(seg)
        
    return spline_points


# ==============================================================================
# 3. GENERACIÓN GEOMÉTRICA FÍSICA (BMESH)
# ==============================================================================

def build_fountain_geometry(col, mats):
    mesh = bpy.data.meshes.new("Fuente_Parque_Hidalgo_Mesh")
    obj = bpy.data.objects.new("Fuente_Parque_Hidalgo", mesh)
    col.objects.link(obj)

    mat_order = ["ocre", "zocalo", "terracota", "talavera", "azul_ceramica", "cantera", "copa", "fondo", "agua", "chorro"]
    mat_indices = {}
    for idx, key in enumerate(mat_order):
        mesh.materials.append(mats[key])
        mat_indices[key] = idx

    bm = bmesh.new()

    # --------------------------------------------------------------------------
    # A. MURETE PERIMETRAL, ZÓCALO BASAL Y ALBARDILLA DE BANCA
    # --------------------------------------------------------------------------
    pts = generate_perimeter_points(samples_per_seg=6)
    n = len(pts)

    # Normales unitarias exteriores 2D (curva CCW -> nx = -ty, ny = tx)
    normals = []
    for i in range(n):
        prev_p = pts[(i - 1) % n]
        next_p = pts[(i + 1) % n]
        dx = next_p[0] - prev_p[0]
        dy = next_p[1] - prev_p[1]
        length = math.hypot(dx, dy)
        tx, ty = (dx / length, dy / length) if length > 1e-6 else (1.0, 0.0)
        nx = -ty
        ny =  tx
        normals.append((nx, ny))

    wall_w = 0.42           # Ancho del muro
    coping_overhang = 0.05  # Vuelo de la albardilla
    coping_w = wall_w + 2 * coping_overhang
    z_sub = -1.30           # Zócalo subterráneo enterrado (Z <= -1.20 m)
    z_ground = 0.00         # Nivel de rasante de banqueta
    z_wall_groove_b = 0.20  # Ranura/buña estética del muro
    z_wall_groove_t = 0.24
    z_wall_top = 0.46       # Cota superior del muro de estuco
    z_coping_top = 0.52     # Cota superior de asiento de albardilla
    z_floor = -0.15         # Fondo sumergido del estanque
    z_water = 0.28          # Espejo de agua

    rings = []
    hw = wall_w * 0.5
    hc = coping_w * 0.5

    for i in range(n):
        cx, cy = pts[i]
        nx, ny = normals[i]

        p_out_w = (cx + nx * hw, cy + ny * hw)
        p_in_w  = (cx - nx * hw, cy - ny * hw)
        p_out_c = (cx + nx * hc, cy + ny * hc)
        p_in_c  = (cx - nx * hc, cy - ny * hc)

        v0  = bm.verts.new((p_out_w[0], p_out_w[1], z_sub))
        v1  = bm.verts.new((p_out_w[0], p_out_w[1], z_ground))
        v2  = bm.verts.new((p_out_w[0], p_out_w[1], z_wall_groove_b))
        v3  = bm.verts.new((p_out_w[0] - nx * 0.02, p_out_w[1] - ny * 0.02, z_wall_groove_t))
        v4  = bm.verts.new((p_out_w[0], p_out_w[1], z_wall_top))
        v5  = bm.verts.new((p_out_c[0], p_out_c[1], z_wall_top))
        v6  = bm.verts.new((p_out_c[0], p_out_c[1], z_coping_top))
        v7  = bm.verts.new((p_in_c[0],  p_in_c[1],  z_coping_top))
        v8  = bm.verts.new((p_in_c[0],  p_in_c[1],  z_wall_top))
        v9  = bm.verts.new((p_in_w[0],  p_in_w[1],  z_wall_top))
        v10 = bm.verts.new((p_in_w[0],  p_in_w[1],  z_water))
        v11 = bm.verts.new((p_in_w[0],  p_in_w[1],  z_floor))
        v12 = bm.verts.new((p_in_w[0],  p_in_w[1],  z_sub))

        rings.append((v0, v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, v11, v12))

    for i in range(n):
        j = (i + 1) % n
        r1 = rings[i]
        r2 = rings[j]

        # 1. Zócalo basal exterior subterráneo (Z in [-1.30, 0.00 m])
        f_zoc = bm.faces.new((r1[0], r2[0], r2[1], r1[1]))
        f_zoc.material_index = mat_indices["zocalo"]
        f_zoc.smooth = True

        # 2. Muro exterior bajo buña (Z in [0.00, 0.20 m], Estuco ocre)
        f_ext1 = bm.faces.new((r1[1], r2[1], r2[2], r1[2]))
        f_ext1.material_index = mat_indices["ocre"]
        f_ext1.smooth = True

        # 3. Buña / Ranura decorativa (Z in [0.20, 0.24 m])
        f_groove = bm.faces.new((r1[2], r2[2], r2[3], r1[3]))
        f_groove.material_index = mat_indices["zocalo"]
        f_groove.smooth = True

        # 4. Muro exterior sobre buña (Z in [0.24, 0.46 m], Estuco ocre)
        f_ext2 = bm.faces.new((r1[3], r2[3], r2[4], r1[4]))
        f_ext2.material_index = mat_indices["ocre"]
        f_ext2.smooth = True

        # 5. Volado inferior albardilla exterior (Terracota)
        f_v_ext = bm.faces.new((r1[4], r2[4], r2[5], r1[5]))
        f_v_ext.material_index = mat_indices["terracota"]
        f_v_ext.smooth = True

        # 6. Canto exterior albardilla (Terracota)
        f_c_ext = bm.faces.new((r1[5], r2[5], r2[6], r1[6]))
        f_c_ext.material_index = mat_indices["terracota"]
        f_c_ext.smooth = True

        # 7. Asiento superior albardilla (Terracota)
        f_top = bm.faces.new((r1[6], r2[6], r2[7], r1[7]))
        f_top.material_index = mat_indices["terracota"]
        f_top.smooth = True

        # 8. Canto interior albardilla (Terracota)
        f_c_int = bm.faces.new((r1[7], r2[7], r2[8], r1[8]))
        f_c_int.material_index = mat_indices["terracota"]
        f_c_int.smooth = True

        # 9. Volado interior albardilla (Terracota)
        f_v_int = bm.faces.new((r1[8], r2[8], r2[9], r1[9]))
        f_v_int.material_index = mat_indices["terracota"]
        f_v_int.smooth = True

        # 10. Pared interior visible sobre agua (Z in [0.28, 0.46 m], Mosaico turquesa)
        f_int_top = bm.faces.new((r1[9], r2[9], r2[10], r1[10]))
        f_int_top.material_index = mat_indices["fondo"]
        f_int_top.smooth = True

        # 11. Pared interior sumergida (Z in [-0.15, 0.28 m], Mosaico turquesa)
        f_int_sub = bm.faces.new((r1[10], r2[10], r2[11], r1[11]))
        f_int_sub.material_index = mat_indices["fondo"]
        f_int_sub.smooth = True

        # 12. Muro subterráneo interior de contención (Z in [-1.30, -0.15 m])
        f_sub_int = bm.faces.new((r1[11], r2[11], r2[12], r1[12]))
        f_sub_int.material_index = mat_indices["zocalo"]
        f_sub_int.smooth = True

        # 13. Fondo basal del cimiento subterráneo
        f_bot = bm.faces.new((r1[12], r2[12], r2[0], r1[0]))
        f_bot.material_index = mat_indices["zocalo"]

    # --------------------------------------------------------------------------
    # B. FONDO DEL ESTANQUE Y ESPEJO DE AGUA
    # --------------------------------------------------------------------------
    vw_center = bm.verts.new((0.0, 0.0, z_water))
    vf_center = bm.verts.new((0.0, 0.0, z_floor))

    for i in range(n):
        j = (i + 1) % n
        # Cara del espejo de agua (suave)
        f_w = bm.faces.new((vw_center, rings[i][10], rings[j][10]))
        f_w.material_index = mat_indices["agua"]
        f_w.smooth = True

        # Cara del fondo de mosaico (suave)
        f_f = bm.faces.new((vf_center, rings[j][11], rings[i][11]))
        f_f.material_index = mat_indices["fondo"]
        f_f.smooth = True

    # --------------------------------------------------------------------------
    # C. NÚCLEO MONUMENTAL CENTRAL (8 CARAS OCTAGONALES)
    # --------------------------------------------------------------------------
    # 1. Anillo vertical octagonal con friso Talavera
    num_sides = 8
    r_talavera = 2.30
    z_tal_bot = 0.05
    z_tal_top = 0.68
    tal_verts_bot = []
    tal_verts_top = []

    for k in range(num_sides):
        ang = k * (2.0 * math.pi / num_sides) + math.radians(22.5)
        vx = r_talavera * math.cos(ang)
        vy = r_talavera * math.sin(ang)
        vb = bm.verts.new((vx, vy, z_tal_bot))
        vt = bm.verts.new((vx, vy, z_tal_top))
        tal_verts_bot.append(vb)
        tal_verts_top.append(vt)

    for k in range(num_sides):
        nxt = (k + 1) % num_sides
        # Friso de azulejos
        f_tal = bm.faces.new((tal_verts_bot[k], tal_verts_bot[nxt], tal_verts_top[nxt], tal_verts_top[k]))
        f_tal.material_index = mat_indices["talavera"]
        f_tal.smooth = False

        # Base sumergida hasta el fondo del estanque
        vx1, vy1 = tal_verts_bot[k].co.x, tal_verts_bot[k].co.y
        vx2, vy2 = tal_verts_bot[nxt].co.x, tal_verts_bot[nxt].co.y
        vs1 = bm.verts.new((vx1, vy1, z_floor))
        vs2 = bm.verts.new((vx2, vy2, z_floor))
        f_sub = bm.faces.new((vs1, vs2, tal_verts_bot[nxt], tal_verts_bot[k]))
        f_sub.material_index = mat_indices["fondo"]
        f_sub.smooth = False

    # Cornisa corrida de cantera sobre el friso Talavera (Z = 0.68 a 0.76 m, R = 2.42 m)
    r_corn = 2.42
    z_corn_mid = 0.74
    z_corn_top = 0.76
    corn_verts_mid = []
    corn_verts_top = []
    for k in range(num_sides):
        ang = k * (2.0 * math.pi / num_sides) + math.radians(22.5)
        vx = r_corn * math.cos(ang)
        vy = r_corn * math.sin(ang)
        v_m = bm.verts.new((vx, vy, z_corn_mid))
        v_t = bm.verts.new((r_talavera * math.cos(ang), r_talavera * math.sin(ang), z_corn_top))
        corn_verts_mid.append(v_m)
        corn_verts_top.append(v_t)

    for k in range(num_sides):
        nxt = (k + 1) % num_sides
        f_c1 = bm.faces.new((tal_verts_top[k], tal_verts_top[nxt], corn_verts_mid[nxt], corn_verts_mid[k]))
        f_c1.material_index = mat_indices["cantera"]
        f_c1.smooth = False
        f_c2 = bm.faces.new((corn_verts_mid[k], corn_verts_mid[nxt], corn_verts_top[nxt], corn_verts_top[k]))
        f_c2.material_index = mat_indices["cantera"]
        f_c2.smooth = False

    # 2. Toberas / Esferas Cerámicas Azules en la cornisa
    num_spheres = 16
    for s_idx in range(num_spheres):
        s_ang = s_idx * (2.0 * math.pi / num_spheres)
        sx = (r_talavera + 0.04) * math.cos(s_ang)
        sy = (r_talavera + 0.04) * math.sin(s_ang)
        sz = z_corn_mid + 0.06
        sr = 0.065
        add_faceted_sphere(bm, (sx, sy, sz), sr, mat_indices["azul_ceramica"])

    # 3. Pirámide Inclinada con Mochetas Radiales Continuas de Cantera (Ground Truth)
    # En lugar de tiras separadas, la pirámide tiene 8 nervaduras radiales integradas
    # y paños inclinados con 3 resaltes de rotura de cascada.
    z_pyr_bot = 0.76
    z_pyr_top = 1.80
    r_pyr_bot = 2.30
    r_pyr_top = 0.72

    num_steps = 3
    step_levels = []
    for s in range(num_steps + 1):
        frac = s / float(num_steps)
        z_s = z_pyr_bot + frac * (z_pyr_top - z_pyr_bot)
        r_s = r_pyr_bot + frac * (r_pyr_top - r_pyr_bot)
        step_levels.append((r_s, z_s))

    # Anillos para los paños de la cascada
    pyr_rings = []
    for r_s, z_s in step_levels:
        ring = []
        for k in range(num_sides):
            ang = k * (2.0 * math.pi / num_sides) + math.radians(22.5)
            vx = r_s * math.cos(ang)
            vy = r_s * math.sin(ang)
            v = bm.verts.new((vx, vy, z_s))
            ring.append(v)
        pyr_rings.append(ring)

    # Caras de los paños inclinados
    for s in range(num_steps):
        r_lower = pyr_rings[s]
        r_upper = pyr_rings[s + 1]
        for k in range(num_sides):
            nxt = (k + 1) % num_sides
            f_pyr = bm.faces.new((r_lower[k], r_lower[nxt], r_upper[nxt], r_upper[k]))
            f_pyr.material_index = mat_indices["cantera"]
            f_pyr.smooth = False

    # 8 Nervaduras / Mochetas Radiales Continuas en las aristas (Cantera maciza)
    rib_w = 0.09 # Semiancho de nervadura (18 cm total)
    rib_h = 0.06 # Altura de resalte (6 cm sobre la superficie)
    for k in range(num_sides):
        ang = k * (2.0 * math.pi / num_sides) + math.radians(22.5)
        ca = math.cos(ang)
        sa = math.sin(ang)
        px = -sa * rib_w
        py =  ca * rib_w

        # Vértices de la nervadura en la base y en la cúspide
        p_bot = (r_pyr_bot * ca, r_pyr_bot * sa, z_pyr_bot)
        p_top = (r_pyr_top * ca, r_pyr_top * sa, z_pyr_top)

        v_b1 = bm.verts.new((p_bot[0] + px, p_bot[1] + py, p_bot[2] + rib_h))
        v_b2 = bm.verts.new((p_bot[0] - px, p_bot[1] - py, p_bot[2] + rib_h))
        v_t1 = bm.verts.new((p_top[0] + px, p_top[1] + py, p_top[2] + rib_h))
        v_t2 = bm.verts.new((p_top[0] - px, p_top[1] - py, p_top[2] + rib_h))

        # Cara superior de la nervadura
        f_rib_top = bm.faces.new((v_b1, v_b2, v_t2, v_t1))
        f_rib_top.material_index = mat_indices["cantera"]
        f_rib_top.smooth = False

        # Cara frontal/pie de la nervadura
        v_bf1 = bm.verts.new((p_bot[0] + px, p_bot[1] + py, p_bot[2]))
        v_bf2 = bm.verts.new((p_bot[0] - px, p_bot[1] - py, p_bot[2]))
        f_rib_foot = bm.faces.new((v_bf1, v_bf2, v_b2, v_b1))
        f_rib_foot.material_index = mat_indices["cantera"]
        f_rib_foot.smooth = False

        # Costados laterales de la nervadura
        v_tf1 = bm.verts.new((p_top[0] + px, p_top[1] + py, p_top[2]))
        v_tf2 = bm.verts.new((p_top[0] - px, p_top[1] - py, p_top[2]))
        f_rib_l = bm.faces.new((v_bf1, v_b1, v_t1, v_tf1))
        f_rib_l.material_index = mat_indices["cantera"]
        f_rib_l.smooth = False
        f_rib_r = bm.faces.new((v_b2, v_bf2, v_tf2, v_t2))
        f_rib_r.material_index = mat_indices["cantera"]
        f_rib_r.smooth = False

    # 4. Plataforma superior y Pedestal Central
    z_ped_base = 1.80
    z_ped_top  = 2.15
    r_ped = 0.38
    r_torus = 0.46

    ped_base_verts = []
    ped_torus_verts = []
    ped_top_verts  = []
    for k in range(16):
        p_ang = k * (2.0 * math.pi / 16)
        ca = math.cos(p_ang)
        sa = math.sin(p_ang)
        vb = bm.verts.new((r_ped * ca, r_ped * sa, z_ped_base))
        vt_mid = bm.verts.new((r_torus * ca, r_torus * sa, 1.96))
        vt = bm.verts.new((r_ped * ca, r_ped * sa, z_ped_top))
        ped_base_verts.append(vb)
        ped_torus_verts.append(vt_mid)
        ped_top_verts.append(vt)

    # Conectar plataforma octagonal al pedestal
    top_pyr_ring = pyr_rings[-1]
    for k in range(num_sides):
        nxt = (k + 1) % num_sides
        p1 = k * 2
        p2 = ((k + 1) * 2) % 16
        pm = (k * 2 + 1) % 16
        f_plat1 = bm.faces.new((top_pyr_ring[k], top_pyr_ring[nxt], ped_base_verts[p2], ped_base_verts[pm]))
        f_plat1.material_index = mat_indices["cantera"]
        f_plat1.smooth = False
        f_plat2 = bm.faces.new((top_pyr_ring[k], ped_base_verts[pm], ped_base_verts[p1]))
        f_plat2.material_index = mat_indices["cantera"]
        f_plat2.smooth = False

    # Fuste y moldura toro del pedestal (Suave)
    for k in range(16):
        nxt = (k + 1) % 16
        f_p1 = bm.faces.new((ped_base_verts[k], ped_base_verts[nxt], ped_torus_verts[nxt], ped_torus_verts[k]))
        f_p1.material_index = mat_indices["copa"]
        f_p1.smooth = True
        f_p2 = bm.faces.new((ped_torus_verts[k], ped_torus_verts[nxt], ped_top_verts[nxt], ped_top_verts[k]))
        f_p2.material_index = mat_indices["copa"]
        f_p2.smooth = True

    # 5. Copa / Tazón Labrado Superior (Z in [2.15, 2.48 m])
    r_cup_belly = 0.58
    r_cup_rim   = 0.72
    r_cup_lip   = 0.76
    r_cup_inner = 0.62
    z_cup_belly = 2.28
    z_cup_rim   = 2.44
    z_cup_lip   = 2.47
    z_cup_floor = 2.34

    cup_belly_verts = []
    cup_rim_verts   = []
    cup_lip_verts   = []
    cup_in_verts    = []
    for k in range(16):
        ang = k * (2.0 * math.pi / 16)
        ca = math.cos(ang)
        sa = math.sin(ang)
        vb = bm.verts.new((r_cup_belly * ca, r_cup_belly * sa, z_cup_belly))
        vr = bm.verts.new((r_cup_rim   * ca, r_cup_rim   * sa, z_cup_rim))
        vl = bm.verts.new((r_cup_lip   * ca, r_cup_lip   * sa, z_cup_lip))
        vi = bm.verts.new((r_cup_inner * ca, r_cup_inner * sa, z_cup_floor))
        cup_belly_verts.append(vb)
        cup_rim_verts.append(vr)
        cup_lip_verts.append(vl)
        cup_in_verts.append(vi)

    v_cup_center = bm.verts.new((0.0, 0.0, z_cup_floor))

    for k in range(16):
        nxt = (k + 1) % 16
        f_cb = bm.faces.new((ped_top_verts[k], ped_top_verts[nxt], cup_belly_verts[nxt], cup_belly_verts[k]))
        f_cb.material_index = mat_indices["copa"]
        f_cb.smooth = True

        f_cr = bm.faces.new((cup_belly_verts[k], cup_belly_verts[nxt], cup_rim_verts[nxt], cup_rim_verts[k]))
        f_cr.material_index = mat_indices["copa"]
        f_cr.smooth = True

        f_cl = bm.faces.new((cup_rim_verts[k], cup_rim_verts[nxt], cup_lip_verts[nxt], cup_lip_verts[k]))
        f_cl.material_index = mat_indices["copa"]
        f_cl.smooth = True

        f_ci = bm.faces.new((cup_lip_verts[k], cup_lip_verts[nxt], cup_in_verts[nxt], cup_in_verts[k]))
        f_ci.material_index = mat_indices["copa"]
        f_ci.smooth = True

        f_cc = bm.faces.new((cup_in_verts[k], cup_in_verts[nxt], v_cup_center))
        f_cc.material_index = mat_indices["fondo"]
        f_cc.smooth = True

    # 6. Geiser / Chorro Vertical y Penacho de Agua (Z in [2.45, 3.10 m])
    jet_base_verts = []
    jet_mid_verts  = []
    jet_top_vert   = bm.verts.new((0.0, 0.0, 3.10))
    r_jb = 0.16
    r_jm = 0.26
    for k in range(12):
        j_ang = k * (2.0 * math.pi / 12)
        ca = math.cos(j_ang)
        sa = math.sin(j_ang)
        vb = bm.verts.new((r_jb * ca, r_jb * sa, 2.45))
        vm = bm.verts.new((r_jm * ca, r_jm * sa, 2.80))
        jet_base_verts.append(vb)
        jet_mid_verts.append(vm)

    for k in range(12):
        nxt = (k + 1) % 12
        f_jb = bm.faces.new((jet_base_verts[k], jet_base_verts[nxt], jet_mid_verts[nxt], jet_mid_verts[k]))
        f_jb.material_index = mat_indices["chorro"]
        f_jb.smooth = True
        f_jt = bm.faces.new((jet_mid_verts[k], jet_mid_verts[nxt], jet_top_vert))
        f_jt.material_index = mat_indices["chorro"]
        f_jt.smooth = True

    # Finalizar BMesh
    bm.to_mesh(mesh)
    bm.free()

    # Recalcular normales hacia afuera
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')

    return obj


def add_faceted_sphere(bm, center, radius, mat_idx):
    """Crea una tobera esférica decorativa."""
    cx, cy, cz = center
    num_lat, num_lon = 4, 8
    v_bottom = bm.verts.new((cx, cy, cz - radius))
    v_top    = bm.verts.new((cx, cy, cz + radius))

    levels = []
    for i in range(1, num_lat):
        phi = -math.pi * 0.5 + i * (math.pi / num_lat)
        z = cz + radius * math.sin(phi)
        r_ring = radius * math.cos(phi)
        ring = []
        for j in range(num_lon):
            theta = j * (2.0 * math.pi / num_lon)
            ring.append(bm.verts.new((cx + r_ring * math.cos(theta), cy + r_ring * math.sin(theta), z)))
        levels.append(ring)

    for j in range(num_lon):
        nxt = (j + 1) % num_lon
        f = bm.faces.new((v_bottom, levels[0][nxt], levels[0][j]))
        f.material_index = mat_idx
        f.smooth = True

    for i in range(len(levels) - 1):
        for j in range(num_lon):
            nxt = (j + 1) % num_lon
            f = bm.faces.new((levels[i][j], levels[i][nxt], levels[i+1][nxt], levels[i+1][j]))
            f.material_index = mat_idx
            f.smooth = True

    for j in range(num_lon):
        nxt = (j + 1) % num_lon
        f = bm.faces.new((levels[-1][j], levels[-1][nxt], v_top))
        f.material_index = mat_idx
        f.smooth = True


# ==============================================================================
# 4. GENERACIÓN DE ESCENA GODOT (.TSCN) CON FÍSICA ANALÍTICA
# ==============================================================================

def generate_godot_tscn(tscn_path, glb_res_path):
    pts = generate_perimeter_points(samples_per_seg=6)
    n = len(pts)
    step = 5
    sampled_indices = list(range(0, n, step))

    col_nodes = []
    sub_resources = []
    
    initial_sub_res = '''[sub_resource type="CylinderShape3D" id="CylinderShape3D_nucleo_base"]
height = 0.65
radius = 2.35

[sub_resource type="CylinderShape3D" id="CylinderShape3D_cascada_cuerpo"]
height = 1.05
radius = 1.65

[sub_resource type="CylinderShape3D" id="CylinderShape3D_copa_superior"]
height = 0.75
radius = 0.75

[sub_resource type="BoxShape3D" id="BoxShape3D_fondo_estanque"]
size = Vector3(11.5, 0.20, 11.5)
'''

    for c_idx, i in enumerate(sampled_indices):
        j = (i + step) % n
        p1 = pts[i]
        p2 = pts[j]
        mx = (p1[0] + p2[0]) * 0.5
        my = (p1[1] + p2[1]) * 0.5
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        seg_len = math.hypot(dx, dy)
        yaw = math.atan2(dx, dy)

        gx = mx
        gy = 0.25 # Z_blender = 0.25 m (centro de la banca)
        gz = -my  # Z_godot = -Y_blender

        sub_res = f'''[sub_resource type="BoxShape3D" id="BoxShape3D_banca_{c_idx}"]
size = Vector3(0.44, 0.52, {seg_len + 0.08:.3f})
'''
        sub_resources.append(sub_res)

        cos_y = math.cos(yaw)
        sin_y = math.sin(yaw)
        t_matrix = f"{cos_y:.6f}, 0, {sin_y:.6f}, 0, 1, 0, {-sin_y:.6f}, 0, {cos_y:.6f}, {gx:.3f}, {gy:.3f}, {gz:.3f}"
        node_str = f'''[node name="Col_Banca_{c_idx}" type="CollisionShape3D" parent="."]
transform = Transform3D({t_matrix})
shape = SubResource("BoxShape3D_banca_{c_idx}")
'''
        col_nodes.append(node_str)

    central_nodes = '''
[node name="Col_Nucleo_Base" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0.38, 0)
shape = SubResource("CylinderShape3D_nucleo_base")

[node name="Col_Cascada_Cuerpo" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1.28, 0)
shape = SubResource("CylinderShape3D_cascada_cuerpo")

[node name="Col_Copa_Superior" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 2.15, 0)
shape = SubResource("CylinderShape3D_copa_superior")

[node name="Col_Fondo_Estanque" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, -0.05, 0)
shape = SubResource("BoxShape3D_fondo_estanque")
'''

    total_steps = len(sub_resources) + 4 + 1 + 1 # banca + 4 formas centrales + 1 ext_res + 1 escena
    header = f'''[gd_scene load_steps={total_steps} format=3 uid="uid://fuente_parque_hidalgo_2009"]

[ext_resource type="PackedScene" path="{glb_res_path}" id="1_mesh"]

'''
    full_content = header + initial_sub_res + "".join(sub_resources) + body_header + "".join(col_nodes) + central_nodes
    os.makedirs(os.path.dirname(os.path.abspath(tscn_path)), exist_ok=True)
    with open(tscn_path, "w", encoding="utf-8") as f:
        f.write(full_content)
    print(f"[TSCN] Escena analítica generada exitosamente en: {tscn_path}")


# ==============================================================================
# 5. CÁMARAS DE VALIDACIÓN Y RENDERIZADO CYCLES
# ==============================================================================

def setup_lighting_and_cameras(col):
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    if hasattr(scene.cycles, 'device'):
        scene.cycles.device = 'CPU'
    scene.cycles.samples = 64
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720

    # Sol Diurno
    sun_data = bpy.data.lights.new("Sun_Light", 'SUN')
    sun_data.energy = 4.5
    sun_data.color = (1.0, 0.98, 0.92)
    sun_obj = bpy.data.objects.new("Sun_Light", sun_data)
    col.objects.link(sun_obj)
    sun_obj.rotation_euler = (math.radians(48.0), math.radians(18.0), math.radians(-35.0))

    # Cielo diurno
    world = bpy.data.worlds.new("World_Diurno")
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (0.65, 0.78, 0.92, 1.0)
    bg.inputs["Strength"].default_value = 1.25
    scene.world = world

    # Batería de 5 Cámaras Canónicas
    cams_config = [
        ("Cam_Cenital_Top",      (0.0, 0.0, 22.0),     (0.0, 0.0, 0.0), 32),
        ("Cam_Corte_Frente",     (0.0, 13.5, 3.8),     (0.0, 0.0, 1.2), 35),
        ("Cam_Perspectiva_45",   (-10.5, 10.5, 6.2),   (0.0, 0.0, 1.2), 32),
        ("Cam_Peatonal_Banca",   (-6.8, 6.8, 1.65),    (0.0, 0.0, 1.0), 28),
        ("Cam_Closeup_Cascada",  (2.8, 3.2, 2.4),      (0.0, 0.0, 1.6), 45)
    ]

    cams = {}
    for name, pos, tgt, lens in cams_config:
        c_data = bpy.data.cameras.new(name)
        c_data.lens = lens
        c_obj = bpy.data.objects.new(name, c_data)
        col.objects.link(c_obj)
        c_obj.location = Vector(pos)
        direction = Vector(tgt) - Vector(pos)
        c_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
        cams[name] = c_obj

    return cams

def render_validation_views(cams, render_dir):
    os.makedirs(render_dir, exist_ok=True)
    scene = bpy.context.scene
    for name, cam_obj in cams.items():
        scene.camera = cam_obj
        out_path = os.path.join(render_dir, f"{name}.png")
        scene.render.filepath = out_path
        bpy.ops.render.render(write_still=True)
        print(f"[Render] Generado: {out_path}")


# ==============================================================================
# 6. MAIN PIPELINE
# ==============================================================================

def main():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    blend_path = os.path.join(root_dir, "blender_assets", "fuente_parque_hidalgo.blend")
    glb_path   = os.path.join(root_dir, "godot_project", "assets", "fuente_parque_hidalgo.glb")
    tscn_path  = os.path.join(root_dir, "godot_project", "assets", "fuente_parque_hidalgo.tscn")
    render_dir = os.path.join(root_dir, "docs", "images", "fuente_parque_hidalgo")

    os.makedirs(os.path.dirname(blend_path), exist_ok=True)
    os.makedirs(os.path.dirname(glb_path), exist_ok=True)
    os.makedirs(render_dir, exist_ok=True)

    print(">>> 1. Inicializando escena y creando materiales PBR refinados V4.0...")
    col = clean_scene()
    mats = create_materials()

    print(">>> 2. Construyendo geometría física procedural de la Fuente de la Paz V4.0...")
    fountain_obj = build_fountain_geometry(col, mats)

    print(">>> 3. Guardando archivo maestro Blender (.blend)...")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"[Blender] Archivo maestro guardado en: {blend_path}")

    print(">>> 4. Exportando runtime de producción GLB...")
    bpy.ops.object.select_all(action='DESELECT')
    fountain_obj.select_set(True)
    bpy.context.view_layer.objects.active = fountain_obj

    bpy.ops.export_scene.gltf(
        filepath=glb_path,
        use_selection=True,
        export_format='GLB',
        export_apply=True,
        export_yup=True
    )
    print(f"[GLTF] Runtime exportado exitosamente en: {glb_path}")

    print(">>> 5. Generando escena Godot (.tscn) con colisionadores analíticos coordinados 1:1...")
    generate_godot_tscn(tscn_path, "res://assets/fuente_parque_hidalgo.glb")

    print(">>> 6. Configurando batería de validación y renderizando cámaras Cycles...")
    cams = setup_lighting_and_cameras(col)
    render_validation_views(cams, render_dir)

    print(">>> PROCESO DE GENERACIÓN PROCEDURAL V4.0 COMPLETADO EXITOSAMENTE.")

if __name__ == "__main__":
    main()
