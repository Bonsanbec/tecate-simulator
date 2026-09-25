import json
import os
import shutil
import time

def main():
    target_dir = os.path.abspath("scratch/staging/juarez_235")
    os.makedirs(target_dir, exist_ok=True)

    with open("scratch/cache/facades_cache.json", "r", encoding="utf-8") as f:
        facades = json.load(f)

    block_id = "block_lat_32.57381_lon_-116.62658"
    sub = {k: v for k, v in facades.items() if block_id in k}

    unique_images = sorted(list({f"{v['pano_id']}_yaw_{v['heading']:.2f}.png" for v in sub.values()}))
    print(f"Total unique images to stage: {len(unique_images)}")

    src_dir = "/Volumes/tecate-backup/data/screenshots/pano"

    copied = 0
    already_present = 0
    errors = []

    t0 = time.time()
    for idx, img_name in enumerate(unique_images, 1):
        dst_path = os.path.join(target_dir, img_name)
        if os.path.exists(dst_path) and os.path.getsize(dst_path) > 10000:
            already_present += 1
            continue

        src_path = os.path.join(src_dir, img_name)
        try:
            shutil.copyfile(src_path, dst_path)
            copied += 1
            print(f"[{idx}/{len(unique_images)}] Copied {img_name} ({os.path.getsize(dst_path):,} bytes)")
        except Exception as e:
            errors.append((img_name, str(e)))
            print(f"[{idx}/{len(unique_images)}] Failed {img_name}: {e}")

    dt = time.time() - t0
    print("\n=== Resumen de Transferencia ===")
    print(f"Directorio destino: {target_dir}")
    print(f"Total imágenes: {len(unique_images)}")
    print(f"Ya presentes: {already_present}")
    print(f"Copiadas exitosamente: {copied}")
    print(f"Errores: {len(errors)}")
    print(f"Tiempo total: {dt:.2f} segundos")

if __name__ == "__main__":
    main()
