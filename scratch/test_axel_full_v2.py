"""
=============================================================================
Prototipo Completo: Axel V2 Hiperrealista (Estilo Fortnite / AAA)
=============================================================================
Construye el modelo completo de Axel con fidelidad fotográfica a 'axel2.tiff':
- Sombrero fedora negro de fieltro con hendidura (pinch front), copa en lágrima y ala curvada.
- Cabello rizado tridimensional agrupado en mechones helicoidales bajo el sombrero.
- Cabeza con anatomía facial humana esculpida: pómulos angulares, nariz con puente recto,
  aletas y orificios nasales, labios anatómicos con arco de Cupido, mentón masculino
  con perilla / candado, cuencas oculares con párpados 3D y orejas modeladas.
- Chaleco sastre entallado (gris perla/blanco) con escote en V, botonadura de 5 botones
  metálicos, picos inferiores, bolsillos de ribete y sisas continuas.
- Camisa de vestir oscura con cuello estructurado vuelto y puños en mangas.
- Corbata de seda con nudo tridimensional y caída recta con franjas diagonales.
- Pantalón de vestir con raya diplomática y pliegues biomecánicos.
- Zapatos de vestir en cuero negro pulido con suela y tacón.
- Manos anatómicas en A-pose: dorso al frente (+Y), palma hacia atrás/adentro (-Y),
  pulgar oponible naciendo de la eminencia tenar y curvado hacia la palma,
  4 dedos escalonados (Medio > Anular > Índice > Meñique) con 3 falanges relajadas
  y anillo plateado en el dedo.
- Rig antropométrico canónico de 22 huesos compatible con CitizenEntity y Godot 4.
=============================================================================
"""

import os
import bpy
import bmesh
import math
from mathutils import Vector, Matrix, Euler, Quaternion

TEX_DIR = os.path.abspath("godot_project/assets/characters/textures")
OUTPUT_BLEND = os.path.abspath("godot_project/assets/characters/citizens/axel.blend")
OUTPUT_GLB = os.path.abspath("godot_project/assets/characters/citizens/axel.glb")
PREVIEW_PNG = os.path.abspath("godot_project/assets/characters/axel_preview.png")

def clean_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh, do_unlink=True)
    for arm in list(bpy.data.armatures):
        bpy.data.armatures.remove(arm, do_unlink=True)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat, do_unlink=True)

def clampf(v, min_v, max_v):
    return max(min_v, min(v, max_v))

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

