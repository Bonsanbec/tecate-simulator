import os
import json
import math
import requests
import hashlib
from src.core_io.coords import local_to_gps

def get_edge_key(u, v):
    """Generates a stable, direction-independent key for a road edge."""
    u_str = str(u)
    v_str = str(v)
    return f"{min(u_str, v_str)},{max(u_str, v_str)}"

def get_default_metadata(highway_type=None, name=""):
    """Returns default metadata based on highway type."""
    hw = highway_type or "residential"
    
    # Establish default lanes
    if hw in ["motorway", "motorway_link", "trunk", "trunk_link"]:
        lanes = 3
    elif hw in ["primary", "primary_link", "secondary", "secondary_link", "tertiary", "tertiary_link", "residential", "unclassified"]:
        lanes = 2
    else:
        lanes = 1
        
    # Establish default widths (in meters/blocks)
    if hw in ["motorway", "motorway_link", "trunk", "trunk_link"]:
        width = 12.0
    elif hw in ["primary", "primary_link"]:
        width = 10.0
    elif hw in ["secondary", "secondary_link"]:
        width = 8.0
    elif hw in ["tertiary", "tertiary_link"]:
        width = 7.0
    elif hw in ["residential", "unclassified"]:
        width = 6.0
    elif hw in ["living_street"]:
        width = 5.0
    elif hw in ["service"]:
        width = 4.0
    else:
        width = 4.0
        
    # Establish surface type
    if hw in ["track", "path", "bridleway"]:
        surface = "gravel"
    else:
        surface = "asphalt"
        
    return {
        "highway": hw,
        "lanes": lanes,
        "width": width,
        "surface": surface,
        "service": "",
        "name": name,
        "bridge": "",
        "layer": ""
    }

