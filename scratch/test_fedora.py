import bpy, bmesh, math
from mathutils import Vector, Matrix

bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new("TestFedora")
obj = bpy.data.objects.new("TestFedora", me)
bpy.context.scene.collection.objects.link(obj)
bm = bmesh.new()

n_hat = 32
hat_levels = [
    # z, rx, ry, y_c, pinch_x, crease
    (1.575, 0.092, 0.102, -0.002, 1.00, 0.000),
    (1.600, 0.090, 0.100, -0.003, 0.96, 0.000),
    (1.630, 0.086, 0.096, -0.004, 0.90, 0.000),
    (1.655, 0.082, 0.092, -0.005, 0.84, 0.000),
    (1.675, 0.078, 0.088, -0.006, 0.78, 0.016),
]
crown_rings = []
for (z, rx, ry, y_c, pinch_x, crease) in hat_levels:
    cur_ring = []
    for i in range(n_hat):
        ang = (2.0 * math.pi * i) / n_hat
        cos_a = math.cos(ang)
        sin_a = math.sin(ang)
        cur_rx = rx * (pinch_x if sin_a > 0 else 1.0)
        vx = cur_rx * cos_a
        vy = ry * sin_a + y_c
        vz = z
        if crease > 0.0:
            dist_x = abs(vx) / cur_rx
            if dist_x < 0.6: vz -= crease * (1.0 - dist_x / 0.6)
        cur_ring.append(bm.verts.new((vx, vy, vz)))
    crown_rings.append(cur_ring)

# Crown walls
for l in range(len(hat_levels) - 1):
    r1 = crown_rings[l]
    r2 = crown_rings[l + 1]
    for i in range(n_hat):
        inxt = (i + 1) % n_hat
        bm.faces.new((r1[i], r1[inxt], r2[inxt], r2[i]))

# Crown top
top_c = bm.verts.new((0.0, -0.006, 1.660))
for i in range(n_hat):
    inxt = (i + 1) % n_hat
    bm.faces.new((crown_rings[-1][i], crown_rings[-1][inxt], top_c))

# Manifold Brim with upper and lower surface + perimeter thickness
brim_inner_top = crown_rings[0]
brim_outer_top = []
brim_outer_bot = []
brim_inner_bot = []

for i in range(n_hat):
    ang = (2.0 * math.pi * i) / n_hat
    cos_a = math.cos(ang)
    sin_a = math.sin(ang)
    dip_z = -0.018 * max(0.0, sin_a) + 0.012 * abs(cos_a) + 0.006 * max(0.0, -sin_a)
    bx = 0.158 * cos_a
    by = 0.170 * sin_a - 0.002
    bz = 1.575 + dip_z
    brim_outer_top.append(bm.verts.new((bx, by, bz + 0.0015)))
    brim_outer_bot.append(bm.verts.new((bx, by, bz - 0.0015)))
    
    # inner bot ring (slightly tucked inside crown)
    in_v = crown_rings[0][i].co
    brim_inner_bot.append(bm.verts.new((in_v.x * 0.98, in_v.y * 0.98, in_v.z - 0.003)))

for i in range(n_hat):
    inxt = (i + 1) % n_hat
    # Upper brim surface (normal UP)
    bm.faces.new((brim_inner_top[inxt], brim_inner_top[i], brim_outer_top[i], brim_outer_top[inxt]))
    # Outer edge rim (normal OUT)
    bm.faces.new((brim_outer_top[i], brim_outer_bot[i], brim_outer_bot[inxt], brim_outer_top[inxt]))
    # Lower brim surface (normal DOWN)
    bm.faces.new((brim_outer_bot[i], brim_inner_bot[i], brim_inner_bot[inxt], brim_outer_bot[inxt]))

bm.normal_update()
for f in bm.faces: f.smooth = True
bm.to_mesh(me)
bm.free()

sub = obj.modifiers.new("Subsurf", type='SUBSURF')
sub.levels = 1

# Save blend and render test
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 16
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
cam.location = Vector((0.0, 1.5, 1.6))
cam.rotation_euler = (math.radians(90), 0.0, math.radians(180))
scene.collection.objects.link(cam)
scene.camera = cam

light = bpy.data.objects.new("Light", bpy.data.lights.new("Light", 'AREA'))
light.location = Vector((-0.5, 1.2, 1.8))
light.data.energy = 50.0
scene.collection.objects.link(light)

scene.render.filepath = "/tmp/test_fedora.png"
bpy.ops.render.render(write_still=True)
print("Fedora test rendered cleanly to /tmp/test_fedora.png!")
