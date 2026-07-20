import bpy
import mathutils
import numpy as np

def get_building_centroids_reconstruction():
    bpy.ops.wm.open_mainfile(filepath="tecate_reconstruction_textureless.blend")
    centroids = []
    
    for obj in bpy.data.objects:
        # Check if it is a roof mesh
        if obj.type == 'MESH' and obj.name.startswith("roof_block_"):
            # Calculate world-space centroid
            matrix = obj.matrix_world
            if len(obj.data.vertices) > 0:
                local_centroid = sum((v.co for v in obj.data.vertices), mathutils.Vector()) / len(obj.data.vertices)
                world_centroid = matrix @ local_centroid
                centroids.append((world_centroid.x, world_centroid.y))
                
    return np.array(centroids)

def get_building_centroids_osm2world():
    bpy.ops.wm.open_mainfile(filepath="models/tecate/osm2world.blend")
    centroids = []
    
    # Building materials typically used by OSM2World
    building_materials = {'clay', 'Plaster002', 'RoofingTiles010', 'Concrete034', 'Material'}
    
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            # Filter out road network, terrain, or rails (which are very large or have many vertices)
            if len(obj.data.vertices) > 500:
                continue
                
            is_building = False
            for slot in obj.material_slots:
                if slot.material and slot.material.name in building_materials:
                    is_building = True
                    break
            
            if is_building:
                matrix = obj.matrix_world
                if len(obj.data.vertices) > 0:
                    local_centroid = sum((v.co for v in obj.data.vertices), mathutils.Vector()) / len(obj.data.vertices)
                    world_centroid = matrix @ local_centroid
                    centroids.append((world_centroid.x, world_centroid.y))
                    
    return np.array(centroids)

print("Extracting centroids from Reconstruction...")
pts_rec = get_building_centroids_reconstruction()
print(f"Extracted {len(pts_rec)} building centroids from Reconstruction.")

print("\nExtracting centroids from OSM2World...")
pts_osm = get_building_centroids_osm2world()
print(f"Extracted {len(pts_osm)} building centroids from OSM2World.")

if len(pts_rec) == 0 or len(pts_osm) == 0:
    print("Error: Could not extract centroids from one or both files.")
    exit(1)

# Now, we want to find translation (dx, dy) and scale s such that:
# pts_rec = s * pts_osm + [dx, dy]
# Since we know both represent the same town center, let's normalize by their mean and standard deviation to find scale and rough offset
mean_rec = np.mean(pts_rec, axis=0)
std_rec = np.std(pts_rec, axis=0)

mean_osm = np.mean(pts_osm, axis=0)
std_osm = np.std(pts_osm, axis=0)

print("\n--- Statistics ---")
print(f"Reconstruction Center (Mean): {mean_rec}")
print(f"Reconstruction Std Dev: {std_rec}")
print(f"OSM2World Center (Mean): {mean_osm}")
print(f"OSM2World Std Dev: {std_osm}")

# Rough estimate of scale based on standard deviation
s_est_x = std_rec[0] / std_osm[0]
s_est_y = std_rec[1] / std_osm[1]
s_est = (s_est_x + s_est_y) / 2.0
print(f"Rough Scale Estimate: X={s_est_x:.6f}, Y={s_est_y:.6f}, Mean={s_est:.6f}")

# Rough translation estimate
dx_est = mean_rec[0] - s_est * mean_osm[0]
dy_est = mean_rec[1] - s_est * mean_osm[1]
print(f"Rough Offset Estimate: dX={dx_est:.4f}m, dY={dy_est:.4f}m")

# Refined matching:
# For a range of scale factors around s_est, we'll find translation by matching closest points
# We'll use a grid search to find the scale and offset that minimizes the median distance of matched pairs.
best_s = 1.0
best_dx = 0.0
best_dy = 0.0
min_median_dist = float('inf')

# Test scale factors from 0.8 * s_est to 1.2 * s_est
scales_to_test = np.linspace(s_est * 0.9, s_est * 1.1, 41)

# Include exactly 1.0 (unscaled) as a key test
if 1.0 not in scales_to_test:
    scales_to_test = np.append(scales_to_test, 1.0)
    
for s in sorted(scales_to_test):
    # Scale OSM points
    scaled_osm = pts_osm * s
    # Center of scaled OSM points
    scaled_mean_osm = np.mean(scaled_osm, axis=0)
    # Estimate offset to align centers
    dx = mean_rec[0] - scaled_mean_osm[0]
    dy = mean_rec[1] - scaled_mean_osm[1]
    
    # Translate scaled OSM points
    aligned_osm = scaled_osm + np.array([dx, dy])
    
    # Calculate nearest neighbor distance for each Reconstruction point to aligned OSM points
    dists = []
    for p in pts_rec:
        # Distance to all aligned OSM points
        d = np.linalg.norm(aligned_osm - p, axis=1)
        dists.append(np.min(d))
        
    median_dist = np.median(dists)
    if median_dist < min_median_dist:
        min_median_dist = median_dist
        best_s = s
        best_dx = dx
        best_dy = dy

print("\n--- Best Alignment Parameters (Median Closest-Point Distance) ---")
print(f"  Scale Factor s: {best_s:.6f} (Scale is {'1:1' if abs(best_s - 1.0) < 0.01 else 'NOT 1:1'})")
print(f"  Translation dX: {best_dx:.4f}m")
print(f"  Translation dY: {best_dy:.4f}m")
print(f"  Median distance between aligned buildings: {min_median_dist:.4f}m")

# Test specifically for s = 1.0 (since map data should theoretically be 1:1 scale)
scaled_osm = pts_osm * 1.0
scaled_mean_osm = np.mean(scaled_osm, axis=0)
dx_1 = mean_rec[0] - scaled_mean_osm[0]
dy_1 = mean_rec[1] - scaled_mean_osm[1]
aligned_osm = scaled_osm + np.array([dx_1, dy_1])
dists_1 = [np.min(np.linalg.norm(aligned_osm - p, axis=1)) for p in pts_rec]
median_dist_1 = np.median(dists_1)

print("\n--- Force 1:1 Scale Alignment Parameters ---")
print(f"  Scale Factor s: 1.000000")
print(f"  Translation dX: {dx_1:.4f}m")
print(f"  Translation dY: {dy_1:.4f}m")
print(f"  Median distance between aligned buildings: {median_dist_1:.4f}m")
