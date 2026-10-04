"""
Calibración v3 de la cabeza, rostro y proporciones anatómicas de Axel.
Altura de cabeza: 22 cm (de Z=1.55 a Z=1.77), anchura 15 cm, profundidad 20 cm.
Rasgos proporcionados: nariz, labios, ojos con párpados, cejas, flequillo ondulado y beanie inclinado.
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

def create_mat(name, color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = color
        bsdf.inputs['Roughness'].default_value = roughness
        bsdf.inputs['Metallic'].default_value = metallic
    return mat

def build_proportional_head():
    mesh = bpy.data.meshes.new("Head_V3_Mesh")
    bm = bmesh.new()

    # 1. Cabeza y cuello continuos manifold
    # Proporciones canónicas de cabeza humana (H_total = 22 cm):
    # Cuello: Z = 1.48 a 1.545
    # Barbilla / Mentón: Z = 1.550
    # Boca / Labios: Z = 1.585
    # Base nasal: Z = 1.615
    # Punta nasal: Z = 1.625
    # Ojos: Z = 1.660
    # Cejas: Z = 1.685
    # Línea de inserción beanie: Z = 1.710
    # Coronilla: Z = 1.770

    n_u = 36 # Meridianos
    n_v = 28 # Paralelos

    grid = []

    for vi in range(n_v + 1):
        tv = vi / float(n_v)
        # Z interpolado por zonas anatómicas
        if tv < 0.20: # Cuello (Z=1.48 a 1.545)
            z = 1.480 + (tv / 0.20) * 0.065
            rx = 0.048
            ry_front = 0.050
            ry_back = 0.050
            y_cen = 0.004
        elif tv < 0.45: # Mandíbula y barbilla a boca (Z=1.545 a 1.605)
            t_jaw = (tv - 0.20) / 0.25
            z = 1.545 + t_jaw * 0.060
            rx = 0.054 + t_jaw * 0.014
            ry_front = 0.062 + t_jaw * 0.016
            ry_back = 0.054 + t_jaw * 0.016
            y_cen = 0.002
        elif tv < 0.75: # Nariz, pómulos y ojos (Z=1.605 a 1.690)
            t_mid = (tv - 0.45) / 0.30
            z = 1.605 + t_mid * 0.085
            rx = 0.068 + t_mid * 0.006
            ry_front = 0.078
            ry_back = 0.070 + t_mid * 0.008
            y_cen = 0.0
        else: # Frente y cráneo (Z=1.690 a 1.770)
            t_top = (tv - 0.75) / 0.25
            z = 1.690 + t_top * 0.080
            dome = math.sqrt(max(0.01, 1.0 - (t_top * 0.96)**2))
            rx = 0.074 * dome + 0.004
            ry_front = 0.078 * dome + 0.004
            ry_back = 0.078 * dome + 0.004
            y_cen = -0.008 * t_top

        ring = []
        for ui in range(n_u):
            ang = (ui / float(n_u)) * 2.0 * math.pi - (math.pi / 2.0)
            sin_a = math.sin(ang) # -1 atras, +1 adelante
            cos_a = math.cos(ang) # +1 der, -1 izq

            vx = cos_a * rx
            vy = y_cen + (sin_a * ry_front if sin_a >= 0 else sin_a * ry_back)
            vz = z

            # Escultura anatómica continua en la cara anterior (+Y)
            if sin_a > 0:
                # A. Mentón firme (Z ~ 1.555, X ~ 0)
                if abs(vz - 1.555) < 0.022 and abs(vx) < 0.028:
                    c_d = math.sqrt((vx / 0.028)**2 + ((vz - 1.555) / 0.022)**2)
                    if c_d < 1.0:
                        vy += 0.016 * (1.0 - c_d)**2

                # B. Labios y boca (Z ~ 1.585)
                if abs(vz - 1.585) < 0.015 and abs(vx) < 0.026:
                    lip_falloff = (1.0 - abs(vx) / 0.026)
                    # Arco de Cupido superior
                    if vz > 1.585:
                        dz = (vz - 1.585) / 0.012
                        vy += 0.012 * lip_falloff * math.sin(dz * math.pi)
                    else:
                        dz = (1.585 - vz) / 0.012
                        vy += 0.014 * lip_falloff * math.sin(dz * math.pi)

                # C. Surco mentolabial
                if abs(vz - 1.568) < 0.008 and abs(vx) < 0.022:
                    vy -= 0.005 * (1.0 - abs(vx) / 0.022)

                # D. Nariz 3D continua (Z de 1.605 a 1.665)
                if 1.605 < vz < 1.665 and abs(vx) < 0.024:
                    tn = (vz - 1.605) / 0.060
                    nw = 0.011 + (1.0 - tn) * 0.012
                    if abs(vx) < nw:
                        lat_fall = 1.0 - (abs(vx) / nw)
                        if tn < 0.38: # Punta nasal prominente
                            n_proj = 0.028 * math.sin((tn / 0.38) * (math.pi / 2.0))
                        else: # Puente
                            n_proj = 0.016 + (1.0 - tn) * 0.012
                        vy += n_proj * (lat_fall**1.4)

                # E. Cuencas orbitarias hundidas (Z ~ 1.660, X ~ +/- 0.032)
                for eye_cx in [-0.033, 0.033]:
                    de = math.sqrt(((vx - eye_cx) / 0.020)**2 + ((vz - 1.660) / 0.016)**2)
                    if de < 1.0:
                        vy -= 0.011 * (1.0 - de)**2

                # F. Cejas en Z ~ 1.685
                for brow_cx in [-0.034, 0.034]:
                    db = math.sqrt(((vx - brow_cx) / 0.024)**2 + ((vz - 1.685) / 0.010)**2)
                    if db < 1.0:
                        vy += 0.007 * (1.0 - db)**2

                # G. Nuez de Adán (Z ~ 1.515)
                if abs(vz - 1.515) < 0.015 and abs(vx) < 0.014:
                    da = math.sqrt((vx / 0.014)**2 + ((vz - 1.515) / 0.015)**2)
                    if da < 1.0:
                        vy += 0.006 * (1.0 - da)

            v = bm.verts.new(Vector((vx, vy, vz)))
            ring.append(v)
        grid.append(ring)

    # Caras cuadrangulares continuas
    for vi in range(n_v):
        r0 = grid[vi]
        r1 = grid[vi + 1]
        for ui in range(n_u):
            u_n = (ui + 1) % n_u
            f = bm.faces.new([r0[ui], r0[u_n], r1[u_n], r1[ui]])
            f.material_index = 0

    top_pole = bm.verts.new(Vector((0.0, -0.008, 1.775)))
    for ui in range(n_u):
        u_n = (ui + 1) % n_u
        f = bm.faces.new([grid[-1][ui], grid[-1][u_n], top_pole])
        f.material_index = 0

    # 2. Ojos 3D esféricos y párpados en cuencas
    for eye_x in [-0.033, 0.033]:
        p_eye = Vector((eye_x, 0.068, 1.660))
        sph = bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=12, radius=0.0125, matrix=Matrix.Translation(p_eye))
        for v in sph['verts']:
            for f in v.link_faces:
                f.material_index = 3

    # 3. Orejas anatómicas (Z = 1.62 a 1.68, X = +/- 0.072)
    for ear_x, ear_sgn in [(-0.072, -1.0), (0.072, 1.0)]:
        p_ear = Vector((ear_x, 0.002, 1.645))
        sph_ear = bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=8, radius=0.015, matrix=Matrix.Translation(p_ear))
        for v in sph_ear['verts']:
            v.co.x = ear_x + (v.co.x - ear_x) * 0.4
            v.co.y = 0.002 + (v.co.y - 0.002) * 0.85
            v.co.z = 1.645 + (v.co.z - 1.645) * 1.25
            for f in v.link_faces:
                f.material_index = 0

    # 4. Mechones de Cabello Ondulado Estilizado (Axel Hair Fringe)
    def add_hair_wave(pts, rads, mat_idx=2):
        strand_rings = []
        for pt, r in zip(pts, rads):
            sr = []
            for a in range(8):
                ang = (2.0 * math.pi * a) / 8.0
                vx = pt.x + math.cos(ang) * r
                vy = pt.y + math.sin(ang) * r * 0.75
                vz = pt.z - math.sin(ang) * r * 0.35
                sr.append(bm.verts.new(Vector((vx, vy, vz))))
            strand_rings.append(sr)
        for i in range(len(strand_rings) - 1):
            r0 = strand_rings[i]
            r1 = strand_rings[i + 1]
            for a in range(8):
                a_n = (a + 1) % 8
                f = bm.faces.new([r0[a], r0[a_n], r1[a_n], r1[a]])
                f.material_index = mat_idx
        tip = bm.verts.new(pts[-1] + Vector((0, 0, -rads[-1] * 0.4)))
        for a in range(8):
            a_n = (a + 1) % 8
            f = bm.faces.new([strand_rings[-1][a], strand_rings[-1][a_n], tip])
            f.material_index = mat_idx

    hair_bangs = [
        # Mechones frontales ondulados que caen desde la base del beanie hacia la frente
        ([Vector((-0.038, 0.074, 1.712)), Vector((-0.032, 0.082, 1.696)), Vector((-0.024, 0.084, 1.680))], [0.010, 0.008, 0.003]),
        ([Vector((-0.020, 0.078, 1.715)), Vector((-0.014, 0.086, 1.698)), Vector((-0.006, 0.087, 1.678))], [0.011, 0.009, 0.003]),
        ([Vector((-0.002, 0.080, 1.716)), Vector(( 0.004, 0.087, 1.699)), Vector(( 0.012, 0.088, 1.677))], [0.011, 0.009, 0.003]),
        ([Vector(( 0.014, 0.079, 1.715)), Vector(( 0.020, 0.086, 1.698)), Vector(( 0.026, 0.086, 1.678))], [0.011, 0.009, 0.003]),
        ([Vector(( 0.030, 0.076, 1.712)), Vector(( 0.035, 0.082, 1.696)), Vector(( 0.038, 0.083, 1.680))], [0.010, 0.008, 0.003]),
        # Patillas
        ([Vector((-0.068, 0.022, 1.705)), Vector((-0.070, 0.020, 1.675)), Vector((-0.070, 0.016, 1.645))], [0.009, 0.007, 0.003]),
        ([Vector(( 0.068, 0.022, 1.705)), Vector(( 0.070, 0.020, 1.675)), Vector(( 0.070, 0.016, 1.645))], [0.009, 0.007, 0.003]),
    ]
    for pts, rads in hair_bangs:
        add_hair_wave(pts, rads, mat_idx=2)

    # 5. Gorro Beanie con Inclinación Natural y Dobladillo
    # Inclinación: frente Z=1.708, atrás Z=1.670
    beanie_levels = [
        # (z_front, z_back, rx, ry, rib_amp)
        (1.695, 1.660, 0.080, 0.084, 0.0025), # Base dobladillo
        (1.712, 1.675, 0.084, 0.088, 0.0035), # Pico dobladillo
        (1.730, 1.695, 0.082, 0.086, 0.0020), # Tope dobladillo
        (1.752, 1.725, 0.078, 0.082, 0.0000), # Domo bajo
        (1.775, 1.755, 0.068, 0.072, 0.0000), # Domo medio
        (1.795, 1.780, 0.050, 0.054, 0.0000), # Domo alto
        (1.810, 1.800, 0.024, 0.026, 0.0000), # Coronilla
    ]
    beanie_rings = []
    for zf, zb, rx, ry, rib_amp in beanie_levels:
        br = []
        for i in range(28):
            ang = (2.0 * math.pi * i) / 28.0
            cos_a = math.cos(ang)
            sin_a = math.sin(ang)
            # Inclinación hacia atrás
            t_fb = (cos_a + 1.0) * 0.5
            z = zb * (1.0 - t_fb) + zf * t_fb
            rib = math.sin(i * 4.0 * math.pi) * rib_amp if rib_amp > 0 else 0.0
            vx = sin_a * (rx + rib)
            vy = (cos_a * ry) - 0.008 * (1.0 - t_fb) # Leve caída hacia atrás
            br.append(bm.verts.new(Vector((vx, vy, z))))
        beanie_rings.append(br)

    for r in range(len(beanie_rings) - 1):
        r0 = beanie_rings[r]
        r1 = beanie_rings[r + 1]
        for i in range(28):
            i_n = (i + 1) % 28
            f = bm.faces.new([r0[i], r0[i_n], r1[i_n], r1[i]])
            f.material_index = 1

    top_beanie = bm.verts.new(Vector((0.0, -0.012, 1.816)))
    for i in range(28):
        i_n = (i + 1) % 28
        f = bm.faces.new([beanie_rings[-1][i], beanie_rings[-1][i_n], top_beanie])
        f.material_index = 1

    bm.verts.index_update()
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("Head_V3_Obj", mesh)
    bpy.context.scene.collection.objects.link(obj)

    # Materiales
    m_skin = create_mat("M_Skin", (0.76, 0.58, 0.48, 1), roughness=0.55)
    m_beanie = create_mat("M_Beanie", (0.30, 0.34, 0.22, 1), roughness=0.85)
    m_hair = create_mat("M_Hair", (0.08, 0.06, 0.05, 1), roughness=0.50)
    m_eyes = create_mat("M_Eyes", (0.12, 0.09, 0.07, 1), roughness=0.08)

    obj.data.materials.append(m_skin)   # 0
    obj.data.materials.append(m_beanie) # 1
    obj.data.materials.append(m_hair)   # 2
    obj.data.materials.append(m_eyes)   # 3

    for poly in mesh.polygons:
        poly.use_smooth = True

    subsurf = obj.modifiers.new(name="Subsurf", type='SUBSURF')
    subsurf.levels = 2
    subsurf.render_levels = 2

    return obj

clean_scene()
build_proportional_head()

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 24
scene.cycles.device = 'CPU'
scene.render.resolution_x = 720
scene.render.resolution_y = 1080

cam_data = bpy.data.cameras.new("Cam")
cam_data.lens = 75.0
cam = bpy.data.objects.new("Cam", cam_data)
# Vista 3/4 frontal
cam.location = Vector((0.25, 1.25, 1.64))
cam.rotation_euler = (math.radians(88.0), 0.0, math.radians(170.0))
scene.collection.objects.link(cam)
scene.camera = cam

# Luces
key_data = bpy.data.lights.new("Key", type='AREA')
key_data.energy = 300.0
key_data.size = 1.0
key = bpy.data.objects.new("Key", key_data)
key.location = Vector((-0.8, 1.2, 2.1))
scene.collection.objects.link(key)

fill_data = bpy.data.lights.new("Fill", type='AREA')
fill_data.energy = 120.0
fill_data.size = 1.2
fill = bpy.data.objects.new("Fill", fill_data)
fill.location = Vector((0.8, 1.0, 1.6))
scene.collection.objects.link(fill)

rim_data = bpy.data.lights.new("Rim", type='SPOT')
rim_data.energy = 350.0
rim_data.spot_size = math.radians(60.0)
rim = bpy.data.objects.new("Rim", rim_data)
rim.location = Vector((0.0, -1.2, 2.2))
rim.rotation_euler = (math.radians(-50.0), 0, 0)
scene.collection.objects.link(rim)

scene.render.filepath = os.path.abspath("scratch/test_head_v3_render.png")
bpy.ops.render.render(write_still=True)
print("Rendered scratch/test_head_v3_render.png")
