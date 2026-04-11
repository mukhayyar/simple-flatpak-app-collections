#!/bin/bash

# --- Configuration ---
APP_ID="com.pens.UnitConverter"
MANIFEST="com.pens.UnitConverter.yml"
REPO_DIR="my-repo"
BUILD_DIR="build-dir"

# 1. Detect Architecture (Default to x86_64, accept argument for others)
# Usage: ./manage_repo.sh aarch64
target_arch="${1:-x86_64}"

echo "========================================"
echo "  Building for Architecture: $target_arch"
echo "========================================"

# 2. Initialize Repo (if it doesn't exist)
if [ ! -d "$REPO_DIR" ]; then
    echo "-> Initializing new OSTree repository in $REPO_DIR..."
    ostree init --mode=archive-z2 --repo="$REPO_DIR"
fi

# 3. Clean previous builds
echo "-> Cleaning build directory..."
rm -rf "$BUILD_DIR"

# 4. Build and Export to Repo
echo "-> Building application..."
flatpak-builder --force-clean \
    --repo="$REPO_DIR" \
    --arch="$target_arch" \
    --install-deps-from=flathub \
    --gpg-sign=GPG_KEY_ID_HERE \
    "$BUILD_DIR" \
    "$MANIFEST"

# NOTE: Remove --gpg-sign if you don't have a GPG key set up yet.

if [ $? -ne 0 ]; then
    echo "❌ Build failed!"
    exit 1
fi

# 5. Update Repo Metadata
echo "-> Updating repository metadata..."
flatpak build-update-repo "$REPO_DIR"

# 6. Create a Single-File Bundle
BUNDLE_NAME="${APP_ID}_${target_arch}.flatpak"
echo "-> Creating offline bundle: $BUNDLE_NAME"
flatpak build-bundle "$REPO_DIR" "$BUNDLE_NAME" "$APP_ID" --arch="$target_arch"

echo "========================================"
echo "✅ Success!"
echo "Repository located at: ./$REPO_DIR"
echo "Offline bundle: ./$BUNDLE_NAME"
echo ""
echo "To test this repo locally:"
echo "  flatpak remote-add --user --no-gpg-verify my-test-repo ./$REPO_DIR"
echo "  flatpak install --user my-test-repo $APP_ID"
echo "========================================"
