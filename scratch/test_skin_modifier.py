"""
Prueba del modificador Skin + Subsurf de Blender para generar un cuerpo humanoide continuo,
orgánico, sin fisuras en hombros, codos ni cintura.
"""
import bpy
import math
import os
from mathutils import Vector

def clean_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh, do_unlink=True)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat, do_unlink=True)

clean_scene()

mesh = bpy.data.meshes.new("Skin_Body_Mesh")
obj = bpy.data.objects.new("Skin_Body_Obj", mesh)
bpy.context.scene.collection.objects.link(obj)

# Definir la estructura de vértices del esqueleto del cuerpo humanoide
# (x, y, z, rx, ry)
nodes = [
    # 0: Pelvis centro
    (0.0, 0.0, 0.98, 0.16, 0.13),
    # 1: Cintura / Ombligo
    (0.0, 0.0, 1.10, 0.15, 0.12),
    # 2: Pecho bajo / Esternón
    (0.0, 0.0, 1.25, 0.17, 0.13),
    # 3: Pecho alto
    (0.0, 0.0, 1.40, 0.19, 0.14),
    # 4: Base del cuello
    (0.0, 0.0, 1.48, 0.052, 0.052),
    # 5: Mitad del cuello
    (0.0, 0.0, 1.54, 0.048, 0.048),
    # 6: Barbilla / Mandíbula
    (0.0, 0.015, 1.58, 0.065, 0.075),
    # 7: Centro de la cabeza / Ojos
    (0.0, 0.0, 1.66, 0.075, 0.080),
    # 8: Coronilla
    (0.0, -0.01, 1.76, 0.065, 0.070),

    # Hombros y brazos Izquierda (-X)
    # 9: Clavícula izq
    (-0.08, 0.0, 1.45, 0.08, 0.08),
    # 10: Hombro izq
    (-0.19, 0.0, 1.40, 0.075, 0.075),
    # 11: Codo izq
    (-0.29, 0.0, 1.16, 0.062, 0.062),
    # 12: Muñeca izq
    (-0.37, 0.0, 0.92, 0.045, 0.040),
    # 13: Mano izq
    (-0.40, 0.0, 0.82, 0.035, 0.020),

    # Hombros y brazos Derecha (+X)
    # 14: Clavícula der
    (0.08, 0.0, 1.45, 0.08, 0.08),
    # 15: Hombro der
    (0.19, 0.0, 1.40, 0.075, 0.075),
    # 16: Codo der
    (0.29, 0.0, 1.16, 0.062, 0.062),
    # 17: Muñeca der
    (0.37, 0.0, 0.92, 0.045, 0.040),
    # 18: Mano der
    (0.40, 0.0, 0.82, 0.035, 0.020),

    # Piernas Izquierda (-X)
    # 19: Cadera izq
    (-0.10, 0.0, 0.94, 0.10, 0.10),
    # 20: Muslo medio izq
    (-0.11, 0.0, 0.72, 0.095, 0.095),
    # 21: Rodilla izq
    (-0.11, 0.0, 0.50, 0.080, 0.080),
    # 22: Pantorrilla izq
    (-0.11, 0.0, 0.30, 0.072, 0.072),
    # 23: Tobillo izq
    (-0.11, 0.0, 0.12, 0.055, 0.055),
    # 24: Pie izq
    (-0.11, 0.08, 0.04, 0.060, 0.12),

    # Piernas Derecha (+X)
    # 25: Cadera der
    (0.10, 0.0, 0.94, 0.10, 0.10),
    # 26: Muslo medio der
    (0.11, 0.0, 0.72, 0.095, 0.095),
    # 27: Rodilla der
    (0.11, 0.0, 0.50, 0.080, 0.080),
    # 28: Pantorrilla der
    (0.11, 0.0, 0.30, 0.072, 0.072),
    # 29: Tobillo der
    (0.11, 0.0, 0.12, 0.055, 0.055),
    # 30: Pie der
    (0.11, 0.08, 0.04, 0.060, 0.12),
]

edges = [
    # Columna vertebral y cabeza
    (0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 8),
    # Brazo izquierdo
    (3, 9), (9, 10), (10, 11), (11, 12), (12, 13),
    # Brazo derecho
    (3, 14), (14, 15), (15, 16), (16, 17), (17, 18),
    # Pierna izquierda
    (0, 19), (19, 20), (20, 21), (21, 22), (22, 23), (23, 24),
    # Pierna derecha
    (0, 25), (25, 26), (26, 27), (27, 28), (28, 29), (29, 30),
]

# Crear geometría base
verts = [Vector((n[0], n[1], n[2])) for n in nodes]
mesh.from_pydata(verts, edges, [])
mesh.update()

# Configurar Skin Modifier
bpy.context.view_layer.objects.active = obj
mod_skin = obj.modifiers.new(name="Skin", type='SKIN')

# Asignar radios del modificador Skin a cada vértice
# En Blender, el radio de piel se almacena en mesh.skin_vertices[0].data[i].radius
skin_data = mesh.skin_vertices[0].data
for i, n in enumerate(nodes):
    skin_data[i].radius = (n[3], n[4])

# Añadir Subdivision Surface para suavidad orgánica
mod_subsurf = obj.modifiers.new(name="Subsurf", type='SUBSURF')
mod_subsurf.levels = 2
mod_subsurf.render_levels = 2

# Render de prueba
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 24
scene.cycles.device = 'CPU'
scene.render.resolution_x = 720
scene.render.resolution_y = 1280

cam_data = bpy.data.cameras.new("Cam")
cam_data.lens = 55.0
cam = bpy.data.objects.new("Cam", cam_data)
cam.location = Vector((0.2, 2.8, 1.1))
cam.rotation_euler = (math.radians(88.0), 0.0, math.radians(175.0))
scene.collection.objects.link(cam)
scene.camera = cam

light_data = bpy.data.lights.new("Key", type='AREA')
light_data.energy = 50.0
light_data.size = 1.2
light = bpy.data.objects.new("Key", light_data)
light.location = Vector((-1.0, 2.0, 2.0))
scene.collection.objects.link(light)

scene.render.filepath = os.path.abspath("scratch/test_skin_render.png")
bpy.ops.render.render(write_still=True)
print("Rendered scratch/test_skin_render.png")
