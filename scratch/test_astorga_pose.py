import bpy
import math
import os
from mathutils import Vector, Euler, Matrix

PROJECT_ROOT = "/Users/hakkindavid/Documents/GitHub/tecate-simulator"
ASTORGA_BLEND = os.path.join(PROJECT_ROOT, "godot_project/assets/characters/citizens/astorga.blend")
VIOLIN_BLEND = os.path.join(PROJECT_ROOT, "godot_project/assets/props/violin.blend")
SCRATCH_DIR = os.path.join(PROJECT_ROOT, "scratch")
TEST_OUT = os.path.join(SCRATCH_DIR, "test_astorga_card_pose.png")

bpy.ops.wm.open_mainfile(filepath=ASTORGA_BLEND)
scene = bpy.context.scene

arm = bpy.data.objects.get("Skeleton3D")
assert arm is not None

# Activar shade smooth explícito en las mallas
for o in bpy.data.objects:
    if o.type == 'MESH':
        for p in o.data.polygons:
            p.use_smooth = True

bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='POSE')

for pb in arm.pose.bones:
    pb.rotation_mode = 'XYZ'
    pb.rotation_euler = (0, 0, 0)

# 1. Torso y Cabeza: Porte formal erguido con leve giro 3/4
arm.pose.bones['Chest'].rotation_euler = (math.radians(-2), math.radians(-5), math.radians(2))
arm.pose.bones['Head'].rotation_euler = (math.radians(-1), math.radians(7), math.radians(2))

# 2. Brazo izquierdo alzado sosteniendo el mástil del violín en posición vertical junto al hombro
arm.pose.bones['UpperArm.L'].rotation_euler = (math.radians(-22), math.radians(-28), math.radians(42))
arm.pose.bones['Forearm.L'].rotation_euler = (math.radians(116), math.radians(-14), math.radians(16))
arm.pose.bones['Hand.L'].rotation_euler = (math.radians(24), math.radians(-10), math.radians(-42))

# 3. Brazo derecho relajado con el arco apuntando en diagonal descendente
arm.pose.bones['UpperArm.R'].rotation_euler = (math.radians(-14), math.radians(6), math.radians(-12))
arm.pose.bones['Forearm.R'].rotation_euler = (math.radians(38), math.radians(10), math.radians(-6))
arm.pose.bones['Hand.R'].rotation_euler = (math.radians(20), math.radians(-15), math.radians(25))

bpy.ops.object.mode_set(mode='OBJECT')
bpy.context.view_layer.update()

# Posiciones globales de las manos
hand_l_mat = arm.matrix_world @ arm.pose.bones['Hand.L'].matrix
hand_r_mat = arm.matrix_world @ arm.pose.bones['Hand.R'].matrix

hand_l_loc = hand_l_mat.to_translation()
hand_r_loc = hand_r_mat.to_translation()
print("Hand.L global pos:", hand_l_loc)
print("Hand.R global pos:", hand_r_loc)

# Cargar Violín y Arco
if os.path.exists(VIOLIN_BLEND):
    with bpy.data.libraries.load(VIOLIN_BLEND, link=False) as (data_from, data_to):
        data_to.objects = [o for o in data_from.objects if o in ("Violin_Prop", "Violin_Bow")]
    for o in data_to.objects:
        if o:
            scene.collection.objects.link(o)
            for p in o.data.polygons:
                p.use_smooth = True
            if o.name == "Violin_Prop":
                o.scale = (0.78, 0.78, 0.78)
                # Violín vertical con el frente (puente y cuerdas) mirando a la cámara (+Y)
                # X = -82 deg (mástil arriba), Y = 175 deg (frente hacia cámara), Z = -15 deg (inclinación hacia hombro L)
                o.rotation_euler = Euler((math.radians(-82), math.radians(172), math.radians(-14)), 'XYZ')
                # Alinear de modo que el mástil pase por Hand.L
                o.location = Vector((hand_l_loc.x + 0.015, hand_l_loc.y - 0.025, hand_l_loc.z - 0.325))
            elif o.name == "Violin_Bow":
                o.scale = (0.80, 0.80, 0.80)
                # El arco sostenido en mano derecha apuntando diagonal abajo / frente
                o.rotation_euler = Euler((math.radians(-42), math.radians(32), math.radians(-68)), 'XYZ')
                o.location = Vector((hand_r_loc.x + 0.015, hand_r_loc.y + 0.020, hand_r_loc.z - 0.015))

# Limpiar luces y cámaras
for o in list(scene.objects):
    if o.type in {'LIGHT', 'CAMERA'}:
        bpy.data.objects.remove(o, do_unlink=True)

# Cámara retrato
cam_data = bpy.data.cameras.new("TestCam")
cam_data.lens = 72.0
cam_obj = bpy.data.objects.new("TestCam", cam_data)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj

cam_obj.location = Vector((0.0, 2.12, 1.28))
target = Vector((0.0, 0.0, 1.25))
cam_obj.rotation_euler = (target - cam_obj.location).to_track_quat('-Z', 'Y').to_euler()

# Iluminación de concierto calibrada
def add_light(name, ltype, energy, loc, target_p, col, size=1.4):
    ld = bpy.data.lights.new(name, ltype)
    ld.energy = energy
    ld.color = col
    if hasattr(ld, 'size'): ld.size = size
    lo = bpy.data.objects.new(name, ld)
    lo.location = Vector(loc)
    lo.rotation_euler = (Vector(target_p) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    scene.collection.objects.link(lo)

add_light("KeyLight", 'AREA', 150.0, (-0.8, 1.8, 1.6), (0, 0, 1.25), (1.0, 0.95, 0.90), size=1.6)
add_light("FillLight", 'AREA', 80.0, ( 1.0, 1.6, 1.4), (0, 0, 1.30), (0.94, 0.96, 1.0), size=2.0)
add_light("RimLight",  'SPOT', 130.0, ( 0.1, -1.3, 1.9), (0, 0, 1.40), (1.0, 0.96, 0.92))
add_light("ViolinLight", 'AREA', 70.0, (0.35, 1.7, 1.30), (0.18, 0, 1.30), (1.0, 0.95, 0.90), size=1.0)

# Render de prueba
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 32
scene.render.resolution_x = 800
scene.render.resolution_y = 1000
scene.render.film_transparent = True
scene.render.filepath = TEST_OUT

bpy.ops.render.render(write_still=True)
print("✓ Render de prueba guardado en:", TEST_OUT)
