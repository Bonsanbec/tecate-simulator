import bpy
import os
import math
from mathutils import Vector, Euler

def render_axel_test():
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath("godot_project/assets/characters/citizens/axel.blend"))
    scene = bpy.context.scene
    arm = bpy.data.objects['Skeleton3D']
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='POSE')

    # Reset bones
    for pb in arm.pose.bones:
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (0, 0, 0)

    # Chest: rotated slightly to character's right (~12 degrees)
    arm.pose.bones['Chest'].rotation_euler = (0, math.radians(-12), 0)

    # Head: turned to his right (~24 deg), chin slightly up (-5 deg)
    arm.pose.bones['Head'].rotation_euler = (math.radians(-5), math.radians(-24), math.radians(3))

    # Right arm: UpperArm and Forearm using the solved angles
    uarm_r = arm.pose.bones['UpperArm.R']
    farm_r = arm.pose.bones['Forearm.R']
    hand_r = arm.pose.bones['Hand.R']

    uarm_r.rotation_euler = (math.radians(-20), math.radians(30), math.radians(-20))
    farm_r.rotation_euler = (math.radians(100), math.radians(20), math.radians(20))
    # Align hand naturally resting on vest
    hand_r.rotation_euler = (math.radians(-10), math.radians(10), math.radians(10))

    # Left arm: relaxed at side
    arm.pose.bones['UpperArm.L'].rotation_euler = (math.radians(8), 0, math.radians(8))

    # Camera & render
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 28
    scene.cycles.device = 'CPU'
    scene.render.resolution_x = 768
    scene.render.resolution_y = 768
    scene.render.film_transparent = True

    cam_data = bpy.data.cameras.new("IconCamera")
    cam_data.lens = 62.0
    cam_obj = bpy.data.objects.new("IconCamera", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    # Framing: head to belt (bust portrait icon)
    cam_obj.location = Vector((0.18, 1.80, 1.25))
    target = Vector((0.0, 0.0, 1.22))
    direction = target - cam_obj.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam_obj.rotation_euler = rot_quat.to_euler()

    # Lights
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
    add_light('KeyLight', 'AREA', 180.0, (-0.8, 1.5, 1.8), (1.0, 0.96, 0.92), 1.5)
    add_light('FillLight', 'AREA', 80.0, (1.1, 1.4, 1.3), (0.92, 0.96, 1.0), 2.0)
    add_light('RimLight', 'SPOT', 130.0, (0.0, -1.2, 1.9), (1.0, 1.0, 1.0))
    add_light('FrontLight', 'AREA', 45.0, (0.0, 1.8, 1.3), (1.0, 0.98, 0.95), 1.0)

    out_path = os.path.abspath("scratch/test_axel_fk_render.png")
    scene.render.filepath = out_path
    bpy.ops.render.render(write_still=True)
    print("Rendered:", out_path)

if __name__ == "__main__":
    render_axel_test()
