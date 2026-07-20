import bpy
import mathutils
import time
import os

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

print(f"Total buildings: {len(building_objs)}")

# Translate
translation = mathutils.Vector((34975.75, -31878.95, 0.0))
for obj in building_objs:
    obj.location += translation
bpy.context.view_layer.update()

# Test export of 20 buildings
test_dir = os.path.abspath("scratch/test_buildings_export")
os.makedirs(test_dir, exist_ok=True)

start_time = time.time()
for i in range(20):
    obj = building_objs[i]
    # Select only this object
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    
    # Export
    filepath = os.path.join(test_dir, f"{obj.name}.gltf")
    bpy.ops.export_scene.gltf(
        filepath=filepath,
        export_format='GLTF_SEPARATE',
        use_selection=True
    )

elapsed = time.time() - start_time
print(f"Exported 20 buildings in {elapsed:.4f} seconds.")
print(f"Average time per building: {elapsed/20:.4f} seconds.")
print(f"Estimated time for 4,177 buildings: {elapsed/20 * 4177 / 60:.2f} minutes.")
