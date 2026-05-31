import json
import networkx as nx

with open("data/tecate_osm_cache.json", "r", encoding="utf-8") as f:
    raw_data = json.load(f)

from src.gis_graph.graph_builder import TecateGraphBuilder
builder = TecateGraphBuilder(cache_dir="data")
G = builder.build_networkx_graph(raw_data)

# Let's inspect edges of Avenida Revolución that connect or do not connect to Avenida Benito Juárez
revolucion_nodes = []
for u, v, key, data in G.edges(keys=True, data=True):
    name = data.get("name", "")
    if "revolución" in name.lower():
        revolucion_nodes.extend([u, v])
        
revolucion_nodes = set(revolucion_nodes)
print(f"Total nodes in Avenida Revolución: {len(revolucion_nodes)}")

# Let's print their degrees and if they connect to Juárez
juarez_nodes = []
for u, v, key, data in G.edges(keys=True, data=True):
    name = data.get("name", "")
    if "juárez" in name.lower():
        juarez_nodes.extend([u, v])
juarez_nodes = set(juarez_nodes)

print(f"Total nodes in Avenida Benito Juárez: {len(juarez_nodes)}")

connections = revolucion_nodes.intersection(juarez_nodes)
print(f"Nodes in intersection of Revolución and Juárez: {connections}")

for nid in connections:
    data = G.nodes[nid]
    print(f"  Connection node: {nid}, coordinates=({data['lat']:.6f}, {data['lon']:.6f}), degree in G={G.degree(nid)}")
    # Print neighbors and street names
    for neighbor in G.neighbors(nid):
        edge_data = G.get_edge_data(nid, neighbor)
        # edge_data is a dict because G is a MultiGraph
        for k, d in edge_data.items():
            print(f"    -> Neighbor {neighbor}: name='{d.get('name')}'")
