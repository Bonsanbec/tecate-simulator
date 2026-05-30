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
    target_x, target_y = gps_to_local(target_lat, target_lon)
    
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
        cx = sum(pt[0] for pt in poly[:-1]) / (len(poly) - 1)
        cy = sum(pt[1] for pt in poly[:-1]) / (len(poly) - 1)
        
        dist = math.sqrt((cx - target_x)**2 + (cy - target_y)**2)
        if dist < min_dist:
            min_dist = dist
            closest_block = block
            
    if closest_block:
        print(f"Closest Block ID: {closest_block['block_id']}")
        print(f"Centroid: {closest_block['centroid'] if 'centroid' in closest_block else 'not computed'}")
        print(f"Number of vertices: {len(closest_block['polygon'])}")
            
if __name__ == "__main__":
    find_block()
