#!/bin/bash
APP_ID="com.pens.IVIVehicleDashboard"
MANIFEST="com.pens.IVIVehicleDashboard.yml"
REPO_DIR="my-repo"
BUILD_DIR="build-dir"
target_arch="${1:-x86_64}"
[ ! -d "$REPO_DIR" ] && ostree init --mode=archive-z2 --repo="$REPO_DIR"
rm -rf "$BUILD_DIR"
flatpak-builder --force-clean --repo="$REPO_DIR" --arch="$target_arch" \
  --install-deps-from=flathub "$BUILD_DIR" "$MANIFEST" || { echo "Build failed!"; exit 1; }
flatpak build-update-repo "$REPO_DIR"
flatpak build-bundle "$REPO_DIR" "${APP_ID}_${target_arch}.flatpak" "$APP_ID" --arch="$target_arch"
echo "✅ Done: ${APP_ID}_${target_arch}.flatpak"
