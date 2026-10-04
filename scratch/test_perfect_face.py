"""
Prueba de modelado facial hiperrealista y armónico para Axel:
- Labios 3D con volumen anatómico y arco de Cupido (sin rectángulos de material)
- Nariz 3D con puente esculpido, punta redondeada y aletas nasales
- Cuencas orbitarias con globos oculares 3D, párpados envolventes y cejas arqueadas
- Cabello ondulado estilizado con rizos orgánicos y patillas
- Gorro beanie que abraza el cráneo con dobladillo acanalado en relieve
- Piel con tono apiñonado homogéneo y dispersión subsuperficial (SSS)
"""
import bpy
import bmesh
import math
import os
from mathutils import Vector, Matrix

def clean_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh, do_unlink=True)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat, do_unlink=True)

clean_scene()

def create_mat(name, color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = color
        bsdf.inputs['Roughness'].default_value = roughness
        bsdf.inputs['Metallic'].default_value = metallic
    return mat

mesh = bpy.data.meshes.new("Head_Perfect_Mesh")
bm = bmesh.new()

# Materiales:
# 0: Piel (Skin)
# 1: Beanie (Verde oliva)
# 2: Cabello (Castaño oscuro)
# 3: Ojos (Esclera/Iris/Pupila)
# 4: Cejas (Pelo oscuro)
# 5: Labios (Bermellón suave con volumen 3D)

# 1. Base del Cráneo y Cuello (Manifold, piel homogénea)
u_segs = 32
v_rings = 24
grid = []

for vi in range(v_rings + 1):
    tv = vi / float(v_rings)
    if tv < 0.22: # Cuello esbelto
        z = 1.460 + (tv / 0.22) * 0.065
        rx = 0.048
        ry_f = 0.050
        ry_b = 0.048
        yc = 0.004
    elif tv < 0.50: # Mandíbula y mentón
        tj = (tv - 0.22) / 0.28
        z = 1.525 + tj * 0.055
        rx = 0.052 + tj * 0.016
        ry_f = 0.062 + tj * 0.016
        ry_b = 0.050 + tj * 0.016
        yc = 0.002
    elif tv < 0.78: # Nariz, mejillas y ojos
        tm = (tv - 0.50) / 0.28
        z = 1.580 + tm * 0.055
        rx = 0.068 + tm * 0.006
        ry_f = 0.076
        ry_b = 0.066 + tm * 0.008
        yc = 0.0
    else: # Frente y cráneo
        tt = (tv - 0.78) / 0.22
        z = 1.635 + tt * 0.075
        dome = math.sqrt(max(0.01, 1.0 - (tt * 0.94)**2))
        rx = 0.074 * dome + 0.003
        ry_f = 0.076 * dome + 0.003
        ry_b = 0.076 * dome + 0.003
        yc = -0.008 * tt

    ring = []
    for ui in range(u_segs):
        ang = (ui / float(u_segs)) * 2.0 * math.pi - (math.pi / 2.0)
        sin_a = math.sin(ang)
        cos_a = math.cos(ang)
        vx = cos_a * rx
        vy = yc + (sin_a * ry_f if sin_a >= 0 else sin_a * ry_b)
        vz = z

        if sin_a > 0:
            # Mentón suave
            if abs(vz - 1.535) < 0.020 and abs(vx) < 0.026:
                cd = math.sqrt((vx / 0.026)**2 + ((vz - 1.535) / 0.020)**2)
                if cd < 1.0:
                    vy += 0.014 * (1.0 - cd)**2
            # Surco mentolabial
            if abs(vz - 1.548) < 0.008 and abs(vx) < 0.022:
                vy -= 0.004 * (1.0 - abs(vx) / 0.022)
            # Nariz 3D continua: puente y punta redondeada
            if 1.570 < vz < 1.625 and abs(vx) < 0.022:
                tn = (vz - 1.570) / 0.055
                nw = 0.010 + (1.0 - tn) * 0.010
                if abs(vx) < nw:
                    lf = 1.0 - (abs(vx) / nw)
                    n_proj = 0.026 * math.sin(tn * math.pi * 0.85) if tn < 0.40 else 0.016 + (1.0 - tn) * 0.010
                    vy += n_proj * (lf**1.4)
            # Cuencas de ojos
            for ecx in [-0.032, 0.032]:
                de = math.sqrt(((vx - ecx) / 0.018)**2 + ((vz - 1.618) / 0.014)**2)
                if de < 1.0:
                    vy -= 0.011 * (1.0 - de)**2
            # Nuez de Adán
            if abs(vz - 1.490) < 0.012 and abs(vx) < 0.012:
                vy += 0.005 * (1.0 - abs(vx) / 0.012)

        ring.append(bm.verts.new(Vector((vx, vy, vz))))
    grid.append(ring)

# Caras de la cabeza (Toda la piel es material 0: suave y uniforme)
for vi in range(v_rings):
    r0 = grid[vi]
    r1 = grid[vi + 1]
    for ui in range(u_segs):
        un = (ui + 1) % u_segs
        f = bm.faces.new([r0[ui], r0[un], r1[un], r1[ui]])
        f.material_index = 0

top_vh = bm.verts.new(Vector((0.0, -0.008, 1.715)))
for ui in range(u_segs):
    un = (ui + 1) % u_segs
    f = bm.faces.new([grid[-1][ui], grid[-1][un], top_vh])
    f.material_index = 0

# 2. Labios 3D Anatómicos Esculpidos (Arco de Cupido, volumen vermellón y comisuras)
# Modelados como geometría 3D suave con volumen orgánico
def add_sculpted_lips(bm):
    # Puntos del arco superior (Cupid's bow)
    lip_top_pts = [
        Vector(( 0.000, 0.076, 1.564)), # Centro hendidura Cupido
        Vector((-0.008, 0.078, 1.566)), # Pico izq Cupido
        Vector(( 0.008, 0.078, 1.566)), # Pico der Cupido
        Vector((-0.018, 0.072, 1.561)), # Borde lateral izq
        Vector(( 0.018, 0.072, 1.561)), # Borde lateral der
        Vector((-0.024, 0.068, 1.558)), # Comisura izq
        Vector(( 0.024, 0.068, 1.558)), # Comisura der
        # Línea de cierre bucal
        Vector(( 0.000, 0.077, 1.558)), # Centro hendidura cierre
        Vector((-0.010, 0.076, 1.558)),
        Vector(( 0.010, 0.076, 1.558)),
        # Labio inferior (cuerpo redondeado carnoso)
        Vector(( 0.000, 0.079, 1.550)), # Centro labio inferior
        Vector((-0.010, 0.077, 1.551)), # Medio labio inf izq
        Vector(( 0.010, 0.077, 1.551)), # Medio labio inf der
        Vector((-0.018, 0.072, 1.554)),
        Vector(( 0.018, 0.072, 1.554)),
    ]
    lv = [bm.verts.new(p) for p in lip_top_pts]
    # Caras del labio superior
    f_sup1 = bm.faces.new([lv[0], lv[1], lv[8], lv[7]])
    f_sup2 = bm.faces.new([lv[0], lv[7], lv[9], lv[2]])
    f_sup3 = bm.faces.new([lv[1], lv[3], lv[5], lv[8]])
    f_sup4 = bm.faces.new([lv[2], lv[9], lv[6], lv[4]])
    # Caras del labio inferior
    f_inf1 = bm.faces.new([lv[7], lv[8], lv[11], lv[10]])
    f_inf2 = bm.faces.new([lv[7], lv[10], lv[12], lv[9]])
    f_inf3 = bm.faces.new([lv[8], lv[5], lv[13], lv[11]])
    f_inf4 = bm.faces.new([lv[9], lv[12], lv[14], lv[6]])

    for f in [f_sup1, f_sup2, f_sup3, f_sup4, f_inf1, f_inf2, f_inf3, f_inf4]:
        f.material_index = 5 # mat_lips

add_sculpted_lips(bm)

# 3. Globos Oculares 3D en Cuencas (Z=1.618, X=+/-0.032)
for ex in [-0.032, 0.032]:
    p_eye = Vector((ex, 0.066, 1.618))
    sph = bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=12, radius=0.0125, matrix=Matrix.Translation(p_eye))
    for v in sph['verts']:
        for f in v.link_faces:
            f.material_index = 3 # ojos

    # Párpado superior e inferior
    etop = [
        Vector((ex - 0.014, 0.070, 1.616)),
        Vector((ex - 0.006, 0.076, 1.626)),
        Vector((ex + 0.006, 0.076, 1.626)),
        Vector((ex + 0.014, 0.070, 1.616)),
        Vector((ex + 0.016, 0.073, 1.622)),
        Vector((ex + 0.007, 0.079, 1.631)),
        Vector((ex - 0.007, 0.079, 1.631)),
        Vector((ex - 0.016, 0.073, 1.622)),
    ]
    ev = [bm.verts.new(p) for p in etop]
    f1 = bm.faces.new([ev[0], ev[1], ev[6], ev[7]])
    f2 = bm.faces.new([ev[1], ev[2], ev[5], ev[6]])
    f3 = bm.faces.new([ev[2], ev[3], ev[4], ev[5]])
    for ff in [f1, f2, f3]:
        ff.material_index = 0

    # Cejas 3D
    sb = -1.0 if ex < 0 else 1.0
    bpts = [
        Vector((ex - sb * 0.015, 0.073, 1.634)),
        Vector((ex - sb * 0.004, 0.078, 1.642)),
        Vector((ex + sb * 0.010, 0.077, 1.640)),
        Vector((ex + sb * 0.018, 0.072, 1.634)),
        Vector((ex + sb * 0.016, 0.073, 1.638)),
        Vector((ex + sb * 0.008, 0.080, 1.646)),
        Vector((ex - sb * 0.004, 0.081, 1.647)),
        Vector((ex - sb * 0.013, 0.075, 1.639)),
    ]
    bv = [bm.verts.new(p) for p in bpts]
    bf1 = bm.faces.new([bv[0], bv[1], bv[6], bv[7]])
    bf2 = bm.faces.new([bv[1], bv[2], bv[5], bv[6]])
    bf3 = bm.faces.new([bv[2], bv[3], bv[4], bv[5]])
    for bf in [bf1, bf2, bf3]:
        bf.material_index = 4

