import os
import json
import requests
from src.core_io.coords import local_to_gps, gps_to_local

def extract_and_cache_terrain_classification(reconstruction_json_path, output_json_path):
    """
    Downloads landuse and natural features from OpenStreetMap for the reconstruction area,
    classifies them, projects them, and saves the output cache.
    """
    if os.path.exists(output_json_path):
        print(f"[TerrainClassifier] Loading classification from cache: {output_json_path}")
        try:
            with open(output_json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[TerrainClassifier Warning] Failed to read cache: {e}. Re-extracting...")

    print(f"[TerrainClassifier] Extracting classification for {reconstruction_json_path}...")
    try:
        with open(reconstruction_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"[TerrainClassifier Error] Failed to read reconstruction JSON: {e}")
        return []

    blocks = data.get("blocks", [])
    if not blocks:
        print("[TerrainClassifier Warning] No blocks found in reconstruction JSON. Creating empty classification.")
        empty_data = []
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(empty_data, f, indent=4)
        return empty_data

    # Calculate active bounding box in GPS
    xs = []
    ys = []
    for b in blocks:
        for pt in b["polygon"]:
            xs.append(pt[0])
            ys.append(pt[1])

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    # Convert corners to GPS
    lat1, lon1 = local_to_gps(min_x, min_y)
    lat2, lon2 = local_to_gps(max_x, max_y)

    min_lat, max_lat = min(lat1, lat2) - 0.005, max(lat1, lat2) + 0.005
    min_lon, max_lon = min(lon1, lon2) - 0.005, max(lon1, lon2) + 0.005

    print(f"[TerrainClassifier] Active BBox: ({min_lat:.5f}, {min_lon:.5f}) to ({max_lat:.5f}, {max_lon:.5f})")

    overpass_url = "https://overpass-api.de/api/interpreter"
    query = f"""[out:json][timeout:60];
(
  way["landuse"]({min_lat},{min_lon},{max_lat},{max_lon});
  relation["landuse"]({min_lat},{min_lon},{max_lat},{max_lon});
  way["leisure"]({min_lat},{min_lon},{max_lat},{max_lon});
  relation["leisure"]({min_lat},{min_lon},{max_lat},{max_lon});
  way["natural"]({min_lat},{min_lon},{max_lat},{max_lon});
  relation["natural"]({min_lat},{min_lon},{max_lat},{max_lon});
  way["surface"]({min_lat},{min_lon},{max_lat},{max_lon});
  relation["surface"]({min_lat},{min_lon},{max_lat},{max_lon});
);
out body geom;
"""
    headers = {
        "User-Agent": "TecateSimulatorMinecraftPipeline/1.0 (contact: hakkindavid@github)"
    }

    osm_data = None
    try:
        print("[TerrainClassifier] Requesting terrain features from Overpass API...")
        resp = requests.post(overpass_url, data={"data": query}, headers=headers, timeout=45)
        if resp.status_code == 200:
            osm_data = resp.json()
            print("[TerrainClassifier] Overpass API query successful!")
        else:
            print(f"[TerrainClassifier Warning] Overpass API failed with status code: {resp.status_code}")
    except Exception as e:
        print(f"[TerrainClassifier Warning] Overpass API request failed: {e}")

    classified_polygons = []
    if not osm_data:
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=4)
        return []

    elements = osm_data.get("elements", [])
    for el in elements:
        tags = el.get("tags", {})
        el_type = el.get("type")
        
        landuse = tags.get("landuse", "")
        leisure = tags.get("leisure", "")
        natural = tags.get("natural", "")
        surface = tags.get("surface", "")
        highway = tags.get("highway", "")
        amenity = tags.get("amenity", "")

        surface_class = None
        # Green/Grass
        if (
            landuse in ["grass", "meadow", "forest", "orchard", "cemetery", "village_green", "recreation_ground", "vineyard", "farmyard", "farmland", "allotments"] or
            leisure in ["park", "garden", "pitch", "playground", "nature_reserve", "golf_course"] or
            natural in ["wood", "grassland", "scrub", "heath", "fell"] or
            surface == "grass"
        ):
            surface_class = "grass"
        # Paved
        elif (
            landuse in ["industrial", "commercial", "retail", "construction", "military"] or
            surface in ["paved", "asphalt", "concrete", "paved_stone", "cobblestone"] or
            highway in ["pedestrian", "footway", "cycleway", "platform", "steps"] or
            amenity in ["parking", "marketplace"]
        ):
            surface_class = "paved"
        # Dirt/Unpaved
        elif (
            natural in ["sand", "mud", "shingle", "scree"] or
            surface in ["dirt", "unpaved", "gravel", "earth", "ground", "sand", "clay", "fine_gravel", "pebbles"]
        ):
            surface_class = "dirt"

        if not surface_class:
            continue

        poly_pts = []
        if el_type == "way":
            geom = el.get("geometry", [])
            for pt in geom:
                lx, ly = gps_to_local(pt["lat"], pt["lon"])
                poly_pts.append((lx, -ly))
        elif el_type == "relation":
            members = el.get("members", [])
            for m in members:
                if m.get("role") == "outer" and m.get("type") == "way":
                    geom = m.get("geometry", [])
                    for pt in geom:
                        lx, ly = gps_to_local(pt["lat"], pt["lon"])
                        poly_pts.append((lx, -ly))

        if len(poly_pts) >= 3:
            classified_polygons.append({
                "vertices": poly_pts,
                "class": surface_class
            })

    print(f"[TerrainClassifier] Extracted {len(classified_polygons)} classified polygons.")
    try:
        os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(classified_polygons, f, indent=4)
        print(f"[TerrainClassifier] Saved cache to {output_json_path}")
    except Exception as e:
        print(f"[TerrainClassifier Error] Failed to write cache: {e}")

    return classified_polygons