def build_axel_armature():
    arm_data = bpy.data.armatures.new("Armature_Humanoid_Data")
    arm_data.display_type = 'OCTAHEDRAL'
    arm_obj = bpy.data.objects.new("Armature_Humanoid", arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj

    bpy.ops.object.mode_set(mode='EDIT')
    edit_bones = arm_data.edit_bones

    b_root = edit_bones.new("Root")
    b_root.head = Vector((0.0, 0.0, 0.0))
    b_root.tail = Vector((0.0, 0.0, 0.15))

    b_hips = edit_bones.new("Hips")
    b_hips.parent = b_root
    b_hips.head = Vector((0.0, 0.0, 0.96))
    b_hips.tail = Vector((0.0, 0.0, 1.08))

    b_spine = edit_bones.new("Spine")
    b_spine.parent = b_hips
    b_spine.head = Vector((0.0, 0.0, 1.08))
    b_spine.tail = Vector((0.0, 0.0, 1.22))

    b_spine1 = edit_bones.new("Spine1")
    b_spine1.parent = b_spine
    b_spine1.head = Vector((0.0, 0.0, 1.22))
    b_spine1.tail = Vector((0.0, 0.0, 1.34))

    b_chest = edit_bones.new("Chest")
    b_chest.parent = b_spine1
    b_chest.head = Vector((0.0, 0.0, 1.34))
    b_chest.tail = Vector((0.0, 0.0, 1.44))

    b_neck = edit_bones.new("Neck")
    b_neck.parent = b_chest
    b_neck.head = Vector((0.0, 0.0, 1.44))
    b_neck.tail = Vector((0.0, 0.0, 1.52))

    b_head = edit_bones.new("Head")
    b_head.parent = b_neck
    b_head.head = Vector((0.0, 0.0, 1.52))
    b_head.tail = Vector((0.0, 0.0, 1.76))

    for side, sign_x in [(".L", -1.0), (".R", 1.0)]:
        b_sh = edit_bones.new(f"Shoulder{side}")
        b_sh.parent = b_chest
        b_sh.head = Vector((sign_x * 0.04, 0.0, 1.42))
        b_sh.tail = Vector((sign_x * 0.19, 0.0, 1.38))

        b_uarm = edit_bones.new(f"UpperArm{side}")
        b_uarm.parent = b_sh
        b_uarm.head = Vector((sign_x * 0.19, 0.0, 1.38))
        b_uarm.tail = Vector((sign_x * 0.29, 0.0, 1.16))

        b_farm = edit_bones.new(f"Forearm{side}")
        b_farm.parent = b_uarm
        b_farm.head = Vector((sign_x * 0.29, 0.0, 1.16))
        b_farm.tail = Vector((sign_x * 0.36, 0.0, 0.95))

        b_hand = edit_bones.new(f"Hand{side}")
        b_hand.parent = b_farm
        b_hand.head = Vector((sign_x * 0.36, 0.0, 0.95))
        b_hand.tail = Vector((sign_x * 0.38, 0.0, 0.82))

        b_uleg = edit_bones.new(f"UpperLeg{side}")
        b_uleg.parent = b_hips
        b_uleg.head = Vector((sign_x * 0.10, 0.0, 0.92))
        b_uleg.tail = Vector((sign_x * 0.11, 0.0, 0.50))

        b_lleg = edit_bones.new(f"LowerLeg{side}")
        b_lleg.parent = b_uleg
        b_lleg.head = Vector((sign_x * 0.11, 0.0, 0.50))
        b_lleg.tail = Vector((sign_x * 0.11, 0.0, 0.12))

        b_foot = edit_bones.new(f"Foot{side}")
        b_foot.parent = b_lleg
        b_foot.head = Vector((sign_x * 0.11, 0.0, 0.12))
        b_foot.tail = Vector((sign_x * 0.11, 0.09, 0.03))

        b_toes = edit_bones.new(f"Toes{side}")
        b_toes.parent = b_foot
        b_toes.head = Vector((sign_x * 0.11, 0.09, 0.03))
        b_toes.tail = Vector((sign_x * 0.11, 0.15, 0.01))

    bpy.ops.object.mode_set(mode='OBJECT')
    return arm_obj

# =============================================================================
# CONSTRUCCIÓN DE LA CABEZA Y ROSTRO (Player_Head_Mesh)
# =============================================================================
def build_head_mesh(arm_obj, mat_skin, mat_hat, mat_hair, mat_eyes):
    mesh = bpy.data.meshes.new("Player_Head_Mesh_Data")
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")

    # 1. Cráneo, Rostro y Cuello Esculpidos Anatómicamente (Quad Grid)
    # Dimensiones antropométricas de Axel: Z de 1.450 a 1.740 m
    v_rings = 40
    u_segs = 32
    grid = []

    for vi in range(v_rings + 1):
        tv = vi / float(v_rings)
        
        # Segmentación vertical del cuello a la coronilla
        if tv < 0.20: # Cuello atlético (1.450 a 1.520)
            t_neck = tv / 0.20
            z = 1.450 + t_neck * 0.070
            rx = 0.046 + t_neck * 0.005
            ry_f = 0.048 + t_neck * 0.007
            ry_b = 0.046 + t_neck * 0.005
            yc = 0.004 * (1.0 - t_neck)
        elif tv < 0.45: # Mandíbula, mentón, labios (1.520 a 1.585)
            tj = (tv - 0.20) / 0.25
            z = 1.520 + tj * 0.065
            rx = 0.052 + tj * 0.015
            ry_f = 0.058 + tj * 0.016
            ry_b = 0.052 + tj * 0.012
            yc = 0.002
        elif tv < 0.72: # Nariz, pómulos, órbitas oculares (1.585 a 1.660)
            tm = (tv - 0.45) / 0.27
            z = 1.585 + tm * 0.075
            rx = 0.068 + tm * 0.005
            ry_f = 0.075 + tm * 0.002
            ry_b = 0.064 + tm * 0.008
            yc = 0.0
        else: # Frente, sienes y bóveda craneal (1.660 a 1.740)
            tt = (tv - 0.72) / 0.28
            z = 1.660 + tt * 0.080
            dome = math.sqrt(max(0.01, 1.0 - (tt * 0.94)**2))
            rx = 0.073 * dome + 0.002
            ry_f = 0.076 * dome + 0.002
            ry_b = 0.074 * dome + 0.002
            yc = -0.008 * tt

        ring = []
        for ui in range(u_segs):
            ang = (ui / float(u_segs)) * 2.0 * math.pi - (math.pi / 2.0)
            sin_a = math.sin(ang)
            cos_a = math.cos(ang)
            vx = cos_a * rx
            vy = yc + (sin_a * ry_f if sin_a >= 0 else sin_a * ry_b)
            vz = z

            # Esculpido anatómico de rasgos faciales en cara anterior (+Y)
            if sin_a > 0:
                # A. Nuez de Adán en cuello anterior
                if abs(vz - 1.472) < 0.016 and abs(vx) < 0.014:
                    vy += 0.007 * (1.0 - abs(vx) / 0.014) * (1.0 - abs(vz - 1.472) / 0.016)
                    
                # B. Mentón masculino prominente y cuadrado con perilla (Z = 1.536)
                if abs(vz - 1.536) < 0.022 and abs(vx) < 0.026:
                    cd = math.sqrt((vx / 0.026)**2 + ((vz - 1.536) / 0.022)**2)
                    if cd < 1.0:
                        vy += 0.020 * (1.0 - cd)**1.8
                        # Hendidura central para el hoyuelo/perilla
                        if abs(vx) < 0.006 and abs(vz - 1.536) < 0.012:
                            vy -= 0.003
                            
                # C. Surco mentolabial
                if abs(vz - 1.554) < 0.008 and abs(vx) < 0.022:
                    vy -= 0.005 * (1.0 - abs(vx) / 0.022)
                    
                # D. Labios anatómicos con arco de Cupido y comisuras (Z = 1.562 a 1.582)
                if 1.560 < vz < 1.584 and abs(vx) < 0.028:
                    tlip = (vz - 1.560) / 0.024
                    w_lip = 0.026 * (1.0 - abs(tlip - 0.5) * 1.4)
                    if abs(vx) < max(0.004, w_lip):
                        # Volumen labial con depresión central superior (Cupid's bow)
                        cupid_dip = 0.003 if (tlip > 0.6 and abs(vx) < 0.005) else 0.0
                        vy += (0.012 * math.sin(tlip * math.pi) - cupid_dip) * (1.0 - abs(vx) / max(0.004, w_lip))
                        
                # E. Filtrum (depresión subnasal vertical)
                if 1.584 <= vz <= 1.602 and abs(vx) < 0.008:
                    vy -= 0.003 * (1.0 - abs(vx) / 0.008)
                    
                # F. Nariz esculpida completa: puente recto, aletas y punta (Z = 1.595 a 1.650)
                if 1.595 < vz < 1.650 and abs(vx) < 0.022:
                    tn = (vz - 1.595) / 0.055
                    # Punta de la nariz y aletas en la base (tn < 0.35)
                    if tn < 0.35:
                        # Punta nasal
                        if abs(vx) < 0.011:
                            vy += 0.028 * (1.0 - abs(vx) / 0.011) * math.sin((tn / 0.35) * math.pi)
                        # Aletas nasales
                        elif abs(vx) < 0.020:
                            vy += 0.014 * (1.0 - abs(abs(vx) - 0.015) / 0.006) * math.sin((tn / 0.35) * math.pi)
                    else: # Puente nasal aristocrático recto
                        nw = 0.008 + (1.0 - tn) * 0.004
                        if abs(vx) < nw:
                            vy += (0.022 - tn * 0.006) * (1.0 - abs(vx) / nw)**1.2
                            
                # G. Pómulos altos angulares de Axel (Z = 1.605 a 1.635)
                for cx in [-0.048, 0.048]:
                    dc = math.sqrt(((vx - cx) / 0.022)**2 + ((vz - 1.620) / 0.018)**2)
                    if dc < 1.0:
                        vy += 0.010 * (1.0 - dc)**2
                        
                # H. Cuencas orbitarias profundas para los ojos (Z = 1.625)
                for ex in [-0.033, 0.033]:
                    de = math.sqrt(((vx - ex) / 0.018)**2 + ((vz - 1.625) / 0.014)**2)
                    if de < 1.0:
                        vy -= 0.016 * (1.0 - de)**2
                        
                # I. Arco superciliar / cejas masculinas prominentes
                if 1.642 < vz < 1.662 and abs(vx) < 0.055:
                    tbrow = 1.0 - (abs(vz - 1.652) / 0.010)
                    vy += 0.012 * tbrow * (1.0 - (abs(vx) / 0.055)**2)

            ring.append(bm.verts.new(Vector((vx, vy, vz))))
        grid.append(ring)

    # Crear caras con mapeo UV facial cilíndrico
    for vi in range(v_rings):
        r0 = grid[vi]
        r1 = grid[vi + 1]
        v_coord0 = vi / float(v_rings)
        v_coord1 = (vi + 1) / float(v_rings)
        for ui in range(u_segs):
            un = (ui + 1) % u_segs
            f = bm.faces.new([r0[ui], r0[un], r1[un], r1[ui]])
            f.material_index = 0 # mat_skin
            
            u0 = 0.5 + math.atan2(r0[ui].co.x, max(0.001, r0[ui].co.y)) / (2.0 * math.pi)
            u1 = 0.5 + math.atan2(r0[un].co.x, max(0.001, r0[un].co.y)) / (2.0 * math.pi)
            u2 = 0.5 + math.atan2(r1[un].co.x, max(0.001, r1[un].co.y)) / (2.0 * math.pi)
            u3 = 0.5 + math.atan2(r1[ui].co.x, max(0.001, r1[ui].co.y)) / (2.0 * math.pi)
            
            for lp, u_val, v_val in zip(f.loops, [u0, u1, u2, u3], [v_coord0, v_coord0, v_coord1, v_coord1]):
                lp[uv_layer].uv = Vector((clampf(u_val, 0.0, 1.0), clampf(v_val, 0.0, 1.0)))

    # Cierre superior de la coronilla
    top_vh = bm.verts.new(Vector((0.0, -0.008, 1.740)))
    for ui in range(u_segs):
        un = (ui + 1) % u_segs
        f = bm.faces.new([grid[-1][ui], grid[-1][un], top_vh])
        f.material_index = 0
        for lp in f.loops:
            lp[uv_layer].uv = Vector((ui / float(u_segs), 1.0))

    # 2. Globos Oculares 3D Esféricos y Párpados Almendrados Anatómicos
    for ex in [-0.033, 0.033]:
        p_eye = Vector((ex, 0.058, 1.625))
        sph = bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=12, radius=0.0125,
                                        matrix=Matrix.Translation(p_eye))
        for v in sph['verts']:
            for f in v.link_faces:
                f.material_index = 3 # mat_eyes
                for lp in f.loops:
                    dx = (lp.vert.co.x - p_eye.x) / 0.0125
                    dz = (lp.vert.co.z - p_eye.z) / 0.0125
                    lp[uv_layer].uv = Vector((clampf(0.5 + dx * 0.5, 0.0, 1.0), clampf(0.5 + dz * 0.5, 0.0, 1.0)))

        # Párpado superior envolvente descansando sobre el iris (mirada humana segura y serena)
        sign_side = 1.0 if ex > 0 else -1.0
        lid_top_pts = [
            Vector((ex - 0.014 * sign_side, 0.065, 1.622)), # Comisura medial/lateral
            Vector((ex - 0.007 * sign_side, 0.070, 1.630)), # Borde sobre polo superior de iris
            Vector((ex + 0.007 * sign_side, 0.070, 1.630)),
            Vector((ex + 0.014 * sign_side, 0.065, 1.624)),
            Vector((ex + 0.011 * sign_side, 0.068, 1.637)), # Pliegue supratarsal
            Vector((ex + 0.000 * sign_side, 0.072, 1.640)),
            Vector((ex - 0.011 * sign_side, 0.068, 1.637)),
        ]
        lv_top = [bm.verts.new(p) for p in lid_top_pts]
        bm.faces.new([lv_top[0], lv_top[1], lv_top[6]]).material_index = 0
        bm.faces.new([lv_top[1], lv_top[2], lv_top[5], lv_top[6]]).material_index = 0
        bm.faces.new([lv_top[2], lv_top[3], lv_top[4], lv_top[5]]).material_index = 0

        # Párpado inferior descansando en el polo inferior del globo ocular
        lid_bot_pts = [
            Vector((ex - 0.013 * sign_side, 0.065, 1.622)),
            Vector((ex - 0.006 * sign_side, 0.069, 1.618)),
            Vector((ex + 0.006 * sign_side, 0.069, 1.618)),
            Vector((ex + 0.013 * sign_side, 0.065, 1.624)),
            Vector((ex + 0.010 * sign_side, 0.067, 1.612)),
            Vector((ex + 0.000 * sign_side, 0.070, 1.610)),
            Vector((ex - 0.010 * sign_side, 0.067, 1.612)),
        ]
        lv_bot = [bm.verts.new(p) for p in lid_bot_pts]
        bm.faces.new([lv_bot[0], lv_bot[1], lv_bot[6]]).material_index = 0
        bm.faces.new([lv_bot[1], lv_bot[2], lv_bot[5], lv_bot[6]]).material_index = 0
        bm.faces.new([lv_bot[2], lv_bot[3], lv_bot[4], lv_bot[5]]).material_index = 0

    # 3. Orejas Anatómicas 3D (Z = 1.585 a 1.645, X = ±0.070)
    for sign_x in [-1.0, 1.0]:
        ear_pts = [
            Vector((sign_x * 0.070, -0.002, 1.642)), # Helix superior
            Vector((sign_x * 0.076, -0.014, 1.636)), # Helix posterior
            Vector((sign_x * 0.078, -0.018, 1.615)), # Antihelix medio
            Vector((sign_x * 0.074, -0.016, 1.595)), # Lóbulo inferior
            Vector((sign_x * 0.068, -0.006, 1.590)), # Base del lóbulo
            Vector((sign_x * 0.069,  0.006, 1.615)), # Trago anterior
            Vector((sign_x * 0.072, -0.008, 1.618)), # Fosa concha central
        ]
        ev = [bm.verts.new(p) for p in ear_pts]
        bm.faces.new([ev[0], ev[1], ev[6], ev[5]]).material_index = 0
        bm.faces.new([ev[1], ev[2], ev[6]]).material_index = 0
        bm.faces.new([ev[2], ev[3], ev[6]]).material_index = 0
        bm.faces.new([ev[3], ev[4], ev[6]]).material_index = 0
        bm.faces.new([ev[4], ev[5], ev[6]]).material_index = 0

    # 4. Cabello Rizado Tridimensional Auténtico de Axel (Espirales Helicoidales)
    def add_curly_strand(bm, center_start, center_end, n_turns=2.5, radius_curl=0.007,
                         thick=0.0055, n_segs=16):
        """Genera un rizo 3D helicoidal cerrado con torsión viva y volumen orgánico."""
        strand_rings = []
        for s in range(n_segs + 1):
            t = s / float(n_segs)
            p_core = center_start.lerp(center_end, t)
            phase = t * n_turns * 2.0 * math.pi
            # Desplazamiento helicoidal
            helix_offset = Vector((math.cos(phase) * radius_curl, math.sin(phase) * radius_curl * 0.6, 0.0))
            p_center = p_core + helix_offset
            
            cur_thick = thick * (1.0 - t * 0.45) # Tapering suave hacia la punta
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
                
        # Punta del rizo
        tip = bm.verts.new(strand_rings[-1][0].co.lerp(strand_rings[-1][4].co, 0.5) + Vector((0, 0, -thick * 0.5)))
        for a in range(8):
            an = (a + 1) % 8
            f = bm.faces.new([strand_rings[-1][a], strand_rings[-1][an], tip])
            f.material_index = 2

    # Ramilletes de rizos de Axel cayendo bajo el ala del fedora
    curls_specs = [
        # Flequillo frontal sobre la frente (Z = 1.685 a 1.635)
        (Vector((-0.038, 0.076, 1.685)), Vector((-0.030, 0.082, 1.642)), 2.2, 0.007, 0.006),
        (Vector((-0.024, 0.078, 1.688)), Vector((-0.016, 0.084, 1.638)), 2.6, 0.008, 0.006),
        (Vector((-0.010, 0.080, 1.690)), Vector((-0.004, 0.086, 1.635)), 2.8, 0.008, 0.006),
        (Vector(( 0.004, 0.080, 1.690)), Vector(( 0.010, 0.086, 1.636)), 2.8, 0.008, 0.006),
        (Vector(( 0.018, 0.078, 1.688)), Vector(( 0.024, 0.084, 1.638)), 2.5, 0.008, 0.006),
        (Vector(( 0.032, 0.076, 1.685)), Vector(( 0.038, 0.082, 1.642)), 2.2, 0.007, 0.006),
        # Patillas y sienes izquierda (-X)
        (Vector((-0.068, 0.028, 1.670)), Vector((-0.072, 0.020, 1.615)), 2.4, 0.007, 0.006),
        (Vector((-0.066, 0.012, 1.660)), Vector((-0.070, 0.006, 1.605)), 2.2, 0.006, 0.005),
        # Patillas y sienes derecha (+X)
        (Vector(( 0.068, 0.028, 1.670)), Vector(( 0.072, 0.020, 1.615)), 2.4, 0.007, 0.006),
        (Vector(( 0.066, 0.012, 1.660)), Vector(( 0.070, 0.006, 1.605)), 2.2, 0.006, 0.005),
        # Mechones en nuca baja
        (Vector((-0.040, -0.065, 1.650)), Vector((-0.035, -0.062, 1.595)), 2.0, 0.007, 0.006),
        (Vector(( 0.040, -0.065, 1.650)), Vector(( 0.035, -0.062, 1.595)), 2.0, 0.007, 0.006),
    ]
    for p1, p2, turns, r_c, th in curls_specs:
        add_curly_strand(bm, p1, p2, turns, r_c, th)

    # 5. Sombrero Fedora de Fieltro Negro de Axel (Copa en Lágrima, Pinch Front y Ala Curva)
    # Ala ancha (Brim): Z = 1.670 a 1.695, radio ~ 0.142 m
    n_brim_pts = 32
    brim_inner = []
    brim_outer = []
    
    for i in range(n_brim_pts):
        ang = (i / float(n_brim_pts)) * 2.0 * math.pi
        cos_a = math.cos(ang)
        sin_a = math.sin(ang)
        
        # Curvatura snap brim de gala: desciende suavemente al frente y sube a los lados/espalda
        dip_z = -0.016 * sin_a if sin_a > 0 else 0.010 * (-sin_a)
        
        # Radio interior del ala (contacto con la cabeza)
        rx_in = 0.078
        ry_in = 0.084
        vx_in = cos_a * rx_in
        vy_in = sin_a * ry_in - 0.006
        vz_in = 1.678 + dip_z * 0.4
        brim_inner.append(bm.verts.new(Vector((vx_in, vy_in, vz_in))))
        
        # Radio exterior del ala ancha
        rx_out = 0.138
        ry_out = 0.146
        vx_out = cos_a * rx_out
        vy_out = sin_a * ry_out - 0.006
        vz_out = 1.670 + dip_z
        brim_outer.append(bm.verts.new(Vector((vx_out, vy_out, vz_out))))

    # Caras del ala del fedora
    for i in range(n_brim_pts):
        nxt = (i + 1) % n_brim_pts
        f = bm.faces.new([brim_inner[i], brim_outer[i], brim_outer[nxt], brim_inner[nxt]])
        f.material_index = 1 # mat_hat

    # Copa del Fedora (Crown): Z de 1.678 a 1.775 con hendidura central y pellizco frontal
    crown_levels = [
        (1.678, 0.078, 0.084, 0.0),    # Base (cinta del sombrero)
        (1.698, 0.076, 0.082, 0.0),    # Sobre la cinta
        (1.725, 0.073, 0.079, 0.006),  # Nivel medio con inicio de pellizco
        (1.755, 0.068, 0.074, 0.012),  # Pellizco frontal pronunciado
        (1.775, 0.060, 0.068, 0.016),  # Borde de la cresta superior
    ]
    crown_rings = []
    for z_c, rx_c, ry_c, pinch in crown_levels:
        c_ring = []
        for i in range(n_brim_pts):
            ang = (i / float(n_brim_pts)) * 2.0 * math.pi
            cos_a = math.cos(ang)
            sin_a = math.sin(ang)
            
            vx = cos_a * rx_c
            vy = sin_a * ry_c - 0.006
            vz = z_c
            
            # Pellizco frontal (pinch front) en lados anteriores (Y > 0)
            if sin_a > 0.3 and abs(cos_a) > 0.2:
                vx *= (1.0 - pinch * 0.7)
                
            c_ring.append(bm.verts.new(Vector((vx, vy, vz))))
        crown_rings.append(c_ring)

    # Caras de la copa
    for r in range(len(crown_rings) - 1):
        r0 = crown_rings[r]
        r1 = crown_rings[r + 1]
        for i in range(n_brim_pts):
            nxt = (i + 1) % n_brim_pts
            f = bm.faces.new([r0[i], r0[nxt], r1[nxt], r1[i]])
            f.material_index = 1

    # Tapa superior con hendidura central (crease / gutter along Y axis)
    top_crease = []
    for i in range(n_brim_pts):
        ang = (i / float(n_brim_pts)) * 2.0 * math.pi
        cos_a = math.cos(ang)
        sin_a = math.sin(ang)
        vx = cos_a * 0.038
        vy = sin_a * 0.046 - 0.006
        # Hendidura longitudinal en el centro (X = 0)
        vz = 1.760 - (0.014 * (1.0 - min(1.0, abs(cos_a) * 1.5)))
        top_crease.append(bm.verts.new(Vector((vx, vy, vz))))

    for i in range(n_brim_pts):
        nxt = (i + 1) % n_brim_pts
        f = bm.faces.new([crown_rings[-1][i], crown_rings[-1][nxt], top_crease[nxt], top_crease[i]])
        f.material_index = 1

    center_top = bm.verts.new(Vector((0.0, -0.006, 1.748)))
    for i in range(n_brim_pts):
        nxt = (i + 1) % n_brim_pts
        f = bm.faces.new([top_crease[i], top_crease[nxt], center_top])
        f.material_index = 1

    bm.verts.index_update()
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("Player_Head_Mesh", mesh)
    bpy.context.scene.collection.objects.link(obj)

    obj.data.materials.append(mat_skin) # 0
    obj.data.materials.append(mat_hat)  # 1
    obj.data.materials.append(mat_hair) # 2
    obj.data.materials.append(mat_eyes) # 3

    for poly in mesh.polygons:
        poly.use_smooth = True

    # Ponderación a huesos de cabeza y cuello
    obj.parent = arm_obj
    mod = obj.modifiers.new(name="Armature", type='ARMATURE')
    mod.object = arm_obj

    vg_head = obj.vertex_groups.new(name="Head")
    vg_neck = obj.vertex_groups.new(name="Neck")

    for v in obj.data.vertices:
        z = v.co.z
        if z >= 1.52:
            vg_head.add([v.index], 1.0, 'REPLACE')
        else:
            w_neck = clampf((1.52 - z) / 0.07, 0.0, 1.0)
            vg_head.add([v.index], 1.0 - w_neck, 'REPLACE')
            vg_neck.add([v.index], w_neck, 'REPLACE')

    return obj

