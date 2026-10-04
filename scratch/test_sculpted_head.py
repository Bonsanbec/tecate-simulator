"""
Test de Cabeza Esculpida Anatómica, Rizos Volumétricos y Sombrero Fedora de Axel (Close-up Portrait)
"""
import bpy
import bmesh
import math
import os
from mathutils import Vector, Matrix, Euler

def clean_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh, do_unlink=True)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat, do_unlink=True)

clean_scene()

def clampf(v, min_v, max_v):
    return max(min_v, min(v, max_v))

TEX_DIR = os.path.abspath("godot_project/assets/characters/textures")

def create_pbr_material(name, base_color=(1, 1, 1, 1), roughness=0.5, metallic=0.0,
                        tex_diffuse_path=None, tex_normal_path=None, sss_weight=0.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    node_out = nodes.new(type='ShaderNodeOutputMaterial')
    node_bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    links.new(node_bsdf.outputs['BSDF'], node_out.inputs['Surface'])
    
    node_bsdf.inputs['Base Color'].default_value = base_color
    node_bsdf.inputs['Roughness'].default_value = roughness
    node_bsdf.inputs['Metallic'].default_value = metallic
    
    if sss_weight > 0.0:
        if 'Subsurface Weight' in node_bsdf.inputs:
            node_bsdf.inputs['Subsurface Weight'].default_value = sss_weight
        elif 'Subsurface' in node_bsdf.inputs:
            node_bsdf.inputs['Subsurface'].default_value = sss_weight
        if 'Subsurface Radius' in node_bsdf.inputs:
            node_bsdf.inputs['Subsurface Radius'].default_value = (0.04, 0.02, 0.01)
            
    if tex_diffuse_path and os.path.exists(tex_diffuse_path):
        tex_img = bpy.data.images.load(tex_diffuse_path)
        node_tex = nodes.new(type='ShaderNodeTexImage')
        node_tex.image = tex_img
        links.new(node_tex.outputs['Color'], node_bsdf.inputs['Base Color'])
        
    if tex_normal_path and os.path.exists(tex_normal_path):
        norm_img = bpy.data.images.load(tex_normal_path)
        norm_img.colorspace_settings.name = 'Non-Color'
        node_norm_img = nodes.new(type='ShaderNodeTexImage')
        node_norm_img.image = norm_img
        node_norm_map = nodes.new(type='ShaderNodeNormalMap')
        node_norm_map.inputs['Strength'].default_value = 1.0
        links.new(node_norm_img.outputs['Color'], node_norm_map.inputs['Color'])
        links.new(node_norm_map.outputs['Normal'], node_bsdf.inputs['Normal'])
        
    return mat

tex_face_diff = os.path.join(TEX_DIR, "axel_face_diffuse.png")
tex_face_norm = os.path.join(TEX_DIR, "axel_face_normal.png")
tex_hat_diff = os.path.join(TEX_DIR, "axel_hat_diffuse.png")
tex_hat_norm = os.path.join(TEX_DIR, "axel_hat_normal.png")
tex_eye_diff = os.path.join(TEX_DIR, "axel_eye_diffuse.png")

mat_skin = create_pbr_material("Mat_Axel_Skin", (0.80, 0.58, 0.46, 1.0), roughness=0.45,
                               tex_diffuse_path=tex_face_diff, tex_normal_path=tex_face_norm, sss_weight=0.35)
mat_hat = create_pbr_material("Mat_Axel_Hat", (0.08, 0.08, 0.09, 1.0), roughness=0.85,
                              tex_diffuse_path=tex_hat_diff, tex_normal_path=tex_hat_norm)
mat_hair = create_pbr_material("Mat_Axel_Hair", (0.08, 0.06, 0.05, 1.0), roughness=0.55, metallic=0.05)
mat_eyes = create_pbr_material("Mat_Axel_Eyes", (1, 1, 1, 1), roughness=0.05,
                               tex_diffuse_path=tex_eye_diff)

# =============================================================================
# CONSTRUCCIÓN DE LA CABEZA ESCULPIDA ANATÓMICAMENTE
# =============================================================================
mesh = bpy.data.meshes.new("Axel_Head_Mesh_Data")
obj = bpy.data.objects.new("Axel_Head", mesh)
bpy.context.scene.collection.objects.link(obj)

bm = bmesh.new()
uv_layer = bm.loops.layers.uv.new("UVMap")

# Coordenadas antropométricas (1.75m estándar):
# Cuello base: Z = 1.38
# Barbilla / mentón: Z = 1.44 (anchura 4.5 cm, proyección +Y = 0.048)
# Labios: Z = 1.48 (comisuras en ±0.024, arco de cupido central en Z = 1.488)
# Base de la nariz / subnasal: Z = 1.505
# Punta de la nariz: Z = 1.515 (proyección +Y = 0.080)
# Puente de la nariz: Z = 1.520 a 1.545 (proyección +Y = 0.068 a 0.060)
# Ojos (pupilas): Z = 1.540, X = ±0.033, Y = 0.050
# Arco superciliar / cejas: Z = 1.558
# Frente: Z = 1.565 a 1.630
# Coronilla: Z = 1.660

# 1. Malla Facial Quad-Loop Esculpida con Planos Asaro
# Definimos anillos anatómicos desde el cuello hasta la coronilla:
levels = [
    # (Z, Radio_X, Y_anterior, Y_posterior)
    (1.380, 0.046, 0.046, -0.046), # 0: Cuello base (collar)
    (1.410, 0.048, 0.052, -0.048), # 1: Cuello medio con nuez de Adán (+Y = 0.056 en centro)
    (1.435, 0.050, 0.054, -0.050), # 2: Mandíbula base / submentón
    (1.448, 0.048, 0.065, -0.052), # 3: Mentón cuadrado de Axel (+Y = 0.068 en centro)
    (1.465, 0.052, 0.060, -0.054), # 4: Surco mentolabial
    (1.478, 0.056, 0.068, -0.056), # 5: Labio inferior carnoso
    (1.488, 0.058, 0.066, -0.058), # 6: Labio superior y arco de Cupido
    (1.505, 0.062, 0.072, -0.060), # 7: Filtrum y base nasal / aletas
    (1.518, 0.066, 0.085, -0.062), # 8: Punta nasal y pómulos inferiores
    (1.535, 0.068, 0.074, -0.064), # 9: Puente nasal y pómulos altos prominentes
    (1.545, 0.067, 0.058, -0.066), # 10: Cuencas oculares y sellion nasal
    (1.560, 0.068, 0.070, -0.068), # 11: Arco superciliar / cejas masculinas
    (1.585, 0.069, 0.068, -0.070), # 12: Frente media
    (1.615, 0.068, 0.062, -0.070), # 13: Frente alta / nacimiento del pelo
    (1.645, 0.062, 0.048, -0.065), # 14: Bóveda craneal superior
    (1.665, 0.040, 0.028, -0.045), # 15: Coronilla
]

n_u = 32
head_grid = []

for lev_idx, (z, rx, yf, yb) in enumerate(levels):
    ring = []
    for ui in range(n_u):
        ang = (ui / float(n_u)) * 2.0 * math.pi - (math.pi / 2.0)
        sin_a = math.sin(ang)
        cos_a = math.cos(ang)
        
        # Coordenadas base elípticas
        vx = cos_a * rx
        vy = (sin_a * yf if sin_a >= 0 else sin_a * (-yb))
        vz = z
        
        # Modulaciones anatómicas específicas en cara anterior (+Y):
        if sin_a > 0:
            # Mentón cuadrado de Axel en nivel 3 (Z ~ 1.448)
            if lev_idx in [2, 3]:
                if abs(vx) < 0.022:
                    vy += 0.010 * (1.0 - (vx / 0.022)**2)
                    # Hendidura central para perilla
                    if abs(vx) < 0.005:
                        vy -= 0.002
            # Labios en niveles 5 y 6 (Z ~ 1.478 a 1.488)
            elif lev_idx in [5, 6]:
                if abs(vx) < 0.025:
                    w_l = 1.0 - abs(vx) / 0.025
                    cupid = 0.003 if (lev_idx == 6 and abs(vx) < 0.006) else 0.0
                    vy += (0.009 - cupid) * w_l
            # Nariz esculpida en niveles 7, 8, 9 (Z ~ 1.505 a 1.535)
            elif lev_idx == 8: # Punta nasal prominente
                if abs(vx) < 0.011:
                    vy += 0.014 * (1.0 - abs(vx) / 0.011)
                elif abs(vx) < 0.019: # Aletas nasales
                    vy += 0.006 * (1.0 - abs(abs(vx) - 0.015) / 0.005)
            elif lev_idx == 9: # Puente nasal aristocrático recto
                if abs(vx) < 0.008:
                    vy += 0.010 * (1.0 - abs(vx) / 0.008)
                # Pómulos altos angulares en los lados (X = ±0.046)
                elif 0.030 < abs(vx) < 0.060:
                    vy += 0.008 * (1.0 - abs(abs(vx) - 0.046) / 0.015)
            # Cuencas orbitales profundas en nivel 10 (Z ~ 1.545)
            elif lev_idx == 10:
                if 0.018 < abs(vx) < 0.048:
                    vy -= 0.012 * (1.0 - abs(abs(vx) - 0.033) / 0.015)
            # Arco superciliar en nivel 11 (Z ~ 1.560)
            elif lev_idx == 11:
                if abs(vx) < 0.050:
                    vy += 0.008 * (1.0 - (vx / 0.050)**2)
                    
        ring.append(bm.verts.new(Vector((vx, vy, vz))))
    head_grid.append(ring)

# Conectar cuadriláteros del cráneo
for r in range(len(head_grid) - 1):
    r0 = head_grid[r]
    r1 = head_grid[r + 1]
    v_coord0 = r / float(len(head_grid) - 1)
    v_coord1 = (r + 1) / float(len(head_grid) - 1)
    for i in range(n_u):
        nxt = (i + 1) % n_u
        f = bm.faces.new([r0[i], r0[nxt], r1[nxt], r1[i]])
        f.material_index = 0 # mat_skin
        
        u0 = 0.5 + math.atan2(r0[i].co.x, max(0.001, r0[i].co.y)) / (2.0 * math.pi)
        u1 = 0.5 + math.atan2(r0[nxt].co.x, max(0.001, r0[nxt].co.y)) / (2.0 * math.pi)
        u2 = 0.5 + math.atan2(r1[nxt].co.x, max(0.001, r1[nxt].co.y)) / (2.0 * math.pi)
        u3 = 0.5 + math.atan2(r1[i].co.x, max(0.001, r1[i].co.y)) / (2.0 * math.pi)
        for lp, u_val, v_val in zip(f.loops, [u0, u1, u2, u3], [v_coord0, v_coord0, v_coord1, v_coord1]):
            lp[uv_layer].uv = Vector((clampf(u_val, 0.0, 1.0), clampf(v_val, 0.0, 1.0)))

# Cierre superior
top_vh = bm.verts.new(Vector((0.0, -0.010, 1.675)))
for i in range(n_u):
    nxt = (i + 1) % n_u
    f = bm.faces.new([head_grid[-1][i], head_grid[-1][nxt], top_vh])
    f.material_index = 0
    for lp in f.loops:
        lp[uv_layer].uv = Vector((i / float(n_u), 1.0))

# 2. Globos Oculares 3D y Párpados Almendrados
for ex in [-0.033, 0.033]:
    p_eye = Vector((ex, 0.048, 1.542))
    sph = bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=12, radius=0.0125,
                                    matrix=Matrix.Translation(p_eye))
    for v in sph['verts']:
        for f in v.link_faces:
            f.material_index = 3 # mat_eyes
            for lp in f.loops:
                dx = (lp.vert.co.x - p_eye.x) / 0.0125
                dz = (lp.vert.co.z - p_eye.z) / 0.0125
                lp[uv_layer].uv = Vector((clampf(0.5 + dx * 0.5, 0.0, 1.0), clampf(0.5 + dz * 0.5, 0.0, 1.0)))

    # Párpado superior descansando sobre el iris (mirada humana segura y serena)
    sign_side = 1.0 if ex > 0 else -1.0
    lid_top_pts = [
        Vector((ex - 0.014 * sign_side, 0.055, 1.539)),
        Vector((ex - 0.007 * sign_side, 0.060, 1.547)),
        Vector((ex + 0.007 * sign_side, 0.060, 1.547)),
        Vector((ex + 0.014 * sign_side, 0.055, 1.541)),
        Vector((ex + 0.011 * sign_side, 0.058, 1.553)),
        Vector((ex + 0.000 * sign_side, 0.062, 1.556)),
        Vector((ex - 0.011 * sign_side, 0.058, 1.553)),
    ]
    lv_top = [bm.verts.new(p) for p in lid_top_pts]
    bm.faces.new([lv_top[0], lv_top[1], lv_top[6]]).material_index = 0
    bm.faces.new([lv_top[1], lv_top[2], lv_top[5], lv_top[6]]).material_index = 0
    bm.faces.new([lv_top[2], lv_top[3], lv_top[4], lv_top[5]]).material_index = 0

    lid_bot_pts = [
        Vector((ex - 0.013 * sign_side, 0.055, 1.539)),
        Vector((ex - 0.006 * sign_side, 0.059, 1.535)),
        Vector((ex + 0.006 * sign_side, 0.059, 1.535)),
        Vector((ex + 0.013 * sign_side, 0.055, 1.541)),
        Vector((ex + 0.010 * sign_side, 0.057, 1.529)),
        Vector((ex + 0.000 * sign_side, 0.060, 1.527)),
        Vector((ex - 0.010 * sign_side, 0.057, 1.529)),
    ]
    lv_bot = [bm.verts.new(p) for p in lid_bot_pts]
    bm.faces.new([lv_bot[0], lv_bot[1], lv_bot[6]]).material_index = 0
    bm.faces.new([lv_bot[1], lv_bot[2], lv_bot[5], lv_bot[6]]).material_index = 0
    bm.faces.new([lv_bot[2], lv_bot[3], lv_bot[4], lv_bot[5]]).material_index = 0

