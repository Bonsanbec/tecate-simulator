import bpy
import math
import os
import numpy as np
from mathutils import Vector, Euler, Matrix

PROJECT_ROOT = "/Users/hakkindavid/Documents/GitHub/tecate-simulator"
ASTORGA_BLEND = os.path.join(PROJECT_ROOT, "godot_project/assets/characters/citizens/astorga.blend")
VIOLIN_BLEND = os.path.join(PROJECT_ROOT, "godot_project/assets/props/violin.blend")
SCRATCH_DIR = os.path.join(PROJECT_ROOT, "scratch")
TEST_OUT = os.path.join(SCRATCH_DIR, "test_astorga_card_final.png")
BG_PATH = os.path.join(SCRATCH_DIR, "fondo_astorga.tiff")

bpy.ops.wm.open_mainfile(filepath=ASTORGA_BLEND)
scene = bpy.context.scene

arm = bpy.data.objects.get("Skeleton3D")
assert arm is not None

# Shade smooth
for o in bpy.data.objects:
    if o.type == 'MESH':
        for p in o.data.polygons:
            p.use_smooth = True

bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='POSE')

for pb in arm.pose.bones:
    pb.rotation_mode = 'XYZ'
    pb.rotation_euler = (0, 0, 0)

# Torso & Cabeza
arm.pose.bones['Chest'].rotation_euler = (math.radians(-2), math.radians(-6), math.radians(2))
arm.pose.bones['Head'].rotation_euler = (math.radians(-2), math.radians(8), math.radians(2))

# Brazo en VIEWER'S RIGHT (Hand.R, -X): Sostiene el VIOLÍN verticalmente junto al hombro / pecho alto
arm.pose.bones['UpperArm.R'].rotation_euler = (math.radians(-58), math.radians(-16), math.radians(-42))
arm.pose.bones['Forearm.R'].rotation_euler = (math.radians(116), math.radians(-22), math.radians(-12))
arm.pose.bones['Hand.R'].rotation_euler = (math.radians(12), math.radians(-16), math.radians(28))

# Brazo en VIEWER'S LEFT (Hand.L, +X): Sostiene el ARCO apuntando diagonal cruzado
arm.pose.bones['UpperArm.L'].rotation_euler = (math.radians(-16), math.radians(10), math.radians(18))
arm.pose.bones['Forearm.L'].rotation_euler = (math.radians(48), math.radians(-10), math.radians(12))
arm.pose.bones['Hand.L'].rotation_euler = (math.radians(20), math.radians(12), math.radians(-18))

bpy.ops.object.mode_set(mode='OBJECT')
bpy.context.view_layer.update()

hand_l_mat = arm.matrix_world @ arm.pose.bones['Hand.L'].matrix
hand_r_mat = arm.matrix_world @ arm.pose.bones['Hand.R'].matrix
hand_l_loc = hand_l_mat.to_translation()
hand_r_loc = hand_r_mat.to_translation()

print("Hand.L (viewer left) pos:", hand_l_loc)
print("Hand.R (viewer right) pos:", hand_r_loc)

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
                o.scale = (0.76, 0.76, 0.76)
                # Violín vertical con frente mirando a la cámara (+Y)
                # Scroll arriba, cuerpo abajo, apoyado en Hand.R
                o.rotation_euler = Euler((math.radians(-82), math.radians(172), math.radians(14)), 'XYZ')
                o.location = Vector((hand_r_loc.x + 0.010, hand_r_loc.y - 0.035, hand_r_loc.z - 0.290))
            elif o.name == "Violin_Bow":
                o.scale = (0.78, 0.78, 0.78)
                # El arco sostenido en Hand.L apuntando en diagonal ascendente hacia el pecho
                o.rotation_euler = Euler((math.radians(42), math.radians(-28), math.radians(-48)), 'XYZ')
                o.location = Vector((hand_l_loc.x - 0.010, hand_l_loc.y + 0.025, hand_l_loc.z - 0.010))

