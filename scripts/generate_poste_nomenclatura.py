"""
=============================================================================
Generador 3D Paramétrico: Poste de Nomenclatura Urbana Clásica de Tecate, B.C.
=============================================================================
Este script automatiza la creación completa del asset de señalización urbana:
1. Pedestal / Base de campana con 16 facetas radiales y molduras clásicas.
2. Fuste tubular continuo de hierro fundido (H = 1.78 m, D = 0.085 m).
3. Capitel ornamental tipo balustre (H = 0.18 m) con collares y vástago.
4. Placa Inferior (Eje X):
   - Cota Z: 2.41 a 2.63 m (H = 0.22 m, centro Z = 2.52 m).
   - Rectangular pura 0.90 x 0.22 m sin crestería superior (lomo recto continuo).
   - Recuadro 2/3 izquierdo para calle (verde cardenillo).
   - Filete divisor vertical en relieve (latón).
   - Recuadro 1/3 derecho para patrocinador (blanco esmaltado).
5. Placa Superior (Eje Y, a 90°):
   - Cota Z: 2.63 a 2.85 m (H = 0.22 m, centro Z = 2.74 m).
   - Reposa directamente sobre la inferior (Z = 2.63 m), CERO clipping.
   - Crestería semicircular centrada en la longitud total (x = 0.0 m, Z = 2.85 a 2.95 m).
   - Inscripción en arco concéntrico 'AYUNTAMIENTO'.
   - Número central '17' con serifa superior en el 1 y asta dinámica en el 7.
   - Recuadro 2/3 para calle y recuadro 1/3 para patrocinador (blanco esmaltado).
6. Altura total exacta: 2.95 m.
7. Materiales PBR calibrados para StandardMaterial3D (ORM) de Godot 4.
8. Exportaciones .blend y .glb (modular limpio y demo con textos de calle).
=============================================================================
"""

import os
import bpy
import bmesh
import math
from mathutils import Vector, Matrix, Euler

FONT_CAST_METAL = "godot_project/assets/fonts/DIN_Condensed_Bold.ttf"

