import bpy

bpy.ops.wm.open_mainfile(filepath="blender_assets/osm2world_adjusted.blend")

print("\n--- EDIFICIOS CERCANOS A PARQUE HIDALGO EN OSM2WORLD ---")
buildings_near = []
for obj in bpy.data.objects:
    if obj.type == 'MESH' and obj.name.startswith("Building_"):
        mesh = obj.data
        if len(mesh.vertices) > 0:
            xs = [v.co.x for v in mesh.vertices]
            ys = [v.co.y for v in mesh.vertices]
            zs = [v.co.z for v in mesh.vertices]
            cx = (min(xs) + max(xs)) / 2.0
            cy = (min(ys) + max(ys)) / 2.0
            cz = (min(zs) + max(zs)) / 2.0
            dx = cx - (-50.0)
            dy = cy - (10.0)
            dist = (dx*dx + dy*dy)**0.5
            if dist < 120.0:
                buildings_near.append((dist, obj.name, (min(xs), max(xs)), (min(ys), max(ys)), (min(zs), max(zs)), (cx, cy, cz)))

buildings_near.sort(key=lambda x: x[0])
for d, name, xr, yr, zr, c in buildings_near:
    # Convert to Godot coordinates:
    # Godot X = cx, Godot Y = cz, Godot Z = -cy
    gx, gy, gz = c[0], c[2], -c[1]
    print(f"{name} (dist={d:.1f}m):")
    print(f"   Blender: X={xr[0]:.2f}..{xr[1]:.2f}, Y={yr[0]:.2f}..{yr[1]:.2f}, Z={zr[0]:.2f}..{zr[1]:.2f}")
    print(f"   Godot Centroid: Vector3({gx:.2f}, {gy:.2f}, {gz:.2f})")
