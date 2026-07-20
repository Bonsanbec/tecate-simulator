import bpy

bpy.ops.wm.open_mainfile(filepath="models/tecate/osm2world.blend")

print("=" * 60)
print("INSPECTING OSM2WORLD.BLEND METADATA & CUSTOM PROPERTIES")
print("=" * 60)

print("1. Collections in osm2world.blend:")
for col in bpy.data.collections:
    print(f"  Collection: '{col.name}' (objects: {len(col.objects)})")
    for keys in col.keys():
        if keys not in ["_RNA_UI"]:
            print(f"    col prop: {keys} = {col[keys]}")

print("\n2. Sample Objects Custom Properties & Names:")
objects_with_props = 0
named_buildings = 0

for obj in bpy.data.objects:
    if obj.type == 'MESH':
        custom_keys = [k for k in obj.keys() if k not in ["_RNA_UI", "cycles"]]
        if custom_keys:
            objects_with_props += 1
            if objects_with_props <= 10:
                print(f"  Object '{obj.name}' custom props: {custom_keys}")
                for k in custom_keys:
                    print(f"    {k} = {obj[k]}")
        # Check if name is descriptive (not just Mesh_XX)
        if not obj.name.startswith("Mesh_"):
            named_buildings += 1
            if named_buildings <= 10:
                print(f"  Named object: '{obj.name}'")

print(f"\nTotal Mesh Objects: {len(bpy.data.objects)}")
print(f"Objects with custom properties: {objects_with_props}")
print(f"Objects with non-Mesh_ names: {named_buildings}")
print("=" * 60)
