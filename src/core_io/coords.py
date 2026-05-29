import math

# Reference center point for Tecate: Parque Hidalgo
TECATE_LAT_CENTER = 32.573229
TECATE_LON_CENTER = -116.626536
EARTH_RADIUS = 6378137.0  # in meters

def gps_to_local(lat: float, lon: float) -> tuple[float, float]:
    """
    Converts GPS latitude and longitude to local Cartesian coordinates (x, y) in meters
    relative to Tecate's center point.
    x is East, y is North.
    """
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    lat_c_rad = math.radians(TECATE_LAT_CENTER)
    lon_c_rad = math.radians(TECATE_LON_CENTER)
    
    # Standard local tangent plane approximation (Equirectangular local projection)
    dx = EARTH_RADIUS * (lon_rad - lon_c_rad) * math.cos(lat_c_rad)
    dy = EARTH_RADIUS * (lat_rad - lat_c_rad)
    
    return dx, dy

def local_to_gps(x: float, y: float) -> tuple[float, float]:
    """
    Converts local Cartesian coordinates (x, y) back to GPS latitude and longitude.
    """
    lat_c_rad = math.radians(TECATE_LAT_CENTER)
    
    lat_rad = (y / EARTH_RADIUS) + lat_c_rad
    lon_rad = (x / (EARTH_RADIUS * math.cos(lat_c_rad))) + math.radians(TECATE_LON_CENTER)
    
    lat = math.degrees(lat_rad)
    lon = math.degrees(lon_rad)
    
    return lat, lon
