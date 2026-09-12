import subprocess
import json
import os

def load_env():
    """Loads environment variables from .env file if it exists."""
    possible_paths = [
        ".env",
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    ]
    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        if "=" in line:
                            key, val = line.split("=", 1)
                            key = key.strip()
                            val = val.strip()
                            # Strip quotes if any
                            if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                                val = val[1:-1]
                            os.environ[key] = val
                break
            except Exception as e:
                print(f"[Warning] Failed to read .env file at {path}: {e}")

def main():    
    with open("data/facades_cache.json", "r") as f:
        facades = json.load(f)

    # Get 10 sample images
    sample_files = []
    for k, v in facades.items():
        if k.startswith("block_lat_32.57293_lon_-116.62685_facade_"):
            pid = v["pano_id"]
            hdg = v["heading"]
            img = f"data/screenshots/pano/{pid}_yaw_{hdg:.2f}.png"
            if img not in sample_files:
                sample_files.append(img)
            if len(sample_files) >= 5:
                break

    print(f"Testing transfer of {len(sample_files)} sample files...")
    file_list_str = "\n".join(sample_files) + "\n"

    # Test SSH tar with stdin
    cmd = f'ssh -o ConnectTimeout=15 {os.environ.get("REMOTE_HOST")} "wsl bash -c \\"cd {os.environ.get("REMOTE_PATH")} && tar -czf - -T -\\"" | tar -xzf -'
    print("Running cmd:", cmd)
    res = subprocess.run(cmd, input=file_list_str, shell=True, capture_output=True, text=True)
    print("Return code:", res.returncode)
    print("Stdout:", res.stdout)
    print("Stderr:", res.stderr)

if __name__ == "__main__":
    load_env()
    main()
