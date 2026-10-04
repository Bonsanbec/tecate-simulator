"""
Generador de rostro humanoide continuo, orgánico y estilizado (estilo Fortnite/AAA).
Utiliza una malla cuadrangular continua (manifold) sin fisuras ni piezas desprendidas.
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

def build_seamless_head():
    mesh = bpy.data.meshes.new("Head_Seamless_Mesh")
    bm = bmesh.new()

    # Malla continua de 36 columnas (U) x 32 filas (V)
    # De Z=1.46 (cuello dentro de chamarra) a Z=1.82 (coronilla)
    n_u = 36 # Meridianos
    n_v = 32 # Paralelos

    grid = []

    for vi in range(n_v + 1):
        tv = vi / float(n_v)
        # Altura vertical z
        # No lineal: más densidad de anillos alrededor de boca, nariz y ojos (Z=1.56 a Z=1.72)
        if tv < 0.25:
            # Cuello: 1.46 a 1.55
            z = 1.46 + (tv / 0.25) * 0.09
        elif tv < 0.70:
            # Rostro (mandíbula, boca, nariz, ojos): 1.55 a 1.72
            z = 1.55 + ((tv - 0.25) / 0.45) * 0.17
        else:
            # Frente y bóveda craneal: 1.72 a 1.83
            z = 1.72 + ((tv - 0.70) / 0.30) * 0.11

        # Perfil base de anchura (rx) y profundidad (ry)
        if z < 1.54:
            # Cuello esbelto cilíndrico
            rx = 0.052
            ry_front = 0.054
            ry_back = 0.052
            y_center = 0.005 # Cuello ligeramente adelantado
        elif z < 1.62:
            # Mandíbula y barbilla
            t_jaw = (z - 1.54) / 0.08
            rx = 0.052 + t_jaw * 0.016
            ry_front = 0.054 + t_jaw * 0.024
            ry_back = 0.052 + t_jaw * 0.016
            y_center = 0.005 - t_jaw * 0.005
        elif z < 1.72:
            # Mejillas, pómulos, nariz y ojos
            t_mid = (z - 1.62) / 0.10
            rx = 0.068 + t_mid * 0.007
            ry_front = 0.078
            ry_back = 0.068 + t_mid * 0.010
            y_center = 0.0
        else:
            # Frente y cráneo
            t_top = (z - 1.72) / 0.11
            dome = math.sqrt(max(0.01, 1.0 - (t_top * 0.96)**2))
            rx = 0.075 * dome + 0.002
            ry_front = 0.078 * dome + 0.002
            ry_back = 0.078 * dome + 0.002
            y_center = -0.006 * t_top

        ring = []
        for ui in range(n_u):
            # ui = 0 -> posterior (-Y)
            # ui = n_u/2 -> anterior (+Y)
            ang = (ui / float(n_u)) * 2.0 * math.pi - (math.pi / 2.0)
            # ang = -pi/2 -> -Y (posterior)
            # ang = +pi/2 -> +Y (anterior)
            # ang = 0 -> +X (derecha)
            # ang = pi -> -X (izquierda)
            sin_a = math.sin(ang) # -1 atras, +1 adelante
            cos_a = math.cos(ang) # +1 der, -1 izq

            vx = cos_a * rx
            vy = y_center + (sin_a * ry_front if sin_a >= 0 else sin_a * ry_back)
            vz = z

            # =========================================================
            # MODULACIÓN ANATÓMICA CONTINUA DEL ROSTRO (sin fisuras)
            # =========================================================
            if sin_a > 0: # Solo en la parte frontal de la cabeza
                front_weight = sin_a # 0 en los lados, 1 en el centro exacto

                # 1. Mentón (Barbilla) en Z ~ 1.56, X ~ 0
                if abs(vz - 1.560) < 0.030 and abs(vx) < 0.032:
                    c_dist = math.sqrt((vx / 0.032)**2 + ((vz - 1.560) / 0.030)**2)
                    if c_dist < 1.0:
                        vy += 0.020 * (1.0 - c_dist)**2

                # 2. Labios y Boca en Z ~ 1.595, X ~ 0
                # A. Surco de la boca (hendidura)
                if abs(vz - 1.595) < 0.018 and abs(vx) < 0.030:
                    lip_w = (1.0 - abs(vx) / 0.030)
                    # Labio superior (arco)
                    if vz > 1.595:
                        dz_sup = (vz - 1.595) / 0.014
                        vy += 0.014 * lip_w * math.sin(dz_sup * math.pi)
                    else:
                        # Labio inferior (cuerpo más grueso y redondeado)
                        dz_inf = (1.595 - vz) / 0.014
                        vy += 0.016 * lip_w * math.sin(dz_inf * math.pi)

                # 3. Surco mentolabial (hendidura bajo el labio inferior)
                if abs(vz - 1.575) < 0.010 and abs(vx) < 0.025:
                    vy -= 0.006 * (1.0 - abs(vx) / 0.025)

                # 4. Nariz 3D continua: puente, dorso y punta
                # Z de 1.620 (base) a 1.685 (nasion)
                if 1.615 < vz < 1.685 and abs(vx) < 0.026:
                    t_nose = (vz - 1.615) / 0.070 # 0 en base, 1 en nasion
                    # Anchura de la nariz según altura
                    nose_w = 0.012 + (1.0 - t_nose) * 0.012 # más ancha en base (aletas), fina en nasion
                    if abs(vx) < nose_w:
                        lat_fall = 1.0 - (abs(vx) / nose_w)
                        # Altura del perfil de la nariz
                        if t_nose < 0.35: # Punta nasal y aletas
                            nose_proj = 0.032 * math.sin((t_nose / 0.35) * (math.pi / 2.0))
                        else: # Puente nasal descendiendo hacia nasion
                            nose_proj = 0.018 + (1.0 - t_nose) * 0.014
                        vy += nose_proj * (lat_fall**1.5)

                # 5. Cuencas Oculares (Órbitas hundidas)
                # Ojos en X = +/- 0.032, Z = 1.678
                for eye_cx in [-0.033, 0.033]:
                    d_eye = math.sqrt(((vx - eye_cx) / 0.022)**2 + ((vz - 1.678) / 0.018)**2)
                    if d_eye < 1.0:
                        vy -= 0.012 * (1.0 - d_eye)**2

                # 6. Cejas y Arco Superciliar en Z ~ 1.705
                for brow_cx in [-0.034, 0.034]:
                    d_brow = math.sqrt(((vx - brow_cx) / 0.026)**2 + ((vz - 1.705) / 0.012)**2)
                    if d_brow < 1.0:
                        vy += 0.008 * (1.0 - d_brow)**2

                # 7. Nuez de Adán en el cuello (Z ~ 1.515, X = 0)
                if abs(vz - 1.515) < 0.016 and abs(vx) < 0.016:
                    d_adam = math.sqrt((vx / 0.016)**2 + ((vz - 1.515) / 0.016)**2)
                    if d_adam < 1.0:
                        vy += 0.006 * (1.0 - d_adam)

            v = bm.verts.new(Vector((vx, vy, vz)))
            ring.append(v)
        grid.append(ring)

    # Crear caras quad continuas
    for vi in range(n_v):
        r0 = grid[vi]
        r1 = grid[vi + 1]
        for ui in range(n_u):
            u_n = (ui + 1) % n_u
            f = bm.faces.new([r0[ui], r0[u_n], r1[u_n], r1[ui]])
            f.material_index = 0

    # Cierre superior del cráneo con polo
    top_pole = bm.verts.new(Vector((0.0, -0.006, 1.832)))
    for ui in range(n_u):
        u_n = (ui + 1) % n_u
        f = bm.faces.new([grid[-1][ui], grid[-1][u_n], top_pole])
        f.material_index = 0

    # ---------------------------------------------------------
    # 2. Globos Oculares 3D (Insertados en las cuencas)
    # ---------------------------------------------------------
    for eye_x in [-0.033, 0.033]:
        p_eye = Vector((eye_x, 0.068, 1.678))
        sph = bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=12, radius=0.0125, matrix=Matrix.Translation(p_eye))
        for v in sph['verts']:
            for f in v.link_faces:
                f.material_index = 3 # Ojos

    # ---------------------------------------------------------
    # 3. Orejas 3D integradas
    # ---------------------------------------------------------
    for ear_x, ear_sgn in [(-0.072, -1.0), (0.072, 1.0)]:
        p_ear = Vector((ear_x, 0.002, 1.660))
        sph_ear = bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=8, radius=0.015, matrix=Matrix.Translation(p_ear))
        # Escalar para aplanar oreja
        for v in sph_ear['verts']:
            v.co.x = ear_x + (v.co.x - ear_x) * 0.4
            v.co.y = 0.002 + (v.co.y - 0.002) * 0.9
            v.co.z = 1.660 + (v.co.z - 1.660) * 1.3
            for f in v.link_faces:
                f.material_index = 0 # Piel

    # ---------------------------------------------------------
    # 4. Mechones 3D de Cabello Rizado Orgánico (Axel bangs)
    # ---------------------------------------------------------
    def add_curved_hair_strand(points, radii, mat_idx=2):
        strand_rings = []
        for pt, r in zip(points, radii):
            sr = []
            for a in range(8):
                ang = (2.0 * math.pi * a) / 8.0
                vx = pt.x + math.cos(ang) * r
                vy = pt.y + math.sin(ang) * r * 0.8
                vz = pt.z - math.sin(ang) * r * 0.3
                sr.append(bm.verts.new(Vector((vx, vy, vz))))
            strand_rings.append(sr)
        for i in range(len(strand_rings) - 1):
            r0 = strand_rings[i]
            r1 = strand_rings[i + 1]
            for a in range(8):
                a_n = (a + 1) % 8
                f = bm.faces.new([r0[a], r0[a_n], r1[a_n], r1[a]])
                f.material_index = mat_idx
        # Tapa final cónica
        tip = bm.verts.new(points[-1] + Vector((0, 0, -radii[-1] * 0.5)))
        for a in range(8):
            a_n = (a + 1) % 8
            f = bm.faces.new([strand_rings[-1][a], strand_rings[-1][a_n], tip])
            f.material_index = mat_idx

    hair_strands = [
        # Mechones frontales ondulados sobre la frente
        ([Vector((-0.036, 0.076, 1.745)), Vector((-0.032, 0.084, 1.722)), Vector((-0.026, 0.086, 1.700))], [0.010, 0.008, 0.004]),
        ([Vector((-0.020, 0.080, 1.748)), Vector((-0.016, 0.088, 1.724)), Vector((-0.010, 0.090, 1.698))], [0.011, 0.009, 0.004]),
        ([Vector((-0.004, 0.082, 1.750)), Vector(( 0.000, 0.090, 1.725)), Vector(( 0.006, 0.091, 1.696))], [0.011, 0.009, 0.004]),
        ([Vector(( 0.012, 0.082, 1.750)), Vector(( 0.016, 0.090, 1.725)), Vector(( 0.022, 0.091, 1.698))], [0.011, 0.009, 0.004]),
        ([Vector(( 0.028, 0.080, 1.748)), Vector(( 0.032, 0.086, 1.724)), Vector(( 0.036, 0.086, 1.702))], [0.010, 0.008, 0.004]),
        ([Vector(( 0.042, 0.075, 1.742)), Vector(( 0.046, 0.080, 1.720)), Vector(( 0.048, 0.080, 1.702))], [0.009, 0.007, 0.003]),
        # Patillas
        ([Vector((-0.066, 0.028, 1.730)), Vector((-0.068, 0.025, 1.695)), Vector((-0.068, 0.020, 1.660))], [0.010, 0.008, 0.003]),
        ([Vector(( 0.066, 0.028, 1.730)), Vector(( 0.068, 0.025, 1.695)), Vector(( 0.068, 0.020, 1.660))], [0.010, 0.008, 0.003]),
    ]
    for pts, rads in hair_strands:
        add_curved_hair_strand(pts, rads, mat_idx=2)

    # ---------------------------------------------------------
    # 5. Gorro Beanie 3D Suave y Continuo (Con dobladillo)
    # ---------------------------------------------------------
    # Dobladillo envolvente con reborde
    beanie_z_levels = [
        # (z, rx, ry, y_c, rib_strength)
        (1.720, 0.082, 0.086, -0.002, 0.003), # Borde inferior del dobladillo
        (1.740, 0.086, 0.090, -0.004, 0.004), # Pico del dobladillo
        (1.760, 0.084, 0.088, -0.006, 0.003), # Parte superior del dobladillo
        (1.785, 0.080, 0.082, -0.008, 0.000), # Inicio de la cúpula
        (1.810, 0.070, 0.072, -0.010, 0.000), # Cúpula media
        (1.835, 0.052, 0.054, -0.012, 0.000), # Cúpula alta
        (1.855, 0.026, 0.028, -0.014, 0.000), # Coronilla
    ]
    beanie_rings = []
    for z, rx, ry, yc, rib_amp in beanie_z_levels:
        br = []
        for i in range(28):
            ang = (2.0 * math.pi * i) / 28.0
            rib = math.sin(i * 4.0 * math.pi) * rib_amp if rib_amp > 0 else 0.0
            vx = math.sin(ang) * (rx + rib)
            vy = yc + math.cos(ang) * (ry + rib)
            br.append(bm.verts.new(Vector((vx, vy, z))))
        beanie_rings.append(br)

    for r in range(len(beanie_rings) - 1):
        r0 = beanie_rings[r]
        r1 = beanie_rings[r + 1]
        for i in range(28):
            i_n = (i + 1) % 28
            f = bm.faces.new([r0[i], r0[i_n], r1[i_n], r1[i]])
            f.material_index = 1

    top_beanie = bm.verts.new(Vector((0.0, -0.014, 1.862)))
    for i in range(28):
        i_n = (i + 1) % 28
        f = bm.faces.new([beanie_rings[-1][i], beanie_rings[-1][i_n], top_beanie])
        f.material_index = 1

    bm.verts.index_update()
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("Head_Seamless_Obj", mesh)
    bpy.context.scene.collection.objects.link(obj)

    # Materiales
    m_skin = create_mat("M_Axel_Skin", (0.76, 0.58, 0.48, 1), roughness=0.55)
    m_beanie = create_mat("M_Axel_Beanie", (0.30, 0.34, 0.22, 1), roughness=0.85)
    m_hair = create_mat("M_Axel_Hair", (0.08, 0.06, 0.05, 1), roughness=0.50)
    m_eyes = create_mat("M_Axel_Eyes", (0.12, 0.09, 0.07, 1), roughness=0.08)

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
build_seamless_head()

# Render front & 3/4
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 24
scene.cycles.device = 'CPU'
scene.render.resolution_x = 720
scene.render.resolution_y = 1080

cam_data = bpy.data.cameras.new("Cam")
cam_data.lens = 75.0
cam = bpy.data.objects.new("Cam", cam_data)
cam.location = Vector((0.25, 1.35, 1.68))
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

scene.render.filepath = os.path.abspath("scratch/test_seamless_face_render.png")
bpy.ops.render.render(write_still=True)
print("Rendered scratch/test_seamless_face_render.png")
