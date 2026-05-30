import os
import json
import networkx as nx
from src.gis_graph.graph_builder import TecateGraphBuilder

def inspect_streets():
    builder = TecateGraphBuilder(cache_dir="data")
    osm_data = builder.fetch_osm_tecate()
    G = builder.build_networkx_graph(osm_data)
    
    print("Listing all edges in G within the Bancomer block region:")
    print("x range: [-250, 50], y range: [0, 200]\n")
    
    found_edges = []
    for u, v, data in G.edges(data=True):
        ux, uy = G.nodes[u]["x"], G.nodes[u]["y"]
        vx, vy = G.nodes[v]["x"], G.nodes[v]["y"]
        
        # Check if edge is within or crosses the region
        in_u = (-250 <= ux <= 50) and (0 <= uy <= 200)
        in_v = (-250 <= vx <= 50) and (0 <= vy <= 200)
        
        if in_u or in_v:
            found_edges.append((data["id"], data["name"], (ux, uy), (vx, vy)))
            
    print(f"Found {len(found_edges)} road segments in this region:")
    for ed_id, name, p1, p2 in found_edges:
        print(f"  ID: {ed_id}, Name: '{name}', P1: ({p1[0]:.2f}, {p1[1]:.2f}), P2: ({p2[0]:.2f}, {p2[1]:.2f})")

if __name__ == "__main__":
    inspect_streets()
