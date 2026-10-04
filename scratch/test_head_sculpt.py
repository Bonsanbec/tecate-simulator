"""
Prototipo de modelado anatómico procedural de alta fidelidad para la cabeza y rostro de Axel.
Utiliza modelado poligonal de bucles anatómicos (edge loops) con modificador Subdivision Surface (Catmull-Clark).
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

def build_human_head():
    """
    Construye una cabeza humana estilizada de alta calidad (estilo Fortnite/Pixar)
    usando una topología limpia de quads con modificador Subdivision Surface.
    """
    mesh = bpy.data.meshes.new("Head_Base_Mesh")
    bm = bmesh.new()

    # Definimos la cabeza a partir de anillos de sección horizontal cuidadosamente modelados
    # que capturan: nuca, occipital, mandíbula, mentón, boca, surco nasolabial, nariz, órbitas, frente y cráneo.
    
    # Alturas Z de las secciones anatómicas:
    # 1. Base del cuello (entra en la chamarra): Z = 1.48
    # 2. Mitad del cuello (nuez de Adán): Z = 1.52
    # 3. Mandíbula inferior y mentón: Z = 1.56
    # 4. Labio inferior y comisura: Z = 1.585
    # 5. Labio superior y arco de Cupido: Z = 1.605
    # 6. Fosas nasales y base de la nariz: Z = 1.625
    # 7. Punta y puente nasal: Z = 1.645
    # 8. Ojos y cuencas orbitarias: Z = 1.680
    # 9. Cejas y arco superciliar: Z = 1.705
    # 10. Frente inferior: Z = 1.730
    # 11. Frente media (línea de inserción del cabello / borde del beanie): Z = 1.755
    # 12. Parietal / Bóveda craneal: Z = 1.785
    # 13. Coronilla / Vértice: Z = 1.815

    sections = [
        # (z, rx_lateral, ry_anterior, ry_posterior, offset_y_center, chin_disp, nose_disp, lip_disp, eye_socket)
        # z,     rx,    y_front, y_back, y_cen, chin, nose, lips, eyes
        (1.480, 0.052, 0.050, -0.050,  0.000, 0.000, 0.000, 0.000, 0.000), # Base cuello
        (1.520, 0.050, 0.052, -0.052,  0.002, 0.000, 0.000, 0.000, 0.000), # Nuez cuello
        (1.555, 0.058, 0.070, -0.058,  0.006, 0.016, 0.000, 0.000, 0.000), # Mentón y ángulo mandibular
        (1.585, 0.063, 0.076, -0.064,  0.008, 0.005, 0.000, 0.014, 0.000), # Labio inferior
        (1.605, 0.066, 0.078, -0.068,  0.008, 0.000, 0.000, 0.016, 0.000), # Labio superior / filtrum
        (1.625, 0.068, 0.082, -0.072,  0.006, 0.000, 0.024, 0.000, 0.000), # Fosas nasales / ala nasi
        (1.645, 0.071, 0.082, -0.075,  0.004, 0.000, 0.028, 0.000, 0.000), # Punta y dorso nasal
        (1.680, 0.074, 0.078, -0.078,  0.000, 0.000, 0.016, 0.000, 0.018), # Ojos y cuencas
        (1.705, 0.075, 0.080, -0.080, -0.002, 0.000, 0.000, 0.000, 0.000), # Cejas y arco supraciliar
        (1.730, 0.075, 0.080, -0.080, -0.004, 0.000, 0.000, 0.000, 0.000), # Frente baja
        (1.755, 0.074, 0.076, -0.080, -0.006, 0.000, 0.000, 0.000, 0.000), # Frente alta / inicio beanie
        (1.785, 0.070, 0.068, -0.076, -0.008, 0.000, 0.000, 0.000, 0.000), # Parietal
        (1.815, 0.055, 0.052, -0.060, -0.010, 0.000, 0.000, 0.000, 0.000), # Coronilla alta
    ]

    # Número de meridianos (vértices por anillo)
    num_meridians = 24
    grid_rings = []

    for z, rx, y_f, y_b, y_c, chin, nose, lips, eyes in sections:
        ring = []
        for mi in range(num_meridians):
            angle = (2.0 * math.pi * mi) / num_meridians
            cos_a = math.cos(angle)
            sin_a = math.sin(angle)

            # X coordenada
            vx = sin_a * rx

            # Y coordenada: anterior vs posterior
            if cos_a >= 0:
                vy = y_c + cos_a * y_f
            else:
                vy = y_c + abs(cos_a) * y_b

            # Modulaciones anatómicas específicas:
            # A. Mentón (en la zona frontal centro)
            if chin > 0 and cos_a > 0.7:
                vy += chin * math.cos((1.0 - cos_a) * math.pi / 0.6)

            # B. Labios (proyección anterior de la boca)
            if lips > 0 and cos_a > 0.6:
                vy += lips * math.cos((1.0 - cos_a) * math.pi / 0.8)

            # C. Nariz (pirámide nasal estrecha en la línea media frontal)
            if nose > 0 and abs(vx) < 0.024 and cos_a > 0.8:
                lateral_falloff = 1.0 - (abs(vx) / 0.024)
                vy += nose * lateral_falloff

            # D. Cuencas oculares (recesión de los ojos a ambos lados de la nariz)
            if eyes > 0 and cos_a > 0.7:
                # Ojos en x ~ +/- 0.032
                for eye_x in [-0.032, 0.032]:
                    dist_eye = abs(vx - eye_x)
                    if dist_eye < 0.022:
                        eye_falloff = 1.0 - (dist_eye / 0.022)
                        vy -= eyes * eye_falloff

            v = bm.verts.new(Vector((vx, vy, z)))
            ring.append(v)
        grid_rings.append(ring)

    # Conectar anillos en caras quads
    for ri in range(len(grid_rings) - 1):
        r_cur = grid_rings[ri]
        r_nxt = grid_rings[ri + 1]
        for mi in range(num_meridians):
            m_nxt = (mi + 1) % num_meridians
            bm.faces.new([r_cur[mi], r_cur[m_nxt], r_nxt[m_nxt], r_nxt[mi]])

    # Tapa superior del cráneo (polo superior)
    v_top = bm.verts.new(Vector((0.0, -0.010, 1.835)))
    r_last = grid_rings[-1]
    for mi in range(num_meridians):
        m_nxt = (mi + 1) % num_meridians
        bm.faces.new([r_last[mi], r_last[m_nxt], v_top])

    bm.verts.index_update()
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("Head_Object", mesh)
    bpy.context.scene.collection.objects.link(obj)

    # Modificador Subdivision Surface Catmull-Clark
    subsurf = obj.modifiers.new(name="Subsurf", type='SUBSURF')
    subsurf.levels = 2
    subsurf.render_levels = 2

    # Smooth shading
    for poly in mesh.polygons:
        poly.use_smooth = True

    return obj

clean_scene()
head_obj = build_human_head()

# Render test
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 16
scene.cycles.device = 'CPU'
scene.render.resolution_x = 720
scene.render.resolution_y = 1280

cam_data = bpy.data.cameras.new("Cam")
cam_data.lens = 65.0
cam = bpy.data.objects.new("Cam", cam_data)
cam.location = Vector((0.0, 1.2, 1.66))
cam.rotation_euler = (math.radians(88.0), 0.0, math.radians(180.0))
scene.collection.objects.link(cam)
scene.camera = cam

light_data = bpy.data.lights.new("Light", type='AREA')
light_data.energy = 250.0
light_data.size = 1.0
light = bpy.data.objects.new("Light", light_data)
light.location = Vector((-0.8, 1.0, 2.0))
scene.collection.objects.link(light)

fill_data = bpy.data.lights.new("Fill", type='AREA')
fill_data.energy = 80.0
fill = bpy.data.objects.new("Fill", fill_data)
fill.location = Vector((0.8, 1.0, 1.6))
scene.collection.objects.link(fill)

scene.render.filepath = os.path.abspath("scratch/test_head_render.png")
bpy.ops.render.render(write_still=True)
print("Rendered scratch/test_head_render.png")
