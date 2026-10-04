import bpy
import sys
import os

PROJECT_ROOT = "/Users/hakkindavid/Documents/GitHub/tecate-simulator"
sys.path.insert(0, os.path.join(PROJECT_ROOT, "scratch"))
import test_axel_vest_v15 as t

t.clean_scene()
mat_skin = t.create_pbr_material("Mat_Axel_Skin", (0.82, 0.61, 0.49, 1.0))
mat_eye = t.create_pbr_material("Mat_Axel_Eyes", (1, 1, 1, 1))
mat_hair = t.create_pbr_material("Mat_Axel_Hair", (0.04, 0.035, 0.03, 1.0))
mat_fedora = t.create_pbr_material("Mat_Axel_Fedora", (0.02, 0.02, 0.025, 1.0))
mat_hatband = t.create_pbr_material("Mat_Axel_Hatband", (0.015, 0.015, 0.02, 1.0))
mat_shirt = t.create_pbr_material("Mat_Axel_Shirt", (0.17, 0.18, 0.20, 1.0))
mat_pants = t.create_pbr_material("Mat_Axel_Pants", (0.13, 0.14, 0.16, 1.0))
mat_shoes = t.create_pbr_material("Mat_Axel_Shoes", (0.03, 0.03, 0.035, 1.0))
mat_vest = t.create_pbr_material("Mat_Axel_Vest", (0.84, 0.85, 0.87, 1.0))
mat_tie = t.create_pbr_material("Mat_Axel_Tie", (0.35, 0.36, 0.38, 1.0))
mat_silver = t.create_pbr_material("Mat_Axel_Silver", (0.88, 0.89, 0.90, 1.0))

materials = {
    "head": [mat_skin, mat_eye, mat_hair, mat_fedora, mat_hatband],
    "body": [mat_shirt, mat_pants, mat_shoes, mat_vest, mat_tie, mat_silver, mat_skin]
}

skel = t.build_skeleton()
head = t.build_head_mesh(materials)
t.assign_weights(head, is_head=True)

body = t.build_body_mesh(materials)
t.assign_weights(body, is_head=False)

print("\n--- AUDITORÍA DE VERTEX GROUPS Y PESOS DE RIGGING ---")
leg_groups = ["UpperLeg.L", "UpperLeg.R", "LowerLeg.L", "LowerLeg.R", "Foot.L", "Foot.R", "Toes.L", "Toes.R"]

leaks = 0
for g_name in leg_groups:
    if g_name in body.vertex_groups:
        grp = body.vertex_groups[g_name]
        for v in body.data.vertices:
            for g in v.groups:
                if g.group == grp.index and g.weight > 0.0:
                    if abs(v.co.x) > 0.18:
                        print(f"ERROR: Vertice {v.index} en {v.co} asignado a {g_name} con peso {g.weight} (|X| > 0.18)")
                        leaks += 1

hand_verts_L = 0
hand_verts_R = 0
for v in body.data.vertices:
    for g in v.groups:
        if g.group == body.vertex_groups["Hand.L"].index and g.weight > 0.0:
            hand_verts_L += 1
        elif g.group == body.vertex_groups["Hand.R"].index and g.weight > 0.0:
            hand_verts_R += 1

print(f"Vértices asignados a Hand.L: {hand_verts_L}")
print(f"Vértices asignados a Hand.R: {hand_verts_R}")
print(f"Fugas a huesos de piernas: {leaks}")
assert leaks == 0, "Existen fugas de vértices hacia las piernas!"
print("✓ AUDITORÍA RIGGING BLINDADA: 0 fugas de vértices a piernas.")