# Limpiar luces y cámaras
for o in list(scene.objects):
    if o.type in {'LIGHT', 'CAMERA'}:
        bpy.data.objects.remove(o, do_unlink=True)

cam_data = bpy.data.cameras.new("CardCam")
cam_data.lens = 72.0
cam_obj = bpy.data.objects.new("CardCam", cam_data)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj

cam_obj.location = Vector((0.0, 2.15, 1.28))
target = Vector((0.0, 0.0, 1.25))
cam_obj.rotation_euler = (target - cam_obj.location).to_track_quat('-Z', 'Y').to_euler()

def add_light(name, ltype, energy, loc, target_p, col, size=1.4):
    ld = bpy.data.lights.new(name, ltype)
    ld.energy = energy
    ld.color = col
    if hasattr(ld, 'size'): ld.size = size
    lo = bpy.data.objects.new(name, ld)
    lo.location = Vector(loc)
    lo.rotation_euler = (Vector(target_p) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    scene.collection.objects.link(lo)

head_p = (0.0, 0.0, 1.48)
chest_p = (0.0, 0.0, 1.22)

add_light("KeyLight", 'AREA', 140.0, (-0.8, 1.6, 1.6), chest_p, (1.0, 0.94, 0.88), size=1.4)
add_light("FillLight", 'AREA', 60.0, ( 1.0, 1.6, 1.4), head_p, (0.92, 0.95, 1.0), size=2.0)
add_light("RimLight",  'SPOT', 120.0, ( 0.1, -1.3, 1.9), head_p, (1.0, 0.97, 0.92))
add_light("ViolinLight", 'AREA', 65.0, (-0.45, 1.7, 1.30), (-0.15, 0, 1.25), (1.0, 0.95, 0.88), size=1.0)

scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 32
scene.render.resolution_x = 1024
scene.render.resolution_y = 1024
scene.render.film_transparent = True
scene.view_settings.exposure = -0.15

raw_fg = os.path.join(SCRATCH_DIR, "test_raw_fg.png")
scene.render.filepath = raw_fg
bpy.ops.render.render(write_still=True)
print("✓ Raw FG render guardado en:", raw_fg)

if os.path.exists(BG_PATH):
    img_fg = bpy.data.images.load(raw_fg)
    img_bg = bpy.data.images.load(BG_PATH)
    w, h = img_fg.size[0], img_fg.size[1]
    bg_w, bg_h = img_bg.size[0], img_bg.size[1]
    
    fg_px = np.empty(w * h * 4, dtype=np.float32)
    bg_px = np.empty(bg_w * bg_h * 4, dtype=np.float32)
    img_fg.pixels.foreach_get(fg_px)
    img_bg.pixels.foreach_get(bg_px)
    
    fg = fg_px.reshape((h, w, 4))
    bg_raw = bg_px.reshape((bg_h, bg_w, 4))
    
    side = min(bg_w, bg_h)
    x0 = (bg_w - side) // 2
    y0 = (bg_h - side) // 2
    cropped = bg_raw[y0:y0+side, x0:x0+side, :]
    y_idx = np.linspace(0, side - 1, h).astype(int)
    x_idx = np.linspace(0, side - 1, w).astype(int)
    bg = cropped[y_idx[:, None], x_idx[None, :], :]
    
    alpha = fg[:, :, 3:4]
    comp = np.empty_like(fg)
    comp[:, :, :3] = fg[:, :, :3] * alpha + bg[:, :, :3] * (1.0 - alpha)
    comp[:, :, 3] = 1.0
    
    out = bpy.data.images.new("FinalComp", width=w, height=h, alpha=False)
    out.pixels.foreach_set(comp.flatten())
    out.filepath_raw = TEST_OUT
    out.file_format = 'PNG'
    out.save()
    print("✓ Tarjeta final compuesta guardada en:", TEST_OUT)
