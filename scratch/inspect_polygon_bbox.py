import json
import os

polygon_path = "reference/tecate-polygon.json"
if os.path.exists(polygon_path):
    with open(polygon_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    features = data.get("features", [])
    if features:
        geom = features[0].get("geometry", {})
        coords = geom.get("coordinates", [])
        
        # Flatten the multipolygon coordinates
        all_lons = []
        all_lats = []
        
        # MultiPolygon format is usually [[[[lon, lat], ...]]]
        def extract_coords(lst):
            if isinstance(lst[0], list):
                for item in lst:
                    extract_coords(item)
            else:
                all_lons.append(lst[0])
                all_lats.append(lst[1])
                
        extract_coords(coords)
        
        min_lon, max_lon = min(all_lons), max(all_lons)
        min_lat, max_lat = min(all_lats), max(all_lats)
        
        print(f"Tecate Polygon Bounding Box:")
        print(f"Latitude range:  {min_lat} to {max_lat}")
        print(f"Longitude range: {min_lon} to {max_lon}")
        print(f"Total points:    {len(all_lons)}")
    else:
        print("No features found in polygon.")
else:
    print(f"Polygon file not found at: {polygon_path}")
