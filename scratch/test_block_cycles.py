import os
import json
import networkx as nx
from src.gis_graph.graph_builder import TecateGraphBuilder
from src.reconstruction.prism_generator import UrbanBlockReconstructor

def test_cycles():
    # Load road graph from OSM cache
    builder = TecateGraphBuilder(cache_dir="data")
    osm_data = builder.fetch_osm_tecate()
    G = builder.build_networkx_graph(osm_data)
    
    # Initialize reconstructor
    reconstructor = UrbanBlockReconstructor(G, data_dir="data")
    
    # We will override reconstructor.extract_block_polygons locally to test without pruning
    def extract_without_pruning():
        print("[Reconstruction Test] Running without recursive dead-end pruning...")
        temp_G = nx.Graph(reconstructor.G)
        
        # ONLY remove completely isolated nodes (degree == 0)
        nodes_to_remove = [n for n in temp_G.nodes() if temp_G.degree(n) == 0]
        temp_G.remove_nodes_from(nodes_to_remove)
        
        print(f"[Reconstruction Test] Nodes: {temp_G.number_of_nodes()}, Edges: {temp_G.number_of_edges()}")
        
        sorted_neighbors = {}
        for u in temp_G.nodes():
            neighbors = list(temp_G.neighbors(u))
            ux, uy = temp_G.nodes[u]["x"], temp_G.nodes[u]["y"]
            
            def get_angle(v):
                import math
                vx, vy = temp_G.nodes[v]["x"], temp_G.nodes[v]["y"]
                return math.atan2(vy - uy, vx - ux)
                
            neighbors.sort(key=get_angle)
            sorted_neighbors[u] = neighbors
            
        half_edges = []
        for u, v in temp_G.edges():
            half_edges.append((u, v))
            half_edges.append((v, u))
            
        visited = set()
        blocks = []
        block_counter = 0
        
        for u, v in half_edges:
            if (u, v) not in visited:
                loop = [u]
                curr_u, curr_v = u, v
                
                while (curr_u, curr_v) not in visited:
                    visited.add((curr_u, curr_v))
                    loop.append(curr_v)
                    
                    neighbors = sorted_neighbors[curr_v]
                    try:
                        idx = neighbors.index(curr_u)
                        next_v = neighbors[(idx + 1) % len(neighbors)]
                        curr_u, curr_v = curr_v, next_v
                    except ValueError:
                        break
                        
                if len(loop) >= 4:
                    x = [temp_G.nodes[n]["x"] for n in loop]
                    y = [temp_G.nodes[n]["y"] for n in loop]
                    signed_area = 0.5 * sum(x[i] * y[(i+1)%len(loop)] - x[(i+1)%len(loop)] * y[i] for i in range(len(loop)))
                    
                    if 50.0 < abs(signed_area) < 2500000.0:
                        poly_verts = [(temp_G.nodes[n]["x"], temp_G.nodes[n]["y"]) for n in loop]
                        if signed_area < 0:
                            poly_verts.reverse()
                            
                        blocks.append({
                            "block_id": f"block_{block_counter}",
                            "polygon": poly_verts,
                            "area_sq_meters": abs(signed_area)
                        })
                        block_counter += 1
        return blocks

    blocks = extract_without_pruning()
    
    print(f"\nTotal blocks detected: {len(blocks)}")
    
    # Find block_19
    b19 = None
    for b in blocks:
        if b["block_id"] == "block_19":
            b19 = b
            break
            
    if b19:
        poly = b19["polygon"]
        area = b19["area_sq_meters"]
        print(f"\nBlock 19 Details:")
        print(f"Area: {area:.2f} sq meters")
        print(f"Number of vertices: {len(poly)}")
        print("Vertices:")
        for idx, pt in enumerate(poly[:15]):
            print(f"  [{idx}] ({pt[0]:.2f}, {pt[1]:.2f})")
        if len(poly) > 15:
            print(f"  ... and {len(poly) - 15} more vertices.")
            
        # Let's see if there are other blocks near the Bancomer target coordinates
        target_x = -69.1
        target_y = 28.3
        print(f"\nBancomer Target Local Coordinates: ({target_x:.2f}, {target_y:.2f})")
        
        # Print the closest 5 blocks to target coordinates
        distances = []
        for b in blocks:
            poly = b["polygon"]
            centroid_x = sum(pt[0] for pt in poly[:-1]) / (len(poly) - 1)
            centroid_y = sum(pt[1] for pt in poly[:-1]) / (len(poly) - 1)
            dist = ((centroid_x - target_x)**2 + (centroid_y - target_y)**2)**0.5
            distances.append((b["block_id"], (centroid_x, centroid_y), dist, len(poly), b["area_sq_meters"]))
            
        distances.sort(key=lambda x: x[2])
        print("\nClosest 5 blocks to Bancomer:")
        for b_id, cent, dist, num_v, b_area in distances[:5]:
            print(f"ID: {b_id}, Centroid: ({cent[0]:.2f}, {cent[1]:.2f}), Distance: {dist:.2f}m, Vertices: {num_v}, Area: {b_area:.2f} sq m")

if __name__ == "__main__":
    test_cycles()
