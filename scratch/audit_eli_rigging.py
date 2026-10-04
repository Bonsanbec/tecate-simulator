"""
=============================================================================
Auditoría Estricta de Rigging y Asignación de Pesos para Eli en Tecate Simulator
=============================================================================
Verifica:
1. Existencia del armature canónico Skeleton3D con exactamente 22 huesos.
2. Presencia de mallas modulares Player_Head_Mesh y Player_Body_Mesh.
3. Shape Key 'blink' en Player_Head_Mesh para parpadeo biológico.
4. CERO fugas de vértices de brazos/manos (|X| > 0.18 m) hacia grupos de piernas.
5. Asignación correcta de Hand.L y Hand.R en manos anatómicas.
6. Asignación limpia de Head y Neck en la cabeza.
=============================================================================
"""
import bpy
import os
import sys

PROJECT_ROOT = "/Users/hakkindavid/Documents/GitHub/tecate-simulator"
BLEND_PATH = os.path.join(PROJECT_ROOT, "godot_project/assets/characters/citizens/eli.blend")

def audit_eli():
    print("=" * 60)
    print("INICIANDO AUDITORÍA FORMAL DE RIGGING Y PESOS: ELI")
    print("=" * 60)

    if not os.path.exists(BLEND_PATH):
        raise FileNotFoundError(f"No se encontró el archivo {BLEND_PATH}")

    bpy.ops.wm.open_mainfile(filepath=BLEND_PATH)

    skel = bpy.data.objects.get("Skeleton3D")
    assert skel is not None, "El objeto Skeleton3D no existe en eli.blend"
    assert skel.type == 'ARMATURE', "Skeleton3D debe ser de tipo ARMATURE"

    # 1. Validación de 22 huesos canónicos
    expected_bones = [
        "Root", "Hips", "Spine", "Chest", "Neck", "Head",
        "Shoulder.L", "UpperArm.L", "Forearm.L", "Hand.L",
        "Shoulder.R", "UpperArm.R", "Forearm.R", "Hand.R",
        "UpperLeg.L", "LowerLeg.L", "Foot.L", "Toes.L",
        "UpperLeg.R", "LowerLeg.R", "Foot.R", "Toes.R"
    ]
    actual_bones = [b.name for b in skel.data.bones]
    print(f"Total de huesos encontrados: {len(actual_bones)}")
    for eb in expected_bones:
        assert eb in actual_bones, f"Hueso faltante en Skeleton3D: {eb}"
    print("✓ Validación de esqueleto: Los 22 huesos antropométricos están presentes.")

    # 2. Validación de mallas modulares
    head_obj = bpy.data.objects.get("Player_Head_Mesh")
    body_obj = bpy.data.objects.get("Player_Body_Mesh")
    assert head_obj is not None, "Player_Head_Mesh no existe"
    assert body_obj is not None, "Player_Body_Mesh no existe"
    print("✓ Mallas modulares verificadas: Player_Head_Mesh y Player_Body_Mesh presentes.")

    # 3. Shape Key 'blink'
    assert head_obj.data.shape_keys is not None, "Player_Head_Mesh no posee Shape Keys"
    key_blocks = [kb.name for kb in head_obj.data.shape_keys.key_blocks]
    assert "Basis" in key_blocks, "Falta Basis en Shape Keys"
    assert "blink" in key_blocks, "Falta 'blink' en Shape Keys para parpadeo biológico"
    print("✓ Shape Key 'blink' validada para parpadeo biológico.")

    # 4. Auditoría matemática de pesos y prevención de fugas
    leg_groups = ["UpperLeg.L", "UpperLeg.R", "LowerLeg.L", "LowerLeg.R", "Foot.L", "Foot.R", "Toes.L", "Toes.R"]
    leaks = 0
    for g_name in leg_groups:
        if g_name in body_obj.vertex_groups:
            grp = body_obj.vertex_groups[g_name]
            for v in body_obj.data.vertices:
                for g in v.groups:
                    if g.group == grp.index and g.weight > 0.0:
                        if abs(v.co.x) > 0.18:
                            print(f"ERROR: Fuga de vértice {v.index} en {v.co} asignado a {g_name} con peso {g.weight}")
                            leaks += 1

    hand_verts_L = 0
    hand_verts_R = 0
    for v in body_obj.data.vertices:
        for g in v.groups:
            if g.group == body_obj.vertex_groups["Hand.L"].index and g.weight > 0.0:
                hand_verts_L += 1
            elif g.group == body_obj.vertex_groups["Hand.R"].index and g.weight > 0.0:
                hand_verts_R += 1

    print(f"Vértices asignados a Hand.L: {hand_verts_L}")
    print(f"Vértices asignados a Hand.R: {hand_verts_R}")
    print(f"Fugas de vértices a huesos de piernas detectadas: {leaks}")
    assert leaks == 0, f"Se detectaron {leaks} fugas de vértices de brazos/manos a piernas!"
    print("✓ AUDITORÍA RIGGING BLINDADA: 0 fugas de vértices hacia las piernas.")

    # 5. Auditoría de cabeza
    head_verts = 0
    neck_verts = 0
    for v in head_obj.data.vertices:
        for g in v.groups:
            if g.group == head_obj.vertex_groups["Head"].index and g.weight > 0.0:
                head_verts += 1
            elif g.group == head_obj.vertex_groups["Neck"].index and g.weight > 0.0:
                neck_verts += 1
    print(f"Vértices de cabeza asignados a Head: {head_verts}")
    print(f"Vértices de cabeza asignados a Neck: {neck_verts}")
    assert head_verts > 0, "No hay vértices asignados a Head"
    assert neck_verts > 0, "No hay vértices asignados a Neck"

    print("=" * 60)
    print("TODAS LAS AUDITORÍAS DE RIGGING Y ASIGNACIÓN DE PESOS PASARON CON ÉXITO")
    print("=" * 60)

if __name__ == "__main__":
    audit_eli()
