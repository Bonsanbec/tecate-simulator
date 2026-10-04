"""
Prototipo integral de Axel: Topología continua para chamarra, cuerpo, cabeza y rostro.
Cero piezas desprendidas, cero esferas flotantes, cero generación por IA.
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

def build_head():
    mesh = bpy.data.meshes.new("Axel_Head_Mesh")
    bm = bmesh.new()

    # 1. Cabeza y cuello proporcionados (H_total cráneo = 20 cm)
    # Cuello: Z=1.46 a 1.53 (r ~ 0.046m)
    # Barbilla: Z=1.54
    # Boca: Z=1.57
    # Nariz punta: Z=1.60
    # Ojos: Z=1.63
    # Cejas: Z=1.655
    # Dobladillo beanie: Z=1.675
    # Coronilla: Z=1.745
    n_u = 32
    n_v = 24
    grid = []

    for vi in range(n_v + 1):
        tv = vi / float(n_v)
        if tv < 0.25: # Cuello
            z = 1.460 + (tv / 0.25) * 0.075
            rx = 0.046
            ry_f = 0.048
            ry_b = 0.046
            yc = 0.005
        elif tv < 0.50: # Mandíbula, mentón y boca (1.535 a 1.590)
            tj = (tv - 0.25) / 0.25
            z = 1.535 + tj * 0.055
            rx = 0.052 + tj * 0.016
            ry_f = 0.060 + tj * 0.016
            ry_b = 0.050 + tj * 0.016
            yc = 0.003
        elif tv < 0.75: # Nariz, pómulos y ojos (1.590 a 1.655)
            tm = (tv - 0.50) / 0.25
            z = 1.590 + tm * 0.065
            rx = 0.068 + tm * 0.006
            ry_f = 0.076
            ry_b = 0.066 + tm * 0.008
            yc = 0.0
        else: # Frente y cráneo (1.655 a 1.740)
            tt = (tv - 0.75) / 0.25
            z = 1.655 + tt * 0.085
            dome = math.sqrt(max(0.01, 1.0 - (tt * 0.94)**2))
            rx = 0.074 * dome + 0.003
            ry_f = 0.076 * dome + 0.003
            ry_b = 0.076 * dome + 0.003
            yc = -0.008 * tt

        ring = []
        for ui in range(n_u):
            ang = (ui / float(n_u)) * 2.0 * math.pi - (math.pi / 2.0)
            sin_a = math.sin(ang)
            cos_a = math.cos(ang)
            vx = cos_a * rx
            vy = yc + (sin_a * ry_f if sin_a >= 0 else sin_a * ry_b)
            vz = z

            # Rasgos faciales continuos en cara anterior
            if sin_a > 0:
                # Mentón
                if abs(vz - 1.545) < 0.020 and abs(vx) < 0.026:
                    cd = math.sqrt((vx / 0.026)**2 + ((vz - 1.545) / 0.020)**2)
                    if cd < 1.0:
                        vy += 0.015 * (1.0 - cd)**2
                # Boca
                if abs(vz - 1.572) < 0.012 and abs(vx) < 0.025:
                    lw = (1.0 - abs(vx) / 0.025)
                    if vz > 1.572:
                        vy += 0.010 * lw * math.sin(((vz - 1.572) / 0.010) * math.pi)
                    else:
                        vy += 0.012 * lw * math.sin(((1.572 - vz) / 0.010) * math.pi)
                # Nariz 3D continua
                if 1.585 < vz < 1.640 and abs(vx) < 0.022:
                    tn = (vz - 1.585) / 0.055
                    nw = 0.010 + (1.0 - tn) * 0.010
                    if abs(vx) < nw:
                        lf = 1.0 - (abs(vx) / nw)
                        n_proj = 0.025 * math.sin(tn * math.pi * 0.8) if tn < 0.4 else 0.016 + (1.0 - tn) * 0.008
                        vy += n_proj * (lf**1.4)
                # Cuencas de ojos
                for ecx in [-0.032, 0.032]:
                    de = math.sqrt(((vx - ecx) / 0.018)**2 + ((vz - 1.632) / 0.014)**2)
                    if de < 1.0:
                        vy -= 0.010 * (1.0 - de)**2
                # Nuez de Adán
                if abs(vz - 1.495) < 0.014 and abs(vx) < 0.012:
                    vy += 0.005 * (1.0 - abs(vx) / 0.012)

            ring.append(bm.verts.new(Vector((vx, vy, vz))))
        grid.append(ring)

    # Caras cuadrangulares
    for vi in range(n_v):
        r0 = grid[vi]
        r1 = grid[vi + 1]
        for ui in range(n_u):
            un = (ui + 1) % n_u
            f = bm.faces.new([r0[ui], r0[un], r1[un], r1[ui]])
            fc = (r0[ui].co + r0[un].co + r1[un].co + r1[ui].co) * 0.25
            if abs(fc.z - 1.572) < 0.012 and abs(fc.x) < 0.022 and fc.y > 0.05:
                f.material_index = 5 # labios
            else:
                f.material_index = 0 # piel

    top_v = bm.verts.new(Vector((0.0, -0.008, 1.745)))
    for ui in range(n_u):
        un = (ui + 1) % n_u
        f = bm.faces.new([grid[-1][ui], grid[-1][un], top_v])
        f.material_index = 0

    # 2. Globos Oculares 3D en cuencas (Z=1.632, X=+/-0.032)
    for ex in [-0.032, 0.032]:
        p_eye = Vector((ex, 0.066, 1.632))
        sph = bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=12, radius=0.012, matrix=Matrix.Translation(p_eye))
        for v in sph['verts']:
            for f in v.link_faces:
                f.material_index = 3 # ojos

        # Párpados
        etop = [
            Vector((ex - 0.014, 0.070, 1.630)),
            Vector((ex - 0.006, 0.076, 1.640)),
            Vector((ex + 0.006, 0.076, 1.640)),
            Vector((ex + 0.014, 0.070, 1.630)),
            Vector((ex + 0.016, 0.073, 1.636)),
            Vector((ex + 0.007, 0.079, 1.645)),
            Vector((ex - 0.007, 0.079, 1.645)),
            Vector((ex - 0.016, 0.073, 1.636)),
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
            Vector((ex - sb * 0.015, 0.073, 1.650)),
            Vector((ex - sb * 0.004, 0.078, 1.658)),
            Vector((ex + sb * 0.010, 0.077, 1.656)),
            Vector((ex + sb * 0.018, 0.072, 1.650)),
            Vector((ex + sb * 0.016, 0.073, 1.654)),
            Vector((ex + sb * 0.008, 0.080, 1.662)),
            Vector((ex - sb * 0.004, 0.081, 1.663)),
            Vector((ex - sb * 0.013, 0.075, 1.655)),
        ]
        bv = [bm.verts.new(p) for p in bpts]
        bf1 = bm.faces.new([bv[0], bv[1], bv[6], bv[7]])
        bf2 = bm.faces.new([bv[1], bv[2], bv[5], bv[6]])
        bf3 = bm.faces.new([bv[2], bv[3], bv[4], bv[5]])
        for bf in [bf1, bf2, bf3]:
            bf.material_index = 4 # cejas

    # 3. Orejas
    for ear_x, ear_sgn in [(-0.070, -1.0), (0.070, 1.0)]:
        p_ear = Vector((ear_x, 0.002, 1.620))
        sph_ear = bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=8, radius=0.014, matrix=Matrix.Translation(p_ear))
        for v in sph_ear['verts']:
            v.co.x = ear_x + (v.co.x - ear_x) * 0.38
            v.co.y = 0.002 + (v.co.y - 0.002) * 0.85
            v.co.z = 1.620 + (v.co.z - 1.620) * 1.25
            for f in v.link_faces:
                f.material_index = 0

    # 4. Mechones de Cabello Ondulado (Axel Bangs)
    def add_hair_lock(pts, rads):
        sr = []
        for pt, r in zip(pts, rads):
            rng = []
            for a in range(8):
                ang = (2.0 * math.pi * a) / 8.0
                vx = pt.x + math.cos(ang) * r
                vy = pt.y + math.sin(ang) * r * 0.75
                vz = pt.z - math.sin(ang) * r * 0.35
                rng.append(bm.verts.new(Vector((vx, vy, vz))))
            sr.append(rng)
        for i in range(len(sr) - 1):
            r0 = sr[i]
            r1 = sr[i + 1]
            for a in range(8):
                an = (a + 1) % 8
                f = bm.faces.new([r0[a], r0[an], r1[an], r1[a]])
                f.material_index = 2
        tip = bm.verts.new(pts[-1] + Vector((0, 0, -rads[-1] * 0.4)))
        for a in range(8):
            an = (a + 1) % 8
            f = bm.faces.new([sr[-1][a], sr[-1][an], tip])
            f.material_index = 2

    hair_locks = [
        ([Vector((-0.036, 0.072, 1.685)), Vector((-0.030, 0.080, 1.670)), Vector((-0.022, 0.082, 1.652))], [0.010, 0.008, 0.003]),
        ([Vector((-0.018, 0.076, 1.688)), Vector((-0.012, 0.084, 1.672)), Vector((-0.005, 0.085, 1.650))], [0.011, 0.009, 0.003]),
        ([Vector((-0.002, 0.078, 1.688)), Vector(( 0.005, 0.085, 1.672)), Vector(( 0.012, 0.085, 1.650))], [0.011, 0.009, 0.003]),
        ([Vector(( 0.014, 0.077, 1.688)), Vector(( 0.020, 0.084, 1.672)), Vector(( 0.026, 0.084, 1.652))], [0.011, 0.009, 0.003]),
        ([Vector(( 0.028, 0.074, 1.685)), Vector(( 0.034, 0.080, 1.670)), Vector(( 0.038, 0.081, 1.654))], [0.010, 0.008, 0.003]),
        # Patillas
        ([Vector((-0.066, 0.020, 1.680)), Vector((-0.068, 0.018, 1.650)), Vector((-0.068, 0.015, 1.620))], [0.009, 0.007, 0.003]),
        ([Vector(( 0.066, 0.020, 1.680)), Vector(( 0.070, 0.018, 1.650)), Vector(( 0.068, 0.015, 1.620))], [0.009, 0.007, 0.003]),
        # Nuca
        ([Vector((-0.028, -0.066, 1.685)), Vector((-0.028, -0.062, 1.645)), Vector((-0.026, -0.058, 1.610))], [0.010, 0.008, 0.003]),
        ([Vector(( 0.000, -0.068, 1.685)), Vector(( 0.000, -0.064, 1.645)), Vector(( 0.000, -0.060, 1.608))], [0.011, 0.009, 0.003]),
        ([Vector(( 0.028, -0.066, 1.685)), Vector(( 0.028, -0.062, 1.645)), Vector(( 0.026, -0.058, 1.610))], [0.010, 0.008, 0.003]),
    ]
    for pts, rads in hair_locks:
        add_hair_lock(pts, rads)

    # 5. Beanie de Lana Verde Oliva Ajustado y Redondeado
    # Se adapta al cráneo (Z=1.66 a 1.765)
    beanie_levels = [
        # (zf, zb, rx, ry, rib)
        (1.665, 1.635, 0.078, 0.082, 0.003), # Dobladillo base
        (1.682, 1.652, 0.082, 0.086, 0.004), # Dobladillo relieve
        (1.700, 1.670, 0.080, 0.084, 0.002), # Dobladillo cima
        (1.722, 1.698, 0.076, 0.080, 0.000), # Domo bajo
        (1.745, 1.725, 0.066, 0.070, 0.000), # Domo medio
        (1.762, 1.748, 0.048, 0.052, 0.000), # Domo alto
        (1.774, 1.765, 0.022, 0.024, 0.000), # Coronilla
    ]
    beanie_rings = []
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
        beanie_rings.append(br)

    for r in range(len(beanie_rings) - 1):
        r0 = beanie_rings[r]
        r1 = beanie_rings[r + 1]
        for i in range(28):
            in_idx = (i + 1) % 28
            f = bm.faces.new([r0[i], r0[in_idx], r1[in_idx], r1[i]])
            f.material_index = 1

    top_beanie = bm.verts.new(Vector((0.0, -0.012, 1.780)))
    for i in range(28):
        in_idx = (i + 1) % 28
        f = bm.faces.new([beanie_rings[-1][i], beanie_rings[-1][in_idx], top_beanie])
        f.material_index = 1

    bm.verts.index_update()
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("Player_Head_Mesh", mesh)
    bpy.context.scene.collection.objects.link(obj)

    # Materiales PBR
    m_skin = create_mat("Mat_Axel_Skin", (0.76, 0.58, 0.48, 1.0), roughness=0.52)
    m_beanie = create_mat("Mat_Axel_Beanie", (0.30, 0.34, 0.22, 1.0), roughness=0.88)
    m_hair = create_mat("Mat_Axel_Hair", (0.08, 0.06, 0.05, 1.0), roughness=0.55)
    m_eyes = create_mat("Mat_Axel_Eyes", (0.16, 0.11, 0.08, 1.0), roughness=0.05)
    m_brows = create_mat("Mat_Axel_Brows", (0.07, 0.05, 0.04, 1.0), roughness=0.65)
    m_lips = create_mat("Mat_Axel_Lips", (0.68, 0.40, 0.36, 1.0), roughness=0.40)

    obj.data.materials.append(m_skin)   # 0
    obj.data.materials.append(m_beanie) # 1
    obj.data.materials.append(m_hair)   # 2
    obj.data.materials.append(m_eyes)   # 3
    obj.data.materials.append(m_brows)  # 4
    obj.data.materials.append(m_lips)   # 5

    for poly in mesh.polygons:
        poly.use_smooth = True

    return obj

def build_body():
    mesh = bpy.data.meshes.new("Axel_Body_Mesh")
    bm = bmesh.new()

    # 1. Chamarra Orgánica Continua con Hombros Cerrados
    # Cuello de la chamarra: Z=1.45 a 1.50
    # Pecho/Hombros: Z=1.42 a 1.45 (conecta clavículas y deltoides)
    # Torso: Z=1.02 a 1.42
    
    # Cuello en V abierto al frente
    collar_rings = []
    for cz, crx, cry, c_v in [
        (1.45, 0.058, 0.060, 0.000),
        (1.48, 0.060, 0.062, 0.008),
        (1.50, 0.062, 0.064, 0.016),
    ]:
        cr = []
        for i in range(20):
            ang = (2.0 * math.pi * i) / 20.0
            sin_a = math.sin(ang)
            cos_a = math.cos(ang)
            x = cos_a * crx
            y = sin_a * cry
            z = cz - (c_v if (sin_a > 0.7 and abs(x) < 0.02) else 0.0)
            cr.append(bm.verts.new(Vector((x, y, z))))
        collar_rings.append(cr)

    for ri in range(len(collar_rings) - 1):
        r0 = collar_rings[ri]
        r1 = collar_rings[ri + 1]
        for i in range(20):
            in_idx = (i + 1) % 20
            f = bm.faces.new([r0[i], r0[in_idx], r1[in_idx], r1[i]])
            f.material_index = 0

    # Hombros inclinados continuos (Trapecio y clavícula de cuello a hombros)
    # Conectan desde el cuello (Z=1.45, rx=0.06) hasta la cabeza de hombro (Z=1.40, rx=0.19)
    shoulder_rings = []
    for t_sh in [0.0, 0.5, 1.0]:
        z = 1.45 - t_sh * 0.05 # De 1.45 a 1.40
        rx = 0.07 + t_sh * 0.12 # De 0.07 a 0.19
        ry = 0.07 + t_sh * 0.06 # De 0.07 a 0.13
        sr = []
        for i in range(24):
            ang = (2.0 * math.pi * i) / 24.0
            vx = math.cos(ang) * rx
            vy = math.sin(ang) * ry
            sr.append(bm.verts.new(Vector((vx, vy, z))))
        shoulder_rings.append(sr)

    for ri in range(len(shoulder_rings) - 1):
        r0 = shoulder_rings[ri]
        r1 = shoulder_rings[ri + 1]
        for i in range(24):
            in_idx = (i + 1) % 24
            f = bm.faces.new([r0[i], r0[in_idx], r1[in_idx], r1[i]])
            f.material_index = 0

    # Torso de la Chamarra Acolchada (Z=1.40 a 1.02)
    torso_rings = 8
    torso_grid = []
    for tri in range(torso_rings + 1):
        t = tri / float(torso_rings)
        z = 1.40 - t * 0.38
        rx = 0.19 - (t * 0.025)
        ry = 0.13 - (t * 0.015)
        baffle = math.sin(t * 6.0 * math.pi) * 0.005
        rx += baffle
        ry += baffle
        tr = []
        for s in range(24):
            ang = (2.0 * math.pi * s) / 24.0
            vx = math.cos(ang) * rx
            vy = math.sin(ang) * ry
            if abs(vx) < 0.015 and vy > 0.0:
                vy += 0.008 # Solapa cremallera
            tr.append(bm.verts.new(Vector((vx, vy, z))))
        torso_grid.append(tr)

    for tri in range(torso_rings):
        r0 = torso_grid[tri]
        r1 = torso_grid[tri + 1]
        for s in range(24):
            sn = (s + 1) % 24
            f = bm.faces.new([r0[s], r0[sn], r1[sn], r1[s]])
            f.material_index = 0

    # Unir hombros con torso
    r_sh_last = shoulder_rings[-1]
    r_torso_first = torso_grid[0]
    for s in range(24):
        sn = (s + 1) % 24
        f = bm.faces.new([r_sh_last[s], r_sh_last[sn], r_torso_first[sn], r_torso_first[s]])
        f.material_index = 0

    # 2. Brazos y Mangas continuos desde los hombros
    def add_cylinder(p0, p1, r0, r1, segs=12, rings=3, mat_i=0, bulge=0.0):
        dv = p1 - p0
        all_v = []
        r_list = []
        norm = dv.normalized()
        up = Vector((0, 0, 1)) if abs(norm.z) < 0.9 else Vector((0, 1, 0))
        xaxis = norm.cross(up).normalized()
        yaxis = xaxis.cross(norm).normalized()
        for ri in range(rings + 1):
            t = ri / float(rings)
            c = p0 + dv * t
            r = r0 + (r1 - r0) * t + math.sin(t * math.pi) * bulge
            rng = []
            for s in range(segs):
                ang = (2.0 * math.pi * s) / segs
                v = bm.verts.new(c + (xaxis * math.cos(ang) + yaxis * math.sin(ang)) * r)
                rng.append(v)
                all_v.append(v)
            r_list.append(rng)
        for ri in range(rings):
            r_a = r_list[ri]
            r_b = r_list[ri + 1]
            for s in range(segs):
                sn = (s + 1) % segs
                f = bm.faces.new([r_a[s], r_a[sn], r_b[sn], r_b[s]])
                f.material_index = mat_i
        return all_v

    # Manos anatómicas con pulgar oponible medial
    def add_hand(p_wrist, sign_x, mat_i=3):
        w_p = 0.034
        t_p = 0.014
        h_layers = [
            ( 0.000, 0.80, 0.85),
            (-0.025, 0.95, 1.00),
            (-0.055, 1.05, 0.95),
            (-0.075, 1.00, 0.80),
        ]
        h_rings = []
        for dz, ws, ts in h_layers:
            c = p_wrist + Vector((0, 0, dz))
            rng = []
            for i in range(12):
                ang = (2.0 * math.pi * i) / 12.0
                vx = c.x + math.cos(ang) * (w_p * ws)
                vy = c.y + math.sin(ang) * (t_p * ts)
                rng.append(bm.verts.new(Vector((vx, vy, c.z))))
            h_rings.append(rng)
        for li in range(len(h_rings) - 1):
            r0 = h_rings[li]
            r1 = h_rings[li + 1]
            for i in range(12):
                in_idx = (i + 1) % 12
                f = bm.faces.new([r0[i], r0[in_idx], r1[in_idx], r1[i]])
                f.material_index = mat_i

        def add_finger(pts, rads):
            fr = []
            for pt, r in zip(pts, rads):
                rng = []
                for a in range(8):
                    ang = (2.0 * math.pi * a) / 8.0
                    rng.append(bm.verts.new(pt + Vector((math.cos(ang) * r, math.sin(ang) * r, 0))))
                fr.append(rng)
            for i in range(len(fr) - 1):
                r0 = fr[i]
                r1 = fr[i + 1]
                for a in range(8):
                    an = (a + 1) % 8
                    f = bm.faces.new([r0[a], r0[an], r1[an], r1[a]])
                    f.material_index = mat_i
            tip = bm.verts.new(pts[-1] + Vector((0, 0, -rads[-1] * 0.4)))
            for a in range(8):
                an = (a + 1) % 8
                f = bm.faces.new([fr[-1][a], fr[-1][an], tip])
                f.material_index = mat_i

        # Pulgar oponible medial hacia el fondo/palma
        t_pts = [
            p_wrist + Vector((-sign_x * 0.022, -0.005, -0.025)),
            p_wrist + Vector((-sign_x * 0.034, -0.008, -0.045)),
            p_wrist + Vector((-sign_x * 0.030, -0.016, -0.065)),
            p_wrist + Vector((-sign_x * 0.020, -0.022, -0.080)),
        ]
        add_finger(t_pts, [0.011, 0.010, 0.0085, 0.0065])

        # 4 Dedos
        fdata = [
            (-sign_x * 0.016, 0.066, 0.0090),
            (-sign_x * 0.005, 0.074, 0.0095),
            ( sign_x * 0.007, 0.068, 0.0085),
            ( sign_x * 0.020, 0.052, 0.0075),
        ]
        for fx, flen, frad in fdata:
            kn = p_wrist + Vector((fx, 0.002, -0.075))
            p1 = kn + Vector((0, -0.006, -flen * 0.45))
            p2 = p1 + Vector((0, -0.012, -flen * 0.35))
            pt = p2 + Vector((0, -0.016, -flen * 0.20))
            add_finger([kn, p1, p2, pt], [frad, frad * 0.88, frad * 0.72, frad * 0.50])

    for sign_x, sfx in [(-1.0, ".L"), (1.0, ".R")]:
        p_sh = Vector((sign_x * 0.18, 0.0, 1.40))
        p_elb = Vector((sign_x * 0.30, 0.0, 1.16))
        p_wri = Vector((sign_x * 0.38, 0.0, 0.92))

        # Manga del brazo superior
        add_cylinder(p_sh, p_elb, 0.068, 0.056, segs=14, rings=4, mat_i=0, bulge=0.008)
        # Codo
        add_cylinder(p_elb, p_wri, 0.056, 0.045, segs=14, rings=4, mat_i=0, bulge=0.006)
        # Puño
        add_cylinder(p_wri + Vector((0, 0, 0.02)), p_wri, 0.046, 0.042, segs=12, rings=1, mat_i=0)
        # Mano
        add_hand(p_wri, sign_x, mat_i=3)

    # 3. Cinturón de Cuero y Hebilla Metálica
    add_cylinder(Vector((0, 0, 1.02)), Vector((0, 0, 0.96)), 0.162, 0.164, segs=20, rings=2, mat_i=4)
    # Hebilla frontal rectangular
    b_box = bmesh.ops.create_cube(bm, size=0.034, matrix=Matrix.Translation(Vector((0, 0.170, 0.99))))
    for v in b_box['verts']:
        for f in v.link_faces:
            f.material_index = 5

    # 4. Pantalón de Mezclilla Oscura Continuo
    add_cylinder(Vector((0, 0, 0.98)), Vector((0, 0, 0.88)), 0.158, 0.142, segs=18, rings=2, mat_i=1)
    for sign_x in [-1.0, 1.0]:
        p_hip = Vector((sign_x * 0.11, 0.0, 0.92))
        p_knee = Vector((sign_x * 0.11, 0.0, 0.50))
        p_ank = Vector((sign_x * 0.11, 0.0, 0.12))
        add_cylinder(p_hip, p_knee, 0.098, 0.078, segs=16, rings=5, mat_i=1, bulge=0.010)
        add_cylinder(p_knee, p_ank, 0.078, 0.064, segs=16, rings=5, mat_i=1, bulge=0.006)

    # 5. Calzado Deportivo (Sneakers)
    for sign_x in [-1.0, 1.0]:
        cx = sign_x * 0.11
        add_cylinder(Vector((cx, -0.06, 0.02)), Vector((cx, 0.18, 0.02)), 0.062, 0.052, segs=12, rings=2, mat_i=2)
        add_cylinder(Vector((cx, 0.0, 0.12)), Vector((cx, 0.06, 0.04)), 0.058, 0.064, segs=12, rings=3, mat_i=2)

    bm.verts.index_update()
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("Player_Body_Mesh", mesh)
    bpy.context.scene.collection.objects.link(obj)

    # Materiales PBR
    m_jacket = create_mat("Mat_Axel_Jacket", (0.10, 0.12, 0.18, 1.0), roughness=0.60)
    m_pants = create_mat("Mat_Axel_Pants", (0.12, 0.13, 0.16, 1.0), roughness=0.85)
    m_shoes = create_mat("Mat_Axel_Shoes", (0.12, 0.12, 0.14, 1.0), roughness=0.50)
    m_skin = create_mat("Mat_Axel_Skin", (0.76, 0.58, 0.48, 1.0), roughness=0.52)
    m_belt = create_mat("Mat_Axel_Belt", (0.24, 0.15, 0.10, 1.0), roughness=0.45)
    m_buckle = create_mat("Mat_Axel_Buckle", (0.75, 0.75, 0.78, 1.0), roughness=0.25, metallic=0.95)

    obj.data.materials.append(m_jacket) # 0
    obj.data.materials.append(m_pants)  # 1
    obj.data.materials.append(m_shoes)  # 2
    obj.data.materials.append(m_skin)   # 3
    obj.data.materials.append(m_belt)   # 4
    obj.data.materials.append(m_buckle) # 5

    for poly in mesh.polygons:
        poly.use_smooth = True

    return obj

clean_scene()
head_obj = build_head()
body_obj = build_body()

# Configurar render de estudio calibrado (iluminación de 3 puntos suave y realista)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 32
scene.cycles.device = 'CPU'
scene.render.resolution_x = 720
scene.render.resolution_y = 1280

cam_data = bpy.data.cameras.new("Cam")
cam_data.lens = 65.0
cam = bpy.data.objects.new("Cam", cam_data)
# Encuadre medio que muestra rostro en detalle, chamarra, cinturón y ambas manos
cam.location = Vector((0.18, 2.2, 1.34))
cam.rotation_euler = (math.radians(88.0), 0.0, math.radians(175.0))
scene.collection.objects.link(cam)
scene.camera = cam

# Luces de estudio suaves (50W - 25W en lugar de 350W quemados)
key_data = bpy.data.lights.new("Key", type='AREA')
key_data.energy = 55.0
key_data.size = 1.0
key_data.color = (1.0, 0.98, 0.95)
key = bpy.data.objects.new("Key", key_data)
key.location = Vector((-1.0, 1.8, 1.9))
key.rotation_euler = (math.radians(60.0), 0.0, math.radians(-145.0))
scene.collection.objects.link(key)

fill_data = bpy.data.lights.new("Fill", type='AREA')
fill_data.energy = 22.0
fill_data.size = 1.4
fill_data.color = (0.90, 0.95, 1.0)
fill = bpy.data.objects.new("Fill", fill_data)
fill.location = Vector((1.2, 1.8, 1.4))
scene.collection.objects.link(fill)

rim_data = bpy.data.lights.new("Rim", type='SPOT')
rim_data.energy = 45.0
rim_data.spot_size = math.radians(70.0)
rim = bpy.data.objects.new("Rim", rim_data)
rim.location = Vector((0.0, -1.5, 2.0))
rim.rotation_euler = (math.radians(-50.0), 0.0, 0.0)
scene.collection.objects.link(rim)

scene.render.filepath = os.path.abspath("scratch/test_complete_render.png")
bpy.ops.render.render(write_still=True)
print("Rendered scratch/test_complete_render.png")