# 3. Orejas Anatómicas 3D
for sign_x in [-1.0, 1.0]:
    ear_pts = [
        Vector((sign_x * 0.068, -0.004, 1.562)), # Helix superior
        Vector((sign_x * 0.075, -0.016, 1.556)), # Helix posterior
        Vector((sign_x * 0.076, -0.020, 1.535)), # Antihelix medio
        Vector((sign_x * 0.072, -0.018, 1.515)), # Lóbulo inferior
        Vector((sign_x * 0.066, -0.008, 1.510)), # Base del lóbulo
        Vector((sign_x * 0.067,  0.004, 1.535)), # Trago anterior
        Vector((sign_x * 0.070, -0.010, 1.538)), # Fosa concha
    ]
    ev = [bm.verts.new(p) for p in ear_pts]
    bm.faces.new([ev[0], ev[1], ev[6], ev[5]]).material_index = 0
    bm.faces.new([ev[1], ev[2], ev[6]]).material_index = 0
    bm.faces.new([ev[2], ev[3], ev[6]]).material_index = 0
    bm.faces.new([ev[3], ev[4], ev[6]]).material_index = 0
    bm.faces.new([ev[4], ev[5], ev[6]]).material_index = 0

# 4. Cabello Rizado Tridimensional Auténtico de Axel (Espirales Helicoidales)
def add_curly_strand(bm, center_start, center_end, n_turns=2.4, radius_curl=0.0075,
                     thick=0.006, n_segs=14):
    strand_rings = []
    for s in range(n_segs + 1):
        t = s / float(n_segs)
        p_core = center_start.lerp(center_end, t)
        phase = t * n_turns * 2.0 * math.pi
        helix_offset = Vector((math.cos(phase) * radius_curl, math.sin(phase) * radius_curl * 0.65, 0.0))
        p_center = p_core + helix_offset
        cur_thick = thick * (1.0 - t * 0.40)
        rng = []
        for a in range(8):
            ang = (a / 8.0) * 2.0 * math.pi
            vx = p_center.x + math.cos(ang) * cur_thick
            vy = p_center.y + math.sin(ang) * cur_thick * 0.8
            vz = p_center.z + math.sin(ang + phase) * cur_thick * 0.3
            rng.append(bm.verts.new(Vector((vx, vy, vz))))
        strand_rings.append(rng)
        
    for i in range(len(strand_rings) - 1):
        r0 = strand_rings[i]
        r1 = strand_rings[i + 1]
        for a in range(8):
            an = (a + 1) % 8
            f = bm.faces.new([r0[a], r0[an], r1[an], r1[a]])
            f.material_index = 2 # mat_hair
            
    tip = bm.verts.new(strand_rings[-1][0].co.lerp(strand_rings[-1][4].co, 0.5) + Vector((0, 0, -thick * 0.5)))
    for a in range(8):
        an = (a + 1) % 8
        f = bm.faces.new([strand_rings[-1][a], strand_rings[-1][an], tip])
        f.material_index = 2

