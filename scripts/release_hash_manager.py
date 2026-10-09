#!/usr/bin/env python3
"""
scripts/release_hash_manager.py
--------------------------------
Gestor criptográfico y Single Source of Truth (SSOT) para releases de Tecate Simulator.

Responsabilidades:
1. Hash de Fuentes: Calcula el hash SHA-256 compuesto de las fuentes de godot_project/ y assets.
2. Caché Local: Evita re-exportar binarios si el artefacto existe y las fuentes no cambiaron.
3. Evaluación y Manifiesto de Release (SSOT):
   - Descarga e inspecciona `version_manifest.json` del último release en GitHub.
   - Compara los hashes locales contra los remotos por cada plataforma.
   - Si NADA cambió: Detiene la operación (NOTHING_TO_DO).
   - Si cambiaron binarios (o se añadieron nuevos):
     - Crea la nueva versión con el tag actual (YY.MM.DD-HH).
     - Identifica los binarios que SÍ cambiaron para subirlos (UPDATED).
     - Identifica los binarios intactos para referenciarlos a su release de origen (PRESERVED),
       evitando subirlos nuevamente.
     - Genera el nuevo `version_manifest.json`, `SHA256SUMS.txt` y notas de release en Markdown.
"""

import os
import sys
import json
import hashlib
import argparse
import subprocess
import re
from datetime import datetime, timezone

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GODOT_DIR = os.path.join(WORKSPACE_ROOT, "godot_project")
BUILD_DIR = os.path.join(GODOT_DIR, "build")
LOCAL_MANIFEST_PATH = os.path.join(BUILD_DIR, ".export_manifest.json")
VERSION_MANIFEST_FILE = os.path.join(BUILD_DIR, "version_manifest.json")
RELEASE_NOTES_FILE = os.path.join(BUILD_DIR, "release_notes.md")

TARGET_CONFIG = {
    "macos": {
        "filename": "tecate-macos.zip",
        "path": os.path.join(BUILD_DIR, "macos", "tecate-macos.zip"),
        "display_name": "macOS (Apple Silicon & Intel Universal)",
    },
    "windows": {
        "filename": "tecate-windows.zip",
        "path": os.path.join(BUILD_DIR, "windows", "tecate-windows.zip"),
        "display_name": "Windows (x86_64 Desktop)",
    },
    "linux": {
        "filename": "tecate-linux.zip",
        "path": os.path.join(BUILD_DIR, "linux", "tecate-linux.zip"),
        "display_name": "Linux (x86_64)",
    },
    "android": {
        "filename": "tecate.apk",
        "path": os.path.join(BUILD_DIR, "android", "tecate.apk"),
        "display_name": "Android (arm64-v8a APK)",
    },
    "ios": {
        "filename": "tecate-ios.zip",
        "path": os.path.join(BUILD_DIR, "ios", "tecate-ios.zip"),
        "display_name": "iOS (Xcode Project Archive)",
    },
}

# Invertir mapa para identificar plataforma por nombre de archivo
FILENAME_TO_TARGET = {cfg["filename"]: tgt for tgt, cfg in TARGET_CONFIG.items()}


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

    bake_manifest = os.path.join(WORKSPACE_ROOT, "blender_assets", ".bake_manifest.json")
    if os.path.exists(bake_manifest):
        try:
            st = os.stat(bake_manifest)
            h.update(f"bake_manifest:{st.st_size}:{st.st_mtime_ns}".encode("utf-8"))
        except OSError:
            pass

    return h.hexdigest()


def load_local_manifest():
    if os.path.isfile(LOCAL_MANIFEST_PATH):
        try:
            with open(LOCAL_MANIFEST_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"source_hash": None, "targets": {}}


