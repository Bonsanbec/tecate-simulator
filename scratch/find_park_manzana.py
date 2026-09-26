import bpy
import bmesh
from mathutils import Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath='godot_project/assets/manzanas_baked.glb')

obj = bpy.data.objects['UrbanManzanas']
mesh = obj.data

# Kiosko in Godot is: X = -6.6844, Y_elev = 400.0132, Z = 2.6878
# In Blender imported from glTF:
# Blender X = Godot X = -6.6844
# Blender Z = Godot Y = 400.0132
# Blender Y = -Godot Z = -2.6878
kiosko_blender = Vector((-6.6844, -2.6878, 400.0132))

print(f"Finding polygons of UrbanManzanas near Kiosko: {kiosko_blender}")

# Let's inspect faces where vertices are within 70m of kiosko in XY
park_faces = []
for poly in mesh.polygons:
    poly_center = Vector((0, 0, 0))
    for vi in poly.vertices:
        poly_center += mesh.vertices[vi].co
    poly_center /= len(poly.vertices)
    
    if (poly_center.x - kiosko_blender.x)**2 + (poly_center.y - kiosko_blender.y)**2 < 70**2:
        park_faces.append(poly)

print(f"Found {len(park_faces)} faces near park.")

# Find unique vertices in these faces
vert_indices = set()
for poly in park_faces:
    for vi in poly.vertices:
        vert_indices.add(vi)

verts = [mesh.vertices[vi].co for vi in vert_indices]
print(f"Total unique vertices in park faces: {len(verts)}")

xs = [v.x for v in verts]
ys = [v.y for v in verts]
zs = [v.z for v in verts]
print(f"Blender X range (Godot X): {min(xs):.2f} to {max(xs):.2f}")
print(f"Blender Y range (-Godot Z): {min(ys):.2f} to {max(ys):.2f}")
print(f"Blender Z range (Godot Elevation Y): {min(zs):.2f} to {max(zs):.2f}")

# Let's print the boundary vertices or polygon loop
# Also let's check materials of these faces
mats = {mesh.materials[poly.material_index].name for poly in park_faces if poly.material_index < len(mesh.materials)}
print(f"Materials in park faces: {mats}")

# Print face details
for i, poly in enumerate(park_faces[:10]):
    print(f"Face {i}: area={poly.area:.2f}, normal={poly.normal}, verts={[mesh.vertices[vi].co for vi in poly.vertices]}")
