import bpy
import bmesh
import math
from mathutils import Vector, Matrix, Euler

# Load astorga.blend
bpy.ops.wm.open_mainfile(filepath="godot_project/assets/characters/citizens/astorga.blend")
head_obj = bpy.data.objects['Player_Head_Mesh']

# Let's inspect existing materials
for i, m in enumerate(head_obj.data.materials):
    print(f"Mat {i}: {m.name}")

