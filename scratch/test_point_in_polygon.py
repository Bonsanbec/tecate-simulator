import json
import os

def load_tecate_polygon():
    polygon_path = "reference/tecate-polygon.json"
    if not os.path.exists(polygon_path):
        print(f"Error: {polygon_path} not found.")
        return None
        
    with open(polygon_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    features = data.get("features", [])
    if not features:
        return None
        
    geometry = features[0].get("geometry", {})
    geom_type = geometry.get("type")
    coords = geometry.get("coordinates", [])
    
    # We will parse MultiPolygon or Polygon into a flat list of rings (each ring is a list of [lon, lat] points)
    rings = []
    if geom_type == "Polygon":
        for ring in coords:
            rings.append(ring)
    elif geom_type == "MultiPolygon":
        for poly in coords:
            for ring in poly:
                rings.append(ring)
                
    print(f"[Polygon Loader] Loaded {len(rings)} rings from {geom_type} geometry.")
    return rings

def is_point_in_polygon(lat: float, lon: float, rings) -> bool:
    """
    Ray-casting algorithm to determine if a point (lat, lon) is inside the polygon rings.
    lon maps to X, lat maps to Y.
    """
    if not rings:
        return False
        
    # Standard ray-casting for polygon with holes.
    # An odd number of total ring crossings means the point is inside the polygon.
    inside = False
    x, y = lon, lat
    
    for ring in rings:
        n = len(ring)
        if n < 3:
            continue
            
        # Ray casting
        p1x, p1y = ring[0][0], ring[0][1]
        for i in range(n + 1):
            p2x, p2y = ring[i % n][0], ring[i % n][1]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xints = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xints:
                            inside = not inside
            p1x, p1y = p2x, p2y
            
    return inside

# Test a few coordinates
rings = load_tecate_polygon()
if rings:
    # Parque Hidalgo (Center)
    hidalgo_lat, hidalgo_lon = 32.573229, -116.626536
    print(f"Parque Hidalgo inside? {is_point_in_polygon(hidalgo_lat, hidalgo_lon, rings)}")
    
    # A point far away
    far_lat, far_lon = 33.0, -117.0
    print(f"San Diego inside? {is_point_in_polygon(far_lat, far_lon, rings)}")
    
    # Let's check a point near the border
    border_lat, border_lon = 32.56, -116.7
    print(f"Point near border inside? {is_point_in_polygon(border_lat, border_lon, rings)}")
