import json
import math
import networkx as nx
from src.gis_graph.graph_builder import TecateGraphBuilder

builder = TecateGraphBuilder(cache_dir="data")
osm_data = builder.fetch_osm_tecate()
G = builder.build_networkx_graph(osm_data)

temp_G = nx.Graph(G)

# Trim dead-ends
changed = True
while changed:
    changed = False
    nodes_to_remove = [n for n in temp_G.nodes() if temp_G.degree(n) < 2]
    if nodes_to_remove:
        temp_G.remove_nodes_from(nodes_to_remove)
        changed = True

print(f"Nodes: {temp_G.number_of_nodes()}, Edges: {temp_G.number_of_edges()}")

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
loops = []
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
            loops.append((loop, signed_area))

print(f"Traced {len(loops)} loops total.")
for idx, (loop, area) in enumerate(loops[:20]):
    print(f"Loop {idx}: len={len(loop)}, area={area}")
