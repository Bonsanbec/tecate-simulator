import json
import networkx as nx

with open("data/tecate_osm_cache.json", "r", encoding="utf-8") as f:
    raw_data = json.load(f)

# Build the networkx graph
from src.gis_graph.graph_builder import TecateGraphBuilder
builder = TecateGraphBuilder(cache_dir="data")
G = builder.build_networkx_graph(raw_data)

# Run pruning
temp_G = nx.Graph(G)
changed = True
while changed:
    changed = False
    nodes_to_remove = [n for n in temp_G.nodes() if temp_G.degree(n) < 2]
    if nodes_to_remove:
        temp_G.remove_nodes_from(nodes_to_remove)
        changed = True

print(f"Original Graph nodes: {G.number_of_nodes()}, edges: {G.number_of_edges()}")
print(f"Pruned Graph nodes: {temp_G.number_of_nodes()}, edges: {temp_G.number_of_edges()}")

street_keywords = ["Juárez", "Libertad", "Revolución", "Támesis"]

for kw in street_keywords:
    print(f"\n=================== STREET: {kw} ===================")
    orig_edges = []
    pruned_edges = []
    
    # In G (original)
    for u, v, key, data in G.edges(keys=True, data=True):
        if kw in data.get("name", ""):
            orig_edges.append((u, v, data.get("name")))
            
    # In temp_G (pruned)
    for u, v, data in temp_G.edges(data=True):
        if kw in data.get("name", ""):
            pruned_edges.append((u, v, data.get("name")))
            
    print(f"Original edges containing '{kw}': {len(orig_edges)}")
    for idx, (u, v, name) in enumerate(orig_edges[:10]):
        u_deg = G.degree(u)
        v_deg = G.degree(v)
        print(f"  Edge {idx}: {u}(deg={u_deg}) -> {v}(deg={v_deg}) | Name='{name}'")
    if len(orig_edges) > 10:
        print(f"  ... and {len(orig_edges) - 10} more.")
        
    print(f"Pruned edges containing '{kw}': {len(pruned_edges)}")
    for idx, (u, v, name) in enumerate(pruned_edges[:10]):
        u_deg_pr = temp_G.degree(u)
        v_deg_pr = temp_G.degree(v)
        print(f"  Pruned Edge {idx}: {u}(deg={u_deg_pr}) -> {v}(deg={v_deg_pr}) | Name='{name}'")
    if len(pruned_edges) > 10:
        print(f"  ... and {len(pruned_edges) - 10} more.")
