#!/usr/bin/env bash
set -euo pipefail

# -------------------------------------------------
# Variables de entorno
# -------------------------------------------------
export GODOT_PATH="${GODOT_PATH:-$(which godot-mono)}"
export ANDROID_SDK_ROOT="${ANDROID_SDK_ROOT:-$HOME/Library/Android/sdk}"
export ANDROID_NDK_ROOT="${ANDROID_NDK_ROOT:-$ANDROID_SDK_ROOT/ndk/25.2.9519653}"
export JAVA_HOME="${JAVA_HOME:-$(/usr/libexec/java_home -v 11)}"

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