import bpy
import mathutils
import numpy as np

def get_local_road_vertices_reconstruction():
    bpy.ops.wm.open_mainfile(filepath="tecate_reconstruction_textureless.blend")
    obj = bpy.data.objects.get("RoadNetwork")
    if not obj:
        print("Error: RoadNetwork not found in Reconstruction")
        return np.array([])
        
    matrix = obj.matrix_world
    verts = []
    
    # Filter vertices within 1000m of (0, 0)
    for v in obj.data.vertices:
        world_v = matrix @ v.co
        if abs(world_v.x) < 1000.0 and abs(world_v.y) < 1000.0:
            verts.append((world_v.x, world_v.y))
            
    return np.array(verts)

def get_local_road_vertices_osm2world(approx_center):
    bpy.ops.wm.open_mainfile(filepath="models/tecate/osm2world.blend")
    verts = []
    
    # Find all road objects
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            is_road = False
            for slot in obj.material_slots:
                if slot.material and slot.material.name == 'ASPHALT':
                    is_road = True
                    break
            if is_road:
                matrix = obj.matrix_world
                # Quick bounding box check to see if it could overlap with our 1000m region
                bbox_corners = [matrix @ mathutils.Vector(corner) for corner in obj.bound_box]
                min_x = min(c.x for c in bbox_corners)
                max_x = max(c.x for c in bbox_corners)
                min_y = min(c.y for c in bbox_corners)
                max_y = max(c.y for c in bbox_corners)
                
                # Check if it overlaps with [approx_center - 1100, approx_center + 1100]
                if max_x < approx_center[0] - 1100.0 or min_x > approx_center[0] + 1100.0 or \
                   max_y < approx_center[1] - 1100.0 or min_y > approx_center[1] + 1100.0:
                    continue
                    
                # Extract vertices inside the region
                for v in obj.data.vertices:
                    world_v = matrix @ v.co
                    if abs(world_v.x - approx_center[0]) < 1000.0 and abs(world_v.y - approx_center[1]) < 1000.0:
                        verts.append((world_v.x, world_v.y))
                        
    return np.array(verts)

# Approx town center in OSM2World
approx_center = (-34975.25, 31823.95)

print("Extracting local road vertices from Reconstruction...")
verts_rec = get_local_road_vertices_reconstruction()
print(f"Extracted {len(verts_rec)} vertices.")

print("Extracting local road vertices from OSM2World...")
verts_osm = get_local_road_vertices_osm2world(approx_center)
print(f"Extracted {len(verts_osm)} vertices.")

if len(verts_rec) == 0 or len(verts_osm) == 0:
    print("Error: Could not extract vertices.")
    exit(1)

# Now, we do a grid search for translation (dX, dY) around the nominal offset:
# nominal dX = approx_center[0] - 0 = -34975.25
# nominal dY = approx_center[1] - 0 = 31823.95
# Wait! In our mapping:
# x_rec = x_osm + dX -> dX = x_rec - x_osm = 0 - (-34975.25) = 34975.25
# y_rec = y_osm + dY -> dY = y_rec - y_osm = 0 - 31823.95 = -31823.95
nominal_dx = -approx_center[0]
nominal_dy = -approx_center[1]

print(f"Nominal translation search center: dX={nominal_dx:.2f}, dY={nominal_dy:.2f}")

# First pass: Coarse search with 20m steps in a 400m window
search_window = 200.0
step_coarse = 10.0
dx_range = np.arange(nominal_dx - search_window, nominal_dx + search_window, step_coarse)
dy_range = np.arange(nominal_dy - search_window, nominal_dy + search_window, step_coarse)

best_dx = nominal_dx
best_dy = nominal_dy
min_score = float('inf')

# Downsample points to make matching extremely fast
downsample_rec = verts_rec[::10]
downsample_osm = verts_osm[::10]

print("Running coarse grid search...")
for dx in dx_range:
    for dy in dy_range:
        # Translate OSM points
        trans_osm = downsample_osm + np.array([dx, dy])
        
        # Calculate sum of squared distances to closest points
        # For speed, we just compute distance for each point to nearest neighbor in a subset
        total_dist = 0
        for p in downsample_rec[:100]: # Check 100 points
            d = np.linalg.norm(trans_osm - p, axis=1)
            total_dist += np.min(d)
            
        if total_dist < min_score:
            min_score = total_dist
            best_dx = dx
            best_dy = dy

print(f"Coarse search result: dX={best_dx:.2f}, dY={best_dy:.2f}")

# Second pass: Fine search with 0.5m steps in a 25m window around coarse result
fine_window = 20.0
step_fine = 0.5
dx_range_fine = np.arange(best_dx - fine_window, best_dx + fine_window, step_fine)
dy_range_fine = np.arange(best_dy - fine_window, best_dy + fine_window, step_fine)

min_score_fine = float('inf')
fine_dx = best_dx
fine_dy = best_dy

print("Running fine grid search...")
for dx in dx_range_fine:
    for dy in dy_range_fine:
        trans_osm = downsample_osm + np.array([dx, dy])
        total_dist = 0
        for p in downsample_rec[:200]: # Check 200 points
            d = np.linalg.norm(trans_osm - p, axis=1)
            total_dist += np.min(d)
            
        if total_dist < min_score_fine:
            min_score_fine = total_dist
            fine_dx = dx
            fine_dy = dy

print(f"Fine search result: dX={fine_dx:.4f}, dY={fine_dy:.4f}")

# Final verification of matched points median distance
trans_osm = verts_osm + np.array([fine_dx, fine_dy])
dists = []
for p in verts_rec[::5]:
    d = np.linalg.norm(trans_osm - p, axis=1)
    dists.append(np.min(d))

print(f"\n--- FINAL ALIGNMENT ---")
print(f"  Translation dX: {fine_dx:.4f}m")
print(f"  Translation dY: {fine_dy:.4f}m")
print(f"  Median road alignment error: {np.median(dists):.4f}m")