# Rizos cayendo naturalmente sobre la frente y sienes de Axel (Z = 1.590 a 1.545)
curls_specs = [
    # Flequillo sobre la frente (cayendo por debajo del ala del fedora)
    (Vector((-0.038, 0.070, 1.595)), Vector((-0.030, 0.076, 1.552)), 2.2, 0.008, 0.0065),
    (Vector((-0.024, 0.072, 1.598)), Vector((-0.016, 0.078, 1.548)), 2.6, 0.009, 0.0065),
    (Vector((-0.010, 0.074, 1.600)), Vector((-0.004, 0.080, 1.545)), 2.8, 0.009, 0.0070),
    (Vector(( 0.004, 0.074, 1.600)), Vector(( 0.010, 0.080, 1.546)), 2.8, 0.009, 0.0070),
    (Vector(( 0.018, 0.072, 1.598)), Vector(( 0.024, 0.078, 1.548)), 2.5, 0.009, 0.0065),
    (Vector(( 0.032, 0.070, 1.595)), Vector(( 0.038, 0.076, 1.552)), 2.2, 0.008, 0.0065),
    # Sienes y patillas
    (Vector((-0.066, 0.026, 1.585)), Vector((-0.070, 0.018, 1.525)), 2.4, 0.007, 0.006),
    (Vector((-0.064, 0.010, 1.575)), Vector((-0.068, 0.004, 1.515)), 2.2, 0.006, 0.0055),
    (Vector(( 0.066, 0.026, 1.585)), Vector(( 0.070, 0.018, 1.525)), 2.4, 0.007, 0.006),
    (Vector(( 0.064, 0.010, 1.575)), Vector(( 0.068, 0.004, 1.515)), 2.2, 0.006, 0.0055),
    # Nuca
    (Vector((-0.038, -0.062, 1.565)), Vector((-0.032, -0.058, 1.505)), 2.0, 0.007, 0.006),
    (Vector(( 0.038, -0.062, 1.565)), Vector(( 0.032, -0.058, 1.505)), 2.0, 0.007, 0.006),
]
for p1, p2, turns, r_c, th in curls_specs:
    add_curly_strand(bm, p1, p2, turns, r_c, th)

