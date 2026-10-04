import bpy, bmesh, math
from mathutils import Vector, Matrix

bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new("TestHand")
obj = bpy.data.objects.new("TestHand", me)
bpy.context.scene.collection.objects.link(obj)
bm = bmesh.new()

is_left = True
sign_h = 1.0
w_m = sign_h * 0.305 # Medial (thumb side)
w_l = sign_h * 0.355 # Lateral (pinky side)

# Palm vertices (Dorsum and Palmar sides)
palm_z_top = 0.920
palm_z_mid = 0.885
palm_z_mcp = 0.852

# Build fingers with natural relaxed curvature
finger_params = [
    # name, frac, len, radius, curl_factor, ring
    ("Index",  0.15, 0.075, 0.0068, 0.85, True),
    ("Middle", 0.40, 0.084, 0.0072, 1.00, True),
    ("Ring",   0.65, 0.078, 0.0068, 1.15, False),
    ("Little", 0.90, 0.066, 0.0058, 1.30, False),
]

for (f_name, f_frac, f_len, f_rad, curl, has_ring) in finger_params:
    fx = w_m + (w_l - w_m) * f_frac
    mcp_z = palm_z_mcp - 0.004 * math.sin(f_frac * math.pi)
    mcp_y = 0.012

    # Natural anatomical 4-point curve for relaxed finger:
    # 0: MCP, 1: PIP, 2: DIP, 3: Tip
    p_joints = [
        Vector((fx, mcp_y, mcp_z)),
        Vector((fx, mcp_y + 0.014 * curl, mcp_z - f_len * 0.38)),
        Vector((fx, mcp_y + 0.030 * curl, mcp_z - f_len * 0.72)),
        Vector((fx, mcp_y + 0.042 * curl, mcp_z - f_len * 0.98)),
    ]

    prev_ring = None
    for j_idx, pt in enumerate(p_joints):
        rad = f_rad * (1.0 - 0.28 * (j_idx / 3.0))
        cur_ring = []
        for k in range(6):
            ang = (2.0 * math.pi * k) / 6.0
            vx = pt.x + rad * 1.1 * math.cos(ang)
            vy = pt.y + rad * math.sin(ang) * 0.9
            vz = pt.z + rad * math.sin(ang) * 0.4
            cur_ring.append(bm.verts.new((vx, vy, vz)))
        if prev_ring:
            for k in range(6):
                kn = (k + 1) % 6
                bm.faces.new((prev_ring[k], prev_ring[kn], cur_ring[kn], cur_ring[k]))
        prev_ring = cur_ring

    # Tip
    tip_v = bm.verts.new((p_joints[-1].x, p_joints[-1].y + 0.004 * curl, p_joints[-1].z - 0.003))
    for k in range(6):
        kn = (k + 1) % 6
        bm.faces.new((prev_ring[kn], prev_ring[k], tip_v))

# Thumb
th_joints = [
    Vector((w_m - sign_h * 0.005, 0.018, 0.890)),
    Vector((w_m - sign_h * 0.016, 0.026, 0.865)),
    Vector((w_m - sign_h * 0.022, 0.034, 0.840)),
    Vector((w_m - sign_h * 0.024, 0.038, 0.822)),
]
prev_th = None
for j_idx, pt in enumerate(th_joints):
    rad = 0.0075 * (1.0 - 0.22 * (j_idx / 3.0))
    cur_ring = []
    for k in range(6):
        ang = (2.0 * math.pi * k) / 6.0
        vx = pt.x + rad * math.cos(ang)
        vy = pt.y + rad * math.sin(ang)
        vz = pt.z + rad * math.sin(ang) * 0.4
        cur_ring.append(bm.verts.new((vx, vy, vz)))
    if prev_th:
        for k in range(6):
            kn = (k + 1) % 6
            bm.faces.new((prev_th[k], prev_th[kn], cur_ring[kn], cur_ring[k]))
    prev_th = cur_ring
tip_th = bm.verts.new((th_joints[-1].x, th_joints[-1].y + 0.003, th_joints[-1].z - 0.004))
for k in range(6):
    kn = (k + 1) % 6
    bm.faces.new((prev_th[kn], prev_th[k], tip_th))

bm.to_mesh(me)
bm.free()

print(f"Hand generated! Total verts: {len(me.vertices)}, Total faces: {len(me.polygons)}")