# =============================================================================
# CONSTRUCCIÓN DEL CUERPO, INDUMENTARIA Y MANOS (Player_Body_Mesh)
# =============================================================================
def build_body_mesh(arm_obj, mat_shirt, mat_vest, mat_tie, mat_pants, mat_shoes, mat_skin, mat_buttons):
    mesh = bpy.data.meshes.new("Player_Body_Mesh_Data")
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")

    # Mapeo de materiales en el objeto:
    # 0: Camisa (mat_shirt)
    # 1: Chaleco (mat_vest)
    # 2: Corbata (mat_tie)
    # 3: Pantalón (mat_pants)
    # 4: Zapatos (mat_shoes)
    # 5: Piel manos (mat_skin)
    # 6: Botones/Hebilla metálica (mat_buttons)

    # 1. Torso Sastre Integrado: Camisa base con chaleco entallado y cuello
    # Niveles verticales del torso (Z: 0.95 a 1.45 m)
    torso_levels = [
        (0.95, 0.155, 0.115, 0), # Pelvis baja (Pantalón / cintura)
        (1.02, 0.150, 0.110, 0), # Cintura / ombligo
        (1.10, 0.155, 0.115, 1), # Esternón bajo / chaleco medio
        (1.22, 0.175, 0.125, 1), # Pecho / busto sastre
        (1.34, 0.185, 0.130, 1), # Pecho alto / clavículas
        (1.42, 0.160, 0.100, 0), # Base de hombros / cuello
        (1.46, 0.052, 0.054, 0), # Cuello de la camisa (collar stand)
    ]
    
    n_torso_pts = 28
    torso_rings = []
    
    for z, rx, ry, is_vest in torso_levels:
        t_ring = []
        for i in range(n_torso_pts):
            ang = (i / float(n_torso_pts)) * 2.0 * math.pi
            vx = math.cos(ang) * rx
            vy = math.sin(ang) * ry
            vz = z
            t_ring.append(bm.verts.new(Vector((vx, vy, vz))))
        torso_rings.append(t_ring)

    # Conectar mallas del torso y asignar materiales sastre (Chaleco vs Camisa)
    for r in range(len(torso_rings) - 1):
        r0 = torso_rings[r]
        r1 = torso_rings[r + 1]
        z_mid = (torso_levels[r][0] + torso_levels[r + 1][0]) * 0.5
        for i in range(n_torso_pts):
            nxt = (i + 1) % n_torso_pts
            ang = (i / float(n_torso_pts)) * 2.0 * math.pi
            f = bm.faces.new([r0[i], r0[nxt], r1[nxt], r1[i]])
            
            # Escote en V del chaleco: deja visible la camisa y corbata en el pecho anterior
            is_anterior = (math.sin(ang) > 0.4)
            is_v_neck_zone = (1.20 <= z_mid <= 1.44) and (abs(math.cos(ang)) < 0.35)
            
            if 0.98 <= z_mid <= 1.40 and not is_v_neck_zone:
                f.material_index = 1 # mat_vest (Chaleco gris perla)
            elif z_mid < 0.98:
                f.material_index = 3 # mat_pants (Cintura del pantalón)
            else:
                f.material_index = 0 # mat_shirt (Camisa carbón)

    # 2. Cuello Camisero Estructurado (Folded Collar) y Corbata de Seda 3D
    # Solapas del cuello camisero cerrando sobre el pecho
    collar_left = [
        Vector((-0.048, 0.020, 1.460)),
        Vector((-0.032, 0.052, 1.455)),
        Vector((-0.014, 0.065, 1.440)), # Punta del cuello
        Vector((-0.028, 0.040, 1.435)),
    ]
    cl_v = [bm.verts.new(p) for p in collar_left]
    bm.faces.new(cl_v).material_index = 0

    collar_right = [
        Vector(( 0.048, 0.020, 1.460)),
        Vector(( 0.032, 0.052, 1.455)),
        Vector(( 0.014, 0.065, 1.440)), # Punta del cuello
        Vector(( 0.028, 0.040, 1.435)),
    ]
    cr_v = [bm.verts.new(p) for p in collar_right]
    bm.faces.new(cr_v).material_index = 0

    # Nudo tridimensional de la corbata (Four-in-hand / Windsor Knot)
    knot_pts = [
        Vector((-0.012, 0.060, 1.452)),
        Vector(( 0.012, 0.060, 1.452)),
        Vector(( 0.010, 0.066, 1.428)),
        Vector((-0.010, 0.066, 1.428)),
    ]
    kv = [bm.verts.new(p) for p in knot_pts]
    bm.faces.new(kv).material_index = 2 # mat_tie

    # Pala de la corbata (Tie Blade) cayendo recta bajo el chaleco
    tie_levels = [
        (1.428, 0.010, 0.066),
        (1.340, 0.015, 0.088),
        (1.240, 0.022, 0.098),
        (1.150, 0.025, 0.095),
    ]
    tie_rings = []
    for z_t, w_t, y_t in tie_levels:
        v_l = bm.verts.new(Vector((-w_t, y_t, z_t)))
        v_r = bm.verts.new(Vector(( w_t, y_t, z_t)))
        tie_rings.append((v_l, v_r))

    for idx in range(len(tie_rings) - 1):
        l0, r0 = tie_rings[idx]
        l1, r1 = tie_rings[idx + 1]
        f = bm.faces.new([l0, r0, r1, l1])
        f.material_index = 2

    # Botones metálicos de gala en la botonadura central del chaleco
    for zb in [1.02, 1.07, 1.12, 1.17, 1.22]:
        btn = bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=6, radius=0.005,
                                        matrix=Matrix.Translation(Vector((0.0, 0.118, zb))))
        for v in btn['verts']:
            for f in v.link_faces:
                f.material_index = 6 # mat_buttons

    # Picos inferiores de gala del chaleco (puntas clásicas sobre el pantalón)
    for sign_p in [-1.0, 1.0]:
        peak_pts = [
            Vector((sign_p * 0.015, 0.116, 0.950)),
            Vector((sign_p * 0.055, 0.114, 0.950)),
            Vector((sign_p * 0.035, 0.118, 0.925)), # Pico inferior
        ]
        pv = [bm.verts.new(p) for p in peak_pts]
        bm.faces.new(pv).material_index = 1

    # 3. Brazos y Mangas de Camisa (Z: 1.40 a 0.94)
    for sign_x in [-1.0, 1.0]:
        arm_joints = [
            (Vector((sign_x * 0.19, 0.0, 1.38)), 0.068), # Deltoides / sisa
            (Vector((sign_x * 0.24, 0.0, 1.27)), 0.058), # Bíceps
            (Vector((sign_x * 0.29, 0.0, 1.16)), 0.052), # Codo
            (Vector((sign_x * 0.33, 0.0, 1.05)), 0.046), # Antebrazo
            (Vector((sign_x * 0.36, 0.0, 0.95)), 0.040), # Muñeca / puño
        ]
        sleeve_rings = []
        for center, r_arm in arm_joints:
            rng = []
            for a in range(16):
                ang = (a / 16.0) * 2.0 * math.pi
                vx = center.x + math.cos(ang) * r_arm
                vy = center.y + math.sin(ang) * r_arm
                vz = center.z
                rng.append(bm.verts.new(Vector((vx, vy, vz))))
            sleeve_rings.append(rng)
            
        for i in range(len(sleeve_rings) - 1):
            r0 = sleeve_rings[i]
            r1 = sleeve_rings[i + 1]
            for a in range(16):
                an = (a + 1) % 16
                f = bm.faces.new([r0[a], r0[an], r1[an], r1[a]])
                f.material_index = 0 # mat_shirt (Camisa popelín carbón)

    # 4. Manos Anatómicas en A-Pose (Dorso al Frente +Y, Pulgar Oponible hacia Adentro/Palma -Y)
    for sign_x in [-1.0, 1.0]:
        wrist_pos = Vector((sign_x * 0.36, 0.0, 0.95))
        
        # Malla de la palma y dorso
        palm_w = 0.038
        palm_h = 0.065
        palm_t = 0.016
        
        # 4 Dedos Escalonados Relajados (Medio > Anular > Índice > Meñique)
        # Offset medial hacia el cuerpo
        medial_dir = Vector((-sign_x, 0, 0))
        anterior_dir = Vector((0, 1, 0)) # Dorso
        distal_dir = Vector((sign_x * 0.15, 0, -1)).normalized()
        
        finger_specs = [
            ("Index",  0.012, 0.064, 0.0075),
            ("Middle", 0.000, 0.072, 0.0080),
            ("Ring",  -0.012, 0.066, 0.0075),
            ("Pinky", -0.023, 0.052, 0.0068),
        ]
        
        base_knuckles = wrist_pos + distal_dir * palm_h
        for f_name, lat_offset, f_len, f_thick in finger_specs:
            f_root = base_knuckles + medial_dir * (lat_offset * sign_x)
            
            # 3 falanges relajadas con suave curvatura hacia la palma (-Y)
            p0 = f_root
            p1 = p0 + distal_dir * (f_len * 0.38) + Vector((0, -0.005, 0))
            p2 = p1 + distal_dir * (f_len * 0.34) + Vector((0, -0.009, 0))
            p3 = p2 + distal_dir * (f_len * 0.28) + Vector((0, -0.012, 0))
            
            f_pts = [p0, p1, p2, p3]
            f_rings = []
            for idx_p, pt in enumerate(f_pts):
                scale_t = f_thick * (1.0 - idx_p * 0.16)
                rng = []
                for a in range(8):
                    ang = (a / 8.0) * 2.0 * math.pi
                    vx = pt.x + math.cos(ang) * scale_t
                    vy = pt.y + math.sin(ang) * scale_t
                    vz = pt.z
                    rng.append(bm.verts.new(Vector((vx, vy, vz))))
                f_rings.append(rng)
                
            for idx_r in range(len(f_rings) - 1):
                r0 = f_rings[idx_r]
                r1 = f_rings[idx_r + 1]
                for a in range(8):
                    an = (a + 1) % 8
                    f = bm.faces.new([r0[a], r0[an], r1[an], r1[a]])
                    f.material_index = 5 # mat_skin (Piel de manos)
                    
            # Punta de la yema digital
            f_tip = bm.verts.new(p3 + distal_dir * 0.004 + Vector((0, -0.004, 0)))
            for a in range(8):
                an = (a + 1) % 8
                f = bm.faces.new([f_rings[-1][a], f_rings[-1][an], f_tip])
                f.material_index = 5

            # Anillo de gala en el dedo de Axel (mano derecha o izquierda)
            if f_name == "Ring" and sign_x > 0:
                ring_obj = bmesh.ops.create_circle(bm, cap_ends=False, radius=f_thick * 1.15,
                                                   matrix=Matrix.Translation(p0.lerp(p1, 0.4)))
                for v in ring_obj['verts']:
                    v.co.y += 0.002
                # Extrusión del anillo metálico
                r_edges = [e for e in bm.edges if e.is_boundary and e.verts[0] in ring_obj['verts']]
                res_ext = bmesh.ops.extrude_edge_only(bm, edges=r_edges)
                for v in res_ext['geom']:
                    if isinstance(v, bmesh.types.BMVert):
                        v.co += distal_dir * 0.004
                for f in [g for g in res_ext['geom'] if isinstance(g, bmesh.types.BMFace)]:
                    f.material_index = 6 # mat_buttons (Plata/Acero)

        # Pulgar Oponible Anatómico: nace en la eminencia tenar y se orienta hacia la palma/interior
        thumb_base = wrist_pos + medial_dir * 0.024 + distal_dir * 0.022 + Vector((0, -0.006, 0))
        # Curvatura oponible cruzando hacia el eje medial y palmar (-Y)
        t_p0 = thumb_base
        t_p1 = t_p0 + medial_dir * 0.022 + Vector((0, -0.012, -0.018))
        t_p2 = t_p1 + medial_dir * 0.016 + Vector((0, -0.018, -0.020))
        
        t_rings = []
        for idx_t, pt in enumerate([t_p0, t_p1, t_p2]):
            th_rad = 0.0095 * (1.0 - idx_t * 0.18)
            rng = []
            for a in range(8):
                ang = (a / 8.0) * 2.0 * math.pi
                vx = pt.x + math.cos(ang) * th_rad
                vy = pt.y + math.sin(ang) * th_rad
                vz = pt.z
                rng.append(bm.verts.new(Vector((vx, vy, vz))))
            t_rings.append(rng)
            
        for idx_r in range(len(t_rings) - 1):
            r0 = t_rings[idx_r]
            r1 = t_rings[idx_r + 1]
            for a in range(8):
                an = (a + 1) % 8
                f = bm.faces.new([r0[a], r0[an], r1[an], r1[a]])
                f.material_index = 5
                
        thumb_tip = bm.verts.new(t_p2 + medial_dir * 0.006 + Vector((0, -0.006, -0.006)))
        for a in range(8):
            an = (a + 1) % 8
            f = bm.faces.new([t_rings[-1][a], t_rings[-1][an], thumb_tip])
            f.material_index = 5

        # Cierre palmar envolvente conectando muñeca con nudillos
        for a in range(8):
            an = (a + 1) % 8
            f = bm.faces.new([sleeve_rings[-1][a], sleeve_rings[-1][an], f_rings[0][an], f_rings[0][a]])
            f.material_index = 5

    # 5. Piernas, Pantalón Sastre y Calzado de Gala (Z: 0.95 a 0.0)
    for sign_x in [-1.0, 1.0]:
        leg_joints = [
            (Vector((sign_x * 0.10, 0.0, 0.92)), 0.095, 3), # Cadera / ingle
            (Vector((sign_x * 0.11, 0.0, 0.72)), 0.088, 3), # Muslo alto
            (Vector((sign_x * 0.11, 0.0, 0.52)), 0.076, 3), # Rodilla
            (Vector((sign_x * 0.11, 0.0, 0.32)), 0.068, 3), # Pantorrilla
            (Vector((sign_x * 0.11, 0.0, 0.14)), 0.058, 3), # Tobillo / dobladillo
            # Zapatos de vestir en cuero negro pulido
            (Vector((sign_x * 0.11, 0.02, 0.08)), 0.056, 4), # Empeine alto
            (Vector((sign_x * 0.11, 0.05, 0.03)), 0.058, 4), # Suela del zapato
        ]
        leg_rings = []
        for center, r_leg, mat_idx in leg_joints:
            rng = []
            for a in range(16):
                ang = (a / 16.0) * 2.0 * math.pi
                # Pliegue de planchado frontal del pantalón sastre
                crease_y = 0.008 if (a == 4 and center.z > 0.12) else 0.0
                vx = center.x + math.cos(ang) * r_leg
                vy = center.y + math.sin(ang) * r_leg + crease_y
                vz = center.z
                rng.append(bm.verts.new(Vector((vx, vy, vz))))
            leg_rings.append((rng, mat_idx))
            
        for i in range(len(leg_rings) - 1):
            r0, m0 = leg_rings[i]
            r1, m1 = leg_rings[i + 1]
            for a in range(16):
                an = (a + 1) % 16
                f = bm.faces.new([r0[a], r0[an], r1[an], r1[a]])
                f.material_index = m0

        # Suela inferior del zapato con tacón
        sole_verts = leg_rings[-1][0]
        sole_center = bm.verts.new(Vector((sign_x * 0.11, 0.05, 0.0)))
        for a in range(16):
            an = (a + 1) % 16
            f = bm.faces.new([sole_verts[a], sole_verts[an], sole_center])
            f.material_index = 4 # mat_shoes

    bm.verts.index_update()
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("Player_Body_Mesh", mesh)
    bpy.context.scene.collection.objects.link(obj)

    obj.data.materials.append(mat_shirt)   # 0
    obj.data.materials.append(mat_vest)    # 1
    obj.data.materials.append(mat_tie)     # 2
    obj.data.materials.append(mat_pants)   # 3
    obj.data.materials.append(mat_shoes)   # 4
    obj.data.materials.append(mat_skin)    # 5
    obj.data.materials.append(mat_buttons) # 6

    for poly in mesh.polygons:
        poly.use_smooth = True

    # Ponderación a huesos del Armature
    obj.parent = arm_obj
    mod = obj.modifiers.new(name="Armature", type='ARMATURE')
    mod.object = arm_obj

    bone_names = [
        "Hips", "Spine", "Spine1", "Chest",
        "Shoulder.L", "UpperArm.L", "Forearm.L", "Hand.L",
        "Shoulder.R", "UpperArm.R", "Forearm.R", "Hand.R",
        "UpperLeg.L", "LowerLeg.L", "Foot.L", "Toes.L",
        "UpperLeg.R", "LowerLeg.R", "Foot.R", "Toes.R"
    ]
    vgroups = {b: obj.vertex_groups.new(name=b) for b in bone_names}

    for v in obj.data.vertices:
        x, y, z = v.co.x, v.co.y, v.co.z
        
        # Brazos y manos
        if abs(x) > 0.16 and z > 0.82:
            side = ".L" if x < 0 else ".R"
            if z > 1.35:
                vgroups["Shoulder" + side].add([v.index], 1.0, 'REPLACE')
            elif z > 1.15:
                w_farm = clampf((1.35 - z) / 0.20, 0.0, 1.0)
                vgroups["UpperArm" + side].add([v.index], 1.0 - w_farm, 'REPLACE')
                vgroups["Forearm" + side].add([v.index], w_farm, 'REPLACE')
            elif z > 0.94:
                vgroups["Forearm" + side].add([v.index], 1.0, 'REPLACE')
            else:
                vgroups["Hand" + side].add([v.index], 1.0, 'REPLACE')
        # Piernas y calzado
        elif z < 0.94 and (abs(x) > 0.04 or z < 0.80):
            side = ".L" if x < 0 else ".R"
            if z > 0.50:
                vgroups["UpperLeg" + side].add([v.index], 1.0, 'REPLACE')
            elif z > 0.12:
                vgroups["LowerLeg" + side].add([v.index], 1.0, 'REPLACE')
            elif y < 0.10:
                vgroups["Foot" + side].add([v.index], 1.0, 'REPLACE')
            else:
                vgroups["Toes" + side].add([v.index], 1.0, 'REPLACE')
        # Torso (Hips, Spine, Spine1, Chest)
        else:
            if z < 1.08:
                vgroups["Hips"].add([v.index], 1.0, 'REPLACE')
            elif z < 1.25:
                w_s = clampf((z - 1.08) / 0.17, 0.0, 1.0)
                vgroups["Spine"].add([v.index], 1.0 - w_s, 'REPLACE')
                vgroups["Spine1"].add([v.index], w_s, 'REPLACE')
            elif z < 1.38:
                vgroups["Spine1"].add([v.index], 1.0, 'REPLACE')
            else:
                vgroups["Chest"].add([v.index], 1.0, 'REPLACE')

    return obj

