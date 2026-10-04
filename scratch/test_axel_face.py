"""
Prototipo detallado de rostro, cabello, gorro y rasgos faciales estilizados de Axel.
Inspirado en estética AAA/Fortnite:
- Cráneo y rostro proporcionado con mentón, pómulos y mandíbula definida
- Nariz 3D anatómica con puente, punta redondeada y aletas nasales
- Labios 3D con arco de Cupido y comisuras
- Cuencas orbitarias con globos oculares y párpados superior e inferior
- Cejas estilizadas oscuras en relieve
- Mechones 3D de cabello castaño rizado que asoman en la frente, patillas y nuca
- Gorro beanie 3D con dobladillo acanalado y caída natural
- Cuello esbelto proporcionado (r ~ 0.052 m) con nuez de Adán
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

def create_mat(name, color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = color
        bsdf.inputs['Roughness'].default_value = roughness
        bsdf.inputs['Metallic'].default_value = metallic
    return mat

def build_detailed_face():
    mesh = bpy.data.meshes.new("Detailed_Head_Data")
    bm = bmesh.new()

    # Índices de materiales:
    # 0: Piel (Skin)
    # 1: Beanie (Verde oliva)
    # 2: Cabello (Castaño oscuro / negro)
    # 3: Ojos (Esclerótica + Iris/Pupila)
    # 4: Cejas (Pelo oscuro)
    # 5: Labios (Tono bermellón suave)

    # -------------------------------------------------------------
    # 1. Base del Cráneo, Mandíbula, Cuello y Rostro
    # -------------------------------------------------------------
    # Cuello esbelto
    neck_radii = [
        (1.48, 0.050, 0.052, 0.000), # Base en chamarra
        (1.52, 0.048, 0.051, 0.004), # Nuez de Adán (Z=1.52, leve prominencia +Y)
        (1.55, 0.050, 0.053, 0.002), # Transición a mandíbula
    ]
    neck_rings = []
    for z, rx, ry, adams in neck_radii:
        ring = []
        for i in range(20):
            ang = (2.0 * math.pi * i) / 20.0
            x = math.cos(ang) * rx
            y = math.sin(ang) * ry
            if adams > 0 and math.sin(ang) > 0.7:
                y += adams * math.sin(ang)
            v = bm.verts.new(Vector((x, y, z)))
            ring.append(v)
        neck_rings.append(ring)

    for r in range(len(neck_rings) - 1):
        for i in range(20):
            i_n = (i + 1) % 20
            f = bm.faces.new([neck_rings[r][i], neck_rings[r][i_n], neck_rings[r+1][i_n], neck_rings[r+1][i]])
            f.material_index = 0

    # Cabeza y cráneo elipsoidal base
    # Centro en Z=1.68, Y=0.0, X=0.0
    # Modela el volumen craneal y la mandíbula
    head_rings_data = [
        # (z, rx, ry_front, ry_back, y_center, is_beanie)
        (1.550, 0.042, 0.058, 0.042, 0.012, False), # Mentón y quijada inferior
        (1.580, 0.058, 0.070, 0.058, 0.010, False), # Boca y mandíbula
        (1.615, 0.068, 0.078, 0.068, 0.008, False), # Base nasal y pómulos
        (1.650, 0.072, 0.080, 0.075, 0.004, False), # Pómulos y dorso nasal
        (1.680, 0.074, 0.078, 0.080, 0.000, False), # Ojos y sien
        (1.710, 0.075, 0.076, 0.082, -0.004, False),# Frente y cejas
        (1.740, 0.076, 0.074, 0.084, -0.006, False),# Frente superior
        (1.770, 0.072, 0.070, 0.082, -0.008, True), # Bóveda / Beanie
        (1.800, 0.062, 0.060, 0.072, -0.010, True), # Cúpula beanie
        (1.825, 0.042, 0.040, 0.050, -0.012, True), # Coronilla beanie
    ]
    head_rings = []
    for z, rx, ry_f, ry_b, y_c, is_b in head_rings_data:
        ring = []
        for i in range(24):
            ang = (2.0 * math.pi * i) / 24.0
            cos_a = math.cos(ang)
            sin_a = math.sin(ang)
            x = sin_a * rx
            y = y_c + (cos_a * ry_f if cos_a >= 0 else abs(cos_a) * ry_b)
            v = bm.verts.new(Vector((x, y, z)))
            ring.append(v)
        head_rings.append((ring, is_b))

    for r in range(len(head_rings) - 1):
        r_a, is_b_a = head_rings[r]
        r_b, is_b_b = head_rings[r+1]
        mat_i = 1 if (is_b_a and is_b_b) else 0
        for i in range(24):
            i_n = (i + 1) % 24
            f = bm.faces.new([r_a[i], r_a[i_n], r_b[i_n], r_b[i]])
            f.material_index = mat_i

    # Cierre superior del cráneo
    top_v = bm.verts.new(Vector((0.0, -0.012, 1.838)))
    last_r, _ = head_rings[-1]
    for i in range(24):
        i_n = (i + 1) % 24
        f = bm.faces.new([last_r[i], last_r[i_n], top_v])
        f.material_index = 1

    # -------------------------------------------------------------
    # 2. Nariz Anatómica 3D (Puente, Punta y Aletas)
    # -------------------------------------------------------------
    # Modelamos la pirámide nasal con geometría quad
    nose_verts = [
        # Nasion (raíz)
        bm.verts.new(Vector(( 0.000, 0.082, 1.685))), # 0: nasion centro
        bm.verts.new(Vector((-0.010, 0.080, 1.685))), # 1: nasion izq
        bm.verts.new(Vector(( 0.010, 0.080, 1.685))), # 2: nasion der
        # Puente (rhinion)
        bm.verts.new(Vector(( 0.000, 0.096, 1.655))), # 3: puente centro
        bm.verts.new(Vector((-0.011, 0.088, 1.655))), # 4: puente izq
        bm.verts.new(Vector(( 0.011, 0.088, 1.655))), # 5: puente der
        # Punta nasal (supratip & tip)
        bm.verts.new(Vector(( 0.000, 0.108, 1.632))), # 6: punta centro
        bm.verts.new(Vector((-0.009, 0.104, 1.632))), # 7: punta izq
        bm.verts.new(Vector(( 0.009, 0.104, 1.632))), # 8: punta der
        # Aletas nasales (ala lobules)
        bm.verts.new(Vector((-0.018, 0.094, 1.624))), # 9: aleta izq
        bm.verts.new(Vector(( 0.018, 0.094, 1.624))), # 10: aleta der
        # Columela y base
        bm.verts.new(Vector(( 0.000, 0.092, 1.618))), # 11: columela base
        bm.verts.new(Vector((-0.014, 0.086, 1.616))), # 12: base aleta izq
        bm.verts.new(Vector(( 0.014, 0.086, 1.616))), # 13: base aleta der
    ]
    # Caras del puente y dorso
    nose_faces = [
        [0, 1, 4, 3], [0, 3, 5, 2],
        [3, 4, 7, 6], [3, 6, 8, 5],
        [4, 9, 7],    [5, 8, 10],
        [7, 9, 12, 11], [6, 7, 11], [6, 11, 8], [8, 11, 13, 10]
    ]
    for face_indices in nose_faces:
        f = bm.faces.new([nose_verts[idx] for idx in face_indices])
        f.material_index = 0

    # -------------------------------------------------------------
    # 3. Labios Anatómicos 3D (Arco de Cupido, Bermellón y Volumen)
    # -------------------------------------------------------------
    lip_verts = [
        # Labio superior (arco de Cupido)
        bm.verts.new(Vector(( 0.000, 0.088, 1.602))), # 0: arco centro dip
        bm.verts.new(Vector((-0.008, 0.091, 1.604))), # 1: arco pico izq
        bm.verts.new(Vector(( 0.008, 0.091, 1.604))), # 2: arco pico der
        bm.verts.new(Vector((-0.024, 0.080, 1.594))), # 3: comisura izq
        bm.verts.new(Vector(( 0.024, 0.080, 1.594))), # 4: comisura der
        # Línea de cierre labial (surco bucal)
        bm.verts.new(Vector(( 0.000, 0.089, 1.592))), # 5: cierre centro
        bm.verts.new(Vector((-0.012, 0.088, 1.593))), # 6: cierre medio izq
        bm.verts.new(Vector(( 0.012, 0.088, 1.593))), # 7: cierre medio der
        # Labio inferior (cuerpo redondeado)
        bm.verts.new(Vector(( 0.000, 0.092, 1.580))), # 8: bermellón inf centro
        bm.verts.new(Vector((-0.012, 0.089, 1.581))), # 9: bermellón inf izq
        bm.verts.new(Vector(( 0.012, 0.089, 1.581))), # 10: bermellón inf der
        # Surco mentolabial (base del labio inferior)
        bm.verts.new(Vector(( 0.000, 0.082, 1.568))), # 11: mentolabial centro
        bm.verts.new(Vector((-0.018, 0.078, 1.570))), # 12: mentolabial izq
        bm.verts.new(Vector(( 0.018, 0.078, 1.570))), # 13: mentolabial der
    ]
    lip_faces = [
        [0, 1, 6, 5], [0, 5, 7, 2],
        [1, 3, 6],    [2, 7, 4],
        [5, 6, 9, 8], [5, 8, 10, 7],
        [6, 3, 12, 9],[7, 10, 13, 4],
        [8, 9, 12, 11],[8, 11, 13, 10]
    ]
    for face_indices in lip_faces:
        f = bm.faces.new([lip_verts[idx] for idx in face_indices])
        f.material_index = 5 # 5: Labios bermellón

    # -------------------------------------------------------------
    # 4. Globos Oculares 3D y Párpados
    # -------------------------------------------------------------
    for eye_x, eye_sign in [(-0.033, -1.0), (0.033, 1.0)]:
        p_eye = Vector((eye_x, 0.068, 1.678))
        # Esfera ocular
        sph = bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=12, radius=0.0135, matrix=Matrix.Translation(p_eye))
        for v in sph['verts']:
            for f in v.link_faces:
                f.material_index = 3 # 3: Ojos

        # Párpado superior (almond fold)
        eyelid_top = [
            Vector((eye_x - 0.015, 0.072, 1.676)),
            Vector((eye_x - 0.007, 0.079, 1.688)),
            Vector((eye_x + 0.007, 0.079, 1.688)),
            Vector((eye_x + 0.015, 0.072, 1.676)),
            Vector((eye_x + 0.018, 0.075, 1.684)),
            Vector((eye_x + 0.008, 0.082, 1.694)),
            Vector((eye_x - 0.008, 0.082, 1.694)),
            Vector((eye_x - 0.018, 0.075, 1.684)),
        ]
        ev = [bm.verts.new(p) for p in eyelid_top]
        f1 = bm.faces.new([ev[0], ev[1], ev[6], ev[7]])
        f2 = bm.faces.new([ev[1], ev[2], ev[5], ev[6]])
        f3 = bm.faces.new([ev[2], ev[3], ev[4], ev[5]])
        f1.material_index = 0
        f2.material_index = 0
        f3.material_index = 0

        # Ceja 3D oscura
        brow_pts = [
            Vector((eye_x - 0.018, 0.076, 1.698)),
            Vector((eye_x - 0.005, 0.082, 1.706)),
            Vector((eye_x + 0.012, 0.080, 1.704)),
            Vector((eye_x + 0.022, 0.075, 1.696)),
            Vector((eye_x + 0.020, 0.076, 1.702)),
            Vector((eye_x + 0.010, 0.084, 1.710)),
            Vector((eye_x - 0.005, 0.086, 1.712)),
            Vector((eye_x - 0.016, 0.078, 1.704)),
        ]
        bv = [bm.verts.new(p) for p in brow_pts]
        bf1 = bm.faces.new([bv[0], bv[1], bv[6], bv[7]])
        bf2 = bm.faces.new([bv[1], bv[2], bv[5], bv[6]])
        bf3 = bm.faces.new([bv[2], bv[3], bv[4], bv[5]])
        bf1.material_index = 4
        bf2.material_index = 4
        bf3.material_index = 4

    # -------------------------------------------------------------
    # 5. Orejas Anatómicas 3D
    # -------------------------------------------------------------
    for ear_x, ear_sign in [(-0.075, -1.0), (0.075, 1.0)]:
        # Hélix y lóbulo
        ear_pts = [
            Vector((ear_x, 0.015, 1.690)), # Superior inserción
            Vector((ear_x + ear_sign * 0.015, 0.005, 1.695)), # Hélix alto
            Vector((ear_x + ear_sign * 0.020, -0.010, 1.670)),# Hélix lateral
            Vector((ear_x + ear_sign * 0.016, -0.012, 1.640)),# Lóbulo lateral
            Vector((ear_x, 0.002, 1.630)), # Lóbulo inserción
            Vector((ear_x, 0.005, 1.665)), # Concha centro
        ]
        erv = [bm.verts.new(p) for p in ear_pts]
        ef1 = bm.faces.new([erv[0], erv[1], erv[2], erv[5]])
        ef2 = bm.faces.new([erv[5], erv[2], erv[3], erv[4]])
        ef1.material_index = 0
        ef2.material_index = 0

    # -------------------------------------------------------------
    # 6. Mechones 3D de Cabello Rizado bajo el Beanie
    # -------------------------------------------------------------
    # En la foto de Axel, mechones oscuros caen sobre la frente y patillas
    def add_curved_hair_lock(p_start, p_mid, p_end, radius, mat_idx=2):
        # 3 tramos de anillo tubular cónico
        pts = [p_start, p_mid, p_end]
        radii = [radius, radius * 0.85, radius * 0.4]
        ring_v = []
        for pi, (pt, r) in enumerate(zip(pts, radii)):
            rng = []
            for a in range(8):
                ang = (2.0 * math.pi * a) / 8.0
                vx = pt.x + math.cos(ang) * r
                vy = pt.y + math.sin(ang) * r * 0.7
                vz = pt.z - math.sin(ang) * r * 0.3
                rng.append(bm.verts.new(Vector((vx, vy, vz))))
            ring_v.append(rng)
        for pi in range(len(pts) - 1):
            r0 = ring_v[pi]
            r1 = ring_v[pi + 1]
            for a in range(8):
                a_n = (a + 1) % 8
                f = bm.faces.new([r0[a], r0[a_n], r1[a_n], r1[a]])
                f.material_index = mat_idx
        # Tapa punta
        tip_v = bm.verts.new(p_end + Vector((0, 0, -radius * 0.3)))
        last_rng = ring_v[-1]
        for a in range(8):
            a_n = (a + 1) % 8
            f = bm.faces.new([last_rng[a], last_rng[a_n], tip_v])
            f.material_index = mat_idx

    # Mechones frontales rizados que caen sobre la frente (Axel bangs)
    hair_locks = [
        # Flequillo izquierdo
        (Vector((-0.038, 0.076, 1.745)), Vector((-0.035, 0.082, 1.725)), Vector((-0.030, 0.084, 1.705)), 0.010),
        (Vector((-0.022, 0.080, 1.748)), Vector((-0.018, 0.086, 1.722)), Vector((-0.014, 0.088, 1.702)), 0.011),
        (Vector((-0.006, 0.082, 1.748)), Vector((-0.002, 0.087, 1.720)), Vector(( 0.002, 0.089, 1.698)), 0.011),
        # Flequillo derecho
        (Vector(( 0.010, 0.082, 1.748)), Vector(( 0.014, 0.087, 1.722)), Vector(( 0.018, 0.088, 1.704)), 0.011),
        (Vector(( 0.026, 0.080, 1.745)), Vector(( 0.030, 0.085, 1.724)), Vector(( 0.034, 0.086, 1.706)), 0.010),
        (Vector(( 0.042, 0.074, 1.740)), Vector(( 0.046, 0.078, 1.718)), Vector(( 0.048, 0.078, 1.698)), 0.009),
        # Patillas
        (Vector((-0.066, 0.032, 1.730)), Vector((-0.068, 0.030, 1.695)), Vector((-0.068, 0.025, 1.660)), 0.010),
        (Vector(( 0.066, 0.032, 1.730)), Vector(( 0.068, 0.030, 1.695)), Vector(( 0.068, 0.025, 1.660)), 0.010),
        # Nuca
        (Vector((-0.030, -0.072, 1.730)), Vector((-0.030, -0.068, 1.690)), Vector((-0.028, -0.064, 1.650)), 0.011),
        (Vector(( 0.000, -0.074, 1.730)), Vector(( 0.000, -0.070, 1.688)), Vector(( 0.000, -0.066, 1.648)), 0.012),
        (Vector(( 0.030, -0.072, 1.730)), Vector(( 0.030, -0.068, 1.690)), Vector(( 0.028, -0.064, 1.650)), 0.011),
    ]
    for p_st, p_md, p_en, r_h in hair_locks:
        add_curved_hair_lock(p_st, p_md, p_en, r_h, mat_idx=2)

    # -------------------------------------------------------------
    # 7. Gorro Beanie 3D con Dobladillo Acanalado (Cuff Ring)
    # -------------------------------------------------------------
    # Dobladillo acanalado en relieve envolvente alrededor de la cabeza
    cuff_z_front = 1.735
    cuff_z_back = 1.710
    cuff_rings = []
    for h_off, r_extra in [(-0.015, 0.008), (0.000, 0.014), (0.018, 0.012), (0.032, 0.006)]:
        cr = []
        for i in range(28):
            ang = (2.0 * math.pi * i) / 28.0
            cos_a = math.cos(ang)
            sin_a = math.sin(ang)
            # Altura inclinada (más baja atrás, más alta al frente)
            t_fb = (cos_a + 1.0) * 0.5
            z = (cuff_z_back * (1.0 - t_fb) + cuff_z_front * t_fb) + h_off
            rx = 0.078 + r_extra
            ry = 0.082 + r_extra
            # Relieve de acanalado vertical (ribbed knit)
            rib = math.sin(i * 3.0 * math.pi) * 0.0025
            x = sin_a * (rx + rib)
            y = (cos_a * ry if cos_a >= 0 else cos_a * (ry + 0.004)) + (rib if cos_a >= 0 else -rib)
            cr.append(bm.verts.new(Vector((x, y, z))))
        cuff_rings.append(cr)

    for r in range(len(cuff_rings) - 1):
        r0 = cuff_rings[r]
        r1 = cuff_rings[r+1]
        for i in range(28):
            i_n = (i + 1) % 28
            f = bm.faces.new([r0[i], r0[i_n], r1[i_n], r1[i]])
            f.material_index = 1

    # Cúpula superior del Beanie (Domo que envuelve el cráneo)
    beanie_dome_rings = []
    dome_levels = [
        (1.770, 0.084, 0.086, -0.005),
        (1.800, 0.076, 0.078, -0.008),
        (1.828, 0.058, 0.060, -0.010),
        (1.848, 0.032, 0.034, -0.012),
    ]
    for z, rx, ry, y_c in dome_levels:
        dr = []
        for i in range(24):
            ang = (2.0 * math.pi * i) / 24.0
            x = math.sin(ang) * rx
            y = y_c + math.cos(ang) * ry
            dr.append(bm.verts.new(Vector((x, y, z))))
        beanie_dome_rings.append(dr)

    for r in range(len(beanie_dome_rings) - 1):
        r0 = beanie_dome_rings[r]
        r1 = beanie_dome_rings[r+1]
        for i in range(24):
            i_n = (i + 1) % 24
            f = bm.faces.new([r0[i], r0[i_n], r1[i_n], r1[i]])
            f.material_index = 1

    # Cierre superior del domo
    top_beanie_v = bm.verts.new(Vector((0.0, -0.012, 1.856)))
    for i in range(24):
        i_n = (i + 1) % 24
        f = bm.faces.new([beanie_dome_rings[-1][i], beanie_dome_rings[-1][i_n], top_beanie_v])
        f.material_index = 1

    bm.verts.index_update()
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("Detailed_Head_Obj", mesh)
    bpy.context.scene.collection.objects.link(obj)

    # Materiales
    m_skin = create_mat("M_Skin", (0.78, 0.62, 0.52, 1), roughness=0.55)
    m_beanie = create_mat("M_Beanie", (0.30, 0.34, 0.22, 1), roughness=0.85)
    m_hair = create_mat("M_Hair", (0.08, 0.06, 0.05, 1), roughness=0.50)
    m_eyes = create_mat("M_Eyes", (0.12, 0.09, 0.07, 1), roughness=0.08)
    m_brows = create_mat("M_Brows", (0.06, 0.05, 0.04, 1), roughness=0.60)
    m_lips = create_mat("M_Lips", (0.72, 0.44, 0.40, 1), roughness=0.45)

    obj.data.materials.append(m_skin)   # 0
    obj.data.materials.append(m_beanie) # 1
    obj.data.materials.append(m_hair)   # 2
    obj.data.materials.append(m_eyes)   # 3
    obj.data.materials.append(m_brows)  # 4
    obj.data.materials.append(m_lips)   # 5

    for poly in mesh.polygons:
        poly.use_smooth = True

    subsurf = obj.modifiers.new(name="Subsurf", type='SUBSURF')
    subsurf.levels = 1
    subsurf.render_levels = 2

    return obj

clean_scene()
build_detailed_face()

# Configurar render
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 24
scene.cycles.device = 'CPU'
scene.render.resolution_x = 720
scene.render.resolution_y = 1080

cam_data = bpy.data.cameras.new("Cam")
cam_data.lens = 70.0
cam = bpy.data.objects.new("Cam", cam_data)
# Vista 3/4 frontal ligeramente desde la derecha
cam.location = Vector((0.35, 1.25, 1.68))
cam.rotation_euler = (math.radians(88.0), 0.0, math.radians(165.0))
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

scene.render.filepath = os.path.abspath("scratch/test_axel_face_render.png")
bpy.ops.render.render(write_still=True)
print("Rendered scratch/test_axel_face_render.png")
