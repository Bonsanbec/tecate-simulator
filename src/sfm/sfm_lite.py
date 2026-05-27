import math
import cv2
import numpy as np

class SfMLite:
    """
    A modular, classical Structure-from-Motion (SfM-lite) pipeline in OpenCV.
    Extracts features, finds pairwise correspondences, computes essential matrices,
    recovers relative camera poses, and triangulates sparse 3D points.
    """
    def __init__(self, feature_type: str = "ORB"):
        self.feature_type = feature_type
        if feature_type == "SIFT":
            self.detector = cv2.SIFT_create()
            self.matcher = cv2.BFMatcher(cv2.NORM_L2, crossCheck=False)
        else:
            self.detector = cv2.ORB_create(nfeatures=1500)
            self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
            
        # Camera Intrinsics (K) for a standard 640x640 perspective viewpoint
        # Assuming f ~ 320 pixels (90 degree FOV), optical center at (320, 320)
        self.focal_length = 320.0
        self.principal_point = (320.0, 320.0)
        self.K = np.array([
            [self.focal_length, 0.0, self.principal_point[0]],
            [0.0, self.focal_length, self.principal_point[1]],
            [0.0, 0.0, 1.0]
        ], dtype=np.float32)

    def extract_features(self, img) -> tuple[list, np.ndarray]:
        """Detects keypoints and descriptors in the perspective image."""
        cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
        kp, des = self.detector.detectAndCompute(cv_img, None)
        return kp, des

    def match_features(self, des1: np.ndarray, des2: np.ndarray) -> list[cv2.DMatch]:
        """Matches descriptors between two images with Lowe's ratio test filter."""
        if des1 is None or des2 is None or len(des1) == 0 or len(des2) == 0:
            return []
            
        raw_matches = self.matcher.knnMatch(des1, des2, k=2)
        
        # Apply ratio test to filter out ambiguous matches
        good_matches = []
        for m_pair in raw_matches:
            if len(m_pair) == 2:
                m, n = m_pair
                if m.distance < 0.75 * n.distance:
                    good_matches.append(m)
                    
        return good_matches

    def reconstruct_pair(self, 
                         img1, 
                         img2, 
                         camera_pose1: dict, 
                         camera_pose2: dict) -> tuple[np.ndarray, np.ndarray, list]:
        """
        Runs SfM on two adjacent perspective views.
        1. Feature matching
        2. Essential Matrix estimation (cv2.findEssentialMat)
        3. Pose recovery (cv2.recoverPose)
        4. Triangulation (cv2.triangulatePoints)
        5. Transformation to global local Cartesian space.
        """
        kp1, des1 = self.extract_features(img1)
        kp2, des2 = self.extract_features(img2)
        
        good_matches = self.match_features(des1, des2)
        
        # We need at least 8 matches for the fundamental/essential matrix
        if len(good_matches) < 15:
            # Fall back to an empty point cloud if matches are too sparse
            return np.zeros((0, 3)), np.zeros((0, 3)), []
            
        pts1 = np.float32([kp1[m.queryIdx].pt for m in good_matches])
        pts2 = np.float32([kp2[m.trainIdx].pt for m in good_matches])
        
        # Estimate Essential Matrix
        E, mask = cv2.findEssentialMat(
            pts1, pts2, 
            cameraMatrix=self.K, 
            method=cv2.RANSAC, 
            prob=0.99, 
            threshold=1.0
        )
        
        if E is None or E.shape != (3, 3):
            return np.zeros((0, 3)), np.zeros((0, 3)), []
            
        # Filter matches based on RANSAC inlier mask
        inlier_mask = mask.ravel() == 1
        pts1_inliers = pts1[inlier_mask]
        pts2_inliers = pts2[inlier_mask]
        inlier_matches = [m for idx, m in enumerate(good_matches) if inlier_mask[idx]]
        
        if len(pts1_inliers) < 8:
            return np.zeros((0, 3)), np.zeros((0, 3)), []
            
        # Recover relative pose R and t
        _, R, t, _ = cv2.recoverPose(E, pts1_inliers, pts2_inliers, cameraMatrix=self.K)
        
        # Define projection matrices
        # P1 = K [I | 0]
        # P2 = K [R | t]
        P1 = np.dot(self.K, np.hstack((np.eye(3), np.zeros((3, 1)))))
        P2 = np.dot(self.K, np.hstack((R, t)))
        
        # Triangulate points
        pts4D = cv2.triangulatePoints(P1, P2, pts1_inliers.T, pts2_inliers.T)
        # Convert homogeneous coordinates to 3D Cartesian in camera 1 space
        pts3D_cam = (pts4D[:3] / pts4D[3]).T
        
        # Filter points that are behind either camera (Z <= 0) or are unreasonably far (Z > 40 meters)
        # In our cropped facade view, Z is the distance from camera to the wall (should be 2 to 25 meters)
        valid_indices = []
        for i, pt in enumerate(pts3D_cam):
            # Transform point to camera 2 space to check depth there as well
            pt2 = np.dot(R, pt) + t.ravel()
            if pt[2] > 1.0 and pt[2] < 30.0 and pt2[2] > 1.0 and pt2[2] < 30.0:
                valid_indices.append(i)
                
        if len(valid_indices) == 0:
            return np.zeros((0, 3)), np.zeros((0, 3)), []
            
        pts3D_cam = pts3D_cam[valid_indices]
        
        # Extract RGB colors for each point from the first image
        pts_pixels = pts1_inliers[valid_indices].astype(int)
        colors = []
        img1_np = np.array(img1)
        for px, py in pts_pixels:
            px = np.clip(px, 0, img1_np.shape[1] - 1)
            py = np.clip(py, 0, img1_np.shape[0] - 1)
            colors.append(img1_np[py, px])
        colors = np.array(colors, dtype=np.float32) / 255.0
        
        # Transform 3D points from Camera 1 coordinate system to Global Cartesian space
        # Camera 1 global pose
        c1_x, c1_y = camera_pose1["x"], camera_pose1["y"]
        c1_heading = math.radians(camera_pose1["heading"])
        
        # In Camera 1 coordinate system:
        # Z is forward optical axis (orthogonal to the street if looking at facade, i.e., in direction of heading)
        # X is horizontal (along the street direction)
        # Y is vertical (upward)
        # Let's map this properly to Global Local grid:
        pts3D_global = []
        for pt in pts3D_cam:
            # Relative rotation to global
            # If camera heading is theta, the optical axis points at heading
            # pt[0] is X (horizontal in image plane, meaning along the street)
            # pt[1] is Y (vertical/upward)
            # pt[2] is Z (depth/optical axis, meaning outward/inward toward facade)
            
            # Let's rotate the 2D planar vector (pt[0], pt[2]) by the camera yaw heading
            angle = c1_heading
            cos_a = math.cos(angle)
            sin_a = math.sin(angle)
            
            # pt[2] (depth) is forward (along optical axis)
            # pt[0] is rightward (orthogonal to optical axis)
            # In world Cartesian (meters):
            wx = c1_x + (pt[2] * cos_a - pt[0] * sin_a)
            wy = c1_y + (pt[2] * sin_a + pt[0] * cos_a)
            wz = pt[1]  # Elevation relative to road level
            
            pts3D_global.append([wx, wy, wz])
            
        return np.array(pts3D_global), colors, [inlier_matches[idx] for idx in valid_indices]
