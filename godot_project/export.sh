#!/usr/bin/env bash
set -euo pipefail

# -------------------------------------------------
# Ubicación canónica del proyecto Godot
# -------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
PROJECT_DIR="$SCRIPT_DIR"

# -------------------------------------------------
# Cargar variables desde .env (si existe)
# -------------------------------------------------
if [[ -f "./.env" ]]; then
  set -a
  # shellcheck source=/dev/null
  source "./.env"
  set +a
fi

# -------------------------------------------------
# Variables de entorno de toolchain
# -------------------------------------------------
if [[ -z "${GODOT_PATH:-}" ]]; then
  if [[ -n "${GODOT:-}" ]]; then
    GODOT_PATH="$GODOT"
  elif command -v godot-mono >/dev/null 2>&1; then
    GODOT_PATH="$(command -v godot-mono)"
  elif command -v godot >/dev/null 2>&1; then
    GODOT_PATH="$(command -v godot)"
  elif command -v godot4 >/dev/null 2>&1; then
    GODOT_PATH="$(command -v godot4)"
  else
    GODOT_PATH="godot"
  fi
fi
export GODOT_PATH
export ANDROID_SDK_ROOT="${ANDROID_SDK_ROOT:-$HOME/Library/Android/sdk}"
export JAVA_HOME="${JAVA_HOME:-$(/usr/libexec/java_home -v 11 2>/dev/null || echo /usr)}"

# Credenciales de Android desde variables de entorno (no interactivas para CI/CD)
if [[ -n "${ANDROID_KEYSTORE_PATH:-}" ]]; then
  export GODOT_ANDROID_KEYSTORE_RELEASE_PATH="${GODOT_ANDROID_KEYSTORE_RELEASE_PATH:-$ANDROID_KEYSTORE_PATH}"
fi
export GODOT_ANDROID_KEYSTORE_DEBUG_PATH="${GODOT_ANDROID_KEYSTORE_DEBUG_PATH:-${GODOT_ANDROID_KEYSTORE_RELEASE_PATH:-}}"

if [[ -n "${ANDROID_KEYSTORE_ALIAS:-}" ]]; then
  export GODOT_ANDROID_KEYSTORE_RELEASE_USER="${GODOT_ANDROID_KEYSTORE_RELEASE_USER:-$ANDROID_KEYSTORE_ALIAS}"
fi
export GODOT_ANDROID_KEYSTORE_DEBUG_USER="${GODOT_ANDROID_KEYSTORE_DEBUG_USER:-${GODOT_ANDROID_KEYSTORE_RELEASE_USER:-}}"

if [[ -n "${ANDROID_KEYSTORE_PASSWORD:-}" ]]; then
  export GODOT_ANDROID_KEYSTORE_RELEASE_PASSWORD="${GODOT_ANDROID_KEYSTORE_RELEASE_PASSWORD:-$ANDROID_KEYSTORE_PASSWORD}"
fi
export GODOT_ANDROID_KEYSTORE_DEBUG_PASSWORD="${GODOT_ANDROID_KEYSTORE_DEBUG_PASSWORD:-${GODOT_ANDROID_KEYSTORE_RELEASE_PASSWORD:-}}"

# -------------------------------------------------
# 1) Inicializar proyecto e importar recursos
# -------------------------------------------------
init_godot() {
  echo "=== Inicializando proyecto e importando recursos con Godot ==="
  "$GODOT_PATH" --headless --path "$PROJECT_DIR" --quit || true
}

# -------------------------------------------------
# 2) Exportar macOS
# -------------------------------------------------
export_macos() {
  mkdir -p build/macos
  echo "=== Exportando a macOS ==="
  "$GODOT_PATH" \
    --headless \
    --path "$PROJECT_DIR" \
    --export-release "macOS" "build/macos/tecate.app"

  # Empaquetar en .zip para distribución en releases
  if [[ -d "build/macos/tecate.app" ]] && command -v zip >/dev/null 2>&1; then
    echo "=== Empaquetando macOS en tecate-macos.zip ==="
    (cd build/macos && rm -f tecate-macos.zip && zip -r -q tecate-macos.zip tecate.app)
  fi
}

