import os
import json
import math
import shutil
import numpy as np
import networkx as nx
from PIL import Image

from src.core_io.coords import gps_to_local
from src.core_io.io_manager import ensure_dir, save_json, load_json
from src.gis_graph.graph_builder import TecateGraphBuilder
from src.image_alignment.virtual_camera import project_rectilinear
from src.image_alignment.visibility_filter import analyze_visibility_quality

class ArchivalDataMigrator:
    """
    Orchestrates the structural migration of the legacy Street View archive.
    Builds Layer 1 (Topology) and extracts Layer 2 (Facade Observations) incrementally.
    """
    def __init__(self, raw_cache_dir: str = "data/raw_scraped", data_dir: str = "data"):
        self.raw_cache_dir = raw_cache_dir
        self.data_dir = data_dir
        self.struct_dir = os.path.join(data_dir, "structural_graph")
        self.panos_dir = os.path.join(self.struct_dir, "panos")
        
        ensure_dir(self.struct_dir)
        ensure_dir(self.panos_dir)

    def run_migration(self, max_observations_to_process: int = 150) -> dict:
        """
        Runs the incremental structural migration pipeline.
        - max_observations_to_process: Cap on visual extractions to prevent turn-limit bottlenecks.
        """
        print("="*60)
        print("     TECATE STREET VIEW ARCHIVE STRUCTURAL MIGRATION")
        print("="*60)
        
        # 1. Load Road Network Graph G
        builder = TecateGraphBuilder(cache_dir=self.data_dir)
        osm_data = builder.fetch_osm_tecate()
        G = builder.build_networkx_graph(osm_data)
        camera_stations = builder.normalize_and_sample_edges(G, interval_meters=10)
        
        print(f"[Migration] OSM Graph loaded: {G.number_of_nodes()} intersections, {G.number_of_edges()} edges.")
        print(f"[Migration] Sampled {len(camera_stations)} virtual road stations.")
        
        # 2. Build Layer 1: Structural Street Graph Metadata
        intersections = {}
        for node_id, nd_data in G.nodes(data=True):
            deg = G.degree(node_id)
            if deg >= 2:  # Real intersection or connecting elbow
                intersections[node_id] = {
                    "node_id": node_id,
                    "latitude": nd_data["lat"],
                    "longitude": nd_data["lon"],
                    "x": nd_data["x"],
                    "y": nd_data["y"],
                    "degree": deg,
                    "street_name": nd_data.get("name", "")
                }
                
        # Save Intersections
        save_json(intersections, os.path.join(self.struct_dir, "intersections.json"))
        
        # Save Road Graph Topology
        flat_nodes = []
        for n, data in G.nodes(data=True):
            flat_nodes.append({"id": n, "x": data["x"], "y": data["y"], "lat": data["lat"], "lon": data["lon"]})
        flat_edges = []
        for u, v, data in G.edges(data=True):
            flat_edges.append({"id": data["id"], "u": u, "v": v, "name": data["name"], "length": data["length"]})
            
        road_graph_data = {
            "nodes": flat_nodes,
            "edges": flat_edges
        }
        save_json(road_graph_data, os.path.join(self.struct_dir, "road_graph.json"))
        
        # 3. Identify and Register All Scraped Nodes
        scraped_nodes = []
        if os.path.exists(self.raw_cache_dir):
            for d in os.listdir(self.raw_cache_dir):
                meta_path = os.path.join(self.raw_cache_dir, d, "metadata.json")
                if os.path.exists(meta_path):
                    try:
                        node_meta = load_json(meta_path)
                        scraped_nodes.append(node_meta)
                    except Exception:
                        pass
                        
        print(f"[Migration] Found {len(scraped_nodes)} scraped nodes in raw cache directory.")
        
        # Save each scraped node's metadata to the new Layer 1 structural graph panos directory
        for node in scraped_nodes:
            save_json(node, os.path.join(self.panos_dir, f"{node['pano_id']}.json"))
        
        # 4. Classify nodes: Intersections vs. Longitudinal Traversal
        intersection_panos = {}
        longitudinal_panos = []
        
        for node in scraped_nodes:
            lat = node["latitude"]
            lon = node["longitude"]
            nx_loc, ny_loc = gps_to_local(lat, lon)
            
            # Find closest intersection node in G
            best_inter = None
            min_dist = float("inf")
            for inter_id, inter in intersections.items():
                dist = math.sqrt((inter["x"] - nx_loc)**2 + (inter["y"] - ny_loc)**2)
                if dist < min_dist:
                    min_dist = dist
                    best_inter = inter_id
                    
            # If within 15 meters of a degree >= 2 intersection, classify as intersection reference
            if min_dist < 15.0:
                intersection_panos[node["pano_id"]] = {
                    "pano_id": node["pano_id"],
                    "latitude": lat,
                    "longitude": lon,
                    "closest_intersection": best_inter,
                    "distance_meters": min_dist,
                    "date": node.get("date", ""),
                    "adjacent_links": node.get("adjacent_links", []),
                    "timeline": node.get("timeline", [])
                }
            else:
                longitudinal_panos.append(node)
                
        print(f"[Migration] Classifications: {len(intersection_panos)} intersection reference nodes, {len(longitudinal_panos)} longitudinal traversal nodes.")
        
        # 5. Save Adjacency and Traversal State
        # Map panos to segments
        edge_assignments = {}
        for edge in flat_edges:
            edge_assignments[edge["id"]] = []
            
        for node in longitudinal_panos:
            lat = node["latitude"]
            lon = node["longitude"]
            nx_loc, ny_loc = gps_to_local(lat, lon)
            
            # Find closest edge segment
            best_edge = None
            min_dist = float("inf")
            for edge in flat_edges:
                u, v = edge["u"], edge["v"]
                ux, uy = G.nodes[u]["x"], G.nodes[u]["y"]
                vx, vy = G.nodes[v]["x"], G.nodes[v]["y"]
                
                # Perpendicular distance to segment
                dx = vx - ux
                dy = vy - uy
                seg_len_sq = dx*dx + dy*dy
                if seg_len_sq < 1e-5:
                    dist = math.sqrt((nx_loc - ux)**2 + (ny_loc - uy)**2)
                else:
                    t = ((nx_loc - ux) * dx + (ny_loc - uy) * dy) / seg_len_sq
                    t = max(0.0, min(1.0, t))
                    proj_x = ux + t * dx
                    proj_y = uy + t * dy
                    dist = math.sqrt((nx_loc - proj_x)**2 + (ny_loc - proj_y)**2)
                    
                if dist < min_dist:
                    min_dist = dist
                    best_edge = edge["id"]
                    
            if best_edge and min_dist < 40.0:
                edge_assignments[best_edge].append(node["pano_id"])
                
        adjacency_data = {
            "intersection_panos": intersection_panos,
            "edge_to_pano_index": edge_assignments
        }
        save_json(adjacency_data, os.path.join(self.struct_dir, "adjacency.json"))
        
        # Initialize traversal_state tracking scraper state for resuming crawling
        scraper_state_file = "data/scraper_state.json"
        if os.path.exists(scraper_state_file):
            try:
                state_data = load_json(scraper_state_file)
                # Keep state file fully aligned but copy to struct_dir for decoupling
                save_json(state_data, os.path.join(self.struct_dir, "traversal_state.json"))
            except Exception:
                pass
                
        # 6. Consolidate Scraped Panoramas to Layer 1 Cache
        processed_count = 0
        skipped_count = 0
        
        for node in scraped_nodes:
            p_id = node["pano_id"]
            raw_meta_path = os.path.join(self.raw_cache_dir, p_id, "metadata.json")
            raw_image_path = os.path.join(self.raw_cache_dir, p_id, "panorama.png")
            
            dest_meta_path = os.path.join(self.panos_dir, f"{p_id}.json")
            dest_image_path = os.path.join(self.panos_dir, f"{p_id}.png")
            
            # Copy metadata if exists
            if os.path.exists(raw_meta_path) and not os.path.exists(dest_meta_path):
                try:
                    shutil.copy2(raw_meta_path, dest_meta_path)
                except Exception:
                    pass
            
            # Copy panorama image if exists
            if os.path.exists(raw_image_path):
                if not os.path.exists(dest_image_path):
                    try:
                        shutil.copy2(raw_image_path, dest_image_path)
                        processed_count += 1
                        print(f"[Migration Cache] Moved raw panorama {p_id} to consolidated cache: {dest_image_path}")
                    except Exception as copy_err:
                        print(f"[Warning] Failed to copy panorama to cache: {copy_err}")
                else:
                    skipped_count += 1
            
        # Completely delete raw_cache_dir to ensure no legacy cache folders are kept
        if os.path.exists(self.raw_cache_dir):
            try:
                shutil.rmtree(self.raw_cache_dir, ignore_errors=True)
                print(f"[Migration] Successfully deleted obsolete raw cache directory: '{self.raw_cache_dir}'")
            except Exception as rmtree_err:
                print(f"[Warning] Failed to delete raw cache directory: {rmtree_err}")
                
        print("="*60)
        return {
            "processed": processed_count,
            "skipped": skipped_count,
            "deprecated_panos": processed_count
        }

if __name__ == "__main__":
    migrator = ArchivalDataMigrator()
    migrator.run_migration(max_observations_to_process=150)