# Orejas
for ear_x, ear_sgn in [(-0.070, -1.0), (0.070, 1.0)]:
    p_ear = Vector((ear_x, 0.002, 1.605))
    sph_ear = bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=8, radius=0.014, matrix=Matrix.Translation(p_ear))
    for v in sph_ear['verts']:
        v.co.x = ear_x + (v.co.x - ear_x) * 0.38
        v.co.y = 0.002 + (v.co.y - 0.002) * 0.85
        v.co.z = 1.605 + (v.co.z - 1.605) * 1.25
        for f in v.link_faces:
            f.material_index = 0

# 4. Mechones 3D de Cabello Ondulado (Axel Bangs)
def add_hair_curl(bm, p_start, p_mid, p_end, width, thick):
    pts = [p_start, p_mid, p_end]
    scale_w = [width, width * 0.85, width * 0.3]
    scale_t = [thick, thick * 0.80, thick * 0.3]
    c_rings = []
    for pt, w, t in zip(pts, scale_w, scale_t):
        rng = []
        for a in range(8):
            ang = (2.0 * math.pi * a) / 8.0
            vx = pt.x + math.cos(ang) * w
            vy = pt.y + math.sin(ang) * t * 0.7
            vz = pt.z - math.sin(ang) * t * 0.4
            rng.append(bm.verts.new(Vector((vx, vy, vz))))
        c_rings.append(rng)
    for i in range(len(c_rings) - 1):
        r0 = c_rings[i]
        r1 = c_rings[i + 1]
        for a in range(8):
            an = (a + 1) % 8
            f = bm.faces.new([r0[a], r0[an], r1[an], r1[a]])
            f.material_index = 2
    tip = bm.verts.new(pts[-1] + Vector((0, 0, -thick * 0.4)))
    for a in range(8):
        an = (a + 1) % 8
        f = bm.faces.new([c_rings[-1][a], c_rings[-1][an], tip])
        f.material_index = 2

