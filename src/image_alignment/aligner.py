import math
import cv2
import numpy as np
from src.core_io.coords import gps_to_local

class ImageAligner:
    """
    Geospatially anchors and aligns Street View panoramas to the road graph.
    Uses classical OpenCV Line Segment Detector (LSD) to estimate vanishing points,
    correcting any camera yaw heading errors relative to the street segment.
    """
    def __init__(self):
        # Create standard ORB detector for image similarity and verification
        self.orb = cv2.ORB_create(nfeatures=1000)
        # Create BFMatcher with Hamming distance
        self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

    def anchor_to_graph(self, 
                        pano_data: dict, 
                        camera_stations: list[dict]) -> dict | None:
        """
        Maps a panorama's GPS coordinate to the closest virtual camera station on the road graph.
        Returns the best-fit camera station dictionary with an assigned alignment score.
        """
        pano_lat = pano_data["latitude"]
        pano_lon = pano_data["longitude"]
        px, py = gps_to_local(pano_lat, pano_lon)
        
        best_station = None
        min_dist = float("inf")
        
        for station in camera_stations:
            sx, sy = station["x"], station["y"]
            dist = math.sqrt((px - sx)**2 + (py - sy)**2)
            if dist < min_dist:
                min_dist = dist
                best_station = station
                
        # If the closest virtual station is within 30 meters, we successfully anchor it
        if best_station and min_dist < 30.0:
            aligned_meta = {
                "pano_id": pano_data.get("pano_id", "sim_pano"),
                "station_id": best_station["station_id"],
                "edge_id": best_station["edge_id"],
                "dist_along": best_station["dist_along"],
                "graph_x": best_station["x"],
                "graph_y": best_station["y"],
                "latitude": pano_data["latitude"],
                "longitude": pano_data["longitude"],
                "alignment_distance": min_dist,
                "road_heading": best_station["road_heading"],
                "temporal_probability": pano_data.get("temporal_probability", 1.0)
            }
            return aligned_meta
            
        return None

    def estimate_vanishing_point_heading_offset(self, pil_image) -> float:
        """
        Uses OpenCV's LSD (Line Segment Detector) in the forward quadrant (front view)
        to identify converging lines, estimate the vanishing point, and compute heading yaw offset.
        Returns yaw correction angle in degrees.
        """
        # Convert PIL Image to OpenCV grayscale
        cv_img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
        
        # We focus on the forward quadrant of the equirectangular panorama.
        # In a 2560x640 image, 0 heading is in the center of the first tile: pixels [0, 640].
        # However, because equirectangular stitched maps place 0 degrees (North) at x=0 (and x=2560),
        # the center of the image (x=1280) is 180 degrees (South), and 0 heading is split at the edges,
        # OR 0 heading is centered at x=320 (if stitched as 0, 90, 180, 270).
        # In our Procedural Generator and downloader, 0 heading is centered in the first 640px tile (x_center = 320).
        # We crop the forward quadrant: x from 0 to 640, y from 160 to 480 (focused on the horizon).
        roi = gray[160:480, 0:640]
        h_roi, w_roi = roi.shape
        
        # Detect lines using LSD
        lsd = cv2.createLineSegmentDetector(cv2.LSD_REFINE_STD)
        lines, _, _, _ = lsd.detect(roi)
        
        if lines is None or len(lines) < 2:
            return 0.0  # Safe default if no line structure found
            
        # We calculate the intersections of lines that have a reasonable slope.
        # Line equation: y = m*x + c
        line_eqs = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            dx = x2 - x1
            dy = y2 - y1
            if abs(dx) < 1e-5:
                continue
            slope = dy / dx
            # Filter out almost horizontal (slope ≈ 0) or completely vertical lines
            if 0.15 < abs(slope) < 4.0:
                c = y1 - slope * x1
                line_eqs.append((slope, c))
                
        if len(line_eqs) < 2:
            return 0.0
            
        # Standard RANSAC or basic voting to find the densest intersection point
        intersections = []
        for i in range(len(line_eqs)):
            for j in range(i + 1, len(line_eqs)):
                m1, c1 = line_eqs[i]
                m2, c2 = line_eqs[j]
                if abs(m1 - m2) < 0.05:
                    continue
                ix = (c2 - c1) / (m1 - m2)
                iy = m1 * ix + c1
                
                # Check if intersection is within reasonable boundaries of the front view
                if 0 <= ix <= w_roi and 0 <= iy <= h_roi:
                    intersections.append((ix, iy))
                    
        if len(intersections) == 0:
            return 0.0
            
        # Mean or median intersection point
        avg_ix = np.median([pt[0] for pt in intersections])
        
        # The ideal vanishing point in our cropped quadrant (width 640) is at x = 320.
        # Difference in pixels:
        delta_x = avg_ix - 320.0
        
        # Map pixel difference to yaw offset angle in degrees.
        # Since the entire panorama width (2560 pixels) covers 360 degrees,
        # 1 pixel = 360 / 2560 = 0.140625 degrees.
        yaw_offset_deg = delta_x * (360.0 / 2560.0)
        
        return yaw_offset_deg

    def compute_descriptor_similarity(self, img1, img2) -> float:
        """
        Computes ORB feature matching similarity between two views.
        Used to verify structural match of neighboring camera segments.
        """
        cv_img1 = cv2.cvtColor(np.array(img1), cv2.COLOR_RGB2GRAY)
        cv_img2 = cv2.cvtColor(np.array(img2), cv2.COLOR_RGB2GRAY)
        
        kp1, des1 = self.orb.detectAndCompute(cv_img1, None)
        kp2, des2 = self.orb.detectAndCompute(cv_img2, None)
        
        if des1 is None or des2 is None or len(des1) == 0 or len(des2) == 0:
            return 0.0
            
        matches = self.matcher.match(des1, des2)
        if len(matches) == 0:
            return 0.0
            
        # Similarity score based on ratio of good matches to total keypoints
        good_matches = [m for m in matches if m.distance < 60.0]
        score = len(good_matches) / max(len(kp1), len(kp2))
        
        return score