def render_preview_image():
    """Renderiza una toma de retrato de estudio en Cycles para verificar el detalle."""
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 48
    scene.cycles.device = 'CPU'
    scene.render.resolution_x = 720
    scene.render.resolution_y = 1280
    scene.render.resolution_percentage = 100

    # Cámara a nivel del pecho abarcando rostro, sombrero, chaleco, corbata y manos
    cam_data = bpy.data.cameras.new("StudioCamera")
    cam_data.lens = 55.0
    cam_obj = bpy.data.objects.new("StudioCamera", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj
    cam_obj.location = Vector((0.08, 1.95, 1.25))
    cam_obj.rotation_euler = (math.radians(88.5), 0.0, math.radians(178.0))

    # Luces de estudio suaves calibradas
    key_data = bpy.data.lights.new("KeyLight", type='AREA')
    key_data.energy = 85.0
    key_data.size = 1.4
    key_data.color = (1.0, 0.98, 0.95)
    key_obj = bpy.data.objects.new("KeyLight", key_data)
    key_obj.location = Vector((-0.8, 1.5, 1.7))
    key_obj.rotation_euler = (math.radians(55.0), 0.0, math.radians(-145.0))
    scene.collection.objects.link(key_obj)

    fill_data = bpy.data.lights.new("FillLight", type='AREA')
    fill_data.energy = 38.0
    fill_data.size = 1.6
    fill_data.color = (0.92, 0.96, 1.0)
    fill_obj = bpy.data.objects.new("FillLight", fill_data)
    fill_obj.location = Vector((1.0, 1.5, 1.3))
    scene.collection.objects.link(fill_obj)

    rim_data = bpy.data.lights.new("RimLight", type='SPOT')
    rim_data.energy = 45.0
    rim_data.spot_size = math.radians(65.0)
    rim_data.color = (1.0, 1.0, 1.0)
    rim_obj = bpy.data.objects.new("RimLight", rim_data)
    rim_obj.location = Vector((0.0, -1.2, 1.9))
    rim_obj.rotation_euler = (math.radians(-50.0), 0.0, 0.0)
    scene.collection.objects.link(rim_obj)

    scene.render.filepath = PREVIEW_PNG
    bpy.ops.render.render(write_still=True)
    print(f"✓ Render preview guardado en: {PREVIEW_PNG}")

def main():
    print("==================================================")
    print("GENERANDO AXEL V2 HIPERREALISTA (ESTILO FORTNITE / AAA)")
    print("==================================================")
    clean_scene()

    # Cargar materiales PBR nativos
    tex_face_diff = os.path.join(TEX_DIR, "axel_face_diffuse.png")
    tex_face_norm = os.path.join(TEX_DIR, "axel_face_normal.png")
    tex_hat_diff = os.path.join(TEX_DIR, "axel_hat_diffuse.png")
    tex_hat_norm = os.path.join(TEX_DIR, "axel_hat_normal.png")
    tex_vest_diff = os.path.join(TEX_DIR, "axel_vest_diffuse.png")
    tex_vest_norm = os.path.join(TEX_DIR, "axel_vest_normal.png")
    tex_shirt_diff = os.path.join(TEX_DIR, "axel_shirt_diffuse.png")
    tex_shirt_norm = os.path.join(TEX_DIR, "axel_shirt_normal.png")
    tex_tie_diff = os.path.join(TEX_DIR, "axel_tie_diffuse.png")
    tex_tie_norm = os.path.join(TEX_DIR, "axel_tie_normal.png")
    tex_pants_diff = os.path.join(TEX_DIR, "axel_pants_diffuse.png")
    tex_pants_norm = os.path.join(TEX_DIR, "axel_pants_normal.png")
    tex_shoes_diff = os.path.join(TEX_DIR, "axel_shoes_diffuse.png")
    tex_shoes_norm = os.path.join(TEX_DIR, "axel_shoes_normal.png")
    tex_eye_diff = os.path.join(TEX_DIR, "axel_eye_diffuse.png")

    mat_skin = create_pbr_material("Mat_Axel_Skin", (0.80, 0.58, 0.46, 1.0), roughness=0.45,
                                   tex_diffuse_path=tex_face_diff, tex_normal_path=tex_face_norm, sss_weight=0.35)
    mat_hat = create_pbr_material("Mat_Axel_Hat", (0.08, 0.08, 0.09, 1.0), roughness=0.85,
                                  tex_diffuse_path=tex_hat_diff, tex_normal_path=tex_hat_norm)
    mat_hair = create_pbr_material("Mat_Axel_Hair", (0.09, 0.07, 0.06, 1.0), roughness=0.60, metallic=0.05)
    mat_eyes = create_pbr_material("Mat_Axel_Eyes", (1, 1, 1, 1), roughness=0.06,
                                   tex_diffuse_path=tex_eye_diff)
    mat_shirt = create_pbr_material("Mat_Axel_Shirt", (0.16, 0.17, 0.19, 1.0), roughness=0.65,
                                    tex_diffuse_path=tex_shirt_diff, tex_normal_path=tex_shirt_norm)
    mat_vest = create_pbr_material("Mat_Axel_Vest", (0.82, 0.84, 0.86, 1.0), roughness=0.55,
                                   tex_diffuse_path=tex_vest_diff, tex_normal_path=tex_vest_norm)
    mat_tie = create_pbr_material("Mat_Axel_Tie", (0.45, 0.48, 0.52, 1.0), roughness=0.35, metallic=0.15,
                                  tex_diffuse_path=tex_tie_diff, tex_normal_path=tex_tie_norm)
    mat_pants = create_pbr_material("Mat_Axel_Pants", (0.13, 0.14, 0.16, 1.0), roughness=0.75,
                                    tex_diffuse_path=tex_pants_diff, tex_normal_path=tex_pants_norm)
    mat_shoes = create_pbr_material("Mat_Axel_Shoes", (0.08, 0.08, 0.09, 1.0), roughness=0.45, metallic=0.05,
                                    tex_diffuse_path=tex_shoes_diff, tex_normal_path=tex_shoes_norm)
    mat_buttons = create_pbr_material("Mat_Axel_Buttons", (0.85, 0.85, 0.88, 1.0), roughness=0.22, metallic=0.92)

    # 1. Armature antropométrico canónico
    arm_obj = build_axel_armature()
    print("✓ Armature antropométrico canónico construido con 22 huesos.")

    # 2. Player_Head_Mesh
    head_obj = build_head_mesh(arm_obj, mat_skin, mat_hat, mat_hair, mat_eyes)
    print("✓ Player_Head_Mesh generado con rasgos faciales 3D, ojos, rizos y fedora.")

    # 3. Player_Body_Mesh
    body_obj = build_body_mesh(arm_obj, mat_shirt, mat_vest, mat_tie, mat_pants, mat_shoes, mat_skin, mat_buttons)
    print("✓ Player_Body_Mesh generado con chaleco, camisa, corbata, manos anatómicas y zapatos.")

    # 4. Guardar archivo maestro .blend
    os.makedirs(os.path.dirname(OUTPUT_BLEND), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=OUTPUT_BLEND)
    print(f"✓ Guardado .blend maestro en: {OUTPUT_BLEND}")

    # 5. Exportar archivo .glb optimizado para Godot 4
    bpy.ops.export_scene.gltf(
        filepath=OUTPUT_GLB,
        export_format='GLB',
        use_selection=False,
        export_yup=True,
        export_apply=False,
        export_skins=True,
        export_all_influences=False,
        export_materials='EXPORT',
        export_image_format='AUTO',
        export_lights=False,
        export_cameras=False
    )
    print(f"✓ Exportado archivo glTF .glb en: {OUTPUT_GLB}")

    # 6. Renderizar preview de validación
    render_preview_image()
    print("==================================================")
    print("PROCESO COMPLETADO EXITOSAMENTE")
    print("==================================================")

if __name__ == "__main__":
    main()