curls = [
    (Vector((-0.038, 0.074, 1.660)), Vector((-0.030, 0.082, 1.646)), Vector((-0.020, 0.083, 1.630)), 0.012, 0.008),
    (Vector((-0.020, 0.078, 1.664)), Vector((-0.012, 0.086, 1.648)), Vector((-0.004, 0.086, 1.628)), 0.013, 0.009),
    (Vector((-0.002, 0.080, 1.664)), Vector(( 0.005, 0.086, 1.648)), Vector(( 0.012, 0.086, 1.628)), 0.013, 0.009),
    (Vector(( 0.016, 0.079, 1.664)), Vector(( 0.022, 0.085, 1.648)), Vector(( 0.028, 0.085, 1.630)), 0.013, 0.009),
    (Vector(( 0.030, 0.075, 1.660)), Vector(( 0.036, 0.081, 1.646)), Vector(( 0.040, 0.082, 1.632)), 0.012, 0.008),
    # Patillas
    (Vector((-0.068, 0.022, 1.655)), Vector((-0.070, 0.020, 1.625)), Vector((-0.068, 0.016, 1.595)), 0.010, 0.007),
    (Vector(( 0.068, 0.022, 1.655)), Vector(( 0.070, 0.020, 1.625)), Vector(( 0.068, 0.016, 1.595)), 0.010, 0.007),
    # Nuca
    (Vector((-0.028, -0.066, 1.655)), Vector((-0.028, -0.062, 1.615)), Vector((-0.026, -0.058, 1.580)), 0.011, 0.008),
    (Vector(( 0.000, -0.068, 1.655)), Vector(( 0.000, -0.064, 1.615)), Vector(( 0.000, -0.060, 1.578)), 0.012, 0.008),
    (Vector(( 0.028, -0.066, 1.655)), Vector(( 0.028, -0.062, 1.615)), Vector(( 0.026, -0.058, 1.580)), 0.011, 0.008),
]
for p1, p2, p3, w, t in curls:
    add_hair_curl(bm, p1, p2, p3, w, t)

