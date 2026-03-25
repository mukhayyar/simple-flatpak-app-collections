#!/bin/bash

# --- KONFIGURASI SERVER ---
# URL API Flat-manager (Port 8080) - Tanpa nama repo di belakangnya
SERVER_API_URL="https://hub.agl-store.cyou"
REPO_NAME="stable"

# Token Admin Anda
export REPO_TOKEN="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJidWlsZCIsInNjb3BlIjpbImJ1aWxkIiwidXBsb2FkIl0sIm5hbWUiOiJkZXZlbG9wZXIiLCJwcmVmaXhlcyI6WyJjb20ucGVucy5Qb21vZG9ybyJdLCJyZXBvcyI6WyJzdGFibGUiXSwiZXhwIjoxODAwMjk3NTQxLCJ0b2tlbl90eXBlIjoiYXBwIiwiYnJhbmNoZXMiOlsic3RhYmxlIl19.0pP0Lui8SK7ZZ3iTeG9zTik2BD0GbVa4adCjGdw5hT8"

# --- KONFIGURASI APLIKASI ---
APP_ID="com.pens.Pomodoro"
MANIFEST_FILE="com.pens.Pomodoro.yml"
BUILD_DIR="flatpak_build"
REPO_TEMP="repo_temp" 

echo ">>> 1. Cleaning up previous builds..."
rm -rf "$BUILD_DIR" "$REPO_TEMP"

echo ">>> 2. Building the Flatpak application..."
# Tambahkan --install-deps-from=flathub jika perlu dependency luar
flatpak-builder --force-clean --repo="$REPO_TEMP" "$BUILD_DIR" "$MANIFEST_FILE"

if [ $? -ne 0 ]; then
    echo "❌ Build Failed!"
    exit 1
fi

# Catatan: flatpak-builder dengan opsi --repo sudah otomatis melakukan export.
# Jadi kita tidak perlu 'flatpak build-export' manual lagi, tapi folder REPO_TEMP sudah siap.

echo ">>> 3. Initiating Upload to Server..."

# [LANGKAH A] Minta Izin Buat Build Baru (CREATE)
# Ini akan mengembalikan URL unik, misal: http://.../api/v1/build/123
echo "    > Creating new build transaction..."
BUILD_URL=$(flat-manager-client create "$SERVER_API_URL" "$REPO_NAME")

if [ -z "$BUILD_URL" ]; then
    echo "❌ Failed to create build. Check connection or token."
    exit 1
fi
echo "    > Build created at: $BUILD_URL"

# [LANGKAH B] Upload File ke Build URL tersebut (PUSH)
echo "    > Pushing files..."
flat-manager-client push "$BUILD_URL" "$REPO_TEMP"

if [ $? -ne 0 ]; then
    echo "❌ Push Failed!"
    exit 1
fi

# [LANGKAH C] Resmikan Upload (COMMIT)
echo "    > Committing (Publishing)..."
flat-manager-client commit --wait "$BUILD_URL"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ UPLOAD SUCCESS!"
    echo "Download URL (via Port 8000): https://hub.agl-store.cyou/"
else
    echo "❌ Commit Failed."
    exit 1
fi