# 5. Sombrero Fedora de Fieltro Negro de Axel (Z = 1.580 a 1.685)
# Ala ancha de fieltro (Brim) con curvatura snap brim
n_brim_pts = 32
brim_inner = []
brim_outer = []

for i in range(n_brim_pts):
    ang = (i / float(n_brim_pts)) * 2.0 * math.pi
    cos_a = math.cos(ang)
    sin_a = math.sin(ang)
    dip_z = -0.018 * sin_a if sin_a > 0 else 0.012 * (-sin_a)
    
    rx_in = 0.076
    ry_in = 0.082
    vx_in = cos_a * rx_in
    vy_in = sin_a * ry_in - 0.008
    vz_in = 1.588 + dip_z * 0.4
    brim_inner.append(bm.verts.new(Vector((vx_in, vy_in, vz_in))))
    
    # Ala ancha elegante (14.5 cm de radio)
    rx_out = 0.142
    ry_out = 0.150
    vx_out = cos_a * rx_out
    vy_out = sin_a * ry_out - 0.008
    vz_out = 1.580 + dip_z
    brim_outer.append(bm.verts.new(Vector((vx_out, vy_out, vz_out))))

for i in range(n_brim_pts):
    nxt = (i + 1) % n_brim_pts
    f = bm.faces.new([brim_inner[i], brim_outer[i], brim_outer[nxt], brim_inner[nxt]])
    f.material_index = 1 # mat_hat