# 5. Beanie de Lana Verde Oliva Ajustado y Redondeado
# Enmarca la cabeza de forma natural (Z=1.638 a 1.745)
beanie_levels = [
    # (zf, zb, rx, ry, rib)
    (1.642, 1.610, 0.082, 0.086, 0.0035),
    (1.660, 1.628, 0.087, 0.091, 0.0045),
    (1.678, 1.646, 0.084, 0.088, 0.0025),
    (1.700, 1.672, 0.080, 0.084, 0.0000),
    (1.720, 1.696, 0.068, 0.072, 0.0000),
    (1.736, 1.718, 0.050, 0.054, 0.0000),
    (1.746, 1.734, 0.024, 0.026, 0.0000),
]
b_rings = []
for zf, zb, rx, ry, rib_amp in beanie_levels:
    br = []
    for i in range(28):
        ang = (2.0 * math.pi * i) / 28.0
        cos_a = math.cos(ang)
        sin_a = math.sin(ang)
        t_fb = (cos_a + 1.0) * 0.5
        z = zb * (1.0 - t_fb) + zf * t_fb
        rib = math.sin(i * 4.0 * math.pi) * rib_amp if rib_amp > 0 else 0.0
        vx = sin_a * (rx + rib)
        vy = (cos_a * ry) - 0.008 * (1.0 - t_fb)
        br.append(bm.verts.new(Vector((vx, vy, z))))
    b_rings.append(br)

