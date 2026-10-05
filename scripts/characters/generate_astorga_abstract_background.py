"""
=============================================================================
GENERADOR DE FONDO ABSTRACTO ACÚSTICO / SINFÓNICO: ASTORGA
=============================================================================
Tecate Simulator - Fondo Cinemático para la Tarjeta de Selección (astorga_card.png)

Crea una composición geométrica abstracta inspirada en difusores y reflectores
acústicos de salas sinfónicas, con la paleta de Astorga:
- Terracota oficial Tecate (Pueblo Mágico)
- Ámbar cálido de arce barnizado
- Borgoña profundo de sala de concierto
- Ébano acústico y oro pulido
Guarda el render en 'scratch/fondo_astorga.png'.
=============================================================================
"""

import bpy
import math
import os
from mathutils import Vector, Euler

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
OUTPUT_BG = os.path.join(PROJECT_ROOT, "scratch/fondo_astorga.png")

def create_acoustic_acoustic_background():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene

    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 64
    scene.render.resolution_x = 1024
    scene.render.resolution_y = 1024
    scene.render.film_transparent = False

    # Cámara ortogonal
    cam_data = bpy.data.cameras.new("OrthoCam")
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = 2.4
    cam_obj = bpy.data.objects.new("OrthoCam", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj
    cam_obj.location = Vector((0.0, -3.0, 0.0))
    cam_obj.rotation_euler = (math.radians(90.0), 0.0, 0.0)

    palette = [
        ("Mat_DeepEbony",      (0.045, 0.050, 0.065, 1.0), 0.40, 0.10),
        ("Mat_BurgundyHall",   (0.240, 0.055, 0.080, 1.0), 0.45, 0.05),
        ("Mat_TerracottaTecate",(0.940, 0.310, 0.140, 1.0), 0.35, 0.10),
        ("Mat_AmberWood",      (0.720, 0.420, 0.160, 1.0), 0.30, 0.25),
        ("Mat_GoldConcert",    (0.880, 0.680, 0.220, 1.0), 0.25, 0.50),
        ("Mat_WarmCharcoal",   (0.080, 0.090, 0.110, 1.0), 0.50, 0.00),
        ("Mat_IvoryBow",       (0.920, 0.880, 0.820, 1.0), 0.35, 0.05),
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

    # Plano base posterior
    bg_mesh = bpy.data.meshes.new("Backplane")
    bg_obj = bpy.data.objects.new("Backplane", bg_mesh)
    scene.collection.objects.link(bg_obj)
    verts_bg = [
        Vector((-1.5, 0.30, -1.5)),
        Vector(( 1.5, 0.30, -1.5)),
        Vector(( 1.5, 0.30,  1.5)),
        Vector((-1.5, 0.30,  1.5)),
    ]
    bg_mesh.from_pydata(verts_bg, [], [(0, 1, 2, 3)])
    bg_obj.data.materials.append(mat_objs[0])

    # Red geométrica armónica: facetado tipo difusor acústico
    tri_mesh = bpy.data.meshes.new("AcousticFacets")
    tri_obj = bpy.data.objects.new("AcousticFacets", tri_mesh)
    scene.collection.objects.link(tri_obj)
    for m in mat_objs:
        tri_obj.data.materials.append(m)

    nodes = [
        ( 0.00,  0.04,  0.00), # 0: Centro
        ( 0.22,  0.10,  0.18), # 1
        (-0.24,  0.08,  0.22), # 2
        ( 0.32,  0.06, -0.16), # 3
        (-0.30,  0.05, -0.22), # 4
        ( 0.06,  0.14,  0.42), # 5
        (-0.04, -0.02, -0.38), # 6
        ( 0.48,  0.08,  0.38), # 7
        ( 0.20,  0.12,  0.64), # 8
        ( 0.52,  0.05,  0.68), # 9
        ( 0.00,  0.10,  0.88), # 10
        (-0.25,  0.12,  0.62), # 11
        (-0.50,  0.06,  0.36), # 12
        (-0.54,  0.04,  0.66), # 13
        ( 0.58,  0.02,  0.08), # 14
        (-0.56,  0.02,  0.06), # 15
        ( 0.44,  0.00, -0.42), # 16
        (-0.42,  0.00, -0.44), # 17
        ( 0.18, -0.04, -0.66), # 18
        (-0.16, -0.04, -0.68), # 19
        ( 0.00, -0.06, -0.88), # 20
    ]

    faces_def = [
        ((0, 1, 5), 2),  # Terracotta
        ((0, 5, 2), 3),  # Amber
        ((0, 2, 4), 1),  # Burgundy
        ((0, 4, 6), 5),  # Charcoal
        ((0, 6, 3), 3),  # Amber
        ((0, 3, 1), 4),  # Gold
        ((1, 7, 5), 4),  # Gold
        ((5, 7, 9), 2),  # Terracotta
        ((5, 9, 8), 3),  # Amber
        ((5, 8, 10), 4), # Gold
        ((5, 10, 11), 6),# Ivory
        ((5, 11, 2), 1), # Burgundy
        ((2, 11, 13), 2),# Terracotta
        ((2, 13, 12), 3),# Amber
        ((2, 12, 4), 1), # Burgundy
        ((1, 14, 7), 5), # Charcoal
        ((3, 14, 1), 3), # Amber
        ((4, 15, 2), 5), # Charcoal
        ((4, 12, 15), 1),# Burgundy
        ((3, 16, 14), 4),# Gold
        ((3, 6, 16), 1), # Burgundy
        ((4, 17, 15), 3),# Amber
        ((4, 6, 17), 5), # Charcoal
        ((6, 18, 16), 2),# Terracotta
        ((6, 20, 18), 3),# Amber
        ((6, 19, 20), 1),# Burgundy
        ((6, 17, 19), 5),# Charcoal
    ]

    verts = [Vector(n) for n in nodes]
    faces = [f[0] for f in faces_def]
    tri_mesh.from_pydata(verts, [], faces)

    for i, (_, m_idx) in enumerate(faces_def):
        tri_mesh.polygons[i].material_index = m_idx

    # Iluminación de estudio
    def add_light(name, energy, loc, color=(1.0, 1.0, 1.0)):
        ld = bpy.data.lights.new(name, 'AREA')
        ld.energy = energy
        ld.color = color
        ld.size = 2.0
        lo = bpy.data.objects.new(name, ld)
        lo.location = loc
        scene.collection.objects.link(lo)
        return lo

    add_light("LightKey",   220.0, ( 0.8, -2.2,  1.2), color=(1.0, 0.95, 0.88))
    add_light("LightWarm",  160.0, (-1.0, -2.0, -0.6), color=(0.98, 0.60, 0.35))
    add_light("LightRim",   120.0, ( 0.0, -2.5, -1.4), color=(0.90, 0.95, 1.00))

    scene.render.filepath = OUTPUT_BG
    bpy.ops.render.render(write_still=True)
    print(f"✓ Fondo abstracto de Astorga guardado en: {OUTPUT_BG}")

if __name__ == "__main__":
    create_acoustic_acoustic_background()
