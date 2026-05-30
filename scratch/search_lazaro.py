import os
import json
import networkx as nx
from src.gis_graph.graph_builder import TecateGraphBuilder

def search_lazaro():
    builder = TecateGraphBuilder(cache_dir="data")
    osm_data = builder.fetch_osm_tecate()
    G = builder.build_networkx_graph(osm_data)
    
    print("Searching for streets containing 'Lázaro' or 'Cárdenas' in the graph:")
    found = 0
    for u, v, data in G.edges(data=True):
        name = data.get("name", "")
        if "lázaro" in name.lower() or "cárdenas" in name.lower():
            print(f"  Edge: {data['id']}, Name: '{name}', U: {u}, V: {v}")
            found += 1
            
    print(f"\nFound {found} matching edges in G.")

if __name__ == "__main__":
    search_lazaro()
