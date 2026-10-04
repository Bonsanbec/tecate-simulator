"""
Generador de Fondo Abstracto Formado por Triángulos (Diseño Moderno)
Para la Tarjeta de Selección de Eli (eli_card.png)
"""
import bpy
import math
import os
from mathutils import Vector, Euler

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
OUTPUT_BG = os.path.join(PROJECT_ROOT, "scratch/fondo_eli_triangulos.png")

def create_modern_triangle_background():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene

    # Configuración de render 1024x1024
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 64
    scene.render.resolution_x = 1024
    scene.render.resolution_y = 1024
    scene.render.film_transparent = False

    # Cámara ortogonal centrada
    cam_data = bpy.data.cameras.new("OrthoCam")
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = 2.4
    cam_obj = bpy.data.objects.new("OrthoCam", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj
    cam_obj.location = Vector((0.0, -3.0, 0.0))
    cam_obj.rotation_euler = (math.radians(90.0), 0.0, 0.0)

    # Materiales para los triángulos con paleta de diseño contemporáneo
    palette = [
        ("Mat_DeepNavy",   (0.04, 0.06, 0.12, 1.0), 0.35, 0.10),
        ("Mat_Indigo",     (0.08, 0.14, 0.25, 1.0), 0.40, 0.05),
        ("Mat_TealDark",   (0.09, 0.28, 0.35, 1.0), 0.45, 0.05),
        ("Mat_TealBright", (0.15, 0.48, 0.55, 1.0), 0.35, 0.05),
        ("Mat_CyanMuted",  (0.28, 0.62, 0.68, 1.0), 0.30, 0.05),
        ("Mat_GoldAccent", (0.82, 0.60, 0.24, 1.0), 0.25, 0.50),
        ("Mat_AmberSoft",  (0.88, 0.72, 0.42, 1.0), 0.30, 0.30),
        ("Mat_IvoryLinen", (0.90, 0.88, 0.82, 1.0), 0.50, 0.00),
        ("Mat_SlateGrey",  (0.18, 0.22, 0.28, 1.0), 0.45, 0.05),
        ("Mat_WarmCharcoal",(0.07, 0.08, 0.10, 1.0), 0.50, 0.00),
    ]

    mat_objs = []
    for name, color, roughness, metallic in palette:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = color
            bsdf.inputs["Roughness"].default_value = roughness
            bsdf.inputs["Metallic"].default_value = metallic
        mat_objs.append(mat)

    # Plano base oscuro posterior
    bg_plane_mesh = bpy.data.meshes.new("Backplane")
    bg_plane_obj = bpy.data.objects.new("Backplane", bg_plane_mesh)
    scene.collection.objects.link(bg_plane_obj)
    verts_bg = [
        Vector((-1.5, 0.30, -1.5)),
        Vector(( 1.5, 0.30, -1.5)),
        Vector(( 1.5, 0.30,  1.5)),
        Vector((-1.5, 0.30,  1.5)),
    ]
    bg_plane_mesh.from_pydata(verts_bg, [], [(0, 1, 2, 3)])
    bg_plane_obj.data.materials.append(mat_objs[0])

    # Construcción de una figura abstracta moderna compuesta por triángulos facetados (Delaunay-style)
    # Vértices de una red geométrica poligonal abstracta dinámica en el plano XZ con leves relieves en Y
    mesh_tri = bpy.data.meshes.new("ModernAbstractTriangles")
    obj_tri = bpy.data.objects.new("ModernAbstractTriangles", mesh_tri)
    scene.collection.objects.link(obj_tri)

    for m in mat_objs:
        obj_tri.data.materials.append(m)

    # Nodos de la red geométrica moderna (figura abstracta piramidal/cristalina ascendente)
    nodes = [
        # Centro y núcleo geométrico
        ( 0.00,  0.02,  0.00), # 0
        ( 0.25,  0.08,  0.20), # 1
        (-0.22,  0.06,  0.25), # 2
        ( 0.35,  0.04, -0.15), # 3
        (-0.30,  0.05, -0.20), # 4
        ( 0.05,  0.12,  0.45), # 5 (pico alto central)
        (-0.05, -0.02, -0.42), # 6 (base inferior)

        # Rama superior derecha
        ( 0.50,  0.06,  0.42), # 7
        ( 0.20,  0.10,  0.68), # 8
        ( 0.55,  0.04,  0.72), # 9
        ( 0.00,  0.08,  0.92), # 10 (cúspide superior)
        ( 0.72, -0.02,  0.25), # 11
        ( 0.85, -0.04,  0.55), # 12

        # Rama superior izquierda
        (-0.45,  0.05,  0.48), # 13
        (-0.25,  0.09,  0.75), # 14
        (-0.55,  0.03,  0.78), # 15
        (-0.75, -0.02,  0.30), # 16
        (-0.85, -0.04,  0.60), # 17

        # Cintura lateral y expansión media
        ( 0.65,  0.02, -0.10), # 18
        ( 0.90, -0.05, -0.05), # 19
        (-0.60,  0.03, -0.12), # 20
        (-0.88, -0.05, -0.08), # 21

        # Rama inferior derecha
        ( 0.40,  0.05, -0.45), # 22
        ( 0.68, -0.02, -0.40), # 23
        ( 0.25,  0.02, -0.72), # 24
        ( 0.55, -0.04, -0.75), # 25
        ( 0.80, -0.06, -0.55), # 26

        # Rama inferior izquierda
        (-0.38,  0.04, -0.48), # 27
        (-0.65, -0.02, -0.42), # 28
        (-0.22,  0.02, -0.76), # 29
        (-0.52, -0.04, -0.78), # 30
        (-0.78, -0.06, -0.58), # 31

        # Base inferior extrema
        ( 0.00,  0.00, -0.98), # 32
        ( 0.32, -0.05, -1.05), # 33
        (-0.30, -0.05, -1.05), # 34

        # Perímetro de fondo envolvente
        (-1.25, -0.10,  1.25), # 35
        ( 0.00, -0.08,  1.25), # 36
        ( 1.25, -0.10,  1.25), # 37
        ( 1.25, -0.10,  0.00), # 38
        ( 1.25, -0.10, -1.25), # 39
        ( 0.00, -0.08, -1.25), # 40
        (-1.25, -0.10, -1.25), # 41
        (-1.25, -0.10,  0.00), # 42
    ]

    verts = [Vector((n[0], n[1], n[2])) for n in nodes]

    # Lista de caras triangulares (índice_v1, índice_v2, índice_v3, mat_idx)
    # Combinando turquesas, índigos, toques de oro y marfil moderno
    triangles_def = [
        # Núcleo
        (0, 1, 5, 3), # TealBright
        (0, 5, 2, 4), # CyanMuted
        (0, 2, 4, 2), # TealDark
        (0, 4, 6, 1), # Indigo
        (0, 6, 3, 5), # GoldAccent
        (0, 3, 1, 6), # AmberSoft

        # Corona superior
        (5, 1, 8, 7), # IvoryLinen
        (1, 7, 8, 3), # TealBright
        (5, 8, 10, 5), # GoldAccent
        (5, 10, 14, 6), # AmberSoft
        (5, 14, 2, 4), # CyanMuted
        (2, 14, 13, 2), # TealDark
        (8, 9, 10, 3), # TealBright
        (8, 7, 9, 1), # Indigo
        (14, 10, 15, 7), # IvoryLinen
        (14, 15, 13, 3), # TealBright

        # Flancos superiores
        (7, 11, 9, 2),
        (9, 11, 12, 1),
        (13, 15, 16, 2),
        (15, 17, 16, 1),
        (1, 3, 18, 5), # Acento dorado
        (1, 18, 7, 3),
        (7, 18, 11, 8),
        (2, 13, 20, 4),
        (2, 20, 4, 2),
        (13, 16, 20, 8),

        # Cintura lateral
        (18, 19, 11, 1),
        (11, 19, 12, 8),
        (20, 16, 21, 1),
        (16, 17, 21, 8),
        (3, 22, 18, 2),
        (18, 22, 23, 1),
        (18, 23, 19, 8),
        (4, 20, 27, 2),
        (20, 28, 27, 1),
        (20, 21, 28, 8),

        # Parte inferior
        (6, 4, 27, 1),
        (6, 27, 29, 3),
        (6, 29, 32, 5), # Acento dorado
        (6, 32, 24, 6), # Acento ámbar
        (6, 24, 22, 4),
        (6, 22, 3, 2),

        (27, 28, 30, 2),
        (27, 30, 29, 3),
        (29, 30, 34, 1),
        (29, 34, 32, 5),

        (22, 24, 25, 3),
        (22, 25, 23, 2),
        (24, 32, 33, 6),
        (24, 33, 25, 1),

        (23, 25, 26, 8),
        (19, 23, 26, 9),
        (28, 31, 30, 8),
        (21, 28, 31, 9),

        (32, 34, 40, 1),
        (32, 40, 33, 1),
        (34, 30, 40, 8),
        (33, 40, 25, 8),

        # Perímetro exterior hacia el marco
        (10, 9, 37, 8),
        (10, 37, 36, 1),
        (10, 36, 35, 1),
        (10, 35, 15, 8),
        (9, 12, 37, 9),
        (12, 38, 37, 8),
        (12, 19, 38, 9),
        (15, 35, 17, 9),
        (17, 35, 42, 8),
        (17, 42, 21, 9),
        (19, 26, 38, 9),
        (26, 39, 38, 8),
        (26, 25, 39, 9),
        (25, 33, 39, 9),
        (33, 40, 39, 8),
        (21, 42, 31, 9),
        (31, 42, 41, 8),
        (31, 41, 30, 9),
        (30, 41, 40, 8),
    ]

    faces = [(t[0], t[1], t[2]) for t in triangles_def]
    mesh_tri.from_pydata(verts, [], faces)
    mesh_tri.update()

    for idx, poly in enumerate(mesh_tri.polygons):
        poly.material_index = triangles_def[idx][3]

    # Iluminación de estudio moderna para realzar el relieve facetado
    l1 = bpy.data.lights.new("ModernKeyLight", 'AREA')
    l1.energy = 85.0
    l1.size = 1.8
    l1.color = (1.0, 0.98, 0.95)
    lo1 = bpy.data.objects.new("ModernKeyLight", l1)
    lo1.location = Vector((-1.2, -2.2, 1.4))
    lo1.rotation_euler = (math.radians(55), 0, math.radians(-30))
    scene.collection.objects.link(lo1)

    l2 = bpy.data.lights.new("ModernFillLight", 'AREA')
    l2.energy = 35.0
    l2.size = 2.2
    l2.color = (0.75, 0.88, 1.0)
    lo2 = bpy.data.objects.new("ModernFillLight", l2)
    lo2.location = Vector((1.4, -2.0, -0.8))
    lo2.rotation_euler = (math.radians(65), 0, math.radians(40))
    scene.collection.objects.link(lo2)

    l3 = bpy.data.lights.new("ModernGoldAccent", 'POINT')
    l3.energy = 25.0
    l3.color = (1.0, 0.82, 0.55)
    lo3 = bpy.data.objects.new("ModernGoldAccent", l3)
    lo3.location = Vector((0.1, -1.2, 0.2))
    scene.collection.objects.link(lo3)

    os.makedirs(os.path.dirname(OUTPUT_BG), exist_ok=True)
    scene.render.filepath = OUTPUT_BG
    bpy.ops.render.render(write_still=True)
    print(f"✓ Fondo abstracto moderno de triángulos guardado en: {OUTPUT_BG}")

if __name__ == "__main__":
    create_modern_triangle_background()
