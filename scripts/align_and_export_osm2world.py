import bpy
import mathutils
import os

# Configuration
glb_source = "models/tecate/osm2world.blend"
output_dir = "godot_project/assets/blocks"
translation = mathutils.Vector((34975.75, -31878.95, 0.0))

print("=" * 60)
print("  OSM2WORLD BUILDING ALIGNMENT & GLTF EXPORT PIPELINE")
print("=" * 60)

# Create output directory
os.makedirs(output_dir, exist_ok=True)

# 1. Open the OSM2World blend file
if not os.path.exists(glb_source):
    print(f"Error: Source file {glb_source} does not exist.")
    exit(1)
    
print(f"[1/4] Loading {glb_source}...")
bpy.ops.wm.open_mainfile(filepath=glb_source)

# 2. Identify non-building objects to prune
# Materials representing roads, terrain, water, foliage, etc.
excluded_materials = {
    'ASPHALT', 'ASPHALT.001', 'EARTH', 'GRAVEL', 'HEDGE', 
    'helipad_markings', 'PAVING_STONE', 'pitchTennis', 
    'RAIL_BALLAST', 'road_arrow_right', 'road_arrow_through', 
    'ROAD_MARKING', 'ROAD_MARKING.001', 'road_marking_crossing', 
    'road_marking_dash', 'RUNWAY_CENTER_MARKING', 'SAND', 
    'SCREE', 'TENNIS_NET', 'TERRAIN_DEFAULT', 'WATER'
}

print("[2/4] Identifying and selecting building objects...")
original_collection = bpy.data.collections.get("Collection")

# Deselect everything first
bpy.ops.object.select_all(action='DESELECT')

building_objs = []
pruned_count = 0

for obj in original_collection.objects:
    if obj.type != 'MESH':
        pruned_count += 1
        continue
        
    is_excluded = False
    if len(obj.material_slots) == 0:
        is_excluded = True
    else:
        for slot in obj.material_slots:
            if slot.material and slot.material.name in excluded_materials:
                is_excluded = True
                break
                
    if is_excluded:
        pruned_count += 1
    else:
        obj.select_set(True)
        building_objs.append(obj)

print(f"  Selected {len(building_objs)} building objects.")
print(f"  Skipped {pruned_count} non-building/excluded objects.")

# 3. Translate selected building meshes to the reconstruction coordinate space
print(f"[3/4] Translating building meshes by {translation}...")
for obj in building_objs:
    obj.location += translation

# Force scene update
bpy.context.view_layer.update()

# 4. Export scene to optimized GLTF
gltf_paths = [
    os.path.join(output_dir, "geometry.gltf"),
    os.path.join(output_dir, "geometry_textureless.gltf")
]

print("[4/4] Exporting selected building meshes to glTF format...")
for gp in gltf_paths:
    print(f"  Exporting to: {gp}")
    try:
        # Export as separate GLTF using selection
        bpy.ops.export_scene.gltf(
            filepath=gp,
            export_format='GLTF_SEPARATE',
            export_copyright="OSM2World Tecate Buildings",
            export_texcoords=True,
            export_normals=True,
            export_materials='EXPORT',
            export_image_format='AUTO',
            export_extras=True,
            use_selection=True
        )
        print(f"  Successfully exported: {gp}")
    except Exception as e:
        print(f"  [Error] Failed to export glTF: {e}")

print("=" * 60)
print("  Alignment & Export Pipeline Complete!")
print("=" * 60)
