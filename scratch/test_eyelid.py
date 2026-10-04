import bpy, bmesh, math
from mathutils import Vector, Matrix

bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new("TestHead")
obj = bpy.data.objects.new("TestHead", me)
bpy.context.scene.collection.objects.link(obj)
bm = bmesh.new()

eye_c = Vector((0.033, 0.055, 1.542))
r = 0.0125

# Create eye
e_bm = bmesh.new()
bmesh.ops.create_uvsphere(e_bm, u_segments=16, v_segments=12, radius=r)
v_map = {v: bm.verts.new(v.co + eye_c) for v in e_bm.verts}
for f in e_bm.faces:
    bm.faces.new([v_map[v] for v in f.verts])
e_bm.free()

# Upper lid arc
n_pts = 7
upper_lid_v = []
for row in range(3):
    cur_row = []
    for i in range(n_pts):
        t = (i / float(n_pts - 1)) * 2.0 - 1.0 # -1 to 1
        x = eye_c.x + t * 0.012
        dx = x - eye_c.x
        if row == 0:
            dz = 0.013 * math.sqrt(max(0.0, 1.0 - (dx / 0.013)**2))
        elif row == 1:
            dz = 0.007 * math.sqrt(max(0.0, 1.0 - (dx / 0.013)**2))
        else:
            dz = 0.0025 * math.sqrt(max(0.0, 1.0 - (dx / 0.013)**2))
        dy = math.sqrt(max(0.0001, (r * 1.06)**2 - dx**2 - dz**2))
        cur_row.append(bm.verts.new((x, eye_c.y + dy, eye_c.z + dz)))
    upper_lid_v.append(cur_row)

for row in range(2):
    for i in range(n_pts - 1):
        bm.faces.new((upper_lid_v[row][i], upper_lid_v[row][i+1], upper_lid_v[row+1][i+1], upper_lid_v[row+1][i]))

# Lower lid arc
lower_lid_v = []
for row in range(2):
    cur_row = []
    for i in range(n_pts):
        t = (i / float(n_pts - 1)) * 2.0 - 1.0
        x = eye_c.x + t * 0.012
        dx = x - eye_c.x
        if row == 0:
            dz = -0.0035 * math.sqrt(max(0.0, 1.0 - (dx / 0.013)**2))
        else:
            dz = -0.010 * math.sqrt(max(0.0, 1.0 - (dx / 0.013)**2))
        dy = math.sqrt(max(0.0001, (r * 1.05)**2 - dx**2 - dz**2))
        cur_row.append(bm.verts.new((x, eye_c.y + dy, eye_c.z + dz)))
    lower_lid_v.append(cur_row)

for i in range(n_pts - 1):
    bm.faces.new((lower_lid_v[0][i], lower_lid_v[0][i+1], lower_lid_v[1][i+1], lower_lid_v[1][i]))

bm.verts.ensure_lookup_table()
margin_verts = [v.index for v in upper_lid_v[2]]
crease_verts = [v.index for v in upper_lid_v[1]]
bm.to_mesh(me)
bm.free()

print(f"Mesh created! Total verts: {len(me.vertices)}, faces: {len(me.polygons)}")

# Test shape key blink
sk_basis = obj.shape_key_add(name="Basis")
sk_blink = obj.shape_key_add(name="blink")

# Track upper lid margin verts and move them down
for v_idx in margin_verts:
    sk_blink.data[v_idx].co.z -= 0.006
    sk_blink.data[v_idx].co.y += 0.001
for v_idx in crease_verts:
    sk_blink.data[v_idx].co.z -= 0.003

print(f"Shape key blink added with {len(margin_verts)} animated vertices!")
