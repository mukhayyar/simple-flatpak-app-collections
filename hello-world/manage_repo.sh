#!/bin/bash

# --- Configuration ---
APP_ID="com.pens.HelloWorld"
MANIFEST="com.pens.HelloWorld.yml"
REPO_DIR="my-repo"
BUILD_DIR="build-dir"

# 1. Detect Architecture (Default to x86_64, accept argument for others)
# Usage: ./manage_repo.sh aarch64
target_arch="${1:-x86_64}"

echo "========================================"
echo "  Building for Architecture: $target_arch"
echo "========================================"

# 2. Initialize Repo (if it doesn't exist)
# mode=archive-z2 is standard for HTTP hosting
if [ ! -d "$REPO_DIR" ]; then
    echo "-> Initializing new OSTree repository in $REPO_DIR..."
    ostree init --mode=archive-z2 --repo="$REPO_DIR"
fi

# 3. Clean previous builds to ensure no architecture mix-ups
echo "-> Cleaning build directory..."
rm -rf "$BUILD_DIR"

# 4. Build and Export to Repo
# --repo=$REPO_DIR tells builder to automatically export the result there
# --arch=$target_arch forces the specific CPU architecture
# --install-deps-from=flathub ensures we get the ARM64 SDKs if needed
echo "-> Building application..."
flatpak-builder --force-clean \
    --repo="$REPO_DIR" \
    --arch="$target_arch" \
    --install-deps-from=flathub \
    --gpg-sign=GPG_KEY_ID_HERE \
    "$BUILD_DIR" \
    "$MANIFEST"

# NOTE: If you don't have a GPG key set up yet, remove the --gpg-sign line above.
# However, for production AGL, GPG signing is highly recommended.

if [ $? -ne 0 ]; then
    echo "❌ Build failed!"
    exit 1
fi

# 5. Update Repo Metadata
# This generates the summary file clients need to see the app list
echo "-> Updating repository metadata..."
flatpak build-update-repo "$REPO_DIR"

# 6. (Optional) Create a Single-File Bundle
# Useful for USB updates if the car has no internet
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