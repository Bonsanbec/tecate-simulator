import os
import json
import subprocess
import shutil

def main():
    target_dir = "scratch/staging/bloque_alcaldia"
    os.makedirs(target_dir, exist_ok=True)

    with open('scratch/cache/facades_cache.json') as f:
        facades = json.load(f)

    block_prefix = 'block_lat_32.57293_lon_-116.62685'
    block_facades = [v for k, v in facades.items() if k.startswith(block_prefix)]

    pairs = sorted(list(set((v['pano_id'], f"{v['heading']:.2f}") for v in block_facades)))
    all_filenames = [f"{p[0]}_yaw_{p[1]}.png" for p in pairs]

    # Also check if any existing images in scratch/staging can be copied
    for root, dirs, files in os.walk('scratch/staging'):
        if root == target_dir:
            continue
        for fn in files:
            if fn in all_filenames:
                dest = os.path.join(target_dir, fn)
                if not os.path.exists(dest):
                    src = os.path.join(root, fn)
                    shutil.copy2(src, dest)
                    print(f"Copied from staging: {fn}")

    existing = set(os.listdir(target_dir))
    to_download = [fn for fn in all_filenames if fn not in existing]

    print(f"Total images for block: {len(all_filenames)}")
    print(f"Already in {target_dir}: {len(all_filenames) - len(to_download)}")
    print(f"Remaining to download: {len(to_download)}")

    if not to_download:
        print("All images already staged!")
        return

    host = "HakkinDavid@hakkin.tail4b53f5.ts.net"
    remote_base = "D:/tecate-backup/data/screenshots/pano"
    batch_size = 10

    for i in range(0, len(to_download), batch_size):
        batch = to_download[i:i+batch_size]
        remote_paths = [f"{host}:{remote_base}/{fn}" for fn in batch]
        cmd = ["scp", "-o", "ConnectTimeout=15", "-q"] + remote_paths + [target_dir]
        print(f"Downloading batch {i//batch_size + 1}/{(len(to_download)+batch_size-1)//batch_size} ({len(batch)} files)...")
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"Batch failed, trying file by file...")
            for fn in batch:
                dest_file = os.path.join(target_dir, fn)
                if os.path.exists(dest_file):
                    continue
                single_cmd = ["scp", "-o", "ConnectTimeout=15", "-q", f"{host}:{remote_base}/{fn}", target_dir]
                s_res = subprocess.run(single_cmd, capture_output=True, text=True)
                if s_res.returncode == 0:
                    print(f"  Downloaded: {fn}")
                else:
                    print(f"  Failed: {fn} ({s_res.stderr.strip()})")

    final_count = len([f for f in os.listdir(target_dir) if f.endswith('.png')])
    print(f"Staging complete! Total PNGs in {target_dir}: {final_count}")

if __name__ == "__main__":
    main()
