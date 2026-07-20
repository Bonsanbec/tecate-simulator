import bpy
import mathutils
import os
import sys

log_path = os.path.abspath("scratch/test_join_export_run.log")
log_f = open(log_path, "w")

def log_print(msg):
    log_f.write(str(msg) + "\n")
    log_f.flush()
    print(msg)

log_print("Starting script...")

try:
    log_print("Opening blend file...")
    bpy.ops.wm.open_mainfile(filepath="models/tecate/osm2world.blend")
    log_print("Blend file loaded successfully.")
    
    excluded_materials = {
        'ASPHALT', 'ASPHALT.001', 'EARTH', 'GRAVEL', 'HEDGE', 
        'helipad_markings', 'PAVING_STONE', 'pitchTennis', 
        'RAIL_BALLAST', 'road_arrow_right', 'road_arrow_through', 
        'ROAD_MARKING', 'ROAD_MARKING.001', 'road_marking_crossing', 
        'road_marking_dash', 'RUNWAY_CENTER_MARKING', 'SAND', 
        'SCREE', 'TENNIS_NET', 'TERRAIN_DEFAULT', 'WATER'
    }

    original_collection = bpy.data.collections.get("Collection")
    if not original_collection:
        log_print("Error: Collection 'Collection' not found!")
        sys.exit(1)
        
    # 1. Identify building objects
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

    log_print(f"Total building objects found: {len(building_objs)}")

    # Group by material name
    mat_groups = {}
    for obj in building_objs:
        mat_name = "default"
        if len(obj.material_slots) > 0 and obj.material_slots[0].material:
            mat_name = obj.material_slots[0].material.name
        if mat_name not in mat_groups:
            mat_groups[mat_name] = []
        mat_groups[mat_name].append(obj)

    log_print(f"Grouped into {len(mat_groups)} material groups.")

    # Create a new collection for joined objects
    new_collection = bpy.data.collections.new("JoinedBuildings")
    bpy.context.scene.collection.children.link(new_collection)

    joined_objs = []

    for mat_name, objs in mat_groups.items():
        log_print(f"  Joining group '{mat_name}' with {len(objs)} objects...")
        if len(objs) == 1:
            new_collection.objects.link(objs[0])
            joined_objs.append(objs[0])
            continue
            
        bpy.ops.object.select_all(action='DESELECT')
        for obj in objs:
            obj.select_set(True)
            
        bpy.context.view_layer.objects.active = objs[0]
        bpy.ops.object.join()
        
        joined_obj = bpy.context.view_layer.objects.active
        joined_obj.name = f"combined_{mat_name}"
        
        # Move to new collection
        for col in list(joined_obj.users_collection):
            col.objects.unlink(joined_obj)
        new_collection.objects.link(joined_obj)
        joined_objs.append(joined_obj)

    # Unlink original collection
    bpy.context.scene.collection.children.unlink(original_collection)

    log_print(f"Pruning and joining complete. Active objects: {len(bpy.context.scene.objects)}")

    # Translate
    translation = mathutils.Vector((34975.75, -31878.95, 0.0))
    for obj in joined_objs:
        obj.location += translation

    bpy.context.view_layer.update()

    # Export test
    out_path = os.path.abspath("godot_project/assets/blocks/geometry.gltf")
    log_print(f"Exporting to: {out_path}")
    bpy.ops.export_scene.gltf(
        filepath=out_path,
        export_format='GLTF_SEPARATE',
        use_selection=False
    )
    log_print("Export finished successfully!")

except Exception as e:
    log_print(f"ERROR OCCURRED: {e}")
    import traceback
    traceback.print_exc(file=log_f)
    log_f.flush()
finally:
    log_f.close()
    print("Script finished.")
