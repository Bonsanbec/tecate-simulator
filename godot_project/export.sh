#!/usr/bin/env bash
set -euo pipefail

# -------------------------------------------------
# Cargar variables desde .env (si existe)
# -------------------------------------------------
if [[ -f "../.env" ]]; then
  set -a
  # shellcheck source=/dev/null
  source "../.env"
  set +a
fi

# -------------------------------------------------
# Variables de entorno de toolchain
# -------------------------------------------------
export GODOT_PATH="${GODOT_PATH:-$(which godot-mono)}"
export ANDROID_SDK_ROOT="${ANDROID_SDK_ROOT:-$HOME/Library/Android/sdk}"
export JAVA_HOME="${JAVA_HOME:-$(/usr/libexec/java_home -v 11 2>/dev/null || echo /usr)}"

# -------------------------------------------------
# Solicitar credenciales de Android si no están definidas
# -------------------------------------------------
if [[ -z "${ANDROID_KEYSTORE_PATH:-}" ]]; then
  read -rp "Path to Android keystore file: " ANDROID_KEYSTORE_PATH
fi
if [[ -z "${ANDROID_KEYSTORE_ALIAS:-}" ]]; then
  read -rp "Android keystore alias: " ANDROID_KEYSTORE_ALIAS
fi
if [[ -z "${ANDROID_KEYSTORE_PASSWORD:-}" ]]; then
  read -rs -p "Android keystore password: " ANDROID_KEYSTORE_PASSWORD
  echo
fi

if [[ -z "${ANDROID_NDK_ROOT:-}" ]]; then
  read -rp "Path to Android NDK: " ANDROID_NDK_ROOT
fi
export ANDROID_NDK_ROOT

# -------------------------------------------------
# Inyectar keystore en export_presets.cfg
# (Godot lee el archivo de forma literal, no lee env vars)
# -------------------------------------------------
PRESETS="export_presets.cfg"

if [[ ! -f "$PRESETS" ]]; then
  echo "❌ No se encontró $PRESETS. Ejecuta primero:"
  echo "   godot-mono --headless --path . --script res://tools/generate_export_presets.gd --quit"
  exit 1
fi

echo "=== Inyectando keystore en $PRESETS ==="
# Usa sed para reemplazar los valores vacíos del keystore con los reales.
# Guardamos los originales para restaurarlos al final.
cp "$PRESETS" "${PRESETS}.bak"

sed -i '' \
  -e "s|^keystore/debug=\"\"|keystore/debug=\"${ANDROID_KEYSTORE_PATH}\"|" \
  -e "s|^keystore/debug_user=\"\"|keystore/debug_user=\"${ANDROID_KEYSTORE_ALIAS}\"|" \
  -e "s|^keystore/debug_password=\"\"|keystore/debug_password=\"${ANDROID_KEYSTORE_PASSWORD}\"|" \
  -e "s|^keystore/release=\"\"|keystore/release=\"${ANDROID_KEYSTORE_PATH}\"|" \
  -e "s|^keystore/release_user=\"\"|keystore/release_user=\"${ANDROID_KEYSTORE_ALIAS}\"|" \
  -e "s|^keystore/release_password=\"\"|keystore/release_password=\"${ANDROID_KEYSTORE_PASSWORD}\"|" \
  "$PRESETS"

# Función para restaurar el archivo limpio al salir (éxito o error)
cleanup() {
  echo "=== Restaurando $PRESETS (sin credenciales) ==="
  mv "${PRESETS}.bak" "$PRESETS"
}
trap cleanup EXIT

# -------------------------------------------------
# 1) Generar ensamblados Mono
# -------------------------------------------------
echo "=== Generando ensamblados Mono ==="
"$GODOT_PATH" --headless --path "$(pwd)" --no-window --quit || true

# -------------------------------------------------
# 2) Exportar Android
# -------------------------------------------------
mkdir -p build/android
echo "=== Exportando a Android (APK) ==="
"$GODOT_PATH" \
  --headless \
  --path "$(pwd)" \
  --export-release "Android"

# -------------------------------------------------
# 3) Exportar iOS (Xcode project)
# -------------------------------------------------
mkdir -p build/ios
echo "=== Exportando a iOS (Xcode project) ==="
"$GODOT_PATH" \
  --headless \
  --path "$(pwd)" \
  --export-release "iOS"

# -------------------------------------------------
# 4) Compilar el proyecto Xcode (iOS) desde la CLI
# -------------------------------------------------
if command -v xcodebuild >/dev/null; then
  echo "=== Compilando el proyecto Xcode (modo Release) ==="
  pushd "build/ios/tecate.xcodeproj"
  xcodebuild -scheme "tecate" -configuration Release -sdk iphoneos clean build
  popd
else
  echo "⚠️  xcodebuild no está disponible – solo se generó el proyecto Xcode."
fi

echo "✅ Exportaciones completadas."