#!/bin/bash

APP_ID="com.pens.TextToSpeech"
MANIFEST="com.pens.TextToSpeech.yml"
REPO_DIR="my-repo"
BUILD_DIR="build-dir"

target_arch="${1:-x86_64}"

echo "========================================"
echo "  Building for Architecture: $target_arch"
echo "========================================"

if [ ! -d "$REPO_DIR" ]; then
    echo "-> Initializing new OSTree repository in $REPO_DIR..."
    ostree init --mode=archive-z2 --repo="$REPO_DIR"
fi

echo "-> Cleaning build directory..."
rm -rf "$BUILD_DIR"

echo "-> Building application..."
flatpak-builder --force-clean \
    --repo="$REPO_DIR" \
    --arch="$target_arch" \
    --install-deps-from=flathub \
    "$BUILD_DIR" \
    "$MANIFEST"

if [ $? -ne 0 ]; then
    echo "Build failed!"
    exit 1
fi

echo "-> Updating repository metadata..."
flatpak build-update-repo "$REPO_DIR"

BUNDLE_NAME="${APP_ID}_${target_arch}.flatpak"
echo "-> Creating offline bundle: $BUNDLE_NAME"
flatpak build-bundle "$REPO_DIR" "$BUNDLE_NAME" "$APP_ID" --arch="$target_arch"

echo "========================================"
echo "Success!"
echo "Repository located at: ./$REPO_DIR"
echo "Offline bundle: $BUNDLE_NAME"
echo ""
echo "To test this repo locally:"
echo "  flatpak remote-add --user --no-gpg-verify my-test-repo ./$REPO_DIR"
echo "  flatpak install --user my-test-repo $APP_ID"
echo "========================================"