def extract_and_cache_road_metadata(reconstruction_json_path, output_metadata_path):
    """
    Extracts road metadata from OpenStreetMap for all edges in the reconstruction graph,
    applying fallback rules, and saves the output to a cache file.
    """
    if os.path.exists(output_metadata_path):
        print(f"[RoadMetadataCache] Loading metadata from cache: {output_metadata_path}")
        try:
            with open(output_metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[RoadMetadataCache Warning] Failed to read cache: {e}. Re-extracting...")

    print(f"[RoadMetadataCache] Extracting metadata for {reconstruction_json_path}...")
    try:
        with open(reconstruction_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"[RoadMetadataCache Error] Failed to read reconstruction JSON: {e}")
        return {}

    road_graph = data.get("road_graph", {})
    nodes = road_graph.get("nodes", [])
    edges = road_graph.get("edges", [])

    if not nodes or not edges:
        print("[RoadMetadataCache Warning] Road graph nodes or edges empty. Creating empty cache.")
        empty_cache = {"edges": {}}
        with open(output_metadata_path, 'w', encoding='utf-8') as f:
            json.dump(empty_cache, f, indent=4)
        return empty_cache

    # 1. Calculate active bounding box in GPS coordinates
    lats = []
    lons = []
    for nd in nodes:
        lat, lon = local_to_gps(nd["x"], nd["y"])
        lats.append(lat)
        lons.append(lon)
        
    # Add 0.005 degrees padding (~500m) to ensure way coverage
    min_lat, max_lat = min(lats) - 0.005, max(lats) + 0.005
    min_lon, max_lon = min(lons) - 0.005, max(lons) + 0.005
    
    print(f"[RoadMetadataCache] Active area GPS BBox: ({min_lat:.5f}, {min_lon:.5f}) to ({max_lat:.5f}, {max_lon:.5f})")

    # 2. Query OSM Overpass API
    overpass_url = "https://overpass-api.de/api/interpreter"
    query = f"""[out:json][timeout:60];
(
  way["highway"]({min_lat},{min_lon},{max_lat},{max_lon});
);
out body;
"""
    headers = {
        "User-Agent": "TecateSimulatorMinecraftPipeline/1.0 (contact: hakkindavid@github)"
    }
    
    osm_data = None
    try:
        print("[RoadMetadataCache] Requesting street segment tags from Overpass API...")
        resp = requests.post(overpass_url, data={"data": query}, headers=headers, timeout=45)
        if resp.status_code == 200:
            osm_data = resp.json()
            print("[RoadMetadataCache] Overpass API query successful!")
        else:
            print(f"[RoadMetadataCache Warning] Overpass API failed with status code: {resp.status_code}")
    except Exception as e:
        print(f"[RoadMetadataCache Warning] Overpass API request timed out or failed: {e}")

    # Map mapping node_id -> list of (way_id, tags_dict, way_nodes_list)
    node_to_ways = {}
    
    if osm_data:
        elements = osm_data.get("elements", [])
        for el in elements:
            if el["type"] == "way":
                way_id = str(el["id"])
                tags = el.get("tags", {})
                way_nodes = [str(nid) for nid in el.get("nodes", [])]
                
                # Index nodes
                for nid in way_nodes:
                    node_to_ways.setdefault(nid, []).append((way_id, tags, way_nodes))

    # 3. Match edges to OSM way tags and build the metadata mapping
    metadata_map = {}
    matched_count = 0
    fallback_count = 0

    for ed in edges:
        u = str(ed["u"])
        v = str(ed["v"])
        name = ed.get("name", "")
        edge_key = get_edge_key(u, v)

        matched_tags = None
        
        # Look for a common way containing both u and v
        u_ways = node_to_ways.get(u, [])
        v_ways = node_to_ways.get(v, [])
        
        common_ways = []
        for u_way_id, u_tags, u_nodes in u_ways:
            for v_way_id, v_tags, v_nodes in v_ways:
                if u_way_id == v_way_id:
                    common_ways.append((u_tags, u_nodes))
                    
        if common_ways:
            # Pick the first common way (usually there's only one)
            matched_tags, _ = common_ways[0]
            
        # If no common way, fall back to checking if either node is associated with a way
        if not matched_tags:
            if u_ways:
                matched_tags = u_ways[0][1]
            elif v_ways:
                matched_tags = v_ways[0][1]

        if matched_tags:
            # We found matching tags from OSM!
            hw = matched_tags.get("highway", "residential")
            
            # Lanes parsing
            lanes_val = matched_tags.get("lanes")
            if lanes_val:
                try:
                    # Strip any non-numeric characters
                    lanes_val = "".join(c for c in lanes_val if c.isdigit())
                    lanes = int(lanes_val) if lanes_val else None
                except ValueError:
                    lanes = None
            else:
                lanes = None
                
            # Width parsing
            width_val = matched_tags.get("width")
            if width_val:
                try:
                    # Replace comma with dot and strip non-numeric/non-dot chars
                    width_val = width_val.replace(',', '.')
                    width_val = "".join(c for c in width_val if c.isdigit() or c == '.')
                    width = float(width_val) if width_val else None
                except ValueError:
                    width = None
            else:
                width = None

            # Get default values to fall back on if width/lanes are missing or invalid
            defaults = get_default_metadata(hw, name or matched_tags.get("name", ""))
            
            # Assemble custom metadata with parsed fields falling back to defaults
            metadata_map[edge_key] = {
                "highway": hw,
                "lanes": lanes if lanes is not None else defaults["lanes"],
                "width": width if width is not None else defaults["width"],
                "surface": matched_tags.get("surface", defaults["surface"]),
                "service": matched_tags.get("service", ""),
                "name": name or matched_tags.get("name", defaults["name"]),
                "bridge": matched_tags.get("bridge", ""),
                "layer": matched_tags.get("layer", "")
            }
            matched_count += 1
        else:
            # Apply default fallback metadata
            metadata_map[edge_key] = get_default_metadata(name=name)
            fallback_count += 1

    print(f"[RoadMetadataCache] Matched {matched_count} edges with OSM. Fallback default used for {fallback_count} edges.")

    # 4. Save metadata to cache file
    cache_data = {"edges": metadata_map}
    try:
        os.makedirs(os.path.dirname(output_metadata_path), exist_ok=True)
        with open(output_metadata_path, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=4)
        print(f"[RoadMetadataCache] Saved metadata to {output_metadata_path}")
    except Exception as e:
        print(f"[RoadMetadataCache Error] Failed to write cache: {e}")

    return cache_data
