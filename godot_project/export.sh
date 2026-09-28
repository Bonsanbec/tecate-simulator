#!/usr/bin/env bash
set -euo pipefail

# -------------------------------------------------
# Variables de entorno
# -------------------------------------------------
export GODOT_PATH="${GODOT_PATH:-$(which godot-mono)}"
export ANDROID_SDK_ROOT="${ANDROID_SDK_ROOT:-$HOME/Library/Android/sdk}"
export JAVA_HOME="${JAVA_HOME:-$(/usr/libexec/java_home -v 11)}"

# Prompt for Android keystore information if not already set
if [[ -z "${ANDROID_KEYSTORE_PATH:-}" ]]; then
  read -p "Path to Android keystore file: " ANDROID_KEYSTORE_PATH
fi
if [[ -z "${ANDROID_KEYSTORE_ALIAS:-}" ]]; then
  read -p "Android keystore alias: " ANDROID_KEYSTORE_ALIAS
fi
if [[ -z "${ANDROID_KEYSTORE_PASSWORD:-}" ]]; then
  read -s -p "Android keystore password: " ANDROID_KEYSTORE_PASSWORD
  echo
fi

if [[ -z "${ANDROID_NDK_ROOT:-}" ]]; then
  read -p "Path to Android NDK: " ANDROID_NDK_ROOT
fi

# Export the variables so Godot can use them
export ANDROID_KEYSTORE_PATH ANDROID_KEYSTORE_ALIAS ANDROID_KEYSTORE_PASSWORD ANDROID_NDK_ROOT

# -------------------------------------------------
# 1) Compilar (opcional) – Godot‑Mono necesita generar los ensamblados .dll,
#    aunque el proyecto no tenga C#.  Esto se hace con --script.
# -------------------------------------------------
echo "=== Generando ensamblados Mono (aunque no haya C#) ==="
"$GODOT_PATH" --headless --path "$(pwd)" --no-window --quit

# -------------------------------------------------
# 2) Exportar Android
# -------------------------------------------------
echo "=== Exportando a Android (APK) ==="
"$GODOT_PATH" \
  --headless \
  --path "$(pwd)" \
  --export-release "Android" \
  --quiet \
  --config-file "android_export.cfg"

# -------------------------------------------------
# 3) Exportar iOS (Xcode project)
# -------------------------------------------------
echo "=== Exportando a iOS (Xcode project) ==="
"$GODOT_PATH" \
  --headless \
  --path "$(pwd)" \
  --export-release "iOS" \
  --quiet \
  --config-file "ios_export.cfg"

# -------------------------------------------------
# 4) Compilar el proyecto Xcode (iOS) desde la CLI
# -------------------------------------------------
if command -v xcodebuild >/dev/null; then
  echo "=== Compilando el proyecto Xcode (modo Release) ==="
  pushd "build/ios/tecate.xcodeproj"
  xcodebuild -scheme "tecate" -configuration Release -sdk iphoneos clean build
  popd
else
  echo "⚠️  xcodebuild no está disponible - solo se generó el proyecto Xcode."
fi

echo "✅ Exportaciones completadas."