for r in range(len(b_rings) - 1):
    r0 = b_rings[r]
    r1 = b_rings[r + 1]
    for i in range(28):
        in_idx = (i + 1) % 28
        f = bm.faces.new([r0[i], r0[in_idx], r1[in_idx], r1[i]])
        f.material_index = 1

top_b = bm.verts.new(Vector((0.0, -0.012, 1.750)))
for i in range(28):
    in_idx = (i + 1) % 28
    f = bm.faces.new([b_rings[-1][i], b_rings[-1][in_idx], top_b])
    f.material_index = 1

bm.to_mesh(mesh)
bm.free()

obj = bpy.data.objects.new("Player_Head_Mesh", mesh)
bpy.context.scene.collection.objects.link(obj)

m_skin = create_mat("Mat_Axel_Skin", (0.76, 0.58, 0.48, 1.0), roughness=0.52)
m_beanie = create_mat("Mat_Axel_Beanie", (0.30, 0.34, 0.22, 1.0), roughness=0.88)
m_hair = create_mat("Mat_Axel_Hair", (0.08, 0.06, 0.05, 1.0), roughness=0.55)
m_eyes = create_mat("Mat_Axel_Eyes", (0.16, 0.11, 0.08, 1.0), roughness=0.05)
m_brows = create_mat("Mat_Axel_Brows", (0.07, 0.05, 0.04, 1.0), roughness=0.65)
m_lips = create_mat("Mat_Axel_Lips", (0.64, 0.38, 0.35, 1.0), roughness=0.38)

obj.data.materials.append(m_skin)   # 0
obj.data.materials.append(m_beanie) # 1
obj.data.materials.append(m_hair)   # 2
obj.data.materials.append(m_eyes)   # 3
obj.data.materials.append(m_brows)  # 4
obj.data.materials.append(m_lips)   # 5

for poly in mesh.polygons:
    poly.use_smooth = True

mod_sub = obj.modifiers.new(name="Subsurf", type='SUBSURF')
mod_sub.levels = 1
mod_sub.render_levels = 2

# Render de prueba
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 32
scene.cycles.device = 'CPU'
scene.render.resolution_x = 720
scene.render.resolution_y = 1080

cam_data = bpy.data.cameras.new("Cam")
cam_data.lens = 75.0
cam = bpy.data.objects.new("Cam", cam_data)
cam.location = Vector((0.15, 1.35, 1.61))
cam.rotation_euler = (math.radians(88.0), 0.0, math.radians(174.0))
scene.collection.objects.link(cam)
scene.camera = cam

key_data = bpy.data.lights.new("Key", type='AREA')
key_data.energy = 120.0
key_data.size = 1.0
key = bpy.data.objects.new("Key", key_data)
key.location = Vector((-1.0, 1.4, 2.0))
scene.collection.objects.link(key)

fill_data = bpy.data.lights.new("Fill", type='AREA')
fill_data.energy = 50.0
fill_data.size = 1.2
fill = bpy.data.objects.new("Fill", fill_data)
fill.location = Vector((1.0, 1.4, 1.5))
scene.collection.objects.link(fill)

rim_data = bpy.data.lights.new("Rim", type='SPOT')
rim_data.energy = 80.0
rim_data.spot_size = math.radians(65.0)
rim = bpy.data.objects.new("Rim", rim_data)
rim.location = Vector((0.0, -1.2, 2.1))
rim.rotation_euler = (math.radians(-50.0), 0.0, 0.0)
scene.collection.objects.link(rim)

scene.render.filepath = os.path.abspath("scratch/test_perfect_face_render.png")
bpy.ops.render.render(write_still=True)
print("Rendered scratch/test_perfect_face_render.png")
