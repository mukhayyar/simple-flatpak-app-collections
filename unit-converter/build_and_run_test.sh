#!/bin/bash

# --- KONFIGURASI SERVER ---
SERVER_API_URL="https://hub.agl-store.cyou/"
REPO_NAME="stable"

# Token Admin
export REPO_TOKEN="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJidWlsZCIsInNjb3BlIjpbImJ1aWxkIiwidXBsb2FkIl0sIm5hbWUiOiJkZXZlbG9wZXIiLCJwcmVmaXhlcyI6WyJjb20ucGVucy5Vbml0Q29udmVydGVyIl0sInJlcG9zIjpbInN0YWJsZSJdLCJleHAiOjE3OTczMDE2NDYsInRva2VuX3R5cGUiOiJhcHAiLCJicmFuY2hlcyI6WyJzdGFibGUiXX0.placeholder"

# --- KONFIGURASI APLIKASI ---
APP_ID="com.pens.UnitConverter"
MANIFEST_FILE="com.pens.UnitConverter.yml"
BUILD_DIR="flatpak_build"
REPO_TEMP="repo_temp"

echo ">>> 1. Cleaning up previous builds..."
rm -rf "$BUILD_DIR" "$REPO_TEMP"

echo ">>> 2. Building the Flatpak application..."
flatpak-builder --force-clean --repo="$REPO_TEMP" "$BUILD_DIR" "$MANIFEST_FILE"

if [ $? -ne 0 ]; then
    echo "❌ Build Failed!"
    exit 1
fi

echo ">>> 3. Initiating Upload to Server..."

echo "    > Creating new build transaction..."
BUILD_URL=$(flat-manager-client create "$SERVER_API_URL" "$REPO_NAME")

if [ -z "$BUILD_URL" ]; then
    echo "❌ Failed to create build. Check connection or token."
    exit 1
fi
echo "    > Build created at: $BUILD_URL"

echo "    > Pushing files..."
flat-manager-client push "$BUILD_URL" "$REPO_TEMP"

if [ $? -ne 0 ]; then
    echo "❌ Push Failed!"
    exit 1
fi

echo "    > Committing (Publishing)..."
flat-manager-client commit --wait "$BUILD_URL"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ UPLOAD SUCCESS!"
    echo "Download URL (via Port 8000): http://172.21.164.231:8000"
else
    echo "❌ Commit Failed."
    exit 1
fi
