import bpy, bmesh, math
from mathutils import Vector, Matrix

bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new("TestRelaxedHand")
obj = bpy.data.objects.new("TestRelaxedHand", me)
bpy.context.scene.collection.objects.link(obj)
bm = bmesh.new()

is_left = True
sign_h = 1.0

# Hand position: Left wrist at (0.33, 0.01, 0.92)
# Semi-pronated orientation: Palm faces inward (-X, +Y at ~30 deg)
# Knuckle line runs from Index (front-medial) to Pinky (rear-lateral)
wrist_c = Vector((sign_h * 0.33, 0.01, 0.92))

# 4 Fingers: Index, Middle, Ring, Little
finger_specs = [
    # (name, offset_along_knuckles, len, rad, curl_angle_deg, has_ring)
    ("Index",  Vector((sign_h * 0.318,  0.024, 0.852)), 0.076, 0.0068, 25.0, True),
    ("Middle", Vector((sign_h * 0.328,  0.012, 0.848)), 0.084, 0.0072, 35.0, True),
    ("Ring",   Vector((sign_h * 0.338, -0.002, 0.850)), 0.078, 0.0068, 42.0, False),
    ("Little", Vector((sign_h * 0.346, -0.016, 0.855)), 0.066, 0.0058, 50.0, False),
]

# Palm construction
# Wrist ring (8 vertices)
wrist_r = 0.022
w_verts = []
for k in range(8):
    ang = (2.0 * math.pi * k) / 8.0
    vx = wrist_c.x + wrist_r * 0.85 * math.cos(ang)
    vy = wrist_c.y + wrist_r * 1.15 * math.sin(ang)
    vz = wrist_c.z
    w_verts.append(bm.verts.new((vx, vy, vz)))

# Knuckle row (Dorsum and Palmar vertices)
dorsum_knuckles = []
palmar_knuckles = []
for (name, mcp, flen, frad, curl, ring) in finger_specs:
    # Vector perpendicular to knuckle line (facing outward for dorsum, inward for palmar)
    dorsum_v = bm.verts.new((mcp.x + sign_h * 0.012, mcp.y - 0.008, mcp.z + 0.002))
    palmar_v = bm.verts.new((mcp.x - sign_h * 0.010, mcp.y + 0.006, mcp.z - 0.002))
    dorsum_knuckles.append(dorsum_v)
    palmar_knuckles.append(palmar_v)

# Connect wrist to knuckles (palm faces)
for i in range(3):
    # Dorsum face
    bm.faces.new((dorsum_knuckles[i], dorsum_knuckles[i+1], w_verts[i+4], w_verts[i+3]))
    # Palmar face
    bm.faces.new((palmar_knuckles[i+1], palmar_knuckles[i], w_verts[i], w_verts[i+1]))

# Build each finger with 3 articulated phalanxes curling inward-forward
for (name, mcp, flen, frad, curl_deg, has_ring) in finger_specs:
    rad_curl = math.radians(curl_deg)
    # Direction of curling: toward inward (-X) and forward (+Y)
    curl_dir = Vector((-sign_h * 0.70, 0.40, 0.0)).normalized()
    
    # 4 joint points: MCP -> PIP -> DIP -> Tip
    p0 = mcp
    # Phalanx 1: down and slightly in direction of curl
    p1 = p0 + Vector((0, 0, -flen * 0.38)) + curl_dir * (flen * 0.15)
    # Phalanx 2: curling further in
    p2 = p1 + Vector((0, 0, -flen * 0.34)) + curl_dir * (flen * 0.38)
    # Tip: curled softly toward palm
    p3 = p2 + Vector((0, 0, -flen * 0.24)) + curl_dir * (flen * 0.50)

    joints = [p0, p1, p2, p3]
    prev_ring = None
    for j_idx, pt in enumerate(joints):
        cur_rad = frad * (1.0 - 0.28 * (j_idx / 3.0))
        cur_ring = []
        for k in range(6):
            k_ang = (2.0 * math.pi * k) / 6.0
            vx = pt.x + cur_rad * math.cos(k_ang)
            vy = pt.y + cur_rad * math.sin(k_ang)
            vz = pt.z + cur_rad * 0.5 * math.sin(k_ang)
            cur_ring.append(bm.verts.new((vx, vy, vz)))
        if prev_ring:
            for k in range(6):
                kn = (k + 1) % 6
                bm.faces.new((prev_ring[k], prev_ring[kn], cur_ring[kn], cur_ring[k]))
        prev_ring = cur_ring

    # Rounded tip
    tip_v = bm.verts.new(p3 + curl_dir * 0.003 - Vector((0, 0, 0.003)))
    for k in range(6):
        kn = (k + 1) % 6
        bm.faces.new((prev_ring[kn], prev_ring[k], tip_v))

# Thumb: starts from thenar cushion (front-medial) and opposes toward index
th_base = Vector((sign_h * 0.312, 0.026, 0.885))
th_joints = [
    th_base,
    th_base + Vector((-sign_h * 0.010, 0.012, -0.024)),
    th_base + Vector((-sign_h * 0.016, 0.020, -0.046)),
    th_base + Vector((-sign_h * 0.018, 0.022, -0.062)),
]
prev_th = None
for j_idx, pt in enumerate(th_joints):
    th_rad = 0.0078 * (1.0 - 0.22 * (j_idx / 3.0))
    cur_ring = []
    for k in range(6):
        k_ang = (2.0 * math.pi * k) / 6.0
        vx = pt.x + th_rad * math.cos(k_ang)
        vy = pt.y + th_rad * math.sin(k_ang)
        vz = pt.z + th_rad * 0.5 * math.sin(k_ang)
        cur_ring.append(bm.verts.new((vx, vy, vz)))
    if prev_th:
        for k in range(6):
            kn = (k + 1) % 6
            bm.faces.new((prev_th[k], prev_th[kn], cur_ring[kn], cur_ring[k]))
    prev_th = cur_ring
tip_th = bm.verts.new(th_joints[-1] + Vector((-sign_h * 0.003, 0.004, -0.003)))
for k in range(6):
    kn = (k + 1) % 6
    bm.faces.new((prev_th[kn], prev_th[k], tip_th))

bm.normal_update()
for f in bm.faces: f.smooth = True
bm.to_mesh(me)
bm.free()

sub = obj.modifiers.new("Subsurf", type='SUBSURF')
sub.levels = 1

# Render test from camera
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 16
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
cam.location = Vector((0.33, 0.50, 0.85))
cam.rotation_euler = (math.radians(90), 0.0, math.radians(180))
scene.collection.objects.link(cam)
scene.camera = cam

light = bpy.data.objects.new("Light", bpy.data.lights.new("Light", 'AREA'))
light.location = Vector((0.2, 0.4, 1.0))
light.data.energy = 25.0
scene.collection.objects.link(light)

scene.render.filepath = "/tmp/test_hand_v2.png"
bpy.ops.render.render(write_still=True)
print("Hand test rendered cleanly to /tmp/test_hand_v2.png!")
