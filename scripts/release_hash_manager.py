#!/usr/bin/env python3
"""
scripts/release_hash_manager.py
--------------------------------
Gestor criptográfico y validador de integridad para releases locales de Tecate Simulator:
1. Hash de Fuentes: Calcula el hash SHA-256 compuesto de las fuentes de godot_project/ y assets.
2. Caché Local: Evita re-exportar binarios si el artefacto existe y las fuentes no cambiaron.
3. Generación de Sumas: Produce godot_project/build/SHA256SUMS.txt (con soporte de merge para upsert).
4. Validación Remota: Compara los artefactos contra el último release de GitHub:
   - Si NINGÚN hash coincide: Autoriza la creación de un nuevo release (código 0).
   - Si ALGÚN hash coincide pero otros cambiaron: Indica UPSERT en el release existente (código 1).
   - Si TODOS los hashes coinciden: Indica que todo está al día y no hace nada (código 2).
"""

import os
import sys
import json
import hashlib
import argparse
from datetime import datetime, timezone

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GODOT_DIR = os.path.join(WORKSPACE_ROOT, "godot_project")
BUILD_DIR = os.path.join(GODOT_DIR, "build")
MANIFEST_PATH = os.path.join(BUILD_DIR, ".export_manifest.json")
CHECKSUMS_FILE = os.path.join(BUILD_DIR, "SHA256SUMS.txt")

TARGET_FILES = {
    "macos": os.path.join(BUILD_DIR, "macos", "tecate-macos.zip"),
    "windows": os.path.join(BUILD_DIR, "windows", "tecate-windows.zip"),
    "linux": os.path.join(BUILD_DIR, "linux", "tecate-linux.zip"),
    "android": os.path.join(BUILD_DIR, "android", "tecate.apk"),
    "ios": os.path.join(BUILD_DIR, "ios", "tecate-ios.zip"),
}

def compute_file_sha256(filepath):
    """Calcula SHA-256 de un archivo en bloques de 1MB."""
    if not os.path.isfile(filepath):
        return None
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(1048576):
            h.update(chunk)
    return h.hexdigest()

def compute_source_hash():
    """
    Calcula un hash compuesto ultra-rápido de todo el contenido de godot_project/
    (excluyendo .godot/ y build/) más el manifiesto de horneado si existe.
    """
    h = hashlib.sha256()
    
    # 1. Escaneo de godot_project/
    for root, dirs, files in os.walk(GODOT_DIR):
        dirs[:] = [d for d in dirs if d not in (".godot", "build", ".tmp")]
        for fname in sorted(files):
            if fname.startswith(".DS_Store") or fname.endswith(".log"):
                continue
            fpath = os.path.join(root, fname)
            try:
                st = os.stat(fpath)
                rel = os.path.relpath(fpath, WORKSPACE_ROOT)
                h.update(f"{rel}:{st.st_size}:{st.st_mtime_ns}".encode("utf-8"))
            except OSError:
                continue

    # 2. Manifiesto de bake de Blender
    bake_manifest = os.path.join(WORKSPACE_ROOT, "blender_assets", ".bake_manifest.json")
    if os.path.exists(bake_manifest):
        try:
            st = os.stat(bake_manifest)
            h.update(f"bake_manifest:{st.st_size}:{st.st_mtime_ns}".encode("utf-8"))
        except OSError:
            pass

    return h.hexdigest()

def load_manifest():
    if os.path.isfile(MANIFEST_PATH):
        try:
            with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"source_hash": None, "targets": {}}