# Copa del Fedora (Crown): compacta, cónica con pinch front y lágrima
crown_levels = [
    (1.588, 0.076, 0.082, 0.0),    # Base (cinta grosgrain)
    (1.608, 0.074, 0.080, 0.0),    # Sobre cinta
    (1.635, 0.070, 0.076, 0.008),  # Pinch front inicial
    (1.662, 0.064, 0.070, 0.015),  # Pinch front medio
    (1.680, 0.056, 0.064, 0.020),  # Cresta superior
]
crown_rings = []
for z_c, rx_c, ry_c, pinch in crown_levels:
    c_ring = []
    for i in range(n_brim_pts):
        ang = (i / float(n_brim_pts)) * 2.0 * math.pi
        cos_a = math.cos(ang)
        sin_a = math.sin(ang)
        vx = cos_a * rx_c
        vy = sin_a * ry_c - 0.008
        vz = z_c
        if sin_a > 0.3 and abs(cos_a) > 0.2:
            vx *= (1.0 - pinch * 0.7)
        c_ring.append(bm.verts.new(Vector((vx, vy, vz))))
    crown_rings.append(c_ring)

for r in range(len(crown_rings) - 1):
    r0 = crown_rings[r]
    r1 = crown_rings[r + 1]
    for i in range(n_brim_pts):
        nxt = (i + 1) % n_brim_pts
        f = bm.faces.new([r0[i], r0[nxt], r1[nxt], r1[i]])
        f.material_index = 1

