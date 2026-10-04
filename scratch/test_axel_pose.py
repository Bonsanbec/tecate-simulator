import bpy
import os
import math
from mathutils import Vector, Euler

def test_axel_pose():
    blend_path = os.path.abspath("godot_project/assets/characters/citizens/axel.blend")
    bpy.ops.wm.open_mainfile(filepath=blend_path)
    scene = bpy.context.scene

    arm = bpy.data.objects.get("Skeleton3D")
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='POSE')

    # Switch all bones to XYZ Euler
    for pb in arm.pose.bones:
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (0, 0, 0)

    # Axel reference pose (axel2.png):
    # 1. Torso slightly angled (Chest and Spine slight rotation)
    chest = arm.pose.bones.get("Chest")
    if chest:
        chest.rotation_euler = (0, math.radians(-15), 0) # Chest turns slightly to his right (Y is up)

    # 2. Head looking towards his right with slight upward chin tilt
    head = arm.pose.bones.get("Head")
    if head:
        # Y is up (yaw), X is pitch (chin up/down), Z is roll
        head.rotation_euler = (math.radians(-6), math.radians(-26), math.radians(4))

    # 3. Right arm bent across chest / holding vest using IK
    target_empty = bpy.data.objects.new("IK_Target_R", None)
    scene.collection.objects.link(target_empty)
    # Target right at lower chest / vest lapel: slightly in front (+Y), slight right of center (-X), Z=1.06
    target_empty.location = Vector((-0.06, 0.14, 1.06))

    pole_empty = bpy.data.objects.new("IK_Pole_R", None)
    scene.collection.objects.link(pole_empty)
    # Pole target to ensure elbow stays down and back/side
    pole_empty.location = Vector((-0.35, -0.15, 1.10))

    hand_r = arm.pose.bones.get("Hand.R")
    ik = hand_r.constraints.new('IK')
    ik.target = target_empty
    ik.pole_target = pole_empty
    ik.pole_angle = math.radians(90)
    ik.chain_count = 2

    # Hand orientation: palm facing chest / fingers resting naturally
    hand_r.rotation_mode = 'XYZ'
    hand_r.rotation_euler = (math.radians(20), math.radians(40), math.radians(-30))

    # Left arm relaxed at side
    uarm_l = arm.pose.bones.get("UpperArm.L")
    if uarm_l:
        uarm_l.rotation_euler = (math.radians(5), 0, math.radians(5))

    # Render settings
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 32
    scene.cycles.device = 'CPU'
    scene.render.resolution_x = 768
    scene.render.resolution_y = 768
    scene.render.film_transparent = True

    # Camera framing
    cam_data = bpy.data.cameras.new("IconCamera")
    cam_data.lens = 60.0
    cam_obj = bpy.data.objects.new("IconCamera", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    # Position camera for portrait / icon view (head to waist)
    cam_obj.location = Vector((0.15, 1.85, 1.28))
    # Look at chest/neck
    target = Vector((0.0, 0.0, 1.25))
    direction = target - cam_obj.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam_obj.rotation_euler = rot_quat.to_euler()

    # Lighting
    for light in [o for o in scene.objects if o.type == 'LIGHT']:
        bpy.data.objects.remove(light, do_unlink=True)

    def add_light(name, ltype, energy, loc, color=(1.0, 1.0, 1.0), size=1.0):
        ld = bpy.data.lights.new(name, ltype)
        ld.energy = energy
        ld.color = color
        if hasattr(ld, 'size'):
            ld.size = size
        lo = bpy.data.objects.new(name, ld)
        lo.location = Vector(loc)
        scene.collection.objects.link(lo)
        return lo

    add_light("KeyLight", 'AREA', 180.0, (-0.8, 1.5, 1.8), color=(1.0, 0.96, 0.92), size=1.5)
    add_light("FillLight", 'AREA', 80.0, (1.1, 1.4, 1.3), color=(0.92, 0.96, 1.0), size=2.0)
    add_light("RimLight", 'SPOT', 120.0, (0.0, -1.2, 1.9), color=(1.0, 1.0, 1.0))
    add_light("FrontLight", 'AREA', 40.0, (0.0, 1.8, 1.3), color=(1.0, 0.98, 0.95), size=1.0)

    out_path = os.path.abspath("scratch/test_axel_pose_render.png")
    scene.render.filepath = out_path
    bpy.ops.render.render(write_still=True)
    print("Rendered:", out_path)

if __name__ == "__main__":
    test_axel_pose()
