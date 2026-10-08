#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# scripts/release_local.sh
# ------------------------------------------------------------------------------
# Genera los binarios de release localmente con todos los assets integrados,
# los empaqueta en .zip y gestiona la publicación inteligente en GitHub Releases:
#
# 1. Caché Local (Anti-Regeneración):
#    - Si las fuentes y assets no cambiaron y el .zip existe, omite la exportación.
#
# 2. Validación Remota (Tres Vías):
#    - Si NINGÚN hash coincide: Crea una NUEVA release con formato YY.MM.DD-HH (latest).
#    - Si ALGÚN hash coincide pero otros cambiaron: NO crea release nueva, sino que
#      realiza un UPSERT actualizando únicamente los binarios que cambiaron en la
#      release existente en GitHub.
#    - Si TODOS los hashes coinciden: No realiza ninguna acción ni carga (evita duplicados).
#
# Uso:
#   ./scripts/release_local.sh [all|windows|macos|android|ios|linux] [VERSION_TAG] [--force]
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
      echo "  --force, -f       Fuerza la recompilación y publicación ignorando las cachés de hash."
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
echo "  TECATE SIMULATOR: PUBLICACIÓN LOCAL DE RELEASE"
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
    echo "✅ [$t] Exportación completada y registrada en caché."
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
# 3. Validación de hashes contra el último release en GitHub
# ------------------------------------------------------------------------------
if command -v gh >/dev/null 2>&1; then
  echo "📡 [GitHub] Consultando el último release para verificar hashes..."
  
  LATEST_TAG="$(gh release view --json tagName -q .tagName 2>/dev/null || true)"
  
  if [[ -n "$LATEST_TAG" && "$FORCE" == false ]]; then
    echo "ℹ️ Último release en GitHub detectado: $LATEST_TAG"
    
    # Intentar descargar SHA256SUMS.txt del último release
    REMOTE_SUMS="$(gh release download "$LATEST_TAG" -p "SHA256SUMS.txt" -O - 2>/dev/null || true)"
    
    if [[ -n "$REMOTE_SUMS" ]]; then
      set +e
      COMPARE_JSON="$(python3 "$HASH_MGR" compare-remote --remote-sums "$REMOTE_SUMS" "${BINARY_FILES[@]}")"
      COMPARE_STATUS=$?
      set -e

      case $COMPARE_STATUS in
        2)
          # CASO A: TODOS LOS HASHES COINCIDEN (NOTHING_TO_DO)
          echo "================================================================="
          echo "🟢 VALIDACIÓN REMOTA: TODOS LOS ARTEFACTOS ESTÁN AL DÍA"
          echo "================================================================="
          echo "Todos los binarios locales son idénticos a los existentes en el"
          echo "último release de GitHub ($LATEST_TAG):"
          echo "$COMPARE_JSON" | grep -A 10 '"matches"' || true
          echo ""
          echo "🛑 Se cancela la publicación. No se requieren cambios ni duplicados."
          echo "   (Para forzar una nueva publicación, use: $0 --force)"
          echo "================================================================="
          exit 0
          ;;

        1)
          # CASO B: AL MENOS UN HASH COINCIDE, PERO OTROS CAMBIARON (UPSERT_EXISTING)
          echo "================================================================="
          echo "🔄 VALIDACIÓN REMOTA: UPSERT EN EL RELEASE EXISTENTE ($LATEST_TAG)"
          echo "================================================================="
          echo "Se detectó coincidencia en al menos un binario. Por consiguiente,"
          echo "NO se creará un release nuevo, sino que se actualizarán únicamente"
          echo "los binarios modificados dentro del release actual ($LATEST_TAG):"
          echo "$COMPARE_JSON" | grep -A 10 '"differs"' || true
          echo "$COMPARE_JSON" | grep -A 10 '"new_files"' || true
          echo "================================================================="

          # Extraer archivos modificados de la respuesta JSON
          CHANGED_FILES=($(echo "$COMPARE_JSON" | python3 -c "import sys, json; data=json.load(sys.stdin); print(' '.join(data.get('changed_files', [])))"))
          
          # Generar SHA256SUMS.txt fusionado (mantiene hashes no modificados y actualiza los nuevos)
          MERGED_SUMS_FILE="$(python3 "$HASH_MGR" generate-checksums --merge-remote "$REMOTE_SUMS" "${BINARY_FILES[@]}")"
          FILES_TO_UPSERT=("${CHANGED_FILES[@]}" "$MERGED_SUMS_FILE")

          echo "🚀 Subiendo binarios modificados a $LATEST_TAG..."
          gh release upload "$LATEST_TAG" "${FILES_TO_UPSERT[@]}" --clobber
          gh release edit "$LATEST_TAG" --latest
          
          echo "✅ Upsert completado exitosamente en el release $LATEST_TAG:"
          gh release view "$LATEST_TAG" --web 2>/dev/null || gh release view "$LATEST_TAG"
          echo "🎉 Proceso finalizado con éxito."
          exit 0
          ;;

        0)
          # CASO C: NINGÚN HASH COINCIDE (CREATE_NEW)
          echo "================================================================="
          echo "🚀 VALIDACIÓN REMOTA: NINGÚN HASH COINCIDE (NUEVA VERSIÓN)"
          echo "================================================================="
          echo "Ningún binario coincide con los existentes en el último release ($LATEST_TAG)."
          echo "Todos los artefactos representan una nueva versión completa."
          echo "Creando nuevo release $TAG como 'latest'..."
          echo "================================================================="
          ;;
      esac
    else
      echo "ℹ️ El release previo ($LATEST_TAG) no incluye SHA256SUMS.txt. Se procederá con la creación de la nueva versión."
    fi
  elif [[ "$FORCE" == true ]]; then
    echo "⚡ Modo --force activo: Omitiendo validación contra el último release."
  else
    echo "ℹ️ No se encontraron releases previos en el repositorio. Creando el primer release."
  fi

  # ------------------------------------------------------------------------------
  # 4. Creación de Nuevo Release en GitHub (Caso C o Primer Release)
  # ------------------------------------------------------------------------------
  # Generar sumas para el nuevo release
  CHECKSUMS_FILE="$(python3 "$HASH_MGR" generate-checksums "${BINARY_FILES[@]}")"
  ALL_RELEASE_FILES=("${BINARY_FILES[@]}" "$CHECKSUMS_FILE")

  echo "🚀 Creando release $TAG en GitHub..."
  
  if gh release view "$TAG" >/dev/null 2>&1; then
    echo "ℹ️ El release $TAG ya existe. Actualizando binarios con --clobber..."
    gh release upload "$TAG" "${ALL_RELEASE_FILES[@]}" --clobber
    gh release edit "$TAG" --latest --title "Tecate Simulator v$TAG"
  else
    echo "ℹ️ Creando nuevo release $TAG como 'latest'..."
    gh release create "$TAG" "${ALL_RELEASE_FILES[@]}" \
      --title "Tecate Simulator v$TAG" \
      --notes "Release con geometría urbana, terreno y edificios completos ($TAG)." \
      --latest
  fi
  
  echo "✅ Release publicado exitosamente:"
  gh release view "$TAG" --web 2>/dev/null || gh release view "$TAG"

else
  # Sin CLI de GitHub
  CHECKSUMS_FILE="$(python3 "$HASH_MGR" generate-checksums "${BINARY_FILES[@]}")"
  echo "⚠️ Advertencia: 'gh' CLI no está instalada o no está en el PATH."
  echo "   Los binarios y su archivo de sumas (SHA256SUMS.txt) están listos en 'godot_project/build/'."
  echo "   Para instalar GitHub CLI: brew install gh && gh auth login"
fi

echo "🎉 Proceso finalizado con éxito."