top_crease = []
for i in range(n_brim_pts):
    ang = (i / float(n_brim_pts)) * 2.0 * math.pi
    cos_a = math.cos(ang)
    sin_a = math.sin(ang)
    vx = cos_a * 0.035
    vy = sin_a * 0.042 - 0.008
    vz = 1.668 - (0.015 * (1.0 - min(1.0, abs(cos_a) * 1.5)))
    top_crease.append(bm.verts.new(Vector((vx, vy, vz))))

for i in range(n_brim_pts):
    nxt = (i + 1) % n_brim_pts
    f = bm.faces.new([crown_rings[-1][i], crown_rings[-1][nxt], top_crease[nxt], top_crease[i]])
    f.material_index = 1

center_top = bm.verts.new(Vector((0.0, -0.008, 1.654)))
for i in range(n_brim_pts):
    nxt = (i + 1) % n_brim_pts
    f = bm.faces.new([top_crease[i], top_crease[nxt], center_top])
    f.material_index = 1

bm.verts.index_update()
bm.to_mesh(mesh)
bm.free()

obj.data.materials.append(mat_skin) # 0
obj.data.materials.append(mat_hat)  # 1
obj.data.materials.append(mat_hair) # 2
obj.data.materials.append(mat_eyes) # 3

for poly in mesh.polygons:
    poly.use_smooth = True

# Subsurf para acabado orgánico Fortnite AAA
mod_sub = obj.modifiers.new(name="Subsurf", type='SUBSURF')
mod_sub.levels = 1

# Cámara de retrato Close-up centrada en el rostro de Axel
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 48
scene.cycles.device = 'CPU'
scene.render.resolution_x = 720
scene.render.resolution_y = 1080

cam_data = bpy.data.cameras.new("PortraitCam")
cam_data.lens = 70.0 # Lente retrato suave para resaltar planos faciales
cam_obj = bpy.data.objects.new("PortraitCam", cam_data)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj

# Encuadre a la altura de los ojos (Z = 1.54) con ligera inclinación frontal
cam_obj.location = Vector((0.05, 0.95, 1.54))
cam_obj.rotation_euler = (math.radians(88.0), 0.0, math.radians(177.0))

# Iluminación de estudio retrato
key = bpy.data.lights.new("Key", type='AREA')
key.energy = 65.0
key.size = 0.8
key.color = (1.0, 0.97, 0.94)
key_obj = bpy.data.objects.new("Key", key)
key_obj.location = Vector((-0.45, 0.70, 1.75))
key_obj.rotation_euler = (math.radians(45.0), 0.0, math.radians(-150.0))
scene.collection.objects.link(key_obj)

fill = bpy.data.lights.new("Fill", type='AREA')
fill.energy = 28.0
fill.size = 1.2
fill.color = (0.92, 0.96, 1.0)
fill_obj = bpy.data.objects.new("Fill", fill)
fill_obj.location = Vector((0.55, 0.75, 1.50))
scene.collection.objects.link(fill_obj)

rim = bpy.data.lights.new("Rim", type='SPOT')
rim.energy = 40.0
rim.spot_size = math.radians(55.0)
rim_obj = bpy.data.objects.new("Rim", rim)
rim_obj.location = Vector((0.0, -0.8, 1.85))
rim_obj.rotation_euler = (math.radians(-50.0), 0.0, 0.0)
scene.collection.objects.link(rim_obj)

render_out = os.path.abspath("scratch/test_axel_face_render.png")
scene.render.filepath = render_out
bpy.ops.render.render(write_still=True)
print(f"✓ Render retrato guardado en: {render_out}")
