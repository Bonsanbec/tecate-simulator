"""
Prototipo y calibración anatómica de la mano humana con pulgar oponible y dorso hacia el frente.
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

def build_test_hand(sign_x=1.0):
    """
    Construye una mano humana realista (sign_x = +1 para mano derecha, -1 para izquierda).
    - Dorso hacia el frente (+Y)
    - Palma hacia atrás (-Y)
    - Pulgar OPONIBLE naciendo en el borde medial (hacia el cuerpo) y curvándose hacia la palma
    - 4 dedos (índice, medio, anular, meñique) escalonados con articulaciones
    """
    mesh = bpy.data.meshes.new("Hand_Mesh_Data")
    bm = bmesh.new()

    p_wrist = Vector((0.0, 0.0, 0.0))

    # 1. Bloque de la palma / dorso (metacarpo)
    # Dimensiones: ancho ~ 0.075m, grosor ~ 0.028m, largo ~ 0.085m
    w_palm = 0.038
    t_palm = 0.015
    l_palm = 0.075

    # Capas de la palma desde la muñeca hasta los nudillos
    palm_layers = [
        # (z_offset, w_scale, t_scale, y_shift)
        ( 0.000, 0.70, 0.85, 0.000), # Muñeca
        (-0.025, 0.90, 1.00, 0.002), # Eminencia tenar / mitad palma
        (-0.055, 1.05, 0.95, 0.004), # Zona pre-nudillos
        (-0.075, 1.00, 0.80, 0.002), # Arco de los nudillos
    ]
    palm_rings = []
    for dz, ws, ts, dy in palm_layers:
        r = []
        # Anillo elíptico aplanado de 12 vértices
        rx = w_palm * ws
        ry = t_palm * ts
        for i in range(12):
            ang = (2.0 * math.pi * i) / 12.0
            vx = math.cos(ang) * rx
            vy = dy + math.sin(ang) * ry
            vz = dz
            r.append(bm.verts.new(Vector((vx, vy, vz))))
        palm_rings.append(r)

    for li in range(len(palm_rings) - 1):
        r0 = palm_rings[li]
        r1 = palm_rings[li + 1]
        for i in range(12):
            i_n = (i + 1) % 12
            bm.faces.new([r0[i], r0[i_n], r1[i_n], r1[i]])

    # 2. Pulgar Oponible Anatómico
    # Emerge del borde medial (-sign_x) en la eminencia tenar (Y ligeramente hacia atrás, -Y)
    # y se proyecta hacia la palma / dedos
    def add_digit(segments_pts, radii):
        dig_rings = []
        for pt, r in zip(segments_pts, radii):
            dr = []
            for a in range(8):
                ang = (2.0 * math.pi * a) / 8.0
                vx = pt.x + math.cos(ang) * r
                vy = pt.y + math.sin(ang) * r
                vz = pt.z
                dr.append(bm.verts.new(Vector((vx, vy, vz))))
            dig_rings.append(dr)
        for i in range(len(dig_rings) - 1):
            r0 = dig_rings[i]
            r1 = dig_rings[i + 1]
            for a in range(8):
                a_n = (a + 1) % 8
                bm.faces.new([r0[a], r0[a_n], r1[a_n], r1[a]])
        # Tapa punta
        tip = bm.verts.new(segments_pts[-1] + Vector((0, 0, -radii[-1] * 0.4)))
        for a in range(8):
            a_n = (a + 1) % 8
            bm.faces.new([dig_rings[-1][a], dig_rings[-1][a_n], tip])

    # Pulgar oponible: medial, curvado hacia la palma (-Y)
    # Nace en X=-0.025, Y=-0.005, Z=-0.025
    thumb_pts = [
        Vector((-sign_x * 0.025, -0.005, -0.025)), # Base eminencia tenar
        Vector((-sign_x * 0.038, -0.008, -0.045)), # Articulación metacarpofalángica
        Vector((-sign_x * 0.034, -0.016, -0.065)), # Articulación interfalángica (curva hacia palma)
        Vector((-sign_x * 0.024, -0.022, -0.080)), # Punta del pulgar (en oposición frente a los dedos)
    ]
    add_digit(thumb_pts, [0.012, 0.011, 0.0095, 0.0075])

    # 3. Cuatro Dedos (Índice, Medio, Anular, Meñique)
    # Distribuidos en el arco distal de los nudillos (Z = -0.075)
    finger_data = [
        # (nombre, x_offset, largo, radio_base)
        ("Index",  -sign_x * 0.018, 0.068, 0.0095),
        ("Middle", -sign_x * 0.006, 0.076, 0.0100),
        ("Ring",    sign_x * 0.008, 0.070, 0.0090),
        ("Pinky",   sign_x * 0.022, 0.055, 0.0080),
    ]

    for name, fx, flen, frad in finger_data:
        # Nudillo
        p_knuckle = Vector((fx, 0.002, -0.075))
        # Falange proximal (curvatura relajada hacia -Y)
        p_pip = p_knuckle + Vector((0.0, -0.006, -flen * 0.45))
        # Falange media
        p_dip = p_pip + Vector((0.0, -0.012, -flen * 0.35))
        # Falange distal / punta
        p_tip = p_dip + Vector((0.0, -0.016, -flen * 0.20))

        add_digit([p_knuckle, p_pip, p_dip, p_tip], [frad, frad * 0.90, frad * 0.75, frad * 0.55])

    bm.verts.index_update()
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("Hand_Obj", mesh)
    bpy.context.scene.collection.objects.link(obj)

    mat = bpy.data.materials.new("Skin_Hand")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.76, 0.58, 0.48, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.50
    obj.data.materials.append(mat)

    for poly in mesh.polygons:
        poly.use_smooth = True

    subsurf = obj.modifiers.new(name="Subsurf", type='SUBSURF')
    subsurf.levels = 2
    subsurf.render_levels = 2

    return obj

clean_scene()
hand_obj = build_test_hand(sign_x=1.0) # Mano derecha

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 24
scene.cycles.device = 'CPU'
scene.render.resolution_x = 720
scene.render.resolution_y = 720

cam_data = bpy.data.cameras.new("Cam")
cam_data.lens = 75.0
cam = bpy.data.objects.new("Cam", cam_data)
# Cámara frontal mirando al dorso de la mano (+Y -> -Y)
cam.location = Vector((0.0, 0.45, -0.07))
cam.rotation_euler = (math.radians(90.0), 0.0, math.radians(180.0))
scene.collection.objects.link(cam)
scene.camera = cam

light_data = bpy.data.lights.new("Light", type='AREA')
light_data.energy = 25.0
light_data.size = 0.4
light = bpy.data.objects.new("Light", light_data)
light.location = Vector((-0.2, 0.4, 0.1))
scene.collection.objects.link(light)

scene.render.filepath = os.path.abspath("scratch/test_hand_render.png")
bpy.ops.render.render(write_still=True)
print("Rendered scratch/test_hand_render.png")
