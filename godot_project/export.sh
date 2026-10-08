#!/usr/bin/env bash
set -euo pipefail

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
export GODOT_PATH="${GODOT_PATH:-$(which godot-mono)}"
export ANDROID_SDK_ROOT="${ANDROID_SDK_ROOT:-$HOME/Library/Android/sdk}"
export JAVA_HOME="${JAVA_HOME:-$(/usr/libexec/java_home -v 11 2>/dev/null || echo /usr)}"

# # -------------------------------------------------
# # Solicitar credenciales de Android si no están definidas.
# # Godot 4 reconoce estas variables de entorno de forma nativa
# # y sobreescribe los valores de export_presets.cfg sin tocarlo:
# #
# #   GODOT_ANDROID_KEYSTORE_DEBUG_PATH
# #   GODOT_ANDROID_KEYSTORE_DEBUG_USER
# #   GODOT_ANDROID_KEYSTORE_DEBUG_PASSWORD
# #   GODOT_ANDROID_KEYSTORE_RELEASE_PATH
# #   GODOT_ANDROID_KEYSTORE_RELEASE_USER
# #   GODOT_ANDROID_KEYSTORE_RELEASE_PASSWORD
# #
# # El archivo export_presets.cfg NUNCA se modifica.
# # -------------------------------------------------

# # Ruta al keystore
# if [[ -z "${GODOT_ANDROID_KEYSTORE_RELEASE_PATH:-}" ]]; then
#   if [[ -n "${ANDROID_KEYSTORE_PATH:-}" ]]; then
#     export GODOT_ANDROID_KEYSTORE_RELEASE_PATH="$ANDROID_KEYSTORE_PATH"
#   else
#     read -rp "Path to Android keystore file: " GODOT_ANDROID_KEYSTORE_RELEASE_PATH
#   fi
# fi
# export GODOT_ANDROID_KEYSTORE_DEBUG_PATH="${GODOT_ANDROID_KEYSTORE_DEBUG_PATH:-$GODOT_ANDROID_KEYSTORE_RELEASE_PATH}"

# # Alias
# if [[ -z "${GODOT_ANDROID_KEYSTORE_RELEASE_USER:-}" ]]; then
#   if [[ -n "${ANDROID_KEYSTORE_ALIAS:-}" ]]; then
#     export GODOT_ANDROID_KEYSTORE_RELEASE_USER="$ANDROID_KEYSTORE_ALIAS"
#   else
#     read -rp "Android keystore alias: " GODOT_ANDROID_KEYSTORE_RELEASE_USER
#   fi
# fi
# export GODOT_ANDROID_KEYSTORE_DEBUG_USER="${GODOT_ANDROID_KEYSTORE_DEBUG_USER:-$GODOT_ANDROID_KEYSTORE_RELEASE_USER}"

# # Contraseña
# if [[ -z "${GODOT_ANDROID_KEYSTORE_RELEASE_PASSWORD:-}" ]]; then
#   if [[ -n "${ANDROID_KEYSTORE_PASSWORD:-}" ]]; then
#     export GODOT_ANDROID_KEYSTORE_RELEASE_PASSWORD="$ANDROID_KEYSTORE_PASSWORD"
#   else
#     read -rs -p "Android keystore password: " GODOT_ANDROID_KEYSTORE_RELEASE_PASSWORD
#     echo
#   fi
# fi
# export GODOT_ANDROID_KEYSTORE_DEBUG_PASSWORD="${GODOT_ANDROID_KEYSTORE_DEBUG_PASSWORD:-$GODOT_ANDROID_KEYSTORE_RELEASE_PASSWORD}"

# # NDK
# if [[ -z "${ANDROID_NDK_ROOT:-}" ]]; then
#   read -rp "Path to Android NDK: " ANDROID_NDK_ROOT
# fi
# export ANDROID_NDK_ROOT

# -------------------------------------------------
# 1) Generar ensamblados Mono
# -------------------------------------------------
echo "=== Generando ensamblados Mono ==="
"$GODOT_PATH" --headless --path "$(pwd)" --no-window --quit || true

# # -------------------------------------------------
# # -------------------------------------------------
# # 2) Exportar Android
# # -------------------------------------------------
# mkdir -p build/android
# echo "=== Exportando a Android (APK) ==="
# "$GODOT_PATH" \
#   --headless \
#   --path "$(pwd)" \
#   --export-release "Android" "build/android/tecate.apk"

# # -------------------------------------------------
# # 3) Exportar iOS (Xcode project)
# # -------------------------------------------------
# mkdir -p build/ios
# echo "=== Exportando a iOS (Xcode project) ==="
# "$GODOT_PATH" \
#   --headless \
#   --path "$(pwd)" \
#   --export-release "iOS" "build/ios/tecate.xcodeproj"

# -------------------------------------------------
# 4) Exportar macOS
# -------------------------------------------------
mkdir -p build/macos
echo "=== Exportando a macOS ==="
"$GODOT_PATH" \
  --headless \
  --path "$(pwd)" \
  --export-release "macOS" "build/macos/tecate.app"

# -------------------------------------------------
# 5) Exportar Windows
# -------------------------------------------------
mkdir -p build/windows
echo "=== Exportando a Windows ==="
"$GODOT_PATH" \
  --headless \
  --path "$(pwd)" \
  --export-release "Windows" "build/windows/tecate.exe"

# -------------------------------------------------
# 6) Exportar Linux
# -------------------------------------------------
# mkdir -p build/linux
# echo "=== Exportando a Linux ==="
# "$GODOT_PATH" \
#   --headless \
#   --path "$(pwd)" \
#   --export-release "Linux/X11" "build/linux/tecate.x86_64"

# # -------------------------------------------------
# # n) Compilar el proyecto Xcode (iOS) desde la CLI
# # -------------------------------------------------
# if command -v xcodebuild >/dev/null; then
#   echo "=== Compilando el proyecto Xcode (modo Release) ==="
#   pushd "build/ios/tecate.xcodeproj"
#   xcodebuild -scheme "tecate" -configuration Release -sdk iphoneos clean build
#   popd
# else
#   echo "⚠️  xcodebuild no está disponible – solo se generó el proyecto Xcode."
# fi

echo "✅ Exportaciones completadas."