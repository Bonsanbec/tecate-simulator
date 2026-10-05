import bpy
import bmesh
import math
from mathutils import Vector, Matrix, Euler

# Load astorga.blend
bpy.ops.wm.open_mainfile(filepath="godot_project/assets/characters/citizens/astorga.blend")
scene = bpy.context.scene

head = bpy.data.objects['Player_Head_Mesh']

# Clear previous test lights/cams
for o in list(scene.objects):
    if o.type in {'LIGHT', 'CAMERA'}:
        bpy.data.objects.remove(o, do_unlink=True)

cam_data = bpy.data.cameras.new("FaceCam")
cam_data.lens = 85.0
cam = bpy.data.objects.new("FaceCam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam

cam.location = Vector((0.0, 1.30, 1.50))
target = Vector((0.0, 0.0, 1.50))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()

# Lights
ld1 = bpy.data.lights.new('Key', 'AREA')
ld1.energy = 55.0
ld1.size = 1.0
lo1 = bpy.data.objects.new('Key', ld1)
lo1.location = Vector((-0.6, 1.1, 1.65))
lo1.rotation_euler = (target - lo1.location).to_track_quat('-Z', 'Y').to_euler()
scene.collection.objects.link(lo1)

ld2 = bpy.data.lights.new('Fill', 'AREA')
ld2.energy = 25.0
ld2.size = 1.4
lo2 = bpy.data.objects.new('Fill', ld2)
lo2.location = Vector((0.6, 1.0, 1.45))
lo2.rotation_euler = (target - lo2.location).to_track_quat('-Z', 'Y').to_euler()
scene.collection.objects.link(lo2)

ld3 = bpy.data.lights.new('Rim', 'SPOT')
ld3.energy = 60.0
lo3 = bpy.data.objects.new('Rim', ld3)
lo3.location = Vector((0.1, -1.0, 1.85))
lo3.rotation_euler = (target - lo3.location).to_track_quat('-Z', 'Y').to_euler()
scene.collection.objects.link(lo3)

scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 24
scene.render.resolution_x = 512
scene.render.resolution_y = 512
scene.render.film_transparent = True
scene.view_settings.exposure = -0.15
scene.render.filepath = 'scratch/test_astorga_current_head.png'

bpy.ops.render.render(write_still=True)
print("Rendered current head to scratch/test_astorga_current_head.png")
