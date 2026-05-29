import cv2
import numpy as np
import networkx as nx

class TemporalVisualClassifier:
    """
    Classifies images into historical ~2009 vs. Modern (~2026) using classical computer vision.
    Analyzes resolution, Laplacian variance (blurriness), sensor noise level, and keypoint density.
    """
    def __init__(self):
        self.orb = cv2.ORB_create(nfeatures=1500)

    def compute_visual_2009_probability(self, pil_image) -> float:
        """
        Extracts visual descriptors and returns a probability score P(2009) based on low-tech artifacts.
        - Low-res CCD sensor noise
        - Higher blur (Laplacian variance)
        - Keypoint count (lower density in blurred areas)
        """
        # Convert PIL to grayscale
        cv_img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
        
        # 1. Evaluate sharpness (Variance of Laplacian)
        # 2009 Street View is heavily blurred/compressed (low variance of Laplacian)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Normalize: high sharp images (var > 250) are likely modern; low sharp (var < 80) are 2009.
        if laplacian_var > 220:
            p_blur = 0.15
        elif laplacian_var < 70:
            p_blur = 0.85
        else:
            # Linear interpolation
            p_blur = 0.85 - 0.70 * ((laplacian_var - 70) / 150)
            
        # 2. Evaluate keypoint density (Blurred and compressed images yield fewer ORB keypoints)
        kp = self.orb.detect(gray, None)
        num_kp = len(kp)
        
        if num_kp > 1100:
            p_kp = 0.10
        elif num_kp < 400:
            p_kp = 0.90
        else:
            p_kp = 0.90 - 0.80 * ((num_kp - 400) / 700)
            
        # 3. Sensor Noise Check (2009 images have distinct high-frequency CCD noise and JPEG blocking)
        # We compute noise by subtracting a slightly blurred version of the image
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        noise_diff = cv2.absdiff(gray, blurred)
        noise_mean = noise_diff.mean()
        
        # Higher sensor noise in old cameras
        if noise_mean > 6.0:
            p_noise = 0.80
        elif noise_mean < 2.5:
            p_noise = 0.20
        else:
            p_noise = 0.20 + 0.60 * ((noise_mean - 2.5) / 3.5)
            
        # Combined weighted probability
        # Sharpness and keypoints are highly indicative of modern vs. old Street View
        final_prob = 0.40 * p_blur + 0.30 * p_kp + 0.30 * p_noise
        return float(np.clip(final_prob, 0.01, 0.99))


class TemporalMRFSolver:
    """
    Uses a Markov Random Field (MRF) approach to enforce neighborhood consistency.
    If timestamps are missing, it diffuses 2009 probabilities across connected roads.
    Operates directly on the observation graph via metadata adjacent_links,
    with distance-based adjacency along edges as a robust fallback.
    """
    def __init__(self, G: nx.MultiGraph):
        self.G = G

    def solve_temporal_consistency(self, 
                                  aligned_panos: list[dict], 
                                  alpha: float = 0.6, 
                                  iterations: int = 8) -> list[dict]:
        """
        Propagates P(2009) through the observation neighborhood.
        - aligned_panos: list of dicts containing 'station_id', 'pano_id', 'temporal_probability'
        - alpha: diffusion factor (weight of neighbor's influence)
        
        Algorithm: Iterative label propagation over graph structure.
        """
        # Map pano to graph node and vice-versa
        pano_lookup = {p["pano_id"]: p for p in aligned_panos}
        station_to_pano = {p["station_id"]: p for p in aligned_panos}

        # Build adjacency graph of panoramas
        obs_graph = nx.Graph()
        
        # Add all panoramas as nodes
        for p in aligned_panos:
            p_id = p["pano_id"]
            obs_graph.add_node(
                p_id, 
                p_init=p["temporal_probability"], 
                p_curr=p["temporal_probability"]
            )
            
        # 1. Connect via metadata adjacent_links if present
        metadata_links_added = 0
        for p in aligned_panos:
            p_id = p["pano_id"]
            adj_links = p.get("adjacent_links", [])
            for link in adj_links:
                neighbor_id = link.get("pano_id")
                if neighbor_id in pano_lookup:
                    obs_graph.add_edge(p_id, neighbor_id)
                    metadata_links_added += 1
                    
        # 2. Fallback / Augment: Connect adjacent stations along the same edges
        # This preserves backwards compatibility with synthetic test cases and fills missing links.
        edge_panos = {}
        for p in aligned_panos:
            edge_id = p.get("edge_id")
            if edge_id:
                if edge_id not in edge_panos:
                    edge_panos[edge_id] = []
                edge_panos[edge_id].append((p.get("dist_along", 0.0), p["pano_id"]))
                
        for edge_id, panos_list in edge_panos.items():
            panos_list.sort() # sort by distance along edge
            for i in range(len(panos_list) - 1):
                u_id = panos_list[i][1]
                v_id = panos_list[i+1][1]
                obs_graph.add_edge(u_id, v_id)
                
        print(f"[Temporal Filter] Built MRF observation graph: {obs_graph.number_of_nodes()} nodes, {obs_graph.number_of_edges()} edges (metadata links: {metadata_links_added}).")
        
        # Iterative propagation (neighborhood relaxation)
        for _ in range(iterations):
            next_probs = {}
            for node in obs_graph.nodes:
                neighbors = list(obs_graph.neighbors(node))
                p_init = obs_graph.nodes[node]["p_init"]
                
                if len(neighbors) == 0:
                    next_probs[node] = p_init
                else:
                    neighbor_sum = sum(obs_graph.nodes[nbr]["p_curr"] for nbr in neighbors)
                    neighbor_avg = neighbor_sum / len(neighbors)
                    # MRF Update equation
                    next_probs[node] = (1.0 - alpha) * p_init + alpha * neighbor_avg
                    
            for node, p_new in next_probs.items():
                obs_graph.nodes[node]["p_curr"] = p_new

        # Update original panoramas with new MRF probability estimates
        filtered_panos = []
        for pano in aligned_panos:
            p_id = pano["pano_id"]
            mrf_prob = obs_graph.nodes[p_id]["p_curr"] if p_id in obs_graph.nodes else pano["temporal_probability"]
            
            updated_pano = pano.copy()
            updated_pano["temporal_probability"] = mrf_prob
            
            # Strict filter threshold: Accept P(2009) >= 0.70
            if mrf_prob >= 0.70:
                updated_pano["accepted"] = True
                filtered_panos.append(updated_pano)
            else:
                updated_pano["accepted"] = False
                print(f"[Temporal Filter] Pruned non-2009 panorama {pano['pano_id']} (P(2009) = {mrf_prob:.3f})")
                
        return filtered_panos
