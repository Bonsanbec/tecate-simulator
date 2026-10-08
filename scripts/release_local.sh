#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# scripts/release_local.sh
# ------------------------------------------------------------------------------
# Genera los binarios de release localmente con todos los assets integrados,
# los empaqueta en .zip y gestiona la publicación en GitHub Releases utilizando
# `version_manifest.json` como Single Source of Truth (SSOT):
#
# 1. Caché Local (Anti-Regeneración):
#    - Si las fuentes y assets no han cambiado y el .zip existe, omite la exportación.
#
# 2. Evaluación SSOT con Referencia Cruzada:
#    - Descarga el `version_manifest.json` del último release en GitHub.
#    - Si TODOS los binarios coinciden: Cancela la operación sin subir duplicados.
#    - Si algún binario cambió (o es nuevo):
#      - Crea una NUEVA release con el tag actual (YY.MM.DD-HH) marcada como 'latest'.
#      - Sube ÚNICAMENTE los binarios modificados/nuevos (ahorrando cientos de MB).
#      - Para los binarios no modificados, genera referencias directas de descarga
#        hacia su release de origen en las notas y en el manifiesto.
#      - Publica el nuevo `version_manifest.json` (SSOT).
#
# Uso:
#   ./scripts/release_local.sh [all|windows|macos|android|ios|linux] [VERSION_TAG] [--force]
#
# Opciones:
#   all|windows|...   Plataforma a exportar (por defecto: all).
#   VERSION_TAG       Etiqueta de versión para nuevos releases (por defecto: YY.MM.DD-HH).
#   --force, -f       Fuerza la recompilación y subida de todos los binarios.
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$WORKSPACE_ROOT"

# Parámetros y banderas
TARGET="all"
TAG=""
FORCE=false

for arg in "$@"; do
  case "$arg" in
    --help|-h)
      echo "Uso: $0 [all|windows|macos|android|ios|linux] [VERSION_TAG] [--force]"
      echo ""
      echo "Opciones:"
      echo "  all|windows|...   Plataforma a exportar (por defecto: all)."
      echo "  VERSION_TAG       Etiqueta de versión para nuevos releases (por defecto: YY.MM.DD-HH)."
      echo "  --force, -f       Fuerza la recompilación y subida ignorando las cachés."
      exit 0
      ;;
    --force|-f)
      FORCE=true
      ;;
    windows|macos|android|ios|linux|all)
      TARGET="$arg"
      ;;
    *)
      if [[ -z "$TAG" ]]; then
        TAG="$arg"
      fi
      ;;
  esac
done

if [[ -z "$TAG" ]]; then
  TAG="$(date +"%y.%m.%d-%H")"
fi

HASH_MGR="scripts/release_hash_manager.py"
chmod +x "$HASH_MGR" godot_project/export.sh

echo "================================================================="
echo "  TECATE SIMULATOR: PUBLICACIÓN LOCAL DE RELEASE (SSOT)"
echo "  Versión (Tag):     $TAG"
echo "  Objetivo export:   $TARGET"
echo "  Modo forzado:      $FORCE"
echo "================================================================="

# Determinar plataformas a procesar
TARGETS_TO_PROCESS=()
if [[ "$TARGET" == "all" ]]; then
  TARGETS_TO_PROCESS=("macos" "windows")
else
  TARGETS_TO_PROCESS=("$TARGET")
fi

# ------------------------------------------------------------------------------
# 1. Compilación modular con validación de caché local
# ------------------------------------------------------------------------------
echo "🔍 [Caché Local] Comprobando integridad de fuentes y artefactos existentes..."

for t in "${TARGETS_TO_PROCESS[@]}"; do
  if [[ "$FORCE" == false ]] && python3 "$HASH_MGR" check-local-cache --target "$t" >/dev/null 2>&1; then
    echo "🟢 [$t] Artefacto al día (las fuentes y assets no han cambiado). Omitiendo regeneración."
  else
    echo "🔨 [$t] Compilando y empaquetando binario..."
    ./godot_project/export.sh "$t"
    python3 "$HASH_MGR" update-local-cache --target "$t"
    echo "✅ [$t] Exportación completada y registrada en caché local."
  fi
done

# ------------------------------------------------------------------------------
# 2. Recolectar archivos generados
# ------------------------------------------------------------------------------
BINARY_FILES=()
for t in "${TARGETS_TO_PROCESS[@]}"; do
  case "$t" in
    macos)
      [[ -f "godot_project/build/macos/tecate-macos.zip" ]] && BINARY_FILES+=("godot_project/build/macos/tecate-macos.zip")
      ;;
    windows)
      [[ -f "godot_project/build/windows/tecate-windows.zip" ]] && BINARY_FILES+=("godot_project/build/windows/tecate-windows.zip")
      ;;
    linux)
      [[ -f "godot_project/build/linux/tecate-linux.zip" ]] && BINARY_FILES+=("godot_project/build/linux/tecate-linux.zip")
      ;;
    android)
      [[ -f "godot_project/build/android/tecate.apk" ]] && BINARY_FILES+=("godot_project/build/android/tecate.apk")
      ;;
    ios)
      [[ -f "godot_project/build/ios/tecate-ios.zip" ]] && BINARY_FILES+=("godot_project/build/ios/tecate-ios.zip")
      ;;
  esac
