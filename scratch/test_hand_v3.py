import bpy, bmesh, math
from mathutils import Vector, Matrix

bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new("TestHumanHand")
obj = bpy.data.objects.new("TestHumanHand", me)
bpy.context.scene.collection.objects.link(obj)
bm = bmesh.new()

is_left = True
sign_h = 1.0

# Center of wrist at Z = 0.920
# Hand orientation: Semi-pronated.
# Palm faces inward (-X for left hand), thumb is forward (+Y), pinky is rearward (-Y)
w_center = Vector((sign_h * 0.33, 0.008, 0.920))

# Palm dimensions
palm_len = 0.065 # from wrist to knuckles in Z
palm_thick = 0.024 # across X
palm_width = 0.055 # along Y (from thumb side to pinky side)

# 8 box vertices for the palm core
# In X: medial (palm/inner) to lateral (dorsum/outer)
x_in = w_center.x - sign_h * 0.012  # inner / palmar side
x_out = w_center.x + sign_h * 0.012 # outer / dorsum side
y_ant = w_center.y + 0.028          # anterior (index/thumb side)
y_post = w_center.y - 0.026         # posterior (pinky side)
z_top = 0.920
z_bot = 0.855

p_box = [
    # Top ring (wrist)
    bm.verts.new((x_in,  y_ant,  z_top)), # 0: in-ant
    bm.verts.new((x_out, y_ant,  z_top)), # 1: out-ant
    bm.verts.new((x_out, y_post, z_top)), # 2: out-post
    bm.verts.new((x_in,  y_post, z_top)), # 3: in-post
    # Bottom ring (knuckles)
    bm.verts.new((x_in,  y_ant,  z_bot)), # 4: in-ant
    bm.verts.new((x_out, y_ant,  z_bot)), # 5: out-ant
    bm.verts.new((x_out, y_post, z_bot)), # 6: out-post
    bm.verts.new((x_in,  y_post, z_bot)), # 7: in-post
]

# Palm core faces
bm.faces.new((p_box[0], p_box[1], p_box[5], p_box[4])) # Front (anterior/thenar)
bm.faces.new((p_box[1], p_box[2], p_box[6], p_box[5])) # Dorsum (outer/back of hand)
bm.faces.new((p_box[2], p_box[3], p_box[7], p_box[6])) # Hypothenar (rear)
bm.faces.new((p_box[3], p_box[0], p_box[4], p_box[7])) # Palm (inner/facing thigh)

# 4 Fingers: Index, Middle, Ring, Little
# Distributed along Y from y_ant down to y_post
finger_specs = [
    # name, y_pos, len, rad, curl_factor, has_ring
    ("Index",   w_center.y + 0.018, 0.060, 0.0070, 0.85, is_left),
    ("Middle",  w_center.y + 0.005, 0.066, 0.0074, 1.00, is_left),
    ("Ring",    w_center.y - 0.008, 0.061, 0.0070, 1.15, False),
    ("Little",  w_center.y - 0.020, 0.050, 0.0060, 1.30, False),
]

curl_dir = Vector((-sign_h * 0.70, 0.35, 0.0)).normalized()

for (f_name, fy, flen, frad, curl, has_ring) in finger_specs:
    mcp = Vector((w_center.x, fy, z_bot))
    # Joints: MCP -> PIP -> DIP -> Tip
    p0 = mcp
    p1 = p0 + Vector((0, 0, -flen * 0.38)) + curl_dir * (flen * 0.18 * curl)
    p2 = p1 + Vector((0, 0, -flen * 0.34)) + curl_dir * (flen * 0.38 * curl)
    p3 = p2 + Vector((0, 0, -flen * 0.24)) + curl_dir * (flen * 0.48 * curl)

    joints = [p0, p1, p2, p3]
    prev_ring = None
    for j_idx, pt in enumerate(joints):
        rad = frad * (1.0 - 0.25 * (j_idx / 3.0))
        cur_ring = []
        for k in range(6):
            ang = (2.0 * math.pi * k) / 6.0
            vx = pt.x + rad * math.cos(ang)
            vy = pt.y + rad * math.sin(ang)
            vz = pt.z + rad * 0.5 * math.sin(ang)
            cur_ring.append(bm.verts.new((vx, vy, vz)))
        if prev_ring:
            for k in range(6):
                kn = (k + 1) % 6
                bm.faces.new((prev_ring[k], prev_ring[kn], cur_ring[kn], cur_ring[k]))
        prev_ring = cur_ring

    tip_v = bm.verts.new(p3 + curl_dir * 0.003 - Vector((0, 0, 0.003)))
    for k in range(6):
        kn = (k + 1) % 6
        bm.faces.new((prev_ring[kn], prev_ring[k], tip_v))

# Thumb: from antero-medial corner of palm
th_mcp = Vector((x_in - sign_h * 0.004, y_ant + 0.005, z_bot + 0.025))
th_joints = [
    th_mcp,
    th_mcp + Vector((-sign_h * 0.008, 0.012, -0.018)),
    th_mcp + Vector((-sign_h * 0.014, 0.018, -0.035)),
    th_mcp + Vector((-sign_h * 0.016, 0.020, -0.048)),
]
prev_th = None
for j_idx, pt in enumerate(th_joints):
    th_rad = 0.0080 * (1.0 - 0.20 * (j_idx / 3.0))
    cur_ring = []
    for k in range(6):
        ang = (2.0 * math.pi * k) / 6.0
        vx = pt.x + th_rad * math.cos(ang)
        vy = pt.y + th_rad * math.sin(ang)
        vz = pt.z + th_rad * 0.5 * math.sin(ang)
        cur_ring.append(bm.verts.new((vx, vy, vz)))
    if prev_th:
        for k in range(6):
            kn = (k + 1) % 6
            bm.faces.new((prev_th[k], prev_th[kn], cur_ring[kn], cur_ring[k]))
    prev_th = cur_ring
tip_th = bm.verts.new(th_joints[-1] + Vector((-sign_h * 0.002, 0.003, -0.003)))
for k in range(6):
    kn = (k + 1) % 6
    bm.faces.new((prev_th[kn], prev_th[k], tip_th))

bm.normal_update()
for f in bm.faces: f.smooth = True
bm.to_mesh(me)
bm.free()

sub = obj.modifiers.new("Subsurf", type='SUBSURF')
sub.levels = 1

# Render preview
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 16
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
cam.location = Vector((0.33, 0.40, 0.85))
cam.rotation_euler = (math.radians(90), 0.0, math.radians(180))
scene.collection.objects.link(cam)
scene.camera = cam

light = bpy.data.objects.new("Light", bpy.data.lights.new("Light", 'AREA'))
light.location = Vector((0.2, 0.4, 1.0))
light.data.energy = 25.0
scene.collection.objects.link(light)

scene.render.filepath = "/tmp/test_hand_v3.png"
bpy.ops.render.render(write_still=True)
print("Hand v3 rendered cleanly!")
