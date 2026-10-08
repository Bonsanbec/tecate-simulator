#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# scripts/release_local.sh
# ------------------------------------------------------------------------------
# Genera los binarios de release localmente con todos los assets integrados,
# los empaqueta en .zip y crea o actualiza el release en GitHub con la versión
# en formato YY.MM.DD-HH marcado como 'latest'.
#
# Uso:
#   ./scripts/release_local.sh [all|windows|macos|android|ios|linux] [VERSION_TAG]
#
# Ejemplos:
#   ./scripts/release_local.sh
#   ./scripts/release_local.sh macos
#   ./scripts/release_local.sh all 26.10.08-14
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$WORKSPACE_ROOT"

TARGET="${1:-all}"
TAG="${2:-$(date +"%y.%m.%d-%H")}"

echo "================================================================="
echo "  TECATE SIMULATOR: PUBLICACIÓN LOCAL DE RELEASE"
echo "  Versión (Tag):     $TAG"
echo "  Objetivo export:   $TARGET"
echo "================================================================="

# 1. Exportar binarios mediante export.sh
chmod +x godot_project/export.sh
./godot_project/export.sh "$TARGET"

# 2. Recolectar archivos generados
FILES=()
case "$TARGET" in
  macos)
    [[ -f "godot_project/build/macos/tecate-macos.zip" ]] && FILES+=("godot_project/build/macos/tecate-macos.zip")
    ;;
  windows)
    [[ -f "godot_project/build/windows/tecate-windows.zip" ]] && FILES+=("godot_project/build/windows/tecate-windows.zip")
    ;;
  linux)
    [[ -f "godot_project/build/linux/tecate-linux.zip" ]] && FILES+=("godot_project/build/linux/tecate-linux.zip")
    ;;
  android)
    [[ -f "godot_project/build/android/tecate.apk" ]] && FILES+=("godot_project/build/android/tecate.apk")
    ;;
  ios)
    [[ -f "godot_project/build/ios/tecate-ios.zip" ]] && FILES+=("godot_project/build/ios/tecate-ios.zip")
    ;;
  all)
    [[ -f "godot_project/build/macos/tecate-macos.zip" ]] && FILES+=("godot_project/build/macos/tecate-macos.zip")
    [[ -f "godot_project/build/windows/tecate-windows.zip" ]] && FILES+=("godot_project/build/windows/tecate-windows.zip")
    [[ -f "godot_project/build/linux/tecate-linux.zip" ]] && FILES+=("godot_project/build/linux/tecate-linux.zip")
    [[ -f "godot_project/build/android/tecate.apk" ]] && FILES+=("godot_project/build/android/tecate.apk")
    [[ -f "godot_project/build/ios/tecate-ios.zip" ]] && FILES+=("godot_project/build/ios/tecate-ios.zip")
    ;;
esac

if [[ ${#FILES[@]} -eq 0 ]]; then
  echo "❌ Error: No se encontraron archivos de salida para empaquetar."
  exit 1
fi

echo "📦 Archivos listos para release:"
for f in "${FILES[@]}"; do
  echo "   - $f ($(du -h "$f" | cut -f1))"
done

# 3. Publicar o actualizar en GitHub Releases mediante la CLI gh
if command -v gh >/dev/null 2>&1; then
  echo "🚀 Sincronizando con GitHub Releases (Tag: $TAG)..."
  
  if gh release view "$TAG" >/dev/null 2>&1; then
    echo "ℹ️ El release $TAG ya existe. Actualizando binarios con --clobber..."
    gh release upload "$TAG" "${FILES[@]}" --clobber
    gh release edit "$TAG" --latest --title "Tecate Simulator $TAG"
  else
    echo "ℹ️ Creando nuevo release $TAG como 'latest'..."
    gh release create "$TAG" "${FILES[@]}" \
      --title "Tecate Simulator $TAG" \
      --notes "Release automático local con geometría y assets urbanos completos ($TAG)." \
      --latest
  fi
  
  echo "✅ Release publicado exitosamente:"
  gh release view "$TAG" --web 2>/dev/null || gh release view "$TAG"
else
  echo "⚠️ Advertencia: 'gh' CLI no está instalada o no está en el PATH."
  echo "   Los binarios están listos en 'godot_project/build/'."
  echo "   Para instalador de GitHub CLI: brew install gh && gh auth login"
fi

echo "🎉 Proceso local finalizado con éxito."
