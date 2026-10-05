import bpy
import bmesh
import math
from mathutils import Vector, Matrix, Euler

bpy.ops.wm.open_mainfile(filepath="godot_project/assets/characters/citizens/astorga.blend")
scene = bpy.context.scene
head_obj = bpy.data.objects['Player_Head_Mesh']

# Clear previous lights and cameras
for o in list(scene.objects):
    if o.type in {'LIGHT', 'CAMERA'}:
        bpy.data.objects.remove(o, do_unlink=True)

# Build a clean head mesh without the old hair
# We can read the head_obj mesh and rebuild hair
bm = bmesh.new()
bm.from_mesh(head_obj.data)

# Remove old hair faces (material_index == 2 except skull faces)
# Let's inspect vertices with z > 1.35
verts_to_delete = []
for v in bm.verts:
    # If vert belongs to the hair locks we added (not part of the head rings)
    # The head rings were built up to top_vert. Hair locks had material 2 and were added later.
    pass

bm.free()
print("Test script loaded blend successfully")