def save_local_manifest(data):
    os.makedirs(BUILD_DIR, exist_ok=True)
    with open(LOCAL_MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def is_target_cached(target):
    """Verifica si el binario local está al día con el estado actual de las fuentes."""
    cfg = TARGET_CONFIG.get(target)
    if not cfg:
        return False, "Target desconocido."
    target_file = cfg["path"]
    if not os.path.isfile(target_file):
        return False, "El archivo empaquetado no existe en disco."

    manifest = load_local_manifest()
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
    cfg = TARGET_CONFIG.get(target)
    if not cfg:
        return False
    target_file = cfg["path"]
    if not os.path.isfile(target_file):
        return False

    current_source_hash = compute_source_hash()
    actual_file_hash = compute_file_sha256(target_file)
    size_bytes = os.path.getsize(target_file)

    manifest = load_local_manifest()
    manifest["source_hash"] = current_source_hash
    manifest.setdefault("targets", {})[target] = {
        "file": os.path.relpath(target_file, WORKSPACE_ROOT),
        "sha256": actual_file_hash,
        "size_bytes": size_bytes,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    save_local_manifest(manifest)
    return True


def get_repo_slug():
    """Detecta el repositorio 'owner/repo' configurado en git origin."""
    try:
        res = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True, text=True, check=True
        )
        url = res.stdout.strip()
        m = re.search(r"github\.com[:/]([^/]+)/([^/.]+)", url)
        if m:
            return f"{m.group(1)}/{m.group(2)}"
    except Exception:
        pass
    return "Bonsanbec/tecate-simulator"


def get_git_commit():
    """Obtiene el hash SHA corto y largo del commit actual."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True
        )
        return res.stdout.strip()
    except Exception:
        return "unknown"


def evaluate_release(local_files, remote_manifest_text, new_tag, force=False):
    """
    Función central de evaluación de release basada en version_manifest.json (SSOT).
    Compara los binarios locales con el manifiesto del último release.
    """
    os.makedirs(BUILD_DIR, exist_ok=True)
    repo = get_repo_slug()
    commit_sha = get_git_commit()
    now_utc = datetime.now(timezone.utc).isoformat()

    # Parsear manifiesto remoto
    remote_manifest = {}
    if remote_manifest_text:
        try:
            remote_manifest = json.loads(remote_manifest_text)
        except Exception:
            pass

    remote_binaries = remote_manifest.get("binaries", {})
    new_binaries = {}
    files_to_upload = []
    updated_platforms = []
    preserved_platforms = []

    # Evaluar cada binario local proporcionado
    for fpath in local_files:
        if not os.path.isfile(fpath):
            continue

        fname = os.path.basename(fpath)
        platform_id = FILENAME_TO_TARGET.get(fname, os.path.splitext(fname)[0])
        display_name = TARGET_CONFIG.get(platform_id, {}).get("display_name", platform_id)
        local_hash = compute_file_sha256(fpath)
        size_bytes = os.path.getsize(fpath)

        remote_entry = remote_binaries.get(platform_id, {})
        remote_hash = remote_entry.get("sha256")

        # Comprobar si coincide con el release remoto
        if (not force) and remote_hash and (local_hash == remote_hash):
            # PRESERVED: El binario es idéntico al del release previo.
            # No se sube de nuevo; se referencia el URL y el origen anterior.
            origin_tag = remote_entry.get("origin_release", remote_manifest.get("release_version", new_tag))
            download_url = remote_entry.get("download_url") or f"https://github.com/{repo}/releases/download/{origin_tag}/{fname}"

            new_binaries[platform_id] = {
                "filename": fname,
                "display_name": display_name,
                "sha256": local_hash,
                "size_bytes": size_bytes,
                "status": "PRESERVED",
                "origin_release": origin_tag,
                "download_url": download_url
            }
            preserved_platforms.append(platform_id)
        else:
            # UPDATED: El binario cambió, es nuevo, o se especificó --force.
            # Se sube al nuevo release.
            download_url = f"https://github.com/{repo}/releases/download/{new_tag}/{fname}"
            new_binaries[platform_id] = {
                "filename": fname,
                "display_name": display_name,
                "sha256": local_hash,
                "size_bytes": size_bytes,
                "status": "UPDATED",
                "origin_release": new_tag,
                "download_url": download_url
            }
            files_to_upload.append(fpath)
            updated_platforms.append(platform_id)

    # Preservar plataformas que existían en el release remoto pero no se compilaron en esta corrida
    for remote_pid, remote_info in remote_binaries.items():
        if remote_pid not in new_binaries:
            new_binaries[remote_pid] = {
                "filename": remote_info.get("filename", f"tecate-{remote_pid}.zip"),
                "display_name": remote_info.get("display_name", remote_pid),
                "sha256": remote_info.get("sha256", ""),
                "size_bytes": remote_info.get("size_bytes", 0),
                "status": "PRESERVED",
                "origin_release": remote_info.get("origin_release", remote_manifest.get("release_version", new_tag)),
                "download_url": remote_info.get("download_url", "")
            }
            preserved_platforms.append(remote_pid)

    # Determinar acción
    if len(updated_platforms) == 0 and not force:
        action = "NOTHING_TO_DO"
        reason = "Todos los binarios evaluados son idénticos a los del último release en GitHub."
    else:
        action = "CREATE_RELEASE"
        reason = f"Se publicará el release {new_tag} con {len(updated_platforms)} binario(s) actualizado(s) y {len(preserved_platforms)} preservado(s)."

    # Construir el nuevo version_manifest.json (SSOT)
    manifest_data = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "format_version": "1.0",
        "release_version": new_tag,
        "published_at_utc": now_utc,
        "git_commit": commit_sha,
        "repository": repo,
        "binaries": new_binaries
    }

    with open(VERSION_MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    # Generar Release Notes en Markdown con enlaces cruzados de descarga
    notes_lines = [
        "| Plataforma | Archivo | Tamaño | SHA-256 | Descarga |",
        "| :--- | :--- | :--- | :--- | :--- |"
    ]

    for pid in sorted(new_binaries.keys()):
        b = new_binaries[pid]
        size_mb = f"{b['size_bytes'] / (1024 * 1024):.1f} MB" if b["size_bytes"] else "N/A"
        sha_short = b["sha256"][:12] + "..." if b["sha256"] else "N/A"
        
        if b["status"] == "UPDATED":
            link_label = f"Descargar (v{new_tag})"
        else:
            link_label = f"Descargar (v{b['origin_release']})"

        url = b.get("download_url", "#")
        notes_lines.append(
            f"| **{b.get('display_name', pid)}** | `{b['filename']}` | {size_mb} | `{sha_short}` | [{link_label}]({url}) |"
        )

    with open(RELEASE_NOTES_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(notes_lines) + "\n")

    # Archivos que se deben subir físicamente al nuevo release:
    # 1. Los binarios que SÍ cambiaron
    # 2. El nuevo version_manifest.json (SSOT)
    if action == "CREATE_RELEASE":
        files_to_upload.append(VERSION_MANIFEST_FILE)

    return {
        "action": action,
        "reason": reason,
        "release_tag": new_tag,
        "updated_platforms": updated_platforms,
        "preserved_platforms": preserved_platforms,
        "files_to_upload": files_to_upload,
        "manifest_path": VERSION_MANIFEST_FILE,
        "notes_path": RELEASE_NOTES_FILE,
    }


def main():
    parser = argparse.ArgumentParser(description="Gestor criptográfico y SSOT para releases.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcomando: source-hash
    subparsers.add_parser("source-hash", help="Muestra el hash compuesto actual de las fuentes")

    # Subcomando: check-local-cache
    p_check = subparsers.add_parser("check-local-cache", help="Verifica si un target local está al día")
    p_check.add_argument("--target", required=True, choices=["macos", "windows", "linux", "android", "ios"])

    # Subcomando: update-local-cache
    p_upd = subparsers.add_parser("update-local-cache", help="Actualiza el registro de caché de un target")
    p_upd.add_argument("--target", required=True, choices=["macos", "windows", "linux", "android", "ios"])

    # Subcomando: eval-release
    p_eval = subparsers.add_parser("eval-release", help="Evalúa el release contra el version_manifest remoto (SSOT)")
    p_eval.add_argument("--remote-manifest", default="", help="Texto o ruta de version_manifest.json del release anterior")
    p_eval.add_argument("--new-tag", required=True, help="Nuevo tag de versión (YY.MM.DD-HH)")
    p_eval.add_argument("--force", action="store_true", help="Fuerza actualización de todas las plataformas")
    p_eval.add_argument("files", nargs="+", help="Rutas de los binarios locales a evaluar")

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

    elif args.command == "eval-release":
        remote_text = args.remote_manifest
        if os.path.isfile(remote_text):
            with open(remote_text, "r", encoding="utf-8") as f:
                remote_text = f.read()

        result = evaluate_release(args.files, remote_text, args.new_tag, force=args.force)
        print(json.dumps(result, indent=2))

        # Exit code: 0 -> CREATE_RELEASE, 2 -> NOTHING_TO_DO
        if result["action"] == "CREATE_RELEASE":
            sys.exit(0)
        else:
            sys.exit(2)


if __name__ == "__main__":
    main()
