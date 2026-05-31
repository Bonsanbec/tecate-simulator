import json
import math
import networkx as nx
from src.gis_graph.graph_builder import TecateGraphBuilder
from src.reconstruction.prism_generator import UrbanBlockReconstructor

# Load road graph from OSM cache
builder = TecateGraphBuilder(cache_dir="data")
osm_data = builder.fetch_osm_tecate()
G = builder.build_networkx_graph(osm_data)

reconstructor = UrbanBlockReconstructor(G, data_dir="data")

print("1. Testing cycle extraction with unpruned graph...")
# ONLY remove isolated nodes
temp_G = nx.Graph(reconstructor.G)
nodes_to_remove = [n for n in temp_G.nodes() if temp_G.degree(n) == 0]
temp_G.remove_nodes_from(nodes_to_remove)

sorted_neighbors = {}
for u in temp_G.nodes():
    neighbors = list(temp_G.neighbors(u))
    ux, uy = temp_G.nodes[u]["x"], temp_G.nodes[u]["y"]
    def get_angle(v):
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

print(f"Extracted {len(blocks)} blocks from unpruned graph.")

print("\n2. Testing shrink_polygon on all extracted blocks...")
success_count = 0
fail_count = 0

for b in blocks:
    poly = b["polygon"]
    try:
        shrunk = reconstructor.shrink_polygon(poly, d=6.0)
        success_count += 1
    except Exception as e:
        fail_count += 1
        print(f"  Failed to shrink {b['block_id']}: {e}")

print(f"Shrink Results: Successes={success_count}, Failures={fail_count}")
