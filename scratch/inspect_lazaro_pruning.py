import os
import json
import networkx as nx
from src.gis_graph.graph_builder import TecateGraphBuilder

def inspect_lazaro_pruning():
    builder = TecateGraphBuilder(cache_dir="data")
    osm_data = builder.fetch_osm_tecate()
    G = builder.build_networkx_graph(osm_data)
    
    nodes_of_interest = ["5284817711", "8801830527", "317525956"]
    
    print("Coordinates and Degrees in original G:")
    for n in nodes_of_interest:
        if n in G:
            data = G.nodes[n]
            deg = G.degree(n)
            print(f"  Node: {n}, Coord: ({data['x']:.2f}, {data['y']:.2f}), Degree: {deg}")
        else:
            print(f"  Node: {n} NOT in G!")
            
    # Simulate dead-end pruning
    temp_G = nx.Graph(G)
    print("\nSimulating dead-end pruning on nx.Graph...")
    
    # Degree before pruning
    for n in nodes_of_interest:
        if n in temp_G:
            print(f"  Node {n} degree in simple graph: {temp_G.degree(n)}")
            
    changed = True
    iteration = 0
    while changed:
        changed = False
        nodes_to_remove = [n for n in temp_G.nodes() if temp_G.degree(n) < 2]
        if nodes_to_remove:
            # Check if any of our nodes are being removed in this step
            for n in nodes_of_interest:
                if n in nodes_to_remove:
                    print(f"  ---> Iteration {iteration}: Removing node {n} (Degree: {temp_G.degree(n)})")
            temp_G.remove_nodes_from(nodes_to_remove)
            changed = True
            iteration += 1
            
    print(f"\nFinal state in pruned graph:")
    for n in nodes_of_interest:
        print(f"  Node {n} in pruned graph: {n in temp_G}")

if __name__ == "__main__":
    inspect_lazaro_pruning()
