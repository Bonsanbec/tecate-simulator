"""
Prototipo de Cabeza Anatómica basada en Quad-Sphere / Box Modeling en Blender
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

clean_scene()

# Crear un cubo y subdividirlo para obtener una topología cuadriculada perfecta (Quad-Sphere)
mesh = bpy.data.meshes.new("Head_Quad_Mesh")
obj = bpy.data.objects.new("Axel_Head", mesh)
bpy.context.scene.collection.objects.link(obj)

bm = bmesh.new()
# Crear un cubo base de 16x16x18 cm centrado en la cabeza
bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Scale(1.0, 4))
bmesh.ops.subdivide_edges(bm, edges=bm.edges, cuts=3, use_grid_fill=True)

# Normalizar y esculpir las proporciones de la cabeza de Axel (Z: 1.44 a 1.66)
# Dimensiones: ancho X = 0.15 m, profundidad Y = 0.18 m, altura Z = 0.22 m
center_head = Vector((0.0, 0.0, 1.55))
scale_box = Vector((0.075, 0.090, 0.110))

for v in bm.verts:
    # Coordenadas normalizadas [-1, 1]
    nx = v.co.x * 2.0
    ny = v.co.y * 2.0
    nz = v.co.z * 2.0
    
    # Proyección a elipsoide suave
    length = math.sqrt(nx**2 + ny**2 + nz**2)
    if length > 0.001:
        dir_v = Vector((nx/length, ny/length, nz/length))
    else:
        dir_v = Vector((0, 0, 0))
        
    px = dir_v.x * scale_box.x
    py = dir_v.y * scale_box.y
    pz = center_head.z + dir_v.z * scale_box.z
    
    # Esculpido anatómico según posición de los rasgos:
    # 1. Mandíbula y barbilla (Z < 1.48, Y > -0.02)
    if pz < 1.50 and py > -0.02:
        # Aplanar lados de la mandíbula
        px *= 0.82
        # Proyectar barbilla cuadrada hacia adelante
        if pz < 1.46 and py > 0.02:
            py += 0.018 * (1.0 - min(1.0, (px / 0.025)**2))
            pz -= 0.008
            
    # 2. Nariz (Z: 1.50 a 1.54, Y > 0.05, abs(X) < 0.025)
    if 1.49 < pz < 1.55 and py > 0.04 and abs(px) < 0.025:
        # Extrusión nasal
        t_nose = (pz - 1.49) / 0.06
        w_n = 0.010 + (1.0 - t_nose) * 0.008
        if abs(px) < w_n:
            n_proj = 0.022 * math.sin(t_nose * math.pi)
            py += n_proj * (1.0 - abs(px) / w_n)
            
    # 3. Labios (Z: 1.465 a 1.490, Y > 0.05, abs(X) < 0.030)
    if 1.465 < pz < 1.490 and py > 0.04 and abs(px) < 0.030:
        w_l = 0.024
        if abs(px) < w_l:
            l_proj = 0.008 * math.sin(((pz - 1.465) / 0.025) * math.pi)
            py += l_proj * (1.0 - abs(px) / w_l)
            
    # 4. Cuencas orbitales para los ojos (Z: 1.53 a 1.56, 0.018 < abs(X) < 0.050, Y > 0.03)
    if 1.525 < pz < 1.560 and py > 0.03 and 0.018 < abs(px) < 0.050:
        dist_eye = math.sqrt(((abs(px) - 0.033) / 0.015)**2 + ((pz - 1.542) / 0.014)**2)
        if dist_eye < 1.0:
            py -= 0.016 * (1.0 - dist_eye)**2
            
    # 5. Pómulos altos (Z: 1.52 a 1.54, 0.035 < abs(X) < 0.065, Y > 0.02)
    if 1.515 < pz < 1.545 and py > 0.02 and 0.035 < abs(px) < 0.065:
        py += 0.007 * (1.0 - abs(abs(px) - 0.050) / 0.015)
        
    # 6. Aplanamiento de las sienes (Z > 1.54, abs(X) > 0.055)
    if pz > 1.54 and abs(px) > 0.055:
        px *= 0.94
        
    v.co = Vector((px, py, pz))

# Extruir el cuello hacia abajo desde la base del cráneo (Z < 1.46, Y < 0.02)
# Seleccionar caras de la base inferior
neck_faces = [f for f in bm.faces if f.calc_center_median().z < 1.46 and f.calc_center_median().y < 0.02]
if neck_faces:
    res_neck = bmesh.ops.extrude_face_region(bm, geom=neck_faces)
    neck_verts = [v for v in res_neck['geom'] if isinstance(v, bmesh.types.BMVert)]
    for v in neck_verts:
        v.co.z -= 0.065 # Extrusión hacia el collar
        v.co.x *= 0.85
        v.co.y = (v.co.y - 0.010) * 0.85

bm.verts.index_update()
bm.to_mesh(mesh)
bm.free()

for poly in mesh.polygons:
    poly.use_smooth = True

# Subsurf Nivel 2 para una superficie orgánica continua
bpy.context.view_layer.objects.active = obj
mod_sub = obj.modifiers.new(name="Subsurf", type='SUBSURF')
mod_sub.levels = 2
bpy.ops.object.modifier_apply(modifier="Subsurf")

# Material piel cálida
mat_skin = bpy.data.materials.new("Mat_Skin")
mat_skin.use_nodes = True
bsdf = mat_skin.node_tree.nodes.get("Principled BSDF")
bsdf.inputs['Base Color'].default_value = (0.80, 0.58, 0.46, 1.0)
bsdf.inputs['Roughness'].default_value = 0.45
if 'Subsurface Weight' in bsdf.inputs:
    bsdf.inputs['Subsurface Weight'].default_value = 0.35
elif 'Subsurface' in bsdf.inputs:
    bsdf.inputs['Subsurface'].default_value = 0.35
obj.data.materials.append(mat_skin)

# Render de prueba close-up
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 32
scene.cycles.device = 'CPU'
scene.render.resolution_x = 720
scene.render.resolution_y = 1080

cam_data = bpy.data.cameras.new("Cam")
cam_data.lens = 70.0
cam_obj = bpy.data.objects.new("Cam", cam_data)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj
cam_obj.location = Vector((0.15, 0.95, 1.53))
cam_obj.rotation_euler = (math.radians(88.0), 0.0, math.radians(170.0))

key = bpy.data.lights.new("Key", type='AREA')
key.energy = 70.0
key.size = 1.0
key_obj = bpy.data.objects.new("Key", key)
key_obj.location = Vector((-0.5, 0.8, 1.7))
key_obj.rotation_euler = (math.radians(45.0), 0.0, math.radians(-150.0))
scene.collection.objects.link(key_obj)

fill = bpy.data.lights.new("Fill", type='AREA')
fill.energy = 30.0
fill_obj = bpy.data.objects.new("Fill", fill)
fill_obj.location = Vector((0.6, 0.8, 1.5))
scene.collection.objects.link(fill_obj)

rim = bpy.data.lights.new("Rim", type='SPOT')
rim.energy = 50.0
rim_obj = bpy.data.objects.new("Rim", rim)
rim_obj.location = Vector((0.0, -0.8, 1.8))
rim_obj.rotation_euler = (math.radians(-50.0), 0.0, 0.0)
scene.collection.objects.link(rim_obj)

render_path = os.path.abspath("scratch/test_quad_head.png")
scene.render.filepath = render_path
bpy.ops.render.render(write_still=True)
print(f"Render guardado en {render_path}")
