import pytest
import networkx as nx
import tempfile
import os
from src.reconstruction.prism_generator import UrbanBlockReconstructor

def test_road_distance_orthogonal():
    """Verify distance calculation for orthogonal road segments."""
    # Create a simple MultiGraph G
    G = nx.MultiGraph()
    # Horizontal road from (0, 0) to (100, 0)
    G.add_node(1, x=0.0, y=0.0)
    G.add_node(2, x=100.0, y=0.0)
    G.add_edge(1, 2, id="edge_horizontal")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        reconstructor = UrbanBlockReconstructor(G, export_dir=tmpdir, data_dir=tmpdir)
        
        # Point at (50, 10) should have distance 10 to edge_horizontal
        dist, edge_id = reconstructor.get_road_distance(50.0, 10.0)
        assert abs(dist - 10.0) < 1e-5
        assert edge_id == "edge_horizontal"

def test_road_distance_diagonal():
    """Verify distance calculation for diagonal road segments."""
    G = nx.MultiGraph()
    # Diagonal road from (0, 0) to (100, 100)
    # Direction vector = [100, 100], unit vector = [1/sqrt(2), 1/sqrt(2)]
    G.add_node(1, x=0.0, y=0.0)
    G.add_node(2, x=100.0, y=100.0)
    G.add_edge(1, 2, id="edge_diagonal")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        reconstructor = UrbanBlockReconstructor(G, export_dir=tmpdir, data_dir=tmpdir)
        
        # Point at (0, 10). Projected point on line y=x is (5, 5).
        # Distance should be sqrt((0-5)^2 + (10-5)^2) = sqrt(50) = 7.0710678...
        dist, edge_id = reconstructor.get_road_distance(0.0, 10.0)
        expected_dist = 5.0 * 2.0**0.5  # 7.0710678
        assert abs(dist - expected_dist) < 1e-5
        assert edge_id == "edge_diagonal"

def test_road_distance_outside_segment():
    """Verify distance calculation when projection falls outside the segment endpoints."""
    G = nx.MultiGraph()
    # Segment from (0, 0) to (10, 0)
    G.add_node(1, x=0.0, y=0.0)
    G.add_node(2, x=10.0, y=0.0)
    G.add_edge(1, 2, id="edge_short")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        reconstructor = UrbanBlockReconstructor(G, export_dir=tmpdir, data_dir=tmpdir)
        
        # Point at (15, 5) — closest point on segment is the endpoint (10, 0)
        # Distance = sqrt((15-10)^2 + (5-0)^2) = sqrt(50)
        dist, edge_id = reconstructor.get_road_distance(15.0, 5.0)
        expected_dist = 50.0**0.5
        assert abs(dist - expected_dist) < 1e-5
        assert edge_id == "edge_short"

def test_road_distance_grid_indexing():
    """Verify that spatial grid indexing yields correct nearest road segment."""
    G = nx.MultiGraph()
    # Set up two parallel horizontal roads
    # Road 1: y = 0
    G.add_node(1, x=0.0, y=0.0)
    G.add_node(2, x=100.0, y=0.0)
    G.add_edge(1, 2, id="road_bottom")
    
    # Road 2: y = 100
    G.add_node(3, x=0.0, y=100.0)
    G.add_node(4, x=100.0, y=100.0)
    G.add_edge(3, 4, id="road_top")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        reconstructor = UrbanBlockReconstructor(G, export_dir=tmpdir, data_dir=tmpdir)
        
        # Test near bottom road
        dist1, edge_id1 = reconstructor.get_road_distance(50.0, 10.0)
        assert abs(dist1 - 10.0) < 1e-5
        assert edge_id1 == "road_bottom"
        
        # Test near top road
        dist2, edge_id2 = reconstructor.get_road_distance(50.0, 95.0)
        assert abs(dist2 - 5.0) < 1e-5
        assert edge_id2 == "road_top"
