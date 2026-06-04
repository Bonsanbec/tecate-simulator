import pytest
import math
from src.core_io.coords import gps_to_local, local_to_gps, TECATE_LAT_CENTER, TECATE_LON_CENTER

def test_center_point():
    """Verify that the reference center converts to (0, 0)."""
    x, y = gps_to_local(TECATE_LAT_CENTER, TECATE_LON_CENTER)
    assert abs(x) < 1e-7
    assert abs(y) < 1e-7

def test_round_trip_center():
    """Verify round trip at center point."""
    lat, lon = local_to_gps(0.0, 0.0)
    assert abs(lat - TECATE_LAT_CENTER) < 1e-7
    assert abs(lon - TECATE_LON_CENTER) < 1e-7

def test_round_trip_target():
    """Verify round trip at the target study case coordinates."""
    # Target location: 32.5728966, -116.6245526
    target_lat = 32.5728966
    target_lon = -116.6245526
    
    x, y = gps_to_local(target_lat, target_lon)
    lat_rt, lon_rt = local_to_gps(x, y)
    
    assert abs(lat_rt - target_lat) < 1e-7
    assert abs(lon_rt - target_lon) < 1e-7

def test_tangent_plane_distance():
    """Verify coordinate scaling by comparing with Haversine distance."""
    target_lat = 32.5728966
    target_lon = -116.6245526
    
    # Calculate distance using local Cartesian coordinates
    x, y = gps_to_local(target_lat, target_lon)
    local_dist = math.sqrt(x**2 + y**2)
    
    # Haversine distance calculation
    lat1, lon1 = math.radians(TECATE_LAT_CENTER), math.radians(TECATE_LON_CENTER)
    lat2, lon2 = math.radians(target_lat), math.radians(target_lon)
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6378137.0  # Earth radius
    haversine_dist = r * c
    
    # Difference should be tiny for close coordinates (~65m)
    assert abs(local_dist - haversine_dist) < 0.1  # less than 10cm difference
