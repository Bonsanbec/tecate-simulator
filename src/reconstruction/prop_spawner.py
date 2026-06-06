import cv2
import math
import numpy as np

class PropSpawner:
    """
    Analyzes semantic segmentation masks to locate windows and doors on a facade texture plane,
    and projects them to 3D Cartesian space to spawn procedurally instanced props (sills, signs, awnings).
    """
    def __init__(self, pixel_per_meter=100.0):
        self.pixel_per_meter = pixel_per_meter
        # Semantic label indices
        self.label_window = 8
        self.label_door = 14
        self.label_gate = 58

    def extract_props(self, mask: np.ndarray, A: list, B: list, base_z: float, height: float, facade_id: str = "") -> list:
        """
        Locates windows/doors in the 2D semantic mask, projects them to 3D coords,
        and returns a list of prop description dictionaries.
        """
        h_px, w_px = mask.shape
        props = []
        
        # Calculate facade segment properties
        A = np.array(A[:2])
        B = np.array(B[:2])
        vec_ab = B - A
        length = np.linalg.norm(vec_ab)
        if length < 1e-5:
            return props
            
        dir_ab = vec_ab / length
        normal = np.array([-dir_ab[1], dir_ab[0]]) # Outward pointing 2D normal
        
        # Facade rotation around Z axis in radians
        yaw = math.atan2(dir_ab[1], dir_ab[0])
        
        # --- 1. WINDOW PROPS (Sills, Awnings) ---
        window_mask = (mask == self.label_window).astype(np.uint8)
        contours_w, _ = cv2.findContours(window_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for idx, cnt in enumerate(contours_w):
            area = cv2.contourArea(cnt)
            if area < 50: # Filter noise
                continue
                
            x_px, y_px, w_cnt, h_cnt = cv2.boundingRect(cnt)
            
            # Normalize to [0.0, 1.0] texture space coordinates
            u_min = x_px / float(w_px)
            u_max = (x_px + w_cnt) / float(w_px)
            v_min = y_px / float(h_px)
            v_max = (y_px + h_cnt) / float(h_px)
            
            # Center of the window
            u_ctr = (u_min + u_max) / 2.0
            v_ctr = (v_min + v_max) / 2.0
            
            # Project 2D center to 3D Cartesian coords
            # Horizontal interpolation along segment AB
            pos_2d = A + u_ctr * vec_ab
            # Vertical height (v=0 is top, v=1 is bottom in image space)
            z_pos = base_z + (1.0 - v_ctr) * height
            
            # Dimensions in meters
            w_m = w_cnt / float(w_px) * length
            h_m = h_cnt / float(h_px) * height
            
            # Window Sill: Position at the bottom of the window
            sill_z = base_z + (1.0 - v_max) * height
            sill_pos = [float(pos_2d[0]), float(pos_2d[1]), float(sill_z)]
            
            props.append({
                "facade_id": facade_id,
                "prop_type": "window_sill",
                "position": sill_pos,
                "rotation": [0.0, 0.0, float(yaw)],
                "scale": [float(w_m), 1.0, 1.0],
                "size_m": [float(w_m), float(h_m)],
                "type": "window"
            })
            
            # Large windows can have an awning
            if w_m > 1.2:
                awning_z = base_z + (1.0 - v_min) * height
                awning_pos = [float(pos_2d[0] + 0.1 * normal[0]), float(pos_2d[1] + 0.1 * normal[1]), float(awning_z)]
                props.append({
                    "facade_id": facade_id,
                    "prop_type": "awning",
                    "position": awning_pos,
                    "rotation": [0.0, 0.0, float(yaw)],
                    "scale": [float(w_m), 1.0, 1.0],
                    "size_m": [float(w_m), float(h_m)],
                    "type": "window"
                })

        # --- 2. DOOR PROPS (Awnings, Signs) ---
        door_mask = np.logical_or(mask == self.label_door, mask == self.label_gate).astype(np.uint8)
        contours_d, _ = cv2.findContours(door_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for idx, cnt in enumerate(contours_d):
            area = cv2.contourArea(cnt)
            if area < 80:
                continue
                
            x_px, y_px, w_cnt, h_cnt = cv2.boundingRect(cnt)
            
            u_min = x_px / float(w_px)
            u_max = (x_px + w_cnt) / float(w_px)
            v_min = y_px / float(h_px)
            v_max = (y_px + h_cnt) / float(h_px)
            
            u_ctr = (u_min + u_max) / 2.0
            
            # Position at door center horizontal, but top edge for door signs/awnings
            pos_2d = A + u_ctr * vec_ab
            top_z = base_z + (1.0 - v_min) * height
            door_pos = [float(pos_2d[0]), float(pos_2d[1]), float(top_z)]
            
            w_m = w_cnt / float(w_px) * length
            h_m = h_cnt / float(h_px) * height
            
            # Spawn a sign or awning above the door
            sign_pos = [float(pos_2d[0] + 0.05 * normal[0]), float(pos_2d[1] + 0.05 * normal[1]), float(top_z + 0.2)]
            props.append({
                "facade_id": facade_id,
                "prop_type": "sign",
                "position": sign_pos,
                "rotation": [0.0, 0.0, float(yaw)],
                "scale": [1.0, 1.0, 1.0],
                "size_m": [float(w_m), float(h_m)],
                "type": "door"
            })
            
        return props
