import bpy
import os
import math
from mathutils import Vector, Euler

def test_eli_pose():
    blend_path = os.path.abspath("godot_project/assets/characters/citizens/eli.blend")
    bpy.ops.wm.open_mainfile(filepath=blend_path)
    scene = bpy.context.scene

    arm = bpy.data.objects.get("Skeleton3D")
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='POSE')

    # Reset bones
    for pb in arm.pose.bones:
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (0, 0, 0)

    # In eli.png:
    # 1. Torso slightly angled (Chest turns ~10 degrees to his left)
    chest = arm.pose.bones.get("Chest")
    if chest:
        chest.rotation_euler = (0, math.radians(-10), 0)

    # 2. Head: facing camera directly, tilted slightly (~6 deg) to his right shoulder
    head = arm.pose.bones.get("Head")
    if head:
        head.rotation_euler = (0, math.radians(10), math.radians(6))

    # 3. Right arm pointing towards the right (screen right):
    uarm_r = arm.pose.bones.get("UpperArm.R")
    farm_r = arm.pose.bones.get("Forearm.R")
    hand_r = arm.pose.bones.get("Hand.R")

    if uarm_r:
        uarm_r.rotation_euler = (0, math.radians(30), math.radians(-30))
    if farm_r:
        farm_r.rotation_euler = (math.radians(100), math.radians(15), math.radians(15))
    if hand_r:
        # Orient hand so the fingers point towards screen-right
        hand_r.rotation_euler = (math.radians(-10), math.radians(15), math.radians(10))

    # Left arm relaxed at side
    uarm_l = arm.pose.bones.get("UpperArm.L")
    if uarm_l:
        uarm_l.rotation_euler = (math.radians(6), 0, math.radians(6))

    # Render settings
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 28
    scene.cycles.device = 'CPU'
    scene.render.resolution_x = 768
    scene.render.resolution_y = 768
    scene.render.film_transparent = True

    # Camera setup
    cam_data = bpy.data.cameras.new("IconCamera")
    cam_data.lens = 60.0
    cam_obj = bpy.data.objects.new("IconCamera", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    # Position camera for portrait / icon view (head to belt)
    cam_obj.location = Vector((0.0, 1.85, 1.25))
    target = Vector((0.0, 0.0, 1.22))
    direction = target - cam_obj.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam_obj.rotation_euler = rot_quat.to_euler()

    # Studio Lighting
    for l in [o for o in scene.objects if o.type == 'LIGHT']:
        bpy.data.objects.remove(l, do_unlink=True)

    def add_light(name, ltype, energy, loc, color=(1,1,1), size=1.0):
        ld = bpy.data.lights.new(name, ltype)
        ld.energy = energy
        ld.color = color
        if hasattr(ld, 'size'): ld.size = size
        lo = bpy.data.objects.new(name, ld)
        lo.location = Vector(loc)
        scene.collection.objects.link(lo)
        return lo

    add_light("KeyLight", 'AREA', 200.0, (0.7, 1.5, 1.7), color=(1.0, 0.97, 0.94), size=1.5)
    add_light("FillLight", 'AREA', 90.0, (-1.0, 1.4, 1.3), color=(0.93, 0.97, 1.0), size=2.0)
    add_light("RimLight", 'SPOT', 140.0, (0.0, -1.3, 1.9), color=(1.0, 1.0, 1.0))
    add_light("FrontLight", 'AREA', 50.0, (0.0, 1.8, 1.3), color=(1.0, 0.98, 0.95), size=1.0)

    out_path = os.path.abspath("scratch/test_eli_pointing_render.png")
    scene.render.filepath = out_path
    bpy.ops.render.render(write_still=True)
    print("Rendered:", out_path)

if __name__ == "__main__":
    test_eli_pose()
