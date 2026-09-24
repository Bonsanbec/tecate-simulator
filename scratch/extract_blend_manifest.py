"""
extract_blend_manifest.py
Extrae todos los objetos y mallas de osm2world_adjusted.blend
y exporta sus metadatos a JSON para cruzar con los cachés.

Uso:
    blender --background blender_assets/osm2world_adjusted.blend \
            --python scratch/extract_blend_manifest.py

Si el .blend es un enlace simbólico a otro directorio, ajusta la ruta.
"""

import bpy
import json
import os
import sys
import math

OUTPUT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "blend_objects_raw.json"
)

def get_world_bbox(obj):
    """Bounding box en coordenadas mundo (8 esquinas)."""
    if obj.type != 'MESH' or not obj.data or len(obj.data.vertices) == 0:
        return None
    world_verts = [obj.matrix_world @ v.co for v in obj.data.vertices]
    xs = [v.x for v in world_verts]
    ys = [v.y for v in world_verts]
    zs = [v.z for v in world_verts]
    return {
        "x_min": min(xs), "x_max": max(xs),
        "y_min": min(ys), "y_max": max(ys),
        "z_min": min(zs), "z_max": max(zs),
        "cx": (min(xs) + max(xs)) / 2,
        "cy": (min(ys) + max(ys)) / 2,
        "cz": (min(zs) + max(zs)) / 2,
        "width_x": max(xs) - min(xs),
        "depth_y": max(ys) - min(ys),
        "height_z": max(zs) - min(zs),
    }


def blender_to_godot(bx, by, bz):
    """Convierte coordenadas de Blender a Godot (glTF Y-up)."""
    # En exportación glTF desde Blender: X=X, Y=Z, Z=-Y
    return (bx, bz, -by)


def get_custom_props(obj):
    """Extrae propiedades personalizadas del objeto."""
    props = {}
    for key in obj.keys():
        if key.startswith("_"):
            continue
        val = obj[key]
        try:
            if hasattr(val, "to_list"):
                props[key] = val.to_list()
            else:
                props[key] = val
        except Exception:
            props[key] = str(val)
    return props


def get_materials(obj):
    """Lista los nombres de materiales asignados."""
    if obj.type != 'MESH' or not obj.data:
        return []
    return [slot.material.name if slot.material else None for slot in obj.material_slots]


def get_collections(obj):
    """Devuelve las colecciones a las que pertenece el objeto."""
    return [col.name for col in obj.users_collection]


def main():
    scene = bpy.context.scene
    print(f"[extract_blend_manifest] Escena activa: {scene.name}")
    print(f"[extract_blend_manifest] Total objetos en escena: {len(bpy.data.objects)}")

    records = []
    type_histogram = {}

    for obj in bpy.data.objects:
        obj_type = obj.type
        type_histogram[obj_type] = type_histogram.get(obj_type, 0) + 1

        loc = obj.matrix_world.translation
        rot_euler = obj.matrix_world.to_euler()

        bbox = get_world_bbox(obj) if obj_type == 'MESH' else None
        godot_loc = blender_to_godot(loc.x, loc.y, loc.z)
        godot_centroid = None
        if bbox:
            godot_centroid = blender_to_godot(bbox["cx"], bbox["cy"], bbox["cz"])

        vert_count = 0
        face_count = 0
        if obj_type == 'MESH' and obj.data:
            vert_count = len(obj.data.vertices)
            face_count = len(obj.data.polygons)

        record = {
            "name": obj.name,
            "type": obj_type,
            "collections": get_collections(obj),
            "parent": obj.parent.name if obj.parent else None,
            "blender_location": [round(loc.x, 4), round(loc.y, 4), round(loc.z, 4)],
            "blender_rotation_euler_deg": [
                round(math.degrees(rot_euler.x), 2),
                round(math.degrees(rot_euler.y), 2),
                round(math.degrees(rot_euler.z), 2),
            ],
            "godot_location": [round(godot_loc[0], 4), round(godot_loc[1], 4), round(godot_loc[2], 4)],
            "bbox_blender": bbox,
            "godot_centroid": [round(c, 4) for c in godot_centroid] if godot_centroid else None,
            "vertex_count": vert_count,
            "face_count": face_count,
            "materials": get_materials(obj),
            "custom_properties": get_custom_props(obj),
            "data_name": obj.data.name if obj.data else None,
            "visible": obj.visible_get(),
            "hide_viewport": obj.hide_viewport,
            "hide_render": obj.hide_render,
        }

        # Inferir si es un edificio por nombre o propiedades
        name_lower = obj.name.lower()
        is_building_hint = any(k in name_lower for k in [
            "building", "edificio", "osm", "way", "relation",
            "structure", "house", "comercio", "bbva", "hotel",
            "iglesia", "farmacia", "tienda", "restaurante",
        ])
        record["is_building_hint"] = is_building_hint

        records.append(record)

    # Ordenar: primero mallas, luego por nombre
    records.sort(key=lambda r: (0 if r["type"] == "MESH" else 1, r["name"]))

    summary = {
        "blend_file": "osm2world_adjusted.blend",
        "total_objects": len(records),
        "type_histogram": type_histogram,
        "objects": records,
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n[extract_blend_manifest] ✅ Exportado: {OUTPUT_PATH}")
    print(f"  Total objetos: {len(records)}")
    print("  Distribución por tipo:")
    for t, c in sorted(type_histogram.items(), key=lambda x: -x[1]):
        print(f"    {t}: {c}")


main()