done

if [[ ${#BINARY_FILES[@]} -eq 0 ]]; then
  echo "❌ Error: No se encontraron archivos binarios empaquetados en godot_project/build/."
  exit 1
fi

echo "📦 Binarios locales evaluados:"
for f in "${BINARY_FILES[@]}"; do
  echo "   - $(basename "$f") ($(du -h "$f" | cut -f1))"
done

# ------------------------------------------------------------------------------
# 3. Evaluación SSOT contra version_manifest.json del último release
# ------------------------------------------------------------------------------
if command -v gh >/dev/null 2>&1; then
  echo "📡 [GitHub] Consultando el último release para evaluar version_manifest.json..."
  
  LATEST_TAG="$(gh release view --json tagName -q .tagName 2>/dev/null || true)"
  REMOTE_MANIFEST=""
  
  if [[ -n "$LATEST_TAG" ]]; then
    echo "ℹ️ Último release en GitHub detectado: $LATEST_TAG"
    REMOTE_MANIFEST="$(gh release download "$LATEST_TAG" -p "version_manifest.json" -O - 2>/dev/null || true)"
  else
    echo "ℹ️ No se detectaron releases previos. Se inicializará el primer release del repositorio."
  fi

  EVAL_ARGS=("--new-tag" "$TAG")
  if [[ -n "$REMOTE_MANIFEST" ]]; then
    EVAL_ARGS+=("--remote-manifest" "$REMOTE_MANIFEST")
  fi
  if [[ "$FORCE" == true ]]; then
    EVAL_ARGS+=("--force")
  fi

  set +e
  EVAL_JSON="$(python3 "$HASH_MGR" eval-release "${EVAL_ARGS[@]}" "${BINARY_FILES[@]}")"
  EVAL_STATUS=$?
  set -e

  ACTION="$(echo "$EVAL_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin).get('action', ''))")"
  REASON="$(echo "$EVAL_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin).get('reason', ''))")"

  if [[ "$ACTION" == "NOTHING_TO_DO" ]]; then
    echo "================================================================="
    echo "🟢 VALIDACIÓN SSOT: TODOS LOS ARTEFACTOS ESTÁN AL DÍA"
    echo "================================================================="
    echo "$REASON"
    echo ""
    echo "🛑 Se cancela la publicación. No se requieren cambios ni duplicados."
    echo "   (Para forzar una nueva versión, use: $0 --force)"
    echo "================================================================="
    exit 0
  fi

  # Extraer datos de la evaluación
  FILES_TO_UPLOAD=($(echo "$EVAL_JSON" | python3 -c "import sys, json; print(' '.join(json.load(sys.stdin).get('files_to_upload', [])))"))
  UPDATED_PLATS="$(echo "$EVAL_JSON" | python3 -c "import sys, json; print(', '.join(json.load(sys.stdin).get('updated_platforms', [])))")"
  PRESERVED_PLATS="$(echo "$EVAL_JSON" | python3 -c "import sys, json; print(', '.join(json.load(sys.stdin).get('preserved_platforms', [])))")"
  NOTES_FILE="$(echo "$EVAL_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin).get('notes_path', ''))")"

  echo "================================================================="
  echo "🚀 PUBLICANDO NUEVO RELEASE: $TAG (latest)"
  echo "================================================================="
  echo "  - Plataformas actualizadas (se suben ahora): ${UPDATED_PLATS:-ninguna}"
  echo "  - Plataformas preservadas  (referenciadas):  ${PRESERVED_PLATS:-ninguna}"
  echo "  - Archivos a transferir:                     ${#FILES_TO_UPLOAD[@]}"
  echo "================================================================="

  # ------------------------------------------------------------------------------
  # 4. Creación o actualización del Release en GitHub
  # ------------------------------------------------------------------------------
  if gh release view "$TAG" >/dev/null 2>&1; then
    echo "ℹ️ El release $TAG ya existe en GitHub. Actualizando activos con --clobber..."
    gh release upload "$TAG" "${FILES_TO_UPLOAD[@]}" --clobber
    gh release edit "$TAG" --notes-file "$NOTES_FILE" --latest --title "Tecate Simulator v$TAG"
  else
    echo "ℹ️ Creando nuevo release $TAG como 'latest'..."
    gh release create "$TAG" "${FILES_TO_UPLOAD[@]}" \
      --title "Tecate Simulator v$TAG" \
      --notes-file "$NOTES_FILE" \
      --latest
  fi

  echo "✅ Release $TAG publicado exitosamente:"
  gh release view "$TAG" --web 2>/dev/null || gh release view "$TAG"

else
  # Sin CLI de GitHub
  python3 "$HASH_MGR" eval-release --new-tag "$TAG" "${BINARY_FILES[@]}" >/dev/null
  echo "⚠️ Advertencia: 'gh' CLI no está instalada o no está en el PATH."
  echo "   Los binarios y 'version_manifest.json' están listos en 'godot_project/build/'."
  echo "   Para instalar GitHub CLI: brew install gh && gh auth login"
fi

echo "🎉 Proceso SSOT finalizado con éxito."