def get_cast_metal_font():
    """Carga y devuelve la tipografía histórica de fundición DIN 1451 Engschrift / Grotesque Condensed."""
    if os.path.exists(FONT_CAST_METAL):
        for f in bpy.data.fonts:
            if "DIN" in f.name:
                return f
        try:
            return bpy.data.fonts.load(os.path.abspath(FONT_CAST_METAL))
        except Exception:
            pass
    return None

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
    Crea los 4 materiales PBR físicamente basados:
    1. M_Hierro_Fundido_Poste: Poste y herrajes (gris plomo oscuro #2C2A26).
    2. M_Placa_Bronce_Patinado: Fondo de calle y semicírculo (verde cardenillo #3E4E40).
    3. M_Placa_Relieve_Laton: Molduras, letras y 17 (latón desgastado #8A856A).
    4. M_Placa_Recuadro_Blanco: Recuadro derecho para patrocinador (#EDEDE8).
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

    # 4. Placas: Recuadro lateral de patrocinador (Blanco esmaltado)
    mat_blanco = bpy.data.materials.new(name="M_Placa_Recuadro_Blanco")
    nodes_w = mat_blanco.node_tree.nodes
    bsdf_w = nodes_w.get("Principled BSDF")
    if bsdf_w:
        bsdf_w.inputs["Base Color"].default_value = (0.82, 0.82, 0.78, 1.0) # #EDEDE8
        bsdf_w.inputs["Metallic"].default_value = 0.05
        bsdf_w.inputs["Roughness"].default_value = 0.55

    return mat_poste, mat_placa, mat_relieve, mat_blanco

def build_post_mesh(mat_poste, col):
    """
    Construye la columna de hierro fundido ajustada para apilamiento limpio:
    - Base de campana (H = 0.45 m, D = 0.32 m con 16 facetas radiales)
    - Fuste cilíndrico (0.45 a 2.23 m, H = 1.78 m, D = 0.085 m)
    - Capitel ornamental tipo balustre (2.23 a 2.41 m, H = 0.18 m, D_max = 0.14 m)
    - Vástago cilíndrico interior de acero (2.41 a 2.93 m, D = 0.025 m)
    - Abrazaderas dobles de sujeción a cotas z = 2.52 m y z = 2.74 m
    """
    bm = bmesh.new()
    NUM_SEGS = 32

    profile = []
    # 1. Base pedestal: Anillo de suelo (0.000 a 0.040 m, D = 0.32 m -> r = 0.160 m)
    profile.append((0.000, 0.160, 0.0))
    profile.append((0.010, 0.160, 0.0))
    profile.append((0.025, 0.160, 0.0))
    profile.append((0.040, 0.140, 0.0))

    # 2. Cuerpo de campana hiperbólico con acanalado/estriado de 16 facetas suaves
    num_bell = 16
    for i in range(1, num_bell + 1):
        t = i / float(num_bell)
        z = 0.04 + 0.30 * t
        r = 0.140 - 0.085 * (1.0 - math.exp(-3.2 * t)) / (1.0 - math.exp(-3.2))
        flute_amp = 0.0035 * math.sin(math.pi * t)
        profile.append((z, r, flute_amp))

    # 3. Moldura de transición (Cuello) (0.340 a 0.450 m)
    profile.append((0.345, 0.057, 0.0))
    profile.append((0.360, 0.062, 0.0))
    profile.append((0.375, 0.065, 0.0))
    profile.append((0.390, 0.062, 0.0))
    profile.append((0.400, 0.056, 0.0))
    profile.append((0.415, 0.047, 0.0))
    profile.append((0.435, 0.0435, 0.0))
    profile.append((0.450, 0.0425, 0.0))

    # 4. Fuste (Columna Central) (0.450 a 2.230 m, D continuo 0.085 m)
    for i in range(1, 9):
        z = 0.45 + 1.78 * (i / 8.0)
        profile.append((z, 0.0425, 0.0))

    # 5. Capitel ornamental tipo balustre (2.230 a 2.410 m, H = 0.18 m)
    profile.append((2.238, 0.052, 0.0))
    profile.append((2.248, 0.055, 0.0)) # Collarín inferior
    profile.append((2.258, 0.048, 0.0))
    profile.append((2.275, 0.062, 0.0))
    profile.append((2.300, 0.070, 0.0)) # Cénit del bulbo
    profile.append((2.325, 0.064, 0.0))
    profile.append((2.350, 0.052, 0.0))
    profile.append((2.365, 0.055, 0.0)) # Collarín superior
    profile.append((2.380, 0.055, 0.0))
    profile.append((2.395, 0.040, 0.0))
    profile.append((2.410, 0.016, 0.0)) # Asiento de la placa inferior

    # 6. Vástago cilíndrico interior de acero y collarines de asiento
    # Sube desde el capitel (2.410 m) a través de los collarines de montaje
    profile.append((2.410, 0.022, 0.0)) # Collarín base placa inferior
    profile.append((2.415, 0.022, 0.0))
    profile.append((2.420, 0.008, 0.0)) # Eje interior (oculto dentro de la placa)
    profile.append((2.625, 0.008, 0.0))
    profile.append((2.630, 0.022, 0.0)) # Collarín asiento placa superior
    profile.append((2.635, 0.022, 0.0))
    profile.append((2.640, 0.008, 0.0)) # Eje interior placa superior
    profile.append((2.740, 0.008, 0.0)) # Cénit del eje en centro de la placa superior
    profile.append((2.745, 0.000, 0.0)) # Termina limpio sin invadir la crestería

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

    base_center = bm.verts.new((0.0, 0.0, 0.0))
    for s in range(NUM_SEGS):
        s_next = (s + 1) % NUM_SEGS
        bm.faces.new((base_center, ring_verts[0][s_next], ring_verts[0][s]))

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
    mesh = bpy.data.meshes.new("Poste_Columna_Mesh")
    bm.to_mesh(mesh)
    bm.free()

    mesh.materials.append(mat_poste)
    obj = bpy.data.objects.new("Poste_Estructura", mesh)
    col.objects.link(obj)

    for poly in mesh.polygons:
        poly.use_smooth = True

    return obj

def build_lower_plate(mat_placa, mat_relieve, mat_blanco, col):
    """
    Construye la Placa Inferior:
    - Cota: z = 2.41 a 2.63 m (centro en z = 2.52 m), orientación en eje X (0°).
    - Rectangular pura 0.90 x 0.22 m sin crestería superior (lomo recto sobre el cual reposa la superior).
    - Recuadro 2/3 izquierdo (calle) en verde cardenillo.
    - Filete divisor en altorrelieve (latón).
    - Recuadro 1/3 derecho (patrocinador) en blanco esmaltado.
    """
    L = 0.90
    H = 0.22
    L2 = L / 2.0
    H2 = H / 2.0
    bw = 0.015
    div_x = 0.16
    t_plate = 0.018
    t_half = t_plate / 2.0
    h_relief = 0.0035

    # 1. Base prismática rectangular
    bm_base = bmesh.new()
    p_outer = [(-L2, -H2), (L2, -H2), (L2, H2), (-L2, H2)]
    v_base = [bm_base.verts.new((x, 0.0, z)) for (x, z) in p_outer]
    bm_base.faces.new(v_base)

    res_b = bmesh.ops.extrude_face_region(bm_base, geom=bm_base.faces)
    v_ext = [e for e in res_b['geom'] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm_base, vec=(0.0, t_plate, 0.0), verts=v_ext)
    bmesh.ops.translate(bm_base, vec=(0.0, -t_half, 0.0), verts=bm_base.verts)

    # UV base
    uv_b = bm_base.loops.layers.uv.new("UVMap")
    for face in bm_base.faces:
        for loop in face.loops:
            p = loop.vert.co
            u = (p.x + L2) / L
            v = (p.z + H2) / H
            if p.y < 0:
                u = 1.0 - u
            loop[uv_b].uv = (u, v)

    mesh_base = bpy.data.meshes.new("Placa_Inferior_BaseMesh")
    bm_base.to_mesh(mesh_base)
    bm_base.free()

    obj_base = bpy.data.objects.new("Placa_Inferior", mesh_base)
    col.objects.link(obj_base)

    # 2. Relieves y marcos
    bm_rel = bmesh.new()
    for side_sign in [1.0, -1.0]:
        y_b = side_sign * t_half
        dy = side_sign * h_relief
        div_x_side = -div_x if side_sign > 0 else div_x

        # Filete divisor
        vf = [
            bm_rel.verts.new((div_x_side - bw*0.5, y_b, -H2 + bw)),
            bm_rel.verts.new((div_x_side + bw*0.5, y_b, -H2 + bw)),
            bm_rel.verts.new((div_x_side + bw*0.5, y_b,  H2 - bw)),
            bm_rel.verts.new((div_x_side - bw*0.5, y_b,  H2 - bw)),
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

        # Marco superior completo
        vt = [
            bm_rel.verts.new((-L2, y_b, H2 - bw)),
            bm_rel.verts.new(( L2, y_b, H2 - bw)),
            bm_rel.verts.new(( L2, y_b, H2)),
            bm_rel.verts.new((-L2, y_b, H2)),
        ]
        ft = bm_rel.faces.new(vt)
        res_top = bmesh.ops.extrude_face_region(bm_rel, geom=[ft])
        bmesh.ops.translate(bm_rel, vec=(0.0, dy, 0.0), verts=[e for e in res_top['geom'] if isinstance(e, bmesh.types.BMVert)])

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

    uv_rel = bm_rel.loops.layers.uv.new("UVMap")
    for face in bm_rel.faces:
        for loop in face.loops:
            p = loop.vert.co
            u = (p.x + L2) / L
            v = (p.z + H2) / H
            if p.y < 0:
                u = 1.0 - u
            loop[uv_rel].uv = (u, v)

    mesh_rel = bpy.data.meshes.new("Placa_Inferior_ReliefMesh")
    bm_rel.to_mesh(mesh_rel)
    bm_rel.free()

    obj_rel = bpy.data.objects.new("Placa_Inferior_Relief", mesh_rel)
    col.objects.link(obj_rel)

    # 3. Caras del Recuadro Blanco de Patrocinador (1/3 derecho)
    bm_w = bmesh.new()
    for side_sign in [1.0, -1.0]:
        y_w = side_sign * (t_half + 0.0005) # Ligeramente por encima del fondo
        div_x_side = -div_x if side_sign > 0 else div_x
        if side_sign > 0:
            x_left = -L2 + bw
            x_right = div_x_side - bw * 0.5
        else:
            x_left = div_x_side + bw * 0.5
            x_right = L2 - bw

        v_w = [
            bm_w.verts.new((x_left, y_w, -H2 + bw)),
            bm_w.verts.new((x_right, y_w, -H2 + bw)),
            bm_w.verts.new((x_right, y_w,  H2 - bw)),
            bm_w.verts.new((x_left, y_w,  H2 - bw)),
        ]
        if side_sign < 0:
            v_w = list(reversed(v_w))
        bm_w.faces.new(v_w)

    uv_w = bm_w.loops.layers.uv.new("UVMap")
    for face in bm_w.faces:
        for loop in face.loops:
            p = loop.vert.co
            if p.y > 0:
                div_x_side = -div_x
                xr = div_x_side - bw * 0.5
                xl = -L2 + bw
                u = (xr - p.x) / (xr - xl)
            else:
                div_x_side = div_x
                xl = div_x_side + bw * 0.5
                xr = L2 - bw
                u = (p.x - xl) / (xr - xl)
            v = (p.z + H2 - bw) / (2.0 * (H2 - bw))
            loop[uv_w].uv = (u, v)

    mesh_w = bpy.data.meshes.new("Placa_Inferior_WhiteMesh")
    bm_w.to_mesh(mesh_w)
    bm_w.free()

    obj_w = bpy.data.objects.new("Placa_Inferior_White", mesh_w)
    col.objects.link(obj_w)

    # Asignar Slots de Material
    # Slot 0: Fondo Bronce Patinado
    # Slot 1: Relieve Latón
    # Slot 2: Recuadro Blanco
    obj_base.data.materials.append(mat_placa)
    obj_rel.data.materials.append(mat_relieve)
    obj_w.data.materials.append(mat_blanco)

    # Unir en un único objeto
    bpy.ops.object.select_all(action='DESELECT')
    obj_base.select_set(True)
    obj_rel.select_set(True)
    obj_w.select_set(True)
    bpy.context.view_layer.objects.active = obj_base
    bpy.ops.object.join()
    obj_joined = bpy.context.active_object
    obj_joined.name = "Placa_Inferior"

    # Posición: z = 2.52 m (base en 2.41, tope en 2.63 m)
    obj_joined.location = (0.0, 0.0, 2.52)
    obj_joined.rotation_euler = (0.0, 0.0, 0.0)

    for poly in obj_joined.data.polygons:
        if abs(poly.normal.y) > 0.5:
            poly.use_smooth = False
        else:
            poly.use_smooth = True

    return obj_joined

def build_upper_plate(mat_placa, mat_relieve, mat_blanco, col):
    """
    Construye la Placa Superior:
    - Cota: z = 2.63 a 2.85 m (centro en z = 2.74 m), rotada 90° (eje Y).
    - Reposa directamente sobre la inferior (Z = 2.63 m), sin intersección.
    - Semicírculo centrado en la longitud total (x = 0.0 m, r = 0.10 m), alcanzando Z = 2.95 m.
    - Marco perimetral altorrelieve de 9 mm en toda la crestería.
    - Inscripción curva en arco continuo 'AYUNTAMIENTO'.
    - Número central '17' con serifa superior en el 1 y asta dinámica en el 7.
    - Recuadro 2/3 para calle y recuadro 1/3 para patrocinador (blanco esmaltado).
    """
    L = 0.90
    H = 0.22
    L2 = L / 2.0  # 0.45 m
    H2 = H / 2.0  # 0.11 m
    crest_x = 0.0 # ¡CENTRADO EN LA LONGITUD COMPLETA!
    crest_r = 0.10 # Radio de 10 cm (sobresale 0.10 m)
    n_arc = 24
    bw = 0.015     # Ancho marco rectangular
    bw_crest = 0.009 # Ancho pestaña crestería (9 mm según spec)
    div_x = 0.16   # Filete divisor en 2/3
    t_plate = 0.018 # Grosor base
    t_half = t_plate / 2.0
    h_relief = 0.0035

    # 1. Base prismática con semicírculo centrado
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

    uv_b = bm_base.loops.layers.uv.new("UVMap")
    for face in bm_base.faces:
        for loop in face.loops:
            p = loop.vert.co
            u = (p.x + L2) / L
            v = (p.z + H2) / (H + crest_r)
            if p.y < 0:
                u = 1.0 - u
            loop[uv_b].uv = (u, v)

    mesh_base = bpy.data.meshes.new("Placa_Superior_BaseMesh")
    bm_base.to_mesh(mesh_base)
    bm_base.free()

    obj_base = bpy.data.objects.new("Placa_Superior", mesh_base)
    col.objects.link(obj_base)

    # 2. Relieves (Marcos, Filete divisor y Arco de Crestería)
    bm_rel = bmesh.new()
    for side_sign in [1.0, -1.0]:
        y_b = side_sign * t_half
        dy = side_sign * h_relief
        div_x_side = -div_x if side_sign > 0 else div_x

        # Filete divisor
        vf = [
            bm_rel.verts.new((div_x_side - bw*0.5, y_b, -H2 + bw)),
            bm_rel.verts.new((div_x_side + bw*0.5, y_b, -H2 + bw)),
            bm_rel.verts.new((div_x_side + bw*0.5, y_b,  H2 - bw)),
            bm_rel.verts.new((div_x_side - bw*0.5, y_b,  H2 - bw)),
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

        # Marco superior derecho (de x = +crest_r a +L2)
        vtr = [
            bm_rel.verts.new((crest_x + crest_r, y_b, H2 - bw)),
            bm_rel.verts.new((L2, y_b, H2 - bw)),
            bm_rel.verts.new((L2, y_b, H2)),
            bm_rel.verts.new((crest_x + crest_r, y_b, H2)),
        ]
        ftr = bm_rel.faces.new(vtr)
        res_tr = bmesh.ops.extrude_face_region(bm_rel, geom=[ftr])
        bmesh.ops.translate(bm_rel, vec=(0.0, dy, 0.0), verts=[e for e in res_tr['geom'] if isinstance(e, bmesh.types.BMVert)])

        # Marco superior izquierdo (de x = -L2 a -crest_r)
        vtl = [
            bm_rel.verts.new((-L2, y_b, H2 - bw)),
            bm_rel.verts.new((crest_x - crest_r, y_b, H2 - bw)),
            bm_rel.verts.new((crest_x - crest_r, y_b, H2)),
            bm_rel.verts.new((-L2, y_b, H2)),
        ]
        ftl = bm_rel.faces.new(vtl)
        res_tl = bmesh.ops.extrude_face_region(bm_rel, geom=[ftl])
        bmesh.ops.translate(bm_rel, vec=(0.0, dy, 0.0), verts=[e for e in res_tl['geom'] if isinstance(e, bmesh.types.BMVert)])

        # Arco perimetral de crestería (pestaña de 9 mm)
        r_in = crest_r - bw_crest
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

    uv_rel = bm_rel.loops.layers.uv.new("UVMap")
    for face in bm_rel.faces:
        for loop in face.loops:
            p = loop.vert.co
            u = (p.x + L2) / L
            v = (p.z + H2) / (H + crest_r)
            if p.y < 0:
                u = 1.0 - u
            loop[uv_rel].uv = (u, v)

    mesh_rel = bpy.data.meshes.new("Placa_Superior_ReliefMesh")
    bm_rel.to_mesh(mesh_rel)
    bm_rel.free()

    obj_rel = bpy.data.objects.new("Placa_Superior_Relief", mesh_rel)
    col.objects.link(obj_rel)

    # 3. Recuadro Blanco de Patrocinador (1/3 derecho)
    bm_w = bmesh.new()
    for side_sign in [1.0, -1.0]:
        y_w = side_sign * (t_half + 0.0005)
        div_x_side = -div_x if side_sign > 0 else div_x
        if side_sign > 0:
            x_left = -L2 + bw
            x_right = div_x_side - bw * 0.5
        else:
            x_left = div_x_side + bw * 0.5
            x_right = L2 - bw

        v_w = [
            bm_w.verts.new((x_left, y_w, -H2 + bw)),
            bm_w.verts.new((x_right, y_w, -H2 + bw)),
            bm_w.verts.new((x_right, y_w,  H2 - bw)),
            bm_w.verts.new((x_left, y_w,  H2 - bw)),
        ]
        if side_sign < 0:
            v_w = list(reversed(v_w))
        bm_w.faces.new(v_w)

    uv_w = bm_w.loops.layers.uv.new("UVMap")
    for face in bm_w.faces:
        for loop in face.loops:
            p = loop.vert.co
            if p.y > 0:
                div_x_side = -div_x
                xr = div_x_side - bw * 0.5
                xl = -L2 + bw
                u = (xr - p.x) / (xr - xl)
            else:
                div_x_side = div_x
                xl = div_x_side + bw * 0.5
                xr = L2 - bw
                u = (p.x - xl) / (xr - xl)
            v = (p.z + H2 - bw) / (2.0 * (H2 - bw))
            loop[uv_w].uv = (u, v)

    mesh_w = bpy.data.meshes.new("Placa_Superior_WhiteMesh")
    bm_w.to_mesh(mesh_w)
    bm_w.free()

    obj_w = bpy.data.objects.new("Placa_Superior_White", mesh_w)
    col.objects.link(obj_w)

    # 4. Inscripción 'AYUNTAMIENTO' y Número '17' en altorrelieve 3D (ambas caras)
    # Se construyen como mallas y se unen con material de relieve
    heraldic_objs = []
    word = "AYUNTAMIENTO"
    n_chars = len(word)
    r_arc_txt = 0.076 # Radio medio de curvatura del texto
    span_deg = 126.0
    start_deg = 90.0 - span_deg / 2.0

    f_font = get_cast_metal_font()
    for side_sign in [1.0, -1.0]:
        y_txt = side_sign * (t_half + 0.0025)

        # Caracteres de AYUNTAMIENTO
        for i, ch in enumerate(word):
            ang_deg = start_deg + i * (span_deg / (n_chars - 1))
            ang_rad = math.radians(ang_deg)

            if side_sign > 0:
                px = r_arc_txt * math.cos(ang_rad)
                pz = H2 + r_arc_txt * math.sin(ang_rad)
                # Cara +Y: Normal = (0, 1, 0), Up = radial (cos, 0, sin), Right = tangente (-sin, 0, cos)
                vr = Vector((-math.sin(ang_rad), 0.0, math.cos(ang_rad)))
                vu = Vector((math.cos(ang_rad), 0.0, math.sin(ang_rad)))
                vn = Vector((0.0, 1.0, 0.0))
            else:
                px = -r_arc_txt * math.cos(ang_rad)
                pz = H2 + r_arc_txt * math.sin(ang_rad)
                # Cara -Y: Normal = (0, -1, 0), Up = radial (-cos, 0, sin), Right = tangente (sin, 0, cos)
                vr = Vector((math.sin(ang_rad), 0.0, math.cos(ang_rad)))
                vu = Vector((-math.cos(ang_rad), 0.0, math.sin(ang_rad)))
                vn = Vector((0.0, -1.0, 0.0))

            mat_rot = Matrix.Identity(3)
            mat_rot.col[0] = vr
            mat_rot.col[1] = vu
            mat_rot.col[2] = vn
            rot_euler = mat_rot.to_euler()

            txt_d = bpy.data.curves.new(f"Txt_Ayto_{ch}_{i}_{side_sign}", type='FONT')
            if f_font:
                txt_d.font = f_font
            txt_d.body = ch
            txt_d.size = 0.017
            txt_d.extrude = 0.0022
            txt_d.align_x = 'CENTER'
            txt_d.align_y = 'CENTER'

            o_ch = bpy.data.objects.new(f"Obj_Ayto_{ch}_{i}_{side_sign}", txt_d)
            o_ch.location = (px, y_txt, pz)
            o_ch.rotation_euler = rot_euler
            o_ch.data.materials.append(mat_relieve)
            col.objects.link(o_ch)
            heraldic_objs.append(o_ch)

        # Número 17 en el centro geométrico
        txt_17 = bpy.data.curves.new(f"Txt_Num17_{side_sign}", type='FONT')
        if f_font:
            txt_17.font = f_font
        txt_17.body = "17"
        txt_17.size = 0.048 # ~48 mm de altura
        txt_17.extrude = 0.0025
        txt_17.align_x = 'CENTER'
        txt_17.align_y = 'CENTER'

        o_17 = bpy.data.objects.new(f"Obj_Num17_{side_sign}", txt_17)
        o_17.location = (0.0, y_txt, H2 + 0.038)
        rot_17_z = math.radians(180.0) if side_sign > 0 else 0.0
        o_17.rotation_euler = (math.radians(90.0), 0.0, rot_17_z)
        o_17.data.materials.append(mat_relieve)
        col.objects.link(o_17)
        heraldic_objs.append(o_17)

    # Convertir textos heráldicos a mallas
    bpy.ops.object.select_all(action='DESELECT')
    for ho in heraldic_objs:
        ho.select_set(True)
    bpy.context.view_layer.objects.active = heraldic_objs[0]
    bpy.ops.object.convert(target='MESH')

    # Asignar Slots de Material a los componentes principales
    obj_base.data.materials.append(mat_placa)
    obj_rel.data.materials.append(mat_relieve)
    obj_w.data.materials.append(mat_blanco)

    # Unir todo el conjunto de la placa superior (base, relieves, recuadro blanco y escudo 17)
    bpy.ops.object.select_all(action='DESELECT')
    obj_base.select_set(True)
    obj_rel.select_set(True)
    obj_w.select_set(True)
    for ho in heraldic_objs:
        ho.select_set(True)
    bpy.context.view_layer.objects.active = obj_base
    bpy.ops.object.join()
    obj_joined = bpy.context.active_object
    obj_joined.name = "Placa_Superior"

    # Posición: z = 2.74 m (base en 2.63 m reposando sobre la inferior, cúspide crestería en 2.95 m)
    obj_joined.location = (0.0, 0.0, 2.74)
    obj_joined.rotation_euler = (0.0, 0.0, math.radians(90.0))

    for poly in obj_joined.data.polygons:
        # Caras en plano local Y (frente y dorso de la placa)
        if abs(poly.normal.y) > 0.5:
            poly.use_smooth = False
        else:
            poly.use_smooth = True

    return obj_joined

def build_demo_street_texts(mat_relieve):
    """
    Crea los textos 3D de muestra opcionales en la colección Texto_Demostracion_Ejemplo:
    - Placa Inferior: 'ESTEBAN CANTU' y 'C.P. / HOSPITAL / SANTA CATARINA'
    - Placa Superior: 'BENITO JUAREZ' y 'CLINICA / HOSPITAL / SANTA CATARINA'
    """
    demo_col = bpy.data.collections.new("Texto_Demostracion_Ejemplo")
    bpy.context.scene.collection.children.link(demo_col)

    f_font = get_cast_metal_font()
    created_objs = []
    # Placa Inferior (z = 2.52 m)
    # Cara +Y (observador al norte mirando al sur):
    # - Texto en verde (izq del observador = +X): X = +0.14, Euler (90, 0, 180)
    # - Patrocinador en blanco (der del observador = -X): X = -0.295, Euler (90, 0, 180)
    # Cara -Y (observador al sur mirando al norte):
    # - Texto en verde (izq del observador = -X): X = -0.14, Euler (90, 0, 0)
    # - Patrocinador en blanco (der del observador = +X): X = +0.295, Euler (90, 0, 0)
    for side_sign, y_pos, rot_z in [(1.0, 0.010, 180.0), (-1.0, -0.010, 0.0)]:
        t_c = bpy.data.curves.new(f"Txt_EstebanCantu_{'F' if side_sign > 0 else 'B'}", type='FONT')
        if f_font:
            t_c.font = f_font
        t_c.body = "ESTEBAN CANTU"
        t_c.size = 0.062
        t_c.space_character = 1.05
        t_c.extrude = 0.0022
        t_c.align_x = 'CENTER'
        t_c.align_y = 'CENTER'
        o_c = bpy.data.objects.new(f"Texto_EstebanCantu_{'F' if side_sign > 0 else 'B'}", t_c)
        o_c.location = (0.14 * side_sign, y_pos, 2.52)
        o_c.rotation_euler = (math.radians(90.0), 0.0, math.radians(rot_z))
        o_c.data.materials.append(mat_relieve)
        demo_col.objects.link(o_c)
        created_objs.append(o_c)

        # En el recuadro blanco de patrocinador
        t_cp = bpy.data.curves.new(f"Txt_Patrocinador1_{'F' if side_sign > 0 else 'B'}", type='FONT')
        if f_font:
            t_cp.font = f_font
        t_cp.body = "HOSPITAL\nSANTA CATARINA\nC.P. 21400"
        t_cp.size = 0.024
        t_cp.space_line = 1.15
        t_cp.space_character = 1.05
        t_cp.extrude = 0.0018
        t_cp.align_x = 'CENTER'
        t_cp.align_y = 'CENTER'
        o_cp = bpy.data.objects.new(f"Texto_Patrocinador1_{'F' if side_sign > 0 else 'B'}", t_cp)
        o_cp.location = (-0.295 * side_sign, y_pos, 2.52)
        o_cp.rotation_euler = (math.radians(90.0), 0.0, math.radians(rot_z))
        o_cp.data.materials.append(mat_relieve)
        demo_col.objects.link(o_cp)
        created_objs.append(o_cp)

    # Placa Superior (z = 2.74 m, a 90°)
    # Cara -X (observador al oeste mirando al este):
    # - Texto en verde (izq del observador = +Y): Y = +0.14, Euler (90, 0, -90)
    # - Patrocinador en blanco (der del observador = -Y): Y = -0.295, Euler (90, 0, -90)
    # Cara +X (observador al este mirando al oeste):
    # - Texto en verde (izq del observador = -Y): Y = -0.14, Euler (90, 0, 90)
    # - Patrocinador en blanco (der del observador = +Y): Y = +0.295, Euler (90, 0, 90)
    for side_sign, x_pos, rot_z in [(-1.0, -0.010, -90.0), (1.0, 0.010, 90.0)]:
        t_j = bpy.data.curves.new(f"Txt_BenitoJuarez_{'F' if side_sign < 0 else 'B'}", type='FONT')
        if f_font:
            t_j.font = f_font
        t_j.body = "BENITO JUAREZ"
        t_j.size = 0.062
        t_j.space_character = 1.05
        t_j.extrude = 0.0022
        t_j.align_x = 'CENTER'
        t_j.align_y = 'CENTER'
        o_j = bpy.data.objects.new(f"Texto_BenitoJuarez_{'F' if side_sign < 0 else 'B'}", t_j)
        o_j.location = (x_pos, -0.14 * side_sign, 2.74)
        o_j.rotation_euler = (math.radians(90.0), 0.0, math.radians(rot_z))
        o_j.data.materials.append(mat_relieve)
        demo_col.objects.link(o_j)
        created_objs.append(o_j)

        t_cp2 = bpy.data.curves.new(f"Txt_Patrocinador2_{'F' if side_sign < 0 else 'B'}", type='FONT')
        if f_font:
            t_cp2.font = f_font
        t_cp2.body = "CLINICA\nHOSPITAL\nSANTA CATARINA"
        t_cp2.size = 0.024
        t_cp2.space_line = 1.15
        t_cp2.space_character = 1.05
        t_cp2.extrude = 0.0018
        t_cp2.align_x = 'CENTER'
        t_cp2.align_y = 'CENTER'
        o_cp2 = bpy.data.objects.new(f"Texto_Patrocinador2_{'F' if side_sign < 0 else 'B'}", t_cp2)
        o_cp2.location = (x_pos, 0.295 * side_sign, 2.74)
        o_cp2.rotation_euler = (math.radians(90.0), 0.0, math.radians(rot_z))
        o_cp2.data.materials.append(mat_relieve)
        demo_col.objects.link(o_cp2)
        created_objs.append(o_cp2)

    bpy.ops.object.select_all(action='DESELECT')
    for o in created_objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = created_objs[0]
    bpy.ops.object.convert(target='MESH')

    return demo_col

def setup_lighting_and_cameras():
    """Configura iluminación de estudio de tres puntos, World Background y Cycles CPU."""
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

    # World Ambient Light
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
    """Genera los 4 renders técnicos oficiales de inspección."""
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

    # 2. Acercamiento a las Placas de Nomenclatura (mostrando el apoyo sin clipping)
    cam2_d = bpy.data.cameras.new("Cam_Placas")
    cam2_d.lens = 65
    cam2 = bpy.data.objects.new("Cam_Placas", cam2_d)
    bpy.context.scene.collection.objects.link(cam2)
    bpy.context.scene.camera = cam2

    cam2.location = (1.2, -1.4, 2.70)
    cam2.rotation_euler = (math.radians(85.0), 0.0, math.radians(40.0))

    bpy.context.scene.render.resolution_x = 1200
    bpy.context.scene.render.resolution_y = 1200
    p2 = "docs/images/poste_nomenclatura_closeup.png"
    bpy.context.scene.render.filepath = f"//{p2}"
    bpy.ops.render.render(write_still=True)
    print(f"Render acercamiento guardado: {p2}")

    # 3. Detalle Morfológico del Semicírculo Superior (Crestón con 'AYUNTAMIENTO' y '17')
    cam_crest_d = bpy.data.cameras.new("Cam_Creston")
    cam_crest_d.lens = 85
    cam_crest = bpy.data.objects.new("Cam_Creston", cam_crest_d)
    bpy.context.scene.collection.objects.link(cam_crest)
    bpy.context.scene.camera = cam_crest

    # Enfocando de frente al crestón de la placa superior (orientada en Y)
    cam_crest.location = (-0.85, 0.0, 2.89)
    cam_crest.rotation_euler = (math.radians(90.0), 0.0, math.radians(-90.0))

    bpy.context.scene.render.resolution_x = 1000
    bpy.context.scene.render.resolution_y = 1000
    p_crest = "docs/images/poste_nomenclatura_creston.png"
    bpy.context.scene.render.filepath = f"//{p_crest}"
    bpy.ops.render.render(write_still=True)
    print(f"Render crestón guardado: {p_crest}")

    # 4. Acercamiento a la Base de Campana / Pedestal (z = 0.22 m)
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
    print(" GENERADOR POSTE NOMENCLATURA TECATE (V2 ACTUALIZADA)          ")
    print("================================================================")
    clean_scene()

    # 1. Colección Principal del Asset
    main_col = bpy.data.collections.new("Poste_Nomenclatura_Tecate")
    bpy.context.scene.collection.children.link(main_col)

    # 2. Configurar Materiales PBR
    mat_poste, mat_placa, mat_relieve, mat_blanco = create_materials()

    # 3. Construir Poste de Hierro (Pedestal + Fuste + Capitel + Vástago)
    obj_poste = build_post_mesh(mat_poste, main_col)

    # 4. Construir Placa Inferior (Eje X, sin crestería, z = 2.41 a 2.63 m)
    obj_placa_inf = build_lower_plate(mat_placa, mat_relieve, mat_blanco, main_col)

    # 5. Construir Placa Superior (Eje Y, con crestería centrada y '17', z = 2.63 a 2.95 m)
    obj_placa_sup = build_upper_plate(mat_placa, mat_relieve, mat_blanco, main_col)

    # Emparentar placas a la columna central
    obj_placa_inf.parent = obj_poste
    obj_placa_sup.parent = obj_poste

    # 6. Textos 3D de Muestra en Colección Independiente
    demo_col = build_demo_street_texts(mat_relieve)
    for txt_o in demo_col.objects:
        if "Esteban" in txt_o.name or "Patrocinador1" in txt_o.name:
            txt_o.parent = obj_placa_inf
        else:
            txt_o.parent = obj_placa_sup

    # 7. Configurar iluminación y cámaras antes de guardar el .blend
    setup_lighting_and_cameras()

    # Actualizar transformaciones globales
    bpy.context.view_layer.update()

    # Validación dimensional
    all_objs = [obj_poste, obj_placa_inf, obj_placa_sup]
    min_z = min([min([(obj.matrix_world @ Vector(corner)).z for corner in obj.bound_box]) for obj in all_objs])
    max_z = max([max([(obj.matrix_world @ Vector(corner)).z for corner in obj.bound_box]) for obj in all_objs])
    total_height = max_z - min_z

    print(f"--> Altura Total Verificada: {total_height:.4f} m (Min Z: {min_z:.4f} m, Max Z: {max_z:.4f} m)")
    print(f"--> Cota Placa Inferior: {obj_placa_inf.location.z - 0.11:.3f} a {obj_placa_inf.location.z + 0.11:.3f} m")
    print(f"--> Cota Placa Superior: {obj_placa_sup.location.z - 0.11:.3f} a {obj_placa_sup.location.z + 0.21:.3f} m")
    print(f"--> Diámetro Base: {obj_poste.dimensions.x:.4f} m x {obj_poste.dimensions.y:.4f} m")

    # 8. Guardar archivo .blend maestro en blender_assets/
    blend_path = "blender_assets/poste_nomenclatura_tecate.blend"
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"--> Archivo maestro guardado: {blend_path}")

    # 9. Exportar versión modular limpia para Godot (malla única optimizada para MultiMesh)
    bpy.ops.object.select_all(action='DESELECT')
    for o in all_objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obj_poste
    bpy.ops.object.duplicate()
    dup_objs = bpy.context.selected_objects
    bpy.ops.object.join()
    obj_clean_joined = bpy.context.active_object
    obj_clean_joined.name = "Poste_Nomenclatura_Mesh"

    bpy.ops.object.select_all(action='DESELECT')
    obj_clean_joined.select_set(True)
    bpy.context.view_layer.objects.active = obj_clean_joined

    glb_clean_path = "godot_project/assets/poste_nomenclatura_tecate.glb"
    bpy.ops.export_scene.gltf(
        filepath=glb_clean_path,
        export_format='GLB',
        use_selection=True,
        export_apply=True,
        export_materials='EXPORT',
        export_yup=True
    )
    print(f"--> Asset Godot modular exportado (malla única): {glb_clean_path}")
    bpy.data.objects.remove(obj_clean_joined, do_unlink=True)


    # 10. Exportar versión demo con texto
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
    print(f"--> Asset Godot demo exportado: {glb_demo_path}")

    # 11. Generar Renders oficiales
    render_views()

    print("================================================================")
    print(" ACTUALIZACIÓN FINALIZADA SATISFACTORIAMENTE                    ")
    print("================================================================")

if __name__ == "__main__":
    main()
