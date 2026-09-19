import bpy

bpy.ops.wm.open_mainfile(filepath="blender_assets/osm2world_adjusted.blend")
print("Total objects in osm2world_adjusted.blend:", len(bpy.data.objects))

# Find objects around BBVA / Parque Hidalgo
# In Godot, BBVA is at X = -66.8, Y = 400.38, Z = -24.81
# In glTF / Godot conversion:
# Godot (X, Y, Z) = Blender (X, Z, -Y)
# So Godot (-66.8, 400.38, -24.81) -> Blender (-66.8, 24.81, 400.38)
bbva_blender = (-66.8, 24.81, 400.38)
print(f"Target BBVA in Blender coords: {bbva_blender}")

# Search for meshes near this point (within 100 meters)
nearby = []
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        loc = obj.matrix_world.translation
        dx = loc.x - bbva_blender[0]
        dy = loc.y - bbva_blender[1]
        dist = (dx*dx + dy*dy)**0.5
        if dist < 120.0:
            nearby.append((dist, obj.name, (loc.x, loc.y, loc.z)))

nearby.sort(key=lambda x: x[0])
print(f"Total meshes within 120m of BBVA: {len(nearby)}")
for d, name, loc in nearby[:30]:
    print(f"  d={d:.1f}m: {name} at ({loc[0]:.2f}, {loc[1]:.2f}, {loc[2]:.2f})")
