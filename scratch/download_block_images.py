import os
import json
import subprocess
import sys

def main():
    with open('scratch/cache/facades_cache.json') as f:
        facades = json.load(f)

    b_facades = [v for k, v in facades.items() if 'block_lat_32.57328_lon_-116.62516' in k]

    pairs = sorted(list(set((v['pano_id'], f"{v['heading']:.2f}") for v in b_facades)))
    all_filenames = [f"{p[0]}_yaw_{p[1]}.png" for p in pairs]

    target_dir = "scratch/staging/manzana_central"
    os.makedirs(target_dir, exist_ok=True)

    # Check which ones are already downloaded
    existing = set(os.listdir(target_dir))
    to_download = [fn for fn in all_filenames if fn not in existing]

    print(f"Total images for block: {len(all_filenames)}")
    print(f"Already in {target_dir}: {len(all_filenames) - len(to_download)}")
    print(f"Remaining to download: {len(to_download)}")

    if not to_download:
        print("All images already staged!")
        return

    # Download in batches of 10 using scp
    batch_size = 10
    host = "HakkinDavid@hakkin.tail4b53f5.ts.net"
    remote_base = "D:/tecate-backup/data/screenshots/pano"

    for i in range(0, len(to_download), batch_size):
        batch = to_download[i:i+batch_size]
        remote_paths = [f"{host}:{remote_base}/{fn}" for fn in batch]
        cmd = ["scp", "-o", "ConnectTimeout=15", "-q"] + remote_paths + [target_dir]
        print(f"Downloading batch {i//batch_size + 1}/{(len(to_download)+batch_size-1)//batch_size} ({len(batch)} files)...")
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"Error in batch: {res.stderr}")
            # Try file by file in this batch
            for fn in batch:
                single_cmd = ["scp", "-o", "ConnectTimeout=15", "-q", f"{host}:{remote_base}/{fn}", target_dir]
                s_res = subprocess.run(single_cmd, capture_output=True, text=True)
                if s_res.returncode == 0:
                    print(f"  Downloaded: {fn}")
                else:
                    print(f"  Failed: {fn}")

    current_count = len([f for f in os.listdir(target_dir) if f.endswith('.png')])
    print(f"Download complete. Total PNGs in {target_dir}: {current_count}")

if __name__ == "__main__":
    main()
