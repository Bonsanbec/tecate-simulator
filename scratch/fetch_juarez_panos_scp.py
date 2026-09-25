import json
import os
import subprocess
import time

def main():
    target_dir = os.path.abspath("scratch/staging/juarez_235")
    os.makedirs(target_dir, exist_ok=True)

    with open("scratch/cache/facades_cache.json", "r", encoding="utf-8") as f:
        facades = json.load(f)

    block_id = "block_lat_32.57381_lon_-116.62658"
    sub = {k: v for k, v in facades.items() if block_id in k}

    unique_images = sorted(list({f"{v['pano_id']}_yaw_{v['heading']:.2f}.png" for v in sub.values()}))
    print(f"Total unique facade images for block {block_id}: {len(unique_images)}")

    remote_host = "HakkinDavid@hakkin.tail4b53f5.ts.net"
    remote_base = "D:/tecate-backup/data/screenshots/pano"

    to_download = []
    already_present = []
    for img_name in unique_images:
        dst_path = os.path.join(target_dir, img_name)
        if os.path.exists(dst_path) and os.path.getsize(dst_path) > 10000:
            already_present.append(img_name)
        else:
            to_download.append(img_name)

    print(f"Already present: {len(already_present)}")
    print(f"To download: {len(to_download)}")

    if not to_download:
        print("All images are already staged.")
        return

    # Download in batches of 10 files using scp
    batch_size = 10
    t0 = time.time()
    for i in range(0, len(to_download), batch_size):
        batch = to_download[i:i+batch_size]
        sources = [f"{remote_host}:{remote_base}/{img}" for img in batch]
        cmd = ["scp", "-q"] + sources + [target_dir]
        print(f"Downloading batch {i//batch_size + 1}/{(len(to_download)-1)//batch_size + 1} ({len(batch)} files)...")
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"Batch failed: {res.stderr}")
            # Try file by file fallback
            for img in batch:
                single_src = f"{remote_host}:{remote_base}/{img}"
                res_single = subprocess.run(["scp", "-q", single_src, target_dir], capture_output=True, text=True)
                if res_single.returncode != 0:
                    print(f"Failed to fetch {img}: {res_single.stderr}")
                else:
                    print(f"  Fetched {img}")

    dt = time.time() - t0
    print(f"Completed download of {len(to_download)} files in {dt:.2f}s.")

if __name__ == "__main__":
    main()
