import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from src.core_io.coords import gps_to_local, TECATE_LAT_CENTER, TECATE_LON_CENTER

# Bounding box limits for Tecate
BBOX_SW_LAT = 32.521704
BBOX_SW_LON = -116.681499
BBOX_NE_LAT = 32.580233
BBOX_NE_LON = -116.510525

# Priority Center: Parque Hidalgo
PARQUE_HIDALGO_LAT = 32.573229
PARQUE_HIDALGO_LON = -116.626536

class SpatialCoverageVisualizer:
    """
    Generates a stunning, highly aesthetic spatial diagnostic map (coverage_map.png)
    to visualize roads, crawled nodes, unresolved regions, density, confidence,
    and crawl progression outward from Parque Hidalgo.
    """
    def __init__(self, width: int = 1920, height: int = 1080):
        self.width = width
        self.height = height
        self.margin = 80
        
        # Calculate local bounds
        self.xmin, self.ymin = gps_to_local(BBOX_SW_LAT, BBOX_SW_LON)
        self.xmax, self.ymax = gps_to_local(BBOX_NE_LAT, BBOX_NE_LON)
        
        # Let's expand a bit to cover the nodes if any go slightly beyond bounds
        self.dx = self.xmax - self.xmin
        self.dy = self.ymax - self.ymin

    def to_pixel(self, x: float, y: float) -> tuple[int, int]:
        """Maps local Cartesian meters to pixel coordinates (X, Y) on the canvas."""
        px = self.margin + int(((x - self.xmin) / self.dx) * (self.width - 2 * self.margin))
        # Flip Y for standard GIS orientation (North is up)
        py = self.height - self.margin - int(((y - self.ymin) / self.dy) * (self.height - 2 * self.margin))
        return px, py

    def draw_coverage_map(self, 
                          G, 
                          panoramas: list[dict], 
                          blocks: list[dict], 
                          output_path: str = "coverage_map.png"):
        """
        Renders a multi-layered diagnostic map.
        - Background: Dark charcoal gradient.
        - Layer 1: Crawl progression radial rings from Parque Hidalgo.
        - Layer 2: OSM road segments (charcoal/grey for standard, colored highlights for coverage).
        - Layer 3: Block texture coverage confidence fills.
        - Layer 4: Crawled panoramas (colored by status/year).
        - Overlay: High-fidelity legend, title card, and analytics text.
        """
        print(f"[Visualization] Renders spatial coverage diagnostic map to: {output_path}")
        
        # 1. Base Canvas - Sleek Dark Mode (radial dark blue-charcoal gradient)
        canvas = Image.new("RGB", (self.width, self.height), (15, 17, 22))
        draw = ImageDraw.Draw(canvas, "RGBA")
        
        # Draw background radial glow
        center_px, center_py = self.to_pixel(*gps_to_local(PARQUE_HIDALGO_LAT, PARQUE_HIDALGO_LON))
        for r in range(self.width, 0, -80):
            alpha = int(35 * (1.0 - r / self.width))
            draw.ellipse(
                [center_px - r, center_py - r, center_px + r, center_py + r],
                fill=(28, 52, 94, alpha)
            )

        # 2. Draw Crawl Progression Radial Rings (outward from Parque Hidalgo)
        hidalgo_x, hidalgo_y = gps_to_local(PARQUE_HIDALGO_LAT, PARQUE_HIDALGO_LON)
        ring_distances = [250, 500, 1000, 1500, 2500, 4000]  # meters
        for r_m in ring_distances:
            # We sample points on circle to map accurately
            circle_pts = []
            for angle in np.linspace(0, 2 * math.pi, 100):
                cx = hidalgo_x + r_m * math.cos(angle)
                cy = hidalgo_y + r_m * math.sin(angle)
                circle_pts.append(self.to_pixel(cx, cy))
                
            # Draw ring line
            for i in range(len(circle_pts) - 1):
                draw.line([circle_pts[i], circle_pts[i+1]], fill=(40, 60, 90, 80), width=1)
            draw.line([circle_pts[-1], circle_pts[0]], fill=(40, 60, 90, 80), width=1)
            
            # Label the ring (eastward)
            lbl_x, lbl_y = self.to_pixel(hidalgo_x + r_m, hidalgo_y)
            if 0 < lbl_x < self.width and 0 < lbl_y < self.height:
                draw.text((lbl_x + 5, lbl_y - 12), f"{r_m}m", fill=(80, 110, 150, 160))

        # 3. Density Heatmap Layer
        # Aggregate density of 2009 panoramas on a coarse grid
        grid_w, grid_h = 32, 18
        grid = np.zeros((grid_w, grid_h))
        for pano in panoramas:
            px, py = gps_to_local(pano["latitude"], pano["longitude"])
            if self.xmin <= px <= self.xmax and self.ymin <= py <= self.ymax:
                gx = int(((px - self.xmin) / self.dx) * grid_w)
                gy = int(((py - self.ymin) / self.dy) * grid_h)
                gx = np.clip(gx, 0, grid_w - 1)
                gy = np.clip(gy, 0, grid_h - 1)
                grid[gx, gy] += 1.0
                
        # Draw soft density boxes
        if grid.max() > 0:
            grid_scale_x = (self.width - 2 * self.margin) / grid_w
            grid_scale_y = (self.height - 2 * self.margin) / grid_h
            for gx in range(grid_w):
                for gy in range(grid_h):
                    val = grid[gx, gy]
                    if val > 0:
                        alpha = int(min(120, 25 * val))
                        x0 = self.margin + int(gx * grid_scale_x)
                        y0 = self.height - self.margin - int((gy + 1) * grid_scale_y)
                        x1 = self.margin + int((gx + 1) * grid_scale_x)
                        y1 = self.height - self.margin - int(gy * grid_scale_y)
                        draw.rectangle([x0, y0, x1, y1], fill=(235, 130, 35, alpha))

        # 4. Draw Block Confidence & Texture Coverage
        # Highlight blocks: Green if they have high texture coverage, Red if they are procedural
        for bl in blocks:
            poly = bl["polygon"]
            pixel_poly = [self.to_pixel(pt[0], pt[1]) for pt in poly]
            
            # Check coverage based on atlas traceability
            atlas_filename = bl.get("texture_atlas_filename", "none")
            trace = bl.get("traceability", [])
            
            # Calculate ratio of real-world textured facades
            image_facades = sum(1 for t in trace if t.get("source") == "image")
            total_facades = max(1, len(trace))
            coverage_ratio = image_facades / total_facades
            
            # Semi-transparent block fill color
            # High confidence = Green, Mid = Yellow, Fallback = Red
            if atlas_filename == "none" or coverage_ratio == 0:
                fill_col = (200, 40, 40, 30)  # low/procedural
                outline_col = (200, 40, 40, 90)
            elif coverage_ratio < 0.5:
                fill_col = (220, 180, 30, 45)  # partial
                outline_col = (220, 180, 30, 100)
            else:
                fill_col = (40, 200, 120, 50)  # high
                outline_col = (40, 200, 120, 125)
                
            draw.polygon(pixel_poly, fill=fill_col, outline=outline_col)

        # 5. Draw Road Graph Segments
        # Unresolved areas highlighted in orange, resolved in thin teal, uncrawled in dark charcoal
        unresolved_count = 0
        resolved_count = 0
        
        # To determine if an edge is resolved, we check if any accepted 2009 panorama is near
        accepted_2009_coords = np.array([
            gps_to_local(p["latitude"], p["longitude"])
            for p in panoramas if p.get("temporal_probability", 0.0) >= 0.70
        ])
        
        for u, v, data in G.edges(data=True):
            ux, uy = G.nodes[u]["x"], G.nodes[u]["y"]
            vx, vy = G.nodes[v]["x"], G.nodes[v]["y"]
            
            p_u = self.to_pixel(ux, uy)
            p_v = self.to_pixel(vx, vy)
            
            # Midpoint of edge
            mx, my = (ux + vx) / 2.0, (uy + vy) / 2.0
            
            # Distance to nearest 2009 panorama
            is_resolved = False
            if len(accepted_2009_coords) > 0:
                dists = np.sqrt((accepted_2009_coords[:, 0] - mx)**2 + (accepted_2009_coords[:, 1] - my)**2)
                if dists.min() < 35.0:
                    is_resolved = True
                    
            if is_resolved:
                resolved_count += 1
                edge_color = (0, 235, 235, 160)  # Neon Cyan
                edge_width = 2
            else:
                unresolved_count += 1
                edge_color = (255, 120, 0, 120)  # Neon Orange (unresolved priority queue target)
                edge_width = 2
                
            draw.line([p_u, p_v], fill=edge_color, width=edge_width)

        # 6. Draw Crawled Panoramas
        # 2009 accepted: neon green, non-2009/modern: yellow-orange, failed: red
        for pano in panoramas:
            px, py = gps_to_local(pano["latitude"], pano["longitude"])
            pix_x, pix_y = self.to_pixel(px, py)
            
            prob = pano.get("temporal_probability", 1.0)
            if prob >= 0.70:
                node_color = (40, 255, 120)  # Accepted 2009 (neon green)
                size = 5
            else:
                node_color = (255, 180, 0)  # Modern/Filtered (amber)
                size = 4
                
            draw.ellipse(
                [pix_x - size, pix_y - size, pix_x + size, pix_y + size],
                fill=node_color,
                outline=(255, 255, 255, 180)
            )

        # Draw Parque Hidalgo Seed Center
        hidalgo_px, hidalgo_py = self.to_pixel(hidalgo_x, hidalgo_y)
        draw.ellipse(
            [hidalgo_px - 8, hidalgo_py - 8, hidalgo_px + 8, hidalgo_py + 8],
            fill=(255, 40, 120, 255),
            outline=(255, 255, 255, 255)
        )
        draw.text((hidalgo_px + 10, hidalgo_py - 10), "Parque Hidalgo (Crawl Origin)", fill=(255, 255, 255, 220))

        # 7. Add Title Panel & Legend Overlay
        # Main Title Panel
        draw.rectangle([50, 50, 550, 310], fill=(20, 25, 35, 220), outline=(80, 110, 150, 120), width=2)
        draw.text((70, 70), "TECATE RECONSTRUCTION MAP", fill=(255, 255, 255, 255))
        draw.text((70, 95), "Historical Urban Spatial Diagnostics", fill=(80, 180, 255, 255))
        draw.text((70, 120), "-" * 48, fill=(80, 110, 150, 100))
        
        # Legend Items
        legend_items = [
            ("Seed Origin (Parque Hidalgo)", (255, 40, 120), "circle"),
            ("Accepted 2009 Pano Observation", (40, 255, 120), "circle"),
            ("Modern/Pruned Pano Observation", (255, 180, 0), "circle"),
            ("Resolved Street Segment (<35m)", (0, 235, 235), "line"),
            ("Unresolved Street Segment (Needs Crawl)", (255, 120, 0), "line"),
            ("Fully Reconstructed & Textured Block", (40, 200, 120, 60), "block"),
            ("Procedural / Fallback Stucco Block", (200, 40, 40, 40), "block"),
        ]
        
        ly = 140
        for name, col, geom in legend_items:
            if geom == "circle":
                draw.ellipse([70, ly + 2, 82, ly + 14], fill=col, outline=(255, 255, 255, 180))
            elif geom == "line":
                draw.line([70, ly + 8, 85, ly + 8], fill=col, width=3)
            elif geom == "block":
                draw.rectangle([70, ly + 2, 85, ly + 14], fill=col, outline=(col[0], col[1], col[2], 180))
                
            draw.text((100, ly), name, fill=(210, 220, 235, 255))
            ly += 22

        # 8. Add Statistics Dashboard (Bottom Right)
        total_panos = len(panos_to_show := list(panoramas))
        total_2009 = sum(1 for p in panos_to_show if p.get("temporal_probability", 0.0) >= 0.70)
        total_modern = total_panos - total_2009
        
        total_blocks = len(blocks)
        textured_blocks = sum(1 for b in blocks if b.get("texture_atlas_filename", "none") != "none" and sum(1 for t in b.get("traceability", []) if t.get("source") == "image") > 0)
        texture_percentage = (textured_blocks / total_blocks * 100.0) if total_blocks > 0 else 0.0
        
        draw.rectangle([self.width - 500, self.height - 350, self.width - 50, self.height - 50], 
                       fill=(20, 25, 35, 220), outline=(80, 110, 150, 120), width=2)
                       
        draw.text((self.width - 470, self.height - 330), "RECONSTRUCTION ANALYTICS", fill=(255, 255, 255, 255))
        draw.text((self.width - 470, self.height - 305), "-" * 40, fill=(80, 110, 150, 100))
        
        stat_rows = [
            ("Total Crawled Nodes:", f"{total_panos}"),
            ("Accepted 2009 Obs:", f"{total_2009} ({(total_2009/total_panos*100.0 if total_panos > 0 else 0.0):.1f}%)"),
            ("Modern/Pruned Obs:", f"{total_modern}"),
            ("Total Urban Blocks:", f"{total_blocks}"),
            ("Real-Textured Blocks:", f"{textured_blocks} ({texture_percentage:.1f}%)"),
            ("Resolved Street Length:", f"{resolved_count} / {resolved_count + unresolved_count} segs"),
            ("Bounding Box SW:", f"{BBOX_SW_LAT:.4f}, {BBOX_SW_LON:.4f}"),
            ("Bounding Box NE:", f"{BBOX_NE_LAT:.4f}, {BBOX_NE_LON:.4f}")
        ]
        
        sy = self.height - 285
        for label, val in stat_rows:
            draw.text((self.width - 470, sy), label, fill=(160, 180, 210, 255))
            draw.text((self.width - 250, sy), val, fill=(0, 235, 235, 255))
            sy += 24

        # 9. Add Bounding Box Frame
        draw.rectangle([self.margin, self.margin, self.width - self.margin, self.height - self.margin], 
                       outline=(80, 110, 150, 80), width=2)
                       
        # Save to disk
        canvas.save(output_path)
        print(f"[Visualization] Successfully exported high-fidelity spatial coverage map to: {output_path}")

