import os
import subprocess
import shutil

def main():
    print("Testing COLMAP execution on case study images...")
    
    # Paths
    img_dir = "data/case_study/target_images"
    sfm_dir = "data/case_study/sfm_test"
    db_path = os.path.join(sfm_dir, "database.db")
    sparse_dir = os.path.join(sfm_dir, "sparse")
    
    # Cleanup previous run
    if os.path.exists(sfm_dir):
        shutil.rmtree(sfm_dir)
    os.makedirs(sfm_dir, exist_ok=True)
    os.makedirs(sparse_dir, exist_ok=True)
    
    # 1. Database creation
    # Implicitly handled by feature_extractor if not exists
    
    # 2. Feature Extraction
    print("Running feature extractor...")
    cmd = [
        "colmap", "feature_extractor",
        "--database_path", db_path,
        "--image_path", img_dir,
        "--ImageReader.camera_model", "SIMPLE_PINHOLE"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    print("Feature extractor exit code:", res.returncode)
    
    # 3. Matching
    print("Running exhaustive matcher...")
    cmd = [
        "colmap", "exhaustive_matcher",
        "--database_path", db_path
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    print("Matcher exit code:", res.returncode)
    
    # 4. Reconstruction (Mapper)
    print("Running mapper...")
    cmd = [
        "colmap", "mapper",
        "--database_path", db_path,
        "--image_path", img_dir,
        "--output_path", sparse_dir
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    print("Mapper exit code:", res.returncode)
    
    # Check output
    recon_0 = os.path.join(sparse_dir, "0")
    if os.path.exists(recon_0):
        print("Success! Reconstructed model folder '0' exists.")
        # Convert to text to check points
        cmd = [
            "colmap", "model_converter",
            "--input_path", recon_0,
            "--output_path", recon_0,
            "--output_type", "TXT"
        ]
        subprocess.run(cmd, capture_output=True)
        
        pts_file = os.path.join(recon_0, "points3D.txt")
        if os.path.exists(pts_file):
            with open(pts_file) as f:
                lines = [l for l in f if not l.startswith("#") and l.strip()]
            print(f"Number of reconstructed 3D points: {len(lines)}")
        else:
            print("points3D.txt not found!")
    else:
        print("Mapper failed to produce a reconstruction.")

if __name__ == "__main__":
    main()
