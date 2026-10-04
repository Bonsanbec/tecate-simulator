"""
Test anatómico con mandíbula real, plano submandibular retrasado, ojos integrados y fedora curvo
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
# Sombrero negro azabache mate
mat_hat = create_pbr_material("Mat_Axel_Hat", (0.03, 0.03, 0.035, 1.0), roughness=0.92,
                              tex_normal_path=tex_hat_norm)
mat_hair = create_pbr_material("Mat_Axel_Hair", (0.05, 0.04, 0.035, 1.0), roughness=0.55, metallic=0.05)
mat_eyes = create_pbr_material("Mat_Axel_Eyes", (1, 1, 1, 1), roughness=0.05,
                               tex_diffuse_path=tex_eye_diff)

mesh = bpy.data.meshes.new("Axel_Head_Mesh_Data")
obj = bpy.data.objects.new("Axel_Head", mesh)
bpy.context.scene.collection.objects.link(obj)

bm = bmesh.new()
uv_layer = bm.loops.layers.uv.new("UVMap")

# Anillos anatómicos con cuello retrasado (Y_centro del cuello en -0.015 m):
# Cuello base: Z = 1.38, Yc = -0.015, r = 0.044 -> Y_ant = +0.029, Y_post = -0.059
# Garganta / Adán: Z = 1.41, Yc = -0.012, r = 0.044 -> Y_ant = +0.032 (+ nuez = +0.038)
# Submentón: Z = 1.435, Y_ant se retrae a +0.028 mientras la mandíbula se proyecta
# Barbilla / mentón: Z = 1.450, Y_ant = +0.075! (4.7 cm por delante de la garganta)
levels = [
    # (Z, Radio_X, Y_anterior, Y_posterior, Y_centro)
    (1.380, 0.045, 0.030, 0.055, -0.012), # 0: Cuello base
    (1.410, 0.046, 0.036, 0.055, -0.010), # 1: Nuez de Adán (+Y = 0.040 en centro)
    (1.432, 0.048, 0.038, 0.056, -0.008), # 2: Submentón y base del hioides
    (1.450, 0.055, 0.075, 0.058,  0.000), # 3: Mentón cuadrado prominente de Axel (+Y = 0.076)
    (1.468, 0.058, 0.068, 0.060,  0.000), # 4: Surco mentolabial
    (1.482, 0.062, 0.076, 0.062,  0.000), # 5: Labio inferior carnoso
    (1.492, 0.064, 0.074, 0.064,  0.000), # 6: Labio superior y arco de Cupido
    (1.508, 0.068, 0.080, 0.066,  0.000), # 7: Filtrum y base nasal / aletas
    (1.520, 0.072, 0.092, 0.068,  0.000), # 8: Punta nasal (+Y = 0.092) y pómulos inferiores
    (1.536, 0.074, 0.082, 0.070,  0.000), # 9: Puente nasal recto y pómulos altos prominentes
    (1.546, 0.073, 0.066, 0.070,  0.000), # 10: Cuencas orbitales recesadas y sellion nasal
    (1.562, 0.074, 0.078, 0.072,  0.000), # 11: Arco superciliar / cejas masculinas
    (1.585, 0.075, 0.074, 0.072, -0.005), # 12: Frente media
    (1.615, 0.072, 0.066, 0.070, -0.008), # 13: Nacimiento del cabello
    (1.642, 0.065, 0.050, 0.064, -0.012), # 14: Bóveda craneal
    (1.662, 0.042, 0.030, 0.045, -0.015), # 15: Coronilla
]

n_u = 32
head_grid = []

for lev_idx, (z, rx, yf, yb, yc) in enumerate(levels):
    ring = []
    for ui in range(n_u):
        ang = (ui / float(n_u)) * 2.0 * math.pi - (math.pi / 2.0)
        sin_a = math.sin(ang)
        cos_a = math.cos(ang)
        
        vx = cos_a * rx
        vy = yc + (sin_a * yf if sin_a >= 0 else sin_a * (-yb))
        vz = z
        
        if sin_a > 0:
            # Mentón cuadrado en nivel 3
            if lev_idx == 3:
                if abs(vx) < 0.024:
                    vy += 0.008 * (1.0 - (vx / 0.024)**2)
                    if abs(vx) < 0.005:
                        vy -= 0.002 # Hoyuelo central
            # Labios en niveles 5 y 6
            elif lev_idx in [5, 6]:
                if abs(vx) < 0.026:
                    w_l = 1.0 - abs(vx) / 0.026
                    cupid = 0.003 if (lev_idx == 6 and abs(vx) < 0.006) else 0.0
                    vy += (0.008 - cupid) * w_l
            # Nariz en niveles 7, 8, 9
            elif lev_idx == 8:
                if abs(vx) < 0.012:
                    vy += 0.012 * (1.0 - abs(vx) / 0.012)
                elif abs(vx) < 0.020:
                    vy += 0.005 * (1.0 - abs(abs(vx) - 0.016) / 0.005)
            elif lev_idx == 9:
                if abs(vx) < 0.009:
                    vy += 0.009 * (1.0 - abs(vx) / 0.009)
                elif 0.035 < abs(vx) < 0.065:
                    vy += 0.009 * (1.0 - abs(abs(vx) - 0.050) / 0.015) # Pómulos altos
            # Cuencas orbitales recesadas en nivel 10
            elif lev_idx == 10:
                if 0.018 < abs(vx) < 0.048:
                    vy -= 0.014 * (1.0 - abs(abs(vx) - 0.033) / 0.015)
            # Arco superciliar en nivel 11
            elif lev_idx == 11:
                if abs(vx) < 0.052:
                    vy += 0.007 * (1.0 - (vx / 0.052)**2)
                    
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

# Coronilla
top_vh = bm.verts.new(Vector((0.0, -0.015, 1.670)))
for i in range(n_u):
    nxt = (i + 1) % n_u
    f = bm.faces.new([head_grid[-1][i], head_grid[-1][nxt], top_vh])
    f.material_index = 0
    for lp in f.loops:
        lp[uv_layer].uv = Vector((i / float(n_u), 1.0))

# 2. Globos Oculares 3D dentro de las cuencas (Z = 1.545, Y = 0.052)
for ex in [-0.033, 0.033]:
    p_eye = Vector((ex, 0.052, 1.545))
    sph = bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=12, radius=0.0125,
                                    matrix=Matrix.Translation(p_eye))
    for v in sph['verts']:
        for f in v.link_faces:
            f.material_index = 3 # mat_eyes
            for lp in f.loops:
                dx = (lp.vert.co.x - p_eye.x) / 0.0125
                dz = (lp.vert.co.z - p_eye.z) / 0.0125
                lp[uv_layer].uv = Vector((clampf(0.5 + dx * 0.5, 0.0, 1.0), clampf(0.5 + dz * 0.5, 0.0, 1.0)))

# 3. Orejas 3D integradas
for sign_x in [-1.0, 1.0]:
    ear_pts = [
        Vector((sign_x * 0.074, -0.004, 1.562)),
        Vector((sign_x * 0.080, -0.018, 1.556)),
        Vector((sign_x * 0.082, -0.022, 1.535)),
        Vector((sign_x * 0.078, -0.020, 1.515)),
        Vector((sign_x * 0.072, -0.008, 1.510)),
        Vector((sign_x * 0.073,  0.004, 1.535)),
        Vector((sign_x * 0.076, -0.012, 1.538)),
    ]
    ev = [bm.verts.new(p) for p in ear_pts]
    bm.faces.new([ev[0], ev[1], ev[6], ev[5]]).material_index = 0
    bm.faces.new([ev[1], ev[2], ev[6]]).material_index = 0
    bm.faces.new([ev[2], ev[3], ev[6]]).material_index = 0
    bm.faces.new([ev[3], ev[4], ev[6]]).material_index = 0
    bm.faces.new([ev[4], ev[5], ev[6]]).material_index = 0

# 4. Ramilletes de Cabello Rizado 3D de Axel (debajo del sombrero)
def add_curly_strand(bm, center_start, center_end, n_turns=2.4, radius_curl=0.008,
                     thick=0.0065, n_segs=14):
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

# Rizos cayendo naturalmente bajo el ala del fedora
curls_specs = [
    # Flequillo sobre la frente (Z = 1.585 a 1.545)
    (Vector((-0.038, 0.074, 1.585)), Vector((-0.030, 0.082, 1.548)), 2.2, 0.008, 0.0065),
    (Vector((-0.024, 0.076, 1.588)), Vector((-0.016, 0.084, 1.544)), 2.6, 0.009, 0.0065),
    (Vector((-0.010, 0.078, 1.590)), Vector((-0.004, 0.086, 1.542)), 2.8, 0.009, 0.0070),
    (Vector(( 0.004, 0.078, 1.590)), Vector(( 0.010, 0.086, 1.543)), 2.8, 0.009, 0.0070),
    (Vector(( 0.018, 0.076, 1.588)), Vector(( 0.024, 0.084, 1.544)), 2.5, 0.009, 0.0065),
    (Vector(( 0.032, 0.074, 1.585)), Vector(( 0.038, 0.082, 1.548)), 2.2, 0.008, 0.0065),
    # Sienes y patillas
    (Vector((-0.070, 0.028, 1.580)), Vector((-0.074, 0.020, 1.525)), 2.4, 0.007, 0.006),
    (Vector((-0.068, 0.012, 1.570)), Vector((-0.072, 0.006, 1.515)), 2.2, 0.006, 0.0055),
    (Vector(( 0.070, 0.028, 1.580)), Vector(( 0.074, 0.020, 1.525)), 2.4, 0.007, 0.006),
    (Vector(( 0.068, 0.012, 1.570)), Vector(( 0.072, 0.006, 1.515)), 2.2, 0.006, 0.0055),
]
for p1, p2, turns, r_c, th in curls_specs:
    add_curly_strand(bm, p1, p2, turns, r_c, th)

# 5. Sombrero Fedora de Fieltro Negro Auténtico (Ala ancha curva + Copa estilizada)
# El ala se apoya en Z = 1.595 (sobre las cejas y sienes)
n_brim = 32
brim_inner = []
brim_outer = []

for i in range(n_brim):
    ang = (i / float(n_brim)) * 2.0 * math.pi
    cos_a = math.cos(ang)
    sin_a = math.sin(ang)
    
    # Snap brim clásico: desciende suavemente al frente y sube a los lados/espalda
    dip_z = -0.016 * sin_a if sin_a > 0 else 0.012 * (-sin_a)
    
    rx_in = 0.078
    ry_in = 0.084
    vx_in = cos_a * rx_in
    vy_in = sin_a * ry_in - 0.005
    vz_in = 1.596 + dip_z * 0.4
    brim_inner.append(bm.verts.new(Vector((vx_in, vy_in, vz_in))))
    
    # Ala ancha elegante (14.5 cm de radio exterior)
    rx_out = 0.145
    ry_out = 0.152
    vx_out = cos_a * rx_out
    vy_out = sin_a * ry_out - 0.005
    vz_out = 1.588 + dip_z
    brim_outer.append(bm.verts.new(Vector((vx_out, vy_out, vz_out))))

for i in range(n_brim):
    nxt = (i + 1) % n_brim
    f = bm.faces.new([brim_inner[i], brim_outer[i], brim_outer[nxt], brim_inner[nxt]])
    f.material_index = 1 # mat_hat

# Copa compacta estilizada (Z de 1.596 a 1.675)
crown_levels = [
    (1.596, 0.078, 0.084, 0.0),    # Base (cinta grosgrain)
    (1.615, 0.075, 0.081, 0.0),    # Sobre cinta
    (1.638, 0.070, 0.076, 0.008),  # Pinch front
    (1.658, 0.064, 0.070, 0.016),  # Pellizco medio
    (1.675, 0.055, 0.062, 0.022),  # Borde superior
]
crown_rings = []
for z_c, rx_c, ry_c, pinch in crown_levels:
    c_ring = []
    for i in range(n_brim):
        ang = (i / float(n_brim)) * 2.0 * math.pi
        cos_a = math.cos(ang)
        sin_a = math.sin(ang)
        vx = cos_a * rx_c
        vy = sin_a * ry_c - 0.005
        vz = z_c
        if sin_a > 0.3 and abs(cos_a) > 0.2:
            vx *= (1.0 - pinch * 0.75)
        c_ring.append(bm.verts.new(Vector((vx, vy, vz))))
    crown_rings.append(c_ring)

for r in range(len(crown_rings) - 1):
    r0 = crown_rings[r]
    r1 = crown_rings[r + 1]
    for i in range(n_brim):
        nxt = (i + 1) % n_brim
        f = bm.faces.new([r0[i], r0[nxt], r1[nxt], r1[i]])
        f.material_index = 1

# Hendidura longitudinal en lágrima en la copa superior
top_crease = []
for i in range(n_brim):
    ang = (i / float(n_brim)) * 2.0 * math.pi
    cos_a = math.cos(ang)
    sin_a = math.sin(ang)
    vx = cos_a * 0.034
    vy = sin_a * 0.040 - 0.005
    vz = 1.662 - (0.014 * (1.0 - min(1.0, abs(cos_a) * 1.5)))
    top_crease.append(bm.verts.new(Vector((vx, vy, vz))))

for i in range(n_brim):
    nxt = (i + 1) % n_brim
    f = bm.faces.new([crown_rings[-1][i], crown_rings[-1][nxt], top_crease[nxt], top_crease[i]])
    f.material_index = 1

center_top = bm.verts.new(Vector((0.0, -0.005, 1.650)))
for i in range(n_brim):
    nxt = (i + 1) % n_brim
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

mod_sub = obj.modifiers.new(name="Subsurf", type='SUBSURF')
mod_sub.levels = 1

# Cámara de retrato Close-up centrada en el rostro
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 48
scene.cycles.device = 'CPU'
scene.render.resolution_x = 720
scene.render.resolution_y = 1080

cam_data = bpy.data.cameras.new("PortraitCam")
cam_data.lens = 65.0
cam_obj = bpy.data.objects.new("PortraitCam", cam_data)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj

# Encuadre a la altura de los ojos (Z = 1.54) con suave ángulo semi-perfil (como en la foto de Axel)
cam_obj.location = Vector((0.18, 0.95, 1.53))
cam_obj.rotation_euler = (math.radians(88.0), 0.0, math.radians(169.0))

# Iluminación de estudio
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

render_out = os.path.abspath("scratch/test_head_v4_render.png")
scene.render.filepath = render_out
bpy.ops.render.render(write_still=True)
print(f"✓ Render retrato guardado en: {render_out}")
