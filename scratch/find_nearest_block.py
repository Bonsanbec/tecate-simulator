import sys
import os
import math
import networkx as nx

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.gis_graph.graph_builder import TecateGraphBuilder
from src.reconstruction.prism_generator import UrbanBlockReconstructor
from src.core_io.coords import gps_to_local, local_to_gps

def find_block():
    target_lat = 32.573484
    target_lon = -116.627276
    
    print(f"Target Coordinates (Bancomer): {target_lat}, {target_lon}")
    target_x, target_y = gps_to_local(target_lat, target_lon)
    print(f"Local Metric Coordinates: {target_x}, {target_y}")
    
    builder = TecateGraphBuilder(cache_dir="data")
    osm_data = builder.fetch_osm_tecate()
    G = builder.build_networkx_graph(osm_data)
    
    reconstructor = UrbanBlockReconstructor(G, data_dir="data")
    blocks = reconstructor.extract_block_polygons()
    
    # Find the block whose centroid or polygon vertices are closest to the target
    closest_block = None
    min_dist = float("inf")
    
    for block in blocks:
        poly = block["polygon"]
        # Compute centroid
        cx = sum(pt[0] for pt in poly[:-1]) / (len(poly) - 1)
        cy = sum(pt[1] for pt in poly[:-1]) / (len(poly) - 1)
        
        dist = math.sqrt((cx - target_x)**2 + (cy - target_y)**2)
        if dist < min_dist:
            min_dist = dist
            closest_block = block
            
    if closest_block:
        print("\nClosest Block to Bancomer:")
        print(f"Block ID: {closest_block['block_id']}")
        print(f"Centroid Distance: {min_dist:.2f} meters")
        print("Polygon Vertices (GPS):")
        for pt in closest_block["polygon"]:
            lat, lon = local_to_gps(pt[0], pt[1])
            print(f"  ({lat:.6f}, {lon:.6f}) -> metric ({pt[0]:.2f}, {pt[1]:.2f})")
            
        # Find roads next to this block
        print("\nAdjacent Road Segments:")
        for i in range(len(closest_block["polygon"]) - 1):
            A = closest_block["polygon"][i]
            B = closest_block["polygon"][i+1]
            mx = (A[0] + B[0]) / 2.0
            my = (A[1] + B[1]) / 2.0
            road_dist, edge_id = reconstructor.get_road_distance(mx, my)
            print(f"  Facade {i}: Midpoint=({mx:.2f}, {my:.2f}), Closest Road Dist={road_dist:.2f}m, Edge ID={edge_id}")
            
if __name__ == "__main__":
    find_block()