# -------------------------------------------------
# 3) Exportar Windows
# -------------------------------------------------
export_windows() {
  mkdir -p build/windows
  echo "=== Exportando a Windows ==="
  "$GODOT_PATH" \
    --headless \
    --path "$PROJECT_DIR" \
    --export-release "Windows" "build/windows/tecate.exe"

  # Empaquetar en .zip para distribución en releases (incluye .exe y .pck si existe)
  if [[ -f "build/windows/tecate.exe" ]] && command -v zip >/dev/null 2>&1; then
    echo "=== Empaquetando Windows en tecate-windows.zip ==="
    (cd build/windows && rm -f tecate-windows.zip && zip -r -q tecate-windows.zip tecate.exe $([ -f tecate.pck ] && echo tecate.pck))
  fi
}

# -------------------------------------------------
# 4) Exportar Android (APK)
# -------------------------------------------------
export_android() {
  mkdir -p build/android
  echo "=== Exportando a Android (APK) ==="
  "$GODOT_PATH" \
    --headless \
    --path "$PROJECT_DIR" \
    --export-release "Android" "build/android/tecate.apk"
}

# -------------------------------------------------
# 5) Exportar iOS (Xcode Project)
# -------------------------------------------------
export_ios() {
  mkdir -p build/ios
  echo "=== Exportando a iOS (Xcode project) ==="
  "$GODOT_PATH" \
    --headless \
    --path "$PROJECT_DIR" \
    --export-release "iOS" "build/ios/tecate.xcodeproj"

  if command -v xcodebuild >/dev/null 2>&1; then
    echo "=== Compilando el proyecto Xcode (modo Release) ==="
    pushd "build/ios/tecate.xcodeproj" >/dev/null
    xcodebuild -scheme "tecate" -configuration Release -sdk iphoneos clean build
    popd >/dev/null
  elif command -v zip >/dev/null 2>&1; then
    echo "=== Empaquetando proyecto Xcode en tecate-ios.zip ==="
    (cd build/ios && rm -f tecate-ios.zip && zip -r -q tecate-ios.zip tecate.xcodeproj)
  fi
}

# -------------------------------------------------
# 6) Exportar Linux
# -------------------------------------------------
export_linux() {
  mkdir -p build/linux
  echo "=== Exportando a Linux ==="
  "$GODOT_PATH" \
    --headless \
    --path "$PROJECT_DIR" \
    --export-release "Linux/X11" "build/linux/tecate.x86_64"

  if [[ -f "build/linux/tecate.x86_64" ]] && command -v zip >/dev/null 2>&1; then
    echo "=== Empaquetando Linux en tecate-linux.zip ==="
    (cd build/linux && rm -f tecate-linux.zip && zip -r -q tecate-linux.zip tecate.x86_64 $([ -f tecate.pck ] && echo tecate.pck))
  fi
}

# -------------------------------------------------
# Despachador principal de plataformas
# -------------------------------------------------
TARGET="${1:-all}"

case "$TARGET" in
  windows|macos|android|ios|linux|all)
    ;;
  *)
    echo "Uso: $0 [all|windows|macos|android|ios|linux]"
    exit 1
    ;;
esac

init_godot

case "$TARGET" in
  windows)
    export_windows
    ;;
  macos)
    export_macos
    ;;
  android)
    export_android
    ;;
  ios)
    export_ios
    ;;
  linux)
    export_linux
    ;;
  all)
    # Por defecto, exportar plataformas actualmente activas (macOS y Windows)
    export_macos
    export_windows
    ;;
esac

echo "✅ Exportaciones completadas exitosamente para objetivo: $TARGET"
