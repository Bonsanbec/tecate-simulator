import bpy
import json
import mathutils

bpy.ops.wm.open_mainfile(filepath="models/tecate/osm2world.blend")

excluded_materials = {
    'ASPHALT', 'ASPHALT.001', 'EARTH', 'GRAVEL', 'HEDGE', 
    'helipad_markings', 'PAVING_STONE', 'pitchTennis', 
    'RAIL_BALLAST', 'road_arrow_right', 'road_arrow_through', 
    'ROAD_MARKING', 'ROAD_MARKING.001', 'road_marking_crossing', 
    'road_marking_dash', 'RUNWAY_CENTER_MARKING', 'SAND', 
    'SCREE', 'TENNIS_NET', 'TERRAIN_DEFAULT', 'WATER'
}

original_collection = bpy.data.collections.get("Collection")
building_objs = []
for obj in original_collection.objects:
    if obj.type == 'MESH':
        is_excluded = False
        if len(obj.material_slots) == 0:
            is_excluded = True
        else:
            for slot in obj.material_slots:
                if slot.material and slot.material.name in excluded_materials:
                    is_excluded = True
                    break
        if not is_excluded:
            building_objs.append(obj)

print(f"Total building objects: {len(building_objs)}")

# Inspect first 10 building objects
for i, obj in enumerate(building_objs[:10]):
    print(f"Obj {i}: Name='{obj.name}', Loc={obj.location}, CustomProps={list(obj.keys())}")
    for k in obj.keys():
        if k not in ['_RNA_UI']:
            print(f"  {k} = {obj[k]}")
    mats = [s.material.name for s in obj.material_slots if s.material]
    print(f"  Materials: {mats}")

