"""
=============================================================================
Generador 3D Paramétrico: Poste de Nomenclatura Urbana Clásica de Tecate, B.C.
=============================================================================
Este script automatiza la creación completa del asset de señalización urbana:
1. Pedestal / Base de campana con 16 facetas radiales y molduras clásicas.
2. Fuste tubular continuo de hierro fundido.
3. Capitel ornamental tipo balustre con collares y vástago de montaje.
4. Placas rectangulares con crestería semicircular asimétrica, marco perimetral
   en altorrelieve, filete divisor 2/3 (calle) y 1/3 (colonia/C.P.) y camas
   rebajadas para textos dinámicos o personalizados.
5. Placa superior e inferior a 90° con desfase vertical de +0.10 m (H total = 2.95 m).
6. Textos 3D de muestra en una colección independiente opcional.
7. Materiales PBR listos para StandardMaterial3D (ORM) de Godot 4.
8. Exportación de .blend, .glb modular y renders de inspección técnica.
=============================================================================
"""

import bpy
import bmesh
import math
from mathutils import Vector

def clean_scene():
    """Elimina todos los objetos, mallas y materiales residuales."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh, do_unlink=True)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat, do_unlink=True)
    for col in list(bpy.data.collections):
        bpy.data.collections.remove(col)

def create_materials():
    """
    Crea los materiales PBR físicamente basados respetando la especificación:
    - M_Hierro_Fundido_Poste: Gris plomo oxidado oscuro, Metallic 0.70, Roughness 0.78.
    - M_Placa_Bronce_Patinado: Verde cardenillo mate oxidado, Metallic 0.45, Roughness 0.75.
    - M_Placa_Relieve_Laton: Latón/bronce desgastado eólico, Metallic 0.55, Roughness 0.65.
    """
    # 1. Poste de hierro fundido
    mat_poste = bpy.data.materials.new(name="M_Hierro_Fundido_Poste")
    nodes_p = mat_poste.node_tree.nodes
    bsdf_p = nodes_p.get("Principled BSDF")
    if bsdf_p:
        bsdf_p.inputs["Base Color"].default_value = (0.042, 0.039, 0.035, 1.0)
        bsdf_p.inputs["Metallic"].default_value = 0.70
        bsdf_p.inputs["Roughness"].default_value = 0.78

    # 2. Placas: Fondo cardenillo oscuro
    mat_placa = bpy.data.materials.new(name="M_Placa_Bronce_Patinado")
    nodes_pl = mat_placa.node_tree.nodes
    bsdf_pl = nodes_pl.get("Principled BSDF")
    if bsdf_pl:
        bsdf_pl.inputs["Base Color"].default_value = (0.065, 0.105, 0.075, 1.0)
        bsdf_pl.inputs["Metallic"].default_value = 0.45
        bsdf_pl.inputs["Roughness"].default_value = 0.75

    # 3. Placas: Relieves, marcos y filetes (Latón desgastado)
    mat_relieve = bpy.data.materials.new(name="M_Placa_Relieve_Laton")
    nodes_r = mat_relieve.node_tree.nodes
    bsdf_r = nodes_r.get("Principled BSDF")
    if bsdf_r:
        bsdf_r.inputs["Base Color"].default_value = (0.32, 0.29, 0.18, 1.0)
        bsdf_r.inputs["Metallic"].default_value = 0.55
        bsdf_r.inputs["Roughness"].default_value = 0.65

    return mat_poste, mat_placa, mat_relieve

def build_post_mesh(mat_poste, col):
    """
    Construye la columna de hierro fundido completa:
    - Base de campana (H = 0.45 m, D = 0.32 m con 16 facetas radiales suaves)
    - Fuste cilíndrico (H = 1.95 m, D = 0.085 m continuo)
    - Capitel ornamental tipo balustre (H = 0.18 m, D_max = 0.14 m)
    - Vástago cilíndrico de acero (H = 0.35 m, D = 0.025 m)
    - Abrazaderas dobles de sujeción a cotas z = 2.64 m y z = 2.74 m
    """
    bm = bmesh.new()
    NUM_SEGS = 32

    profile = []
    # 1. Base pedestal: Anillo de suelo (0.000 a 0.040 m, D = 0.32 m -> r = 0.160 m)
    profile.append((0.000, 0.160, 0.0))
    profile.append((0.010, 0.160, 0.0))
    profile.append((0.025, 0.160, 0.0))
    profile.append((0.040, 0.140, 0.0)) # Bisel perimetral hacia arriba (D = 0.28 m)

    # 2. Cuerpo de campana hiperbólico con acanalado/estriado de 16 facetas suaves
    num_bell = 16
    for i in range(1, num_bell + 1):
        t = i / float(num_bell)
        z = 0.04 + 0.30 * t
        r = 0.140 - 0.085 * (1.0 - math.exp(-3.2 * t)) / (1.0 - math.exp(-3.2))
        flute_amp = 0.0035 * math.sin(math.pi * t) # Relieve de 16 facetas
        profile.append((z, r, flute_amp))

    # 3. Moldura de transición (Cuello) (0.340 a 0.450 m)
    profile.append((0.345, 0.057, 0.0))
    # Toroide (bocel abultado de D = 0.13 m -> r = 0.065 m)
    profile.append((0.360, 0.062, 0.0))
    profile.append((0.375, 0.065, 0.0))
    profile.append((0.390, 0.062, 0.0))
    profile.append((0.400, 0.056, 0.0))
    # Escocia cóncava acoplada a D = 0.085 m (r = 0.0425 m)
    profile.append((0.415, 0.047, 0.0))
    profile.append((0.435, 0.0435, 0.0))
    profile.append((0.450, 0.0425, 0.0))

    # 4. Fuste (Columna Central) (0.450 a 2.400 m, D continuo 0.085 m)
    for i in range(1, 9):
        z = 0.45 + 1.95 * (i / 8.0)
        profile.append((z, 0.0425, 0.0))

    # 5. Capitel ornamental tipo balustre (2.400 a 2.580 m, H = 0.18 m)
    profile.append((2.408, 0.052, 0.0))
    profile.append((2.418, 0.055, 0.0)) # Collarín inferior (D = 0.11 m)
    profile.append((2.428, 0.048, 0.0))
    # Bulbo ornamental (D_max = 0.14 m -> r = 0.07 m)
    profile.append((2.445, 0.062, 0.0))
    profile.append((2.470, 0.070, 0.0)) # Cénit del bulbo
    profile.append((2.495, 0.064, 0.0))
    profile.append((2.520, 0.052, 0.0))
    profile.append((2.535, 0.055, 0.0)) # Collarín superior (D = 0.11 m)
    profile.append((2.550, 0.055, 0.0))
    profile.append((2.565, 0.040, 0.0))
    profile.append((2.580, 0.016, 0.0)) # Cuello hacia el vástago

    # 6. Vástago cilíndrico de acero (2.580 a 2.930 m, D = 0.025 m -> r = 0.0125 m)
    profile.append((2.585, 0.0125, 0.0))
    profile.append((2.640, 0.0125, 0.0))
    profile.append((2.740, 0.0125, 0.0))
    profile.append((2.930, 0.0125, 0.0))
    profile.append((2.936, 0.0140, 0.0))
    profile.append((2.941, 0.0080, 0.0))
    profile.append((2.943, 0.0000, 0.0))

    # Construir anillos de vértices
    ring_verts = []
    for (z, r, flute_amp) in profile:
        current_ring = []
        if r <= 0.0001:
            v = bm.verts.new((0.0, 0.0, z))
            current_ring.append(v)
        else:
            for s in range(NUM_SEGS):
                th = (2.0 * math.pi * s) / NUM_SEGS
                rad = r + flute_amp * math.cos(16.0 * th)
                x = rad * math.cos(th)
                y = rad * math.sin(th)
                current_ring.append(bm.verts.new((x, y, z)))
        ring_verts.append(current_ring)

    # Tapa de la base (z = 0.0)
    base_center = bm.verts.new((0.0, 0.0, 0.0))
    for s in range(NUM_SEGS):
        s_next = (s + 1) % NUM_SEGS
        bm.faces.new((base_center, ring_verts[0][s_next], ring_verts[0][s]))

    # Caras laterales del poste
    for r_idx in range(len(ring_verts) - 1):
        r1 = ring_verts[r_idx]
        r2 = ring_verts[r_idx + 1]
        if len(r2) == 1:
            apex = r2[0]
            for s in range(len(r1)):
                s_next = (s + 1) % len(r1)
                bm.faces.new((r1[s], r1[s_next], apex))
        else:
            for s in range(NUM_SEGS):
                s_next = (s + 1) % NUM_SEGS
                bm.faces.new((r1[s], r1[s_next], r2[s_next], r2[s]))

    # Abrazaderas dobles de montaje en cruz (en z = 2.64 m y z = 2.74 m)
    for z_c, angle_deg in [(2.64, 0), (2.74, 90)]:
        rad_clamp = 0.021
        c_ring1 = []
        c_ring2 = []
        for s in range(16):
            th = 2.0 * math.pi * s / 16.0
            x = rad_clamp * math.cos(th)
            y = rad_clamp * math.sin(th)
            c_ring1.append(bm.verts.new((x, y, z_c - 0.020)))
            c_ring2.append(bm.verts.new((x, y, z_c + 0.020)))
        for s in range(16):
            s_n = (s + 1) % 16
            bm.faces.new((c_ring1[s], c_ring1[s_n], c_ring2[s_n], c_ring2[s]))

    mesh = bpy.data.meshes.new("Poste_Columna_Mesh")
    bm.to_mesh(mesh)
    bm.free()

    mesh.materials.append(mat_poste)
    obj = bpy.data.objects.new("Poste_Estructura", mesh)
    col.objects.link(obj)

    for poly in mesh.polygons:
        poly.use_smooth = True

    return obj

def build_plate_object(name, mat_placa, mat_relieve, col, is_superior=False):
    """
    Construye la placa completa como una pieza sólida con 2 slots de material:
    - Base: M_Placa_Bronce_Patinado (Cuerpo rectangular 0.90 x 0.22 m con crestería a 0.32 m).
    - Relieves: M_Placa_Relieve_Laton (Marcos perimetrales, filete divisor 2/3 y crestería heráldica).
    """
    L = 0.90
    H = 0.22
    L2 = L / 2.0  # 0.45 m
    H2 = H / 2.0  # 0.11 m
    crest_x = -0.16 # Tercio superior izquierdo
    crest_r = 0.095 # Radio crestería
    n_arc = 18
    bw = 0.015     # Ancho marco
    div_x = 0.16   # División 2/3
    t_plate = 0.018 # Grosor base
    t_half = t_plate / 2.0
    h_relief = 0.0035 # Relieve sobresaliente

    # 1. Base prismática
    bm_base = bmesh.new()
    p_outer = []
    p_outer.append((-L2, -H2))
    p_outer.append(( L2, -H2))
    p_outer.append(( L2,  H2))
    p_outer.append((crest_x + crest_r, H2))
    for i in range(1, n_arc):
        a = (math.pi * i) / n_arc
        p_outer.append((crest_x + crest_r * math.cos(a), H2 + crest_r * math.sin(a)))
    p_outer.append((crest_x - crest_r, H2))
    p_outer.append((-L2, H2))

    v_base = [bm_base.verts.new((x, 0.0, z)) for (x, z) in p_outer]
    bm_base.faces.new(v_base)

    res_b = bmesh.ops.extrude_face_region(bm_base, geom=bm_base.faces)
    v_ext = [e for e in res_b['geom'] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm_base, vec=(0.0, t_plate, 0.0), verts=v_ext)
    bmesh.ops.translate(bm_base, vec=(0.0, -t_half, 0.0), verts=bm_base.verts)

    uv_base = bm_base.loops.layers.uv.new("UVMap")
    for face in bm_base.faces:
        for loop in face.loops:
            p = loop.vert.co
            u = (p.x + L2) / L
            v = (p.z + H2) / (H + crest_r)
            if p.y < 0:
                u = 1.0 - u
            loop[uv_base].uv = (u, v)

    mesh_base = bpy.data.meshes.new(f"{name}_BaseMesh")
    bm_base.to_mesh(mesh_base)
    bm_base.free()

    obj_base = bpy.data.objects.new(name, mesh_base)
    col.objects.link(obj_base)

    # 2. Relieves
    bm_rel = bmesh.new()
    for side_sign in [1.0, -1.0]:
        y_b = side_sign * t_half
        dy = side_sign * h_relief

        # Filete divisor
        vf = [
            bm_rel.verts.new((div_x - bw*0.5, y_b, -H2 + bw)),
            bm_rel.verts.new((div_x + bw*0.5, y_b, -H2 + bw)),
            bm_rel.verts.new((div_x + bw*0.5, y_b,  H2 - bw)),
            bm_rel.verts.new((div_x - bw*0.5, y_b,  H2 - bw)),
        ]
        ff = bm_rel.faces.new(vf)
        res_f = bmesh.ops.extrude_face_region(bm_rel, geom=[ff])
        bmesh.ops.translate(bm_rel, vec=(0.0, dy, 0.0), verts=[e for e in res_f['geom'] if isinstance(e, bmesh.types.BMVert)])

        # Marco inferior
        vb = [
            bm_rel.verts.new((-L2, y_b, -H2)),
            bm_rel.verts.new(( L2, y_b, -H2)),
            bm_rel.verts.new(( L2, y_b, -H2 + bw)),
            bm_rel.verts.new((-L2, y_b, -H2 + bw)),
        ]
        fb = bm_rel.faces.new(vb)
        res_bot = bmesh.ops.extrude_face_region(bm_rel, geom=[fb])
        bmesh.ops.translate(bm_rel, vec=(0.0, dy, 0.0), verts=[e for e in res_bot['geom'] if isinstance(e, bmesh.types.BMVert)])

        # Marco izquierdo
        vl = [
            bm_rel.verts.new((-L2, y_b, -H2 + bw)),
            bm_rel.verts.new((-L2 + bw, y_b, -H2 + bw)),
            bm_rel.verts.new((-L2 + bw, y_b,  H2 - bw)),
            bm_rel.verts.new((-L2, y_b,  H2 - bw)),
        ]
        fl = bm_rel.faces.new(vl)
        res_l = bmesh.ops.extrude_face_region(bm_rel, geom=[fl])
        bmesh.ops.translate(bm_rel, vec=(0.0, dy, 0.0), verts=[e for e in res_l['geom'] if isinstance(e, bmesh.types.BMVert)])

        # Marco derecho
        vr = [
            bm_rel.verts.new((L2 - bw, y_b, -H2 + bw)),
            bm_rel.verts.new((L2, y_b, -H2 + bw)),
            bm_rel.verts.new((L2, y_b,  H2 - bw)),
            bm_rel.verts.new((L2 - bw, y_b,  H2 - bw)),
        ]
        fr = bm_rel.faces.new(vr)
        res_r = bmesh.ops.extrude_face_region(bm_rel, geom=[fr])
        bmesh.ops.translate(bm_rel, vec=(0.0, dy, 0.0), verts=[e for e in res_r['geom'] if isinstance(e, bmesh.types.BMVert)])

        # Marco superior derecho
        vtr = [
            bm_rel.verts.new((crest_x + crest_r, y_b, H2 - bw)),
            bm_rel.verts.new((L2, y_b, H2 - bw)),
            bm_rel.verts.new((L2, y_b, H2)),
            bm_rel.verts.new((crest_x + crest_r, y_b, H2)),
        ]
        ftr = bm_rel.faces.new(vtr)
        res_tr = bmesh.ops.extrude_face_region(bm_rel, geom=[ftr])
        bmesh.ops.translate(bm_rel, vec=(0.0, dy, 0.0), verts=[e for e in res_tr['geom'] if isinstance(e, bmesh.types.BMVert)])

        # Marco superior izquierdo
        vtl = [
            bm_rel.verts.new((-L2, y_b, H2 - bw)),
            bm_rel.verts.new((crest_x - crest_r, y_b, H2 - bw)),
            bm_rel.verts.new((crest_x - crest_r, y_b, H2)),
            bm_rel.verts.new((-L2, y_b, H2)),
        ]
        ftl = bm_rel.faces.new(vtl)
        res_tl = bmesh.ops.extrude_face_region(bm_rel, geom=[ftl])
        bmesh.ops.translate(bm_rel, vec=(0.0, dy, 0.0), verts=[e for e in res_tl['geom'] if isinstance(e, bmesh.types.BMVert)])

        # Arco crestería
        r_in = crest_r - bw
        for i in range(n_arc):
            a1 = (math.pi * i) / n_arc
            a2 = (math.pi * (i + 1)) / n_arc
            p1_out = (crest_x + crest_r * math.cos(a1), y_b, H2 + crest_r * math.sin(a1))
            p2_out = (crest_x + crest_r * math.cos(a2), y_b, H2 + crest_r * math.sin(a2))
            p2_in  = (crest_x + r_in * math.cos(a2),    y_b, H2 + r_in * math.sin(a2))
            p1_in  = (crest_x + r_in * math.cos(a1),    y_b, H2 + r_in * math.sin(a1))
            va = [bm_rel.verts.new(p1_out), bm_rel.verts.new(p2_out), bm_rel.verts.new(p2_in), bm_rel.verts.new(p1_in)]
            fa = bm_rel.faces.new(va)
            res_a = bmesh.ops.extrude_face_region(bm_rel, geom=[fa])
            bmesh.ops.translate(bm_rel, vec=(0.0, dy, 0.0), verts=[e for e in res_a['geom'] if isinstance(e, bmesh.types.BMVert)])

        # Medallón interior
        r_med_out = r_in * 0.72
        r_med_in  = r_med_out - 0.008
        for i in range(n_arc):
            a1 = (math.pi * i) / n_arc
            a2 = (math.pi * (i + 1)) / n_arc
            p1_m_out = (crest_x + r_med_out * math.cos(a1), y_b, H2 + r_med_out * math.sin(a1))
            p2_m_out = (crest_x + r_med_out * math.cos(a2), y_b, H2 + r_med_out * math.sin(a2))
            p2_m_in  = (crest_x + r_med_in * math.cos(a2),  y_b, H2 + r_med_in * math.sin(a2))
            p1_m_in  = (crest_x + r_med_in * math.cos(a1),  y_b, H2 + r_med_in * math.sin(a1))
            vm = [bm_rel.verts.new(p1_m_out), bm_rel.verts.new(p2_m_out), bm_rel.verts.new(p2_m_in), bm_rel.verts.new(p1_m_in)]
            fm = bm_rel.faces.new(vm)
            res_m = bmesh.ops.extrude_face_region(bm_rel, geom=[fm])
            bmesh.ops.translate(bm_rel, vec=(0.0, side_sign * 0.0020, 0.0), verts=[e for e in res_m['geom'] if isinstance(e, bmesh.types.BMVert)])

    uv_rel = bm_rel.loops.layers.uv.new("UVMap")
    for face in bm_rel.faces:
        for loop in face.loops:
            p = loop.vert.co
            u = (p.x + L2) / L
            v = (p.z + H2) / (H + crest_r)
            if p.y < 0:
                u = 1.0 - u
            loop[uv_rel].uv = (u, v)

    mesh_rel = bpy.data.meshes.new(f"{name}_ReliefMesh")
    bm_rel.to_mesh(mesh_rel)
    bm_rel.free()

    obj_rel = bpy.data.objects.new(f"{name}_Relief", mesh_rel)
    col.objects.link(obj_rel)

    # Asignar Materiales
    obj_base.data.materials.append(mat_placa)
    obj_rel.data.materials.append(mat_relieve)

    # Unir ambas geometrías aislando la selección
    bpy.ops.object.select_all(action='DESELECT')
    obj_base.select_set(True)
    obj_rel.select_set(True)
    bpy.context.view_layer.objects.active = obj_base
    bpy.ops.object.join()
    obj_joined = bpy.context.active_object
    obj_joined.name = name

    # Posicionamiento exacto
    if is_superior:
        obj_joined.location = (0.0, 0.0, 2.74)
        obj_joined.rotation_euler = (0.0, 0.0, math.radians(90.0))
    else:
        obj_joined.location = (0.0, 0.0, 2.64)
        obj_joined.rotation_euler = (0.0, 0.0, 0.0)

    # Ajustar sombreado: las caras planas deben ser planas, no suaves, para evitar artefactos de luz
    for poly in obj_joined.data.polygons:
        if abs(poly.normal.y) > 0.5:
            poly.use_smooth = False
        else:
            poly.use_smooth = True

    return obj_joined

def build_demo_text_objects(mat_relieve):
    """
    Crea los textos 3D de demostración histórica según la especificación:
    - Placa Inferior: 'ESTEBAN CANTU' y 'C.P.\nHOSPITAL\nSANTA CATARINA'
    - Placa Superior: 'BENITO JUAREZ' y 'CLINICA\nHOSPITAL\nSANTA CATARINA'
    Se colocan en ambas caras (frontal y trasera) para visibilidad en 360°.
    """
    demo_col = bpy.data.collections.new("Texto_Demostracion_Ejemplo")
    bpy.context.scene.collection.children.link(demo_col)

    created_objs = []

    # Configuración de textos para Placa Inferior (en eje X)
    for side_sign, y_pos, rot_x, rot_z in [(1.0, 0.010, 90.0, 0.0), (-1.0, -0.010, 90.0, 180.0)]:
        # Nombre de calle
        t_c = bpy.data.curves.new(f"Txt_EstebanCantu_{'F' if side_sign > 0 else 'B'}", type='FONT')
        t_c.body = "ESTEBAN CANTU"
        t_c.size = 0.062
        t_c.extrude = 0.0022
        t_c.align_x = 'CENTER'
        t_c.align_y = 'CENTER'
        o_c = bpy.data.objects.new(f"Texto_EstebanCantu_{'F' if side_sign > 0 else 'B'}", t_c)
        o_c.location = (-0.14 * side_sign, y_pos, 2.64)
        o_c.rotation_euler = (math.radians(rot_x), 0.0, math.radians(rot_z))
        o_c.data.materials.append(mat_relieve)
        demo_col.objects.link(o_c)
        created_objs.append(o_c)

        # Colonia / C.P.
        t_cp = bpy.data.curves.new(f"Txt_Colonia1_{'F' if side_sign > 0 else 'B'}", type='FONT')
        t_cp.body = "C.P.\nHOSPITAL\nSANTA CATARINA"
        t_cp.size = 0.026
        t_cp.space_line = 1.15
        t_cp.extrude = 0.0018
        t_cp.align_x = 'CENTER'
        t_cp.align_y = 'CENTER'
        o_cp = bpy.data.objects.new(f"Texto_Colonia1_{'F' if side_sign > 0 else 'B'}", t_cp)
        o_cp.location = (0.295 * side_sign, y_pos, 2.64)
        o_cp.rotation_euler = (math.radians(rot_x), 0.0, math.radians(rot_z))
        o_cp.data.materials.append(mat_relieve)
        demo_col.objects.link(o_cp)
        created_objs.append(o_cp)

    # Configuración de textos para Placa Superior (en eje Y)
    for side_sign, x_pos, rot_x, rot_z in [(-1.0, -0.010, 90.0, 90.0), (1.0, 0.010, 90.0, -90.0)]:
        # Nombre de calle
        t_j = bpy.data.curves.new(f"Txt_BenitoJuarez_{'F' if side_sign < 0 else 'B'}", type='FONT')
        t_j.body = "BENITO JUAREZ"
        t_j.size = 0.062
        t_j.extrude = 0.0022
        t_j.align_x = 'CENTER'
        t_j.align_y = 'CENTER'
        o_j = bpy.data.objects.new(f"Texto_BenitoJuarez_{'F' if side_sign < 0 else 'B'}", t_j)
        o_j.location = (x_pos, -0.14 * (-side_sign), 2.74)
        o_j.rotation_euler = (math.radians(rot_x), 0.0, math.radians(rot_z))
        o_j.data.materials.append(mat_relieve)
        demo_col.objects.link(o_j)
        created_objs.append(o_j)

        # Colonia / C.P.
        t_cp2 = bpy.data.curves.new(f"Txt_Colonia2_{'F' if side_sign < 0 else 'B'}", type='FONT')
        t_cp2.body = "CLINICA\nHOSPITAL\nSANTA CATARINA"
        t_cp2.size = 0.026
        t_cp2.space_line = 1.15
        t_cp2.extrude = 0.0018
        t_cp2.align_x = 'CENTER'
        t_cp2.align_y = 'CENTER'
        o_cp2 = bpy.data.objects.new(f"Texto_Colonia2_{'F' if side_sign < 0 else 'B'}", t_cp2)
        o_cp2.location = (x_pos, 0.295 * (-side_sign), 2.74)
        o_cp2.rotation_euler = (math.radians(rot_x), 0.0, math.radians(rot_z))
        o_cp2.data.materials.append(mat_relieve)
        demo_col.objects.link(o_cp2)
        created_objs.append(o_cp2)

    # Convertir textos a mallas para exportación glTF
    bpy.ops.object.select_all(action='DESELECT')
    for o in created_objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = created_objs[0]
    bpy.ops.object.convert(target='MESH')

    return demo_col

def setup_lighting_and_cameras():
    """Configura iluminación de estudio de tres puntos y Cycles CPU."""
    # Key Light
    sun_data = bpy.data.lights.new('Luz_Key_Sun', type='SUN')
    sun_data.energy = 4.5
    sun_data.color = (1.0, 0.98, 0.94)
    sun = bpy.data.objects.new('Luz_Key_Sun', sun_data)
    bpy.context.scene.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(50.0), math.radians(20.0), math.radians(-35.0))

    # Fill Light
    fill_data = bpy.data.lights.new('Luz_Fill_Sun', type='SUN')
    fill_data.energy = 2.0
    fill_data.color = (0.75, 0.85, 1.0)
    fill = bpy.data.objects.new('Luz_Fill_Sun', fill_data)
    bpy.context.scene.collection.objects.link(fill)
    fill.rotation_euler = (math.radians(65.0), math.radians(-35.0), math.radians(145.0))

    # Rim Light
    rim_data = bpy.data.lights.new('Luz_Rim_Sun', type='SUN')
    rim_data.energy = 2.8
    rim_data.color = (1.0, 0.92, 0.80)
    rim = bpy.data.objects.new('Luz_Rim_Sun', rim_data)
    bpy.context.scene.collection.objects.link(rim)
    rim.rotation_euler = (math.radians(30.0), math.radians(-50.0), math.radians(-160.0))

    # Luz de Entorno Ambiental (World Ambient)
    world = bpy.context.scene.world
    if not world:
        world = bpy.data.worlds.new('World')
        bpy.context.scene.world = world
    bg = world.node_tree.nodes.get('Background')
    if bg:
        bg.inputs['Color'].default_value = (0.78, 0.85, 0.92, 1.0)
        bg.inputs['Strength'].default_value = 1.0

    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.device = 'CPU'
    bpy.context.scene.cycles.samples = 32
    bpy.context.scene.render.film_transparent = True

def render_views():
    """Genera los 3 renders técnicos oficiales de inspección."""
    # 1. Vista Completa General (2.95 m de altura enmarcado al 85%)
    cam1_d = bpy.data.cameras.new("Cam_General")
    cam1_d.lens = 36
    cam1 = bpy.data.objects.new("Cam_General", cam1_d)
    bpy.context.scene.collection.objects.link(cam1)
    bpy.context.scene.camera = cam1

    cam1.location = (2.8, -3.5, 1.475)
    cam1.rotation_euler = (math.radians(90.0), 0.0, math.radians(38.66))

    bpy.context.scene.render.resolution_x = 900
    bpy.context.scene.render.resolution_y = 1800
    p1 = "docs/images/poste_nomenclatura_preview.png"
    bpy.context.scene.render.filepath = f"//{p1}"
    bpy.ops.render.render(write_still=True)
    print(f"Render general guardado: {p1}")

    # 2. Acercamiento a las Placas de Nomenclatura (z = 2.70 m)
    cam2_d = bpy.data.cameras.new("Cam_Placas")
    cam2_d.lens = 65
    cam2 = bpy.data.objects.new("Cam_Placas", cam2_d)
    bpy.context.scene.collection.objects.link(cam2)
    bpy.context.scene.camera = cam2

    cam2.location = (1.2, -1.4, 2.78)
    cam2.rotation_euler = (math.radians(85.0), 0.0, math.radians(40.0))

    bpy.context.scene.render.resolution_x = 1200
    bpy.context.scene.render.resolution_y = 1200
    p2 = "docs/images/poste_nomenclatura_closeup.png"
    bpy.context.scene.render.filepath = f"//{p2}"
    bpy.ops.render.render(write_still=True)
    print(f"Render acercamiento guardado: {p2}")

    # 3. Acercamiento a la Base de Campana / Pedestal (z = 0.22 m)
    cam3_d = bpy.data.cameras.new("Cam_Base")
    cam3_d.lens = 50
    cam3 = bpy.data.objects.new("Cam_Base", cam3_d)
    bpy.context.scene.collection.objects.link(cam3)
    bpy.context.scene.camera = cam3

    cam3.location = (1.0, -1.2, 0.28)
    cam3.rotation_euler = (math.radians(88.0), 0.0, math.radians(39.8))

    bpy.context.scene.render.resolution_x = 1000
    bpy.context.scene.render.resolution_y = 1000
    p3 = "docs/images/poste_nomenclatura_base.png"
    bpy.context.scene.render.filepath = f"//{p3}"
    bpy.ops.render.render(write_still=True)
    print(f"Render base guardado: {p3}")

def main():
    print("================================================================")
    print(" INICIANDO GENERACIÓN DEL POSTE DE NOMENCLATURA URBANA TECATE   ")
    print("================================================================")
    clean_scene()

    # 1. Crear Colección Principal del Asset
    main_col = bpy.data.collections.new("Poste_Nomenclatura_Tecate")
    bpy.context.scene.collection.children.link(main_col)

    # 2. Configurar Materiales PBR Físicos
    mat_poste, mat_placa, mat_relieve = create_materials()

    # 3. Construir Poste de Hierro (Pedestal + Fuste + Capitel + Vástago)
    obj_poste = build_post_mesh(mat_poste, main_col)

    # 4. Construir Placas de Nomenclatura Perpendiculares
    obj_placa_inf = build_plate_object("Placa_Inferior", mat_placa, mat_relieve, main_col, is_superior=False)
    obj_placa_sup = build_plate_object("Placa_Superior", mat_placa, mat_relieve, main_col, is_superior=True)

    # Emparentar placas a la columna central
    obj_placa_inf.parent = obj_poste
    obj_placa_sup.parent = obj_poste

    # 5. Generar Textos 3D de Muestra en Colección Independiente
    demo_col = build_demo_text_objects(mat_relieve)
    for txt_o in demo_col.objects:
        if "Esteban" in txt_o.name or "Colonia1" in txt_o.name:
            txt_o.parent = obj_placa_inf
        else:
            txt_o.parent = obj_placa_sup

    # 6. Configurar iluminación y cámaras antes de guardar el .blend
    setup_lighting_and_cameras()

    # Actualizar transformaciones globales
    bpy.context.view_layer.update()

    # Validación dimensional
    all_objs = [obj_poste, obj_placa_inf, obj_placa_sup]
    min_z = min([min([(obj.matrix_world @ Vector(corner)).z for corner in obj.bound_box]) for obj in all_objs])
    max_z = max([max([(obj.matrix_world @ Vector(corner)).z for corner in obj.bound_box]) for obj in all_objs])
    total_height = max_z - min_z

    print(f"--> Altura Total Verificada: {total_height:.4f} m (Min Z: {min_z:.4f} m, Max Z: {max_z:.4f} m)")
    print(f"--> Diámetro Base: {obj_poste.dimensions.x:.4f} m x {obj_poste.dimensions.y:.4f} m")

    # 7. Guardar archivo .blend maestro en blender_assets/
    blend_path = "blender_assets/poste_nomenclatura_tecate.blend"
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"--> Archivo maestro guardado: {blend_path}")

    # 8. Exportar versión modular limpia para Godot (sin textos fijos)
    bpy.ops.object.select_all(action='DESELECT')
    for o in all_objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obj_poste

    glb_clean_path = "godot_project/assets/poste_nomenclatura_tecate.glb"
    bpy.ops.export_scene.gltf(
        filepath=glb_clean_path,
        export_format='GLB',
        use_selection=True,
        export_apply=False,
        export_materials='EXPORT',
        export_yup=True
    )
    print(f"--> Asset Godot modular exportado: {glb_clean_path}")

    # 9. Exportar versión con texto demo (para previsualización directa)
    bpy.ops.object.select_all(action='DESELECT')
    for o in all_objs + list(demo_col.objects):
        o.select_set(True)
    bpy.context.view_layer.objects.active = obj_poste

    glb_demo_path = "godot_project/assets/poste_nomenclatura_tecate_demo.glb"
    bpy.ops.export_scene.gltf(
        filepath=glb_demo_path,
        export_format='GLB',
        use_selection=True,
        export_apply=False,
        export_materials='EXPORT',
        export_yup=True
    )
    print(f"--> Asset Godot demo con texto exportado: {glb_demo_path}")

    # 10. Generar Renders oficiales
    render_views()

    print("================================================================")
    print(" GENERACIÓN FINALIZADA SATISFACTORIAMENTE                       ")
    print("================================================================")

if __name__ == "__main__":
    main()