def save_manifest(data):
    os.makedirs(BUILD_DIR, exist_ok=True)
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def is_target_cached(target):
    """Verifica si el binario local está al día con el estado actual de las fuentes."""
    target_file = TARGET_FILES.get(target)
    if not target_file or not os.path.isfile(target_file):
        return False, "El archivo empaquetado no existe en disco."

    manifest = load_manifest()
    cached_source_hash = manifest.get("source_hash")
    current_source_hash = compute_source_hash()

    if not cached_source_hash or cached_source_hash != current_source_hash:
        return False, "Las fuentes del proyecto han cambiado desde la última compilación."

    target_entry = manifest.get("targets", {}).get(target, {})
    cached_file_hash = target_entry.get("sha256")
    actual_file_hash = compute_file_sha256(target_file)

    if not cached_file_hash or cached_file_hash != actual_file_hash:
        return False, "El hash del binario generado no coincide con el manifiesto local."

    return True, f"Hash de fuentes idéntico ({current_source_hash[:10]}...)"

def update_target_cache(target):
    """Actualiza la entrada del target en el manifiesto tras una compilación exitosa."""
    target_file = TARGET_FILES.get(target)
    if not target_file or not os.path.isfile(target_file):
        return False

    current_source_hash = compute_source_hash()
    actual_file_hash = compute_file_sha256(target_file)
    size_bytes = os.path.getsize(target_file)

    manifest = load_manifest()
    manifest["source_hash"] = current_source_hash
    manifest.setdefault("targets", {})[target] = {
        "file": os.path.relpath(target_file, WORKSPACE_ROOT),
        "sha256": actual_file_hash,
        "size_bytes": size_bytes,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    save_manifest(manifest)
    return True

def parse_sums(text):
    """Convierte texto de formato sha256sum en dict {basename: sha256}."""
    sums = {}
    if not text:
        return sums
    for line in text.strip().splitlines():
        parts = line.strip().split()
        if len(parts) >= 2:
            sums[os.path.basename(parts[1])] = parts[0].lower()
    return sums

def generate_checksums(file_list, remote_sums_text=None):
    """
    Genera archivo godot_project/build/SHA256SUMS.txt.
    Si se proporciona remote_sums_text, fusiona las sumas para preservar
    los hashes de archivos remotos no modificados durante un upsert.
    """
    os.makedirs(BUILD_DIR, exist_ok=True)
    merged_sums = {}
    if remote_sums_text:
        merged_sums = parse_sums(remote_sums_text)

    for f in file_list:
        if os.path.isfile(f):
            h = compute_file_sha256(f)
            bname = os.path.basename(f)
            merged_sums[bname] = h

    lines = [f"{merged_sums[k]}  {k}" for k in sorted(merged_sums.keys())]
    content = "\n".join(lines) + "\n"
    with open(CHECKSUMS_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    return CHECKSUMS_FILE

def compare_remote_checksums(local_files, remote_sums_text):
    """
    Compara los hashes locales con los del último release en GitHub.
    Determina si:
      - CREATE_NEW: Ningún hash coincide (o no hay sumas remotas).
      - UPSERT_EXISTING: Algún hash coincide pero otros cambiaron o son nuevos.
      - NOTHING_TO_DO: Todos los binarios evaluados coinciden exactamente con el release remoto.
    """
    remote_sums = parse_sums(remote_sums_text)
    if not remote_sums:
        return {
            "action": "CREATE_NEW",
            "reason": "No hay sumas de verificación registradas en el release remoto.",
            "matches": [],
            "differs": [],
            "new_files": [{"path": f, "file": os.path.basename(f)} for f in local_files],
            "changed_files": [f for f in local_files],
            "any_match": False,
            "none_match": True,
            "all_match": False
        }

    matches = []
    differs = []
    new_files = []

    for f in local_files:
        bname = os.path.basename(f)
        local_hash = compute_file_sha256(f)
        if bname in remote_sums:
            remote_hash = remote_sums[bname]
            if local_hash == remote_hash:
                matches.append({"path": f, "file": bname, "sha256": local_hash})
            else:
                differs.append({"path": f, "file": bname, "local": local_hash, "remote": remote_hash})
        else:
            new_files.append({"path": f, "file": bname, "sha256": local_hash})

    changed_files = [d["path"] for d in differs] + [n["path"] for n in new_files]
    any_match = len(matches) > 0
    none_match = len(matches) == 0
    all_match = (len(matches) == len(local_files)) and (len(changed_files) == 0)

    if all_match:
        action = "NOTHING_TO_DO"
        reason = "Todos los binarios coinciden con los existentes en el release remoto."
    elif any_match and len(changed_files) > 0:
        action = "UPSERT_EXISTING"
        reason = "Al menos un binario coincide, pero otros cambiaron o son nuevos (requiere upsert)."
    else:
        action = "CREATE_NEW"
        reason = "Ningún binario coincide con los existentes en el release remoto."

    return {
        "action": action,
        "reason": reason,
        "matches": matches,
        "differs": differs,
        "new_files": new_files,
        "changed_files": changed_files,
        "any_match": any_match,
        "none_match": none_match,
        "all_match": all_match
    }

def main():
    parser = argparse.ArgumentParser(description="Gestor de hashes y caché para releases locales.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcomando: source-hash
    subparsers.add_parser("source-hash", help="Muestra el hash compuesto actual de las fuentes")

    # Subcomando: check-local-cache
    p_check = subparsers.add_parser("check-local-cache", help="Verifica si un target local está al día")
    p_check.add_argument("--target", required=True, choices=["macos", "windows", "linux", "android", "ios"])

    # Subcomando: update-local-cache
    p_upd = subparsers.add_parser("update-local-cache", help="Actualiza el registro de caché de un target")
    p_upd.add_argument("--target", required=True, choices=["macos", "windows", "linux", "android", "ios"])

    # Subcomando: generate-checksums
    p_sums = subparsers.add_parser("generate-checksums", help="Genera SHA256SUMS.txt")
    p_sums.add_argument("--merge-remote", default=None, help="Texto o ruta de sumas remotas a fusionar")
    p_sums.add_argument("files", nargs="+", help="Rutas de los archivos a incluir")

    # Subcomando: compare-remote
    p_comp = subparsers.add_parser("compare-remote", help="Compara artefactos locales con sumas remotas")
    p_comp.add_argument("--remote-sums", default="", help="Texto o ruta del archivo con sumas remotas")
    p_comp.add_argument("files", nargs="+", help="Rutas de los archivos locales a comparar")

    args = parser.parse_args()

    if args.command == "source-hash":
        print(compute_source_hash())

    elif args.command == "check-local-cache":
        cached, reason = is_target_cached(args.target)
        if cached:
            print(f"[CACHE_HIT] {args.target}: {reason}")
            sys.exit(0)
        else:
            print(f"[CACHE_MISS] {args.target}: {reason}")
            sys.exit(1)

    elif args.command == "update-local-cache":
        ok = update_target_cache(args.target)
        if ok:
            print(f"[CACHE_UPDATED] {args.target}")
            sys.exit(0)
        else:
            print(f"[CACHE_ERROR] No se pudo actualizar {args.target}")
            sys.exit(1)

    elif args.command == "generate-checksums":
        remote_text = args.merge_remote
        if remote_text and os.path.isfile(remote_text):
            with open(remote_text, "r", encoding="utf-8") as f:
                remote_text = f.read()
        out_path = generate_checksums(args.files, remote_text)
        print(out_path)

    elif args.command == "compare-remote":
        remote_text = args.remote_sums
        if os.path.isfile(remote_text):
            with open(remote_text, "r", encoding="utf-8") as f:
                remote_text = f.read()

        result = compare_remote_checksums(args.files, remote_text)
        print(json.dumps(result, indent=2))
        
        # Códigos de salida para orquestación en bash:
        # Exit 0 -> CREATE_NEW (ningún hash coincide o release nuevo)
        # Exit 1 -> UPSERT_EXISTING (algún hash coincide y hay binarios modificados)
        # Exit 2 -> NOTHING_TO_DO (todos coinciden exactamente, release al día)
        action = result["action"]
        if action == "CREATE_NEW":
            sys.exit(0)
        elif action == "UPSERT_EXISTING":
            sys.exit(1)
        else:
            sys.exit(2)

if __name__ == "__main__":
    main()
