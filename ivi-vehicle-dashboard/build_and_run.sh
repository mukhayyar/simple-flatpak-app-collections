#!/bin/bash
APP_ID="com.pens.IVIVehicleDashboard"
MANIFEST_FILE="com.pens.IVIVehicleDashboard.yml"
BUILD_DIR="flatpak_build"
REPO_DIR="flatpak_repo"
echo "1. Cleaning previous builds..."
rm -rf "$BUILD_DIR" "$REPO_DIR"
echo "2. Building Flatpak..."
flatpak-builder --force-clean "$BUILD_DIR" "$MANIFEST_FILE"
[ $? -ne 0 ] && { echo "Build failed."; exit 1; }
echo "3. Exporting to local repo..."
flatpak build-export "$REPO_DIR" "$BUILD_DIR"
echo "4. Installing..."
flatpak remote-delete --user local-repo 2>/dev/null || true
flatpak remote-add --user --no-gpg-verify local-repo "$REPO_DIR"
flatpak install --user -y local-repo "$APP_ID"
echo "5. Running..."
flatpak run "$APP_ID"
