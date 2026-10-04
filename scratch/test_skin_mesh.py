"""
Test de malla anatómica continua con Skin Modifier + Subsurf + Materiales y Estudio
"""
import bpy
import bmesh
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

mesh = bpy.data.meshes.new("Human_Skin_Graph")
obj = bpy.data.objects.new("Human_Body", mesh)
bpy.context.scene.collection.objects.link(obj)

nodes = [
    # Tronco
    (0.00,  0.00, 0.82, 0.130, 0.100), # 0: Crotch / Pelvis base
    (0.00,  0.00, 0.94, 0.145, 0.110), # 1: Pelvis / Cadera
    (0.00,  0.00, 1.05, 0.135, 0.100), # 2: Cintura / Ombligo
    (0.00,  0.00, 1.18, 0.155, 0.115), # 3: Esternón bajo
    (0.00,  0.00, 1.28, 0.175, 0.125), # 4: Pecho medio
    (0.00,  0.00, 1.37, 0.150, 0.110), # 5: Pecho alto / Clavículas
    (0.00,  0.00, 1.42, 0.052, 0.052), # 6: Base del cuello

    # Brazo Izquierdo (-X)
    (-0.06, 0.00, 1.36, 0.070, 0.070), # 7: Clavícula L
    (-0.18, 0.00, 1.34, 0.065, 0.065), # 8: Hombro L
    (-0.27, 0.00, 1.14, 0.052, 0.052), # 9: Codo L
    (-0.35, 0.00, 0.94, 0.038, 0.035), # 10: Muñeca L

    # Brazo Derecho (+X)
    ( 0.06, 0.00, 1.36, 0.070, 0.070), # 11: Clavícula R
    ( 0.18, 0.00, 1.34, 0.065, 0.065), # 12: Hombro R
    ( 0.27, 0.00, 1.14, 0.052, 0.052), # 13: Codo R
    ( 0.35, 0.00, 0.94, 0.038, 0.035), # 14: Muñeca R

    # Pierna Izquierda (-X)
    (-0.09, 0.00, 0.82, 0.090, 0.090), # 15: Cadera / Ingle L
    (-0.095,0.00, 0.65, 0.082, 0.082), # 16: Muslo L
    (-0.10, 0.00, 0.48, 0.070, 0.070), # 17: Rodilla L
    (-0.10, 0.00, 0.30, 0.062, 0.062), # 18: Pantorrilla L
    (-0.10, 0.00, 0.12, 0.050, 0.050), # 19: Tobillo L
    (-0.10, 0.05, 0.03, 0.052, 0.105), # 20: Pie L

    # Pierna Derecha (+X)
    ( 0.09, 0.00, 0.82, 0.090, 0.090), # 21: Cadera / Ingle R
    ( 0.095,0.00, 0.65, 0.082, 0.082), # 22: Muslo R
    ( 0.10, 0.00, 0.48, 0.070, 0.070), # 23: Rodilla R
    ( 0.10, 0.00, 0.30, 0.062, 0.062), # 24: Pantorrilla R
    ( 0.10, 0.00, 0.12, 0.050, 0.050), # 25: Tobillo R
    ( 0.10, 0.05, 0.03, 0.052, 0.105), # 26: Pie R
]

edges = [
    (0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6),
    (5, 7), (7, 8), (8, 9), (9, 10),
    (5, 11), (11, 12), (12, 13), (13, 14),
    (0, 15), (15, 16), (16, 17), (17, 18), (18, 19), (19, 20),
    (0, 21), (21, 22), (22, 23), (23, 24), (24, 25), (25, 26),
]

verts = [Vector((n[0], n[1], n[2])) for n in nodes]
mesh.from_pydata(verts, edges, [])
mesh.update()

bpy.context.view_layer.objects.active = obj
mod_skin = obj.modifiers.new(name="Skin", type='SKIN')
skin_data = mesh.skin_vertices[0].data
for i, n in enumerate(nodes):
    skin_data[i].radius = (n[3], n[4])

bpy.ops.object.modifier_apply(modifier="Skin")

mod_sub = obj.modifiers.new(name="Subsurf", type='SUBSURF')
mod_sub.levels = 2
bpy.ops.object.modifier_apply(modifier="Subsurf")

for p in mesh.polygons:
    p.use_smooth = True

# Material de prueba
mat = bpy.data.materials.new("Mat_Test")
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")
bsdf.inputs['Base Color'].default_value = (0.7, 0.72, 0.75, 1.0)
bsdf.inputs['Roughness'].default_value = 0.5
obj.data.materials.append(mat)

# Configurar Iluminación de Estudio y Cámara
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 32
scene.cycles.device = 'CPU'
scene.render.resolution_x = 720
scene.render.resolution_y = 1280

cam_data = bpy.data.cameras.new("Cam")
cam_data.lens = 55.0
cam_obj = bpy.data.objects.new("Cam", cam_data)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj
cam_obj.location = Vector((0.0, 2.2, 0.9))
cam_obj.rotation_euler = (math.radians(90.0), 0.0, math.radians(180.0))

# 3-Point Lighting frontal
key = bpy.data.lights.new("Key", type='AREA')
key.energy = 120.0
key.size = 1.5
key_obj = bpy.data.objects.new("Key", key)
key_obj.location = Vector((-0.8, 1.8, 1.5))
key_obj.rotation_euler = (math.radians(55.0), 0.0, math.radians(-145.0))
scene.collection.objects.link(key_obj)

fill = bpy.data.lights.new("Fill", type='AREA')
fill.energy = 60.0
fill.size = 2.0
fill_obj = bpy.data.objects.new("Fill", fill)
fill_obj.location = Vector((0.9, 1.7, 1.2))
scene.collection.objects.link(fill_obj)

rim = bpy.data.lights.new("Rim", type='SPOT')
rim.energy = 80.0
rim_obj = bpy.data.objects.new("Rim", rim)
rim_obj.location = Vector((0.0, -1.5, 1.8))
rim_obj.rotation_euler = (math.radians(-50.0), 0.0, 0.0)
scene.collection.objects.link(rim_obj)

scene.render.filepath = os.path.abspath("scratch/test_skin_render.png")
bpy.ops.render.render(write_still=True)
print("Render guardado en scratch/test_skin_render.png")
